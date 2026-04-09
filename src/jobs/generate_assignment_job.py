from __future__ import annotations

import argparse
import json
import sys
import uuid
from typing import Any


from src.jobs._bootstrap import resolve_project_root


def _ensure_project_root() -> None:
    project_root = resolve_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


_ensure_project_root()

from src.services.assignment_workflow import persist_assignment_version, run_assignment_workflow
from src.storage.backend import get_storage_backend
from src.utils.config import get_settings


def _str_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _read_job_text(args: argparse.Namespace) -> str:
    if args.job_text_file:
        from pathlib import Path

        return Path(args.job_text_file).read_text(encoding="utf-8")
    if args.job_text:
        return args.job_text
    raise ValueError("Provide either --job-text or --job-text-file.")


def _build_parser(settings) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and persist a take-home assignment.")
    parser.add_argument("--job-id", default="", help="Optional job identifier. A UUID is generated if omitted.")
    parser.add_argument("--job-text", default="", help="Raw job advertisement text.")
    parser.add_argument("--job-text-file", default="", help="Path to a file containing the job advertisement text.")
    parser.add_argument("--assignment-hours", default=settings.default_duration, help="Target assignment duration label.")
    parser.add_argument("--difficulty", default=settings.default_difficulty, help="Difficulty label.")
    parser.add_argument("--focus-area", default="", help="Optional focus area to bias the assignment.")
    parser.add_argument("--use-retrieval", type=_str_to_bool, default=settings.use_retrieval_default)
    parser.add_argument("--top-k", type=int, default=settings.retrieval_top_k_default)
    parser.add_argument("--domain-override", default="auto")
    parser.add_argument("--show-retrieval-debug", type=_str_to_bool, default=settings.show_retrieval_debug_default)
    return parser


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = _build_parser(settings)
    args = parser.parse_args(argv)

    job_text = _read_job_text(args)
    job_id = args.job_id.strip() or str(uuid.uuid4())
    assignment_id = str(uuid.uuid4())
    backend = get_storage_backend()
    current_versions = backend.list_assignment_versions(job_id)
    version = len(current_versions) + 1

    workflow = run_assignment_workflow(
        job_text=job_text,
        use_retrieval=_str_to_bool(args.use_retrieval),
        top_k=int(args.top_k),
        domain_override=args.domain_override,
        assignment_hours=args.assignment_hours,
        difficulty=args.difficulty,
        focus_area=args.focus_area,
    )

    payload = persist_assignment_version(
        job_id=job_id,
        assignment_id=assignment_id,
        workflow=workflow,
        version=version,
        target_duration=args.assignment_hours,
        difficulty=args.difficulty,
        focus_area=args.focus_area,
        use_retrieval=_str_to_bool(args.use_retrieval),
        top_k=int(args.top_k),
        domain_override=args.domain_override,
        show_retrieval_debug=_str_to_bool(args.show_retrieval_debug),
    )

    summary: dict[str, Any] = {
        "job_id": job_id,
        "assignment_id": assignment_id,
        "version": payload.get("version"),
        "parsing_source": workflow.parsing_source,
        "judge_error": workflow.judge_error,
        "kpis": workflow.kpis,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
