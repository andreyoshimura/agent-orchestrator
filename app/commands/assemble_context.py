import json
import os
import sys

from app.core.context_builder import ContextBuilder
from app.core.project_loader import load_runtime_project


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.assemble_context <task-type> [json-payload]")
        return 1

    task_type = sys.argv[1]
    raw_payload = " ".join(sys.argv[2:]).strip()
    payload = json.loads(raw_payload) if raw_payload else {}

    runtime_project = load_runtime_project(os.getenv("AI_DEFAULT_PROJECT", "ia-trade"))
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
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
