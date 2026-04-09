from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.storage.backend import get_storage_backend


def save_json(data: dict[str, Any], file_path: str | Path) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path


def load_json(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_job_record(record: dict[str, Any]) -> Path:
    return get_storage_backend().save_job_record(record)  # type: ignore[return-value]


def load_job_record(job_id: str) -> dict[str, Any] | None:
    return get_storage_backend().load_job_record(job_id)


def load_parsed_job(job_id: str) -> dict[str, Any] | None:
    return get_storage_backend().load_parsed_job(job_id)


def save_assignment(job_id: str, assignment_id: str, payload: dict[str, Any]) -> Path:
    return get_storage_backend().save_assignment(job_id, assignment_id, payload)  # type: ignore[return-value]


def save_generation_artifacts(
    *,
    record: dict[str, Any],
    job_id: str,
    parsed_data: dict[str, Any],
    assignment_id: str,
    payload: dict[str, Any],
) -> Path:
    return get_storage_backend().save_generation_artifacts(
        record=record,
        job_id=job_id,
        parsed_data=parsed_data,
        assignment_id=assignment_id,
        payload=payload,
    )  # type: ignore[return-value]


def update_assignment_kpis(job_id: str, assignment_id: str, kpi_updates: dict[str, Any]) -> Path | None:
    return get_storage_backend().update_assignment_kpis(job_id, assignment_id, kpi_updates)  # type: ignore[return-value]


def list_assignment_versions(job_id: str) -> list[dict[str, Any]]:
    return get_storage_backend().list_assignment_versions(job_id)


def load_assignment_events(job_id: str) -> list[dict[str, Any]]:
    return get_storage_backend().load_assignment_events(job_id)


def load_review_decisions(job_id: str | None = None) -> list[dict[str, Any]]:
    return get_storage_backend().load_review_decisions(job_id)


def refresh_gold_views(job_id: str | None = None) -> int:
    return get_storage_backend().refresh_gold_views(job_id)
