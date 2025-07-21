"""
Overview tab layout — includes AgGrid tables and filter display block.
"""

from dash import html
import dash_ag_grid as dag

def layout():
    return html.Div([
        html.Div(id="filter-display"),
        html.H4("Filtered Invoice Triggers"),
        dag.AgGrid(
            id="filtered-events",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "250px"},
            dashGridOptions={"rowHeight": 32},
            columnSize="responsiveSizeToFit",
            className=""
        ),
        html.H4("Invoices Matching Filters"),
        dag.AgGrid(
            id="filtered-invoices",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "250px"},
            dashGridOptions={"rowHeight": 32},
            columnSize="responsiveSizeToFit",
            className=""
        ),
        html.H4("Genre Catalog"),
        dag.AgGrid(
            id="genre-catalog",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "250px"},
            dashGridOptions={"rowHeight": 32},
            columnSize="responsiveSizeToFit",
            className=""
        ),
        html.H4("Artist Catalog"),
        dag.AgGrid(
            id="artist-catalog",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "250px"},
            dashGridOptions={"rowHeight": 32},
            columnSize="responsiveSizeToFit",
            className=""
        )
    ]
)
