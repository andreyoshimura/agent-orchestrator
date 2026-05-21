import json
from typing import Dict
from urllib import error, request as urllib_request

from app.providers.base import BaseProvider, ProviderRequest, ProviderResponse


class OpenAIProvider(BaseProvider):
    name = "openai"

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
        if "output_text" not in data:
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:missing_output_text",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        if not isinstance(data.get("output_text"), str):
            return ProviderResponse(
                provider=self.name,
                status="error",
                output={
                    "mode": "live",
                    "model": self.settings.model,
                    "reason": "invalid_response_shape:output_text_not_string",
                    "failure_type": "temporary",
                    "body_preview": raw[:1000],
                },
            )
        usage_metrics = _extract_usage_metrics(data.get("usage"))

        output: Dict[str, object] = {
            "mode": "live",
            "model": self.settings.model,
            "response_id": data.get("id"),
            "output_text": data.get("output_text", ""),
            "raw": data,
        }
        if usage_metrics is not None:
            output["usage"] = usage_metrics

        return ProviderResponse(
            provider=self.name,
            status="completed",
            output=output,
        )


def _extract_usage_metrics(usage: object) -> Dict[str, int] | None:
    if not isinstance(usage, dict):
        return None
    prompt_tokens = _coerce_int(
        usage.get("input_tokens", usage.get("prompt_tokens"))
    )
    completion_tokens = _coerce_int(
        usage.get("output_tokens", usage.get("completion_tokens"))
    )
    total_tokens_raw = usage.get("total_tokens")
    total_tokens = _coerce_int(total_tokens_raw) if total_tokens_raw is not None else prompt_tokens + completion_tokens
    if prompt_tokens == 0 and completion_tokens == 0 and total_tokens == 0:
        return None
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def _coerce_int(raw_value: object) -> int:
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return 0


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


def _timeout_seconds(raw_value: object, default: int = 30) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value
