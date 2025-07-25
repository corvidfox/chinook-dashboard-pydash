"""
services/kpi/core.py

Compute core subset-level KPIs for a filtered invoice dataset.

This module provides functions to aggregate high-level metrics over a
prefiltered set of invoice data, including:
  - Total distinct purchases and unique customers
  - First-time customer counts and share of new customers
  - Total tracks sold
  - Revenue totals and per-month / per-customer / per-purchase rates
  - Counts of distinct genres, artists, and billing countries

Functions:
  get_subset_core_kpis(conn, date_range) → Dict[str, Any]
"""

from typing import List, Dict, Any
import pandas as pd
from duckdb import DuckDBPyConnection

from services.logging_utils import log_msg
from services.display_utils import format_kpi_value

def get_subset_core_kpis(
    conn: DuckDBPyConnection,
    date_range: List[str]
) -> Dict[str, Any]:
    """
    Computes a set of subset-level KPIs over a filtered invoice subset.

    Metrics include:
      - purchases_num: Total number of distinct purchases
      - cust_num: Total number of unique customers
      - cust_num_new: Count of first-time customers (global first purchase in range)
      - cust_per_new: First-time customers as a share of total customers
      - tracks_sold_num: Number of tracks sold
      - revenue_total: Raw revenue (unformatted)
      - revenue_total_fmt: Revenue formatted as USD string
      - revenue_per_month: Average monthly revenue over date window
      - revenue_per_cust: Revenue per customer
      - revenue_per_purchase: Revenue per purchase
      - genre_num: Count of distinct genres in subset
      - artist_num: Count of distinct artists in subset
      - country_num: Count of distinct billing countries
    """
    # Convert date strings to month-aligned bounds
    start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
    end   = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
    num_months = (end.year - start.year) * 12 + (end.month - start.month) + 1

    check_sql = f"""
    SELECT COUNT(*) AS num_rows
    FROM filtered_invoices
    WHERE DATE(dt) BETWEEN DATE('{start}') AND DATE('{end}');
    """

    count_df = conn.execute(check_sql).df()
    if count_df.iloc[0]["num_rows"] == 0:
        log_msg("[SQL - KPIs] filtered_invoices is empty for that date range.")
        return {}

    sql = f"""
    WITH
      date_filtered AS (
        SELECT *
        FROM filtered_invoices e
        WHERE DATE(e.dt) BETWEEN DATE('{start}') AND DATE('{end}')
      ),

      customer_lifespan AS (
        SELECT
          CustomerId,
          MIN(InvoiceDate) AS first_purchase
        FROM Invoice
        GROUP BY CustomerId
      ),

      metrics AS (
        SELECT
          COUNT(DISTINCT df.InvoiceId)                                    AS num_purchases,
          COUNT(DISTINCT df.CustomerId)                                   AS num_customers,
          COUNT(DISTINCT CASE
                           WHEN DATE(cl.first_purchase)
                                BETWEEN DATE('{start}') AND DATE('{end}')
                           THEN df.CustomerId END)                       AS num_first_timers,
          COALESCE(SUM(il.Quantity), 0)                                AS tracks_sold,
          ROUND(COALESCE(SUM(il.Quantity * il.UnitPrice), 0), 2)      AS total_revenue,
          COUNT(DISTINCT t.GenreId)                                    AS num_genres,
          COUNT(DISTINCT ar.ArtistId)                                   AS num_artists,
          COUNT(DISTINCT i.BillingCountry)                             AS num_countries
        FROM date_filtered df
        -- first-time customer join
        LEFT JOIN customer_lifespan cl   ON df.CustomerId = cl.CustomerId
        -- invoice lines for tracks/revenue
        LEFT JOIN InvoiceLine il         ON df.InvoiceId  = il.InvoiceId
        LEFT JOIN Track t                ON il.TrackId    = t.TrackId
        -- artist from album
        LEFT JOIN Album al               ON t.AlbumId     = al.AlbumId
        LEFT JOIN Artist ar              ON al.ArtistId   = ar.ArtistId
        -- billing country
        LEFT JOIN Invoice i              ON df.InvoiceId  = i.InvoiceId
      )

    SELECT
      '{start:%b %Y} - {end:%b %Y}' AS date_range,
      num_purchases,
      num_customers,
      num_first_timers     AS num_first_time_customers,
      tracks_sold,
      total_revenue,
      num_genres,
      num_artists,
      num_countries
    FROM metrics;
    """

    df = conn.execute(sql).df()

    row = df.iloc[0]

    # Prepare formatted output
    revenue = float(row["total_revenue"])
    purchases = int(row["num_purchases"])
    customers = int(row["num_customers"])
    new_customers = int(row["num_first_time_customers"])

    kpis: Dict[str, Any] = {
        "purchases_num":           format_kpi_value(purchases, "number", accuracy=1),
        "cust_num":                format_kpi_value(customers, "number", accuracy=1),
        "cust_num_new":            format_kpi_value(new_customers, "number", accuracy=1),
        "cust_per_new":            format_kpi_value(
            new_customers / customers if customers > 0 else None, 
            "percent"
            ),
        "tracks_sold_num":         format_kpi_value(int(row["tracks_sold"]), "number", accuracy=1),
        "revenue_total":           revenue,
        "revenue_total_fmt":       format_kpi_value(revenue, "dollar"),
        "revenue_per_month":       format_kpi_value(
            revenue / num_months if num_months > 0 else None, 
            "dollar"
            ),
        "revenue_per_cust":        format_kpi_value(
            revenue / customers if customers > 0 else None, 
            "dollar"
            ),
        "revenue_per_purchase":    format_kpi_value(
            revenue / purchases if purchases > 0 else None, 
            "dollar"
            ),
        "genre_num":               format_kpi_value(int(row["num_genres"]), "number", accuracy=1),
        "artist_num":              format_kpi_value(int(row["num_artists"]), "number", accuracy=1),
        "country_num":             format_kpi_value(int(row["num_countries"]), "number", accuracy=1),
    }

    log_msg(f"[SQL - KPIs] Generated {len(kpis)} metrics.")
    return kpis
