# Operations

## Session start

```bash
bash scripts/start_ai_session.sh
```

Runs healthcheck, diagnostics, budget inspection, regenerates AI bundles, and prints the resume prompt for the AI tool.

## Healthcheck

```bash
bash scripts/healthcheck.sh --all --strict   # CI-friendly summary only
bash scripts/healthcheck.sh --all            # full payload
bash scripts/healthcheck.sh --quiet          # silent when ok
```

Returns exit code `0` (ok) or `2` (degraded).

## Task commands

```bash
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
bash scripts/task.sh inspect-task <task-type> '<json>'
bash scripts/task.sh purge-cache
```

## Available task types

| Command | Description |
|---|---|
| `explain-file` | Explain a specific file |
| `review-file` | Review a specific file |
| `summarize-repo-area` | Summarize multiple files |
| `map-dependencies` | Extract imports, symbols, call graph |
| `list-python-files` | List Python files in target repo |
| `pick-python-file` | Find best Python file for a query |
| `review-best-python-match` | Review best Python match for a query |
| `explain-best-python-match` | Explain best Python match for a query |
| `inspect-project` | Inspect active profile and target repo state |
| `inspect-task` | Preview routing + context for any task |
| `inspect-budget` | Show daily budget usage per provider |
| `diagnose-orchestrator` | Full orchestrator diagnostics |
| `assemble-context` | Build context bundle for a task |
| `purge-cache` | Remove orphaned cache files |

## AI bundle generation

```bash
bash scripts/generate_ai_bundle.sh
```

Regenerates `.ai_context/AI_BUNDLE_SHORT.md` and `.ai_context/AI_BUNDLE.md`.

## Session end

```bash
bash scripts/end_ai_session.sh "summary of what was done"
```

Updates `.ai_context/SESSION_STATE.md`.

## Key paths

| Path | Purpose |
|---|---|
| `.env` | Local environment variables (gitignored) |
| `.env.example` | Template for env vars |
| `config/routing.yaml` | Task routing policy |
| `config/providers.yaml` | Provider registry |
| `config/budgets.yaml` | Daily budget limits |
| `var/state/` | Persistent operational state |
| `var/cache/` | Task result cache |
| `var/logs/` | Audit log |
| `projects/ia-trade/` | IA-Trade project profile |

## Routing policy (per task)

Fields in `config/routing.yaml` under `routing.<task>.execution`:

| Field | Purpose |
|---|---|
| `preferred` | Primary provider |
| `fallback` | Ordered fallback list |
| `max_provider_retries` | Retries before falling to next provider |
| `provider_timeout_sec` | HTTP timeout per provider call |
| `budget_switch_threshold_ratio` | Switch proactively when budget headroom is below this ratio |
| `fallback_on` | Error types that trigger fallback |

## Cache control env vars

| Variable | Purpose |
|---|---|
| `AI_CACHE_REUSE_ENABLED` | Enable task result caching (default: true) |
| `AI_INSPECT_CACHE_REUSE_ENABLED` | Enable inspect-task caching |
| `AI_INSPECT_CACHE_TTL_SEC` | TTL for inspect-task cache |
