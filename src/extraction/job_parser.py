"""
Job Advertisement Parser Module
-------------------------------
This module extracts structured features from raw job descriptions.
It identifies job titles, seniority levels, industry domains, and
categorizes skills/tools using regex pattern matching.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field


@dataclass
class JobAdFeatures:
    """Data structure to hold extracted job information."""
    job_title: str = "Unknown Role"
    seniority: str = "Not specified"
    domain: str = "General"
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Converts the dataclass instance to a standard dictionary."""
        return asdict(self)


# Mapping of skills to regex patterns for robust matching
SKILL_KEYWORDS = {
    "Python": [r"\bpython\b"],
    "SQL": [r"\bsql\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Deep Learning": [r"\bdeep learning\b"],
    "Data Analysis": [r"\bdata analysis\b", r"\banalytics\b"],
    "Statistics": [r"\bstatistics\b", r"\bstatistical\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "Computer Vision": [r"\bcomputer vision\b"],
    "Spark": [r"\bspark\b", r"\bpyspark\b"],
    "Databricks": [r"\bdatabricks\b"],
    "Pandas": [r"\bpandas\b"],
    "Scikit-learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "PyTorch": [r"\bpytorch\b"],
    "Docker": [r"\bdocker\b"],
    "Git": [r"\bgit\b"],
    "Azure": [r"\bazure\b"],
    "GCP": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
}

# Industry domains keywords
DOMAIN_KEYWORDS = {
    "Manufacturing": [r"\bmanufacturing\b", r"\bindustrial\b"],
    "Healthcare": [r"\bhealthcare\b", r"\bmedical\b", r"\bpharma\b"],
    "Finance": [r"\bfinance\b", r"\bbanking\b", r"\binsurance\b"],
    "Retail": [r"\bretail\b", r"\be-commerce\b", r"\becommerce\b"],
    "Education": [r"\beducation\b", r"\blearning\b"],
    "Technology": [r"\bsoftware\b", r"\bsaas\b", r"\btechnology\b"],
}

# Patterns to identify where the job title is explicitly mentioned
TITLE_PATTERNS = [
    r"job title\s*:\s*(.+)",
    r"position\s*:\s*(.+)",
    r"role\s*:\s*(.+)",
]

# Experience level mapping
SENIORITY_PATTERNS = {
    "Intern": [r"\bintern\b", r"\btrainee\b"],
    "Junior": [r"\bjunior\b", r"\bentry[- ]level\b"],
    "Mid-level": [r"\bmid[- ]level\b", r"\bassociate\b"],
    "Senior": [r"\bsenior\b", r"\blead\b", r"\bprincipal\b"],
}

# Common job roles to help identify titles in messy text
ROLE_HINTS = [
    "data scientist",
    "data analyst",
    "machine learning engineer",
    "ml engineer",
    "ai engineer",
    "software engineer",
    "backend engineer",
    "frontend engineer",
    "full stack engineer",
    "data engineer",
    "research scientist",
    "research engineer",
    "product manager",
    "business analyst",
]

# Phrases that often start a sentence but are NOT job titles
BAD_TITLE_STARTS = (
    "we are",
    "you will",
    "experience with",
    "responsibilities",
    "requirements",
    "preferred",
    "about the role",
    "apply now",
)


def _normalize_line(line: str) -> str:
    """Cleans up extra spaces and common symbols from a single line."""
    return re.sub(r"\s+", " ", line).strip(" :-•\t")


def _extract_title(text: str) -> str:
    """
    Attempts to find the job title by searching for patterns
    or analyzing the top lines of the description.
    """
    # 1. Look for explicit "Job Title: ..." markers
    for pattern in TITLE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _normalize_line(match.group(1))

    lines = [_normalize_line(line) for line in text.splitlines() if _normalize_line(line)]

    # 2. Look for known role names in the first 12 lines
    for line in lines[:12]:
        lower_line = line.lower()
        if any(role in lower_line for role in ROLE_HINTS):
            return line

    # 3. Heuristic: Find the first clean, short line that doesn't start with 'bad' words
    for line in lines[:8]:
        lower_line = line.lower()

        if lower_line.startswith(BAD_TITLE_STARTS):
            continue

        if len(line.split()) < 2 or len(line.split()) > 8:
            continue

        if any(word in lower_line for word in ["experience", "responsibilities", "requirements", "skills", "plus"]):
            continue

        return line

    return "Unknown Role"


def _extract_seniority(text: str) -> str:
    """Matches seniority keywords against the text."""
    for label, patterns in SENIORITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return label
    return "Not specified"


def _extract_domain(text: str) -> str:
    """Identifies the industry/domain of the job."""
    for domain, patterns in DOMAIN_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return domain
    return "General"


def _extract_skills(text: str) -> list[str]:
    """Finds all pre-defined skills present in the advertisement."""
    found = []
    for skill, patterns in SKILL_KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(skill)
                break
    return sorted(set(found))


def _split_required_preferred(skills: list[str]) -> tuple[list[str], list[str]]:
    """Heuristic split: first 4 skills are required, others are preferred."""
    if len(skills) <= 4:
        return skills, []

    required = skills[:4]
    preferred = skills[4:]
    return required, preferred


def _extract_tools(skills: list[str]) -> list[str]:
    """Filters a list of skills to only return software tools and platforms."""
    tool_like = {
        "Python", "SQL", "Spark", "Databricks", "Pandas", "Scikit-learn",
        "TensorFlow", "PyTorch", "Docker", "Git", "Azure", "GCP", "AWS"
    }
    return [item for item in skills if item in tool_like]


def parse_job_ad(text: str) -> JobAdFeatures:
    """
    The main entry point: transforms raw text into a JobAdFeatures object.
    """
    title = _extract_title(text)
    seniority = _extract_seniority(text)
    domain = _extract_domain(text)
    skills = _extract_skills(text)
    required_skills, preferred_skills = _split_required_preferred(skills)
    tools = _extract_tools(skills)

    return JobAdFeatures(
        job_title=title,
        seniority=seniority,
        domain=domain,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        tools=tools,
    )