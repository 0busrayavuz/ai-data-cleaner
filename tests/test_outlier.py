import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from backend.modules.outlier_detector import analyze_outliers, apply_outlier

df = pd.DataFrame({
    'yas':   [25, 30, 22, 28, 999, 27, 24, 31, 26, 29, 23, 28],
    'gelir': [5000, 8000, 4500, 7000, 6000, 5500, 999999, 6200, 5800, 7200, 4800, 6500]
})

print('=== AYKIRI DEĞER ANALİZİ ===')
result = analyze_outliers(df)
for col, info in result.items():
    print(f'\n[{col}]')
    print(f'  IQR aykırı: {info["iqr_outlier_count"]}')
    print(f'  IsolationForest aykırı: {info["iso_outlier_count"]}')
    print(f'  LOF aykırı: {info["lof_outlier_count"]}')
    print(f'  Sınırlar: {info["iqr_bounds"]}')

print('\n=== YÖNTEM UYGULAMA TESTİ ===')
df2, detail = apply_outlier(df, 'yas', 'cap')
print(detail)
print(df2['yas'].tolist())

print('\n=== BAŞARILI ===')