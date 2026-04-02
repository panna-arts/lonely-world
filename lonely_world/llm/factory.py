"""Factory for creating LLM providers."""

from lonely_world.llm.anthropic_provider import AnthropicProvider
from lonely_world.llm.base import LLMProvider
from lonely_world.llm.openai_provider import OpenAIProvider


def create_provider(
    provider: str, api_key: str, base_url: str = "", model: str = ""
) -> LLMProvider:
    provider = provider.lower().strip()
    if provider in ("openai", "ollama", "vllm", "local"):
        return OpenAIProvider(api_key=api_key, base_url=base_url, model=model)
    if provider in ("anthropic", "claude"):
        return AnthropicProvider(api_key=api_key, base_url=base_url, model=model)
    raise ValueError(f"Unsupported LLM provider: {provider}")
