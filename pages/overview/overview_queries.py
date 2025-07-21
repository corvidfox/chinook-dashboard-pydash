"""
overview_queries.py

Overview tab-specific SQL logic for fetching invoice details.
"""

import pandas as pd
from duckdb import DuckDBPyConnection
from services.logging_utils import log_msg

def get_invoices_details(conn: DuckDBPyConnection, invoice_ids: list, date_range: list) -> pd.DataFrame:
    """
    Returns full invoice-level data scoped to selected IDs + date range.

    Parameters:
        conn (DuckDBPyConnection)
        invoice_ids (List[int])
        date_range (List[str]) → ["YYYY-MM-DD", "YYYY-MM-DD"]

    Returns:
        pd.DataFrame
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
