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
        Output("page-content-loading", "data"),
        Input("main-tabs", "value"),
        State("events-shared-fingerprint", "data"),
        State("date-range-store",          "data"),
        State("max-offset-store",          "data"),
        State("metric-store",              "data"),
        State("metric-label-store",        "data"),
        State("offsets-store",             "data"),
        State("cohort-fingerprint",        "data"),
        State("retention-cohort-data",     "data"),
        State("kpis-fingerprint",          "data"),
        State("static-kpis",               "data"),
    )
    def render_page(
        tab_value,
        events_hash,
        date_range,
        max_offset,
        metric_val,
        metric_label,
        offsets,
        cohort_hash,
        cohort_data,
        kpis_hash,
        kpis_store
        ):
        if not tab_value:
            raise PreventUpdate

        if tab_value not in PAGE_MAP:
            log_msg(f"     [CALLBACK:routing] Invalid tab route: {tab_value}", level="warning")

        log_msg(f"[CALLBACK:routing] Rendering page → {tab_value}")

        layout_func = PAGE_MAP.get(
            tab_value, 
            lambda **kwargs: html.Div("404")
            )
        
        content = layout_func(
            events_hash=events_hash,
            date_range=date_range,
            max_offset=max_offset,
            metric_val=metric_val,
            metric_label=metric_label,
            offsets=offsets,
            cohort_hash=cohort_hash,
            cohort_data=cohort_data,
            kpis_hash=kpis_hash,
            kpis_store=kpis_store
        )
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
        log_msg(f"[CALLBACK:routing] URL updated from tab selection → {tab_value}")
        return tab_value
