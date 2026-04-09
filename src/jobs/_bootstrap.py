from __future__ import annotations

from pathlib import Path


def resolve_project_root() -> Path:
    """Resolve the project root in Databricks job and local execution contexts."""
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        cwd = Path.cwd().resolve()
        for candidate in [cwd, *cwd.parents]:
            if (candidate / "src").exists():
                return candidate
        return cwd
