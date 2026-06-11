import os
import pandas as pd
from backend.modules.file_reader import read_file, get_basic_profile

def test_file_reader(tmp_path):
    test_path = os.path.join(tmp_path, "test.csv")
    pd.DataFrame({
        'isim': ['Ali', 'Ayse', None, 'Mehmet'],
        'yas': [25, None, 30, 22],
        'gelir': [5000, 8000, None, 4500]
    }).to_csv(test_path, index=False)

    df, meta = read_file(test_path)
    assert meta["row_count"] == 4
    assert meta["col_count"] == 3
    assert "isim" in meta["columns"]

    profile = get_basic_profile(df)
    assert profile["isim"]["missing_count"] == 1
    assert profile["yas"]["missing_count"] == 1

def test_bad_csv_lines(tmp_path):
    # Create a malformed CSV file
    bad_csv_path = os.path.join(tmp_path, "bad.csv")
    with open(bad_csv_path, "w", encoding="utf-8") as f:
        f.write("col1,col2\n")
        f.write("val1,val2\n")
        f.write("val3,val4,val5\n")  # extra column value (bad line)

    import pytest
    with pytest.raises(ValueError, match="geçersiz/bozuk satır"):
        read_file(bad_csv_path)
