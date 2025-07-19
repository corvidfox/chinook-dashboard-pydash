# services/style_sidebar_utils.py

from dash_iconify import DashIconify
import dash_mantine_components as dmc
from services.style_tokens import FONT_SIZES

def make_meta_row(
    icon_name: str,
    label: str = "",
    content: str = "",
    link_url: str = None,
    font_size: str = FONT_SIZES["sm"]
) -> dmc.Flex:
    """Creates a responsive metadata row with an icon, optional label, and optional link or plain content."""

    icon = DashIconify(icon=icon_name, style={"fontSize": font_size})

    # Compose the text block
    if link_url:
        text_block = dmc.Text([
            f"{label} ",
            dmc.Anchor(content, href=link_url, target="_blank", style={"fontSize": font_size})
        ], style={"fontSize": font_size})
    else:
        text_block = dmc.Text(f"{label} {content}", style={"fontSize": font_size})

    # Let parent container (e.g., Stack) control vertical spacing
    return dmc.Flex(
        justify="start",
        align="center",
        gap=6,
        wrap="wrap",
        children=[icon, text_block]
    )
