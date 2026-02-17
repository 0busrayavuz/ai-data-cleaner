import pandas as pd
import numpy as np
import re


def analyze_format(df: pd.DataFrame) -> dict:
    """
    Sütunlardaki format hatalarını tespit eder:
    - Sayısal görünümlü metin sütunları
    - Tarih görünümlü metin sütunları  
    - Karışık tip içeren sütunlar
    - Boşluk/özel karakter sorunları
    """
    result = {}

    for col in df.columns:
        issues = []
        recommendations = []

        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue

        dtype = str(df[col].dtype)

        # ── Kontrol 1: object tipinde ama aslında sayısal mı? ──
        if df[col].dtype == object:
            numeric_convertible = pd.to_numeric(col_data, errors='coerce').notna().sum()
            numeric_ratio = numeric_convertible / len(col_data)

            if numeric_ratio > 0.8:
                issues.append({
                    "type": "numeric_as_string",
                    "desc": f"Sütun metin tipinde ama %{round(numeric_ratio*100,1)} oranında sayısal değer içeriyor.",
                })
                recommendations.append({
                    "id": "to_numeric",
                    "name": "Sayısal Tipe Dönüştür",
                    "desc": "Sütunu float/int tipine dönüştürür, dönüşemeyen değerleri NaN yapar.",
                    "tags": ["Otomatik", "Hızlı"]
                })

        # ── Kontrol 2: Tarih formatı tespiti ──
        if df[col].dtype == object:
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',          # 2024-01-15
                r'\d{2}/\d{2}/\d{4}',           # 15/01/2024
                r'\d{2}\.\d{2}\.\d{4}',         # 15.01.2024
                r'\d{4}/\d{2}/\d{2}',           # 2024/01/15
            ]
            date_match_count = 0
            for pattern in date_patterns:
                date_match_count += col_data.astype(str).str.match(pattern).sum()

            date_ratio = date_match_count / len(col_data)
            if date_ratio > 0.5:
                issues.append({
                    "type": "date_as_string",
                    "desc": f"Sütun tarih verisi içeriyor gibi görünüyor (%{round(date_ratio*100,1)} eşleşme).",
                })
                recommendations.append({
                    "id": "to_datetime",
                    "name": "Tarih Tipine Dönüştür",
                    "desc": "Sütunu datetime tipine dönüştürür.",
                    "tags": ["Otomatik", "Hızlı"]
                })

        # ── Kontrol 3: Baştaki/sondaki boşluklar ──
        if df[col].dtype == object:
            has_whitespace = col_data.astype(str).str.strip() != col_data.astype(str)
            whitespace_count = int(has_whitespace.sum())
            if whitespace_count > 0:
                issues.append({
                    "type": "whitespace",
                    "desc": f"{whitespace_count} hücrede baş/son boşluk karakteri var.",
                })
                recommendations.append({
                    "id": "strip_whitespace",
                    "name": "Boşlukları Temizle",
                    "desc": "Tüm hücrelerdeki baş ve son boşlukları kaldırır.",
                    "tags": ["Hızlı", "Temiz"]
                })

        # ── Kontrol 4: Büyük/küçük harf tutarsızlığı ──
        if df[col].dtype == object and col_data.nunique() < 20:
            lower_vals = col_data.str.lower().unique()
            actual_vals = col_data.unique()
            if len(lower_vals) < len(actual_vals):
                issues.append({
                    "type": "case_inconsistency",
                    "desc": "Aynı değerin farklı büyük/küçük harf versiyonları var (örn: 'Erkek' ve 'erkek').",
                })
                recommendations.append({
                    "id": "normalize_case",
                    "name": "Büyük/Küçük Harf Düzenle",
                    "desc": "Tüm değerleri küçük harfe dönüştürür.",
                    "tags": ["Hızlı", "Tutarlılık"]
                })

        if issues:
            result[col] = {
                "issues": issues,
                "recommendations": recommendations,
                "dtype": dtype,
            }

    return result


def apply_format(df: pd.DataFrame, column: str, method: str) -> tuple[pd.DataFrame, str]:
    """
    Seçilen format düzeltmesini uygular.
    """
    df = df.copy()

    if method == "to_numeric":
        df[column] = pd.to_numeric(df[column], errors='coerce')
        detail = f"{column} sütunu sayısal tipe dönüştürüldü."

    elif method == "to_datetime":
        df[column] = pd.to_datetime(df[column], errors='coerce', dayfirst=True)
        detail = f"{column} sütunu tarih tipine dönüştürüldü."

    elif method == "strip_whitespace":
        df[column] = df[column].astype(str).str.strip()
        detail = f"{column} sütunundaki baş/son boşluklar temizlendi."

    elif method == "normalize_case":
        df[column] = df[column].str.lower()
        detail = f"{column} sütunu küçük harfe dönüştürüldü."

    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

    return df, detail