import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

MODULES = {
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_evidence_trend.py": {
        "polymarket_alpha_lab.strategy_evidence",
    },
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "outcome_freshness.py": {
        "polymarket_alpha_lab.outcome_tracker",
    },
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "nav_risk_trend.py": {
        "polymarket_alpha_lab.nav_risk_metrics",
    },
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_cost_trend.py": {
        "polymarket_alpha_lab.paper_trade_cost_audit",
    },
}

ALLOWED_STDLIB_IMPORTS = {
    "__future__",
    "ast",
    "collections",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "collections.abc",
}

FORBIDDEN_IMPORTS = {
    "api",
    "auth",
    "wallet",
    "private_key",
    "client",
    "network",
    "request",
    "http",
    "urllib",
    "journal",
    "log",
}

FORBIDDEN_CALL_NAMES = {
    "open",
    "read",
    "write",
    "rank",
    "recommend",
    "instruction",
    "advice",
}

FORBIDDEN_ATTR_NAMES = (
    "auth",
    "client",
    "delete",
    "fetch",
    "get",
    "list_markets",
    "open",
    "rank",
    "read",
    "recommend",
    "request",
    "sign",
    "submit",
    "write",
)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def parse_module(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return tuple(modules)


def imported_project_modules(tree: ast.AST) -> set[str]:
    return {
        module
        for module in imported_modules(tree)
        if module.startswith("polymarket_alpha_lab.")
    }


def assert_import_scope(path: Path) -> None:
    tree = parse_module(path)

    assert imported_project_modules(tree) == MODULES[path]
    for module in imported_modules(tree):
        if module.startswith("polymarket_alpha_lab."):
            continue
        top_level = module.split(".", 1)[0]
        assert top_level in ALLOWED_STDLIB_IMPORTS, (path.name, module)
        for fragment in FORBIDDEN_IMPORTS:
            assert normalize_identifier(fragment) not in normalize_identifier(module), (
                path.name,
                module,
                fragment,
            )


def assert_operation_scope(path: Path) -> None:
    tree = parse_module(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            if callee_name in FORBIDDEN_CALL_NAMES:
                raise AssertionError((path.name, callee_name))
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, (path.name, node.attr)


def test_strategy_evidence_trend_scope():
    path = next(iter(MODULES.keys()))
    assert_import_scope(path)
    assert_operation_scope(path)


def test_outcome_freshness_scope():
    path = list(MODULES.keys())[1]
    assert_import_scope(path)
    assert_operation_scope(path)


def test_nav_risk_trend_scope():
    path = list(MODULES.keys())[2]
    assert_import_scope(path)
    assert_operation_scope(path)


def test_paper_trade_cost_trend_scope():
    path = list(MODULES.keys())[3]
    assert_import_scope(path)
    assert_operation_scope(path)
