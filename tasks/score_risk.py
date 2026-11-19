# fraud_detection/tasks/score_risk.py
def compute_risk_score(payload: dict) -> float:
    """
    Combine rule_score with static heuristics (device/ip risk scores).
    Returns a value in [0, 1].
    """
    rule_score = payload.get("rule_score", 0.0)
    device = payload.get("device_risk_score", 0.0)
    ip = payload.get("ip_risk_score", 0.0)

    # Adjusted weighted average for higher sensitivity
    risk = 0.6 * rule_score + 0.2 * device + 0.2 * ip
    return min(max(risk, 0.0), 1.0)