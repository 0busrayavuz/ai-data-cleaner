from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Veritabanı dosyası database/ klasöründe oluşacak
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "cleaner.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── TABLO 1: Yüklenen veri setleri ──
class Dataset(Base):
    __tablename__ = "datasets"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    filename    = Column(String, nullable=False)
    format      = Column(String, nullable=False)   # csv / txt / xlsx
    row_count   = Column(Integer)
    col_count   = Column(Integer)
    file_path   = Column(String)
    upload_time = Column(DateTime, default=datetime.now)


# ── TABLO 2: İşlem günlüğü ──
class CleaningLog(Base):
    __tablename__ = "cleaning_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id  = Column(Integer)
    module      = Column(String)    # missing_value / outlier / format
    column_name = Column(String)
    method      = Column(String)    # KNNImputer, mean, drop vb.
    details     = Column(Text)      # JSON string olarak ek bilgi
    applied_at  = Column(DateTime, default=datetime.now)


# ── TABLO 3: Kalite raporları ──
class QualityReport(Base):
    __tablename__ = "quality_reports"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id     = Column(Integer)
    before_missing = Column(Float)   # Temizlik öncesi eksik %
    after_missing  = Column(Float)   # Temizlik sonrası eksik %
    outlier_count  = Column(Integer)
    format_errors  = Column(Integer)
    report_path    = Column(String)
    created_at     = Column(DateTime, default=datetime.now)


def init_db():
    """Tabloları oluşturur — uygulama ilk açılışında çağrılır."""
    Base.metadata.create_all(bind=engine)
    print("[DB] Veritabanı hazır:", DB_PATH)


def get_db():
    """Her istek için yeni bir oturum açar, biter kapanır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()