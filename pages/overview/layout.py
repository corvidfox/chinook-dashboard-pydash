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
            style={"height": "300px"},
            className=""
        ),
        html.H4("Invoices Matching Filters"),
        dag.AgGrid(
            id="filtered-invoices",
            columnDefs=[], rowData=[],
            style={"height": "300px"},
            className=""
        )
    ])
