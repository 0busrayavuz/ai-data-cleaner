import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.modules.format_checker import analyze_format, apply_format

df = pd.DataFrame({
    'gelir':      ['5000', '8000', '4500', '7000'],
    'kayit_tar':  ['2024-01-15', '2023-06-20', '2024-03-10', '2022-11-05'],
    'isim':       ['  Ali', 'Ayse  ', ' Mehmet', 'Fatma'],
    'cinsiyet':   ['Erkek', 'Kadın', 'erkek', 'KADIN'],
})

print('=== FORMAT ANALİZİ ===')
result = analyze_format(df)
for col, info in result.items():
    print(f'\n[{col}] - {info["dtype"]}')
    for issue in info['issues']:
        print(f'  ⚠ {issue["desc"]}')
    for rec in info['recommendations']:
        print(f'  → {rec["name"]}')

print('\n=== YÖNTEM UYGULAMA TESTİ ===')
df2, detail = apply_format(df, 'gelir', 'to_numeric')
print(detail)
print(df2.dtypes)

print('\n=== BAŞARILI ===')