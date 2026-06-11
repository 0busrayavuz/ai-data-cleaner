import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import ExtraTreesRegressor


def analyze_missing(df: pd.DataFrame) -> dict:
    """
    Her sütun için eksik değer analizi yapar ve
    sütun tipine göre hangi yöntemlerin uygun olduğunu önerir.
    """
    result = {}

    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        if missing_count == 0:
            continue  # Eksik değer yoksa atla

        missing_pct = round(df[col].isnull().mean() * 100, 2)
        is_numeric = pd.api.types.is_numeric_dtype(df[col])

        # Sütun tipine göre öneri listesi oluştur
        if is_numeric:
            recommendations = [
                {
                    "id": "mice",
                    "name": "AI Tahminci (MICE)",
                    "desc": "Eksik değerleri, tablodaki diğer tüm sütunların desenlerini öğrenen bir Makine Öğrenmesi (ExtraTrees) modeli ile doldurur. Kurumsal standarttır.",
                    "tags": ["Yapay Zeka", "En Yüksek Doğruluk"]
                },
                {
                    "id": "knn",
                    "name": "KNN Imputer (k=5)",
                    "desc": "En yakın 5 komşunun ortalamasıyla doldurur. Yüksek doğruluk, veri dağılımını korur.",
                    "tags": ["Yüksek Doğruluk", "Yavaş"]
                },
                {
                    "id": "mean",
                    "name": "Ortalama ile Doldur",
                    "desc": "Sütun ortalamasıyla doldurur. Hızlı ama aykırı değerlere duyarlı.",
                    "tags": ["Hızlı", "Basit"]
                },
                {
                    "id": "median",
                    "name": "Medyan ile Doldur",
                    "desc": "Sütun medyanıyla doldurur. Aykırı değerlere karşı sağlamlı.",
                    "tags": ["Sağlam", "Orta Hız"]
                },
                {
                    "id": "drop",
                    "name": "Satırı Sil",
                    "desc": "Eksik değer içeren satırı tamamen siler. Veri kaybı riski var.",
                    "tags": ["Hızlı", "Veri Kaybı"]
                },
            ]
        else:
            recommendations = [
                {
                    "id": "mode",
                    "name": "Mod ile Doldur",
                    "desc": "En sık tekrar eden değerle doldurur. Kategorik veriler için idealdir.",
                    "tags": ["Hızlı", "Kategorik"]
                },
                {
                    "id": "constant",
                    "name": "'Bilinmiyor' ile Doldur",
                    "desc": "Eksik hücreleri sabit bir etiketle doldurur.",
                    "tags": ["Hızlı", "Şeffaf"]
                },
                {
                    "id": "drop",
                    "name": "Satırı Sil",
                    "desc": "Eksik değer içeren satırı tamamen siler.",
                    "tags": ["Hızlı", "Veri Kaybı"]
                },
            ]

        result[col] = {
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "dtype": "numeric" if is_numeric else "categorical",
            "recommendations": recommendations,
        }

    return result


def apply_missing(df: pd.DataFrame, column: str, method: str) -> tuple[pd.DataFrame, str]:
    """
    Seçilen yöntemi uygular, güncellenmiş DataFrame ve açıklama döner.
    """
    df = df.copy()

    if method == "mice":
        # Yalnızca sayısal sütunları seç, MICE modeli sayısal matris bekler
        all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        if column not in all_numeric:
            raise ValueError(f"MICE sadece sayısal sütunlara uygulanabilir. ({column})")
        if df[column].isnull().all():
            raise ValueError(f"'{column}' sütunu tamamen boş olduğu için MICE ile tahmin edilemez. Lütfen basit bir doldurma yöntemi seçin.")

        # Sadece tamamen boş olmayan sayısal sütunları dahil et (sklearn'ün sütun silmesini engellemek için)
        numeric_cols = [c for c in all_numeric if not df[c].isnull().all()]

        missing_mask = df[column].isnull()

        # MICE (Iterative Imputer) ile diğer tüm sayısal değişkenleri kullanarak bu sütunu tahmin et
        imputer = IterativeImputer(estimator=ExtraTreesRegressor(n_estimators=10, random_state=42), random_state=42, max_iter=10)
        imputed_data = imputer.fit_transform(df[numeric_cols])
        col_idx = numeric_cols.index(column)
        predictions = pd.Series(imputed_data[:, col_idx], index=df.index)
        df.loc[missing_mask, column] = predictions.loc[missing_mask]

        detail = (
            f"{column} sütunundaki {int(missing_mask.sum())} eksik değer MICE "
            f"(ExtraTrees) modeliyle tahmin edildi."
        )

    elif method == "knn":
        all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        if column not in all_numeric:
            raise ValueError(f"KNN sadece sayısal sütunlara uygulanabilir. ({column})")
        if df[column].isnull().all():
            raise ValueError(f"'{column}' sütunu tamamen boş olduğu için KNN ile tahmin edilemez. Lütfen basit bir doldurma yöntemi seçin.")

        # Sadece tamamen boş olmayan sayısal sütunları dahil et
        numeric_cols = [c for c in all_numeric if not df[c].isnull().all()]

        imputer = KNNImputer(n_neighbors=5)
        imputed_data = imputer.fit_transform(df[numeric_cols])
        col_idx = numeric_cols.index(column)
        df[column] = imputed_data[:, col_idx]
        detail = f"{column} sütunu KNN Imputer (k=5) ile dolduruldu."

    elif method == "mean":
        imputer = SimpleImputer(strategy="mean")
        df[[column]] = imputer.fit_transform(df[[column]])
        detail = f"{column} sütunu ortalama ({round(df[column].mean(), 2)}) ile dolduruldu."

    elif method == "median":
        imputer = SimpleImputer(strategy="median")
        df[[column]] = imputer.fit_transform(df[[column]])
        detail = f"{column} sütunu medyan ({round(df[column].median(), 2)}) ile dolduruldu."

    elif method == "mode":
        mode_val = df[column].mode()[0]
        df[column] = df[column].fillna(mode_val)
        detail = f"{column} sütunu mod ('{mode_val}') ile dolduruldu."

    elif method == "constant":
        df[column] = df[column].fillna("Bilinmiyor")
        detail = f"{column} sütunu 'Bilinmiyor' sabit değeriyle dolduruldu."

    elif method == "drop":
        before = len(df)
        df = df.dropna(subset=[column])
        dropped = before - len(df)
        detail = f"{column} sütunundaki eksik {dropped} satır silindi."

    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

    return df, detail
