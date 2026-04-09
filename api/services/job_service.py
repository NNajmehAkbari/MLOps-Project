from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from threading import Lock

from api.schemas.job_ads import JobAdCreateRequest, JobStatus
from api.services.databricks_client import (
    DatabricksConfig,
    fetch_latest_assignment_result,
    get_run_state,
    trigger_assignment_pipeline,
)

_STORE_LOCK = Lock()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _store_path() -> Path:
    return _project_root() / "data" / "api_jobs.json"


def _load_store() -> dict[str, dict[str, Any]]:
    path = _store_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            return {str(key): value for key, value in payload.items() if isinstance(value, dict)}
    except Exception:
        return {}
    return {}


def _save_store(store: dict[str, dict[str, Any]]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


def _read_record(job_id: str) -> dict[str, Any] | None:
    with _STORE_LOCK:
        store = _load_store()
        record = store.get(job_id)
        return dict(record) if isinstance(record, dict) else None


def _write_record(record: dict[str, Any]) -> None:
    job_id = str(record.get("job_id") or "").strip()
    if not job_id:
        return
    with _STORE_LOCK:
        store = _load_store()
        store[job_id] = record
        _save_store(store)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_from_run_state(run_state: dict[str, Any]) -> tuple[JobStatus, str]:
    life_cycle = str(run_state.get("life_cycle_state") or "").upper()
    result_state = str(run_state.get("result_state") or "").upper()
    message = str(run_state.get("state_message") or "").strip()

    if life_cycle in {"PENDING", "RUNNING", "TERMINATING", "QUEUED"}:
        return JobStatus.running, life_cycle.lower()
    if life_cycle == "TERMINATED" and result_state == "SUCCESS":
        return JobStatus.completed, "completed"
    if life_cycle:
        return JobStatus.failed, life_cycle.lower()
    return JobStatus.queued, "queued"


def create_job_ad(request: JobAdCreateRequest) -> dict[str, Any]:
    job_id = str(uuid.uuid4())
    config = DatabricksConfig.from_env()

    record: dict[str, Any] = {
        "job_id": job_id,
        "status": JobStatus.queued,
        "stage": "queued",
        "message": "Job received and queued.",
        "created_at": _now(),
        "updated_at": _now(),
        "request": request.model_dump(),
        "run_id": None,
        "databricks_job_id": None,
        "result": None,
        "error_message": None,
    }
    _write_record(record)

    try:
        trigger = trigger_assignment_pipeline(
            config,
            job_parameters={
                "job_id": job_id,
                "job_text": request.job_text,
                "assignment_hours": request.assignment_hours,
                "difficulty": request.difficulty,
                "focus_area": request.focus_area,
                "use_retrieval": str(request.use_retrieval).lower(),
                "top_k": str(request.top_k),
                "domain_override": request.domain_override,
                "show_retrieval_debug": str(request.show_retrieval_debug).lower(),
                "secret_scope": request.secret_scope,
            },
        )
        record["run_id"] = trigger["databricks_run_id"]
        record["databricks_job_id"] = trigger["databricks_job_id"]
        record["status"] = JobStatus.running
        record["stage"] = "generate_assignment"
        record["message"] = "Databricks pipeline started."
        record["updated_at"] = _now()
        _write_record(record)
    except Exception as exc:
        record["status"] = JobStatus.failed
        record["stage"] = "trigger_failed"
        record["error_message"] = str(exc)
        record["message"] = "Failed to trigger Databricks job."
        record["updated_at"] = _now()
        _write_record(record)

    return record


def get_job_ad(job_id: str) -> dict[str, Any] | None:
    record = _read_record(job_id)
    if not record:
        return None

    if record.get("run_id") and record["status"] in {JobStatus.queued, JobStatus.running}:
        try:
            config = DatabricksConfig.from_env()
            run_state = get_run_state(config, int(record["run_id"]))
            status, stage = _status_from_run_state(run_state)
            record["status"] = status
            record["stage"] = stage
            record["message"] = run_state.get("state_message") or record.get("message")
            record["updated_at"] = _now()
            if status == JobStatus.completed and record.get("result") is None:
                result = fetch_latest_assignment_result(config, job_id)
                record["result"] = result
            _write_record(record)
        except Exception as exc:
            record["status"] = JobStatus.failed
            record["stage"] = "status_failed"
            record["error_message"] = str(exc)
            record["updated_at"] = _now()
            _write_record(record)

    return record


def get_job_result(job_id: str) -> dict[str, Any] | None:
    record = get_job_ad(job_id)
    if not record:
        return None

    if record.get("result") is None and record.get("status") == JobStatus.completed:
        try:
            config = DatabricksConfig.from_env()
            record["result"] = fetch_latest_assignment_result(config, job_id)
            _write_record(record)
        except Exception as exc:
            record["error_message"] = str(exc)
            _write_record(record)

    return record.get("result")
