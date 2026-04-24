from pathlib import Path


def create_test_project_profile(
    projects_root: Path,
    project_id: str,
    repo_env: str = "AI_TARGET_REPO_ALT",
    write_env: str = "AI_REPO_WRITE_ENABLED_ALT",
    context_rules: dict | None = None,
    task_prompt_overrides: dict | None = None,
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
    lines = [
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
        ]
    if context_rules:
        lines.extend([
            "context_rules:",
            f"  max_target_files: {int(context_rules.get('max_target_files', 5))}",
        ])
        task_file_limits = context_rules.get("task_file_limits", {})
        if isinstance(task_file_limits, dict) and task_file_limits:
            lines.append("  task_file_limits:")
            for task_type, limit in task_file_limits.items():
                lines.append(f"    {task_type}: {int(limit)}")
        task_queries = context_rules.get("task_queries", {})
        if isinstance(task_queries, dict) and task_queries:
            lines.append("  task_queries:")
            for task_type, queries in task_queries.items():
                if not isinstance(queries, list):
                    continue
                lines.append(f"    {task_type}:")
                for query in queries:
                    lines.append(f"      - {query}")
        pinned_files = context_rules.get("pinned_files_by_task", {})
        if isinstance(pinned_files, dict) and pinned_files:
            lines.append("  pinned_files_by_task:")
            for task_type, files in pinned_files.items():
                if not isinstance(files, list):
                    continue
                lines.append(f"    {task_type}:")
                for path in files:
                    lines.append(f"      - {path}")
    if task_prompt_overrides:
        lines.append("task_prompt_overrides:")
        for task_type, prompt_name in task_prompt_overrides.items():
            lines.append(f"  {task_type}: {prompt_name}")
    lines.append("")

    (project_dir / "project.yaml").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return project_dir
