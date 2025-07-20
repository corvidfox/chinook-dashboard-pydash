# components/sidebar.py
import dash_mantine_components as dmc
import dash_ag_grid as dag
from services.style_sidebar_utils import make_meta_row
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
        },
    ]

def make_sidebar(color_scheme, filter_meta, summary_df, last_updated):

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
        # Add soft buffers from the edges
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
                    # Filters
                    dmc.Title("Filters", order=3),
                    filters.date_filter(filter_meta),
                    filters.country_filter(filter_meta),
                    filters.genre_filter(filter_meta),
                    filters.artist_filter(filter_meta),
                    filters.metric_filter(),
                    filters.clear_button(),
                    # "About This Data" Accordion
                    dmc.Accordion(
                        value="about-data",
                        children=[
                            dmc.AccordionItem(
                                value="about-data",
                                children=[
                                    dmc.AccordionControl("About This Data"),
                                    dmc.AccordionPanel([
                                        # Static Items/Links
                                        dmc.Stack([
                                            make_meta_row("fa:pencil", "Created by", "Morrigan M.", "https://github.com/corvidfox"),
                                            make_meta_row("fa:github", "", "GitHub Repo", "https://github.com/corvidfox/chinook-dashboard-rshiny"),
                                            make_meta_row("fa:link", "", "Chinook Dataset", "https://github.com/lerocha/chinook-database"),
                                            make_meta_row("fa:file", "", "Portfolio Post", "https://corvidfox.github.io/projects/posts/2025_bi_chinook.html"),
                                            make_meta_row("tdesign:calendar-2-filled", "Last updated:", last_updated),
                                        ], gap="xs", mb="md"),

                                        dmc.Divider(),
                                        # Static Metadata Table
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
