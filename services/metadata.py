"""
Metadata services for the Chinook dashboard.

Provides:
- Sidebar filter metadata (genres, countries, artists, date range)
- Static summary KPIs from the dataset
- GitHub commit timestamp (with local caching)

Designed for high-efficiency reads from DuckDB and low-frequency API usage.
"""

import os
import json
import pandas as pd
from typing import Dict, Tuple, Any

from github import Github
from services.db import get_connection
from services.logging_utils import log_msg
from services.display_utils import format_kpi_value
from config import CACHE_PATH

def get_last_commit_date() -> str:
    """
    Retrieves the timestamp of the most recent commit on GitHub.

    Caches the result locally to avoid hitting GitHub's API rate limits.

    Returns:
        str: Formatted commit date (e.g. "Jul 20, 2025") or "Unavailable"
    """
    # Check for cached value
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f:
                cache = json.load(f)
                return cache.get("last_updated", "Unavailable")
        except Exception as e:
            log_msg(f"[GITHUB] Error reading cache: {e}")

    # Fallback to GitHub API
    try:
        token = os.getenv("GITHUB_TOKEN")
        g = Github(token) if token else Github()
        repo = g.get_repo("corvidfox/chinook-dashboard-pydash")
        last_commit = repo.get_commits()[0]
        date_str = last_commit.commit.author.date.strftime("%b %d, %Y")

        with open(CACHE_PATH, "w") as f:
            json.dump({"last_updated": date_str}, f)

        return date_str
    except Exception as e:
        log_msg(f"[GITHUB] API fetch failed: {e}")
        return "Unavailable"


def get_filter_metadata() -> Dict[str, Any]:
    """
    Fetches metadata required for dashboard filters.

    Extracts genre, country, artist names, and full dataset date range
    in ISO format.

    Returns:
        dict: {
            'genres': List[str],
            'countries': List[str],
            'artists': List[str],
            'date_range': (str, str)
        }
    """
    log_msg("[META] Fetching filter metadata from DuckDB.")
    conn = get_connection()

    queries = {
        "genres": "SELECT DISTINCT Name FROM Genre ORDER BY Name",
        "countries": "SELECT DISTINCT BillingCountry FROM Invoice ORDER BY BillingCountry",
        "artists": "SELECT DISTINCT Name FROM Artist ORDER BY Name",
        "date_range": "SELECT MIN(InvoiceDate), MAX(InvoiceDate) FROM Invoice"
    }

    genres    = [r[0] for r in conn.execute(queries["genres"]).fetchall()]
    countries = [r[0] for r in conn.execute(queries["countries"]).fetchall()]
    artists   = [r[0] for r in conn.execute(queries["artists"]).fetchall()]
    date_min, date_max = conn.execute(queries["date_range"]).fetchone()

    def to_iso(val):
        return val.date().isoformat() if hasattr(val, "date") else str(val)[:10]

    return {
        "genres": genres,
        "countries": countries,
        "artists": artists,
        "date_range": (to_iso(date_min), to_iso(date_max))
    }


def get_static_summary() -> pd.DataFrame:
    """
    Fetches and formats static dashboard-level KPIs.

    Unpivots SQL aggregates into labeled rows and applies formatting
    for display in sidebar or summary views.

    Returns:
        pd.DataFrame: Columns = ['Metric', 'Value']
    """
    conn = get_connection()
    sql = """
    WITH
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
    track_summary AS (
        SELECT COUNT(*) AS TracksSold FROM InvoiceLine
    ),
    genre_ct  AS (SELECT COUNT(*) AS NumGenres FROM Genre),
    artist_ct AS (SELECT COUNT(*) AS NumArtists FROM Artist)
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

    df: pd.DataFrame = conn.execute(sql).df()

    def format_row(row):
        metric, value = row["Metric"], row["Value"]
        if metric == "Date Range":
            return value
        return format_kpi_value(float(value), value_type="dollar" if "Revenue" in metric else "number")

    df["Value"] = df.apply(format_row, axis=1)
    return df
