# tests/test_metadata.py

import pytest
import time
from unittest.mock import mock_open
import json
from services import metadata

def test_get_filter_metadata_values():
    """Test that get_filter_metadata returns expected counts and date range."""
    meta = metadata.get_filter_metadata()

    assert isinstance(meta, dict)
    assert len(meta["genres"]) == 25
    assert len(meta["countries"]) == 24
    assert len(meta["artists"]) == 275
    assert meta["date_range"] == ("2009-01-01", "2013-12-22")

def test_get_static_summary_values():
    """Test that get_static_summary returns expected KPIs."""
    df = metadata.get_static_summary()

    assert not df.empty
    assert set(df.columns) == {"Metric", "Value"}

    expected = {
        "Total Revenue (USD$)": "$2,328.60",
        "Number of Customers": "59",
        "Number of Purchases": "412",
        "Tracks Sold": "2,240",
        "Number of Genres": "25",
        "Number of Countries": "24",
        "Number of Artists": "275",
        "Date Range": "Jan 2009 – Dec 2013"
    }

    for metric, value in expected.items():
        row = df[df["Metric"] == metric]
        assert not row.empty
        assert row.iloc[0]["Value"] == value

def test_catalog_table_creation_and_check(duckdb_conn):
    """Test creation and validation of catalog temp tables."""
    metadata.create_catalog_tables(duckdb_conn)
    assert metadata.check_catalog_tables(duckdb_conn) is True

def test_catalog_table_missing_check(duckdb_conn):
    """Test check_catalog_tables returns False when tables are missing."""
    # Drop tables if they exist
    duckdb_conn.execute("DROP TABLE IF EXISTS genre_catalog")
    duckdb_conn.execute("DROP TABLE IF EXISTS artist_catalog")
    assert metadata.check_catalog_tables(duckdb_conn) is False

def test_get_last_commit_date_mock(monkeypatch):
    """Mock GitHub cache file and test commit date retrieval."""
    from services import metadata

    # Simulate cache content
    fake_cache = {
        "timestamp": str(time.time()),
        "last_updated": "Jul 20, 2025"
    }
    fake_json = json.dumps(fake_cache)

    # Patch os.path.exists to simulate cache file presence
    monkeypatch.setattr("os.path.exists", lambda path: True)

    # Patch built-in open to return fake JSON
    m = mock_open(read_data=fake_json)
    monkeypatch.setattr("builtins.open", m)

    result = metadata.get_last_commit_date()
    assert result == "Jul 20, 2025"

def test_get_last_commit_date_expired_cache(monkeypatch):
    """Test that expired cache still returns last_updated value."""
    from services import metadata

    old_timestamp = str(time.time() - 999999)  # way older than 1 day
    fake_cache = {
        "timestamp": old_timestamp,
        "last_updated": "Aug 10, 2025"
    }
    fake_json = json.dumps(fake_cache)

    monkeypatch.setattr("os.path.exists", lambda path: True)
    m = mock_open(read_data=fake_json)
    monkeypatch.setattr("builtins.open", m)

    result = metadata.get_last_commit_date()
    assert result == "Unavailable" 

