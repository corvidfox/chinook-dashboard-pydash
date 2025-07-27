"""
Routing and page rendering callbacks for the Chinook dashboard.
Handles synchronization between tab selection, URL path, and active page view.
"""

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
from services.logging_utils import log_msg

from pages import timeseries, geo, overview, coming_soon

# Page map for routing tabs to layouts
PAGE_MAP = {
    "/": timeseries.layout,
    "/geo": geo.layout,
    "/by-genre": coming_soon.layout,
    "/by-artist": coming_soon.layout,
    "/retention": coming_soon.layout,
    "/insights": coming_soon.layout,
    "/debug": overview.layout,
}

def register_callbacks(app):
    @app.callback(
        Output("page-content", "children"),
        Output("current-page", "data"),
        Output("page-content-loading", "data"),
        Input("main-tabs", "value"),
    )
    def render_page(
        tab_value
        ):
        if not tab_value:
            raise PreventUpdate

        if tab_value not in PAGE_MAP:
            log_msg(
                f"     [CALLBACK:routing] Invalid tab route: {tab_value}", 
                level="warning"
                )

        log_msg(f"[CALLBACK:routing] Rendering page → {tab_value}")

        layout_func = PAGE_MAP.get(
            tab_value, 
            lambda **kwargs: html.Div("404")
            )
        
        content = layout_func()
        return content, tab_value, False

    @app.callback(
        Output("url", "pathname"),
        Input("main-tabs", "value"),
        prevent_initial_call=True
    )
    def update_url_from_tabs(tab_value):
        """
        Syncs tab selection with browser URL.
        """
        log_msg(
            f"[CALLBACK:routing] URL updated from tab selection → {tab_value}"
            )
        return tab_value
