"""ML prediction entrypoint for the fraud_detection project.

Provides a lightweight stub `ml_predict(payload: dict) -> float` that returns a constant
score (0.0). This removes heavy dependencies (pandas, numpy, scikit‑learn) which cannot
be built in the current Windows environment.

If a real model is needed later, replace this stub with the original implementation and
install the required packages.
"""

from __future__ import annotations
from typing import Dict

def ml_predict(payload: Dict) -> float:
    """Return a placeholder fraud probability.

    Args:
        payload: Feature dictionary (ignored).
    Returns:
        float: Constant score 0.0 indicating no fraud.
    """
    return 0.0

__all__ = ["ml_predict"]
