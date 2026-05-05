# References

## Repository

- Repo: `andreyoshimura/agent-orchestrator`
- Branch: `main`
- First project profile: `projects/ia-trade/`
- Target repo (ia-trade): configured via `AI_TARGET_REPO` (default: `../IA-Trade`)

## Providers

| Provider | Type | Config prefix | Role |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_*` | Arbitration, final decision |
| Gemini | `gemini` | `GEMINI_*` | Large repo analysis, dependency mapping |
| Gemini V2 | `gemini` | `GEMINI_V2_*` | Second Gemini account, same adapter |
| Claude | `claude` | `CLAUDE_*` | Local review, snippet analysis |
| OpenRouter | `openrouter` | `OPENROUTER_*` | Multi-model fallback, OpenAI-compatible route |

## Configuration files

| File | Purpose |
|---|---|
| `config/providers.yaml` | Provider registry: type, env var names |
| `config/routing.yaml` | Task → provider mapping, retry, timeout, budget threshold |
| `config/budgets.yaml` | Daily budget caps, max context files per provider |
| `.env` | Active credentials and toggles (gitignored) |
| `.env.example` | Template |

## Project profile structure

```
projects/<project_id>/
  project.yaml          required: profile metadata, env var names, memory/prompt lists
  AGENT_CONTEXT.md      project context loaded into every agent
  CODEX_BOOTSTRAP.md    Codex-specific bootstrap for this project
  memory/
    facts.md            key project facts
    guardrails.md       project-specific guardrails
  prompts/
    repo_worker.md
    micro_reviewer.md
    arbiter.md
  playbooks/            optional task playbooks
```

## Key environment variables

| Variable | Default | Purpose |
|---|---|---|
| `AI_TARGET_REPO` | — | Path to the target repository |
| `AI_DEFAULT_PROJECT` | `ia-trade` | Active project profile ID |
| `AI_PROJECTS_ROOT` | — | Override root for project profiles |
| `AI_ROUTER_ENABLED` | `true` | Enable task router |
| `AI_REPO_WRITE_ENABLED` | `false` | Enable write access to target repo |
| `AI_CACHE_REUSE_ENABLED` | `true` | Enable task result caching |
| `AI_INSPECT_CACHE_REUSE_ENABLED` | — | Enable inspect-task caching |
| `AI_INSPECT_CACHE_TTL_SEC` | — | TTL for inspect-task cache entries |
| `AI_BUDGET_ALERT_THRESHOLD_RATIO` | — | Budget alert threshold ratio |
| `BUDGET_<PROVIDER>_DAILY_USD` | — | Daily budget cap per provider |
| `MAX_CONTEXT_FILES_<PROVIDER>` | — | Max files sent to each provider |
| `<PROVIDER>_ENABLED` | — | Toggle provider on/off |
| `<PROVIDER>_MODEL` | — | Model alias for provider |
| `<PROVIDER>_API_KEY` | — | API credentials |
| `<PROVIDER>_API_BASE` | — | Optional endpoint override |

## Model aliases (current `.env`)

| Alias | Provider |
|---|---|
| `high_reasoning` | OpenAI |
| `code_heavy` | Gemini / Gemini V2 |
| `cheap_local_reviewer` | Claude |
| `openrouter/pareto-code` | OpenRouter |

## Key source files

| File | Role |
|---|---|
| `app/core/task_runner.py` | Main pipeline executor |
| `app/core/context_builder.py` | Context assembly |
| `app/core/file_selector.py` | File ranking and selection |
| `app/core/project_loader.py` | Profile loading |
| `app/core/provider_failure_policy.py` | Fallback/retry policy |
| `app/core/operational_store.py` | State + cache persistence |
| `config/routing.yaml` | Routing rules |
