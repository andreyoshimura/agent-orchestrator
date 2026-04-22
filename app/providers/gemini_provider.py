import json
from urllib import error, parse as urllib_parse, request as urllib_request

from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class GeminiProvider(BaseProvider):
    name = "gemini"

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

        base_url = self.settings.api_base or "https://generativelanguage.googleapis.com/v1beta"
        endpoint = f"{base_url}/models/{self.settings.model}:generateContent"
        url = f"{endpoint}?{urllib_parse.urlencode({'key': self.settings.api_key})}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": request.prompt}]}],
        }).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
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
        output_text_parts = []
        candidates = data.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
            for part in content.get("parts", []):
                if isinstance(part, dict):
                    text = str(part.get("text", ""))
                    if text:
                        output_text_parts.append(text)

        return ProviderResponse(
            provider=self.name,
            status="completed",
            output={
                "mode": "live",
                "model": self.settings.model,
                "output_text": "\n".join(output_text_parts).strip(),
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
