from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.storage.backend import get_storage_backend
    from src.utils.config import get_settings

    settings = get_settings()
    backend = get_storage_backend()

    print(f"project_root={project_root}")
    print(f"storage_backend={settings.storage_backend}")
    print(f"backend_name={backend.name}")
    print(f"llm_provider={settings.llm_provider}")
    print(f"judge_provider={settings.judge_provider}")

    try:
        status = backend.bootstrap()
    except Exception as exc:  # pragma: no cover - CLI smoke check
        print(f"bootstrap_error={exc}")
        return 1

    print(f"bootstrap_status={status.get('status')}")
    print(f"bootstrap_message={status.get('message')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
