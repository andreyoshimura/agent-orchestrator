from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

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
        decision = self.router.decide(request.task_type)
        project_id = str(request.payload.get("project_id", "unknown"))
        planning = self._build_context_info(request)
        context_info = planning["context"]
        local_plan = planning["local_plan"]
        local_plan_object = planning["local_plan_object"]
        dependency_artifacts = self._dependency_artifacts(request, local_plan, context_info=context_info)
        cache_context = self._build_cache_context(local_plan, context_info)

        if self.allow_cache_reuse and not bool(request.payload.get("force_refresh")):
            cached_result = self.operational_store.load_cached_task_result(
                task_type=request.task_type,
                project_id=project_id,
                payload=request.payload,
                cache_context=cache_context,
            )
            if cached_result:
                output = {
                    **cached_result["output"],
                    "cache": {"hit": True, "cache_key": cached_result["cache_key"]},
                }
                return TaskResult(
                    provider=str(cached_result["provider"]),
                    task_type=request.task_type,
                    status=str(cached_result["status"]),
                    output=output,
                )
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
            provider_result = current_result

            if should_accept_provider_result(current_result["status"]):
                chosen_provider = provider_name
                break
            if not should_continue_to_fallback:
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
                    **dependency_artifacts,
                    "provider_attempts": attempted_providers,
                    "provider_result": provider_result,
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
                "local_plan": local_plan,
                **dependency_artifacts,
                "provider_result": provider_result,
                "provider_attempts": attempted_providers,
                "cache": {"hit": False},
            },
        )
        self._persist_result(request, result, cache_context=cache_context)
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

        inspection = {
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
        inspection.update(
            self._dependency_artifacts(
                request,
                planning["local_plan"],
                context_info=planning["context"],
            )
        )
        return inspection

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
            current_result = self._execute_provider(
                provider_name=provider_name,
                request=request,
                local_plan=local_plan_object,
                context_info=context_info,
            )
            failure_type = classify_provider_failure(current_result["status"], current_result.get("output"))
            if self._should_record_cost(current_result["status"], current_result.get("output"), estimated_cost):
                self.budget_manager.record(provider_name, estimated_cost)
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
