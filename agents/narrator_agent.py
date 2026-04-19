"""
Narrator Agent — generates voiceover narration for each scene using ionrouter.io TTS.
Falls back to gTTS if ionrouter is unavailable.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

IONROUTER_API_KEY = os.getenv("IONROUTER_API_KEY", "sk-bb3d84f1cea67cd03ef7e1355f51e184837a72cfd321fbbb")
IONROUTER_BASE_URL = "https://ionrouter.io/v1"


def generate_narration(text: str, output_path: str, voice: str = "alloy") -> str:
    """
    Generate TTS narration via ionrouter.io (OpenAI-compatible TTS endpoint).
    Returns path to audio file.
    """
    print(f"  [Narrator Agent] Generating narration: '{text[:50]}...'")

    try:
        headers = {
            "Authorization": f"Bearer {IONROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice,
            "response_format": "mp3",
        }
        resp = requests.post(
            f"{IONROUTER_BASE_URL}/audio/speech",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)
        print(f"  [Narrator Agent] Audio saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"  [Narrator Agent] ionrouter failed ({e}), falling back to gTTS")
        return _gtts_fallback(text, output_path)


def _gtts_fallback(text: str, output_path: str) -> str:
    """Fallback TTS using gTTS (no API key needed)."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        mp3_path = output_path.replace(".wav", ".mp3")
        tts.save(mp3_path)
        return mp3_path
    except ImportError:
        print("  [Narrator Agent] gTTS not installed, skipping narration")
        return ""
