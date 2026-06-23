import os
from datetime import datetime, timedelta
import logging

import bcrypt
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.database import SessionLocal, User

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "cleaner_default_secret_key_9921_xyz":
    import secrets
    secret_path = os.path.join("outputs", ".jwt_secret")
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                SECRET_KEY = f.read().strip()
        except Exception as e:
            logger.error("Kalıcı secret key okunamadı: %s", e)
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_hex(32)
        try:
            os.makedirs("outputs", exist_ok=True)
            with open(secret_path, "w", encoding="utf-8") as f:
                f.write(SECRET_KEY)
            logger.info("Yeni kalıcı SECRET_KEY üretildi ve diske kaydedildi.")
        except Exception as e:
            logger.error("Kalıcı secret key diske yazılamadı: %s", e)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", str(30)))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Oturum gerekli. Lütfen giriş yapın.")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Geçersiz token tipi.")
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Geçersiz oturum.")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş oturum.")
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error("Kullanıcı sorgusu başarısız: %s", e)
        raise HTTPException(status_code=500, detail="Kimlik doğrulama sırasında bir hata oluştu.")
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    return user
