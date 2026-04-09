from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.evaluation.metrics import build_assignment_kpis
from src.feedback.feedback_store import load_feedback_records
from src.preprocessing.cleaner import clean_job_text
from src.storage.local_store import list_assignment_versions, load_job_record, load_parsed_job
from src.utils.config import get_settings


@dataclass
class LoadedVersionBundle:
    job_id: str
    job_record: dict[str, Any] | None
    parsed_data: dict[str, Any] | None
    cleaned_job_text: str
    version_history: list[dict[str, Any]]
    latest_assignment: dict[str, Any]
    latest_version_item: dict[str, Any]


def _latest_feedback_for_assignment(job_id: str | None, assignment_id: str | None) -> dict[str, Any] | None:
    if not job_id or not assignment_id:
        return None

    records = load_feedback_records(job_id=job_id, assignment_id=assignment_id)
    if not records:
        return None

    return records[-1]


def _build_kpis_payload(
    *,
    cleaned_text: str,
    assignment_text: str,
    parsed_data: dict[str, Any],
    retrieved_examples: list[dict[str, Any]],
    reviewer_feedback: str | None,
    reviewer_rating: float | int | None = None,
    llm_judge_score: float | None = None,
    llm_judge_details: Any = None,
    regenerated: bool = False,
    generation_latency_seconds: float | None = None,
    judge_latency_seconds: float | None = None,
    workflow_latency_seconds: float | None = None,
    existing_kpis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    computed = build_assignment_kpis(
        cleaned_text=cleaned_text,
        assignment_text=assignment_text,
        parsed_data=parsed_data,
        retrieved_examples=retrieved_examples,
        reviewer_feedback=reviewer_feedback,
        reviewer_rating=reviewer_rating,
        llm_judge_score=llm_judge_score,
        llm_judge_details=llm_judge_details,
        regenerated=regenerated,
        generation_latency_seconds=generation_latency_seconds,
        judge_latency_seconds=judge_latency_seconds,
        workflow_latency_seconds=workflow_latency_seconds,
    )

    merged = dict(computed)
    for key, value in (existing_kpis or {}).items():
        if value is not None and key not in {"jobbert_v3_score", "model_score", "reviewer_rating"}:
            merged[key] = value

    if merged.get("reviewer_rating") is None and existing_kpis:
        existing_rating = existing_kpis.get("reviewer_rating")
        if existing_rating is not None:
            merged["reviewer_rating"] = existing_rating

    merged.pop("reviewer_feedback_score", None)
    return merged


def load_version_bundle(job_id: str) -> LoadedVersionBundle | None:
    settings = get_settings()
    assignments = list_assignment_versions(job_id)
    if not assignments:
        return None

    job_record = load_job_record(job_id)
    parsed_data = load_parsed_job(job_id)
    cleaned_job_text = clean_job_text(job_record["job_text"]) if job_record else ""

    version_history: list[dict[str, Any]] = []
    for item in assignments:
        judge_result = item.get("judge_result") if isinstance(item.get("judge_result"), dict) else {}
        existing_kpis = item.get("kpis") if isinstance(item.get("kpis"), dict) else None
        latest_feedback = _latest_feedback_for_assignment(job_id, item.get("assignment_id"))
        reviewer_feedback = latest_feedback.get("feedback") if latest_feedback else None
        reviewer_rating = latest_feedback.get("rating") if latest_feedback else None
        generation_latency_seconds = existing_kpis.get("generation_latency_seconds") if existing_kpis else None
        judge_latency_seconds = existing_kpis.get("judge_latency_seconds") if existing_kpis else None
        workflow_latency_seconds = existing_kpis.get("workflow_latency_seconds") if existing_kpis else None

        llm_judge_score = None
        if isinstance(judge_result, dict):
            llm_judge_score = judge_result.get("overall_score")
        if llm_judge_score is None and existing_kpis:
            llm_judge_score = existing_kpis.get("llm_judge_score")

        kpis = _build_kpis_payload(
            cleaned_text=cleaned_job_text,
            assignment_text=item.get("assignment_text", ""),
            parsed_data=parsed_data or {},
            retrieved_examples=item.get("retrieved_examples", []),
            reviewer_feedback=reviewer_feedback,
            reviewer_rating=reviewer_rating,
            llm_judge_score=llm_judge_score,
            llm_judge_details=judge_result,
            regenerated=bool(item.get("generated_from_feedback_reason")),
            generation_latency_seconds=generation_latency_seconds,
            judge_latency_seconds=judge_latency_seconds,
            workflow_latency_seconds=workflow_latency_seconds,
            existing_kpis=existing_kpis,
        )

        version_history.append(
            {
                "version": item.get("version", 0),
                "assignment_id": item.get("assignment_id"),
                "text": item.get("assignment_text", ""),
                "retrieved_examples": item.get("retrieved_examples", []),
                "kpis": kpis,
                "use_retrieval": item.get("use_retrieval", False),
                "top_k": item.get("top_k", settings.retrieval_top_k_default),
                "domain_override": item.get("domain_override", "auto"),
                "show_retrieval_debug": item.get("show_retrieval_debug", True),
                "judge_result": item.get("judge_result"),
                "judge_error": item.get("judge_error"),
                "target_duration": item.get("target_duration"),
                "difficulty": item.get("difficulty"),
                "focus_area": item.get("focus_area"),
            }
        )

    latest_assignment = assignments[-1]
    latest_version_item = version_history[-1]

    return LoadedVersionBundle(
        job_id=job_id,
        job_record=job_record,
        parsed_data=parsed_data,
        cleaned_job_text=cleaned_job_text,
        version_history=version_history,
        latest_assignment=latest_assignment,
        latest_version_item=latest_version_item,
    )
