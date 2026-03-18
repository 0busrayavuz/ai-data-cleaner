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
                    "desc": f"Sütun metin tipinde ama %{numeric_ratio*100:.1f} oranında sayısal değer içeriyor.",
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

            date_ratio = float(date_match_count) / len(col_data)
            if date_ratio > 0.5:
                issues.append({
                    "type": "date_as_string",
                    "desc": f"Sütun tarih verisi içeriyor gibi görünüyor (%{date_ratio*100:.1f} eşleşme).",
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

        # ── Kontrol 5: Semantik / Yazım Yanlışı Benzerliği (Fuzzy Matching) ──
        if df[col].dtype == object:
            actual_vals = col_data.dropna().unique()
            if 2 < len(actual_vals) < 100:
                import difflib
                similar_pairs = []
                for i in range(len(actual_vals)):
                    for j in range(i + 1, len(actual_vals)):
                        val1 = str(actual_vals[i])
                        val2 = str(actual_vals[j])
                        ratio = difflib.SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
                        if 0.85 <= ratio < 1.0:
                            similar_pairs.append((val1, val2, ratio))
                
                if similar_pairs:
                    issues.append({
                        "type": "fuzzy_duplicates",
                        "desc": f"Sütunda birbirine çok benzeyen (yazım hatalı) {len(similar_pairs)} eşleşme bulundu (Örnek: '{similar_pairs[0][0]}' ve '{similar_pairs[0][1]}').",
                    })
                    recommendations.append({
                        "id": "semantic_merge",
                        "name": "Benzer Kelimeleri Birleştir (NLP/Fuzzy)",
                        "desc": "Yazım hataları nedeniyle farklıymış gibi duran benzer kelimeleri tek bir standart kategori (en sık geçen) altında birleştirir.",
                        "tags": ["Yapay Zeka", "Temiz"]
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

    elif method == "semantic_merge":
        # En sık geçen kelimeye (mode) veya ilkine birleştirme yapacağız
        actual_vals = df[column].dropna().unique()
        import difflib
        
        value_counts = df[column].value_counts()
        replace_map = {}
        
        for i in range(len(actual_vals)):
            for j in range(i + 1, len(actual_vals)):
                val1 = str(actual_vals[i])
                val2 = str(actual_vals[j])
                ratio = difflib.SequenceMatcher(None, val1.lower(), val2.lower()).ratio()
                if 0.85 <= ratio < 1.0:
                    # Keep the one that is more frequent
                    if value_counts.get(val1, 0) >= value_counts.get(val2, 0):
                        replace_map[val2] = val1
                    else:
                        replace_map[val1] = val2

        mapped_count = len(replace_map)
        if mapped_count > 0:
            df[column] = df[column].replace(replace_map)
            detail = f"{column} sütununda birbirine benzeyen (yazım hatalı) kelimeler {mapped_count} kez ana kategoriyle birleştirildi."
        else:
            detail = f"{column} sütununda birleştirilecek kelime bulunamadı."

    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

    return df, detail