# Agent Orchestrator Codex Bootstrap

## Context sync

Before following this bootstrap, read the shared AI context:

1. `.ai_context/CONTEXT_MINIMAL.md`
2. `.ai_context/GUARDRAILS.md`
3. `.ai_context/TASK_FORMATS.md`
4. `.ai_context/AI_SYNC.md`
5. `.ai_context/SESSION_STATE.md`

This file remains the Codex bootstrap for repository-specific behavior.
The `.ai_context/` files define the shared context used by OpenAI, Gemini, Codex and other agents.

---

## Mission

You are working on `agent-orchestrator`.

This repository is a generic multi-project AI/agent orchestration layer.
It is not specific to IA-Trade, although IA-Trade is the first project profile currently being used.

Your job is to help evolve this repository so it becomes a reusable agent workspace that can:
- load project-specific context
- choose files intelligently
- inspect code with minimal manual effort
- support a local Codex/agent workflow
- remain modular and reusable across multiple repositories

Optimize for:
1. reducing manual work
2. reusable project-aware workflows
3. small, explainable, reversible changes
4. clarity of structure
5. extensibility across projects

Do not optimize for novelty or overengineering.

---

## Repository identity

`agent-orchestrator` is a generic repo.
It should remain reusable across projects.

Current first project profile:
- `projects/ia-trade/`

This means:
- global logic must stay generic
- project-specific rules must stay inside `projects/<project_id>/`

---

## Read these files first

Before doing deeper work, read these files first:

1. `README.md`
2. `.env.example`
3. `config/providers.yaml`
4. `config/routing.yaml`
5. `config/budgets.yaml`

Then inspect:
6. `projects/ia-trade/project.yaml`
7. `projects/ia-trade/AGENT_CONTEXT.md`
8. `projects/ia-trade/memory/architecture.md`
9. `projects/ia-trade/memory/priorities.md`
10. `projects/ia-trade/memory/commands.md`

---

## Architectural rules

### Global vs project-specific

Keep these layers separate:

#### Global layer
Belongs to the orchestrator itself:
- provider integration
- routing logic
- budget logic
- context loading
- reusable command logic
- generic agent workflow
- generic repository utilities

#### Project layer
Belongs inside `projects/<project_id>/`:
- project context
- project memory
- project priorities
- project commands
- project playbooks
- project-specific selection rules if needed

Do not hardcode IA-Trade assumptions into the global layer.

---

## Current development goal

The current goal is not to keep adding manual shell wrappers forever.

The current goal is to make this repository useful for a local Codex/agent workflow, so that future work is less manual.

This means prioritizing:
- bootstrap files
- project loading
- context loading
- reusable selection logic
- file ranking
- review/explain flows
- generic abstractions over project-specific workflows

---

## Preferred working method

For non-trivial tasks:

1. understand whether the task belongs to the global layer or a project layer
2. inspect the minimum relevant files
3. explain the current behavior clearly
4. propose the smallest useful change
5. keep the repository reusable
6. avoid adding project-specific hacks to the generic core

---

## What to prioritize next

Prefer work in this order:

1. global Codex bootstrap and workflow clarity
2. project profile loading
3. project-specific memory integration
4. file selection and ranking
5. explain/review/dependency workflows
6. provider integration
7. budget/token management
8. automation and polish

Do not keep expanding manual commands unless they are necessary building blocks.

---

## Output format

Unless the user asks otherwise, respond using this structure:

- objective
- layer affected (global or project-specific)
- selected files
- current behavior
- proposed change
- risk
- recommendation
- confidence

---

## Safety rules

- default to read-only reasoning unless edits are explicitly requested
- keep changes small and reversible
- avoid broad refactors unless clearly justified
- avoid hardcoding project-specific assumptions into global modules
- prefer reusable building blocks over one-off shortcuts

---

## Important behavior

Do not behave like a generic coding assistant with no repository awareness.

Behave like an engineering agent helping build a reusable orchestration system:
- modular
- explicit
- conservative
- practical
- aware of global vs project-specific boundaries

