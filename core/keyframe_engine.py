"""
Keyframe Generator — uses Seedream 5.0 (via Pollinations or BytePlus) to generate
a reference image per scene, then feeds it into Seedance 2.0 as I2V.
This gives visual consistency across scenes and uses a second BytePlus model.
"""

import os
import asyncio
import aiohttp
import logging
from pathlib import Path

# Pollinations has Seedream 5.0 as 'seedream5' — free, no key needed
POLLINATIONS_IMAGE_URL = "https://gen.pollinations.ai/image/{prompt}?model=seedream5&width=1280&height=720&seed=-1"

# BytePlus direct (if key available)
BYTEPLUS_IMAGE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
SEEDREAM_MODEL = "seedream-5-0-lite-260128"


async def generate_keyframe(prompt: str, output_path: str) -> str:
    """
    Generate a keyframe image using Seedream 5.0.
    Returns local path to saved image.
    Uses Pollinations (free) → falls back to BytePlus if key set.
    """
    byteplus_key = os.getenv("SEEDANCE_API_KEY")

    # Try BytePlus Seedream 5.0 first if key available
    if byteplus_key:
        try:
            result = await _byteplus_seedream(prompt, output_path, byteplus_key)
            if result:
                return result
        except Exception as e:
            logging.warning(f"[Keyframe] BytePlus failed ({e}), trying Pollinations...")

    # Fallback: Pollinations Seedream 5.0 (free)
    return await _pollinations_seedream(prompt, output_path)


async def _pollinations_seedream(prompt: str, output_path: str) -> str:
    """Generate keyframe via Pollinations Seedream 5.0 (free)."""
    import urllib.parse
    encoded = urllib.parse.quote(prompt[:200])
    url = f"https://gen.pollinations.ai/image/{encoded}?model=seedream5&width=1280&height=720&seed=-1&nologo=true"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            if resp.status == 200:
                data = await resp.read()
                with open(output_path, "wb") as f:
                    f.write(data)
                logging.info(f"[Keyframe] Saved: {output_path}")
                return output_path
            else:
                raise RuntimeError(f"Pollinations returned {resp.status}")


async def _byteplus_seedream(prompt: str, output_path: str, api_key: str) -> str:
    """Generate keyframe via BytePlus Seedream 5.0."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": SEEDREAM_MODEL,
        "prompt": prompt,
        "response_format": "url",
        "size": "1280x720",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BYTEPLUS_IMAGE_URL}/images/generations",
            json=payload, headers=headers,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            data = await resp.json()
            img_url = data["data"][0]["url"]

        # Download the image
        async with session.get(img_url) as img_resp:
            with open(output_path, "wb") as f:
                f.write(await img_resp.read())

    return output_path
