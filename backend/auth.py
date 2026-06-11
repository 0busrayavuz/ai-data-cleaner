import os
from datetime import datetime, timedelta

import bcrypt
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.database import SessionLocal, User

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "cleaner_default_secret_key_9921_xyz":
    import secrets
    import logging
    secret_path = os.path.join("outputs", ".jwt_secret")
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                SECRET_KEY = f.read().strip()
        except Exception as e:
            logging.error(f"Failed to read persistent secret key: {e}")
    if not SECRET_KEY:
        SECRET_KEY = secrets.token_hex(32)
        try:
            os.makedirs("outputs", exist_ok=True)
            with open(secret_path, "w", encoding="utf-8") as f:
                f.write(SECRET_KEY)
            logging.info("Generated a new persistent secure SECRET_KEY.")
        except Exception as e:
            logging.error(f"Failed to write persistent secret key: {e}")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

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
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Oturum gerekli. Lütfen giriş yapın.")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Geçersiz oturum.")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş oturum.")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
    finally:
        db.close()
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı.")
    return user
