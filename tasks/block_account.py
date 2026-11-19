import logging

logger = logging.getLogger("block_account")


def block_account(payload: dict) -> None:
    logger.warning(
        "Auto-blocking user_id=%s for transaction_id=%s with combined_score=%.3f",
        payload.get("user_id"),
        payload.get("transaction_id"),
        payload.get("combined_score", 0.0),
    )
