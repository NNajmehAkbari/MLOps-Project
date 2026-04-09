"""
Job Data Loader Module
----------------------
This module provides utility functions to ingest job advertisements from
various formats including raw text, TXT files, CSVs, and JSON.
Each record is standardized with a unique UUID and a UTC timestamp.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def build_job_record(job_text: str, source: str = "manual_input") -> dict[str, Any]:
    """
        Standardizes raw job text into a structured dictionary format.
        Generates a unique ID and timestamps the record.
        """
    cleaned_text = job_text.strip()
    if not cleaned_text:
        raise ValueError("Job advertisement text is empty.")

    return {
        "job_id": str(uuid.uuid4()),  # Generate a unique identifier for each job
        "source": source,  # Track where the data came from
        "job_text": cleaned_text,  # Store the actual advertisement content
        "created_at": datetime.utcnow().isoformat(),  # Timestamp in ISO 8601 format
    }


def load_job_ad_from_text(job_text: str, source: str = "manual_input") -> dict[str, Any]:
    """Wraps text input into a job record dictionary."""
    return build_job_record(job_text=job_text, source=source)


def load_job_ad_from_txt(file_path: str | Path) -> dict[str, Any]:
    """Reads a plain text file and converts its content into a job record."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Read content and use the file path as the source metadata
    content = path.read_text(encoding="utf-8")
    return build_job_record(job_text=content, source=str(path))


def load_job_ads_from_csv(
    file_path: str | Path,
    text_column: str = "job_text",
) -> pd.DataFrame:
    """
    Loads multiple job ads from a CSV file into a Pandas DataFrame.
    Validates if the required text column exists.
    """
    import pandas as pd

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in CSV.")

    return df


def load_job_ad_from_json(file_path: str | Path, text_key: str = "job_text") -> dict[str, Any]:
    """
    Parses a JSON file to extract job information based on a specific key.
     """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    # Load JSON content and extract the value associated with the text_key
    payload = json.loads(path.read_text(encoding="utf-8"))
    if text_key not in payload:
        raise ValueError(f"Key '{text_key}' not found in JSON file.")

    return build_job_record(job_text=payload[text_key], source=str(path))
