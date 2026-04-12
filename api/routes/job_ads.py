from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas.job_ads import (
    JobAdCreateRequest,
    JobAdCreateResponse,
    JobAdResultResponse,
    JobAdStatusResponse,
)
from api.services.job_service import create_job_ad, get_job_ad, get_job_result

router = APIRouter(prefix="/job-ads", tags=["job-ads"])


@router.post("", response_model=JobAdCreateResponse)
def create_job_ad_endpoint(payload: JobAdCreateRequest) -> JobAdCreateResponse:
    record = create_job_ad(payload)
    return JobAdCreateResponse(
        job_id=record["job_id"],
        status=record["status"],
        message=record["message"],
        databricks_run_id=record.get("run_id"),
        databricks_job_id=record.get("databricks_job_id"),
        error_message=record.get("error_message"),
    )


@router.get("/{job_id}", response_model=JobAdStatusResponse)
def get_job_status_endpoint(job_id: str) -> JobAdStatusResponse:
    record = get_job_ad(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobAdStatusResponse(
        job_id=record["job_id"],
        status=record["status"],
        stage=record.get("stage"),
        message=record.get("message"),
        databricks_run_id=record.get("run_id"),
        databricks_job_id=record.get("databricks_job_id"),
        updated_at=record.get("updated_at"),
        error_message=record.get("error_message"),
    )


@router.get("/{job_id}/result", response_model=JobAdResultResponse)
def get_job_result_endpoint(job_id: str) -> JobAdResultResponse:
    record = get_job_ad(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")

    result = get_job_result(job_id)
    return JobAdResultResponse(
        job_id=record["job_id"],
        status=record["status"],
        assignment_id=(result or {}).get("assignment_id"),
        version=(result or {}).get("version"),
        assignment_text=(result or {}).get("assignment_text"),
        kpis=(result or {}).get("kpis"),
        result_payload=result,
        error_message=record.get("error_message"),
    )
