"""
services/kpi/retention.py

Compute cohort retention heatmap data and summary retention KPIs.

This module provides:
  - Function to generate month-offset cohort retention percentages
    suitable for heatmaps or time-series analysis
  - Function to summarize customer-level retention behavior into KPIs:
      repeat counts, retention rates, repeat conversion,
      customer lifespan in months, purchase gaps, and average gaps

Functions:
  get_retention_cohort_data(conn, date_range, max_offset) → pd.DataFrame
  get_retention_kpis(conn, date_range, cohort_df, offsets) → Dict[str, str]
"""

from typing import List, Dict, Optional
import pandas as pd
from duckdb import DuckDBPyConnection

from services.logging_utils import log_msg
from services.display_utils import format_kpi_value

def get_retention_cohort_data(
    conn: DuckDBPyConnection,
    date_range: List[str],
    max_offset: Optional[int] = None
) -> pd.DataFrame:
    """
    Returns cohort retention percentages by month offset.

    Parameters:
        conn (DuckDBPyConnection): Active DuckDB connection
        date_range (List[str]): ['YYYY-MM-DD', 'YYYY-MM-DD']
        max_offset (int, optional): max month offset to include

    Returns:
        pd.DataFrame with columns:
          ['cohort_month', 'month_offset', 'num_active_customers',
           'cohort_size', 'retention_pct']
    """
    assert len(date_range) == 2 and all(isinstance(d, str) for d in date_range)
    log_msg("[SQL - COHORT] get_retention_cohort_data(): querying cohort heatmap data.")

    # Step 1: If no max_offset, compute from full dataset range
    if max_offset is None:
        bounds_sql = f"""
        SELECT MIN(i.InvoiceDate) AS min_date,
               MAX(i.InvoiceDate) AS max_date
        FROM filtered_invoices fi
        JOIN Invoice i ON fi.InvoiceId = i.InvoiceId
        """
        date_bounds = conn.execute(bounds_sql).fetchdf()
        min_date = pd.to_datetime(date_bounds["min_date"].iloc[0])
        max_date = pd.to_datetime(date_bounds["max_date"].iloc[0])
        max_offset = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month)

    # Step 2: Format SQL
    start = pd.to_datetime(date_range[0]).date()
    end   = pd.to_datetime(date_range[1]).date()

    sql = f"""
    WITH cohort_dates AS (
        SELECT CustomerId,
               DATE_TRUNC('month', MIN(InvoiceDate)) AS cohort_month
        FROM Invoice
        GROUP BY CustomerId
    ),
    cohort_sizes AS (
        SELECT cohort_month,
               COUNT(*) AS cohort_size
        FROM cohort_dates
        GROUP BY cohort_month
    ),
    activity AS (
        SELECT
            fi.CustomerId,
            c.cohort_month,
            DATE_TRUNC('month', i.InvoiceDate) AS activity_month,
            DATE_DIFF('month', c.cohort_month, i.InvoiceDate) AS month_offset
        FROM filtered_invoices fi
        JOIN Invoice i ON fi.InvoiceId = i.InvoiceId
        JOIN cohort_dates c ON fi.CustomerId = c.CustomerId
        WHERE DATE_DIFF('month', c.cohort_month, i.InvoiceDate) >= 0
          AND fi.dt BETWEEN DATE('{start}') AND DATE('{end}')
          AND DATE_DIFF('month', c.cohort_month, i.InvoiceDate) <= {max_offset}
    ),
    activity_counts AS (
        SELECT cohort_month,
               month_offset,
               COUNT(DISTINCT CustomerId) AS num_active_customers
        FROM activity
        GROUP BY cohort_month, month_offset
    )
    SELECT
        ac.cohort_month,
        ac.month_offset,
        ac.num_active_customers,
        cs.cohort_size,
        ROUND(ac.num_active_customers * 1.0 / cs.cohort_size, 4) AS retention_pct
    FROM activity_counts ac
    JOIN cohort_sizes cs ON ac.cohort_month = cs.cohort_month
    WHERE ac.month_offset > 0
    ORDER BY ac.cohort_month, ac.month_offset
    ;
    """

    df = conn.execute(sql).fetchdf()
    log_msg(f"[SQL - COHORT] Cohort retention query returned {len(df)} rows.")
    return df

def get_retention_kpis(
    conn: DuckDBPyConnection,
    date_range: List[str],
    cohort_df: pd.DataFrame,
    offsets: List[int] = [3, 6, 9]
) -> Dict[str, str]:
    """
    Computes retention KPIs, including counts, conversion, purchase gaps,
    lifespan, and top cohort retention values.

    Returns:
        Dict[str, str]: Formatted KPI display values
    """
    log_msg("[SQL - KPIs] get_retention_kpis(): querying customer retention KPIs.")

    # Fallback date range if not specified
    if not date_range:
        bounds_sql = f"""
        SELECT MIN(i.InvoiceDate) AS min_date,
               MAX(i.InvoiceDate) AS max_date
        FROM filtered_invoices e
        JOIN Invoice i ON i.InvoiceId = e.InvoiceId
        """
        bounds_df = conn.execute(bounds_sql).fetchdf()
        date_range = bounds_df.iloc[0].tolist()

    start_date = pd.to_datetime(date_range[0]).date()
    end_date   = pd.to_datetime(date_range[1]).date()

    # Load event boundaries per customer
    query = f"""
    WITH all_events AS (
        SELECT
            e.CustomerId,
            e.InvoiceId,
            DATE(i.InvoiceDate) AS dt,
            ROW_NUMBER() OVER (
              PARTITION BY e.CustomerId
              ORDER BY DATE(i.InvoiceDate), e.InvoiceId
            ) AS rn,
            COUNT(*) OVER (PARTITION BY e.CustomerId) AS total_purchases
        FROM filtered_invoices e
        JOIN Invoice i ON i.InvoiceId = e.InvoiceId
    ),
    windowed_events AS (
        SELECT
            CustomerId,
            dt,
            ROW_NUMBER() OVER (
              PARTITION BY CustomerId
              ORDER BY dt, InvoiceId
            ) AS win_rn,
            COUNT(*) OVER (PARTITION BY CustomerId) AS num_in_window
        FROM all_events
        WHERE dt BETWEEN DATE('{start_date}') AND DATE('{end_date}')
    ),
    bounds_all AS (
        SELECT
            CustomerId,
            MIN(dt) FILTER (WHERE rn = 1) AS first_date,
            MIN(dt) FILTER (WHERE rn = 2) AS second_date,
            MAX(dt) AS last_date,
            total_purchases,
            MAX(dt) FILTER (WHERE dt < DATE('{start_date}')) AS last_before_window,
            MIN(dt) FILTER (WHERE dt > DATE('{end_date}')) AS first_after_window
        FROM all_events
        GROUP BY CustomerId, total_purchases
    ),
    bounds_window AS (
        SELECT
            CustomerId,
            MAX(num_in_window) AS num_in_window,
            MAX(CASE WHEN win_rn = 1 THEN dt END) AS first_in_window,
            MAX(CASE WHEN win_rn = 2 THEN dt END) AS second_in_window,
            MAX(dt) AS last_in_window
        FROM windowed_events
        GROUP BY CustomerId
    )
    SELECT *
    FROM bounds_all a
    JOIN bounds_window w USING (CustomerId)
    WHERE w.num_in_window > 0
    ;
    """

    df = conn.execute(query).fetchdf()
    if df.empty:
        log_msg("[SQL - KPIs] No customer data for retention KPI window")
        return {}

    log_msg(f"[SQL - KPIs] Loaded {len(df)} customers with in-window data")

    # Derived flags and metrics
    df["cust_new"]     = df["num_in_window"] > 0 & df["last_before_window"].isna()
    df["repeat_any"]   = df["total_purchases"] > 1
    df["repeat_ret"]   = ~df["cust_new"] & (df["num_in_window"] > 0)
    df["repeat_conv"]  = df["cust_new"] & ((df["num_in_window"] > 1) | df["first_after_window"].isna())
    df["repeat_window"]= df["num_in_window"] > 1

    # Lifespan calculations (months)
    def month_diff(start, end):
        if pd.isna(start) or pd.isna(end):
            return None
        return (end.year - start.year) * 12 + (end.month - start.month)

    df["lifespan_mo_total"] = df.apply(
        lambda r: month_diff(r["first_date"], r["last_date"]) if r["total_purchases"] > 1 else None,
        axis=1
    )

    def lifespan_window(r):
        if pd.isna(r["last_before_window"]) and pd.isna(r["first_after_window"]):
            return month_diff(r["first_in_window"], r["last_in_window"]) if r["num_in_window"] > 1 else None
        if pd.isna(r["last_before_window"]):
            return month_diff(r["first_in_window"], end_date)
        if pd.isna(r["first_after_window"]):
            return month_diff(start_date, r["last_in_window"])
        return month_diff(start_date, end_date)

    df["lifespan_mo_window"] = df.apply(lifespan_window, axis=1)

    # Gaps and intervals (days)
    def gap(d1, d2): return (d2 - d1).days if pd.notna(d1) and pd.notna(d2) else None
    df["gap_life"] = df.apply(lambda r: gap(r["first_date"], r["second_date"]) if r["total_purchases"] > 1 else None, axis=1)
    df["gap_window"] = df.apply(lambda r: gap(r["first_in_window"], r["second_in_window"]), axis=1)
    df["gap_winback"] = df.apply(lambda r: gap(r["last_before_window"], r["first_in_window"]), axis=1)
    df["gap_retention"] = df.apply(lambda r: gap(r["last_in_window"], r["first_after_window"]), axis=1)
    df["avg_gap_life"] = df.apply(lambda r: gap(r["first_date"], r["last_date"]) / (r["total_purchases"] - 1)
                                  if r["total_purchases"] > 1 else None, axis=1)
    df["avg_gap_window"] = df.apply(lambda r: gap(r["first_in_window"], r["last_in_window"]) / (r["num_in_window"] - 1)
                                    if r["num_in_window"] > 1 else None, axis=1)

    def avg_gap_bound(r):
        if pd.isna(r["last_before_window"]) and pd.isna(r["first_after_window"]):
            return r["avg_gap_window"]
        if pd.notna(r["last_before_window"]) and pd.notna(r["first_after_window"]):
            return gap(r["last_before_window"], r["first_after_window"]) / (r["num_in_window"] + 1)
        if pd.isna(r["last_before_window"]):
            return gap(r["first_in_window"], r["first_after_window"]) / r["num_in_window"]
        if pd.isna(r["first_after_window"]):
            return gap(r["last_before_window"], r["last_in_window"]) / r["num_in_window"]
        return r["avg_gap_window"]

    df["avg_gap_bound"] = df.apply(avg_gap_bound, axis=1)

    # Aggregates
    n_total = len(df)
    n_new   = df["cust_new"].sum()
    n_repeat = df["repeat_any"].sum()
    n_ret = df["repeat_ret"].sum()
    n_conv = df["repeat_conv"].sum()
    n_rep_w = df["repeat_window"].sum()

    raw_kpis = {
        "num_cust": n_total,
        "num_new": n_new,
        "pct_new": n_new / n_total,
        "ret_n_any": n_repeat,
        "ret_rate_any": n_repeat / n_total,
        "ret_n_return": n_ret,
        "ret_rate_return": n_ret / (n_total - n_new),
        "ret_n_conv": n_conv,
        "ret_rate_conv": n_conv / n_new,
        "ret_n_window": n_rep_w,
        "ret_rate_window": n_rep_w / n_total,
        "avg_life_mo_tot": df["lifespan_mo_total"].mean(skipna=True),
        "avg_life_mo_win": df["lifespan_mo_window"].mean(skipna=True),
        "med_gap_life": df["gap_life"].median(skipna=True),
        "med_gap_window": df["gap_window"].median(skipna=True),
        "med_gap_winback": df["gap_winback"].median(skipna=True),
        "med_gap_ret": df["gap_retention"].median(skipna=True),
        "avg_gap_life": df["avg_gap_life"].mean(skipna=True),
        "avg_gap_window": df["avg_gap_window"].mean(skipna=True),
        "avg_gap_bound": df["avg_gap_bound"].mean(skipna=True),
    }

    # Format KPIs
    kpis: Dict[str, str] = {}
    for key, val in raw_kpis.items():
        if val is None:
            fmt_type = "number"  # fallback for NA
        # Explicit format for known types
        elif "pct" in key or "rate" in key:
            fmt_type = "percent"
        elif "avg" in key or "gap" in key or "life" in key:
            fmt_type = "float"
        elif isinstance(val, float) and abs(val - round(val)) < 1e-10:
            fmt_type = "number"  # float that's really an integer
        else:
            fmt_type = "number"

        kpis[key] = format_kpi_value(val, value_type=fmt_type)

    # Add top cohort retention snapshots
    for offset in offsets:
        subset = cohort_df[
            (cohort_df["month_offset"] == offset) &
            (cohort_df["retention_pct"].notna())
        ]

        if not subset.empty:
            top_row = subset.sort_values("retention_pct", ascending=False).iloc[0]
            cohort_fmt = pd.to_datetime(top_row["cohort_month"]).strftime("%b %Y")
            retention_fmt = format_kpi_value(top_row["retention_pct"], value_type="percent")
        else:
            cohort_fmt = "NA"
            retention_fmt = "NA"

        kpis[f"top_cohort_month_{offset}"] = cohort_fmt
        kpis[f"top_cohort_retention_{offset}"] = retention_fmt

    log_msg("[SQL - KPIs] get_retention_kpis(): Retention KPI aggregation complete.")
    return kpis