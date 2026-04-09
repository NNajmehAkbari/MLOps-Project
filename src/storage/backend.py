from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from src.utils.config import Settings, get_settings


def _dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _load_json(content: str | None) -> dict[str, Any]:
    if not content:
        return {}
    return json.loads(content)


@runtime_checkable
class StorageBackend(Protocol):
    name: str

    def bootstrap(self) -> dict[str, Any]: ...

    def save_job_record(self, record: dict[str, Any]) -> Path | str: ...

    def load_job_record(self, job_id: str) -> dict[str, Any] | None: ...

    def load_parsed_job(self, job_id: str) -> dict[str, Any] | None: ...

    def save_assignment(self, job_id: str, assignment_id: str, payload: dict[str, Any]) -> Path | str: ...

    def load_assignment_events(self, job_id: str) -> list[dict[str, Any]]: ...

    def load_bronze_reviewer_feedback(
        self,
        job_id: str | None = None,
        assignment_id: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def load_bronze_candidate_feedback(self, job_id: str) -> list[dict[str, Any]]: ...

    def load_bronze_review_decisions(self, job_id: str | None = None) -> list[dict[str, Any]]: ...

    def save_generation_artifacts(
        self,
        *,
        record: dict[str, Any],
        job_id: str,
        parsed_data: dict[str, Any],
        assignment_id: str,
        payload: dict[str, Any],
    ) -> Path | str: ...

    def update_assignment_kpis(
        self,
        job_id: str,
        assignment_id: str,
        kpi_updates: dict[str, Any],
    ) -> Path | str | None: ...

    def list_assignment_versions(self, job_id: str) -> list[dict[str, Any]]: ...

    def load_gold_kpi_summaries(self, job_id: str | None = None) -> list[dict[str, Any]]: ...

    def load_gold_latest_assignments(self, job_id: str | None = None) -> list[dict[str, Any]]: ...

    def refresh_gold_views(self, job_id: str | None = None) -> int: ...

    def save_feedback(self, payload: dict[str, Any]) -> Path | str: ...

    def load_feedback_records(
        self,
        job_id: str | None = None,
        assignment_id: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def save_review_decision(self, payload: dict[str, Any]) -> Path | str: ...

    def save_candidate_feedback(self, payload: dict[str, Any]) -> Path | str: ...

    def load_candidate_feedback(self, job_id: str) -> list[dict[str, Any]]: ...

    def load_review_decisions(self, job_id: str | None = None) -> list[dict[str, Any]]: ...


class LocalFilesystemStorageBackend:
    name = "local"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def bootstrap(self) -> dict[str, Any]:
        return {
            "backend": self.name,
            "status": "ready",
            "message": "Local filesystem storage is ready.",
        }

    def _save_json(self, data: dict[str, Any], file_path: Path) -> Path:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    def _load_json(self, file_path: Path) -> dict[str, Any]:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save_job_record(self, record: dict[str, Any]) -> Path:
        return self._save_json(record, self.settings.raw_dir / f"{record['job_id']}.json")

    def save_generation_artifacts(
        self,
        *,
        record: dict[str, Any],
        job_id: str,
        parsed_data: dict[str, Any],
        assignment_id: str,
        payload: dict[str, Any],
    ) -> Path:
        self.save_job_record(record)
        self._save_json(parsed_data, self.settings.processed_dir / f"{job_id}_parsed.json")
        self.save_assignment(job_id, assignment_id, payload)
        return self.settings.processed_dir / f"{job_id}_{assignment_id}_assignment.json"

    def load_job_record(self, job_id: str) -> dict[str, Any] | None:
        file_path = self.settings.raw_dir / f"{job_id}.json"
        if not file_path.exists():
            return None
        return self._load_json(file_path)

    def load_parsed_job(self, job_id: str) -> dict[str, Any] | None:
        file_path = self.settings.processed_dir / f"{job_id}_parsed.json"
        if not file_path.exists():
            return None
        return self._load_json(file_path)

    def save_assignment(self, job_id: str, assignment_id: str, payload: dict[str, Any]) -> Path:
        return self._save_json(
            payload,
            self.settings.processed_dir / f"{job_id}_{assignment_id}_assignment.json",
        )

    def load_assignment_events(self, job_id: str) -> list[dict[str, Any]]:
        pattern = f"{job_id}_*_assignment.json"
        files = sorted(self.settings.processed_dir.glob(pattern))
        events: list[dict[str, Any]] = []
        for file_path in files:
            try:
                events.append(self._load_json(file_path))
            except Exception:
                continue
        events.sort(key=lambda x: (x.get("version", 0), x.get("updated_at", ""), x.get("created_at", "")))
        return events

    def load_bronze_reviewer_feedback(
        self,
        job_id: str | None = None,
        assignment_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return self.load_feedback_records(job_id=job_id, assignment_id=assignment_id)

    def load_bronze_candidate_feedback(self, job_id: str) -> list[dict[str, Any]]:
        return self.load_candidate_feedback(job_id)

    def load_bronze_review_decisions(self, job_id: str | None = None) -> list[dict[str, Any]]:
        return self.load_review_decisions(job_id)

    def update_assignment_kpis(
        self,
        job_id: str,
        assignment_id: str,
        kpi_updates: dict[str, Any],
    ) -> Path | None:
        file_path = self.settings.processed_dir / f"{job_id}_{assignment_id}_assignment.json"
        if not file_path.exists():
            return None

        data = self._load_json(file_path)
        kpis = data.get("kpis")
        if not isinstance(kpis, dict):
            kpis = {}
        kpis.update(kpi_updates)
        data["kpis"] = kpis
        return self._save_json(data, file_path)

    def list_assignment_versions(self, job_id: str) -> list[dict[str, Any]]:
        pattern = f"{job_id}_*_assignment.json"
        files = sorted(self.settings.processed_dir.glob(pattern))
        assignments: list[dict[str, Any]] = []
        for file_path in files:
            try:
                assignments.append(self._load_json(file_path))
            except Exception:
                continue
        assignments.sort(key=lambda x: x.get("version", 0))
        return assignments

    def load_gold_kpi_summaries(self, job_id: str | None = None) -> list[dict[str, Any]]:
        versions = self.list_assignment_versions(job_id) if job_id else []
        summaries: list[dict[str, Any]] = []
        for item in versions:
            kpis = item.get("kpis") if isinstance(item.get("kpis"), dict) else {}
            summaries.append(
                {
                    "job_id": job_id,
                    "assignment_id": item.get("assignment_id"),
                    "version": item.get("version"),
                    "kpis": kpis,
                    "assignment_text": item.get("assignment_text", ""),
                    "judge_result": item.get("judge_result"),
                    "judge_error": item.get("judge_error"),
                    "retrieved_examples": item.get("retrieved_examples", []),
                }
            )
        return summaries

    def load_gold_latest_assignments(self, job_id: str | None = None) -> list[dict[str, Any]]:
        versions = self.list_assignment_versions(job_id) if job_id else []
        latest_by_assignment: dict[str, dict[str, Any]] = {}
        for item in versions:
            assignment_id = str(item.get("assignment_id") or "").strip()
            if not assignment_id:
                continue
            current = latest_by_assignment.get(assignment_id)
            current_version = int(current.get("version") or 0) if current else -1
            version = int(item.get("version") or 0)
            if current is None or version >= current_version:
                latest_by_assignment[assignment_id] = item
        return list(latest_by_assignment.values())

    def refresh_gold_views(self, job_id: str | None = None) -> int:
        if job_id:
            return len(self.list_assignment_versions(job_id))

        return 0

    def save_feedback(self, payload: dict[str, Any]) -> Path:
        feedback_dir = self.settings.feedback_dir
        feedback_dir.mkdir(parents=True, exist_ok=True)
        file_path = feedback_dir / f"{payload['feedback_id']}.json"
        return self._save_json(payload, file_path)

    def load_feedback_records(
        self,
        job_id: str | None = None,
        assignment_id: str | None = None,
    ) -> list[dict[str, Any]]:
        feedback_dir = self.settings.feedback_dir
        if not feedback_dir.exists():
            return []

        rows: list[dict[str, Any]] = []
        for file_path in sorted(feedback_dir.glob("*.json")):
            try:
                record = self._load_json(file_path)
            except Exception:
                continue

            if job_id and record.get("job_id") != job_id:
                continue
            if assignment_id and record.get("assignment_id") != assignment_id:
                continue
            rows.append(record)

        rows.sort(key=lambda item: item.get("timestamp", ""))
        return rows

    def save_review_decision(self, payload: dict[str, Any]) -> Path:
        review_dir = self.settings.reviews_dir
        review_dir.mkdir(parents=True, exist_ok=True)
        file_path = review_dir / f"{payload['job_id']}_{payload['review_id']}_review.json"
        return self._save_json(payload, file_path)

    def save_candidate_feedback(self, payload: dict[str, Any]) -> Path:
        candidate_dir = self.settings.candidate_feedback_dir
        candidate_dir.mkdir(parents=True, exist_ok=True)
        file_path = candidate_dir / f"{payload['job_id']}.jsonl"
        existing = []
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as f:
                existing = [line.rstrip("\n") for line in f if line.strip()]
        existing.append(json.dumps(payload, ensure_ascii=False))
        with file_path.open("w", encoding="utf-8") as f:
            f.write("\n".join(existing) + ("\n" if existing else ""))
        return file_path

    def load_candidate_feedback(self, job_id: str) -> list[dict[str, Any]]:
        file_path = self.settings.candidate_feedback_dir / f"{job_id}.jsonl"
        if not file_path.exists():
            return []

        rows: list[dict[str, Any]] = []
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows

    def load_review_decisions(self, job_id: str | None = None) -> list[dict[str, Any]]:
        review_dir = self.settings.reviews_dir
        if not review_dir.exists():
            return []

        rows: list[dict[str, Any]] = []
        for file_path in sorted(review_dir.glob("*.json")):
            try:
                record = self._load_json(file_path)
            except Exception:
                continue

            if job_id and record.get("job_id") != job_id:
                continue
            rows.append(record)

        rows.sort(key=lambda item: item.get("timestamp", ""))
        return rows


class DatabricksSqlStorageBackend:
    name = "databricks"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._initialized = False

    def bootstrap(self) -> dict[str, Any]:
        self._ensure_tables()
        rows = self._execute("SELECT 1 AS ready", [], fetch=True)
        if not rows:
            raise RuntimeError("Databricks connection test did not return a result.")
        return {
            "backend": self.name,
            "status": "ready",
            "message": "Databricks connection and tables are ready.",
            "catalog": self.settings.databricks_catalog,
            "schema": self.settings.databricks_schema,
        }

    @property
    def _qualified_namespace(self) -> str:
        parts = [self.settings.databricks_catalog, self.settings.databricks_schema]
        return ".".join(part for part in parts if part)

    def _qualified(self, table_name: str) -> str:
        namespace = self._qualified_namespace
        return f"{namespace}.{table_name}" if namespace else table_name

    def _connect(self):
        try:
            from databricks import sql
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Databricks SQL connector is not installed. Install databricks-sql-connector to use the Databricks backend."
            ) from exc

        hostname = self.settings.databricks_server_hostname.strip()
        http_path = self.settings.databricks_http_path.strip()
        token = self.settings.databricks_token.strip()
        if not hostname or not http_path or not token:
            raise ValueError(
                "Databricks backend requires DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN."
            )

        return sql.connect(
            server_hostname=hostname,
            http_path=http_path,
            access_token=token,
        )

    def _execute(self, statement: str, params: list[Any] | None = None, fetch: bool = False):
        self._ensure_tables()
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, params or [])
                if fetch:
                    return cursor.fetchall()
        return None

    def _ensure_tables(self) -> None:
        if self._initialized:
            return

        statements = [
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_bronze_job_ads_table)} (
                job_id STRING,
                job_text STRING,
                source STRING,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_bronze_assignment_versions_table)} (
                job_id STRING,
                assignment_id STRING,
                version INT,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_silver_parsed_jobs_table)} (
                job_id STRING,
                parsing_source STRING,
                parsed_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_silver_assignment_versions_table)} (
                job_id STRING,
                assignment_id STRING,
                version INT,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_silver_reviewer_feedback_table)} (
                feedback_id STRING,
                job_id STRING,
                assignment_id STRING,
                feedback STRING,
                reason STRING,
                reviewer STRING,
                rating DOUBLE,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_silver_candidate_feedback_table)} (
                feedback_id STRING,
                job_id STRING,
                assignment_id STRING,
                candidate_name STRING,
                overall_score INT,
                clarity_score INT,
                difficulty_score INT,
                relevance_score INT,
                time_reasonable STRING,
                comments STRING,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_silver_review_decisions_table)} (
                review_id STRING,
                job_id STRING,
                selected_assignment_id STRING,
                selected_version INT,
                decision STRING,
                reviewer STRING,
                notes STRING,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_gold_kpi_summary_table)} (
                job_id STRING,
                assignment_id STRING,
                version INT,
                jobbert_v3_score DOUBLE,
                retrieval_semantic_avg DOUBLE,
                retrieval_score_avg DOUBLE,
                retrieval_domain_precision DOUBLE,
                skill_coverage DOUBLE,
                structure_compliance DOUBLE,
                llm_judge_score DOUBLE,
                llm_judge_relevance DOUBLE,
                llm_judge_clarity DOUBLE,
                llm_judge_realism DOUBLE,
                llm_judge_difficulty_fit DOUBLE,
                reviewer_rating DOUBLE,
                generation_latency_seconds DOUBLE,
                judge_latency_seconds DOUBLE,
                workflow_latency_seconds DOUBLE,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_gold_latest_assignments_table)} (
                job_id STRING,
                assignment_id STRING,
                version INT,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_bronze_reviewer_feedback_table)} (
                feedback_id STRING,
                job_id STRING,
                assignment_id STRING,
                feedback STRING,
                reason STRING,
                reviewer STRING,
                rating DOUBLE,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_bronze_candidate_feedback_table)} (
                feedback_id STRING,
                job_id STRING,
                assignment_id STRING,
                candidate_name STRING,
                overall_score INT,
                clarity_score INT,
                difficulty_score INT,
                relevance_score INT,
                time_reasonable STRING,
                comments STRING,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self._qualified(self.settings.databricks_bronze_review_decisions_table)} (
                review_id STRING,
                job_id STRING,
                selected_assignment_id STRING,
                selected_version INT,
                decision STRING,
                reviewer STRING,
                notes STRING,
                payload_json STRING,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            USING DELTA
            """,
        ]

        with self._connect() as connection:
            with connection.cursor() as cursor:
                for statement in statements:
                    cursor.execute(statement)

        self._initialized = True

    @staticmethod
    def _row_value(row: Any, index: int = 0) -> Any:
        try:
            return row[index]
        except Exception:
            return None

    def _delete_insert(self, delete_sql: str, insert_sql: str, params: list[Any]) -> None:
        self._execute(delete_sql, params)
        self._execute(insert_sql, params)

    def save_generation_artifacts(
        self,
        *,
        record: dict[str, Any],
        job_id: str,
        parsed_data: dict[str, Any],
        assignment_id: str,
        payload: dict[str, Any],
    ) -> Path:
        self.save_job_record(record)
        self.save_silver_parsed_job(job_id, parsed_data)
        result = self.save_assignment(job_id, assignment_id, payload)
        return result

    def save_job_record(self, record: dict[str, Any]) -> Path:
        table = self._qualified(self.settings.databricks_bronze_job_ads_table)
        payload = _dump_json(record)
        self._delete_insert(
            f"DELETE FROM {table} WHERE job_id = ?",
            f"""
            INSERT INTO {table} (job_id, job_text, source, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [
                record["job_id"],
                record.get("job_text"),
                record.get("source"),
                payload,
            ],
        )
        return Path(f"databricks://{table}/{record['job_id']}")

    def load_job_record(self, job_id: str) -> dict[str, Any] | None:
        bronze_table = self._qualified(self.settings.databricks_bronze_job_ads_table)
        rows = self._execute(
            f"SELECT payload_json FROM {bronze_table} WHERE job_id = ? ORDER BY updated_at DESC LIMIT 1",
            [job_id],
            fetch=True,
        )
        if rows:
            return _load_json(self._row_value(rows[0], 0))
        return None

    def save_silver_parsed_job(self, job_id: str, parsed_data: dict[str, Any]) -> Path:
        table = self._qualified(self.settings.databricks_silver_parsed_jobs_table)
        payload = _dump_json(parsed_data)
        parsing_source = str(parsed_data.get("parsing_source", "unknown"))
        self._delete_insert(
            f"DELETE FROM {table} WHERE job_id = ?",
            f"""
            INSERT INTO {table} (job_id, parsing_source, parsed_json, created_at, updated_at)
            VALUES (?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [job_id, parsing_source, payload],
        )
        return Path(f"databricks://{table}/{job_id}")

    def load_parsed_job(self, job_id: str) -> dict[str, Any] | None:
        silver_table = self._qualified(self.settings.databricks_silver_parsed_jobs_table)
        rows = self._execute(
            f"SELECT parsed_json FROM {silver_table} WHERE job_id = ? ORDER BY updated_at DESC LIMIT 1",
            [job_id],
            fetch=True,
        )
        if rows:
            return _load_json(self._row_value(rows[0], 0))

        bronze_table = self._qualified(self.settings.databricks_bronze_assignment_versions_table)
        rows = self._execute(
            f"""
            SELECT payload_json
            FROM {bronze_table}
            WHERE job_id = ?
            ORDER BY version DESC, updated_at DESC
            LIMIT 1
            """,
            [job_id],
            fetch=True,
        )
        if rows:
            payload = _load_json(self._row_value(rows[0], 0))
            parsed_data = payload.get("parsed_data") if isinstance(payload, dict) else None
            if isinstance(parsed_data, dict) and parsed_data:
                return parsed_data
        return None

    def save_assignment(self, job_id: str, assignment_id: str, payload: dict[str, Any]) -> Path:
        table = self._qualified(self.settings.databricks_bronze_assignment_versions_table)
        version = int(payload.get("version") or 0)
        payload_json = _dump_json(payload)
        self._execute(
            f"""
            INSERT INTO {table} (job_id, assignment_id, version, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [job_id, assignment_id, version, payload_json],
        )
        self._save_silver_assignment_version(job_id, assignment_id, payload)
        self._save_gold_latest_assignment_version(job_id, assignment_id, payload)
        return Path(f"databricks://{table}/{job_id}/{assignment_id}")

    def _save_silver_assignment_version(
        self,
        job_id: str,
        assignment_id: str,
        payload: dict[str, Any],
    ) -> None:
        table = self._qualified(self.settings.databricks_silver_assignment_versions_table)
        version = int(payload.get("version") or 0)
        payload_json = _dump_json(payload)
        self._delete_insert(
            f"DELETE FROM {table} WHERE job_id = ? AND assignment_id = ?",
            f"""
            INSERT INTO {table} (job_id, assignment_id, version, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [job_id, assignment_id, version, payload_json],
        )

    def _save_gold_latest_assignment_version(
        self,
        job_id: str,
        assignment_id: str,
        payload: dict[str, Any],
    ) -> None:
        table = self._qualified(self.settings.databricks_gold_latest_assignments_table)
        version = int(payload.get("version") or 0)
        payload_json = _dump_json(payload)
        self._delete_insert(
            f"DELETE FROM {table} WHERE job_id = ? AND assignment_id = ?",
            f"""
            INSERT INTO {table} (job_id, assignment_id, version, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [job_id, assignment_id, version, payload_json],
        )
        self._save_gold_kpi_summary(job_id, assignment_id, payload)

    def _save_gold_kpi_summary(
        self,
        job_id: str,
        assignment_id: str,
        payload: dict[str, Any],
    ) -> None:
        table = self._qualified(self.settings.databricks_gold_kpi_summary_table)
        version = int(payload.get("version") or 0)
        kpis = payload.get("kpis") if isinstance(payload.get("kpis"), dict) else {}
        payload_json = _dump_json(payload)
        self._delete_insert(
            f"DELETE FROM {table} WHERE job_id = ? AND assignment_id = ?",
            f"""
            INSERT INTO {table} (
                job_id, assignment_id, version,
                jobbert_v3_score, retrieval_semantic_avg, retrieval_score_avg, retrieval_domain_precision,
                skill_coverage, structure_compliance, llm_judge_score, llm_judge_relevance,
                llm_judge_clarity, llm_judge_realism, llm_judge_difficulty_fit, reviewer_rating,
                generation_latency_seconds, judge_latency_seconds, workflow_latency_seconds,
                payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [
                job_id,
                assignment_id,
                version,
                kpis.get("jobbert_v3_score"),
                kpis.get("retrieval_semantic_avg"),
                kpis.get("retrieval_score_avg"),
                kpis.get("retrieval_domain_precision"),
                kpis.get("skill_coverage"),
                kpis.get("structure_compliance"),
                kpis.get("llm_judge_score"),
                kpis.get("llm_judge_relevance"),
                kpis.get("llm_judge_clarity"),
                kpis.get("llm_judge_realism"),
                kpis.get("llm_judge_difficulty_fit"),
                kpis.get("reviewer_rating"),
                kpis.get("generation_latency_seconds"),
                kpis.get("judge_latency_seconds"),
                kpis.get("workflow_latency_seconds"),
                payload_json,
            ],
        )

    def load_assignment_events(self, job_id: str) -> list[dict[str, Any]]:
        table = self._qualified(self.settings.databricks_bronze_assignment_versions_table)
        rows = self._execute(
            f"""
            SELECT payload_json
            FROM {table}
            WHERE job_id = ?
            ORDER BY version ASC, updated_at ASC
            """,
            [job_id],
            fetch=True,
        )
        events: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                events.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return events

    def update_assignment_kpis(
        self,
        job_id: str,
        assignment_id: str,
        kpi_updates: dict[str, Any],
    ) -> Path | None:
        table = self._qualified(self.settings.databricks_bronze_assignment_versions_table)
        rows = self._execute(
            f"SELECT version, payload_json FROM {table} WHERE job_id = ? AND assignment_id = ? ORDER BY updated_at DESC LIMIT 1",
            [job_id, assignment_id],
            fetch=True,
        )
        if not rows:
            return None

        row = rows[0]
        payload = _load_json(self._row_value(row, 1))
        kpis = payload.get("kpis")
        if not isinstance(kpis, dict):
            kpis = {}
        kpis.update(kpi_updates)
        payload["kpis"] = kpis
        self.save_assignment(job_id, assignment_id, payload)
        return Path(f"databricks://{table}/{job_id}/{assignment_id}")

    def list_assignment_versions(self, job_id: str) -> list[dict[str, Any]]:
        silver_table = self._qualified(self.settings.databricks_silver_assignment_versions_table)
        rows = self._execute(
            f"""
            SELECT payload_json
            FROM {silver_table}
            WHERE job_id = ?
            ORDER BY version ASC, updated_at ASC
            """,
            [job_id],
            fetch=True,
        )
        assignments: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                assignments.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        if assignments:
            return assignments

        bronze_table = self._qualified(self.settings.databricks_bronze_assignment_versions_table)
        rows = self._execute(
            f"""
            SELECT payload_json
            FROM {bronze_table}
            WHERE job_id = ?
            ORDER BY version ASC, updated_at ASC
            """,
            [job_id],
            fetch=True,
        )
        assignments = []
        for row in rows or []:
            try:
                assignments.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return assignments

    def save_feedback(self, payload: dict[str, Any]) -> Path:
        table = self._qualified(self.settings.databricks_bronze_reviewer_feedback_table)
        feedback_id = payload["feedback_id"]
        self._execute(
            f"""
            INSERT INTO {table} (feedback_id, job_id, assignment_id, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [feedback_id, payload["job_id"], payload["assignment_id"], _dump_json(payload)],
        )
        self._save_silver_reviewer_feedback(payload)
        return Path(f"databricks://{table}/{feedback_id}")

    def _save_silver_reviewer_feedback(self, payload: dict[str, Any]) -> None:
        table = self._qualified(self.settings.databricks_silver_reviewer_feedback_table)
        feedback_id = payload["feedback_id"]
        payload_json = _dump_json(payload)
        self._delete_insert(
            f"DELETE FROM {table} WHERE feedback_id = ?",
            f"""
            INSERT INTO {table} (
                feedback_id, job_id, assignment_id, feedback, reason, reviewer, rating,
                payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [
                feedback_id,
                payload["job_id"],
                payload.get("assignment_id"),
                payload.get("feedback"),
                payload.get("reason"),
                payload.get("reviewer"),
                payload.get("rating"),
                payload_json,
            ],
        )

    def load_feedback_records(
        self,
        job_id: str | None = None,
        assignment_id: str | None = None,
    ) -> list[dict[str, Any]]:
        silver_table = self._qualified(self.settings.databricks_silver_reviewer_feedback_table)
        sql = f"SELECT payload_json FROM {silver_table}"
        params: list[Any] = []
        filters = []
        if job_id:
            filters.append("job_id = ?")
            params.append(job_id)
        if assignment_id:
            filters.append("assignment_id = ?")
            params.append(assignment_id)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY created_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        if records:
            return records

        bronze_table = self._qualified(self.settings.databricks_bronze_reviewer_feedback_table)
        sql = f"SELECT payload_json FROM {bronze_table}"
        params: list[Any] = []
        filters = []
        if job_id:
            filters.append("job_id = ?")
            params.append(job_id)
        if assignment_id:
            filters.append("assignment_id = ?")
            params.append(assignment_id)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY created_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def load_bronze_reviewer_feedback(
        self,
        job_id: str | None = None,
        assignment_id: str | None = None,
    ) -> list[dict[str, Any]]:
        bronze_table = self._qualified(self.settings.databricks_bronze_reviewer_feedback_table)
        sql = f"SELECT payload_json FROM {bronze_table}"
        params: list[Any] = []
        filters = []
        if job_id:
            filters.append("job_id = ?")
            params.append(job_id)
        if assignment_id:
            filters.append("assignment_id = ?")
            params.append(assignment_id)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        sql += " ORDER BY created_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def save_review_decision(self, payload: dict[str, Any]) -> Path:
        table = self._qualified(self.settings.databricks_bronze_review_decisions_table)
        review_id = payload["review_id"]
        self._execute(
            f"""
            INSERT INTO {table} (review_id, job_id, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [review_id, payload["job_id"], _dump_json(payload)],
        )
        self._save_silver_review_decision(payload)
        return Path(f"databricks://{table}/{review_id}")

    def _save_silver_review_decision(self, payload: dict[str, Any]) -> None:
        table = self._qualified(self.settings.databricks_silver_review_decisions_table)
        review_id = payload["review_id"]
        payload_json = _dump_json(payload)
        self._delete_insert(
            f"DELETE FROM {table} WHERE review_id = ?",
            f"""
            INSERT INTO {table} (
                review_id, job_id, selected_assignment_id, selected_version, decision, reviewer,
                notes, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [
                review_id,
                payload["job_id"],
                payload.get("selected_assignment_id"),
                payload.get("selected_version"),
                payload.get("decision"),
                payload.get("reviewer"),
                payload.get("notes"),
                payload_json,
            ],
        )

    def save_candidate_feedback(self, payload: dict[str, Any]) -> Path:
        table = self._qualified(self.settings.databricks_bronze_candidate_feedback_table)
        feedback_id = payload["feedback_id"]
        self._execute(
            f"""
            INSERT INTO {table} (feedback_id, job_id, payload_json, created_at, updated_at)
            VALUES (?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [feedback_id, payload["job_id"], _dump_json(payload)],
        )
        self._save_silver_candidate_feedback(payload)
        return Path(f"databricks://{table}/{feedback_id}")

    def _save_silver_candidate_feedback(self, payload: dict[str, Any]) -> None:
        table = self._qualified(self.settings.databricks_silver_candidate_feedback_table)
        feedback_id = payload["feedback_id"]
        payload_json = _dump_json(payload)
        self._delete_insert(
            f"DELETE FROM {table} WHERE feedback_id = ?",
            f"""
            INSERT INTO {table} (
                feedback_id, job_id, assignment_id, candidate_name, overall_score, clarity_score,
                difficulty_score, relevance_score, time_reasonable, comments, payload_json,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp(), current_timestamp())
            """,
            [
                feedback_id,
                payload["job_id"],
                payload.get("assignment_id"),
                payload.get("candidate_name"),
                payload.get("overall_score"),
                payload.get("clarity_score"),
                payload.get("difficulty_score"),
                payload.get("relevance_score"),
                payload.get("time_reasonable"),
                payload.get("comments"),
                payload_json,
            ],
        )

    def load_candidate_feedback(self, job_id: str) -> list[dict[str, Any]]:
        silver_table = self._qualified(self.settings.databricks_silver_candidate_feedback_table)
        rows = self._execute(
            f"SELECT payload_json FROM {silver_table} WHERE job_id = ? ORDER BY created_at ASC",
            [job_id],
            fetch=True,
        )
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        if records:
            return records

        bronze_table = self._qualified(self.settings.databricks_bronze_candidate_feedback_table)
        rows = self._execute(
            f"SELECT payload_json FROM {bronze_table} WHERE job_id = ? ORDER BY created_at ASC",
            [job_id],
            fetch=True,
        )
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def load_bronze_candidate_feedback(self, job_id: str) -> list[dict[str, Any]]:
        bronze_table = self._qualified(self.settings.databricks_bronze_candidate_feedback_table)
        rows = self._execute(
            f"SELECT payload_json FROM {bronze_table} WHERE job_id = ? ORDER BY created_at ASC",
            [job_id],
            fetch=True,
        )
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def load_review_decisions(self, job_id: str | None = None) -> list[dict[str, Any]]:
        silver_table = self._qualified(self.settings.databricks_silver_review_decisions_table)
        sql = f"SELECT payload_json FROM {silver_table}"
        params: list[Any] = []
        if job_id:
            sql += " WHERE job_id = ?"
            params.append(job_id)
        sql += " ORDER BY created_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        if records:
            return records

        bronze_table = self._qualified(self.settings.databricks_bronze_review_decisions_table)
        sql = f"SELECT payload_json FROM {bronze_table}"
        params: list[Any] = []
        if job_id:
            sql += " WHERE job_id = ?"
            params.append(job_id)
        sql += " ORDER BY created_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def load_bronze_review_decisions(self, job_id: str | None = None) -> list[dict[str, Any]]:
        bronze_table = self._qualified(self.settings.databricks_bronze_review_decisions_table)
        sql = f"SELECT payload_json FROM {bronze_table}"
        params: list[Any] = []
        if job_id:
            sql += " WHERE job_id = ?"
            params.append(job_id)
        sql += " ORDER BY created_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def load_gold_kpi_summaries(self, job_id: str | None = None) -> list[dict[str, Any]]:
        gold_table = self._qualified(self.settings.databricks_gold_kpi_summary_table)
        sql = f"SELECT payload_json FROM {gold_table}"
        params: list[Any] = []
        if job_id:
            sql += " WHERE job_id = ?"
            params.append(job_id)
        sql += " ORDER BY version ASC, updated_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def load_gold_latest_assignments(self, job_id: str | None = None) -> list[dict[str, Any]]:
        gold_table = self._qualified(self.settings.databricks_gold_latest_assignments_table)
        sql = f"SELECT payload_json FROM {gold_table}"
        params: list[Any] = []
        if job_id:
            sql += " WHERE job_id = ?"
            params.append(job_id)
        sql += " ORDER BY version ASC, updated_at ASC"

        rows = self._execute(sql, params, fetch=True)
        records: list[dict[str, Any]] = []
        for row in rows or []:
            try:
                records.append(_load_json(self._row_value(row, 0)))
            except Exception:
                continue
        return records

    def refresh_gold_views(self, job_id: str | None = None) -> int:
        if job_id:
            job_ids = [job_id]
        else:
            silver_table = self._qualified(self.settings.databricks_silver_assignment_versions_table)
            rows = self._execute(f"SELECT DISTINCT job_id FROM {silver_table}", [], fetch=True)
            job_ids = [str(self._row_value(row, 0)) for row in rows or [] if self._row_value(row, 0)]

            if not job_ids:
                bronze_table = self._qualified(self.settings.databricks_bronze_assignment_versions_table)
                rows = self._execute(f"SELECT DISTINCT job_id FROM {bronze_table}", [], fetch=True)
                job_ids = [str(self._row_value(row, 0)) for row in rows or [] if self._row_value(row, 0)]

        refreshed = 0
        for current_job_id in job_ids:
            for item in self.list_assignment_versions(current_job_id):
                assignment_id = str(item.get("assignment_id") or "").strip()
                if not assignment_id:
                    continue
                self._save_gold_latest_assignment_version(current_job_id, assignment_id, item)
                refreshed += 1
        return refreshed


_BACKEND_NAME: str | None = None
_BACKEND: StorageBackend | None = None


def get_storage_backend() -> StorageBackend:
    global _BACKEND, _BACKEND_NAME
    settings = get_settings()
    backend_name = settings.storage_backend.strip().lower()

    if _BACKEND is not None and _BACKEND_NAME == backend_name:
        return _BACKEND

    if backend_name == "databricks":
        backend: StorageBackend = DatabricksSqlStorageBackend(settings)
    else:
        backend = LocalFilesystemStorageBackend(settings)

    _BACKEND = backend
    _BACKEND_NAME = backend_name
    return backend
