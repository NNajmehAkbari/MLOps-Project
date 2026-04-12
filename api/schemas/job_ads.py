from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobAdCreateRequest(BaseModel):
    job_text: str = Field(..., min_length=1)
    assignment_hours: str = "2h"
    difficulty: str = "medium"
    focus_area: str = ""
    use_retrieval: bool = False
    top_k: int = 2
    domain_override: str = "auto"
    show_retrieval_debug: bool = True
    secret_scope: str = "mlops-project"


class JobAdCreateResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    databricks_run_id: int | None = None
    databricks_job_id: int | None = None
    error_message: str | None = None


class JobAdStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    stage: str | None = None
    message: str | None = None
    databricks_run_id: int | None = None
    databricks_job_id: int | None = None
    updated_at: str | None = None
    error_message: str | None = None


class JobAdResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    assignment_id: str | None = None
    version: int | None = None
    assignment_text: str | None = None
    kpis: dict[str, Any] | None = None
    result_payload: dict[str, Any] | None = None
    error_message: str | None = None
