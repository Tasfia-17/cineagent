"""
Quality Agent — scores video clips and decides whether to regenerate.
Uses free LLM providers.
"""

import json
import asyncio
from core.llm_providers import get_chat_model

QUALITY_PROMPT = """You are a film quality evaluator. A video clip was generated for this scene.

Scene script: {script}
Seedance prompt used: {prompt}

Evaluate the likely quality and return JSON:
{{
  "score": <0-10>,
  "issues": ["list of potential issues"],
  "improved_prompt": "<improved Seedance 2.0 prompt if score < 7, else same prompt>",
  "should_regenerate": <true/false>
}}

Score < 7 = regenerate. Be strict about cinematic quality."""


def evaluate_clip(scene: dict, prompt: str) -> dict:
    """Evaluate a clip and return quality assessment with improved prompt if needed."""
    try:
        chat_model = get_chat_model()

        async def _eval():
            from langchain_core.messages import HumanMessage, SystemMessage
            response = await chat_model.ainvoke([
                SystemMessage(content="You are a film quality evaluator. Return only valid JSON."),
                HumanMessage(content=QUALITY_PROMPT.format(
                    script=scene.get("script", scene.get("action", ""))[:300],
                    prompt=prompt,
                )),
            ])
            return json.loads(response.content)

        result = asyncio.run(_eval())
        score = result.get("score", 7)
        print(f"  [Quality Agent] Score: {score}/10 | Regenerate: {result.get('should_regenerate', False)}")
        return result

    except Exception as e:
        print(f"  [Quality Agent] Evaluation failed ({e}), skipping")
        return {"score": 7, "should_regenerate": False, "improved_prompt": prompt}
