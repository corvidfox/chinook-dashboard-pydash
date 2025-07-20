# layout.py
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def make_layout(FILTER_META, SUMMARY_DF, LAST_UPDATED, navbar_state, scheme, filter_components, active_tab):
    return dmc.AppShell(
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
                        dmc.Burger(id="burger", opened=navbar_state["collapsed"]["mobile"] == False),
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
                    id="main-tabs", value=active_tab,
                    children=[
                        dmc.TabsList([
                            dmc.TabsTab("Overview", value="/"),
                            dmc.TabsTab("Sales",    value="/sales"),
                        ])
                    ],
                    mb="lg"
                ),
                html.Div(id="page-content"),
                # Ensure filter components exist on load to avoid tantrums
                html.Div(filter_components, style={"display": "none"})
            ])
        ]
    )