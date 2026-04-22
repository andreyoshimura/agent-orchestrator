import json
import os
import sys
from app.core.dependency_mapper import map_python_dependencies
from app.core.project_loader import load_runtime_project


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.map_dependencies <relative-path.py>")
        return 1

    relative_path = sys.argv[1]

    try:
        runtime_project = load_runtime_project(os.getenv("AI_DEFAULT_PROJECT", "ia-trade"))
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    mapping = map_python_dependencies(runtime_project.target_repo, relative_path)
    if mapping.get("status") != "ok":
        print(json.dumps(mapping, ensure_ascii=False, indent=2))
        return 1

    result = {
        "status": "ok",
        "project_id": runtime_project.project_id,
        "target_repo": runtime_project.target_repo,
        **mapping,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
