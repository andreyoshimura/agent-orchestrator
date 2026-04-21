from typing import Any, Dict


RETRYABLE_FAILURE_TYPES = {"temporary", "rate_limit", "network"}
FALLBACK_FAILURE_TYPES = {"temporary", "rate_limit", "network", "configuration", "provider_unavailable"}
TERMINAL_FAILURE_TYPES = {"invalid_request", "authorization", "fatal"}


def classify_provider_failure(status: object, output: Dict[str, Any] | None = None) -> str:
    normalized_status = str(status)
    payload = output or {}

    if normalized_status in {"completed", "stub"}:
        return "success"
    if normalized_status in {"disabled", "skipped"}:
        return "provider_unavailable"

    explicit_type = str(payload.get("failure_type", "")).strip()
    if explicit_type:
        return explicit_type

    reason = str(payload.get("reason", "")).lower()
    if reason.startswith("network_error"):
        return "network"
    if reason.startswith("http_error:429"):
        return "rate_limit"
    if reason.startswith("http_error:401") or reason.startswith("http_error:403"):
        return "authorization"
    if reason.startswith("http_error:400") or reason.startswith("http_error:404") or reason.startswith("http_error:422"):
        return "invalid_request"
    if "configuration" in reason or "missing_api_key" in reason or "missing_model" in reason:
        return "configuration"
    return "temporary"


def should_try_fallback(status: object, output: Dict[str, Any] | None = None, fallback_on: list[str] | None = None) -> bool:
    failure_type = classify_provider_failure(status, output)
    allowed_failures = fallback_on or list(FALLBACK_FAILURE_TYPES)
    return failure_type in allowed_failures


def should_accept_provider_result(status: object) -> bool:
    return str(status) in {"completed", "stub"}


def should_retry_provider(status: object, output: Dict[str, Any] | None = None) -> bool:
    failure_type = classify_provider_failure(status, output)
    return failure_type in RETRYABLE_FAILURE_TYPES
