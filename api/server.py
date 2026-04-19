"""
ShopReel FastAPI Server
- POST /webhook/shopify  — receives Shopify products/create webhook
- POST /generate         — manual product input (for demo)
- GET  /status/{job_id}  — poll job status
- GET  /health           — health check
"""

import hmac
import hashlib
import base64
import json
import uuid
import asyncio
import os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from shopreel_pipeline import run_shopreel

app = FastAPI(title="ShopReel", version="1.0.0")

SHOPIFY_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")

# In-memory job store
jobs: dict = {}


def _verify_shopify_hmac(raw_body: bytes, hmac_header: str) -> bool:
    """Verify Shopify webhook HMAC signature."""
    if not SHOPIFY_SECRET:
        return True  # skip verification in dev mode
    digest = hmac.new(
        SHOPIFY_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).digest()
    computed = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed, hmac_header)


def _run_job(job_id: str, product: dict):
    """Background job runner."""
    jobs[job_id]["status"] = "running"
    try:
        result = run_shopreel(product)
        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = result
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/webhook/shopify")
async def shopify_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives Shopify products/create webhook.
    Immediately returns 200 (Shopify requires fast response),
    then processes in background.
    """
    raw_body = await request.body()
    hmac_header = request.headers.get("X-Shopify-Hmac-SHA256", "")

    if not _verify_shopify_hmac(raw_body, hmac_header):
        raise HTTPException(status_code=401, detail="Invalid HMAC")

    product = json.loads(raw_body)
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "pending", "result": None, "error": None, "product": product.get("title")}

    background_tasks.add_task(_run_job, job_id, product)

    print(f"[Webhook] New product: {product.get('title')} → job {job_id}")
    return {"job_id": job_id, "status": "accepted"}


class ManualProduct(BaseModel):
    title: str
    description: str = ""
    price: str = ""
    vendor: str = ""
    image_url: str = ""


@app.post("/generate")
async def manual_generate(product: ManualProduct, background_tasks: BackgroundTasks):
    """Manual product input for demo — no Shopify needed."""
    job_id = str(uuid.uuid4())[:8]
    product_dict = {
        "title": product.title,
        "body_html": product.description,
        "vendor": product.vendor,
        "image_url": product.image_url,
        "variants": [{"price": product.price}] if product.price else [],
    }
    jobs[job_id] = {"status": "pending", "result": None, "error": None, "product": product.title}
    background_tasks.add_task(_run_job, job_id, product_dict)
    return {"job_id": job_id, "status": "accepted"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **jobs[job_id]}


@app.get("/jobs")
async def list_jobs():
    return {"jobs": [{"job_id": k, **v} for k, v in jobs.items()]}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ShopReel"}
