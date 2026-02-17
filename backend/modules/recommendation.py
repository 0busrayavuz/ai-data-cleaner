import pandas as pd
from backend.modules.missing_value import analyze_missing
from backend.modules.outlier_detector import analyze_outliers
from backend.modules.format_checker import analyze_format


def generate_recommendations(df: pd.DataFrame) -> dict:
    """
    Tüm analiz modüllerini çalıştırır ve
    birleşik öneri raporu üretir.
    """

    missing_analysis  = analyze_missing(df)
    outlier_analysis  = analyze_outliers(df)
    format_analysis   = analyze_format(df)

    recommendations = []

    # ── Eksik değer önerileri ──
    for col, info in missing_analysis.items():
        recommendations.append({
            "id":       f"missing_{col}",
            "category": "missing",
            "column":   col,
            "summary":  f"{col}: {info['missing_count']} eksik değer (%{info['missing_pct']})",
            "severity": _severity(info["missing_pct"]),
            "options":  info["recommendations"],
        })

    # ── Aykırı değer önerileri ──
    for col, info in outlier_analysis.items():
        total = max(info["iqr_outlier_count"], info["iso_outlier_count"])
        if total == 0:
            continue
        recommendations.append({
            "id":       f"outlier_{col}",
            "category": "outlier",
            "column":   col,
            "summary":  f"{col}: {total} aykırı değer tespit edildi",
            "severity": "medium" if total < 10 else "high",
            "options":  info["recommendations"],
        })

    # ── Format hata önerileri ──
    for col, info in format_analysis.items():
        for issue in info["issues"]:
            recommendations.append({
                "id":       f"format_{col}_{issue['type']}",
                "category": "format",
                "column":   col,
                "summary":  f"{col}: {issue['desc']}",
                "severity": "low",
                "options":  info["recommendations"],
            })

    return {
        "total":           len(recommendations),
        "missing_count":   len(missing_analysis),
        "outlier_count":   len(outlier_analysis),
        "format_count":    len(format_analysis),
        "recommendations": recommendations,
    }


def _severity(missing_pct: float) -> str:
    if missing_pct > 30:
        return "high"
    elif missing_pct > 10:
        return "medium"
    return "low"