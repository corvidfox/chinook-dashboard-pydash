"""
Key Insights Panel
"""

from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.insights.helpers import load_markdown

# Read markdown text files
exec_summ_text = load_markdown("executive_summary.md")
strategic_text = load_markdown("strategic_opportunities.md")
next_steps_text = load_markdown("next_steps.md")
technical_notes_text = load_markdown("under_the_hood.md")

def layout():
    return html.Div([
        # KPI Card Tabs (Highlights)
        dmc.Title("KPI Highlights", order = 4),
        dmc.Space(h=10),
        dmc.Tabs(
            id="insights-kpi-tabs", 
            value="revenue-insights",
            children = [
                dmc.TabsList([
                    dmc.TabsTab(
                        "Revenue", 
                        value = "revenue-insights"
                    ),
                    dmc.TabsTab(
                        "Purchase Patterns", 
                        value="purchase-insights"
                    ),
                    dmc.TabsTab(
                        "Customer Behavior", 
                        value="customer-insights"
                    )    
                ]),
                dmc.TabsPanel(
                    value = "revenue-insights",
                    children = [
                        html.Div(
                                [
                                    dcc.Loading(
                                        children = dmc.SimpleGrid(
                                            cols={"base": 1, "sm": 2, "lg": 2},
                                            spacing="lg",
                                            children = [],
                                            id = "insight-revenue-kpi-cards"
                                        ),
                                        delay_hide = 400,
                                        custom_spinner = [
                                            dmc.Skeleton(
                                                height = 200, 
                                                width = "50%", 
                                                radius="sm", 
                                                visible = True
                                            ) for _ in range(2)
                                        ]
                                    )
                                ],
                            style={"padding": "1rem"}
                        )
                    ]
                ),
                dmc.TabsPanel(
                    value = "purchase-insights",
                    children = [
                            html.Div(
                                [
                                    dcc.Loading(
                                        children = dmc.SimpleGrid(
                                            cols={"base": 1, "sm": 2, "lg": 2},
                                            spacing="lg",
                                            children = [],
                                            id = "insight-purchase-kpi-cards"
                                        ),
                                        delay_hide = 400,
                                        custom_spinner = [
                                            dmc.Skeleton(
                                                height = 200, 
                                                width = "50%", 
                                                radius="sm", 
                                                visible = True
                                            ) for _ in range(2)
                                        ]
                                    )
                                ],
                            style={"padding": "1rem"}
                        )
                    ]
                ),
                dmc.TabsPanel(
                    value = "customer-insights",
                    children = [
                            html.Div(
                                [
                                    dcc.Loading(
                                        children = dmc.SimpleGrid(
                                            cols={"base": 1, "sm": 2, "lg": 2},
                                            spacing="lg",
                                            children = [],
                                            id = "insight-customer-kpi-cards"
                                        ),
                                        delay_hide = 400,
                                        custom_spinner = [
                                            dmc.Skeleton(
                                                height = 200, 
                                                width = "50%", 
                                                radius="sm", 
                                                visible = True
                                            ) for _ in range(2)
                                        ]
                                    )
                                ],
                            style={"padding": "1rem"}
                        )
                    ]
                )
                
            ]
        ),
        
        dmc.Space(h=10),

    # Key Insights Narrative Cards
        dmc.Tabs(
            id="insights-narrative-tabs", 
            value="executive-summary",
            children = [
                dmc.TabsList([
                    dmc.TabsTab(
                        "Executive Summary", 
                        value = "executive-summary"
                    ),
                    dmc.TabsTab(
                        "Strategic Opportunities", 
                        value="strategic-opportunities"
                    ),
                    dmc.TabsTab(
                        "Next Steps", 
                        value="next-steps"
                    )    
                ]),
                dmc.TabsPanel(
                    value = "executive-summary",
                    children = [
                        dmc.Space(h=10),
                        dmc.ScrollArea(
                            h=200,
                            type="always",
                            offsetScrollbars=True,
                            scrollbarSize=10,
                            children = dmc.Paper(
                                p="md",
                                shadow="sm",
                                children=dcc.Markdown(exec_summ_text)
                            )
                        )
                    ]
                ),
                dmc.TabsPanel(
                    value = "strategic-opportunities",
                    children = [
                        dmc.Space(h=10),
                        dmc.ScrollArea(
                            h=200,
                            type="always",
                            offsetScrollbars=True,
                            scrollbarSize=10,
                            children = dmc.Paper(
                                p="md",
                                shadow="sm",
                                children=dcc.Markdown(strategic_text)
                            )
                        )
                    ]
                ),
                dmc.TabsPanel(
                    value = "next-steps",
                    children = [
                        dmc.Space(h=10),
                        dmc.ScrollArea(
                            h=200,
                            type="always",
                            offsetScrollbars=True,
                            scrollbarSize=10,
                            children = dmc.Paper(
                                p="md",
                                shadow="sm",
                                children=dcc.Markdown(next_steps_text)
                            )
                        )
                    ]
                )
                
            ]
        ),

        dmc.Space(h=10),

        # "Technical Notes"    
        dmc.Accordion(
            children=[
                dmc.AccordionItem(
                    value="under-the-hood",
                    children=[
                        dmc.AccordionControl(
                            "Technical Notes", 
                            icon=DashIconify(icon="mdi:tools")
                            ),
                        dmc.AccordionPanel([
                            dmc.ScrollArea(
                            h=300,
                            type="always",
                            offsetScrollbars=True,
                            scrollbarSize=10,
                            children = dmc.Paper(
                                p="md",
                                shadow="sm",
                                children=dcc.Markdown(technical_notes_text)
                                )
                            )
                        ])
                    ]
                )
            ]
        )
    ]
)