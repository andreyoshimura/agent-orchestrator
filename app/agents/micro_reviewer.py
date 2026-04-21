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
