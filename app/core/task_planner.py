from dataclasses import dataclass
from typing import Any, Dict

from app.agents.arbiter import Arbiter
from app.agents.micro_reviewer import MicroReviewer
from app.agents.repo_worker import RepoWorker
from app.core.context_builder import ContextBundle


AGENT_REGISTRY = {
    "repo_worker": RepoWorker,
    "micro_reviewer": MicroReviewer,
    "arbiter": Arbiter,
}


@dataclass(frozen=True)
class LocalTaskPlan:
    agent_name: str
    prompt_name: str | None
    prompt_template_preview: str
    prompt_text: str
    prompt_preview: str
    recommended_action: str
    selected_files: list[str]
    context_sections: list[str]
    context_length: int
    local_agent_output: dict[str, Any]


def build_local_task_plan(task_type: str, payload: Dict[str, Any], bundle: ContextBundle) -> LocalTaskPlan:
    prompt_name = bundle.prompt_name or "repo_worker"
    agent_cls = AGENT_REGISTRY.get(prompt_name, RepoWorker)
    agent = agent_cls()

    prompt = agent.build_prompt(
        task_payload={
            "task_type": task_type,
            **payload,
            "selected_files": bundle.files,
            "context_sections": bundle.sections,
        },
        project_memory=_compose_project_memory(bundle),
    )
    local_agent_payload = {
        "task_type": task_type,
        **payload,
        "selected_files": bundle.files,
        "context_sections": bundle.sections,
    }
    local_agent_output: dict[str, Any] = {"agent": agent.name, "payload": {"status": "unavailable"}}
    if hasattr(agent, "run_local"):
        raw_output = agent.run_local(  # type: ignore[attr-defined]
            task_payload=local_agent_payload,
            project_memory=_compose_project_memory(bundle),
        )
        if hasattr(raw_output, "payload") and hasattr(raw_output, "agent"):
            local_agent_output = {
                "agent": str(getattr(raw_output, "agent")),
                "payload": dict(getattr(raw_output, "payload")),
            }

    preview_header = (
        f"Agent: {agent.name}\n"
        f"Task type: {task_type}\n"
        f"Prompt profile: {prompt_name}\n"
        f"Selected files: {', '.join(bundle.files) if bundle.files else 'none'}\n"
        f"Recommended action: {_recommended_action(task_type, bundle.files)}\n\n"
    )

    return LocalTaskPlan(
        agent_name=agent.name,
        prompt_name=prompt_name,
        prompt_template_preview=bundle.prompt_text[:800],
        prompt_text=prompt,
        prompt_preview=(preview_header + prompt)[:2000],
        recommended_action=_recommended_action(task_type, bundle.files),
        selected_files=bundle.files,
        context_sections=bundle.sections,
        context_length=len(bundle.context_text),
        local_agent_output=local_agent_output,
    )


def _recommended_action(task_type: str, files: list[str]) -> str:
    if not files:
        return f"Resolve target files for '{task_type}' before invoking a provider."
    if task_type in {"review-file", "review-snippet", "review-diff"}:
        return f"Review the selected files first: {', '.join(files[:2])}."
    if task_type in {"explain-file", "summarize-module"}:
        return f"Summarize the selected files first: {', '.join(files[:2])}."
    if task_type == "map-dependencies":
        return f"Inspect imports and local dependencies in: {', '.join(files[:2])}."
    return f"Use the selected context to handle '{task_type}' with the assigned agent."


def _compose_project_memory(bundle: ContextBundle) -> str:
    if not bundle.prompt_text:
        return bundle.context_text
    return (
        f"Prompt template:\n{bundle.prompt_text}\n\n"
        f"Resolved context:\n{bundle.context_text}"
    )
