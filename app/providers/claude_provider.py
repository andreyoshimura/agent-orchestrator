from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ProviderResponse:
    provider: str
    status: str
    output: Dict[str, Any]


class ClaudeProvider:
    name = "claude"

    def run(self, prompt: str, metadata: Dict[str, Any] | None = None) -> ProviderResponse:
        return ProviderResponse(
            provider=self.name,
            status="stub",
            output={"prompt_length": len(prompt), "metadata": metadata or {}},
        )
