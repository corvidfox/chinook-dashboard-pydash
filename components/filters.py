"""
Filter components for the Chinook dashboard sidebar.

This module provides reusable Mantine-styled filter inputs for country, genre,
artist, metric, and date range selection, along with a filter reset button.
All filters support persistence via Dash's session-based storage.

Includes a helper to assemble all filters into a standardized block layout.
"""

import dash_mantine_components as dmc
from dash_iconify import DashIconify


def date_filter(filter_meta):
    """
    Creates a MonthPickerInput for selecting a date range.

    Parameters:
        filter_meta (dict): Metadata containing min/max date range.

    Returns:
        dmc.MonthPickerInput
    """
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
    """
    Creates a MultiSelect for filtering by country.

    Parameters:
        filter_meta (dict): Metadata containing list of countries.

    Returns:
        dmc.MultiSelect
    """
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
    """
    Creates a MultiSelect for filtering by genre.

    Parameters:
        filter_meta (dict): Metadata containing list of genres.

    Returns:
        dmc.MultiSelect
    """
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
    """
    Creates a MultiSelect for filtering by artist.

    Parameters:
        filter_meta (dict): Metadata containing list of artists.

    Returns:
        dmc.MultiSelect
    """
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


def metric_filter(filter_meta):
    """
    Creates a Select dropdown for choosing a summary metric.

    Returns:
        dmc.Select
    """
    return dmc.Select(
        label="Metric",
        id="filter-metric",
        value="revenue",
        data=[{"label": a["label"], "value": a["var_name"]} for a in filter_meta["metrics"]],
        w="100%",
        persistence=True,
        persistence_type="session"
    )


def clear_button():
    """
    Creates a button to clear all filters.

    Returns:
        dmc.Button
    """
    return dmc.Button(
        "Clear Filters",
        id="clear-filters",
        color="gray",
        variant="outline",
        w="100%",
        mt="xs"
    )


def make_filter_block(filter_meta):
    """
    Assembles all filter components into a vertically stacked layout.

    Parameters:
        filter_meta (dict): Metadata required by filter components.

    Returns:
        dmc.Stack
    """
    return dmc.Stack([
        date_filter(filter_meta),
        country_filter(filter_meta),
        genre_filter(filter_meta),
        artist_filter(filter_meta),
        metric_filter(filter_meta),
        clear_button()
    ], gap="sm")
