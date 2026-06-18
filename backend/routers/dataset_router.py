"""
Dataset işlemleri router'ı.
Endpoint'ler:
  POST /upload
  GET  /me/datasets
  GET  /analyze/{dataset_id}
  POST /apply/{dataset_id}
  GET  /datasets/{dataset_id}/status
  GET  /datasets/{dataset_id}/workspace
  GET  /datasets/{dataset_id}/audit
  GET  /datasets/{dataset_id}/audit-export
  GET  /datasets/{dataset_id}/report
  GET  /logs/{dataset_id}
  GET  /download/{dataset_id}
"""
from __future__ import annotations

import csv
import io
import json
import os
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.core.background_tasks import _apply_selections_to_dataset_async, _run_analysis_async
from backend.core.constants import OUTPUT_DIR, UPLOAD_DIR
from backend.core.helpers import (
    build_comparison,
    cleaned_disk_path,
    dataset_owned,
    download_filename,
    profile_dataframe,
    project_owned,
    read_cleaned_csv,
)
from backend.database import CleaningLog, Dataset, Project, QualityReport, User, get_db
from backend.modules.file_reader import read_file

router = APIRouter()


# ── Pydantic modeller ────────────────────────────────────────────────────────

class Selection(BaseModel):
    category: str
    column: str
    method: str


class ApplyRequest(BaseModel):
    selections: list[Selection]


# ── Endpoint'ler ─────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: int | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    safe_original = Path(file.filename or "upload").name
    ext = Path(safe_original).suffix.lower()
    if ext not in [".csv", ".txt", ".xlsx"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen format.")

    proj_fk = None
    if project_id is not None:
        if not project_owned(db, project_id, user):
            raise HTTPException(status_code=404, detail="Proje bulunamadı.")
        proj_fk = project_id

    storage_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, storage_name)
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
    size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                f.close()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail="Dosya boyutu çok büyük. Maksimum limit 20MB'dir.",
                )
            f.write(chunk)

    try:
        df, meta = read_file(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail="Dosya okunamadı veya desteklenmeyen format. Lütfen geçerli bir CSV, XLSX veya TXT dosyası yükleyin.")

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
    return {
        "dataset_id": dataset.id,
        "meta": meta,
        "original_filename": safe_original,
        "project_id": dataset.project_id,
    }


@router.get("/me/datasets")
def my_datasets(
    project_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proj_rows = (
        db.query(Project)
        .filter(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
        .all()
    )
    q = db.query(Dataset).filter(Dataset.user_id == user.id)
    if project_id is not None:
        q = q.filter(Dataset.project_id == project_id)
    rows = q.order_by(Dataset.upload_time.desc()).all()
    proj_by_id = {p.id: p.name for p in proj_rows}
    total_rows = sum(r.row_count or 0 for r in rows)
    cleaned_count = sum(1 for r in rows if os.path.exists(cleaned_disk_path(r)))
    return {
        "projects": [
            {"id": p.id, "name": p.name, "description": p.description} for p in proj_rows
        ],
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
                "cleaned_ready": os.path.exists(cleaned_disk_path(r)),
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


@router.get("/analyze/{dataset_id}")
def analyze(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Sahiplik kontrolü (kilitlemesiz, hızlı yol)
    chk = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not chk or chk.user_id != user.id:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

    if chk.status in ("analyzing", "processing"):
        return {"status": chk.status, "message": "İşlem devam ediyor."}

    # Önbellek kontrolü
    analysis_path = os.path.join(OUTPUT_DIR, f"analysis_{dataset_id}.json")
    if os.path.exists(analysis_path):
        try:
            with open(analysis_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Analiz başlat — WITH_FOR_UPDATE ile durum güvenli güncelleme
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).with_for_update().first()
    if not dataset or dataset.user_id != user.id:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    if dataset.status in ("analyzing", "processing"):
        return {"status": dataset.status, "message": "İşlem devam ediyor."}

    dataset.status = "analyzing"
    db.commit()

    background_tasks.add_task(_run_analysis_async, dataset_id, user.id)
    return {"status": "analyzing", "message": "Analiz arka planda başlatıldı."}


@router.post("/apply/{dataset_id}")
def apply(
    dataset_id: int,
    request: ApplyRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).with_for_update().first()
    if not dataset or dataset.user_id != user.id:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    if dataset.status in ("processing", "analyzing"):
        raise HTTPException(
            status_code=400,
            detail="Veri seti şu an başka bir işlem tarafından işleniyor.",
        )
    dataset.status = "processing"
    db.commit()

    selections = [s.model_dump() for s in request.selections]
    background_tasks.add_task(_apply_selections_to_dataset_async, dataset_id, user.id, selections)
    return {"status": "processing", "message": "Temizleme işlemi arka planda başlatıldı."}


@router.get("/datasets/{dataset_id}/status")
def get_dataset_status(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    return {"dataset_id": dataset.id, "status": dataset.status}


@router.get("/datasets/{dataset_id}/workspace")
def dataset_workspace(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

    try:
        before, _ = read_file(dataset.file_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Orijinal veri dosyası okunamadı. Dosya silinmiş veya bozulmuş olabilir.") from exc

    cleaned_path = cleaned_disk_path(dataset)
    cleaned_ready = os.path.exists(cleaned_path)
    comparison = None
    if cleaned_ready:
        try:
            after = read_cleaned_csv(cleaned_path)
            comparison = build_comparison(before, after)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Temizlenmiş veri dosyası okunamadı. Lütfen temizleme işlemini tekrar çalıştırın.") from exc

    return {
        "dataset": {
            "id": dataset.id,
            "filename": dataset.original_filename or dataset.filename,
            "format": dataset.format,
            "status": dataset.status,
            "project_id": dataset.project_id,
            "cleaned_ready": cleaned_ready,
        },
        "profile": profile_dataframe(before),
        "comparison": comparison,
    }


@router.get("/datasets/{dataset_id}/audit")
def dataset_audit(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    logs = (
        db.query(CleaningLog)
        .filter(CleaningLog.dataset_id == dataset_id)
        .order_by(CleaningLog.applied_at.asc())
        .all()
    )
    reports = (
        db.query(QualityReport)
        .filter(QualityReport.dataset_id == dataset_id)
        .order_by(QualityReport.created_at.asc())
        .all()
    )
    events = []
    for l in logs:
        events.append({
            "type": "operation",
            "at": l.applied_at.isoformat() if l.applied_at else None,
            "module": l.module,
            "column": l.column_name,
            "method": l.method,
            "detail": l.details,
        })
    for r in reports:
        events.append({
            "id": r.id,
            "type": "quality_report",
            "at": r.created_at.isoformat() if r.created_at else None,
            "before_missing_pct": r.before_missing,
            "after_missing_pct": r.after_missing,
            "outlier_ops": r.outlier_count,
            "format_ops": r.format_errors,
        })
    events.sort(key=lambda x: x.get("at") or "")
    return {
        "dataset_id": dataset_id,
        "filename": dataset.original_filename or dataset.filename,
        "user_email": user.email,
        "events": events,
    }


@router.get("/datasets/{dataset_id}/audit-export")
def dataset_audit_export(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    logs = (
        db.query(CleaningLog)
        .filter(CleaningLog.dataset_id == dataset_id)
        .order_by(CleaningLog.applied_at.asc())
        .all()
    )
    reports = (
        db.query(QualityReport)
        .filter(QualityReport.dataset_id == dataset_id)
        .order_by(QualityReport.created_at.asc())
        .all()
    )
    fn = dataset.original_filename or dataset.filename

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["zaman", "olay_tipi", "kullanici", "dosya", "modul", "sutun", "yontem", "detay", "ek_bilgi"])
    for l in logs:
        w.writerow([
            l.applied_at.isoformat() if l.applied_at else "",
            "islem", user.email, fn,
            l.module or "", l.column_name or "", l.method or "",
            (l.details or "").replace("\n", " ")[:2000], "",
        ])
    for r in reports:
        w.writerow([
            r.created_at.isoformat() if r.created_at else "",
            "kalite_raporu", user.email, fn,
            "", "", "", "",
            f"eksik_once={r.before_missing}% eksik_sonra={r.after_missing}% aykiri_islem={r.outlier_count} format_islem={r.format_errors}",
        ])
    buf.seek(0)
    stem = Path(fn).stem
    filename = f"denetim_{dataset_id}_{stem}.csv"
    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/logs/{dataset_id}")
def get_logs(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == dataset_id).all()
    return {
        "logs": [
            {"column": l.column_name, "method": l.method, "detail": l.details, "time": str(l.applied_at)}
            for l in logs
        ]
    }


@router.get("/download/{dataset_id}")
def download_cleaned(
    dataset_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")
    output_path = cleaned_disk_path(dataset)
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Temizlenmiş dosya henüz oluşturulmadı.")
    return FileResponse(
        path=output_path,
        filename=download_filename(dataset),
        media_type="text/csv",
    )


@router.get("/datasets/{dataset_id}/report")
def download_report(
    dataset_id: int,
    format: Literal["html", "pdf"] = "html",
    report_id: int = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dataset = dataset_owned(db, dataset_id, user)
    if report_id:
        qr = (
            db.query(QualityReport)
            .filter(QualityReport.id == report_id, QualityReport.dataset_id == dataset_id)
            .first()
        )
    else:
        qr = (
            db.query(QualityReport)
            .filter(QualityReport.dataset_id == dataset_id)
            .order_by(QualityReport.created_at.desc())
            .first()
        )

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

    return FileResponse(path=path, filename=filename, media_type=media_type)
