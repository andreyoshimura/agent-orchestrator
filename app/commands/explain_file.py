import json
import os
import sys

from app.core.context_manager import ContextManager


def build_summary(relative_path: str, content: str) -> dict:
    lines = content.splitlines()
    preview = "\n".join(lines[:20])

    return {
        "file": relative_path,
        "line_count": len(lines),
        "char_count": len(content),
        "preview": preview,
        "summary": f"Read file '{relative_path}' successfully and generated a structural preview.",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m app.commands.explain_file <relative-path>")
        return 1

    repo_root = os.environ.get("AI_TARGET_REPO")
    if not repo_root:
        print(json.dumps({"status": "error", "reason": "AI_TARGET_REPO not set"}, ensure_ascii=False, indent=2))
        return 1

    relative_path = sys.argv[1]
    ctx = ContextManager(repo_root=repo_root, max_files=3)

    try:
        content = ctx.read_file(relative_path)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": repo_root,
        **build_summary(relative_path, content),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
