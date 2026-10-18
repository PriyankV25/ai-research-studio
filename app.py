"""Flask API and web interface for the AI Research Studio."""
from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timezone
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder="static", static_url_path="/static")
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def update_job(job_id: str, **updates):
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(updates)
            JOBS[job_id]["updated_at"] = datetime.now(timezone.utc).isoformat()


def run_job(job_id: str, topic: str):
    try:
        # Import inside the worker so missing configuration is reported by the job API.
        from pipeline import run_research_pipeline

        def progress(stage, message):
            update_job(job_id, stage=stage, message=message)

        result = run_research_pipeline(topic, progress_callback=progress)
        update_job(
            job_id,
            status="completed",
            stage="completed",
            message="Your report is ready.",
            report=result.get("report", ""),
            feedback=result.get("feedback", ""),
            search_results=result.get("search_results", ""),
            scraped_content=result.get("scraped_content", ""),
        )
    except Exception as exc:
        update_job(job_id, status="failed", stage="error", message="The research run failed.", error=str(exc))


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/health")
def render_health():
    # Liveness check for the hosting platform; API-key configuration is checked separately.
    return jsonify({"ok": True}), 200


@app.get("/api/health")
def health():
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    required = ["TAVILY_API_KEY"]
    if provider == "groq":
        required.append("GROQ_API_KEY")
    elif provider != "ollama":
        return jsonify({"ok": False, "error": f"Unsupported LLM_PROVIDER: {provider}"}), 500
    missing = [key for key in required if not os.getenv(key)]
    return jsonify({"ok": not missing, "provider": provider, "missing_keys": missing})


@app.post("/api/research")
def start_research():
    payload = request.get_json(silent=True) or {}
    topic = str(payload.get("topic", "")).strip()
    if len(topic) < 3:
        return jsonify({"error": "Enter a research topic with at least 3 characters."}), 400
    if len(topic) > 500:
        return jsonify({"error": "Please keep the topic under 500 characters."}), 400
    job_id = uuid.uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()
    with JOBS_LOCK:
        JOBS[job_id] = {
            "id": job_id, "topic": topic, "status": "running", "stage": "search",
            "message": "Preparing your research run…", "created_at": now, "updated_at": now,
            "report": "", "feedback": "", "search_results": "", "scraped_content": "", "error": "",
        }
    threading.Thread(target=run_job, args=(job_id, topic), daemon=True).start()
    return jsonify({"job_id": job_id, "status": "running"}), 202


@app.get("/api/jobs/<job_id>")
def get_job(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"error": "Research job not found."}), 404
        return jsonify(job)


if __name__ == "__main__":
    # Render and other hosting platforms require binding to all interfaces.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
