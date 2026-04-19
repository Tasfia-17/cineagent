"""
Free LLM provider setup for CineAgent.
Supports: OpenRouter (free models), Groq (free tier), DeepSeek (cheap).
No OpenAI key needed.
"""

import os
from langchain.chat_models import init_chat_model

# ── Free provider configs ──────────────────────────────────────────────────

FREE_PROVIDERS = {
    "openrouter": {
        "model": "google/gemini-2.0-flash-exp:free",
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "note": "Free tier at openrouter.ai — no credit card needed for free models",
    },
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "note": "Free tier at console.groq.com — very fast inference",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "note": "~$0.001/1K tokens — cheapest paid option",
    },
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
        "note": "Standard OpenAI",
    },
}


def get_chat_model(provider: str = None):
    """
    Return a LangChain chat model using the first available free provider.
    Auto-detects from environment variables if provider not specified.
    """
    if provider is None:
        # Auto-detect: try each provider in order
        for name, cfg in FREE_PROVIDERS.items():
            key = os.getenv(cfg["env_key"])
            if key:
                provider = name
                print(f"[LLM] Using provider: {name} ({cfg['model']})")
                break

    if provider is None:
        raise ValueError(
            "No LLM API key found. Set one of:\n"
            + "\n".join(f"  {cfg['env_key']} — {cfg['note']}" for cfg in FREE_PROVIDERS.values())
        )

    cfg = FREE_PROVIDERS[provider]
    api_key = os.getenv(cfg["env_key"])

    return init_chat_model(
        model=cfg["model"],
        model_provider="openai",
        base_url=cfg["base_url"],
        api_key=api_key,
    )
