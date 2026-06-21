import ast
import importlib
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_research_queue"
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_research_queue.py"
)

EXPECTED_EXPORTS = (
    "PaperStrategyCandidateResearchQueueConfig",
    "PaperStrategyCandidateResearchQueueReport",
    "PaperStrategyCandidateResearchQueueRow",
    "build_paper_strategy_candidate_research_queue_report",
)

ALLOWED_STDLIB_IMPORT_MODULES = {
    "__future__",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
}

ALLOWED_FIRST_PARTY_IMPORT_MODULES = {
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue",
    "polymarket_alpha_lab.candidate_assessment",
    "polymarket_alpha_lab.paper_strategy_selection_policy",
    "polymarket_alpha_lab.strategy_candidate_recommendation",
    "polymarket_alpha_lab.strategy_recommendation_bundle",
    "polymarket_alpha_lab.strategy_recommendation_explain",
    "polymarket_alpha_lab.strategy_recommendation_queue",
}

FORBIDDEN_IMPORT_FRAGMENTS = {
    "account",
    "aiohttp",
    "api",
    "auth",
    "cancel",
    "client",
    "eth_account",
    "execute",
    "httpx",
    "journal",
    "network",
    "order",
    "paper_execution",
    "positions",
    "private",
    "psycopg",
    "py_clob_client",
    "requests",
    "sign",
    "socket",
    "sqlalchemy",
    "sqlite3",
    "submit",
    "urllib",
    "wallet",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "input",
    "open",
    "print",
    "read",
    "write",
}


def module_spec() -> importlib.machinery.ModuleSpec:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} must be findable"
    assert spec.origin is not None, f"{MODULE_NAME} must have a source origin"
    assert Path(spec.origin).resolve() == MODULE_PATH, spec.origin
    return spec


def parse_module() -> ast.Module:
    assert MODULE_PATH.exists(), f"{MODULE_NAME} source file must exist"
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def identifier_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if character.isalnum():
            current.append(character.lower())
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def absolute_import_from_module(node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""

    package_parts = MODULE_NAME.split(".")[:-1]
    assert node.level <= len(package_parts), node.level
    base_parts = package_parts[: len(package_parts) - node.level + 1]
    if node.module:
        base_parts.extend(node.module.split("."))
    return ".".join(base_parts)


def imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(absolute_import_from_module(node))
    return modules


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                exports = ast.literal_eval(node.value)
                assert isinstance(exports, tuple)
                return exports
    raise AssertionError("__all__ assignment not found")


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def assert_import_module_is_allowed(module_name: str) -> None:
    root = module_name.split(".", 1)[0]
    assert root in ALLOWED_STDLIB_IMPORT_MODULES | {"polymarket_alpha_lab"}, module_name

    normalized_module = normalize_identifier(module_name)
    for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
        assert normalize_identifier(fragment) not in normalized_module, (
            module_name,
            fragment,
        )

    if root == "polymarket_alpha_lab":
        assert module_name in ALLOWED_FIRST_PARTY_IMPORT_MODULES, module_name
    else:
        assert module_name in ALLOWED_STDLIB_IMPORT_MODULES, module_name


def test_strategy_candidate_research_queue_module_can_be_found_and_imported():
    module_spec()
    module = importlib.import_module(MODULE_NAME)

    assert module.__name__ == MODULE_NAME
    assert module.__all__ == EXPECTED_EXPORTS


def test_strategy_candidate_research_queue_source_exists_and_ast_parses():
    module_spec()
    tree = parse_module()

    assert isinstance(tree, ast.Module)


def test_strategy_candidate_research_queue_imports_stay_paper_report_only():
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert_import_module_is_allowed(module_name)


def test_strategy_candidate_research_queue_blocks_io_and_dynamic_calls():
    tree = parse_module()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        name = call_name(node)
        if name is None:
            continue

        normalized_name = normalize_identifier(name)
        tokens = set(identifier_tokens(name))
        for forbidden_name in FORBIDDEN_CALL_NAMES:
            normalized_forbidden = normalize_identifier(forbidden_name)
            assert normalized_name != normalized_forbidden, name
            assert normalized_forbidden not in tokens, name


def test_strategy_candidate_research_queue_public_exports_are_exact():
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS
