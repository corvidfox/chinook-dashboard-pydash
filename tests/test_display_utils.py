# tests/test_display_utils.py

import pytest
import pandas as pd
from services.display_utils import (
    format_kpi_value,
    standardize_country_to_iso3,
    flagify_country,
    safe_kpi_entry,
    safe_kpi_card,
    make_static_kpi_card,
    make_topn_kpi_card
)

def test_format_kpi_value_dollar():
    """Test formatting a numeric value as a dollar amount."""
    assert format_kpi_value(1234.567, value_type="dollar") == "$1,234.57"

def test_format_kpi_value_percent():
    """Test formatting a numeric value as a percentage."""
    assert format_kpi_value(0.1234, value_type="percent") == "12.34%"

def test_format_kpi_value_number():
    """Test formatting a large number with comma separators."""
    assert format_kpi_value(1000000, value_type="number") == "1,000,000"

def test_format_kpi_value_float():
    """Test formatting a float with default precision."""
    assert format_kpi_value(1234.567, value_type="float") == "1,234.57"

def test_format_kpi_value_invalid_type():
    """Test that an invalid value_type raises a ValueError."""
    with pytest.raises(ValueError):
        format_kpi_value(100, value_type="unknown")

def test_standardize_country_to_iso3_valid():
    """Test valid country name and code conversion to ISO3."""
    assert standardize_country_to_iso3("United States") == "USA"
    assert standardize_country_to_iso3("US") == "USA"

def test_standardize_country_to_iso3_invalid():
    """Test invalid country input returns None."""
    assert standardize_country_to_iso3("Atlantis") is None
    assert standardize_country_to_iso3(123) is None

def test_flagify_country_basic():
    """Test flag emoji generation from ISO2 code with and without label."""
    assert flagify_country("US") == "🇺🇸"
    assert "United States" in flagify_country("US", label=True)

def test_flagify_country_invalid():
    """Test flagify_country returns 'NA' for unknown input."""
    assert flagify_country("Unknownland") == "NA"

def test_safe_kpi_entry_valid():
    """Test safe_kpi_entry returns correct label and value."""
    entry = safe_kpi_entry("Revenue", "$1000")
    assert entry["label"] == "Revenue"
    assert entry["value"] == "$1000"

def test_safe_kpi_entry_missing():
    """Test safe_kpi_entry returns fallback for missing value."""
    assert safe_kpi_entry("Revenue", None)["value"] == "No data available"

def test_safe_kpi_card_structure():
    """Test safe_kpi_card returns a Card with expected content."""
    def dummy_body_fn():
        return [{"label": "Revenue", "value": "$1000"}]

    card = safe_kpi_card(
        kpi_bundle={"Revenue": "$1000"},
        body_fn=dummy_body_fn,
        title="Test KPI"
    )
    assert card.__class__.__name__ == "Card"
    assert "Revenue" in str(card)

def test_make_static_kpi_card_valid():
    """Test make_static_kpi_card renders formatted KPIs correctly."""
    kpi_bundle = {
        "Revenue": format_kpi_value(1000, value_type="dollar"), 
        "Purchases": 200
    }
    specs = [
        {"label": "Revenue", "key_path": ["Revenue"], "fmt": True},
        {"label": "Purchases", "key_path": ["Purchases"], "fmt": False}
    ]
    card = make_static_kpi_card(kpi_bundle, specs, title="Static KPIs")

    assert card.__class__.__name__ == "Card"
    assert "Revenue" in str(card)
    assert "$1,000.00" in str(card)

def test_make_static_kpi_card_empty():
    """Test make_static_kpi_card handles empty data gracefully."""
    specs = [{"label": "Revenue", "key_path": ["Revenue"], "fmt": True}]
    card = make_static_kpi_card({}, specs, title="Empty KPIs")
    assert "No data available" in str(card)

def test_make_topn_kpi_card_valid():
    """Test make_topn_kpi_card renders top-N entries correctly."""
    kpis = {
        "topn": {
            "topn_country": {
                "metric_key": [
                    {"group_val": "US", "fmt_key": "$1000"},
                    {"group_val": "Canada", "fmt_key": "$500"}
                ],
                "num_vals": 2
            }
        }
    }

    kpis["topn"]["topn_country"]["topn_revenue"] = [
        {"group_val": "US", "group_val_fmt": "🇺🇸 United States", "fmt_revenue": "$1,000.00"},
        {"group_val": "CA", "group_val_fmt": "🇨🇦 Canada", "fmt_revenue": "$500.00"}
    ]

    card = make_topn_kpi_card(
        kpis=kpis,
        metric_key="topn_revenue",
        fmt_key="fmt_revenue",
        title="Top Countries"
    )
    assert card.__class__.__name__ == "Card"
    assert "Top Countries" in str(card)
    assert "$1,000.00" in str(card)

def test_make_topn_kpi_card_empty():
    """Test make_topn_kpi_card handles empty input gracefully."""
    kpis = {}
    card = make_topn_kpi_card(
        kpis=kpis,
        metric_key="topn_revenue",
        fmt_key="fmt_revenue",
        title="Top Countries"
    )
    assert card.__class__.__name__ == "Card"
    assert "No data available" in str(card)
