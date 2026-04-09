"""
LLM-Based Job Parser Module
---------------------------
This module uses OpenAI's API to perform advanced semantic analysis of job ads.
It extracts structured data into a JSON format, handling complex fields like
subdomains and suggested assignment types that simple regex might miss.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

from src.utils.config import get_settings


@dataclass
class LLMParsedJob:
    """Dataclass to store structured job information extracted by the LLM."""
    job_title: str = "Unknown"
    seniority: str = "Not specified"
    domain: str = "General"
    subdomain: str = "General"
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    tools: list[str] | None = None
    assignment_type: str = "general_task"

    def to_dict(self) -> dict[str, Any]:
        """Convert the parsed results into a dictionary."""
        return asdict(self)


def _build_prompt(job_text: str) -> str:
    """
    Constructs the system prompt to instruct the LLM on how to parse
    the job advertisement into a specific JSON schema.
    """
    return f"""
You are an expert in analyzing job advertisements.

Extract structured information from the job ad below.

Return ONLY valid JSON. No explanation. No markdown. No extra text.

Schema:
{{
  "job_title": string,
  "seniority": one of ["intern", "junior", "mid", "senior", "not specified"],
  "domain": one of ["software_engineering", "data_science", "business", "general"],
  "subdomain": one of ["frontend", "backend", "mobile", "data", "ml", "general"],
  "required_skills": list of strings,
  "preferred_skills": list of strings,
  "tools": list of strings,
  "assignment_type": one of ["coding_task", "analysis_case", "ml_task", "system_design", "general_task"]
}}

Rules:
- Infer subdomain from skills and context
- Keep lists short (3–6 items)
- Do not hallucinate technologies not implied in text
- If unsure, use "general"

Job Ad:
\"\"\"
{job_text}
\"\"\"
"""


def _safe_json_load(text: str) -> dict:
    """
    Attempts to parse JSON from the LLM response.
    Handles cases where the LLM might wrap the JSON in Markdown or extra text.
    """
    text = text.strip()

    # Step 1: Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Step 2: Try to find and extract a JSON block using curly braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse JSON from LLM response")


def parse_job_ad_with_llm(job_text: str) -> LLMParsedJob:
    """
    Main entry point for LLM parsing.
    Initializes OpenAI client, sends the prompt, and maps the response to LLMParsedJob.
     """
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    prompt = _build_prompt(job_text)

    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You extract structured information from job advertisements and return JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw_output = response.choices[0].message.content or ""
    raw_output = raw_output.strip()

    if not raw_output:
        raise ValueError("Empty response from LLM")

    # Parse raw text into a dictionary
    try:
        parsed_json = _safe_json_load(raw_output)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM JSON: {e}\nRaw output:\n{raw_output}")

    # Return the mapped dataclass object
    return LLMParsedJob(
        job_title=parsed_json.get("job_title", "Unknown"),
        seniority=parsed_json.get("seniority", "Not specified"),
        domain=parsed_json.get("domain", "General"),
        subdomain=parsed_json.get("subdomain", "General"),
        required_skills=parsed_json.get("required_skills", []),
        preferred_skills=parsed_json.get("preferred_skills", []),
        tools=parsed_json.get("tools", []),
        assignment_type=parsed_json.get("assignment_type", "general_task"),
    )
