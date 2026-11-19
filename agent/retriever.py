"""Tiny TF-IDF retriever.

We use scikit-learn's TF-IDF vectorizer (already a dependency) so we
don't add a new package. The retriever holds a corpus of documents
(playbooks + rules + past decided alerts) and returns the top-k most
relevant ones for a query.
"""
from __future__ import annotations

import threading
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from fraud_detection.agent.playbooks import build_seed_documents


class Retriever:
    """Thread-safe in-memory TF-IDF retriever."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._docs: list[dict[str, str]] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._refresh()

    def _refresh(self) -> None:
        self._docs = build_seed_documents()
        texts = [d["text"] for d in self._docs]
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._matrix = self._vectorizer.fit_transform(texts) if texts else None

    def add_documents(self, docs: list[dict[str, str]]) -> None:
        if not docs:
            return
        with self._lock:
            self._docs.extend(docs)
            texts = [d["text"] for d in self._docs]
            self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self._matrix = self._vectorizer.fit_transform(texts)

    def query(self, text: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            if not self._docs or self._matrix is None or self._vectorizer is None:
                return []
            q_vec = self._vectorizer.transform([text])
            sims = cosine_similarity(q_vec, self._matrix).ravel()
            if sims.size == 0:
                return []
            top_k = min(top_k, sims.size)
            idx = np.argsort(-sims)[:top_k]
            return [
                {**self._docs[i], "score": float(sims[i])}
                for i in idx
                if sims[i] > 0
            ]


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
