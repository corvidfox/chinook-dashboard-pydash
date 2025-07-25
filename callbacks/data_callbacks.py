"""
Shared data computation callbacks for the Chinook dashboard.

- Updates filtered invoice table when filters change
- Computes and caches retention cohort data
- Computes and caches shared KPI bundles, including retention KPIs
"""

from dash import Input, Output, State
from dash.exceptions import PreventUpdate

import pandas as pd

from services.db import get_connection
from services.logging_utils import log_msg
from services.sql_core import get_events_shared
from services.sql_filters import form_where_clause
from services.cached_funs import (
    get_retention_cohort_data_cached,
    get_shared_kpis_cached
)


def register_callbacks(app):
    """
    Register Dash callbacks for data pipelines.

    Callbacks:
      - update_filtered_events
      - update_retention_cohort
      - update_retention_kpis
    """

    @app.callback(
        Output("events-shared-fingerprint", "data"),
        Input("filter-country",         "value"),
        Input("filter-genre",           "value"),
        Input("filter-artist",          "value"),
        State("events-shared-fingerprint", "data"),
    )
    def update_filtered_events(country, genre, artist, prev_hash):
        """
        Materialize or skip filtered_invoices in DuckDB.

        Triggers when any filter changes. Uses cached wrapper to
        avoid rerunning identical SQL.
        """
        log_msg("[CALLBACK:data] update_filtered_events() start")
        where_clauses = form_where_clause(
            country=country, genre=genre, artist=artist
        )
        log_msg(f"     Filters → {where_clauses}")

        new_hash = get_events_shared(
            conn = get_connection(),
            where_clauses=tuple(where_clauses), 
            previous_hash=prev_hash
        )

        if new_hash == prev_hash:
            log_msg("     No change in filtered data, skipping update")
            raise PreventUpdate

        log_msg(
            f"     Filtered data updated: new hash = {new_hash}"
        )
        return new_hash

    @app.callback(
        Output("retention-cohort-data", "data"),
        Output("cohort-fingerprint",       "data"),
        Input("events-shared-fingerprint", "data"),
        State("date-range-store",           "data"),
        State("max-offset-store",           "data"),
    )
    def update_retention_cohort(fingerprint, date_range, max_offset):
        """
        Compute or fetch cached cohort retention DataFrame.

        Triggers after filtered events update. Stores JSON records
        for downstream graph callbacks.
        """
        if not fingerprint:
            raise PreventUpdate

        log_msg("[CALLBACK:data] update_retention_cohort() start")
        df, cohort_hash = get_retention_cohort_data_cached(
            date_range=tuple(date_range), max_offset=max_offset
        )
        return df.to_dict("records"), cohort_hash

    @app.callback(
        Output("kpis-fingerprint",           "data"),
        Input("events-shared-fingerprint",   "data"),
        Input("cohort-fingerprint",           "data"),
        State("date-range-store",             "data"),
        State("max-offset-store",             "data"),
        State("offsets-store",                "data"),
    )
    def update_dynamic_kpis(
        events_hash, cohort_hash, date_range, max_offset, offsets
    ):
        """
        Compute or fetch cached shared KPIs.

        Triggers when filtered events or cohort data changes.
        """
        if not events_hash or not cohort_hash:
            raise PreventUpdate

        log_msg("[CALLBACK:data] update_kpis() start")

        bundle, kpi_hash = get_shared_kpis_cached(
            events_hash=events_hash,
            date_range=tuple(date_range),
            max_offset=max_offset,
            offsets=tuple(offsets),
        )
        return kpi_hash
