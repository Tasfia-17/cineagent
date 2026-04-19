"""
LLM provider setup for CineAgent.
Default: Pollinations.ai — completely free, no API key required.
Fallback: OpenRouter, Groq, DeepSeek, OpenAI.
"""

import os
from langchain.chat_models import init_chat_model

PROVIDERS = {
    # No API key needed — works out of the box
    "pollinations": {
        "model": "openai",           # GPT-5.4 Nano via Pollinations
        "base_url": "https://gen.pollinations.ai",
        "env_key": "POLLINATIONS_API_KEY",  # optional
        "note": "Free, no key needed — pollinations.ai",
    },
    "groq": {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "note": "Free tier — console.groq.com",
    },
    "openrouter": {
        "model": "google/gemini-2.0-flash-exp:free",
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "note": "Free models — openrouter.ai",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "note": "Cheap — platform.deepseek.com",
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
    Return a LangChain chat model.
    Defaults to Pollinations (free, no key needed).
    Auto-detects other providers from environment variables.
    """
    # Use explicitly set provider
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "pollinations")

    # If not pollinations, check for API key
    if provider != "pollinations":
        for name, cfg in PROVIDERS.items():
            if name == "pollinations":
                continue
            if os.getenv(cfg["env_key"]):
                provider = name
                break

    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["env_key"], "dummy")  # Pollinations works with any key
    print(f"[LLM] Provider: {provider} | Model: {cfg['model']}")

    return init_chat_model(
        model=cfg["model"],
        model_provider="openai",
        base_url=cfg["base_url"],
        api_key=api_key,
    )
