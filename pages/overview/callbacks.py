"""
Callbacks for overview tab — grid updates and theme application.
"""

from dash import Input, Output, callback, html
from pages.overview.helpers import get_filtered_data

def register_callbacks(app):
    @callback(
        Output("filtered-events", "className"),
        Output("filtered-invoices", "className"),
        Input("grid-theme-store", "data")
    )
    def update_aggrid_theme(grid_class):
        return grid_class, grid_class

    @callback(
        Output("filtered-events", "columnDefs"),
        Output("filtered-events", "rowData"),
        Output("filtered-invoices", "columnDefs"),
        Output("filtered-invoices", "rowData"),
        Output("filter-display", "children"),
        Input("filter-date", "value"),
        Input("filter-country", "value"),
        Input("filter-genre", "value"),
        Input("filter-artist", "value"),
        Input("filter-metric", "value"),
    )
    def update_overview(date_range, country, genre, artist, metric):
        filters = {
            "date": date_range,
            "country": country,
            "genre": genre,
            "artist": artist,
            "metric": metric,
        }

        events_df, invoices_df, where_clauses = get_filtered_data(filters)

        events_coldefs = [{"field": c, "sortable": True, "filter": True} for c in events_df.columns]
        invoice_coldefs = [{"field": c, "sortable": True, "filter": True} for c in invoices_df.columns]

        display = html.Div([
            html.H5("Active Filters"),
            html.Pre(str(filters)),
            html.H5("WHERE Clause (Event-Level)"),
            html.Pre(" AND\n".join(where_clauses) if where_clauses else "(no filters)")
        ])

        return (
            events_coldefs, events_df.to_dict("records"),
            invoice_coldefs, invoices_df.to_dict("records"),
            display
        )
