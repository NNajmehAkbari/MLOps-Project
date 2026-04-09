from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.extraction.job_parser import JobAdFeatures
from src.utils.config import get_settings


@dataclass
class GenerationResult:
    provider: str
    model: str
    content: str


class AssignmentGenerator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = self.settings.llm_provider

    def generate(
        self,
        prompt: str,
        parsed: Optional[JobAdFeatures] = None,
        regenerate: bool = False,
        feedback_reason: str | None = None,
    ) -> GenerationResult:
        if self.provider == "mock":
            return self._generate_mock(
                parsed=parsed,
                regenerate=regenerate,
                feedback_reason=feedback_reason,
            )

        if self.provider == "openai":
            return self._generate_openai(prompt)

        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _generate_mock(
        self,
        parsed: Optional[JobAdFeatures],
        regenerate: bool = False,
        feedback_reason: str | None = None,
    ) -> GenerationResult:
        role = parsed.job_title if parsed else "Data Professional"
        seniority = parsed.seniority if parsed else "Not specified"
        skills = ", ".join(parsed.required_skills) if parsed and parsed.required_skills else "Python, SQL, analysis"

        task_line = (
            "You are given a small sample dataset and a business problem related to the role. "
            "Analyze the data, propose an approach, and implement a clear and practical solution."
        )

        estimated_time = "3 to 5 hours"

        if regenerate:
            if feedback_reason == "too easy":
                task_line = (
                    "You are given a realistic business case, a small dataset, and an open-ended decision problem. "
                    "Analyze the data, build a solution, justify your design choices, and discuss trade-offs."
                )
                estimated_time = "4 to 6 hours"
            elif feedback_reason == "too hard":
                task_line = (
                    "You are given a clearly scoped business case and a small dataset. "
                    "Perform a focused analysis and provide a simple, well-explained solution."
                )
                estimated_time = "2 to 4 hours"
            elif feedback_reason == "not relevant":
                task_line = (
                    f"Design a task directly tied to the role of {role}. "
                    "The solution should clearly demonstrate the candidate's ability in the most relevant job skills."
                )
            elif feedback_reason == "unclear":
                task_line = (
                    "Complete the assignment in clearly defined steps: understand the problem, analyze the data, "
                    "implement a solution, and explain the results and assumptions."
                )
            elif feedback_reason == "generic output":
                task_line = (
                    f"You are working in a realistic domain-specific scenario for a {role} position. "
                    "Use the context of the job ad to propose a concrete and role-specific solution."
                )

        version_note = "Revised Version" if regenerate else "Version 1"

        mock_text = f"""Title:
Take-Home Assignment for {role} ({version_note})

Context:
This assignment is designed for a {seniority} candidate and focuses on the core skills required for the role.

Task Description:
{task_line} Your work should demonstrate your understanding of the role requirements, especially in: {skills}.

Expected Deliverables:
- A short report describing your approach
- A clean and well-structured implementation
- A short explanation of assumptions, limitations, and possible improvements

Evaluation Criteria:
- Relevance to the job requirements
- Technical correctness
- Clarity of communication
- Structure and completeness of the solution

Estimated Completion Time:
{estimated_time}
"""
        return GenerationResult(
            provider="mock",
            model="mock-assignment-generator",
            content=mock_text,
        )

    def _generate_openai(self, prompt: str) -> GenerationResult:
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment.")

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)

        response = client.responses.create(
            model=self.settings.openai_model,
            input=prompt,
        )

        content = getattr(response, "output_text", None)
        if not content or not content.strip():
            raise ValueError("Model returned an empty response.")

        return GenerationResult(
            provider="openai",
            model=self.settings.openai_model,
            content=content.strip(),
        )
