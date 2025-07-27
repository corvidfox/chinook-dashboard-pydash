"""
callbacks.py

Defines and registers all Dash callbacks for the time-series dashboard module.

Callbacks include:
  - AG-Grid theme update
  - Time-series data table refresh
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
from dash_iconify import DashIconify

from config import get_mantine_theme
from pages.timeseries.helpers import (
    get_ts_monthly_summary_cached,
    build_ts_plot,
)
from services.display_utils import safe_kpi_card, safe_kpi_entry
from services.logging_utils import log_msg


__all__ = ["register_callbacks"]


def register_callbacks(app: Dash) -> None:
    """
    Wire up all Dash @app.callback functions for the time-series page.

    Parameters:
        app: The Dash application instance to register callbacks on.

    Returns:
        None
    """
    @app.callback(
        Output("ts-data-scroll", "className"),
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
        log_msg(f"[CALLBACK:timeseries] Updated grid theme → {grid_class}")
        return grid_class

    @app.callback(
        Output("ts-data-scroll", "columnDefs"),
        Output("ts-data-scroll", "rowData"),
        Input("events-shared-fingerprint", "data"),
        Input("date-range-store", "data"),
    )
    def update_ts(
        events_hash: str,
        date_range: Tuple[str, str],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Refresh the time-series DataFrame and push to AG-Grid.

        Parameters:
            events_hash: Unique fingerprint for current filters.
            date_range: Tuple of two 'YYYY-MM-DD' strings.

        Returns:
            A tuple of (columnDefs, rowData) for AG-Grid.
        """
        if not events_hash:
            raise PreventUpdate

        log_msg("[CALLBACK:timeseries] - Callback active.")

        ts_df = get_ts_monthly_summary_cached(events_hash, date_range)
        ts_df_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in ts_df.columns
            ]

        log_msg("[CALLBACK:timeseries] Time Series dashboard data refreshed")
        log_msg(f"     [CALLBACK:timeseries] Data Table Rows = {len(ts_df)}")

        return (
            ts_df_coldefs, ts_df.to_dict("records")
        )

    @app.callback(
        Output("ts-kpi-cards", "children"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data"),
    )
    def update_ts_kpis(
        dynamic_kpis: Dict[str, Any],
        dynamic_kpis_hash: str,
    ) -> List[Any]:
        """
        Build and return KPI cards for revenue, purchases, and customers.

        Parameters:
            dynamic_kpis: Dict containing 'metadata_kpis' with formatted values.
            dynamic_kpis_hash: Fingerprint for the KPI set (unused).

        Returns:
            A list of Dash components representing KPI cards.
        """
        log_msg("[CALLBACK:timeseries] Updating KPI cards.")
        ts_kpis = dynamic_kpis
        
        def revenue_kpis():
            return [
                safe_kpi_entry("Total", ts_kpis["metadata_kpis"].get("revenue_total_fmt"), "Total revenue."),
                safe_kpi_entry("Avg / Month", ts_kpis["metadata_kpis"].get("revenue_per_month"), "Average revenue per month.")
            ]

        def purchase_kpis():
            return [
            safe_kpi_entry("Purchases", ts_kpis["metadata_kpis"].get("purchases_num"), "Total number of unique purchase events."),
            safe_kpi_entry("Tracks Sold", ts_kpis["metadata_kpis"].get("tracks_sold_num"), "Total unit sales."),
            safe_kpi_entry("Avg $ / Purchase", ts_kpis["metadata_kpis"].get("revenue_per_purchase"), "Average revenue per purchase.")
        ]

        def customer_kpis():
            return [
            safe_kpi_entry("Total", ts_kpis["metadata_kpis"].get("cust_num"), "Total unique customers."),
            safe_kpi_entry("First-Time", ts_kpis["metadata_kpis"].get("cust_per_new"), "(%) first-time customers.")
        ]

        cards = [
            safe_kpi_card(
                ts_kpis, 
                revenue_kpis,  
                title="Revenue",  
                icon="tdesign:money", 
                tooltip = "Revenue Statistics"
            ),
            safe_kpi_card(
                ts_kpis, 
                purchase_kpis, 
                title="Purchases", 
                icon="carbon:receipt", 
                tooltip = "Purchase statistics"
                ),
            safe_kpi_card(
                ts_kpis, 
                customer_kpis, 
                title="Customers", 
                icon="mdi:people-outline", 
                tooltip = "Customer statistics"
                )
        ]

        return cards

    @app.callback(
        Output("ts-metric-plot", "figure"),
        Input("events-shared-fingerprint", "data"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("date-range-store", "data"),
        Input("theme-store", "data"),
    )
    def render_plot(
        events_hash: str,
        metric_value: str,
        metric_label: str,
        date_range: Tuple[str, str],
        theme_style: Dict[str, Any],
    ) -> Any:
        """
        Generate and return a Plotly figure for the selected KPI metric.

        Parameters:
            events_hash: Filter fingerprint.
            metric_value: Column name in the TS DataFrame.
            metric_label: Axis label for the plot.
            date_range: Tuple of two 'YYYY-MM-DD' strings.
            theme_style: Dict containing Mantine theme data.

        Returns:
            A Plotly Figure object.
        """
        if not events_hash or not metric_value:
            raise PreventUpdate

        metric_dict = {
            "var_name": metric_value,
            "label": metric_label
        }

        theme_data = get_mantine_theme(theme_style["color_scheme"])

        theme_info = {
            "plotlyTemplate": theme_data.get("plotlyTemplate", "plotly_white"),
            "fontFamily": theme_data.get("fontFamily", "Inter"),
            "primaryColor": theme_data.get("primaryColor", "indigo"),
        }

        log_msg("[CALLBACK:timeseries] Rendering plot.")

        df = get_ts_monthly_summary_cached(events_hash, date_range)
        fig = build_ts_plot(df, metric_dict, theme_info)

        return fig
    
    @app.callback(
        Output("download-ts-csv", "data"),
        Input("btn-download-ts", "n_clicks"),
        State("ts-data-scroll", "rowData"),
        prevent_initial_call=True,
    )
    def download_ts_csv_from_grid(
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
        filename = f"chinook_ts_{today_str}.csv"

        log_msg("[CALLBACK:timeseries] Download processing.")

        return dcc.send_data_frame(df.to_csv, filename=filename, index=False)

    @app.callback(
        Output("btn-download-ts", "disabled"),
        Output("btn-download-ts", "children"),
        Output("btn-download-ts", "style"),
        Input("ts-data-scroll", "rowData"),
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