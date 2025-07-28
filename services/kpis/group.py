"""
services/kpi/group.py

Build and format group-level KPI tables for dashboard Top-N slices.

This module contains utilities to:
  - Compute full-period KPIs by group dimension (Genre, Artist, BillingCountry)
  - Slice out the top-N group values for any given metric, with tie-breakers
  - Enrich and format those Top-N slices with display-ready columns and formatted values

Functions:
  get_group_kpis_full(conn, group_var, date_range) -> pd.DataFrame
  topn_kpis_slice_topn(df, metric, n) -> pd.DataFrame
  topn_kpis_generate(df_full, metrics, n) -> Dict[str, pd.DataFrame]
  topn_kpis_format_display(df, group_var, total_revenue) -> pd.DataFrame
  query_catalog_sales(conn, tbl, group_var) -> pd.DataFrame
  enrich_catalog_kpis(conn, tbl, topn_df, group_var) -> pd.DataFrame
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

def topn_kpis_format_display(
        conn: DuckDBPyConnection, 
        df: pd.DataFrame, 
        group_var: str, 
        total_revenue: float = None
        ) -> pd.DataFrame:
    """
    Adds derived KPI columns and attaches formatted display values.

    Parameters:
        conn : DuckDBPyConnection
            An active DuckDB connection.
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

    # Enrich with catalog statistics for artist and genre
    if group_var in ["Genre", "Artist"]:
        df = enrich_catalog_kpis(conn, df, group_var)

    # Format columns row-by-row
    for col in df.columns:
        if col == "group_val":
            continue  # don't format labels

        # Assign formatting type based on column name
        fmt_type = (
            "percent" if "percent" in col or "share" in col or "pct" in col else
            "dollar"  if "revenue" in col else
            "number"  if col in [
                "tracks_sold", "num_purchases", "num_customers", "catalog_size",
                "first_time_customers", "unique_tracks_sold"
                ] else
            "float"
        )

        fmt_col = f"{col}_fmt"
        df[fmt_col] = df[col].apply(lambda x: format_kpi_value(x, value_type=fmt_type))

    # Optional: Format country labels using flagify_country if needed
    if group_var.lower() == "billingcountry":
        df["group_val_fmt"] = df["group_val"].apply(lambda x: format_kpi_value(x, value_type="country"))
    else:
        df["group_val_fmt"] = df["group_val"]

    return df


def query_catalog_sales(
    conn: DuckDBPyConnection,
    group_var: str = "Genre"
) -> pd.DataFrame:
    """
    Compute percent-of-catalog sold for each Genre or Artist.

    Parameters:
        conn : DuckDBPyConnection
            An active DuckDB connection.
        group_var : str, default "Genre"
            Must be one of {"Genre", "Artist"}.

    Returns:
        pd.DataFrame
            Columns:
            - <genre|artist> (str)          grouping key, lowercase
            - unique_tracks_sold (int)      distinct tracks sold
            - catalog_size (int)            total tracks in catalog
            - pct_catalog_sold (float)      unique_tracks_sold / catalog_size
    """
    # Validate inputs
    if not isinstance(group_var, str):
        raise ValueError("`group_var` must be a string")
    group_var = group_var.capitalize()
    if group_var not in ("Genre", "Artist"):
        raise ValueError("`group_var` must be 'Genre' or 'Artist'")

    # Build the SQL snippets for joins/fields
    if group_var == "Genre":
        join_clause = """
          JOIN Track t           ON il.TrackId = t.TrackId
          JOIN Genre g           ON g.GenreId = t.GenreId
          LEFT JOIN genre_catalog gc
               ON gc.genre = g.Name
        """
        group_field   = "g.Name"
        catalog_field = "gc.num_tracks"
    else:  # Artist
        join_clause = """
          JOIN Track t           ON il.TrackId = t.TrackId
          JOIN Album al          ON al.AlbumId = t.AlbumId
          JOIN Artist ar         ON ar.ArtistId = al.ArtistId
          LEFT JOIN artist_catalog ac
               ON ac.artist = ar.Name
        """
        group_field   = "ar.Name"
        catalog_field = "ac.num_tracks"

    # Compose and execute SQL
    sql = f"""
    SELECT
      {group_field}   AS group_val,
      COUNT(DISTINCT il.TrackId)                AS unique_tracks_sold,
      ANY_VALUE({catalog_field})                AS catalog_size,
      COUNT(DISTINCT il.TrackId) * 1.0
        / NULLIF(ANY_VALUE({catalog_field}), 0)  AS pct_catalog_sold
    FROM filtered_invoices AS e
    JOIN InvoiceLine il ON il.InvoiceId = e.InvoiceId
    {join_clause}
    GROUP BY group_val
    ORDER BY group_val
    """
    df = conn.execute(sql).fetchdf()

    return df


def enrich_catalog_kpis(
    conn: DuckDBPyConnection,
    topn_df: pd.DataFrame,
    group_var: str = "Genre"
) -> pd.DataFrame:
    """
    Join catalog-level KPIs (coverage & diversity) onto a Top-N summary.

    Parameters:
        conn : DuckDBPyConnection
            An active DuckDB connection.
        topn_df : pd.DataFrame
            A Top-N summary DataFrame that must contain a column named
            either 'genre' or 'artist' (lowercase), matching group_var.lower().
        group_var : str, default "Genre"
            Either 'Genre' or 'Artist'.

    Returns:
        pd.DataFrame
            A new DataFrame containing all columns from topn_df, plus:
              - unique_tracks_sold (int)
              - catalog_size (int)
              - pct_catalog_sold (float)
    """
    # Validate group_var
    group_var = group_var.capitalize()
    if group_var not in ("Genre", "Artist"):
        raise ValueError("`group_var` must be 'Genre' or 'Artist'")

    # Fetch full catalog‐sales KPIs
    catalog_df = query_catalog_sales(conn, group_var)

    # Subset to only the Top‐N groups in topn_df
    if "group_val" not in topn_df.columns:
        raise KeyError(f"topn_df must contain a `group_val` column")
    top_values = topn_df["group_val"].unique().tolist()
    catalog_subset = catalog_df[catalog_df["group_val"].isin(top_values)]

    # Left‐join onto topn_df
    enriched = topn_df.merge(
        catalog_subset,
        how="left",
        on="group_val",
        validate="one_to_one"
    )

    return enriched
