from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from src.feedback.candidate_feedback_store import CandidateFeedbackRecord, save_candidate_feedback
from src.feedback.feedback_store import FeedbackRecord, save_feedback
from src.feedback.review_store import ReviewDecision, save_review_decision
from src.services.assignment_workflow import AssignmentWorkflowResult, persist_assignment_version, run_assignment_workflow
from src.utils.config import get_settings


@dataclass
class RegeneratedAssignmentResult:
    assignment_id: str
    version: int
    workflow: AssignmentWorkflowResult


def build_feedback_record(
    *,
    job_id: str,
    assignment_id: str,
    feedback: str,
    reason: str,
    reviewer: str,
    rating: float,
) -> FeedbackRecord:
    try:
        return FeedbackRecord(
            job_id=job_id,
            assignment_id=assignment_id,
            feedback=feedback,
            reason=reason,
            rating=rating,
            reviewer=reviewer,
        )
    except TypeError:
        record = FeedbackRecord(
            job_id=job_id,
            assignment_id=assignment_id,
            feedback=feedback,
            reason=reason,
            reviewer=reviewer,
        )
        setattr(record, "rating", rating)
        return record


def save_reviewer_feedback(
    *,
    job_id: str,
    assignment_id: str,
    feedback: str,
    reason: str,
    reviewer: str,
    rating: float,
) -> FeedbackRecord:
    record = build_feedback_record(
        job_id=job_id,
        assignment_id=assignment_id,
        feedback=feedback,
        reason=reason,
        reviewer=reviewer,
        rating=rating,
    )
    save_feedback(record)
    return record


def regenerate_assignment_from_feedback(
    *,
    job_id: str,
    cleaned_text: str,
    current_version: int,
    assignment_hours: str,
    difficulty: str,
    focus_area: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
    previous_assignment: str,
    feedback_reason: str,
) -> RegeneratedAssignmentResult:
    workflow = run_assignment_workflow(
        job_text=cleaned_text,
        use_retrieval=use_retrieval,
        top_k=top_k,
        domain_override=domain_override,
        assignment_hours=assignment_hours,
        difficulty=difficulty,
        focus_area=focus_area,
        regenerate=True,
        previous_assignment=previous_assignment,
        feedback_reason=feedback_reason,
    )

    assignment_id = str(uuid.uuid4())
    version = current_version + 1

    persist_assignment_version(
        job_id=job_id,
        assignment_id=assignment_id,
        workflow=workflow,
        version=version,
        target_duration=assignment_hours,
        difficulty=difficulty,
        focus_area=focus_area,
        use_retrieval=use_retrieval,
        top_k=top_k,
        domain_override=domain_override,
        show_retrieval_debug=show_retrieval_debug,
        generated_from_feedback_reason=feedback_reason,
    )

    return RegeneratedAssignmentResult(
        assignment_id=assignment_id,
        version=version,
        workflow=workflow,
    )


def save_candidate_feedback_entry(
    *,
    job_id: str,
    assignment_id: str,
    candidate_name: str,
    overall_score: int,
    clarity_score: int,
    difficulty_score: int,
    relevance_score: int,
    time_reasonable: str,
    comments: str,
) -> Path:
    record = CandidateFeedbackRecord(
        job_id=job_id,
        assignment_id=assignment_id,
        candidate_name=candidate_name,
        overall_score=overall_score,
        clarity_score=clarity_score,
        difficulty_score=difficulty_score,
        relevance_score=relevance_score,
        time_reasonable=time_reasonable,
        comments=comments,
    )
    save_candidate_feedback(record)

    settings = get_settings()
    return settings.candidate_feedback_dir / f"{job_id}.jsonl"


def save_final_review_decision(
    *,
    job_id: str,
    selected_assignment_id: str,
    selected_version: int,
    decision: str,
    reviewer: str,
    notes: str,
) -> Path:
    record = ReviewDecision(
        job_id=job_id,
        selected_assignment_id=selected_assignment_id,
        selected_version=selected_version,
        decision=decision,
        reviewer=reviewer,
        notes=notes,
    )
    return save_review_decision(record)
