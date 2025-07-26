"""
Time Series Layout
"""

from dash import html, dcc
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash_iconify import DashIconify

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
        # KPI Cards
        html.Div(
            dmc.SimpleGrid(
                cols={"base": 1, "sm": 3, "lg": 3},
                spacing="lg",
                children=[],
                id = "ts-kpi-cards"
            ),
        style={"padding": "1rem"}
        ),

        dmc.Title("Plot will eventually go here", order = 5),
        dmc.Space(h=20),
        dmc.Title("Scrollable Data Table", order = 4, ta="center"),
        dag.AgGrid(
            id="ts-data-scroll",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "200px"},
            dashGridOptions={"rowHeight": 28},
        ),
        # Mantine Download button
        dmc.Group([
            # Mantine Download button
            dmc.Button(
                "Download CSV",
                id="btn-download-ts",
                fullWidth=True,
                disabled = False,
                style = {},
                leftSection=DashIconify(icon="solar:download-broken")
            ),
            # Hidden download target
            dcc.Download(id="download-ts-csv"),
        ])
    ])


"""        
        dmc.Card(
        children=[
            dmc.CardSection(
                dmc.Group([DashIconify(icon="mdi:chart-line"), dmc.Text("words")], gap="xs", align="center"),
                className="kpi-card-header"),
            dmc.CardSection(dmc.Text("No data available.", ta="center"), className="kpi-card-body")
            ],
        className="kpi-card",
        shadow="sm",
        radius="md",
        withBorder=True
    ),
"""