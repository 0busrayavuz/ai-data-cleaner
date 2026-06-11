import pandas as pd
import pytest
from backend.modules.missing_value import analyze_missing, apply_missing

def test_analyze_missing():
    df = pd.DataFrame({
        'isim': ['Ali', 'Ayse', None, 'Mehmet'],
        'yas':  [25, None, 30, 22],
        'gelir':[5000, 8000, None, 4500]
    })
    analysis = analyze_missing(df)
    assert 'isim' in analysis
    assert analysis['isim']['missing_count'] == 1
    assert analysis['isim']['dtype'] == 'categorical'

    assert 'yas' in analysis
    assert analysis['yas']['missing_count'] == 1
    assert analysis['yas']['dtype'] == 'numeric'

def test_apply_missing():
    df = pd.DataFrame({
        'isim': ['Ali', 'Ayse', None, 'Mehmet'],
        'yas':  [25, None, 30, 22],
        'gelir':[5000, 8000, None, 4500]
    })
    df2, detail = apply_missing(df, 'yas', 'mean')
    assert df2['yas'].isnull().sum() == 0
    assert round(df2['yas'].iloc[1], 2) == 25.67


@pytest.mark.parametrize(
    ("target", "predictor"),
    [
        (
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, None],
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
        ),
        (
            [1.0, 1.0, 1.0, 2.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, None],
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0],
        ),
        (
            [9.0, 10.0, 11.0, 9.5, 10.5, 99.0, 100.0, 101.0, 99.5, 100.5, None],
            [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        ),
    ],
    ids=["balanced", "right_skewed", "bimodal"],
)
def test_mice_fills_only_missing_cells_across_distributions(target, predictor):
    df = pd.DataFrame({"target": target, "predictor": predictor})
    observed_mask = df["target"].notna()
    original_observed = df.loc[observed_mask, "target"].copy()

    cleaned, detail = apply_missing(df, "target", "mice")

    assert cleaned["target"].isna().sum() == 0
    assert pd.notna(cleaned.loc[~observed_mask, "target"]).all()
    pd.testing.assert_series_equal(
        cleaned.loc[observed_mask, "target"],
        original_observed,
    )
    assert "1 eksik değer" in detail
