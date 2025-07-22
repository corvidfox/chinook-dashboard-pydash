"""
services/kpi/group.py

Build and format group-level KPI tables for dashboard Top-N slices.

This module contains utilities to:
  - Compute full-period KPIs by group dimension (Genre, Artist, BillingCountry)
  - Slice out the top-N group values for any given metric, with tie-breakers
  - Enrich and format those Top-N slices with display-ready columns and formatted values

Functions:
  get_group_kpis_full(conn, group_var, date_range) → pd.DataFrame
  topn_kpis_slice_topn(df, metric, n) → pd.DataFrame
  topn_kpis_generate(df_full, metrics, n) → Dict[str, pd.DataFrame]
  topn_kpis_format_display(df, group_var, total_revenue) → pd.DataFrame
"""

from typing import List, Dict, Literal
import pandas as pd
from duckdb import DuckDBPyConnection

from services.logging_utils import log_msg
from services.display_utils import format_kpi_value

def get_group_kpis_full(
    conn: DuckDBPyConnection,
    group_var: Literal["Genre", "Artist", "BillingCountry"],
    date_range: List[str] = None
) -> pd.DataFrame:
    """
    Computes full-period KPIs by group (Genre, Artist, BillingCountry)

    Returns one row per group value with:
      - revenue, num_customers, num_purchases, first_time_customers, tracks_sold
    """
    assert group_var in ["Genre", "Artist", "BillingCountry"]

    log_msg(f"[SQL - KPIs] get_group_kpis_full(): querying full KPIs by {group_var}")

    # Build group-specific joins and fields
    if group_var == "Genre":
        group_expr = "g.Name"
        joins = """
            JOIN Track t ON il.TrackId = t.TrackId
            JOIN Genre g ON g.GenreId = t.GenreId
            LEFT JOIN genre_catalog gc ON gc.genre = g.Name
        """
    elif group_var == "Artist":
        group_expr = "ar.Name"
        joins = """
            JOIN Track t ON il.TrackId = t.TrackId
            JOIN Album al ON t.AlbumId = al.AlbumId
            JOIN Artist ar ON ar.ArtistId = al.ArtistId
            LEFT JOIN artist_catalog ac ON ac.artist = ar.Name
        """
    else:  # BillingCountry
        group_expr = "i.BillingCountry"
        joins = ""

    # Apply invoice filter
    if date_range and len(date_range) == 2:
        start = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end   = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        invoice_join = f"""
            JOIN Invoice i ON i.InvoiceId = e.InvoiceId
            AND DATE(i.InvoiceDate) BETWEEN DATE('{start}') AND DATE('{end}')
        """
    else:
        invoice_join = "JOIN Invoice i ON i.InvoiceId = e.InvoiceId"

    sql = f"""
    WITH base AS (
        SELECT
            e.CustomerId,
            i.InvoiceDate AS invoice_date,
            i.InvoiceId,
            il.TrackId,
            il.Quantity,
            il.UnitPrice,
            {group_expr} AS group_val
        FROM filtered_invoices e
        {invoice_join}
        JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
        {joins}
    ),
    first_purchases AS (
        SELECT CustomerId, MIN(DATE(invoice_date)) AS first_purchase
        FROM base
        GROUP BY CustomerId
    )
    SELECT
        b.group_val,
        COUNT(DISTINCT b.CustomerId) AS num_customers,
        COUNT(DISTINCT b.InvoiceId) AS num_purchases,
        SUM(b.Quantity) AS tracks_sold,
        SUM(b.Quantity * b.UnitPrice) AS revenue,
        COUNT(DISTINCT CASE
            WHEN DATE(b.invoice_date) = fp.first_purchase
            THEN b.CustomerId END) AS first_time_customers
    FROM base b
    LEFT JOIN first_purchases fp ON b.CustomerId = fp.CustomerId
    GROUP BY b.group_val
    ORDER BY b.group_val
    ;
    """

    return conn.execute(sql).df()

def topn_kpis_slice_topn(df: pd.DataFrame, metric: str, n: int = 5) -> pd.DataFrame:
    """Returns top-N rows for a selected metric, with ties broken by group name"""
    return (
        df[df[metric].notna()]
        .sort_values(by=[metric, "group_val"], ascending=[False, True])
        .head(n)
        .reset_index(drop=True)
    )

def topn_kpis_generate(
    df_full: pd.DataFrame,
    metrics: List[Dict[str, str]],
    n: int = 5
) -> Dict[str, pd.DataFrame]:
    """Returns a dictionary of top-N tables keyed by metric name"""
    log_msg(f"[SQL - KPIs] topn_kpis_generate(): Slicing top {n} groups by metrics")

    return {
        m["var_name"]: topn_kpis_slice_topn(df_full, m["var_name"], n)
        for m in metrics
    }

def topn_kpis_format_display(df: pd.DataFrame, group_var: str, total_revenue: float = None) -> pd.DataFrame:
    """
    Adds derived KPI columns and attaches formatted display values.

    Parameters:
        df (pd.DataFrame): Raw top-N KPI slice with columns like revenue, tracks_sold, etc.
        group_var (str): One of 'Genre', 'Artist', 'BillingCountry'
        total_revenue (float): Optional total revenue for share-of-revenue calculations

    Returns:
        pd.DataFrame: Extended with derived KPIs and *_fmt display columns
    """
    # Derived metrics
    df["avg_revenue_per_cust"] = df["revenue"] / df["num_customers"]
    df["avg_revenue_per_purchase"] = df["revenue"] / df["num_purchases"]
    df["avg_tracks_per_purchase"] = df["tracks_sold"] / df["num_purchases"]

    df["revenue_share"] = (
        df["revenue"] / total_revenue
        if total_revenue and total_revenue > 0
        else df["revenue"] / df["revenue"].sum()
    )

    # Format columns row-by-row
    for col in df.columns:
        if col == "group_val":
            continue  # don't format labels

        # Assign formatting type based on column name
        fmt_type = (
            "percent" if "percent" in col or "share" in col else
            "dollar"  if "revenue" in col else
            "number"  if col in ["tracks_sold", "num_purchases", "num_customers"] else
            "float"
        )

        fmt_col = f"{col}_fmt"
        df[fmt_col] = df[col].apply(lambda x: format_kpi_value(x, value_type=fmt_type))

    # Optional: Format country labels using flagify_country if needed
    if group_var.lower() == "billingcountry":
        df["group_val_fmt"] = df["group_val"].apply(lambda x: format_kpi_value(x, value_type="country"))

    return df