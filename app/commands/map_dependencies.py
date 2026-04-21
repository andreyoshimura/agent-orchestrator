import ast
import json
import os
import sys
from pathlib import Path

from app.core.context_manager import ContextManager


def classify_import(name: str) -> str:
    if not name:
        return "unknown"
    root = name.split(".")[0]
    if root in {
        "app",
        "analysis",
        "strategy",
        "scripts",
        "tests",
        "config",
        "db",
        "utils",
        "core",
    }:
        return "local"
    return "external"


def extract_imports(content: str) -> dict:
    tree = ast.parse(content)
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "type": "import",
                        "name": alias.name,
                        "asname": alias.asname,
                        "scope": classify_import(alias.name),
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(
                {
                    "type": "from",
                    "name": module,
                    "level": node.level,
                    "imported": [alias.name for alias in node.names],
                    "scope": "local" if node.level > 0 else classify_import(module),
                }
            )

    local_imports = [item for item in imports if item["scope"] == "local"]
    external_imports = [item for item in imports if item["scope"] == "external"]

    return {
        "imports": imports,
        "local_import_count": len(local_imports),
        "external_import_count": len(external_imports),
        "total_import_count": len(imports),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.map_dependencies <relative-path.py>")
        return 1

    repo_root = os.environ.get("AI_TARGET_REPO")
    if not repo_root:
        print(json.dumps({"status": "error", "reason": "AI_TARGET_REPO not set"}, ensure_ascii=False, indent=2))
        return 1

    relative_path = sys.argv[1]
    if not relative_path.endswith(".py"):
        print(json.dumps({"status": "error", "reason": "target file must be a .py file"}, ensure_ascii=False, indent=2))
        return 1

    ctx = ContextManager(repo_root=repo_root, max_files=3)

    try:
        content = ctx.read_file(relative_path, max_chars=50000)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    try:
        mapping = extract_imports(content)
    except SyntaxError as exc:
        print(json.dumps({"status": "error", "reason": f"syntax error while parsing file: {exc}"}, ensure_ascii=False, indent=2))
        return 1

    result = {
        "status": "ok",
        "project_id": os.environ.get("AI_DEFAULT_PROJECT", "unknown"),
        "target_repo": repo_root,
        "file": relative_path,
        **mapping,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
