"""
metadata.py

Extracts metadata and static summary metrics from the Chinook DuckDB
for use in sidebar filters and dashboard summaries. Optimized for
scalable SQL queries and reusable components.
"""

from services.db import get_connection
from services.logging_utils import log_msg
from typing import Dict, List, Tuple, Any
from datetime import datetime
from github import Github

def get_last_commit_date():
    g = Github()  # Add a token here if your repo is private or rate limits
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

def get_static_summary() -> Dict[str, Any]:
    """Generates a summary of dataset-level metrics for sidebar display.

    Includes counts and aggregates for purchases, customers, tracks sold,
    revenue, genres, artists, and countries.

    Returns:
        dict: A dictionary with summary keys:
            - 'date_range': str
            - 'num_purchases': int
            - 'num_customers': int
            - 'tracks_sold': int
            - 'total_revenue': float
            - 'num_genres': int
            - 'num_artists': int
            - 'num_countries': int
    """
    log_msg("[DATA META] Fetching static dashboard summary from DuckDB.")

    conn = get_connection()

    summary_sql = """
        SELECT
            MIN(InvoiceDate) AS MinDate,
            MAX(InvoiceDate) AS MaxDate,
            COUNT(DISTINCT Invoice.InvoiceId) AS NumPurchases,
            COUNT(DISTINCT CustomerId) AS NumCustomers,
            COUNT(InvoiceLine.TrackId) AS TracksSold,
            ROUND(SUM(Invoice.Total), 2) AS TotalRevenue,
            COUNT(DISTINCT Genre.Name) AS NumGenres,
            COUNT(DISTINCT Artist.Name) AS NumArtists,
            COUNT(DISTINCT Invoice.BillingCountry) AS NumCountries
        FROM Invoice
        JOIN InvoiceLine ON Invoice.InvoiceId = InvoiceLine.InvoiceId
        JOIN Track ON InvoiceLine.TrackId = Track.TrackId
        JOIN Genre ON Track.GenreId = Genre.GenreId
        JOIN Album ON Track.AlbumId = Album.AlbumId
        JOIN Artist ON Album.ArtistId = Artist.ArtistId
    """

    result = conn.execute(summary_sql).fetchone()
    (min_date, max_date, purchases, customers,
     tracks_sold, revenue, genres, artists, countries) = result

    min_date_fmt = min_date.strftime("%b %Y")
    max_date_fmt = max_date.strftime("%b %Y")

    return {
        "date_range": f"{min_date_fmt} to {max_date_fmt}",
        "num_purchases": purchases,
        "num_customers": customers,
        "tracks_sold": tracks_sold,
        "total_revenue": revenue,
        "num_genres": genres,
        "num_artists": artists,
        "num_countries": countries
    }
