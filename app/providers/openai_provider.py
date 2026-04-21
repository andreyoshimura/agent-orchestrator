import json
from urllib import error, request as urllib_request

from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class OpenAIProvider(BaseProvider):
    name = "openai"

    def _run(self, request: ProviderRequest) -> ProviderResponse:
        if not self.settings.ready_for_live_execution:
            missing_fields = []
            if not self.settings.model.strip():
                missing_fields.append("model")
            if not self.settings.api_key.strip():
                missing_fields.append("api_key")
            if missing_fields:
                return ProviderResponse(
                    provider=self.name,
                    status="stub",
                    output={
                        "prompt_length": len(request.prompt),
                        "metadata": request.metadata,
                        "mode": "stub",
                        "model": self.settings.model,
                        "reason": f"missing_{'_'.join(missing_fields)}",
                        "failure_type": "configuration",
                    },
                )
            return self._stub_response(request)

        url = self.settings.api_base or "https://api.openai.com/v1/responses"
        payload = json.dumps({
            "model": self.settings.model,
            "input": request.prompt,
        }).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=30) as response_handle:
                raw = response_handle.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": f"http_error:{exc.code}",
                    "failure_type": _http_failure_type(exc.code),
                    "body_preview": body[:1000],
                },
            )
        except error.URLError as exc:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": f"network_error:{exc.reason}",
                    "failure_type": "network",
                },
            )

        data = json.loads(raw)
        return ProviderResponse(
            provider=self.name,
            status="completed",
            output={
                "mode": "live",
                "model": self.settings.model,
                "response_id": data.get("id"),
                "output_text": data.get("output_text", ""),
                "raw": data,
            },
        )


def _http_failure_type(status_code: int) -> str:
    if status_code == 429:
        return "rate_limit"
    if status_code in {401, 403}:
        return "authorization"
    if status_code in {400, 404, 422}:
        return "invalid_request"
    return "temporary"
