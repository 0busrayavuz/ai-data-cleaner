import pandas as pd
from datetime import datetime
from backend.modules.missing_value import apply_missing
from backend.modules.outlier_detector import apply_outlier
from backend.modules.format_checker import apply_format
from backend.modules.feature_engineering import apply_feature_engineering


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
    total_outliers_modified = 0
    total_format_corrected = 0

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
                current_df, detail, count = apply_outlier(current_df, column, method)
                total_outliers_modified += count

            elif category == "format":
                current_df, detail, count = apply_format(current_df, column, method)
                total_format_corrected += count

            elif category == "feature":
                current_df, detail = apply_feature_engineering(current_df, column, method)

            elif category == "duplicate":
                before_len = len(current_df)
                if method == "drop_duplicates":
                    current_df = current_df.drop_duplicates()
                    dropped = before_len - len(current_df)
                    detail = f"{dropped} adet tekrar eden (duplicate) satır silindi."
                elif method == "keep_duplicates":
                    detail = "Duplicate satırlar korundu, değişiklik yapılmadı."
                else:
                    raise ValueError(f"Bilinmeyen duplicate yöntemi: {method}")

            else:
                raise ValueError(f"Bilinmeyen kategori: {category}")


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
        "outlier_count":      total_outliers_modified,
        "format_errors":      total_format_corrected,
    }


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")
