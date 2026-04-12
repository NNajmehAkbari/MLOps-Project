from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from types import SimpleNamespace
from urllib import error as urllib_error
from urllib import request as urllib_request

import pandas as pd
import streamlit as st


# =========================================================
# Page config + styling
# =========================================================
st.set_page_config(
    page_title="Recruitment Assignment Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }

    .block-container {
        padding-top: 4rem;
        padding-bottom: 2rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.9rem;
        font-weight: 600;
    }

    .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        height: 2.9rem;
        font-weight: 600;
    }

    .stTextArea textarea,
    .stTextInput input,
    .stSelectbox div[data-baseweb="select"],
    .stNumberInput input {
        border-radius: 10px !important;
    }

    .app-title {
        font-size: 2rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 0;
        margin-bottom: 0.2rem;
        line-height: 1.25;
    }

    .app-subtitle {
        color: #475569;
        max-width: 720px;
        line-height: 1.5;
        margin-bottom: 0;
    }

    .hero-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        padding: 1.1rem 1.25rem 1rem;
        border-radius: 20px;
        border: 1px solid #dbe4f0;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
        margin-bottom: 0.75rem;
    }

    .input-card {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        padding: 1rem 1.1rem 1.15rem;
        border-radius: 20px;
        border: 1px solid #dbe4f0;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.04);
        margin-bottom: 1rem;
    }

    .hero-kicker {
        display: inline-block;
        margin-bottom: 0.45rem;
        padding: 0.22rem 0.6rem;
        border-radius: 999px;
        background: #e0f2fe;
        color: #075985;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .section-card {
        background-color: white;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        margin-bottom: 16px;
    }

    .section-title {
        color: #0f172a;
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.75rem;
    }

    .small-muted {
        color: #64748b;
        font-size: 0.92rem;
    }

    .pill {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #3730a3;
        font-size: 0.84rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }

    .runtime-caption {
        color: #64748b;
        font-size: 0.84rem;
        line-height: 1.35;
        margin-bottom: 0.55rem;
    }

    .runtime-pill-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.45rem;
    }

    .runtime-pill {
        width: 100%;
        padding: 0.62rem 0.7rem 0.58rem;
        border-radius: 14px;
        border: 1px solid #dbe4f0;
        background: #ffffff;
        color: #0f172a;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
    }

    .runtime-pill-label {
        display: block;
        color: #64748b;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }

    .runtime-pill-value {
        display: block;
        font-size: 0.84rem;
        font-weight: 700;
        line-height: 1.3;
        word-break: break-word;
    }

    .runtime-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        margin-top: 0.45rem;
        padding: 0.34rem 0.65rem;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #bfdbfe;
    }

    @media (max-width: 720px) {
        .runtime-pill-grid {
            grid-template-columns: 1fr;
        }
    }

    .sidebar-title {
        font-size: 0.98rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0.15rem 0 0.75rem;
        letter-spacing: -0.01em;
    }

    .sidebar-card {
        background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
        border: 1px solid #dbe4f0;
        border-radius: 16px;
        padding: 0.8rem 0.8rem 0.85rem;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
        margin-bottom: 0.75rem;
    }

    .sidebar-card + .sidebar-card {
        margin-top: 0.2rem;
    }

    .sidebar-section-title {
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #475569;
        margin: 0.95rem 0 0.55rem;
    }

    section[data-testid="stSidebar"] {
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 0.92rem;
    }

    section[data-testid="stSidebar"] .sidebar-card,
    section[data-testid="stSidebar"] .sidebar-card * {
        font-family: inherit;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stCaption {
        font-size: inherit;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e2e8f0;
        padding: 12px;
        border-radius: 14px;
        box-shadow: 0 1px 6px rgba(15, 23, 42, 0.03);
    }

    div[data-testid="stExpander"] {
        border: none !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
        border-radius: 12px;
        margin-bottom: 0.9rem;
    }

    .divider-space {
        height: 0.35rem;
    }

    .page-section-gap {
        height: 1.1rem;
    }

    div[data-baseweb="tab-list"] {
        gap: 0.45rem;
        padding: 0.4rem 0.45rem 0.35rem;
        border-bottom: 1px solid #dbe4f0;
        background: #eef4fb;
        border-radius: 16px 16px 0 0;
        margin-bottom: 0.15rem;
    }

    button[data-baseweb="tab"] {
        border-radius: 999px !important;
        padding: 0.7rem 1rem !important;
        margin-right: 0.2rem;
        border: 1px solid transparent !important;
        background: #ffffff !important;
        color: #475569 !important;
        font-weight: 600 !important;
        transition: all 0.18s ease-in-out;
    }

    button[data-baseweb="tab"]:hover {
        background: #f8fbff !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: #0f172a !important;
        color: #ffffff !important;
        border-color: #0f172a !important;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.16);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Project imports
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.feedback.candidate_feedback_store import load_candidate_feedback
from src.services.assignment_workflow import (
    persist_assignment_version,
    run_assignment_workflow,
)
from src.storage.backend import get_storage_backend
from src.services.review_workflow import (
    regenerate_assignment_from_feedback,
    save_candidate_feedback_entry,
    save_final_review_decision,
    save_reviewer_feedback,
)
from src.services.versioning_service import load_version_bundle
from src.utils.config import get_settings


settings = get_settings()


def _safe_json(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


def _render_payload_list(
    title: str,
    payload: list[dict[str, Any]] | None,
    empty_message: str,
    *,
    label_keys: tuple[str, ...] = ("version", "assignment_id", "feedback_id", "review_id", "job_id"),
) -> None:
    with st.expander(title, expanded=False):
        if not payload:
            st.info(empty_message)
            return

        st.write(f"{len(payload)} row(s)")
        for index, item in enumerate(payload, start=1):
            label = None
            for key in label_keys:
                value = item.get(key)
                if value not in {None, ""}:
                    label = value
                    break
            if label is None:
                label = index
            with st.expander(f"Row {index}: {label}", expanded=False):
                st.json(item)


def _render_payload_object(title: str, payload: dict[str, Any] | None, empty_message: str) -> None:
    with st.expander(title, expanded=False):
        if not payload:
            st.info(empty_message)
        else:
            st.json(payload)


def _render_summary_table(
    title: str,
    rows: list[dict[str, Any]] | None,
    empty_message: str,
    columns: list[str],
    filter_column: str | None = None,
    rename_columns: dict[str, str] | None = None,
) -> None:
    with st.expander(title, expanded=False):
        if not rows:
            st.info(empty_message)
            return

        frame = pd.DataFrame(rows)
        if columns:
            selected_columns = [column for column in columns if column in frame.columns]
            if selected_columns:
                frame = frame[selected_columns]

        if rename_columns:
            frame = frame.rename(columns={key: value for key, value in rename_columns.items() if key in frame.columns})

        if filter_column and filter_column in frame.columns and not frame.empty:
            filter_values = sorted({str(value) for value in frame[filter_column].dropna().tolist() if str(value).strip()})
            if filter_values:
                selected_filter = st.selectbox(
                    f"Filter {title}",
                    ["All"] + filter_values,
                    key=f"filter_{title}",
                )
                if selected_filter != "All":
                    frame = frame[frame[filter_column].astype(str) == selected_filter]

        export_name = f"{title.lower().replace(' ', '_').replace('/', '_')}.csv"
        st.download_button(
            f"Download {title}",
            data=frame.to_csv(index=False),
            file_name=export_name,
            mime="text/csv",
            key=f"download_{title}",
        )
        st.dataframe(frame, use_container_width=True, hide_index=True)


def _format_metric_value(value: Any, precision: int = 2) -> str:
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        text = str(value).strip()
        return text or "N/A"


def _format_percentage_metric(value: Any, precision: int = 0) -> str:
    if value is None:
        return "N/A"

    try:
        return f"{float(value) * 100:.{precision}f}%"
    except (TypeError, ValueError):
        return "N/A"


def _kpi_value(kpis: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = kpis.get(key)
        if value is not None:
            return value
    return None


def _sync_selected_version_state(selected_item: dict[str, Any]) -> None:
    st.session_state.assignment_id = selected_item.get("assignment_id")
    st.session_state.assignment_text = selected_item.get("text", "")
    st.session_state.retrieved_examples = selected_item.get("retrieved_examples", [])
    st.session_state.kpis = selected_item.get("kpis")
    st.session_state.version = selected_item.get("version", st.session_state.get("version", 1))


def _get_storage_bootstrap_status(settings) -> dict[str, Any]:
    cache_key = "storage_bootstrap_status"
    cached = st.session_state.get(cache_key)
    if isinstance(cached, dict) and cached.get("backend") == settings.storage_backend:
        return cached

    return {
        "backend": settings.storage_backend,
        "status": "unchecked",
        "message": "Connection check not run yet.",
    }


def _run_storage_bootstrap(settings) -> dict[str, Any]:
    backend = get_storage_backend()
    try:
        status = backend.bootstrap()
    except Exception as exc:
        status = {
            "backend": backend.name,
            "status": "error",
            "message": str(exc),
        }

    st.session_state["storage_bootstrap_status"] = status
    return status


def _render_kpi_metric(label: str, value: Any, *, percentage: bool = False, precision: int = 0) -> None:
    formatted = (
        _format_percentage_metric(value, precision=precision)
        if percentage
        else _format_metric_value(value, precision=precision)
    )
    st.metric(label, formatted)


def _render_kpi_group(title: str, metric_specs: list[dict[str, Any]], columns: int = 2) -> None:
    st.markdown(f"**{title}**")
    rows = [metric_specs[index : index + columns] for index in range(0, len(metric_specs), columns)]

    for row in rows:
        cols = st.columns(len(row))
        for col, spec in zip(cols, row):
            with col:
                _render_kpi_metric(
                    spec["label"],
                    spec["value"],
                    percentage=spec.get("percentage", False),
                    precision=spec.get("precision", 0),
                )


def _apply_feedback_to_current_version(feedback_value: str) -> None:
    current_assignment_id = st.session_state.get("assignment_id")
    if not current_assignment_id:
        return

    updated = False
    feedback_rating = st.session_state.get("review_feedback_rating")
    try:
        feedback_rating = float(feedback_rating) if feedback_rating is not None else None
    except (TypeError, ValueError):
        feedback_rating = None

    if feedback_rating is None:
        return

    for item in st.session_state.get("version_history", []):
        if item.get("assignment_id") != current_assignment_id:
            continue

        kpis = dict(item.get("kpis") or {})
        kpis["reviewer_rating"] = feedback_rating
        kpis.pop("reviewer_feedback_score", None)
        item["kpis"] = kpis
        updated = True
        break

    if updated:
        st.session_state.kpis = kpis


def _format_parsed_value(value):
    if value is None:
        return "—"
    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        return ", ".join(cleaned) if cleaned else "—"
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v if str(x).strip())
            parts.append(f"{k}: {v}")
        return " | ".join(parts) if parts else "—"
    text = str(value).strip()
    return text if text else "—"


def render_parsed_job_human(parsed_data: dict[str, Any] | None) -> None:
    if not parsed_data:
        st.info("Parsed data not available yet.")
        return

    preferred_order = [
        "job_title",
        "title",
        "company",
        "domain",
        "subdomain",
        "seniority",
        "employment_type",
        "location",
        "required_skills",
        "preferred_skills",
        "tools",
        "responsibilities",
        "qualifications",
        "education",
        "language_requirements",
    ]

    labels = {
        "job_title": "Job Title",
        "title": "Job Title",
        "company": "Company",
        "domain": "Domain",
        "subdomain": "Subdomain",
        "seniority": "Seniority",
        "employment_type": "Employment Type",
        "location": "Location",
        "required_skills": "Required Skills",
        "preferred_skills": "Preferred Skills",
        "tools": "Tools",
        "responsibilities": "Responsibilities",
        "qualifications": "Qualifications",
        "education": "Education",
        "language_requirements": "Language Requirements",
    }

    rows = []

    for key in preferred_order:
        if key in parsed_data and not str(key).startswith("_"):
            rows.append(
                {
                    "Field": labels.get(key, key.replace("_", " ").title()),
                    "Value": _format_parsed_value(parsed_data.get(key)),
                }
            )

    for key, value in parsed_data.items():
        if key not in preferred_order and not str(key).startswith("_"):
            rows.append(
                {
                    "Field": labels.get(key, key.replace("_", " ").title()),
                    "Value": _format_parsed_value(value),
                }
            )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_retrieval_debug(retrieved_examples: list[dict[str, Any]]) -> None:
    if not retrieved_examples:
        return

    first_item = retrieved_examples[0]
    route_type = first_item.get("route_type", "N/A")
    selected_domains = first_item.get("selected_domains", ["all"])
    if isinstance(selected_domains, list):
        selected_domains = ", ".join(selected_domains)

    with st.expander("Retrieval Debug", expanded=False):
        st.info(
            f"Route Type: {route_type} | "
            f"Selected Domains: {selected_domains} | "
            f"Retrieved Examples: {len(retrieved_examples)}"
        )
        st.markdown("**Domain Scores**")
        st.code(_safe_json(first_item.get("domain_scores", {})), language="json")


def render_retrieved_examples(retrieved_examples: list[dict[str, Any]]) -> None:
    if not retrieved_examples:
        st.info("No retrieved examples were used for this version.")
        return

    for idx, example in enumerate(retrieved_examples, start=1):
        company = example.get("company") or "Unknown"
        subdomain = example.get("subdomain") or "N/A"
        score = example.get("score", 0.0)
        title = f"{idx}. {company} | {subdomain} | score={score}"

        with st.expander(title, expanded=(idx == 1)):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write("**Semantic score:**", example.get("semantic_score"))
            with c2:
                st.write("**Domain:**", example.get("domain"))
            with c3:
                st.write("**Seniority:**", example.get("seniority"))

            reasons = example.get("reasons", [])
            if reasons:
                st.write("**Reasons:**", ", ".join(reasons))

            if example.get("job_ad_text"):
                st.markdown("**Job Ad Preview**")
                st.write(example.get("job_ad_text", ""))

            if example.get("assignment_text"):
                st.markdown("**Assignment Preview**")
                st.write(example.get("assignment_text", ""))

            folder_path = example.get("folder_path")
            if folder_path:
                st.caption(f"Source: {folder_path}")


def _build_kpi_section_specs(kpis: dict[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = [
        {
            "title": "Similarity KPIs",
            "columns": 2,
            "metrics": [
                {
                    "label": "JobBERT-v3 Score",
                    "value": _kpi_value(kpis, "jobbert_v3_score", "model_score"),
                    "percentage": True,
                },
                {
                    "label": "Semantic Similarity Average",
                    "value": kpis.get("retrieval_semantic_avg"),
                    "percentage": True,
                },
            ],
        },
        {
            "title": "Performance KPIs",
            "columns": 2,
            "metrics": [
                {
                    "label": "Generation Latency (s)",
                    "value": kpis.get("generation_latency_seconds"),
                    "precision": 2,
                },
                {
                    "label": "Judge Latency (s)",
                    "value": kpis.get("judge_latency_seconds"),
                    "precision": 2,
                },
                {
                    "label": "Workflow Latency (s)",
                    "value": kpis.get("workflow_latency_seconds"),
                    "precision": 2,
                },
            ],
            "caption": "Lower latency is better. These timings are measured in seconds.",
        },
        {
            "title": "Retrieval Quality KPIs",
            "columns": 2,
            "metrics": [
                {
                    "label": "Rerank Average",
                    "value": kpis.get("retrieval_score_avg"),
                    "percentage": True,
                },
                {
                    "label": "Domain Precision",
                    "value": kpis.get("retrieval_domain_precision"),
                    "percentage": True,
                },
            ],
        },
        {
            "title": "Evaluation KPIs",
            "columns": 2,
            "metrics": [
                {
                    "label": "Overall Score",
                    "value": kpis.get("llm_judge_score"),
                    "precision": 2,
                },
                {
                    "label": "Relevance",
                    "value": kpis.get("llm_judge_relevance"),
                    "precision": 0,
                },
                {
                    "label": "Clarity",
                    "value": kpis.get("llm_judge_clarity"),
                    "precision": 0,
                },
                {
                    "label": "Realism",
                    "value": kpis.get("llm_judge_realism"),
                    "precision": 0,
                },
                {
                    "label": "Difficulty Fit",
                    "value": kpis.get("llm_judge_difficulty_fit"),
                    "precision": 0,
                },
            ],
            "reasoning": kpis.get("llm_judge_reasoning"),
            "caption": "The Gemini judge produces relevance, clarity, realism, and difficulty-fit sub-scores.",
        },
        {
            "title": "Rule-Based KPIs",
            "columns": 2,
            "metrics": [
                {
                    "label": "Skill Coverage",
                    "value": kpis.get("skill_coverage"),
                    "percentage": True,
                },
                {
                    "label": "Structure Compliance",
                    "value": kpis.get("structure_compliance"),
                    "percentage": True,
                },
                {
                    "label": "Regeneration Flag",
                    "value": kpis.get("regeneration_flag", 0),
                },
            ],
        },
    ]

    reviewer_rating = kpis.get("reviewer_rating")
    if reviewer_rating is not None:
        sections.append(
            {
                "title": "Human Review KPIs",
                "columns": 1,
                "metrics": [
                    {
                        "label": "Reviewer Rating",
                        "value": reviewer_rating,
                        "precision": 0,
                    },
                ],
            }
        )

    return sections


def render_kpis_dashboard(kpis: dict[str, Any] | None) -> None:
    if not kpis:
        st.info("No KPI data available yet.")
        return

    st.caption("Percentage KPIs are shown on a 0-100% scale. Judge scores and reviewer ratings use 1-5 scales. Latency KPIs are shown in seconds.")

    sections = _build_kpi_section_specs(kpis)
    for index, section in enumerate(sections):
        if index:
            st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)

        _render_kpi_group(section["title"], section["metrics"], columns=section.get("columns", 2))

        reasoning = section.get("reasoning")
        if reasoning:
            with st.expander("Gemini judge reasoning", expanded=False):
                st.write(reasoning)

        caption = section.get("caption")
        if caption:
            st.caption(caption)

    st.caption(f"Retrieved examples count: {kpis.get('retrieved_examples_count', 0)}")


def _render_trend_chart(title: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not rows:
        return

    df = pd.DataFrame(rows).sort_values("version")
    if len(columns) == 1:
        st.line_chart(df.set_index("version")[columns[0]])
    else:
        st.line_chart(df.set_index("version")[columns])
    st.caption(title)


def render_kpi_trend_charts(version_history: list[dict[str, Any]]) -> None:
    rows = []
    for item in version_history:
        kpis = item.get("kpis") or {}
        rows.append(
            {
                "version": item.get("version"),
                "jobbert_v3_score": _kpi_value(kpis, "jobbert_v3_score", "model_score"),
                "retrieval_semantic_avg": kpis.get("retrieval_semantic_avg"),
                "retrieval_score_avg": kpis.get("retrieval_score_avg"),
                "retrieval_domain_precision": kpis.get("retrieval_domain_precision"),
                "skill_coverage": kpis.get("skill_coverage"),
                "structure_compliance": kpis.get("structure_compliance"),
                "llm_judge_score": kpis.get("llm_judge_score"),
                "llm_judge_relevance": kpis.get("llm_judge_relevance"),
                "llm_judge_clarity": kpis.get("llm_judge_clarity"),
                "llm_judge_realism": kpis.get("llm_judge_realism"),
                "llm_judge_difficulty_fit": kpis.get("llm_judge_difficulty_fit"),
                "reviewer_rating": kpis.get("reviewer_rating"),
                "generation_latency_seconds": kpis.get("generation_latency_seconds"),
                "judge_latency_seconds": kpis.get("judge_latency_seconds"),
                "workflow_latency_seconds": kpis.get("workflow_latency_seconds"),
            }
        )

    if not rows:
        st.info("No KPI trend data available yet.")
        return

    st.caption("Each trend chart groups metrics on a shared scale so the lines remain comparable.")

    similarity_columns = [
        "jobbert_v3_score",
        "retrieval_semantic_avg",
        "retrieval_score_avg",
        "retrieval_domain_precision",
        "skill_coverage",
        "structure_compliance",
    ]
    judge_columns = [
        "llm_judge_score",
        "llm_judge_relevance",
        "llm_judge_clarity",
        "llm_judge_realism",
        "llm_judge_difficulty_fit",
        "reviewer_rating",
    ]
    latency_columns = [
        "generation_latency_seconds",
        "judge_latency_seconds",
        "workflow_latency_seconds",
    ]

    st.markdown("##### Similarity and Retrieval Trend")
    _render_trend_chart("Similarity and retrieval KPIs are shown on a 0 to 1 scale.", rows, similarity_columns)

    st.markdown("##### Evaluation and Review Trend")
    _render_trend_chart("Gemini judge scores and reviewer ratings are shown on a 1 to 5 scale.", rows, judge_columns)

    st.markdown("##### Performance Trend")
    _render_trend_chart("Latency KPIs are shown in seconds.", rows, latency_columns)


def render_bronze_event_viewer(job_id: str | None) -> None:
    if not job_id:
        st.info("No active job loaded yet.")
        return

    backend = get_storage_backend()
    job_record = backend.load_job_record(job_id)
    assignment_events = backend.load_assignment_events(job_id)
    reviewer_feedback = backend.load_bronze_reviewer_feedback(job_id=job_id)
    candidate_feedback = backend.load_bronze_candidate_feedback(job_id)
    review_decisions = backend.load_bronze_review_decisions(job_id)

    st.caption("Bronze stores the raw or near-raw event stream behind the app.")

    sections: list[tuple[str, Any, str]] = [
        ("Job Ad Event", job_record, "No raw job ad event found yet."),
        ("Assignment Version Events", assignment_events, "No bronze assignment events found yet."),
        ("Reviewer Feedback Events", reviewer_feedback, "No reviewer feedback events found yet."),
        ("Candidate Feedback Events", candidate_feedback, "No candidate feedback events found yet."),
        ("Review Decision Events", review_decisions, "No review decision events found yet."),
    ]

    for title, payload, empty_message in sections:
        if isinstance(payload, list):
            _render_payload_list(title, payload, empty_message)
            continue
        _render_payload_object(title, payload, empty_message)


def render_silver_snapshot_viewer(job_id: str | None) -> None:
    if not job_id:
        st.info("No active job loaded yet.")
        return

    backend = get_storage_backend()
    parsed_job = backend.load_parsed_job(job_id)
    assignment_versions = backend.list_assignment_versions(job_id)
    reviewer_feedback = backend.load_feedback_records(job_id=job_id)
    candidate_feedback = backend.load_candidate_feedback(job_id)
    review_decisions = backend.load_review_decisions(job_id)

    st.caption("Silver stores the normalized snapshots that power the app views and KPIs.")

    with st.expander("Parsed Job Snapshot", expanded=False):
        if not parsed_job:
            st.info("No silver parsed job snapshot found yet.")
        else:
            render_parsed_job_human(parsed_job)

    _render_summary_table(
        "Assignment Snapshot Rows",
        assignment_versions,
        "No silver assignment snapshots found yet.",
        [
            "version",
            "assignment_id",
            "target_duration",
            "difficulty",
            "use_retrieval",
            "top_k",
            "domain_override",
            "judge_error",
        ],
        filter_column="version",
        rename_columns={
            "version": "Version",
            "assignment_id": "Assignment ID",
            "target_duration": "Target Duration",
            "difficulty": "Difficulty",
            "use_retrieval": "Use Retrieval",
            "top_k": "Top K",
            "domain_override": "Domain Override",
            "judge_error": "Judge Error",
        },
    )
    _render_summary_table(
        "Reviewer Feedback Snapshot Rows",
        reviewer_feedback,
        "No silver reviewer feedback rows found yet.",
        [
            "timestamp",
            "feedback_id",
            "assignment_id",
            "feedback",
            "reason",
            "reviewer",
            "rating",
        ],
        filter_column="assignment_id",
        rename_columns={
            "timestamp": "Timestamp",
            "feedback_id": "Feedback ID",
            "assignment_id": "Assignment ID",
            "feedback": "Feedback",
            "reason": "Reason",
            "reviewer": "Reviewer",
            "rating": "Rating",
        },
    )
    _render_summary_table(
        "Candidate Feedback Snapshot Rows",
        candidate_feedback,
        "No silver candidate feedback rows found yet.",
        [
            "created_at",
            "feedback_id",
            "assignment_id",
            "candidate_name",
            "overall_score",
            "clarity_score",
            "difficulty_score",
            "relevance_score",
            "time_reasonable",
        ],
        filter_column="assignment_id",
        rename_columns={
            "created_at": "Created At",
            "feedback_id": "Feedback ID",
            "assignment_id": "Assignment ID",
            "candidate_name": "Candidate Name",
            "overall_score": "Overall Score",
            "clarity_score": "Clarity Score",
            "difficulty_score": "Difficulty Score",
            "relevance_score": "Relevance Score",
            "time_reasonable": "Time Reasonable",
        },
    )
    _render_summary_table(
        "Review Decision Snapshot Rows",
        review_decisions,
        "No silver review decision rows found yet.",
        [
            "timestamp",
            "review_id",
            "selected_assignment_id",
            "selected_version",
            "decision",
            "reviewer",
        ],
        filter_column="decision",
        rename_columns={
            "timestamp": "Timestamp",
            "review_id": "Review ID",
            "selected_assignment_id": "Selected Assignment ID",
            "selected_version": "Selected Version",
            "decision": "Decision",
            "reviewer": "Reviewer",
        },
    )


def render_gold_summary_viewer(job_id: str | None) -> None:
    if not job_id:
        st.info("No active job loaded yet.")
        return

    backend = get_storage_backend()
    kpi_rows = backend.load_gold_kpi_summaries(job_id)
    latest_assignments = backend.load_gold_latest_assignments(job_id)

    st.caption("Gold stores analytics-ready summaries and the latest assignment snapshots.")

    _render_summary_table(
        "Gold KPI Summary Rows",
        kpi_rows,
        "No gold KPI summary rows found yet.",
        [
            "version",
            "assignment_id",
            "jobbert_v3_score",
            "retrieval_semantic_avg",
            "retrieval_domain_precision",
            "skill_coverage",
            "structure_compliance",
            "llm_judge_score",
            "reviewer_rating",
            "generation_latency_seconds",
            "judge_latency_seconds",
            "workflow_latency_seconds",
        ],
        filter_column="version",
        rename_columns={
            "version": "Version",
            "assignment_id": "Assignment ID",
            "jobbert_v3_score": "JobBERT-v3 Score",
            "retrieval_semantic_avg": "Retrieval Semantic Avg",
            "retrieval_domain_precision": "Retrieval Domain Precision",
            "skill_coverage": "Skill Coverage",
            "structure_compliance": "Structure Compliance",
            "llm_judge_score": "Gemini Judge Score",
            "reviewer_rating": "Reviewer Rating",
            "generation_latency_seconds": "Generation Latency (s)",
            "judge_latency_seconds": "Judge Latency (s)",
            "workflow_latency_seconds": "Workflow Latency (s)",
        },
    )
    _render_summary_table(
        "Gold Latest Assignment Rows",
        latest_assignments,
        "No gold latest assignment rows found yet.",
        ["version", "assignment_id", "job_id"],
        filter_column="assignment_id",
        rename_columns={
            "version": "Version",
            "assignment_id": "Assignment ID",
            "job_id": "Job ID",
        },
    )


def reset_current_session() -> None:
    st.session_state.job_id = None
    st.session_state.assignment_id = None
    st.session_state.assignment_text = None
    st.session_state.parsed_data = None
    st.session_state.cleaned_text = None
    st.session_state.version = 1
    st.session_state.version_history = []
    st.session_state.retrieved_examples = []
    st.session_state.parsing_source = None
    st.session_state.kpis = None


def load_versions_into_session(job_id: str) -> None:
    bundle = load_version_bundle(job_id)
    if not bundle:
        return
    st.session_state.job_id = bundle.job_id
    st.session_state.assignment_id = bundle.latest_assignment.get("assignment_id")
    st.session_state.assignment_text = bundle.latest_assignment.get("assignment_text", "")
    st.session_state.parsed_data = bundle.parsed_data
    st.session_state.cleaned_text = bundle.cleaned_job_text or None
    st.session_state.version = bundle.latest_assignment.get("version", len(bundle.version_history))
    st.session_state.version_history = bundle.version_history
    st.session_state.retrieved_examples = bundle.latest_assignment.get("retrieved_examples", [])
    st.session_state.parsing_source = bundle.latest_assignment.get("parsing_source", "unknown")
    st.session_state.kpis = bundle.latest_version_item.get("kpis")


def get_selected_version_item(version_history: list[dict[str, Any]], label: str) -> dict[str, Any]:
    version_number = int(label.replace("Version ", ""))
    return next(item for item in version_history if item["version"] == version_number)


def init_session_defaults() -> None:
    defaults = {
        "job_id": None,
        "assignment_id": None,
        "assignment_text": None,
        "parsed_data": None,
        "cleaned_text": None,
        "version": 1,
        "version_history": [],
        "retrieved_examples": [],
        "parsing_source": None,
        "kpis": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar_controls(settings) -> dict[str, Any]:
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>⚙️ Generator Settings</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-title'>Assignment Settings</div>", unsafe_allow_html=True)
        duration_display = st.select_slider(
            "Target Duration",
            options=list(settings.duration_options),
            value=settings.default_duration,
        )
        assignment_hours = settings.duration_labels[duration_display]

        difficulty = st.select_slider(
            "Difficulty",
            options=list(settings.difficulty_options),
            value=settings.default_difficulty,
        )

        focus_area = st.text_input(
            "Focus Area",
            placeholder=settings.focus_area_placeholder,
            max_chars=50,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-title'>Retrieval Settings</div>", unsafe_allow_html=True)
        use_retrieval = st.toggle("Use few-shot retrieval", value=settings.use_retrieval_default)

        top_k = settings.retrieval_top_k_default
        domain_override = settings.retrieval_domain_options[0]
        show_retrieval_debug = settings.show_retrieval_debug_default

        if use_retrieval:
            top_k = st.slider(
                "Number of retrieved examples",
                min_value=settings.retrieval_top_k_min,
                max_value=settings.retrieval_top_k_max,
                value=settings.retrieval_top_k_default,
            )
            domain_override = st.selectbox(
                "Optional domain override",
                list(settings.retrieval_domain_options),
                index=0,
            )
            show_retrieval_debug = st.checkbox(
                "Show retrieval debug",
                value=settings.show_retrieval_debug_default,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-title'>Session</div>", unsafe_allow_html=True)
        st.caption("Reload saved versions or reset the current workspace.")
        if st.button("Reload Version History", type="secondary"):
            if st.session_state.job_id:
                load_versions_into_session(st.session_state.job_id)
                st.success("Version history reloaded.")
            else:
                st.info("No active job loaded yet.")

        if st.button("Reset Workspace", type="secondary"):
            reset_current_session()
            st.success("Workspace reset.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-title'>Runtime</div>", unsafe_allow_html=True)
        storage_status = _get_storage_bootstrap_status(settings)
        st.markdown(
            f"<div class='runtime-caption'>Loaded from environment variables or `.env`. Storage backend: {settings.storage_backend.title()}.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='runtime-pill-grid'>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='runtime-pill'><span class='runtime-pill-label'>Generation</span><span class='runtime-pill-value'>{_format_provider_label(settings.llm_provider)} · {settings.openai_model}</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='runtime-pill'><span class='runtime-pill-label'>Judge</span><span class='runtime-pill-value'>{_format_provider_label(settings.judge_provider)} · {settings.judge_model}</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='runtime-caption' style='margin-top:0.55rem;'>Storage status: <strong>{storage_status.get('status', 'unknown').title()}</strong>{' - ' + storage_status.get('message', '') if storage_status.get('message') else ''}</div>",
            unsafe_allow_html=True,
        )
        generation_mode = "API" if _api_mode_enabled() else "Local"
        generation_detail = (
            "API-backed generation is enabled via `RECRUITMENT_API_BASE_URL`."
            if generation_mode == "API"
            else "Running the local workflow directly."
        )
        st.markdown(
            f"<div class='runtime-caption'>Generation mode: <strong>{generation_mode}</strong> - {generation_detail}</div>",
            unsafe_allow_html=True,
        )
        read_path_label = "Bronze read path active" if settings.storage_backend == "databricks" else "Local read path active"
        st.markdown(
            f"<div class='runtime-badge'>{read_path_label}</div>",
            unsafe_allow_html=True,
        )
        if st.button("Check Databricks Connection", key="check_databricks_connection"):
            with st.spinner("Checking Databricks connection..."):
                storage_status = _run_storage_bootstrap(settings)
            st.success(storage_status.get("message", "Connection check complete."))
        st.markdown("</div>", unsafe_allow_html=True)

    return {
        "duration_display": duration_display,
        "assignment_hours": assignment_hours,
        "difficulty": difficulty,
        "focus_area": focus_area,
        "use_retrieval": use_retrieval,
        "top_k": top_k,
        "domain_override": domain_override,
        "show_retrieval_debug": show_retrieval_debug,
    }


def render_app_header(settings) -> None:
    st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hero-kicker'>Assignment Lab</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='app-title'>{settings.app_title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='app-subtitle'>{settings.app_subtitle}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_job_input_section(settings) -> tuple[str, bool]:
    st.markdown("<div class='input-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>1. Job Advertisement Input</div>", unsafe_allow_html=True)
    st.caption("Paste the job ad below, then generate a structured assignment from it.")

    job_text_input = st.text_area(
        "Job Advertisement Text",
        height=300,
        placeholder=settings.job_input_placeholder,
        label_visibility="visible",
    )

    generate_col1, generate_col2 = st.columns([2, 1])
    with generate_col1:
        generate_clicked = st.button("✨ Generate Assignment", type="primary")
    with generate_col2:
        st.caption(settings.generation_note)

    st.markdown("</div>", unsafe_allow_html=True)
    return job_text_input, generate_clicked


def _format_provider_label(provider: str) -> str:
    provider = (provider or "").strip().lower()
    if provider == "openai":
        return "OpenAI"
    if provider == "gemini":
        return "Gemini"
    return provider.title() if provider else "Unknown"


def _api_base_url() -> str:
    return os.getenv("RECRUITMENT_API_BASE_URL", "").strip().rstrip("/")


def _api_mode_enabled() -> bool:
    return bool(_api_base_url())


def _api_request_json(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    base_url = _api_base_url()
    if not base_url:
        raise ValueError("RECRUITMENT_API_BASE_URL is not set.")

    url = f"{base_url}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib_request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib_request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8").strip()
            return json.loads(raw) if raw else {}
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"API request failed: {exc.code} {exc.reason}: {detail}") from exc


def _run_generation_via_api(
    *,
    job_text: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
    assignment_hours: str,
    difficulty: str,
    focus_area: str,
) -> dict[str, Any]:
    payload = {
        "job_text": job_text,
        "assignment_hours": assignment_hours,
        "difficulty": difficulty,
        "focus_area": focus_area,
        "use_retrieval": use_retrieval,
        "top_k": top_k,
        "domain_override": domain_override,
        "show_retrieval_debug": show_retrieval_debug,
        "secret_scope": os.getenv("DATABRICKS_SECRET_SCOPE", "mlops-project").strip() or "mlops-project",
    }

    created = _api_request_json("POST", "/job-ads", payload)
    job_id = str(created.get("job_id") or "").strip()
    if not job_id:
        raise RuntimeError("API did not return a job_id.")

    created_status = str(created.get("status") or "").strip().lower()
    created_error = str(created.get("error_message") or "").strip()
    if created_status == "failed":
        raise RuntimeError(created_error or str(created.get("message") or "Failed to trigger Databricks job.").strip())

    status_payload: dict[str, Any] = created
    result_payload: dict[str, Any] = {}
    for _ in range(180):
        status_payload = _api_request_json("GET", f"/job-ads/{job_id}")
        status = str(status_payload.get("status") or "").strip().lower()
        if status in {"completed", "failed"}:
            break
        time.sleep(2)

    status_error = str(status_payload.get("error_message") or "").strip()
    if str(status_payload.get("status") or "").strip().lower() == "failed":
        raise RuntimeError(status_error or str(status_payload.get("message") or "Databricks job failed.").strip())

    for _ in range(15):
        result_payload = _api_request_json("GET", f"/job-ads/{job_id}/result")
        assignment_preview = str(result_payload.get("assignment_text") or "").strip()
        if assignment_preview:
            break
        if str(status_payload.get("status") or "").strip().lower() == "failed":
            break
        time.sleep(1)

    assignment_text = str(result_payload.get("assignment_text") or "").strip()
    result_error = str(result_payload.get("error_message") or "").strip()
    if not assignment_text and result_error:
        raise RuntimeError(result_error)

    parsed_data = result_payload.get("result_payload", {}).get("parsed_data") if isinstance(result_payload.get("result_payload"), dict) else {}
    if not isinstance(parsed_data, dict):
        parsed_data = {}
    parsing_source = (
        result_payload.get("result_payload", {}).get("parsing_source")
        if isinstance(result_payload.get("result_payload"), dict)
        else None
    )
    parsing_source = str(parsing_source or parsed_data.get("parsing_source") or "unknown").strip()
    retrieved_examples = []
    if isinstance(result_payload.get("result_payload"), dict):
        retrieved_examples = result_payload["result_payload"].get("retrieved_examples", []) or []
        if not isinstance(retrieved_examples, list):
            retrieved_examples = []

    result_obj = SimpleNamespace(
        provider="api",
        model="databricks-job",
        content=assignment_text,
    )

    judge_result = result_payload.get("result_payload", {}).get("judge_result") if isinstance(result_payload.get("result_payload"), dict) else None
    if not isinstance(judge_result, dict):
        judge_result = {}

    workflow = SimpleNamespace(
        record={"job_id": job_id},
        cleaned_text=job_text,
        parsed_obj=parsed_data,
        parsed_dict=parsed_data,
        parsing_source=parsing_source,
        retrieved_examples=retrieved_examples,
        prompt=(result_payload.get("result_payload", {}).get("prompt") if isinstance(result_payload.get("result_payload"), dict) else "") or "",
        result=result_obj,
        judge_result=SimpleNamespace(raw_response=judge_result, overall_score=(judge_result or {}).get("overall_score")) if judge_result else None,
        judge_error=result_payload.get("result_payload", {}).get("judge_error") if isinstance(result_payload.get("result_payload"), dict) else None,
        kpis=result_payload.get("kpis") or {},
    )

    return {
        "workflow": workflow,
        "record": {"job_id": job_id},
        "cleaned_text": job_text,
        "parsed_obj": parsed_data,
        "parsed_dict": parsed_data,
        "parsing_source": parsing_source,
        "retrieved_examples": retrieved_examples,
        "prompt": workflow.prompt,
        "result": result_obj,
        "judge_result": workflow.judge_result,
        "judge_error": workflow.judge_error,
        "kpis": result_payload.get("kpis") or {},
        "show_retrieval_debug": show_retrieval_debug,
        "use_retrieval": use_retrieval,
        "top_k": top_k,
        "domain_override": domain_override,
        "assignment_hours": assignment_hours,
        "difficulty": difficulty,
        "focus_area": focus_area,
        "job_id": job_id,
        "assignment_id": result_payload.get("assignment_id"),
        "version": result_payload.get("version"),
        "result_payload": result_payload,
        "status_payload": status_payload,
    }


def render_setting_pills(
    *,
    duration: str,
    difficulty: str,
    focus_area: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
) -> None:
    pills = [
        f"Duration: {duration}",
        f"Difficulty: {difficulty}",
        f"Focus: {focus_area or 'not set'}",
        f"Retrieval: {'on' if use_retrieval else 'off'}",
    ]
    if use_retrieval:
        pills.append(f"Top K: {top_k}")
        pills.append(f"Domain: {domain_override}")

    html = "".join([f"<span class='pill'>{p}</span>" for p in pills])
    st.markdown(html, unsafe_allow_html=True)


def run_generation(
    *,
    job_text: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
    assignment_hours: str,
    difficulty: str,
    focus_area: str,
    regenerate: bool = False,
    previous_assignment: str | None = None,
    feedback_reason: str | None = None,
) -> dict[str, Any]:
    if _api_mode_enabled():
        api_output = _run_generation_via_api(
            job_text=job_text,
            use_retrieval=use_retrieval,
            top_k=top_k,
            domain_override=domain_override,
            show_retrieval_debug=show_retrieval_debug,
            assignment_hours=assignment_hours,
            difficulty=difficulty,
            focus_area=focus_area,
        )
        api_output["execution_mode"] = "api"
        return api_output

    workflow = run_assignment_workflow(
        job_text=job_text,
        use_retrieval=use_retrieval,
        top_k=top_k,
        domain_override=domain_override,
        assignment_hours=assignment_hours,
        difficulty=difficulty,
        focus_area=focus_area,
        regenerate=regenerate,
        previous_assignment=previous_assignment,
        feedback_reason=feedback_reason,
    )

    return {
        "execution_mode": "local",
        "workflow": workflow,
        "record": workflow.record,
        "cleaned_text": workflow.cleaned_text,
        "parsed_obj": workflow.parsed_obj,
        "parsed_dict": workflow.parsed_dict,
        "parsing_source": workflow.parsing_source,
        "retrieved_examples": workflow.retrieved_examples,
        "prompt": workflow.prompt,
        "result": workflow.result,
        "judge_result": workflow.judge_result,
        "judge_error": workflow.judge_error,
        "kpis": workflow.kpis,
        "show_retrieval_debug": show_retrieval_debug,
        "use_retrieval": use_retrieval,
        "top_k": top_k,
        "domain_override": domain_override,
        "assignment_hours": assignment_hours,
        "difficulty": difficulty,
        "focus_area": focus_area,
    }


def render_results_section(
    *,
    settings: Any,
    assignment_hours: str,
    difficulty: str,
    focus_area: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
) -> None:
    if not st.session_state.assignment_text:
        return

    st.markdown("<div class='section-title'>2. Results Dashboard</div>", unsafe_allow_html=True)
    st.caption("Review outputs, compare versions, and inspect KPI trends.")
    st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)

    version_labels = [f"Version {item['version']}" for item in st.session_state.version_history]
    selected_label = st.selectbox(
        "Active version",
        version_labels,
        index=len(version_labels) - 1,
        key="active_version_selector",
    )
    selected_item = get_selected_version_item(st.session_state.version_history, selected_label)
    selected_version_number = selected_item["version"]
    _sync_selected_version_state(selected_item)

    tab_assignment, tab_compare, tab_analytics, tab_reviewer, tab_candidate = st.tabs(
        [
            "📄 Generated Assignment",
            "⚖️ Compare Versions",
            "📊 Analytics",
            "📝 Human Review",
            "🧑 Candidate Feedback",
        ]
    )

    def _render_assignment_tab() -> None:
        left, right = st.columns([2.2, 1])

        with left:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='section-title'>Assignment Output — Version {selected_version_number}</div>",
                unsafe_allow_html=True,
            )

            st.text_area(
                "Assignment Output",
                value=selected_item["text"],
                height=500,
                key=f"assignment_output_display_v{selected_version_number}",
            )

            download_name = f"assignment_v{selected_version_number}.md"
            st.download_button(
                "📥 Download Assignment",
                data=selected_item["text"],
                file_name=download_name,
                mime="text/markdown",
            )

            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Version Summary</div>", unsafe_allow_html=True)

            st.write(f"**Selected version:** {selected_version_number}")
            st.write(f"**Total versions:** {len(st.session_state.version_history)}")
            st.write(f"**Parsing source:** {st.session_state.parsing_source or 'unknown'}")
            st.write(f"**Retrieved examples:** {len(selected_item.get('retrieved_examples', []))}")

            judge_error = selected_item.get("judge_error")
            if judge_error:
                st.warning(f"Judge error: {judge_error}")

            st.markdown("</div>", unsafe_allow_html=True)

    def _render_compare_tab() -> None:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Side-by-Side Version Comparison</div>", unsafe_allow_html=True)

        if len(st.session_state.version_history) >= 2:
            compare_col1, compare_col2 = st.columns(2)

            with compare_col1:
                left_label = st.selectbox(
                    "Left version",
                    version_labels,
                    index=max(0, len(version_labels) - 2),
                    key="left_compare_version",
                )
                left_item = get_selected_version_item(st.session_state.version_history, left_label)
                st.text_area(
                    f"Left: {left_label}",
                    value=left_item["text"],
                    height=420,
                    key=f"left_text_v{left_item['version']}",
                )

            with compare_col2:
                right_label = st.selectbox(
                    "Right version",
                    version_labels,
                    index=len(version_labels) - 1,
                    key="right_compare_version",
                )
                right_item = get_selected_version_item(st.session_state.version_history, right_label)
                st.text_area(
                    f"Right: {right_label}",
                    value=right_item["text"],
                    height=420,
                    key=f"right_text_v{right_item['version']}",
                )
        else:
            st.info("Generate at least two versions to compare them side by side.")

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_analytics_tab() -> None:
        ana_left, ana_right = st.columns([1.3, 1])

        with ana_left:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Current KPIs</div>", unsafe_allow_html=True)
            st.caption(f"Evaluation model: {_format_provider_label(settings.judge_provider)} · {settings.judge_model}")
            render_kpis_dashboard(selected_item.get("kpis"))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>KPI Trend</div>", unsafe_allow_html=True)
            render_kpi_trend_charts(st.session_state.version_history)
            st.markdown("</div>", unsafe_allow_html=True)

        with ana_right:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Parsed Job Details</div>", unsafe_allow_html=True)

            if st.session_state.parsed_data:
                if st.session_state.parsing_source:
                    st.caption(f"Parsing source: {st.session_state.parsing_source}")
                render_parsed_job_human(st.session_state.parsed_data)
            else:
                st.info("Parsed data not available yet.")

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Retrieved Examples</div>", unsafe_allow_html=True)

            selected_retrieved_examples = selected_item.get("retrieved_examples", [])
            selected_show_retrieval_debug = selected_item.get(
                "show_retrieval_debug",
                settings.show_retrieval_debug_default,
            )

            if selected_retrieved_examples:
                if selected_show_retrieval_debug:
                    render_retrieval_debug(selected_retrieved_examples)
                render_retrieved_examples(selected_retrieved_examples)
            else:
                st.info("No retrieved examples were used for this version.")

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Bronze Event Inspector</div>", unsafe_allow_html=True)
            render_bronze_event_viewer(st.session_state.job_id)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Silver Snapshot Inspector</div>", unsafe_allow_html=True)
            render_silver_snapshot_viewer(st.session_state.job_id)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>Gold Summary Inspector</div>", unsafe_allow_html=True)
            render_gold_summary_viewer(st.session_state.job_id)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_assignment:
        _render_assignment_tab()

    with tab_compare:
        _render_compare_tab()

    with tab_analytics:
        _render_analytics_tab()

    with tab_reviewer:
        render_human_review_tab(
            settings=settings,
            selected_item=selected_item,
            assignment_hours=assignment_hours,
            difficulty=difficulty,
            focus_area=focus_area,
            use_retrieval=use_retrieval,
            top_k=top_k,
            domain_override=domain_override,
            show_retrieval_debug=show_retrieval_debug,
        )

    with tab_candidate:
        render_candidate_feedback_tab(settings=settings)


def render_human_review_tab(
    *,
    settings: Any,
    selected_item: dict[str, Any],
    assignment_hours: str,
    difficulty: str,
    focus_area: str,
    use_retrieval: bool,
    top_k: int,
    domain_override: str,
    show_retrieval_debug: bool,
) -> None:
    st.markdown("<div class='section-title'>3. Human Review</div>", unsafe_allow_html=True)
    st.caption("Internal workflow: score the assignment, capture review notes, and decide whether to regenerate.")
    st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)

    review_col1, review_col2 = st.columns(2)

    # -------------------------
    # Internal Review
    # -------------------------
    with review_col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Review Inputs</div>", unsafe_allow_html=True)

        feedback = st.selectbox(
            "Review Feedback",
            list(settings.review_feedback_options),
            key="review_feedback_type",
        )
        rating = st.slider(
            "Reviewer rating",
            min_value=settings.feedback_rating_min,
            max_value=settings.feedback_rating_max,
            value=settings.default_reviewer_rating,
            step=1,
            key="review_feedback_rating",
            help=settings.reviewer_rating_help,
        )
        st.caption("Review feedback controls regeneration; rating is stored as the human-review KPI.")
        reason = st.selectbox(
            "Review Reason",
            list(settings.review_reason_options),
            key="review_feedback_reason",
        )
        reviewer = st.text_input(
            "Reviewer Name",
            value=settings.default_reviewer_name,
            key="review_feedback_reviewer",
        )

        with st.expander("Regeneration Options", expanded=False):
            feedback_use_retrieval = st.checkbox(
                "Use Retrieved Examples (Few-Shot)",
                value=selected_item.get("use_retrieval", use_retrieval),
                key="feedback_use_retrieval",
            )

            feedback_top_k = selected_item.get("top_k", top_k)
            feedback_domain_override = selected_item.get("domain_override", domain_override)
            feedback_show_retrieval_debug = selected_item.get("show_retrieval_debug", show_retrieval_debug)

            if feedback_use_retrieval:
                feedback_top_k = st.slider(
                    "Number of retrieved examples",
                    min_value=settings.retrieval_top_k_min,
                    max_value=settings.retrieval_top_k_max,
                    value=selected_item.get("top_k", top_k),
                    key="feedback_top_k",
                )

                options = list(settings.retrieval_domain_options)
                current_domain = selected_item.get("domain_override", domain_override)
                if current_domain not in options:
                    current_domain = "auto"

                feedback_domain_override = st.selectbox(
                    "Optional Domain Override",
                    options=options,
                    index=options.index(current_domain),
                    key="feedback_domain_override",
                )

                feedback_show_retrieval_debug = st.checkbox(
                    "Show Retrieval Debug Information",
                    value=selected_item.get("show_retrieval_debug", show_retrieval_debug),
                    key="feedback_show_retrieval_debug",
                )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Save Review", key="save_feedback_btn"):
                try:
                    save_reviewer_feedback(
                        job_id=st.session_state.job_id,
                        assignment_id=selected_item.get("assignment_id") or st.session_state.assignment_id,
                        feedback=feedback,
                        reason=reason,
                        reviewer=reviewer.strip() or "default_user",
                        rating=float(rating),
                    )
                    _apply_feedback_to_current_version(feedback)
                    st.success("Review saved.")
                    st.rerun()
                except Exception as exc:
                    st.exception(exc)

        with c2:
            if st.button("Save and Regenerate", key="save_feedback_regenerate_btn"):
                try:
                    save_reviewer_feedback(
                        job_id=st.session_state.job_id,
                        assignment_id=selected_item.get("assignment_id") or st.session_state.assignment_id,
                        feedback=feedback,
                        reason=reason,
                        reviewer=reviewer.strip() or "default_user",
                        rating=float(rating),
                    )
                    _apply_feedback_to_current_version(feedback)

                    if feedback != "negative":
                        st.info("New versions are usually generated for negative feedback only.")
                    else:
                        with st.spinner("Generating a new version from feedback..."):
                            regen = regenerate_assignment_from_feedback(
                                job_id=st.session_state.job_id,
                                cleaned_text=st.session_state.cleaned_text,
                                current_version=st.session_state.version,
                                assignment_hours=assignment_hours,
                                difficulty=difficulty,
                                focus_area=focus_area,
                                use_retrieval=feedback_use_retrieval,
                                top_k=feedback_top_k,
                                domain_override=feedback_domain_override,
                                show_retrieval_debug=feedback_show_retrieval_debug,
                                previous_assignment=st.session_state.assignment_text,
                                feedback_reason=reason,
                            )

                            workflow = regen.workflow
                            st.session_state.assignment_id = regen.assignment_id
                            st.session_state.assignment_text = workflow.result.content
                            st.session_state.parsed_data = workflow.parsed_dict
                            st.session_state.version = regen.version
                            st.session_state.retrieved_examples = workflow.retrieved_examples
                            st.session_state.parsing_source = workflow.parsing_source
                            st.session_state.kpis = workflow.kpis
                            st.session_state.version_history.append(
                                {
                                    "version": regen.version,
                                    "assignment_id": regen.assignment_id,
                                    "text": workflow.result.content,
                                    "retrieved_examples": workflow.retrieved_examples,
                                    "kpis": workflow.kpis,
                                    "use_retrieval": feedback_use_retrieval,
                                    "top_k": feedback_top_k,
                                    "domain_override": feedback_domain_override,
                                    "show_retrieval_debug": feedback_show_retrieval_debug,
                                    "judge_result": workflow.judge_result.raw_response if workflow.judge_result else None,
                                    "judge_error": workflow.judge_error,
                                    "target_duration": assignment_hours,
                                    "difficulty": difficulty,
                                    "focus_area": focus_area,
                                }
                            )

                            st.success("Review saved and a new assignment version was generated.")
                            st.rerun()

                except Exception as exc:
                    st.exception(exc)

        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # Final decision
    # -------------------------
    with review_col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Final Decision</div>", unsafe_allow_html=True)

        if st.session_state.version_history:
            decision_version_labels = [
                f"Version {item['version']}" for item in st.session_state.version_history
            ]

            selected_final_label = st.selectbox(
                "Select final version",
                decision_version_labels,
                index=len(decision_version_labels) - 1,
                key="final_version_selector",
            )

            selected_final_item = get_selected_version_item(
                st.session_state.version_history,
                selected_final_label,
            )
            selected_final_version = selected_final_item["version"]

            final_decision = st.selectbox(
                "Decision",
                list(settings.final_decision_options),
                key="final_decision_status",
            )

            final_reviewer = st.text_input(
                "Reviewer Name",
                value=settings.default_reviewer_name,
                key="final_reviewer_name",
            )

            final_notes = st.text_area(
                "Final Notes",
                placeholder="Optional notes about why this version was chosen...",
                key="final_review_notes",
                height=140,
            )

            if st.button("Save Decision", key="save_final_review_btn"):
                try:
                    save_final_review_decision(
                        job_id=st.session_state.job_id,
                        selected_assignment_id=selected_final_item["assignment_id"],
                        selected_version=selected_final_version,
                        decision=final_decision,
                        reviewer=final_reviewer.strip() or "default_user",
                        notes=final_notes.strip(),
                    )
                    st.success("Decision saved.")
                except Exception as exc:
                    st.exception(exc)

        st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------
    # Candidate feedback
    # -------------------------
    return


def render_candidate_feedback_tab(*, settings: Any) -> None:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>4. Candidate Survey</div>", unsafe_allow_html=True)
    st.caption("External workflow: record how the candidate experienced the assignment.")
    st.markdown("<div class='divider-space'></div>", unsafe_allow_html=True)

    cand_col1, cand_col2 = st.columns(2)

    with cand_col1:
        candidate_name = st.text_input("Candidate Name", key="candidate_name")
        candidate_overall_score = st.slider(
            "Overall",
            settings.candidate_score_min,
            settings.candidate_score_max,
            settings.candidate_score_default,
            key="candidate_overall_score",
        )
        candidate_clarity_score = st.slider(
            "Clarity",
            settings.candidate_score_min,
            settings.candidate_score_max,
            settings.candidate_score_default,
            key="candidate_clarity_score",
        )
        candidate_difficulty_score = st.slider(
            "Difficulty",
            settings.candidate_score_min,
            settings.candidate_score_max,
            settings.candidate_score_default,
            key="candidate_difficulty_score",
        )

    with cand_col2:
        candidate_relevance_score = st.slider(
            "Relevance",
            settings.candidate_score_min,
            settings.candidate_score_max,
            settings.candidate_score_default,
            key="candidate_relevance_score",
        )
        candidate_time_reasonable = st.selectbox(
            "Expected Time Reasonable?",
            list(settings.candidate_time_reasonable_options),
            key="candidate_time_reasonable",
        )
        candidate_comments = st.text_area(
            "Candidate Notes",
            key="candidate_comments",
            height=120,
        )

    if st.button("Save Candidate Survey", key="save_candidate_feedback_btn"):
        try:
            save_candidate_feedback_entry(
                job_id=st.session_state.job_id,
                assignment_id=st.session_state.assignment_id,
                candidate_name=candidate_name.strip() or "anonymous",
                overall_score=candidate_overall_score,
                clarity_score=candidate_clarity_score,
                difficulty_score=candidate_difficulty_score,
                relevance_score=candidate_relevance_score,
                time_reasonable=candidate_time_reasonable,
                comments=candidate_comments.strip(),
            )
            st.success("Candidate survey saved.")
        except Exception as exc:
            st.exception(exc)

    candidate_rows = load_candidate_feedback(st.session_state.job_id) if st.session_state.job_id else []
    if candidate_rows:
        with st.expander(f"Saved Candidate Responses: {len(candidate_rows)}", expanded=False):
            st.write(candidate_rows[-1])

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Init session
# =========================================================
init_session_defaults()


# =========================================================
# Sidebar
# =========================================================
sidebar_state = render_sidebar_controls(settings)
duration_display = sidebar_state["duration_display"]
assignment_hours = sidebar_state["assignment_hours"]
difficulty = sidebar_state["difficulty"]
focus_area = sidebar_state["focus_area"]
use_retrieval = sidebar_state["use_retrieval"]
top_k = sidebar_state["top_k"]
domain_override = sidebar_state["domain_override"]
show_retrieval_debug = sidebar_state["show_retrieval_debug"]


# =========================================================
# Header
# =========================================================
render_app_header(settings)

render_setting_pills(
    duration=assignment_hours,
    difficulty=difficulty,
    focus_area=focus_area,
    use_retrieval=use_retrieval,
    top_k=top_k,
    domain_override=domain_override,
)


# =========================================================
# Input section
# =========================================================
job_text_input, generate_clicked = render_job_input_section(settings)


# =========================================================
# Main generation
# =========================================================
if generate_clicked:
    if not job_text_input.strip():
        st.error("Please paste a job advertisement first.")
    else:
        try:
            with st.spinner("Analyzing the job ad and generating the assignment..."):
                reset_current_session()

                output = run_generation(
                    job_text=job_text_input,
                    use_retrieval=use_retrieval,
                    top_k=top_k,
                    domain_override=domain_override,
                    show_retrieval_debug=show_retrieval_debug,
                    assignment_hours=assignment_hours,
                    difficulty=difficulty,
                    focus_area=focus_area,
                    regenerate=False,
                )

                record = output["record"]
                result = output["result"]
                parsed_dict = output["parsed_dict"]
                parsing_source = output["parsing_source"]
                retrieved_examples = output["retrieved_examples"]
                kpis = output["kpis"]
                judge_result = output["judge_result"]
                judge_error = output["judge_error"]
                workflow = output["workflow"]
                execution_mode = str(output.get("execution_mode") or "local").strip().lower()
                assignment_id = str(output.get("assignment_id") or "").strip() or str(uuid.uuid4())
                version = int(output.get("version") or 1)

                if execution_mode != "api":
                    persist_assignment_version(
                        job_id=record["job_id"],
                        assignment_id=assignment_id,
                        workflow=workflow,
                        version=1,
                        target_duration=assignment_hours,
                        difficulty=difficulty,
                        focus_area=focus_area,
                        use_retrieval=use_retrieval,
                        top_k=top_k,
                        domain_override=domain_override,
                        show_retrieval_debug=show_retrieval_debug,
                    )

                st.session_state.job_id = record["job_id"]
                st.session_state.assignment_id = assignment_id
                st.session_state.assignment_text = result.content
                st.session_state.parsed_data = parsed_dict
                st.session_state.cleaned_text = output["cleaned_text"]
                st.session_state.version = version
                st.session_state.retrieved_examples = retrieved_examples
                st.session_state.parsing_source = parsing_source
                st.session_state.kpis = kpis
                st.session_state.version_history = [
                    {
                        "version": version,
                        "assignment_id": assignment_id,
                        "text": result.content,
                        "retrieved_examples": retrieved_examples,
                        "kpis": kpis,
                        "use_retrieval": use_retrieval,
                        "top_k": top_k,
                        "domain_override": domain_override,
                        "show_retrieval_debug": show_retrieval_debug,
                        "judge_result": judge_result.raw_response if judge_result else None,
                        "judge_error": judge_error,
                        "target_duration": assignment_hours,
                        "difficulty": difficulty,
                        "focus_area": focus_area,
                    }
                ]

                if parsing_source == "llm":
                    st.success("Assignment generated and saved successfully.")
                elif settings.use_llm_job_parser:
                    st.warning("LLM parsing failed, so the fallback parser was used.")
                else:
                    st.info("Rule-based parser was used for this version.")

        except RuntimeError as exc:
            message = str(exc).strip()
            if "Databricks" in message or "API request failed" in message:
                st.error(message or "Databricks trigger failed.")
            else:
                st.exception(exc)
        except Exception as exc:
            st.exception(exc)

st.markdown("<div class='page-section-gap'></div>", unsafe_allow_html=True)


# =========================================================
# Results section
# =========================================================
render_results_section(
    settings=settings,
    assignment_hours=assignment_hours,
    difficulty=difficulty,
    focus_area=focus_area,
    use_retrieval=use_retrieval,
    top_k=top_k,
    domain_override=domain_override,
    show_retrieval_debug=show_retrieval_debug,
)
