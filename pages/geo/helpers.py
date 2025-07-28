"""
helpers.py

Provides utility functions for generating Geographic Distribution panel 
summaries from DuckDB and building Plotly figures for visualization.

Functions:
    - get_geo_metrics: raw SQL query for country aggregated metrics.
    - get_geo_metrics_cached: memoized wrapper around the raw query.
    - build_geo_plot: constructs a Plotly Figure from KPI DataFrame.

"""
from typing import Tuple, Dict, List
from duckdb import DuckDBPyConnection
import pandas as pd
import pycountry

import dash_mantine_components as dmc
import plotly.graph_objects as go

from services.cache_config import cache
from services.db import get_connection
from services.display_utils import format_kpi_value
from services.logging_utils import log_msg

# Register Plotly templates at import time.
dmc.add_figure_templates()

__all__ = [
    "get_geo_metrics",
    "get_geo_metrics_cached",
    "build_geo_plot",
]

import duckdb
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_geo_metrics(conn: duckdb.DuckDBPyConnection,
                    date_range: tuple[str, str],
                    mode: str = "yearly") -> pd.DataFrame:
    """
    Queries the filtered_invoices table in DuckDB and returns
    year-country aggregates for KPIs, including revenue, purchases,
    tracks sold, customer counts, and first-time customer flag.

    Parameters:
        con: an active DuckDB connection.
        date_range: two-element tuple of str dates (YYYY-MM-DD).
        mode: "yearly" (break out by year) or "aggregate" (one row per country).

    Returns:
        pd.DataFrame with columns:
        ['year', 'num_months', 'country', 'num_customers',
         'num_purchases', 'tracks_sold', 'revenue',
         'first_time_customers']
    """
    # Validate inputs
    if mode not in ("yearly", "aggregate"):
        raise ValueError("mode must be 'yearly' or 'aggregate'")
    assert isinstance(date_range, list) and len(date_range) == 2, \
        "`date_range` must be a list of two YYYY-MM-DD strings"

    log_msg("[SQL - GEO] get_geo_metrics(): querying pre-aggregated KPIs.")

    start_date, end_date = date_range
    # Catch poorly-formed dates early
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    # Build SQL fragments
    if mode == "yearly":
        group_by_year     = "STRFTIME('%Y', fd.dt) AS year,"
        group_by_fields   = "STRFTIME('%Y', fd.dt), fd.country"
    else:
        group_by_year     = "'All' AS year,"
        group_by_fields   = "fd.country"

    # Compose & run the query
    sql = f"""
    WITH filtered_data AS (
      SELECT
        fi.CustomerId,
        fi.dt,
        i.BillingCountry AS country,
        fi.InvoiceId
      FROM filtered_invoices fi
      JOIN Invoice i ON fi.InvoiceId = i.InvoiceId
      WHERE fi.dt BETWEEN DATE('{start_date}') AND DATE('{end_date}')
    ),
    first_purchases AS (
      SELECT CustomerId, MIN(dt) AS first_date
      FROM filtered_data
      GROUP BY CustomerId
    )
    SELECT
      {group_by_year}
      fd.country AS country,
      COUNT(DISTINCT fd.CustomerId) AS num_customers,
      COUNT(DISTINCT fd.InvoiceId)     AS num_purchases,
      SUM(il.Quantity)                  AS tracks_sold,
      SUM(il.UnitPrice * il.Quantity)   AS revenue,
      COUNT(DISTINCT CASE
        WHEN fd.dt = fp.first_date THEN fd.CustomerId
        ELSE NULL
      END)                               AS first_time_customers
    FROM filtered_data fd
    JOIN InvoiceLine il ON fd.InvoiceId = il.InvoiceId
    JOIN first_purchases fp ON fd.CustomerId = fp.CustomerId
    GROUP BY {group_by_fields}
    ORDER BY {group_by_fields}
    """
    df = conn.execute(sql).df()

    # Compute `num_months` for each year
    if mode == "yearly":
        years = list(range(start_dt.year, end_dt.year + 1))
    else:
        years = ["All"]

    months_data = []
    for y in years:
        if y == "All":
            # In aggregate mode, cover the full span
            delta = relativedelta(end_dt, start_dt)
            months = delta.years * 12 + delta.months + 1
            months_data.append({"year": "All", "num_months": months})
        else:
            if y == start_dt.year and y == end_dt.year:
                # same year span
                months = end_dt.month - start_dt.month + 1
            elif y == start_dt.year:
                months = 13 - start_dt.month
            elif y == end_dt.year:
                months = end_dt.month
            else:
                months = 12
            months_data.append({"year": str(y), "num_months": months})

    months_df = pd.DataFrame(months_data)

    # Merge & reorder columns
    out = (
        df
        .astype({"year": str})
        .merge(months_df, on="year", how="left")
    )

    # Move num_months right after year
    cols = out.columns.tolist()
    cols.insert(1, cols.pop(cols.index("num_months")))
    out = out[cols]

    return out


@cache.memoize()
def get_geo_metrics_cached(
    events_hash: str,
    date_range: Tuple[str, ...]
) -> pd.DataFrame:
    """
    Memoized wrapper for `get_geo_metrics`.

    The cache key is derived from `events_hash` plus the `date_range`.

    Parameters:
        events_hash: A unique hash representing current filter state.
        date_range:  Tuple of two 'YYYY-MM-DD' date strings.

    Returns:
        DataFrame: Same structure as `get_ts_monthly_summary`.
    """
    conn = get_connection()
    df_yearly = get_geo_metrics(
        conn=conn,
        date_range=list(date_range),
        mode = "yearly"
    )
    df_aggregate = get_geo_metrics(
        conn=conn,
        date_range=list(date_range),
        mode = "aggregate"
    )

    return df_yearly, df_aggregate


def build_geo_plot(
    df: pd.DataFrame,
    metric: Dict[str, str],
    theme_info: Dict[str, str],
) -> go.Figure:
    var, lab = metric["var_name"], metric["label"]
    zmin, zmax = df[var].min(), df[var].max()

    template = theme_info.get("plotlyTemplate", "plotly_white")
    font_family = theme_info.get("fontFamily", "Inter")

    # Fallback for empty data set
    if df.empty or df[var].isna().all():
        fig = go.Figure()
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


    # Build master list of ALL ISO3s via pycountry
    all_iso = [c.alpha_3 for c in pycountry.countries if hasattr(c, "alpha_3")]

    # Generate rich hover text per row
    def mk_hover(r):
        return (
            f"Country: {r.country}<br>"
            f"Year: {r.year}<br>"
            f"{lab}: {format_kpi_value(r[var], 'dollar') if var == 'revenue' else format_kpi_value(r[var], 'number')}<br>"
            f"Purchases: {format_kpi_value(r.num_purchases, 'number')}<br>"
            f"Tracks Sold: {format_kpi_value(r.tracks_sold, 'number')}<br>"
            f"Customers: {format_kpi_value(r.num_customers, 'number')}<br>"
            f"First-Time Cust: {format_kpi_value(r.first_time_customers, 'number')}<br>"
            f"Rev/Cust: {format_kpi_value(r.revenue / r.num_customers, 'dollar')}"
        )

    df["hover"] = df.apply(mk_hover, axis=1)

    frames = []

    log_msg(f"[PLOT:geo] Building frames for years: {df['year'].cat.categories}")

    for yr in df["year"].cat.categories:
        dff = df[df["year"] == yr]

        # Base layer: everyone, dark grey, no colorbar
        base_trace = go.Choropleth(
            locations=all_iso,
            z=[0] * len(all_iso),
            locationmode="ISO-3",
            colorscale=[[0, "darkgrey"], [1, "darkgrey"]],
            showscale=False,
            marker_line_color="white",
            marker_line_width=0.5,
            hoverinfo="skip"
        )

        # Data layer: your Viridis_r choropleth
        data_trace = go.Choropleth(
            locations=dff["iso_alpha"],
            z=dff[var],
            text=dff["hover"],
            hoverinfo="text",
            colorscale="Viridis_r",
            zmin=zmin,
            zmax=zmax,
            marker_line_color="darkgrey",
            marker_line_width=0.5,
            colorbar=dict(title=lab),
        )

        frames.append(
            go.Frame(
                name=str(yr),
                data=[base_trace, data_trace]
            )
        )

    # Start the figure on the first frame
    fig = go.Figure(data=frames[0].data, frames=frames)

    # Layout + play/pause + slider
    fig.update_layout(
        template=template,
        font_family=font_family,
        title=dict(text=f"{lab} by Country (Animated by Year)", x=0.5),
        geo=dict(
            showframe=True,
            showcoastlines=True,
            projection_type="natural earth"
        ),
        updatemenus=[{
            "type": "buttons",
            "direction": "left",
            "buttons": [
                {
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 1000, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 300, "easing": "quadratic-in-out"}
                    }]
                },
                {
                    "label": "Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0},
                        "mode": "immediate"
                    }]
                }
            ],
            "showactive": False,
            "x": 0.1, "y": 0.05,
            "pad": {"r": 10, "t": 10}
        }],
        sliders=[{
            "active": 0,
            "pad": {"t": 50},
            "steps": [
                {
                    "method": "animate",
                    "label": yr,
                    "args": [[yr], {
                        "frame": {"duration": 500, "redraw": True},
                        "mode": "immediate"
                    }]
                }
                for yr in df["year"].cat.categories
            ]
        }],
        # Static legend box for "no data"
        annotations=[
            dict(
                text="No data available.",
                x=0.05, y=0.01,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(color="white", size=12),
                align="left",
                bgcolor="darkgrey",
                bordercolor="black",
                borderwidth=1,
                opacity=0.8
            )
        ]
    )

    return fig
