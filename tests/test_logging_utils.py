# tests/test_logging_utils.py

import pytest
import logging
from services.logging_utils import log_msg

def test_log_msg_info_level(caplog, monkeypatch):
    """Test that info-level messages are logged when ENABLE_LOGGING is True."""
    monkeypatch.setattr("services.logging_utils.ENABLE_LOGGING", True)

    with caplog.at_level("INFO"):
        log_msg("Test info message", level="info")
    
    assert any("Test info message" in record.message for record in caplog.records)

def test_log_msg_cond_false(caplog, monkeypatch):
    """Test that message is not logged when cond=False."""
    monkeypatch.setattr("services.logging_utils.ENABLE_LOGGING", True)

    with caplog.at_level("INFO"):
        log_msg("Should not appear", level="info", cond=False)
    
    assert all("Should not appear" not in record.message for record in caplog.records)

def test_log_msg_logging_disabled(caplog, monkeypatch):
    """Test that message is not logged when ENABLE_LOGGING is False."""
    monkeypatch.setattr("services.logging_utils.ENABLE_LOGGING", False)

    with caplog.at_level("INFO"):
        log_msg("Should not log", level="info")
    
    assert all("Should not log" not in record.message for record in caplog.records)

def test_log_msg_invalid_level(caplog, monkeypatch):
    """Test fallback warning when invalid logging level is used."""
    monkeypatch.setattr("services.logging_utils.ENABLE_LOGGING", True)

    with caplog.at_level("WARNING"):
        log_msg("Invalid level test", level="notalevel")
    
    assert any("Logging failure" in record.message for record in caplog.records)
