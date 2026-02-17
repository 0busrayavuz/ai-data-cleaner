import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.modules.recommendation import generate_recommendations

df = pd.DataFrame({
    'isim':      ['Ali', 'Ayse', None, 'Mehmet', '  Fatma'],
    'yas':       [25, None, 30, 999, 27],
    'gelir':     ['5000', '8000', None, '4500', '7000'],
    'cinsiyet':  ['Erkek', 'kadın', 'ERKEK', 'Kadın', 'erkek'],
})

result = generate_recommendations(df)

print(f"=== TOPLAM {result['total']} ÖNERİ ===")
print(f"Eksik: {result['missing_count']} | Aykırı: {result['outlier_count']} | Format: {result['format_count']}")
print()

for rec in result['recommendations']:
    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec['severity'], "⚪")
    print(f"{severity_icon} [{rec['category'].upper()}] {rec['summary']}")
    for opt in rec['options']:
        print(f"     → {opt['name']}")
    print()

print("=== BAŞARILI ===")