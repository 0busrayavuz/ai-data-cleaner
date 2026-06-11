import os
import time
import pytest

# Force the database URL to be a test-specific SQLite file before importing backend
os.environ["DATABASE_URL"] = "sqlite:///./cleaner_test.db"

import pandas as pd
from fastapi.testclient import TestClient
from backend.auth import SECRET_KEY
from backend.main import calculate_dataframe_health, app, _apply_selections_to_dataset_async
from backend.database import SessionLocal, User, Dataset, QualityReport, init_db, Base, engine
from backend.modules.format_checker import analyze_format

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("cleaner_test.db"):
        os.remove("cleaner_test.db")

def test_jwt_secret_persistence():
    # Verify outputs/.jwt_secret file exists and matches the auth key
    secret_path = os.path.join("outputs", ".jwt_secret")
    assert os.path.exists(secret_path), "outputs/.jwt_secret file should be created"
    with open(secret_path, "r", encoding="utf-8") as f:
        stored_key = f.read().strip()
    assert SECRET_KEY == stored_key, "Loaded SECRET_KEY should match stored key on disk"

def test_health_score_format_problematic_cells_counting():
    # Construct a DataFrame with 5 cells having whitespace formatting issues
    df = pd.DataFrame({
        "isim": ["  Ahmet  ", "  Mehmet  ", "  Ayse  ", "  Fatma  ", "  Ali  "]
    })

    # 1. Check analyze_format has affected_cells = 5
    res = analyze_format(df)
    assert "isim" in res
    issues = res["isim"]["issues"]
    assert len(issues) == 1
    assert issues[0]["type"] == "whitespace"
    assert issues[0]["affected_cells"] == 5, "Should report 5 affected cells"

    # 2. Check calculate_dataframe_health returns format_count = 5
    score, missing_count, outlier_count, format_count = calculate_dataframe_health(df)
    assert format_count == 5, f"Expected 5 format issues count, got {format_count}"
    assert score == 50.0


def test_health_score_uses_lower_penalty_for_outliers():
    df = pd.DataFrame({
        "value": [1.0, 1.0, 1.0, 1.0, 100.0],
        "label": ["ok"] * 5,
    })

    score, missing_count, outlier_count, format_count = calculate_dataframe_health(df)

    assert missing_count == 0
    assert outlier_count == 1
    assert format_count == 0
    assert score == 97.5


def test_health_score_can_use_original_iqr_boundaries_after_imputation():
    before = pd.DataFrame({
        "value": [0.0, 10.0, 20.0, 30.0, 40.0, None, None, None, None],
    })
    after = pd.DataFrame({
        "value": [0.0, 10.0, 20.0, 30.0, 40.0, 20.0, 20.0, 20.0, 20.0],
    })

    _, _, recalculated_outliers, _ = calculate_dataframe_health(after)
    score, missing_count, stable_outliers, format_count = calculate_dataframe_health(
        after,
        outlier_reference_df=before,
    )

    assert recalculated_outliers == 4
    assert stable_outliers == 0
    assert missing_count == 0
    assert format_count == 0
    assert score == 100.0

def _wait_for_status(ds_id: int, expected: str, timeout: float = 15.0) -> bool:
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


def test_non_overwriting_quality_reports():
    # Setup test user and dataset
    email = "test_reports_unique@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_path = "uploads/test_unique_reports.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n30,8000\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    ds = Dataset(
        user_id=u.id,
        filename="test_unique_reports.csv",
        original_filename="test_unique_reports.csv",
        format="CSV",
        row_count=2,
        col_count=2,
        file_path=file_path,
    )
    db.add(ds)
    db.commit()
    ds_id = ds.id
    u_id = u.id
    db.close()

    selections = [{"category": "missing", "column": "yas", "method": "mean"}]

    # Clean operation 1 — call background function directly for determinism
    _apply_selections_to_dataset_async(ds_id, u_id, selections)
    assert _wait_for_status(ds_id, "cleaned"), "First clean should reach 'cleaned'"

    # Reset to ready for second run
    db = SessionLocal()
    ds_obj = db.query(Dataset).filter(Dataset.id == ds_id).first()
    ds_obj.status = "ready"
    db.commit()
    db.close()

    # Clean operation 2
    _apply_selections_to_dataset_async(ds_id, u_id, selections)
    assert _wait_for_status(ds_id, "cleaned"), "Second clean should reach 'cleaned'"

    # Retrieve quality reports from the database
    db = SessionLocal()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id == ds_id).order_by(QualityReport.created_at.asc()).all()
    db.close()

    assert len(reports) == 2, "Should have 2 independent QualityReport records"
    path1 = reports[0].report_path
    path2 = reports[1].report_path

    assert path1 != path2, "Paths of historical reports should be unique"
    assert os.path.exists(path1), f"First report should exist at {path1}"
    assert os.path.exists(path2), f"Second report should exist at {path2}"

    # Clean up test files
    try:
        os.remove(file_path)
        os.remove(f"outputs/cleaned_test_unique_reports.csv")
        os.remove(path1)
        os.remove(path1.replace(".html", ".pdf"))
        os.remove(path2)
        os.remove(path2.replace(".html", ".pdf"))
    except Exception:
        pass

def test_health_score_format_overlap_capping():
    # Construct a DataFrame with 5 cells, having overlapping whitespace and numeric_as_string issues
    # Both issues will affect all 5 rows in the 'num_col' column
    df = pd.DataFrame({
        "num_col": [" 123 ", " 456 ", " 789 ", " 12 ", " 34 "]
    })

    res = analyze_format(df)
    assert len(res["num_col"]["issues"]) >= 2

    # Assert format_count is capped at 5 (taking max affected per column) and not double-counted to 10
    score, missing_count, outlier_count, format_count = calculate_dataframe_health(df)
    assert format_count == 5, f"Expected format count capped at 5, but got {format_count}"

def test_second_clean_failure_preserves_first_clean_csv():
    from unittest.mock import patch
    # Setup test user and dataset
    email = "test_rollback_safety@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_path = "uploads/test_rollback_dataset.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n30,8000\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    u_id = u.id
    ds = Dataset(
        user_id=u_id,
        filename="test_rollback_dataset.csv",
        original_filename="test_rollback_dataset.csv",
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

    # 1. First cleaning run succeeds — call directly
    _apply_selections_to_dataset_async(ds_id, u_id, selections)
    assert _wait_for_status(ds_id, "cleaned"), "First clean should succeed"

    cleaned_csv_path = "outputs/cleaned_test_rollback_dataset.csv"
    assert os.path.exists(cleaned_csv_path)

    with open(cleaned_csv_path, "r", encoding="utf-8") as f:
        first_run_content = f.read()

    # 2. Second cleaning run fails (mocked PDF crash) — call directly
    with patch("backend.reporting.report_generator.SimpleDocTemplate.build", side_effect=Exception("Mock PDF Build Crash")):
        _apply_selections_to_dataset_async(ds_id, u_id, selections)

    # Dataset should be in error state
    db = SessionLocal()
    ds_after = db.query(Dataset).filter(Dataset.id == ds_id).first()
    assert ds_after.status == "error"
    db.close()

    # 3. Assert that the original CSV from the first clean was NOT deleted or corrupted
    assert os.path.exists(cleaned_csv_path)
    with open(cleaned_csv_path, "r", encoding="utf-8") as f:
        current_content = f.read()
    assert current_content == first_run_content, "Previous valid CSV should be restored and match original content"

    # Clean up test files and DB records for this run
    try:
        os.remove(file_path)
        os.remove(cleaned_csv_path)
        db = SessionLocal()
        reports = db.query(QualityReport).filter(QualityReport.dataset_id == ds_id).all()
        db.close()
        for r in reports:
            os.remove(r.report_path)
            os.remove(r.report_path.replace(".html", ".pdf"))
    except Exception:
        pass


def test_fuzzy_duplicates_skipped_on_dates_and_numeric():
    # 6 different dates which might produce fuzzy duplicates if checked, but shouldn't be matched
    df = pd.DataFrame({
        "dates": ["2026-06-10", "2026-06-11", "2026-06-12", "2026-06-13", "2026-06-14", "2026-06-15"]
    })
    res = analyze_format(df)
    # Since it is a date column, it should not have fuzzy_duplicates issue
    if "dates" in res:
        issues = res["dates"]["issues"]
        fuzzy_issues = [x for x in issues if x["type"] == "fuzzy_duplicates"]
        assert len(fuzzy_issues) == 0, "Fuzzy duplicates check should be skipped on date columns"


def test_disjoint_format_issues_sum_and_capping():
    # 10 rows
    # 5 rows have whitespace issues (index 0 to 4), and 9 rows are numeric.
    # The 5 whitespace rows are a subset of the 9 numeric rows, so the union of affected rows is exactly 9.
    df = pd.DataFrame({
        "mix_col": [" 123 ", " 456 ", " 789 ", " 12 ", " 34 ", "123", "456", "789", "12", "abc"]
    })

    res = analyze_format(df)
    assert "mix_col" in res
    issues = res["mix_col"]["issues"]

    types = [x["type"] for x in issues]
    assert "whitespace" in types
    assert "numeric_as_string" in types

    # Union of format issues is exactly 9 unique cells
    score, missing_count, outlier_count, format_count = calculate_dataframe_health(df)
    assert format_count == 9, f"Expected format count 9 (union of format issues), but got {format_count}"


def test_download_historical_report_by_id():
    # Setup test user and dataset
    email = "test_hist_download@example.com"
    password = "password123"
    client.post("/register", json={"email": email, "password": password})
    token = client.post("/login", json={"email": email, "password": password}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_path = "uploads/test_hist_download.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("yas,gelir\n25,5000\n30,8000\n")

    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    u_id = u.id
    ds = Dataset(
        user_id=u_id,
        filename="test_hist_download.csv",
        original_filename="test_hist_download.csv",
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

    # Clean operation 1 — call background function directly
    _apply_selections_to_dataset_async(ds_id, u_id, selections)
    assert _wait_for_status(ds_id, "cleaned"), "First clean should reach 'cleaned'"

    # Reset to ready for second run
    db = SessionLocal()
    ds_obj = db.query(Dataset).filter(Dataset.id == ds_id).first()
    ds_obj.status = "ready"
    db.commit()
    db.close()

    # Clean operation 2
    _apply_selections_to_dataset_async(ds_id, u_id, selections)
    assert _wait_for_status(ds_id, "cleaned"), "Second clean should reach 'cleaned'"

    # Retrieve quality reports from the database
    db = SessionLocal()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id == ds_id).order_by(QualityReport.created_at.asc()).all()
    db.close()

    assert len(reports) == 2
    r1_id = reports[0].id
    r2_id = reports[1].id

    # Test download latest (default)
    resp_latest = client.get(f"/datasets/{ds_id}/report?format=html", headers=headers)
    assert resp_latest.status_code == 200
    assert f"kalite_raporu_{ds_id}_{r2_id}.html" in resp_latest.headers.get("content-disposition", "")

    # Test download historical r1_id
    resp_r1 = client.get(f"/datasets/{ds_id}/report?format=html&report_id={r1_id}", headers=headers)
    assert resp_r1.status_code == 200
    assert f"kalite_raporu_{ds_id}_{r1_id}.html" in resp_r1.headers.get("content-disposition", "")

    # Clean up test files
    try:
        os.remove(file_path)
        os.remove("outputs/cleaned_test_hist_download.csv")
        for r in reports:
            os.remove(r.report_path)
            os.remove(r.report_path.replace(".html", ".pdf"))
    except Exception:
        pass


def test_smtp_ssl_port_465():
    from unittest.mock import patch
    with patch("smtplib.SMTP_SSL") as mock_smtp_ssl:
        from backend.main import send_reset_email
        # Mock env vars
        with patch.dict(os.environ, {"SMTP_HOST": "smtp.gmail.com", "SMTP_PORT": "465", "SMTP_USER": "test@gmail.com", "SMTP_PASSWORD": "pass"}):
            res = send_reset_email("user@gmail.com", "token123")
            assert mock_smtp_ssl.called
