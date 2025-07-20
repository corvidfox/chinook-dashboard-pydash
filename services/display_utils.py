# services/display_utils.py

import locale
import country_converter as coco

locale.setlocale(locale.LC_ALL, '')  # System locale for commas/periods

def format_kpi_value(value, type="number", accuracy=0.01, prefix="$", label=True, label_type="name"):
    """
    Format numeric or country values for consistent dashboard display.
    Supported types: "dollar", "percent", "number", "float", "country".
    """
    if type not in {"dollar", "percent", "number", "float", "country"}:
        raise ValueError(f"Unsupported type: {type}")

    # Handle NA cases
    if value is None or (type != "country" and not isinstance(value, (int, float))):
        return "NA"

    # Format numbers
    if type == "percent":
        return f"{round(value * 100, 2):.2f}%"

    if type == "dollar":
        return f"{prefix}{locale.format_string('%.2f', round(value, 2), grouping=True)}"

    if type == "float":
        return f"{locale.format_string('%.2f', round(value, 2), grouping=True)}"

    if type == "number":
        if value % 1 == 0:
            return locale.format_string("%d", int(value), grouping=True)
        else:
            return locale.format_string('%.2f', round(value, 2), grouping=True)

    if type == "country":
        return flagify_country(value, label=label, label_type=label_type)

    return str(value)


def standardize_country_to_iso3(input_str):
    """
    Convert country name or code to ISO Alpha-3 code (e.g., 'USA').
    """
    if not isinstance(input_str, str):
        return None

    iso3 = coco.convert(names=input_str, to="ISO3")
    return iso3 if iso3 != "not found" else None


def flagify_country(input_str, label=False, label_type="name"):
    """
    Convert country identifier to emoji + optional label ("🇺🇸 United States").
    Accepts country name, ISO2, or ISO3.
    """
    if not isinstance(input_str, str):
        return "NA"

    iso2 = coco.convert(names=input_str, to="ISO2")
    if iso2 == "not found" or len(iso2) != 2:
        return "NA"

    # Unicode flag construction
    flag = ''.join([chr(127397 + ord(c)) for c in iso2.upper()])

    if not label:
        return flag

    if label_type == "name":
        label_text = coco.convert(names=iso2, to="name_short")
    elif label_type == "iso3":
        label_text = coco.convert(names=iso2, to="ISO3")
    else:
        label_text = ""

    return f"{flag} {label_text}" if label_text else flag
