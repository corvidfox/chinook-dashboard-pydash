"""
helpers.py

Provides utility functions for generating Insights panel text elements.

Functions:
    - load_markdown

"""

import os
from dash import html
import dash_mantine_components as dmc
from typing import Dict, Any, Optional
from services.display_utils import safe_kpi_entry, safe_kpi_card

__all__ = [
    "load_markdown",
    "make_revenue_kpi_card"
]

def load_markdown(file_name):
    """
    Safely loads UTF-8 markdown file contents from assets/markdown directory.
    """
    md_path = os.path.join("assets", "markdown", file_name)
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def make_revenue_kpi_card(
        kpi_bundle: Dict[str, Any],
        title: str,
        icon: Optional[str] = None,
        tooltip: Optional[str] = None,
        ) -> dmc.Card:
    """
    Create a unified KPI card that displays:
    - Total Revenue (static value)
    - Top 3 revenue-generating markets (ranked list with bolded country names)
    - Top Genre by revenue (single list item, non-bolded)
    - Top Artist by revenue (single list item, non-bolded)

    All sections are rendered within a single card layout using the 
    `safe_kpi_card` helper.

    Parameters:
    ----------
    kpi_bundle : Dict[str, Any]
        A nested dictionary containing all KPI data structured under
        "metadata_kpis" for static values and "topn" paths for ranked lists.

    Returns:
    -------
    dmc.Card
        A fully rendered KPI card component with mixed static and dynamic 
        metrics.
    """
    def body_fn():
        entries = []

        # Static: Total Revenue
        total_rev = (
            kpi_bundle.get("metadata_kpis", {})
                      .get("revenue_total_fmt", "--")
        )
        entries.append(
            safe_kpi_entry(
                label="Total Revenue",
                value=total_rev,
                tooltip="Total revenue in data set."
            )
        )

        # Dynamic List: Top 3 Markets
        countries = (
            kpi_bundle.get("topn", {})
                      .get("topn_country", {})
                      .get("revenue", [])[:3]
        )
        if countries:
            list_items = [
                html.Li([
                    html.Strong(itm.get("group_val_fmt", "--")),
                    html.Span(f": {itm.get('revenue_fmt', '--')}")
                ])
                for itm in countries
            ]
            entries.append({
                "label": "Top Markets",
                "value": html.Ol(children=list_items, style={"paddingLeft": "1.2em", "margin": 0}),
                "tooltip": "Top revenue-producing countries, sorted by revenue."
            })

        # Top Genre
        genres = (
            kpi_bundle.get("topn", {})
                      .get("topn_genre", {})
                      .get("revenue", [])[:1]
        )
        if genres:
            g = genres[0]
            entries.append({
                "label": "Top Genre",
                "value": html.Ol([
                    html.Li(f"{g.get('group_val_fmt', '--')}: {g.get('revenue_fmt', '--')}")
                ], style={"paddingLeft": "1.2em", "margin": 0}),
                "tooltip": "Highest-grossing genre in the data set."
            })

        # Top Artist
        artists = (
            kpi_bundle.get("topn", {})
                      .get("topn_artist", {})
                      .get("revenue", [])[:1]
        )
        if artists:
            a = artists[0]
            entries.append({
                "label": "Top Artist",
                "value": html.Ol([
                    html.Li(f"{a.get('group_val_fmt', '--')}: {a.get('revenue_fmt', '--')}")
                ], style={"paddingLeft": "1.2em", "margin": 0}),
                tooltip: "Highest-grossing artist in the data set."
            })

        return entries

    return safe_kpi_card(
        kpi_bundle=kpi_bundle,
        body_fn=body_fn,
        title=title,
        icon=icon,
        tooltip=tooltip,
        list_style={"listStyleType": "none", "paddingLeft": 0}
    )
