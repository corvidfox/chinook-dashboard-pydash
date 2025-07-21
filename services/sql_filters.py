"""
sql_filters.py

Converts dashboard filters into SQL WHERE clause fragments.
Used for dynamic query composition in shared or page-specific queries.
"""

from typing import List, Optional
import pandas as pd
from services.logging_utils import log_msg

def form_where_clause(
    date_range: Optional[List[str]] = None,
    country: Optional[List[str]] = None,
    genre: Optional[List[str]] = None,
    artist: Optional[List[str]] = None,
) -> List[str]:
    """
    Builds SQL WHERE clause fragments from app filters.

    Parameters:
        date_range (List[str]): [start, end] ISO strings
        country (List[str])
        genre (List[str])
        artist (List[str])

    Returns:
        List[str]: Individual SQL clauses
    """
    log_msg("[SQL UTILS] Forming WHERE clause.")
    clauses = []

    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        clauses.append(f"DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')")

    def escape_in_list(values: List[str]) -> str:
        return "', '".join(str(v).replace("'", "''") for v in values)

    if country:
        clauses.append(f"i.BillingCountry IN ('{escape_in_list(country)}')")

    if genre:
        clauses.append(f"g.Name IN ('{escape_in_list(genre)}')")

    if artist:
        clauses.append(f"ar.Name IN ('{escape_in_list(artist)}')")

    return clauses
