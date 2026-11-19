# agents/velocity_sequence.py
"""Velocity sequence agent.

This stub calculates a simplistic velocity‑based risk factor. In a production
system you would query recent transaction history for the same user/device and
derive a score. Here we use the transaction amount as a proxy.
"""

from fraud_detection.agents.graph import FraudState


def velocity_sequence(state: FraudState) -> FraudState:
    """Add a mock velocity risk factor.

    The logic is intentionally simple: higher amounts increase the velocity
    risk. The result is stored in ``state.risk_factors['velocity']`` and the
    ``state.risk_score`` is nudged upward.
    """
    # Simple heuristic: amount > $1000 adds 0.2 to risk, else 0.0.
    velocity_risk = 0.2 if state.amount > 1000 else 0.0
    state.risk_factors["velocity"] = {"amount": state.amount, "risk": velocity_risk}
    # Update aggregate risk_score if it already exists.
    if state.risk_score is None:
        state.risk_score = velocity_risk
    else:
        # Blend the new risk with existing one (average for demo).
        state.risk_score = (state.risk_score + velocity_risk) / 2
    state.log("velocity_sequence: computed velocity risk")
    return state
