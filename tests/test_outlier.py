import pandas as pd
from backend.modules.outlier_detector import analyze_outliers, apply_outlier

def test_analyze_outliers():
    df = pd.DataFrame({
        'yas':   [25, 30, 22, 28, 999, 27, 24, 31, 26, 29, 23, 28],
        'gelir': [5000, 8000, 4500, 7000, 6000, 5500, 999999, 6200, 5800, 7200, 4800, 6500]
    })
    result = analyze_outliers(df)
    assert 'yas' in result
    assert result['yas']['iqr_outlier_count'] == 1
    assert 'gelir' in result
    assert result['gelir']['iqr_outlier_count'] == 1


def test_apply_outlier_cap():
    df = pd.DataFrame({
        'yas':   [25, 30, 22, 28, 999, 27, 24, 31, 26, 29, 23, 28],
        'gelir': [5000, 8000, 4500, 7000, 6000, 5500, 999999, 6200, 5800, 7200, 4800, 6500]
    })
    df2, detail, count = apply_outlier(df, 'yas', 'cap')
    assert df2['yas'].max() < 999
    assert count == 1


def test_analyze_outliers_disjoint_index():
    df = pd.DataFrame({
        'yas':   [25, 30, 22, 28, 999, 27, 24, 31, 26, 29, 23, 28],
        'gelir': [5000, 8000, 4500, 7000, 6000, 5500, 999999, 6200, 5800, 7200, 4800, 6500]
    })
    df = df.drop(index=[1, 3, 5, 7])
    result = analyze_outliers(df)
    assert 'yas' in result
    assert result['yas']['iqr_outlier_count'] == 1
    assert result['gelir']['iqr_outlier_count'] == 1
