from __future__ import annotations

import re
from collections import defaultdict


DOMAIN_PATTERNS = {
    "frontend": [
        (r"\bfrontend\b", 3),
        (r"\bfront[- ]end\b", 3),
        (r"\breact\b", 3),
        (r"\bjavascript\b", 2),
        (r"\btypescript\b", 2),
        (r"\bvue\b", 3),
        (r"\bangular\b", 3),
        (r"\bcss\b", 2),
        (r"\bhtml\b", 2),
        (r"\bnext\.?js\b", 3),
    ],
    "backend": [
        (r"\bbackend\b", 3),
        (r"\bback[- ]end\b", 3),
        (r"\bapi\b", 2),
        (r"\bserver[- ]side\b", 2),
        (r"\bdjango\b", 3),
        (r"\bflask\b", 3),
        (r"\bfastapi\b", 3),
        (r"\bnode\.?js\b", 2),
        (r"\bspring\b", 3),
        (r"\bjava\b", 2),
        (r"\bgo\b", 2),
        (r"\bmicroservices?\b", 2),
    ],
    "mobile": [
        (r"\bmobile\b", 3),
        (r"\bandroid\b", 3),
        (r"\bios\b", 3),
        (r"\breact native\b", 3),
        (r"\bflutter\b", 3),
        (r"\bkotlin\b", 2),
        (r"\bswift\b", 2),
    ],
    "data": [
        (r"\bdata engineer(?:ing)?\b", 3),
        (r"\bdata science\b", 3),
        (r"\bmachine learning\b", 3),
        (r"\bml\b", 1),
        (r"\bai\b", 1),
        (r"\bpandas\b", 2),
        (r"\bnumpy\b", 2),
        (r"\bscikit[- ]learn\b", 3),
        (r"\bpyspark\b", 3),
        (r"\bairflow\b", 3),
        (r"\betl\b", 2),
        (r"\bpipeline[s]?\b", 2),
        (r"\bdatabricks\b", 3),
        (r"\bsql\b", 2),
    ],
    "devops": [
        (r"\bdevops\b", 3),
        (r"\bkubernetes\b", 3),
        (r"\bdocker\b", 3),
        (r"\bterraform\b", 3),
        (r"\bcicd\b", 2),
        (r"\bci/cd\b", 2),
        (r"\baws\b", 2),
        (r"\bazure\b", 2),
        (r"\bgcp\b", 2),
        (r"\bhelm\b", 2),
    ],
}


SENIORITY_PATTERNS = {
    "intern": [r"\bintern\b", r"\btrainee\b", r"\binternship\b"],
    "junior": [r"\bjunior\b", r"\bentry[- ]level\b"],
    "mid": [r"\bmid[- ]level\b", r"\bassociate\b"],
    "senior": [r"\bsenior\b", r"\blead\b", r"\bprincipal\b", r"\bstaff\b"],
}


TITLE_PATTERNS = {
    "frontend engineer": [
        r"\bfrontend engineer\b",
        r"\bfront[- ]end engineer\b",
        r"\bui engineer\b",
        r"\bfrontend developer\b",
    ],
    "backend engineer": [
        r"\bbackend engineer\b",
        r"\bback[- ]end engineer\b",
        r"\bbackend developer\b",
        r"\bserver[- ]side engineer\b",
    ],
    "full stack engineer": [
        r"\bfull[- ]stack engineer\b",
        r"\bfull[- ]stack developer\b",
        r"\bfullstack engineer\b",
        r"\bfullstack developer\b",
    ],
    "mobile engineer": [
        r"\bmobile engineer\b",
        r"\bandroid developer\b",
        r"\bios developer\b",
        r"\bmobile developer\b",
    ],
    "data engineer": [
        r"\bdata engineer\b",
        r"\banalytics engineer\b",
    ],
    "data scientist": [
        r"\bdata scientist\b",
        r"\bmachine learning scientist\b",
    ],
    "ml engineer": [
        r"\bmachine learning engineer\b",
        r"\bml engineer\b",
        r"\bai engineer\b",
    ],
    "devops engineer": [
        r"\bdevops engineer\b",
        r"\bsite reliability engineer\b",
        r"\bsre\b",
        r"\bplatform engineer\b",
    ],
}


TECH_KEYWORDS = {
    "react", "javascript", "typescript", "vue", "angular", "css", "html", "nextjs",
    "python", "java", "go", "nodejs", "fastapi", "flask", "django", "spring",
    "kotlin", "swift", "flutter", "react native",
    "pandas", "numpy", "scikit-learn", "pyspark", "spark", "airflow", "sql", "etl",
    "docker", "kubernetes", "terraform", "aws", "azure", "gcp", "helm",
    "microservices", "rest", "api", "graphql", "databricks", "mlflow"
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("node.js", "nodejs")
    text = text.replace("next.js", "nextjs")
    text = text.replace("ci/cd", "cicd")
    return text


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.\-]{1,}", normalized)


def extract_matching_labels(text: str, pattern_map: dict[str, list[str]]) -> set[str]:
    labels: set[str] = set()
    for label, patterns in pattern_map.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                labels.add(label)
                break
    return labels


def score_query_domains(text: str) -> dict[str, int]:
    scores: dict[str, int] = defaultdict(int)

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern, weight in patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                scores[domain] += weight * len(matches)

    return dict(scores)


def select_search_domains(domain_scores: dict[str, int]) -> tuple[list[str] | None, str]:
    if not domain_scores:
        return None, "full"

    ranked = sorted(domain_scores.items(), key=lambda item: item[1], reverse=True)
    top_domain, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    if top_score >= 4 and (top_score - second_score) >= 2:
        return [top_domain], "single"

    if len(ranked) > 1 and top_score >= 3 and second_score >= 2:
        return [top_domain, ranked[1][0]], "double"

    return None, "full"


def infer_query_seniority(text: str) -> str:
    for seniority, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return seniority
    return "unknown"


def extract_titles(text: str) -> set[str]:
    return extract_matching_labels(text, TITLE_PATTERNS)


def extract_tech_keywords(text: str) -> set[str]:
    normalized = normalize_text(text)
    found: set[str] = set()

    for keyword in TECH_KEYWORDS:
        pattern = rf"\b{re.escape(keyword)}\b"
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            found.add(keyword)

    return found