"""Logging setup: rotating file log so the console stays clean for the menu UI."""
import logging
from logging.handlers import RotatingFileHandler

from .config import LOG_DIR

_configured = False


def _configure():
    global _configured
    root = logging.getLogger("srms")
    root.setLevel(logging.INFO)
    root.propagate = False
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            LOG_DIR / "srms.log", maxBytes=512_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        )
    except OSError:  # read-only filesystem etc. - never crash because of logging
        handler = logging.NullHandler()
    root.addHandler(handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not _configured:
        _configure()
    return logging.getLogger(f"srms.{name}")
