from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.feedback.feedback_store import FeedbackRecord, save_feedback
from src.storage.local_store import load_json, save_assignment


@dataclass
class _TempSettings:
    app_data_dir: Path
    raw_dir: Path
    processed_dir: Path
    feedback_dir: Path

    def ensure_directories(self) -> None:
        for directory in [self.app_data_dir, self.raw_dir, self.processed_dir, self.feedback_dir]:
            directory.mkdir(parents=True, exist_ok=True)


def test_save_feedback_persists_reviewer_rating(monkeypatch, tmp_path) -> None:
    settings = _TempSettings(
        app_data_dir=tmp_path / "data",
        raw_dir=tmp_path / "data" / "raw",
        processed_dir=tmp_path / "data" / "processed",
        feedback_dir=tmp_path / "data" / "feedback",
    )

    monkeypatch.setattr("src.feedback.feedback_store.get_settings", lambda: settings)
    monkeypatch.setattr("src.storage.local_store.get_settings", lambda: settings)

    job_id = "job-1"
    assignment_id = "assignment-1"
    save_assignment(
        job_id,
        assignment_id,
        {
            "job_id": job_id,
            "assignment_id": assignment_id,
            "version": 1,
            "kpis": {},
        },
    )

    record = FeedbackRecord(
        job_id=job_id,
        assignment_id=assignment_id,
        feedback="positive",
        reason="good quality",
        rating=4,
    )
    save_feedback(record)

    assignment_path = settings.processed_dir / f"{job_id}_{assignment_id}_assignment.json"
    persisted = load_json(assignment_path)

    assert persisted["kpis"]["reviewer_rating"] == 4
    assert len(list(settings.feedback_dir.glob("*.json"))) == 1
