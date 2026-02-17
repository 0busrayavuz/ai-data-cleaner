import pandas as pd
import os

SUPPORTED_FORMATS = [".csv", ".txt", ".xlsx"]


def read_file(file_path: str) -> tuple[pd.DataFrame, dict]:
    """
    Dosyayı okur, DataFrame ve meta bilgi döner.
    Desteklenen formatlar: CSV, TXT, XLSX
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Desteklenmeyen format: {ext}. Desteklenenler: {SUPPORTED_FORMATS}")

    # Formatına göre oku
    if ext == ".csv":
        df = _read_csv(file_path)
    elif ext == ".txt":
        df = _read_txt(file_path)
    elif ext == ".xlsx":
        df = _read_xlsx(file_path)

    # Meta bilgileri topla
    meta = {
        "filename": os.path.basename(file_path),
        "format": ext.replace(".", "").upper(),
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "file_path": file_path,
    }

    return df, meta


def _read_csv(file_path: str) -> pd.DataFrame:
    # Önce UTF-8, hata verirse latin-1 dene
    for encoding in ["utf-8", "latin-1", "cp1254"]:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Dosya encoding'i okunamadı.")


def _read_txt(file_path: str) -> pd.DataFrame:
    # TXT dosyasında ayırıcıyı otomatik tespit et
    for sep in ["\t", ";", ",", "|"]:
        try:
            df = pd.read_csv(file_path, sep=sep, encoding="utf-8")
            if len(df.columns) > 1:  # Birden fazla sütun varsa doğru ayırıcı
                return df
        except Exception:
            continue
    # Hiçbiri olmazsa tek sütun olarak oku
    return pd.read_csv(file_path, encoding="utf-8")


def _read_xlsx(file_path: str) -> pd.DataFrame:
    return pd.read_excel(file_path, engine="openpyxl")


def get_basic_profile(df: pd.DataFrame) -> dict:
    """
    Veri seti hakkında temel istatistiksel profil çıkarır.
    """
    profile = {}

    for col in df.columns:
        col_info = {
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isnull().sum()),
            "missing_pct": round(df[col].isnull().mean() * 100, 2),
            "unique_count": int(df[col].nunique()),
        }

        # Sayısal sütunlar için ek istatistik
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info.update({
                "mean": round(float(df[col].mean()), 4) if not df[col].isnull().all() else None,
                "median": round(float(df[col].median()), 4) if not df[col].isnull().all() else None,
                "std": round(float(df[col].std()), 4) if not df[col].isnull().all() else None,
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
            })

        profile[col] = col_info

    return profile