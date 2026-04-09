from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


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
    parser = argparse.ArgumentParser(description="Save reviewer, candidate, or final decision feedback.")
    subparsers = parser.add_subparsers(dest="kind", required=True)

    reviewer = subparsers.add_parser("reviewer", help="Save reviewer feedback.")
    reviewer.add_argument("--storage-backend", default=os.getenv("STORAGE_BACKEND", ""))
    reviewer.add_argument("--databricks-catalog", default=os.getenv("DATABRICKS_CATALOG", ""))
    reviewer.add_argument("--databricks-schema", default=os.getenv("DATABRICKS_SCHEMA", ""))
    reviewer.add_argument("--job-id", required=True)
    reviewer.add_argument("--assignment-id", required=True)
    reviewer.add_argument("--feedback", required=True)
    reviewer.add_argument("--reason", required=True)
    reviewer.add_argument("--reviewer", default="default_user")
    reviewer.add_argument("--rating", type=float, required=True)

    candidate = subparsers.add_parser("candidate", help="Save candidate survey feedback.")
    candidate.add_argument("--storage-backend", default=os.getenv("STORAGE_BACKEND", ""))
    candidate.add_argument("--databricks-catalog", default=os.getenv("DATABRICKS_CATALOG", ""))
    candidate.add_argument("--databricks-schema", default=os.getenv("DATABRICKS_SCHEMA", ""))
    candidate.add_argument("--job-id", required=True)
    candidate.add_argument("--assignment-id", required=True)
    candidate.add_argument("--candidate-name", default="anonymous")
    candidate.add_argument("--overall-score", type=int, required=True)
    candidate.add_argument("--clarity-score", type=int, required=True)
    candidate.add_argument("--difficulty-score", type=int, required=True)
    candidate.add_argument("--relevance-score", type=int, required=True)
    candidate.add_argument("--time-reasonable", required=True)
    candidate.add_argument("--comments", default="")

    decision = subparsers.add_parser("decision", help="Save final review decision.")
    decision.add_argument("--storage-backend", default=os.getenv("STORAGE_BACKEND", ""))
    decision.add_argument("--databricks-catalog", default=os.getenv("DATABRICKS_CATALOG", ""))
    decision.add_argument("--databricks-schema", default=os.getenv("DATABRICKS_SCHEMA", ""))
    decision.add_argument("--job-id", required=True)
    decision.add_argument("--selected-assignment-id", required=True)
    decision.add_argument("--selected-version", type=int, required=True)
    decision.add_argument("--decision", required=True)
    decision.add_argument("--reviewer", default="default_user")
    decision.add_argument("--notes", default="")

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

    from src.services.review_workflow import (
        save_candidate_feedback_entry,
        save_final_review_decision,
        save_reviewer_feedback,
    )
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.kind == "reviewer":
        record = save_reviewer_feedback(
            job_id=args.job_id,
            assignment_id=args.assignment_id,
            feedback=args.feedback,
            reason=args.reason,
            reviewer=args.reviewer,
            rating=args.rating,
        )
        print(
            json.dumps(
                {
                    "kind": "reviewer",
                    "feedback_id": record.feedback_id,
                    "job_id": record.job_id,
                    "assignment_id": record.assignment_id,
                    "rating": record.rating,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.kind == "candidate":
        path = save_candidate_feedback_entry(
            job_id=args.job_id,
            assignment_id=args.assignment_id,
            candidate_name=args.candidate_name,
            overall_score=args.overall_score,
            clarity_score=args.clarity_score,
            difficulty_score=args.difficulty_score,
            relevance_score=args.relevance_score,
            time_reasonable=args.time_reasonable,
            comments=args.comments,
        )
        print(
            json.dumps(
                {
                    "kind": "candidate",
                    "job_id": args.job_id,
                    "assignment_id": args.assignment_id,
                    "path": str(path),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    if args.kind == "decision":
        path = save_final_review_decision(
            job_id=args.job_id,
            selected_assignment_id=args.selected_assignment_id,
            selected_version=args.selected_version,
            decision=args.decision,
            reviewer=args.reviewer,
            notes=args.notes,
        )
        print(
            json.dumps(
                {
                    "kind": "decision",
                    "job_id": args.job_id,
                    "selected_assignment_id": args.selected_assignment_id,
                    "selected_version": args.selected_version,
                    "path": str(path),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    raise ValueError(f"Unsupported feedback kind: {args.kind}")


if __name__ == "__main__":
    main()
