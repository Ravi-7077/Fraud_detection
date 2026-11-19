"""Thin LLM client that supports OpenAI and Anthropic with a deterministic
fallback stub. Selected via env vars:

    LLM_PROVIDER = openai | anthropic | stub    (default: stub)
    LLM_API_KEY  = ...                          (required for openai/anthropic)
    LLM_MODEL    = model name                   (default: gpt-4o-mini for openai,
                                                claude-sonnet-4-6 for anthropic)

The client never raises on transport errors. It returns a short error
string so the orchestrator can log it and fall back to the stub output.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fraud_detection.utils.local_llama import safe_generate

# --- Provider configuration ---

def _provider() -> str:
    return os.getenv("LLM_PROVIDER", "stub").lower().strip()


def _model() -> str:
    p = _provider()
    default = "gpt-4o-mini" if p == "openai" else "claude-sonnet-4-6" if p == "anthropic" else "llama-3.1-8b-instant" if p == "groq" else "stub"
    return os.getenv("LLM_MODEL", default)


def _api_key() -> str:
    return os.getenv("LLM_API_KEY", "").strip()


# --- Public interface ---

def call_llm_json(system_prompt: str, user_prompt: str) -> tuple[dict | None, str | None]:
    """Call the configured LLM and return (parsed_json, error).

    On any failure returns (None, error_message). Caller is responsible
    for the stub fallback.
    """
    p = _provider()
    if p == "openai":
        return _call_openai_json(system_prompt, user_prompt)
    if p == "anthropic":
        return _call_anthropic_json(system_prompt, user_prompt)
    if p == "groq":
        return _call_groq_json(system_prompt, user_prompt)
    if p == "ollama":
        return _call_ollama_json(system_prompt, user_prompt)
    return None, f"LLM_PROVIDER='{p}' is not a real provider; using stub"


# --- OpenAI ---

def _call_openai_json(system_prompt: str, user_prompt: str) -> tuple[dict | None, str | None]:
    key = _api_key()
    if not key:
        return None, "LLM_API_KEY not set for openai provider"
    body = json.dumps({
        "model": _model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return _safe_json_loads(text), None
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
        return None, f"openai call failed: {exc}"


# --- Anthropic ---

def _call_anthropic_json(system_prompt: str, user_prompt: str) -> tuple[dict | None, str | None]:
    key = _api_key()
    if not key:
        return None, "LLM_API_KEY not set for anthropic provider"
    body = json.dumps({
        "model": _model(),
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Anthropic returns content blocks; concatenate text blocks.
        text_parts = [
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        text = "\n".join(text_parts)
        return _safe_json_loads(text), None
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
        return None, f"anthropic call failed: {exc}"


# --- Groq ---

def _call_groq_json(system_prompt: str, user_prompt: str) -> tuple[dict | None, str | None]:
    key = _api_key()
    if not key:
        return None, "LLM_API_KEY not set for groq provider"
    body = json.dumps({
        "model": _model(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        return _safe_json_loads(text), None
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
        if hasattr(exc, "read"):
            try:
                err_msg = exc.read().decode("utf-8")
                return None, f"groq call failed: {exc} - {err_msg}"
            except Exception:
                pass
        return None, f"groq call failed: {exc}"



def _safe_json_loads(text: str) -> dict | None:
    """Try to extract a JSON object from a model response (which may have prose)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find the first {...} block.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _call_ollama_json(system_prompt: str, user_prompt: str) -> tuple[dict | None, str | None]:
    """Call the locally hosted Ollama model and parse JSON output.

    The prompts are concatenated and sent to the Ollama generate endpoint.
    Returns a parsed JSON dict or an error message.
    """
    # Combine system and user prompts as Ollama does not support chat roles.
    prompt = f"{system_prompt}\n\n{user_prompt}"
    try:
        raw_output = safe_generate(prompt)
        parsed = _safe_json_loads(raw_output)
        if parsed is None:
            return None, f"Ollama response could not be parsed as JSON: {raw_output!r}"
        return parsed, None
    except Exception as exc:
        return None, f"Ollama call failed: {exc}"
# --- Deterministic stub (used when no API key is set) ---

_STUB_SYSTEM = (
    "You are a fraud-investigation assistant. You will be given transaction features, "
    "rule/risk/ML scores, and retrieved context (playbooks and similar past cases). "
    "Decide what the human reviewer should do. Reply with one JSON object containing: "
    "recommendation (one of: 'block', 'hold', 'approve'), confidence (0.0-1.0), "
    "summary (1-3 sentences), fraud_type (short string or null), "
    "evidence (list of short strings, each citing a specific signal), "
    "suggested_action (one next thing the analyst should do). Be conservative: "
    "if signals conflict, recommend 'hold'."
)


def stub_prompts() -> tuple[str, str]:
    return _STUB_SYSTEM, "{user_prompt}"  # placeholder; real stub is below


def stub_response(payload: dict, context_docs: list[dict[str, Any]]) -> dict:
    """A rule-of-thumb recommendation when no LLM is configured.

    This is intentionally simple — it exists so the UI is usable during
    development without burning API credits, and so the human-in-the-loop
    path is exercised end-to-end.
    """
    combined = float(payload.get("combined_score", 0.0) or 0.0)
    rule = float(payload.get("rule_score", 0.0) or 0.0)
    device = float(payload.get("device_risk_score", 0.0) or 0.0)
    ip = float(payload.get("ip_risk_score", 0.0) or 0.0)
    ml = float(payload.get("ml_score", 0.0) or 0.0)
    amount = float(payload.get("amount", 0.0) or 0.0)
    hour = int(payload.get("hour", 12) or 12)

    evidence: list[str] = []
    if rule > 0:
        evidence.append(f"Rules contributed {rule:.2f} to the score")
    if device > 0.7:
        evidence.append(f"Device risk is high ({device:.2f})")
    if ip > 0.7:
        evidence.append(f"IP risk is high ({ip:.2f})")
    if amount > 1000:
        evidence.append(f"Amount is elevated (${amount:,.0f})")
    if 0 <= hour <= 5:
        evidence.append("Transaction occurred during low-activity hours")
    if ml > 0.6:
        evidence.append(f"ML model flags this as likely fraud (p={ml:.2f})")

    # Decision logic mirrors your risk formula.
    if combined >= 0.8:
        recommendation = "block"
        fraud_type = "high-confidence fraud"
        confidence = min(0.95, 0.6 + combined * 0.4)
        action = "Block the transaction and notify the analyst to confirm."
    elif combined >= 0.5:
        recommendation = "hold"
        fraud_type = "needs review"
        confidence = 0.55
        action = "Hold and review the linked device fingerprint + user history."
    else:
        recommendation = "approve"
        fraud_type = None
        confidence = max(0.5, 0.9 - combined)
        action = "Approve; close the alert if no other signals appear."

    # Mention any matching playbook so the analyst trusts the recommendation.
    matching = [d for d in context_docs if d.get("kind") == "playbook"]
    if matching:
        evidence.append(f"Matches playbook: {matching[0]['title']}")

    return {
        "recommendation": recommendation,
        "confidence": round(confidence, 3),
        "summary": (
            f"Combined score {combined:.2f} with {len(evidence)} contributing signals. "
            f"Recommendation: {recommendation.upper()}."
        ),
        "fraud_type": fraud_type,
        "evidence": evidence,
        "suggested_action": action,
        "model_used": "stub",
    }
