"""
metadata.py

Extracts metadata and static summary metrics from the Chinook DuckDB
for use in sidebar filters and dashboard summaries. Optimized for
scalable SQL queries and reusable components.
"""

from services.db import get_connection
import duckdb
from services.logging_utils import log_msg
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime
from github import Github

def get_last_commit_date():
    g = Github()
    repo = g.get_repo("corvidfox/chinook-dashboard-pydash")
    last_commit = repo.get_commits()[0]
    return last_commit.commit.author.date.strftime("%b %d, %Y")


def get_filter_metadata() -> Dict[str, Any]:
    """Fetches metadata to populate filter options in the dashboard sidebar.

    Returns genre, country, artist, and date range values,
    all alphabetically sorted from the full Chinook dataset.

    Returns:
        dict: A dictionary with keys:
            - 'genres': List[str]
            - 'countries': List[str]
            - 'artists': List[str]
            - 'date_range': Tuple[str, str]  # formatted as ISO strings
    """
    log_msg("[DATA META] Fetching filter metadata from DuckDB.")

    conn = get_connection()
    queries = {
        "genres": "SELECT DISTINCT Name FROM Genre ORDER BY Name",
        "countries": "SELECT DISTINCT BillingCountry FROM Invoice ORDER BY BillingCountry",
        "artists": "SELECT DISTINCT Name FROM Artist ORDER BY Name",
        "date_range": "SELECT MIN(InvoiceDate), MAX(InvoiceDate) FROM Invoice"
    }

    genres = [row[0] for row in conn.execute(queries["genres"]).fetchall()]
    countries = [row[0] for row in conn.execute(queries["countries"]).fetchall()]
    artists = [row[0] for row in conn.execute(queries["artists"]).fetchall()]
    date_min, date_max = conn.execute(queries["date_range"]).fetchone()

    # Ensure ISO 8601 format: "YYYY-MM-DD"
    date_min_iso = date_min.date().isoformat() if hasattr(date_min, "date") else str(date_min)[:10]
    date_max_iso = date_max.date().isoformat() if hasattr(date_max, "date") else str(date_max)[:10]

    return {
        "genres": genres,
        "countries": countries,
        "artists": artists,
        "date_range": (date_min_iso, date_max_iso)
    }

def get_static_summary() -> pd.DataFrame:
    """
    Fires a single SQL pass in DuckDB, unpivots the aggregates,
    and returns a pandas DataFrame with columns ['Metric', 'Value'].
    """
    conn = get_connection()
    sql = """
    WITH
    -- Core summary from Invoice only (no join needed for revenue)
    invoice_summary AS (
      SELECT
        MIN(InvoiceDate) AS MinDate,
        MAX(InvoiceDate) AS MaxDate,
        ROUND(SUM(Total), 2) AS TotalRevenue,
        COUNT(DISTINCT InvoiceId) AS NumPurchases,
        COUNT(DISTINCT CustomerId) AS NumCustomers,
        COUNT(DISTINCT BillingCountry) AS NumCountries
      FROM Invoice
    ),

    -- Track sales from InvoiceLine
    track_summary AS (
      SELECT COUNT(*) AS TracksSold FROM InvoiceLine
    ),

    -- Catalog counts from standalone tables
    genre_ct  AS (SELECT COUNT(*) AS NumGenres FROM Genre),
    artist_ct AS (SELECT COUNT(*) AS NumArtists FROM Artist)

    -- Final unpivot
    SELECT 'Date Range' AS Metric,
          STRFTIME('%b %Y', MinDate) || ' – ' || STRFTIME('%b %Y', MaxDate) AS Value
    FROM invoice_summary

    UNION ALL SELECT 'Number of Purchases',  NumPurchases    FROM invoice_summary
    UNION ALL SELECT 'Number of Customers',  NumCustomers    FROM invoice_summary
    UNION ALL SELECT 'Tracks Sold',          TracksSold      FROM track_summary
    UNION ALL SELECT 'Total Revenue (USD$)', TotalRevenue    FROM invoice_summary
    UNION ALL SELECT 'Number of Genres',     NumGenres       FROM genre_ct
    UNION ALL SELECT 'Number of Artists',    NumArtists      FROM artist_ct
    UNION ALL SELECT 'Number of Countries',  NumCountries    FROM invoice_summary
    """

    # DuckDB’s Python API can directly a pd.DataFrame
    df: pd.DataFrame = conn.execute(sql).df()
    return df
