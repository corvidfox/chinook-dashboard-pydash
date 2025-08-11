# tests/test_cached_funs.py

import pytest
from unittest.mock import MagicMock
import sys

# Patch cache.memoize BEFORE importing cached_funs
from services import cache_config
cache_config.cache.memoize = lambda *args, **kwargs: (lambda f: f)

# Now import the functions
from services.cached_funs import (
    get_retention_cohort_data_cached,
    get_shared_kpis_cached
)

def test_get_retention_cohort_data_cached_basic(prepare_full_data_context):
    """Test that retention cohort data is returned with a valid hash."""
    date_range = ("2009-01-01", "2013-12-31")
    df, signature = get_retention_cohort_data_cached(date_range)

    assert df is not None
    assert not df.empty
    assert "cohort_month" in df.columns
    assert "retention_pct" in df.columns
    assert isinstance(signature, str)

def test_get_retention_cohort_data_cached_with_offset(prepare_full_data_context):
    """Test retention data with a max_offset filter."""
    date_range = ("2009-01-01", "2013-12-31")
    df, signature = get_retention_cohort_data_cached(date_range, max_offset=6)

    assert df["month_offset"].max() <= 6

def test_get_shared_kpis_cached_basic(prepare_full_data_context):
    """Test that shared KPIs are returned with a valid hash."""
    date_range = ("2009-01-01", "2013-12-31")
    offsets = (0, 1, 2)
    events_hash = "dummy_hash"

    bundle, kpi_hash = get_shared_kpis_cached(
        events_hash=events_hash,
        date_range=date_range,
        max_offset=6,
        offsets=offsets
    )

    assert isinstance(bundle, dict)
    assert "metadata_kpis" in bundle
    assert "topn" in bundle
    assert "retention_kpis" in bundle
    assert isinstance(kpi_hash, str)
