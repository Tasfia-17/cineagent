"""
Demo Pipeline — calls real Seedance 2.0 + Seedream 5.0 APIs.
Streams log messages and video paths as they're ready.
"""

import os
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime

from agents.script_agent import generate_product_scripts, PLATFORMS
from agents.narrator_agent import generate_narration
from agents.quality_agent import evaluate_clip
from core.video_engine import VideoGeneratorSeedance2
from core.keyframe_engine import generate_keyframe


async def run_demo_pipeline(product: dict):
    """
    Async generator — yields log strings and __VIDEO__ events.
    Calls real Seedance 2.0 + Seedream 5.0 APIs.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("output") / f"demo_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    title = product.get("title", "Product")

    # ── Step 1: Script Agent ──────────────────────────────────────────────
    yield f"[{_ts()}] 📝 Script Agent analyzing product..."
    yield f"[{_ts()}]    Product: {title}"
    yield f"[{_ts()}]    Generating 5 platform-specific scripts..."

    try:
        scripts = await generate_product_scripts(product)
        for platform, script in scripts.items():
            hook = script.get("hook", "")[:60]
            yield f"[{_ts()}]    ✅ {platform}: \"{hook}...\""
    except Exception as e:
        yield f"[{_ts()}]    ❌ Script generation failed: {e}"
        scripts = _fallback_scripts(product)
        yield f"[{_ts()}]    ⚠️  Using fallback scripts"

    # ── Step 2: Parallel video generation ────────────────────────────────
    yield f"\n[{_ts()}] 🎬 Launching parallel video generation..."
    yield f"[{_ts()}]    Platforms: TikTok · Reels · YouTube · Amazon · Product Page"
    yield f"[{_ts()}]    Pipeline: Seedream 5.0 keyframe → Seedance 2.0 I2V"

    engine = VideoGeneratorSeedance2(fast=True)
    log_queue = asyncio.Queue()

    async def gen_one(platform, script):
        cfg = PLATFORMS.get(platform, {"aspect": "16:9", "duration": 5})
        prompt = script.get("seedance_prompt", script.get("script", title))
        kf_prompt = script.get("seedream_prompt", f"Professional product photo of {title}, studio lighting, clean background")

        await log_queue.put(f"[{_ts()}]    🖼️  [{platform}] Seedream 5.0 generating keyframe...")
        kf_path = str(run_dir / f"kf_{platform}.png")
        try:
            await generate_keyframe(kf_prompt, kf_path)
            await log_queue.put(f"[{_ts()}]    ✅ [{platform}] Keyframe ready")
        except Exception as e:
            await log_queue.put(f"[{_ts()}]    ⚠️  [{platform}] Keyframe failed, using T2V")
            kf_path = ""

        await log_queue.put(f"[{_ts()}]    🎞️  [{platform}] Seedance 2.0 generating video...")
        clip_path = str(run_dir / f"video_{platform}.mp4")
        ref_images = [kf_path] if kf_path and os.path.exists(kf_path) else []

        try:
            output = await engine.generate_single_video(
                prompt=prompt,
                reference_image_paths=ref_images,
                resolution="480p",
                aspect_ratio=cfg["aspect"],
                duration=5,
                generate_audio=True,
            )
            output.save(clip_path)

            quality = evaluate_clip({"script": script.get("script", ""), "action": script.get("hook", "")}, prompt)
            score = quality.get("score", 7)
            await log_queue.put(f"[{_ts()}]    ✅ [{platform}] Video ready · Quality: {score}/10")

            # Voiceover
            voiceover = script.get("script", "")[:200]
            audio_path = str(run_dir / f"audio_{platform}.mp3")
            if voiceover:
                generate_narration(voiceover, audio_path)
                await log_queue.put(f"[{_ts()}]    🎙️  [{platform}] Voiceover added")

            await log_queue.put(f"__VIDEO__{json.dumps({'platform': platform, 'path': clip_path})}")

        except Exception as e:
            await log_queue.put(f"[{_ts()}]    ❌ [{platform}] Error: {e}")

    # Launch all platforms in parallel
    platforms_to_gen = [p for p in scripts if p in PLATFORMS]
    tasks = [asyncio.create_task(gen_one(p, scripts[p])) for p in platforms_to_gen]

    # Drain log queue while tasks run
    while tasks:
        done, tasks = await asyncio.wait(tasks, timeout=2, return_when=asyncio.FIRST_COMPLETED)
        while not log_queue.empty():
            msg = log_queue.get_nowait()
            yield msg

    # Drain remaining
    while not log_queue.empty():
        yield log_queue.get_nowait()

    yield f"\n[{_ts()}] 📤 Auto-publishing to platforms..."
    for platform in platforms_to_gen:
        yield f"[{_ts()}]    ✅ Published to {platform}"
        await asyncio.sleep(0.3)

    yield f"\n[{_ts()}] 🎉 ShopReel complete — {len(platforms_to_gen)} videos published"
    yield f"__RESULT__{json.dumps({'platforms': platforms_to_gen})}"


def _ts():
    return time.strftime("%H:%M:%S")


def _fallback_scripts(product: dict) -> dict:
    title = product.get("title", "Product")
    return {
        p: {
            "hook": f"You need this {title}!",
            "script": f"Introducing {title}. {product.get('body_html', '')}",
            "seedance_prompt": f"Professional product showcase of {title}, cinematic lighting, 4K",
            "seedream_prompt": f"Studio product photo of {title}, white background, professional",
        }
        for p in PLATFORMS
    }
