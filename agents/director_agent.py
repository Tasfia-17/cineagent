"""
Director Agent — reviews screenplay and enhances Seedance prompts for maximum visual quality.
Adds camera movements, lighting, cinematography style to each scene prompt.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

DIRECTOR_PROMPT = """You are a world-class film director. Review this screenplay and enhance each scene's Seedance video generation prompt.

For each scene, improve the seedance_prompt to include:
- Specific camera movement (dolly in, crane shot, tracking shot, etc.)
- Lighting style (golden hour, dramatic shadows, soft diffused, etc.)
- Visual style (cinematic, photorealistic, film grain, color grade)
- Motion and atmosphere details

Keep prompts under 100 words. Return the same JSON structure with enhanced seedance_prompts.

Screenplay:
{screenplay}"""


def direct_screenplay(screenplay: dict) -> dict:
    """Enhance screenplay prompts with cinematic direction."""
    print(f"[Director Agent] Enhancing {len(screenplay['scenes'])} scenes cinematically")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a film director. Return only valid JSON with the same structure."},
            {"role": "user", "content": DIRECTOR_PROMPT.format(screenplay=json.dumps(screenplay, indent=2))},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    directed = json.loads(response.choices[0].message.content)
    print(f"[Director Agent] Direction complete for '{directed.get('title', screenplay['title'])}'")
    return directed
