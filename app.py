"""
Chinook Dashboard Application Entry Point.

Initializes the Dash app, prepares layout, theme, and shared state,
and registers global + page-specific callbacks.
"""

from dash import Dash, html, dcc
import os
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate

from config import DEFAULT_COLORSCHEME, get_mantine_theme
from services.db import get_connection
from services.logging_utils import log_msg
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date, create_catalog_tables, check_catalog_tables
from components import filters
from components.layout import make_layout
from components.sidebar import make_sidebar
from pages import overview, coming_soon

log_msg("[APP] Starting Chinook dashboard")

env = os.getenv("DASH_ENV", "development").lower()
log_msg(f"[APP] Booting dashboard in {env} mode")

# Get connection and make genre/artist summary tables
conn = get_connection()
create_catalog_tables(conn)
check_catalog_tables(conn)

# App Metadata & State Initialization
FILTER_META         = get_filter_metadata()
SUMMARY_DF          = get_static_summary()
LAST_UPDATED        = get_last_commit_date()
INITIAL_NAVBAR_STATE = {"collapsed": {"mobile": False, "desktop": False}}
FILTER_COMPONENTS   = filters.make_filter_block(FILTER_META)

# Dash App Initialization
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)
server = app.server

# Layout Wrapper
def serve_layout():
    return dmc.MantineProvider(
        id="mantine-provider",
        theme=get_mantine_theme(DEFAULT_COLORSCHEME),  # fallback
        withCssVariables=True,
        defaultColorScheme="auto",
        children=[
            html.Div([
                    # Routing & State Stores
                    dcc.Location(id="url", refresh=False),
                    dcc.Interval(id="theme-init-trigger", interval=10, max_intervals=1, disabled=False),
                    dcc.Store(id="current-page", data="/"),
                    dcc.Store(id="theme-store", data=None),
                    dcc.Store(id="grid-theme-store", data="ag-theme-alpine"),
                    dcc.Store(id="preferred-dark-mode", data=False),
                    dcc.Store(id="navbar-state", data=INITIAL_NAVBAR_STATE),
                    dcc.Store(id="viewport-store", data={"width": 1024}),
                    dcc.Store(id="events-shared-fingerprint", data=""),

                    html.Div(id="viewport-trigger", style={"display": "none"}),
                    html.Div(id="dark-mode-log-trigger", style={"display": "none"}),

                    # Dummy theme switch for load
                    dmc.Switch(id={"type":"theme-switch", "role":"init"}, style={"display": "none"}),

                    # Main Layout Entry Placeholder
                    html.Div(id="main-layout")
                ])
        ]
    )

app.layout = serve_layout

# Global Callback Registration
from callbacks.layout_callbacks import register_callbacks as register_layout_callbacks
from callbacks.theme_callbacks import register_callbacks as register_theme_callbacks
from callbacks.routing_callbacks import register_callbacks as register_routing_callbacks
from callbacks.sidebar_callbacks import register_callbacks as register_sidebar_callbacks
from callbacks.filter_callbacks import register_callbacks as register_filter_callbacks
from callbacks.data_callbacks import register_callbacks as register_data_callbacks

register_layout_callbacks(app)
register_theme_callbacks(app)
register_routing_callbacks(app)
register_sidebar_callbacks(app)
register_filter_callbacks(app)
register_data_callbacks(app)

log_msg("[APP] Registered all core callbacks successfully")


# Page-Specific Callbacks
overview.register_callbacks(app)

log_msg("[APP] Registered all page-specific callbacks successfully")

# Run Server
if __name__ == "__main__":
    app.run(debug=True)
