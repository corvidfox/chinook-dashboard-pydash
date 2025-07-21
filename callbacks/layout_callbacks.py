"""
Layout rendering callbacks for the Chinook dashboard.
Handles dynamic layout re-assembly triggered by theme changes,
navbar state updates, or initial hydration events.
"""

from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from components.layout import make_layout
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date
from components import filters

# Pre-load metadata and static content for layout construction
FILTER_META = get_filter_metadata()
SUMMARY_DF = get_static_summary()
LAST_UPDATED = get_last_commit_date()

# Compose filter section for sidebar
filter_components = filters.make_filter_block(FILTER_META)

def register_callbacks(app):
    @app.callback(
        Output("main-layout", "children"),
        Input("navbar-state", "data"),
        Input("theme-store", "data"),
        Input("theme-init-trigger", "n_intervals"),
        State("current-page", "data")
    )
    def update_layout(navbar_state, theme_data, _, current_page):
        """
        Rebuilds the entire dashboard layout when theme changes,
        sidebar is collapsed/expanded, or hydration completes.

        Keeps the active tab and precomputed sidebar components intact.
        """
        if not theme_data or "color_scheme" not in theme_data:
            raise PreventUpdate

        scheme = theme_data["color_scheme"]

        return make_layout(
            FILTER_META,
            SUMMARY_DF,
            LAST_UPDATED,
            navbar_state,
            scheme,
            filter_components,
            active_tab=current_page
        )
