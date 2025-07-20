# services/sql_utils.py

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
    Build SQL WHERE clause fragments from app filters.

    Returns a list of SQL strings to be joined by AND.
    """
    clauses = []

    log_msg("[SQL UTILS] Forming WHERE clause.")
    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        clauses.append(
            f"DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')"
        )

    if country:
        escaped = "', '".join([str(c).replace("'", "''") for c in country])
        clauses.append(f"i.BillingCountry IN ('{escaped}')")

    if genre:
        escaped = "', '".join([str(g).replace("'", "''") for g in genre])
        clauses.append(f"g.Name IN ('{escaped}')")

    if artist:
        escaped = "', '".join([str(a).replace("'", "''") for a in artist])
        clauses.append(f"ar.Name IN ('{escaped}')")

    return clauses
