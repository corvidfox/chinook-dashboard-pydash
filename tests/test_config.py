# tests/test_config.py

import pytest
from config import FONT_SIZES, responsive_font_size

def test_font_sizes():
    """Ensure FONT_SIZES contains expected keys and values."""
    assert "MD" in FONT_SIZES
    assert FONT_SIZES["MD"] == "1rem"
    assert FONT_SIZES["XS"] == "0.75rem"
    assert FONT_SIZES["SM"] == "0.875rem"
    assert FONT_SIZES["LG"] == "1.125rem"
    assert FONT_SIZES["XL"] == "1.25rem"

@pytest.mark.parametrize("width,expected", [
    (100, "0.75rem"),     # Below MOBILE breakpoint
    (479, "0.75rem"),     # Just below MOBILE
    (480, "0.875rem"),    # MOBILE breakpoint
    (767, "0.875rem"),    # Just below TABLET
    (768, "1rem"),        # TABLET breakpoint
    (900, "1rem"),        # Above TABLET
])
def test_responsive_font_size(width, expected):
    """Test responsive font size logic for various screen widths."""
    assert responsive_font_size(width) == expected

def test_get_mantine_theme():
    from config import get_mantine_theme, FONT_SIZES, FONT_WEIGHTS

    theme = get_mantine_theme("dark")
    assert theme["colorScheme"] == "dark"
    assert theme["fontSizes"] == FONT_SIZES
    assert theme["headings"]["fontWeight"] == FONT_WEIGHTS["EXTRA_BOLD"]
    assert theme["plotlyTemplate"] == "mantine_dark"

    theme = get_mantine_theme("light")
    assert theme["colorScheme"] == "light"
    assert theme["plotlyTemplate"] == "mantine_light"
