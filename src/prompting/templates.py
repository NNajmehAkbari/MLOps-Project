"""
Prompt Template Management Module
---------------------------------
This module defines the structural blueprint for generating technical assignments.
It provides a fallback default template and a utility to load custom templates
from external files, ensuring the LLM always has clear instructions.
"""
from __future__ import annotations

from pathlib import Path

# The base instructions that define the persona, rules, and output schema for the AI
DEFAULT_ASSIGNMENT_PROMPT = """You are an expert technical recruiter and hiring manager.

Your task is to create a realistic take-home assignment based on the given job advertisement.

Rules:
- The assignment must match the role, seniority, and required skills.
- It should be practical, relevant, and not too generic.
- It should be realistic for a real hiring process.
- Avoid impossible tasks or overly broad research tasks.
- Keep the assignment at an appropriate scope for a candidate.

Return the result in this format:

Title:
<assignment title>

Context:
<short context paragraph>

Task Description:
<clear task description>

Expected Deliverables:
- item 1
- item 2
- item 3

Evaluation Criteria:
- criterion 1
- criterion 2
- criterion 3

Estimated Completion Time:
<time estimate>

Job Title: {job_title}
Seniority: {seniority}
Domain: {domain}
Required Skills: {required_skills}
Preferred Skills: {preferred_skills}
Tools: {tools}{additional_preferences}

Full Job Ad:
{job_text}
"""


def load_prompt_template(prompt_path: Path) -> str:
    """
    Attempts to read a template from a file.
    If the file is missing, it falls back to the hardcoded DEFAULT_ASSIGNMENT_PROMPT.
    """
    if prompt_path.exists():
        # Load custom instructions from a text file if it exists
        return prompt_path.read_text(encoding="utf-8")

    # Return the built-in default template if no file is found
    return DEFAULT_ASSIGNMENT_PROMPT
