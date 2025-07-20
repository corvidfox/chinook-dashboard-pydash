# app.py
from dash import html, Dash, Input, State, Output, clientside_callback, dcc, ctx
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from config import DEFAULT_COLORSCHEME, get_mantine_theme
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date
from components.sidebar import make_sidebar
from components import filters
from layout import make_layout
from pages import overview, coming_soon
from dash.exceptions import PreventUpdate

FILTER_META = get_filter_metadata()
SUMMARY_DF = get_static_summary()
LAST_UPDATED = get_last_commit_date()
INITIAL_NAVBAR_STATE = {"collapsed": {"mobile": False, "desktop": False}}

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

filter_components = html.Div([
    filters.date_filter(FILTER_META),
    filters.country_filter(FILTER_META),
    filters.genre_filter(FILTER_META),
    filters.artist_filter(FILTER_META),
    filters.metric_filter(),
    filters.clear_button(),
], style={"display": "none"})

def serve_layout():
    return dmc.MantineProvider(
        id="mantine-provider",
        theme=get_mantine_theme(DEFAULT_COLORSCHEME),
        withCssVariables=True,
        defaultColorScheme="auto",
        children=[
            html.Div([
                dcc.Location(id="url", refresh=False),
                dcc.Interval(id="theme-init-trigger", interval=10, max_intervals=1, disabled=False),
                dcc.Store(id="current-page", data="/"),
                dcc.Store(id="theme-store", data=None),
                dcc.Store(id="grid-theme-store", data="ag-theme-alpine"),
                dcc.Store(id="preferred-dark-mode", data=False),
                dcc.Store(id="navbar-state", data=INITIAL_NAVBAR_STATE),
                dcc.Store(id="viewport-store", data={"width": 1024}),
                html.Div(id="viewport-trigger", style={"display": "none"}),
                html.Div([
                    make_layout(FILTER_META, SUMMARY_DF, LAST_UPDATED, INITIAL_NAVBAR_STATE, DEFAULT_COLORSCHEME, filter_components, "/")
                    ], id="main-layout"
                )
            ])
        ]
    )

app.layout = serve_layout

@app.callback(
    Output("page-content", "children"),
    Output("current-page", "data"),
    Input("main-tabs", "value"),
    State("theme-store", "data"),
    State("filter-date", "value"),
    State("filter-country", "value"),
    State("filter-genre", "value"),
    State("filter-artist", "value"),
    State("filter-metric", "value"),
)
def render_page(tab_value, theme_data, date_range, country, genre, artist, metric):
    filters = {
        "date": date_range,
        "country": country,
        "genre": genre,
        "artist": artist,
        "metric": metric,
    }

    if tab_value == "/":
        layout = overview.layout()
    elif tab_value == "/sales":
        layout = coming_soon.layout()
    else:
        layout = html.Div("404 Page Not Found")

    return layout, tab_value

@app.callback(
    Output("url", "pathname"),
    Input("main-tabs", "value"),
    prevent_initial_call=True
)
def update_url_from_tabs(tab_value):
    return tab_value

# Toggle navbar
@app.callback(
    Output("navbar-state", "data"),
    Input("burger", "opened"),
    State("navbar-state", "data")
)
def toggle_navbar(opened, state):
    return {"collapsed": {"mobile": not opened, "desktop": not opened}}

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
    scheme = theme_data["color_scheme"] if theme_data and "color_scheme" in theme_data else DEFAULT_COLORSCHEME
    return make_sidebar(
        scheme,
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

# Updates Layout
@app.callback(
    Output("main-layout", "children"),
    Input("navbar-state", "data"),
    Input("theme-store", "data"),
    Input("theme-init-trigger", "n_intervals"),
    State("current-page", "data")  # <- grab current page!
)
def update_layout(navbar_state, theme_data, _, current_page):
    if not theme_data or "color_scheme" not in theme_data:
        raise PreventUpdate

    scheme = theme_data["color_scheme"]
    return make_layout(
        FILTER_META,
        SUMMARY_DF,
        LAST_UPDATED,
        navbar_state,
        scheme,
        filter_components,
        active_tab=current_page  # <- pass tab state
    )

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

@app.callback(
    Output("grid-theme-store", "data"),
    Input("theme-store", "data")
)
def sync_aggrid_theme(theme_data):
    scheme = theme_data.get("color_scheme") if theme_data else DEFAULT_COLORSCHEME
    return "ag-theme-alpine-dark" if scheme == "dark" else "ag-theme-alpine"

@app.callback(
    Output("static-summary-table", "className"),
    Input("grid-theme-store", "data")
)
def update_sidebar_aggrid_class(theme_class):
    return theme_class

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

overview.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
