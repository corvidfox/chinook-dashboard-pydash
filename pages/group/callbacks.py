"""
callbacks.py

Defines and registers all Dash callbacks for the performance by group
dashboard modules.

Callbacks include:
  - AG-Grid theme update
  - Group data table refresh
  - KPI cards update
  - Metric plot rendering
  - CSV download and button toggle

Public API:
  - register_callbacks(app, group_var)
"""

from datetime import date
from typing import Any, Dict, List, Tuple

import pandas as pd
from dash import Dash, Input, Output, State, dcc
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from config import get_mantine_theme
from pages.group.helpers import (
    get_group_data_cached,
    build_group_stacked_bar
)
from services.display_utils import make_topn_kpi_card
from services.logging_utils import log_msg


__all__ = ["register_callbacks"]


def register_callbacks(app: Dash, group_var: str) -> None:
    """
    Wire up all Dash @app.callback functions for the group performance pages.

    Parameters:
        app: The Dash application instance to register callbacks on.
        group_var: the name of the grouping variable (e.g., "Genre", "Artist")

    Returns:
        None
    """
    @app.callback(
        Output(f"{group_var}-data-scroll", "className"),
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
        log_msg(f"[CALLBACK:group] Updated grid theme: {grid_class}")
        return grid_class


    @app.callback(
        Output(f"{group_var}-data-scroll", "columnDefs"),
        Output(f"{group_var}-data-scroll", "rowData"),
        Input("events-shared-fingerprint", "data"),
        Input("date-range-store", "data"),
    )
    def update_group(
        events_hash: str,
        date_range: Tuple[str, str],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Refresh the group DataFrame and push to AG-Grid.

        Parameters:
            events_hash: Unique fingerprint for current filters.
            date_range: Tuple of two 'YYYY-MM-DD' strings.

        Returns:
            A tuple of (columnDefs, rowData) for AG-Grid.
        """
        if not events_hash or not date_range:
            raise PreventUpdate

        log_msg(f"[CALLBACK:group] - Callback active for {group_var}.")

        start_date = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end_date   = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        date_range=[start_date,end_date]

        group_df = get_group_data_cached(events_hash, date_range, group_var)
        group_df_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in group_df.columns
            ]

        log_msg(f"[CALLBACK:group] Group {group_var} dashboard data refreshed")
        log_msg(f"     [CALLBACK:group] Data Table Rows = {len(group_df)}")

        return (
            group_df_coldefs, group_df.to_dict("records")
        )


    @app.callback(
        Output(f"{group_var}-kpi-cards", "children"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data"),
    )
    def update_group_kpis(
        metric_value: str,
        metric_label: str,
        dynamic_kpis: Dict[str, Any],
        _fingerprint: str
    ) -> List[dmc.Card]:
        """
        Build and return KPI cards for metric, revenue, and catalog penetration.

        Parameters:
            metric_value: Column name in the Geo DataFrame.
            metric_label: Axis label for the plot.
            dynamic_kpis: Dict containing 'topn' with formatted values.
            _fingerprint: Fingerprint for the KPI set (unused).

        Returns:
            A list of Dash components representing KPI cards.
        """

        log_msg(f"[CALLBACK:group] Updating {group_var} KPI cards.")
        
        # Top Group Values by chosen metric
        top_groups = make_topn_kpi_card(
            kpis       = dynamic_kpis,
            metric_key = metric_value,
            fmt_key    = f"{metric_value}_fmt",
            title      = f"Top {group_var.capitalize()}s",
            icon       = "fa7-solid:ranking-star",
            tooltip    = f"Top {group_var.lower()}s by the chosen metric.",
            list_path  = ("topn", f"topn_{group_var.lower()}"),
            total_label = f"Total {group_var.capitalize()}s"
        )

        # Revenue Share: show “revenue_fmt (revenue_share_fmt)”
        revenue_share = make_topn_kpi_card(
            kpis            = dynamic_kpis,
            metric_key      = metric_value,
            fmt_key          = f"{metric_value}_fmt",
            title           = "Revenue (% Share)",
            icon            = "icon-park-solid:chart-proportion",
            tooltip         = "Revenue and percentage of total revenue.",
            include_footer  = False,
            custom_label_fn = lambda idx, itm: itm['revenue_fmt'],
            custom_value_fn = lambda itm: itm['revenue_share_fmt'],
            list_path  = ("topn", f"topn_{group_var.lower()}")
            )

        # Customers & Avg Rev/Customer
        catalog = make_topn_kpi_card(
            kpis            = dynamic_kpis,
            metric_key      = metric_value,
            fmt_key         = f"{metric_value}_fmt",
            title           = "Catalog Size (% Sold)",
            icon            = "ph:vinyl-record-fill",
            tooltip         = "Total tracks in catalog and % catalog sold.",
            include_footer  = False,
            custom_label_fn = lambda idx, itm: itm["catalog_size_fmt"],
            custom_value_fn = lambda itm: itm["pct_catalog_sold_fmt"],
            list_path  = ("topn", f"topn_{group_var.lower()}")
        )

        return [top_groups, revenue_share, catalog]


    @app.callback(
        Output(f"download-{group_var}-csv", "data"),
        Input(f"btn-download-{group_var}", "n_clicks"),
        State(f"{group_var}-data-scroll", "rowData"),
        prevent_initial_call=True,
    )
    def download_group_csv_from_grid(
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
        filename = f"chinook_{group_var}_{today_str}.csv"

        log_msg(f"[CALLBACK:group] {group_var} Download processing.")

        return dcc.send_data_frame(df.to_csv, filename=filename, index=False)


    @app.callback(
        Output(f"btn-download-{group_var}", "disabled"),
        Output(f"btn-download-{group_var}", "children"),
        Output(f"btn-download-{group_var}", "style"),
        Input(f"{group_var}-data-scroll", "rowData"),
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
        Output(f"{group_var}-metric-plot", "figure"),
        Input(f"{group_var}-data-scroll", "rowData"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("theme-store", "data"),
        State("date-range-store", "data"),
        State("events-shared-fingerprint", "data"),
    )
    def render_group_stacked_bar_plot(
        group_df: Dict,
        metric_value: str,
        metric_label: str,
        theme_style: Dict[str, Any],
        date_range: Tuple[str, str],
        events_hash: str
    ) -> Any:
        """
        Generate and return a Group-based Stacked Bar Plotly figure.

        Parameters:
            group_df: Group KPI Data Frame (Dict stored format)
            metric_value: Column name in the TS DataFrame.
            metric_label: Axis label for the plot.
            theme_style: Dict containing Mantine theme data.
            date_range: Tuple of two 'YYYY-MM-DD' strings.
            events_hash: Filter fingerprint.
            group_var:
            
        Returns:
            A Plotly Figure object.
        """
        if not events_hash or not group_df:
            raise PreventUpdate

        log_msg(f"[CALLBACK:group] Updating {group_var} Plot.")

        start_date = pd.to_datetime(date_range[0]).to_period("M").start_time.date()
        end_date   = pd.to_datetime(date_range[1]).to_period("M").end_time.date()
        date_range=[start_date,end_date]

        group_df = pd.DataFrame.from_dict(group_df)

        log_msg(
            f"    [CALLBACK:group] Read in {group_var} df with {len(group_df)} rows"
        )

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

        log_msg("   [CALLBACK:retention] Rendering Cohort plot.")

        fig = build_group_stacked_bar(
            group_df, 
            metric = metric_dict, 
            group_var = group_var, 
            theme=theme_info, 
            max_n=20
        )

        return fig