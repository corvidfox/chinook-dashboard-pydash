"""
Time Series Layout
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
        
        dmc.Title("KPI cards will eventually go here", order = 5),
        dmc.Title("Plot will eventually go here", order = 5),
        dmc.Title("Scrollable Data Table", order = 4),
        dag.AgGrid(
            id="ts-data-scroll",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "200px"},
            dashGridOptions={"rowHeight": 28},
        ),
        dmc.Title("Data download button will eventually go here.", order = 5),
    ])
