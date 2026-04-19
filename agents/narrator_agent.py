"""
Narrator Agent — free TTS using edge-tts (Microsoft Edge, no API key needed).
Falls back to ionrouter.io if edge-tts fails.
"""

import os
import asyncio
import requests


IONROUTER_API_KEY = os.getenv("IONROUTER_API_KEY", "sk-bb3d84f1cea67cd03ef7e1355f51e184837a72cfd321fbbb")


async def _edge_tts(text: str, output_path: str, voice: str = "en-US-AriaNeural") -> str:
    """Free TTS via edge-tts (no API key needed)."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def generate_narration(text: str, output_path: str, voice: str = "en-US-AriaNeural") -> str:
    """
    Generate TTS narration. Uses edge-tts (free) first, then ionrouter.io fallback.
    Returns path to audio file.
    """
    if not text.strip():
        return ""

    print(f"  [Narrator] Generating: '{text[:60]}...'")

    # Try edge-tts first (completely free, no API key)
    try:
        asyncio.run(_edge_tts(text, output_path, voice))
        if os.path.exists(output_path):
            return output_path
    except Exception as e:
        print(f"  [Narrator] edge-tts failed ({e}), trying ionrouter.io...")

    # Fallback: ionrouter.io
    try:
        resp = requests.post(
            "https://ionrouter.io/v1/audio/speech",
            json={"model": "tts-1", "input": text, "voice": "alloy"},
            headers={"Authorization": f"Bearer {IONROUTER_API_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return output_path
    except Exception as e:
        print(f"  [Narrator] ionrouter.io failed ({e}), skipping narration")
        return ""
