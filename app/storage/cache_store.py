import hashlib
from pathlib import Path


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
        path.write_text(value, encoding="utf-8")

    def count(self) -> int:
        return sum(1 for _ in self.base_dir.glob("*.txt"))
