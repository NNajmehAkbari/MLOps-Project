"""
Text Cleaning Utilities for Job Advertisements
----------------------------------------------
This module provides functions to sanitize raw job descriptions.
It removes HTML tags, standardizes whitespace, and filters out
common boilerplate legal/recruitment phrases.
"""

from __future__ import annotations

import re


def remove_html_tags(text: str) -> str:
    """Removes all HTML tags from the string using regular expressions."""
    return re.sub(r"<[^>]+>", " ", text)


def normalize_whitespace(text: str) -> str:
    """
    Standardizes line breaks and removes redundant spaces.
    Converts multiple spaces into one and limits consecutive newlines to two.
    """
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)  # Replace multiple tabs/spaces with one space
    text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 consecutive newlines
    return text.strip()


def remove_common_boilerplate(text: str) -> str:
    """
    Identifies and removes generic recruitment phrases (boilerplate)
    that don't describe the actual job role.
    """

    boilerplate_patterns = [
        r"apply now",
        r"click here to apply",
        r"equal opportunity employer",
        r"we value diversity and inclusion",
    ]

    cleaned = text
    for pattern in boilerplate_patterns:
        # Replaces identified patterns with an empty string, ignoring case.
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned


def clean_job_text(text: str) -> str:
    """
    The main cleaning pipeline.
    Sequentially applies HTML removal, boilerplate filtering, and whitespace normalization.
    """
    if not text or not text.strip():
        raise ValueError("Input job text is empty.")

    cleaned = remove_html_tags(text)
    cleaned = remove_common_boilerplate(cleaned)
    cleaned = normalize_whitespace(cleaned)
    return cleaned