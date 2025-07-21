"""
Theme control callbacks for the Chinook dashboard.
Handles light/dark mode detection, theme switching, and syncing AgGrid styling.
"""

from dash import Input, Output, clientside_callback
from config import DEFAULT_COLORSCHEME

def register_callbacks(app):
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
        return theme_class

    # Detect user's system preference for dark mode
    app.clientside_callback(
        """() => window.matchMedia("(prefers-color-scheme: dark)").matches""",
        Output("preferred-dark-mode", "data"),
        Input("theme-init-trigger", "n_intervals"),
    )

    # Master theme-store setter (switch override OR browser preference)
    app.clientside_callback(
        """
        (switchOn, prefersDark) => {
            const scheme = switchOn!==null
            ? (switchOn ? "dark" : "light")
            : (prefersDark ? "dark" : "light");
            document.documentElement.setAttribute("data-mantine-color-scheme", scheme);
            return { color_scheme: scheme };
        }
        """,
        Output("theme-store", "data"),
        Input("theme-switch", "checked"),
        Input("preferred-dark-mode", "data")
    )