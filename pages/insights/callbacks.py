"""
callbacks.py

Defines and registers all Dash callbacks for the Key Insights dashboard module.

Callbacks include:
  - KPI cards update

Public API:
  - register_callbacks(app)
"""

from typing import Any, Dict, List
from dash import Dash, Input, Output, State
from pages.insights.helpers import make_revenue_kpi_card
from services.display_utils import make_static_kpi_card
from services.logging_utils import log_msg


__all__ = ["register_callbacks"]


def register_callbacks(app: Dash) -> None:
    """
    Wire up all Dash @app.callback functions for the key insights page.

    Parameters:
        app: The Dash application instance to register callbacks on.

    Returns:
        None
    """

    @app.callback(
        Output("insight-revenue-kpi-cards", "children"),
        Output("insight-purchase-kpi-cards", "children"),
        Output("insight-customer-kpi-cards", "children"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data"),
        State("static-kpis", "data")
    )
    def update_insight_kpis(
        dynamic_kpis: Dict[str, Any],
        dynamic_kpis_hash: str,
        static_kpis: Dict[str, Any]
    ) -> List[Any]:
        """
        Build and return KPI cards for revenue, purchases, and customers.

        Parameters:
            dynamic_kpis: Dict containing kpis for subset with formatted values.
            dynamic_kpis_hash: Fingerprint for the KPI set (unused).
            static_kpis: Dict containing static kpis with formatted values.

        Returns:
            A list of Dash components representing KPI cards.
        """
        log_msg("[CALLBACK:insights] Updating KPI cards.")
        
        # Build revenue cards
        revenue_cards = [
            make_revenue_kpi_card(
                kpi_bundle=static_kpis,
                title="All Data",
                icon="lets-icons:full-alt-light",
                tooltip="Full data set metrics."
            ),
            make_revenue_kpi_card(
                kpi_bundle=dynamic_kpis,
                title="Filtered View",
                icon="icon-park-outline:add-subset",
                tooltip="Filtered subset metrics."
            )
        ]

        # Build Purchase Pattern Cards
        purchase_specs = [
        { "label": "Total Orders",
            "key_path": ["metadata_kpis", "purchases_num"],
            "fmt": True,
            "tooltip": "Total number of purchases (invoices) in the data set." },
        { "label": "Avg Revenue per Order",
            "key_path": ["metadata_kpis", "revenue_per_purchase"],
            "fmt": True,
            "tooltip": "Average revenue per invoice." },
        { "label": "Total Tracks Sold",
            "key_path": ["metadata_kpis", "tracks_sold_num"],
            "fmt": True,
            "tooltip": "Total number of individual units (tracks) sold in the data set." },
        { "label": "Avg Tracks per Order",
            "key_path": ["metadata_kpis", "tracks_per_purchase"],
            "fmt": True,
            "tooltip": "Average track count per invoice." }
        ]

        purchase_cards = [
            make_static_kpi_card(
                kpi_bundle=static_kpis,
                specs = purchase_specs,
                title="All Data",
                icon="lets-icons:full-alt-light",
                tooltip="Full data set metrics."
            ),
            make_static_kpi_card(
                kpi_bundle=dynamic_kpis,
                specs = purchase_specs,
                title="Filtered View",
                icon="icon-park-outline:add-subset",
                tooltip="Filtered subset metrics."
            )
        ]

        # Customer Behavior Cards
        customer_specs = [
        { "label": "Total Customers",
            "key_path": ["metadata_kpis", "cust_num"],
            "fmt": True,
            "tooltip": "Number of active customers in the data set." },
        { "label": "% New Customers",
            "key_path": ["metadata_kpis", "cust_per_new"],
            "fmt": True,
            "tooltip": "Proportion of new active customers in the data set." },
        { "label": "Avg Revenue per Customer",
            "key_path": ["metadata_kpis", "revenue_per_cust"],
            "fmt": True,
            "tooltip": "Average revenue per customer in the data set." },
        { "label": "Top 3-Month Retention",
            "key_path": ["retention_kpis", "top_cohort_line_3"],
            "fmt": True,
            "tooltip": "Best performing cohort at 3 months since first purchase." },
        { "label": "Top 6-Month Retention",
            "key_path": ["retention_kpis", "top_cohort_line_6"],
            "fmt": True,
            "tooltip": "Best performing cohort at 6 months since first purchase." }
        ]

        customer_cards = [
            make_static_kpi_card(
                kpi_bundle=static_kpis,
                specs = customer_specs,
                title="All Data",
                icon="lets-icons:full-alt-light",
                tooltip="Full data set metrics."
            ),
            make_static_kpi_card(
                kpi_bundle=dynamic_kpis,
                specs = customer_specs,
                title="Filtered View",
                icon="icon-park-outline:add-subset",
                tooltip="Filtered subset metrics."
            )
        ]

        return (revenue_cards, purchase_cards, customer_cards)

