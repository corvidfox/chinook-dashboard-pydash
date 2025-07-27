"""
helper.py

Provides utility functions for generating Time Series panel summaries
from DuckDB and building Plotly figures for visualization.

Functions:
    - get_ts_monthly_summary: raw SQL query for monthly KPIs.
    - get_ts_monthly_summary_cached: memoized wrapper around the raw query.
    - build_ts_plot: constructs a Plotly Figure from KPI DataFrame.

"""
from typing import Tuple, Dict, List
from duckdb import DuckDBPyConnection
import pandas as pd
import dash_mantine_components as dmc
from plotly.graph_objects import Figure, Scatter

from services.cache_config import cache
from services.db import get_connection
from services.logging_utils import log_msg

# Register Plotly templates at import time.
dmc.add_figure_templates()

__all__ = [
    "get_ts_monthly_summary",
    "get_ts_monthly_summary_cached",
    "build_ts_plot",
]

def get_ts_monthly_summary(
        conn: DuckDBPyConnection, 
        date_range: List[str]
) -> pd.DataFrame:
    """
    Queries the filtered_invoices temp table in DuckDB and returns monthly KPIs.

    Parameters:
        conn (duckdb.DuckDBPyConnection): Active DuckDB connection.
        date_range (List[str]): List of two 'YYYY-MM-DD' strings defining date bounds.

    Returns:
        A pandas DataFrame with columns:
            - month (str, 'YYYY-MM')
            - num_purchases (int)
            - num_customers (int)
            - tracks_sold (int)
            - revenue (float)
            - first_time_customers (int)
    """
    assert isinstance(date_range, list) and len(date_range) == 2, \
        "`date_range` must be a list of two YYYY-MM-DD strings"

    log_msg("[SQL] get_ts_monthly_summary(): querying pre-aggregated KPIs.")

    query = f"""
        WITH first_invoices AS (
            SELECT 
                CustomerId,
                MIN(dt) AS first_invoice_date
            FROM filtered_invoices
            GROUP BY CustomerId
        ),
        invoice_expanded AS (
            SELECT 
                fi.CustomerId,
                fi.InvoiceId,
                fi.dt AS invoice_date,
                STRFTIME(fi.dt, '%Y-%m') AS month,
                i.BillingCountry,
                i.BillingState,
                il.Quantity,
                il.UnitPrice,
                CASE 
                    WHEN STRFTIME(fi.dt, '%Y-%m') = STRFTIME(fi2.first_invoice_date, '%Y-%m') THEN 1
                    ELSE 0
                END AS first_time_flag
            FROM filtered_invoices fi
            JOIN Invoice i ON fi.InvoiceId = i.InvoiceId
            JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
            JOIN first_invoices fi2 ON fi.CustomerId = fi2.CustomerId
            WHERE DATE(fi.dt) BETWEEN DATE('{date_range[0]}') AND DATE('{date_range[1]}')
        )
        SELECT 
            month,
            COUNT(DISTINCT InvoiceId) AS num_purchases,
            COUNT(DISTINCT CustomerId) AS num_customers,
            SUM(Quantity) AS tracks_sold,
            SUM(UnitPrice * Quantity) AS revenue,
            SUM(first_time_flag) AS first_time_customers
        FROM invoice_expanded
        GROUP BY month
        ORDER BY month
    """

    return conn.execute(query).fetchdf()

@cache.memoize()
def get_ts_monthly_summary_cached(
    events_hash: str,
    date_range: Tuple[str, ...]
) -> pd.DataFrame:
    """
    Memoized wrapper for `get_ts_monthly_summary`.

    The cache key is derived from `events_hash` plus the `date_range`.

    Parameters:
        events_hash: A unique hash representing current filter state.
        date_range:  Tuple of two 'YYYY-MM-DD' date strings.

    Returns:
        DataFrame: Same structure as `get_ts_monthly_summary`.
    """
    conn = get_connection()
    df = get_ts_monthly_summary(
        conn=conn,
        date_range=list(date_range)
    )

    return df


def build_ts_plot(
    df: pd.DataFrame,
    metric: Dict[str, str],
    theme: Dict[str, str]
) -> Figure:
    """
    Build a time-series line chart for a given KPI DataFrame.

    Parameters:
        df: DataFrame with a 'month' column and KPI columns.
        metric: Dict with keys:
            - 'var_name': column name in df to plot (e.g., 'revenue')
            - 'label': human-friendly axis label (e.g., 'Revenue')
        theme: Dict with optional keys:
            - 'plotlyTemplate': Plotly template name (default 'plotly_white')
            - 'fontFamily': font family for all text (default 'Inter')

    Returns:
        A Plotly Figure object, either with a line+marker trace
        or a "no data" annotation if the DataFrame is empty.
    """
    template = theme.get("plotlyTemplate", "plotly_white")
    font_family = theme.get("fontFamily", "Inter")

    fig = Figure()

    if df.empty or df[metric["var_name"]].isna().all():
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

    df["month_fmt"] = pd.to_datetime(df["month"])
    df["rev_per_cust"] = df["revenue"] / df["num_customers"]

    hover = (
        "Month: %{x|%b %Y}<br>"
        "Revenue: $%{customdata[0]:,.2f}<br>"
        "Purchases: %{customdata[1]}<br>"
        "Tracks Sold: %{customdata[2]}<br>"
        "Customers: %{customdata[3]}<br>"
        "First-Time: %{customdata[4]}<br>"
        "Rev / Cust: $%{customdata[5]:,.2f}"
    )

    fig.add_trace(Scatter(
        x=df["month_fmt"],
        y=df[metric["var_name"]],
        mode="lines+markers",
        line=dict(width=2),
        marker=dict(size=6),
        customdata=df[[
            "revenue", "num_purchases", "tracks_sold",
            "num_customers", "first_time_customers", "rev_per_cust"
        ]],
        hovertemplate=hover, name = "",
        showlegend=False
    ))

    fig.update_layout(
        title=f"{metric['label']} by Month",
        title_x=0.5,
        xaxis_title="Month",
        yaxis_title=metric["label"],
        template=template,
        font=dict(family=font_family),
        margin=dict(t=50, l=30, r=30, b=50),
        height=450
    )

    return fig
