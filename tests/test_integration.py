import os
import time
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch

# Force the database URL to be a test-specific SQLite file before importing backend
os.environ["DATABASE_URL"] = "sqlite:///./cleaner_test.db"

from fastapi.testclient import TestClient
from backend.main import app, _apply_selections_to_dataset_async
from backend.database import (
    init_db, SessionLocal, Base, engine,
    User, Project, Dataset, CleaningLog, QualityReport, PasswordResetToken,
)

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Initialize database
    init_db()
    yield
    # Clean up test database file and outputs
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("cleaner_test.db"):
        os.remove("cleaner_test.db")

    # Remove any test output/upload directories if created
    for path in ["uploads", "outputs"]:
        if os.path.exists(path):
            for f in Path(path).glob("cleaned_test_*"):
                try:
                    os.remove(f)
                except Exception:
                    pass


def _wait_for_status(ds_id: int, expected: str, timeout: float = 10.0):
    """Poll DB until dataset reaches expected status or timeout."""
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
        time.sleep(0.2)
    return False


def test_weak_registration_validation():
    # 1. Invalid email format
    resp1 = client.post("/register", json={"email": "invalid_email", "password": "securepassword123"})
    assert resp1.status_code == 422

    # 2. Too short password
    resp2 = client.post("/register", json={"email": "valid_email@example.com", "password": "1"})
    assert resp2.status_code == 422


def test_auth_and_forgot_password_flow():
    # 1. Register a test user
    email = "test_integration@example.com"
    password = "securepassword123"

    reg_resp = client.post("/register", json={"email": email, "password": password})
    assert reg_resp.status_code == 200
    assert reg_resp.json()["message"] == "Kayıt başarılı"

    # 2. Login
    login_resp = client.post("/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None

    # 3. Forgot password should NOT return reset_token in response for security reasons
    forgot_resp = client.post("/forgot-password", json={"email": email})
    assert forgot_resp.status_code == 200
    assert "reset_token" not in forgot_resp.json()

    # Query database to find the reset token for verification
    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    pr = db.query(PasswordResetToken).filter(PasswordResetToken.user_id == u.id).first()
    reset_token = pr.token
    db.close()
    assert reset_token != ""

    # 4. Reset password
    reset_resp = client.post("/reset-password", json={"token": reset_token, "new_password": "newsecurepassword123"})
    assert reset_resp.status_code == 200
    assert "güncellendi" in reset_resp.json()["message"]

    # 5. Check new login works
    new_login_resp = client.post("/login", json={"email": email, "password": "newsecurepassword123"})
    assert new_login_resp.status_code == 200


def test_project_update_detached_instance_error():
    # 1. Login user
    email = "test_project@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project
    proj_resp = client.post("/projects", json={"name": "Test Project", "description": "Original Desc"}, headers=headers)
    assert proj_resp.status_code == 200
    proj_id = proj_resp.json()["id"]

    # 3. Update project (Verifies fix for DetachedInstanceError)
    update_resp = client.patch(
        f"/projects/{proj_id}",
        json={"name": "Updated Project Name", "description": "Updated Desc"},
        headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Project Name"
    assert update_resp.json()["description"] == "Updated Desc"


def test_apply_selections_error_status_set():
    """Ensure dataset status becomes 'error' when pipeline has errors."""
    email = "test_apply@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    file_path = "uploads/test_dataset.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n30,8000\n35,NaN\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    ds = Dataset(
        user_id=u.id,
        filename="test_dataset.csv",
        original_filename="test_dataset.csv",
        format="CSV",
        row_count=3,
        col_count=2,
        file_path=file_path,
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    # Call /apply — endpoint now returns 202-like {"status": "processing"}
    selections = [{"category": "missing", "column": "non_existent_column", "method": "mean"}]
    apply_resp = client.post(f"/apply/{ds_id}", json={"selections": selections}, headers=headers)
    assert apply_resp.status_code == 200
    assert apply_resp.json()["status"] == "processing"

    # Wait for the background task (run inline since TestClient runs tasks synchronously)
    reached = _wait_for_status(ds_id, "error", timeout=10)
    assert reached, "Dataset should transition to 'error' status after failed pipeline"

    # Verify no cleaned file was saved to outputs
    cleaned_path = Path("outputs/cleaned_test_dataset.csv")
    assert not cleaned_path.exists()

    # Verify no CleaningLog or QualityReport was saved
    db = SessionLocal()
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == ds_id).all()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id == ds_id).all()
    db.close()

    assert len(logs) == 0
    assert len(reports) == 0

    try:
        os.remove(file_path)
    except Exception:
        pass


def test_unknown_pipeline_category():
    """Dataset with unknown category selection should end with error status."""
    email = "test_category@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_path = "uploads/test_category_dataset.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    ds = Dataset(
        user_id=u.id,
        filename="test_category_dataset.csv",
        original_filename="test_category_dataset.csv",
        format="CSV",
        row_count=1,
        col_count=2,
        file_path=file_path,
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    selections = [{"category": "unknown_invalid_category", "column": "yas", "method": "some_method"}]
    apply_resp = client.post(f"/apply/{ds_id}", json={"selections": selections}, headers=headers)
    assert apply_resp.status_code == 200
    assert apply_resp.json()["status"] == "processing"

    # Background task sets status to error when pipeline raises
    reached = _wait_for_status(ds_id, "error", timeout=10)
    assert reached, "Dataset should transition to 'error' after unknown category"

    try:
        os.remove(file_path)
    except Exception:
        pass


def test_successful_clean_and_report_generation():
    email = "test_success@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_path = "uploads/test_dataset_ok.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n30,8000\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    ds = Dataset(
        user_id=u.id,
        filename="test_dataset_ok.csv",
        original_filename="test_dataset_ok.csv",
        format="CSV",
        row_count=2,
        col_count=2,
        file_path=file_path,
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    selections = [{"category": "missing", "column": "yas", "method": "mean"}]

    # Apply cleaning — returns "processing"
    apply_resp = client.post(f"/apply/{ds_id}", json={"selections": selections}, headers=headers)
    assert apply_resp.status_code == 200
    assert apply_resp.json()["status"] == "processing"

    # Wait until cleaned
    reached = _wait_for_status(ds_id, "cleaned", timeout=20)
    assert reached, "Dataset should reach 'cleaned' status after successful pipeline"

    # Verify status endpoint
    status_resp = client.get(f"/datasets/{ds_id}/status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "cleaned"

    # Download HTML report
    html_resp = client.get(f"/datasets/{ds_id}/report?format=html", headers=headers)
    assert html_resp.status_code == 200
    assert b"VeriTemiz AI" in html_resp.content

    # Download PDF report
    pdf_resp = client.get(f"/datasets/{ds_id}/report?format=pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"

    # Clean up test files
    try:
        os.remove(file_path)
        os.remove("outputs/cleaned_test_dataset_ok.csv")
        db = SessionLocal()
        qr = db.query(QualityReport).filter(QualityReport.dataset_id == ds_id).first()
        db.close()
        if qr and qr.report_path:
            os.remove(qr.report_path)
            os.remove(qr.report_path.replace(".html", ".pdf"))
    except Exception:
        pass


def test_report_escaping_and_pdf_error_rollback():
    email = "test_escaping@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    special_filename = "test_<script>&_dataset.csv"
    safe_disk_filename = "test_escaping_dataset.csv"
    file_path = f"uploads/{safe_disk_filename}"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas & gelir,deger < 10\n25,5000\n30,8000\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    u_id = u.id
    ds = Dataset(
        user_id=u_id,
        filename=safe_disk_filename,
        original_filename=special_filename,
        format="CSV",
        row_count=2,
        col_count=2,
        file_path=file_path,
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    selections = [{"category": "missing", "column": "yas & gelir", "method": "mean"}]

    # 1. Apply cleaning
    apply_resp = client.post(f"/apply/{ds_id}", json={"selections": selections}, headers=headers)
    assert apply_resp.status_code == 200

    reached = _wait_for_status(ds_id, "cleaned", timeout=20)
    assert reached, "Dataset should reach 'cleaned' after escaping test"

    db = SessionLocal()
    qr = db.query(QualityReport).filter(QualityReport.dataset_id == ds_id).first()
    db.close()
    assert qr is not None
    html_path = qr.report_path
    pdf_path = html_path.replace(".html", ".pdf")
    assert os.path.exists(html_path)
    assert os.path.exists(pdf_path)

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        assert "test_&lt;script&gt;&amp;_dataset.csv" in html_content
        assert "yas &amp; gelir" in html_content

    try:
        os.remove(file_path)
        os.remove(f"outputs/cleaned_{safe_disk_filename}")
        os.remove(html_path)
        os.remove(pdf_path)
    except Exception:
        pass

    # 2. Check PDF error rollback using the internal async function directly
    file_path_err = "uploads/test_pdf_err.csv"
    with open(file_path_err, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n")

    db = SessionLocal()
    ds_err = Dataset(
        user_id=u_id,
        filename="test_pdf_err.csv",
        original_filename="test_pdf_err.csv",
        format="CSV",
        row_count=1,
        col_count=2,
        file_path=file_path_err,
        status="processing",
    )
    db.add(ds_err)
    db.commit()
    ds_err_id = ds_err.id
    db.close()

    selections_err = [{"category": "missing", "column": "yas", "method": "mean"}]
    with patch("backend.reporting.report_generator.SimpleDocTemplate.build", side_effect=Exception("Mock PDF Build Crash")):
        # Call background function directly — it handles error internally
        _apply_selections_to_dataset_async(ds_err_id, u_id, selections_err)

    # Verify dataset reaches "error" status
    db = SessionLocal()
    ds_after = db.query(Dataset).filter(Dataset.id == ds_err_id).first()
    assert ds_after.status == "error"
    db.close()

    # Verify rollback: no database records or final/temp files on disk
    cleaned_path = "outputs/cleaned_test_pdf_err.csv"
    assert not os.path.exists(cleaned_path)

    db = SessionLocal()
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == ds_err_id).all()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id == ds_err_id).all()
    db.close()

    assert len(logs) == 0
    assert len(reports) == 0

    try:
        os.remove(file_path_err)
    except Exception:
        pass


def test_apply_blocked_when_analyzing():
    """[P1] /apply must return 400 when the dataset is currently being analyzed."""
    email = "test_race_analyze@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    os.makedirs("uploads", exist_ok=True)
    file_path = "uploads/test_race_analyze.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n")

    # Insert dataset directly with status="analyzing" to simulate an in-progress analysis
    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    ds = Dataset(
        user_id=u.id,
        filename="test_race_analyze.csv",
        original_filename="test_race_analyze.csv",
        format="CSV",
        row_count=1,
        col_count=2,
        file_path=file_path,
        status="analyzing",
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    # Attempt to apply while analyzing — must be rejected
    selections = [{"category": "missing", "column": "yas", "method": "mean"}]
    resp = client.post(f"/apply/{ds_id}", json={"selections": selections}, headers=headers)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
    assert "işleniyor" in resp.json()["detail"].lower()

    try:
        os.remove(file_path)
    except Exception:
        pass


def test_analyze_blocked_when_processing():
    """[P1] /analyze must return the current status when the dataset is being cleaned."""
    email = "test_race_process@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    os.makedirs("uploads", exist_ok=True)
    file_path = "uploads/test_race_process.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n")

    # Insert dataset directly with status="processing"
    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    ds = Dataset(
        user_id=u.id,
        filename="test_race_process.csv",
        original_filename="test_race_process.csv",
        format="CSV",
        row_count=1,
        col_count=2,
        file_path=file_path,
        status="processing",
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    # Analyze endpoint should return current status without starting a new task
    resp = client.get(f"/analyze/{ds_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    # Must NOT have started a new analysis — returns current active status
    assert body.get("status") == "processing", (
        f"Expected status='processing', got: {body}"
    )

    try:
        os.remove(file_path)
    except Exception:
        pass


def test_startup_resets_stuck_datasets():
    """[P2] Startup recovery must reset processing/analyzing datasets to 'error'."""
    from backend.main import startup

    db = SessionLocal()
    # Insert two stuck datasets directly
    ds1 = Dataset(
        user_id=1,  # assumed to exist from earlier tests
        filename="stuck1.csv",
        original_filename="stuck1.csv",
        format="CSV",
        row_count=1,
        col_count=1,
        file_path="uploads/stuck1.csv",
        status="processing",
    )
    ds2 = Dataset(
        user_id=1,
        filename="stuck2.csv",
        original_filename="stuck2.csv",
        format="CSV",
        row_count=1,
        col_count=1,
        file_path="uploads/stuck2.csv",
        status="analyzing",
    )
    db.add_all([ds1, ds2])
    db.commit()
    ds1_id, ds2_id = ds1.id, ds2.id
    db.close()

    # Run startup recovery
    startup()

    # Both stuck datasets should now be "error"
    db = SessionLocal()
    after1 = db.query(Dataset).filter(Dataset.id == ds1_id).first()
    after2 = db.query(Dataset).filter(Dataset.id == ds2_id).first()
    db.close()

    assert after1.status == "error", f"Expected 'error', got '{after1.status}'"
    assert after2.status == "error", f"Expected 'error', got '{after2.status}'"


def test_analyze_cache_requires_ownership():
    """[P1] /analyze must return 404 for a dataset the requesting user doesn't own,
    even when a cached analysis_{id}.json file exists on disk."""
    # ── User A: owns the dataset ──
    email_a = "test_cache_owner@example.com"
    email_b = "test_cache_intruder@example.com"
    password = "password123"
    client.post("/register", json={"email": email_a, "password": password})
    client.post("/register", json={"email": email_b, "password": password})
    token_b = client.post("/login", json={"email": email_b, "password": password}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    file_path = "uploads/test_cache_auth.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n")

    # Create dataset owned by user A
    db = SessionLocal()
    u_a = db.query(User).filter(User.email == email_a).first()
    ds = Dataset(
        user_id=u_a.id,
        filename="test_cache_auth.csv",
        original_filename="test_cache_auth.csv",
        format="CSV",
        row_count=1,
        col_count=2,
        file_path=file_path,
        status="ready",
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    db.close()

    # Write a fake cached analysis file so the endpoint hits the cache path
    cache_path = f"outputs/analysis_{ds_id}.json"
    with open(cache_path, "w", encoding="utf-8") as f:
        import json as _json
        _json.dump({"profile": {}, "recommendations": {}}, f)

    # User B attempts to read user A's cached analysis — must be rejected
    resp = client.get(f"/analyze/{ds_id}", headers=headers_b)
    assert resp.status_code == 404, (
        f"User B should not access user A's dataset. Got {resp.status_code}: {resp.text}"
    )

    try:
        os.remove(file_path)
        os.remove(cache_path)
    except Exception:
        pass
