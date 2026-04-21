# IA-Trade Priorities Memory

## Top priorities

1. operational safety
2. correct understanding of runtime behavior
3. risk clarity
4. reversible changes
5. targeted investigation before broad edits

## What matters most

The agent should first protect:
- execution correctness
- risk correctness
- state consistency
- operational observability
- minimal blast radius of changes

## Runtime priorities

If the user asks about behavior, bugs, or changes, prioritize:
- `paper_trade.py`
- `semi_auto.py`
- `risk/`
- `execution/`
- `strategy/`

## Secondary priorities

Use these when the question is analytical, reporting-oriented, or historical:
- `analysis/`
- dashboards
- snapshots
- promotion gates
- calibration and reporting scripts

## Change policy

Default change policy:
- read-only mindset
- inspect first
- explain before editing
- prefer smallest sufficient change
- do not refactor across many files without need

## Interpretation rules

- “paper” should usually prefer `paper_trade.py`
- “risk” should usually prefer `risk/risk_manager.py` or other files under `risk/`
- “execution” should usually prefer files under `execution/`
- “strategy” should usually prefer `strategy/router.py` or relevant concrete strategy file
- “report” or “snapshot” can prioritize `analysis/`

## What to flag as higher risk

Raise explicit caution for:
- broker behavior
- position sizing
- risk state
- live execution
- safety guards
- synchronization or reconciliation
- changes that affect multiple runtime paths

## What to flag as lower risk

Usually lower risk:
- markdown files
- passive reports
- offline analysis scripts
- tests only
