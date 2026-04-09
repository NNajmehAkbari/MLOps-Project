from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import datetime

from src.storage.backend import get_storage_backend


@dataclass
class ReviewDecision:
    job_id: str
    selected_assignment_id: str
    selected_version: int
    decision: str  # approved / rejected / shortlisted
    reviewer: str = "default_user"
    notes: str = ""
    timestamp: str = ""
    review_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.review_id:
            self.review_id = str(uuid.uuid4())


def save_review_decision(record: ReviewDecision):
    return get_storage_backend().save_review_decision(asdict(record))
