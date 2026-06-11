import csv
import io
import json
import math
import os
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import pandas as pd
import numpy as np
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator
import re
import threading

dataset_locks = {}
dataset_locks_lock = threading.Lock()

def get_dataset_lock(dataset_id: int) -> threading.Lock:
    with dataset_locks_lock:
        if dataset_id not in dataset_locks:
            dataset_locks[dataset_id] = threading.Lock()
        return dataset_locks[dataset_id]

from backend.auth import create_access_token, get_current_user, get_password_hash, verify_password
from backend.database import (
    SessionLocal,
    init_db,
    Dataset,
    CleaningLog,
    CleaningTemplate,
    QualityReport,
    User,
    PasswordResetToken,
    Project,
)
from backend.modules.file_reader import read_file, get_basic_profile
from backend.modules.recommendation import generate_recommendations
from backend.modules.pipeline import run_pipeline
from backend.assistant_gemini import gemini_generate_reply

app = FastAPI(title="VeriTemiz AI", version="1.0.0")

_default_cors = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost,http://127.0.0.1,http://localhost:80"
)
if os.getenv("CORS_ALLOW_ALL", "").strip() == "1":
    _origins = ["*"]
else:
    _origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_cors).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"


@app.on_event("startup")
def startup():
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Recovery: reset any rows left in an active state from a previous crashed run
    try:
        db = SessionLocal()
        stuck = db.query(Dataset).filter(Dataset.status.in_(["processing", "analyzing"])).all()
        for ds in stuck:
            ds.status = "error"
        db.commit()
        if stuck:
            print(f"[Startup] Reset {len(stuck)} stuck dataset(s) to 'error'.")
        db.close()
    except Exception as _e:
        print(f"[Startup] Recovery query failed (non-fatal): {_e}")


def _dataset_owned(db, dataset_id: int, user: User) -> Dataset | None:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if ds is None or ds.user_id != user.id:
        return None
    return ds


def _project_owned(db, project_id: int, user: User) -> Project | None:
    p = db.query(Project).filter(Project.id == project_id).first()
    if p is None or p.user_id != user.id:
        return None
    return p


def _template_owned(db, template_id: int, user: User) -> CleaningTemplate | None:
    t = db.query(CleaningTemplate).filter(CleaningTemplate.id == template_id).first()
    if t is None or t.user_id != user.id:
        return None
    return t


def _cleaned_disk_path(dataset: Dataset) -> str:
    return os.path.join(OUTPUT_DIR, f"cleaned_{dataset.filename}")


def _download_filename(dataset: Dataset) -> str:
    base = dataset.original_filename or dataset.filename
    stem = Path(base).stem
    return f"cleaned_{stem}.csv"


HEALTH_MISSING_WEIGHT = 1.00
HEALTH_FORMAT_WEIGHT = 0.50
HEALTH_OUTLIER_WEIGHT = 0.25


def _count_iqr_outliers(
    df: pd.DataFrame,
    reference_df: pd.DataFrame | None = None,
) -> int:
    """Count numeric IQR outliers using stable reference boundaries."""
    reference = reference_df if reference_df is not None else df
    numeric_cols = df.select_dtypes(include="number").columns
    total = 0

    for column in numeric_cols:
        if column not in reference.columns:
            continue
        reference_values = pd.to_numeric(reference[column], errors="coerce").dropna()
        current_values = pd.to_numeric(df[column], errors="coerce").dropna()
        if reference_values.empty or current_values.empty:
            continue

        q1 = reference_values.quantile(0.25)
        q3 = reference_values.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        total += int(((current_values < lower) | (current_values > upper)).sum())

    return total


def calculate_dataframe_health(
    df: pd.DataFrame,
    outlier_reference_df: pd.DataFrame | None = None,
) -> tuple[float, int, int, int]:
    """
    Calculates a comprehensive health score (0-100) and returns:
    (health_score, missing_count, outlier_count, format_count)

    Missing cells are the strongest quality problem. Format issues are usually
    repairable, while IQR outliers can be valid domain observations, so they
    receive progressively lower penalties.
    """
    if df.empty:
        return 0.0, 0, 0, 0

    total_cells = int(df.size)
    missing_count = int(df.isnull().sum().sum())

    # Use the original dataset as the reference after cleaning. Recalculating
    # quartiles on imputed data can narrow the IQR and falsely make unchanged
    # observations look like newly-created outliers.
    try:
        outlier_count = _count_iqr_outliers(df, outlier_reference_df)
    except Exception:
        outlier_count = 0

    # Calculate format issues
    try:
        format_count = 0
        for col in df.columns:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            if df[col].dtype == object:
                has_issue = pd.Series(False, index=df.index)

                # 1. numeric_as_string
                is_num_conv = pd.to_numeric(col_data, errors='coerce').notna()
                numeric_ratio = is_num_conv.sum() / len(col_data)
                if numeric_ratio > 0.8:
                    has_issue |= is_num_conv

                # 2. date_as_string
                date_patterns = [
                    r'\d{4}-\d{2}-\d{2}',          # 2024-01-15
                    r'\d{2}/\d{2}/\d{4}',           # 15/01/2024
                    r'\d{2}\.\d{2}\.\d{4}',         # 15.01.2024
                    r'\d{4}/\d{2}/\d{2}',           # 2024/01/15
                ]
                is_date_match = pd.Series(False, index=col_data.index)
                for pattern in date_patterns:
                    is_date_match |= col_data.astype(str).str.match(pattern)
                date_ratio = is_date_match.sum() / len(col_data)
                if date_ratio > 0.5:
                    has_issue |= is_date_match

                # 3. whitespace
                is_whitespace = col_data.astype(str).str.strip() != col_data.astype(str)
                has_issue |= is_whitespace

                # 4. case_inconsistency
                if col_data.nunique() < 20:
                    lower_vals = col_data.astype(str).str.lower().unique()
                    actual_vals = col_data.astype(str).unique()
                    if len(lower_vals) < len(actual_vals):
                        is_case_inc = col_data.apply(lambda x: x.lower() != x if isinstance(x, str) else False)
                        has_issue |= is_case_inc

                # 5. fuzzy_duplicates
                sample_data = col_data.head(100)
                is_numeric_or_date = False
                if len(sample_data) > 0:
                    numeric_convertible = pd.to_numeric(sample_data, errors='coerce').notna().sum()
                    num_ratio = numeric_convertible / len(sample_data)

                    date_match_count = 0
                    for pattern in date_patterns:
                        date_match_count += sample_data.astype(str).str.match(pattern).sum()
                    d_ratio = float(date_match_count) / len(sample_data)

                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        datetime_convertible = pd.to_datetime(sample_data, errors='coerce', dayfirst=True).notna().sum()
                    dt_ratio = datetime_convertible / len(sample_data)

                    if num_ratio > 0.8 or d_ratio > 0.5 or dt_ratio > 0.5:
                        is_numeric_or_date = True

                if not is_numeric_or_date:
                    actual_vals = col_data.dropna().unique()
                    if 2 < len(actual_vals) < 100:
                        import difflib
                        similar_pairs = []
                        for i in range(len(actual_vals)):
                            for j in range(i + 1, len(actual_vals)):
                                val1 = str(actual_vals[i])
                                val2 = str(actual_vals[j])
                                ratio = difflib.SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
                                if 0.85 <= ratio < 1.0:
                                    similar_pairs.append((val1, val2, ratio))

                        if similar_pairs:
                            value_counts = col_data.value_counts()
                            replace_keys = set()
                            for val1, val2, ratio in similar_pairs:
                                if value_counts.get(val1, 0) >= value_counts.get(val2, 0):
                                    replace_keys.add(val2)
                                else:
                                    replace_keys.add(val1)
                            is_fuzzy = col_data.isin(replace_keys)
                            has_issue |= is_fuzzy

                format_count += int(has_issue.sum())
    except Exception:
        format_count = 0

    # Weighted cell penalties:
    # - missing: 1.00 (data is unavailable)
    # - format:  0.50 (data exists but needs normalization)
    # - outlier: 0.25 (warning signal; not automatically an error)
    weighted_problems = (
        missing_count * HEALTH_MISSING_WEIGHT
        + format_count * HEALTH_FORMAT_WEIGHT
        + outlier_count * HEALTH_OUTLIER_WEIGHT
    )
    problem_ratio = weighted_problems / total_cells if total_cells > 0 else 0
    health_score = max(0.0, round(100.0 * (1.0 - problem_ratio), 2))

    return health_score, missing_count, outlier_count, format_count


def _json_scalar(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _dataframe_preview(df: pd.DataFrame, limit: int = 12) -> list[dict]:
    return [
        {str(column): _json_scalar(value) for column, value in row.items()}
        for row in df.head(limit).to_dict(orient="records")
    ]


def _profile_dataframe(df: pd.DataFrame) -> dict:
    columns = []
    for column in df.columns:
        series = df[column]
        missing_count = int(series.isna().sum())
        info = {
            "name": str(column),
            "dtype": str(series.dtype),
            "kind": "numeric" if pd.api.types.is_numeric_dtype(series) else "categorical",
            "missing_count": missing_count,
            "missing_pct": round((missing_count / len(df)) * 100, 2) if len(df) else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
        }

        if info["kind"] == "numeric":
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            if not numeric.empty:
                info["stats"] = {
                    "mean": _json_scalar(round(float(numeric.mean()), 4)),
                    "median": _json_scalar(round(float(numeric.median()), 4)),
                    "std": _json_scalar(round(float(numeric.std()), 4)) if len(numeric) > 1 else 0.0,
                    "min": _json_scalar(float(numeric.min())),
                    "max": _json_scalar(float(numeric.max())),
                    "q1": _json_scalar(float(numeric.quantile(0.25))),
                    "q3": _json_scalar(float(numeric.quantile(0.75))),
                }
                if numeric.nunique() == 1:
                    histogram = [{"label": str(_json_scalar(numeric.iloc[0])), "count": int(len(numeric))}]
                else:
                    bin_count = min(10, max(4, int(math.sqrt(len(numeric)))))
                    counts, edges = np.histogram(numeric.to_numpy(), bins=bin_count)
                    histogram = [
                        {
                            "label": f"{edges[index]:.3g} - {edges[index + 1]:.3g}",
                            "count": int(count),
                        }
                        for index, count in enumerate(counts)
                    ]
                info["distribution"] = histogram
        else:
            top_values = series.fillna("Eksik").astype(str).value_counts().head(8)
            info["top_values"] = [
                {"label": str(label), "count": int(count)}
                for label, count in top_values.items()
            ]
        columns.append(info)

    numeric_df = df.select_dtypes(include=[np.number])
    correlations = []
    if 1 < len(numeric_df.columns) <= 30:
        corr = numeric_df.corr()
        for left_index, left in enumerate(corr.columns):
            for right in corr.columns[left_index + 1:]:
                value = corr.loc[left, right]
                if pd.notna(value):
                    correlations.append({
                        "left": str(left),
                        "right": str(right),
                        "value": round(float(value), 4),
                    })
        correlations.sort(key=lambda item: abs(item["value"]), reverse=True)

    return {
        "row_count": int(len(df)),
        "col_count": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": columns,
        "correlations": correlations[:20],
        "preview": _dataframe_preview(df),
    }


def _read_cleaned_csv(path: str) -> pd.DataFrame:
    for encoding in ("utf-8", "cp1254", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Temizlenmiş CSV dosyası okunamadı.")


def _build_comparison(before: pd.DataFrame, after: pd.DataFrame) -> dict:
    before_health = calculate_dataframe_health(before)
    after_health = calculate_dataframe_health(after, outlier_reference_df=before)
    common_columns = [column for column in before.columns if column in after.columns]
    rows_aligned = len(before) == len(after)
    column_metrics = []
    changed_samples = []
    total_changed = 0 if rows_aligned else None

    for column in common_columns:
        before_series = before[column].reset_index(drop=True)
        after_series = after[column].reset_index(drop=True)
        numeric = (
            pd.api.types.is_numeric_dtype(before_series)
            and pd.api.types.is_numeric_dtype(after_series)
        )
        item = {
            "name": str(column),
            "kind": "numeric" if numeric else "categorical",
            "before_missing": int(before_series.isna().sum()),
            "after_missing": int(after_series.isna().sum()),
            "before_unique": int(before_series.nunique(dropna=True)),
            "after_unique": int(after_series.nunique(dropna=True)),
        }

        if numeric:
            item.update({
                "before_mean": _json_scalar(round(float(before_series.mean()), 4)) if before_series.notna().any() else None,
                "after_mean": _json_scalar(round(float(after_series.mean()), 4)) if after_series.notna().any() else None,
                "before_median": _json_scalar(round(float(before_series.median()), 4)) if before_series.notna().any() else None,
                "after_median": _json_scalar(round(float(after_series.median()), 4)) if after_series.notna().any() else None,
            })

        if rows_aligned:
            same = before_series.eq(after_series) | (before_series.isna() & after_series.isna())
            changed_indexes = same.index[~same]
            item["changed_cells"] = int(len(changed_indexes))
            total_changed += item["changed_cells"]
            for row_index in changed_indexes[: max(0, 20 - len(changed_samples))]:
                changed_samples.append({
                    "row": int(row_index) + 1,
                    "column": str(column),
                    "before": _json_scalar(before_series.iloc[row_index]),
                    "after": _json_scalar(after_series.iloc[row_index]),
                })
        else:
            item["changed_cells"] = None
        column_metrics.append(item)

    return {
        "rows_aligned": rows_aligned,
        "before_rows": int(len(before)),
        "after_rows": int(len(after)),
        "before_columns": int(len(before.columns)),
        "after_columns": int(len(after.columns)),
        "total_changed_cells": total_changed,
        "health": {
            "before_score": before_health[0],
            "after_score": after_health[0],
            "before": {
                "missing": before_health[1],
                "outliers": before_health[2],
                "format": before_health[3],
            },
            "after": {
                "missing": after_health[1],
                "outliers": after_health[2],
                "format": after_health[3],
            },
        },
        "weights": {
            "missing": HEALTH_MISSING_WEIGHT,
            "format": HEALTH_FORMAT_WEIGHT,
            "outlier": HEALTH_OUTLIER_WEIGHT,
        },
        "columns": column_metrics,
        "changed_samples": changed_samples,
        "before_preview": _dataframe_preview(before, limit=8),
        "after_preview": _dataframe_preview(after, limit=8),
    }


# ── 0. Kimlik Doğrulama ──
class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", v):
            raise ValueError("Geçersiz e-posta adresi.")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class AssistantChatMessage(BaseModel):
    role: Literal["user", "model"]
    text: str = Field(..., max_length=12000)


class AssistantChatBody(BaseModel):
    messages: list[AssistantChatMessage] = Field(..., min_length=1, max_length=40)


@app.post("/assistant/chat")
def assistant_chat(body: AssistantChatBody, _user: User = Depends(get_current_user)):
    """Gemini ile yardımcı asistan; API anahtarı sunucuda (GEMINI_API_KEY)."""
    msgs = [{"role": m.role, "text": m.text.strip()} for m in body.messages]
    if not msgs or not msgs[0]["text"]:
        raise HTTPException(status_code=400, detail="Geçerli bir mesaj gerekli.")
    if msgs[0]["role"] != "user":
        raise HTTPException(status_code=400, detail="Konuşma kullanıcı mesajı ile başlamalı.")
    try:
        reply = gemini_generate_reply(msgs)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception:
        raise HTTPException(status_code=502, detail="Asistan şu an yanıt veremedi. Lütfen sonra tekrar deneyin.") from None
    return {"reply": reply}


@app.post("/register")
def register_user(user: UserCreate):
    db = SessionLocal()
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        db.close()
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kayıtlı.")

    new_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return {"message": "Kayıt başarılı", "user_id": new_user.id}


@app.post("/login")
def login_user(user: UserLogin):
    db = SessionLocal()
    db_user = db.query(User).filter(User.email == user.email).first()
    db.close()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre.")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "email": db_user.email}


@app.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


def send_reset_email(to_email: str, token: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not smtp_host or not smtp_user or not smtp_pass:
        print(f"\n[DEVELOPMENT ONLY] Password reset token for {to_email}: {token}\n")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        port = int(smtp_port) if smtp_port else 587
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "VeriTemiz AI - Şifre Sıfırlama Kodu"

        body = f"""Merhaba,

VeriTemiz AI hesabınız için şifre sıfırlama talebinde bulundunuz.
Şifrenizi sıfırlamak için arayüzdeki ilgili alana girmeniz gereken kod (token):

{token}

Bu kod 1 saat süreyle geçerlidir. Eğer bu talebi siz yapmadıysanız lütfen bu e-postayı dikkate almayınız.

Saygılarımızla,
VeriTemiz AI Ekibi
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if port == 465:
            server = smtplib.SMTP_SSL(smtp_host, port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, port, timeout=10)
            server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Failed to send email to {to_email}: {str(e)}")
        print(f"\n[FALLBACK] Password reset token for {to_email}: {token}\n")
        return False


@app.post("/forgot-password")
def forgot_password(body: ForgotPasswordBody):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == body.email).first()
        token_str: str | None = None
        if u:
            token_str = uuid.uuid4().hex + uuid.uuid4().hex
            db.add(
                PasswordResetToken(
                    user_id=u.id,
                    token=token_str,
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                )
            )
            db.commit()
            send_reset_email(u.email, token_str)
        out: dict = {
            "message": "İsteğiniz alındı. E-postanız sistemde kayıtlıysa sıfırlama adımları uygulanır."
        }
        return out
    finally:
        db.close()


@app.post("/reset-password")
def reset_password_ep(body: ResetPasswordBody):
    db = SessionLocal()
    try:
        pr = db.query(PasswordResetToken).filter(PasswordResetToken.token == body.token).first()
        if not pr or pr.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş sıfırlama kodu.")
        u = db.query(User).filter(User.id == pr.user_id).first()
        if not u:
            raise HTTPException(status_code=400, detail="Kullanıcı bulunamadı.")
        u.hashed_password = get_password_hash(body.new_password)
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == u.id).delete()
        db.commit()
        return {"message": "Şifreniz güncellendi. Yeni şifreyle giriş yapabilirsiniz."}
    finally:
        db.close()


@app.get("/me/datasets")
def my_datasets(project_id: int | None = None, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        proj_rows = db.query(Project).filter(Project.user_id == user.id).order_by(Project.created_at.desc()).all()
        q = db.query(Dataset).filter(Dataset.user_id == user.id)
        if project_id is not None:
            q = q.filter(Dataset.project_id == project_id)
        rows = q.order_by(Dataset.upload_time.desc()).all()
        proj_by_id = {p.id: p.name for p in proj_rows}
        total_rows = sum(r.row_count or 0 for r in rows)
        cleaned_count = sum(1 for r in rows if os.path.exists(_cleaned_disk_path(r)))
        return {
            "projects": [{"id": p.id, "name": p.name, "description": p.description} for p in proj_rows],
            "datasets": [
                {
                    "id": r.id,
                    "project_id": r.project_id,
                    "project_name": proj_by_id.get(r.project_id) if r.project_id else None,
                    "original_filename": r.original_filename or r.filename,
                    "storage_filename": r.filename,
                    "upload_time": r.upload_time.isoformat() if r.upload_time else None,
                    "row_count": r.row_count,
                    "col_count": r.col_count,
                    "format": r.format,
                    "cleaned_ready": os.path.exists(_cleaned_disk_path(r)),
                    "status": r.status,
                }
                for r in rows
            ],
            "stats": {
                "total_rows_processed": total_rows,
                "dataset_count": len(rows),
                "cleaned_dataset_count": cleaned_count,
            },
        }
    finally:
        db.close()


# ── Projeler ──
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


@app.post("/projects")
def create_project(body: ProjectCreate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    p = Project(user_id=user.id, name=body.name.strip(), description=body.description)
    db.add(p)
    db.commit()
    db.refresh(p)
    db.close()
    return {"id": p.id, "name": p.name, "description": p.description}


@app.get("/projects")
def list_projects(user: User = Depends(get_current_user)):
    db = SessionLocal()
    rows = db.query(Project).filter(Project.user_id == user.id).order_by(Project.created_at.desc()).all()
    db.close()
    return {"projects": [{"id": r.id, "name": r.name, "description": r.description} for r in rows]}


@app.patch("/projects/{project_id}")
def update_project(project_id: int, body: ProjectUpdate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    p = _project_owned(db, project_id, user)
    if not p:
        db.close()
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    if body.name is not None:
        p.name = body.name.strip()
    if body.description is not None:
        p.description = body.description
    db.commit()
    db.refresh(p)
    updated_name = p.name
    updated_description = p.description
    db.close()
    return {"id": project_id, "name": updated_name, "description": updated_description}


# ── Pipeline seçim modeli (şablon + apply için ortak) ──
class Selection(BaseModel):
    category: str
    column: str
    method: str


class ApplyRequest(BaseModel):
    selections: list[Selection]


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    selections: list[Selection]


# ── 1. Dosya Yükleme ──
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: int | None = Form(None),
    user: User = Depends(get_current_user),
):
    safe_original = Path(file.filename or "upload").name
    ext = Path(safe_original).suffix.lower()
    if ext not in [".csv", ".txt", ".xlsx"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen format.")

    db_chk = SessionLocal()
    proj_fk = None
    if project_id is not None:
        if not _project_owned(db_chk, project_id, user):
            db_chk.close()
            raise HTTPException(status_code=404, detail="Proje bulunamadı.")
        proj_fk = project_id
    db_chk.close()

    storage_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, storage_name)
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
    size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                f.close()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(status_code=400, detail="Dosya boyutu çok büyük. Maksimum limit 20MB'dir.")
            f.write(chunk)

    try:
        df, meta = read_file(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Dosya okunamadı veya geçersiz: {str(e)}"
        )

    db = SessionLocal()
    dataset = Dataset(
        user_id=user.id,
        project_id=proj_fk,
        filename=storage_name,
        original_filename=safe_original,
        format=meta["format"],
        row_count=meta["row_count"],
        col_count=meta["col_count"],
        file_path=file_path,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    db.close()

    return {
        "dataset_id": dataset.id,
        "meta": meta,
        "original_filename": safe_original,
        "project_id": dataset.project_id,
    }


# ── Şablonlar ──
@app.get("/me/templates")
def list_templates(user: User = Depends(get_current_user)):
    db = SessionLocal()
    rows = db.query(CleaningTemplate).filter(CleaningTemplate.user_id == user.id).order_by(CleaningTemplate.created_at.desc()).all()
    db.close()
    out = []
    for r in rows:
        try:
            sel = json.loads(r.selections_json)
        except Exception:
            sel = []
        out.append({"id": r.id, "name": r.name, "selections_count": len(sel) if isinstance(sel, list) else 0})
    return {"templates": out}


@app.post("/me/templates")
def save_template(body: TemplateCreate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    t = CleaningTemplate(
        user_id=user.id,
        name=body.name.strip(),
        selections_json=json.dumps([s.model_dump() for s in body.selections], ensure_ascii=False),
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    db.close()
    return {"id": t.id, "name": t.name}


@app.delete("/me/templates/{template_id}")
def delete_template(template_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    t = _template_owned(db, template_id, user)
    if not t:
        db.close()
        raise HTTPException(status_code=404, detail="Şablon bulunamadı.")
    db.delete(t)
    db.commit()
    db.close()
    return {"ok": True}


def _apply_selections_to_dataset_async(dataset_id: int, user_id: int, selections: list[dict]):
    lock = get_dataset_lock(dataset_id)
    with lock:
        db = SessionLocal()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return
            file_path = dataset.file_path
            filename = dataset.filename
            original_filename = dataset.original_filename or dataset.filename
        except Exception:
            return
        finally:
            db.close()

        temp_output_path = None
        report_html_path = None
        report_pdf_path = None
        try:
            df, _ = read_file(file_path)
            result = run_pipeline(df, selections)

            if result["error_count"] > 0:
                err_details = [
                    f"Sütun '{l['column']}' ({l['category']}): {l['detail']}"
                    for l in result["logs"] if l["status"] == "error"
                ]
                err_msg = "; ".join(err_details)
                raise Exception(f"Temizleme işlemi sırasında bazı hatalar oluştu: {err_msg}")

            output_path = os.path.join(OUTPUT_DIR, f"cleaned_{filename}")
            unique_suffix = uuid.uuid4().hex[:12]
            temp_output_path = output_path + "." + unique_suffix + ".tmp"
            backup_output_path = output_path + "." + unique_suffix + ".bak"
            report_html_path = os.path.join(OUTPUT_DIR, f"report_{dataset_id}_{unique_suffix}.html")
            report_pdf_path = os.path.join(OUTPUT_DIR, f"report_{dataset_id}_{unique_suffix}.pdf")

            result["cleaned_df"].to_csv(temp_output_path, index=False)

            outlier_ops = result.get("outlier_count", 0)
            format_ops = result.get("format_errors", 0)

            # Health Score calculations
            before_health_res = calculate_dataframe_health(df)
            before_health = before_health_res[0]

            after_health_res = calculate_dataframe_health(
                result["cleaned_df"],
                outlier_reference_df=df,
            )
            after_base_health = after_health_res[0]

            # Penalize deleted rows (0.5 point per 1% deleted rows)
            row_delete_pct = ((len(df) - len(result["cleaned_df"])) / len(df)) * 100 if len(df) > 0 else 0
            after_health = max(0.0, round(after_base_health - row_delete_pct * 0.5, 2))
            result["health_breakdown"] = {
                "before": {
                    "missing": before_health_res[1],
                    "outliers": before_health_res[2],
                    "format": before_health_res[3],
                },
                "after": {
                    "missing": after_health_res[1],
                    "outliers": after_health_res[2],
                    "format": after_health_res[3],
                },
            }

            # Generate Reports (HTML & PDF)
            from backend.reporting.report_generator import generate_quality_report
            report_html_path, report_pdf_path = generate_quality_report(
                dataset_id=dataset_id,
                filename=original_filename,
                df_before=df,
                df_after=result["cleaned_df"],
                result=result,
                before_health=before_health,
                after_health=after_health,
                suffix=unique_suffix
            )

            db = SessionLocal()
            try:
                for log in result["logs"]:
                    db.add(
                        CleaningLog(
                            dataset_id=dataset_id,
                            user_id=user_id,
                            module=log["category"],
                            column_name=log["column"],
                            method=log["method"],
                            details=log["detail"],
                        )
                    )
                db.add(
                    QualityReport(
                        dataset_id=dataset_id,
                        before_missing=float(result["before_missing_pct"]),
                        after_missing=float(result["after_missing_pct"]),
                        outlier_count=outlier_ops,
                        format_errors=format_ops,
                        report_path=report_html_path,
                    )
                )

                has_backup = os.path.exists(output_path)

                # File finalization (move CSV) happens before database commit
                if has_backup:
                    if os.path.exists(backup_output_path):
                        try:
                            os.remove(backup_output_path)
                        except Exception:
                            pass
                    shutil.move(output_path, backup_output_path)

                shutil.move(temp_output_path, output_path)

                # Commit changes to DB
                db.commit()

                # Update dataset status to cleaned
                try:
                    ds_to_update = db.query(Dataset).filter(Dataset.id == dataset_id).first()
                    if ds_to_update:
                        ds_to_update.status = "cleaned"
                        db.commit()
                except Exception:
                    pass

                # Commit succeeded: we can delete the backup file
                if has_backup and os.path.exists(backup_output_path):
                    try:
                        os.remove(backup_output_path)
                    except Exception:
                        pass

            except Exception as db_err:
                db.rollback()
                # Revert the CSV move if DB commit fails
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                if has_backup and os.path.exists(backup_output_path):
                    try:
                        shutil.move(backup_output_path, output_path)
                    except Exception:
                        pass
                raise db_err
            finally:
                db.close()

        except Exception as e:
            # Update dataset status to error
            db_err_status = SessionLocal()
            try:
                ds_to_update = db_err_status.query(Dataset).filter(Dataset.id == dataset_id).first()
                if ds_to_update:
                    ds_to_update.status = "error"
                    db_err_status.commit()
            except Exception:
                pass
            finally:
                db_err_status.close()
            # Clean up temporary files on disk to prevent orphaned files
            if temp_output_path and os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except Exception:
                    pass
            if report_html_path and os.path.exists(report_html_path):
                try:
                    os.remove(report_html_path)
                except Exception:
                    pass
            if report_pdf_path and os.path.exists(report_pdf_path):
                try:
                    os.remove(report_pdf_path)
                except Exception:
                    pass


def _apply_template_async(dataset_id: int, user_id: int, raw_selections: list):
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            return
        file_path = dataset.file_path
    except Exception:
        return
    finally:
        db.close()

    try:
        df, _ = read_file(file_path)
        cols = set(df.columns)
        matched = [s for s in raw_selections if isinstance(s, dict) and s.get("column") in cols]
        if not matched:
            raise Exception("Şablondaki sütun adları bu dosyada yok. En az bir eşleşen sütun gerekli.")
    except Exception:
        db_err = SessionLocal()
        try:
            ds = db_err.query(Dataset).filter(Dataset.id == dataset_id).first()
            if ds:
                ds.status = "error"
                db_err.commit()
        except Exception:
            pass
        finally:
            db_err.close()
        return

    _apply_selections_to_dataset_async(dataset_id, user_id, matched)


def _run_analysis_async(dataset_id: int, user_id: int):
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user_id).first()
        if not dataset:
            return
        file_path = dataset.file_path
        df, _ = read_file(file_path)
        profile = get_basic_profile(df)
        recommendations = generate_recommendations(df)

        analysis_data = {
            "profile": profile,
            "recommendations": recommendations
        }

        analysis_path = os.path.join(OUTPUT_DIR, f"analysis_{dataset_id}.json")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False)

        dataset.status = "ready"
        db.commit()
    except Exception:
        db.rollback()
        try:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user_id).first()
            if dataset:
                dataset.status = "error"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@app.post("/apply/{dataset_id}")
def apply(
    dataset_id: int,
    request: ApplyRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        # Acquire row lock (SELECT FOR UPDATE) to serialize status check
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).with_for_update().first()
        if not dataset or dataset.user_id != user.id:
            raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

        if dataset.status in ("processing", "analyzing"):
            raise HTTPException(status_code=400, detail="Veri seti şu an başka bir işlem tarafından işleniyor.")

        dataset.status = "processing"
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    selections = [s.model_dump() for s in request.selections]
    background_tasks.add_task(_apply_selections_to_dataset_async, dataset_id, user.id, selections)
    return {"status": "processing", "message": "Temizleme işlemi arka planda başlatıldı."}


@app.post("/datasets/{dataset_id}/apply-template/{template_id}")
def apply_template(
    dataset_id: int,
    template_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    db = SessionLocal()
    try:
        t = _template_owned(db, template_id, user)
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).with_for_update().first()
        if not t or not ds or ds.user_id != user.id:
            raise HTTPException(status_code=404, detail="Şablon veya veri seti bulunamadı.")

        if ds.status in ("processing", "analyzing"):
            raise HTTPException(status_code=400, detail="Veri seti şu an başka bir işlem tarafından işleniyor.")

        try:
            raw = json.loads(t.selections_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Şablon verisi okunamadı.")
        if not isinstance(raw, list):
            raise HTTPException(status_code=400, detail="Geçersiz şablon.")

        ds.status = "processing"
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    background_tasks.add_task(_apply_template_async, dataset_id, user.id, raw)
    return {"status": "processing", "message": "Şablon temizleme işlemi arka planda başlatıldı."}


# ── 2. Analiz ──
@app.get("/analyze/{dataset_id}")
def analyze(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
):
    # ── Ownership check first — always, even for cached results ──
    # We use a plain SELECT (no lock) here; the later FOR UPDATE block
    # re-verifies before mutating state.
    db = SessionLocal()
    try:
        _chk = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not _chk or _chk.user_id != user.id:
            raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    finally:
        db.close()

    # Active operations take precedence over an older cached analysis.
    if _chk.status in ("analyzing", "processing"):
        return {"status": _chk.status, "message": "İşlem devam ediyor."}

    # Serve cached result (fast path — ownership and active state verified above)
    analysis_path = os.path.join(OUTPUT_DIR, f"analysis_{dataset_id}.json")
    if os.path.exists(analysis_path):
        try:
            with open(analysis_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    db = SessionLocal()
    try:
        # Acquire row lock to atomically check-and-set status
        dataset = (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .with_for_update()
            .first()
        )
        if not dataset or dataset.user_id != user.id:
            raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

        # Block if any active job is already running on this dataset
        if dataset.status in ("analyzing", "processing"):
            return {"status": dataset.status, "message": "İşlem devam ediyor."}

        dataset.status = "analyzing"
        db.commit()
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Analiz başlatılamadı.")
    finally:
        db.close()

    background_tasks.add_task(_run_analysis_async, dataset_id, user.id)
    return {"status": "analyzing", "message": "Analiz arka planda başlatıldı."}


@app.get("/datasets/{dataset_id}/status")
def get_dataset_status(dataset_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    db.close()
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    return {
        "dataset_id": dataset.id,
        "status": dataset.status,
    }


@app.get("/datasets/{dataset_id}/workspace")
def dataset_workspace(dataset_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    db.close()
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

    try:
        before, _ = read_file(dataset.file_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Kaynak veri okunamadı: {exc}") from exc

    cleaned_path = _cleaned_disk_path(dataset)
    cleaned_ready = os.path.exists(cleaned_path)
    comparison = None
    if cleaned_ready:
        try:
            after = _read_cleaned_csv(cleaned_path)
            comparison = _build_comparison(before, after)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Temizlenmiş veri okunamadı: {exc}") from exc

    return {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.original_filename or dataset.filename,
            "format": dataset.format,
            "status": dataset.status,
            "project_id": dataset.project_id,
            "cleaned_ready": cleaned_ready,
        },
        "profile": _profile_dataframe(before),
        "comparison": comparison,
    }


# ── Denetim & zaman çizelgesi ──
@app.get("/datasets/{dataset_id}/audit")
def dataset_audit(dataset_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    if not dataset:
        db.close()
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == dataset_id).order_by(CleaningLog.applied_at.asc()).all()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id == dataset_id).order_by(QualityReport.created_at.asc()).all()
    db.close()
    events = []
    for l in logs:
        events.append(
            {
                "type": "operation",
                "at": l.applied_at.isoformat() if l.applied_at else None,
                "module": l.module,
                "column": l.column_name,
                "method": l.method,
                "detail": l.details,
            }
        )
    for r in reports:
        events.append(
            {
                "id": r.id,
                "type": "quality_report",
                "at": r.created_at.isoformat() if r.created_at else None,
                "before_missing_pct": r.before_missing,
                "after_missing_pct": r.after_missing,
                "outlier_ops": r.outlier_count,
                "format_ops": r.format_errors,
            }
        )
    events.sort(key=lambda x: x.get("at") or "")
    return {
        "dataset_id": dataset_id,
        "filename": dataset.original_filename or dataset.filename,
        "user_email": user.email,
        "events": events,
    }


@app.get("/datasets/{dataset_id}/audit-export")
def dataset_audit_export(dataset_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    if not dataset:
        db.close()
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == dataset_id).order_by(CleaningLog.applied_at.asc()).all()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id == dataset_id).order_by(QualityReport.created_at.asc()).all()
    db.close()

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["zaman", "olay_tipi", "kullanici", "dosya", "modul", "sutun", "yontem", "detay", "ek_bilgi"])
    fn = dataset.original_filename or dataset.filename
    for l in logs:
        w.writerow(
            [
                l.applied_at.isoformat() if l.applied_at else "",
                "islem",
                user.email,
                fn,
                l.module or "",
                l.column_name or "",
                l.method or "",
                (l.details or "").replace("\n", " ")[:2000],
                "",
            ]
        )
    for r in reports:
        w.writerow(
            [
                r.created_at.isoformat() if r.created_at else "",
                "kalite_raporu",
                user.email,
                fn,
                "",
                "",
                "",
                "",
                f"eksik_once={r.before_missing}% eksik_sonra={r.after_missing}% aykiri_islem={r.outlier_count} format_islem={r.format_errors}",
            ]
        )
    buf.seek(0)
    stem = Path(fn).stem
    filename = f"denetim_{dataset_id}_{stem}.csv"
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/projects/{project_id}/timeline")
def project_timeline(project_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    p = _project_owned(db, project_id, user)
    if not p:
        db.close()
        raise HTTPException(status_code=404, detail="Proje bulunamadı.")
    dsets = db.query(Dataset).filter(Dataset.project_id == project_id, Dataset.user_id == user.id).all()
    ids = [d.id for d in dsets]
    if not ids:
        db.close()
        return {"project_id": project_id, "project_name": p.name, "events": []}
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id.in_(ids)).order_by(CleaningLog.applied_at.asc()).all()
    reports = db.query(QualityReport).filter(QualityReport.dataset_id.in_(ids)).order_by(QualityReport.created_at.asc()).all()
    ds_map = {d.id: (d.original_filename or d.filename) for d in dsets}
    db.close()

    events = []
    for l in logs:
        events.append(
            {
                "type": "operation",
                "at": l.applied_at.isoformat() if l.applied_at else None,
                "dataset_id": l.dataset_id,
                "dataset_file": ds_map.get(l.dataset_id, ""),
                "module": l.module,
                "column": l.column_name,
                "method": l.method,
                "detail": (l.details or "")[:500],
            }
        )
    for r in reports:
        events.append(
            {
                "id": r.id,
                "type": "quality_report",
                "at": r.created_at.isoformat() if r.created_at else None,
                "dataset_id": r.dataset_id,
                "dataset_file": ds_map.get(r.dataset_id, ""),
                "before_missing_pct": r.before_missing,
                "after_missing_pct": r.after_missing,
            }
        )
    events.sort(key=lambda x: x.get("at") or "")
    return {"project_id": project_id, "project_name": p.name, "events": events}


# ── 4. Loglar ──
@app.get("/logs/{dataset_id}")
def get_logs(dataset_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    if not dataset:
        db.close()
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == dataset_id).all()
    db.close()
    return {
        "logs": [
            {"column": l.column_name, "method": l.method, "detail": l.details, "time": str(l.applied_at)}
            for l in logs
        ]
    }


# ── 5. İndir ──
@app.get("/download/{dataset_id}")
def download_cleaned(dataset_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    db.close()

    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

    output_path = _cleaned_disk_path(dataset)
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Temizlenmiş dosya henüz oluşturulmadı.")

    return FileResponse(
        path=output_path,
        filename=_download_filename(dataset),
        media_type="text/csv",
    )


@app.get("/datasets/{dataset_id}/report")
def download_report(
    dataset_id: int,
    format: Literal["html", "pdf"] = "html",
    report_id: int = None,
    user: User = Depends(get_current_user)
):
    db = SessionLocal()
    dataset = _dataset_owned(db, dataset_id, user)
    if report_id:
        qr = db.query(QualityReport).filter(QualityReport.id == report_id, QualityReport.dataset_id == dataset_id).first()
    else:
        qr = db.query(QualityReport).filter(QualityReport.dataset_id == dataset_id).order_by(QualityReport.created_at.desc()).first()
    db.close()

    if not dataset or not qr:
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")

    if not qr.report_path:
        raise HTTPException(status_code=404, detail="Rapor dosyası veritabanında kayıtlı değil.")

    html_path = qr.report_path
    pdf_path = html_path.replace(".html", ".pdf")

    if format == "pdf":
        path = pdf_path
        media_type = "application/pdf"
        filename = f"kalite_raporu_{dataset_id}_{qr.id}.pdf"
    else:
        path = html_path
        media_type = "text/html"
        filename = f"kalite_raporu_{dataset_id}_{qr.id}.html"

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Rapor dosyası henüz oluşturulmadı veya bulunamadı.")

    return FileResponse(
        path=path,
        filename=filename,
        media_type=media_type,
    )
