"""
ShopReel Pipeline — product → 5 platform videos
Triggered by Shopify webhook or manual product input.

Flow:
  product (title, description, image_url, price)
    → [Script Agent]    Pollinations LLM → 5 platform scripts
    → [Keyframe Engine] Seedream 5.0 → product keyframe per platform
    → [Video Engine]    Seedance 2.0 I2V → 5 videos in parallel
    → [Narrator Agent]  edge-tts → voiceover per platform
    → [Quality Agent]   score hook strength + CTA clarity
    → result dict with all 5 video paths
"""

import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

from agents.script_agent import generate_product_scripts, PLATFORMS
from agents.narrator_agent import generate_narration
from agents.quality_agent import evaluate_clip
from core.video_engine import VideoGeneratorSeedance2
from core.keyframe_engine import generate_keyframe


async def _generate_platform_video(
    engine: VideoGeneratorSeedance2,
    platform: str,
    script: dict,
    product: dict,
    run_dir: Path,
    log_queue: asyncio.Queue,
) -> tuple[str, str]:
    """Generate one platform video. Returns (platform, video_path)."""
    cfg = PLATFORMS[platform]
    prompt = script.get("seedance_prompt", script.get("script", ""))
    kf_prompt = script.get("seedream_prompt", prompt)

    await log_queue.put(f"  🖼️ [{platform}] Generating keyframe (Seedream 5.0)...")
    kf_path = str(run_dir / f"kf_{platform}.png")
    try:
        await generate_keyframe(kf_prompt, kf_path)
        await log_queue.put(f"  ✅ [{platform}] Keyframe ready")
    except Exception as e:
        await log_queue.put(f"  ⚠️ [{platform}] Keyframe failed ({e}), using T2V")
        kf_path = ""

    # Use product image as first frame if available and no keyframe
    product_img = product.get("image_url") or (
        product.get("images", [{}])[0].get("src") if product.get("images") else ""
    )

    ref_images = []
    if os.path.exists(kf_path):
        ref_images = [kf_path]

    await log_queue.put(f"  🎞️ [{platform}] Generating video (Seedance 2.0 {'I2V' if ref_images else 'T2V'})...")
    clip_path = str(run_dir / f"video_{platform}.mp4")

    for attempt in range(2):
        try:
            output = await engine.generate_single_video(
                prompt=prompt,
                reference_image_paths=ref_images,
                resolution="720p",
                aspect_ratio=cfg["aspect"],
                duration=min(cfg["duration"], 10),
                generate_audio=True,
            )
            output.save(clip_path)

            # Quality check
            quality = evaluate_clip(
                {"script": script.get("script", ""), "action": script.get("hook", "")},
                prompt,
            )
            score = quality.get("score", 7)
            await log_queue.put(f"  ✅ [{platform}] Score: {score}/10")

            if quality.get("should_regenerate") and attempt == 0:
                prompt = quality.get("improved_prompt", prompt)
                await log_queue.put(f"  🔄 [{platform}] Retrying with improved prompt...")
                continue
            break
        except Exception as e:
            await log_queue.put(f"  ❌ [{platform}] Error: {e}")
            break

    # Voiceover
    voiceover_text = script.get("script", "")
    audio_path = str(run_dir / f"audio_{platform}.mp3")
    if voiceover_text:
        generate_narration(voiceover_text[:300], audio_path)

    return platform, clip_path


async def run_shopreel_streaming(product: dict) -> AsyncGenerator[str, None]:
    """
    Streaming ShopReel pipeline.
    Yields log lines, then final __RESULT__ JSON.
    """
    log_queue: asyncio.Queue = asyncio.Queue()
    result_holder = {}

    async def _pipeline():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path("output") / f"shopreel_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        title = product.get("title", "Product")
        await log_queue.put(f"🛍️ ShopReel starting for: **{title}**")
        await log_queue.put(f"💰 Price: {product.get('variants', [{}])[0].get('price', 'N/A') if product.get('variants') else 'N/A'}")

        # Step 1: Generate scripts
        await log_queue.put("\n📝 [Script Agent] Generating 5 platform scripts...")
        scripts = await generate_product_scripts(product)
        for platform in scripts:
            await log_queue.put(f"   ✅ {platform}: \"{scripts[platform].get('hook', '')[:60]}...\"")

        # Step 2: Generate all 5 videos in parallel
        await log_queue.put("\n🎬 [Video Engine] Generating 5 videos in parallel...")
        engine = VideoGeneratorSeedance2(fast=False)

        tasks = [
            _generate_platform_video(engine, platform, scripts[platform], product, run_dir, log_queue)
            for platform in scripts
            if platform in PLATFORMS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        videos = {}
        for r in results:
            if isinstance(r, tuple):
                platform, path = r
                if os.path.exists(path):
                    videos[platform] = path
                    await log_queue.put(f"  🎬 {platform} video ready")

        await log_queue.put(f"\n✅ {len(videos)}/5 videos generated")
        result_holder["videos"] = videos
        result_holder["scripts"] = scripts
        result_holder["product"] = title
        result_holder["run_dir"] = str(run_dir)
        await log_queue.put("__DONE__")

    pipeline_task = asyncio.create_task(_pipeline())

    while True:
        try:
            msg = await asyncio.wait_for(log_queue.get(), timeout=600)
            if msg == "__DONE__":
                break
            yield msg
        except asyncio.TimeoutError:
            yield "⚠️ Timeout"
            break

    await pipeline_task
    yield f"__RESULT__{json.dumps(result_holder)}"


def run_shopreel(product: dict) -> dict:
    """Sync wrapper for CLI."""
    async def _collect():
        result = {}
        async for msg in run_shopreel_streaming(product):
            if msg.startswith("__RESULT__"):
                result = json.loads(msg[10:])
            else:
                print(msg)
        return result
    return asyncio.run(_collect())
