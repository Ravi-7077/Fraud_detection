"""NeMo-style RAG investigation agent for fraud alerts.

Public entry point: `investigate(alert: dict, payload: dict) -> dict`.

The agent is intentionally an *investigative assistant* — it never
auto-blocks or auto-approves. It produces a structured recommendation
that a human reviewer can accept, reject, or override.
"""
from fraud_detection.agent.orchestrator import investigate, followup

__all__ = ["investigate", "followup"]
