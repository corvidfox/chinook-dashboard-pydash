# pages/coming_soon.py

from dash import html
import dash_mantine_components as dmc

def layout():
    return dmc.Center([
        dmc.Stack([
            dmc.Title("Coming Soon 🚧", order=2),
            dmc.Text("This section is under construction. Check back soon!", size="md", ta="center", c="dimmed"),
        ], align="center")
    ], style={"height": "80vh"})
