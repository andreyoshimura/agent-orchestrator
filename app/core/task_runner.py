from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Dict, Optional

from app.core.context_builder import ContextBuilder
from app.core.dependency_mapper import map_python_dependencies, summarize_dependency_map
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
        allow_cache_reuse: bool = False,
    ):
        self.router = router
        self.budget_manager = budget_manager
        self.provider_settings = provider_settings or {}
        self.operational_store = operational_store or OperationalStore()
        self.allow_cache_reuse = allow_cache_reuse

    def run(self, request: TaskRequest, estimated_cost: float = 0.0) -> TaskResult:
        stage_metrics: dict[str, dict[str, object]] = {}
        run_started_at = time.perf_counter()
        payload_is_valid = isinstance(request.payload, dict)
        stage_metrics["validate_payload"] = _stage_metric(
            status="ok" if payload_is_valid else "error",
            reason="" if payload_is_valid else "payload must be an object",
            duration_ms=0,
        )
        if not payload_is_valid:
            return TaskResult(
                provider="none",
                task_type=request.task_type,
                status="degraded",
                output={
                    "reason": "invalid payload: payload must be an object",
                    "synthesis": {
                        "status": "degraded",
                        "mode": "run",
                        "final_status": "degraded",
                        "final_provider": "none",
                        "context_sufficient": False,
                        "missing_context_risks": ["invalid_payload"],
                        "provider_attempt_count": 0,
                        "recommended_action": "fix payload before executing the task",
                        "reason": "invalid payload: payload must be an object",
                    },
                    "pipeline": _pipeline_payload(stage_metrics),
                    "execution_metrics": _execution_metrics(
                        planning_ms=0,
                        run_started_at=run_started_at,
                        attempt_metrics=[],
                        cache_hit=False,
                        stage_metrics=stage_metrics,
                    ),
                    "cache": {"hit": False},
                },
            )

        decision = self.router.decide(request.task_type)
        project_id = str(request.payload.get("project_id", "unknown"))
        planning_started_at = time.perf_counter()
        planning = self._build_context_info(request)
        planning_ms = _elapsed_ms(run_started_at)
        stage_metrics["planning"] = _stage_metric(
            status="ok",
            reason="",
            duration_ms=_elapsed_ms(planning_started_at),
        )
        stage_metrics.update(planning["stage_metrics"])
        context_info = planning["context"]
        context_sufficiency = planning["context_sufficiency"]
        local_plan = planning["local_plan"]
        local_plan_object = planning["local_plan_object"]
        local_analysis = planning["local_analysis"]
        dependency_artifacts = self._dependency_artifacts(request, local_plan, context_info=context_info)
        cache_context = self._build_cache_context(local_plan, context_info)
        candidate_providers = [decision.provider, *decision.fallbacks]
        selection_preview = self._build_selection_preview(
            providers=candidate_providers,
            estimated_cost=estimated_cost,
            threshold_ratio=decision.budget_switch_threshold_ratio,
        )

        if self.allow_cache_reuse and not bool(request.payload.get("force_refresh")):
            cached_result = self.operational_store.load_cached_task_result(
                task_type=request.task_type,
                project_id=project_id,
                payload=request.payload,
                cache_context=cache_context,
            )
            if cached_result:
                stage_metrics["provider_execution"] = _stage_metric(
                    status="skipped",
                    reason="cache hit",
                    duration_ms=0,
                )
                stage_metrics["synthesize_result"] = _stage_metric(
                    status="ok",
                    reason="reused cached provider result",
                    duration_ms=0,
                )
                stage_metrics["persistence"] = _stage_metric(
                    status="skipped",
                    reason="cache hit",
                    duration_ms=0,
                )
                stage_metrics["return_diagnostics"] = _stage_metric(
                    status="ok",
                    reason="",
                    duration_ms=0,
                )
                output = {
                    **cached_result["output"],
                    "selection_preview": cached_result["output"].get("selection_preview")
                    if isinstance(cached_result["output"], dict) and isinstance(cached_result["output"].get("selection_preview"), dict)
                    else selection_preview,
                    "synthesis": cached_result["output"].get("synthesis")
                    if isinstance(cached_result["output"], dict) and isinstance(cached_result["output"].get("synthesis"), dict)
                    else self._synthesize_result_summary(
                        mode="run",
                        final_status=str(cached_result["status"]),
                        final_provider=str(cached_result["provider"]),
                        provider_result={"provider": cached_result["provider"], "status": cached_result["status"], "output": {}},
                        context_sufficiency=context_sufficiency,
                        local_analysis=local_analysis,
                        provider_attempts=[],
                    ),
                    "pipeline": _pipeline_payload(stage_metrics),
                    "execution_metrics": {
                        "cache_hit": True,
                        "planning_ms": planning_ms,
                        "provider_execution_ms": 0,
                        "total_ms": _elapsed_ms(run_started_at),
                        "stage_metrics": stage_metrics,
                    },
                    "cache": {"hit": True, "cache_key": cached_result["cache_key"]},
                }
                return TaskResult(
                    provider=str(cached_result["provider"]),
                    task_type=request.task_type,
                    status=str(cached_result["status"]),
                    output=output,
                )
        attempted_providers = []
        attempt_metrics: list[Dict[str, object]] = []
        chosen_provider: Optional[str] = None
        provider_result: Dict[str, object] | None = None

        provider_started_at = time.perf_counter()
        for provider_index, provider_name in enumerate(candidate_providers):
            if not self._provider_usable(provider_name, estimated_cost):
                attempted_providers.append({
                    "provider": provider_name,
                    "attempt": 0,
                    "status": "skipped",
                    "reason": "provider unavailable within current settings or budget",
                })
                continue

            if self._should_defer_provider(
                provider_name=provider_name,
                remaining_candidates=candidate_providers[provider_index + 1:],
                estimated_cost=estimated_cost,
                threshold_ratio=decision.budget_switch_threshold_ratio,
            ):
                attempted_providers.append({
                    "provider": provider_name,
                    "attempt": 0,
                    "status": "skipped",
                    "reason": "provider below proactive budget threshold",
                })
                continue

            current_result, provider_attempts, provider_attempt_metrics, should_continue_to_fallback = self._run_provider_with_retry(
                provider_name=provider_name,
                request=request,
                local_plan_object=local_plan_object,
                context_info=context_info,
                estimated_cost=estimated_cost,
                max_provider_retries=decision.max_provider_retries,
                fallback_on=decision.fallback_on,
                provider_timeout_sec=decision.provider_timeout_sec,
                provider_max_tokens=decision.provider_max_tokens,
            )
            attempted_providers.extend(provider_attempts)
            attempt_metrics.extend(provider_attempt_metrics)
            provider_result = current_result

            if should_accept_provider_result(current_result["status"]):
                chosen_provider = provider_name
                break
            if not should_continue_to_fallback:
                break
        stage_metrics["provider_execution"] = _stage_metric(
            status="ok" if chosen_provider else "degraded",
            reason="" if chosen_provider else "no provider completed successfully",
            duration_ms=_elapsed_ms(provider_started_at),
        )
        stage_metrics["synthesize_result"] = _stage_metric(
            status="ok",
            reason="",
            duration_ms=0,
        )

        if not chosen_provider:
            result = TaskResult(
                provider=str(provider_result["provider"]) if provider_result else "none",
                task_type=request.task_type,
                status="degraded",
                output={
                    "reason": "no provider completed successfully",
                    "context": context_info,
                    "context_sufficiency": context_sufficiency,
                    "local_plan": local_plan,
                    "local_analysis": local_analysis,
                    **dependency_artifacts,
                    "selection_preview": selection_preview,
                    "provider_attempts": attempted_providers,
                    "provider_result": provider_result,
                    "synthesis": self._synthesize_result_summary(
                        mode="run",
                        final_status="degraded",
                        final_provider=str(provider_result["provider"]) if isinstance(provider_result, dict) else "none",
                        provider_result=provider_result,
                        context_sufficiency=context_sufficiency,
                        local_analysis=local_analysis,
                        provider_attempts=attempted_providers,
                    ),
                    "pipeline": _pipeline_payload(stage_metrics),
                    "execution_metrics": _execution_metrics(
                        planning_ms=planning_ms,
                        run_started_at=run_started_at,
                        attempt_metrics=attempt_metrics,
                        cache_hit=False,
                        stage_metrics=stage_metrics,
                    ),
                    "cache": {"hit": False},
                },
            )
            self._persist_result(request, result, cache_context=cache_context)
            return result

        result = TaskResult(
            provider=chosen_provider,
            task_type=request.task_type,
            status=str(provider_result["status"]),
            output={
                "payload": request.payload,
                "context": context_info,
                "context_sufficiency": context_sufficiency,
                "local_plan": local_plan,
                "local_analysis": local_analysis,
                **dependency_artifacts,
                "selection_preview": selection_preview,
                "provider_result": provider_result,
                "provider_attempts": attempted_providers,
                "synthesis": self._synthesize_result_summary(
                    mode="run",
                    final_status=str(provider_result["status"]),
                    final_provider=chosen_provider,
                    provider_result=provider_result,
                    context_sufficiency=context_sufficiency,
                    local_analysis=local_analysis,
                    provider_attempts=attempted_providers,
                ),
                "pipeline": _pipeline_payload(stage_metrics),
                "execution_metrics": _execution_metrics(
                    planning_ms=planning_ms,
                    run_started_at=run_started_at,
                    attempt_metrics=attempt_metrics,
                    cache_hit=False,
                    stage_metrics=stage_metrics,
                ),
                "cache": {"hit": False},
            },
        )
        self._persist_result(request, result, cache_context=cache_context)
        return result

    def inspect(self, request: TaskRequest, estimated_cost: float = 0.0) -> Dict[str, object]:
        stage_metrics: dict[str, dict[str, object]] = {}
        payload_is_valid = isinstance(request.payload, dict)
        stage_metrics["validate_payload"] = _stage_metric(
            status="ok" if payload_is_valid else "error",
            reason="" if payload_is_valid else "payload must be an object",
            duration_ms=0,
        )
        if not payload_is_valid:
            invalid_decision = self.router.decide(request.task_type)
            stage_metrics["load_runtime_profile"] = _stage_metric("unavailable", "payload validation failed", 0)
            stage_metrics["build_context"] = _stage_metric("unavailable", "payload validation failed", 0)
            stage_metrics["evaluate_context_sufficiency"] = _stage_metric("unavailable", "payload validation failed", 0)
            stage_metrics["local_analysis"] = _stage_metric("unavailable", "payload validation failed", 0)
            stage_metrics["provider_execution"] = _stage_metric("skipped", "inspect mode", 0)
            stage_metrics["synthesize_result"] = _stage_metric("skipped", "inspect mode", 0)
            stage_metrics["persistence"] = _stage_metric("skipped", "inspect mode", 0)
            stage_metrics["return_diagnostics"] = _stage_metric("ok", "", 0)
            return {
                "task_type": request.task_type,
                "payload": request.payload,
                "route": {
                    "preferred": invalid_decision.provider,
                    "fallbacks": invalid_decision.fallbacks,
                    "max_provider_retries": invalid_decision.max_provider_retries,
                    "fallback_on": invalid_decision.fallback_on,
                    "provider_timeout_sec": invalid_decision.provider_timeout_sec,
                    "budget_switch_threshold_ratio": invalid_decision.budget_switch_threshold_ratio,
                },
                "context": {"status": "unavailable", "reason": "payload must be an object"},
                "context_sufficiency": {
                    "context_sufficient": False,
                    "selected_files": [],
                    "missing_context_risks": ["invalid_payload"],
                    "reason": "payload must be an object",
                },
                "local_plan": {"status": "unavailable", "reason": "payload must be an object"},
                "local_analysis": {"status": "unavailable", "reason": "payload must be an object"},
                "synthesis": {
                    "status": "unavailable",
                    "mode": "inspect",
                    "final_status": "inspect_preview",
                    "final_provider": invalid_decision.provider,
                    "context_sufficient": False,
                    "missing_context_risks": ["invalid_payload"],
                    "provider_attempt_count": 0,
                    "recommended_action": "fix payload before inspecting the task",
                    "reason": "payload must be an object",
                },
                "providers": [],
                "pipeline": _pipeline_payload(stage_metrics),
            }
        decision = self.router.decide(request.task_type)
        planning = self._build_context_info(request)
        stage_metrics.update(planning["stage_metrics"])
        stage_metrics["provider_execution"] = _stage_metric(
            status="skipped",
            reason="inspect mode",
            duration_ms=0,
        )
        stage_metrics["synthesize_result"] = _stage_metric(
            status="skipped",
            reason="inspect mode",
            duration_ms=0,
        )
        stage_metrics["persistence"] = _stage_metric(
            status="skipped",
            reason="inspect mode",
            duration_ms=0,
        )
        stage_metrics["return_diagnostics"] = _stage_metric(
            status="ok",
            reason="",
            duration_ms=0,
        )
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
                    "remaining_ratio": budget_status.remaining_ratio,
                },
                "usable_for_estimated_cost": self._provider_usable(provider_name, estimated_cost),
            })
        selection_preview = self._build_selection_preview(
            providers=providers,
            estimated_cost=estimated_cost,
            threshold_ratio=decision.budget_switch_threshold_ratio,
        )

        inspection = {
            "task_type": request.task_type,
            "payload": request.payload,
            "route": {
                "preferred": decision.provider,
                "fallbacks": decision.fallbacks,
                "max_provider_retries": decision.max_provider_retries,
                "fallback_on": decision.fallback_on,
                "provider_timeout_sec": decision.provider_timeout_sec,
                "budget_switch_threshold_ratio": decision.budget_switch_threshold_ratio,
            },
            "selection_preview": selection_preview,
            "context": planning["context"],
            "context_sufficiency": planning["context_sufficiency"],
            "local_plan": planning["local_plan"],
            "local_analysis": planning["local_analysis"],
            "synthesis": self._synthesize_result_summary(
                mode="inspect",
                final_status="inspect_preview",
                final_provider=decision.provider,
                provider_result=None,
                context_sufficiency=planning["context_sufficiency"],
                local_analysis=planning["local_analysis"],
                provider_attempts=[],
            ),
            "providers": provider_status,
            "pipeline": _pipeline_payload(stage_metrics),
        }
        inspection.update(
            self._dependency_artifacts(
                request,
                planning["local_plan"],
                context_info=planning["context"],
            )
        )
        return inspection

    def _build_context_info(self, request: TaskRequest) -> Dict[str, object]:
        load_started_at = time.perf_counter()
        project_id = str(request.payload.get("project_id", "")).strip() or None
        try:
            runtime_project = load_runtime_project(project_id=project_id)
            stage_metrics = {
                "load_runtime_profile": _stage_metric(
                    status="ok",
                    reason="",
                    duration_ms=_elapsed_ms(load_started_at),
                ),
            }
            context_started_at = time.perf_counter()
            bundle = ContextBuilder(runtime_project).build(
                task_type=request.task_type,
                payload=request.payload,
            )
        except FileNotFoundError:
            stage_metrics = {
                "load_runtime_profile": _stage_metric(
                    status="error",
                    reason="project profile not found",
                    duration_ms=_elapsed_ms(load_started_at),
                ),
                "build_context": _stage_metric(
                    status="unavailable",
                    reason="project profile not found",
                    duration_ms=0,
                ),
                "evaluate_context_sufficiency": _stage_metric(
                    status="unavailable",
                    reason="project profile not found",
                    duration_ms=0,
                ),
                "local_analysis": _stage_metric(
                    status="unavailable",
                    reason="project profile not found",
                    duration_ms=0,
                ),
            }
            return {
                "context": {"status": "unavailable", "reason": "project profile not found"},
                "local_plan_object": None,
                "local_plan": {"status": "unavailable", "reason": "project profile not found"},
                "local_analysis": {"status": "unavailable", "reason": "project profile not found"},
                "context_sufficiency": {
                    "context_sufficient": False,
                    "selected_files": [],
                    "missing_context_risks": ["project_profile_not_found"],
                    "reason": "project profile not found",
                },
                "stage_metrics": stage_metrics,
            }

        stage_metrics["build_context"] = _stage_metric(
            status="ok",
            reason="",
            duration_ms=_elapsed_ms(context_started_at),
        )
        local_analysis_started_at = time.perf_counter()
        local_plan = build_local_task_plan(
            task_type=request.task_type,
            payload=request.payload,
            bundle=bundle,
        )
        stage_metrics["local_analysis"] = _stage_metric(
            status="ok",
            reason="",
            duration_ms=_elapsed_ms(local_analysis_started_at),
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
        missing_context_risks = []
        if not target_repo:
            missing_context_risks.append("target_repo_not_configured")
        elif context_reason.startswith("target repo path not found"):
            missing_context_risks.append("target_repo_path_missing")
        if not bundle.files:
            missing_context_risks.append("no_target_files_selected")
        context_sufficiency = {
            "context_sufficient": context_status == "ready" and len(missing_context_risks) == 0,
            "selected_files": list(local_plan.selected_files),
            "missing_context_risks": missing_context_risks,
            "reason": context_reason or "context ready",
        }
        stage_metrics["evaluate_context_sufficiency"] = _stage_metric(
            status="ok" if context_sufficiency["context_sufficient"] else "partial",
            reason=context_sufficiency["reason"],
            duration_ms=0,
        )
        local_analysis = {
            "status": "ready",
            "reason": "",
            "agent_name": local_plan.agent_name,
            "recommended_action": local_plan.recommended_action,
            "local_agent_output": local_plan.local_agent_output,
        }

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
                "context_sufficiency": context_sufficiency,
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
                "local_agent_output": local_plan.local_agent_output,
                "context_sufficiency": context_sufficiency,
            },
            "local_analysis": local_analysis,
            "context_sufficiency": context_sufficiency,
            "stage_metrics": stage_metrics,
        }

    def _execute_provider(
        self,
        provider_name: str,
        request: TaskRequest,
        local_plan: object,
        context_info: Dict[str, object],
        provider_timeout_sec: int = 30,
        provider_max_tokens: int = 2048,
    ) -> Dict[str, object]:
        if local_plan is None:
            return {
                "provider": provider_name,
                "status": "skipped",
                "output": {"reason": "local plan unavailable"},
            }
        settings = self.provider_settings.get(provider_name)
        if settings is None:
            return {
                "provider": provider_name,
                "status": "error",
                "output": {
                    "reason": f"provider settings not found for '{provider_name}'",
                    "failure_type": "configuration",
                },
            }
        try:
            provider = get_provider(provider_name, settings)
        except KeyError as exc:
            return {
                "provider": provider_name,
                "status": "error",
                "output": {
                    "reason": str(exc),
                    "failure_type": "provider_unavailable",
                },
            }
        response = provider.run(
            ProviderRequest(
                prompt=str(getattr(local_plan, "prompt_text", "")),
                metadata={
                    "task_type": request.task_type,
                    "project_id": request.payload.get("project_id", ""),
                    "selected_files": getattr(local_plan, "selected_files", []),
                    "local_agent_output": getattr(local_plan, "local_agent_output", {}),
                    "provider_timeout_sec": provider_timeout_sec,
                    "provider_max_tokens": provider_max_tokens,
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

    def _should_defer_provider(
        self,
        provider_name: str,
        remaining_candidates: list[str],
        estimated_cost: float,
        threshold_ratio: float,
    ) -> bool:
        if threshold_ratio <= 0:
            return False

        status = self.budget_manager.status(provider_name)
        if status.limit <= 0 or status.remaining <= 0:
            return False
        if status.remaining_ratio > threshold_ratio:
            return False

        for fallback_name in remaining_candidates:
            if not self._provider_usable(fallback_name, estimated_cost):
                continue
            fallback_status = self.budget_manager.status(fallback_name)
            if fallback_status.remaining_ratio > threshold_ratio:
                return True
        return False

    def _build_selection_preview(
        self,
        providers: list[str],
        estimated_cost: float,
        threshold_ratio: float,
    ) -> Dict[str, object]:
        if not providers:
            return {
                "strategy": "unavailable",
                "decision": "none",
                "reason": "no providers configured",
            }

        primary = providers[0]
        primary_status = self.budget_manager.status(primary)
        viable_fallback = None
        for fallback_name in providers[1:]:
            if not self._provider_usable(fallback_name, estimated_cost):
                continue
            fallback_status = self.budget_manager.status(fallback_name)
            viable_fallback = {
                "provider": fallback_name,
                "remaining": fallback_status.remaining,
                "remaining_ratio": fallback_status.remaining_ratio,
            }
            break

        if primary_status.limit > 0 and primary_status.remaining > 0 and primary_status.remaining_ratio <= threshold_ratio and viable_fallback is not None:
            return {
                "strategy": "proactive_budget_switch",
                "decision": "switch_now_due_to_budget",
                "primary_provider": primary,
                "primary_remaining": primary_status.remaining,
                "primary_remaining_ratio": primary_status.remaining_ratio,
                "threshold_ratio": threshold_ratio,
                "selected_fallback": viable_fallback,
                "reason": (
                    f"primary provider {primary} is below proactive budget threshold; "
                    f"switching to fallback {viable_fallback['provider']} before quota exhaustion"
                ),
            }

        if primary_status.limit > 0 and primary_status.remaining > 0 and primary_status.remaining_ratio <= threshold_ratio:
            return {
                "strategy": "proactive_budget_switch",
                "decision": "defer_switch_no_viable_fallback",
                "primary_provider": primary,
                "primary_remaining": primary_status.remaining,
                "primary_remaining_ratio": primary_status.remaining_ratio,
                "threshold_ratio": threshold_ratio,
                "reason": (
                    f"primary provider {primary} is below proactive budget threshold, "
                    "but no fallback with enough headroom is available"
                ),
            }

        return {
            "strategy": "standard_route",
            "decision": "keep_primary",
            "primary_provider": primary,
            "primary_remaining": primary_status.remaining,
            "primary_remaining_ratio": primary_status.remaining_ratio,
            "threshold_ratio": threshold_ratio,
            "reason": "primary provider remains above proactive switch threshold",
        }

    def _run_provider_with_retry(
        self,
        provider_name: str,
        request: TaskRequest,
        local_plan_object: object,
        context_info: Dict[str, object],
        estimated_cost: float,
        max_provider_retries: int,
        fallback_on: list[str],
        provider_timeout_sec: int,
        provider_max_tokens: int = 2048,
    ) -> tuple[Dict[str, object], list[Dict[str, object]], list[Dict[str, object]], bool]:
        attempts: list[Dict[str, object]] = []
        attempt_metrics: list[Dict[str, object]] = []
        current_result: Dict[str, object] | None = None

        for attempt_index in range(max_provider_retries + 1):
            attempt_started_at = time.perf_counter()
            current_result = self._execute_provider(
                provider_name=provider_name,
                request=request,
                local_plan=local_plan_object,
                context_info=context_info,
                provider_timeout_sec=provider_timeout_sec,
                provider_max_tokens=provider_max_tokens,
            )
            attempt_duration_ms = _elapsed_ms(attempt_started_at)
            failure_type = classify_provider_failure(current_result["status"], current_result.get("output"))
            if self._should_record_cost(current_result["status"], current_result.get("output"), estimated_cost):
                self.budget_manager.record(provider_name, estimated_cost)
            attempts.append({
                "provider": provider_name,
                "attempt": attempt_index + 1,
                "status": current_result["status"],
                "failure_type": failure_type,
            })
            attempt_metrics.append({
                "provider": provider_name,
                "attempt": attempt_index + 1,
                "status": current_result["status"],
                "failure_type": failure_type,
                "duration_ms": attempt_duration_ms,
            })

            if should_accept_provider_result(current_result["status"]):
                return current_result, attempts, attempt_metrics, False
            if attempt_index < max_provider_retries and should_retry_provider(current_result["status"], current_result.get("output")):
                continue
            return current_result, attempts, attempt_metrics, should_try_fallback(
                current_result["status"],
                current_result.get("output"),
                fallback_on=fallback_on,
            )

        assert current_result is not None
        return current_result, attempts, attempt_metrics, False

    def _should_record_cost(self, status: object, output: Dict[str, object] | None, estimated_cost: float) -> bool:
        if estimated_cost <= 0:
            return False
        failure_type = classify_provider_failure(status, output)
        return failure_type not in {"provider_unavailable", "configuration"}

    def _persist_result(
        self,
        request: TaskRequest,
        result: TaskResult,
        cache_context: Dict[str, object] | None = None,
    ) -> None:
        result.output.setdefault("pipeline", {})
        pipeline = result.output["pipeline"]
        if isinstance(pipeline, dict):
            stage_metrics = pipeline.get("stage_metrics")
            if isinstance(stage_metrics, dict):
                stage_metrics["persistence"] = _stage_metric(status="ok", reason="", duration_ms=0)
                stage_metrics["return_diagnostics"] = _stage_metric(status="ok", reason="", duration_ms=0)
                pipeline["stages"] = _pipeline_stages_list(stage_metrics)
                execution_metrics = result.output.get("execution_metrics")
                if isinstance(execution_metrics, dict):
                    execution_metrics["stage_metrics"] = stage_metrics
        project_id = str(request.payload.get("project_id", "unknown"))
        persistence = self.operational_store.persist_task_result(
            task_type=request.task_type,
            project_id=project_id,
            payload=request.payload,
            output=result.output,
            cache_context=cache_context,
        )
        result.output["persistence"] = persistence

    def _dependency_artifacts(
        self,
        request: TaskRequest,
        local_plan: Dict[str, object],
        context_info: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        if request.task_type != "map-dependencies":
            return {}

        target_repo = str(request.payload.get("target_repo", "")).strip()
        if not target_repo and isinstance(context_info, dict):
            target_repo_info = context_info.get("target_repo", {})
            if isinstance(target_repo_info, dict):
                target_repo = str(target_repo_info.get("path", "")).strip()
        selected_files = local_plan.get("selected_files", [])
        fallback_file = selected_files[0] if isinstance(selected_files, list) and selected_files else ""
        target_file = str(request.payload.get("file") or fallback_file).strip()
        dependency_map = map_python_dependencies(target_repo, target_file)

        return {
            "dependency_map": dependency_map,
            "dependency_highlights": summarize_dependency_map(dependency_map),
        }

    def _build_cache_context(self, local_plan: Dict[str, object], context_info: Dict[str, object]) -> Dict[str, object]:
        target_repo_info = context_info.get("target_repo", {})
        if not isinstance(target_repo_info, dict):
            return {"target_repo": "", "selected_files": [], "signature": ""}
        target_repo = str(target_repo_info.get("path", "")).strip()
        selected_files = local_plan.get("selected_files", [])
        if not isinstance(selected_files, list):
            selected_files = []
        normalized_files = [str(item) for item in selected_files if isinstance(item, str)]
        file_fingerprints = self._file_fingerprints(target_repo, normalized_files)
        signature = hashlib.sha256(
            json.dumps(file_fingerprints, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return {
            "target_repo": target_repo,
            "selected_files": normalized_files,
            "file_fingerprints": file_fingerprints,
            "signature": signature,
        }

    def _file_fingerprints(self, target_repo: str, selected_files: list[str]) -> list[Dict[str, object]]:
        if not target_repo:
            return []
        repo_root = Path(target_repo).resolve()
        fingerprints: list[Dict[str, object]] = []
        for relative_path in selected_files:
            full_path = (repo_root / relative_path).resolve()
            if not str(full_path).startswith(str(repo_root)):
                fingerprints.append({
                    "file": relative_path,
                    "exists": False,
                    "reason": "out_of_repo",
                })
                continue
            if not full_path.exists() or not full_path.is_file():
                fingerprints.append({
                    "file": relative_path,
                    "exists": False,
                    "reason": "missing",
                })
                continue
            content = full_path.read_bytes()
            stat = full_path.stat()
            fingerprints.append(
                {
                    "file": relative_path,
                    "exists": True,
                    "size": stat.st_size,
                    "mtime_ns": int(stat.st_mtime_ns),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
        return fingerprints

    def _synthesize_result_summary(
        self,
        mode: str,
        final_status: str,
        final_provider: str,
        provider_result: Dict[str, object] | None,
        context_sufficiency: Dict[str, object],
        local_analysis: Dict[str, object],
        provider_attempts: list[Dict[str, object]],
    ) -> Dict[str, object]:
        missing_context_risks = context_sufficiency.get("missing_context_risks", [])
        if not isinstance(missing_context_risks, list):
            missing_context_risks = []
        recommended_action = str(local_analysis.get("recommended_action", "")).strip()
        if not recommended_action:
            if final_status in {"completed", "stub"}:
                recommended_action = "consume provider output and persist follow-up actions"
            elif mode == "inspect":
                recommended_action = "execute the task via task_cli to obtain provider output"
            else:
                recommended_action = "review provider attempts and adjust route/context before retrying"

        provider_output = provider_result.get("output", {}) if isinstance(provider_result, dict) else {}
        if not isinstance(provider_output, dict):
            provider_output = {}
        reason = str(provider_output.get("reason", "")).strip()
        if not reason:
            if final_status in {"completed", "stub"}:
                reason = "provider completed successfully"
            elif mode == "inspect":
                reason = "inspect mode does not execute provider"
            else:
                reason = "provider execution did not complete successfully"

        synthesis_status = "ready" if final_status in {"completed", "stub"} else "degraded"
        if mode == "inspect":
            synthesis_status = "preview"
        return {
            "status": synthesis_status,
            "mode": mode,
            "final_status": final_status,
            "final_provider": final_provider,
            "context_sufficient": bool(context_sufficiency.get("context_sufficient", False)),
            "missing_context_risks": missing_context_risks,
            "provider_attempt_count": len(provider_attempts),
            "recommended_action": recommended_action,
            "reason": reason,
        }


def _elapsed_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def _execution_metrics(
    planning_ms: int,
    run_started_at: float,
    attempt_metrics: list[Dict[str, object]],
    cache_hit: bool,
    stage_metrics: dict[str, dict[str, object]] | None = None,
) -> Dict[str, object]:
    provider_execution_ms = sum(
        int(item.get("duration_ms", 0))
        for item in attempt_metrics
        if isinstance(item, dict)
    )
    return {
        "cache_hit": cache_hit,
        "planning_ms": planning_ms,
        "provider_execution_ms": provider_execution_ms,
        "total_ms": _elapsed_ms(run_started_at),
        "attempt_metrics": attempt_metrics,
        "stage_metrics": stage_metrics or {},
    }


def _stage_metric(status: str, reason: str, duration_ms: int) -> dict[str, object]:
    return {
        "status": status,
        "reason": reason,
        "duration_ms": max(duration_ms, 0),
    }


def _pipeline_stages_list(stage_metrics: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    ordered = []
    for stage_name in [
        "validate_payload",
        "load_runtime_profile",
        "build_context",
        "evaluate_context_sufficiency",
        "local_analysis",
        "provider_execution",
        "synthesize_result",
        "persistence",
        "return_diagnostics",
    ]:
        metric = stage_metrics.get(stage_name, {})
        if not isinstance(metric, dict):
            metric = {}
        ordered.append({
            "stage": stage_name,
            "status": str(metric.get("status", "unknown")),
            "reason": str(metric.get("reason", "")),
            "duration_ms": int(metric.get("duration_ms", 0)),
        })
    return ordered


def _pipeline_payload(stage_metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        "stage_metrics": stage_metrics,
        "stages": _pipeline_stages_list(stage_metrics),
    }
