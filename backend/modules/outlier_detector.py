import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor


def analyze_outliers(df: pd.DataFrame) -> dict:
    """
    Sayısal sütunlar için IsolationForest ve LOF ile aykırı değer tespiti yapar.
    """
    result = {}

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) == 0:
        return result

    # ── IsolationForest (tüm sayısal sütunlara birlikte bakar) ──
    df_numeric = df[numeric_cols].dropna()

    if len(df_numeric) > 10:  # Yeterli satır yoksa çalıştırma
        iso = IsolationForest(contamination=0.05, random_state=42)
        iso_labels = iso.fit_predict(df_numeric)
        iso_outlier_indices = df_numeric.index[iso_labels == -1].tolist()
    else:
        iso_outlier_indices = []

    # ── LOF (tüm sayısal sütunlara birlikte bakar) ──
    if len(df_numeric) > 10:
        lof = LocalOutlierFactor(n_neighbors=5, contamination=0.05)
        lof_labels = lof.fit_predict(df_numeric)
        lof_outlier_indices = df_numeric.index[lof_labels == -1].tolist()
    else:
        lof_outlier_indices = []

    # Her sayısal sütun için sonuçları topla
    for col in numeric_cols:
        col_data = df[col].dropna()

        # IQR yöntemi (tek sütun bazında ek kontrol)
        Q1 = col_data.quantile(0.25)
        Q3 = col_data.quantile(0.75)
        IQR = Q3 - Q1
        iqr_outliers = col_data[(col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)]

        recommendations = [
            {
                "id": "cap",
                "name": "Sınırla (Winsorize)",
                "desc": "Aykırı değerleri %5-%95 aralığına sıkıştırır. Veri kaybı olmaz.",
                "tags": ["Güvenli", "Veri Korur"]
            },
            {
                "id": "drop_outliers",
                "name": "Aykırı Satırları Sil",
                "desc": "Tespit edilen aykırı satırları veri setinden çıkarır.",
                "tags": ["Temiz", "Veri Kaybı"]
            },
            {
                "id": "median_replace",
                "name": "Medyan ile Değiştir",
                "desc": "Aykırı değerleri sütun medyanıyla değiştirir.",
                "tags": ["Sağlam", "Hızlı"]
            },
            {
                "id": "keep",
                "name": "Olduğu Gibi Bırak",
                "desc": "Aykırı değerlere dokunma, yalnızca raporla.",
                "tags": ["Güvenli", "Pasif"]
            },
        ]

        result[col] = {
            "iqr_outlier_count": int(len(iqr_outliers)),
            "iso_outlier_count": int(sum(1 for i in iso_outlier_indices if df[col].notna().iloc[i] if i < len(df))),
            "lof_outlier_count": int(sum(1 for i in lof_outlier_indices if df[col].notna().iloc[i] if i < len(df))),
            "iqr_bounds": {"lower": round(Q1 - 1.5 * IQR, 2), "upper": round(Q3 + 1.5 * IQR, 2)},
            "recommendations": recommendations,
        }

    return result


def apply_outlier(df: pd.DataFrame, column: str, method: str) -> tuple[pd.DataFrame, str]:
    """
    Seçilen aykırı değer yöntemini uygular.
    """
    df = df.copy()

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    if method == "cap":
        df[column] = df[column].clip(lower=lower, upper=upper)
        detail = f"{column} sütunu [{round(lower,2)}, {round(upper,2)}] aralığına sınırlandırıldı."

    elif method == "drop_outliers":
        before = len(df)
        df = df[(df[column] >= lower) & (df[column] <= upper)]
        dropped = before - len(df)
        detail = f"{column} sütunundaki {dropped} aykırı satır silindi."

    elif method == "median_replace":
        median_val = df[column].median()
        mask = (df[column] < lower) | (df[column] > upper)
        df.loc[mask, column] = median_val
        detail = f"{column} sütunundaki aykırı değerler medyan ({round(median_val,2)}) ile değiştirildi."

    elif method == "keep":
        detail = f"{column} sütunundaki aykırı değerler raporlandı, değiştirilmedi."

    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

    return df, detail