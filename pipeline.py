"""
CineAgent Pipeline — orchestrates all agents to produce a short film from one sentence.

Flow:
  idea (str)
    → ScreenplayAgent  → screenplay (3 scenes)
    → DirectorAgent    → enhanced prompts
    → [parallel] VideoEngine × 3 scenes (Seedance 2.0)
    → QualityAgent     → score each clip, regenerate if < 7
    → NarratorAgent    → voiceover per scene
    → Assembler        → final .mp4
"""

import os
import asyncio
import concurrent.futures
from pathlib import Path
from datetime import datetime

from agents.screenplay_agent import write_screenplay
from agents.director_agent import direct_screenplay
from agents.quality_agent import evaluate_clip
from agents.narrator_agent import generate_narration
from core.video_engine import generate_and_download
from core.assembler import assemble_film


def run_pipeline(idea: str, output_dir: str = "output", fast_mode: bool = False) -> dict:
    """
    Full CineAgent pipeline. Returns dict with paths and metadata.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(output_dir) / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  CineAgent — Generating film from idea:")
    print(f"  \"{idea}\"")
    print(f"{'='*60}\n")

    # ── Step 1: Screenplay Agent ──────────────────────────────
    screenplay = write_screenplay(idea)

    # ── Step 2: Director Agent ────────────────────────────────
    screenplay = direct_screenplay(screenplay)

    scenes = screenplay["scenes"]
    title = screenplay.get("title", "Untitled")

    # ── Step 3: Generate video clips (parallel) ───────────────
    print(f"\n[Pipeline] Generating {len(scenes)} video clips in parallel...")
    clip_paths = [None] * len(scenes)

    def generate_scene_clip(i, scene):
        prompt = scene["seedance_prompt"]
        clip_path = str(run_dir / f"clip_{i+1:02d}.mp4")
        print(f"  [Scene {i+1}] Submitting: {prompt[:60]}...")

        # Quality loop: try up to 2 times
        for attempt in range(2):
            try:
                generate_and_download(
                    prompt=prompt,
                    output_path=clip_path,
                    duration=5,
                    resolution="480p" if fast_mode else "720p",
                    aspect_ratio="16:9",
                    generate_audio=True,
                    fast=fast_mode,
                )
                # Quality check
                quality = evaluate_clip(scene, prompt)
                if not quality.get("should_regenerate") or attempt == 1:
                    break
                # Retry with improved prompt
                prompt = quality.get("improved_prompt", prompt)
                print(f"  [Scene {i+1}] Retrying with improved prompt...")
            except Exception as e:
                print(f"  [Scene {i+1}] Error: {e}")
                break

        return i, clip_path

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(generate_scene_clip, i, scene) for i, scene in enumerate(scenes)]
        for future in concurrent.futures.as_completed(futures):
            i, path = future.result()
            clip_paths[i] = path

    # ── Step 4: Narrator Agent ────────────────────────────────
    print(f"\n[Pipeline] Generating narration for {len(scenes)} scenes...")
    audio_paths = []
    for i, scene in enumerate(scenes):
        narration_text = scene.get("action", "") + " " + scene.get("dialogue", "")
        narration_text = narration_text.strip()
        audio_path = str(run_dir / f"narration_{i+1:02d}.mp3")
        if narration_text:
            generate_narration(narration_text, audio_path)
            audio_paths.append(audio_path if os.path.exists(audio_path) else "")
        else:
            audio_paths.append("")

    # ── Step 5: Assemble final film ───────────────────────────
    print(f"\n[Pipeline] Assembling final film...")
    valid_clips = [p for p in clip_paths if p and os.path.exists(p)]
    valid_audio = [audio_paths[clip_paths.index(p)] for p in valid_clips]

    final_path = str(run_dir / f"{title.replace(' ', '_')}.mp4")
    assemble_film(valid_clips, valid_audio, final_path, title=title)

    result = {
        "title": title,
        "idea": idea,
        "screenplay": screenplay,
        "clip_paths": clip_paths,
        "final_video": final_path,
        "run_dir": str(run_dir),
    }

    print(f"\n{'='*60}")
    print(f"  ✅ Film complete: {final_path}")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    import sys
    idea = sys.argv[1] if len(sys.argv) > 1 else "A lone astronaut discovers an ancient alien artifact on Mars that begins to speak in a forgotten human language."
    run_pipeline(idea, fast_mode="--fast" in sys.argv)
