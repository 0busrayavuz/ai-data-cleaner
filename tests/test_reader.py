import pandas as pd
from backend.modules.file_reader import read_file, get_basic_profile

# Test CSV oluştur
test_path = 'uploads/test.csv'
pd.DataFrame({
    'isim': ['Ali', 'Ayse', None, 'Mehmet'],
    'yas': [25, None, 30, 22],
    'gelir': [5000, 8000, None, 4500]
}).to_csv(test_path, index=False)

df, meta = read_file(test_path)
print('=== META BİLGİ ===')
print(f'Dosya: {meta["filename"]}')
print(f'Format: {meta["format"]}')
print(f'Satır: {meta["row_count"]}, Sütun: {meta["col_count"]}')
print(f'Sütunlar: {meta["columns"]}')

print()
print('=== EKSİK DEĞER PROFİLİ ===')
profile = get_basic_profile(df)
for col, info in profile.items():
    print(f'{col}: eksik={info["missing_count"]} (%{info["missing_pct"]})')

print()
print('=== BAŞARILI ===')