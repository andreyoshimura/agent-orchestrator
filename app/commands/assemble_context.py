import json
import os
import sys

from app.cli.payload_parser import parse_json_payload
from app.core.context_builder import ContextBuilder
from app.core.dependency_mapper import map_python_dependencies, summarize_dependency_map
from app.core.project_loader import load_runtime_project


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.assemble_context <task-type> [json-payload]")
        return 1

    task_type = sys.argv[1]
    raw_payload = " ".join(sys.argv[2:]).strip()
    payload, payload_error = parse_json_payload(raw_payload)
    if payload_error:
        print(json.dumps({"status": "error", "reason": payload_error}, ensure_ascii=False, indent=2))
        return 1

    try:
        runtime_project = load_runtime_project(os.getenv("AI_DEFAULT_PROJECT", "ia-trade"))
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    bundle = ContextBuilder(runtime_project).build(task_type=task_type, payload=payload)

    result = {
        "status": "ok",
        "project_id": bundle.project_id,
        "task_type": bundle.task_type,
        "objective": bundle.objective,
        "prompt_name": bundle.prompt_name,
        "prompt_template_preview": bundle.prompt_text[:800],
        "files": bundle.files,
        "sections": bundle.sections,
        "context_preview": bundle.context_text[:4000],
        "context_length": len(bundle.context_text),
    }
    if task_type == "map-dependencies":
        target_file = str(payload.get("file") or (bundle.files[0] if bundle.files else "")).strip()
        dependency_map = map_python_dependencies(runtime_project.target_repo, target_file)
        result["dependency_map"] = dependency_map
        result["dependency_highlights"] = summarize_dependency_map(dependency_map)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
