import json
import os
from pathlib import Path


IGNORED_PARTS = {
    "venv",
    ".venv",
    "__pycache__",
    "site-packages",
    ".git",
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.parts)


def main() -> int:
    repo_root = os.environ.get("AI_TARGET_REPO")
    if not repo_root:
        print(json.dumps({"status": "error", "reason": "AI_TARGET_REPO not set"}, ensure_ascii=False, indent=2))
        return 1

    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"status": "error", "reason": f"repo path not found: {root}"}, ensure_ascii=False, indent=2))
        return 1

    files = []
    for path in root.rglob("*.py"):
        if should_ignore(path):
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        files.append(str(relative))

    files.sort()

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": str(root),
        "file_count": len(files),
        "files": files,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
