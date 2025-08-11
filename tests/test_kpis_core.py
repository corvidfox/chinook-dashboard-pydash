# tests/test_kpis_core.py

import pytest
from services.kpis.core import get_subset_core_kpis

def test_core_kpis_full_range(prepare_full_data_context):
    """Validate core KPIs for full date range."""
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    kpis = get_subset_core_kpis(conn, date_range)

    assert kpis["purchases_num"] == "412"
    assert kpis["cust_num"] == "59"
    assert kpis["cust_num_new"] == "59"
    assert kpis["cust_per_new"] == "100.00%"
    assert kpis["tracks_sold_num"] == "2,240"
    assert kpis["revenue_total"] == 2328.6
    assert kpis["revenue_per_purchase"] == "$5.65"
    assert kpis["genre_num"] == "24"
    assert kpis["artist_num"] == "165"
    assert kpis["country_num"] == "24"

def test_core_kpis_2010_range(prepare_full_data_context):
    """Validate core KPIs for 2010-only range."""
    conn = prepare_full_data_context
    date_range = ["2010-01-01", "2010-12-31"]
    kpis = get_subset_core_kpis(conn, date_range)

    assert kpis["purchases_num"] == "83"
    assert kpis["cust_num"] == "46"
    assert kpis["cust_num_new"] == "13"
    assert kpis["cust_per_new"] == "28.26%"
    assert kpis["tracks_sold_num"] == "455"
    assert kpis["revenue_total"] == 481.45
    assert kpis["revenue_per_purchase"] == "$5.80"
    assert kpis["genre_num"] == "24"
    assert kpis["artist_num"] == "113"
    assert kpis["country_num"] == "20"

def test_core_kpis_empty_artist(prepare_empty_artist_context):
    """Should return empty dict for artist with no invoices."""
    conn = prepare_empty_artist_context
    date_range = ["2009-01-01", "2013-12-31"]
    kpis = get_subset_core_kpis(conn, date_range)

    assert kpis == {}
