"""
Cached wrappers for core service functions.

This module provides memoized versions of:
  - get_events_shared
  - get_retention_cohort_data
  - get_shared_kpis

Each wrapper builds cache keys from simple, hashable inputs and
opens a fresh DuckDB connection per call.
"""

from typing import Any, Dict, Optional, Sequence, Tuple

import pandas as pd
from services.cache_config import cache
from services.db import get_connection
from services.sql_core import get_events_shared as _get_events_shared
from services.sql_core import hash_dataframe, hash_kpi_bundle
from services.kpis.shared import get_shared_kpis as _get_shared_kpis
from services.kpis.retention import get_retention_cohort_data as \
    _get_retention_cohort_data
from services.metadata import get_filter_metadata

FILTER_META = get_filter_metadata()
METRICS_DICT = FILTER_META["metrics"]

@cache.memoize()
def get_events_shared_cached(
    where_clauses: Tuple[str, ...],
    previous_hash: Optional[str]
) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Fetch filtered events and cache the result.

    Parameters:
        where_clauses: Tuple of SQL WHERE clauses (must be hashable).
        previous_hash: Prior hash of the invoice set (or None).

    Returns:
        (DataFrame or None, new_hash) as in get_events_shared.
    """
    conn = get_connection()
    return _get_events_shared(
        conn=conn,
        where_clauses=list(where_clauses),
        previous_hash=previous_hash,
    )


@cache.memoize()
def get_retention_cohort_data_cached(
    date_range: Tuple[str, ...],
    max_offset: Optional[int] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Return cohort retention data, memoized by date_range and offset.
    Also returns hash fingerprint.

    Parameters:
        date_range: Tuple of [start_date, end_date] strings.
        max_offset: Max month offset to include (or None).

    Returns:
        Tuple:
            DataFrame with columns
            ['cohort_month', 'month_offset', 'num_active_customers',
            'cohort_size', 'retention_pct'].
            Hash fingerprint
    """
    conn = get_connection()
    df = _get_retention_cohort_data(
        conn=conn,
        date_range=list(date_range),
        max_offset=max_offset,
    )
    signature = hash_dataframe(df)
    return df, signature


@cache.memoize()
def get_shared_kpis_cached(
    events_hash: str,
    date_range: Tuple[str, str],
    max_offset: Optional[int],
    offsets: Tuple[int, ...],
    ) -> Tuple[Dict[str, Any], str]:
    """
    Wrap get_shared_kpis, fetching the cohort DataFrame under the hood.
    Also returns hash fingerprint.

    Parameters:
        events_hash: hash of the filtered events table.
        date_range: tuple of [start_date, end_date] strings.
        max_offset: max month offset for cohort retention.
        offsets: tuple of month offsets for KPI snapshots.

    Returns:
        Tuple:
            Dict with keys 'metadata_kpis', 'topn', 'retention_kpis'.
            Hash fingerprint.
    """
    conn = get_connection()
    cohort_df, cohort_hash = get_retention_cohort_data_cached(
        date_range=date_range,
        max_offset=max_offset
    )

    bundle = _get_shared_kpis(
        conn=conn,
        metrics=list(tuple(METRICS_DICT)),
        date_range=list(date_range),
        cohort_df=cohort_df,
        top_n=5,
        offsets=list(offsets),
    )

    kpi_hash = hash_kpi_bundle(bundle)
    return bundle, kpi_hash