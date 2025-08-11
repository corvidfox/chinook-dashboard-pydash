# tests/test_kpis_retention.py

import pytest
import pandas as pd
from services.kpis.retention import get_retention_cohort_data

def test_retention_cohort_full_range(prepare_full_data_context):
    """Test full-range cohort metrics match expected structure and values."""
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    df = get_retention_cohort_data(conn, date_range)

    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 304
    assert list(df.columns) == [
        "cohort_month", "month_offset", "num_active_customers",
        "cohort_size", "retention_pct"
    ]

    # First cohort: Jan 2009, offset 1
    first = df[(df["cohort_month"] == "2009-01-01") & (df["month_offset"] == 1)]
    assert first["num_active_customers"].values[0] == 1
    assert first["cohort_size"].values[0] == 6
    assert first["retention_pct"].values[0] == pytest.approx(0.1667, rel=1e-4)

    # Last cohort: Jul 2010, offset 41
    last = df[(df["cohort_month"] == "2010-07-01") & (df["month_offset"] == 41)]
    assert last["num_active_customers"].values[0] == 1
    assert last["cohort_size"].values[0] == 1
    assert last["retention_pct"].values[0] == pytest.approx(1.0)

def test_retention_cohort_2010_only(prepare_full_data_context):
    """Test 2010-only cohort metrics match expected structure and values."""
    conn = prepare_full_data_context
    date_range = ["2010-01-01", "2010-12-31"]
    df = get_retention_cohort_data(conn, date_range)

    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 65
    assert list(df.columns) == [
        "cohort_month", "month_offset", "num_active_customers",
        "cohort_size", "retention_pct"
    ]

    # First row: cohort Jan 2009, offset 18
    first = df.iloc[0]
    assert str(first["cohort_month"])[:10] == "2009-01-01"
    assert first["month_offset"] == 18
    assert first["num_active_customers"] == 1
    assert first["cohort_size"] == 6
    assert first["retention_pct"] == pytest.approx(0.1667, rel=1e-4)

    # Last row: cohort Jul 2010, offset 3
    last = df.iloc[-1]
    assert str(last["cohort_month"])[:10] == "2010-07-01"
    assert last["month_offset"] == 3
    assert last["num_active_customers"] == 1
    assert last["cohort_size"] == 1
    assert last["retention_pct"] == pytest.approx(1.0)

import pytest
from services.kpis.retention import get_retention_cohort_data, get_retention_kpis

def test_retention_kpis_full_range(prepare_full_data_context):
    """Test full-range retention KPIs match expected values."""
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    cohort_df = get_retention_cohort_data(conn, date_range)
    result = get_retention_kpis(conn, date_range, cohort_df)

    assert result["num_cust"] == "59"
    assert result["num_new"] == "59"
    assert result["pct_new"] == "100.00%"
    assert result["ret_n_any"] == "59"
    assert result["ret_rate_any"] == "100.00%"
    assert result["ret_n_return"] == "0"
    assert result["ret_rate_return"] == "NA"
    assert result["ret_n_conv"] == "59"
    assert result["ret_rate_conv"] == "100.00%"
    assert result["ret_n_window"] == "59"
    assert result["ret_rate_window"] == "100.00%"
    assert result["avg_life_mo_tot"] == "46.03"
    assert result["avg_life_mo_win"] == "46.03"
    assert result["med_gap_life"] == "94.00"
    assert result["med_gap_window"] == "94.00"
    assert result["med_gap_winback"] == "NA"
    assert result["med_gap_ret"] == "NA"
    assert result["avg_gap_life"] == "234.61"
    assert result["avg_gap_window"] == "234.61"
    assert result["avg_gap_bound"] == "234.61"
    assert result["top_cohort_month_3"] == "Jul 2010"
    assert result["top_cohort_retention_3"] == "100.00%"
    assert result["top_cohort_month_6"] == "Jul 2010"
    assert result["top_cohort_retention_6"] == "100.00%"
    assert result["top_cohort_month_9"] == "Sep 2009"
    assert result["top_cohort_retention_9"] == "50.00%"

def test_retention_kpis_2010_only(prepare_full_data_context):
    """Test 2010-only retention KPIs match expected values."""
    conn = prepare_full_data_context
    date_range = ["2010-01-01", "2010-12-31"]
    cohort_df = get_retention_cohort_data(conn, date_range)
    result = get_retention_kpis(conn, date_range, cohort_df)

    assert result["num_cust"] == "46"
    assert result["num_new"] == "13"
    assert result["pct_new"] == "28.26%"
    assert result["ret_n_any"] == "46"
    assert result["ret_rate_any"] == "100.00%"
    assert result["ret_n_return"] == "33"
    assert result["ret_rate_return"] == "100.00%"
    assert result["ret_n_conv"] == "13"
    assert result["ret_rate_conv"] == "100.00%"
    assert result["ret_n_window"] == "27"
    assert result["ret_rate_window"] == "58.70%"
    assert result["avg_life_mo_tot"] == "44.28"
    assert result["avg_life_mo_win"] == "10.22"
    assert result["med_gap_life"] == "94.00"
    assert result["med_gap_window"] == "94.00"
    assert result["med_gap_winback"] == "243.00"
    assert result["med_gap_ret"] == "391.50"
    assert result["avg_gap_life"] == "225.97"
    assert result["avg_gap_window"] == "107.17"
    assert result["avg_gap_bound"] == "285.14"
    assert result["top_cohort_month_3"] == "Jul 2010"
    assert result["top_cohort_retention_3"] == "100.00%"
    assert result["top_cohort_month_6"] == "Sep 2009"
    assert result["top_cohort_retention_6"] == "50.00%"
    assert result["top_cohort_month_9"] == "Sep 2009"
    assert result["top_cohort_retention_9"] == "50.00%"

def test_retention_kpis_empty_context(prepare_empty_artist_context):
    """Test retention KPIs return NA or zero values for empty dataset."""
    conn = prepare_empty_artist_context
    date_range = ["2009-01-01", "2013-12-31"]
    cohort_df = get_retention_cohort_data(conn, date_range)
    result = get_retention_kpis(conn, date_range, cohort_df)

    assert result == {}
