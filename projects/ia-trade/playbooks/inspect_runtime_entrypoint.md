# Playbook: Inspect Runtime Entrypoint

## Goal

Use this playbook when the task is about understanding a central runtime file, especially:
- `paper_trade.py`
- `semi_auto.py`
- `main.py`

The objective is to understand real operational behavior, not just summarize code superficially.

## When to use this playbook

Use it when the request is about:
- runtime behavior
- execution flow
- signal processing
- order or paper execution
- state persistence
- operational bugs
- risk-related behavior starting from a runtime entrypoint

## Inspection order

### Step 1 — confirm the selected file
First confirm that the chosen file is really the best operational entrypoint for the request.

If the query is broad and references:
- paper -> prefer `paper_trade.py`
- semi-auto -> prefer `semi_auto.py`
- runtime / run / entrypoint -> prefer top-level runtime files before analysis scripts

### Step 2 — identify the file purpose
Extract:
- what this file is responsible for
- whether it is runtime-critical
- what kind of mode it represents
- whether it orchestrates other modules

### Step 3 — inspect top-level imports
Look for imports from:
- `strategy/`
- `risk/`
- `execution/`
- `data/`
- `utils/`
- `analysis/`

This helps locate downstream modules that actually define behavior.

### Step 4 — identify main flow
Understand:
- input sources
- config usage
- signal generation path
- risk evaluation path
- execution or simulation path
- persistence/logging/reporting path
- notification path

### Step 5 — identify operational risk
Explicitly flag whether the file touches:
- broker interaction
- execution planning
- state mutation
- live risk checks
- position sizing
- synchronization/reconciliation
- file writes or artifact persistence

### Step 6 — identify likely next files
After reviewing the entrypoint, propose the next file(s) to inspect based on imports and operational relevance.

Prioritize:
1. risk
2. execution
3. strategy
4. config/utilities
5. analysis helpers

## Output structure

Use this output structure:

- objective
- selected entrypoint
- purpose
- main flow
- key dependencies
- operational risk
- likely next files
- recommendation
- confidence

## Important rules

- Do not treat analysis scripts as primary runtime unless explicitly requested.
- Do not jump into tests first.
- Do not recommend broad refactor by default.
- Keep focus on actual runtime behavior.
- Prefer the smallest set of next files that explain the operational path.
