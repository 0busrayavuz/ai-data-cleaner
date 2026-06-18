"""
Paylaşılan yardımcı fonksiyonlar.
- DB sahiplik kontrolleri
- DataFrame profilleme ve karşılaştırma
- Health score hesaplama
- Dosya yolu yardımcıları
"""
from __future__ import annotations

import difflib
import io
import math
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from backend.database import Dataset, CleaningTemplate, Project, User
from backend.core.constants import (
    OUTPUT_DIR,
    HEALTH_MISSING_WEIGHT,
    HEALTH_FORMAT_WEIGHT,
    HEALTH_OUTLIER_WEIGHT,
)


# ── DB sahiplik kontrolleri ───────────────────────────────────────────────────

def dataset_owned(db, dataset_id: int, user: User) -> Dataset | None:
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if ds is None or ds.user_id != user.id:
        return None
    return ds


def project_owned(db, project_id: int, user: User) -> Project | None:
    p = db.query(Project).filter(Project.id == project_id).first()
    if p is None or p.user_id != user.id:
        return None
    return p


def template_owned(db, template_id: int, user: User) -> CleaningTemplate | None:
    t = db.query(CleaningTemplate).filter(CleaningTemplate.id == template_id).first()
    if t is None or t.user_id != user.id:
        return None
    return t


# ── Dosya yolu yardımcıları ───────────────────────────────────────────────────

def cleaned_disk_path(dataset: Dataset) -> str:
    return os.path.join(OUTPUT_DIR, f"cleaned_{dataset.filename}")


def download_filename(dataset: Dataset) -> str:
    base = dataset.original_filename or dataset.filename
    stem = Path(base).stem
    return f"cleaned_{stem}.csv"


# ── JSON serileştirme yardımcısı ──────────────────────────────────────────────

def json_scalar(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def dataframe_preview(df: pd.DataFrame, limit: int = 12) -> list[dict]:
    return [
        {str(column): json_scalar(value) for column, value in row.items()}
        for row in df.head(limit).to_dict(orient="records")
    ]


# ── Health Score ──────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",
    r"\d{2}/\d{2}/\d{4}",
    r"\d{2}\.\d{2}\.\d{4}",
    r"\d{4}/\d{2}/\d{2}",
]


def _count_iqr_outliers(df: pd.DataFrame, reference_df: pd.DataFrame | None = None) -> int:
    reference = reference_df if reference_df is not None else df
    numeric_cols = df.select_dtypes(include="number").columns
    total = 0
    for column in numeric_cols:
        if column not in reference.columns:
            continue
        reference_values = pd.to_numeric(reference[column], errors="coerce").dropna()
        current_values = pd.to_numeric(df[column], errors="coerce").dropna()
        if reference_values.empty or current_values.empty:
            continue
        q1 = reference_values.quantile(0.25)
        q3 = reference_values.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        total += int(((current_values < lower) | (current_values > upper)).sum())
    return total


def calculate_dataframe_health(
    df: pd.DataFrame,
    outlier_reference_df: pd.DataFrame | None = None,
) -> tuple[float, int, int, int]:
    if df.empty:
        return 0.0, 0, 0, 0

    total_cells = int(df.size)
    missing_count = int(df.isnull().sum().sum())

    try:
        outlier_count = _count_iqr_outliers(df, outlier_reference_df)
    except Exception:
        outlier_count = 0

    try:
        format_count = 0
        for col in df.columns:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            if df[col].dtype == object:
                has_issue = pd.Series(False, index=df.index)

                is_num_conv = pd.to_numeric(col_data, errors="coerce").notna()
                if is_num_conv.sum() / len(col_data) > 0.8:
                    has_issue |= is_num_conv

                is_date_match = pd.Series(False, index=col_data.index)
                for pat in _DATE_PATTERNS:
                    is_date_match |= col_data.astype(str).str.match(pat)
                if is_date_match.sum() / len(col_data) > 0.5:
                    has_issue |= is_date_match

                is_whitespace = col_data.astype(str).str.strip() != col_data.astype(str)
                has_issue |= is_whitespace

                if col_data.nunique() < 20:
                    lower_vals = col_data.astype(str).str.lower().unique()
                    actual_vals = col_data.astype(str).unique()
                    if len(lower_vals) < len(actual_vals):
                        is_case_inc = col_data.apply(
                            lambda x: x.lower() != x if isinstance(x, str) else False
                        )
                        has_issue |= is_case_inc

                sample_data = col_data.head(100)
                is_numeric_or_date = False
                if len(sample_data) > 0:
                    num_r = pd.to_numeric(sample_data, errors="coerce").notna().sum() / len(sample_data)
                    d_cnt = sum(
                        sample_data.astype(str).str.match(p).sum() for p in _DATE_PATTERNS
                    )
                    d_r = d_cnt / len(sample_data)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        dt_r = pd.to_datetime(sample_data, errors="coerce", dayfirst=True).notna().sum() / len(sample_data)
                    if num_r > 0.8 or d_r > 0.5 or dt_r > 0.5:
                        is_numeric_or_date = True

                if not is_numeric_or_date:
                    actual_vals = col_data.dropna().unique()
                    if 2 < len(actual_vals) < 100:
                        similar_pairs = []
                        for i in range(len(actual_vals)):
                            for j in range(i + 1, len(actual_vals)):
                                val1, val2 = str(actual_vals[i]), str(actual_vals[j])
                                ratio = difflib.SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
                                if 0.85 <= ratio < 1.0:
                                    similar_pairs.append((val1, val2))
                        if similar_pairs:
                            vc = col_data.value_counts()
                            replace_keys = {
                                (v2 if vc.get(v1, 0) >= vc.get(v2, 0) else v1)
                                for v1, v2 in similar_pairs
                            }
                            has_issue |= col_data.isin(replace_keys)

                format_count += int(has_issue.sum())
    except Exception:
        format_count = 0

    weighted_problems = (
        missing_count * HEALTH_MISSING_WEIGHT
        + format_count * HEALTH_FORMAT_WEIGHT
        + outlier_count * HEALTH_OUTLIER_WEIGHT
    )
    problem_ratio = weighted_problems / total_cells if total_cells > 0 else 0
    health_score = max(0.0, round(100.0 * (1.0 - problem_ratio), 2))
    return health_score, missing_count, outlier_count, format_count


def health_score_with_row_deletion_penalty(
    base_score: float,
    before_rows: int,
    after_rows: int,
) -> tuple[float, float, float]:
    if before_rows <= 0 or after_rows >= before_rows:
        return base_score, 0.0, 0.0
    row_delete_pct = round(((before_rows - after_rows) / before_rows) * 100, 2)
    row_delete_penalty = round(row_delete_pct * 0.5, 2)
    adjusted_score = max(0.0, round(base_score - row_delete_penalty, 2))
    return adjusted_score, row_delete_pct, row_delete_penalty


# ── DataFrame profilleme ──────────────────────────────────────────────────────

def profile_dataframe(df: pd.DataFrame) -> dict:
    columns = []
    for column in df.columns:
        series = df[column]
        missing_count = int(series.isna().sum())
        info = {
            "name": str(column),
            "dtype": str(series.dtype),
            "kind": "numeric" if pd.api.types.is_numeric_dtype(series) else "categorical",
            "missing_count": missing_count,
            "missing_pct": round((missing_count / len(df)) * 100, 2) if len(df) else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
        }
        if info["kind"] == "numeric":
            numeric = pd.to_numeric(series, errors="coerce").dropna()
            if not numeric.empty:
                info["stats"] = {
                    "mean": json_scalar(round(float(numeric.mean()), 4)),
                    "median": json_scalar(round(float(numeric.median()), 4)),
                    "std": json_scalar(round(float(numeric.std()), 4)) if len(numeric) > 1 else 0.0,
                    "min": json_scalar(float(numeric.min())),
                    "max": json_scalar(float(numeric.max())),
                    "q1": json_scalar(float(numeric.quantile(0.25))),
                    "q3": json_scalar(float(numeric.quantile(0.75))),
                }
                if numeric.nunique() == 1:
                    histogram = [{"label": str(json_scalar(numeric.iloc[0])), "count": int(len(numeric))}]
                else:
                    bin_count = min(10, max(4, int(math.sqrt(len(numeric)))))
                    counts, edges = np.histogram(numeric.to_numpy(), bins=bin_count)
                    histogram = [
                        {"label": f"{edges[i]:.3g} - {edges[i + 1]:.3g}", "count": int(c)}
                        for i, c in enumerate(counts)
                    ]
                info["distribution"] = histogram
        else:
            top_values = series.fillna("Eksik").astype(str).value_counts().head(8)
            info["top_values"] = [
                {"label": str(label), "count": int(count)}
                for label, count in top_values.items()
            ]
        columns.append(info)

    numeric_df = df.select_dtypes(include=[np.number])
    correlations = []
    if 1 < len(numeric_df.columns) <= 30:
        corr = numeric_df.corr()
        for li, left in enumerate(corr.columns):
            for right in corr.columns[li + 1:]:
                value = corr.loc[left, right]
                if pd.notna(value):
                    correlations.append({"left": str(left), "right": str(right), "value": round(float(value), 4)})
        correlations.sort(key=lambda item: abs(item["value"]), reverse=True)

    return {
        "row_count": int(len(df)),
        "col_count": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": columns,
        "correlations": correlations[:20],
        "preview": dataframe_preview(df),
    }


def read_cleaned_csv(path: str) -> pd.DataFrame:
    for encoding in ("utf-8", "cp1254", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Temizlenmiş CSV dosyası okunamadı.")


def build_comparison(before: pd.DataFrame, after: pd.DataFrame) -> dict:
    before_health = calculate_dataframe_health(before)
    after_health = calculate_dataframe_health(after, outlier_reference_df=before)
    after_score, row_delete_pct, row_delete_penalty = health_score_with_row_deletion_penalty(
        after_health[0], len(before), len(after)
    )
    common_columns = [c for c in before.columns if c in after.columns]
    rows_aligned = len(before) == len(after)
    column_metrics = []
    changed_samples = []
    total_changed = 0 if rows_aligned else None

    for column in common_columns:
        before_series = before[column].reset_index(drop=True)
        after_series = after[column].reset_index(drop=True)
        numeric = (
            pd.api.types.is_numeric_dtype(before_series)
            and pd.api.types.is_numeric_dtype(after_series)
        )
        item = {
            "name": str(column),
            "kind": "numeric" if numeric else "categorical",
            "before_missing": int(before_series.isna().sum()),
            "after_missing": int(after_series.isna().sum()),
            "before_unique": int(before_series.nunique(dropna=True)),
            "after_unique": int(after_series.nunique(dropna=True)),
        }
        if numeric:
            item.update({
                "before_mean": json_scalar(round(float(before_series.mean()), 4)) if before_series.notna().any() else None,
                "after_mean": json_scalar(round(float(after_series.mean()), 4)) if after_series.notna().any() else None,
                "before_median": json_scalar(round(float(before_series.median()), 4)) if before_series.notna().any() else None,
                "after_median": json_scalar(round(float(after_series.median()), 4)) if after_series.notna().any() else None,
            })
        if rows_aligned:
            same = before_series.eq(after_series) | (before_series.isna() & after_series.isna())
            changed_indexes = same.index[~same]
            item["changed_cells"] = int(len(changed_indexes))
            total_changed += item["changed_cells"]
            for row_index in changed_indexes[: max(0, 20 - len(changed_samples))]:
                changed_samples.append({
                    "row": int(row_index) + 1,
                    "column": str(column),
                    "before": json_scalar(before_series.iloc[row_index]),
                    "after": json_scalar(after_series.iloc[row_index]),
                })
        else:
            item["changed_cells"] = None
        column_metrics.append(item)

    return {
        "rows_aligned": rows_aligned,
        "before_rows": int(len(before)),
        "after_rows": int(len(after)),
        "before_columns": int(len(before.columns)),
        "after_columns": int(len(after.columns)),
        "total_changed_cells": total_changed,
        "health": {
            "before_score": before_health[0],
            "after_score": after_score,
            "row_delete_pct": row_delete_pct,
            "row_delete_penalty": row_delete_penalty,
            "before": {"missing": before_health[1], "outliers": before_health[2], "format": before_health[3]},
            "after": {"missing": after_health[1], "outliers": after_health[2], "format": after_health[3]},
        },
        "weights": {
            "missing": HEALTH_MISSING_WEIGHT,
            "format": HEALTH_FORMAT_WEIGHT,
            "outlier": HEALTH_OUTLIER_WEIGHT,
        },
        "columns": column_metrics,
        "changed_samples": changed_samples,
        "before_preview": dataframe_preview(before, limit=8),
        "after_preview": dataframe_preview(after, limit=8),
    }
