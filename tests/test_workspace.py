import pandas as pd

from backend.main import _build_comparison, _profile_dataframe


def test_profile_dataframe_supports_mixed_columns():
    df = pd.DataFrame({
        "amount": [10.0, 20.0, None, 40.0],
        "city": ["Ankara", "İzmir", "Ankara", None],
    })

    profile = _profile_dataframe(df)
    by_name = {column["name"]: column for column in profile["columns"]}

    assert profile["row_count"] == 4
    assert profile["col_count"] == 2
    assert profile["missing_cells"] == 2
    assert by_name["amount"]["kind"] == "numeric"
    assert by_name["amount"]["missing_count"] == 1
    assert by_name["amount"]["distribution"]
    assert by_name["city"]["kind"] == "categorical"
    assert by_name["city"]["top_values"][0] == {"label": "Ankara", "count": 2}


def test_comparison_reports_changed_cells_when_rows_align():
    before = pd.DataFrame({
        "amount": [10.0, None, 30.0],
        "city": ["A", "B", "C"],
    })
    after = pd.DataFrame({
        "amount": [10.0, 20.0, 30.0],
        "city": ["A", "B", "C"],
    })

    comparison = _build_comparison(before, after)

    assert comparison["rows_aligned"] is True
    assert comparison["total_changed_cells"] == 1
    assert comparison["health"]["before"]["missing"] == 1
    assert comparison["health"]["after"]["missing"] == 0
    assert comparison["changed_samples"][0]["column"] == "amount"


def test_comparison_avoids_false_cell_alignment_after_row_deletion():
    before = pd.DataFrame({"value": [1, 2, 3]})
    after = pd.DataFrame({"value": [1, 3]})

    comparison = _build_comparison(before, after)

    assert comparison["rows_aligned"] is False
    assert comparison["total_changed_cells"] is None
    assert comparison["columns"][0]["changed_cells"] is None
