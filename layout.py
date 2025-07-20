# layout.py
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from config import get_mantine_theme
from components.sidebar import make_sidebar

def make_layout(filter_meta, summary_df, last_updated, navbar_state, color_scheme):
    theme_config = get_mantine_theme(color_scheme)

    return dmc.MantineProvider(
        id="mantine-provider",
        theme=theme_config,
        withCssVariables=True,
        defaultColorScheme=color_scheme,
        children=[
            # AppShell
            dmc.AppShell(
                padding="md",
                header={"height": 60},
                navbar={"width": 300, "breakpoint": "sm"},
                children=[

                    # Header
                    dmc.AppShellHeader(
                        dmc.Group(
                            justify="space-between",
                            align="center",
                            px="md", py="sm",
                            children=[
                                dmc.Burger(id="burger", opened=True),
                                # This <Text> now inherits var(--mantine-color-text)
                                dmc.Title("Chinook BI Dashboard", order=2),
                                dmc.Switch(
                                    id="theme-switch",
                                    persistence=True,
                                    offLabel=DashIconify(icon="radix-icons:sun",  width=15),
                                    onLabel=DashIconify(icon="radix-icons:moon", width=15)
                                )
                            ]
                        )
                    ),

                    # Sidebar
                    dmc.AppShellNavbar(id="navbar", children = [], style = {}),

                    # Main
                    dmc.AppShellMain([
                        dmc.Tabs(
                            id="main-tabs", value="/",
                            children=[
                                dmc.TabsList([
                                    dmc.TabsTab("Overview", value="/"),
                                    dmc.TabsTab("Sales",    value="/sales"),
                                ])
                            ],
                            mb="lg"
                        ),
                        html.Div(id="page-content")
                    ])
                ]
            )
        ]
    )
