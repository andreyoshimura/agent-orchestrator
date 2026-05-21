# Roadmap

## Purpose

This roadmap tracks product/runtime evolution of `agent-orchestrator`.
Operational history and session checkpoints are kept here only when they affect the current roadmap. Historical notes must not contradict the current state.

AI workflow infrastructure is tracked separately in:

- `docs/ai_context_progress.md`
- `.ai_context/AI_SYNC.md`
- `docs/ai_session_workflow.md`

---

## Status legend

- `[x]` completed
- `[~]` partially implemented / needs hardening
- `[ ]` pending

---

## Current project status

Current status: **functional technical MVP in active hardening**.

Latest published commit: `ce92b343` (`feat(observability): provider usage telemetry and proactive switch alert`)
Branch: `main`
Remote status: synced with `origin/main`
Current validation: `150` passing tests

### Implemented

- Multi-provider routing through `config/routing.yaml`
- Rule-based provider fallback
- Retry/fallback policy per task
- Provider timeout per task
- `provider_max_tokens` support through `routing.<task>.execution`
- Proactive provider switching when budget headroom is below threshold
- Project profiles through `projects/<project_id>/project.yaml`
- Context assembly with bootstrap, memory, prompts and selected files
- Task pipeline with diagnostics and stage metrics
- Local agent planning output (`repo_worker`, `micro_reviewer`, `arbiter`)
- Provider interface beyond stub status
- Live HTTP execution for OpenAI, Gemini, Claude and OpenRouter when configured
- OpenRouter support
- HTTP error classification, including `insufficient_credits` for HTTP 402
- Daily budget persistence in `var/state`
- Task result cache with fingerprint-based invalidation
- Inspect-task cache with TTL and force-refresh support
- `StateStore` and `CacheStore` atomic writes for light concurrency safety
- `OperationalStore` persistence for task results, metrics and cache summaries
- Provider usage telemetry when provider usage data is available
- Proactive switch telemetry
- `diagnose-orchestrator`, `inspect-project` and `healthcheck.sh` operational diagnostics
- Health-only, compact, strict and quiet diagnostic modes
- Cache purge through `scripts/task.sh purge-cache`
- `.env` fallback loading in scripts without overriding exported variables
- AI documentation structure under `docs/`

### Partially implemented

- Generic multi-language analysis: current selection flow is strongest for Python repositories
- Token usage accounting: daily token telemetry and daily-token alert are in place; per-model USD cost accounting is out of scope (token-based alerting is the canonical signal)
- Provider usage telemetry: normalized for OpenRouter, Claude, Gemini and OpenAI; cost accounting still pending
- Streaming provider execution: not yet implemented
- Product packaging: still closer to local engineering tool than packaged product
- Context security: `ContextSanitizer` covers known secret families and prompt-injection markers; AuditLog wiring is opt-in (no default sink yet)

---

## Completed phases

### Fase 0 - Local base and initial commands

- `[x]` prepare local environment
- `[x]` validate access to target repository
- `[x]` connect real file reading through `ContextManager`
- `[x]` implement and expose initial commands:
  - `explain-file`
  - `review-file`
  - `summarize-repo-area`
  - `map-dependencies`
  - `list-python-files`
  - `pick-python-file`
  - `review-best-python-match`
  - `explain-best-python-match`
- `[x]` improve ranking and tie-breaking for Python file selection

### Fase 1 - Global orchestrator structure

- `[x]` centralize project/profile loading in the core
- `[x]` create reusable active-project inspection (`inspect-project`)
- `[x]` connect the generic CLI to the central project loader
- `[x]` add tests for project profile loading
- `[~]` keep the global layer generic while `ia-trade` remains the first project profile

### Fase 2 - Automatic context assembly

- `[x]` create global context builder per task
- `[x]` combine global bootstrap, project profile, memory and selected files
- `[x]` move selection/ranking heuristics to `app/core/`
- `[x]` support project-specific context rules without contaminating the global layer:
  - `max_target_files`
  - `task_file_limits`
  - `task_queries`
  - `pinned_files_by_task`
- `[x]` support `task_prompt_overrides` in `project.yaml`

### Fase 3 - Runtime execution flow

- `[~]` harden `TaskRunner` as a real pipeline executor
  - `TaskRunner.run` publishes `execution_metrics`
  - pipeline stages are explicit
  - `run`/`inspect` include `pipeline`, `stage_metrics`, `context_sufficiency` and `synthesis`
- `[~]` connect local agents to prompts and project memory
  - `build_local_task_plan` returns structured `local_agent_output`
  - `TaskRunner` passes local analysis metadata to providers
- `[x]` standardize provider interface beyond `stub`
- `[x]` allow multiple accounts per adapter through provider type/prefix mapping
- `[x]` implement real provider fallback
- `[x]` externalize retry/fallback policy per task
- `[x]` support provider timeout per task
- `[x]` support proactive budget-based provider switching
- `[x]` support `provider_max_tokens` per task with default fallback

### Fase 4 - Persistence and operational autonomy

- `[x]` persist daily budget in `var/state`
- `[~]` persist reusable context/task-result cache
  - fingerprint lookup is available in `OperationalStore`
  - cache can be reused by default with `AI_CACHE_REUSE_ENABLED`
  - `force_refresh` bypass is supported
  - fingerprints include selected-file content signatures
- `[~]` operational diagnostics
  - cache index metrics
  - recent task status summaries
  - budget alerts
  - storage health
  - health summary
  - health-only and fail-on-degraded modes
  - compact JSON output
  - healthcheck wrapper for CI/cron
  - output artifact support
  - metadata support
- `[~]` reduce local inspection recomputation
  - `inspect-task` cache with TTL
  - cache invalidation when selected files change
- `[~]` reduce dependency on manual wrappers
  - legacy aliases delegate to generic inspect/context flows where possible
  - `map-dependencies` remains dedicated for UX/compatibility but uses generic runtime data

### Fase 5 - Reliability

- `[x]` expand tests for commands, ranking and context assembly
- `[x]` cover missing `AI_TARGET_REPO` and invalid profile scenarios
- `[x]` cover invalid JSON and non-object payloads
- `[x]` validate multiple project profiles beyond `ia-trade`
- `[x]` document recommended local workflow
- `[x]` harden providers for partial/invalid responses
- `[x]` cover fallback for partial provider responses classified as temporary failures
- `[x]` cover E2E `inspect-task -> task_cli` with degradation, fallback and persistence
- `[x]` cover light local persistence concurrency
- `[x]` cover task cache hit/miss after selected-file changes
- `[x]` add provider usage telemetry and proactive switch alert tests

---

## Current priorities

1. `[x]` Normalize provider usage telemetry across Claude, Gemini and OpenAI
2. `[x]` Add daily token limit alert signals to `health_summary`
3. `[x]` Refine `provider_max_tokens` by task/profile/model
4. `[x]` Harden context security against secret leakage and prompt injection
5. `[~]` Expand file selection beyond Python
6. `[ ]` Add streaming provider execution for long tasks
7. `[ ]` Define productized output format for code audit/review
8. `[ ]` Evaluate GitHub PR integration for review workflows

---

## Latest checkpoint

### 2026-05-04 / 2026-05-05 UTC

Commit: `ce92b343`
Title: `feat(observability): provider usage telemetry and proactive switch alert`
Remote: `origin/main` synced

Delivered:

- `provider_max_tokens` flows through `RouteDecision` into provider execution
- HTTP `402` is mapped to `insufficient_credits`
- OpenRouter usage metrics are extracted and included in provider output
- `OperationalStore.persist_task_result` accumulates provider usage in `provider_usage_metrics_<date>`
- `diagnose-orchestrator` exposes `provider_usage_telemetry`
- `AI_PROACTIVE_SWITCH_ALERT_THRESHOLD` added with default `20`
- `proactive_switches_high` signal added to `health_summary`
- `--health-only` includes proactive switch checks
- Documentation reorganized under `docs/`
- README reduced to a compact entrypoint
- AI bundles updated to reference the new documentation structure
- `.env` fallback loading added to `task.sh` and `healthcheck.sh`
- `purge-cache` exposed through `task.sh`

Validation:

- `150` tests passing
- `healthcheck --all --strict` returning `ok`
- `inspect-task review-file` running without errors

Next:

- Normalize usage telemetry for Claude, Gemini and OpenAI
- Add daily cost/token alerting to `health_summary`
- Refine token limits by profile/model/task
- Explore streaming for long-running provider tasks
