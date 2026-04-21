import json
from pathlib import Path
from typing import Any, Dict


class StateStore:
    def __init__(self, base_dir: str = "var/state"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.base_dir / f"{key}.json"

    def path_for(self, key: str) -> Path:
        return self._path(key)

    def load(self, key: str) -> Dict[str, Any]:
        path = self._path(key)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save(self, key: str, payload: Dict[str, Any]) -> None:
        path = self._path(key)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_keys(self, prefix: str = "") -> list[str]:
        keys: list[str] = []
        for path in sorted(self.base_dir.glob("*.json")):
            key = path.stem
            if prefix and not key.startswith(prefix):
                continue
            keys.append(key)
        return keys
