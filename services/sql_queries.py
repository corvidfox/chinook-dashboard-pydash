# services/sql_queries.py

from duckdb import DuckDBPyConnection
from typing import List
from services.logging_utils import log_msg
import pandas as pd

def get_events_shared(conn: DuckDBPyConnection, where_clauses: List[str]) -> pd.DataFrame:
    """
    Fetches event-level invoice data with optional WHERE clauses.
    Equivalent to R's get_events_shared().
    """
    log_msg("[SQL] Running get_events_shared() with active filters")

    # Construct WHERE clause
    where = ""
    if where_clauses:
        where = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT
            i.CustomerId,
            DATE(i.InvoiceDate) AS dt,
            i.InvoiceId
        FROM Invoice i
        JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
        JOIN Track t ON il.TrackId = t.TrackId
        JOIN Album al ON t.AlbumId = al.AlbumId
        JOIN Artist ar ON al.ArtistId = ar.ArtistId
        JOIN Genre g ON t.GenreId = g.GenreId
        {where}
    """

    df = conn.execute(query).fetchdf()

    # Drop duplicates, sort
    df = df.drop_duplicates(subset=["CustomerId", "InvoiceId", "dt"])
    df = df.sort_values(["CustomerId", "dt"])

    return df

def get_invoices_details(conn: DuckDBPyConnection, invoice_ids: list, date_range: list) -> pd.DataFrame:
    """
    Fetch full invoice data for a filtered set of InvoiceIds, bounded by an optional date_range.
    """
    from services.logging_utils import log_msg
    log_msg("[SQL] Running get_invoices_details()")

    if not invoice_ids:
        return pd.DataFrame()  # Empty fallback

    invoice_id_str = ", ".join(str(i) for i in invoice_ids)

    where_clauses = [f"i.InvoiceId IN ({invoice_id_str})"]

    # Add date filter if available
    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        where_clauses.append(f"DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')")

    where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT
            i.InvoiceId,
            i.CustomerId,
            i.InvoiceDate,
            i.BillingCountry,
            i.Total
        FROM Invoice i
        {where_sql}
    """

    df = conn.execute(query).fetchdf()
    return df
