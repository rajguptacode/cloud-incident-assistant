"""Sentinel's own logging — file handler under ~/.local/share/cloudops-sentinel/logs/."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import logs_dir


def setup_logging(level: int = logging.INFO) -> None:
    log_path = logs_dir() / "sentinel.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger("cloudops_sentinel")
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)