from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cleaner_dev.db")

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    name        = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Dataset(Base):
    __tablename__ = "datasets"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    user_id           = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id        = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    filename          = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    format            = Column(String, nullable=False)
    row_count         = Column(Integer)
    col_count         = Column(Integer)
    file_path         = Column(String)
    status            = Column(String, default="ready", nullable=False)
    upload_time       = Column(DateTime, default=datetime.utcnow)

class CleaningLog(Base):
    __tablename__ = "cleaning_logs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id  = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module      = Column(String)
    column_name = Column(String)
    method      = Column(String)
    details     = Column(Text)
    applied_at  = Column(DateTime, default=datetime.utcnow)


class QualityReport(Base):
    __tablename__ = "quality_reports"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id     = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    before_missing = Column(Float)
    after_missing  = Column(Float)
    outlier_count  = Column(Integer)
    format_errors  = Column(Integer)
    report_path    = Column(String)
    created_at     = Column(DateTime, default=datetime.utcnow)


class CleaningTemplate(Base):
    __tablename__ = "cleaning_templates"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    name            = Column(String, nullable=False)
    selections_json = Column(Text, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    full_name       = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    token      = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def run_light_migrations():
    is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

    # 0. Update users columns
    try:
        inspector = inspect(engine)
        if inspector.has_table("users"):
            cols = {c["name"] for c in inspector.get_columns("users")}
            if "full_name" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
    except Exception as e:
        logger.warning("[Migration] users sütun güncellemesi başarısız: %s", e)

    # 1. Update datasets columns
    try:
        inspector = inspect(engine)
        if inspector.has_table("datasets"):
            cols = {c["name"] for c in inspector.get_columns("datasets")}
            to_add_user_id = "user_id" not in cols
            to_add_orig_fn = "original_filename" not in cols
            to_add_proj_id = "project_id" not in cols
            to_add_status = "status" not in cols

            if to_add_user_id or to_add_orig_fn or to_add_proj_id or to_add_status:
                with engine.begin() as conn:
                    if to_add_user_id:
                        if is_sqlite:
                            conn.execute(text("ALTER TABLE datasets ADD COLUMN user_id INTEGER"))
                        else:
                            conn.execute(text("ALTER TABLE datasets ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE"))
                    if to_add_orig_fn:
                        conn.execute(text("ALTER TABLE datasets ADD COLUMN original_filename VARCHAR"))
                        conn.execute(text("UPDATE datasets SET original_filename = filename WHERE original_filename IS NULL"))
                    if to_add_proj_id:
                        conn.execute(text("ALTER TABLE datasets ADD COLUMN project_id INTEGER"))
                    if to_add_status:
                        conn.execute(text("ALTER TABLE datasets ADD COLUMN status VARCHAR DEFAULT 'ready'"))
    except Exception as e:
        logger.warning("[Migration] datasets sütun güncellemesi başarısız: %s", e)

    # 2. Update cleaning_logs columns
    try:
        inspector = inspect(engine)
        if inspector.has_table("cleaning_logs"):
            log_cols = {c["name"] for c in inspector.get_columns("cleaning_logs")}
            if "user_id" not in log_cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE cleaning_logs ADD COLUMN user_id INTEGER"))
    except Exception as e:
        logger.warning("[Migration] cleaning_logs sütun güncellemesi başarısız: %s", e)

    # Add constraints on PostgreSQL if they don't exist
    if not is_sqlite:
        # ── datasets.user_id FK ──────────────────────────────────────────
        try:
            inspector = inspect(engine)
            if inspector.has_table("datasets") and inspector.has_table("users"):
                fks = inspector.get_foreign_keys("datasets")
                has_user_fk = any(
                    fk["referred_table"] == "users" and "user_id" in fk["constrained_columns"]
                    for fk in fks
                )
                if not has_user_fk:
                    with engine.begin() as conn:
                        # Only set user_id to NULL for rows whose user_id is set but points to a
                        # non-existent user. NULL rows are handled separately below.
                        conn.execute(text(
                            "UPDATE datasets SET user_id = NULL "
                            "WHERE user_id IS NOT NULL "
                            "  AND user_id NOT IN (SELECT id FROM users)"
                        ))
                        conn.execute(text(
                            "ALTER TABLE datasets "
                            "ADD CONSTRAINT fk_datasets_user "
                            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
                        ))
        except Exception as e:
            logger.warning("[Migration] datasets user FK eklenemedi: %s", e)

        # ── cleaning_logs dataset FK ─────────────────────────────────────
        try:
            inspector = inspect(engine)
            if inspector.has_table("cleaning_logs") and inspector.has_table("datasets"):
                fks = inspector.get_foreign_keys("cleaning_logs")
                has_dataset_fk = any(
                    fk["referred_table"] == "datasets" and "dataset_id" in fk["constrained_columns"]
                    for fk in fks
                )
                if not has_dataset_fk:
                    with engine.begin() as conn:
                        conn.execute(text(
                            "DELETE FROM cleaning_logs "
                            "WHERE dataset_id IS NOT NULL "
                            "  AND dataset_id NOT IN (SELECT id FROM datasets)"
                        ))
                        conn.execute(text(
                            "ALTER TABLE cleaning_logs "
                            "ADD CONSTRAINT fk_cleaning_logs_dataset "
                            "FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE"
                        ))
        except Exception as e:
            logger.warning("[Migration] cleaning_logs dataset FK eklenemedi: %s", e)

        # ── cleaning_logs user FK ────────────────────────────────────────
        try:
            inspector = inspect(engine)
            if inspector.has_table("cleaning_logs") and inspector.has_table("users"):
                fks = inspector.get_foreign_keys("cleaning_logs")
                has_user_fk = any(
                    fk["referred_table"] == "users" and "user_id" in fk["constrained_columns"]
                    for fk in fks
                )
                if not has_user_fk:
                    with engine.begin() as conn:
                        conn.execute(text(
                            "UPDATE cleaning_logs SET user_id = NULL "
                            "WHERE user_id IS NOT NULL "
                            "  AND user_id NOT IN (SELECT id FROM users)"
                        ))
                        conn.execute(text(
                            "ALTER TABLE cleaning_logs "
                            "ADD CONSTRAINT fk_cleaning_logs_user "
                            "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
                        ))
        except Exception as e:
            logger.warning("[Migration] cleaning_logs user FK eklenemedi: %s", e)

        # ── quality_reports.dataset_id FK ────────────────────────────────
        try:
            inspector = inspect(engine)
            if inspector.has_table("quality_reports") and inspector.has_table("datasets"):
                fks = inspector.get_foreign_keys("quality_reports")
                has_dataset_fk = any(
                    fk["referred_table"] == "datasets" and "dataset_id" in fk["constrained_columns"]
                    for fk in fks
                )
                if not has_dataset_fk:
                    with engine.begin() as conn:
                        conn.execute(text(
                            "DELETE FROM quality_reports "
                            "WHERE dataset_id IS NOT NULL "
                            "  AND dataset_id NOT IN (SELECT id FROM datasets)"
                        ))
                        conn.execute(text(
                            "ALTER TABLE quality_reports "
                            "ADD CONSTRAINT fk_quality_reports_dataset "
                            "FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE"
                        ))
        except Exception as e:
            logger.warning("[Migration] quality_reports dataset FK eklenemedi: %s", e)

        # ── NOT NULL enforcement — user_id ────────────────────────────────
        def _enforce_not_null_user_id(table: str, col_dict: dict) -> None:
            if col_dict.get("nullable", True):
                try:
                    with engine.begin() as conn:
                        null_count = conn.execute(
                            text(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
                        ).scalar()
                        if null_count > 0:
                            user_count = conn.execute(
                                text("SELECT COUNT(*) FROM users")
                            ).scalar()
                            if user_count == 1:
                                # Safe: assign orphan rows to the only user
                                conn.execute(text(
                                    f"UPDATE {table} SET user_id = (SELECT id FROM users LIMIT 1) "
                                    f"WHERE user_id IS NULL"
                                ))
                                logger.info(
                                    "[Migration] '%s' tablosundaki %d NULL user_id satır(lar)ı tek mevcut kullanıcıya atandı.",
                                    table, null_count,
                                )
                            else:
                                logger.warning(
                                    "[Migration] '%s' tablosunda %d NULL user_id satırı var "
                                    "ve %d kullanıcı mevcut — sahiplik belirlenemiyor. "
                                    "NOT NULL kuralı uygulanmadı. "
                                    "Manuel düzeltme: UPDATE %s SET user_id = <id> WHERE user_id IS NULL;",
                                    table, null_count, user_count, table,
                                )
                                return  # Skip NOT NULL — would break data
                        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN user_id SET NOT NULL"))
                except Exception as e:
                    logger.warning("[Migration] %s.user_id NOT NULL ayarlanamadı: %s", table, e)

        try:
            inspector = inspect(engine)
            if inspector.has_table("datasets"):
                d_cols = {c["name"]: c for c in inspector.get_columns("datasets")}
                if "user_id" in d_cols:
                    _enforce_not_null_user_id("datasets", d_cols["user_id"])
        except Exception as e:
            logger.warning("[Migration] datasets NOT NULL kontrolü başarısız: %s", e)

        try:
            inspector = inspect(engine)
            if inspector.has_table("cleaning_logs"):
                l_cols = {c["name"]: c for c in inspector.get_columns("cleaning_logs")}
                if "user_id" in l_cols:
                    _enforce_not_null_user_id("cleaning_logs", l_cols["user_id"])
        except Exception as e:
            logger.warning("[Migration] cleaning_logs NOT NULL kontrolü başarısız: %s", e)

        # ── NOT NULL enforcement — dataset_id (cleaning_logs) ────────────
        try:
            inspector = inspect(engine)
            if inspector.has_table("cleaning_logs"):
                l_cols = {c["name"]: c for c in inspector.get_columns("cleaning_logs")}
                if "dataset_id" in l_cols and l_cols["dataset_id"].get("nullable", True):
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM cleaning_logs WHERE dataset_id IS NULL"))
                        conn.execute(text(
                            "ALTER TABLE cleaning_logs ALTER COLUMN dataset_id SET NOT NULL"
                        ))
        except Exception as e:
            logger.warning("[Migration] cleaning_logs.dataset_id NOT NULL ayarlanamadı: %s", e)

        # ── NOT NULL enforcement — dataset_id (quality_reports) ──────────
        try:
            inspector = inspect(engine)
            if inspector.has_table("quality_reports"):
                r_cols = {c["name"]: c for c in inspector.get_columns("quality_reports")}
                if "dataset_id" in r_cols and r_cols["dataset_id"].get("nullable", True):
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM quality_reports WHERE dataset_id IS NULL"))
                        conn.execute(text(
                            "ALTER TABLE quality_reports ALTER COLUMN dataset_id SET NOT NULL"
                        ))
        except Exception as e:
            logger.warning("[Migration] quality_reports.dataset_id NOT NULL ayarlanamadı: %s", e)





def init_db():
    Base.metadata.create_all(bind=engine)
    run_light_migrations()
    logger.info("[DB] Tablolar hazır.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
