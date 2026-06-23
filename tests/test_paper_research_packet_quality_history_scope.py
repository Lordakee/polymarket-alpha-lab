import ast
import importlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "polymarket_alpha_lab.paper_research_packet_quality_history"
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_research_packet_quality_history.py"
)

EXPECTED_EXPORTS = (
    "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_HISTORY_CONFIG_VERSION",
    "PaperResearchPacketQualityHistoryConfig",
    "PaperResearchPacketQualityHistoryCheckSummaryRow",
    "PaperResearchPacketQualityHistoryRecurringReasonCodeRow",
    "PaperResearchPacketQualityHistoryReport",
    "PaperResearchPacketQualityHistoryStatusRow",
    "build_paper_research_packet_quality_history_report",
)

ALLOWED_STDLIB_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
}
ALLOWED_FIRST_PARTY_IMPORT_MODULES = {
    "polymarket_alpha_lab.paper_research_packet_quality",
}

FORBIDDEN_LIVE_OR_BOUNDARY_TERMS = {
    "account",
    "api",
    "auth",
    "browser",
    "cancel",
    "client",
    "cli",
    "commit",
    "connect",
    "credential",
    "database",
    "db",
    "delete",
    "env",
    "exchange",
    "execute",
    "http",
    "insert",
    "live",
    "mutation",
    "mutate",
    "network",
    "order",
    "private",
    "psycopg",
    "request",
    "rollback",
    "secret",
    "sign",
    "signing",
    "socket",
    "submit",
    "trade",
    "wallet",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "connect",
    "eval",
    "exec",
    "input",
    "insert",
    "open",
    "print",
    "read",
    "request",
    "rollback",
    "submit",
    "update",
    "write",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def collected_source_terms(tree: ast.Module) -> set[str]:
    terms: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            terms.add(node.name)
        elif isinstance(node, ast.Name):
            terms.add(node.id)
        elif isinstance(node, ast.Attribute):
            terms.add(node.attr)
        elif isinstance(node, ast.arg):
            terms.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            terms.add(node.arg)
        elif isinstance(node, ast.alias):
            terms.add(node.name)
            if node.asname is not None:
                terms.add(node.asname)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            terms.add(node.value)
    return terms


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def test_paper_research_packet_quality_history_module_can_be_found_and_imported():
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None
    assert spec.origin is not None
    assert Path(spec.origin).resolve() == MODULE_PATH

    module = importlib.import_module(MODULE_NAME)

    assert module.__name__ == MODULE_NAME


def test_paper_research_packet_quality_history_imports_only_allowed_dependencies():
    tree = parse_module()

    for module_name in imported_modules(tree):
        if module_name.startswith("polymarket_alpha_lab"):
            assert module_name in ALLOWED_FIRST_PARTY_IMPORT_MODULES, module_name
        else:
            assert module_name in ALLOWED_STDLIB_IMPORT_MODULES, module_name


def test_paper_research_packet_quality_history_exports_only_public_reducer_api():
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_paper_research_packet_quality_history_does_not_mention_forbidden_surfaces():
    tree = parse_module()
    normalized_terms = {
        normalize_identifier(term)
        for term in collected_source_terms(tree)
        if normalize_identifier(term) != "readonly"
    }

    for forbidden in FORBIDDEN_LIVE_OR_BOUNDARY_TERMS:
        normalized_forbidden = normalize_identifier(forbidden)
        assert not any(
            normalized_forbidden in term for term in normalized_terms
        ), forbidden


def test_paper_research_packet_quality_history_does_not_perform_io_or_dynamic_execution():
    tree = parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name is not None:
                assert name not in FORBIDDEN_CALL_NAMES, name
