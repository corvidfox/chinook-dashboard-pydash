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
        [
          Output("navbar-state", "data"),
          Output("shell",         "className"),
        ],
        Input("burger", "opened"),
        State("navbar-state", "data"),
        prevent_initial_call=True
    )
    def toggle_navbar(opened, current):
        """
        Updates navbar collapsed state from burger toggle.
        """
        collapsed = not opened
        new_state = {"collapsed":{"mobile":collapsed, "desktop":collapsed}}

        # CSS class to push/pull the shell
        cls = "nav-closed" if collapsed else "nav-open"

        log_msg(f"[CALLBACK:sidebar] Toggling shell → {cls}")
        return new_state, cls

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
    )
    def render_sidebar(nav_state):
        """
        Rebuilds sidebar content when navbar state changes.
        """
        log_msg(f"[CALLBACK:sidebar] Rebuilding sidebar")
        return make_sidebar(FILTER_META, SUMMARY_DF, LAST_UPDATED)

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
