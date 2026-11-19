"""Seed knowledge base: rules file + fraud playbooks.

`build_seed_documents()` returns a list of dicts:
    {"id": str, "title": str, "kind": str, "text": str}

These get indexed by the retriever (TF-IDF over the union of all
documents). Past-decided alerts are also added to the index at query
time, so the more analysts decide, the smarter the agent gets.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

# -- Built-in fraud type playbooks. Edit freely. --

_PLAYBOOKS: list[dict[str, str]] = [
    {
        "id": "pb-account-takeover",
        "title": "Account takeover (ATO) playbook",
        "kind": "playbook",
        "text": (
            "Account takeover indicators: login from new device combined with high-value transfer or "
            "password reset followed by transaction within minutes. Device risk score typically above "
            "0.7 and IP risk above 0.6. Recommended action: block, force MFA challenge on next login, "
            "and lock card. Notify customer via verified channel only."
        ),
    },
    {
        "id": "pb-card-not-present",
        "title": "Card-not-present (CNP) fraud playbook",
        "kind": "playbook",
        "text": (
            "Card-not-present fraud signals: online merchant category, country mismatch with user "
            "history, transaction occurring at unusual hour (00:00-05:00 local), and amount above "
            "the user's typical spend. Recommended action: hold the transaction, request 3DS step-up, "
            "and contact cardholder. Do not auto-block if 3DS is available."
        ),
    },
    {
        "id": "pb-mule-network",
        "title": "Mule / money-mule network playbook",
        "kind": "playbook",
        "text": (
            "Mule accounts show: multiple inbound transfers followed by a fast outbound transfer, low "
            "account age, and transfers to high-risk jurisdictions. Device and IP risk may look "
            "benign because the user is real — focus on flow-of-funds. Recommended action: block "
            "outbound transfer, escalate to AML team, and file a suspicious activity note."
        ),
    },
    {
        "id": "pb-chargeback-fraud",
        "title": "Chargeback / friendly fraud playbook",
        "kind": "playbook",
        "text": (
            "Friendly fraud looks like a normal purchase from a real cardholder, then the cardholder "
            "disputes the charge. Hard to detect at the moment of the transaction. If device/IP risk "
            "are low, the agent should generally approve. If customer has prior chargebacks, flag "
            "for closer review and attach evidence for the dispute team."
        ),
    },
    {
        "id": "pb-synthetic-identity",
        "title": "Synthetic identity playbook",
        "kind": "playbook",
        "text": (
            "Synthetic identities: short account history, sparse transaction data, sudden bursts of "
            "activity. Device/IP may be clean. Recommended action: hold and request identity "
            "verification documents before releasing large transactions."
        ),
    },
    {
        "id": "pb-velocity-attack",
        "title": "Velocity / automated attack playbook",
        "kind": "playbook",
        "text": (
            "Velocity attacks: many transactions in a short window, often from one device or one IP. "
            "Device risk and IP risk are usually high. Recommended action: rate-limit the source, "
            "block the user, and add the device fingerprint to a deny list."
        ),
    },
    {
        "id": "pb-low-risk-legit",
        "title": "Looks-legitimate case playbook",
        "kind": "playbook",
        "text": (
            "When rule score, risk score, and ML score are all low and the transaction fits the "
            "user's normal pattern, the agent should recommend approve with a note. These cases "
            "should be fast-tracked and not consume reviewer attention."
        ),
    },
]


def build_seed_documents() -> list[dict[str, str]]:
    """Return playbooks + the current rules file as documents."""
    docs: list[dict[str, str]] = list(_PLAYBOOKS)

    rules_path = Path(__file__).resolve().parents[1] / "rules" / "default_rules.yaml"
    if rules_path.is_file():
        try:
            rules = yaml.safe_load(rules_path.read_text()) or []
            for i, rule in enumerate(rules):
                docs.append({
                    "id": f"rule-{i}",
                    "title": f"Rule {i+1}: {rule.get('field')} {rule.get('operator')} {rule.get('value')}",
                    "kind": "rule",
                    "text": (
                        f"Rule fires when `{rule.get('field')}` {rule.get('operator')} "
                        f"{rule.get('value')}. Adds {rule.get('score')} to the rule score."
                    ),
                })
        except Exception:
            pass
    return docs


def alert_to_document(alert: dict[str, Any]) -> dict[str, str] | None:
    """Turn a past decided alert into a retrieval document. Returns None if not useful."""
    if alert.get("status") not in ("approved", "blocked"):
        return None
    summary = (alert.get("agent_summary") or "").strip()
    if not summary:
        return None
    evidence = alert.get("agent_evidence") or []
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except Exception:
            evidence = []
    text = (
        f"Past case (txn #{alert.get('transaction_id')}, status={alert.get('status')}, "
        f"combined={alert.get('combined_score'):.3f}, fraud_type={alert.get('agent_fraud_type')}): "
        f"{summary}"
    )
    if evidence:
        text += " Evidence: " + "; ".join(str(e) for e in evidence[:5])
    return {
        "id": f"alert-{alert.get('id')}",
        "title": f"Past alert #{alert.get('id')}",
        "kind": "past_alert",
        "text": text,
    }
