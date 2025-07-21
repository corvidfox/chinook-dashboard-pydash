"""
config.py

Central configuration for the Chinook dashboard, including:

- Mantine theme generator
- Typography, spacing, and breakpoints
- Global constants like default theme and cache paths
"""

import os

ENABLE_LOGGING = os.getenv("DASH_ENV", "development").lower() != "production"

# Font sizes (responsive and rem-based)
FONT_SIZES = {
    "XS": "0.75rem",      # ~12px
    "SM": "0.875rem",     # ~14px
    "MD": "1rem",         # ~16px
    "LG": "1.125rem",     # ~18px
    "XL": "1.25rem"       # ~20px
}

# Font weights
FONT_WEIGHTS = {
    "NORMAL": 400,
    "MEDIUM": 500,
    "BOLD": 600,
    "EXTRA_BOLD": 700
}

# Spacing units (px)
SPACING = {
    "XS": 4,
    "SM": 8,
    "MD": 12,
    "LG": 16,
    "XL": 24
}

# Responsive breakpoints (px)
BREAKPOINTS = {
    "MOBILE": 480,
    "TABLET": 768,
    "DESKTOP": 1024
}

# GitHub metadata caching path
CACHE_PATH = "data/last_commit_cache.json"

# Default color scheme
DEFAULT_COLORSCHEME = "light"

# Responsive font sizing utility
def responsive_font_size(width: int) -> str:
    """
    Returns an appropriate font size token based on viewport width.

    Parameters:
        width (int): Viewport width in pixels

    Returns:
        str: Font size string
    """
    if width < BREAKPOINTS["MOBILE"]:
        return FONT_SIZES["XS"]
    elif width < BREAKPOINTS["TABLET"]:
        return FONT_SIZES["SM"]
    return FONT_SIZES["MD"]

# Mantine theme generator
def get_mantine_theme(color_scheme: str) -> dict:
    """
    Constructs a Mantine-compatible theme dictionary.

    Parameters:
        color_scheme (str): 'light' or 'dark'

    Returns:
        dict: Theme object used by MantineProvider
    """
    return {
        "colorScheme": color_scheme,
        "fontFamily": "'Inter', sans-serif",
        "fontSizes": FONT_SIZES,
        "headings": {
            "fontFamily": "'Greycliff CF', sans-serif",
            "fontWeight": FONT_WEIGHTS["EXTRA_BOLD"],
        },
        "primaryColor": "indigo",
        "radius": {"sm": 4, "md": 8, "lg": 12},
        "withCssVariables": True,
        "withGlobalClasses": True
    }
