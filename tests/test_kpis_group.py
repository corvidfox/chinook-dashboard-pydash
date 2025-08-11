# tests/test_kpis_group.py

import pytest
import pandas as pd
from services.kpis.group import (
    get_group_kpis_full,
    topn_kpis_slice_topn,
    topn_kpis_generate,
    topn_kpis_format_display,
    query_catalog_sales,
    enrich_catalog_kpis
)

def test_get_group_kpis_full_genre(prepare_full_data_context):
    conn = prepare_full_data_context
    df = get_group_kpis_full(conn, "Genre", ["2009-01-01", "2013-12-31"])
    assert not df.empty
    assert "group_val" in df.columns
    assert "revenue" in df.columns
    assert df["group_val"].nunique() == 24

def test_topn_kpis_slice_topn_basic():
    df = pd.DataFrame({
        "group_val": ["A", "B", "C", "D", "E"],
        "revenue": [100, 200, 150, 50, 300]
    })
    topn = topn_kpis_slice_topn(df, "revenue", n=3)
    assert list(topn["group_val"]) == ["E", "B", "C"]

def test_topn_kpis_generate_basic():
    df = pd.DataFrame({
        "group_val": ["A", "B", "C", "D", "E"],
        "revenue": [100, 200, 150, 50, 300],
        "tracks_sold": [10, 20, 15, 5, 30]
    })
    metrics = [
        {"var_name": "revenue"},
        {"var_name": "tracks_sold"}
    ]
    result = topn_kpis_generate(df, metrics, n=2)
    assert "revenue" in result
    assert "tracks_sold" in result
    assert list(result["revenue"]["group_val"]) == ["E", "B"]
    assert list(result["tracks_sold"]["group_val"]) == ["E", "B"]

def test_group_kpis_genre_full_range(prepare_full_data_context):
    """Test genre-level KPIs for full date range."""
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    df = get_group_kpis_full(conn, "Genre", date_range)

    assert not df.empty
    assert df["group_val"].nunique() == 24
    assert df.loc[df["group_val"] == "Alternative & Punk", "revenue"].values[0] == pytest.approx(241.56)
    assert df.loc[df["group_val"] == "Comedy", "tracks_sold"].values[0] == pytest.approx(9.0)

def test_group_kpis_genre_2010_range(prepare_full_data_context):
    """Test genre-level KPIs for 2010 subset."""
    conn = prepare_full_data_context
    date_range = ["2010-01-01", "2010-12-31"]
    df = get_group_kpis_full(conn, "Genre", date_range)

    assert not df.empty
    assert df["group_val"].nunique() == 24
    assert df.loc[df["group_val"] == "Alternative & Punk", "revenue"].values[0] == pytest.approx(39.60)
    assert df.loc[df["group_val"] == "Comedy", "tracks_sold"].values[0] == pytest.approx(2.0)

def test_group_kpis_artist_full_range(prepare_full_data_context):
    """Test artist-level KPIs for full date range."""
    conn = prepare_full_data_context
    date_range = ["2009-01-01", "2013-12-31"]
    df = get_group_kpis_full(conn, "Artist", date_range)

    assert not df.empty
    assert df["group_val"].nunique() == 165
    assert df.loc[df["group_val"] == "AC/DC", "revenue"].values[0] == pytest.approx(15.84)
    assert df.loc[df["group_val"] == "Zeca Pagodinho", "tracks_sold"].values[0] == pytest.approx(9.0)

def test_group_kpis_artist_2010_range(prepare_full_data_context):
    """Test artist-level KPIs for 2010 subset."""
    conn = prepare_full_data_context
    date_range = ["2010-01-01", "2010-12-31"]
    df = get_group_kpis_full(conn, "Artist", date_range)

    assert not df.empty
    assert df["group_val"].nunique() < 165  # subset
    assert df.loc[df["group_val"] == "AC/DC", "revenue"].values[0] == pytest.approx(3.96)
    assert df.loc[df["group_val"] == "Aerosmith", "tracks_sold"].values[0] == pytest.approx(3.0)

def test_group_kpis_artist_empty_subset(prepare_empty_artist_context):
    """Test artist-level KPIs return empty DataFrame for artist with no invoices."""
    conn = prepare_empty_artist_context
    date_range = ["2009-01-01", "2013-12-31"]
    df = get_group_kpis_full(conn, "Artist", date_range)

    assert df.empty

def test_topn_kpis_format_display_genre(prepare_full_data_context):
    conn = prepare_full_data_context
    df = get_group_kpis_full(conn, "Genre", ["2009-01-01", "2013-12-31"])
    topn = topn_kpis_slice_topn(df, "revenue", n=5)
    formatted = topn_kpis_format_display(conn, topn, "Genre", total_revenue=df["revenue"].sum())
    assert "avg_revenue_per_cust_fmt" in formatted.columns
    assert "group_val_fmt" in formatted.columns
    assert "pct_catalog_sold_fmt" in formatted.columns

def test_query_catalog_sales_artist(prepare_full_data_context):
    conn = prepare_full_data_context
    df = query_catalog_sales(conn, "Artist", ["2009-01-01", "2013-12-31"])
    assert not df.empty
    assert "unique_tracks_sold" in df.columns
    assert "catalog_size" in df.columns
    assert "pct_catalog_sold" in df.columns

def test_enrich_catalog_kpis_artist(prepare_full_data_context):
    conn = prepare_full_data_context
    df = get_group_kpis_full(conn, "Artist", ["2009-01-01", "2013-12-31"])
    topn = topn_kpis_slice_topn(df, "revenue", n=5)
    enriched = enrich_catalog_kpis(conn, topn, "Artist", ["2009-01-01", "2013-12-31"])
    assert "catalog_size" in enriched.columns
    assert "pct_catalog_sold" in enriched.columns
