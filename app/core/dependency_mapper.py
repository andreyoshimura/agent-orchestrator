import ast
from pathlib import Path
from typing import Any

from app.core.context_manager import ContextManager


LOCAL_IMPORT_ROOTS = {
    "app",
    "analysis",
    "strategy",
    "scripts",
    "tests",
    "config",
    "db",
    "utils",
    "core",
}


def classify_import(name: str) -> str:
    if not name:
        return "unknown"
    root = name.split(".")[0]
    if root in LOCAL_IMPORT_ROOTS:
        return "local"
    return "external"


def extract_imports(tree: ast.AST) -> dict[str, Any]:
    imports: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    {
                        "type": "import",
                        "name": alias.name,
                        "asname": alias.asname,
                        "scope": classify_import(alias.name),
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(
                {
                    "type": "from",
                    "name": module,
                    "level": node.level,
                    "imported": [alias.name for alias in node.names],
                    "imported_details": [{"name": alias.name, "asname": alias.asname} for alias in node.names],
                    "scope": "local" if node.level > 0 else classify_import(module),
                }
            )

    local_imports = [item for item in imports if item["scope"] == "local"]
    external_imports = [item for item in imports if item["scope"] == "external"]

    return {
        "imports": imports,
        "local_import_count": len(local_imports),
        "external_import_count": len(external_imports),
        "total_import_count": len(imports),
    }


def extract_structure(tree: ast.AST) -> dict[str, Any]:
    top_level_functions: list[str] = []
    classes: list[str] = []
    methods: list[str] = []
    named_calls: list[str] = []
    attribute_calls: list[str] = []

    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(f"{node.name}.{child.name}")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            named_calls.append(node.func.id)
            continue
        if isinstance(node.func, ast.Attribute):
            attr_name = _attribute_name(node.func)
            if attr_name:
                attribute_calls.append(attr_name)

    unique_top_level_functions = sorted(set(top_level_functions))
    unique_classes = sorted(set(classes))
    unique_methods = sorted(set(methods))
    unique_named_calls = sorted(set(named_calls))
    unique_attribute_calls = sorted(set(attribute_calls))
    named_call_frequencies = _call_frequencies(named_calls)
    attribute_call_frequencies = _call_frequencies(attribute_calls)

    local_named_call_count = len(set(unique_top_level_functions).intersection(set(unique_named_calls)))

    return {
        "symbols": {
            "top_level_functions": unique_top_level_functions,
            "classes": unique_classes,
            "methods": unique_methods,
        },
        "calls": {
            "named_calls": unique_named_calls,
            "attribute_calls": unique_attribute_calls,
            "named_call_frequencies": named_call_frequencies,
            "attribute_call_frequencies": attribute_call_frequencies,
            "local_named_call_count": local_named_call_count,
        },
        "top_level_function_count": len(unique_top_level_functions),
        "class_count": len(unique_classes),
        "method_count": len(unique_methods),
        "named_call_count": len(unique_named_calls),
        "attribute_call_count": len(unique_attribute_calls),
    }


def _attribute_name(node: ast.Attribute) -> str:
    parts: list[str] = [node.attr]
    current = node.value

    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value

    if isinstance(current, ast.Name):
        parts.append(current.id)

    parts.reverse()
    return ".".join(parts)


def map_python_dependencies(repo_root: str, relative_path: str) -> dict[str, Any]:
    if not repo_root:
        return {"status": "error", "reason": "target repo not configured"}
    if not relative_path:
        return {"status": "error", "reason": "target file not provided"}
    if not relative_path.endswith(".py"):
        return {"status": "error", "reason": "target file must be a .py file"}

    ctx = ContextManager(repo_root=repo_root, max_files=1)
    try:
        content = ctx.read_file(relative_path, max_chars=50000)
    except FileNotFoundError as exc:
        return {"status": "error", "reason": str(exc)}

    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return {"status": "error", "reason": f"syntax error while parsing file: {exc}"}

    import_mapping = extract_imports(tree)
    structure_mapping = extract_structure(tree)
    target_mapping = resolve_local_import_targets(
        repo_root=repo_root,
        source_file=relative_path,
        imports=import_mapping["imports"],
    )
    mapping = {
        **import_mapping,
        **structure_mapping,
        **target_mapping,
        **build_call_relations(
            imports=import_mapping["imports"],
            named_calls=structure_mapping["calls"]["named_calls"],
            attribute_calls=structure_mapping["calls"]["attribute_calls"],
            local_import_targets=target_mapping["local_import_targets"],
            named_call_frequencies=structure_mapping["calls"]["named_call_frequencies"],
            attribute_call_frequencies=structure_mapping["calls"]["attribute_call_frequencies"],
        ),
    }

    return {
        "status": "ok",
        "file": relative_path,
        **mapping,
    }


def summarize_dependency_map(mapping: dict[str, Any]) -> dict[str, Any]:
    if mapping.get("status") != "ok":
        return {
            "status": "unavailable",
            "reason": mapping.get("reason", "dependency map unavailable"),
        }

    summary = mapping.get("call_relation_summary", {})
    top_relation = summary.get("top_relation")
    risk_flags = summary.get("risk_flags", {})
    by_priority = summary.get("by_priority", {})
    recommended_next_step = _recommended_next_step(
        risk_flags=risk_flags,
        unresolved_relations=int(mapping.get("unresolved_call_relation_count", 0)),
        high_priority_relations=int(by_priority.get("high", 0)),
    )

    return {
        "status": "ready",
        "file": mapping.get("file", ""),
        "import_counts": {
            "total": int(mapping.get("total_import_count", 0)),
            "local": int(mapping.get("local_import_count", 0)),
            "external": int(mapping.get("external_import_count", 0)),
        },
        "relation_counts": {
            "total": int(mapping.get("call_relation_count", 0)),
            "resolved": int(mapping.get("resolved_call_relation_count", 0)),
            "unresolved": int(mapping.get("unresolved_call_relation_count", 0)),
        },
        "priority_counts": {
            "high": int(by_priority.get("high", 0)),
            "medium": int(by_priority.get("medium", 0)),
            "low": int(by_priority.get("low", 0)),
        },
        "has_structural_risk": bool(risk_flags.get("has_structural_risk", False)),
        "recommended_next_step": recommended_next_step,
        "top_relation": top_relation or None,
    }


def resolve_local_import_targets(repo_root: str, source_file: str, imports: list[dict[str, Any]]) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    source_path = Path(source_file)
    source_parent = source_path.parent
    targets: list[dict[str, Any]] = []

    for item in imports:
        if item.get("scope") != "local":
            continue
        candidates = _import_candidates(item=item, source_parent=source_parent)
        resolved_path = ""
        for candidate in candidates:
            absolute = (repo / candidate).resolve()
            if absolute.exists():
                resolved_path = str(candidate)
                break
        targets.append(
            {
                "import": _import_label(item),
                "alias_tokens": _import_alias_tokens(item),
                "candidates": [str(path) for path in candidates],
                "resolved": resolved_path,
                "exists": bool(resolved_path),
                "target_symbols": _target_symbols(repo, resolved_path) if resolved_path else {"functions": [], "classes": []},
            }
        )

    existing_count = sum(1 for target in targets if target["exists"])
    return {
        "local_import_targets": targets,
        "local_import_resolved_count": existing_count,
        "local_import_unresolved_count": len(targets) - existing_count,
    }


def _import_candidates(item: dict[str, Any], source_parent: Path) -> list[Path]:
    if item.get("type") == "import":
        name = str(item.get("name", "")).strip()
        if not name:
            return []
        module_path = Path(*name.split("."))
        return [module_path.with_suffix(".py"), module_path / "__init__.py"]

    module = str(item.get("name", "")).strip()
    level = int(item.get("level", 0))
    if level > 0:
        base = _resolve_relative_base(source_parent=source_parent, level=level)
        module_path = base / Path(*module.split(".")) if module else base
    else:
        if not module:
            return []
        module_path = Path(*module.split("."))

    imported = item.get("imported", [])
    candidates = [module_path.with_suffix(".py"), module_path / "__init__.py"]
    if isinstance(imported, list):
        for name in imported:
            if not isinstance(name, str) or not name.strip():
                continue
            candidates.append(module_path / f"{name}.py")
            candidates.append(module_path / name / "__init__.py")
    return _unique_paths(candidates)


def build_call_relations(
    imports: list[dict[str, Any]],
    named_calls: list[str],
    attribute_calls: list[str],
    local_import_targets: list[dict[str, Any]],
    named_call_frequencies: dict[str, int] | None = None,
    attribute_call_frequencies: dict[str, int] | None = None,
) -> dict[str, Any]:
    target_by_import = {
        str(target.get("import", "")): target
        for target in local_import_targets
    }
    relations: list[dict[str, Any]] = []
    named_frequencies = named_call_frequencies or {}
    attribute_frequencies = attribute_call_frequencies or {}

    for item in imports:
        if item.get("scope") != "local":
            continue
        import_label = _import_label(item)
        target = target_by_import.get(import_label, {})
        resolved_path = str(target.get("resolved", ""))
        exists = bool(target.get("exists", False))
        target_symbols = target.get("target_symbols", {"functions": [], "classes": []})
        aliases = _import_alias_tokens(item)

        if item.get("type") == "from":
            imported_details = item.get("imported_details", [])
            if isinstance(imported_details, list):
                for imported in imported_details:
                    if not isinstance(imported, dict):
                        continue
                    alias = str(imported.get("asname") or imported.get("name") or "").strip()
                    if not alias:
                        continue
                    if alias in named_calls:
                        symbol_match = _target_symbol_match(alias, target_symbols)
                        call_frequency = int(named_frequencies.get(alias, 1))
                        relations.append(
                            {
                                "call": alias,
                                "relation_type": "from_import_call",
                                "import": import_label,
                                "target_file": resolved_path,
                                "target_exists": exists,
                                "target_symbol_match": symbol_match,
                                "call_frequency": call_frequency,
                            }
                        )
            continue

        for call in attribute_calls:
            if not any(call == alias or call.startswith(f"{alias}.") for alias in aliases):
                continue
            called_symbol = call.split(".")[-1]
            symbol_match = _target_symbol_match(called_symbol, target_symbols)
            call_frequency = int(attribute_frequencies.get(call, 1))
            relations.append(
                {
                    "call": call,
                    "relation_type": "module_attribute_call",
                    "import": import_label,
                    "target_file": resolved_path,
                    "target_exists": exists,
                    "target_symbol_match": symbol_match,
                    "call_frequency": call_frequency,
                }
            )

    unique_relations = _unique_relations(relations)
    for relation in unique_relations:
        score = _relation_score(
            relation_type=str(relation.get("relation_type", "")),
            target_exists=bool(relation.get("target_exists", False)),
            target_symbol_match=bool(relation.get("target_symbol_match", False)),
            call_frequency=int(relation.get("call_frequency", 1)),
        )
        relation["relation_score"] = score
        relation["relation_priority"] = _priority_label(score)

    unique_relations.sort(
        key=lambda item: (
            -int(item.get("relation_score", 0)),
            str(item.get("call", "")),
            str(item.get("target_file", "")),
        )
    )
    for index, relation in enumerate(unique_relations, start=1):
        relation["relation_rank"] = index

    resolved_count = sum(1 for relation in unique_relations if relation["target_exists"])
    risk_flags = _risk_flags(unique_relations)
    priority_counts = {
        "high": sum(1 for relation in unique_relations if relation["relation_priority"] == "high"),
        "medium": sum(1 for relation in unique_relations if relation["relation_priority"] == "medium"),
        "low": sum(1 for relation in unique_relations if relation["relation_priority"] == "low"),
    }
    return {
        "call_relations": unique_relations,
        "call_relation_count": len(unique_relations),
        "resolved_call_relation_count": resolved_count,
        "unresolved_call_relation_count": len(unique_relations) - resolved_count,
        "call_relation_summary": {
            "by_priority": priority_counts,
            "top_relation": unique_relations[0] if unique_relations else None,
            "risk_flags": risk_flags,
        },
    }


def _resolve_relative_base(source_parent: Path, level: int) -> Path:
    if level <= 1:
        return source_parent
    parts = source_parent.parts
    trim = min(level - 1, len(parts))
    return Path(*parts[: len(parts) - trim]) if trim else source_parent


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    unique: list[Path] = []
    for path in paths:
        normalized = str(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return unique


def _import_label(item: dict[str, Any]) -> str:
    if item.get("type") == "import":
        return str(item.get("name", ""))
    name = str(item.get("name", ""))
    level = int(item.get("level", 0))
    prefix = "." * level if level > 0 else ""
    return f"{prefix}{name}" if name else prefix or "<unknown>"


def _target_symbols(repo: Path, relative_path: str) -> dict[str, list[str]]:
    absolute = (repo / relative_path).resolve()
    if not absolute.exists() or not absolute.is_file():
        return {"functions": [], "classes": []}
    try:
        content = absolute.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = absolute.read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"functions": [], "classes": []}

    functions: list[str] = []
    classes: list[str] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {
        "functions": sorted(set(functions)),
        "classes": sorted(set(classes)),
    }


def _import_alias_tokens(item: dict[str, Any]) -> list[str]:
    if item.get("type") == "import":
        explicit_alias = str(item.get("asname") or "").strip()
        if explicit_alias:
            return [explicit_alias]
        name = str(item.get("name") or "").strip()
        if not name:
            return []
        return [name.split(".")[0]]

    imported_details = item.get("imported_details", [])
    aliases: list[str] = []
    if isinstance(imported_details, list):
        for imported in imported_details:
            if not isinstance(imported, dict):
                continue
            alias = str(imported.get("asname") or imported.get("name") or "").strip()
            if alias:
                aliases.append(alias)
    return sorted(set(aliases))


def _unique_relations(relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen = set()
    for relation in relations:
        signature = (
            relation.get("call"),
            relation.get("relation_type"),
            relation.get("import"),
            relation.get("target_file"),
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(relation)
    return unique


def _target_symbol_match(symbol: str, target_symbols: dict[str, Any]) -> bool:
    if not symbol:
        return False
    functions = target_symbols.get("functions", [])
    classes = target_symbols.get("classes", [])
    return symbol in functions or symbol in classes


def _relation_score(relation_type: str, target_exists: bool, target_symbol_match: bool, call_frequency: int) -> int:
    base_score = 70 if relation_type == "from_import_call" else 50
    if target_exists:
        base_score += 30
    if target_symbol_match:
        base_score += 15
    if call_frequency > 1:
        base_score += min((call_frequency - 1) * 5, 20)
    return base_score


def _call_frequencies(calls: list[str]) -> dict[str, int]:
    frequencies: dict[str, int] = {}
    for call in calls:
        frequencies[call] = frequencies.get(call, 0) + 1
    return frequencies


def _priority_label(score: int) -> str:
    if score >= 100:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def _risk_flags(relations: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved_high_frequency = [
        {
            "call": relation.get("call"),
            "import": relation.get("import"),
            "call_frequency": relation.get("call_frequency"),
            "relation_score": relation.get("relation_score"),
        }
        for relation in relations
        if not relation.get("target_exists") and int(relation.get("call_frequency", 1)) >= 2
    ]
    unresolved_high_priority = [
        {
            "call": relation.get("call"),
            "import": relation.get("import"),
            "relation_priority": relation.get("relation_priority"),
            "relation_score": relation.get("relation_score"),
        }
        for relation in relations
        if not relation.get("target_exists") and relation.get("relation_priority") == "high"
    ]
    return {
        "unresolved_high_frequency": unresolved_high_frequency,
        "unresolved_high_priority": unresolved_high_priority,
        "has_structural_risk": bool(unresolved_high_frequency or unresolved_high_priority),
    }


def _recommended_next_step(risk_flags: dict[str, Any], unresolved_relations: int, high_priority_relations: int) -> str:
    unresolved_high_frequency = risk_flags.get("unresolved_high_frequency", [])
    unresolved_high_priority = risk_flags.get("unresolved_high_priority", [])

    if unresolved_high_frequency:
        return "Validate unresolved high-frequency relations first and align import paths or module structure."
    if unresolved_high_priority:
        return "Review unresolved high-priority relations and confirm whether targets were moved or renamed."
    if unresolved_relations > 0:
        return "Investigate unresolved call relations to prevent dependency drift."
    if high_priority_relations > 0:
        return "Review high-priority resolved relations and confirm they match intended architecture."
    return "No immediate structural risk detected; keep dependency map as baseline for future diffs."
