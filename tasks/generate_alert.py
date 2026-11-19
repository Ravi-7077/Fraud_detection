# fraud_detection/tasks/generate_alert.py
import sqlalchemy as sa
from fraud_detection.config import load_config
from fraud_detection.tasks.db import init_db, Session

cfg = load_config()

def maybe_create_alert(payload: dict):
    threshold = cfg.get("risk_score_threshold", 0.7)
    if payload.get("combined_score", 0) < threshold:
        return None

    init_db()
    session = Session()
    try:
        insert_stmt = sa.text(
            """INSERT INTO alerts (transaction_id, risk_score, ml_score, combined_score, status)
               VALUES (:tid, :risk, :ml, :combined, 'pending')
               RETURNING id"""
        )
        result = session.execute(insert_stmt, {
            "tid": payload["transaction_id"],
            "risk": payload["risk_score"],
            "ml": payload["ml_score"],
            "combined": payload["combined_score"],
        })
        alert_id = result.scalar_one()
        session.commit()
        # Send email notification
        from .email_alert import send_alert_email
        send_alert_email(alert_id, payload)
        return {"id": alert_id, "payload": payload}
    finally:
        session.close()