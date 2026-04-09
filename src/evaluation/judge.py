from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from src.utils.config import get_settings


@dataclass
class JudgeResult:
    overall_score: float
    relevance_score: float
    clarity_score: float
    realism_score: float
    difficulty_fit_score: float
    reasoning: str
    raw_response: dict[str, Any]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _clamp_score(value: Any) -> float:
    score = _safe_float(value)
    if score < 1:
        return 1.0
    if score > 5:
        return 5.0
    return round(score, 2)


def _parse_json_text(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {}
        return {}


def _parse_compact_score_text(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if not text:
        return {}

    overall_match = re.search(r"overall_score\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)", text, flags=re.IGNORECASE)
    if overall_match:
        return {"overall_score": float(overall_match.group(1))}

    bare_number = re.search(r"\b([1-5](?:\.[0-9]+)?)\b", text)
    if bare_number:
        return {"overall_score": float(bare_number.group(1))}

    return {}


def _extract_gemini_text(response: Any) -> str:
    text = getattr(response, "text", "") or ""
    if text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    parts_text: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if part_text:
                parts_text.append(str(part_text))

    return "".join(parts_text).strip()


def _build_judge_prompt(
    *,
    cleaned_job_text: str,
    assignment_text: str,
    parsed_data: dict[str, Any] | None = None,
) -> str:
    job_excerpt = (cleaned_job_text or "").strip()[:900]
    assignment_excerpt = (assignment_text or "").strip()[:900]

    return f"""
Return exactly one line with five numeric scores:
relevance_score=4 clarity_score=4 realism_score=4 difficulty_fit_score=4 overall_score=4
No JSON. No explanation.

Job:
{job_excerpt}

Assignment:
{assignment_excerpt}
""".strip()


def _build_gemini_judge_config() -> dict[str, Any]:
    config: dict[str, Any] = {
        "temperature": 0,
        "response_mime_type": "text/plain",
        "max_output_tokens": 1024,
    }
    return config


def _call_mock_judge(
    *,
    prompt: str,
) -> dict[str, Any]:
    prompt_lower = prompt.lower()
    score = 4.0
    if any(keyword in prompt_lower for keyword in ["unclear", "generic", "too hard"]):
        score = 3.0
    if any(keyword in prompt_lower for keyword in ["excellent", "strong", "clear"]):
        score = 4.5
    return {
        "relevance_score": score,
        "clarity_score": score,
        "realism_score": score,
        "difficulty_fit_score": score,
        "overall_score": score,
        "reasoning": "Mock judge used for local smoke testing.",
    }


def _call_gemini_judge(
    *,
    api_key: str,
    model: str,
    prompt: str,
) -> dict[str, Any]:
    try:
        from google import genai
    except Exception as exc:
        raise ValueError("google-genai is not installed. Install google-genai to use the Gemini judge.") from exc

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=_build_gemini_judge_config(),
    )

    content = _extract_gemini_text(response)
    data = _parse_compact_score_text(content)
    if data:
        return data

    data = _parse_json_text(content)
    if data:
        return data

    preview = content.strip().replace("\n", " ")[:300]
    candidate_preview = ""
    candidates = getattr(response, "candidates", None) or []
    if candidates:
        first_candidate = candidates[0]
        finish_reason = getattr(first_candidate, "finish_reason", None)
        safety_ratings = getattr(first_candidate, "safety_ratings", None)
        candidate_preview = f" finish_reason={finish_reason} safety_ratings={safety_ratings}"
    raise ValueError(
        "Gemini judge returned an empty or unparsable response. "
        f"Response preview: {preview or '<empty>'}.{candidate_preview}"
    )


def _call_openai_judge(
    *,
    api_key: str,
    model: str,
    prompt: str,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a strict evaluator of recruitment assignments.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content or "{}"
    return _parse_json_text(content)


def judge_assignment_with_llm(
    *,
    cleaned_job_text: str,
    assignment_text: str,
    parsed_data: dict[str, Any] | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> JudgeResult:
    settings = get_settings()
    resolved_provider = (provider or settings.judge_provider or "gemini").strip().lower()
    resolved_model = (model or settings.judge_model or "").strip()
    if not resolved_model:
        resolved_model = "gemini-2.5-flash" if resolved_provider == "gemini" else settings.openai_model

    prompt = _build_judge_prompt(
        cleaned_job_text=cleaned_job_text,
        assignment_text=assignment_text,
        parsed_data=parsed_data,
    )

    if resolved_provider == "gemini":
        resolved_api_key = (api_key or settings.judge_api_key or "").strip()
        if not resolved_api_key:
            raise ValueError("JUDGE_API_KEY or GEMINI_API_KEY is not set.")

        data = _call_gemini_judge(
            api_key=resolved_api_key,
            model=resolved_model,
            prompt=prompt,
        )
    elif resolved_provider == "mock":
        data = _call_mock_judge(prompt=prompt)
    elif resolved_provider == "openai":
        resolved_api_key = (api_key or settings.openai_api_key or "").strip()
        if not resolved_api_key:
            raise ValueError("OPENAI_API_KEY is not set.")

        data = _call_openai_judge(
            api_key=resolved_api_key,
            model=resolved_model,
            prompt=prompt,
        )
    else:
        raise ValueError(f"Unsupported judge provider: {resolved_provider}")

    return JudgeResult(
        overall_score=_clamp_score(data.get("overall_score")),
        relevance_score=_clamp_score(data.get("relevance_score", data.get("overall_score"))),
        clarity_score=_clamp_score(data.get("clarity_score", data.get("overall_score"))),
        realism_score=_clamp_score(data.get("realism_score", data.get("overall_score"))),
        difficulty_fit_score=_clamp_score(data.get("difficulty_fit_score", data.get("overall_score"))),
        reasoning=str(data.get("reasoning", "")).strip(),
        raw_response=data,
    )
