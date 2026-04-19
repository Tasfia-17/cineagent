"""
CineAgent Pipeline — async orchestration of all agents.

Flow:
  idea
    → [Screenplay Agent]  story + 3-scene script
    → [Director Agent]    cinematic storyboard prompts
    → [Keyframe Engine]   Seedream 5.0 → reference image per scene  ← NEW
    → [Video Engine]      Seedance 2.0 I2V (image+prompt → clip)    ← upgraded
    → [Quality Agent]     score + auto-retry with improved prompt
    → [Narrator Agent]    edge-tts voiceover
    → [Assembler]         final .mp4
"""

import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

from agents.screenplay_agent import write_screenplay
from agents.director_agent import direct_screenplay
from agents.quality_agent import evaluate_clip
from agents.narrator_agent import generate_narration
from core.video_engine import VideoGeneratorSeedance2
from core.keyframe_engine import generate_keyframe
from core.assembler import assemble_film


async def _generate_scene(
    engine: VideoGeneratorSeedance2,
    scene: dict,
    clip_path: str,
    keyframe_path: str,
    fast: bool,
    log_queue: asyncio.Queue,
) -> str:
    prompt = scene["seedance_prompt"]

    for attempt in range(2):
        await log_queue.put(f"  🎞️ Scene {scene['scene_number']} {'[retry] ' if attempt else ''}generating...")
        try:
            # Use I2V if keyframe exists, else T2V
            ref_images = [keyframe_path] if os.path.exists(keyframe_path) else []
            mode = "I2V" if ref_images else "T2V"
            await log_queue.put(f"  🖼️ Scene {scene['scene_number']} mode: {mode} (Seedance 2.0)")

            output = await engine.generate_single_video(
                prompt=prompt,
                reference_image_paths=ref_images,
                resolution="480p" if fast else "720p",
                aspect_ratio="16:9",
                duration=5,
                generate_audio=True,
            )
            output.save(clip_path)

            # Quality gate
            quality = evaluate_clip(scene, prompt)
            score = quality.get("score", 7)
            await log_queue.put(f"  ✅ Scene {scene['scene_number']} quality score: {score}/10")

            if not quality.get("should_regenerate") or attempt == 1:
                break
            prompt = quality.get("improved_prompt", prompt)
            scene["seedance_prompt"] = prompt
            await log_queue.put(f"  🔄 Scene {scene['scene_number']} retrying with improved prompt...")

        except Exception as e:
            await log_queue.put(f"  ❌ Scene {scene['scene_number']} error: {e}")
            break

    return clip_path


async def run_pipeline_streaming(
    idea: str,
    output_dir: str = "output",
    fast: bool = False,
) -> AsyncGenerator[str, None]:
    """
    Streaming pipeline — yields log lines as they happen.
    Use this for the Gradio UI to show live agent reasoning.
    """
    log_queue: asyncio.Queue = asyncio.Queue()
    result_holder = {}

    async def _pipeline():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(output_dir) / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        await log_queue.put(f"🎬 CineAgent starting...")
        await log_queue.put(f"💡 Idea: \"{idea}\"")

        # Step 1: Screenplay
        await log_queue.put("\n📝 [Screenplay Agent] Developing story...")
        screenplay = write_screenplay(idea)
        await log_queue.put(f"📝 [Screenplay Agent] Story developed — {len(screenplay['scenes'])} scenes")
        for s in screenplay["scenes"]:
            await log_queue.put(f"   Scene {s['scene_number']}: {s['script'][:80]}...")

        # Step 2: Director
        await log_queue.put("\n🎥 [Director Agent] Creating storyboard...")
        screenplay = direct_screenplay(screenplay)
        await log_queue.put("🎥 [Director Agent] Storyboard complete")
        for s in screenplay["scenes"]:
            await log_queue.put(f"   Scene {s['scene_number']} prompt: {s['seedance_prompt'][:80]}...")

        scenes = screenplay["scenes"]
        title = screenplay.get("title", "Untitled")
        with open(run_dir / "screenplay.json", "w") as f:
            json.dump(screenplay, f, indent=2)

        # Step 3: Keyframes (Seedream 5.0)
        await log_queue.put("\n🖼️ [Keyframe Engine] Generating reference images with Seedream 5.0...")
        keyframe_paths = []
        for i, scene in enumerate(scenes):
            kf_path = str(run_dir / f"keyframe_{i+1:02d}.png")
            try:
                await generate_keyframe(scene["seedance_prompt"], kf_path)
                await log_queue.put(f"   ✅ Keyframe {i+1} generated (Seedream 5.0)")
            except Exception as e:
                await log_queue.put(f"   ⚠️ Keyframe {i+1} failed ({e}), using T2V")
                kf_path = ""
            keyframe_paths.append(kf_path)

        # Step 4: Video clips (Seedance 2.0 I2V) — parallel
        await log_queue.put("\n🎞️ [Video Engine] Generating clips with Seedance 2.0 (parallel)...")
        engine = VideoGeneratorSeedance2(fast=fast)
        clip_paths = [str(run_dir / f"clip_{i+1:02d}.mp4") for i in range(len(scenes))]

        tasks = [
            _generate_scene(engine, scene, clip_paths[i], keyframe_paths[i], fast, log_queue)
            for i, scene in enumerate(scenes)
        ]
        await asyncio.gather(*tasks)

        # Step 5: Narration (edge-tts, free)
        await log_queue.put("\n🎙️ [Narrator Agent] Generating voiceover (edge-tts)...")
        audio_paths = []
        for i, scene in enumerate(scenes):
            text = f"{scene.get('action', '')} {scene.get('dialogue', '')}".strip()
            audio_path = str(run_dir / f"narration_{i+1:02d}.mp3")
            if text:
                generate_narration(text, audio_path)
                await log_queue.put(f"   🎙️ Scene {i+1} narration done")
            audio_paths.append(audio_path if os.path.exists(audio_path) else "")

        # Step 6: Assemble
        await log_queue.put("\n🎬 [Assembler] Stitching final film...")
        valid = [(c, a) for c, a in zip(clip_paths, audio_paths) if os.path.exists(c)]
        final_path = str(run_dir / f"{title.replace(' ', '_')}.mp4")

        if valid:
            assemble_film([c for c, _ in valid], [a for _, a in valid], final_path)
            await log_queue.put(f"\n✅ Film complete: {final_path}")
        else:
            await log_queue.put("\n❌ No clips generated — check Seedance API key")
            final_path = ""

        result_holder["final_video"] = final_path
        result_holder["screenplay"] = screenplay
        result_holder["title"] = title
        await log_queue.put("__DONE__")

    # Run pipeline in background, yield logs as they arrive
    pipeline_task = asyncio.create_task(_pipeline())

    while True:
        try:
            msg = await asyncio.wait_for(log_queue.get(), timeout=300)
            if msg == "__DONE__":
                break
            yield msg
        except asyncio.TimeoutError:
            yield "⚠️ Timeout waiting for pipeline..."
            break

    await pipeline_task
    yield f"__RESULT__{json.dumps(result_holder)}"


def run_pipeline(idea: str, output_dir: str = "output", fast_mode: bool = False) -> dict:
    """Sync wrapper for CLI use."""
    async def _collect():
        result = {}
        async for msg in run_pipeline_streaming(idea, output_dir, fast_mode):
            if msg.startswith("__RESULT__"):
                result = json.loads(msg[10:])
            else:
                print(msg)
        return result
    return asyncio.run(_collect())


if __name__ == "__main__":
    import sys
    idea = sys.argv[1] if len(sys.argv) > 1 else \
        "A lone astronaut discovers an ancient alien artifact on Mars that begins to speak in a forgotten human language."
    run_pipeline(idea, fast_mode="--fast" in sys.argv)
