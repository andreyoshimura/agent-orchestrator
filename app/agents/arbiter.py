from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class AgentOutput:
    agent: str
    payload: Dict[str, Any]


class Arbiter:
    name = "arbiter"

    def build_prompt(self, task_payload: Dict[str, Any], project_memory: str = "") -> str:
        objective = task_payload.get("objective", "make final decision")
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
        objective = str(task_payload.get("objective", "make final decision")).strip()
        return AgentOutput(
            agent=self.name,
            payload={
                "status": "ready",
                "strategy": "decision_arbitration",
                "objective": objective,
                "focus_files": [str(item) for item in selected_files[:3]],
                "decision_criteria": [
                    "risk",
                    "implementation_cost",
                    "operational_impact",
                ],
                "has_project_memory": bool(project_memory.strip()),
            },
        )
