from __future__ import annotations

from src.retrieval.embedding_service import compute_similarity_scores


class _ArrayLikeEmbedding:
    def __init__(self, vectors):
        self._vectors = vectors

    def __len__(self):
        return len(self._vectors)

    def __getitem__(self, index):
        return self._vectors[index]

    def __iter__(self):
        return iter(self._vectors)

    def __bool__(self):
        raise ValueError("The truth value of an array with more than one element is ambiguous")


class _DummyEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):  # noqa: ANN001
        if len(texts) == 1:
            return _ArrayLikeEmbedding([[1.0, 0.0]])
        return _ArrayLikeEmbedding([[1.0, 0.0] for _ in texts])


def test_compute_similarity_scores_handles_array_like_embeddings(monkeypatch) -> None:
    monkeypatch.setattr("src.retrieval.embedding_service.get_embedding_model", lambda: _DummyEmbeddingModel())

    scores = compute_similarity_scores("hello world", ["candidate one", "candidate two"])

    assert scores == [1.0, 1.0]
