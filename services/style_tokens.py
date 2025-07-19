# services/style_tokens.py

# Font sizes (responsive and rem-based)
FONT_SIZES = {
    "xs": "0.75rem",      # ~12px
    "sm": "0.875rem",     # ~14px
    "md": "1rem",         # ~16px
    "lg": "1.125rem",     # ~18px
    "xl": "1.25rem"       # ~20px
}

# Example usage: style={"fontSize": FONT_SIZES["sm"]}


# Font weights
FONT_WEIGHTS = {
    "normal": 400,
    "medium": 500,
    "bold": 600,
    "extra-bold": 700
}

# Example usage: style={"fontWeight": FONT_WEIGHTS["bold"]}


# Shared spacing units
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24
}

# Breakpoints (you can use these in responsive logic)
BREAKPOINTS = {
    "mobile": 480,
    "tablet": 768,
    "desktop": 1024
}

def responsive_font_size(width: int) -> str:
    if width < 480:
        return FONT_SIZES["xs"]
    elif width < 768:
        return FONT_SIZES["sm"]
    else:
        return FONT_SIZES["md"]
