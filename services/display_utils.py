"""
Display utilities for formatting values and rendering KPI card displays.

Includes:
- format_kpi_value(): Converts numbers, currencies, percentages, and country 
    codes to human-readable strings
- flagify_country(): Translates ISO country codes into emoji flags + labels
- standardize_country_to_iso3(): Cleans arbitrary country names to ISO-3 format
- safe_kpi_entry(): Returns a kpi entry dict, with a fallback for empty values.
- _build_kpi_list(): Internal helper. Converts a list of KPI dicts into an HTML 
    <ul> with styled <li> items.
- safe_kpi_card(): Renders a KPI card with a header and body.
- make_topn_kpi_card(): Makes a "Top N" ranking KPI card.
- make_static_kpi_card(): Makes a static "set list of values" KPI card.
"""

import locale
import numbers
import math
import country_converter as coco
import pandas as pd
from typing import Tuple, Union, List, Dict, Any, Callable, Optional

from dash import html
from dash.development.base_component import Component
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
        if value is None or not (
            isinstance(value, numbers.Number) or math.isnan(value)
            ):
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
            # fractional: use decimal_places
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


def flagify_country(
        input_str: str, 
        label: bool = False, 
        label_type: str = "name"
        ) -> str:
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

    label_text = coco.convert(
        names=iso2, 
        to="name_short" if label_type == "name" else "ISO3"
        )
    return f"{flag} {label_text}" if (
        label_text and label_text != "not found"
        ) else flag


def safe_kpi_entry(
    label: str,
    value: Any,
    tooltip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Return a KPI entry dict.
    Falls back to "No data available" for None, empty string, or NaN.
    """
    if value is None or value == "" or (
       isinstance(value, float) and pd.isna(value)
    ):
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
            line = dmc.Tooltip(
                line,
                label=k["tooltip"],
                withArrow=True,
                position="top"
            )
        items.append(html.Li(line, className="kpi-list-item"))

    return html.Ul(items, className="kpi-list")


def safe_kpi_card(
    kpi_bundle: Dict[str, Any],
    body_fn: Callable[
        [], 
        Union[List[Dict[str, Any]], Component, Dict[str, Any]]
    ],
    title: str,
    icon: Optional[str] = None,
    tooltip: Optional[str] = None,
    list_style: Optional[Dict[str, Any]] = None
) -> dmc.Card:
    """
    Render a KPI card with:
      • Header (icon + title + optional tooltip) — always shown
      • Body
        - If kpi_bundle is empty → one line “No data available.”
        - Else if body_fn() yields no items → same one-line fallback
        - Else show your UL/OL/custom component + optional footer
    """
    # Build the header
    header_elems: List[Any] = []
    if icon:
        try:
            header_elems = [
                DashIconify(icon=icon, inline=True, width=20, height=20),
                dmc.Text(title, fw=700, size="md", span=True),
            ]
        except Exception:
            header_elems = [dmc.Text(title, fw=700, size="md")]
    else:
        header_elems = [dmc.Text(title, fw=700, size="md")]

    header_group = dmc.Group(header_elems, gap="xs", ta="center", wrap=True)
    if tooltip:
        header_group = dmc.Tooltip(
            header_group, label=tooltip, withArrow=True, position="top"
        )

    header = dmc.CardSection(
        html.Div(header_group, className="kpi-card-header"),
        style={"padding": 0},
        className="kpi-card-header-wrapper"
    )

    # If there's no bundle at all, skip to single-line body
    if not kpi_bundle:
        body_only = dmc.CardSection(
            dmc.Text("No data available.", ta="center"),
            className="kpi-card-body"
        )
        return dmc.Card(
            children=[header, body_only],
            className="kpi-card",
            shadow="sm", radius="md", withBorder=True,
            style={"width": "100%"}
        )

    # Otherwise invoke body_fn() once
    try:
        result = body_fn() if callable(body_fn) else []
    except Exception:
        result = []

    # Detect an “empty” result
    def _empty(res) -> bool:
        # Nothing at all
        if res is None:
            return True

        # A plain list with zero length
        if isinstance(res, list):
            return len(res) == 0

        # Any Dash component or HTML element:
        #     check its .children property instead of .props
        if hasattr(res, "children"):
            kids = res.children
            # None, empty list/tuple -> truly empty
            if kids is None:
                return True
            if isinstance(kids, (list, tuple)) and len(kids) == 0:
                return True
            # anything else (string, single child, non-empty list) -> non-empty
            return False

        # “dict with body/footer” convention
        if isinstance(res, dict) and "body" in res:
            return _empty(res["body"]) and not bool(res.get("footer"))

        # By default assume it isn’t empty
        return False

    # If body_fn gave nothing, again fall back to single-line body
    if _empty(result):
        body_comp = dmc.Text("No data available.", ta="center")
        footer_txt = None

    else:
        # Non-empty: normalize into a component + optional footer
        # dict-with-body/footer protocol
        if isinstance(result, dict) and "body" in result:
            body_comp = result["body"]
            footer_txt = result.get("footer")

        #any Dash/HTML component -> render it directly
        elif hasattr(result, "children"):
            body_comp = result
            footer_txt = None

        # a plain Python list of KPI-dicts -> build a <ul> via helper
        elif isinstance(result, list):
            from services.display_utils import _build_kpi_list
            body_comp = _build_kpi_list(result)
            footer_txt = None
            if list_style:
                # optional inline override
                body_comp = html.Ul(
                    children=body_comp.children,
                    className=body_comp.className,
                    style=list_style
                )

        # (shouldn’t happen) fallback
        else:
            body_comp = dmc.Text("No data available.", ta="center")
            footer_txt = None


    # Wrap the body component in its section
    body_section = dmc.CardSection(body_comp, className="kpi-card-body")

    # Assemble the final card
    children = [header, body_section]
    if not _empty(result) and isinstance(result, dict) and result.get("footer"):
        children.append(
            dmc.CardSection(
                dmc.Text(result["footer"], size="md", ta="left"),
                className="kpi-card-footer"
            )
        )

    return dmc.Card(
        children=children,
        className="kpi-card",
        shadow="sm", radius="md", withBorder=True,
        style={"width": "100%"}
    )


def make_static_kpi_card(
    kpi_bundle: Dict[str, Any],
    specs: List[Dict[str, Any]],
    title: str,
    icon: Optional[str] = None,
    tooltip: Optional[str] = None
) -> dmc.Card:
    """
    Build a KPI card with a fixed list of metrics.

    specs: list of {
        "label":    str,
        "key_path": List[str],
        "fmt":      bool,
        "tooltip":  Optional[str]
    }
    """
    def body_fn() -> List[Dict[str, Any]]:
        entries = []
        for s in specs:
            val = kpi_bundle
            for k in s["key_path"]:
                val = (val or {}).get(k)
            display = val if s.get("fmt", False) else format_kpi_value(val)
            entries.append(
                safe_kpi_entry(
                    label=s["label"], 
                    value=display, 
                    tooltip=s.get("tooltip")
                    )
            )
        return entries

    return safe_kpi_card(
        kpi_bundle=kpi_bundle,
        body_fn=body_fn,
        title=title,
        icon=icon,
        tooltip=tooltip,
        list_style={"listStyleType": "none", "paddingLeft": 0}
    )


def make_topn_kpi_card(
    kpis: Dict[str, Any],
    metric_key: str,
    fmt_key: str,
    title: str,
    top_n: int = 5,
    icon: str = None,
    tooltip: str = None,
    total_label: str = "Total Countries",
    custom_label_fn: Optional[Callable[[int, Dict[str, Any]], str]] = None,
    custom_value_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    list_path: Tuple[str, ...] = ("topn", "topn_country"),
    include_footer: bool = True
) -> dmc.Card:
    """
    A Top N “ol” card. We pass only the nested slice as bundle,
    so safe_kpi_card sees that slice’s num_vals and won’t fallback.
    """
    # Pre‐drill the slice for safe_kpi_card’s bundle check
    src = kpis
    for p in list_path:
        src = src.get(p, {})

    def body_fn():
        # only build the top-N list items
        items = src.get(metric_key, [])[:top_n]
        li_children = []
        for idx, itm in enumerate(items, start=1):
            label = (
                custom_label_fn(idx, itm)
                if custom_label_fn
                else itm.get("group_val_fmt", itm.get("group_val", "--"))
            )
            val = (
                custom_value_fn(itm)
                if custom_value_fn
                else itm.get(fmt_key, "--")
            )
            li_children.append(
                html.Li([
                    html.Strong(f"{label} "),
                    html.Span(f"({str(val)})")
                ])
            )

        ol = html.Ol(
            children=li_children,
            style={"paddingLeft": "1.2em", "margin": 0}
        )

        # return a dict so safe_kpi_card will render
        # ol in the body section and footer separately
        if include_footer:
            total = src.get("num_vals", "--")
            footer = f"{total_label}: {total}"
            return {"body": ol, "footer": footer}
        else:
            return ol

    return safe_kpi_card(
        kpi_bundle=src,
        body_fn=body_fn,
        title=title,
        icon=icon,
        tooltip=tooltip
    )