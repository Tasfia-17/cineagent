"""
CineAgent — Multi-agent cinematic short film generator
Pipeline: idea → screenplay → storyboard → video clips (Seedance 2.0) → assembled film
"""

import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SEEDANCE_API_KEY = os.getenv("SEEDANCE_API_KEY", "a3f914cf-838f-4bd3-91c7-135c33518f40")
SEEDANCE_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
SEEDANCE_MODEL = "doubao-seedance-2-0-260128"
SEEDANCE_FAST_MODEL = "doubao-seedance-2-0-fast-260128"


def generate_video_clip(
    prompt: str,
    image_url: Optional[str] = None,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    generate_audio: bool = True,
    fast: bool = False,
) -> str:
    """
    Submit a Seedance 2.0 video generation task.
    Returns task_id for polling.
    """
    model = SEEDANCE_FAST_MODEL if fast else SEEDANCE_MODEL

    content = [{"type": "text", "text": prompt}]
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    payload = {
        "model": model,
        "content": content,
        "resolution": resolution,
        "ratio": aspect_ratio,
        "duration": duration,
        "watermark": False,
        "generate_audio": generate_audio,
    }

    headers = {
        "Authorization": f"Bearer {SEEDANCE_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        f"{SEEDANCE_BASE_URL}/contents/generations/tasks",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def poll_video_task(task_id: str, timeout: int = 300) -> str:
    """
    Poll until task succeeds. Returns video URL.
    """
    headers = {"Authorization": f"Bearer {SEEDANCE_API_KEY}"}
    deadline = time.time() + timeout
    wait = 10

    while time.time() < deadline:
        resp = requests.get(
            f"{SEEDANCE_BASE_URL}/contents/generations/tasks/{task_id}",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")

        if status == "succeeded":
            return data["content"]["video_url"]
        elif status in ("failed", "expired", "cancelled"):
            raise RuntimeError(f"Seedance task {task_id} failed with status: {status}")

        time.sleep(wait)
        wait = min(wait * 1.5, 60)

    raise TimeoutError(f"Seedance task {task_id} timed out after {timeout}s")


def download_video(url: str, output_path: str) -> str:
    """Download video from URL to local path."""
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path


def generate_and_download(
    prompt: str,
    output_path: str,
    image_url: Optional[str] = None,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    generate_audio: bool = True,
    fast: bool = False,
) -> str:
    """Full flow: submit → poll → download. Returns local file path."""
    task_id = generate_video_clip(
        prompt=prompt,
        image_url=image_url,
        duration=duration,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        generate_audio=generate_audio,
        fast=fast,
    )
    print(f"  [Seedance] Task submitted: {task_id}")
    video_url = poll_video_task(task_id)
    print(f"  [Seedance] Done: {video_url[:60]}...")
    return download_video(video_url, output_path)
