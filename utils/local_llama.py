# utils/local_llama.py
"""Thin wrapper for safe LLaMA generation.
Re-exports :func:`safe_generate` from ``local_llama_impl`` which provides a fallback
implementation when a real LLaMA model cannot be loaded.
"""

from .local_llama_impl import safe_generate  # noqa: F401

__all__ = ["safe_generate"]