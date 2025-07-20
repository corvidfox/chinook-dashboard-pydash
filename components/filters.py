# components/filters.py
import dash_mantine_components as dmc
from dash_iconify import DashIconify

def date_filter(filter_meta):
    return dmc.MonthPickerInput(
        label="Date Range",
        id="filter-date",
        leftSection=DashIconify(icon="fa:calendar"),
        type="range",
        valueFormat="MMM YYYY",
        value=[filter_meta["date_range"][0], filter_meta["date_range"][1]],
        minDate=filter_meta["date_range"][0],
        maxDate=filter_meta["date_range"][1],
        w="100%",
        persistence=True, 
        persistence_type="session"
    )

def country_filter(filter_meta):
    return dmc.MultiSelect(
        label="Country",
        id="filter-country",
        data=[{"label": c, "value": c} for c in filter_meta["countries"]],
        searchable=True,
        clearable=True,
        nothingFoundMessage="No matches",
        maxDropdownHeight=160,
        w="100%",
        persistence=True, 
        persistence_type="session"
    )

def genre_filter(filter_meta):
    return dmc.MultiSelect(
        label="Genre",
        id="filter-genre",
        data=[{"label": g, "value": g} for g in filter_meta["genres"]],
        searchable=True,
        clearable=True,
        nothingFoundMessage="No matches",
        maxDropdownHeight=160,
        w="100%",
        persistence=True, 
        persistence_type="session"
    )

def artist_filter(filter_meta):
    return dmc.MultiSelect(
        label="Artist",
        id="filter-artist",
        data=[{"label": a, "value": a} for a in filter_meta["artists"]],
        searchable=True,
        clearable=True,
        nothingFoundMessage="No matches",
        maxDropdownHeight=180,
        w="100%",
        persistence=True, 
        persistence_type="session"
    )

def metric_filter():
    return dmc.Select(
        label="Metric",
        id="filter-metric",
        value="revenue",
        data=[
            {"label": "Revenue (USD$)", "value": "revenue"},
            {"label": "Number of Customers", "value": "num_cust"},
        ],
        w="100%",
        persistence=True, 
        persistence_type="session"
    )

def clear_button():
    return dmc.Button("Clear Filters", id="clear-filters", color="gray", variant="outline", w="100%", mt="xs")
