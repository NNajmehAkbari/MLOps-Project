"""
Prompt Construction Module (Advanced Version)
--------------------------------------------
This module orchestrates the creation of complex prompts for the LLM.
It supports:
1. Dynamic template filling with job features.
2. Few-shot learning via past examples.
3. User preference injection (duration, difficulty, focus).
4. Conditional logic for task regeneration based on specific feedback.
"""

from __future__ import annotations

from typing import Any

from src.prompting.templates import load_prompt_template
from src.utils.config import get_settings


def _format_list(items: list[str] | None) -> str:
    """Converts a list into a comma-separated string or 'Not specified' if empty."""
    return ", ".join(items) if items else "Not specified"


def _truncate_text(text: str, max_chars: int = 800) -> str:
    """Truncates long text to stay within LLM context window limits."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def _build_few_shot_section(retrieved_examples: list[dict[str, Any]]) -> str:
    """
    Creates a 'Few-Shot' learning section by providing examples of
    past job ads and their successful assignments to guide the LLM.
    """
    lines = [
        "",
        "",
        "You are given examples of real job ads and their corresponding take-home assignments.",
        "Use these examples to understand the expected structure, level of detail, and style.",
        "Do NOT copy content. Generate a new assignment based on the new job ad.",
    ]

    for idx, example in enumerate(retrieved_examples, start=1):
        # Truncate examples to prevent them from dominating the prompt
        job_ad_text = _truncate_text(example.get("job_ad_text", ""))
        assignment_text = _truncate_text(example.get("assignment_text", ""))

        lines.extend(
            [
                "",
                f"### Example {idx}",
                "",
                "Job Ad:",
                job_ad_text,
                "",
                "Assignment:",
                assignment_text,
            ]
        )

    lines.extend(
        [
            "",
            "### Now generate a new assignment for the following job:",
        ]
    )

    return "\n".join(lines)


def _build_preferences_section(
    target_duration: str | None = None,
    focus_area: str | None = None,
    difficulty: str | None = None,
) -> str:
    """
    Adds optional constraints to the prompt like time limit or technical focus.
    """
    lines = []

    if target_duration:
        lines.append(f"- Target completion time: around {target_duration}.")
    if difficulty:
        lines.append(f"- Difficulty level: {difficulty}.")
    if focus_area:
        lines.append(f"- Focus more on this area: {focus_area}.")

    if not lines:
        return ""

    return "\n\nAdditional preferences:\n" + "\n".join(lines)


def build_prompt(
    job_text: str,
    parsed,
    previous_assignment: str | None = None,
    feedback_reason: str | None = None,
    regenerate: bool = False,
    retrieved_examples: list[dict[str, Any]] | None = None,
    target_duration: str | None = None,
    focus_area: str | None = None,
    difficulty: str | None = None,
) -> str:
    """
    Main function to generate the complete prompt string for the LLM.
    Handles standard generation and iterative feedback loops.
    """

    settings = get_settings()
    template = load_prompt_template(settings.prompt_file)

    # Safely get attributes from the parsed job object
    prompt = template.format(
        job_title=getattr(parsed, "job_title", "Unknown Role"),
        seniority=getattr(parsed, "seniority", "Not specified"),
        domain=getattr(parsed, "domain", "General"),
        required_skills=_format_list(getattr(parsed, "required_skills", [])),
        preferred_skills=_format_list(getattr(parsed, "preferred_skills", [])),
        tools=_format_list(getattr(parsed, "tools", [])),
        job_text=job_text,
    )

    # Add specific constraints if provided by the user
    preferences_section = _build_preferences_section(
        target_duration=target_duration,
        focus_area=focus_area,
        difficulty=difficulty,
    )
    if preferences_section:
        prompt += preferences_section

    # Inject few-shot examples at the beginning to prime the model
    if retrieved_examples:
        prompt = _build_few_shot_section(retrieved_examples) + "\n\n" + prompt

    # If this is a re-generation, add corrective instructions based on feedback
    if regenerate:
        extra_instruction = "\n\nCreate a NEW version of the assignment."
        extra_instruction += "\nDo not repeat the previous version."

        if feedback_reason:
            extra_instruction += f"\nThe previous version was rejected for this reason: {feedback_reason}."

        # Mapping feedback categories to specific prompt adjustments
        if feedback_reason == "too easy":
            extra_instruction += "\nMake the new version slightly more challenging, but still realistic."
        elif feedback_reason == "too hard":
            extra_instruction += "\nMake the new version simpler and narrower in scope."
        elif feedback_reason == "not relevant":
            extra_instruction += "\nMake the new version more closely aligned with the role, " \
                                 "required skills, and domain."
        elif feedback_reason == "unclear":
            extra_instruction += "\nMake the instructions clearer, more structured, and less ambiguous."
        elif feedback_reason == "generic output":
            extra_instruction += "\nMake the assignment more specific, realistic, and role-tailored."
        elif feedback_reason == "too brief":
            extra_instruction += "\nMake the assignment a bit more complete and informative."
        elif feedback_reason == "too time-consuming":
            extra_instruction += "\nReduce the scope so the task is more realistic for candidates."
        elif feedback_reason == "high labor intensity":
            extra_instruction += "\nReduce unnecessary workload and focus on the most relevant evaluation points."

        # Provide the failed version so the LLM knows what to improve
        if previous_assignment:
            extra_instruction += f"\n\nPrevious assignment:\n{previous_assignment}"

        prompt += extra_instruction

    return prompt
