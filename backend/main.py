from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import shutil
import os

from backend.database import init_db, SessionLocal, Dataset, CleaningLog, QualityReport
from backend.modules.file_reader import read_file, get_basic_profile
from backend.modules.recommendation import generate_recommendations
from backend.modules.pipeline import run_pipeline

app = FastAPI(title="VeriTemiz AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# ── 1. Dosya Yükleme ──
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".txt", ".xlsx"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen format.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    df, meta = read_file(file_path)

    # Veritabanına kaydet
    db = SessionLocal()
    dataset = Dataset(
        filename  = meta["filename"],
        format    = meta["format"],
        row_count = meta["row_count"],
        col_count = meta["col_count"],
        file_path = file_path,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    db.close()

    return {"dataset_id": dataset.id, "meta": meta}


# ── 2. Analiz ──
@app.get("/analyze/{dataset_id}")
def analyze(dataset_id: int):
    db = SessionLocal()
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    db.close()

    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

    df, _ = read_file(dataset.file_path)
    profile = get_basic_profile(df)
    recommendations = generate_recommendations(df)

    return {"profile": profile, "recommendations": recommendations}


# ── 3. Pipeline Uygula ──
class Selection(BaseModel):
    category: str
    column:   str
    method:   str

class ApplyRequest(BaseModel):
    selections: list[Selection]

@app.post("/apply/{dataset_id}")
def apply(dataset_id: int, request: ApplyRequest):
    db = SessionLocal()
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    db.close()

    if not dataset:
        raise HTTPException(status_code=404, detail="Veri seti bulunamadı.")

    df, _ = read_file(dataset.file_path)
    selections = [s.dict() for s in request.selections]
    result = run_pipeline(df, selections)

    # Temizlenmiş dosyayı kaydet
    output_path = os.path.join(OUTPUT_DIR, f"cleaned_{dataset.filename}")
    result["cleaned_df"].to_csv(output_path, index=False)

    # Logları veritabanına kaydet
    db = SessionLocal()
    for log in result["logs"]:
        db.add(CleaningLog(
            dataset_id  = dataset_id,
            module      = log["category"],
            column_name = log["column"],
            method      = log["method"],
            details     = log["detail"],
        ))

    # Kalite raporunu kaydet
    db.add(QualityReport(
        dataset_id     = dataset_id,
        before_missing = result["before_missing_pct"],
        after_missing  = result["after_missing_pct"],
        outlier_count  = 0,
        format_errors  = 0,
    ))
    db.commit()
    db.close()

    return {
        "applied_count":      result["applied_count"],
        "error_count":        result["error_count"],
        "before_missing_pct": result["before_missing_pct"],
        "after_missing_pct":  result["after_missing_pct"],
        "output_path":        output_path,
        "logs":               result["logs"],
    }


# ── 4. Logları Getir ──
@app.get("/logs/{dataset_id}")
def get_logs(dataset_id: int):
    db = SessionLocal()
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == dataset_id).all()
    db.close()
    return {"logs": [{"column": l.column_name, "method": l.method, "detail": l.details, "time": str(l.applied_at)} for l in logs]}