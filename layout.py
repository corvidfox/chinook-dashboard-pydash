# layout.py
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from config import DEFAULT_COLORSCHEME, get_mantine_theme
from components.sidebar import make_sidebar

def make_layout(filter_meta, summary_df, last_updated):
    theme_config = get_mantine_theme(DEFAULT_COLORSCHEME)

    return dmc.MantineProvider(
        id="mantine-provider",
        theme=theme_config,
        children=[
            # Hidden triggers & stores
            dcc.Location(id="url", refresh=False),
            html.Button(id="theme-init-trigger", style={"display": "none"}),
            dcc.Store(id="theme-store", data={"color_scheme": DEFAULT_COLORSCHEME}),
            dcc.Store(id="preferred-dark-mode", data=False),
            dcc.Store(id="navbar-state", data={"collapsed": {"mobile": False, "desktop": False}}),
            dcc.Store(id="viewport-store", data={"width": 1024}),
            html.Div(id="viewport-trigger", style={"display": "none"}),

            # AppShell
            dmc.AppShell(
                padding="md",
                header={"height": 60},
                navbar={"width": 300, "breakpoint": "sm", "collapsed": True},
                children=[

                    # Header
                    dmc.AppShellHeader(
                        dmc.Group(
                            justify="space-between",
                            align="center",
                            px="md", py="sm",
                            children=[
                                dmc.Burger(id="burger"),
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
                    dmc.AppShellNavbar(make_sidebar(theme_config, filter_meta, summary_df, last_updated), id="navbar"),

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
