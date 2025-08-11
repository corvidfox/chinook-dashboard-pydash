# tests/test_kpis_shared.py

import pytest
import pandas as pd
from services.kpis.shared import get_shared_kpis, make_serializable
from services.kpis.retention import get_retention_cohort_data


def test_get_shared_kpis_full_context(prepare_full_data_context):
    """
    Test full KPI aggregation with valid invoice data and retention cohort.
    """
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    cohort_df = get_retention_cohort_data(conn, date_range)
    metrics = [{"var_name": "revenue"}, {"var_name": "num_purchases"}]

    result = get_shared_kpis(conn, metrics, date_range, cohort_df, top_n=3, offsets=[3, 6, 9])

    assert isinstance(result, dict)
    assert "metadata_kpis" in result
    assert "topn" in result
    assert "retention_kpis" in result

    for group_key in ["topn_genre", "topn_artist", "topn_country"]:
        assert group_key in result["topn"]
        assert "num_vals" in result["topn"][group_key]


def test_get_shared_kpis_empty_context(prepare_empty_artist_context):
    """
    Test KPI aggregation with empty invoice data — should return empty dict.
    """
    conn = prepare_empty_artist_context
    date_range = ["2009-01-01", "2013-12-31"]
    cohort_df = pd.DataFrame(columns=[
        "cohort_month", "month_offset", "num_active_customers",
        "cohort_size", "retention_pct"
    ])
    metrics = [{"var_name": "revenue"}]

    result = get_shared_kpis(conn, metrics, date_range, cohort_df)

    assert result == {}


def test_get_shared_kpis_missing_var_name_key(prepare_full_data_context):
    """
    Test error handling when metrics list is malformed (missing 'var_name').
    """
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    cohort_df = get_retention_cohort_data(conn, date_range)
    metrics = [{"wrong_key": "revenue_total"}]  # malformed

    with pytest.raises(KeyError):
        get_shared_kpis(conn, metrics, date_range, cohort_df)


def test_make_serializable_nested():
    """
    Test recursive serialization of nested objects including DataFrames.
    """
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    nested = {
        "df": df,
        "list": [df, {"key": df}],
        "val": 42
    }

    result = make_serializable(nested)

    assert isinstance(result, dict)
    assert isinstance(result["df"], list)
    assert isinstance(result["list"][0], list)
    assert isinstance(result["list"][1]["key"], list)
    assert result["val"] == 42
