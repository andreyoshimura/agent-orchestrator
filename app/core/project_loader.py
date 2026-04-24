import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded or {}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_projects_root(projects_root: str | None = None) -> Path:
    configured = projects_root or os.getenv("AI_PROJECTS_ROOT", "projects")
    return Path(configured)


@dataclass(frozen=True)
class ProjectProfile:
    project_id: str
    display_name: str
    repo_path_env: str
    write_enabled_env: str
    default_mode: str
    agent_profile: str
    memory_files: list[str]
    prompt_files: Dict[str, str]
    task_prompt_overrides: Dict[str, str]
    context_rules: Dict[str, Any]
    project_dir: Path
    raw_config: Dict[str, Any]

    @property
    def project_yaml_path(self) -> Path:
        return self.project_dir / "project.yaml"

    @property
    def bootstrap_path(self) -> Path:
        return self.project_dir / "CODEX_BOOTSTRAP.md"

    @property
    def agent_context_path(self) -> Path:
        return self.project_dir / "AGENT_CONTEXT.md"

    def resolve_target_repo(self) -> str:
        return os.getenv(self.repo_path_env, "")

    def write_enabled(self) -> bool:
        return _env_bool(self.write_enabled_env, False)


@dataclass(frozen=True)
class ProjectRuntime:
    profile: ProjectProfile
    target_repo: str
    write_enabled: bool

    @property
    def project_id(self) -> str:
        return self.profile.project_id


def load_project_profile(project_id: str | None = None, projects_root: str | None = None) -> ProjectProfile:
    resolved_project_id = project_id or os.getenv("AI_DEFAULT_PROJECT", "ia-trade")
    project_dir = _resolve_projects_root(projects_root) / resolved_project_id
    config = _load_yaml(project_dir / "project.yaml")

    if not config:
        raise FileNotFoundError(f"project profile not found for '{resolved_project_id}' at {project_dir / 'project.yaml'}")

    return ProjectProfile(
        project_id=str(config.get("project_id", resolved_project_id)),
        display_name=str(config.get("display_name", resolved_project_id)),
        repo_path_env=str(config.get("repo_path_env", "AI_TARGET_REPO")),
        write_enabled_env=str(config.get("write_enabled_env", "AI_REPO_WRITE_ENABLED")),
        default_mode=str(config.get("default_mode", "read-only")),
        agent_profile=str(config.get("agent_profile", "engineering")),
        memory_files=list(config.get("memory_files", [])),
        prompt_files=dict(config.get("prompt_files", {})),
        task_prompt_overrides=dict(config.get("task_prompt_overrides", {})),
        context_rules=dict(config.get("context_rules", {})),
        project_dir=project_dir,
        raw_config=config,
    )


def load_runtime_project(project_id: str | None = None, projects_root: str | None = None) -> ProjectRuntime:
    profile = load_project_profile(project_id=project_id, projects_root=projects_root)
    return ProjectRuntime(
        profile=profile,
        target_repo=profile.resolve_target_repo(),
        write_enabled=profile.write_enabled(),
    )
