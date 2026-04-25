import json
from urllib import error, request as urllib_request

from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class OpenRouterProvider(BaseProvider):
    name = "openrouter"

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

        url = self.settings.api_base or "https://openrouter.ai/api/v1/chat/completions"
        payload = json.dumps({
            "model": self.settings.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": _max_tokens(request.metadata.get("provider_max_tokens", 2048)),
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
        if "choices" not in data:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:missing_choices",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )

        choices = data.get("choices", [])
        if not isinstance(choices, list):
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:choices_not_list",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )

        output_text = _extract_output_text(choices)

        if not output_text:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:missing_choice_content",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )

        return ProviderResponse(
            provider=self.name,
            status="completed",
            output={
                "mode": "live",
                "model": self.settings.model,
                "response_id": data.get("id"),
                "output_text": output_text,
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


def _timeout_seconds(raw_value: object, default: int = 30) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


def _max_tokens(raw_value: object, default: int = 2048) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


def _extract_output_text(choices: list[object]) -> str:
    for choice in choices:
        if not isinstance(choice, dict):
            continue

        message = choice.get("message", {})
        if isinstance(message, dict):
            content = message.get("content")
            normalized = _normalize_content(content)
            if normalized:
                return normalized

        text_value = choice.get("text")
        if isinstance(text_value, str) and text_value.strip():
            return text_value.strip()

    return ""


def _normalize_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            text = item.strip()
            if text:
                parts.append(text)
            continue

        if not isinstance(item, dict):
            continue

        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
            continue

        # Some providers return nested text payloads under a data object.
        data = item.get("data")
        if isinstance(data, dict):
            nested_text = data.get("text")
            if isinstance(nested_text, str) and nested_text.strip():
                parts.append(nested_text.strip())

    return "\n".join(parts).strip()
