"""
Time Series Panel Layout
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
            [
                dcc.Loading(
                    children = dmc.SimpleGrid(
                        cols={"base": 1, "sm": 3, "lg": 3},
                        spacing="lg",
                        children = [],
                        id = "ts-kpi-cards"
                    ),
                    delay_hide = 400,
                    custom_spinner = [
                        dmc.Skeleton(
                            height = 200, 
                            width = "33%", 
                            radius="sm", 
                            visible = True
                        ) for _ in range(3)
                    ]
                )
            ],
        style={"padding": "1rem"}
        ),

        # Plot
        dmc.Space(h=20),
        dmc.Title("Interactive Plot", order = 4, ta = "center"),
        dmc.Paper([
            dcc.Loading(
                dcc.Graph(
                    id="ts-metric-plot", 
                    style={"height": "100%", "width": "100%"}
                ),
                delay_hide = 400,
                custom_spinner = dmc.Skeleton(
                    height = 200, width = "100%", radius="sm", visible = True
                )
            )
            ], shadow="sm", p="md", radius="md"
        ),

        # Scrollable Data Table with Download Button
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
