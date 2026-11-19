# fraud_detection/tasks/pipeline.py
"""Pipeline orchestrator for a single transaction.
It sequentially invokes:
1. Rule checks
2. Risk scoring
3. ML detection
4. Alert generation
5. NeMo RAG investigation agent (when an alert is created)
6. Decision engine (auto or manual)
"""
import logging
from typing import Dict

from fraud_detection.tasks.run_rules import apply_rules
from fraud_detection.tasks.score_risk import compute_risk_score
from fraud_detection.tasks.run_ml import ml_predict
from fraud_detection.tasks.generate_alert import maybe_create_alert
from fraud_detection.tasks.decision_engine import decide_and_act

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline")

def run_pipeline(payload: Dict):
    logger.info("Starting pipeline for transaction %s", payload.get("transaction_id"))
    # 1. Rule checks
    rule_results = apply_rules(payload)
    payload.update(rule_results)
    # 2. Risk scoring
    risk_score = compute_risk_score(payload)
    payload["risk_score"] = risk_score
    # 3. ML detection
    ml_score = ml_predict(payload)
    payload["ml_score"] = ml_score
    # 4. Combine scores (weighted average)
    combined_score = 0.7 * risk_score + 0.3 * ml_score
    payload["combined_score"] = combined_score
    # 5. Alert generation
    alert = maybe_create_alert(payload)
    # 5b. NeMo RAG investigation (advisory only — never auto-blocks here)
    if alert:
        try:
            from fraud_detection.agent import investigate as _investigate
            _investigate(alert, payload)
        except Exception as exc:
            logger.warning("Agent investigation failed: %s", exc)
    # 6. Decision engine (auto or manual)
    decide_and_act(payload, alert)
    logger.info("Pipeline completed for transaction %s", payload.get("transaction_id"))
