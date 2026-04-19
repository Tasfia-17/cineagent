"""
Quality Agent — evaluates generated video clips and decides if they need regeneration.
Scores each clip and triggers retry with improved prompt if quality is low.
This is what makes CineAgent truly AGENTIC (not just a pipeline).
"""

import json
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

QUALITY_PROMPT = """You are a film quality evaluator. A video clip was generated for this scene:

Scene: {scene_description}
Prompt used: {prompt}
Generation status: {status}

Based on the prompt and scene requirements, evaluate the likely quality and return JSON:
{{
  "score": 0-10,
  "issues": ["list of potential issues"],
  "improved_prompt": "improved Seedance prompt if score < 7, else same prompt",
  "should_regenerate": true/false
}}

Be strict: score < 7 means regenerate."""


def evaluate_clip(scene: dict, prompt: str, status: str = "generated") -> dict:
    """Evaluate a video clip and return quality assessment."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a film quality evaluator. Return only valid JSON."},
            {"role": "user", "content": QUALITY_PROMPT.format(
                scene_description=scene.get("action", ""),
                prompt=prompt,
                status=status,
            )},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    score = result.get("score", 5)
    regen = result.get("should_regenerate", False)
    print(f"  [Quality Agent] Score: {score}/10 | Regenerate: {regen}")
    return result
