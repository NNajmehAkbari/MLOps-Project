from __future__ import annotations

from time import perf_counter
from dataclasses import dataclass
from typing import Any

from src.evaluation.judge import JudgeResult, judge_assignment_with_llm
from src.evaluation.metrics import build_assignment_kpis
from src.generation.generator import AssignmentGenerator, GenerationResult
from src.ingestion.loader import load_job_ad_from_text
from src.preprocessing.cleaner import clean_job_text
from src.prompting.prompt_builder import build_prompt
from src.retrieval.retriever import retrieve_similar_examples
from src.extraction.job_parser import JobAdFeatures, parse_job_ad
from src.extraction.llm_job_parser import parse_job_ad_with_llm
from src.storage.local_store import (
    save_generation_artifacts,
)
from src.utils.config import get_settings


@dataclass
class AssignmentWorkflowResult:
    record: dict[str, Any]
    cleaned_text: str
    parsed_obj: JobAdFeatures | dict[str, Any]
    parsed_dict: dict[str, Any]
    parsing_source: str
    retrieved_examples: list[dict[str, Any]]
    prompt: str
    result: GenerationResult
    judge_result: JudgeResult | None
    judge_error: str | None
    kpis: dict[str, Any]
    generation_latency_seconds: float | None
    judge_latency_seconds: float | None
    workflow_latency_seconds: float | None


def to_dict_safe(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {"value": str(obj)}


def parse_job_with_fallback(
    cleaned_text: str,
    *,
    use_llm_parser: bool,
) -> tuple[JobAdFeatures | dict[str, Any], dict[str, Any], str]:
    llm_error = None
    if use_llm_parser:
        try:
            parsed_obj = parse_job_ad_with_llm(cleaned_text)
            parsed_dict = to_dict_safe(parsed_obj)
            if parsed_dict and "error" not in parsed_dict:
                parsed_dict["parsing_source"] = "llm"
                return parsed_obj, parsed_dict, "llm"
        except Exception as exc:
            llm_error = str(exc)

    parsed_obj = parse_job_ad(cleaned_text)
    parsed_dict = to_dict_safe(parsed_obj)
    parsed_dict["parsing_source"] = "rule_based"

    if llm_error:
        parsed_dict["_fallback_reason"] = llm_error

    return parsed_obj, parsed_dict, "rule_based"


def build_retrieval_metadata(
    parsed_dict: dict[str, Any],
    domain_override: str,
) -> dict[str, Any] | None:
    if domain_override != "auto":
        retrieval_meta: dict[str, Any] = {"subdomain": domain_override}

        seniority = parsed_dict.get("seniority")
        if seniority:
            retrieval_meta["seniority"] = seniority

        domain = parsed_dict.get("domain")
        if domain:
            retrieval_meta["domain"] = domain

        return retrieval_meta

    return parsed_dict or None


def run_assignment_workflow(
    *,
    job_text: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    assignment_hours: str,
    difficulty: str,
    focus_area: str,
    regenerate: bool = False,
    previous_assignment: str | None = None,
    feedback_reason: str | None = None,
) -> AssignmentWorkflowResult:
    settings = get_settings()
    workflow_started_at = perf_counter()
    record = load_job_ad_from_text(job_text, source="streamlit")
    cleaned_text = clean_job_text(record["job_text"])

    parsed_obj, parsed_dict, parsing_source = parse_job_with_fallback(
        cleaned_text,
        use_llm_parser=settings.use_llm_job_parser,
    )

    retrieved_examples: list[dict[str, Any]] = []
    if use_retrieval:
        retrieval_meta = build_retrieval_metadata(
            parsed_dict=parsed_dict,
            domain_override=domain_override,
        )
        retrieved_examples = retrieve_similar_examples(
            query_text=cleaned_text,
            top_k=top_k,
            parsed_llm=retrieval_meta,
        )

    prompt = build_prompt(
        job_text=cleaned_text,
        parsed=parsed_obj,
        previous_assignment=previous_assignment,
        feedback_reason=feedback_reason,
        regenerate=regenerate,
        retrieved_examples=retrieved_examples,
        target_duration=assignment_hours,
        focus_area=focus_area,
        difficulty=difficulty,
    )

    generator = AssignmentGenerator()
    generation_started_at = perf_counter()
    result = generator.generate(
        prompt=prompt,
        parsed=parsed_obj,
        regenerate=regenerate,
        feedback_reason=feedback_reason,
    )
    generation_latency_seconds = round(perf_counter() - generation_started_at, 4)

    judge_result = None
    judge_error = None
    judge_latency_seconds = None
    judge_started_at = None
    try:
        judge_started_at = perf_counter()
        judge_result = judge_assignment_with_llm(
            cleaned_job_text=cleaned_text,
            assignment_text=result.content,
            parsed_data=parsed_dict,
        )
        judge_latency_seconds = round(perf_counter() - judge_started_at, 4)
    except Exception as exc:
        judge_error = str(exc)
        if judge_started_at is not None:
            judge_latency_seconds = round(perf_counter() - judge_started_at, 4)

    workflow_latency_seconds = round(perf_counter() - workflow_started_at, 4)

    kpis = build_assignment_kpis(
        cleaned_text=cleaned_text,
        assignment_text=result.content,
        parsed_data=parsed_dict,
        retrieved_examples=retrieved_examples,
        reviewer_feedback="negative" if regenerate else None,
        llm_judge_score=judge_result.overall_score if judge_result else None,
        llm_judge_details=judge_result.raw_response if judge_result else None,
        regenerated=regenerate,
        generation_latency_seconds=generation_latency_seconds,
        judge_latency_seconds=judge_latency_seconds,
        workflow_latency_seconds=workflow_latency_seconds,
    )

    return AssignmentWorkflowResult(
        record=record,
        cleaned_text=cleaned_text,
        parsed_obj=parsed_obj,
        parsed_dict=parsed_dict,
        parsing_source=parsing_source,
        retrieved_examples=retrieved_examples,
        prompt=prompt,
        result=result,
        judge_result=judge_result,
        judge_error=judge_error,
        kpis=kpis,
        generation_latency_seconds=generation_latency_seconds,
        judge_latency_seconds=judge_latency_seconds,
        workflow_latency_seconds=workflow_latency_seconds,
    )


def build_assignment_version_payload(
    *,
    job_id: str,
    assignment_id: str,
    workflow: AssignmentWorkflowResult,
    version: int,
    target_duration: str,
    difficulty: str,
    focus_area: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
    generated_from_feedback_reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "job_id": job_id,
        "assignment_id": assignment_id,
        "version": version,
        "provider": workflow.result.provider,
        "model": workflow.result.model,
        "prompt": workflow.prompt,
        "assignment_text": workflow.result.content,
        "parsed_data": workflow.parsed_dict,
        "retrieved_examples": workflow.retrieved_examples,
        "parsing_source": workflow.parsing_source,
        "target_duration": target_duration,
        "difficulty": difficulty,
        "focus_area": focus_area,
        "use_retrieval": use_retrieval,
        "top_k": top_k,
        "domain_override": domain_override,
        "show_retrieval_debug": show_retrieval_debug,
        "kpis": workflow.kpis,
        "judge_result": workflow.judge_result.raw_response if workflow.judge_result else None,
        "judge_error": workflow.judge_error,
    }

    if generated_from_feedback_reason:
        payload["generated_from_feedback_reason"] = generated_from_feedback_reason

    return payload


def persist_assignment_version(
    *,
    job_id: str,
    assignment_id: str,
    workflow: AssignmentWorkflowResult,
    version: int,
    target_duration: str,
    difficulty: str,
    focus_area: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
    generated_from_feedback_reason: str | None = None,
) -> dict[str, Any]:
    payload = build_assignment_version_payload(
        job_id=job_id,
        assignment_id=assignment_id,
        workflow=workflow,
        version=version,
        target_duration=target_duration,
        difficulty=difficulty,
        focus_area=focus_area,
        use_retrieval=use_retrieval,
        top_k=top_k,
        domain_override=domain_override,
        show_retrieval_debug=show_retrieval_debug,
        generated_from_feedback_reason=generated_from_feedback_reason,
    )
    save_generation_artifacts(
        record=workflow.record,
        job_id=job_id,
        parsed_data=workflow.parsed_dict,
        assignment_id=assignment_id,
        payload=payload,
    )
    return payload
