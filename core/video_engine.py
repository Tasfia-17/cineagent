"""
Seedance 2.0 video generation backend.
Implements ViMax's VideoGenerator protocol (duck-typed).
Upgraded from ViMax's doubao-seedance-1-0 → doubao-seedance-2-0-260128.

Key Seedance 2.0 upgrades over 1.0:
- Native audio generation (dialogue, SFX, ambient — all in one pass)
- Multimodal inputs: up to 9 images + 3 videos + 3 audio in one request
- @image1 / @audio1 reference syntax for conditioning
- Up to 2K resolution, 4–15s clips
"""

import os
import logging
import asyncio
import aiohttp
from typing import List, Literal, Optional
from interfaces.video_output import VideoOutput
from utils.image import image_path_to_b64

SEEDANCE_API_KEY = os.getenv("SEEDANCE_API_KEY", "a3f914cf-838f-4bd3-91c7-135c33518f40")
SEEDANCE_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
T2V_MODEL = "doubao-seedance-2-0-260128"
T2V_FAST_MODEL = "doubao-seedance-2-0-fast-260128"


class VideoGeneratorSeedance2:
    """
    Seedance 2.0 backend. Satisfies ViMax's VideoGenerator protocol.
    Supports T2V, I2V (first frame), first+last frame, and native audio generation.
    """

    def __init__(
        self,
        api_key: str = SEEDANCE_API_KEY,
        fast: bool = False,
    ):
        self.api_key = api_key
        self.model = T2V_FAST_MODEL if fast else T2V_MODEL

    def _build_content(
        self,
        prompt: str,
        reference_image_paths: List[str],
        audio_path: Optional[str] = None,
        resolution: str = "720p",
        aspect_ratio: str = "16:9",
        duration: int = 5,
        generate_audio: bool = True,
    ) -> list:
        """Build the multimodal content array for Seedance 2.0."""
        # Seedance 2.0 accepts params inline in the prompt string
        full_prompt = (
            f"{prompt} "
            f"--rs {resolution} --rt {aspect_ratio} "
            f"--dur {duration} --fps 24 --wm false --seed -1 "
            f"--cf false --ga {'true' if generate_audio else 'false'}"
        )
        content = [{"type": "text", "text": full_prompt}]

        # First frame reference
        if len(reference_image_paths) >= 1:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_path_to_b64(reference_image_paths[0])},
                "role": "first_frame",
            })

        # Last frame reference (first+last frame mode)
        if len(reference_image_paths) >= 2:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_path_to_b64(reference_image_paths[1])},
                "role": "last_frame",
            })

        # Audio reference for native lip-sync (Seedance 2.0 exclusive)
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                import base64
                audio_b64 = "data:audio/mp3;base64," + base64.b64encode(f.read()).decode()
            content.append({
                "type": "audio_url",
                "audio_url": {"url": audio_b64},
            })

        return content

    async def _submit_task(self, content: list) -> str:
        """Submit generation task, return task_id."""
        payload = {"model": self.model, "content": content}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(SEEDANCE_ENDPOINT, headers=headers, json=payload) as resp:
                        data = await resp.json()
                        task_id = data["id"]
                        logging.info(f"[Seedance2] Task submitted: {task_id}")
                        return task_id
            except Exception as e:
                logging.error(f"[Seedance2] Submit error: {e}. Retrying in 2s...")
                await asyncio.sleep(2)

    async def _poll_task(self, task_id: str) -> str:
        """Poll until succeeded, return video URL."""
        url = f"https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        wait = 5
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as resp:
                        data = await resp.json()
            except Exception as e:
                logging.error(f"[Seedance2] Poll error: {e}. Retrying...")
                await asyncio.sleep(wait)
                continue

            status = data.get("status")
            if status == "succeeded":
                video_url = data["content"]["video_url"]
                logging.info(f"[Seedance2] Done: {video_url[:60]}...")
                return video_url
            elif status in ("failed", "expired", "cancelled"):
                raise RuntimeError(f"[Seedance2] Task {task_id} failed: {status}")
            else:
                logging.info(f"[Seedance2] Status: {status}. Waiting {wait}s...")
                await asyncio.sleep(wait)
                wait = min(wait * 1.5, 30)

    async def generate_single_video(
        self,
        prompt: str,
        reference_image_paths: List[str],
        resolution: Literal["480p", "720p", "1080p"] = "720p",
        aspect_ratio: str = "16:9",
        duration: Literal[5, 10] = 5,
        generate_audio: bool = True,
        audio_path: Optional[str] = None,
        **kwargs,
    ) -> VideoOutput:
        """
        Generate a video. Satisfies ViMax VideoGenerator protocol.
        Returns VideoOutput with video URL.
        """
        content = self._build_content(
            prompt=prompt,
            reference_image_paths=reference_image_paths,
            audio_path=audio_path,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            duration=duration,
            generate_audio=generate_audio,
        )
        task_id = await self._submit_task(content)
        video_url = await self._poll_task(task_id)
        return VideoOutput(fmt="url", ext="mp4", data=video_url)
