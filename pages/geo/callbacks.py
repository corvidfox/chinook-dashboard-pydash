"""
callbacks.py

Defines and registers all Dash callbacks for the geographic distribution 
dashboard module.

Callbacks include:
  - AG-Grid theme update
  - Geo data table refresh
  - KPI cards update
  - Metric plot rendering
  - CSV download and button toggle

Public API:
  - register_callbacks(app)
"""

from datetime import date
from typing import Any, Dict, List, Tuple

import pandas as pd
from dash import Dash, Input, Output, State, dcc
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import plotly.graph_objects as go

from config import get_mantine_theme
from pages.geo.helpers import (
    get_geo_metrics_cached,
    build_geo_plot
)
from services.display_utils import (
    standardize_country_to_iso3,
    make_topn_kpi_card
    )
from services.logging_utils import log_msg


__all__ = ["register_callbacks"]


def register_callbacks(app: Dash) -> None:
    """
    Wire up all Dash @app.callback functions for the geo page.

    Parameters:
        app: The Dash application instance to register callbacks on.

    Returns:
        None
    """
    @app.callback(
        Output("geo-data-scroll", "className"),
        Input("grid-theme-store", "data")
    )
    def update_aggrid_theme(grid_class: str) -> str:
        """
        Set the AG-Grid CSS class based on the selected theme.

        Parameters:
            grid_class: The CSS class name stored in grid-theme-store.

        Returns:
            The same CSS class name to apply to the grid container.
        """
        log_msg(f"[CALLBACK:geo] Updated grid theme: {grid_class}")
        return grid_class


    @app.callback(
        Output("geo-data-scroll", "columnDefs"),
        Output("geo-data-scroll", "rowData"),
        Output("geo-agg-store", "data"),
        Input("events-shared-fingerprint", "data"),
        Input("date-range-store", "data"),
    )
    def update_geo(
        events_hash: str,
        date_range: Tuple[str, str],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Refresh the geographic distribution DataFrame and push to AG-Grid.

        Parameters:
            events_hash: Unique fingerprint for current filters.
            date_range: Tuple of two 'YYYY-MM-DD' strings.

        Returns:
            A tuple of (columnDefs, rowData) for AG-Grid.
        """
        if not events_hash:
            raise PreventUpdate

        log_msg("[CALLBACK:geo] - Callback active.")

        geo_df_yr, geo_df_agg = get_geo_metrics_cached(events_hash, date_range)
        geo_df_yr_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in geo_df_yr.columns
            ]

        log_msg("[CALLBACK:geo] Geo dashboard data refreshed")
        log_msg(f"     [CALLBACK:geo] Geo Table Rows = {len(geo_df_yr)}")

        return (
            geo_df_yr_coldefs, 
            geo_df_yr.to_dict("records"), 
            geo_df_agg.to_dict("records")
        )


    @app.callback(
        Output("geo-kpi-cards", "children"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data"),
    )
    def update_geo_kpis(
        metric_value: str,
        metric_label: str,
        geo_kpis: Dict[str, Any],
        _fingerprint: str
    ) -> List[dmc.Card]:
        """
        Build and return KPI cards for metric, revenue, and customers.

        Parameters:
            metric_value: Column name in the Geo DataFrame.
            metric_label: Axis label for the plot.
            geo_kpis: Dict containing 'topn' with formatted values.
            _fingerprint: Fingerprint for the KPI set (unused).

        Returns:
            A list of Dash components representing KPI cards.
        """

        log_msg("[CALLBACK:geo] Updating KPI cards.")

        # Top Countries by your chosen metric
        top_countries   = make_topn_kpi_card(
            kpis        = geo_kpis,
            metric_key  = metric_value,
            fmt_key     = f"{metric_value}_fmt",
            title       = "Top Countries",
            icon        = "fa7-solid:ranking-star",
            tooltip     = "Top countries by the chosen metric.",
            list_path   = ("topn", "topn_country"),
            total_label = "Total Countries"
        )

        # Revenue Share: show “revenue_fmt (revenue_share_fmt)”
        revenue_share = make_topn_kpi_card(
            kpis            = geo_kpis,
            metric_key      = metric_value,
            fmt_key         = f"{metric_value}_fmt",
            title           = "Revenue (% Share)",
            icon            = "icon-park-solid:chart-proportion",
            tooltip         = "Revenue and percentage of total revenue.",
            include_footer  = False,
            custom_label_fn = lambda idx, itm: itm['revenue_fmt'],
            custom_value_fn = lambda itm: itm['revenue_share_fmt'],
            list_path  = ("topn", "topn_country")
            )

        # Customers & Avg Rev/Customer
        customers = make_topn_kpi_card(
            kpis            = geo_kpis,
            metric_key      = metric_value,
            fmt_key         = f"{metric_value}_fmt",
            title           = "Customers (Avg Revenue Per)",
            icon            = "mdi:people-outline",
            tooltip         = "Customer count and average revenue per customer.",
            include_footer  = False,
            custom_label_fn = lambda idx, itm: itm["num_customers_fmt"],
            custom_value_fn = lambda itm: itm["avg_revenue_per_cust_fmt"],
            list_path  = ("topn", "topn_country")
        )

        return [top_countries, revenue_share, customers]
   
    
    @app.callback(
        Output("download-geo-csv", "data"),
        Input("btn-download-geo", "n_clicks"),
        State("geo-data-scroll", "rowData"),
        prevent_initial_call=True,
    )
    def download_geo_csv_from_grid(
        n_clicks: int,
        row_data: List[Dict[str, Any]],
    ) -> Any:
        """
        Serialize the AG-Grid rowData to CSV and trigger download.

        Parameters:
            n_clicks: Number of download button clicks.
            row_data: Current rowData from the grid.

        Returns:
            A `dcc.send_data_frame` payload to prompt CSV download.
        """
        if not row_data:
            raise PreventUpdate

        df = pd.DataFrame(row_data)
        today_str = date.today().strftime("%Y_%m_%d")
        filename = f"chinook_geo_{today_str}.csv"

        log_msg("[CALLBACK:geo] Download processing.")

        return dcc.send_data_frame(df.to_csv, filename=filename, index=False)


    @app.callback(
        Output("btn-download-geo", "disabled"),
        Output("btn-download-geo", "children"),
        Output("btn-download-geo", "style"),
        Input("geo-data-scroll", "rowData"),
    )
    def toggle_download_btn(
        row_data: List[Dict[str, Any]],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enable or disable the download button based on rowData presence.

        Parameters:
            row_data: The current AG-Grid rowData list.

        Returns:
            disabled flag, button label, and style dict.
        """
        # If no rows: disable & show alternate text
        if not row_data or len(row_data) == 0:
            disabled = True
            label    = "No data in range to download"
            style    = {"opacity": "0.5", "cursor": "not-allowed"}
            # Or to hide: style = {"display": "none"}
        else:
            disabled = False
            label    = "Download CSV"
            style    = {}

        return disabled, label, style
    

    @app.callback(
        Output("geo-metric-plot", "figure"),
        Input("geo-data-scroll", "rowData"),
        Input("geo-agg-store", "data"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("theme-store", "data"),
        State("date-range-store", "data"),
        State("events-shared-fingerprint", "data"),
    )
    def render_geo_plot(
        geo_yearly_df: Dict,
        geo_agg_df: Dict,
        metric_value: str,
        metric_label: str,
        theme_style: Dict[str, Any],
        date_range: Tuple[str, str],
        events_hash: str,
    ) -> go.Figure:
        """ 
        Generate and return a Choropleth Plotly figure for the selected metric.

        Parameters:
            geo_yearly_df: Geo Yearly DataFrame (Dict stored format)
            geo_agg_df: Geo Aggregated DataFrame (Dict stored format)
            metric_value: Column name in the Geo DataFrame.
            metric_label: Axis label for the plot.
            theme_style: Dict containing Mantine theme data.
            date_range: Tuple of two 'YYYY-MM-DD' strings.
            events_hash: Filter fingerprint.

        Returns:
            A Plotly Figure object.
        """
        if not events_hash or not metric_value or not geo_yearly_df or not geo_agg_df:
            raise PreventUpdate

        log_msg("[CALLBACK:geo] Updating Plot.")

        # Mantine‐themed Plotly settings
        theme_data = get_mantine_theme(theme_style["color_scheme"])
        theme_info = {
            "plotlyTemplate": theme_data.get("plotlyTemplate", "plotly_white"),
            "fontFamily": theme_data.get("fontFamily", "Inter")
        }

        metric_dict = {
            "var_name": metric_value,
            "label": metric_label
        }

        # Load data
        df_yearly = pd.DataFrame.from_dict(geo_yearly_df)
        df_aggregate = pd.DataFrame.from_dict(geo_agg_df)

        # Ensure the yearly slice is strings and tag aggregate with "All"
        df_yearly["year"] = df_yearly["year"].astype(str)
        df_aggregate = df_aggregate.assign(year="All")

        log_msg(f"    [CALLBACK:geo] Read in GEO YEARLY DF with {len(df_yearly)} rows")

        # Combine both DataFrames
        df = pd.concat([df_yearly, df_aggregate], ignore_index=True)

        # Standardize to ISO3, drop only invalid ISO rows
        df["iso_alpha"] = df["country"].apply(standardize_country_to_iso3)
        df = df.dropna(subset=["iso_alpha"])

        # Order years, putting "All" last
        years = sorted([y for y in df["year"].unique() if y != "All"]) + ["All"]
        df["year"] = pd.Categorical(df["year"], categories=years, ordered=True)

        log_msg("   [CALLBACK:geo] Rendering plot.")

        # Build and return the animated choropleth
        fig = build_geo_plot(df, metric_dict,theme_info)

        return fig
