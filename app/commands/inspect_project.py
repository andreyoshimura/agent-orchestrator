import json
import os
import sys
from pathlib import Path

from app.core.project_loader import load_runtime_project


def _path_status(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
    }


def _target_repo_summary(target_repo: str) -> dict:
    if not target_repo:
        return {
            "configured": False,
            "path": "",
            "exists": False,
            "is_dir": False,
            "top_level_entries": [],
        }

    path = Path(target_repo).resolve()
    entries = []
    if path.exists() and path.is_dir():
        entries = sorted(item.name for item in path.iterdir())[:20]

    return {
        "configured": True,
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "top_level_entries": entries,
    }


def main() -> int:
    project_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv("AI_DEFAULT_PROJECT", "ia-trade")

    try:
        runtime = load_runtime_project(project_id=project_id)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    profile = runtime.profile
    memory_status = [_path_status(Path(path)) for path in profile.memory_files]
    prompt_status = {
        name: _path_status(Path(path))
        for name, path in profile.prompt_files.items()
    }

    result = {
        "status": "ok",
        "project_id": profile.project_id,
        "display_name": profile.display_name,
        "project_dir": str(profile.project_dir),
        "default_mode": profile.default_mode,
        "agent_profile": profile.agent_profile,
        "repo_path_env": profile.repo_path_env,
        "write_enabled_env": profile.write_enabled_env,
        "write_enabled": runtime.write_enabled,
        "profile_files": {
            "project_yaml": _path_status(profile.project_yaml_path),
            "bootstrap": _path_status(profile.bootstrap_path),
            "agent_context": _path_status(profile.agent_context_path),
            "memory_files": memory_status,
            "prompt_files": prompt_status,
        },
        "target_repo": _target_repo_summary(runtime.target_repo),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
