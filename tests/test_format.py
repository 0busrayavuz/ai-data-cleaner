import pandas as pd
import numpy as np
from backend.modules.format_checker import analyze_format, apply_format

def test_analyze_format():
    df = pd.DataFrame({
        'gelir':      ['5000', '8000', '4500', '7000'],
        'kayit_tar':  ['2024-01-15', '2023-06-20', '2024-03-10', '2022-11-05'],
        'isim':       ['  Ali', 'Ayse  ', ' Mehmet', 'Fatma'],
        'cinsiyet':   ['Erkek', 'Kadın', 'erkek', 'KADIN'],
    })
    result = analyze_format(df)
    assert 'gelir' in result
    assert 'kayit_tar' in result
    assert 'isim' in result
    assert 'cinsiyet' in result


def test_apply_format_to_numeric():
    df = pd.DataFrame({
        'gelir':      ['5000', '8000', '4500', '7000']
    })
    df2, detail, count = apply_format(df, 'gelir', 'to_numeric')
    assert pd.api.types.is_numeric_dtype(df2['gelir'])
    assert count == 4


def test_strip_whitespace_preserves_nan():
    df = pd.DataFrame({
        'isim': ['  Ali', None, 'Fatma  ']
    })
    df2, detail, count = apply_format(df, 'isim', 'strip_whitespace')
    assert df2['isim'].iloc[0] == 'Ali'
    assert pd.isna(df2['isim'].iloc[1]) or df2['isim'].iloc[1] is None
    assert df2['isim'].iloc[1] != 'nan'
    assert df2['isim'].iloc[2] == 'Fatma'
    assert count == 2
