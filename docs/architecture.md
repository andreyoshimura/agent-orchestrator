# Architecture

## Overview

`agent-orchestrator` is a generic multi-provider AI routing layer for local repositories. It loads project-specific context, selects relevant files, routes tasks to the best available provider, and persists results locally.

## Layer separation

### Global layer (`app/`)
Belongs to the orchestrator — reusable across all projects:
- Provider integration and fallback
- Routing and budget logic
- Context loading and file selection
- Task pipeline and persistence

### Project layer (`projects/<project_id>/`)
Belongs to a specific project — never bleeds into the global layer:
- Project context and memory
- Prompt templates per agent role
- File selection rules (`context_rules` in `project.yaml`)
- Playbooks

## Component map

```
app/
  cli/          task_cli.py — CLI entrypoint for all tasks
  commands/     one module per task type (inspect, diagnose, review, explain, purge...)
  core/         runtime: task_runner, context_builder, file_selector, project_loader
  providers/    HTTP adapters: openai, gemini, claude, openrouter
  agents/       local agents: repo_worker, micro_reviewer, arbiter
  storage/      StateStore, CacheStore (atomic writes, fingerprint-based cache)

config/
  providers.yaml    provider registry (type, env var names)
  routing.yaml      task → preferred+fallback providers, retry/timeout/budget policy
  budgets.yaml      daily budget limits per provider

projects/
  <project_id>/
    project.yaml          profile metadata, env var names, memory/prompt file lists
    AGENT_CONTEXT.md      project context loaded into every agent
    CODEX_BOOTSTRAP.md    project-specific Codex bootstrap
    memory/               facts, guardrails, architecture notes
    prompts/              repo_worker, micro_reviewer, arbiter
    playbooks/            optional task playbooks

var/
  state/    daily budget usage, recent task results
  cache/    task result cache (_index.json + fingerprint-keyed .txt files)
  logs/     audit log (jsonl)
```

## Task execution pipeline

```
task_cli → TaskRunner.run()
  1. validate_payload
  2. load_runtime_profile
  3. build_context         (ContextBuilder: bootstrap + memory + selected files)
  4. evaluate_context_sufficiency
  5. local_analysis        (local agents: repo_worker → micro_reviewer → arbiter)
  6. provider_execution    (with retry + budget-aware fallback)
  7. synthesize_result
  8. persistence           (StateStore + CacheStore)
  9. return_diagnostics
```

## Provider selection

Each task has a `preferred` provider and `fallback` list in `config/routing.yaml`.

Before executing, `TaskRunner` checks `BudgetManager`:
- If the preferred provider is above `budget_switch_threshold_ratio`, switches proactively to the first viable fallback.
- On provider failure, retries up to `max_provider_retries` before falling through to the next fallback.
- Fallback types: `temporary`, `rate_limit`, `network`, `configuration`, `provider_unavailable`.

## Cache invalidation

Cache keys are fingerprints of:
- task type + payload fields
- content hash + metadata of selected files

A cache hit is only valid when file content has not changed since the last run.
Orphaned cache files (not in `_index.json`) can be removed with `bash scripts/task.sh purge-cache`.

## Context assembly

`ContextBuilder.build()` assembles context in this order:
1. Global bootstrap (`docs/bootstrap.md`)
2. Project bootstrap (`projects/<id>/CODEX_BOOTSTRAP.md`)
3. Project agent context (`projects/<id>/AGENT_CONTEXT.md`)
4. Project memory files
5. Project prompt for the task's agent role
6. Selected target repo files (ranked by `FileSelector`)

File selection is governed by `context_rules` in `project.yaml`:
- `max_target_files`
- `task_file_limits`
- `task_queries`
- `pinned_files_by_task`
