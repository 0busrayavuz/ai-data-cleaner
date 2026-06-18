"""
VeriTemiz AI - FastAPI Giriş Noktası

Bu dosya yalnızca şunları içerir:
  - FastAPI uygulaması oluşturma
  - CORS middleware yapılandırması
  - Rate limiting (SlowAPI) kurulumu
  - Uygulama başlangıç (startup) olayı
  - Router kayıtları

Tüm endpoint iş mantığı backend/routers/ altındaki dosyalara,
paylaşılan yardımcı fonksiyonlar backend/core/ altındaki dosyalara taşınmıştır.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.database import Dataset, SessionLocal, init_db
from backend.core.constants import UPLOAD_DIR, OUTPUT_DIR

# ── Router importları ─────────────────────────────────────────────────────────
from backend.routers.auth_router import router as auth_router
from backend.routers.assistant_router import router as assistant_router
from backend.routers.project_router import router as project_router
from backend.routers.template_router import router as template_router
from backend.routers.dataset_router import router as dataset_router

# ── Rate Limiter ──────────────────────────────────────────────────────────────
# IP bazlı in-memory rate limiting.
# Üretimde Redis backend kullanılması önerilir:
#   storage_uri="redis://redis:6379"
limiter = Limiter(key_func=get_remote_address)

# ── Uygulama oluşturma ────────────────────────────────────────────────────────
app = FastAPI(title="VeriTemiz AI", version="1.0.0")
app.state.limiter = limiter

# 429 Too Many Requests için Türkçe hata handler'ı
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Çok fazla istek gönderildi. Lütfen bir süre bekleyin."},
    )

app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
_default_cors = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost,http://127.0.0.1,http://localhost:80"
)
if os.getenv("CORS_ALLOW_ALL", "").strip() == "1":
    _origins = ["*"]
else:
    _origins = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", _default_cors).split(",")
        if o.strip()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Uygulama başlangıç olayı ──────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Çökmüş durumda kalan işlemleri hata olarak işaretle
    # Startup sırasında Depends kulınamaz — SessionLocal() burada kabul edilebilir
    try:
        from backend.database import SessionLocal
        with SessionLocal() as db:
            stuck = db.query(Dataset).filter(Dataset.status.in_(["processing", "analyzing"])).all()
            for ds in stuck:
                ds.status = "error"
            db.commit()
            if stuck:
                print(f"[Startup] Reset {len(stuck)} stuck dataset(s) to 'error'.")
    except Exception as _e:
        print(f"[Startup] Recovery query failed (non-fatal): {_e}")

# ── Router kayıtları ──────────────────────────────────────────────────────────
# Tüm endpoint'ler /api/v1/ prefix'i altında toplanır.
app.include_router(auth_router,      prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")
app.include_router(project_router,   prefix="/api/v1")
app.include_router(template_router,  prefix="/api/v1")
app.include_router(dataset_router,   prefix="/api/v1")
