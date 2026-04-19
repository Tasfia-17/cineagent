"""
Screenplay Agent — turns a one-line idea into a structured 3-scene screenplay.
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

SCREENPLAY_PROMPT = """You are a cinematic screenplay writer. Given a one-line story idea, write a 3-scene short film screenplay.

Return ONLY valid JSON in this exact format:
{{
  "title": "Film title",
  "genre": "genre",
  "scenes": [
    {{
      "scene_number": 1,
      "setting": "Brief setting description",
      "action": "What happens visually (2-3 sentences)",
      "dialogue": "Character dialogue if any, or empty string",
      "mood": "emotional tone",
      "seedance_prompt": "Cinematic video generation prompt for Seedance 2.0 (50-80 words, vivid, specific camera movement, lighting, style)"
    }}
  ]
}}

Story idea: {idea}"""


def write_screenplay(idea: str) -> dict:
    """Generate a 3-scene screenplay from a story idea."""
    print(f"[Screenplay Agent] Writing screenplay for: {idea}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a cinematic screenplay writer. Return only valid JSON."},
            {"role": "user", "content": SCREENPLAY_PROMPT.format(idea=idea)},
        ],
        temperature=0.8,
        response_format={"type": "json_object"},
    )

    screenplay = json.loads(response.choices[0].message.content)
    print(f"[Screenplay Agent] Title: {screenplay['title']} | Scenes: {len(screenplay['scenes'])}")
    return screenplay
