from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _ensure_project_root() -> None:
    try:
        project_root = Path(__file__).resolve().parents[2]
    except NameError:
        cwd = Path.cwd().resolve()
        project_root = cwd
        for candidate in [cwd, *cwd.parents]:
            if (candidate / "src").exists():
                project_root = candidate
                break
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


_ensure_project_root()

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh Gold KPI and latest assignment views.")
    parser.add_argument("--job-id", default="", help="Optional job identifier to refresh only one job.")
    parser.add_argument("--storage-backend", default=os.getenv("STORAGE_BACKEND", ""))
    parser.add_argument("--databricks-catalog", default=os.getenv("DATABRICKS_CATALOG", ""))
    parser.add_argument("--databricks-schema", default=os.getenv("DATABRICKS_SCHEMA", ""))
    return parser


def _bootstrap_runtime_config(argv: list[str] | None = None) -> None:
    bootstrap_parser = argparse.ArgumentParser(add_help=False)
    bootstrap_parser.add_argument("--storage-backend", default=os.getenv("STORAGE_BACKEND", ""))
    bootstrap_parser.add_argument("--databricks-catalog", default=os.getenv("DATABRICKS_CATALOG", ""))
    bootstrap_parser.add_argument("--databricks-schema", default=os.getenv("DATABRICKS_SCHEMA", ""))
    parsed, _ = bootstrap_parser.parse_known_args(argv)

    storage_backend = str(getattr(parsed, "storage_backend", "") or "").strip()
    if storage_backend:
        os.environ["STORAGE_BACKEND"] = storage_backend

    databricks_catalog = str(getattr(parsed, "databricks_catalog", "") or "").strip()
    if databricks_catalog:
        os.environ["DATABRICKS_CATALOG"] = databricks_catalog

    databricks_schema = str(getattr(parsed, "databricks_schema", "") or "").strip()
    if databricks_schema:
        os.environ["DATABRICKS_SCHEMA"] = databricks_schema


def main(argv: list[str] | None = None) -> int:
    _bootstrap_runtime_config(argv)

    from src.storage.backend import get_storage_backend
    parser = _build_parser()
    args = parser.parse_args(argv)
    backend = get_storage_backend()
    job_id = args.job_id.strip() or None
    refreshed = backend.refresh_gold_views(job_id=job_id)

    print(
        json.dumps(
            {
                "backend": backend.name,
                "job_id": job_id,
                "refreshed_rows": refreshed,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    main()
