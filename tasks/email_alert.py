# fraud_detection/tasks/email_alert.py
import logging
import smtplib
from email.message import EmailMessage

from fraud_detection.config import load_config

logger = logging.getLogger("email_alert")

def send_alert_email(alert_id: int, payload: dict):
    cfg = load_config()
    email_cfg = cfg["email"]
    msg = EmailMessage()
    msg["Subject"] = f"Fraud Alert #{alert_id}"
    msg["From"] = email_cfg["from_addr"]
    msg["To"] = email_cfg["to_addrs"]
    body = f"""
Alert ID: {alert_id}
Transaction ID: {payload['transaction_id']}
User ID: {payload['user_id']}
Combined Score: {payload['combined_score']:.3f}
Details: {payload}
"""
    msg.set_content(body)

    try:
        with smtplib.SMTP(email_cfg["smtp_host"], int(email_cfg["smtp_port"])) as server:
            server.starttls()
            server.login(email_cfg["smtp_user"], email_cfg["smtp_password"])
            server.send_message(msg)
        logger.info("Alert email sent for alert %s", alert_id)
    except Exception as exc:
        logger.warning("Skipping email send for alert %s: %s", alert_id, exc)
