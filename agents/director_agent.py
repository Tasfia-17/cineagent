"""
Director Agent — wraps ViMax's StoryboardArtist to enhance scene prompts.
Uses free LLM providers.
"""

import asyncio
from core.llm_providers import get_chat_model
from agents.vimax.storyboard_artist import StoryboardArtist
from interfaces.character import CharacterInScene


async def direct_screenplay_async(screenplay: dict) -> dict:
    """
    Use ViMax's StoryboardArtist to enhance each scene's Seedance prompt
    with proper cinematography: shot types, camera moves, lighting.
    """
    chat_model = get_chat_model()
    artist = StoryboardArtist(chat_model=chat_model)

    print(f"[Director Agent] Enhancing {len(screenplay['scenes'])} scenes with storyboard direction...")

    for scene in screenplay["scenes"]:
        try:
            storyboard = await artist.design_storyboard(
                script=scene["script"],
                characters=[],  # no pre-extracted characters for speed
                user_requirement="cinematic, dramatic lighting, Seedance 2.0 video generation style",
            )
            if storyboard:
                # Use first shot's visual description as the Seedance prompt
                first_shot = storyboard[0]
                scene["seedance_prompt"] = (
                    f"{first_shot.visual_desc} "
                    f"Cinematic, photorealistic, 4K, film grain."
                )
                scene["storyboard"] = [s.model_dump() for s in storyboard]
        except Exception as e:
            print(f"  [Director Agent] Scene {scene['scene_number']} storyboard failed ({e}), using script prompt")

    print(f"[Director Agent] Direction complete")
    return screenplay


def direct_screenplay(screenplay: dict) -> dict:
    """Sync wrapper."""
    return asyncio.run(direct_screenplay_async(screenplay))
