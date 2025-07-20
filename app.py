# app.py
from dash import html, Dash, Input, Output, clientside_callback, dcc, ctx
import dash_bootstrap_components as dbc
from config import DEFAULT_COLORSCHEME
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date
from components.sidebar import make_sidebar
from layout import make_layout
from pages import overview, coming_soon

FILTER_META = get_filter_metadata()
SUMMARY_DF = get_static_summary()
LAST_UPDATED = get_last_commit_date()
INITIAL_NAVBAR_STATE = {"collapsed": {"mobile": False, "desktop": False}}

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

app.layout = html.Div([
    # Hidden triggers & stores
    dcc.Location(id="url", refresh=False),
    dcc.Interval(id="theme-init-trigger", interval=10, max_intervals=1, disabled=False),
    dcc.Store(id="theme-store", data=None),
    dcc.Store(id="preferred-dark-mode", data=False),
    dcc.Store(id="navbar-state", data=INITIAL_NAVBAR_STATE),
    dcc.Store(id="viewport-store", data={"width": 1024}),
    html.Div(id="viewport-trigger", style={"display": "none"}),
    make_layout(FILTER_META, SUMMARY_DF, LAST_UPDATED, INITIAL_NAVBAR_STATE, DEFAULT_COLORSCHEME)
])

# Swap page content
PAGE_MAP = {"/": overview.layout(), "/sales": coming_soon.layout()}

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    return PAGE_MAP.get(pathname, "404")

# Toggle sidebar collapse
@app.callback(
    Output("navbar-state", "data"),
    Input("burger", "opened"),
)
def toggle_navbar(o): return {"collapsed": {"mobile": not o, "desktop": not o}}

@app.callback(
    Output("navbar", "collapsed"),
    Input("navbar-state", "data")
)
def sync_navbar(navbar_state):
    return navbar_state["collapsed"]["mobile"]

@app.callback(
    Output("navbar", "children"),
    Input("navbar-state", "data"),
    Input("theme-store", "data"),
)
def render_sidebar(nav_state, theme_data):
    return make_sidebar(
        theme_data["color_scheme"],
        FILTER_META,
        SUMMARY_DF,
        LAST_UPDATED
    )

@app.callback(
    Output("navbar", "style"),
    Input("navbar-state", "data")
)
def collapse_navbar(navbar_state):
    collapsed = navbar_state["collapsed"]["mobile"]
    return {
        "width": 0 if collapsed else 300,
        "overflow": "hidden",
        "transition": "width 0.3s ease",
        "backgroundColor": "var(--mantine-color-body)"
    }

@app.callback(
    Output("main-layout", "children"),
    Input("navbar-state", "data"),
    Input("theme-store", "data")
)
def update_layout(navbar_state, theme_data):
    return make_layout(
        FILTER_META,
        SUMMARY_DF,
        LAST_UPDATED,
        navbar_state,
        theme_data["color_scheme"]
    )

from dash import ctx  # to identify the triggered Input

@app.callback(
    Output("filter-date", "value"),
    Output("filter-country", "value"),
    Output("filter-genre", "value"),
    Output("filter-artist", "value"),
    Output("filter-metric", "value"),
    Input("clear-filters", "n_clicks"),
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    return (
        # Date Range
        [FILTER_META["date_range"][0], FILTER_META["date_range"][1]],
        # Country, Genre, Artist
        [],
        [],
        [],
        # Metric
        "revenue"  # metric
    )

# Detect OS/browser light/dark mode preference once
clientside_callback(
    """() => window.matchMedia("(prefers-color-scheme: dark)").matches""",
    Output("preferred-dark-mode", "data"),
    Input("theme-init-trigger", "n_intervals"),
)

# Master theme-store updater
clientside_callback(
    """
    (switchOn, prefersDark) => {
      const scheme = switchOn!==null
        ? (switchOn ? "dark" : "light")
        : (prefersDark ? "dark" : "light");
      document.documentElement.setAttribute("data-mantine-color-scheme", scheme);
      return { color_scheme: scheme };
    }
    """,
    Output("theme-store", "data"),
    Input("theme-switch", "checked"),
    Input("preferred-dark-mode", "data")
)

clientside_callback(
    """
    function(navbarState) {
        const collapsed = navbarState.collapsed;
        const shell = document.querySelector('[data-dash-is-loading="true"]');
        if (!shell) return;
        shell.setAttribute("data-navbar-collapsed", JSON.stringify(collapsed));
    }
    """,
    Output("viewport-trigger", "style"), 
    Input("navbar-state", "data")
)

if __name__ == "__main__":
    app.run(debug=True)
