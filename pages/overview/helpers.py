"""
helpers.py

Overview tab utilities for filtering, data orchestration, and page-specific queries.
Includes:
- get_filtered_data(): end-to-end data pipeline for overview filters
- get_invoices_details(): overview-specific SQL for invoice-level results
"""

import pandas as pd
from duckdb import DuckDBPyConnection
from services.db import get_connection
from services.sql_filters import form_where_clause
from services.sql_core import get_events_shared
from services.logging_utils import log_msg


def get_invoices_details(conn: DuckDBPyConnection, invoice_ids: list, date_range: list) -> pd.DataFrame:
    """
    Returns full invoice-level data scoped to selected IDs + date range.

    Parameters:
        conn (DuckDBPyConnection): Active DuckDB connection
        invoice_ids (List[int]): Invoice ID filter list
        date_range (List[str]): ISO dates ["YYYY-MM-DD", "YYYY-MM-DD"]

    Returns:
        pd.DataFrame: Invoice metadata with totals
    """
    log_msg("[SQL] Running get_invoices_details()")

    if not invoice_ids:
        return pd.DataFrame()

    invoice_str = ", ".join(str(i) for i in invoice_ids)
    clauses = [f"i.InvoiceId IN ({invoice_str})"]

    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        clauses.append(f"DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')")

    query = f"""
        SELECT
            i.InvoiceId,
            i.CustomerId,
            i.InvoiceDate,
            i.BillingCountry,
            i.Total
        FROM Invoice i
        WHERE {' AND '.join(clauses)}
    """

    return conn.execute(query).fetchdf()


def get_filtered_data(filters: dict):
    """
    Applies dashboard filters and returns matching event + invoice results.

    Parameters:
        filters (dict): {
            'date': List[str],
            'country': List[str],
            'genre': List[str],
            'artist': List[str],
            'metric': str
        }

    Returns:
        tuple:
            pd.DataFrame → event-level stream
            pd.DataFrame → invoice-level summary
            List[str]    → SQL WHERE clauses used
    """
    conn = get_connection()

    where_clauses = form_where_clause(
        country=filters.get("country"),
        genre=filters.get("genre"),
        artist=filters.get("artist")
    )

    event_df = get_events_shared(conn, where_clauses)
    invoice_ids = event_df["InvoiceId"].unique().tolist()

    invoice_df = get_invoices_details(conn, invoice_ids, filters.get("date"))

    return event_df, invoice_df, where_clauses
