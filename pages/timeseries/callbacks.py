import json
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate
import pandas as pd

from pages.timeseries.helpers import (
    get_ts_monthly_summary_cached
    )

from services.logging_utils import log_msg


def register_callbacks(app):
    @app.callback(
        Output("ts-data-scroll", "className"),
        Input("grid-theme-store", "data")
    )
    def update_aggrid_theme(grid_class):
        log_msg(f"[CALLBACK:overview] Updated grid theme → {grid_class}")
        return grid_class

    @app.callback(
        Output("ts-data-scroll", "columnDefs"),
        Output("ts-data-scroll", "rowData"),


        Input("events-shared-fingerprint", "data"),
        Input("kpis-fingerprint", "data"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("date-range-store", "data"),
        State("max-offset-store", "data"),
        State("offsets-store", "data"),
        State("static-kpis", "data")
    )
    def update_ts(
        events_hash,
        dynamic_kpi_hash,
        metric_value,
        metric_label,
        date_range,
        max_offset,
        offsets,
        static_kpis
        ):
        if not events_hash:
            raise PreventUpdate

        log_msg("[CALLBACK:timeseries] - Callback active.")

        ts_df = get_ts_monthly_summary_cached(events_hash, date_range)
        ts_df_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in ts_df.columns
            ]

        log_msg("[CALLBACK:timeseries] Time Series dashboard data refreshed")
        log_msg(f"     [CALLBACK:timeseries] Data Table Rows = {len(ts_df)}")

        return (
            ts_df_coldefs, ts_df.to_dict("records")
        )

