# pages/overview.py
from dash import html, Input, Output, callback
import dash_ag_grid as dag
from services.db import get_connection
from services.sql_utils import form_where_clause
import pandas as pd
from services.sql_queries import get_events_shared, get_invoices_details

def get_filtered_data(filters):
    conn = get_connection()

    # Events-level filters → invoice triggers
    clauses = form_where_clause(
        country=filters.get("country"),
        genre=filters.get("genre"),
        artist=filters.get("artist")
    )
    filtered_df = get_events_shared(conn, clauses)

    # Downstream invoice-level query
    invoice_ids = filtered_df["InvoiceId"].unique().tolist()
    invoices_df = get_invoices_details(conn, invoice_ids, filters.get("date"))

    return filtered_df, invoices_df, clauses

# This function returns a layout, which will be updated based on the global layout callback
def layout():
    return html.Div([
        html.Div(id="filter-display"),
        html.H4("Filtered Invoice Triggers"),
        dag.AgGrid(id="filtered-events", columnDefs=[], rowData=[], style={"height": "300px"}, className=""),

        html.H4("Invoices Matching Filters"),
        dag.AgGrid(id="filtered-invoices", columnDefs=[], rowData=[], style={"height": "300px"}, className="")
    ])


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

        filtered_df, invoices_df, where_clauses = get_filtered_data(filters)

        coldef_events = [{"field": c, "sortable": True, "filter": True} for c in filtered_df.columns]
        coldef_invoices = [{"field": c, "sortable": True, "filter": True} for c in invoices_df.columns]

        display = html.Div([
            html.H5("Active Filters"),
            html.Pre(str(filters)),
            html.H5("WHERE Clause (Event-Level)"),
            html.Pre(" AND\n".join(where_clauses) if where_clauses else "(no filters)")
        ])

        return (
            coldef_events, filtered_df.to_dict("records"),
            coldef_invoices, invoices_df.to_dict("records"),
            display
        )


