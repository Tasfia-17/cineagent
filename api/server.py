"""
FastAPI backend — REST API for CineAgent pipeline.
Run: uvicorn api.server:app --reload
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uuid
import json

from pipeline import run_pipeline

app = FastAPI(title="CineAgent API", version="1.0.0")

# In-memory job store (use Redis in production)
jobs: dict = {}


class GenerateRequest(BaseModel):
    idea: str
    fast_mode: bool = True


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending | running | done | failed
    result: dict | None = None
    error: str | None = None


def _run_job(job_id: str, idea: str, fast_mode: bool):
    jobs[job_id]["status"] = "running"
    try:
        result = run_pipeline(idea, output_dir=f"output/{job_id}", fast_mode=fast_mode)
        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = {
            "title": result["title"],
            "final_video": result["final_video"],
            "screenplay": result["screenplay"],
        }
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/generate", response_model=JobStatus)
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "pending", "result": None, "error": None}
    background_tasks.add_task(_run_job, job_id, req.idea, req.fast_mode)
    return JobStatus(job_id=job_id, status="pending")


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return JobStatus(job_id=job_id, **job)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "CineAgent"}
