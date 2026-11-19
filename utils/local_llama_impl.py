# utils/local_llama_impl.py
"""
Utility for generating text using an Ollama model (gemma4:31b-cloud).
If the Ollama server is unavailable or the request fails, a deterministic
fallback placeholder is returned so the rest of the pipeline continues to work.
"""

import json
import logging
import os
from typing import Callable, Optional

import httpx

logger = logging.getLogger(__name__)

# Ollama endpoint – can be overridden via env var for flexibility.
_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
_MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")


def _remote_generate(prompt: str) -> str:
    """Call the Ollama /api/generate endpoint.

    Returns the generated text on success, raises an exception on failure.
    """
    payload = {"model": _MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(_OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            # Ollama returns the generated text under the "response" key.
            return data.get("response", "").strip()
    except Exception as exc:
        logger.error(f"Ollama generation failed: {exc}")
        raise


def _load_generator() -> Optional[Callable[[str], str]]:
    """Attempt to validate the Ollama service.

    Returns a callable that performs remote generation, or ``None`` if the
    service is unreachable.
    """
    try:
        # Simple health check – ask for a short dummy generation.
        test_prompt = "test"
        _remote_generate(test_prompt)
        logger.info("Ollama server reachable; using remote generation.")
        return _remote_generate
    except Exception:
        logger.warning("Ollama server not available; falling back to stub generation.")
        return None

# Load once at import time.
_generate_fn = _load_generator()


def safe_generate(prompt: str) -> str:
    """Generate text safely using Ollama, falling back to a placeholder.

    The placeholder includes a dummy ``ML_SCORE`` to keep downstream parsing logic
    functional when the model cannot be reached.
    """
    if _generate_fn is not None:
        try:
            return _generate_fn(prompt)
        except Exception:
            # If the remote call fails for this specific prompt, fall back.
            pass
    placeholder = "ML_SCORE: 0.5"
    logger.info("Using fallback generation stub")
    return placeholder
