from pathlib import Path
from typing import Iterable, List


class ContextManager:
    def __init__(self, max_files: int = 5):
        self.max_files = max_files

    def select_files(self, files: Iterable[str]) -> List[str]:
        selected = []
        for file_path in files:
            selected.append(str(file_path))
            if len(selected) >= self.max_files:
                break
        return selected

    def read_files(self, files: Iterable[str]) -> str:
        chunks: List[str] = []
        for file_path in self.select_files(files):
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="ignore")
            chunks.append(f"## FILE: {path}\n{text[:8000]}")
        return "\n\n".join(chunks)
