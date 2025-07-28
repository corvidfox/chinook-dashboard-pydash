"""
helpers.py

Provides utility functions for generating Time Series panel summaries
from DuckDB and building Plotly figures for visualization.

Functions:
    - get_group_data: raw SQL query for monthly KPIs.
    - get_group_data_cached: memoized wrapper around the raw query.
    - build_group_plot: constructs a Plotly Figure from KPI DataFrame.

"""
from typing import Tuple, Dict, List
from duckdb import DuckDBPyConnection
import pandas as pd
import textwrap
import dash_mantine_components as dmc
from plotly.graph_objects import Figure, Bar
from plotly.colors import sample_colorscale

from services.db import get_connection
from services.cache_config import cache
from services.logging_utils import log_msg

# Register Plotly templates at import time.
dmc.add_figure_templates()

__all__ = [
    "get_group_data",
    "get_group_data_cached",
    "build_group_stacked_bar",
]

def get_group_data(
        conn: DuckDBPyConnection, 
        date_range: List[str],
        group_var: str
) -> pd.DataFrame:
    """
    Queries the filtered_invoices temp table in DuckDB and returns 
    year-aggregated KPIs for the grouping variable.

    Parameters:
        conn (duckdb.DuckDBPyConnection): Active DuckDB connection.
        date_range (List[str]): List of two 'YYYY-MM-DD' strings defining date bounds.
        group_var(str): Name of grouping variable.

    Returns:
        A pandas DataFrame with columns:
            - year (int 'YYYY')
            - group_var (artist or genre) (str)
            - num_customers (int)
            - num_purchases (int)
            - num_countries (int)
            - tracks_sold (int)
            - revenue (float)
            - first_time_customers (int)
            - unique_tracks_sold (int)
            - first_tracks_sold (int)
            - catalog_size (int)
    """
    # Validate inputs
    assert isinstance(date_range, list) and len(date_range) == 2, \
        "`date_range` must be a list of two YYYY-MM-DD strings"

    group_var = group_var.capitalize()
    assert group_var in ("Genre", "Artist"), "`group_var` must be 'Genre' or 'Artist'"

    log_msg(
        f"[SQL-GROUP] get_group_data(): {group_var}: querying pre-aggregated KPIs."
    )

    # Map join based on group_var
    mapping = {
        "Genre": {
            "join_clause": """
        JOIN Track t    ON il.TrackId = t.TrackId
        JOIN Genre g    ON g.GenreId = t.GenreId
        LEFT JOIN genre_catalog gc
             ON gc.genre = g.Name
            """,
            "group_expr":   "g.Name",
            "catalog_expr": "gc.num_tracks"
        },
        "Artist": {
            "join_clause": """
        JOIN Track t    ON il.TrackId = t.TrackId
        JOIN Album al   ON al.AlbumId = t.AlbumId
        JOIN Artist ar  ON ar.ArtistId = al.ArtistId
        LEFT JOIN artist_catalog ac
             ON ac.artist = ar.Name
            """,
            "group_expr":   "ar.Name",
            "catalog_expr": "ac.num_tracks"
        }
    }

    cfg = mapping[group_var]

    query = f"""
    WITH base AS (
      SELECT
        fi.CustomerId,
        fi.dt,
        i.BillingCountry AS country,
        fi.InvoiceId,
        il.TrackId,
        il.Quantity,
        il.UnitPrice,
        {cfg['group_expr']}   AS group_val,
        {cfg['catalog_expr']} AS catalog_size
      FROM filtered_invoices fi
      JOIN Invoice i       ON fi.InvoiceId = i.InvoiceId
      JOIN InvoiceLine il  ON fi.InvoiceId = il.InvoiceId
      {cfg['join_clause']}
      WHERE fi.dt BETWEEN DATE '{date_range[0]}' 
                      AND DATE '{date_range[1]}'
    ),
    first_purchases AS (
      SELECT CustomerId, MIN(dt) AS first_date
      FROM base
      GROUP BY CustomerId
    ),
    first_track_sales AS (
      SELECT TrackId, MIN(dt) AS first_sold_date
      FROM base
      GROUP BY TrackId
    )
    SELECT
      STRFTIME('%Y', b.dt)           AS year,
      b.group_val                    AS group_val,
      COUNT(DISTINCT b.CustomerId)   AS num_customers,
      COUNT(DISTINCT b.InvoiceId)    AS num_purchases,
      COUNT(DISTINCT b.country)      AS num_countries,
      SUM(b.Quantity)                AS tracks_sold,
      SUM(b.UnitPrice * b.Quantity)  AS revenue,
      COUNT(DISTINCT CASE
        WHEN STRFTIME('%Y', b.dt) = STRFTIME('%Y', fp.first_date)
        THEN b.CustomerId END
      )                               AS first_time_customers,
      COUNT(DISTINCT b.TrackId)       AS unique_tracks_sold,
      COUNT(DISTINCT CASE
        WHEN STRFTIME('%Y', b.dt) = STRFTIME('%Y', fts.first_sold_date)
        THEN b.TrackId END
      )                               AS first_tracks_sold,
      ANY_VALUE(b.catalog_size)       AS catalog_size
    FROM base b
    LEFT JOIN first_purchases fp ON b.CustomerId = fp.CustomerId
    LEFT JOIN first_track_sales fts ON b.TrackId   = fts.TrackId
    GROUP BY year, b.group_val
    ORDER BY year, b.group_val
    """

    df = conn.execute(query).fetchdf()

    # Rename group_val column to lowercase group_var
    df = df.rename(columns={"group_val": group_var.lower()})

    log_msg(f"[SQL-GROUP] get_group_data(): retrieved rows: {len(df)}")
        
    return df

@cache.memoize()
def get_group_data_cached(
    events_hash: str,
    date_range: Tuple[str, ...],
    group_var: str
) -> pd.DataFrame:
    """
    Memoized wrapper for `get_group_data`.

    The cache key is derived from `events_hash` plus the `date_range` and 
    `group_var`.

    Parameters:
        events_hash: A unique hash representing current filter state.
        date_range:  Tuple of two 'YYYY-MM-DD' date strings.
        group_var: Grouping variable (string).

    Returns:
        DataFrame: Same structure as `get_ts_monthly_summary`.
    """
    df = get_group_data(
        conn=get_connection(),
        date_range=list(date_range),
        group_var=group_var
    )

    return df


def build_group_stacked_bar(
    df: pd.DataFrame,
    metric: Dict[str, str],
    group_var: str,
    theme: Dict[str, str],
    max_n: int = 20
) -> Figure:
    """
    Build a stacked bar chart of yearly performance metrics for a group 
    dimension.

    Parameters:
        df : pd.DataFrame
            Must contain columns:
            - 'year'                   (int or str)
            - lowercased group_var     (str)
            - metric['var_name']       (numeric)
            - 'num_purchases'          (numeric)
            - 'tracks_sold'            (numeric)
            - 'revenue'                (numeric)
            - 'catalog_size'           (numeric)
            - 'unique_tracks_sold'     (numeric)
        metric : dict
            A dict with keys:
            - 'var_name': DataFrame column to stack (e.g. 'revenue')
            - 'label':     Text label for the y-axis (e.g. 'Revenue (USD$)')
        group_var : str
            Either "Genre" or "Artist".
        group_label : str
            Display label for the x-axis and tooltip (e.g. "Genre").
        theme : dict
            Optional theming keys:
            - 'plotlyTemplate': Plotly template (default 'plotly_white')
            - 'fontFamily':     Font family (default 'Inter')
        max_n : int
            Number of top groups (by total metric) to display.

    Returns:
        fig : plotly.graph_objs.Figure
            A stacked bar chart.
    """
    template   = theme.get("plotlyTemplate", "plotly_white")
    font_family = theme.get("fontFamily", "Inter")

    y_var = metric["var_name"]
    y_label = metric["label"]
    group_col = group_var.lower()
    group_label = group_var.capitalize()

    # Fallback for no data
    if df.empty or df[y_var].isna().all():
        fig = Figure()
        fig.add_annotation(
            text="No data available for selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(family=font_family, size=16),
        )
        fig.update_layout(
            template=template,
            font=dict(family=font_family),
            height=200,
            margin=dict(t=30, b=30, l=30, r=30),
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    # Prepare data
    df = df.copy()

    # Ensure year is string for grouping
    df["year_str"] = df["year"].astype(str)

    # Compute total metric per group and pick top_n
    top_groups = (
        df.groupby(group_col)[y_var]
        .sum()
        .sort_values(ascending=False)
        .head(max_n)
        .index.tolist()
    )

    # Filter to max_n groups
    df = df[df[group_col].isin(top_groups)]

    # Sort years and apply colors
    years_sorted = sorted(df["year_str"].unique())
    n_years = len(years_sorted)
    year_colors = sample_colorscale("Viridis", [i / n_years for i in range(n_years)])
    year_colors.reverse()

    fig = Figure()

    # Build stacked bars, one trace per year
    for i, year in enumerate(years_sorted):
        sub = df[df["year_str"] == year]

        hover = (
            f"{group_label}: " + sub[group_col].astype(str) + "<br>" +
            f"Year: {year}<br>" +
            "Revenue: " + sub["revenue"].map("${:,.0f}".format) + "<br>" +
            "Purchases: " + sub["num_purchases"].map("{:,}".format) + "<br>" +
            "Tracks Sold: " + sub["tracks_sold"].map("{:,}".format) + "<br>" +
            "Tracks in Catalog: " + sub["catalog_size"].map("{:,}".format) + 
            "<br>" + "Revenue/Track in Catalog: " + 
            (sub["revenue"] / sub["catalog_size"]).map("${:,.2f}".format) + 
            "<br>" +
            "Pct Catalog Sold: " + 
            (sub["unique_tracks_sold"] / sub["catalog_size"]).map("{:.1%}".format)
        )

        fig.add_trace(
            Bar(
                x=sub[group_col],
                y=sub[y_var],
                name=year,
                marker_color=year_colors[i],
                hovertext=hover,
                hoverinfo="text"
            )
        )

    # Wrap and center title
    base_title = f"{group_label} Performance: {y_label} - Top {len(top_groups)}"
    wrapped_lines = textwrap.wrap(
        base_title, width=30, break_long_words=False, break_on_hyphens=False
        )
    title_wrapped = "<br>".join(wrapped_lines)

    fig.update_layout(
        barmode="stack",
        template=template,
        font=dict(family=font_family),
        title=dict(text=title_wrapped, x=0.5),
        xaxis=dict(
            title=group_label,
            categoryorder="array",
            categoryarray=top_groups,
            tickangle=45
        ),
        yaxis=dict(title=y_label),
        legend=dict(
            title="Year",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        margin=dict(t=80, l=40, r=120, b=60),
        height=450
    )

    return fig
