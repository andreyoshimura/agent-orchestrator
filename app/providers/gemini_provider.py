import json
from urllib import error, parse as urllib_parse, request as urllib_request

from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class GeminiProvider(BaseProvider):
    name = "gemini"

    def _run(self, request: ProviderRequest) -> ProviderResponse:
        timeout_sec = _timeout_seconds(request.metadata.get("provider_timeout_sec", 30))
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
            "generationConfig": {"maxOutputTokens": _max_tokens(request.metadata.get("provider_max_tokens", 2048))},
        }).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=timeout_sec) as response_handle:
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
        if "candidates" not in data:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:missing_candidates",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        output_text_parts = []
        candidates = data.get("candidates", [])
        if not isinstance(candidates, list):
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:candidates_not_list",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
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
    if status_code == 402:
        return "insufficient_credits"
    if status_code in {401, 403}:
        return "authorization"
    if status_code in {400, 404, 422}:
        return "invalid_request"
    return "temporary"


def _max_tokens(raw_value: object, default: int = 2048) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


def _timeout_seconds(raw_value: object, default: int = 30) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value
