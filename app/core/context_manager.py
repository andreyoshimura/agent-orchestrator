from pathlib import Path
from typing import Iterable, List


class ContextManager:
    def __init__(self, repo_root: str, max_files: int = 5):
        self.repo_root = Path(repo_root).resolve()
        self.max_files = max_files

    def select_files(self, files: Iterable[str]) -> List[str]:
        selected = []
        for file_path in files:
            selected.append(str(file_path))
            if len(selected) >= self.max_files:
                break
        return selected

    def resolve_path(self, relative_path: str) -> Path:
        return (self.repo_root / relative_path).resolve()

    def read_file(self, relative_path: str, max_chars: int = 8000) -> str:
        path = self.resolve_path(relative_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"file not found: {path}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        return text[:max_chars]

    def read_files(self, files: Iterable[str], max_chars_per_file: int = 8000) -> str:
        chunks: List[str] = []
        for relative_path in self.select_files(files):
            path = self.resolve_path(relative_path)
            if not path.exists() or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="ignore")
            chunks.append(f"## FILE: {relative_path}\n{text[:max_chars_per_file]}")
        return "\n\n".join(chunks)
