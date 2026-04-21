from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from app.core.context_builder import ContextBuilder
from app.core.operational_store import OperationalStore
from app.core.provider_failure_policy import (
    classify_provider_failure,
    should_accept_provider_result,
    should_retry_provider,
    should_try_fallback,
)
from app.core.project_loader import load_runtime_project
from app.core.router import Router
from app.core.budget_manager import BudgetManager
from app.core.task_planner import build_local_task_plan
from app.providers import get_provider
from app.providers.base import ProviderRequest
from app.providers.config import ProviderSettings


@dataclass
class TaskRequest:
    task_type: str
    payload: Dict[str, object]


@dataclass
class TaskResult:
    provider: str
    task_type: str
    status: str
    output: Dict[str, object]


class TaskRunner:
    def __init__(
        self,
        router: Router,
        budget_manager: BudgetManager,
        provider_settings: Dict[str, ProviderSettings] | None = None,
        operational_store: OperationalStore | None = None,
    ):
        self.router = router
        self.budget_manager = budget_manager
        self.provider_settings = provider_settings or {}
        self.operational_store = operational_store or OperationalStore()

    def run(self, request: TaskRequest, estimated_cost: float = 0.0) -> TaskResult:
        decision = self.router.decide(request.task_type)
        planning = self._build_context_info(request)
        context_info = planning["context"]
        local_plan = planning["local_plan"]
        local_plan_object = planning["local_plan_object"]
        attempted_providers = []
        chosen_provider: Optional[str] = None
        provider_result: Dict[str, object] | None = None

        for provider_name in [decision.provider, *decision.fallbacks]:
            if not self._provider_usable(provider_name, estimated_cost):
                attempted_providers.append({
                    "provider": provider_name,
                    "attempt": 0,
                    "status": "skipped",
                    "reason": "provider unavailable within current settings or budget",
                })
                continue

            current_result, provider_attempts, should_continue_to_fallback = self._run_provider_with_retry(
                provider_name=provider_name,
                request=request,
                local_plan_object=local_plan_object,
                context_info=context_info,
                estimated_cost=estimated_cost,
                max_provider_retries=decision.max_provider_retries,
                fallback_on=decision.fallback_on,
            )
            attempted_providers.extend(provider_attempts)

            if should_accept_provider_result(current_result["status"]):
                chosen_provider = provider_name
                provider_result = current_result
                break
            if not should_continue_to_fallback:
                provider_result = current_result
                break

        if not chosen_provider:
            result = TaskResult(
                provider=str(provider_result["provider"]) if provider_result else "none",
                task_type=request.task_type,
                status="degraded",
                output={
                    "reason": "no provider completed successfully",
                    "context": context_info,
                    "local_plan": local_plan,
                    "provider_attempts": attempted_providers,
                    "provider_result": provider_result,
                },
            )
            self._persist_result(request, result)
            return result

        result = TaskResult(
            provider=chosen_provider,
            task_type=request.task_type,
            status=str(provider_result["status"]),
            output={
                "payload": request.payload,
                "context": context_info,
                "local_plan": local_plan,
                "provider_result": provider_result,
                "provider_attempts": attempted_providers,
            },
        )
        self._persist_result(request, result)
        return result

    def inspect(self, request: TaskRequest, estimated_cost: float = 0.0) -> Dict[str, object]:
        decision = self.router.decide(request.task_type)
        planning = self._build_context_info(request)
        providers = [decision.provider, *decision.fallbacks]

        provider_status = []
        for provider_name in providers:
            settings = self.provider_settings.get(provider_name)
            budget_status = self.budget_manager.status(provider_name)
            provider_status.append({
                "provider": provider_name,
                "enabled": settings.enabled if settings is not None else True,
                "budget": {
                    "spent": budget_status.spent,
                    "limit": budget_status.limit,
                    "remaining": budget_status.remaining,
                    "available": budget_status.available,
                },
                "usable_for_estimated_cost": self._provider_usable(provider_name, estimated_cost),
            })

        return {
            "task_type": request.task_type,
            "payload": request.payload,
            "route": {
                "preferred": decision.provider,
                "fallbacks": decision.fallbacks,
                "max_provider_retries": decision.max_provider_retries,
                "fallback_on": decision.fallback_on,
            },
            "context": planning["context"],
            "local_plan": planning["local_plan"],
            "providers": provider_status,
        }

    def _build_context_info(self, request: TaskRequest) -> Dict[str, object]:
        project_id = str(request.payload.get("project_id", "")).strip() or None
        try:
            runtime_project = load_runtime_project(project_id=project_id)
            bundle = ContextBuilder(runtime_project).build(
                task_type=request.task_type,
                payload=request.payload,
            )
        except FileNotFoundError:
            return {
                "context": {"status": "unavailable", "reason": "project profile not found"},
                "local_plan_object": None,
                "local_plan": {"status": "unavailable", "reason": "project profile not found"},
            }

        local_plan = build_local_task_plan(
            task_type=request.task_type,
            payload=request.payload,
            bundle=bundle,
        )

        context_status = "ready"
        context_reason = ""
        target_repo = runtime_project.target_repo
        explicit_files = bool(request.payload.get("file")) or bool(request.payload.get("files"))

        if not target_repo:
            context_status = "partial"
            context_reason = "target repo not configured"
        else:
            target_repo_path = Path(target_repo).resolve()
            if not target_repo_path.exists() or not target_repo_path.is_dir():
                context_status = "partial"
                context_reason = f"target repo path not found: {target_repo_path}"
            elif not bundle.files and not explicit_files:
                context_status = "partial"
                context_reason = "no target files selected"

        return {
            "context": {
                "status": context_status,
                "reason": context_reason,
                "prompt_name": bundle.prompt_name,
                "sections": bundle.sections,
                "file_count": len(bundle.files),
                "context_length": len(bundle.context_text),
                "target_repo": {
                    "configured": bool(target_repo),
                    "path": target_repo,
                },
            },
            "local_plan_object": local_plan,
            "local_plan": {
                "status": context_status,
                "reason": context_reason,
                "agent_name": local_plan.agent_name,
                "prompt_name": local_plan.prompt_name,
                "prompt_template_preview": local_plan.prompt_template_preview,
                "selected_files": local_plan.selected_files,
                "context_sections": local_plan.context_sections,
                "context_length": local_plan.context_length,
                "recommended_action": local_plan.recommended_action,
                "prompt_preview": local_plan.prompt_preview,
            },
        }

    def _execute_provider(
        self,
        provider_name: str,
        request: TaskRequest,
        local_plan: object,
        context_info: Dict[str, object],
    ) -> Dict[str, object]:
        if local_plan is None:
            return {
                "provider": provider_name,
                "status": "skipped",
                "output": {"reason": "local plan unavailable"},
            }
        provider = get_provider(provider_name, self.provider_settings[provider_name])
        response = provider.run(
            ProviderRequest(
                prompt=str(getattr(local_plan, "prompt_text", "")),
                metadata={
                    "task_type": request.task_type,
                    "project_id": request.payload.get("project_id", ""),
                    "selected_files": getattr(local_plan, "selected_files", []),
                    "context": context_info,
                },
            )
        )
        return {
            "provider": response.provider,
            "status": response.status,
            "output": response.output,
        }

    def _provider_usable(self, provider_name: str, estimated_cost: float) -> bool:
        settings = self.provider_settings.get(provider_name)
        if settings is not None and not settings.enabled:
            return False
        return self.budget_manager.can_use(provider_name, estimated_cost)

    def _run_provider_with_retry(
        self,
        provider_name: str,
        request: TaskRequest,
        local_plan_object: object,
        context_info: Dict[str, object],
        estimated_cost: float,
        max_provider_retries: int,
        fallback_on: list[str],
    ) -> tuple[Dict[str, object], list[Dict[str, object]], bool]:
        attempts: list[Dict[str, object]] = []
        current_result: Dict[str, object] | None = None

        for attempt_index in range(max_provider_retries + 1):
            self.budget_manager.record(provider_name, estimated_cost)
            current_result = self._execute_provider(
                provider_name=provider_name,
                request=request,
                local_plan=local_plan_object,
                context_info=context_info,
            )
            failure_type = classify_provider_failure(current_result["status"], current_result.get("output"))
            attempts.append({
                "provider": provider_name,
                "attempt": attempt_index + 1,
                "status": current_result["status"],
                "failure_type": failure_type,
            })

            if should_accept_provider_result(current_result["status"]):
                return current_result, attempts, False
            if attempt_index < max_provider_retries and should_retry_provider(current_result["status"], current_result.get("output")):
                continue
            return current_result, attempts, should_try_fallback(
                current_result["status"],
                current_result.get("output"),
                fallback_on=fallback_on,
            )

        assert current_result is not None
        return current_result, attempts, False

    def _persist_result(self, request: TaskRequest, result: TaskResult) -> None:
        project_id = str(request.payload.get("project_id", "unknown"))
        persistence = self.operational_store.persist_task_result(
            task_type=request.task_type,
            project_id=project_id,
            payload=request.payload,
            output=result.output,
        )
        result.output["persistence"] = persistence
