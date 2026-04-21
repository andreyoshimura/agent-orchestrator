from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse
from app.providers.claude_provider import ClaudeProvider
from app.providers.config import ProviderSettings
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider


PROVIDER_REGISTRY = {
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


def get_provider(name: str, settings: ProviderSettings) -> BaseProvider:
    provider_cls = PROVIDER_REGISTRY.get(name)
    if provider_cls is None:
        raise KeyError(f"unknown provider: {name}")
    return provider_cls(settings)
