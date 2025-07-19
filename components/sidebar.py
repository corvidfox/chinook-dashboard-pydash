# components/sidebar.py
from dash import html
import dash_mantine_components as dmc
import dash_ag_grid as dag
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date
from services.style_sidebar_utils import make_meta_row
from dash_iconify import DashIconify

meta = get_filter_metadata()
summary_df = get_static_summary()
last_updated = get_last_commit_date()

columnDefs = [
        {
            "headerName": "Metric",
            "field": "Metric",
            "flex": 1,
            "sortable": True,
            "filter": True,
        },
        {
            "headerName": "Value",
            "field": "Value",
            "flex": 1,
            "sortable": True,
            "filter": True,
        },
    ]

def make_sidebar(color_scheme):
    is_dark = color_scheme == "dark"
    ag_theme = "ag-theme-alpine-dark" if is_dark else "ag-theme-alpine"

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
        className=ag_theme, 
        style={"width": "100%"},
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

                    dmc.MonthPickerInput(
                        label="Date Range",
                        id="filter-date",
                        leftSection=DashIconify(icon="fa:calendar"),
                        type="range",
                        valueFormat="MMM YYYY",
                        value=[meta["date_range"][0], meta["date_range"][1]],
                        minDate=meta["date_range"][0],
                        maxDate=meta["date_range"][1],
                        w="100%"
                    ),

                    dmc.MultiSelect(
                        label="Country",
                        id="filter-country",
                        data=[{"label": c, "value": c} for c in meta["countries"]],
                        searchable=True,
                        clearable=True,
                        nothingFoundMessage="No matches",
                        maxDropdownHeight=160,
                        w="100%"
                    ),

                    dmc.MultiSelect(
                        label="Genre",
                        id="filter-genre",
                        data=[{"label": g, "value": g} for g in meta["genres"]],
                        searchable=True,
                        clearable=True,
                        nothingFoundMessage="No matches",
                        maxDropdownHeight=160,
                        w="100%"
                    ),

                    dmc.MultiSelect(
                        label="Artist",
                        id="filter-artist",
                        data=[{"label": a, "value": a} for a in meta["artists"]],
                        searchable=True,
                        clearable=True,
                        nothingFoundMessage="No matches",
                        maxDropdownHeight=180,
                        w="100%"
                    ),

                    dmc.Select(
                        label="Metric",
                        id="filter-metric",
                        value="revenue",
                        data=[
                            {"label": "Revenue (USD$)", "value": "revenue"},
                            {"label": "Number of Customers", "value": "num_cust"},
                        ],
                        w="100%"
                    ),

                    dmc.Button("Clear Filters", id="clear-filters", color="gray", variant="outline", w="100%", mt="xs"),

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
                                        dmc.Text("Dataset Overview:", size="sm", fw=500, mb=4),
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
