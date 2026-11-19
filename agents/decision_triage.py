from __future__ import annotations

from typing import Any

from fraud_detection.agents.graph import FraudState
from fraud_detection.utils.circuit_breaker import circuit_breaker
from fraud_detection.utils.logger import logger


@circuit_breaker()
def decision_triage(state: FraudState) -> FraudState:
    """Final decision agent that determines fraud flag and decision reason.

    Simple rule‑based policy (configurable later):
    - If ``risk_score`` >= 0.7 or ``ml_prediction`` >= 0.7 -> flag fraud.
    - Otherwise, not fraud.
    The ``decision_reason`` provides a brief explanation.
    """
    logger.info("Decision Triage: evaluating final decision")
    # Default thresholds (could be moved to config.yaml)
    risk_threshold = 0.7
    ml_threshold = 0.7
    fraud = False
    reasons = []
    if state.risk_score is not None and state.risk_score >= risk_threshold:
        fraud = True
        reasons.append(f"Risk score {state.risk_score:.2f} >= {risk_threshold}")
    if state.ml_prediction is not None and state.ml_prediction >= ml_threshold:
        fraud = True
        reasons.append(f"ML prediction {state.ml_prediction:.2f} >= {ml_threshold}")
    state.fraud_flag = fraud
    state.decision_reason = ", ".join(reasons) if reasons else "Score below thresholds"
    state.log("Decision triage completed")
    return state
