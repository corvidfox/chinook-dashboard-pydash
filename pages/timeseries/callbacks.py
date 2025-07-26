import json
from datetime import date
from dash import Input, Output, State, callback, html, dcc
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate
import pandas as pd

from pages.timeseries.helpers import (
    get_ts_monthly_summary_cached
    )

from services.display_utils import (
    safe_kpi_card, safe_kpi_entry
)

from services.logging_utils import log_msg

def register_callbacks(app):
    @app.callback(
        Output("ts-data-scroll", "className"),
        Input("grid-theme-store", "data")
    )
    def update_aggrid_theme(grid_class):
        log_msg(f"[CALLBACK:overview] Updated grid theme → {grid_class}")
        return grid_class

    @app.callback(
        Output("ts-data-scroll", "columnDefs"),
        Output("ts-data-scroll", "rowData"),

        Input("events-shared-fingerprint", "data"),
        Input("metric-store", "data"),
        Input("metric-label-store", "data"),
        Input("date-range-store", "data"),
        State("max-offset-store", "data"),
        State("offsets-store", "data"),
        State("static-kpis", "data")
    )
    def update_ts(
        events_hash,
        metric_value,
        metric_label,
        date_range,
        max_offset,
        offsets,
        static_kpis
        ):
        if not events_hash:
            raise PreventUpdate

        log_msg("[CALLBACK:timeseries] - Callback active.")

        ts_df = get_ts_monthly_summary_cached(events_hash, date_range)
        ts_df_coldefs = [
            {"field": c, "headerName": c, "sortable": True, "filter": True} 
            for c in ts_df.columns
            ]

        log_msg("[CALLBACK:timeseries] Time Series dashboard data refreshed")
        log_msg(f"     [CALLBACK:timeseries] Data Table Rows = {len(ts_df)}")

        return (
            ts_df_coldefs, ts_df.to_dict("records")
        )

    @app.callback(    
        Output("ts-kpi-cards", "children"),
        Input("kpis-store", "data"),
        Input("kpis-fingerprint", "data")
    )
    def update_ts_kpis(dynamic_kpis, dynamic_kpis_hash):
        ts_kpis = dynamic_kpis

        def revenue_kpis():
            return [
                safe_kpi_entry("Total", ts_kpis["metadata_kpis"].get("revenue_total_fmt"), "Total revenue."),
                safe_kpi_entry("Avg / Month", ts_kpis["metadata_kpis"].get("revenue_per_month", "Average revenue per month."))
            ]

        def purchase_kpis():
            return [
            safe_kpi_entry("Purchases", ts_kpis["metadata_kpis"].get("purchases_num"), "Total number of unique purchase events."),
            safe_kpi_entry("Tracks Sold", ts_kpis["metadata_kpis"].get("tracks_sold_num"), "Total unit sales."),
            safe_kpi_entry("Avg $ / Purchase", ts_kpis["metadata_kpis"].get("revenue_per_purchase"), "Average revenue per purchase.")
        ]

        def customer_kpis():
            return [
            safe_kpi_entry("Total", ts_kpis["metadata_kpis"].get("cust_num"), "Total unique customers."),
            safe_kpi_entry("First-Time", ts_kpis["metadata_kpis"].get("cust_per_new", "(%) first-time customers."))
        ]

        return [
            safe_kpi_card(
                ts_kpis, revenue_kpis,  
                title="Revenue",  icon = "mdi:chart-line", #icon="tdesign:money", 
                tooltip="Gross revenue"),
            safe_kpi_card(ts_kpis, purchase_kpis, title="Purchases", icon="carbon:receipt", tooltip="Purchase patterns"),
            safe_kpi_card(ts_kpis, customer_kpis,   title="Customers", icon="mdi:people-outline", tooltip="Customer stats"),
        ]
    
    @app.callback(
        Output("download-ts-csv", "data"),
        Input("btn-download-ts", "n_clicks"),
        State("ts-data-scroll", "rowData"),
        prevent_initial_call=True,
    )
    def download_ts_csv_from_grid(n_clicks, row_data):
        if not row_data:
            raise PreventUpdate

        df = pd.DataFrame(row_data)
        today_str = date.today().strftime("%Y_%m_%d")
        filename = f"chinook_ts_{today_str}.csv"


        return dcc.send_data_frame(df.to_csv, filename=filename, index=False)

    @app.callback(
        Output("btn-download-ts", "disabled"),
        Output("btn-download-ts", "children"),
        Output("btn-download-ts", "style"),
        Input("ts-data-scroll", "rowData"),
    )
    def toggle_download_btn(row_data):
        # If no rows: disable & show alternate text
        if not row_data or len(row_data) == 0:
            disabled = True
            label    = "No data in range to download"
            style    = {"opacity": "0.5", "cursor": "not-allowed"}
            # Or to hide: style = {"display": "none"}
        else:
            disabled = False
            label    = "Download CSV"
            style    = {}

        return disabled, label, style