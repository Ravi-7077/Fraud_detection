# agents/web_data_fetcher.py
"""Web data fetcher agent.

This agent demonstrates pulling *real‑time* information from an external HTTP
endpoint and injecting it into the ``FraudState``. For the demo we query a
public JSON endpoint (ExchangeRate‑API) that returns the latest USD‑to‑EUR rate.
In a production system you could replace the URL with any site that provides
risk‑relevant data (e.g. a threat‑intel feed, currency conversion, geo‑IP
service, etc.).
"""

from __future__ import annotations

import json
import requests

from fraud_detection.agents.graph import FraudState
from fraud_detection.utils.logger import log
from fraud_detection.utils.circuit_breaker import circuit_breaker


@circuit_breaker()
def _fetch_rate() -> float:
    """Fetch the USD→EUR exchange rate.

    The function is wrapped with ``circuit_breaker`` so transient network
    failures trigger retries (default 3). If all retries fail we raise a
    ``RuntimeError`` which the caller will catch and handle gracefully.
    """
    url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return float(data["rates"].get("EUR", 1.0))


def web_data_fetcher(state: FraudState) -> FraudState:
    """Agent entry‑point added to the LangGraph pipeline.

    * Retrieves a live exchange rate.
    * Stores it under ``state.risk_factors['web_data']``.
    * Logs the activity.
    * If the fetch fails, we store a sentinel value (``None``) and continue.
    """
    try:
        rate = _fetch_rate()
        state.risk_factors["web_data"] = {"usd_to_eur": rate}
        log(f"Web data fetcher: obtained USD->EUR rate {rate}")
    except Exception as exc:  # pragma: no cover – defensive fallback
        log(f"Web data fetcher failed: {exc}")
        state.risk_factors["web_data"] = {"usd_to_eur": None}
    state.log("web_data_fetcher: added web data factor")
    return state
