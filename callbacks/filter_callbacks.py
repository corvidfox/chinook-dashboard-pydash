"""
Filter control callbacks for the Chinook dashboard.
Resets all persistent filter inputs to their default state.
Also synchronizes individual filter inputs to their corresponding session-level stores.
"""

import pandas as pd
from dash import Input, Output
from dash.exceptions import PreventUpdate
from services.logging_utils import log_msg
from services.metadata import get_filter_metadata

FILTER_META = get_filter_metadata()
log_msg("[CALLBACK:filter] Loaded static filter metadata for defaults")


def register_callbacks(app):
    # Reset all filter inputs to default values
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
        log_msg("[CALLBACK:filter] Clear button clicked — filters reset to defaults")
        log_msg(f"     [CALLBACK:filter] Default date range: {FILTER_META['date_range']}, metric: revenue")

        return (
            [FILTER_META["date_range"][0], FILTER_META["date_range"][1]],
            [],  # Country
            [],  # Genre
            [],  # Artist
            "revenue"  # Metric
        )

    # Sync date range filter to store
    @app.callback(
        Output("date-range-store", "data"),
        Input("filter-date", "value"),
        prevent_initial_call=True
    )
    def sync_date_range(value):
        if not value or len(value) != 2 or any(v is None for v in value):
            raise PreventUpdate

        # Safely convert to datetime and round to full month
        try:
            start_dt = pd.to_datetime(value[0]).replace(day=1)
            end_dt = pd.to_datetime(value[1]).replace(day=1) + pd.offsets.MonthEnd(0)

            rounded_dates = [
                start_dt.strftime("%Y-%m-%d"),
                end_dt.strftime("%Y-%m-%d")
            ]

            log_msg(f"[CALLBACK:filter] Synced date-range-store: {rounded_dates}")
            return rounded_dates

        except Exception as e:
            log_msg(f"[CALLBACK ERROR]: {e}")
            raise PreventUpdate


    # Sync metric filter to store
    @app.callback(
        Output("metric-store", "data"),
        Output("metric-label-store", "data"),
        Input("filter-metric", "value"),
        prevent_initial_call=True
    )
    def sync_metric(value):
        if not value:
            raise PreventUpdate
        METRIC_MAP = {m["var_name"]: m["label"] for m in FILTER_META["metrics"]}
        label = METRIC_MAP.get(value, value)

        log_msg(f"[CALLBACK:filter] Synced metric-store: {value}")
        return value, label

    # Optionally: Add similar callbacks for country, genre, or artist if you want to store those too
