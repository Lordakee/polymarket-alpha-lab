from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "phase_2_readiness_streak.py"
)

ALLOWED_PROJECT_IMPORTS = {
    "polymarket_alpha_lab.phase_2_observability_state",
}

ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "typing",
}

FORBIDDEN_IMPORT_FRAGMENTS = {
    "api",
    "auth",
    "client",
    "http",
    "journal",
    "log",
    "network",
    "private_key",
    "request",
    "urllib",
    "wallet",
}

FORBIDDEN_IDENTIFIER_FRAGMENTS = {
    "advice",
    "auth",
    "client",
    "fetch",
    "http",
    "invest",
    "live",
    "network",
    "order",
    "rank",
    "recommend",
    "request",
    "score",
    "submit",
    "wallet",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "hasattr",
    "input",
    "locals",
    "open",
    "print",
    "read",
    "setattr",
    "write",
}

FORBIDDEN_ATTR_NAMES = {
    "append",
    "connect",
    "delete",
    "execute",
    "fetch",
    "get",
    "iterdir",
    "list_markets",
    "mkdir",
    "open",
    "post",
    "read",
    "request",
    "send",
    "sign",
    "submit",
    "write",
}

ALLOWED_IDENTIFIER_NAMES = {
    "BLOCKING_REASON_NAMES",
    "blocking_reason_names",
    "latest_blocking_reason_names",
    "not_ready_report_count",
    "consecutive_not_ready_count",
}

ALLOWED_STRING_VALUES = {
    "PaperPhase2ReadinessStreakConfig",
    "PaperPhase2ReadinessStreakReport",
    "build_paper_phase_2_readiness_streak_report",
    "latest_phase_2_ready",
    "consecutive_ready_count",
    "consecutive_not_ready_count",
    "ready_report_count",
    "not_ready_report_count",
    "state_reports must be a list or tuple",
    "state_reports must contain PaperPhase2ObservabilityStateReport values",
    "state_reports must contain paper_only reports",
    "state_reports must contain report_only reports",
    "state_reports must contain readonly reports",
    "config must be a PaperPhase2ReadinessStreakConfig",
    "generated_at must be a datetime",
    "config_version must be a string",
    "config_version must be a canonical nonblank string",
    "generated_at must be a datetime",
    "state_report_count must be an int",
    "state_report_count must be nonnegative",
    "consecutive_ready_count must be an int",
    "consecutive_ready_count must be nonnegative",
    "consecutive_not_ready_count must be an int",
    "consecutive_not_ready_count must be nonnegative",
    "ready_report_count must be an int",
    "ready_report_count must be nonnegative",
    "not_ready_report_count must be an int",
    "not_ready_report_count must be nonnegative",
    "latest_phase_2_ready must be a bool or None",
    "latest_blocking_reason_names must be an iterable",
    "latest_blocking_reason_names must not contain duplicates",
    "latest_blocking_reason_names must contain known names",
    "latest_blocking_reason_names must use deterministic sequence",
    "state_report_count must match ready and not-ready counts",
    "latest_phase_2_ready must be absent without state reports",
    "latest_blocking_reason_names must be absent without state reports",
    "consecutive streaks must be zero without state reports",
    "latest_phase_2_ready is required with state reports",
    "ready latest report must have a ready streak",
    "ready latest report must not have a not-ready streak",
    "ready latest report must not have blocking reasons",
    "not-ready latest report must have a not-ready streak",
    "not-ready latest report must not have a ready streak",
    "not-ready latest report must have blocking reasons",
    "consecutive_ready_count must not exceed ready_report_count",
    "consecutive_not_ready_count must not exceed not_ready_report_count",
    "paper_only must be True",
    "report_only must be True",
    "readonly must be True",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module() -> ast.AST:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def identifier_candidates(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.arg):
        return (node.arg,)
    if isinstance(node, ast.Attribute):
        return (node.attr,)
    if isinstance(node, ast.alias):
        return tuple(value for value in (node.name, node.asname) if value is not None)
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return (node.name,)
    return ()


def test_readiness_streak_import_scope_is_local_and_report_only():
    tree = parse_module()

    for module in imported_modules(tree):
        if module.startswith("polymarket_alpha_lab."):
            assert module in ALLOWED_PROJECT_IMPORTS
        else:
            assert module in ALLOWED_STDLIB_IMPORTS
        normalized_module = normalize_identifier(module)
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
            assert normalize_identifier(fragment) not in normalized_module, (
                module,
                fragment,
            )


def test_readiness_streak_has_no_forbidden_names_or_aliases():
    tree = parse_module()

    for node in ast.walk(tree):
        for candidate in identifier_candidates(node):
            if candidate in ALLOWED_IDENTIFIER_NAMES:
                continue
            normalized_candidate = normalize_identifier(candidate)
            for fragment in FORBIDDEN_IDENTIFIER_FRAGMENTS:
                assert normalize_identifier(fragment) not in normalized_candidate, (
                    candidate,
                    fragment,
                )


def test_readiness_streak_has_no_forbidden_calls_or_attributes():
    tree = parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node)
            assert name not in FORBIDDEN_CALL_NAMES, name
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr


def test_readiness_streak_has_no_dynamic_escape_strings():
    tree = parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in ALLOWED_STRING_VALUES:
                continue
            normalized_value = normalize_identifier(node.value)
            for fragment in FORBIDDEN_IDENTIFIER_FRAGMENTS | FORBIDDEN_CALL_NAMES:
                assert normalize_identifier(fragment) not in normalized_value, (
                    node.value,
                    fragment,
                )
