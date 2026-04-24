from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AgentOutput:
    agent: str
    payload: Dict[str, Any]


class MicroReviewer:
    name = "micro_reviewer"

    def build_prompt(self, task_payload: Dict[str, Any], project_memory: str = "") -> str:
        objective = task_payload.get("objective", "review local code context")
        return (
            f"Agent: {self.name}\n"
            f"Objective: {objective}\n\n"
            f"Project memory:\n{project_memory}\n\n"
            f"Task payload:\n{task_payload}"
        )

    def run_local(self, task_payload: Dict[str, Any], project_memory: str = "") -> AgentOutput:
        selected_files = task_payload.get("selected_files", [])
        if not isinstance(selected_files, list):
            selected_files = []
        objective = str(task_payload.get("objective", "review local code context")).strip()
        return AgentOutput(
            agent=self.name,
            payload={
                "status": "ready",
                "strategy": "focused_review",
                "objective": objective,
                "focus_files": [str(item) for item in selected_files[:2]],
                "review_checklist": [
                    "behavioral_regression",
                    "edge_cases",
                    "missing_tests",
                ],
                "has_project_memory": bool(project_memory.strip()),
            },
        )
