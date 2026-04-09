from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from src.storage.backend import get_storage_backend


@dataclass
class FeedbackRecord:
    job_id: str
    assignment_id: str
    feedback: str
    reason: str
    rating: float | None = None
    reviewer: str = "default_user"
    timestamp: str = ""
    feedback_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.feedback_id:
            self.feedback_id = str(uuid.uuid4())


def save_feedback(record: FeedbackRecord):
    payload = asdict(record)
    if "rating" not in payload:
        payload["rating"] = getattr(record, "rating", None)
    backend = get_storage_backend()
    file_path = backend.save_feedback(payload)

    rating = getattr(record, "rating", None)
    if rating is not None:
        backend.update_assignment_kpis(
            job_id=record.job_id,
            assignment_id=record.assignment_id,
            kpi_updates={"reviewer_rating": rating},
        )

    return file_path


def load_feedback_records(job_id: str | None = None, assignment_id: str | None = None) -> list[dict[str, Any]]:
    return get_storage_backend().load_feedback_records(job_id=job_id, assignment_id=assignment_id)
