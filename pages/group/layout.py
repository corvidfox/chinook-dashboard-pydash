"""
Group Panel Layout
"""

from dash import html, dcc
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def layout(group_var:str):
    return html.Div([
        # KPI Cards
        html.Div(
            [
                dcc.Loading(
                    children = dmc.SimpleGrid(
                        cols={"base": 1, "sm": 3, "lg": 3},
                        spacing="lg",
                        children = [],
                        id = f"{group_var}-kpi-cards"
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
        dmc.Space(h=10),
        dmc.Title("Interactive Plot", order = 4, ta = "center"),
        dmc.Space(h=10),
        
        dmc.Paper([
            dcc.Loading(
                dcc.Graph(
                    id=f"{group_var}-metric-plot", 
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
        dmc.Space(h=10),
        dmc.Title("Scrollable Data Table", order = 4, ta="center"),
        dmc.Space(h=10),

        dag.AgGrid(
            id=f"{group_var}-data-scroll",
            columnDefs=[], rowData=[],
            style={"width": "100%", "height": "200px"},
            dashGridOptions={"rowHeight": 28},
        ),
        # Mantine Download button
        dmc.Group([
            # Mantine Download button
            dmc.Button(
                "Download CSV",
                id=f"btn-download-{group_var}",
                fullWidth=True,
                disabled = False,
                style = {},
                leftSection=DashIconify(icon="solar:download-broken")
            ),
            # Hidden download target
            dcc.Download(id=f"download-{group_var}-csv"),
        ])
    ])
