# IA-Trade Architecture Memory

## Operational shape

IA-Trade is organized around a separation between:
- runtime / operational entrypoints
- execution and risk controls
- strategy logic
- analysis and reporting
- tests

## Main operational flow

Typical reasoning about the system should start from:
1. top-level entrypoint
2. strategy selection or signal logic
3. risk evaluation / position sizing
4. execution planning or paper execution
5. persistence, reporting, or notification

## Architectural areas

### Runtime entrypoints
Files that often represent user-facing or operational behavior:
- `paper_trade.py`
- `semi_auto.py`
- `main.py`

### Strategy layer
Contains strategy logic and routing:
- `strategy/router.py`
- `strategy/breakout_structural.py`
- `strategy/range_mean_reversion.py`
- `strategy/pullback_trend.py`
- `strategy/sentiment_filter.py`
- `strategy/strategy_contract.py`

### Risk layer
Contains risk policy and position sizing behavior:
- `risk/risk_manager.py`
- `risk/live_risk_policy.py`
- `risk/live_risk_state.py`

### Execution layer
Contains broker and execution concerns:
- `execution/broker.py`
- `execution/live_executor.py`
- `execution/position_sync.py`
- `execution/safety_guard.py`
- `execution/models.py`

### Analysis layer
Contains reports, snapshots, calibration, analytics, and support scripts:
- `analysis/phase4_status_report.py`
- `analysis/live_risk_report.py`
- `analysis/strategy_context_report.py`
- `analysis/postgres_replica_sync.py`
- other files under `analysis/`

These files are important, but usually secondary to runtime files when the task is broad.

### Utilities and data
Support layers:
- `utils/`
- `data/`
- `config.py`

## Architectural reading order

When the user asks broad operational questions, prefer this order:
1. top-level entrypoint
2. direct imports from strategy/risk/execution
3. config and utilities
4. analysis/reporting modules
5. tests

When the user asks about reports or metrics, analysis modules can be first.

## Heuristics for file selection

Prefer:
- root runtime files
- core domain folders (`risk/`, `execution/`, `strategy/`)
- exact file-name matches
- non-test files

Deprioritize:
- `tests/`
- `analysis/` for broad runtime questions
- duplicates or copied files
- `__init__.py` unless module shape matters
