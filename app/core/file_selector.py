from dataclasses import dataclass
from pathlib import Path


IGNORED_PARTS = {
    "venv",
    ".venv",
    "__pycache__",
    "site-packages",
    ".git",
}


DEFAULT_TASK_QUERIES = {
    "review-snippet": ["snippet", "review"],
    "review-diff": ["diff", "review"],
    "review-file": ["file", "review"],
    "explain-file": ["explain", "file"],
    "map-dependencies": ["dependencies", "imports"],
}

DEFAULT_TASK_LIMITS = {
    "review-snippet": 1,
    "review-diff": 2,
    "review-file": 1,
    "explain-file": 1,
    "map-dependencies": 1,
}


@dataclass(frozen=True)
class RankedFile:
    file: str
    score: int


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.parts)


def collect_python_files(root: Path) -> list[str]:
    files = []
    for path in root.rglob("*.py"):
        if should_ignore(path):
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        files.append(str(relative))
    files.sort()
    return files


def score_match(query: str, candidate: str) -> int:
    q = query.lower().strip()
    if not q:
        return 0

    c = candidate.lower()
    path = Path(candidate)
    filename = path.name.lower()
    stem = path.stem.lower()

    score = 0
    if q == c:
        score += 100
    if q == stem:
        score += 80
    if filename.startswith(q):
        score += 35
    if c.endswith(q):
        score += 25
    if q in filename:
        score += 20
    if q in c:
        score += 10

    if score <= 0:
        return 0

    if len(path.parts) == 1:
        score += 20

    if "tests" in path.parts:
        score -= 25
    if "analysis" in path.parts:
        score -= 10
    if filename == "__init__.py":
        score -= 20
    if "(cópia)" in filename:
        score -= 30

    return score


def rank_python_files(query: str, files: list[str]) -> list[RankedFile]:
    ranked = []
    for candidate in files:
        score = score_match(query, candidate)
        if score > 0:
            ranked.append(RankedFile(file=candidate, score=score))
    ranked.sort(key=lambda item: (-item.score, item.file))
    return ranked


def choose_best_python_match(query: str, files: list[str]) -> RankedFile | None:
    ranked = rank_python_files(query, files)
    return ranked[0] if ranked else None


def infer_queries(task_type: str, objective: str = "", query: str = "") -> list[str]:
    queries: list[str] = []
    if query.strip():
        queries.append(query.strip())

    for token in _tokenize_objective(objective):
        if token not in queries:
            queries.append(token)

    for token in DEFAULT_TASK_QUERIES.get(task_type, []):
        if token not in queries:
            queries.append(token)

    return queries


def auto_select_python_files(
    root: Path,
    task_type: str,
    objective: str = "",
    query: str = "",
    limit: int = 3,
) -> list[RankedFile]:
    files = collect_python_files(root)
    inferred_queries = infer_queries(task_type=task_type, objective=objective, query=query)
    merged_scores: dict[str, int] = {}
    best_per_query: dict[str, RankedFile] = {}

    for inferred_query in inferred_queries:
        ranked_for_query = rank_python_files(inferred_query, files)
        if ranked_for_query:
            best_per_query[inferred_query] = ranked_for_query[0]
        for item in ranked_for_query:
            merged_scores[item.file] = merged_scores.get(item.file, 0) + item.score

    ranked = [RankedFile(file=file, score=score) for file, score in merged_scores.items() if score > 0]
    ranked.sort(key=lambda item: (-item.score, item.file))
    task_limit = DEFAULT_TASK_LIMITS.get(task_type, limit)
    constrained_limit = min(limit, task_limit)
    if _has_comparative_intent(task_type=task_type, objective=objective):
        return _trim_comparative_results(ranked, best_per_query, inferred_queries, constrained_limit)
    return _trim_ranked_results(ranked, constrained_limit)


def _tokenize_objective(objective: str) -> list[str]:
    cleaned = objective.lower()
    for char in ",.:;!?()[]{}\"'":
        cleaned = cleaned.replace(char, " ")

    tokens = []
    seen = set()
    for token in cleaned.split():
        if len(token) < 4:
            continue
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def _trim_ranked_results(ranked: list[RankedFile], limit: int) -> list[RankedFile]:
    if not ranked or limit <= 0:
        return []

    best_score = ranked[0].score
    if limit == 1:
        return [ranked[0]]

    floor_score = max(best_score - 15, 1)
    trimmed = [item for item in ranked if item.score >= floor_score]
    return trimmed[:limit]


def _trim_comparative_results(
    ranked: list[RankedFile],
    best_per_query: dict[str, RankedFile],
    inferred_queries: list[str],
    limit: int,
) -> list[RankedFile]:
    if not ranked or limit <= 0:
        return []

    selected: list[RankedFile] = []
    seen = set()

    for inferred_query in inferred_queries:
        item = best_per_query.get(inferred_query)
        if item is None or item.file in seen:
            continue
        selected.append(item)
        seen.add(item.file)
        if len(selected) >= limit:
            return selected

    for item in _trim_ranked_results(ranked, limit):
        if item.file in seen:
            continue
        selected.append(item)
        seen.add(item.file)
        if len(selected) >= limit:
            break

    return selected


def _has_comparative_intent(task_type: str, objective: str) -> bool:
    lowered = objective.lower()
    if task_type in {"review-diff", "compare-options"}:
        return True
    comparative_markers = ("compare", "comparar", "versus", " vs ", " contra ")
    return any(marker in lowered for marker in comparative_markers)
