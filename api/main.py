from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api.routes.job_ads import router as job_ads_router

app = FastAPI(title="Recruitment Assignment API", version="0.1.0")
app.include_router(job_ads_router)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Recruitment Assignment API</title>
    <style>
      body {
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 0;
        background: linear-gradient(180deg, #f6f8fc 0%, #eef2f7 100%);
        color: #1f2937;
      }
      .wrap {
        max-width: 960px;
        margin: 0 auto;
        padding: 48px 20px 64px;
      }
      .card {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        padding: 28px;
      }
      h1 {
        margin: 0 0 8px;
        font-size: 32px;
      }
      p {
        margin: 0 0 18px;
        color: #6b7280;
      }
      label {
        display: block;
        font-weight: 600;
        margin: 16px 0 8px;
      }
      textarea, input, select {
        width: 100%;
        border: 1px solid #d1d5db;
        border-radius: 12px;
        padding: 12px 14px;
        font: inherit;
        box-sizing: border-box;
        background: #fff;
      }
      textarea {
        min-height: 220px;
        resize: vertical;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .row {
        margin-top: 16px;
      }
      .actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 20px;
      }
      button {
        border: 0;
        border-radius: 999px;
        padding: 12px 18px;
        background: #2563eb;
        color: white;
        font-weight: 700;
        cursor: pointer;
      }
      button.secondary {
        background: #e5e7eb;
        color: #111827;
      }
      pre {
        background: #0f172a;
        color: #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        overflow: auto;
        white-space: pre-wrap;
        word-break: break-word;
      }
      .muted {
        color: #6b7280;
        font-size: 14px;
      }
      @media (max-width: 720px) {
        .grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="card">
        <h1>Recruitment Assignment API</h1>
        <p>Paste a job ad, submit it once, and the pipeline will trigger in the background.</p>

        <label for="job_text">Job Ad</label>
        <textarea id="job_text" placeholder="Paste the full job advertisement here..."></textarea>

        <div class="grid">
          <div>
            <label for="assignment_hours">Assignment Hours</label>
            <select id="assignment_hours">
              <option value="1h">1h</option>
              <option value="2h" selected>2h</option>
              <option value="3h">3h</option>
              <option value="4h">4h</option>
              <option value="5h+">5h+</option>
            </select>
          </div>
          <div>
            <label for="difficulty">Difficulty</label>
            <select id="difficulty">
              <option value="easy">easy</option>
              <option value="medium" selected>medium</option>
              <option value="hard">hard</option>
            </select>
          </div>
        </div>

        <div class="grid">
          <div>
            <label for="focus_area">Focus Area</label>
            <input id="focus_area" placeholder="e.g. CRM, backend APIs, analytics" />
          </div>
          <div>
            <label for="secret_scope">Secret Scope</label>
            <input id="secret_scope" value="mlops-project" />
          </div>
        </div>

        <div class="row">
          <label>
            <input type="checkbox" id="use_retrieval" />
            Use retrieval
          </label>
        </div>

        <div class="actions">
          <button id="submit_btn" onclick="submitJob()">Generate Assignment</button>
          <button class="secondary" onclick="loadLatest()">Check Latest Result</button>
        </div>

        <div class="row muted" id="status">Ready.</div>
        <div class="row">
          <pre id="output">{}</pre>
        </div>
      </div>
    </div>

    <script>
      let latestJobId = "";

      function setStatus(message) {
        document.getElementById("status").textContent = message;
      }

      function setOutput(data) {
        document.getElementById("output").textContent = JSON.stringify(data, null, 2);
      }

      async function submitJob() {
        const payload = {
          job_text: document.getElementById("job_text").value,
          assignment_hours: document.getElementById("assignment_hours").value,
          difficulty: document.getElementById("difficulty").value,
          focus_area: document.getElementById("focus_area").value,
          use_retrieval: document.getElementById("use_retrieval").checked,
          top_k: 2,
          domain_override: "auto",
          show_retrieval_debug: true,
          secret_scope: document.getElementById("secret_scope").value || "mlops-project",
        };

        if (!payload.job_text.trim()) {
          setStatus("Please paste a job ad first.");
          return;
        }

        setStatus("Submitting job ad...");
        const response = await fetch("/job-ads", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        latestJobId = data.job_id || "";
        setOutput(data);
        setStatus(`Submitted. Job ID: ${latestJobId}`);
      }

      async function loadLatest() {
        if (!latestJobId) {
          setStatus("No job id yet. Submit a job first.");
          return;
        }

        setStatus("Checking status...");
        const statusResponse = await fetch(`/job-ads/${latestJobId}`);
        const statusData = await statusResponse.json();

        const resultResponse = await fetch(`/job-ads/${latestJobId}/result`);
        const resultData = await resultResponse.json();

        setOutput({ status: statusData, result: resultData });
        setStatus(`Status: ${statusData.status}`);
      }
    </script>
  </body>
</html>
    """


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
