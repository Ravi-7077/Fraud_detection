import logging

logger = logging.getLogger("approve_transaction")


def approve_transaction(payload: dict) -> None:
    logger.info(
        "Auto-approving user_id=%s for transaction_id=%s with combined_score=%.3f",
        payload.get("user_id"),
        payload.get("transaction_id"),
        payload.get("combined_score", 0.0),
    )
