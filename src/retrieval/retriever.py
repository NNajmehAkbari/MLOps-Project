from __future__ import annotations

from src.retrieval.embedding_service import compute_similarity_scores
from src.retrieval.example_pair_store import load_example_pairs
from src.retrieval.routing import (
    extract_tech_keywords,
    extract_titles,
    infer_query_seniority,
    score_query_domains,
    select_search_domains,
)
from src.retrieval.scoring import compute_rerank_adjustments
from src.utils.config import DEFAULT_RETRIEVAL_TOP_K


def _truncate_text(text: str, max_chars: int = 700) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def _normalize_domain_label(value: str | None) -> str:
    value = (value or "").strip().lower()

    mapping = {
        "front-end": "frontend",
        "front end": "frontend",
        "frontend": "frontend",
        "ui": "frontend",

        "back-end": "backend",
        "back end": "backend",
        "backend": "backend",
        "server-side": "backend",
        "server side": "backend",

        "mobile": "mobile",
        "android": "mobile",
        "ios": "mobile",

        "data": "data",
        "data engineering": "data",
        "data engineer": "data",
        "data science": "data",
        "machine learning": "data",
        "ml": "data",
        "ai": "data",
        "analytics": "data",

        "devops": "devops",
        "platform": "devops",
        "sre": "devops",
        "site reliability": "devops",
        "infrastructure": "devops",
    }

    return mapping.get(value, value)


def _filter_examples_by_domains(
    example_pairs,
    selected_domains: list[str] | None,
    strict: bool = False,
):
    if not selected_domains:
        return example_pairs

    normalized_selected = {_normalize_domain_label(domain) for domain in selected_domains}

    filtered = []
    for pair in example_pairs:
        pair_subdomain = _normalize_domain_label(getattr(pair, "subdomain", None))
        pair_domain = _normalize_domain_label(getattr(pair, "domain", None))

        if pair_subdomain in normalized_selected or pair_domain in normalized_selected:
            filtered.append(pair)

    if filtered:
        return filtered

    if strict:
        return []

    return example_pairs


def retrieve_similar_examples(
    query_text: str,
    top_k: int = DEFAULT_RETRIEVAL_TOP_K,
    parsed_llm: dict | None = None,
) -> list[dict]:
    example_pairs = load_example_pairs()
    if not example_pairs:
        return []

    query_text = (query_text or "").strip()
    if not query_text:
        return []

    forced_domain = None
    if parsed_llm:
        forced_domain = _normalize_domain_label(parsed_llm.get("subdomain"))

    if forced_domain:
        selected_domains = [forced_domain]
        route_type = "manual_override"
        domain_scores = {forced_domain: 999}
        strict_domain_filter = True
    else:
        domain_scores = score_query_domains(query_text)
        selected_domains, route_type = select_search_domains(domain_scores)

        if selected_domains:
            selected_domains = [_normalize_domain_label(domain) for domain in selected_domains]

        strict_domain_filter = False

    if parsed_llm and parsed_llm.get("seniority"):
        query_seniority = parsed_llm["seniority"]
    else:
        query_seniority = infer_query_seniority(query_text)

    query_titles = extract_titles(query_text)
    query_keywords = extract_tech_keywords(query_text)

    candidate_pairs = _filter_examples_by_domains(
        example_pairs,
        selected_domains,
        strict=strict_domain_filter,
    )

    if not candidate_pairs:
        return []

    similarities = compute_similarity_scores(query_text, candidate_pairs)

    results: list[dict] = []

    for pair, similarity in zip(candidate_pairs, similarities):
        final_score = float(similarity)
        reasons: list[str] = ["semantic similarity"]

        adjustment, adjustment_reasons = compute_rerank_adjustments(
            pair=pair,
            query_text=query_text,
            selected_domains=selected_domains,
            query_seniority=query_seniority,
            query_titles=query_titles,
            query_keywords=query_keywords,
        )

        final_score += adjustment
        reasons.extend(adjustment_reasons)

        results.append(
            {
                "pair_id": getattr(pair, "pair_id", None),
                "company": getattr(pair, "company", None),
                "domain": getattr(pair, "domain", None),
                "subdomain": getattr(pair, "subdomain", None),
                "seniority": getattr(pair, "seniority", None),
                "year": getattr(pair, "year", None),
                "sequence": getattr(pair, "sequence", None),
                "score": round(final_score, 4),
                "semantic_score": round(float(similarity), 4),
                "reasons": reasons,
                "route_type": route_type,
                "selected_domains": selected_domains or ["all"],
                "domain_scores": domain_scores,
                "job_ad_text": _truncate_text(getattr(pair, "job_ad_text", ""), 500),
                "assignment_text": _truncate_text(getattr(pair, "assignment_text", ""), 900),
                "folder_path": getattr(pair, "folder_path", None),
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]
