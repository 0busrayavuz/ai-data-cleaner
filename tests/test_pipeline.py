import pandas as pd
from backend.modules.pipeline import run_pipeline

def test_run_pipeline():
    df = pd.DataFrame({
        'isim':     ['Ali', 'Ayse', None, 'Mehmet', 'Can', 'Ece', 'Elif', 'Omer', 'Asli', 'Hasan'],
        'yas':      [25, None, 30, 999, 28, 22, 27, 24, 26, 29],
        'gelir':    [5000, 8000, None, 4500, 6000, 5500, 7000, 4800, 5200, 6300],
        'cinsiyet': ['Erkek', 'kadın', 'ERKEK', 'Kadın', 'erkek', 'kadin', 'ERKEK', 'KADIN', 'Erkek', 'KADIN'],
    })

    selections = [
        {"category": "missing", "column": "yas",      "method": "mean"},
        {"category": "missing", "column": "gelir",    "method": "median"},
        {"category": "missing", "column": "isim",     "method": "constant"},
        {"category": "outlier", "column": "yas",      "method": "cap"},
        {"category": "format",  "column": "cinsiyet", "method": "normalize_case"},
    ]

    result = run_pipeline(df, selections)
    assert result['error_count'] == 0
    assert result['applied_count'] == 5
    assert result['after_missing_pct'] == 0.0

    cleaned_df = result['cleaned_df']
    assert cleaned_df['isim'].iloc[2] == 'Bilinmiyor'
    assert cleaned_df['cinsiyet'].iloc[2] == 'erkek'
    assert cleaned_df['yas'].iloc[3] < 999
