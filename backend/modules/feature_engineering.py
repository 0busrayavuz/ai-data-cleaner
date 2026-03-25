import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder

def analyze_features(df: pd.DataFrame) -> dict:
    """
    Sütunların veri yapısına bakarak otomatik özellik çıkarımı veya veri dönüşümü önerir.
    """
    result = {}

    for col in df.columns:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue
            
        recommendations = []
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        is_datetime = pd.api.types.is_datetime64_any_dtype(df[col])
        is_object = df[col].dtype == object

        # ── 1. Tarih Özellikleri Çıkarma ──
        if is_datetime:
            recommendations.append({
                "id": "extract_date_features",
                "name": "Tarih Özellikleri Üret",
                "desc": "Tarihten yıl, ay, gün ve haftanın günü sütunlarını otomatik türetir.",
                "tags": ["Yapay Zeka", "Özellik Çıkarımı"]
            })
            
        # ── 2. Kategorik Dönüşümler (Encoding) ──
        if is_object:
            unique_count = col_data.nunique()
            if 1 < unique_count <= 15:
                # One-hot encoding için uygun
                recommendations.append({
                    "id": "one_hot_encode",
                    "name": "One-Hot Encoding (OHE)",
                    "desc": f"Bu kategorik sütunu {unique_count} adet ikili (0-1) sütuna ayırır. Makine öğrenmesi algoritmaları için idealdir.",
                    "tags": ["Dönüşüm", "ML Hazırlığı"]
                })
            elif unique_count > 15:
                # Label encoding
                recommendations.append({
                    "id": "label_encode",
                    "name": "Label Encoding",
                    "desc": "Çok fazla benzersiz değer içeren metinleri sayısal ID'lere dönüştürür.",
                    "tags": ["Dönüşüm", "Bellek Dostu"]
                })
                
        # ── 3. Sayısal Dönüşümler (Scaling & Skewness) ──
        if is_numeric:
            skewness = float(col_data.skew())
            if abs(skewness) > 1.0:
                # Highly skewed
                recommendations.append({
                    "id": "log_transform",
                    "name": "Logaritmik Dönüşüm",
                    "desc": f"Veri dağılımı çarpık (skewness={skewness:.2f}). Log dönüşümü ile normal dağılıma yaklaştırılır.",
                    "tags": ["İstatistik", "Normalizasyon"]
                })
                
            # Standardization
            recommendations.append({
                "id": "standard_scale",
                "name": "Standartlaştırma (Z-Score)",
                "desc": "Verileri ortalaması 0, standart sapması 1 olacak şekilde ölçeklendirir.",
                "tags": ["Ölçekleme", "Standart"]
            })
            recommendations.append({
                "id": "minmax_scale",
                "name": "Min-Max Ölçekleme (0-1)",
                "desc": "Verileri 0 ile 1 aralığına sıkıştırır. Sinir ağları için sınırları sabitler.",
                "tags": ["Ölçekleme", "Normalizasyon"]
            })

        if recommendations:
            # Default as skip so we don't forcefully overwrite
            recommendations.insert(0, {
                "id": "skip",
                "name": "Değişiklik Yapma",
                "desc": "Özellik mühendisliği uygulanmaz. Orijinal veri korunur.",
                "tags": ["Varsayılan", "Güvenli"]
            })
            result[col] = {
                "dtype": str(df[col].dtype),
                "recommendations": recommendations,
            }

    return result

def apply_feature_engineering(df: pd.DataFrame, column: str, method: str) -> tuple[pd.DataFrame, str]:
    """
    Seçilen özellik mühendisliği yöntemini uygular.
    """
    df = df.copy()

    if method == "skip":
        detail = f"{column} sütununa özellik mühendisliği uygulanmadı (atlandı)."

    if method == "extract_date_features":
        df[column] = pd.to_datetime(df[column], errors='coerce')
        df[f"{column}_year"] = df[column].dt.year
        df[f"{column}_month"] = df[column].dt.month
        df[f"{column}_day"] = df[column].dt.day
        df[f"{column}_dayofweek"] = df[column].dt.dayofweek
        detail = f"{column} tarih sütunundan yıl, ay, gün ve haftanın günü sütunları otomatik türetildi."

    elif method == "one_hot_encode":
        dummies = pd.get_dummies(df[column], prefix=column, drop_first=False)
        df = pd.concat([df.drop(columns=[column]), dummies], axis=1)
        detail = f"{column} sütununa One-Hot Encoding uygulandı ve {dummies.shape[1]} yeni ikili (0/1) sütun oluşturuldu. Orijinal sütun korundu: Yok."

    elif method == "label_encode":
        le = LabelEncoder()
        mask = df[column].notna()
        df.loc[mask, column] = le.fit_transform(df.loc[mask, column].astype(str))
        detail = f"{column} sütunundaki metin verileri benzersiz sayısal kimliklere (Label Encoding) çevrildi."

    elif method == "log_transform":
        min_val = df[column].min()
        if min_val <= 0:
            shift = abs(min_val) + 1
            df[column] = np.log1p(df[column] + shift)
        else:
            df[column] = np.log1p(df[column])
        detail = f"{column} sütununa veri çarpıklığını (skewness) azaltmak için Logaritmik Dönüşüm uygulandı."

    elif method == "standard_scale":
        scaler = StandardScaler()
        mask = df[column].notna()
        df.loc[mask, column] = scaler.fit_transform(df.loc[mask, [column]])
        detail = f"{column} sütunu Standart Ölçekleyici (Ort:0, Sapma:1) ile ölçeklendirildi."

    elif method == "minmax_scale":
        scaler = MinMaxScaler()
        mask = df[column].notna()
        df.loc[mask, column] = scaler.fit_transform(df.loc[mask, [column]])
        detail = f"{column} sütunu Min-Max Ölçekleyici ile (0-1 arasında) sınırlandırıldı."

    else:
        raise ValueError(f"Bilinmeyen yöntem: {method}")

    return df, detail
