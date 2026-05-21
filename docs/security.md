# Context Security Guardrails

`agent-orchestrator` sanitizes the **target-file** content it sends to any
external LLM provider. The goal is to keep two specific classes of leakage
out of provider prompts:

- **Secrets** committed to the analyzed repository (API keys, private
  keys, database URLs with credentials, JWTs, bearer tokens).
- **Prompt-injection markers** authored inside the repository content
  itself (override phrases, role-reset markers, `<|system|>` style
  control tokens).

Trusted documents under the orchestrator's own control
(`docs/bootstrap.md`, project memory, project prompts) are **not**
sanitized — they are managed by the operators of this repository.

---

## How it works

`ContextBuilder.build()` calls `ContextSanitizer.sanitize(content,
source)` for every `TARGET_FILE::` chunk before appending it to the
outgoing context. The sanitizer returns the (possibly rewritten) text
along with a list of `Finding` records that travel back on the
`ContextBundle` as `security_findings` and `blocked_files`.

Each `Finding` carries:

| Field | Description |
|---|---|
| `pattern_id` | Stable identifier of the rule that matched (e.g. `openai_api_key`) |
| `category` | `secret` / `private_key` / `prompt_injection` |
| `severity` | `high` / `medium` / `low` |
| `source` | Origin label (e.g. `target_file:src/config.py`) |
| `line_number` | 1-based line index inside the source text |
| `snippet_preview` | First 32 characters of the match (truncated) |

When an `AuditLog` instance is wired into the `ContextBuilder`, every
match also appends a `context_security_finding` event to
`var/logs/audit.jsonl` with the project id, file, mode and per-finding
metadata (no raw secret material).

---

## Modes

Mode is read from `AI_CONTEXT_SECURITY_MODE`. Unknown values fall back
to `redact`.

| Mode | Behavior |
|---|---|
| `redact` (default) | Replaces each match with `[REDACTED:<pattern_id>]` (or `[FLAGGED:<pattern_id>]` for prompt-injection patterns). The rest of the file content is preserved. |
| `block` | If **any** high-severity finding is observed, the entire file is dropped from the outgoing context and added to `bundle.blocked_files`. |
| `audit` | The original text is sent to the provider unchanged; `findings` are still collected and logged. Use only for debugging. |

`redact` is the safe default and matches the existing read-only stance
of the orchestrator.

---

## Detected patterns

### Secrets (`category = "secret"`, severity `high` unless noted)

- `anthropic_api_key` — `sk-ant-…`
- `openai_api_key` — `sk-…` (excludes `sk-ant-` prefix)
- `aws_access_key_id` — `AKIA…`
- `github_token` — `ghp_…`, `gho_…`, `ghu_…`, `ghs_…`, `ghr_…`
- `slack_token` — `xox[baprs]-…`
- `google_api_key` — `AIza…`
- `jwt_token` — `eyJ…` (severity `medium`)
- `db_url_with_credentials` — `postgres|mysql|mongodb|redis|amqp` URLs containing credentials (severity `medium`)
- `bearer_token` — `Authorization: Bearer …` (severity `medium`)

### Private keys (`category = "private_key"`)

- `private_key_block` — PEM block, including RSA / EC / DSA / OpenSSH /
  PGP variants

### Prompt injection (`category = "prompt_injection"`)

- `ignore_previous_instructions`
- `disregard_instructions`
- `role_override` — `you are now <role>` style phrases
- `system_token_in_content` — `<|im_start|>`, `<|system|>`, etc.

---

## Adding new patterns

Patterns live in `app/core/security.py` as two tuples:
`_SECRET_PATTERNS` and `_INJECTION_PATTERNS`. Each entry is
`(pattern_id, category, severity, compiled_regex)`. The order matters:
more specific patterns (e.g. `anthropic_api_key`) must appear before
broader ones (`openai_api_key`) so the first match wins.

`ContextSanitizer.__init__` accepts custom `secret_patterns` and
`injection_patterns` for tests and for any consumer that wants to layer
project-specific rules on top of the defaults.
