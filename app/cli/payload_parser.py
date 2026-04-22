import json
from json import JSONDecodeError
from typing import Any


def parse_json_payload(raw_payload: str) -> tuple[dict[str, Any] | None, str | None]:
    if not raw_payload:
        return {}, None

    try:
        payload = json.loads(raw_payload)
    except JSONDecodeError as exc:
        return None, f"invalid json payload: {exc.msg}"

    if not isinstance(payload, dict):
        return None, "json payload must be an object"

    return payload, None
