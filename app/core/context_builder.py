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
    def __init__(self, runtime_project: ProjectRuntime, max_target_files: int | None = None):
        self.runtime_project = runtime_project
        self.context_rules = runtime_project.profile.context_rules if isinstance(runtime_project.profile.context_rules, dict) else {}
        default_max = _positive_int(self.context_rules.get("max_target_files"), 5)
        self.max_target_files = max_target_files if max_target_files is not None else default_max

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
        task_limit = self._task_file_limit(task_type)
        explicit_files = _normalize_relative_files(payload)[:task_limit]
        if explicit_files:
            return explicit_files

        repo_root = self.runtime_project.target_repo
        if not repo_root:
            return []

        root = Path(repo_root).resolve()
        if not root.exists() or not root.is_dir():
            return []

        profile_queries = self._task_queries(task_type)
        query = str(payload.get("query") or "").strip() or (profile_queries[0] if profile_queries else "")
        selection_objective = objective
        if profile_queries:
            selection_objective = objective + " " + " ".join(profile_queries)
        ranked = auto_select_python_files(
            root=root,
            task_type=task_type,
            objective=selection_objective,
            query=query,
            limit=task_limit,
            task_limit_override=task_limit,
        )
        selected = [item.file for item in ranked]
        return self._merge_pinned_files(task_type=task_type, selected=selected, task_limit=task_limit, root=root)

    def _append_document(self, parts: list[str], sections: list[str], section_name: str, path: Path) -> None:
        content = _safe_read(path)
        if not content:
            return
        sections.append(section_name)
        parts.append(f"## {section_name}\n{content}")

    def _prompt_name_for_task(self, task_type: str) -> str | None:
        task_overrides = self.runtime_project.profile.task_prompt_overrides
        if isinstance(task_overrides, dict):
            overridden = task_overrides.get(task_type)
            if isinstance(overridden, str) and overridden.strip():
                return overridden.strip()
        if task_type in {"review-snippet", "review-diff", "review-file"}:
            return "micro_reviewer"
        if task_type in {"compare-options", "final-decision"}:
            return "arbiter"
        return "repo_worker"

    def _task_file_limit(self, task_type: str) -> int:
        task_limits = self.context_rules.get("task_file_limits", {})
        if not isinstance(task_limits, dict):
            return self.max_target_files
        task_limit = _positive_int(task_limits.get(task_type), self.max_target_files)
        return min(self.max_target_files, task_limit)

    def _task_queries(self, task_type: str) -> list[str]:
        task_queries = self.context_rules.get("task_queries", {})
        if not isinstance(task_queries, dict):
            return []
        raw = task_queries.get(task_type, [])
        if not isinstance(raw, list):
            return []
        queries: list[str] = []
        seen = set()
        for item in raw:
            if not isinstance(item, str):
                continue
            query = item.strip()
            if not query or query in seen:
                continue
            seen.add(query)
            queries.append(query)
        return queries

    def _merge_pinned_files(self, task_type: str, selected: list[str], task_limit: int, root: Path) -> list[str]:
        pinned_by_task = self.context_rules.get("pinned_files_by_task", {})
        if not isinstance(pinned_by_task, dict):
            return selected[:task_limit]
        raw_pinned = pinned_by_task.get(task_type, [])
        if not isinstance(raw_pinned, list):
            return selected[:task_limit]

        merged: list[str] = []
        seen = set()

        for item in raw_pinned:
            if not isinstance(item, str):
                continue
            relative = item.strip()
            if not relative:
                continue
            candidate = (root / relative).resolve()
            if not candidate.exists() or not candidate.is_file():
                continue
            if not str(candidate).startswith(str(root.resolve())):
                continue
            if relative in seen:
                continue
            seen.add(relative)
            merged.append(relative)
            if len(merged) >= task_limit:
                return merged

        for item in selected:
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
            if len(merged) >= task_limit:
                break

        return merged


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed <= 0:
        return default
    return parsed
