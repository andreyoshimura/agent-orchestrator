import json
from pathlib import Path
from typing import Any, Dict


class StateStore:
    def __init__(self, base_dir: str = "var/state"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.base_dir / f"{key}.json"

    def load(self, key: str) -> Dict[str, Any]:
        path = self._path(key)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, key: str, payload: Dict[str, Any]) -> None:
        path = self._path(key)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
