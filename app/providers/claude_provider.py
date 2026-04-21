from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class ClaudeProvider(BaseProvider):
    name = "claude"

    def _run(self, request: ProviderRequest) -> ProviderResponse:
        return self._stub_response(request)
