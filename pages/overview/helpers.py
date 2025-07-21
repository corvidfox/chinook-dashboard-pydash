"""
helpers.py

Overview tab utilities for filtering, data orchestration, and page-specific queries.
Includes:
- get_filtered_data(): end-to-end data pipeline for overview filters
- get_invoices_details(): overview-specific SQL for invoice-level results
- get_genre_catalog(): review the genre_catalog temp table from DuckDB
- get_artist_catalog(): review the artist_catalog temp table from DuckDB
"""

import pandas as pd
from duckdb import DuckDBPyConnection
from services.db import get_connection
from services.logging_utils import log_msg
from services.sql_filters import apply_date_filter

def get_invoices_details(conn: DuckDBPyConnection, date_range: list) -> pd.DataFrame:
    """
    Returns full invoice-level data scoped to filtered_invoices + date range.

    Parameters:
        conn (DuckDBPyConnection): Active DuckDB connection
        date_range (List[str]): ISO dates ["YYYY-MM-DD", "YYYY-MM-DD"]

    Returns:
        pd.DataFrame: Invoice metadata with totals
    """
    log_msg(f"[PAGE-OVV-SQL] Running get_invoices_details for range: {date_range}")

    join_clause = apply_date_filter(date_range)

    query = f"""
        SELECT
            i.InvoiceId,
            i.CustomerId,
            i.InvoiceDate,
            i.BillingCountry,
            i.Total
        FROM filtered_invoices e
        {join_clause}
    """

    return conn.execute(query).fetchdf()


def get_filtered_data(date_range: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Pulls filtered event and invoice data from DuckDB, using current temp table.

    Parameters:
        date_range (List[str]): ISO dates ["YYYY-MM-DD", "YYYY-MM-DD"]

    Returns:
        tuple:
            pd.DataFrame → event-level stream (from filtered_invoices)
            pd.DataFrame → invoice-level summary
    """
    conn = get_connection()

    log_msg("[PAGE-OVV-SQL] Reading filtered_invoices temp table")
    try:
        events_df = conn.execute("SELECT * FROM filtered_invoices").fetchdf()
    except Exception:
        log_msg("[PAGE-OVV-SQL] filtered_invoices temp table not found", level="warning")
        return pd.DataFrame(), pd.DataFrame()

    invoices_df = get_invoices_details(conn, date_range)

    log_msg(f"     [PAGE-OVV-SQL] Loaded {len(events_df)} filtered events, {len(invoices_df)} invoices")

    return events_df, invoices_df

def get_genre_catalog() -> pd.DataFrame:
    """
    Reads the genre_catalog temp table from DuckDB.

    Returns:
        pd.DataFrame: Columns = ['genre', 'num_tracks']
    """
    conn = get_connection()
    log_msg("[PAGE-OVV-SQL] Reading genre_catalog temp table.")
    try:
        return conn.execute("SELECT * FROM genre_catalog").fetchdf()
    except Exception:
        log_msg("     [PAGE-OVV-SQL] genre_catalog temp table not found", level="warning")
        return pd.DataFrame()


def get_artist_catalog() -> pd.DataFrame:
    """
    Reads the artist_catalog temp table from DuckDB.

    Returns:
        pd.DataFrame: Columns = ['artist', 'num_tracks']
    """
    conn = get_connection()
    log_msg("[PAGE-OVV-SQL] Reading artist_catalog temp table")
    try:
        return conn.execute("SELECT * FROM artist_catalog").fetchdf()
    except Exception:
        log_msg("     [PAGE-OVV-SQL] artist_catalog temp table not found", level="warning")
        return pd.DataFrame()
