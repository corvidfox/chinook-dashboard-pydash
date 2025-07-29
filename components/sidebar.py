"""
Sidebar layout for the Chinook dashboard.

Includes filter controls, static metadata links, and summary KPI table.
"""

import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_iconify import DashIconify
from config import FONT_SIZES
from components import filters


columnDefs = [
    {
        "headerName": "Metric",
        "field": "Metric",
        "flex": 1,
        "minWidth": 120,
        "sortable": True,
        "filter": True,
        "wrapText": True,
        "autoHeight": True,
        "cellStyle": {
            "whiteSpace": "normal",
            "wordBreak": "break-word",
            "lineHeight": "1.3",
        }
    },
    {
        "headerName": "Value",
        "field": "Value",
        "flex": 1,
        "minWidth": 120,
        "sortable": True,
        "filter": True,
        "wrapText": True,
        "autoHeight": True,
        "cellStyle": {
            "whiteSpace": "normal",
            "wordBreak": "break-word",
            "lineHeight": "1.3",
        }
    }
]


def make_meta_row(
    icon_name: str,
    label: str = "",
    content: str = "",
    link_url: str = None,
    font_size: str = FONT_SIZES["SM"]
) -> dmc.Flex:
    """
    Creates a responsive metadata row with icon and optional link.

    Parameters:
        icon_name (str): Iconify name.
        label (str): Label text before content.
        content (str): Display text or link text.
        link_url (str): Optional external URL.
        font_size (str): Font size token.

    Returns:
        dmc.Flex: Metadata row element.
    """
    icon = DashIconify(icon=icon_name, style={"fontSize": font_size})

    text_block = (
        dmc.Text([
            f"{label} ",
            dmc.Anchor(content, href=link_url, target="_blank", style={"fontSize": font_size})
        ])
        if link_url else
        dmc.Text(f"{label} {content}", style={"fontSize": font_size})
    )

    return dmc.Flex(
        justify="start",
        align="center",
        gap=6,
        wrap="wrap",
        children=[icon, text_block]
    )


def make_sidebar(filter_meta, summary_df, last_updated):
    """
    Renders the full sidebar layout including filters, metadata, and summary table.

    Parameters:
        filter_meta (dict): Precomputed filter options.
        summary_df (pd.DataFrame): Aggregated summary metrics.
        last_updated (str): Last data refresh timestamp.

    Returns:
        dmc.ScrollArea: Sidebar layout component.
    """
    summary_table_grid = dag.AgGrid(
        id="static-summary-table",
        columnDefs=columnDefs,
        rowData=summary_df.to_dict("records"),
        defaultColDef={
            "resizable": True,
            "sortable": True,
            "filter": True,
        },
        dashGridOptions={"domLayout": "autoHeight"},
        className="",
        style={"width": "100%", "maxWidth": "100%"},
    )

    return dmc.ScrollArea(
        type="scroll",
        style={
            "height": "100vh",
            "paddingTop": "1rem",
            "paddingRight": "1rem",
            "paddingLeft": "1.2rem",
            "paddingBottom": "1rem",
        },
        children=[
            dmc.Stack(
                gap="sm",
                children=[
                    dmc.Title("Filters", order=3),
                    filters.make_filter_block(filter_meta),
                    dmc.Accordion(
                        value="about-data",
                        children=[
                            dmc.AccordionItem(
                                value="about-data",
                                children=[
                                    dmc.AccordionControl("About This Data"),
                                    dmc.AccordionPanel([
                                        dmc.Stack([
                                            make_meta_row("fa:pencil", "Created by", "Morrigan M.", "https://github.com/corvidfox"),
                                            make_meta_row("fa:github", "", "GitHub Repo", "https://github.com/corvidfox/chinook-dashboard-pydash"),
                                            make_meta_row("fa:link", "", "Chinook Dataset", "https://github.com/lerocha/chinook-database"),
                                            make_meta_row("fa:file", "", "Portfolio Post", "https://corvidfox.github.io/projects/posts/2025_bi_chinook.html"),
                                            make_meta_row("tdesign:calendar-2-filled", "Last updated:", last_updated),
                                        ], gap="xs", mb="md"),
                                        dmc.Divider(),
                                        dmc.Title("Dataset Overview:", order=5, mb=4),
                                        summary_table_grid
                                    ])
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )
