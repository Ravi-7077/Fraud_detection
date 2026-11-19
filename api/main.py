# fraud_detection/api/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os


import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from fraud_detection.config import load_config
from fraud_detection.tasks.run_rules import apply_rules
from fraud_detection.tasks.score_risk import compute_risk_score
from fraud_detection.agents.graph import run_graph, FraudState
from fraud_detection.tasks.pipeline import run_pipeline
from fraud_detection.tasks.db import (
    init_db,
    get_alerts,
    get_pending_alerts,
    get_alert,
    set_alert_status,
    save_reviewer_feedback,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"

app = FastAPI(title="Fraud Detection Service")
app.mount("/ui", StaticFiles(directory=UI_DIR), name="ui")

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Serve the professional demo page."""
    demo_path = UI_DIR / "transactions.html"
    with open(demo_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

class Transaction(BaseModel):
    transaction_id: int
    user_id: int = 0
    amount: float
    transaction_type: str = ""
    merchant_category: str = ""
    country: str = ""
    hour: int = 0
    device_risk_score: float = 0.0
    ip_risk_score: float = 0.0
    is_fraud: int | None = None

class DecisionRequest(BaseModel):
    decision: str

class FeedbackRequest(BaseModel):
    decision: str           # 'approve' | 'block' | 'override_block' | 'override_approve'
    notes: str | None = None

class FollowupRequest(BaseModel):
    question: str

cfg = load_config()

def _serialize_alert(alert: dict) -> dict:
    """Make an alert dict JSON-safe (parse agent_evidence JSON)."""
    if not alert:
        return alert
    out = dict(alert)
    ev = out.get("agent_evidence")
    if isinstance(ev, str) and ev:
        try:
            out["agent_evidence"] = json.loads(ev)
        except json.JSONDecodeError:
            out["agent_evidence"] = []
    elif ev is None:
        out["agent_evidence"] = []
    return out

@app.get("/")
def read_ui():
    path = UI_DIR / "index.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(path)

@app.get("/investigate")
def read_investigate():
    path = UI_DIR / "investigate.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Investigation UI not found")
    return FileResponse(path)

@app.get("/analytics")
def read_analytics():
    path = UI_DIR / "analytics.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Analytics UI not found")
    return FileResponse(path)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/evaluate")
def evaluate_transaction(tx: Transaction):
    """Run the fraud evaluation using the LangGraph agentic pipeline.

    The incoming transaction is wrapped in a ``FraudState`` model which is then
    passed through the graph. The graph mutates the state in‑place and returns the
    final decision and investigation note.
    """
    from fraud_detection.agents.graph import run_graph
    from fraud_detection.agents.graph import FraudState

    # Initialise the shared state from the incoming payload
    state = FraudState(
        transaction_id=str(tx.transaction_id),
        user_id=str(tx.user_id),
        amount=tx.amount,
        currency="USD",
        device_id=None,
        ip_address=None,
        merchant_id=None,
        timestamp=datetime.utcnow(),
    )

    # Run the graph – agents will populate risk scores, investigation notes, etc.
    state = run_graph(state)

    # Prepare a concise response for the UI
    return {
        "transaction": tx.dict(),
        "flagged": state.fraud_flag or False,
        "decision_reason": state.decision_reason,
        "investigation_note": getattr(state, "investigation_note", None),
        "risk_score": state.risk_score,
        "ml_score": state.ml_prediction,
        "combined_score": state.risk_score * 0.7 + (state.ml_prediction or 0) * 0.3,
    }


@app.post("/transactions")
def ingest_transaction(tx: Transaction, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_transaction, tx.dict())
    return {"status": "queued"}

@app.get("/api/alerts")
def api_get_alerts():
    try:
        init_db()
        return [_serialize_alert(a) for a in get_alerts()]
    except Exception:
        raise HTTPException(status_code=503, detail="Alert database unavailable")

@app.get("/api/alerts/pending")
def api_get_pending_alerts():
    try:
        init_db()
        return [_serialize_alert(a) for a in get_pending_alerts()]
    except Exception:
        raise HTTPException(status_code=503, detail="Alert database unavailable")

@app.get("/api/alerts/{alert_id}")
def api_get_alert(alert_id: int):
    try:
        init_db()
        alert = get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return _serialize_alert(alert)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Alert database unavailable")

@app.get("/api/alerts/{alert_id}/investigation")
def api_get_investigation(alert_id: int):
    """Return the agent's stored investigation for an alert, or run it on-demand."""
    try:
        init_db()
        alert = get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert = _serialize_alert(alert)
        if not alert.get("agent_summary"):
            # Lazy-run the agent if the alert was created before the agent existed.
            from fraud_detection.agent import investigate as _investigate
            payload = _payload_for_alert(alert)
            result = _investigate(alert, payload)
            return {"alert_id": alert_id, "investigation": result, "from_cache": False}
        return {
            "alert_id": alert_id,
            "investigation": {
                "summary": alert.get("agent_summary"),
                "recommendation": alert.get("agent_recommendation"),
                "confidence": alert.get("agent_confidence"),
                "fraud_type": alert.get("agent_fraud_type"),
                "evidence": alert.get("agent_evidence") or [],
                "run_at": alert.get("agent_run_at"),
            },
            "from_cache": True,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Investigation failed: {exc}")

@app.post("/api/alerts/{alert_id}/decision")
def api_alert_decision(alert_id: int, request: DecisionRequest):
    try:
        init_db()
        if request.decision not in {"approve", "block"}:
            raise HTTPException(status_code=400, detail="Invalid decision")
        status = "approved" if request.decision == "approve" else "blocked"
        set_alert_status(alert_id, status)
        return {"status": status}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Could not update alert status")

@app.post("/api/alerts/{alert_id}/feedback")
def api_alert_feedback(alert_id: int, request: FeedbackRequest):
    """Human-in-the-loop feedback. The reviewer's decision becomes the
    alert's status and is recorded for the RAG index."""
    try:
        init_db()
        alert = get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        decision_map = {
            "approve": ("approved", "agree"),
            "block": ("blocked", "agree"),
            "override_block": ("blocked", "override_approve"),
            "override_approve": ("approved", "override_block"),
        }
        if request.decision not in decision_map:
            raise HTTPException(
                status_code=400,
                detail="decision must be approve, block, override_block, or override_approve",
            )
        new_status, reviewer_decision = decision_map[request.decision]
        save_reviewer_feedback(
            alert_id,
            decision=reviewer_decision,
            notes=request.notes,
            new_status=new_status,
        )
        return {"status": new_status, "reviewer_decision": reviewer_decision}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not save feedback: {exc}")

@app.post("/api/alerts/{alert_id}/followup")
def api_alert_followup(alert_id: int, request: FollowupRequest):
    """Chat-style follow-up question to the agent about one alert."""
    try:
        init_db()
        alert = get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        payload = _payload_for_alert(alert)
        from fraud_detection.agent import followup as _followup
        result = _followup(alert, payload, request.question)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Follow-up failed: {exc}")

@app.get("/api/analytics/summary")
def api_analytics_summary():
    """Aggregate stats for the analytics dashboard."""
    try:
        init_db()
        alerts = get_alerts(limit=500)
        total = len(alerts)
        by_status: dict[str, int] = {}
        by_recommendation: dict[str, int] = {}
        by_fraud_type: dict[str, int] = {}
        score_buckets = [0] * 10  # 0.0-0.1, 0.1-0.2, ...
        reviewer_agree = 0
        reviewer_disagree = 0
        reviewer_total = 0
        for a in alerts:
            by_status[a.get("status") or "unknown"] = by_status.get(a.get("status") or "unknown", 0) + 1
            rec = a.get("agent_recommendation")
            if rec:
                by_recommendation[rec] = by_recommendation.get(rec, 0) + 1
            ft = a.get("agent_fraud_type")
            if ft:
                by_fraud_type[ft] = by_fraud_type.get(ft, 0) + 1
            score = float(a.get("combined_score") or 0.0)
            idx = min(9, max(0, int(score * 10)))
            score_buckets[idx] += 1
            if a.get("reviewer_decision"):
                reviewer_total += 1
                if a.get("reviewer_decision") == "agree":
                    reviewer_agree += 1
                else:
                    reviewer_disagree += 1
        agreement_rate = (reviewer_agree / reviewer_total) if reviewer_total else None
        return {
            "total": total,
            "by_status": by_status,
            "by_recommendation": by_recommendation,
            "by_fraud_type": by_fraud_type,
            "score_histogram": score_buckets,
            "reviewer": {
                "total": reviewer_total,
                "agree": reviewer_agree,
                "disagree": reviewer_disagree,
                "agreement_rate": agreement_rate,
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Analytics unavailable: {exc}")

def process_transaction(payload: dict):
    run_pipeline(payload)

def _payload_for_alert(alert: dict) -> dict:
    """Best-effort reconstruction of the original payload for an alert row.

    The pipeline only persists a few score columns; we still have enough
    to build a meaningful query for the RAG agent.
    """
    return {
        "transaction_id": alert.get("transaction_id"),
        "user_id": alert.get("transaction_id"),  # best-effort placeholder
        "amount": 0.0,
        "transaction_type": "unknown",
        "merchant_category": "unknown",
        "country": "unknown",
        "hour": 12,
        "device_risk_score": 0.0,
        "ip_risk_score": 0.0,
        "rule_score": alert.get("rule_score") or 0.0,
        "ml_score": alert.get("ml_score") or 0.0,
        "combined_score": alert.get("combined_score") or 0.0,
    }
