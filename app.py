"""
Chinook Dashboard Application Entry Point.

Initializes the Dash app, prepares layout, theme, and shared state,
and registers global + page-specific callbacks.
"""

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate

from config import DEFAULT_COLORSCHEME, get_mantine_theme
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date
from components import filters
from components.layout import make_layout
from components.sidebar import make_sidebar
from pages import overview, coming_soon

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

# Layout Wrapper
def serve_layout():
    return dmc.MantineProvider(
        id="mantine-provider",
        theme=get_mantine_theme(DEFAULT_COLORSCHEME),
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
                html.Div(id="viewport-trigger", style={"display": "none"}),

                # Main Layout Entry
                html.Div([
                    make_layout(
                        FILTER_META, SUMMARY_DF, LAST_UPDATED,
                        INITIAL_NAVBAR_STATE, DEFAULT_COLORSCHEME,
                        FILTER_COMPONENTS, active_tab="/"
                    )
                ], id="main-layout")
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

register_layout_callbacks(app)
register_theme_callbacks(app)
register_routing_callbacks(app)
register_sidebar_callbacks(app)
register_filter_callbacks(app)

# Page-Specific Callbacks
overview.register_callbacks(app)

# Run Server
if __name__ == "__main__":
    app.run(debug=True)
