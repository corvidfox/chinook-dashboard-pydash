"""
logging_utils.py

Provides a wrapper for logging behavior throughout the dashboard.
Supports conditional logging controlled by `enable_logging` in config,
and includes safe error handling to prevent logging failures.
"""

import logging
# Try importing enable_logging, fall back to default
try:
    from config import enable_logging
except ImportError:
    enable_logging = False 

# Configure logging format and default level
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def log_msg(msg: str, level: str = "info", cond: bool = True) -> None:
    """Logs a message to the console if logging is enabled and condition is met.

    Args:
        msg (str): The message to be logged.
        level (str, optional): Logging level (e.g., 'info', 'warning', 'error'). Defaults to 'info'.
        cond (bool, optional): An optional condition. If False, skips logging. Defaults to True.

    Raises:
        None: Silently ignores errors during logging and outputs a warning instead.
    """
    try:
        if enable_logging and cond:
            getattr(logging, level)(msg)
    except Exception as e:
        logging.warning(f"Logging failure: {e}")
