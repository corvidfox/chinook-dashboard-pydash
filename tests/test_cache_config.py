# tests/test_cache_config.py

from services.cache_config import cache
from flask_caching import Cache

def test_cache_instance():
    """Test that the cache object is an instance of flask_caching.Cache."""
    assert isinstance(cache, Cache)
