from src.evaluation import judge as judge_module


def test_judge_assignment_uses_gemini_provider(monkeypatch) -> None:
    monkeypatch.setenv("JUDGE_PROVIDER", "gemini")
    monkeypatch.setenv("JUDGE_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("JUDGE_API_KEY", "dummy-key")

    captured: dict[str, object] = {}

    def fake_call_gemini_judge(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return {
            "relevance_score": 5,
            "clarity_score": 4,
            "realism_score": 5,
            "difficulty_fit_score": 4,
            "overall_score": 4.5,
            "reasoning": "Looks good",
        }

    monkeypatch.setattr(judge_module, "_call_gemini_judge", fake_call_gemini_judge)

    result = judge_module.judge_assignment_with_llm(
        cleaned_job_text="Job text",
        assignment_text="Assignment text",
        parsed_data={"domain": "business"},
    )

    assert captured["model"] == "gemini-2.5-flash"
    assert captured["api_key"] == "dummy-key"
    assert result.overall_score == 4.5
    assert result.relevance_score == 5.0
    assert result.reasoning == "Looks good"
