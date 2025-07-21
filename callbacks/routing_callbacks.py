"""
Routing and page rendering callbacks for the Chinook dashboard.
Handles synchronization between tab selection, URL path, and active page view.
"""

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
from services.logging_utils import log_msg

from pages import overview, coming_soon

# Page map for routing tabs to layouts
PAGE_MAP = {
    "/": overview.layout,
    "/time-series": coming_soon.layout,
    "/geo": coming_soon.layout,
    "/by-genre": coming_soon.layout,
    "/by-artist": coming_soon.layout,
    "/retention": coming_soon.layout,
    "/insights": coming_soon.layout,
}

def register_callbacks(app):
    @app.callback(
        Output("page-content", "children"),
        Output("current-page", "data"),
        Input("main-tabs", "value"),
        State("theme-store", "data"),
        State("filter-date", "value"),
        State("filter-country", "value"),
        State("filter-genre", "value"),
        State("filter-artist", "value"),
        State("filter-metric", "value"),
    )
    def render_page(tab_value, theme_data, date_range, country, genre, artist, metric):
        if not tab_value:
            raise PreventUpdate

        if tab_value not in PAGE_MAP:
            log_msg(f"     [CALLBACK:routing] Invalid tab route: {tab_value}", level="warning")

        filters = {
            "date": date_range,
            "country": country,
            "genre": genre,
            "artist": artist,
            "metric": metric,
        }

        log_msg(f"[CALLBACK:routing] Rendering page → {tab_value}")
        log_msg(f"     [CALLBACK:routing] Active filters → {filters}")

        layout_func = PAGE_MAP.get(tab_value, lambda: html.Div("404 Page Not Found"))
        return layout_func(), tab_value

    @app.callback(
        Output("url", "pathname"),
        Input("main-tabs", "value"),
        prevent_initial_call=True
    )
    def update_url_from_tabs(tab_value):
        """
        Syncs tab selection with browser URL.
        """
        log_msg(f"[CALLBACK:routing] URL updated from tab selection → {tab_value}")
        return tab_value
