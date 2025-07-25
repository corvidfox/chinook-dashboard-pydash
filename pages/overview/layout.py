"""
Overview tab layout — used for debugging
"""


from dash import html
import dash_ag_grid as dag
import dash_mantine_components as dmc

def layout(
    events_hash=None,
    date_range=None,
    max_offset=None,
    metric_val=None,
    metric_label=None,
    offsets=None,
    cohort_hash=None,
    cohort_data=None,
    kpis_hash=None,
    kpis_store=None
    ):
    return html.Div([

        html.H4("Date Range"),
        html.Div(id="date-range-display"),

        html.H4("Metric Active"),
        html.Div(id="metric-display"),

        html.H4("Static KPIs (initial build)"),
        dmc.Code(id="static-kpi-json", block = True, children=[], style={"whiteSpace": "pre-wrap", "maxHeight": "300px", "overflowY": "auto"}),

        html.H4("Dynamic KPIs (recomputed)"),
        dmc.Code(id="dynamic-kpi-json", block = True, children=[], style={"whiteSpace": "pre-wrap","maxHeight": "300px", "overflowY": "auto"}),

        html.H4("Filtered Events"),
        dag.AgGrid(
            id="filtered-events",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "200px"},
            dashGridOptions={"rowHeight": 28},
        ),

        html.H4("Filtered Invoices"),
        dag.AgGrid(
            id="filtered-invoices",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "200px"},
            dashGridOptions={"rowHeight": 28},
        ),

        html.H4("Cohort Data"),
        dag.AgGrid(
            id="cohort-table",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "200px"},
            dashGridOptions={"rowHeight": 28},
        ),
        html.H4("Genre Catalog"), 
        dag.AgGrid( 
            id="genre-catalog", 
            columnDefs=[], 
            rowData=[], 
            style={"width": "100%", "height": "250px"}, 
            dashGridOptions={"rowHeight": 32}, 
            columnSize="responsiveSizeToFit", 
            className="" 
            ), 
        html.H4("Artist Catalog"), 
        dag.AgGrid( 
            id="artist-catalog", 
            columnDefs=[], 
            rowData=[], 
            style={"width": "100%", "height": "250px"}, 
            dashGridOptions={"rowHeight": 32}, 
            columnSize="responsiveSizeToFit", 
            className="" 
            )
    ])
