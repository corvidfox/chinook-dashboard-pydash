"""
helpers.py

Provides utility functions for generating Customer Retention panel 
summaries from DuckDB and building Plotly figures for visualization.

Functions:
    - get_retention_decay_data: raw SQL query for retention decay metrics.
    - get_retention_decay_data_cached: memoized wrapper around the raw query.
    - build_decay_plot: constructs a Plotly Figure from KPI DataFrame.
    - build_cohort_heatmap: constructs a Plotly Figure from KPI DataFrame.

"""
from typing import Tuple, Dict, Optional
import duckdb
import pandas as pd
import numpy as np

import dash_mantine_components as dmc
from plotly.graph_objects import Figure, Scatter, Heatmap

from services.cache_config import cache
from services.db import get_connection
from services.logging_utils import log_msg

# Register Plotly templates at import time.
dmc.add_figure_templates()

__all__ = [
    "get_retention_decay_data",
    "get_retention_decay_data_cached",
    "build_decay_plot",
    "build_cohort_heatmap"
]

def get_retention_decay_data(conn: duckdb.DuckDBPyConnection,
                    date_range: tuple[str, str],
                    max_offset: Optional[int] = None
                    ) -> pd.DataFrame:
    """
    Queries the filtered_invoices table in DuckDB and returns
    overall retention percentages by month offset.

    Parameters:
        conn: an active DuckDB connection.
        date_range: two-element tuple of str dates (YYYY-MM-DD).
        max_offset (int, optional): max month offset to include

    Returns:
        pd.DataFrame with columns:
        ['month_offset', 'num_retained', 'num_customers' 'country', 
        'retention_rate']
    """
    assert len(date_range) == 2 and all(isinstance(d, str) for d in date_range)
    log_msg("[SQL - DECAY] get_retention_decay_data(): querying retention decay data.")

    # If no max_offset, compute from full dataset range
    if max_offset is None:
        bounds_sql = f"""
        SELECT MIN(i.InvoiceDate) AS min_date,
               MAX(i.InvoiceDate) AS max_date
        FROM filtered_invoices fi
        JOIN Invoice i ON fi.InvoiceId = i.InvoiceId
        """
        date_bounds = conn.execute(bounds_sql).fetchdf()
        min_date = pd.to_datetime(date_bounds["min_date"].iloc[0])
        max_date = pd.to_datetime(date_bounds["max_date"].iloc[0])
        max_offset = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month)

    # Format Dates for SQL
    start = pd.to_datetime(date_range[0]).date()
    end   = pd.to_datetime(date_range[1]).date()

    # Compose & run the query
    sql = f"""
    WITH cohorts AS (
        SELECT
            CustomerId,
            DATE_TRUNC('month', MIN(InvoiceDate)) AS cohort_start
        FROM Invoice
        GROUP BY CustomerId
    ),
    activity AS (
        SELECT
            fi.CustomerId,
            i.InvoiceDate,
            DATE_TRUNC('month', c.cohort_start) AS cohort_month,
            DATE_TRUNC('month', i.InvoiceDate) AS activity_month,
            DATE_DIFF('month', c.cohort_start, i.InvoiceDate) AS month_offset
        FROM filtered_invoices fi
        JOIN Invoice i ON i.InvoiceId = fi.InvoiceId
        JOIN (
            SELECT
                CustomerId,
                DATE_TRUNC('month', MIN(InvoiceDate)) AS cohort_start
            FROM Invoice
            GROUP BY CustomerId
        ) c ON fi.CustomerId = c.CustomerId
        WHERE DATE_DIFF('month', c.cohort_start, i.InvoiceDate) >= 0
          AND fi.dt BETWEEN DATE '{start}' AND DATE '{end}'
          {"AND DATE_DIFF('month', c.cohort_start, i.InvoiceDate) <= " + str(max_offset) if max_offset is not None else ""}
    ),
    retention AS (
        SELECT 
            month_offset,
            COUNT(DISTINCT CustomerId) AS num_retained
        FROM activity
        GROUP BY month_offset
    ),
    cohort_size AS (
        SELECT COUNT(DISTINCT CustomerId) AS num_customers FROM activity
    )
    SELECT
        r.month_offset,
        r.num_retained,
        cs.num_customers,
        r.num_retained * 1.0 / cs.num_customers AS retention_rate
    FROM retention r, cohort_size cs
    WHERE r.month_offset > 0
    ORDER BY r.month_offset
    """

    df = conn.execute(sql).fetchdf()
    log_msg(f"[SQL - DECAY] Retention Decay query returned {len(df)} rows.")
    return df


@cache.memoize()
def get_retention_decay_data_cached(
    events_hash: str,
    date_range: Tuple[str, ...],
    max_offset: Optional[int] = None
) -> pd.DataFrame:
    """
    Memoized wrapper for `get_retention_decay_data`.

    The cache key is derived from `events_hash` plus the `date_range` and 
    `max_offset`.

    Parameters:
        events_hash: A unique hash representing current filter state.
        date_range:  Tuple of two 'YYYY-MM-DD' date strings.
        max_offset (int, optional): max month offset to include

    Returns:
        DataFrame: Same structure as `get_retention_decay_data_cached`.
    """

    df = get_retention_decay_data(
        conn=get_connection(),
        date_range=list(date_range),
        max_offset=max_offset
    )

    return df


def build_decay_plot(
    df: pd.DataFrame,
    theme: Dict[str, str]
) -> Figure:
    """
    Build a retention decay line chart for a given decay subset DataFrame.

    Parameters:
        df: DataFrame with a 'month_offset' column and 'retention_rate' column.
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

    # Fallback for empty data set
    if df.empty or df['retention_rate'].isna().all():
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

    hover = (
        "Month Offset: %{x}<br>"
        "Retention Rate: %{y:,.2f}%"
    )

    df["retention_rate"] = df["retention_rate"] * 100

    fig.add_trace(Scatter(
        x=df["month_offset"],
        y=df["retention_rate"],
        mode="lines+markers",
        line=dict(width=2),
        marker=dict(size=6),
        customdata=df[[
            "month_offset", "retention_rate"
        ]],
        hovertemplate=hover, name = "",
        showlegend=False
    ))

    fig.update_layout(
        title="Customer Retention Decay",
        title_x=0.5,
        xaxis={
          "title": "Months Since First Purchase",
          "tickmode": "linear",
          "tick0": 0,
          "dtick": 3
        },
        yaxis={
            "title": "Retention (%)",
            "range": [0,100],
            "ticksuffix": "%"
            },
        template=template,
        font=dict(family=font_family),
        margin=dict(t=50, l=30, r=30, b=50),
        height=450
    )

    return fig

def build_cohort_heatmap(
    raw_df: pd.DataFrame,
    theme: dict
) -> Figure:
    """
    Build a cohort retention heatmap.

    Parameters:
        raw_df : pd.DataFrame
            Must contain columns:
              - 'cohort_month'       (datetime64[ns])
              - 'month_offset'       (int)
              - 'cohort_size'        (int)
              - 'retention_pct'      (float, 0-100)
        theme : dict
            Optional keys:
              - 'plotlyTemplate': Plotly template (default 'plotly_white')
              - 'fontFamily':     Font family (default 'Inter')

    Returns:
        fig : plotly.graph_objects.Figure
    """
    template   = theme.get("plotlyTemplate", "plotly_white")
    font_family = theme.get("fontFamily", "Inter")

    # Fallback for empty data set
    if raw_df.empty or raw_df["retention_pct"].isna().all():
        fig = Figure()
        fig.add_annotation(
            text="No data available for selected filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
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

    # Fill in missing cohort×offset combinations
    raw_df["cohort_month"] = pd.to_datetime(raw_df["cohort_month"])
    raw_df["retention_pct"] = raw_df["retention_pct"] * 100

    cohort_range = pd.date_range(
        start=raw_df["cohort_month"].min(),
        end  =raw_df["cohort_month"].max(),
        freq ="MS"
    )
    month_range = range(
        int(raw_df["month_offset"].min()),
        int(raw_df["month_offset"].max()) + 1
    )
    full_idx = pd.MultiIndex.from_product(
        [cohort_range, month_range],
        names=["cohort_month", "month_offset"]
    )
    full_df = (
        pd.DataFrame(index=full_idx)
          .reset_index()
          .merge(raw_df, how="left",
                 on=["cohort_month", "month_offset"])
    )

    # Labels & hover text
    full_df["CohortLabel"] = full_df["cohort_month"].dt.strftime("%b %Y")
    full_df["hover_text"] = np.where(
        full_df["retention_pct"].notna(),
        "Cohort: "    + full_df["CohortLabel"] +
        "<br>Month: " + full_df["month_offset"].astype(str) +
        "<br>Size: "  + full_df["cohort_size"].fillna(0).astype(int).astype(str) +
        "<br>Retention Rate: "  + 
            full_df["retention_pct"].round(1).astype(str) + "%",
        "Cohort: "    + full_df["CohortLabel"] +
        "<br>Month: " + full_df["month_offset"].astype(str) +
        "<br>No data"
    )

    # Pivot to matrices
    z = full_df.pivot(
        index="CohortLabel",
        columns="month_offset",
        values="retention_pct"
        ).values
    t = full_df.pivot(
        index="CohortLabel",
        columns="month_offset",
        values="hover_text"
        ).values
    x = sorted(full_df["month_offset"].unique())
    y = sorted(full_df["CohortLabel"].unique(),
               key=lambda lbl: pd.to_datetime(lbl, format="%b %Y"))

    # Build heatmap
    fig = Figure(
        data=Heatmap(
            z=z,
            x=x,
            y=y,
            text=t,
            hoverinfo="text",
            colorscale="Viridis_r",
            zmin=0,
            zmax=100,            
            #zmax=np.nanmax(z),
            colorbar=dict(title="Retention (%)"),
            hoverongaps=False
        )
    )

    # Layout & theming
    fig.update_layout(
        template=template,
        font=dict(family=font_family),
        title="Customer Retention by Cohort",
        xaxis=dict(
            title="Months Since First Purchase",
            type="category",
            tickangle=45
        ),
        yaxis=dict(
            title="Cohort Month (First Purchase)",
            type="category"
        ),
        height=600,
        margin=dict(t=50, l=40, r=40, b=50)
    )

    return fig
