from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.core.context_manager import ContextManager
from app.core.file_selector import auto_select_python_files
from app.core.project_loader import ProjectRuntime


def _safe_read(path: Path, max_chars: int = 12000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    return text[:max_chars]


def _normalize_relative_files(payload: dict[str, Any]) -> list[str]:
    raw_files: list[str] = []

    single_file = payload.get("file")
    if isinstance(single_file, str) and single_file.strip():
        raw_files.append(single_file.strip())

    many_files = payload.get("files")
    if isinstance(many_files, Iterable) and not isinstance(many_files, (str, bytes, dict)):
        for item in many_files:
            if isinstance(item, str) and item.strip():
                raw_files.append(item.strip())

    seen = set()
    normalized = []
    for item in raw_files:
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


@dataclass(frozen=True)
class ContextBundle:
    project_id: str
    task_type: str
    objective: str
    files: list[str]
    prompt_name: str | None
    prompt_text: str
    context_text: str
    sections: list[str]


class ContextBuilder:
    def __init__(self, runtime_project: ProjectRuntime, max_target_files: int = 5):
        self.runtime_project = runtime_project
        self.max_target_files = max_target_files

    def build(self, task_type: str, payload: dict[str, Any]) -> ContextBundle:
        profile = self.runtime_project.profile
        objective = str(payload.get("objective") or f"Handle task '{task_type}' safely and with minimal context.")
        target_files = self._resolve_target_files(task_type=task_type, payload=payload, objective=objective)
        prompt_name = self._prompt_name_for_task(task_type)
        prompt_text = ""

        sections: list[str] = []
        parts: list[str] = []

        self._append_document(parts, sections, "GLOBAL_BOOTSTRAP", Path("CODEX_BOOTSTRAP.md"))
        self._append_document(parts, sections, "PROJECT_BOOTSTRAP", profile.bootstrap_path)
        self._append_document(parts, sections, "PROJECT_AGENT_CONTEXT", profile.agent_context_path)

        for memory_file in profile.memory_files:
            self._append_document(parts, sections, f"PROJECT_MEMORY::{Path(memory_file).name}", Path(memory_file))

        if prompt_name:
            prompt_path = profile.prompt_files.get(prompt_name)
            if prompt_path:
                prompt_text = _safe_read(Path(prompt_path), max_chars=8000)
                self._append_document(parts, sections, f"PROJECT_PROMPT::{prompt_name}", Path(prompt_path))

        repo_root = self.runtime_project.target_repo
        if repo_root:
            ctx = ContextManager(repo_root=repo_root, max_files=self.max_target_files)
            for relative_path in target_files:
                try:
                    content = ctx.read_file(relative_path, max_chars=12000)
                except FileNotFoundError:
                    continue
                sections.append(f"TARGET_FILE::{relative_path}")
                parts.append(f"## TARGET_FILE::{relative_path}\n{content}")

        header = [
            f"task_type: {task_type}",
            f"project_id: {profile.project_id}",
            f"display_name: {profile.display_name}",
            f"agent_profile: {profile.agent_profile}",
            f"default_mode: {profile.default_mode}",
            f"write_enabled: {self.runtime_project.write_enabled}",
            f"target_repo_configured: {bool(repo_root)}",
            f"objective: {objective}",
        ]

        context_text = "\n".join(header) + "\n\n" + "\n\n".join(parts)
        return ContextBundle(
            project_id=profile.project_id,
            task_type=task_type,
            objective=objective,
            files=target_files,
            prompt_name=prompt_name,
            prompt_text=prompt_text,
            context_text=context_text.strip(),
            sections=sections,
        )

    def _resolve_target_files(self, task_type: str, payload: dict[str, Any], objective: str) -> list[str]:
        explicit_files = _normalize_relative_files(payload)[: self.max_target_files]
        if explicit_files:
            return explicit_files

        repo_root = self.runtime_project.target_repo
        if not repo_root:
            return []

        root = Path(repo_root).resolve()
        if not root.exists() or not root.is_dir():
            return []

        query = str(payload.get("query") or "").strip()
        ranked = auto_select_python_files(
            root=root,
            task_type=task_type,
            objective=objective,
            query=query,
            limit=self.max_target_files,
        )
        return [item.file for item in ranked]

    def _append_document(self, parts: list[str], sections: list[str], section_name: str, path: Path) -> None:
        content = _safe_read(path)
        if not content:
            return
        sections.append(section_name)
        parts.append(f"## {section_name}\n{content}")

    def _prompt_name_for_task(self, task_type: str) -> str | None:
        if task_type in {"review-snippet", "review-diff", "review-file"}:
            return "micro_reviewer"
        if task_type in {"compare-options", "final-decision"}:
            return "arbiter"
        return "repo_worker"
