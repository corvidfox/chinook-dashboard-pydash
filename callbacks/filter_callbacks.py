"""
Filter control callbacks for the Chinook dashboard.
Resets all persistent filter inputs to their default state.
"""

from dash import Input, Output
from services.metadata import get_filter_metadata

FILTER_META = get_filter_metadata()

def register_callbacks(app):
    @app.callback(
        Output("filter-date", "value"),
        Output("filter-country", "value"),
        Output("filter-genre", "value"),
        Output("filter-artist", "value"),
        Output("filter-metric", "value"),
        Input("clear-filters", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_filters(n_clicks):
        """
        Resets all filters to initial default values when Clear button is clicked.
        """
        return (
            [FILTER_META["date_range"][0], FILTER_META["date_range"][1]],
            [],  # Country
            [],  # Genre
            [],  # Artist
            "revenue"  # Metric
        )
