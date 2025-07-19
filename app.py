from dash import Dash, html, Input, Output, State, dcc
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeSwitchAIO
from config import THEMES, DBC_CSS, DEFAULT_COLORSCHEME
from layout import make_layout
from pages import overview, coming_soon

# Dynamically get the actual theme object
#theme_name = THEMES[DEFAULT_COLORSCHEME]
#bootstrap_theme = getattr(dbc.themes, theme_name)

PAGE_MAP = {
    "/": overview.layout(),
    "/sales": coming_soon.layout()  # replace with real sales later
}

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.COSMO, dbc.themes.SLATE, DBC_CSS],
    suppress_callback_exceptions=True
)

app.layout = html.Div([
    dcc.Location(id="url"),
    ThemeSwitchAIO(aio_id="theme", themes=list(THEMES.values())),
    dcc.Store(id="navbar-state", data={"collapsed": {"mobile": False, "desktop": False}}), 
    html.Div(id="main-layout")
])


@app.callback(
    Output("main-layout", "children"),
    Input("url", "pathname"),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
    Input("navbar-state", "data"),
)
def update_layout(pathname, theme_url, navbar_config):
    color_scheme = "dark" if theme_url == dbc.themes.SLATE else "light"
    page = PAGE_MAP.get(pathname, html.Div("404 - Page not found"))
    return make_layout(color_scheme, navbar_config, page, pathname)

@app.callback(
    Output("url", "pathname"),
    Input("main-tabs", "value")
)
def update_url_from_tab(tab_value):
    return tab_value

@app.callback(
    Output("navbar-state", "data"),
    Input("burger", "opened"),
)
def toggle_navbar(opened):
    return {"collapsed": {"mobile": not opened, "desktop": not opened}}


if __name__ == "__main__":
    app.run(debug=True)
