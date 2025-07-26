"""
Display utilities for formatting values in the Chinook dashboard.

Includes:
- format_kpi_value(): Converts numbers, currencies, percentages, and country codes to human-readable strings
- flagify_country(): Translates ISO country codes into emoji flags + labels
- standardize_country_to_iso3(): Cleans arbitrary country names to ISO-3 format
"""

import locale
import numbers
import math
import country_converter as coco
import pandas as pd
from typing import Union, List, Dict, Any, Callable, Optional
from dash import html
from dash_iconify import DashIconify
import dash_mantine_components as dmc

from services.logging_utils import log_msg

# Set system locale for number formatting (fallback to default)
try:
    locale.setlocale(locale.LC_ALL, "")
except Exception:
    locale.setlocale(locale.LC_ALL, "C")


def format_kpi_value(
    value: Union[int, float, str],
    value_type: str = "number",
    accuracy: float = 0.01,
    prefix: str = "$",
    label: bool = True,
    label_type: str = "name"
) -> str:
    """
    Format a KPI value for display. Supports:
    - 'dollar': currency with prefix
    - 'percent': percentage with two decimals
    - 'number': comma-grouped integer or float
    - 'float': float with dynamic precision
    - 'country': flag + optional label

    Parameters:
        value: Numeric or country input
        value_type: Display type ('number', 'dollar', etc)
        accuracy: Rounding precision (e.g. 0.01 → round to hundredths)
        prefix: Currency symbol if value_type == 'dollar'
        label: Country label toggle for value_type == 'country'
        label_type: 'name' or 'iso3' for country label

    Returns:
        str: Formatted string for display
    """
    if value_type not in {"dollar", "percent", "number", "float", "country"}:
        raise ValueError(f"Unsupported value_type: {value_type}")

    # Handle missing or invalid numerics
    if value_type != "country":
        if value is None or not isinstance(value, numbers.Number) or math.isnan(value):
            return "NA"
    else:
        if value is None:
            return "NA"

    # Determine decimal places from accuracy
    try:
        decimal_places = max(0, -int(round(locale.log10(accuracy))))
    except Exception:
        decimal_places = 2  # fallback

    if value_type == "percent":
        return f"{round(value * 100, decimal_places):.{decimal_places}f}%"

    if value_type == "dollar":
        rounded = round(value, decimal_places)
        return f"{prefix}{locale.format_string(f'%.{decimal_places}f', rounded, grouping=True)}"

    if value_type == "float":
        rounded = round(value, decimal_places)
        return locale.format_string(f'%.{decimal_places}f', rounded, grouping=True)

    if value_type == "number":
        # coerce to Python float for is_integer() check
        float_val = float(value)
        if float_val.is_integer():
            # integer formatting
            return locale.format_string("%d", int(float_val), grouping=True)
        else:
            # fractional → use decimal_places
            rounded = round(float_val, decimal_places)
            fmt = f"%.{decimal_places}f"
            return locale.format_string(fmt, rounded, grouping=True)

    if value_type == "country":
        return flagify_country(str(value), label=label, label_type=label_type)

    return str(value)


def standardize_country_to_iso3(input_str: str) -> Union[str, None]:
    """
    Converts a country name or code to ISO-3 format (e.g. "USA").

    Parameters:
        input_str (str): Country name or code

    Returns:
        str or None: ISO-3 code, or None if unresolvable
    """
    if not isinstance(input_str, str):
        return None

    iso3 = coco.convert(names=input_str, to="ISO3")
    return iso3 if iso3 != "not found" else None


def flagify_country(input_str: str, label: bool = False, label_type: str = "name") -> str:
    """
    Creates a country flag emoji string based on input.

    Accepts country name, ISO2, or ISO3; returns "🇺🇸 United States" or just "🇺🇸".

    Parameters:
        input_str (str): Country name or code
        label (bool): Whether to include country name
        label_type (str): "name" or "iso3"

    Returns:
        str: Flag emoji + optional label
    """
    if not isinstance(input_str, str):
        return "NA"

    iso2 = coco.convert(names=input_str, to="ISO2")
    if iso2 == "not found" or len(iso2) != 2:
        return "NA"

    flag = ''.join([chr(127397 + ord(c)) for c in iso2.upper()])

    if not label:
        return flag

    label_text = coco.convert(names=iso2, to="name_short" if label_type == "name" else "ISO3")
    return f"{flag} {label_text}" if label_text and label_text != "not found" else flag

# services/kpi_utils.py %%%

from typing import Any, Callable, Dict, List, Optional
from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd


def safe_kpi_entry(
    label: str,
    value: Any,
    tooltip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Return a KPI entry dict.  
    Falls back to "No data available" for None, empty string, or NaN.
    """
    if value is None or value == "" or (isinstance(value, float) and pd.isna(value)):
        display = "No data available"
    else:
        display = value

    return {"label": label, "value": display, "tooltip": tooltip}

def _build_kpi_list(kpis: List[Dict[str, Any]]) -> html.Ul:
    """
    Convert a list of KPI dicts into an HTML <ul> with styled <li> items.
    """
    items = []
    for k in kpis:
        line = html.Span([
            html.Strong(f"{k['label']}: "),
            html.Span(str(k["value"]))
        ])
        if k.get("tooltip"):
            line = dmc.Tooltip(line, label=k["tooltip"], withArrow=True, position="top")
        items.append(html.Li(line, className="kpi-list-item"))

    return html.Ul(items, className="kpi-list")


def safe_kpi_card(
    kpi_bundle: Dict[str, Any],
    body_fn: Callable[[], List[Dict[str, Any]]],
    title: str,
    icon: Optional[str] = None,
    tooltip: Optional[str] = None
) -> dmc.Card:
    """
    Render a KPI card with a header and body.

    Args:
        kpi_bundle: Used only to detect "no data" when empty.
        body_fn:   Returns a list of KPI dicts (label/value/tooltip).
        title:     Header text.
        icon:      String name for DashIconify (e.g. "mdi:chart-line").
        tooltip:   Optional hover tooltip for the header.

    Returns:
        A styled dmc.Card that obeys light/dark theming.
    """
    # Check if data is present
    has_data = bool(kpi_bundle and callable(body_fn) and body_fn())
    entries = body_fn() if has_data else []

    # Header section
    header_children: List[Any] = []
    if icon:
        try:
            log_msg(f"[DISPLAY UTILS] - attempting to pull icon: {icon}")
            header_children = [
                DashIconify(icon = icon, width = 20, height = 20),
                dmc.Text(title, fw=700, size="md")
            ]
        except Exception:
            log_msg(f"  [DISPLAY UTILS] - Invalid icon: {icon}")
            header_children = [
                dmc.Text(title, fw=700, size="md", span=True)
            ]
    else:
        header_children = [
                dmc.Text(title, fw=700, size="md")
            ]

    header = dmc.CardSection(
        dmc.Group(header_children, gap="xs", align="center", style={"width": "100%"}),
        className="kpi-card-header",
    )
    if tooltip:
        header = dmc.Tooltip(header, label=tooltip, withArrow=True, position="top")

    # Body section
    if not entries:
        # single centered line when no KPIs
        body_content = dmc.Text("No data available.", ta="center")
    else:
        body_content = _build_kpi_list(entries)

    body = dmc.CardSection(body_content, className="kpi-card-body")

    # Full card
    return dmc.Card(
        children=[header, body],
        className="kpi-card",
        shadow="sm",
        radius="md",
        withBorder=True,
        style = {"width": "100%"}
    )
