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

Latest published commit: `8381685` (`feat(security): sanitize target-file content against secrets and prompt injection`)
Branch: `main`
Remote status: synced with `origin/main`
Current validation: `179` passing tests (189 total — 10 pre-existing fixture errors in `tests/test_task_script.py` unrelated to runtime code)

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

### 2026-05-20 UTC

Commit: `8381685`
Title: `feat(security): sanitize target-file content against secrets and prompt injection`
Remote: `origin/main` synced

Delivered in this session:

- `fb6c88a` Normalized provider usage telemetry for Claude, OpenAI and
  Gemini into the unified `{prompt_tokens, completion_tokens,
  total_tokens}` shape already produced by OpenRouter
- `57fa941` Added `daily_tokens_high` signal to `health_summary`, gated
  by `AI_DAILY_TOKEN_ALERT_THRESHOLD` (default `0` = disabled);
  `--health-only` exposes `daily_token_total` / `daily_token_threshold`
- `48fc194` Clarified that the alert is scoped to daily token volume
  (USD cost accounting is intentionally out of scope)
- `41b6363` Layered `provider_max_tokens` resolution into a 7-level
  hierarchy via `Router.resolve_max_tokens(task, provider,
  profile_overrides)`; `TaskRunner` applies it per-provider in the
  candidate loop so fallback providers also get the right cap
- `8381685` Added `app/core/security.ContextSanitizer`; every
  `TARGET_FILE` chunk is screened for known secret families (Anthropic,
  OpenAI, AWS, GitHub, Slack, Google, JWT, Bearer, DB URLs, PEM private
  keys) and prompt-injection markers; modes `redact` / `block` /
  `audit` are selected via `AI_CONTEXT_SECURITY_MODE`; trusted operator
  documents (`docs/`, project memory, prompts) are intentionally not
  sanitized
- `e6cce98` Top-level `ROADMAP.md` introduced with 8 phased tasks,
  completion criteria, dependencies and affected files

Validation:

- `179` tests passing (189 total — 10 pre-existing fixture errors in
  `tests/test_task_script.py` that hardcode `SD200` vs `SD2001` are
  unrelated to runtime code)
- New env vars documented in `docs/references.md`
- New `docs/security.md` covers the sanitizer contract

Next:

- Expand file selection beyond Python (TypeScript, Go, Java, C++)
- Add streaming provider execution for long-running tasks
- Define productized output format for code audit/review
- Evaluate GitHub PR integration for review workflows
- Address pre-existing test_task_script.py hardcoded-path failures
