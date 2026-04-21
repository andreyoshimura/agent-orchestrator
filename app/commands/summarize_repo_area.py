import json
import os
import sys
from pathlib import Path

from app.core.context_manager import ContextManager


DEFAULT_FILES = [
    "README.md",
    "AGENTS.md",
]


def summarize_files(ctx: ContextManager, files: list[str]) -> dict:
    collected = []
    total_chars = 0
    total_lines = 0

    for relative_path in files:
        try:
            content = ctx.read_file(relative_path)
        except FileNotFoundError:
            continue

        lines = content.splitlines()
        preview = "\n".join(lines[:10])

        collected.append(
            {
                "file": relative_path,
                "line_count": len(lines),
                "char_count": len(content),
                "preview": preview,
            }
        )
        total_chars += len(content)
        total_lines += len(lines)

    return {
        "files_analyzed": collected,
        "file_count": len(collected),
        "total_lines": total_lines,
        "total_chars": total_chars,
    }


def main() -> int:
    repo_root = os.environ.get("AI_TARGET_REPO")
    if not repo_root:
        print(json.dumps({"status": "error", "reason": "AI_TARGET_REPO not set"}, ensure_ascii=False, indent=2))
        return 1

    files = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_FILES

    ctx = ContextManager(repo_root=repo_root, max_files=20)
    summary = summarize_files(ctx, files)

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": repo_root,
        "requested_files": files,
        **summary,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
