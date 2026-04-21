import json
import os
import sys
from pathlib import Path

from app.commands.review_file import (
    detect_file_kind,
    collect_signals,
    classify_risk,
    build_recommendation,
)
from app.core.context_manager import ContextManager
from app.core.file_selector import choose_best_python_match, collect_python_files


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.review_best_python_match <query>")
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
    best = choose_best_python_match(query, files)

    if not best:
        print(json.dumps({
            "status": "error",
            "query": query,
            "reason": "no matching python file found",
        }, ensure_ascii=False, indent=2))
        return 1

    ctx = ContextManager(repo_root=str(root), max_files=3)
    content = ctx.read_file(best.file, max_chars=50000)

    file_kind = detect_file_kind(best.file)
    signals = collect_signals(content)
    risk_level = classify_risk(file_kind, signals)
    preview = "\n".join(content.splitlines()[:20])

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": str(root),
        "query": query,
        "selected_file": best.file,
        "score": best.score,
        "file_kind": file_kind,
        "risk_level": risk_level,
        "signals": signals,
        "preview": preview,
        "recommendation": build_recommendation(file_kind, risk_level, best.file),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
