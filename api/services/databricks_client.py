from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, parse, request


def _json_request(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = request.Request(url, data=body, headers=headers, method=method.upper())
    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8").strip()
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Databricks API request failed: {exc.code} {exc.reason}: {detail}") from exc


@dataclass(frozen=True)
class DatabricksConfig:
    host: str
    token: str
    assignment_pipeline_job_id: int | None
    assignment_pipeline_job_name: str = "assignment_pipeline_job"
    catalog: str = "workspace"
    schema: str = "default"
    gold_latest_assignments_table: str = "gold_latest_assignment_versions"

    @classmethod
    def from_env(cls) -> "DatabricksConfig":
        job_id_value = os.getenv("DATABRICKS_ASSIGNMENT_PIPELINE_JOB_ID", "").strip()
        return cls(
            host=os.getenv("DATABRICKS_HOST", "").strip().rstrip("/"),
            token=os.getenv("DATABRICKS_TOKEN", "").strip(),
            assignment_pipeline_job_id=int(job_id_value) if job_id_value else None,
            assignment_pipeline_job_name=os.getenv(
                "DATABRICKS_ASSIGNMENT_PIPELINE_JOB_NAME",
                "assignment_pipeline_job",
            ).strip(),
            catalog=os.getenv("DATABRICKS_CATALOG", "workspace").strip(),
            schema=os.getenv("DATABRICKS_SCHEMA", "default").strip(),
            gold_latest_assignments_table=os.getenv(
                "DATABRICKS_GOLD_LATEST_ASSIGNMENTS_TABLE",
                "gold_latest_assignment_versions",
            ).strip(),
        )

    @property
    def gold_latest_assignments_fqn(self) -> str:
        return ".".join(part for part in [self.catalog, self.schema, self.gold_latest_assignments_table] if part)


def _api_url(host: str, path: str, query: dict[str, str] | None = None) -> str:
    url = f"{host.rstrip('/')}{path}"
    if query:
        url = f"{url}?{parse.urlencode(query)}"
    return url


def resolve_assignment_pipeline_job_id(config: DatabricksConfig) -> int:
    if config.assignment_pipeline_job_id is not None:
        return config.assignment_pipeline_job_id

    url = _api_url(config.host, "/api/2.1/jobs/list")
    data = _json_request("GET", url, config.token)
    jobs = data.get("jobs", [])
    for job in jobs:
        settings = job.get("settings", {})
        if settings.get("name") == config.assignment_pipeline_job_name:
            job_id = job.get("job_id")
            if job_id is not None:
                return int(job_id)

    raise RuntimeError(
        f"Could not resolve Databricks job id for job name {config.assignment_pipeline_job_name!r}. "
        "Set DATABRICKS_ASSIGNMENT_PIPELINE_JOB_ID or verify the job exists."
    )


def trigger_assignment_pipeline(config: DatabricksConfig, job_parameters: dict[str, Any]) -> dict[str, Any]:
    job_id = resolve_assignment_pipeline_job_id(config)
    url = _api_url(config.host, "/api/2.1/jobs/run-now")
    payload = {
        "job_id": job_id,
        "job_parameters": job_parameters,
    }
    data = _json_request("POST", url, config.token, payload=payload)
    return {
        "databricks_job_id": job_id,
        "databricks_run_id": data.get("run_id"),
    }


def get_run_state(config: DatabricksConfig, run_id: int) -> dict[str, Any]:
    url = _api_url(config.host, "/api/2.1/jobs/runs/get", {"run_id": str(run_id)})
    data = _json_request("GET", url, config.token)
    state = data.get("state", {}) or {}
    return {
        "life_cycle_state": state.get("life_cycle_state"),
        "result_state": state.get("result_state"),
        "state_message": state.get("state_message"),
        "run_page_url": data.get("run_page_url"),
    }


def _escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


def fetch_latest_assignment_result(config: DatabricksConfig, job_id: str) -> dict[str, Any] | None:
    try:
        from databricks import sql
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "databricks-sql-connector is required to fetch results from Databricks."
        ) from exc

    hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip()
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "").strip()
    token = os.getenv("DATABRICKS_TOKEN", "").strip() or config.token
    if not hostname or not http_path or not token:
        raise RuntimeError(
            "DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN are required to query results."
        )

    query = f"""
    SELECT payload_json
    FROM {config.gold_latest_assignments_fqn}
    WHERE job_id = '{_escape_sql_literal(job_id)}'
    ORDER BY version DESC
    LIMIT 1
    """
    with sql.connect(server_hostname=hostname, http_path=http_path, access_token=token) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            if not row:
                return None
            payload_raw = row[0]
            if not payload_raw:
                return None
            if isinstance(payload_raw, dict):
                return payload_raw
            try:
                return json.loads(payload_raw)
            except Exception:
                return {"payload_json": payload_raw}
