"""Logging Configuration for Solar Analytics Platform."""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .constants import LOG_LEVEL, LOG_FORMAT, LOG_FILE, LOG_RETENTION_DAYS


def setup_logging(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    retention_days: int = LOG_RETENTION_DAYS,
) -> logging.Logger:
    """
    Configure logging for a module.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        retention_days: Days to retain logs

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level or LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level or LOG_LEVEL)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file or LOG_FILE:
        log_path = Path(log_file or LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=7,  # Keep 7 backups
        )
        file_handler.setLevel(level or LOG_LEVEL)
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# Create module-level logger
logger = setup_logging(__name__)
