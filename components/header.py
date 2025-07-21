"""
Header layout for the Chinook dashboard.

Includes title, navbar toggle (burger), and theme switch control.
"""

import dash_mantine_components as dmc
from dash_iconify import DashIconify


def make_header(navbar_collapsed=False):
    """
    Builds the AppShellHeader with title, burger icon, and theme switch.

    Parameters:
        navbar_collapsed (bool): Whether the sidebar is currently collapsed.

    Returns:
        dmc.AppShellHeader
    """
    return dmc.AppShellHeader(
        dmc.Group(
            justify="space-between",
            align="center",
            px="md",
            py="sm",
            children=[
                dmc.Burger(id="burger", opened=not navbar_collapsed),
                dmc.Title("Chinook BI Dashboard", order=2),
                dmc.Switch(
                    id="theme-switch",
                    persistence=True,
                    offLabel=DashIconify(icon="radix-icons:sun",  width=15),
                    onLabel=DashIconify(icon="radix-icons:moon", width=15)
                )
            ]
        )
    )
