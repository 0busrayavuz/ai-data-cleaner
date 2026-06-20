"""
Kimlik doğrulama router'ı.
Endpoint'ler: /register, /login, /me, /me/account,
              /me/password, /forgot-password, /reset-password
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.auth import create_access_token, get_current_user, get_password_hash, verify_password
from backend.database import Dataset, CleaningTemplate, PasswordResetToken, Project, SessionLocal, User, get_db
from backend.core.helpers import cleaned_disk_path

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


# ── Pydantic modeller ────────────────────────────────────────────────────────

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


class ChangePasswordBody(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


# ── SMTP / e-posta gönderme ──────────────────────────────────────────────────

def send_reset_email(to_email: str, token: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    if not smtp_host or not smtp_user or not smtp_pass:
        logger.info("[DEV] E-posta gönderimi yok — şifre sıfırlama token'u: %s -> %s", to_email, token)
        return False

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        port = int(smtp_port) if smtp_port else 587
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = "PrepWise - Şifre Sıfırlama Kodu"

        body = (
            f"Merhaba,\n\n"
            f"PrepWise hesabınız için şifre sıfırlama talebinde bulundunuz.\n"
            f"Şifrenizi sıfırlamak için arayüzdeki ilgili alana girmeniz gereken kod (token):\n\n"
            f"{token}\n\n"
            f"Bu kod 1 saat süreyle geçerlidir. Eğer bu talebi siz yapmadıysanız lütfen bu e-postayı "
            f"dikkate almayınız.\n\nSaygılarımızla,\nPrepWise Ekibi\n"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

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
        logger.error("SMTP gönderimi başarısız (%s): %s", to_email, e)
        logger.info("[FALLBACK] Şifre sıfırlama token'u: %s -> %s", to_email, token)
        return False


# ── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.post("/register")
@limiter.limit("3/minute")
def register_user(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kayıtlı.")
    new_user = User(email=user.email, hashed_password=get_password_hash(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Kayıt başarılı", "user_id": new_user.id}


@router.post("/login")
@limiter.limit("5/minute")
def login_user(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre.")
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "email": db_user.email}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}


@router.get("/me/account")
def account_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    datasets = db.query(Dataset).filter(Dataset.user_id == user.id).all()
    project_count = db.query(Project).filter(Project.user_id == user.id).count()
    template_count = db.query(CleaningTemplate).filter(CleaningTemplate.user_id == user.id).count()
    cleaned_count = sum(1 for d in datasets if os.path.exists(cleaned_disk_path(d)))
    total_rows = sum(d.row_count or 0 for d in datasets)
    last_upload = max((d.upload_time for d in datasets if d.upload_time), default=None)
    status_counts: dict[str, int] = {}
    for dataset in datasets:
        key = dataset.status or "ready"
        status_counts[key] = status_counts.get(key, 0) + 1

    return {
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
        },
        "usage": {
            "project_count": project_count,
            "dataset_count": len(datasets),
            "cleaned_dataset_count": cleaned_count,
            "template_count": template_count,
            "total_rows_processed": total_rows,
            "last_upload_time": last_upload.isoformat() if last_upload else None,
            "status_counts": status_counts,
        },
        "limits": {
            "max_upload_mb": 20,
            "supported_formats": ["CSV", "XLSX", "TXT"],
        },
    }


@router.post("/me/password")
def change_password(
    body: ChangePasswordBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if not verify_password(body.current_password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifre hatalı.")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="Yeni şifre mevcut şifreyle aynı olamaz.")
    db_user.hashed_password = get_password_hash(body.new_password)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == db_user.id).delete()
    db.commit()
    return {"message": "Şifreniz güncellendi."}


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, body: ForgotPasswordBody, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email).first()
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
    return {"message": "İsteğiniz alındı. E-postanız sistemde kayıtlıysa sıfırlama adımları uygulanır."}


@router.post("/reset-password")
def reset_password_ep(body: ResetPasswordBody, db: Session = Depends(get_db)):
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
