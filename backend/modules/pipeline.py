import pandas as pd
from datetime import datetime
from backend.modules.missing_value import apply_missing
from backend.modules.outlier_detector import apply_outlier
from backend.modules.format_checker import apply_format


def run_pipeline(df: pd.DataFrame, selections: list[dict]) -> dict:
    """
    Kullanıcının seçtiği önerileri sırayla uygular.

    selections listesi şu formatta olmalı:
    [
        {"category": "missing",  "column": "yas",   "method": "mean"},
        {"category": "outlier",  "column": "gelir", "method": "cap"},
        {"category": "format",   "column": "tarih", "method": "to_datetime"},
    ]
    """
    logs = []
    current_df = df.copy()

    for selection in selections:
        category = selection.get("category")
        column   = selection.get("column")
        method   = selection.get("method")

        if column not in current_df.columns:
            logs.append({
                "status":    "error",
                "category":  category,
                "column":    column,
                "method":    method,
                "detail":    f"'{column}' sütunu bulunamadı.",
                "timestamp": _now(),
            })
            continue

        try:
            if category == "missing":
                current_df, detail = apply_missing(current_df, column, method)

            elif category == "outlier":
                current_df, detail = apply_outlier(current_df, column, method)

            elif category == "format":
                current_df, detail = apply_format(current_df, column, method)

            else:
                detail = f"Bilinmeyen kategori: {category}"

            logs.append({
                "status":    "ok",
                "category":  category,
                "column":    column,
                "method":    method,
                "detail":    detail,
                "timestamp": _now(),
            })

        except Exception as e:
            logs.append({
                "status":    "error",
                "category":  category,
                "column":    column,
                "method":    method,
                "detail":    str(e),
                "timestamp": _now(),
            })

    before_missing_pct = round(df.isnull().mean().mean() * 100, 2)
    after_missing_pct  = round(current_df.isnull().mean().mean() * 100, 2)

    return {
        "cleaned_df":         current_df,
        "logs":               logs,
        "before_missing_pct": before_missing_pct,
        "after_missing_pct":  after_missing_pct,
        "applied_count":      len([l for l in logs if l["status"] == "ok"]),
        "error_count":        len([l for l in logs if l["status"] == "error"]),
    }


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")