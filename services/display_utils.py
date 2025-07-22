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
from typing import Union


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
