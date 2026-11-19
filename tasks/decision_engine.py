# fraud_detection/tasks/decision_engine.py
import os
from fraud_detection.config import load_config

def decide_and_act(payload: dict, alert: dict | None):
    if not alert:
        return

    cfg = load_config(os.getenv("CONFIG_YAML"))
    manual = cfg.get("enable_manual_review", True)

    if manual:
        # Leave status as pending; the UI will call approve/block later
        return

    # Auto‑decision: block if combined_score > threshold else approve
    threshold = cfg.get("risk_score_threshold", 0.7)
    if payload["combined_score"] >= threshold:
        from .block_account import block_account
        block_account(payload)
        new_status = "blocked"
    else:
        from .approve_transaction import approve_transaction
        approve_transaction(payload)
        new_status = "approved"

    # Update alert status in DB
    from .update_alert_status import set_status
    set_status(alert["id"], new_status)