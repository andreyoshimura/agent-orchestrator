import json
import os
import sys
from pathlib import Path

from app.core.context_manager import ContextManager
from app.core.file_selector import choose_best_python_match, collect_python_files


def build_summary(relative_path: str, content: str, score: int) -> dict:
    """Gera um resumo estrutural simples do arquivo escolhido."""
    lines = content.splitlines()
    preview = "\n".join(lines[:20])

    return {
        "selected_file": relative_path,
        "score": score,
        "line_count": len(lines),
        "char_count": len(content),
        "preview": preview,
        "summary": f"Selected '{relative_path}' as the best Python match and generated a structural preview.",
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.explain_best_python_match <query>")
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

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": str(root),
        "query": query,
        **build_summary(best.file, content, best.score),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
