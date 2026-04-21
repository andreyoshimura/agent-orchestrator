from pathlib import Path


def create_test_project_profile(
    projects_root: Path,
    project_id: str,
    repo_env: str = "AI_TARGET_REPO_ALT",
    write_env: str = "AI_REPO_WRITE_ENABLED_ALT",
) -> Path:
    project_dir = projects_root / project_id
    (project_dir / "memory").mkdir(parents=True, exist_ok=True)
    (project_dir / "prompts").mkdir(parents=True, exist_ok=True)

    (project_dir / "CODEX_BOOTSTRAP.md").write_text(
        f"# Bootstrap for {project_id}\n",
        encoding="utf-8",
    )
    (project_dir / "AGENT_CONTEXT.md").write_text(
        f"# Context for {project_id}\n",
        encoding="utf-8",
    )
    (project_dir / "memory" / "facts.md").write_text(
        f"facts for {project_id}\n",
        encoding="utf-8",
    )
    (project_dir / "prompts" / "repo_worker.md").write_text(
        "You are the repo_worker agent.\n",
        encoding="utf-8",
    )
    (project_dir / "prompts" / "micro_reviewer.md").write_text(
        "You are the micro_reviewer agent.\n",
        encoding="utf-8",
    )
    (project_dir / "prompts" / "arbiter.md").write_text(
        "You are the arbiter agent.\n",
        encoding="utf-8",
    )
    (project_dir / "project.yaml").write_text(
        "\n".join([
            f"project_id: {project_id}",
            f"display_name: {project_id.title()}",
            f"repo_path_env: {repo_env}",
            f"write_enabled_env: {write_env}",
            "default_mode: read-only",
            "agent_profile: engineering",
            "memory_files:",
            f"  - {project_dir}/memory/facts.md",
            "prompt_files:",
            f"  repo_worker: {project_dir}/prompts/repo_worker.md",
            f"  micro_reviewer: {project_dir}/prompts/micro_reviewer.md",
            f"  arbiter: {project_dir}/prompts/arbiter.md",
            "",
        ]),
        encoding="utf-8",
    )
    return project_dir
