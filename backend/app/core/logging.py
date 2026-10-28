"""Centralised logging setup so every module shares one consistent format."""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    """Install a single stdout StreamHandler on the root logger (idempotent).

    Uvicorn configures its own loggers, but the application modules emit
    through the root logger; configuring it here keeps app + uvicorn logs
    in the same format.
    """
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root.addHandler(handler)
