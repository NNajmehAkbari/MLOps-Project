from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from src.utils.config import get_settings


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _cosine_similarity(left_vector, right_vector) -> float:
    left = [float(value) for value in left_vector]
    right = [float(value) for value in right_vector]
    size = min(len(left), len(right))
    if size == 0:
        return 0.0

    dot_product = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0

    return dot_product / (left_norm * right_norm)


class _SimpleEmbeddingModel:
    def encode(self, texts, normalize_embeddings: bool = True):  # noqa: ANN001
        tokens_per_text = [_tokenize(text) for text in texts]
        vocabulary: dict[str, int] = {}

        for tokens in tokens_per_text:
            for token in tokens:
                if token not in vocabulary:
                    vocabulary[token] = len(vocabulary)

        vectors = []
        for tokens in tokens_per_text:
            counts = Counter(tokens)
            vector = [0.0] * len(vocabulary)
            for token, count in counts.items():
                vector[vocabulary[token]] = float(count)

            if normalize_embeddings:
                norm = math.sqrt(sum(value * value for value in vector))
                if norm:
                    vector = [value / norm for value in vector]

            vectors.append(vector)

        return vectors


_EMBEDDING_MODEL: Any | None = None


def get_embedding_model() -> Any:
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        settings = get_settings()
        if settings.use_sentence_transformers:
            try:
                from sentence_transformers import SentenceTransformer

                _EMBEDDING_MODEL = SentenceTransformer("BAAI/bge-small-en-v1.5")
            except Exception:
                _EMBEDDING_MODEL = _SimpleEmbeddingModel()
        else:
            _EMBEDDING_MODEL = _SimpleEmbeddingModel()
    return _EMBEDDING_MODEL


def build_candidate_text(pair) -> str:
    parts = [
        f"domain: {getattr(pair, 'domain', '')}",
        f"subdomain: {getattr(pair, 'subdomain', '')}",
        f"seniority: {getattr(pair, 'seniority', '')}",
        getattr(pair, "job_ad_text", ""),
        getattr(pair, "assignment_text", ""),
    ]
    return "\n".join(part for part in parts if part)


def compute_similarity_scores(query_text: str, candidate_pairs) -> list[float]:
    if not candidate_pairs:
        return []

    model = get_embedding_model()

    query_text_for_embedding = (
        f"Represent this job advertisement for retrieving similar example pairs: {query_text}"
    )
    candidate_texts = [build_candidate_text(pair) for pair in candidate_pairs]

    query_embedding = model.encode(
        [query_text_for_embedding],
        normalize_embeddings=True,
    )

    candidate_embeddings = model.encode(
        candidate_texts,
        normalize_embeddings=True,
    )

    query_vector = []
    if query_embedding is not None:
        try:
            if len(query_embedding) > 0:
                query_vector = query_embedding[0]
        except TypeError:
            query_vector = query_embedding

    return [
        float(_cosine_similarity(query_vector, candidate_vector))
        for candidate_vector in candidate_embeddings
    ]
