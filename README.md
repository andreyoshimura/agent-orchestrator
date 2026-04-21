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

## Next step

Copy `.env.example` to `.env`, adjust the provider keys you want to use, and configure `projects/ia-trade/project.yaml` with the local target repo path.
