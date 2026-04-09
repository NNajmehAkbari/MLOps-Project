from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


def _load_env_file_fallback() -> None:
    """Load key=value pairs from a local .env file without external deps."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip("\"'")
        os.environ[key] = value


if load_dotenv is not None:
    load_dotenv()
else:
    _load_env_file_fallback()


def _read_databricks_secret(scope: str, key: str) -> str:
    scope = (scope or "").strip()
    key = (key or "").strip()
    if not scope or not key:
        return ""

    secret_value = ""
    try:
        from databricks.sdk.runtime import dbutils  # type: ignore

        secret_value = dbutils.secrets.get(scope=scope, key=key)
    except Exception:
        try:
            from pyspark.sql import SparkSession
            from pyspark.dbutils import DBUtils

            spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
            secret_value = DBUtils(spark).secrets.get(scope=scope, key=key)
        except Exception:
            return ""

    return str(secret_value or "").strip()


DEFAULT_DURATION_OPTIONS: tuple[str, ...] = ("1h", "2h", "3h", "4h", "5h+")
DEFAULT_DURATION_LABELS: dict[str, str] = {
    "1h": "1 hour",
    "2h": "2 hours",
    "3h": "3 hours",
    "4h": "4 hours",
    "5h+": "5+ hours",
}
DEFAULT_DIFFICULTY_OPTIONS: tuple[str, ...] = ("easy", "medium", "hard")
DEFAULT_RETRIEVAL_DOMAIN_OPTIONS: tuple[str, ...] = ("auto", "frontend", "backend", "mobile", "data", "devops")
DEFAULT_REVIEW_FEEDBACK_OPTIONS: tuple[str, ...] = ("positive", "negative")
DEFAULT_REVIEW_REASON_OPTIONS: tuple[str, ...] = (
    "good quality",
    "too easy",
    "too hard",
    "not relevant",
    "unclear",
    "generic output",
    "too time-consuming",
    "too brief",
    "high labor intensity",
)
DEFAULT_FINAL_DECISION_OPTIONS: tuple[str, ...] = ("approved", "shortlisted", "rejected")
DEFAULT_DEFAULT_REVIEWER_NAME = "HR1"
DEFAULT_DEFAULT_REVIEW_RATING = 3
DEFAULT_DEFAULT_DURATION = "2h"
DEFAULT_DEFAULT_DIFFICULTY = "medium"
DEFAULT_FEEDBACK_RATING_MIN = 1
DEFAULT_FEEDBACK_RATING_MAX = 5
DEFAULT_CANDIDATE_SCORE_MIN = 1
DEFAULT_CANDIDATE_SCORE_MAX = 5
DEFAULT_CANDIDATE_SCORE_DEFAULT = 3
DEFAULT_CANDIDATE_TIME_REASONABLE_OPTIONS: tuple[str, ...] = ("yes", "no", "not sure")
DEFAULT_JUDGE_PROVIDER = "gemini"
DEFAULT_JUDGE_MODEL = "gemini-2.5-flash"
DEFAULT_USE_LLM_JOB_PARSER = False
DEFAULT_USE_SENTENCE_TRANSFORMERS = False
DEFAULT_STORAGE_BACKEND = "local"
DEFAULT_DATABRICKS_BRONZE_JOB_ADS_TABLE = "bronze_job_ads"
DEFAULT_DATABRICKS_BRONZE_ASSIGNMENT_VERSIONS_TABLE = "bronze_assignment_versions"
DEFAULT_DATABRICKS_BRONZE_REVIEWER_FEEDBACK_TABLE = "bronze_reviewer_feedback"
DEFAULT_DATABRICKS_BRONZE_CANDIDATE_FEEDBACK_TABLE = "bronze_candidate_feedback"
DEFAULT_DATABRICKS_BRONZE_REVIEW_DECISIONS_TABLE = "bronze_review_decisions"
DEFAULT_DATABRICKS_SILVER_PARSED_JOBS_TABLE = "silver_parsed_jobs"
DEFAULT_DATABRICKS_SILVER_ASSIGNMENT_VERSIONS_TABLE = "silver_assignment_versions"
DEFAULT_DATABRICKS_SILVER_REVIEWER_FEEDBACK_TABLE = "silver_reviewer_feedback"
DEFAULT_DATABRICKS_SILVER_CANDIDATE_FEEDBACK_TABLE = "silver_candidate_feedback"
DEFAULT_DATABRICKS_SILVER_REVIEW_DECISIONS_TABLE = "silver_review_decisions"
DEFAULT_DATABRICKS_GOLD_KPI_SUMMARY_TABLE = "gold_kpi_summary"
DEFAULT_DATABRICKS_GOLD_LATEST_ASSIGNMENTS_TABLE = "gold_latest_assignment_versions"
DEFAULT_DATABRICKS_CATALOG = "main"
DEFAULT_DATABRICKS_SCHEMA = "default"
DEFAULT_DATABRICKS_SECRET_SCOPE = ""
DEFAULT_RETRIEVAL_TOP_K = 2
DEFAULT_RETRIEVAL_TOP_K_MIN = 1
DEFAULT_RETRIEVAL_TOP_K_MAX = 5
DEFAULT_SHOW_RETRIEVAL_DEBUG = True
DEFAULT_USE_RETRIEVAL = False
DEFAULT_APP_TITLE = "AI-Based Recruitment Assignment Generator"
DEFAULT_APP_SUBTITLE = (
    "Paste a job advertisement, generate a take-home assignment, compare versions, "
    "and save reviewer or candidate feedback."
)
DEFAULT_JOB_INPUT_PLACEHOLDER = "Paste the full job advertisement here..."
DEFAULT_FOCUS_AREA_PLACEHOLDER = "e.g. backend APIs, ML, analytics"
DEFAULT_REVIEWER_RATING_HELP = "1 = poor, 5 = excellent"
DEFAULT_GENERATION_NOTE = "OpenAI generates the assignment; Gemini evaluates it."


@dataclass
class Settings:
    project_root: Path
    storage_backend: str
    llm_provider: str
    openai_api_key: str
    openai_model: str
    judge_provider: str
    judge_model: str
    judge_api_key: str
    use_llm_job_parser: bool
    use_sentence_transformers: bool
    jobbert_model_name: str
    databricks_server_hostname: str
    databricks_http_path: str
    databricks_token: str
    databricks_bronze_job_ads_table: str
    databricks_bronze_assignment_versions_table: str
    databricks_bronze_reviewer_feedback_table: str
    databricks_bronze_candidate_feedback_table: str
    databricks_bronze_review_decisions_table: str
    databricks_silver_parsed_jobs_table: str
    databricks_silver_assignment_versions_table: str
    databricks_silver_reviewer_feedback_table: str
    databricks_silver_candidate_feedback_table: str
    databricks_silver_review_decisions_table: str
    databricks_gold_kpi_summary_table: str
    databricks_gold_latest_assignments_table: str
    databricks_catalog: str
    databricks_schema: str
    databricks_secret_scope: str
    app_data_dir: Path
    raw_dir: Path
    processed_dir: Path
    feedback_dir: Path
    candidate_feedback_dir: Path
    example_pairs_raw_dir: Path
    reviews_dir: Path
    prompt_file: Path
    duration_options: tuple[str, ...]
    duration_labels: dict[str, str]
    default_duration: str
    difficulty_options: tuple[str, ...]
    default_difficulty: str
    retrieval_domain_options: tuple[str, ...]
    review_feedback_options: tuple[str, ...]
    review_reason_options: tuple[str, ...]
    final_decision_options: tuple[str, ...]
    default_reviewer_name: str
    default_reviewer_rating: int
    candidate_score_min: int
    candidate_score_max: int
    candidate_score_default: int
    candidate_time_reasonable_options: tuple[str, ...]
    feedback_rating_min: int
    feedback_rating_max: int
    retrieval_top_k_default: int
    retrieval_top_k_min: int
    retrieval_top_k_max: int
    show_retrieval_debug_default: bool
    use_retrieval_default: bool
    app_title: str
    app_subtitle: str
    job_input_placeholder: str
    focus_area_placeholder: str
    reviewer_rating_help: str
    generation_note: str

    def ensure_directories(self) -> None:
        if self.storage_backend.strip().lower() == "databricks":
            return

        for directory in [
            self.app_data_dir,
            self.raw_dir,
            self.processed_dir,
            self.feedback_dir,
            self.candidate_feedback_dir,
            self.reviews_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[2]

    app_data_dir = project_root / os.getenv("APP_DATA_DIR", "data")
    raw_dir = project_root / os.getenv("RAW_DIR", "data/raw")
    processed_dir = project_root / os.getenv("PROCESSED_DIR", "data/processed")
    feedback_dir = project_root / os.getenv("FEEDBACK_DIR", "data/feedback")
    candidate_feedback_dir = project_root / os.getenv("CANDIDATE_FEEDBACK_DIR", "data/candidate_feedback")
    example_pairs_raw_dir = project_root / os.getenv("EXAMPLE_PAIRS_RAW_DIR", "data/example_pairs/raw")
    reviews_dir = project_root / os.getenv("REVIEWS_DIR", "data/processed/reviews")
    prompt_file = project_root / os.getenv("PROMPT_FILE", "prompts/assignment_prompt.txt")

    settings = Settings(
        project_root=project_root,
        storage_backend=os.getenv("STORAGE_BACKEND", DEFAULT_STORAGE_BACKEND).strip().lower(),
        llm_provider=os.getenv("LLM_PROVIDER", "mock").strip().lower(),
        openai_api_key=(
            os.getenv("OPENAI_API_KEY", "").strip()
            or _read_databricks_secret(os.getenv("DATABRICKS_SECRET_SCOPE", ""), "OPENAI_API_KEY")
        ),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        judge_provider=os.getenv("JUDGE_PROVIDER", DEFAULT_JUDGE_PROVIDER).strip().lower(),
        judge_model=os.getenv("JUDGE_MODEL", DEFAULT_JUDGE_MODEL).strip(),
        judge_api_key=(
            os.getenv("JUDGE_API_KEY", "").strip()
            or os.getenv("GEMINI_API_KEY", "").strip()
            or _read_databricks_secret(os.getenv("DATABRICKS_SECRET_SCOPE", ""), "JUDGE_API_KEY")
            or _read_databricks_secret(os.getenv("DATABRICKS_SECRET_SCOPE", ""), "GEMINI_API_KEY")
        ),
        use_llm_job_parser=os.getenv("USE_LLM_JOB_PARSER", str(int(DEFAULT_USE_LLM_JOB_PARSER))).strip().lower()
        in {"1", "true", "yes", "on"},
        use_sentence_transformers=os.getenv("USE_SENTENCE_TRANSFORMERS", str(int(DEFAULT_USE_SENTENCE_TRANSFORMERS))).strip().lower()
        in {"1", "true", "yes", "on"},
        jobbert_model_name=os.getenv("JOBBERT_MODEL_NAME", "JobBERT-v3").strip(),
        databricks_server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip(),
        databricks_http_path=os.getenv("DATABRICKS_HTTP_PATH", "").strip(),
        databricks_token=os.getenv("DATABRICKS_TOKEN", "").strip(),
        databricks_bronze_job_ads_table=os.getenv(
            "DATABRICKS_BRONZE_JOB_ADS_TABLE",
            DEFAULT_DATABRICKS_BRONZE_JOB_ADS_TABLE,
        ).strip(),
        databricks_bronze_assignment_versions_table=os.getenv(
            "DATABRICKS_BRONZE_ASSIGNMENT_VERSIONS_TABLE",
            DEFAULT_DATABRICKS_BRONZE_ASSIGNMENT_VERSIONS_TABLE,
        ).strip(),
        databricks_bronze_reviewer_feedback_table=os.getenv(
            "DATABRICKS_BRONZE_REVIEWER_FEEDBACK_TABLE",
            DEFAULT_DATABRICKS_BRONZE_REVIEWER_FEEDBACK_TABLE,
        ).strip(),
        databricks_bronze_candidate_feedback_table=os.getenv(
            "DATABRICKS_BRONZE_CANDIDATE_FEEDBACK_TABLE",
            DEFAULT_DATABRICKS_BRONZE_CANDIDATE_FEEDBACK_TABLE,
        ).strip(),
        databricks_bronze_review_decisions_table=os.getenv(
            "DATABRICKS_BRONZE_REVIEW_DECISIONS_TABLE",
            DEFAULT_DATABRICKS_BRONZE_REVIEW_DECISIONS_TABLE,
        ).strip(),
        databricks_silver_parsed_jobs_table=os.getenv(
            "DATABRICKS_SILVER_PARSED_JOBS_TABLE",
            DEFAULT_DATABRICKS_SILVER_PARSED_JOBS_TABLE,
        ).strip(),
        databricks_silver_assignment_versions_table=os.getenv(
            "DATABRICKS_SILVER_ASSIGNMENT_VERSIONS_TABLE",
            DEFAULT_DATABRICKS_SILVER_ASSIGNMENT_VERSIONS_TABLE,
        ).strip(),
        databricks_silver_reviewer_feedback_table=os.getenv(
            "DATABRICKS_SILVER_REVIEWER_FEEDBACK_TABLE",
            DEFAULT_DATABRICKS_SILVER_REVIEWER_FEEDBACK_TABLE,
        ).strip(),
        databricks_silver_candidate_feedback_table=os.getenv(
            "DATABRICKS_SILVER_CANDIDATE_FEEDBACK_TABLE",
            DEFAULT_DATABRICKS_SILVER_CANDIDATE_FEEDBACK_TABLE,
        ).strip(),
        databricks_silver_review_decisions_table=os.getenv(
            "DATABRICKS_SILVER_REVIEW_DECISIONS_TABLE",
            DEFAULT_DATABRICKS_SILVER_REVIEW_DECISIONS_TABLE,
        ).strip(),
        databricks_gold_kpi_summary_table=os.getenv(
            "DATABRICKS_GOLD_KPI_SUMMARY_TABLE",
            DEFAULT_DATABRICKS_GOLD_KPI_SUMMARY_TABLE,
        ).strip(),
        databricks_gold_latest_assignments_table=os.getenv(
            "DATABRICKS_GOLD_LATEST_ASSIGNMENTS_TABLE",
            DEFAULT_DATABRICKS_GOLD_LATEST_ASSIGNMENTS_TABLE,
        ).strip(),
        databricks_catalog=os.getenv("DATABRICKS_CATALOG", DEFAULT_DATABRICKS_CATALOG).strip(),
        databricks_schema=os.getenv("DATABRICKS_SCHEMA", DEFAULT_DATABRICKS_SCHEMA).strip(),
        databricks_secret_scope=os.getenv(
            "DATABRICKS_SECRET_SCOPE",
            DEFAULT_DATABRICKS_SECRET_SCOPE,
        ).strip(),
        app_data_dir=app_data_dir,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        feedback_dir=feedback_dir,
        candidate_feedback_dir=candidate_feedback_dir,
        example_pairs_raw_dir=example_pairs_raw_dir,
        reviews_dir=reviews_dir,
        prompt_file=prompt_file,
        duration_options=DEFAULT_DURATION_OPTIONS,
        duration_labels=DEFAULT_DURATION_LABELS,
        default_duration=DEFAULT_DEFAULT_DURATION,
        difficulty_options=DEFAULT_DIFFICULTY_OPTIONS,
        default_difficulty=DEFAULT_DEFAULT_DIFFICULTY,
        retrieval_domain_options=DEFAULT_RETRIEVAL_DOMAIN_OPTIONS,
        review_feedback_options=DEFAULT_REVIEW_FEEDBACK_OPTIONS,
        review_reason_options=DEFAULT_REVIEW_REASON_OPTIONS,
        final_decision_options=DEFAULT_FINAL_DECISION_OPTIONS,
        default_reviewer_name=DEFAULT_DEFAULT_REVIEWER_NAME,
        default_reviewer_rating=DEFAULT_DEFAULT_REVIEW_RATING,
        candidate_score_min=DEFAULT_CANDIDATE_SCORE_MIN,
        candidate_score_max=DEFAULT_CANDIDATE_SCORE_MAX,
        candidate_score_default=DEFAULT_CANDIDATE_SCORE_DEFAULT,
        candidate_time_reasonable_options=DEFAULT_CANDIDATE_TIME_REASONABLE_OPTIONS,
        feedback_rating_min=DEFAULT_FEEDBACK_RATING_MIN,
        feedback_rating_max=DEFAULT_FEEDBACK_RATING_MAX,
        retrieval_top_k_default=DEFAULT_RETRIEVAL_TOP_K,
        retrieval_top_k_min=DEFAULT_RETRIEVAL_TOP_K_MIN,
        retrieval_top_k_max=DEFAULT_RETRIEVAL_TOP_K_MAX,
        show_retrieval_debug_default=DEFAULT_SHOW_RETRIEVAL_DEBUG,
        use_retrieval_default=DEFAULT_USE_RETRIEVAL,
        app_title=DEFAULT_APP_TITLE,
        app_subtitle=DEFAULT_APP_SUBTITLE,
        job_input_placeholder=DEFAULT_JOB_INPUT_PLACEHOLDER,
        focus_area_placeholder=DEFAULT_FOCUS_AREA_PLACEHOLDER,
        reviewer_rating_help=DEFAULT_REVIEWER_RATING_HELP,
        generation_note=DEFAULT_GENERATION_NOTE,
    )
    settings.ensure_directories()
    return settings
