
import pandas as pd

from services.cache_config import cache
from services.logging_utils import log_msg
from services.db import get_connection

from typing import List, Tuple
from duckdb import DuckDBPyConnection

def get_ts_monthly_summary(conn: DuckDBPyConnection, date_range: List[str]) -> pd.DataFrame:
    """
    Queries the filtered_invoices temp table in DuckDB and returns monthly KPIs.

    Parameters:
        conn (duckdb.DuckDBPyConnection): Active DuckDB connection.
        date_range (List[str]): List of two 'YYYY-MM-DD' strings defining date bounds.

    Returns:
        pd.DataFrame: Monthly summary of purchases, customers, revenue, etc.
    """
    assert isinstance(date_range, list) and len(date_range) == 2, \
        "`date_range` must be a list of two YYYY-MM-DD strings"

    log_msg("[SQL] get_ts_monthly_summary(): querying pre-aggregated KPIs.")

    query = f"""
        WITH first_invoices AS (
            SELECT 
                CustomerId,
                MIN(dt) AS first_invoice_date
            FROM filtered_invoices
            GROUP BY CustomerId
        ),
        invoice_expanded AS (
            SELECT 
                fi.CustomerId,
                fi.InvoiceId,
                fi.dt AS invoice_date,
                STRFTIME(fi.dt, '%Y-%m') AS month,
                i.BillingCountry,
                i.BillingState,
                il.Quantity,
                il.UnitPrice,
                CASE 
                    WHEN STRFTIME(fi.dt, '%Y-%m') = STRFTIME(fi2.first_invoice_date, '%Y-%m') THEN 1
                    ELSE 0
                END AS first_time_flag
            FROM filtered_invoices fi
            JOIN Invoice i ON fi.InvoiceId = i.InvoiceId
            JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
            JOIN first_invoices fi2 ON fi.CustomerId = fi2.CustomerId
            WHERE DATE(fi.dt) BETWEEN DATE('{date_range[0]}') AND DATE('{date_range[1]}')
        )
        SELECT 
            month,
            COUNT(DISTINCT InvoiceId) AS num_purchases,
            COUNT(DISTINCT CustomerId) AS num_customers,
            SUM(Quantity) AS tracks_sold,
            SUM(UnitPrice * Quantity) AS revenue,
            SUM(first_time_flag) AS first_time_customers
        FROM invoice_expanded
        GROUP BY month
        ORDER BY month
    """

    return conn.execute(query).fetchdf()

@cache.memoize()
def get_ts_monthly_summary_cached(
    events_hash: str,
    date_range: Tuple[str, ...]
) -> pd.DataFrame:
    """
    """
    conn = get_connection()
    df = get_ts_monthly_summary(
        conn=conn,
        date_range=list(date_range)
    )

    return df

