from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class GeminiProvider(BaseProvider):
    name = "gemini"

    def _run(self, request: ProviderRequest) -> ProviderResponse:
        return self._stub_response(request)
