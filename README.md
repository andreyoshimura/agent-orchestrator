# agent-orchestrator

Generic AI agent orchestrator for local repositories. Routes tasks between multiple AI providers (Claude, Gemini, OpenAI, OpenRouter), controls token budget per provider, and keeps project-specific memory isolated in `projects/<project_id>/`.

## Current status

- Functional technical MVP in active hardening
- Multi-provider routing, fallback, cache, budget and diagnostics are implemented
- Provider usage telemetry normalized across Claude, OpenAI, Gemini and OpenRouter
- Daily token-limit alerting wired into `health_summary`
- `provider_max_tokens` resolved through a layered task/profile/model hierarchy
- Target-file content is sanitized for secrets and prompt-injection markers
- Current validation: `179` passing tests (189 total, 10 pre-existing fixture errors)
- Latest published checkpoint: `8381685`

## Quick start

```bash
bash scripts/start_ai_session.sh
```

## Objectives

- Route tasks between multiple AI providers with rule-based fallback
- Control daily budget and token usage per provider
- Keep project-specific memory outside the central runtime
- Operate read-only on target repositories by default
- Remain plug-and-play and reversible

## Safe diagnostic commands

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Documentation

| Document | Purpose |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Components, pipeline, data flow, layer separation |
| [`docs/operations.md`](docs/operations.md) | Commands, scripts, env vars, routing policy and observability |
| [`docs/roadmap.md`](docs/roadmap.md) | Current status, completed phases and next priorities |
| [`docs/checklist.md`](docs/checklist.md) | Operational pre/post session checklist |
| [`docs/ai_session_workflow.md`](docs/ai_session_workflow.md) | Daily AI session workflow |
| [`docs/ai_context_progress.md`](docs/ai_context_progress.md) | AI infrastructure phases |
| [`docs/references.md`](docs/references.md) | Providers, config files, env vars and state keys |
| [`docs/bootstrap.md`](docs/bootstrap.md) | Codex/agent bootstrap instructions |

## AI context (for agents)

```text
.ai_context/
  CONTEXT_MINIMAL.md   minimal context for any AI agent
  GUARDRAILS.md        safety rules
  TASK_FORMATS.md      response format contract
  AI_SYNC.md           alignment across OpenAI, Gemini, Codex
  SESSION_STATE.md     where we left off
  AI_BUNDLE_SHORT.md   portable short bundle (daily use)
  AI_BUNDLE.md         portable full bundle (long sessions)
```
