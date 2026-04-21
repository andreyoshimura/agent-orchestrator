import json
import os
import sys
from pathlib import Path

from app.core.context_manager import ContextManager


def detect_file_kind(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".md", ".txt"}:
        return "text"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    if suffix == ".sh":
        return "shell"
    return "unknown"


def collect_signals(content: str) -> dict:
    lower = content.lower()
    lines = content.splitlines()

    return {
        "has_todo": "todo" in lower,
        "has_fixme": "fixme" in lower,
        "has_print": "print(" in content,
        "has_eval": "eval(" in content,
        "has_exec": "exec(" in content,
        "has_subprocess": "subprocess" in lower,
        "line_count": len(lines),
        "char_count": len(content),
    }


def classify_risk(file_kind: str, signals: dict) -> str:
    if signals["has_eval"] or signals["has_exec"]:
        return "high"
    if file_kind in {"shell", "python"} and signals["has_subprocess"]:
        return "medium"
    return "low"


def build_recommendation(file_kind: str, risk_level: str, relative_path: str) -> str:
    if risk_level == "high":
        return f"Inspect '{relative_path}' carefully before trusting execution behavior."
    if risk_level == "medium":
        return f"Review '{relative_path}' with attention to command execution and side effects."
    if file_kind == "python":
        return f"'{relative_path}' looks suitable for deeper structural review."
    return f"'{relative_path}' looks safe for a basic documentation-oriented review."


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m app.commands.review_file <relative-path>")
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

    file_kind = detect_file_kind(relative_path)
    signals = collect_signals(content)
    risk_level = classify_risk(file_kind, signals)
    preview = "\n".join(content.splitlines()[:20])

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": repo_root,
        "file": relative_path,
        "file_kind": file_kind,
        "risk_level": risk_level,
        "signals": signals,
        "preview": preview,
        "recommendation": build_recommendation(file_kind, risk_level, relative_path),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
