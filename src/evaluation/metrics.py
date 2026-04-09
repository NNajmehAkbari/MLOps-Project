from __future__ import annotations

import re
import math
from functools import lru_cache
from statistics import mean
from typing import Any

from src.retrieval.embedding_service import get_embedding_model
from src.utils.config import get_settings


KNOWN_SKILLS = {
    "python",
    "java",
    "go",
    "javascript",
    "typescript",
    "react",
    "vue",
    "angular",
    "html",
    "css",
    "nodejs",
    "fastapi",
    "flask",
    "django",
    "spring",
    "kotlin",
    "swift",
    "flutter",
    "pandas",
    "numpy",
    "scikit-learn",
    "pyspark",
    "spark",
    "airflow",
    "sql",
    "etl",
    "docker",
    "kubernetes",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "helm",
    "microservices",
    "api",
    "graphql",
    "databricks",
    "mlflow",
    "machine learning",
    "data engineering",
    "data science",
    "artificial intelligence",
    "crm",
    "salesforce",
    "hubspot",
    "microsoft dynamics",
    "marketing automation",
    "customer support",
    "lead scoring",
    "lead qualification",
    "lead management",
    "pipeline management",
    "customer relationship management",
    "digital sales",
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("node.js", "nodejs")
    text = text.replace("next.js", "nextjs")
    text = text.replace("ci/cd", "cicd")
    return text


def extract_skills(text: str) -> set[str]:
    text = normalize_text(text)
    found: set[str] = set()

    for skill in KNOWN_SKILLS:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.add(skill)

    return found


def compute_retrieval_semantic_avg(retrieved_examples: list[dict[str, Any]]) -> float | None:
    if not retrieved_examples:
        return None

    scores = [
        float(item.get("semantic_score", 0.0))
        for item in retrieved_examples
        if item.get("semantic_score") is not None
    ]
    return round(mean(scores), 4) if scores else None


def compute_retrieval_score_avg(retrieved_examples: list[dict[str, Any]]) -> float | None:
    if not retrieved_examples:
        return None

    scores = [
        float(item.get("score", 0.0))
        for item in retrieved_examples
        if item.get("score") is not None
    ]
    return round(mean(scores), 4) if scores else None


def compute_retrieval_domain_precision(
    parsed_data: dict[str, Any],
    retrieved_examples: list[dict[str, Any]],
) -> float:
    if not retrieved_examples:
        return None

    expected_subdomain = (parsed_data.get("subdomain") or "").strip().lower()
    expected_domain = (parsed_data.get("domain") or "").strip().lower()

    if not expected_subdomain and not expected_domain:
        return None

    hits = 0
    for item in retrieved_examples:
        item_subdomain = (item.get("subdomain") or "").strip().lower()
        item_domain = (item.get("domain") or "").strip().lower()

        if expected_subdomain and item_subdomain == expected_subdomain:
            hits += 1
        elif expected_domain and item_domain == expected_domain:
            hits += 1

    return round(hits / len(retrieved_examples), 4)


def _flatten_skill_context(parsed_data: dict[str, Any] | None) -> str:
    if not parsed_data:
        return ""

    parts: list[str] = []
    for key in ("required_skills", "preferred_skills", "tools"):
        value = parsed_data.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value if str(item).strip())
        elif value:
            parts.append(str(value))

    for key in ("job_title", "domain", "subdomain", "seniority"):
        value = parsed_data.get(key)
        if value:
            parts.append(str(value))

    return " ".join(parts)


def compute_skill_coverage(
    job_text: str,
    assignment_text: str,
    parsed_data: dict[str, Any] | None = None,
) -> float | None:
    reference_text = " ".join(
        part for part in [job_text, _flatten_skill_context(parsed_data)] if part
    ).strip()

    job_skills = extract_skills(reference_text)
    assignment_skills = extract_skills(assignment_text)

    if not job_skills:
        return None

    overlap = len(job_skills & assignment_skills)
    return round(overlap / len(job_skills), 4)


def compute_structure_compliance(assignment_text: str) -> float:
    text = (assignment_text or "").lower()

    expected_sections = [
        "title:",
        "context:",
        "task description:",
        "expected deliverables:",
        "evaluation criteria:",
        "estimated completion time:",
    ]

    found = sum(1 for section in expected_sections if section in text)
    return round(found / len(expected_sections), 4)


def compute_reviewer_feedback_score(feedback: str | None) -> float | None:
    if feedback is None:
        return None

    feedback = feedback.strip().lower()
    if feedback == "positive":
        return 1.0
    if feedback == "negative":
        return 0.0
    return None


def compute_reviewer_rating(rating: float | int | None) -> float | None:
    if rating is None:
        return None

    try:
        numeric_rating = float(rating)
    except (TypeError, ValueError):
        return None

    if numeric_rating <= 0:
        return None

    return round(numeric_rating, 2)


@lru_cache(maxsize=4)
def _load_sentence_transformer(model_name: str) -> Any | None:
    settings = get_settings()
    if not settings.use_sentence_transformers:
        return None

    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(model_name)
    except Exception:
        return None


def _similarity_score(model: Any, left_text: str, right_text: str) -> float | None:
    try:
        embeddings = model.encode(
            [left_text, right_text],
            normalize_embeddings=True,
        )
    except Exception:
        return None

    if len(embeddings) < 2:
        return None

    left_vector = [float(value) for value in embeddings[0]]
    right_vector = [float(value) for value in embeddings[1]]
    left_norm = math.sqrt(sum(value * value for value in left_vector))
    right_norm = math.sqrt(sum(value * value for value in right_vector))
    if not left_norm or not right_norm:
        return 0.0

    dot_product = sum(left_vector[index] * right_vector[index] for index in range(min(len(left_vector), len(right_vector))))
    similarity = dot_product / (left_norm * right_norm)
    return round(max(0.0, min(1.0, float(similarity))), 4)


def compute_jobbert_v3_score(
    job_text: str,
    assignment_text: str,
    model_name: str | None = None,
) -> float | None:
    job_text = (job_text or "").strip()
    assignment_text = (assignment_text or "").strip()
    if not job_text or not assignment_text:
        return 0.0

    settings = get_settings()
    resolved_model_name = (
        model_name
        or getattr(settings, "jobbert_model_name", None)
        or "JobBERT-v3"
    ).strip()

    model = _load_sentence_transformer(resolved_model_name)
    if model is not None:
        score = _similarity_score(model, job_text, assignment_text)
        if score is not None:
            return score

    fallback_model = get_embedding_model()
    score = _similarity_score(fallback_model, job_text, assignment_text)
    return score if score is not None else 0.0


def build_assignment_kpis(
    *,
    cleaned_text: str,
    assignment_text: str,
    parsed_data: dict[str, Any] | None,
    retrieved_examples: list[dict[str, Any]] | None,
    reviewer_feedback: str | None = None,
    reviewer_rating: float | int | None = None,
    llm_judge_score: float | None = None,
    llm_judge_details: dict[str, Any] | None = None,
    regenerated: bool = False,
    jobbert_model_name: str | None = None,
    generation_latency_seconds: float | None = None,
    judge_latency_seconds: float | None = None,
    workflow_latency_seconds: float | None = None,
) -> dict[str, Any]:
    parsed_data = parsed_data or {}
    retrieved_examples = retrieved_examples or []
    llm_judge_details = llm_judge_details or {}
    llm_judge_overall = llm_judge_score
    if llm_judge_overall is None:
        llm_judge_overall = llm_judge_details.get("overall_score")
    llm_judge_relevance = llm_judge_details.get("relevance_score", llm_judge_overall)
    llm_judge_clarity = llm_judge_details.get("clarity_score", llm_judge_overall)
    llm_judge_realism = llm_judge_details.get("realism_score", llm_judge_overall)
    llm_judge_difficulty_fit = llm_judge_details.get("difficulty_fit_score", llm_judge_overall)
    jobbert_v3_score = compute_jobbert_v3_score(
        job_text=cleaned_text,
        assignment_text=assignment_text,
        model_name=jobbert_model_name,
    )

    return {
        "retrieval_semantic_avg": compute_retrieval_semantic_avg(retrieved_examples),
        "retrieval_score_avg": compute_retrieval_score_avg(retrieved_examples),
        "retrieval_domain_precision": compute_retrieval_domain_precision(
            parsed_data=parsed_data,
            retrieved_examples=retrieved_examples,
        ),
        "skill_coverage": compute_skill_coverage(
            job_text=cleaned_text,
            assignment_text=assignment_text,
            parsed_data=parsed_data,
        ),
        "structure_compliance": compute_structure_compliance(assignment_text),
        "reviewer_rating": compute_reviewer_rating(reviewer_rating),
        "jobbert_v3_score": jobbert_v3_score,
        "model_score": jobbert_v3_score,
        "llm_judge_score": llm_judge_overall,
        "llm_judge_relevance": llm_judge_relevance,
        "llm_judge_clarity": llm_judge_clarity,
        "llm_judge_realism": llm_judge_realism,
        "llm_judge_difficulty_fit": llm_judge_difficulty_fit,
        "llm_judge_reasoning": llm_judge_details.get("reasoning"),
        "regeneration_flag": int(regenerated),
        "retrieved_examples_count": len(retrieved_examples),
        "generation_latency_seconds": generation_latency_seconds,
        "judge_latency_seconds": judge_latency_seconds,
        "workflow_latency_seconds": workflow_latency_seconds,
    }
