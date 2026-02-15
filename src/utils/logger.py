"""
Logging utility for bookmaker scraper.
Provides consistent logging across all modules.
"""

import logging
import os
from pathlib import Path


def setup_logger(name: str, log_level: str = None) -> logging.Logger:
    """
    Set up logger with console and file handlers.

    Args:
        name: Logger name (usually __name__ from calling module)
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
    """
    # Get log level from env or use provided/default
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    log_file = os.getenv("LOG_FILE", "logs/bookmaker_scraper.log")
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger
