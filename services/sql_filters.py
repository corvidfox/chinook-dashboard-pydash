"""
sql_filters.py

Converts dashboard filters into SQL WHERE clause fragments.
Used for dynamic query composition in shared or page-specific queries.
Includes helpers for invoice joins and date filtering.
"""

from typing import List, Optional
import pandas as pd
from services.logging_utils import log_msg


def escape_in_list(values: List[str]) -> str:
    """
    Escapes and formats a list of strings for use in SQL IN clauses.

    Parameters:
        values (List[str]): Input strings to escape

    Returns:
        str: Comma-separated, SQL-safe string
    """
    return "', '".join(str(v).replace("'", "''") for v in values)


def form_where_clause(
    date_range: Optional[List[str]] = None,
    country: Optional[List[str]] = None,
    genre: Optional[List[str]] = None,
    artist: Optional[List[str]] = None
) -> List[str]:
    """
    Builds SQL WHERE clause fragments based on active dashboard filters.

    Parameters:
        date_range (Optional[List[str]]): Date range as ["YYYY-MM-DD", "YYYY-MM-DD"]
        country (Optional[List[str]]): List of selected countries
        genre (Optional[List[str]]): List of selected genres
        artist (Optional[List[str]]): List of selected artists

    Returns:
        List[str]: Valid SQL fragments to be joined with 'AND'
    """
    log_msg("[SQL FILTERS] Forming WHERE clause.")
    clauses = []

    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        clauses.append(f"DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')")

    if country:
        clauses.append(f"i.BillingCountry IN ('{escape_in_list(country)}')")

    if genre:
        clauses.append(f"g.Name IN ('{escape_in_list(genre)}')")

    if artist:
        clauses.append(f"ar.Name IN ('{escape_in_list(artist)}')")

    return clauses


def apply_date_filter(date_range: Optional[List[str]]) -> str:
    """
    Constructs a standardized SQL JOIN clause between event and invoice tables,
    with optional date range filtering on the invoice date.

    Parameters:
        date_range (Optional[List[str]]): Date range as ["YYYY-MM-DD", "YYYY-MM-DD"]

    Returns:
        str: SQL JOIN clause between 'e' (event) and 'i' (Invoice), with optional date filter
    """

    log_msg("[SQL FILTERS] Forming date filter.")
    
    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end = pd.to_datetime(date_range[1]).to_period("M").end_time.date()

        return (
            f"JOIN Invoice i ON i.InvoiceId = e.InvoiceId "
            f"AND DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')"
        )

    return "JOIN Invoice i ON i.InvoiceId = e.InvoiceId"
