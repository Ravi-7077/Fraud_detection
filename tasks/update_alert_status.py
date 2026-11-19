import logging
from sqlalchemy import text

from fraud_detection.tasks.db import Session

logger = logging.getLogger("update_alert_status")


def set_status(alert_id: int, status: str) -> None:
    session = Session()
    try:
        stmt = text("UPDATE alerts SET status = :status WHERE id = :id")
        session.execute(stmt, {"status": status, "id": alert_id})
        session.commit()
        logger.info("Alert %s updated to %s", alert_id, status)
    finally:
        session.close()
