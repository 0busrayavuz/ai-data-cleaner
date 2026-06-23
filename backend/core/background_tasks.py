"""
Arka plan görevleri: analiz ve temizleme pipeline'ları.
Bunlar FastAPI BackgroundTasks tarafından çağrılır.
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
import logging

logger = logging.getLogger(__name__)

from backend.core.constants import OUTPUT_DIR
from backend.core.helpers import calculate_dataframe_health, health_score_with_row_deletion_penalty
from backend.database import CleaningLog, Dataset, QualityReport, SessionLocal
from backend.modules.file_reader import read_file, get_basic_profile
from backend.modules.pipeline import run_pipeline
from backend.modules.recommendation import generate_recommendations


def _run_analysis_async(dataset_id: int, user_id: int) -> None:
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id, Dataset.user_id == user_id
        ).first()
        if not dataset:
            return
        file_path = dataset.file_path
        df, _ = read_file(file_path)
        profile = get_basic_profile(df)
        recommendations = generate_recommendations(df)

        analysis_data = {"profile": profile, "recommendations": recommendations}
        analysis_path = os.path.join(OUTPUT_DIR, f"analysis_{dataset_id}.json")
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, ensure_ascii=False)

        dataset.status = "ready"
        db.commit()
    except Exception:
        logger.exception("Analiz görevi başarısız (dataset_id=%s)", dataset_id)
        db.rollback()
        try:
            dataset = db.query(Dataset).filter(
                Dataset.id == dataset_id, Dataset.user_id == user_id
            ).first()
            if dataset:
                dataset.status = "error"
                db.commit()
        except Exception:
            logger.exception("Analiz hata durumu kaydedilemedi (dataset_id=%s)", dataset_id)
    finally:
        db.close()


def _apply_selections_to_dataset_async(
    dataset_id: int, user_id: int, selections: list[dict]
) -> None:
    import threading

    lock = _get_dataset_lock(dataset_id)
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
                    for l in result["logs"]
                    if l["status"] == "error"
                ]
                raise Exception(
                    f"Temizleme işlemi sırasında bazı hatalar oluştu: {'; '.join(err_details)}"
                )

            output_path = os.path.join(OUTPUT_DIR, f"cleaned_{filename}")
            unique_suffix = uuid.uuid4().hex[:12]
            temp_output_path = output_path + "." + unique_suffix + ".tmp"
            backup_output_path = output_path + "." + unique_suffix + ".bak"
            report_html_path = os.path.join(OUTPUT_DIR, f"report_{dataset_id}_{unique_suffix}.html")
            report_pdf_path = os.path.join(OUTPUT_DIR, f"report_{dataset_id}_{unique_suffix}.pdf")

            result["cleaned_df"].to_csv(temp_output_path, index=False)

            outlier_ops = result.get("outlier_count", 0)
            format_ops = result.get("format_errors", 0)

            before_health_res = calculate_dataframe_health(df)
            before_health = before_health_res[0]

            after_health_res = calculate_dataframe_health(
                result["cleaned_df"], outlier_reference_df=df
            )
            after_base_health = after_health_res[0]
            after_health, row_delete_pct, row_delete_penalty = health_score_with_row_deletion_penalty(
                after_base_health, len(df), len(result["cleaned_df"])
            )
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
                "row_deletion": {"pct": row_delete_pct, "penalty": row_delete_penalty},
            }

            from backend.reporting.report_generator import generate_quality_report
            report_html_path, report_pdf_path = generate_quality_report(
                dataset_id=dataset_id,
                filename=original_filename,
                df_before=df,
                df_after=result["cleaned_df"],
                result=result,
                before_health=before_health,
                after_health=after_health,
                suffix=unique_suffix,
            )

            db = SessionLocal()
            has_backup = False  # Başlangıç değeri — except bloğunda UnboundLocalError'ı önler
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
                if has_backup:
                    if os.path.exists(backup_output_path):
                        try:
                            os.remove(backup_output_path)
                        except Exception:
                            pass
                    shutil.move(output_path, backup_output_path)

                shutil.move(temp_output_path, output_path)
                db.commit()

                try:
                    ds_to_update = db.query(Dataset).filter(Dataset.id == dataset_id).first()
                    if ds_to_update:
                        ds_to_update.status = "cleaned"
                        db.commit()
                except Exception:
                    pass

                if has_backup and os.path.exists(backup_output_path):
                    try:
                        os.remove(backup_output_path)
                    except Exception:
                        pass

                # Eski analiz cache'ini temizle — temizleme sonrası yeniden analiz
                # yapıldığında kullanıcı taze (temizlenmiş veriye ait) sonuçları görsün.
                analysis_cache_path = os.path.join(OUTPUT_DIR, f"analysis_{dataset_id}.json")
                if os.path.exists(analysis_cache_path):
                    try:
                        os.remove(analysis_cache_path)
                        logger.info("Analiz cache temizlendi (dataset_id=%s).", dataset_id)
                    except Exception:
                        logger.warning("Analiz cache silinemedi (dataset_id=%s).", dataset_id)

            except Exception as db_err:
                db.rollback()
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

        except Exception:
            logger.exception("Temizleme görevi başarısız (dataset_id=%s)", dataset_id)
            db_err_status = SessionLocal()
            try:
                ds = db_err_status.query(Dataset).filter(Dataset.id == dataset_id).first()
                if ds:
                    ds.status = "error"
                    db_err_status.commit()
            except Exception:
                logger.exception("Temizleme hata durumu kaydedilemedi (dataset_id=%s)", dataset_id)
            finally:
                db_err_status.close()

            for path in (temp_output_path, report_html_path, report_pdf_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        logger.warning("Geçici dosya silinemedi: %s", path)


def _apply_template_async(dataset_id: int, user_id: int, raw_selections: list) -> None:
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
        matched = [
            s for s in raw_selections
            if isinstance(s, dict) and s.get("column") in cols
        ]
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


# ── Dataset başına kilit (thread-safe) ───────────────────────────────────────
import threading

_dataset_locks: dict[int, threading.Lock] = {}
_dataset_locks_lock = threading.Lock()


def _get_dataset_lock(dataset_id: int) -> threading.Lock:
    with _dataset_locks_lock:
        if dataset_id not in _dataset_locks:
            _dataset_locks[dataset_id] = threading.Lock()
        return _dataset_locks[dataset_id]
