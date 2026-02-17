import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.modules.pipeline import run_pipeline

df = pd.DataFrame({
    'isim':     ['Ali', 'Ayse', None, 'Mehmet'],
    'yas':      [25, None, 30, 999],
    'gelir':    [5000, 8000, None, 4500],
    'cinsiyet': ['Erkek', 'kadın', 'ERKEK', 'Kadın'],
})

selections = [
    {"category": "missing", "column": "yas",      "method": "mean"},
    {"category": "missing", "column": "gelir",    "method": "median"},
    {"category": "missing", "column": "isim",     "method": "constant"},
    {"category": "outlier", "column": "yas",      "method": "cap"},
    {"category": "format",  "column": "cinsiyet", "method": "normalize_case"},
]

result = run_pipeline(df, selections)

print("=== PİPELINE SONUCU ===")
print(f"Uygulanan: {result['applied_count']} | Hata: {result['error_count']}")
print(f"Eksik % (önce): %{result['before_missing_pct']} → (sonra): %{result['after_missing_pct']}")

print("\n=== İŞLEM GÜNLÜĞÜ ===")
for log in result['logs']:
    icon = "✅" if log['status'] == 'ok' else "❌"
    print(f"{icon} [{log['timestamp']}] {log['detail']}")

print("\n=== TEMİZLENMİŞ VERİ ===")
print(result['cleaned_df'])

print("\n=== BAŞARILI ===")