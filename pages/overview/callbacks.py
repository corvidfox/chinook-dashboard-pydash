import json
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate
import pandas as pd

from pages.overview.helpers import (
    get_filtered_data,
    get_artist_catalog,
    get_genre_catalog
    )
from services.cached_funs import (
    get_shared_kpis_cached,
    get_retention_cohort_data_cached
)
from services.metadata import get_filter_metadata
from config import DEFAULT_OFFSETS, DEFAULT_MAX_OFFSET
from services.logging_utils import log_msg

FILTER_META = get_filter_metadata()
METRIC_MAP = {m["var_name"]: m["label"] for m in FILTER_META["metrics"]}

def register_callbacks(app):
    @app.callback(
        Output("filtered-events", "className"),
        Output("filtered-invoices", "className"),
        Output("cohort-table", "className"),
        Output("genre-catalog", "className"),
        Output("artist-catalog", "className"),
        Input("grid-theme-store", "data")
    )
    def update_aggrid_theme(grid_class):
        log_msg(f"[CALLBACK:overview] Updated grid theme → {grid_class}")
        return grid_class, grid_class, grid_class, grid_class, grid_class

    @app.callback(
        Output("date-range-display", "children"),
        Output("metric-display", "children"),
        Output("static-kpi-json", "children"),
        Output("dynamic-kpi-json", "children"),
        Output("filtered-events", "columnDefs"),
        Output("filtered-events", "rowData"),
        Output("filtered-invoices", "columnDefs"),
        Output("filtered-invoices", "rowData"),
        Output("cohort-table", "columnDefs"),
        Output("cohort-table", "rowData"),

        Output("genre-catalog", "columnDefs"),
        Output("genre-catalog", "rowData"),
        Output("artist-catalog", "columnDefs"),
        Output("artist-catalog", "rowData"),

        Input("events-shared-fingerprint", "data"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("date-range-store", "data"),
        State("max-offset-store", "data"),
        State("offsets-store", "data"),
        State("static-kpis", "data")
    )
    def update_overview(
        events_hash,
        dynamic_kpis,
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

        log_msg("[DEBUGGING] - Callback active.")

        dr_text = f"{date_range[0]}  →  {date_range[1]}"
        metric_text = f"Metric {metric_value}: {metric_label}"

        static_json = json.dumps(static_kpis, indent=2)
        dyn_json = json.dumps(dynamic_kpis, indent=2)

        events_df, invoices_df = get_filtered_data(date_range)

        event_coldefs = [{"field": c, "sortable": True, "filter": True} for c in events_df.columns]
        invoice_coldefs = [{"field": c, "sortable": True, "filter": True} for c in invoices_df.columns]

        cohort_df, cohort_hash = get_retention_cohort_data_cached(
            date_range=tuple(date_range),
            max_offset=max_offset or DEFAULT_MAX_OFFSET
        )
        cohort_coldefs = [{"field": c} for c in cohort_df.columns]
        cohort_data = cohort_df.to_dict("records")

        genre_df = get_genre_catalog()
        artist_df = get_artist_catalog()

        genre_coldefs = [{"field": c, "sortable": True, "filter": True} for c in genre_df.columns]
        artist_coldefs = [{"field": c, "sortable": True, "filter": True} for c in artist_df.columns]

        log_msg("[CALLBACK:overview] Overview dashboard data refreshed")
        log_msg(f"     [CALLBACK:overview] Events={len(events_df)}, Invoices={len(invoices_df)}, Genres={len(genre_df)}, Artists={len(artist_df)}")

        return (
            dr_text, metric_text, static_json, dyn_json,
            event_coldefs, events_df.to_dict("records"),
            invoice_coldefs, invoices_df.to_dict("records"),
            cohort_coldefs, cohort_data,
            genre_coldefs, genre_df.to_dict("records"),
            artist_coldefs, artist_df.to_dict("records")
        )

