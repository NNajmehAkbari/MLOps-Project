# Recruitment Assignment AI

Databricks integration workspace.

Stable local version:
- `/Users/najmehakbari/recruitment_assignment_ai`

This copy is reserved for the Databricks-backed version so we can evolve the storage and retrieval layer without disturbing the local MVP.

A local MVP for generating take-home assignments from job advertisements.

## Features
- Input a new job ad
- Clean and parse job ad text
- Build a prompt
- Generate an assignment
- Store results through the configured backend
- Save reviewer feedback
- Compute KPI scores, including JobBERT-v3 similarity

## Configuration
Most runtime configuration lives in [`src/utils/config.py`](src/utils/config.py) and can be overridden with environment variables or a local `.env` file. That includes:
- data and output directories
- model names
- prompt file location
- Streamlit defaults such as duration options, retrieval options, and review labels
- the storage backend (`local` or `databricks`)
- Databricks host / HTTP path / token and table names

An example template is available in [`.env.example`](.env.example).

### Secrets
Do not commit real API keys to Git.

- For local development, keep keys in your personal `.env` file and leave it ignored by Git.
- For Databricks, prefer workspace secrets or job-level environment variables that reference secrets, instead of hardcoding values in `databricks.yml`.
- The code already reads `OPENAI_API_KEY`, `JUDGE_API_KEY` or `GEMINI_API_KEY`, and the Databricks connection values from environment variables.

By default:
- generation uses `OPENAI_API_KEY` and `OPENAI_MODEL`
- the judge uses `JUDGE_PROVIDER=gemini`, `JUDGE_MODEL=gemini-2.5-flash`, and `JUDGE_API_KEY` or `GEMINI_API_KEY`
- persistence uses `STORAGE_BACKEND=local` by default

To connect this workspace to Databricks, set:

```env
STORAGE_BACKEND=databricks
DATABRICKS_SERVER_HOSTNAME=...
DATABRICKS_HTTP_PATH=...
DATABRICKS_TOKEN=...
```

## Databricks Data Layers
This workspace now uses a medallion-style layout:

- Bronze: raw event capture
  - job ads
  - generated assignment versions
  - reviewer feedback
  - candidate feedback
  - review decisions
- Silver: normalized snapshots used by the app
  - parsed job snapshots
  - normalized assignment versions
  - normalized feedback and review rows
- Gold: analytics-ready outputs
  - KPI summaries
  - latest assignment snapshots

The Analytics tab in Streamlit shows all three layers so you can inspect the flow end to end.

## Smoke Test
Use the bundled smoke test script to confirm the environment and backend wiring before a demo:

```bash
python scripts/smoke_test.py
```

If Databricks is configured correctly, the script prints the active settings and backend bootstrap status. If the Databricks SQL connector or credentials are missing, it exits with a helpful error message.

## Databricks Job Entry Points
The workflow logic lives in `src/`, and these thin CLI entry points can be used from Databricks Jobs or local shell runs:

- `python -m src.jobs.generate_assignment_job --job-text "..."` or `--job-text-file /path/to/job.txt`
- `python -m src.jobs.save_feedback_job reviewer ...`
- `python -m src.jobs.save_feedback_job candidate ...`
- `python -m src.jobs.save_feedback_job decision ...`
- `python -m src.jobs.refresh_gold_job --job-id ...`

These scripts are intentionally small wrappers around the shared business logic so the same code can run in Streamlit, in Databricks Jobs, or in a local terminal without divergence.

## Databricks Bundle and Jobs
The repo includes [`databricks.yml`](databricks.yml), which defines concrete Databricks Jobs for:

- `assignment_pipeline_job`
- `generate_assignment_job`
- `refresh_gold_job`
- `save_reviewer_feedback_job`
- `save_candidate_feedback_job`
- `save_final_decision_job`

Each job runs one thin Python entrypoint from `src/jobs/` and uses the same shared business logic as Streamlit.

Automation setup:
- `assignment_pipeline_job` is the on-demand workflow for generating an assignment and immediately refreshing Gold tables.
- `refresh_gold_job` also has a nightly schedule in `Europe/Helsinki` so Gold stays up to date even when nobody clicks the app.
- Streamlit remains the interactive trigger for new job ads, which keeps the user-facing flow simple while Databricks handles the recurring refresh.

Deploy the bundle with:

```bash
databricks bundle deploy
```

Run a job from the bundle with:

```bash
databricks bundle run assignment_pipeline_job -- --job_text="Paste job text here"
```

Or run a single-purpose job with:

```bash
databricks bundle run generate_assignment_job -- --job_text="Paste job text here"
```

### Create the Same Workflow in the Databricks UI
If you want to build it manually in the Jobs UI, create a job with two tasks:

1. `generate_assignment`
   - Type: `Python script`
   - Script path: `src/jobs/generate_assignment_job.py`
   - Parameters:
     - `--job-id`
     - `--job-text`
     - `--assignment-hours`
     - `--difficulty`
     - `--focus-area`
     - `--use-retrieval`
     - `--top-k`
     - `--domain-override`
     - `--show-retrieval-debug`
2. `refresh_gold`
   - Type: `Python script`
   - Script path: `src/jobs/refresh_gold_job.py`
   - Add dependency: `generate_assignment`
   - No extra parameters required unless you want to refresh a single job

Use one shared job cluster for both tasks so the workflow stays simple and fast.

The default bundle cluster uses a sample node type and Spark version; if your workspace uses a different cloud or policy, adjust `spark_version` and `node_type_id` in [`databricks.yml`](databricks.yml) before deploying.

## Run Checklist
1. Activate the repo-local virtualenv.
2. Confirm `.env` contains `OPENAI_API_KEY`, `JUDGE_PROVIDER`, `JUDGE_MODEL`, and the Databricks connection values.
3. Run `python scripts/smoke_test.py`.
4. Start Streamlit with `./venv/bin/streamlit run app/streamlit_app.py`.
5. Generate one assignment.
6. Open `Analytics` and verify:
   - Bronze shows the raw event stream
   - Silver shows normalized snapshot rows
   - Gold shows KPI summaries and latest assignment rows

## Setup

```bash
pip install -r requirements.txt
```

If you want the optional JobBERT / sentence-transformers path, install the ML extras too:

```bash
pip install -r requirements-ml.txt
```
