"""
Screenplay Agent — wraps ViMax's Screenwriter for CineAgent.
Uses free LLM providers (OpenRouter/Groq/DeepSeek).
"""

import json
import os
import asyncio
from core.llm_providers import get_chat_model
from agents.vimax.screenwriter import Screenwriter


async def write_screenplay_async(idea: str, user_requirement: str = "3 cinematic scenes, short film style") -> dict:
    """Use ViMax's Screenwriter to develop story + write script."""
    chat_model = get_chat_model()
    writer = Screenwriter(chat_model=chat_model)

    print(f"[Screenplay Agent] Developing story from idea...")
    story = await writer.develop_story(idea=idea, user_requirement=user_requirement)

    print(f"[Screenplay Agent] Writing script from story...")
    scenes = await writer.write_script_based_on_story(story=story, user_requirement=user_requirement)

    # Build structured screenplay dict
    screenplay = {
        "title": idea[:50].strip(),
        "story": story,
        "scenes": [
            {
                "scene_number": i + 1,
                "script": scene,
                "seedance_prompt": _script_to_seedance_prompt(scene),
                "action": scene[:200],
                "dialogue": "",
            }
            for i, scene in enumerate(scenes[:3])  # max 3 scenes
        ],
    }
    print(f"[Screenplay Agent] Done — {len(screenplay['scenes'])} scenes")
    return screenplay


def _script_to_seedance_prompt(script: str) -> str:
    """Convert a scene script to a Seedance 2.0 video prompt."""
    # Take first 150 chars of script as base, add cinematic style
    base = script[:150].replace("\n", " ").strip()
    return f"{base} Cinematic style, dramatic lighting, photorealistic, 4K, film grain, shallow depth of field."


def write_screenplay(idea: str) -> dict:
    """Sync wrapper."""
    return asyncio.run(write_screenplay_async(idea))
