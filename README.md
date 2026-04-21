# agent-orchestrator

Generic multi-provider AI and agent orchestrator for local repositories.

## Goals

- Route tasks across multiple AI providers
- Control budget and token usage
- Keep project-specific memory outside the core runtime
- Stay plug-and-play and reversible
- Default to read-only access on target repositories

## Design principles

- Read-only by default
- No provider-to-provider free chat
- The orchestrator is the only component allowed to pass structured summaries between agents
- Target repository path is configured externally
- Provider fallback is rule-based
- Project-specific prompts and memory live under `projects/<project_id>/`

## Execution policy

- per-task provider preference and fallbacks live in `config/routing.yaml`
- retry and fallback behavior is also configured per task under `routing.<task>.execution`
- the core keeps safe defaults, but task-specific policy should be adjusted in config instead of hardcoded in runtime logic

## Operational persistence

- the latest task result per project/task is persisted under `var/state`
- summarized task execution fingerprints are cached under `var/cache`
- daily provider budget usage is persisted under `var/state`
- this persistence is local and reversible; it is intended to reduce repeated manual inspection work between runs

## Planned provider roles

- **Claude free**: small local review, snippet analysis, second opinion
- **Gemini**: broad repo analysis, dependency mapping, larger refactor planning
- **OpenAI**: arbitration, synthesis, final decision

## Initial tasks

- `explain-file`
- `review-snippet`
- `review-diff`
- `map-dependencies`
- `summarize-module`
- `compare-options`
- `final-decision`

## Local workflow

- `bash scripts/task.sh inspect-project` inspects the active project profile and validates its linked files
- `bash scripts/task.sh inspect-task <task-type> '<json>'` previews routing, selected files, local plan and provider usability for any task
- `bash scripts/task.sh inspect-budget` shows current daily spend/remaining budget by provider
- `bash scripts/task.sh diagnose-orchestrator` shows project/runtime/config/storage diagnostics
- `bash scripts/task.sh assemble-context <task-type> '<json>'` builds reusable task context from global + project sources
- `bash scripts/task.sh list-python-files` lists Python files from the configured target repository
- `bash scripts/task.sh pick-python-file <query>` ranks Python files by partial name
- `bash scripts/task.sh explain-best-python-match <query>` selects and previews the best Python match
- `bash scripts/task.sh review-best-python-match <query>` selects and reviews the best Python match

## Repository structure

```text
agent-orchestrator/
  app/
    core/
    providers/
    agents/
    storage/
  config/
  projects/
    ia-trade/
      prompts/
      memory/
  scripts/
  var/
    logs/
    cache/
    state/
  .env.example
  README.md
```

## Safety defaults

- `AI_REPO_WRITE_ENABLED=false`
- provider usage is optional and controlled by env/config
- project repository is referenced by path, not embedded into this repository
- this repository can be removed without touching the target project

## Profile selection

- `AI_DEFAULT_PROJECT` selects the active project profile
- `AI_PROJECTS_ROOT` can point to an alternate profiles directory when validating multiple project profiles locally

## Next step

Copy `.env.example` to `.env`, adjust the provider keys you want to use, and configure `projects/ia-trade/project.yaml` with the local target repo path.
