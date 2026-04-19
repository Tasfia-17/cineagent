"""
ShopReel — Product Script Agent
Analyzes a product and generates 5 platform-specific ad scripts using Pollinations LLM.
Platforms: TikTok, Instagram Reels, YouTube Short, Amazon listing, Product page
"""

import json
import asyncio
from core.llm_providers import get_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

PLATFORMS = {
    "tiktok":    {"aspect": "9:16",  "duration": 15, "style": "viral hook, fast cuts, trending audio, Gen-Z tone"},
    "reels":     {"aspect": "9:16",  "duration": 15, "style": "aesthetic, lifestyle, aspirational, millennial tone"},
    "youtube":   {"aspect": "16:9",  "duration": 30, "style": "informative, benefit-focused, clear CTA"},
    "amazon":    {"aspect": "16:9",  "duration": 30, "style": "product features, trust-building, professional"},
    "product_page": {"aspect": "1:1", "duration": 10, "style": "clean, minimal, product hero shot"},
}

SYSTEM_PROMPT = """You are an expert ecommerce video ad copywriter. 
Given a product, generate platform-optimized video scripts.
Return ONLY valid JSON."""

SCRIPT_PROMPT = """Product: {title}
Description: {description}
Price: {price}
Brand: {vendor}
Image available: {has_image}

Generate 5 video ad scripts, one per platform. Return JSON:
{{
  "tiktok": {{
    "hook": "First 3 seconds (must stop the scroll)",
    "script": "Full 15-second script with voiceover text",
    "seedance_prompt": "Seedance 2.0 video prompt (cinematic, 9:16, product showcase)",
    "seedream_prompt": "Seedream 5.0 keyframe image prompt"
  }},
  "reels": {{ same structure }},
  "youtube": {{ same structure, 30 seconds }},
  "amazon": {{ same structure, 30 seconds }},
  "product_page": {{ same structure, 10 seconds }}
}}"""


async def generate_product_scripts(product: dict) -> dict:
    """Generate 5 platform-specific scripts for a product."""
    chat_model = get_chat_model()

    title = product.get("title", "Product")
    description = product.get("body_html", product.get("description", ""))[:300]
    price = product.get("variants", [{}])[0].get("price", "N/A") if product.get("variants") else "N/A"
    vendor = product.get("vendor", "")
    has_image = bool(product.get("images") or product.get("image_url"))

    response = await chat_model.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=SCRIPT_PROMPT.format(
            title=title, description=description,
            price=price, vendor=vendor, has_image=has_image,
        )),
    ])

    try:
        scripts = json.loads(response.content)
    except Exception:
        # Extract JSON from response if wrapped in markdown
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        scripts = json.loads(match.group()) if match else {}

    print(f"[Script Agent] Generated scripts for {len(scripts)} platforms")
    return scripts
