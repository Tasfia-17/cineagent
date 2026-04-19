"""
CineAgent Pipeline — async orchestration of all agents.
Follows ViMax's async pipeline pattern.

Flow:
  idea → Screenplay → Director → [parallel] Seedance 2.0 clips
       → Quality check + auto-retry → Narration → Assemble → final.mp4
"""

import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

from agents.screenplay_agent import write_screenplay
from agents.director_agent import direct_screenplay
from agents.quality_agent import evaluate_clip
from agents.narrator_agent import generate_narration
from core.video_engine import VideoGeneratorSeedance2
from core.assembler import assemble_film


async def _generate_scene(
    engine: VideoGeneratorSeedance2,
    scene: dict,
    clip_path: str,
    fast: bool,
) -> str:
    """Generate one scene clip with quality retry loop."""
    prompt = scene["seedance_prompt"]

    for attempt in range(2):
        try:
            print(f"  [Scene {scene['scene_number']}] {'Retry: ' if attempt else ''}Generating...")
            output = await engine.generate_single_video(
                prompt=prompt,
                reference_image_paths=[],
                resolution="480p" if fast else "720p",
                aspect_ratio="16:9",
                duration=5,
                generate_audio=True,
            )
            output.save(clip_path)

            # Quality gate
            quality = evaluate_clip(scene, prompt)
            if not quality.get("should_regenerate") or attempt == 1:
                print(f"  [Scene {scene['scene_number']}] ✅ Score: {quality.get('score')}/10")
                break
            # Improve prompt and retry
            prompt = quality.get("improved_prompt", prompt)
            scene["seedance_prompt"] = prompt

        except Exception as e:
            print(f"  [Scene {scene['scene_number']}] ❌ Error: {e}")
            break

    return clip_path


async def run_pipeline_async(idea: str, output_dir: str = "output", fast: bool = False) -> dict:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(output_dir) / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  🎬 CineAgent")
    print(f"  Idea: \"{idea}\"")
    print(f"{'='*60}\n")

    # Step 1 & 2: Screenplay + Director (sync LLM calls)
    screenplay = write_screenplay(idea)
    screenplay = direct_screenplay(screenplay)
    scenes = screenplay["scenes"]
    title = screenplay.get("title", "Untitled")

    # Save screenplay
    with open(run_dir / "screenplay.json", "w") as f:
        json.dump(screenplay, f, indent=2)

    # Step 3: Generate all clips in parallel (async)
    print(f"\n[Pipeline] Generating {len(scenes)} clips in parallel with Seedance 2.0...")
    engine = VideoGeneratorSeedance2(fast=fast)
    clip_paths = [str(run_dir / f"clip_{i+1:02d}.mp4") for i in range(len(scenes))]

    tasks = [
        _generate_scene(engine, scene, clip_paths[i], fast)
        for i, scene in enumerate(scenes)
    ]
    await asyncio.gather(*tasks)

    # Step 4: Narration per scene
    print(f"\n[Pipeline] Generating narration...")
    audio_paths = []
    for i, scene in enumerate(scenes):
        text = f"{scene.get('action', '')} {scene.get('dialogue', '')}".strip()
        audio_path = str(run_dir / f"narration_{i+1:02d}.mp3")
        if text:
            generate_narration(text, audio_path)
        audio_paths.append(audio_path if os.path.exists(audio_path) else "")

    # Step 5: Assemble
    print(f"\n[Pipeline] Assembling final film...")
    valid = [(c, a) for c, a in zip(clip_paths, audio_paths) if os.path.exists(c)]
    final_path = str(run_dir / f"{title.replace(' ', '_')}.mp4")

    if valid:
        assemble_film([c for c, _ in valid], [a for _, a in valid], final_path)
    else:
        print("[Pipeline] No clips generated — check API key and connectivity")

    print(f"\n✅ Done: {final_path}\n")
    return {
        "title": title,
        "idea": idea,
        "screenplay": screenplay,
        "clip_paths": clip_paths,
        "final_video": final_path,
        "run_dir": str(run_dir),
    }


def run_pipeline(idea: str, output_dir: str = "output", fast_mode: bool = False) -> dict:
    """Sync wrapper for use from Gradio / CLI."""
    return asyncio.run(run_pipeline_async(idea, output_dir, fast=fast_mode))


if __name__ == "__main__":
    import sys
    idea = sys.argv[1] if len(sys.argv) > 1 else \
        "A lone astronaut discovers an ancient alien artifact on Mars that begins to speak in a forgotten human language."
    run_pipeline(idea, fast_mode="--fast" in sys.argv)
