"""
Chinook Dashboard Application Entry Point.

Initializes the Dash app, prepares layout, theme, and shared state,
and registers global + page-specific callbacks.
"""

from dash import Dash, html, dcc
import os
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from config import (
    DEFAULT_COLORSCHEME, 
    get_mantine_theme,
    DEFAULT_OFFSETS,
    DEFAULT_MAX_OFFSET
    )
from services.cache_config import cache
from services.db import get_connection
from services.logging_utils import log_msg
from services.metadata import (
   get_filter_metadata, 
    get_static_summary, 
    get_last_commit_date, 
    create_catalog_tables, 
    check_catalog_tables
    )

from components import filters
from services.sql_core import get_events_shared
from services.kpis.retention import get_retention_cohort_data
from services.kpis.shared import get_shared_kpis

# Start-Up Messages
log_msg("[APP] Starting Chinook dashboard")
env = os.getenv("DASH_ENV", "development").lower()
log_msg(f"[APP] Booting dashboard in {env} mode")

# Get connection, make genre/artist summary tables, and
# make initial filtered data table
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

# Initialize Cache
cache.init_app(
    server,
    config={
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT":  60 * 60, # One Hour
        "CACHE_THRESHOLD": 500, # Max number of items
    }
)

# Import Memoized Wrappers
from services.cached_funs import (
    get_retention_cohort_data_cached,
    get_shared_kpis_cached
)

# Materalize the "no-filter" invoices table, grab hash
initial_events_hash = get_events_shared(
    conn = conn,
    where_clauses=(),
    previous_hash=None,
)

# Static KPIs (Cohort data fetched under the hood)
static_bundle, static_kpis_hash = get_shared_kpis_cached(
    events_hash=initial_events_hash,
    date_range=tuple(FILTER_META["date_range"]),
    max_offset=DEFAULT_MAX_OFFSET,
    offsets=DEFAULT_OFFSETS
)

# Layout Wrapper
def serve_layout():
    return dmc.MantineProvider(
        id="mantine-provider",
        theme=get_mantine_theme(DEFAULT_COLORSCHEME),  # fallback
        withCssVariables=True,
        defaultColorScheme="auto",
        children=[
            html.Div([
                    # Routing Stores
                    dcc.Location(id="url", refresh=False),
                    dcc.Store(id="current-page", data="/"),

                    # Theme Stores
                    dcc.Interval(
                        id="theme-init-trigger", 
                        interval=10, 
                        max_intervals=1, 
                        disabled=False
                        ),
                    dcc.Store(id="preferred-dark-mode", data=False),
                    dcc.Store(id="theme-store", data=None),
                    dcc.Store(id="grid-theme-store", data="ag-theme-alpine"),
                    dcc.Store(id="navbar-state", data=INITIAL_NAVBAR_STATE),
                    dcc.Store(id="viewport-store", data={"width": 1024}),
                    dcc.Store(id="page-content-loading", data=True),

                    # Data Stores
                    dcc.Store(
                        id="events-shared-fingerprint", 
                        data=initial_events_hash
                        ),
                    dcc.Store(
                        id="date-range-store", 
                        storage_type = "session",
                        data=FILTER_META["date_range"]
                        ),
                    dcc.Store(id="max-offset-store", data=DEFAULT_MAX_OFFSET),
                    dcc.Store(
                        id="metric-store",
                        storage_type = "session", 
                        data=FILTER_META["metrics"]
                        ),
                    dcc.Store(
                        id="metric-label-store",
                        storage_type = "session", 
                        data=[m["label"] for m in FILTER_META["metrics"]]
                        ),
                    dcc.Store(id="offsets-store", data=DEFAULT_OFFSETS),
                    dcc.Store(id="retention-cohort-data", data=[]),
                    dcc.Store(id="cohort-fingerprint", data=""),
                    dcc.Store(id="static-kpis", data=static_bundle),
                    dcc.Store(id="kpis-fingerprint", data=static_kpis_hash),

                    # Dummy elements to set off triggered initialization events
                    html.Div(id="viewport-trigger", style={"display": "none"}),
                    html.Div(
                        id="dark-mode-log-trigger", 
                        style={"display": "none"}
                        ),
                    dmc.Switch(
                        id={"type":"theme-switch", "role":"init"}, 
                        style={"display": "none"}
                        ),

                    # Main Layout Entry Placeholder
                    html.Div(id="main-layout")
                ])
        ]
    )

app.layout = html.Div(
    id = "shell", 
    className = "nav-open", 
    children=[serve_layout()]
    )

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

# Import Pages 
from pages import timeseries, overview, coming_soon

# Page-Specific Callback Registration
overview.register_callbacks(app)
timeseries.register_callbacks(app)

log_msg("[APP] Registered all page-specific callbacks successfully")

# Run Server
if __name__ == "__main__":
    app.run(debug=True)
