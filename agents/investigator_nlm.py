"""Investigator NLM agent – replaces the OpenAI call with local LLaMA inference.
The node receives a :class:`FraudState` instance, builds a prompt from the
transaction and risk‑factor data, and invokes ``utils.local_llama.safe_generate``.
The generated text is stored in ``state.investigation_note`` and, if present,
an optional ``ML_SCORE`` is extracted into ``state.ml_score``.
"""
from __future__ import annotations
from typing import Any
from utils.logger import log
from utils.local_llama import safe_generate
from utils.local_llama import safe_generate

_PROMPT_TEMPLATE = (
    "You are a fraud analyst. Given the following transaction details and risk factors, "
    "write a concise investigation note (max 3 sentences). Also, if possible, provide a "
    "risk score between 0 and 1 in the format 'ML_SCORE: <value>'.\n\n"
    "Transaction:\n{transaction}\n\nRisk factors:\n{risk_factors}\n"
)
def _build_prompt(state: Any) -> str:
    """Create the prompt string from the :class:`FraudState`."""
    transaction_repr = repr(state.transaction)
    risk_factors_repr = repr(state.risk_factors)
    return _PROMPT_TEMPLATE.format(
        transaction=transaction_repr,
        risk_factors=risk_factors_repr,
    )
def investigator_nlm(state: Any) -> Any:
    """LangGraph node that adds an investigation note using the local LLaMA model."""
    log("[investigator_nlm] Generating investigation note with local LLaMA")
    prompt = _build_prompt(state)
    # Use the safe wrapper – it will fall back to a stub if the model cannot load.
    raw_output = safe_generate(prompt)
    log(f"[investigator_nlm] Raw LLaMA output: {raw_output}")
    # Store the full note
    state.investigation_note = raw_output
    # Attempt to extract an optional ML_SCORE
    ml_score: float | None = None
    if "ML_SCORE" in raw_output:
        try:
            # Expected pattern: 'ML_SCORE: 0.73' (any whitespace)
            token = raw_output.split("ML_SCORE")[-1]
            token = token.replace(":", " ").strip().split()[0]
            ml_score = float(token)
        except Exception:
            ml_score = None
    state.ml_score = ml_score
    return state
"""Public API – the LangGraph builder imports ``investigator_nlm`` from this module,
so the function name must remain unchanged."""