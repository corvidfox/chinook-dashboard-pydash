"""
services/kpi/shared.py

Orchestrate the full KPI pipeline for dashboard use.

This module ties together core subset KPIs, group-level Top-N KPI slices,
and cohort retention KPIs into a single nested payload.  It:
  - Calls core.py to get subset-level metrics
  - Loops through each grouping (Genre, Artist, BillingCountry) to build,
    slice, and format Top-N tables
  - Accepts a precomputed cohort_df to generate retention KPIs
  - Returns a dictionary with:
      metadata_kpis, topn (nested tables), and retention_kpis

Functions:
  get_shared_kpis(conn, tbl, metrics, date_range, cohort_df, top_n, offsets) → Dict[str, Any]
"""

from typing import List, Dict, Optional, Any
import pandas as pd
from duckdb import DuckDBPyConnection

from services.logging_utils import log_msg
from services.display_utils import format_kpi_value
from services.kpis.core import get_subset_core_kpis
from services.kpis.group import get_group_kpis_full, topn_kpis_slice_topn, topn_kpis_format_display
from services.kpis.retention import get_retention_kpis

def get_shared_kpis(
    conn: DuckDBPyConnection,
    metrics: List[Dict[str, str]],
    date_range: Optional[List[str]],
    cohort_df: pd.DataFrame,
    top_n: int = 5,
    offsets: List[int] = [3, 6, 9]
) -> Dict[str, Any]:
    """
    Aggregate core metadata KPIs, Top-N group slices, and cohort retention KPIs.

    Parameters:
        conn (DuckDBPyConnection): Active DuckDB connection
        metrics (List[Dict]): Metric defs for top-N slices (each dict needs 'var_name')
        date_range (List[str] | None): [start, end] as 'YYYY-MM-DD' or None
        cohort_df (pd.DataFrame): Precomputed cohort retention data
        top_n (int): Number of top groups to include
        offsets (List[int]): Month offsets for top cohort snapshots

    Returns:
        Dict[str,Any] with keys:
          metadata_kpis, topn, retention_kpis
    """
    log_msg("[SQL - KPI PIPELINE] Starting shared KPI aggregation")

    # 1) Core subset‐level KPIs
    metadata_kpis = get_subset_core_kpis(conn, date_range)
    log_msg("   [SQL - KPI PIPELINE] Retrieved subset metadata KPIs")

    # 2) Top-N group slices
    topn_by_group: Dict[str, Dict[str, Any]] = {}
    for group in ["Genre", "Artist", "BillingCountry"]:
        log_msg(f"   [SQL - KPI PIPELINE] Generating top-{top_n} tables for {group}")

        full_df = get_group_kpis_full(conn, group, date_range)
        group_tables: Dict[str, Any] = {}

        for metric_def in metrics:
            var = metric_def["var_name"]
            topn_df = topn_kpis_slice_topn(full_df, var, top_n)
            formatted = topn_kpis_format_display(
                topn_df,
                group_var=group,
                total_revenue=float(metadata_kpis["revenue_total"])
            )
            group_tables[var] = formatted

        # add total distinct values for this group
        num_key = f"{group.lower()}_num"
        group_tables["num_vals"] = format_kpi_value(
            metadata_kpis.get(num_key, 0),
            value_type="number"
        )

        topn_by_group[f"topn_{group.lower()}"] = group_tables

    log_msg("   [SQL - KPI PIPELINE] Retrieved Top-N KPI blocks")

    # 3) Cohort retention KPIs (use passed-in cohort_df)
    retention_kpis = get_retention_kpis(
        conn=conn,
        date_range=date_range,
        cohort_df=cohort_df,
        offsets=offsets
    )
    log_msg("   [SQL - KPI PIPELINE] Retrieved cohort retention KPIs")

    log_msg("   [SQL - KPI PIPELINE] Shared KPI pipeline complete")

    return {
        "metadata_kpis":  metadata_kpis,
        "topn":           topn_by_group,
        "retention_kpis": retention_kpis
    }
