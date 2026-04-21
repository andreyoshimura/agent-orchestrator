from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from app.providers.config import ProviderSettings


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    status: str
    output: Dict[str, Any]


class BaseProvider(ABC):
    name = "provider"

    def __init__(self, settings: ProviderSettings):
        self.settings = settings

    def run(self, request: ProviderRequest) -> ProviderResponse:
        if not self.settings.enabled:
            return ProviderResponse(
                provider=self.name,
                status="disabled",
                output={
                    "reason": "provider disabled in configuration",
                    "failure_type": "provider_unavailable",
                },
            )
        return self._run(request)

    @abstractmethod
    def _run(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

    def _stub_response(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider=self.name,
            status="stub",
            output={
                "prompt_length": len(request.prompt),
                "metadata": request.metadata,
                "mode": "stub",
                "model": self.settings.model,
            },
        )
