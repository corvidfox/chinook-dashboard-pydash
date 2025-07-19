# config.py
from services.style_tokens import FONT_SIZES, FONT_WEIGHTS

DEFAULT_COLORSCHEME = "light"

def get_mantine_theme(color_scheme: str) -> dict:
    return {
        "colorScheme": color_scheme,
        "fontFamily": "'Inter', sans-serif",
        "fontSizes": FONT_SIZES,
        "headings": {
            "fontFamily": "'Greycliff CF', sans-serif",
            "fontWeight": FONT_WEIGHTS["extra-bold"],
        },
        "primaryColor": "indigo",
        "radius": {"sm": 4, "md": 8, "lg": 12},
        "withCssVariables": True,
        "withGlobalClasses": True
    }

