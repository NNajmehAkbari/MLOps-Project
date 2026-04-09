from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from src.storage.backend import get_storage_backend


@dataclass
class CandidateFeedbackRecord:
    job_id: str
    assignment_id: str
    candidate_name: str
    overall_score: int
    clarity_score: int
    difficulty_score: int
    relevance_score: int
    time_reasonable: str
    comments: str
    created_at: str | None = None


def save_candidate_feedback(record: CandidateFeedbackRecord) -> None:
    if not record.created_at:
        record.created_at = datetime.now(timezone.utc).isoformat()

    get_storage_backend().save_candidate_feedback(asdict(record))


def load_candidate_feedback(job_id: str) -> list[dict]:
    return get_storage_backend().load_candidate_feedback(job_id)
