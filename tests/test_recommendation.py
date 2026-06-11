import pandas as pd
from backend.modules.recommendation import generate_recommendations

def test_generate_recommendations():
    df = pd.DataFrame({
        'isim':      ['Ali', 'Ayse', None, 'Mehmet', '  Fatma'],
        'yas':       [25, None, 30, 999, 27],
        'gelir':     ['5000', '8000', None, '4500', '7000'],
        'cinsiyet':  ['Erkek', 'kadın', 'ERKEK', 'Kadın', 'erkek'],
    })

    result = generate_recommendations(df)
    assert result['total'] > 0
    assert result['missing_count'] > 0
    assert result['outlier_count'] > 0
    assert result['format_count'] > 0

    recs = result['recommendations']
    categories = [r['category'] for r in recs]
    assert 'missing' in categories
    assert 'outlier' in categories
    assert 'format' in categories
