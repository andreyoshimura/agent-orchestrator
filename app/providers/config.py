import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


def _load_yaml(path: str) -> Dict[str, Any]:
    loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return loaded or {}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    enabled: bool
    model: str
    api_key: str
    api_base: str

    @property
    def ready_for_live_execution(self) -> bool:
        return self.enabled and bool(self.model.strip()) and bool(self.api_key.strip())


def load_provider_settings(config_path: str = "config/providers.yaml") -> Dict[str, ProviderSettings]:
    config = _load_yaml(config_path).get("providers", {})
    settings: Dict[str, ProviderSettings] = {}

    for provider_name, details in config.items():
        enabled_env = str(details.get("enabled_env", ""))
        model_env = str(details.get("model_env", ""))
        api_key_env = str(details.get("api_key_env", ""))
        api_base_env = str(details.get("api_base_env", ""))

        settings[provider_name] = ProviderSettings(
            name=provider_name,
            enabled=_env_bool(enabled_env, True),
            model=os.getenv(model_env, ""),
            api_key=os.getenv(api_key_env, ""),
            api_base=os.getenv(api_base_env, "").strip(),
        )

    return settings
