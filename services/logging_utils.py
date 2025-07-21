"""
logging_utils.py

Handles logging behavior for the Chinook dashboard.
Respects environment-level logging flags via ENABLE_LOGGING in config.
"""

import logging
from config import ENABLE_LOGGING

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def log_msg(msg: str, level: str = "info", cond: bool = True) -> None:
    """
    Logs a message conditionally based on config and user-defined logic.

    Parameters:
        msg (str): Message to log.
        level (str): Logging level (e.g. 'info', 'warning', 'error').
        cond (bool): Additional condition to trigger logging.

    Returns:
        None
    """
    try:
        if ENABLE_LOGGING and cond:
            getattr(logging, level)(msg)
    except Exception as e:
        logging.warning(f"Logging failure: {e}")
