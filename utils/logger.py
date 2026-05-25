"""Logging setup for CHEVEL AI."""

from __future__ import annotations

import logging
from pathlib import Path

from utils.config_manager import get_config


def setup_logger(name: str = "chevel") -> logging.Logger:
    """Create a console and file logger."""
    config = get_config()
    log_dir = config.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(Path(log_dir) / "chevel.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger

