from __future__ import annotations

# pyrefly: ignore [missing-import]
import sqlalchemy as sa
# pyrefly: ignore [missing-import]
from sqlalchemy import text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker

from fraud_detection.config import load_config
#C:\fraud_detection\fraud_detection\config.py

import os


cfg = load_config()
pg_host = cfg.get('postgres', {}).get('host', 'localhost')
if pg_host == 'db':
    pg_host = 'localhost'

pg_url = (
    f"postgresql+psycopg://{cfg.get('postgres', {}).get('user', 'fraud_user')}:{cfg.get('postgres', {}).get('password', 'fraud_pass')}@"
    f"{pg_host}:{cfg.get('postgres', {}).get('port', 5432)}/{cfg.get('postgres', {}).get('database', 'fraud_db')}"
)

try:
    # Try connecting with a short 2-second timeout to see if Postgres is available
    test_engine = sa.create_engine(pg_url, connect_args={"connect_timeout": 2})
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine = test_engine
    print("Database: Connected to PostgreSQL")
except Exception as e:
    sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fraud_db.sqlite")
    engine = sa.create_engine(f"sqlite:///{sqlite_path}")
    print(f"Database: PostgreSQL connection failed ({e}). Falling back to SQLite: {sqlite_path}")

Session = sessionmaker(bind=engine, future=True)


# Additive columns added when the agent module was introduced. Each entry is
# (column_name, sql_type). init_db() runs them with IF NOT EXISTS so it's safe
# to call against an existing schema.
_AGENT_COLUMNS: list[tuple[str, str]] = [
    ("agent_summary", "TEXT"),
    ("agent_recommendation", "VARCHAR(32)"),
    ("agent_confidence", "DOUBLE PRECISION"),
    ("agent_fraud_type", "VARCHAR(64)"),
    ("agent_evidence", "TEXT"),           # JSON-encoded list of strings
    ("agent_run_at", "TIMESTAMP WITH TIME ZONE"),
    ("reviewer_decision", "VARCHAR(32)"),
    ("reviewer_notes", "TEXT"),
    ("reviewer_decided_at", "TIMESTAMP WITH TIME ZONE"),
]


def init_db() -> None:
    is_sqlite = engine.dialect.name == 'sqlite'
    with engine.begin() as conn:
        if is_sqlite:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER NOT NULL,
                    risk_score REAL NOT NULL,
                    ml_score REAL NOT NULL,
                    combined_score REAL NOT NULL,
                    status VARCHAR(64) NOT NULL DEFAULT 'pending',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    agent_summary TEXT,
                    agent_recommendation VARCHAR(32),
                    agent_confidence REAL,
                    agent_fraud_type VARCHAR(64),
                    agent_evidence TEXT,
                    agent_run_at DATETIME,
                    reviewer_decision VARCHAR(32),
                    reviewer_notes TEXT,
                    reviewer_decided_at DATETIME
                )
                """
            ))
        else:
            conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    transaction_id INTEGER NOT NULL,
                    risk_score DOUBLE PRECISION NOT NULL,
                    ml_score DOUBLE PRECISION NOT NULL,
                    combined_score DOUBLE PRECISION NOT NULL,
                    status VARCHAR(64) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
                )
                """
            ))
            for col_name, col_type in _AGENT_COLUMNS:
                conn.execute(text(
                    f"ALTER TABLE alerts ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                ))


def _alert_select_columns() -> str:
    base = "id, transaction_id, risk_score, ml_score, combined_score, status, created_at"
    agent_cols = ", ".join(name for name, _ in _AGENT_COLUMNS)
    return f"{base}, {agent_cols}"


def get_alerts(limit: int = 100) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(
            f"SELECT {_alert_select_columns()} "
            "FROM alerts ORDER BY created_at DESC LIMIT :limit"
        ), {"limit": limit})
        return [dict(row._mapping) for row in result]


def get_pending_alerts(limit: int = 100) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(
            f"SELECT {_alert_select_columns()} "
            "FROM alerts WHERE status = 'pending' ORDER BY created_at DESC LIMIT :limit"
        ), {"limit": limit})
        return [dict(row._mapping) for row in result]


def get_alert(alert_id: int) -> dict | None:
    """Return one alert by id, or None if not found."""
    with engine.connect() as conn:
        result = conn.execute(text(
            f"SELECT {_alert_select_columns()} FROM alerts WHERE id = :id"
        ), {"id": alert_id})
        row = result.first()
        return dict(row._mapping) if row else None


def set_alert_status(alert_id: int, status: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE alerts SET status = :status WHERE id = :id"
        ), {"status": status, "id": alert_id})


def save_agent_investigation(
    alert_id: int,
    *,
    summary: str,
    recommendation: str,
    confidence: float,
    fraud_type: str | None,
    evidence: list[str],
) -> None:
    """Persist the agent's investigation output on an alert row."""
    import json as _json
    is_sqlite = engine.dialect.name == 'sqlite'
    now_func = "CURRENT_TIMESTAMP" if is_sqlite else "now()"
    with engine.begin() as conn:
        conn.execute(text(
            f"""
            UPDATE alerts SET
                agent_summary = :summary,
                agent_recommendation = :recommendation,
                agent_confidence = :confidence,
                agent_fraud_type = :fraud_type,
                agent_evidence = :evidence,
                agent_run_at = {now_func}
            WHERE id = :id
            """
        ), {
            "summary": summary,
            "recommendation": recommendation,
            "confidence": float(confidence),
            "fraud_type": fraud_type,
            "evidence": _json.dumps(evidence or []),
            "id": alert_id,
        })


def save_reviewer_feedback(
    alert_id: int,
    *,
    decision: str,
    notes: str | None,
    new_status: str | None = None,
) -> None:
    """Record the human reviewer's decision and (optionally) update status."""
    is_sqlite = engine.dialect.name == 'sqlite'
    now_func = "CURRENT_TIMESTAMP" if is_sqlite else "now()"
    with engine.begin() as conn:
        params = {"decision": decision, "notes": notes, "id": alert_id}
        set_status_clause = ""
        if new_status:
            set_status_clause = ", status = :status"
            params["status"] = new_status
        conn.execute(text(
            f"""
            UPDATE alerts SET
                reviewer_decision = :decision,
                reviewer_notes = :notes,
                reviewer_decided_at = {now_func}
                {set_status_clause}
            WHERE id = :id
            """
        ), params)
