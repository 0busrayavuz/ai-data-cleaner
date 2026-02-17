import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.modules.missing_value import analyze_missing, apply_missing

df = pd.DataFrame({
    'isim': ['Ali', 'Ayse', None, 'Mehmet'],
    'yas':  [25, None, 30, 22],
    'gelir':[5000, 8000, None, 4500]
})

print('=== EKSİK DEĞER ANALİZİ ===')
analysis = analyze_missing(df)
for col, info in analysis.items():
    print(f'\n[{col}] - {info["missing_count"]} eksik (%{info["missing_pct"]}) - {info["dtype"]}')
    for rec in info['recommendations']:
        print(f'  → {rec["name"]}')

print('\n=== YÖNTEM UYGULAMA TESTİ ===')
df2, detail = apply_missing(df, 'yas', 'mean')
print(detail)
print(df2)

print('\n=== BAŞARILI ===')