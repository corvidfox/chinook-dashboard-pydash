"""
sql_core.py

Reusable SQL queries that support cross-page data features like event stream.
"""

from typing import List
from duckdb import DuckDBPyConnection
import pandas as pd
from services.logging_utils import log_msg

def get_events_shared(conn: DuckDBPyConnection, where_clauses: List[str]) -> pd.DataFrame:
    """
    Fetches event-level invoice metadata with filters.

    Parameters:
        conn (DuckDBPyConnection)
        where_clauses (List[str])

    Returns:
        pd.DataFrame: Columns = ['CustomerId', 'dt', 'InvoiceId']
    """
    log_msg("[SQL] Running get_events_shared()")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

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
        {where_sql}
    """

    df = conn.execute(query).fetchdf()
    return df.drop_duplicates(subset=["CustomerId", "InvoiceId", "dt"]).sort_values(["CustomerId", "dt"])
