from src.evaluation import metrics


class _DummyJobBertModel:
    def encode(self, texts, normalize_embeddings=True):  # noqa: D401, ANN001
        vectors = {
            "job ad with python and sql": [1.0, 0.0],
            "assignment that uses python and sql": [1.0, 0.0],
        }
        return [vectors[text] for text in texts]


def test_build_assignment_kpis_includes_jobbert_score(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "_load_sentence_transformer", lambda model_name: _DummyJobBertModel())

    kpis = metrics.build_assignment_kpis(
        cleaned_text="job ad with python and sql",
        assignment_text="assignment that uses python and sql",
        parsed_data={},
        retrieved_examples=[],
        reviewer_rating=4,
        llm_judge_score=4.25,
        generation_latency_seconds=1.23,
        judge_latency_seconds=0.45,
        workflow_latency_seconds=1.78,
    )

    assert kpis["jobbert_v3_score"] == 1.0
    assert kpis["model_score"] == 1.0
    assert kpis["reviewer_rating"] == 4.0
    assert kpis["llm_judge_score"] == 4.25
    assert kpis["generation_latency_seconds"] == 1.23
    assert kpis["judge_latency_seconds"] == 0.45
    assert kpis["workflow_latency_seconds"] == 1.78


def test_compute_skill_coverage_uses_skill_overlap() -> None:
    score = metrics.compute_skill_coverage(
        job_text="Python SQL React",
        assignment_text="The assignment uses Python and SQL only.",
    )

    assert score == 0.6667


def test_compute_skill_coverage_supports_crm_terms() -> None:
    score = metrics.compute_skill_coverage(
        job_text="CRM consultant with Salesforce and HubSpot experience",
        assignment_text="The assignment covers Salesforce configuration and HubSpot integration.",
    )

    assert score and score > 0


def test_retrieval_metrics_are_none_without_examples() -> None:
    assert metrics.compute_retrieval_semantic_avg([]) is None
    assert metrics.compute_retrieval_score_avg([]) is None
    assert metrics.compute_retrieval_domain_precision({}, []) is None


def test_compute_reviewer_rating_returns_numeric_value() -> None:
    assert metrics.compute_reviewer_rating(5) == 5.0
    assert metrics.compute_reviewer_rating(None) is None
