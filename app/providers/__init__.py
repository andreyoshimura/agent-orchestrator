from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse
from app.providers.claude_provider import ClaudeProvider
from app.providers.config import ProviderSettings
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.openrouter_provider import OpenRouterProvider


PROVIDER_REGISTRY = {
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider,
}


def _resolve_provider_class(provider_type: str):
    provider_cls = PROVIDER_REGISTRY.get(provider_type)
    if provider_cls is not None:
        return provider_cls

    base_type = provider_type.split("_", 1)[0]
    if base_type != provider_type:
        return PROVIDER_REGISTRY.get(base_type)

    return None


def get_provider(name: str, settings: ProviderSettings) -> BaseProvider:
    provider_type = settings.provider_type or name
    provider_cls = _resolve_provider_class(provider_type)
    if provider_cls is None:
        raise KeyError(f"unknown provider type: {provider_type} (provider name: {name})")
    return provider_cls(settings)
