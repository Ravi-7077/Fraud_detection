# fraud_detection/tasks/run_rules.py
import yaml, os
from pathlib import Path

RULES_PATH = Path(__file__).parents[1] / "rules" / "default_rules.yaml"

def load_rules():
    if not RULES_PATH.is_file():
        return []
    with open(RULES_PATH) as f:
        return yaml.safe_load(f) or []

def apply_rules(payload: dict) -> dict:
    """Return a dict with rule results e.g. {'rule_score': 0.3, 'flag_high_amount': True}"""
    rules = load_rules()
    results = {"rule_score": 0.0}
    for rule in rules:
        # Simple example: rule = {"field": "amount", "operator": ">", "value": 1000, "score": 0.2}
        field, op, val, score = rule["field"], rule["operator"], rule["value"], rule["score"]
        if field not in payload:
            continue
        if op == ">" and payload[field] > val:
            results["rule_score"] += score
        elif op == "<" and payload[field] < val:
            results["rule_score"] += score
        # add more operators as needed
    return results