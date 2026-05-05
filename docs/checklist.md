# Operational Checklist

## Before starting a session

- [ ] Run `bash scripts/start_ai_session.sh`
- [ ] Healthcheck is `ok`: `bash scripts/healthcheck.sh --all --strict`
- [ ] Project profile loaded: `bash scripts/task.sh inspect-project`
- [ ] No budget exhausted: `bash scripts/task.sh inspect-budget`
- [ ] Read `.ai_context/SESSION_STATE.md` to confirm where we left off
- [ ] `AI_TARGET_REPO` is set and target repo is accessible

## Before making changes

- [ ] Declare scope: DOCS / RUNTIME / PROVIDERS / ROUTING / BUDGET / PROJECT_PROFILE / STORAGE / SCRIPTS
- [ ] Use `inspect-task` to preview routing before executing live tasks
- [ ] Confirm whether the change is global layer or project layer — not both
- [ ] Changes to `config/` require a short justification
- [ ] Changes to `app/core/` require explicit rollback plan

## After a session

- [ ] Run `bash scripts/end_ai_session.sh "summary"`
- [ ] Commit with a scope-prefixed message (e.g., `feat(core):`, `fix(providers):`, `docs:`)
- [ ] Push to remote if the session is complete
- [ ] Verify `bash scripts/healthcheck.sh --all --strict` returns `ok`

## Periodic maintenance

- [ ] `bash scripts/task.sh purge-cache` when cache grows large
- [ ] `bash scripts/task.sh inspect-budget` to review daily spend
- [ ] `bash scripts/generate_ai_bundle.sh` after significant doc changes
- [ ] Review `.ai_context/SESSION_STATE.md` for stale state

## Adding a new project profile

- [ ] Create `projects/<project_id>/project.yaml`
- [ ] Add `AGENT_CONTEXT.md`, `CODEX_BOOTSTRAP.md`
- [ ] Add `memory/` and `prompts/` directories
- [ ] Set `AI_DEFAULT_PROJECT=<project_id>` in `.env`
- [ ] Run `bash scripts/task.sh inspect-project` to validate
