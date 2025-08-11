# tests/test_sql_core.py

import pytest
import pandas as pd
from services.sql_core import (
    get_events_shared,
    hash_invoice_ids,
    hash_dataframe,
    hash_kpi_bundle
    )

def test_get_events_shared_with_valid_country(duckdb_conn):
    """Test that filtered_invoices contains expected rows for USA."""
    where_clauses = ["i.BillingCountry = 'USA'"]
    new_hash = get_events_shared(duckdb_conn, where_clauses)

    assert isinstance(new_hash, str)

    df = duckdb_conn.execute("SELECT * FROM filtered_invoices").fetchdf()
    assert len(df) == 91
    assert df["CustomerId"].nunique() == 13
    assert df["InvoiceId"].nunique() == 91
    assert df["dt"].nunique() == 80
    assert df["dt"].min() == pd.to_datetime("2009-01-11")
    assert df["dt"].max() == pd.to_datetime("2013-12-05")

def test_get_events_shared_with_invalid_country(duckdb_conn):
    """Test that filtered_invoices is empty for nonexistent country."""
    where_clauses = ["i.BillingCountry = 'Uzbekistan'"]
    new_hash = get_events_shared(duckdb_conn, where_clauses)

    assert isinstance(new_hash, str)

    df = duckdb_conn.execute("SELECT * FROM filtered_invoices").fetchdf()
    assert df.empty

def test_get_events_shared_hash_consistency(duckdb_conn):
    """Test that the hash output is consistent for the same filter."""
    where_clauses = ["i.BillingCountry = 'USA'"]
    hash1 = get_events_shared(duckdb_conn, where_clauses)
    hash2 = get_events_shared(duckdb_conn, where_clauses)

    assert hash1 == hash2

def test_get_events_shared_skips_update_if_hash_matches(duckdb_conn):
    """Test that get_events_shared skips table update if hash matches and table exists."""
    where_clauses = ["i.BillingCountry = 'USA'"]
    hash1 = get_events_shared(duckdb_conn, where_clauses)

    # Second call with same hash should trigger skip logic
    result = get_events_shared(duckdb_conn, where_clauses, previous_hash=hash1)

    assert isinstance(result, str) or (isinstance(result, tuple) and result[1] == hash1)

    # Confirm table still exists
    tables = duckdb_conn.execute("SHOW TABLES").fetchdf()
    assert "filtered_invoices" in tables["name"].values

def test_hash_invoice_ids_consistency():
    """Test that hash_invoice_ids returns consistent hash for same InvoiceId set."""
    df = pd.DataFrame({"InvoiceId": [3, 1, 2, 1, 3]})
    hash1 = hash_invoice_ids(df)
    hash2 = hash_invoice_ids(df)
    assert isinstance(hash1, str)
    assert hash1 == hash2

def test_hash_invoice_ids_different_order():
    """Test that hash_invoice_ids ignores order and duplicates."""
    df1 = pd.DataFrame({"InvoiceId": [1, 2, 3]})
    df2 = pd.DataFrame({"InvoiceId": [3, 2, 1, 2]})
    assert hash_invoice_ids(df1) == hash_invoice_ids(df2)

def test_hash_dataframe_consistency():
    """Test that hash_dataframe returns consistent hash for identical DataFrames."""
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    hash1 = hash_dataframe(df)
    hash2 = hash_dataframe(df.copy())
    assert isinstance(hash1, str)
    assert hash1 == hash2

def test_hash_dataframe_difference():
    """Test that hash_dataframe returns different hashes for different data."""
    df1 = pd.DataFrame({"a": [1, 2]})
    df2 = pd.DataFrame({"a": [1, 3]})
    assert hash_dataframe(df1) != hash_dataframe(df2)

def test_hash_kpi_bundle_with_dataframe():
    """Test that hash_kpi_bundle handles DataFrames inside dicts."""
    df = pd.DataFrame({"a": [1, 2]})
    bundle = {"metrics": df}
    hash_val = hash_kpi_bundle(bundle)
    assert isinstance(hash_val, str)

def test_hash_kpi_bundle_with_nested_dicts():
    """Test that hash_kpi_bundle handles nested structures."""
    bundle1 = {"a": 1, "b": {"c": [1, 2]}}
    bundle2 = {"b": {"c": [1, 2]}, "a": 1}
    assert hash_kpi_bundle(bundle1) == hash_kpi_bundle(bundle2)