"""
data_callbacks.py

Shared data computation callbacks for the Chinook dashboard.
Handles fingerprint-aware reactivity for event-level filters.
Materializes filtered invoice table in DuckDB if data changes.

Responsibilities:
- Compute filtered invoice table using artist, genre, and country
- Store fingerprint hash to prevent unnecessary recomputation
- Materialize temporary DuckDB table: 'filtered_invoices'
"""

from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from services.logging_utils import log_msg
from services.db import get_connection
from services.sql_core import get_events_shared
from services.sql_filters import form_where_clause

# Register callbacks
def register_callbacks(app):
    @app.callback(
        Output("events-shared-fingerprint", "data"),
        Input("filter-country", "value"),
        Input("filter-genre", "value"),
        Input("filter-artist", "value"),
        State("events-shared-fingerprint", "data")
    )
    def update_filtered_events(country, genre, artist, previous_hash):
        """
        Updates filtered_invoices temp table in DuckDB if resulting data set changes.
        Stores fingerprint hash in dcc.Store to control downstream reactivity.
        """
        log_msg("[CALLBACK:data] Triggered update_filtered_events() from filters")
        log_msg(f"     [CALLBACK:data] Filter inputs → country={country}, genre={genre}, artist={artist}")

        # Generate SQL WHERE clause using filter inputs
        where_clauses = form_where_clause(
            country=country,
            genre=genre,
            artist=artist
        )

        log_msg(f"     [CALLBACK:data] WHERE clause → {where_clauses}")

        # Establish DuckDB connection
        conn = get_connection()

        # Get filtered invoice events and updated hash
        df, new_hash = get_events_shared(conn, where_clauses, previous_hash=previous_hash)

        if df is None:
            log_msg("     [CALLBACK:data] Data unchanged — skipping fingerprint update")
            raise PreventUpdate
        else:
            log_msg(f"     [CALLBACK:data] Filtered data updated → {len(df)} rows, hash={new_hash}")

        return new_hash
