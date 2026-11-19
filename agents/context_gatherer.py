# agents/context_gatherer.py
"""Context gatherer agent stub.

The real implementation would call external services to enrich the transaction
with additional user‑profile or device information. For this exercise we keep
it lightweight and just add a placeholder risk factor and a log entry.
"""

from fraud_detection.agents.graph import FraudState


def context_gatherer(state: FraudState) -> FraudState:
    """Enrich the state with mock contextual data.

    * Adds a ``risk_factors['context']`` entry.
    * Logs the operation.
    """
    # Stub: pretend we retrieved some user reputation score.
    state.risk_factors["context"] = {"user_reputation": "medium"}
    state.log("context_gatherer: added mock context risk factor")
    return state