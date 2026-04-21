# IA-Trade Commands Memory

## Local environment

Activate the orchestrator environment:

```bash
source .venv/bin/activate
set -a && source .env && set +a
```

## Orchestrator commands

### Explain a known file

```bash
bash scripts/task.sh explain-file README.md
bash scripts/task.sh explain-file AGENTS.md
```

### Review a known file

```bash
bash scripts/task.sh review-file README.md
bash scripts/task.sh review-file AGENTS.md
```

### Summarize core project area

```bash
bash scripts/task.sh summarize-repo-area
bash scripts/task.sh summarize-repo-area README.md AGENTS.md
```

### Map dependencies of a Python file

```bash
bash scripts/task.sh map-dependencies paper_trade.py
bash scripts/task.sh map-dependencies semi_auto.py
```

### List Python files

```bash
bash scripts/task.sh list-python-files
```

### Pick best Python file by partial name

```bash
bash scripts/task.sh pick-python-file paper
bash scripts/task.sh pick-python-file risk
bash scripts/task.sh pick-python-file strategy
```

### Explain best Python match

```bash
bash scripts/task.sh explain-best-python-match paper
bash scripts/task.sh explain-best-python-match risk
```

### Review best Python match

```bash
bash scripts/task.sh review-best-python-match paper
bash scripts/task.sh review-best-python-match risk
```

## Repo target

Expected target repo:

```bash
echo "$AI_TARGET_REPO"
```

Expected value:

```text
../IA-Trade
```

## Notes

- Prefer `python3` in this environment.
- The orchestrator is read-only by default.
- Use partial-name matching when the exact file path is unknown.
