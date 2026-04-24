import hashlib
import json
import os
from pathlib import Path
import tempfile
import time


class CacheStore:
    def __init__(self, base_dir: str = "var/cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "_index.json"

    def path_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.base_dir / f"{digest}.txt"

    def get(self, key: str) -> str | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def set(self, key: str, value: str) -> None:
        path = self.path_for(key)
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(self.base_dir),
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = handle.name
            os.replace(temp_path, path)
            self._update_index(key)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def count(self) -> int:
        return sum(1 for _ in self.base_dir.glob("*.txt"))

    def list_entries(self, prefix: str = "", limit: int = 50) -> list[dict]:
        index = self._load_index()
        entries: list[dict] = []
        for digest, metadata in index.items():
            if not isinstance(metadata, dict):
                continue
            key = metadata.get("key")
            updated_at = metadata.get("updated_at")
            if not isinstance(key, str) or not isinstance(updated_at, (int, float)):
                continue
            if prefix and not key.startswith(prefix):
                continue
            entries.append({
                "digest": digest,
                "key": key,
                "updated_at": float(updated_at),
            })
        entries.sort(key=lambda item: item["updated_at"], reverse=True)
        return entries[:limit]

    def _update_index(self, key: str) -> None:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        index = self._load_index()
        index[digest] = {
            "key": key,
            "updated_at": time.time(),
        }
        self._save_index(index)

    def _load_index(self) -> dict:
        if not self.index_path.exists():
            return {}
        try:
            loaded = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
        if not isinstance(loaded, dict):
            return {}
        return loaded

    def _save_index(self, index: dict) -> None:
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=str(self.base_dir),
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(json.dumps(index, ensure_ascii=False, indent=2))
                handle.flush()
                os.fsync(handle.fileno())
                temp_path = handle.name
            os.replace(temp_path, self.index_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
