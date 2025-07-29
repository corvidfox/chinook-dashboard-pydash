"""
callbacks.py

Defines and registers all Dash callbacks for the customer retention
dashboard module.

Callbacks include:
  - AG-Grid theme update
  - Customer Decay & Cohort Retention data table refreshes
  - KPI cards update
  - CSV downloads and button toggles
  - Metric plot renderings

Public API:
  - register_callbacks(app)
"""

from datetime import date
from typing import Any, Dict, List, Tuple

import pandas as pd
from dash import Dash, Input, Output, State, dcc
from dash.exceptions import PreventUpdate

from config import get_mantine_theme
from pages.retention.helpers import (
    get_retention_decay_data_cached,
    build_decay_plot,
    build_cohort_heatmap
)
from services.display_utils import make_static_kpi_card
from services.logging_utils import log_msg


__all__ = ["register_callbacks"]


def register_callbacks(app: Dash) -> None:
    """
    Wire up all Dash @app.callback functions for the retention page.

    Parameters:
        app: The Dash application instance to register callbacks on.

    Returns:
        None
    """
    @app.callback(
        Output("retention-cohort-data-scroll", "className"),
        Output("retention-decay-data-scroll", "className"),
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
        log_msg(f"[CALLBACK:retention] Updated grid theme: {grid_class}")
        return grid_class, grid_class


    @app.callback(
        Output("retention-cohort-data-scroll", "columnDefs"),
        Output("retention-cohort-data-scroll", "rowData"),
        Output("retention-decay-data-scroll", "columnDefs"),
        Output("retention-decay-data-scroll", "rowData"),
        Input("retention-cohort-data", "data"),
        Input("events-shared-fingerprint", "data"),
        Input("date-range-store", "data"),
        Input("max-offset-store", "data")
    )
    def update_retention(
        cohort_df_dict: Dict,
        events_hash: str,
        date_range: Tuple[str, str],
        max_offset: int
    ) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]], 
        List[Dict[str, Any]], List[Dict[str, Any]]
        ]:
        """
        Refresh the customer retention DataFrames and push to AG-Grids.

        Parameters:
            cohort_df_dict: Customer Cohort Retention Data (stored dict)
            events_hash: Unique fingerprint for current filters.
            date_range: Tuple of two 'YYYY-MM-DD' strings.
            max_offset (int): max month offset to include

        Returns:
            A tuple of (columnDefs, rowData) for each AG-Grid.
        """
        if not events_hash:
            raise PreventUpdate

        log_msg("[CALLBACK:retention] - Callback active.")

        cohort_df = pd.DataFrame.from_dict(cohort_df_dict)
        cohort_df_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in cohort_df.columns
            ]

        decay_df = get_retention_decay_data_cached(
            events_hash, date_range, max_offset
            )
        decay_df_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in decay_df.columns
            ]

        log_msg("[CALLBACK:retention] Retention dashboard data refreshed")
        log_msg(f"     [CALLBACK:retention] Decay Table Rows = {len(decay_df)}")
        log_msg(f"     [CALLBACK:retention] Decay Table Rows = {len(cohort_df)}")

        return (
            cohort_df_coldefs,
            cohort_df.to_dict("records"),
            decay_df_coldefs,
            decay_df.to_dict("records")
        )


    @app.callback(
        Output("retention-kpi-cards", "children"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data"),
    )
    def update_retention_kpis(
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
        log_msg("[CALLBACK:retention] Updating KPI cards.")
        
        # Declare content of cards
        overview_specs = [
        { "label": "Total Customers (% New)",
            "key_path": ["retention_kpis", "cust_line"],
            "fmt": True,
            "tooltip": "Total customers active within the current data subset, and % of which are new." },
        { "label": "Avg Lifespan (Full, Months)",
            "key_path": ["retention_kpis", "avg_life_mo_tot"],
            "fmt": True,
            "tooltip": "Average customer lifespan across full history, in months." },
        { "label": "Avg Lifespan (Subset, Months)",
            "key_path": ["retention_kpis", "avg_life_mo_win"],
            "fmt": True,
            "tooltip": "Average customer lifespan in the current data set, in months." }
        ]

        repeat_specs = [
        { "label": "Lifetime",
            "key_path": ["retention_kpis", "ret_any_line"],
            "fmt": True,
            "tooltip": "Number and % of repeat customers (lifetime)." },
        { "label": "Returning",
            "key_path": ["retention_kpis", "ret_return_line"],
            "fmt": True,
            "tooltip": "Number and % of returning repeat customers in the current data subset." },
        { "label": "New → Repeat Rate",
            "key_path": ["retention_kpis", "ret_conv_line"],
            "fmt": True,
            "tooltip": "Number and % of new customers in the current data subset who became repeating customers." },
        { "label": "1st → 2nd Gap (Lifetime, Days)",
            "key_path": ["retention_kpis", "med_gap_life"],
            "fmt": True,
            "tooltip": "Median days between first and second purchase in customer lifetime, days." }
        ]

        purchase_specs = [
        { "label": "Avg Gap (Subset, Days)",
            "key_path": ["retention_kpis", "avg_gap_window"],
            "fmt": True,
            "tooltip": "Average gap between purchases in the current data subset, in days." },
        { "label": "Avg Gap (Bounded, Days)",
            "key_path": ["retention_kpis", "avg_gap_bound"],
            "fmt": True,
            "tooltip": "Average gap between purchases including the most recent purchases before and/or after the subset range, in days." },
        { "label": "Top Cohort (3mo)",
            "key_path": ["retention_kpis", "top_cohort_line_3"],
            "fmt": True,
            "tooltip": "Best 3 month retention cohort and retention rate." },
        { "label": "Top Cohort (6mo)",
            "key_path": ["retention_kpis", "top_cohort_line_6"],
            "fmt": True,
            "tooltip": "Best 6 month retention cohort and retention rate." },
        { "label": "Top Cohort (9mo)",
            "key_path": ["retention_kpis", "top_cohort_line_9"],
            "fmt": True,
            "tooltip": "Best 9 month retention cohort and retention rate." }
        ]

        # Build cards with a single call each
        cards = [
        make_static_kpi_card(
            kpi_bundle=dynamic_kpis,
            specs=overview_specs,
            title="Customer Overview",
            icon="mdi:people-outline",
            tooltip="Customer count and average engagement lifespan."
        ),

        make_static_kpi_card(
            kpi_bundle=dynamic_kpis,
            specs=repeat_specs,
            title="Repeat Customer Behavior",
            icon="ic:baseline-loop",
            tooltip="Conversion from first-time to returning customers."
        ),

        make_static_kpi_card(
            kpi_bundle=dynamic_kpis,
            specs=purchase_specs,
            title="Purchase Tempo",
            icon="mdi:chart-line",
            tooltip="Average purchase spacing and cohort retention highlights."
        ),
        ]

        return cards
   
    
    @app.callback(
        Output("download-decay-csv", "data"),
        Input("btn-download-decay", "n_clicks"),
        State("retention-decay-data-scroll", "rowData"),
        prevent_initial_call=True,
    )
    def download_decay_csv_from_grid(
        n_clicks: int,
        row_data: List[Dict[str, Any]],
    ) -> Any:
        """
        Serialize the AG-Grid rowData to CSV and trigger download of decay data.

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
        filename = f"chinook_decay_{today_str}.csv"

        log_msg("[CALLBACK:retention] Decay download processing.")

        return dcc.send_data_frame(df.to_csv, filename=filename, index=False)


    @app.callback(
        Output("btn-download-decay", "disabled"),
        Output("btn-download-decay", "children"),
        Output("btn-download-decay", "style"),
        Input("retention-decay-data-scroll", "rowData"),
    )
    def toggle_decay_download_btn(
        row_data: List[Dict[str, Any]],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enable or disable the decay download button based on rowData presence.

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
        Output("download-cohort-csv", "data"),
        Input("btn-download-cohort", "n_clicks"),
        State("retention-cohort-data-scroll", "rowData"),
        prevent_initial_call=True,
    )
    def download_cohort_csv_from_grid(
        n_clicks: int,
        row_data: List[Dict[str, Any]],
    ) -> Any:
        """
        Serialize the AG-Grid rowData to CSV and trigger download of cohort data.

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
        filename = f"chinook_cohort_{today_str}.csv"

        log_msg("[CALLBACK:retention] Cohort download processing.")

        return dcc.send_data_frame(df.to_csv, filename=filename, index=False)


    @app.callback(
        Output("btn-download-cohort", "disabled"),
        Output("btn-download-cohort", "children"),
        Output("btn-download-cohort", "style"),
        Input("retention-cohort-data-scroll", "rowData"),
    )
    def toggle_cohort_download_btn(
        row_data: List[Dict[str, Any]],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enable or disable the cohort download button based on rowData presence.

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
        Output("retention-decay-plot", "figure"),
        Input("retention-decay-data-scroll", "rowData"),
        Input("theme-store", "data"),
        State("date-range-store", "data"),
        State("events-shared-fingerprint", "data"),
    )
    def render_decay_plot(
        decay_df: Dict,
        theme_style: Dict[str, Any],
        date_range: Tuple[str, str],
        events_hash: str,
    ) -> Any:
        """
        Generate and return a Retention Decay Plotly figure.

        Parameters:
            decay_df: Retention Decay DataFrame (Dict stored format)
            theme_style: Dict containing Mantine theme data.
            date_range: Tuple of two 'YYYY-MM-DD' strings.
            events_hash: Filter fingerprint.
            
        Returns:
            A Plotly Figure object.
        """
        if not events_hash or not decay_df:
            raise PreventUpdate

        log_msg("[CALLBACK:retention] Updating Decay Plot.")

        decay_df = pd.DataFrame.from_dict(decay_df)

        log_msg(f"    [CALLBACK:retention] Read in Decay DF with {len(decay_df)} rows")

        theme_data = get_mantine_theme(theme_style["color_scheme"])

        theme_info = {
            "plotlyTemplate": theme_data.get("plotlyTemplate", "plotly_white"),
            "fontFamily": theme_data.get("fontFamily", "Inter"),
            "primaryColor": theme_data.get("primaryColor", "indigo"),
        }

        log_msg("   [CALLBACK:retention] Rendering Decay plot.")

        fig = build_decay_plot(decay_df, theme_info)

        return fig
    

    @app.callback(
        Output("retention-cohort-plot", "figure"),
        Input("retention-cohort-data-scroll", "rowData"),
        Input("theme-store", "data"),
        State("date-range-store", "data"),
        State("events-shared-fingerprint", "data"),
    )
    def render_cohort_heatmap(
        cohort_df: Dict,
        theme_style: Dict[str, Any],
        date_range: Tuple[str, str],
        events_hash: str,
    ) -> Any:
        """
        Generate and return a Cohort Retention Heatmap Plotly figure.

        Parameters:
            cohort_df: Cohort Retention DataFrame (Dict stored format)
            theme_style: Dict containing Mantine theme data.
            date_range: Tuple of two 'YYYY-MM-DD' strings.
            events_hash: Filter fingerprint.
            
        Returns:
            A Plotly Figure object.
        """
        if not events_hash or not cohort_df:
            raise PreventUpdate

        log_msg("[CALLBACK:retention] Updating Cohort Plot.")

        cohort_df = pd.DataFrame.from_dict(cohort_df)

        log_msg(f"    [CALLBACK:retention] Read in Cohort DF with {len(cohort_df)} rows")

        theme_data = get_mantine_theme(theme_style["color_scheme"])

        theme_info = {
            "plotlyTemplate": theme_data.get("plotlyTemplate", "plotly_white"),
            "fontFamily": theme_data.get("fontFamily", "Inter"),
            "primaryColor": theme_data.get("primaryColor", "indigo"),
        }

        log_msg("   [CALLBACK:retention] Rendering Cohort plot.")

        fig = build_cohort_heatmap(cohort_df, theme_info)

        return fig