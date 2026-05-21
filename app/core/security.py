import re
from dataclasses import dataclass, field
from typing import Iterable, List, Pattern, Tuple

DEFAULT_MODE = "redact"
SANITIZE_MODES = {"redact", "block", "audit"}

REDACTION_PLACEHOLDER = "[REDACTED:{label}]"
INJECTION_PLACEHOLDER = "[FLAGGED:{label}]"

_SECRET_PATTERNS: Tuple[Tuple[str, str, str, Pattern[str]], ...] = (
    ("anthropic_api_key", "secret", "high",
     re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai_api_key", "secret", "high",
     re.compile(r"sk-(?!ant-)(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("aws_access_key_id", "secret", "high",
     re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", "secret", "high",
     re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("slack_token", "secret", "high",
     re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("google_api_key", "secret", "high",
     re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("jwt_token", "secret", "medium",
     re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),
    ("private_key_block", "private_key", "high",
     re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("db_url_with_credentials", "secret", "medium",
     re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s@]+@[^\s]+", re.IGNORECASE)),
    ("bearer_token", "secret", "medium",
     re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")),
)

_INJECTION_PATTERNS: Tuple[Tuple[str, str, str, Pattern[str]], ...] = (
    ("ignore_previous_instructions", "prompt_injection", "medium",
     re.compile(r"\bignore (?:all |any |the )?(?:previous|prior|above) (?:instructions|prompts|messages|rules)\b", re.IGNORECASE)),
    ("disregard_instructions", "prompt_injection", "medium",
     re.compile(r"\bdisregard (?:your|all|previous|prior|the) (?:instructions|prompt|system message)\b", re.IGNORECASE)),
    ("role_override", "prompt_injection", "low",
     re.compile(r"\byou are now (?:an?|the) [a-z][a-z _-]+\b", re.IGNORECASE)),
    ("system_token_in_content", "prompt_injection", "low",
     re.compile(r"<\|(?:im_start|im_end|system|assistant)\|>")),
)


@dataclass(frozen=True)
class Finding:
    pattern_id: str
    category: str
    severity: str
    source: str
    line_number: int
    snippet_preview: str


@dataclass(frozen=True)
class SanitizationResult:
    sanitized_text: str
    findings: List[Finding] = field(default_factory=list)
    blocked: bool = False


def normalize_mode(raw_mode: str | None) -> str:
    if not isinstance(raw_mode, str):
        return DEFAULT_MODE
    candidate = raw_mode.strip().lower()
    if candidate not in SANITIZE_MODES:
        return DEFAULT_MODE
    return candidate


class ContextSanitizer:
    """Detect and neutralize secrets / prompt-injection markers in text.

    Modes:
      - ``redact`` (default): replace matches with a redaction marker
      - ``block``: return an empty body when any high-severity finding occurs
      - ``audit``: leave the text untouched and only collect findings
    """

    def __init__(
        self,
        mode: str = DEFAULT_MODE,
        secret_patterns: Iterable[Tuple[str, str, str, Pattern[str]]] | None = None,
        injection_patterns: Iterable[Tuple[str, str, str, Pattern[str]]] | None = None,
    ) -> None:
        self.mode = normalize_mode(mode)
        self._secret_patterns = tuple(secret_patterns) if secret_patterns is not None else _SECRET_PATTERNS
        self._injection_patterns = tuple(injection_patterns) if injection_patterns is not None else _INJECTION_PATTERNS

    def sanitize(self, text: str, source: str = "unknown") -> SanitizationResult:
        if not isinstance(text, str) or not text:
            return SanitizationResult(sanitized_text=text or "", findings=[], blocked=False)

        findings: List[Finding] = []
        sanitized_text = text

        for pattern_id, category, severity, pattern in self._secret_patterns:
            sanitized_text, pattern_findings = self._apply_pattern(
                pattern_id=pattern_id,
                category=category,
                severity=severity,
                pattern=pattern,
                text=sanitized_text,
                source=source,
                placeholder=REDACTION_PLACEHOLDER,
            )
            findings.extend(pattern_findings)

        for pattern_id, category, severity, pattern in self._injection_patterns:
            sanitized_text, pattern_findings = self._apply_pattern(
                pattern_id=pattern_id,
                category=category,
                severity=severity,
                pattern=pattern,
                text=sanitized_text,
                source=source,
                placeholder=INJECTION_PLACEHOLDER,
            )
            findings.extend(pattern_findings)

        blocked = False
        if self.mode == "block" and any(item.severity == "high" for item in findings):
            return SanitizationResult(sanitized_text="", findings=findings, blocked=True)
        if self.mode == "audit":
            return SanitizationResult(sanitized_text=text, findings=findings, blocked=False)

        return SanitizationResult(sanitized_text=sanitized_text, findings=findings, blocked=blocked)

    def _apply_pattern(
        self,
        pattern_id: str,
        category: str,
        severity: str,
        pattern: Pattern[str],
        text: str,
        source: str,
        placeholder: str,
    ) -> Tuple[str, List[Finding]]:
        findings: List[Finding] = []
        matches = list(pattern.finditer(text))
        if not matches:
            return text, findings

        result_parts: List[str] = []
        cursor = 0
        for match in matches:
            line_number = text.count("\n", 0, match.start()) + 1
            snippet = _truncate(match.group(0), max_len=32)
            findings.append(
                Finding(
                    pattern_id=pattern_id,
                    category=category,
                    severity=severity,
                    source=source,
                    line_number=line_number,
                    snippet_preview=snippet,
                )
            )
            result_parts.append(text[cursor:match.start()])
            result_parts.append(placeholder.format(label=pattern_id))
            cursor = match.end()
        result_parts.append(text[cursor:])
        return "".join(result_parts), findings


def _truncate(value: str, max_len: int = 32) -> str:
    if len(value) <= max_len:
        return value
    return value[:max_len] + "..."
