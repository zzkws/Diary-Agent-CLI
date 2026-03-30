from __future__ import annotations

from diary_agent.config import Settings
from diary_agent.llm.providers import AnthropicPlaceholderProvider, DeterministicProvider, GeminiProvider


def build_provider(settings: Settings):
    provider = settings.llm_provider.lower().strip()
    model = settings.llm_model

    if provider == "gemini":
        gemini = GeminiProvider(model=model, api_key=settings.gemini_api_key)
        if gemini.is_available():
            return gemini
        return DeterministicProvider()

    if provider == "anthropic":
        anthropic = AnthropicPlaceholderProvider(model=model, api_key=settings.anthropic_api_key)
        if anthropic.is_available():
            return anthropic
        return DeterministicProvider()

    return DeterministicProvider(model=model)
