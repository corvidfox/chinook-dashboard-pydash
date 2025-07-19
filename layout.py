# layout.py
from dash import html, dcc
import dash_mantine_components as dmc
from components.sidebar import make_sidebar
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeSwitchAIO

def make_layout(color_scheme, navbar_config, page_content,pathname):
    return dmc.MantineProvider(
        theme={"colorScheme": color_scheme},
        children=[
            dcc.Location(id="url"),

            dmc.AppShell(
                id = "appshell",
                padding="md",
                header={"height": 60},
                navbar={"width": 260, "breakpoint": "sm", "collapsed": navbar_config["collapsed"]},
                children=[
                    dmc.AppShellHeader(
                        dmc.Group(
                        justify="space-between",
                        align="center",
                        px="md",
                        py="sm",
                        style={"height": 60},
                        children=[
                            dmc.Burger(id = "burger", size = "sm", opened=not navbar_config["collapsed"]["mobile"]),
                            dmc.Text("Chinook BI Dashboard", fw=700, fz="lg"),
                            #ThemeSwitchAIO(aio_id="theme", themes=[dbc.themes.COSMO, dbc.themes.SLATE])
                        ]
                        )
                    ),
                    dmc.AppShellNavbar(make_sidebar(), id = "navbar"),
                    dmc.AppShellMain([
                        dmc.Tabs(
                            id="main-tabs",
                            value=pathname,
                            children=[
                                dmc.TabsList([
                                    dmc.TabsTab("Overview", value="/"),
                                    dmc.TabsTab("Sales", value="/sales"),
                                    # Add more tabs here as we go...
                                ])
                            ],
                            mb="lg"
                        ),
                        html.Div(id="page-content", children=page_content)
                    ])
                ]
            )
        ]
    )
