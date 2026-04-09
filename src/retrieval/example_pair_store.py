from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from src.utils.config import get_settings


SUBDOMAIN_TO_DOMAIN = {
    "frontend": "software_engineering",
    "backend": "software_engineering",
    "mobile": "software_engineering",
    "mobile_engineer": "software_engineering",
    "fullstack": "software_engineering",
    "software": "software_engineering",
}


@dataclass
class ExamplePair:
    pair_id: str
    company: str
    domain: str
    subdomain: str
    seniority: str
    year: str
    sequence: str
    job_ad_text: str
    assignment_text: str
    folder_path: str

    def to_dict(self) -> dict:
        return asdict(self)


def _read_text_candidate(folder: Path, base_name: str) -> str | None:
    for ext in (".md", ".txt"):
        file_path = folder / f"{base_name}{ext}"
        if file_path.exists():
            return file_path.read_text(encoding="utf-8").strip()
    return None


def _infer_metadata(group_dir: Path, posting_dir: Path) -> dict:
    group_name = group_dir.name.lower()
    posting_name = posting_dir.name.lower()

    if "_" in group_name:
        company, subdomain = group_name.split("_", 1)
    else:
        company, subdomain = group_name, "general"

    domain = SUBDOMAIN_TO_DOMAIN.get(subdomain, "general")

    posting_parts = posting_name.split("_")
    seniority = posting_parts[0] if len(posting_parts) >= 1 else "unknown"
    year = posting_parts[1] if len(posting_parts) >= 2 else ""
    sequence = posting_parts[2] if len(posting_parts) >= 3 else ""

    pair_id = f"{group_dir.name}__{posting_dir.name}"

    return {
        "pair_id": pair_id,
        "company": company,
        "domain": domain,
        "subdomain": subdomain,
        "seniority": seniority,
        "year": year,
        "sequence": sequence,
    }


def load_example_pairs(base_dir: Path | None = None) -> list[ExamplePair]:
    settings = get_settings()

    if base_dir is None:
        base_dir = settings.example_pairs_raw_dir

    if not base_dir.exists():
        return []

    pairs: list[ExamplePair] = []

    for group_dir in sorted(base_dir.iterdir()):
        if not group_dir.is_dir():
            continue

        for posting_dir in sorted(group_dir.iterdir()):
            if not posting_dir.is_dir():
                continue

            job_ad_text = _read_text_candidate(posting_dir, "job_ad")
            assignment_text = _read_text_candidate(posting_dir, "assignment")

            if not job_ad_text or not assignment_text:
                continue

            meta = _infer_metadata(group_dir, posting_dir)

            pair = ExamplePair(
                pair_id=meta["pair_id"],
                company=meta["company"],
                domain=meta["domain"],
                subdomain=meta["subdomain"],
                seniority=meta["seniority"],
                year=meta["year"],
                sequence=meta["sequence"],
                job_ad_text=job_ad_text,
                assignment_text=assignment_text,
                folder_path=str(posting_dir),
            )
            pairs.append(pair)

    return pairs
