import logging
import sys
from typing import Any

# Simple logger that writes to stdout. In production you can replace this with a more robust solution.
logger = logging.getLogger("fraud_detection")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def log(message: str, *args: Any, **kwargs: Any) -> None:
    """Convenient wrapper around ``logger.info``.

    All agents can import ``log`` and call ``log("some message")``.
    """
    logger.info(message, *args, **kwargs)
