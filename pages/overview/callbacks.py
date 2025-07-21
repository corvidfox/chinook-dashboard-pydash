from dash import Input, Output, State, callback, html
from services.logging_utils import log_msg
from pages.overview.helpers import (
    get_filtered_data,
    get_genre_catalog,
    get_artist_catalog
)
from dash.exceptions import PreventUpdate

def register_callbacks(app):
    @callback(
        Output("filtered-events", "className"),
        Output("filtered-invoices", "className"),
        Output("genre-catalog", "className"),
        Output("artist-catalog", "className"),
        Input("grid-theme-store", "data")
    )
    def update_aggrid_theme(grid_class):
        log_msg(f"[CALLBACK:overview] Updated grid theme → {grid_class}")
        return grid_class, grid_class, grid_class, grid_class

    @callback(
        Output("filtered-events", "columnDefs"),
        Output("filtered-events", "rowData"),
        Output("filtered-invoices", "columnDefs"),
        Output("filtered-invoices", "rowData"),
        Output("genre-catalog", "columnDefs"),
        Output("genre-catalog", "rowData"),
        Output("artist-catalog", "columnDefs"),
        Output("artist-catalog", "rowData"),
        Output("filter-display", "children"),
        Input("events-shared-fingerprint", "data"),  # triggers data update
        State("filter-date", "value"),
        State("filter-country", "value"),
        State("filter-genre", "value"),
        State("filter-artist", "value"),
        State("filter-metric", "value"),
    )
    def update_overview(fingerprint, date_range, country, genre, artist, metric):
        if not fingerprint:
            raise PreventUpdate

        filters = {
            "date": date_range,
            "country": country,
            "genre": genre,
            "artist": artist,
            "metric": metric,
        }

        events_df, invoices_df = get_filtered_data(date_range)

        event_coldefs = [{"field": c, "sortable": True, "filter": True} for c in events_df.columns]
        invoice_coldefs = [{"field": c, "sortable": True, "filter": True} for c in invoices_df.columns]

        display = html.Div([
            html.H5("Active Filters"),
            html.Pre(str(filters)),
            html.H5("Fingerprint Hash"),
            html.Pre(fingerprint if fingerprint else "(none)")
        ])

        genre_df = get_genre_catalog()
        artist_df = get_artist_catalog()

        genre_coldefs = [{"field": c, "sortable": True, "filter": True} for c in genre_df.columns]
        artist_coldefs = [{"field": c, "sortable": True, "filter": True} for c in artist_df.columns]

        log_msg("[CALLBACK:overview] Overview dashboard data refreshed")
        log_msg(f"     [CALLBACK:overview] Events={len(events_df)}, Invoices={len(invoices_df)}, Genres={len(genre_df)}, Artists={len(artist_df)}")
        log_msg(f"     [CALLBACK:overview] Fingerprint: {fingerprint}")

        return (
            event_coldefs, events_df.to_dict("records"),
            invoice_coldefs, invoices_df.to_dict("records"),
            genre_coldefs, genre_df.to_dict("records"),
            artist_coldefs, artist_df.to_dict("records"),
            display
        )

