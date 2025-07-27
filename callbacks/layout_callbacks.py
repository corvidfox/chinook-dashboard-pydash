"""
Layout rendering callbacks for the Chinook dashboard.
Handles dynamic layout re-assembly triggered by theme changes,
navbar state updates, or initial hydration events.
"""

from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from services.logging_utils import log_msg
from components.layout import make_layout
from services.metadata import (
    get_filter_metadata, 
    get_static_summary, 
    get_last_commit_date
)
from components import filters
from config import get_mantine_theme

# Pre-load metadata and static content for layout construction
FILTER_META = get_filter_metadata()
SUMMARY_DF = get_static_summary()
LAST_UPDATED = get_last_commit_date()
FILTER_COMPONENTS = filters.make_filter_block(FILTER_META)

def register_callbacks(app):
    @app.callback(
    Output("page-content-overlay", "visible"),
    Input("page-content-loading", "data")
    )
    def show_page_overlay(is_loading):
        return is_loading

    @app.callback(
        Output("main-layout", "children"),
        Input("theme-init-trigger", "n_intervals"),
        State("navbar-state", "data"),
        State("theme-store", "data"),
        State("current-page", "data"),
    )
    def update_layout(n_intervals, navbar_state, theme_data, current_page):
        if not theme_data or "color_scheme" not in theme_data:
            raise PreventUpdate

        scheme = theme_data["color_scheme"]
        log_msg(f"[CALLBACK:layout] Layout rebuild → theme: {scheme}, tab: {current_page}")

        return make_layout(
                        FILTER_META, SUMMARY_DF, LAST_UPDATED,
                        navbar_state, scheme,
                        FILTER_COMPONENTS, current_page
                    )