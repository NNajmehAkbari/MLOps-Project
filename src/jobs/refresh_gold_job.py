from __future__ import annotations

import argparse
import json
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

from src.storage.backend import get_storage_backend


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh Gold KPI and latest assignment views.")
    parser.add_argument("--job-id", default="", help="Optional job identifier to refresh only one job.")
    return parser


def main(argv: list[str] | None = None) -> int:
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
