import hashlib
import os
from pathlib import Path
import tempfile


class CacheStore:
    def __init__(self, base_dir: str = "var/cache"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

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
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def count(self) -> int:
        return sum(1 for _ in self.base_dir.glob("*.txt"))
