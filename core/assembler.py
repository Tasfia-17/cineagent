"""
Assembler — stitches video clips + narration into a final film using MoviePy.
"""

import os
from pathlib import Path


def assemble_film(clip_paths: list[str], audio_paths: list[str], output_path: str, title: str = "") -> str:
    """
    Assemble video clips and audio into a final film.
    Returns path to final video.
    """
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
    except ImportError:
        print("[Assembler] MoviePy not available, returning first clip as output")
        if clip_paths:
            import shutil
            shutil.copy(clip_paths[0], output_path)
        return output_path

    print(f"[Assembler] Assembling {len(clip_paths)} clips into film")

    clips = []
    for i, (clip_path, audio_path) in enumerate(zip(clip_paths, audio_paths)):
        if not os.path.exists(clip_path):
            print(f"  [Assembler] Clip {i+1} missing, skipping")
            continue

        video = VideoFileClip(clip_path)

        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            # Trim audio to clip duration if longer
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            video = video.set_audio(audio)

        clips.append(video)

    if not clips:
        raise ValueError("No valid clips to assemble")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

    # Cleanup
    for clip in clips:
        clip.close()
    final.close()

    print(f"[Assembler] Film saved: {output_path} ({final.duration:.1f}s)")
    return output_path
