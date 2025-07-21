"""
Routing and page rendering callbacks for the Chinook dashboard.
Handles synchronization between tab selection, URL path, and active page view.
"""

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
from pages import overview, coming_soon

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
        """
        Renders the current page content based on selected tab.
        Updates the active page store to maintain route on layout refresh.
        """
        if not tab_value:
            raise PreventUpdate

        filters = {
            "date": date_range,
            "country": country,
            "genre": genre,
            "artist": artist,
            "metric": metric,
        }

        if tab_value == "/":
            layout = overview.layout()
        elif tab_value == "/sales":
            layout = coming_soon.layout()
        else:
            layout = html.Div("404 Page Not Found")

        return layout, tab_value

    @app.callback(
        Output("url", "pathname"),
        Input("main-tabs", "value"),
        prevent_initial_call=True
    )
    def update_url_from_tabs(tab_value):
        """
        Syncs tab selection with browser URL.
        """
        return tab_value
