"""Orchestrator: combines retrieval + LLM into an `investigate()` call.

`investigate(alert, payload)` is the only thing the rest of the codebase
calls. It returns a dict the API layer persists in the alerts table.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

from fraud_detection.agent.llm import call_llm_json, stub_response
from fraud_detection.agent.retriever import get_retriever
from fraud_detection.agent.playbooks import alert_to_document
from fraud_detection.tasks.db import get_alerts, save_agent_investigation

logger = logging.getLogger("agent.orchestrator")

_SYSTEM_PROMPT = (
    "You are a fraud-investigation assistant for a financial institution. "
    "You will be given transaction features, rule/risk/ML scores, and retrieved context "
    "(playbooks and similar past cases). Your job is to help a human reviewer decide. "
    "Reply with ONE JSON object, no prose, no markdown, with these exact keys:\n"
    "  recommendation: one of 'block', 'hold', 'approve'\n"
    "  confidence: a float in [0.0, 1.0]\n"
    "  summary: 1-3 sentences for the analyst\n"
    "  fraud_type: short string (e.g. 'account takeover', 'card-not-present', "
    "'mule network', 'velocity attack') or null\n"
    "  evidence: list of short strings, each citing one specific signal\n"
    "  suggested_action: one next step the analyst should take\n"
    "Be conservative: when signals conflict, recommend 'hold'. When everything is low, "
    "recommend 'approve'. Do not refuse; always return JSON."
)

_refresh_lock = threading.Lock()


def _build_query(payload: dict[str, Any]) -> str:
    parts = [
        f"transaction_id={payload.get('transaction_id')}",
        f"user_id={payload.get('user_id')}",
        f"amount={payload.get('amount')}",
        f"type={payload.get('transaction_type')}",
        f"merchant={payload.get('merchant_category')}",
        f"country={payload.get('country')}",
        f"hour={payload.get('hour')}",
        f"device_risk={payload.get('device_risk_score')}",
        f"ip_risk={payload.get('ip_risk_score')}",
        f"rule_score={payload.get('rule_score')}",
        f"ml_score={payload.get('ml_score')}",
        f"combined={payload.get('combined_score')}",
    ]
    return " ".join(str(p) for p in parts)


def _build_user_prompt(query: str, docs: list[dict[str, Any]]) -> str:
    if docs:
        ctx_lines = []
        for d in docs:
            ctx_lines.append(f"[{d.get('kind','ctx')}] {d.get('title')}: {d.get('text')}")
        ctx_block = "\n".join(ctx_lines)
    else:
        ctx_block = "(no matching context)"
    return f"TRANSACTION:\n{query}\n\nRETRIEVED CONTEXT:\n{ctx_block}"


def _refresh_index_with_past_alerts() -> None:
    """Pull decided alerts with agent summaries into the retriever."""
    with _refresh_lock:
        retriever = get_retriever()
        try:
            past = get_alerts(limit=200)
        except Exception as exc:
            logger.warning("Could not load past alerts for RAG index: %s", exc)
            return
        new_docs = []
        for a in past:
            doc = alert_to_document(a)
            if doc:
                new_docs.append(doc)
        if new_docs:
            retriever.add_documents(new_docs)


def investigate(alert: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Run RAG + LLM (or stub) and persist the result on the alert.

    Returns the investigation dict. Always returns something usable —
    on LLM errors it falls back to the deterministic stub.
    """
    query = _build_query(payload)
    _refresh_index_with_past_alerts()
    retriever = get_retriever()
    docs = retriever.query(query, top_k=5)

    user_prompt = _build_user_prompt(query, docs)
    parsed, err = call_llm_json(_SYSTEM_PROMPT, user_prompt)

    if parsed is None:
        if err:
            logger.warning("LLM call failed, using stub: %s", err)
        result = stub_response(payload, docs)
        result["llm_error"] = err
    else:
        result = {
            "recommendation": str(parsed.get("recommendation", "hold")).lower(),
            "confidence": float(parsed.get("confidence", 0.5) or 0.5),
            "summary": str(parsed.get("summary", ""))[:1000],
            "fraud_type": parsed.get("fraud_type"),
            "evidence": [str(x)[:300] for x in (parsed.get("evidence") or [])][:8],
            "suggested_action": str(parsed.get("suggested_action", ""))[:500],
            "model_used": os.getenv("LLM_PROVIDER", "stub"),
        }

    # Persist on the alert.
    try:
        save_agent_investigation(
            alert["id"],
            summary=result["summary"],
            recommendation=result["recommendation"],
            confidence=result["confidence"],
            fraud_type=result.get("fraud_type"),
            evidence=result.get("evidence", []),
        )
    except Exception as exc:
        logger.warning("Failed to persist agent investigation: %s", exc)

    # Echo what context was used (handy in the UI).
    result["retrieved_context"] = [
        {"title": d.get("title"), "kind": d.get("kind"), "score": round(d.get("score", 0), 3)}
        for d in docs
    ]
    return result


def followup(alert: dict[str, Any], payload: dict[str, Any], question: str) -> dict[str, Any]:
    """Answer a follow-up question about a specific alert (chat-style)."""
    ctx_question = _build_query(payload) + "\nAnalyst question: " + question
    retriever = get_retriever()
    docs = retriever.query(ctx_question, top_k=4)
    user_prompt = _build_user_prompt(_build_query(payload), docs)
    user_prompt += f"\n\nANALYST FOLLOW-UP:\n{question}\n\nAnswer in 2-5 sentences, plain prose."
    parsed, err = call_llm_json(
        "You are a fraud-investigation assistant. Answer the analyst's question concisely.",
        user_prompt,
    )
    if parsed is None:
        return {"answer": f"(stub) I cannot reach the LLM ({err}). Look at the evidence chips on this page.", "error": err}
    answer = parsed.get("summary") or parsed.get("answer") or json.dumps(parsed)
    return {"answer": str(answer)[:1500]}
