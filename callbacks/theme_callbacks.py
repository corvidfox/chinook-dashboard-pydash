"""
Theme control callbacks for the Chinook dashboard.
Handles light/dark mode detection, theme switching, and syncing AgGrid styling.
"""

from dash import Input, Output, clientside_callback, ClientsideFunction, ALL
from dash.exceptions import PreventUpdate
from services.logging_utils import log_msg
from config import DEFAULT_COLORSCHEME, get_mantine_theme

def register_callbacks(app):
    # Update the theme scheme
    app.clientside_callback(
        ClientsideFunction(namespace="theme", function_name="setScheme"),
        Output("theme-store", "data"),
        # Trigger once on init, and again on every header theme-switch.checked change
        Input("theme-init-trigger", "n_intervals"),
        Input({"type": "theme-switch", "role": ALL}, "checked"),
    )

    # Update mantine provider
    @app.callback(
        Output("mantine-provider", "theme"),
        Input("theme-store", "data")
    )
    def _update_provider(theme_data):
        """
        Push theme updates to the mantine provider. 
        """
        if not theme_data or "color_scheme" not in theme_data:
            raise PreventUpdate
        return get_mantine_theme(theme_data["color_scheme"])

    # Sync AgGrid theme class with Mantine color scheme
    @app.callback(
        Output("grid-theme-store", "data"),
        Input("theme-store", "data")
    )
    def sync_aggrid_theme(theme_data):
        """
        Updates AgGrid theme className based on Mantine color scheme.
        """
        scheme = theme_data.get("color_scheme") if theme_data else DEFAULT_COLORSCHEME
        log_msg(f"[CALLBACK:theme] AgGrid theme synced → {scheme}")
        return "ag-theme-alpine-dark" if scheme == "dark" else "ag-theme-alpine"

    # Apply AgGrid className to the sidebar table
    @app.callback(
        Output("static-summary-table", "className"),
        Input("grid-theme-store", "data")
    )
    def update_sidebar_aggrid_class(theme_class):
        """
        Applies the active AgGrid theme class to the summary table.
        """
        log_msg(f"[CALLBACK:theme] Sidebar summary table styled with → {theme_class}")
        return theme_class

