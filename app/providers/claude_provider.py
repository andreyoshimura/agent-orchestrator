import json
from urllib import error, request as urllib_request

from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class ClaudeProvider(BaseProvider):
    name = "claude"

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

        url = self.settings.api_base or "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model": self.settings.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": request.prompt}],
        }).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=payload,
            headers={
                "x-api-key": self.settings.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
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

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": f"invalid_response_json:{exc.msg}",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        if not isinstance(data, dict):
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:top_level_not_object",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        if "content" not in data:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:missing_content",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        content = data.get("content", [])
        if not isinstance(content, list):
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:content_not_list",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        output_text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                output_text_parts.append(str(item.get("text", "")))

        return ProviderResponse(
            provider=self.name,
            status="completed",
            output={
                "mode": "live",
                "model": self.settings.model,
                "response_id": data.get("id"),
                "output_text": "\n".join(part for part in output_text_parts if part).strip(),
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
