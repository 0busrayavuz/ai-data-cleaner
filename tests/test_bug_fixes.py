"""
Bug Düzeltme Testleri — Kritik 4 Bug

Bug #1 — Analiz cache, temizleme sonrası temizlenmiyor
Bug #2 — Dataset silme: cleaned CSV / analiz JSON / rapor dosyaları diskte kalıyor
Bug #3 — has_backup scope: except bloğunda UnboundLocalError riski
Bug #4 — Upload orphan: DB commit başarısız olduğunda dosya diskte kalıyor
"""
import os
import json
import glob
import time
import pytest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///./cleaner_test.db")

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import (
    init_db, SessionLocal, Base, engine,
    User, Dataset, QualityReport, CleaningLog,
)
from backend.core.constants import OUTPUT_DIR, UPLOAD_DIR
from backend.core.background_tasks import _apply_selections_to_dataset_async

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("cleaner_test.db"):
        os.remove("cleaner_test.db")


@pytest.fixture(scope="module")
def shared_auth_headers():
    """Tüm testler için ortak bir kullanıcı oluşturur ve token döner. 
    Bu sayede register/login rate limitlerine (429 Too Many Requests) takılmayız."""
    email = "shared_bug_test@example.com"
    password = "password123"
    client.post("/api/v1/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Shared login başarısız: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "email": email}


def _make_dataset(user_email: str, filename: str, content: str = "yas,gelir\n25,5000\n30,8000\n") -> tuple[int, str]:
    """Disk + DB'ye test dataset'i oluşturur. (dataset_id, file_path) döner."""
    db = SessionLocal()
    u = db.query(User).filter(User.email == user_email).first()
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    ds = Dataset(
        user_id=u.id,
        filename=filename,
        original_filename=filename,
        format="CSV",
        row_count=2,
        col_count=2,
        file_path=file_path,
        status="ready",
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()
    return ds_id, file_path


def _wait_status(ds_id: int, expected: str, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        db = SessionLocal()
        ds = db.query(Dataset).filter(Dataset.id == ds_id).first()
        status = ds.status if ds else None
        db.close()
        if status == expected:
            return True
        if status == "error" and expected != "error":
            return False
        time.sleep(0.3)
    return False


# ── Bug #1: Analiz cache temizleme ───────────────────────────────────────────

class TestBug1CacheCleared:
    """Temizleme işlemi sonrasında analiz cache dosyası silinmeli."""

    def test_cache_deleted_after_apply(self, shared_auth_headers):
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug1_test.csv")

        # Sahte bir cache dosyası oluştur (analiz yapılmış gibi)
        cache_path = os.path.join(OUTPUT_DIR, f"analysis_{ds_id}.json")
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"profile": {}, "recommendations": {"recommendations": []}}, f)
        assert os.path.exists(cache_path), "Cache dosyası oluşturulmalıydı"

        # Temizleme uygula
        selections = [{"category": "missing", "column": "yas", "method": "mean"}]
        resp = client.post(f"/api/v1/apply/{ds_id}", json={"selections": selections}, headers=headers)
        assert resp.status_code == 200

        # cleaned durumuna geçmesini bekle
        reached = _wait_status(ds_id, "cleaned", timeout=20)
        assert reached, "Dataset 'cleaned' durumuna geçmeli"

        # ✅ Cache dosyası silinmiş olmalı
        assert not os.path.exists(cache_path), (
            "BUG #1: Temizleme sonrası analiz cache dosyası silinmeli ama hâlâ mevcut!"
        )

    def test_cleaned_dataset_bypasses_cache_on_reanalyze(self, shared_auth_headers):
        """'cleaned' durumundaki dataset için /analyze endpoint'i cache'i bypass etmeli."""
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug1_bypass.csv")

        # Dataset'i 'cleaned' durumuna al
        db = SessionLocal()
        ds = db.query(Dataset).filter(Dataset.id == ds_id).first()
        ds.status = "cleaned"
        db.commit()
        db.close()

        # Cache dosyası oluştur
        cache_path = os.path.join(OUTPUT_DIR, f"analysis_{ds_id}.json")
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"stale": True, "profile": {}, "recommendations": {"recommendations": []}}, f)

        # /analyze çağrısı cache'i bypass edip yeniden analiz başlatmalı
        resp = client.get(f"/api/v1/analyze/{ds_id}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()

        # ✅ Cache'deki stale veriyi DEĞİL, "analyzing" statüsünü döndürmeli
        assert body.get("status") == "analyzing", (
            f"BUG #1: 'cleaned' dataset için cache bypass çalışmıyor. Yanıt: {body}"
        )

        # Temizlik
        if os.path.exists(cache_path):
            os.remove(cache_path)


# ── Bug #2: Dataset silme dosya temizleme ────────────────────────────────────

class TestBug2DeleteCleansFiles:
    """Dataset silinirken tüm ilgili dosyalar diskten kaldırılmalı."""

    def test_delete_removes_upload_file(self, shared_auth_headers):
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug2_upload.csv")

        assert os.path.exists(file_path)
        resp = client.delete(f"/api/v1/datasets/{ds_id}", headers=headers)
        assert resp.status_code == 200

        # ✅ Ham upload dosyası silinmeli
        assert not os.path.exists(file_path), "BUG #2: Ham upload dosyası hâlâ mevcut!"

    def test_delete_removes_cleaned_csv(self, shared_auth_headers):
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug2_cleaned.csv")

        # Sahte cleaned dosyası oluştur
        cleaned_path = os.path.join(OUTPUT_DIR, "cleaned_bug2_cleaned.csv")
        with open(cleaned_path, "w") as f:
            f.write("yas,gelir\n25,5000\n")
        assert os.path.exists(cleaned_path)

        resp = client.delete(f"/api/v1/datasets/{ds_id}", headers=headers)
        assert resp.status_code == 200

        # ✅ Cleaned CSV de silinmeli
        assert not os.path.exists(cleaned_path), "BUG #2: Cleaned CSV hâlâ mevcut!"

    def test_delete_removes_analysis_cache(self, shared_auth_headers):
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug2_cache.csv")

        # Sahte analiz cache oluştur
        cache_path = os.path.join(OUTPUT_DIR, f"analysis_{ds_id}.json")
        with open(cache_path, "w") as f:
            json.dump({"test": True}, f)
        assert os.path.exists(cache_path)

        resp = client.delete(f"/api/v1/datasets/{ds_id}", headers=headers)
        assert resp.status_code == 200

        # ✅ Analiz JSON silinmeli
        assert not os.path.exists(cache_path), "BUG #2: Analiz cache JSON hâlâ mevcut!"

    def test_delete_removes_report_files(self, shared_auth_headers):
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug2_report.csv")

        # Sahte HTML ve PDF rapor oluştur
        suffix = "abc123"
        html_path = os.path.join(OUTPUT_DIR, f"report_{ds_id}_{suffix}.html")
        pdf_path = os.path.join(OUTPUT_DIR, f"report_{ds_id}_{suffix}.pdf")
        for p in [html_path, pdf_path]:
            with open(p, "w") as f:
                f.write("test report")
        assert os.path.exists(html_path) and os.path.exists(pdf_path)

        resp = client.delete(f"/api/v1/datasets/{ds_id}", headers=headers)
        assert resp.status_code == 200

        # ✅ Her iki rapor dosyası da silinmeli
        assert not os.path.exists(html_path), "BUG #2: HTML rapor hâlâ mevcut!"
        assert not os.path.exists(pdf_path), "BUG #2: PDF rapor hâlâ mevcut!"

    def test_delete_other_users_dataset_returns_404(self, shared_auth_headers):
        """Başka kullanıcının dataset'ini silmeye çalışmak 404 dönmeli."""
        # 1 test için yeni kullanıcı gerek, buna bypass ekleyeceğiz (farklı endpoint)
        headers_a = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, _ = _make_dataset(shared_auth_headers["email"], "bug2_owned.csv")
        
        # Sadece test_intruder için başka bir email kullanarak yeni bir kayıt açıyoruz
        client.post("/api/v1/register", json={"email": "intruder@example.com", "password": "password123"})
        token_b = client.post("/api/v1/login", json={"email": "intruder@example.com", "password": "password123"}).json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp = client.delete(f"/api/v1/datasets/{ds_id}", headers=headers_b)
        assert resp.status_code == 404, "Başka kullanıcının dataset'ini silemez"


# ── Bug #3: has_backup scope ──────────────────────────────────────────────────

class TestBug3HasBackupScope:
    """DB commit öncesi exception çıksa bile UnboundLocalError oluşmamalı."""

    def test_has_backup_not_unbound_when_db_fails_early(self, shared_auth_headers):
        """DB'ye kayıt sırasında exception çıkarsa dataset 'error' durumuna geçmeli,
        UnboundLocalError fırlatmamalı."""
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        ds_id, file_path = _make_dataset(shared_auth_headers["email"], "bug3_scope.csv")

        # DB commit'i patche et — Session.add çağrıldığında hata fırlat (tam has_backup'ın atandığı try bloğu)
        with patch("sqlalchemy.orm.Session.add", side_effect=Exception("Sahte DB kayıt hatası")):
            # Bu çağrı UnboundLocalError fırlatmamalı ve sadece sessizce hatayı yakalayıp çıkmalı
            try:
                _apply_selections_to_dataset_async(
                    ds_id, 1,
                    [{"category": "missing", "column": "yas", "method": "mean"}]
                )
            except Exception as e:
                pytest.fail(f"UnboundLocalError veya beklenmedik hata disariya sızdı: {e}")

        # ✅ Dataset 'error' durumuna geçmiş olmalı
        db = SessionLocal()
        ds = db.query(Dataset).filter(Dataset.id == ds_id).first()
        db.close()
        assert ds.status == "error", (
            f"BUG #3: Dataset 'error' durumuna geçmeli, ama: {ds.status}"
        )


# ── Bug #4: Upload orphan dosya ───────────────────────────────────────────────

class TestBug4UploadOrphan:
    """DB commit başarısız olduğunda upload dosyası diskte kalmamalı."""

    def test_upload_file_cleaned_on_db_failure(self, shared_auth_headers):
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}

        # Geçerli bir CSV dosyası hazırla
        import io
        csv_content = b"yas,gelir\n25,5000\n30,8000\n"
        files = {"file": ("orphan_test.csv", io.BytesIO(csv_content), "text/csv")}

        # DB commit'i patche et
        uploaded_paths: list[str] = []

        original_safe_remove = __import__(
            "backend.routers.dataset_router", fromlist=["_safe_remove"]
        )._safe_remove

        def capture_and_remove(path):
            if path:
                uploaded_paths.append(path)
            original_safe_remove(path)

        # get_db dependency'sini override ederek commit anında hata alalım
        from backend.routers.dataset_router import get_db
        from fastapi import Request

        def mock_get_db():
            db = SessionLocal()
            original_commit = db.commit
            def fake_commit():
                raise Exception("Sahte DB hatası")
            db.commit = fake_commit
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = mock_get_db

        with patch("backend.routers.dataset_router._safe_remove", side_effect=capture_and_remove):
            # /upload endpoint'ine istek at — DB hatası simüle edilecek
            # (read_file başarılı, DB commit başarısız)
            with patch("backend.routers.dataset_router.read_file", return_value=(
                __import__("pandas").DataFrame({"yas": [25], "gelir": [5000]}),
                {"format": "CSV", "row_count": 1, "col_count": 2},
            )):
                resp = client.post(
                    "/api/v1/upload",
                    files={"file": ("orphan_test.csv", io.BytesIO(csv_content), "text/csv")},
                    headers=headers,
                )
                
                # FastAPI override'ı temizle
                app.dependency_overrides.clear()
                
                # 500 dönmeli
                assert resp.status_code == 500, (
                    f"DB hatası durumunda 500 bekleniyor, alınan: {resp.status_code}"
                )
                
                # uuid ile oluşturulup _safe_remove ile silinmeye çalışılmış olmalı
                removed_files = [Path(p).name for p in uploaded_paths]
                assert len(removed_files) > 0 and removed_files[-1].endswith(".csv"), (
                    f"Orphan dosya silinmedi! _safe_remove çağrıları: {removed_files}"
                )

    def test_upload_invalid_file_not_left_on_disk(self, shared_auth_headers):
        """Geçersiz format gönderildiğinde dosya diskte kalmamalı."""
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        import io

        # Uploads dizinindeki dosya sayısını önceden say
        before_count = len(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else 0

        # Geçersiz format (JSON)
        resp = client.post(
            "/api/v1/upload",
            files={"file": ("data.json", io.BytesIO(b'{"key": "value"}'), "application/json")},
            headers=headers,
        )
        assert resp.status_code == 400

        after_count = len(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else 0

        # ✅ Yeni dosya bırakılmamalı
        assert after_count == before_count, (
            f"BUG #4: Geçersiz format yüklemesinden sonra dosya sayısı arttı: {before_count} → {after_count}"
        )

    def test_upload_corrupt_csv_not_left_on_disk(self, shared_auth_headers):
        """read_file başarısız olduğunda yüklenen dosya silinmeli."""
        headers = {k: v for k, v in shared_auth_headers.items() if k != "email"}
        import io

        before_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()

        # Bozuk içerik — CSV okuma başarısız olabilir
        corrupt_content = b"\x00\x01\x02\x03\xff\xfe" * 100

        with patch("backend.routers.dataset_router.read_file", side_effect=Exception("Okunamadı")):
            resp = client.post(
                "/api/v1/upload",
                files={"file": ("corrupt.csv", io.BytesIO(corrupt_content), "text/csv")},
                headers=headers,
            )
            assert resp.status_code == 400

        after_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()
        new_files = after_files - before_files

        # ✅ Yeni kalıcı dosya bırakılmamalı
        assert len(new_files) == 0, (
            f"BUG #4: read_file hatası sonrası upload dizininde yeni dosya(lar) kaldı: {new_files}"
        )
