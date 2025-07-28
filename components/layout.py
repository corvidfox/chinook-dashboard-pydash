"""
Application shell layout for the Chinook dashboard.

Composes the AppShell with header, sidebar container, tabs, page content, and hidden filters.
"""

from dash import html
import dash_mantine_components as dmc
from components.header import make_header
from services.logging_utils import log_msg
from config import IS_DEV

tabs = [
    dmc.TabsTab("Trends Over Time", value="/"),
    dmc.TabsTab("Geographic Distribution", value="/geo"),
    dmc.TabsTab("Performance by Genre", value="/by-genre"),
    dmc.TabsTab("Performance by Artist", value="/by-artist"),
    dmc.TabsTab("Customer Retention", value="/retention"),
    dmc.TabsTab("Key Insights", value="/insights"),
]

if IS_DEV:
    tabs.append(dmc.TabsTab("Overview (Debug)", value="/debug"))

log_msg(f"[LAYOUT] - Loading {len(tabs)} tabs.")

def make_layout(filter_meta, summary_df, last_updated, navbar_state, scheme, filter_block, active_tab):
    """
    Builds the full application layout using Mantine AppShell.

    Parameters:
        filter_meta (dict): Filter options metadata.
        summary_df (pd.DataFrame): Summary table metrics.
        last_updated (str): Timestamp string.
        navbar_state (dict): Sidebar collapse state.
        scheme (str): Active color scheme ("light"/"dark").
        filter_block (Component): Hidden filter components.
        active_tab (str): Currently active page path.

    Returns:
        dmc.AppShell
    """
    return dmc.AppShell(
        padding="md",
        header={"height": 60},
        navbar={"width": 300, "breakpoint": "sm"},
        children=[
            make_header(navbar_collapsed=navbar_state["collapsed"]["mobile"], scheme = scheme),

            dmc.AppShellNavbar(id="navbar", children=[], style={}),

            dmc.AppShellMain([
                dmc.Tabs(
                    id="main-tabs",
                    value=active_tab,
                    children=[dmc.TabsList(tabs)],
                    mb="lg"
                ),
                dmc.LoadingOverlay(
                    id = "page-content-overlay",
                    visible = True,
                    overlayProps = {"radius": "sm", "blur": 2, "color": "blue", "size":"md"}
                ),
                html.Div(id="page-content"),
                html.Div(filter_block, style={"display": "none"})
            ], 
            id = "main-container"
            )
        ]
    )
