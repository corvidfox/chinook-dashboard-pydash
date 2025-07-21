"""
Sidebar and navbar callbacks for the Chinook dashboard.
Handles burger toggle logic, sidebar visibility, and dynamic re-rendering.
"""

from dash import Input, Output, State, clientside_callback
from config import DEFAULT_COLORSCHEME
from services.logging_utils import log_msg
from components.sidebar import make_sidebar
from services.metadata import get_filter_metadata, get_static_summary, get_last_commit_date

# Static content for sidebar rendering
FILTER_META = get_filter_metadata()
SUMMARY_DF = get_static_summary()
LAST_UPDATED = get_last_commit_date()
log_msg("[CALLBACK:sidebar] Loaded static sidebar metadata")

def register_callbacks(app):
    @app.callback(
        Output("navbar-state", "data"),
        Input("burger", "opened"),
        State("navbar-state", "data")
    )
    def toggle_navbar(opened, state):
        """
        Updates navbar collapsed state from burger toggle.
        """
        log_msg(f"[CALLBACK:sidebar] Burger toggled — collapsed state now {not opened}")
        return {"collapsed": {"mobile": not opened, "desktop": not opened}}

    @app.callback(
        Output("navbar", "collapsed"),
        Input("navbar-state", "data")
    )
    def sync_navbar(navbar_state):
        """
        Reflects collapsed state on navbar component.
        """
        return navbar_state["collapsed"]["mobile"]

    @app.callback(
        Output("navbar", "children"),
        Input("navbar-state", "data"),
        Input("theme-store", "data"),
    )
    def render_sidebar(nav_state, theme_data):
        """
        Rebuilds sidebar content when theme or navbar state changes.
        """
        scheme = theme_data["color_scheme"] if theme_data and "color_scheme" in theme_data else DEFAULT_COLORSCHEME
        log_msg(f"[CALLBACK:sidebar] Rebuilding sidebar — theme: {scheme}")
        log_msg(f"     [CALLBACK:sidebar] Sidebar content → filters={len(FILTER_META)}, metrics={len(SUMMARY_DF)}")
        return make_sidebar(scheme, FILTER_META, SUMMARY_DF, LAST_UPDATED)

    @app.callback(
        Output("navbar", "style"),
        Input("navbar-state", "data")
    )
    def collapse_navbar(navbar_state):
        """
        Animates sidebar width based on collapsed state.
        """
        collapsed = navbar_state["collapsed"]["mobile"]
        log_msg(f"[CALLBACK:sidebar] Sidebar collapse status: {collapsed}")
        return {
            "width": 0 if collapsed else 300,
            "overflow": "hidden",
            "transition": "width 0.3s ease",
            "backgroundColor": "var(--mantine-color-body)"
        }
    
    # Manipulates viewport styling based on sidebar logic
    app.clientside_callback(
        """
        function(navbarState) {
            const collapsed = navbarState.collapsed;
            const shell = document.querySelector('[data-dash-is-loading="true"]');
            if (!shell) return;
            shell.setAttribute("data-navbar-collapsed", JSON.stringify(collapsed));
        }
        """,
        Output("viewport-trigger", "style"), 
        Input("navbar-state", "data")
    )
