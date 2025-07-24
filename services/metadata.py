"""
Metadata services for the Chinook dashboard.

Provides:
- Sidebar filter metadata (genres, countries, artists, date range)
- Static summary table (overview) from the dataset
- GitHub commit timestamp (with local caching)
- Artist and Genre catalog summary tables (temp DuckDB) creation and validation

Designed for high-efficiency reads from DuckDB and low-frequency API usage.
"""

import os
import json
import pandas as pd
from typing import Dict, Tuple, Any
from duckdb import DuckDBPyConnection
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

    log_msg("[META - GITHUB] Getting last commit date.")

    # Check for cached value
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f:
                cache = json.load(f)
                log_msg("     [META - GITHUB] Last commit date loaded from local cache")
                return cache.get("last_updated", "Unavailable")
        except Exception as e:
            log_msg(f"     [META - GITHUB] Error reading cache: {e}")

    # Fallback to GitHub API
    try:
        log_msg("     [META - GITHUB] Checking GitHub...")
        token = os.getenv("GITHUB_TOKEN")
        g = Github(token) if token else Github()
        repo = g.get_repo("corvidfox/chinook-dashboard-pydash")
        last_commit = repo.get_commits()[0]
        date_str = last_commit.commit.author.date.strftime("%b %d, %Y")

        with open(CACHE_PATH, "w") as f:
            json.dump({"last_updated": date_str}, f)
            log_msg(f"     [META - GITHUB] Last commit date cache updated: {date_str}")

        return date_str
    except Exception as e:
        log_msg(f"     [GITHUB] API fetch failed: {e}")
        return "Unavailable"


def get_filter_metadata() -> Dict[str, Any]:
    """
    Fetches metadata required for dashboard filters.

    Extracts genre, country, artist names, and full dataset date range
    in ISO format. Static values for metric options.

    Returns:
        dict: {
            'genres': List[str],
            'countries': List[str],
            'artists': List[str],
            'date_range': (str, str),
            'metrics': List[Dict]
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

    log_msg(f"     [META] Found {len(genres)} genres, {len(countries)} countries, {len(artists)} artists")

    def to_iso(val):
        return val.date().isoformat() if hasattr(val, "date") else str(val)[:10]

    log_msg(f"     [META] Date range: {to_iso(date_min)} – {to_iso(date_max)}")

    return {
        "genres": genres,
        "countries": countries,
        "artists": artists,
        "date_range": (to_iso(date_min), to_iso(date_max)),
        "metrics": [
            {"label": "Revenue (USD$)", "var_name": "revenue"},
            {"label": "Number of Customers", "var_name": "num_customers"}
            ]
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
    log_msg(f"[META] Static summary generated with {len(df)} metrics")

    return df


def create_catalog_tables(conn: DuckDBPyConnection) -> None:
    """
    Creates temp catalog tables for genre and artist coverage metrics.

    Tables:
        - genre_catalog: [genre, num_tracks]
        - artist_catalog: [artist, num_tracks]
    """
    log_msg("[DATA META - SQL] Creating catalog tables in DuckDB.")

    conn.execute(
    """CREATE OR REPLACE TEMP TABLE genre_catalog AS
        SELECT
            g.Name AS genre,
            COUNT(DISTINCT t.TrackId) AS num_tracks
        FROM Track t
        JOIN Genre g ON t.GenreId = g.GenreId
        GROUP BY genre
    """)

    conn.execute(
    """CREATE OR REPLACE TEMP TABLE artist_catalog AS
        SELECT
            ar.Name AS artist,
            COUNT(DISTINCT t.TrackId) AS num_tracks
        FROM Track t
        JOIN Album al ON t.AlbumId = al.AlbumId
        JOIN Artist ar ON al.ArtistId = ar.ArtistId
        GROUP BY artist
    """)
    num_genres = conn.execute("SELECT COUNT(*) FROM genre_catalog").fetchone()[0]
    num_artists = conn.execute("SELECT COUNT(*) FROM artist_catalog").fetchone()[0]

    log_msg(f"     [DATA META - SQL] genre_catalog populated with {num_genres} rows")
    log_msg(f"     [DATA META - SQL] artist_catalog populated with {num_artists} rows")


def check_catalog_tables(conn: DuckDBPyConnection) -> bool:
    """
    Verifies presence of catalog temp tables: genre_catalog and artist_catalog.

    Parameters:
        conn (DuckDBPyConnection): DuckDB connection

    Returns:
        bool: True if both tables exist, False otherwise
    """
    expected = {"genre_catalog", "artist_catalog"}
    found = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
    missing = expected - found

    if missing:
        log_msg(
            msg=f"[DATA META - SQL] Missing catalog tables: {', '.join(missing)}",
            level="warning"
        )
        return False

    log_msg("[DATA META - SQL] Catalog tables present.")
    return True