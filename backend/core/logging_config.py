"""
Merkezi loglama yapılandırması.
Tüm backend modülleri bu modülden logger alır.

Kullanım:
    from backend.core.logging_config import get_logger
    logger = get_logger(__name__)
"""
import logging
import os
import sys


def configure_logging() -> None:
    """
    Uygulama genelinde logging seviyesini ve formatını ayarlar.
    Yalnızca bir kez çağrılmalıdır (main.py'de).
    """
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt=datefmt,
        stream=sys.stdout,
        force=True,
    )

    # Üçüncü parti kütüphanelerin loglarını azalt
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Modül adına göre logger döner."""
    return logging.getLogger(name)
