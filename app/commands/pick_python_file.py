import json
import os
import sys
from pathlib import Path

from app.core.file_selector import collect_python_files, rank_python_files


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.pick_python_file <query>")
        return 1

    repo_root = os.environ.get("AI_TARGET_REPO")
    if not repo_root:
        print(json.dumps({"status": "error", "reason": "AI_TARGET_REPO not set"}, ensure_ascii=False, indent=2))
        return 1

    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"status": "error", "reason": f"repo path not found: {root}"}, ensure_ascii=False, indent=2))
        return 1

    query = sys.argv[1].strip()
    files = collect_python_files(root)
    ranked = [{"file": item.file, "score": item.score} for item in rank_python_files(query, files)]

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": str(root),
        "query": query,
        "match_count": len(ranked),
        "matches": ranked[:20],
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
