from __future__ import annotations

from src.retrieval.routing import (
    extract_tech_keywords,
    extract_titles,
    tokenize,
)


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_lexical_overlap_score(query_text: str, candidate_text: str) -> float:
    query_tokens = set(tokenize(query_text))
    candidate_tokens = set(tokenize(candidate_text))

    if not query_tokens or not candidate_tokens:
        return 0.0

    overlap = len(query_tokens & candidate_tokens)
    return min(safe_divide(overlap, len(query_tokens)), 1.0)


def compute_keyword_overlap_score(
    query_keywords: set[str],
    candidate_keywords: set[str],
) -> float:
    if not query_keywords or not candidate_keywords:
        return 0.0

    overlap = len(query_keywords & candidate_keywords)
    return safe_divide(overlap, len(query_keywords))


def compute_title_overlap_score(
    query_titles: set[str],
    candidate_titles: set[str],
) -> float:
    if not query_titles or not candidate_titles:
        return 0.0

    overlap = len(query_titles & candidate_titles)
    return safe_divide(overlap, len(query_titles))


def compute_rerank_adjustments(
    pair,
    query_text: str,
    selected_domains: list[str] | None,
    query_seniority: str,
    query_titles: set[str],
    query_keywords: set[str],
) -> tuple[float, list[str]]:
    score_adjustment = 0.0
    reasons: list[str] = []

    pair_domain = getattr(pair, "domain", "") or ""
    pair_subdomain = getattr(pair, "subdomain", "") or ""
    pair_seniority = getattr(pair, "seniority", "") or ""
    pair_job_text = getattr(pair, "job_ad_text", "") or ""
    pair_assignment_text = getattr(pair, "assignment_text", "") or ""

    candidate_text = f"{pair_job_text}\n{pair_assignment_text}"
    candidate_titles = extract_titles(candidate_text)
    candidate_keywords = extract_tech_keywords(candidate_text)

    if selected_domains:
        if pair_subdomain in selected_domains:
            score_adjustment += 0.18
            reasons.append("same routed subdomain")
        elif pair_domain in selected_domains:
            score_adjustment += 0.10
            reasons.append("same routed domain")

    if query_seniority != "unknown":
        if pair_seniority == query_seniority:
            score_adjustment += 0.10
            reasons.append("same seniority")
        elif pair_seniority and pair_seniority != query_seniority:
            score_adjustment -= 0.04
            reasons.append("different seniority")

    title_overlap = compute_title_overlap_score(query_titles, candidate_titles)
    if title_overlap > 0:
        score_adjustment += min(0.08, 0.08 * title_overlap)
        reasons.append("similar job title")

    keyword_overlap = compute_keyword_overlap_score(query_keywords, candidate_keywords)
    if keyword_overlap > 0:
        score_adjustment += min(0.15, 0.15 * keyword_overlap)
        reasons.append("matching tools/skills")

    lexical_overlap = compute_lexical_overlap_score(query_text, candidate_text)
    if lexical_overlap > 0:
        score_adjustment += min(0.06, 0.06 * lexical_overlap)
        reasons.append("lexical overlap")

    return score_adjustment, reasons