# pages/sales/layout.py

from dash import html
import dash_mantine_components as dmc
import dash_ag_grid as dag

def layout():
    return html.Div([
        dmc.Title("Sales Data", order=3, mb="sm"),
        dmc.Alert("Sales dashboard is coming soon. You'll be able to filter and explore metrics here.", color="yellow", variant="light", mb="lg"),
        dag.AgGrid(
            id="table-sales",
            columnDefs=[{"field": "Feature", "sortable": False}],
            rowData=[{"Feature": "Data table coming soon"}, {"Feature": "Filters will be here"}, {"Feature": "Charts and KPIs inbound"}],
            style={"height": "300px", "width": "100%"}
        )
    ])
