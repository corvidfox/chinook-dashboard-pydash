"""
Customer Retention Panel Layout
"""

from dash import html, dcc
import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def layout():
    return html.Div([
        # KPI Cards
        html.Div(
            [
                dcc.Loading(
                    children = dmc.SimpleGrid(
                        cols={"base": 1, "sm": 3, "lg": 3},
                        spacing="lg",
                        children = [],
                        id = "retention-kpi-cards"
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

        dmc.Space(h=10),
        # Tabbed Data View
        dmc.Tabs(
            id="retention-tabs", 
            value="decay",
            children = [
                dmc.TabsList([
                        dmc.TabsTab("Retention Decay Curve", value = "decay"),
                        dmc.TabsTab("Cohort Retention Heatmap", value="cohort")
                ]),
                dmc.TabsPanel(
                    value = "decay",
                    children = [
                            dmc.Space(h=10),
                            dmc.Title(
                                "Interactive Plot", 
                                order = 4, 
                                ta = "center"
                                ),
                            dmc.Space(h=10),

                            dmc.Paper([
                                dcc.Loading(
                                    dcc.Graph(
                                        id="retention-decay-plot", 
                                        style={
                                            "height": "100%", 
                                            "width": "100%"
                                            }
                                    ),
                                    delay_hide = 400,
                                    custom_spinner = dmc.Skeleton(
                                        height = 200, 
                                        width = "100%", 
                                        radius="sm", 
                                        visible = True
                                    )
                                )
                                ], shadow="sm", p="md", radius="md"
                            ),

                            # Scrollable Data Table with Download Button
                            dmc.Space(h=10),
                            dmc.Title(
                                "Scrollable Data Table", 
                                order = 4, 
                                ta="center"
                                ),
                            dmc.Space(h=10),
                            
                            dag.AgGrid(
                                id="retention-decay-data-scroll",
                                columnDefs=[], rowData=[],
                                style={"width": "100%", "height": "200px"},
                                dashGridOptions={"rowHeight": 28},
                            ),
                            # Mantine Download button
                            dmc.Group([
                                # Mantine Download button
                                dmc.Button(
                                    "Download CSV",
                                    id="btn-download-decay",
                                    fullWidth=True,
                                    disabled = False,
                                    style = {},
                                    leftSection=DashIconify(
                                        icon="solar:download-broken"
                                        )
                                ),
                                # Hidden download target
                                dcc.Download(id="download-decay-csv")
                            ])
                    ]
                ),
                dmc.TabsPanel(
                    value = "cohort",
                    children = [

                            dmc.Space(h=10),                            
                            dmc.Title(
                                "Interactive Plot", 
                                order = 4, 
                                ta = "center"
                                ),
                            dmc.Space(h=10),

                            dmc.Paper([
                                dcc.Loading(
                                    dcc.Graph(
                                        id="retention-cohort-plot", 
                                        style={
                                            "height": "100%", 
                                            "width": "100%"
                                            }
                                    ),
                                    delay_hide = 400,
                                    custom_spinner = dmc.Skeleton(
                                        height = 200, 
                                        width = "100%", 
                                        radius="sm", 
                                        visible = True
                                    )
                                )
                                ], shadow="sm", p="md", radius="md"
                            ),

                            # Scrollable Data Table with Download Button
                            dmc.Space(h=10),
                            dmc.Title(
                                "Scrollable Data Table", 
                                order = 4, 
                                ta="center"
                                ),
                            dmc.Space(h=10),
                            
                            dag.AgGrid(
                                id="retention-cohort-data-scroll",
                                columnDefs=[], rowData=[],
                                style={"width": "100%", "height": "200px"},
                                dashGridOptions={"rowHeight": 28},
                            ),
                            # Mantine Download button
                            dmc.Group([
                                # Mantine Download button
                                dmc.Button(
                                    "Download CSV",
                                    id="btn-download-cohort",
                                    fullWidth=True,
                                    disabled = False,
                                    style = {},
                                    leftSection=DashIconify(
                                        icon="solar:download-broken"
                                        )
                                ),
                                # Hidden download target
                                dcc.Download(id="download-cohort-csv"),
                            ])
                    ]
                ),
            ]
        )
    ]
)
