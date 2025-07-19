# app.py
from dash import Dash, Input, Output, clientside_callback
import dash_bootstrap_components as dbc
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date
from layout import make_layout
from pages import overview, coming_soon

FILTER_META = get_filter_metadata()
SUMMARY_DF = get_static_summary()
LAST_UPDATED = get_last_commit_date()


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

app.layout = make_layout(FILTER_META, SUMMARY_DF, LAST_UPDATED)

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

# Detect OS/browser light/dark mode preference once
clientside_callback(
    """() => window.matchMedia("(prefers-color-scheme: dark)").matches""",
    Output("preferred-dark-mode", "data"),
    Input("theme-init-trigger", "n_clicks"),
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

if __name__ == "__main__":
    app.run(debug=True)
