import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_recommendation_queue.py"
)

EXPECTED_EXPORTS = {
    "PaperStrategyRecommendationQueueRow",
    "PaperStrategyRecommendationQueueSummaryReport",
    "build_paper_strategy_recommendation_queue_summary_report",
}

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    "polymarket_alpha_lab.strategy_recommendation_bundle",
}

ALLOWED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.strategy_recommendation_bundle": {
        "PaperStrategyRecommendationBundleReport",
    },
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "duckdb",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "http",
    "httpx",
    "importlib",
    "json",
    "mechanize",
    "os",
    "pandas",
    "pathlib",
    "playwright",
    "polars",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_recommendation_log",
    "py_clob_client",
    "requests",
    "requests_html",
    "runpy",
    "scrapy",
    "selenium",
    "socket",
    "sqlite3",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "accountstate",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "cancelorder",
    "credential",
    "credentialloader",
    "credentialmanager",
    "credentials",
    "dataloader",
    "executionclient",
    "fetch",
    "http",
    "liveorder",
    "network",
    "orderbuilder",
    "placeorder",
    "postorder",
    "private",
    "privatekey",
    "request",
    "secret",
    "sendorder",
    "sign",
    "signature",
    "submit",
    "submitorder",
    "token",
    "tradeclient",
    "wallet",
    "websocket",
}


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                modules.add(node.module)
    return modules


def imported_first_party_symbols(tree: ast.Module) -> dict[str, set[str]]:
    symbols: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module.startswith("polymarket_alpha_lab."):
                symbols.setdefault(node.module, set()).update(
                    alias.name for alias in node.names
                )
    return symbols


def module_exports(tree: ast.Module) -> tuple[str, ...]:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assert isinstance(node.value, (ast.Tuple, ast.List))
                    return tuple(
                        element.value
                        for element in node.value.elts
                        if isinstance(element, ast.Constant)
                        and isinstance(element.value, str)
                    )
    raise AssertionError("__all__ assignment not found")


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def test_strategy_recommendation_queue_module_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_strategy_recommendation_queue_module_does_not_import_forbidden_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_strategy_recommendation_queue_uses_only_allowed_first_party_symbols():
    tree = parse_module()
    assert imported_first_party_symbols(tree) == ALLOWED_FIRST_PARTY_IMPORTS


def test_strategy_recommendation_queue_does_not_define_forbidden_names():
    tree = parse_module()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            names.add(node.arg)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(fragment in name for name in lowered), fragment


def test_strategy_recommendation_queue_public_exports_are_paper_report_only():
    tree = parse_module()
    assigned_exports = set(module_exports(tree))
    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        normalized_name = normalize_identifier(name)
        assert normalized_name.startswith("paperstrategyrecommendationqueue") or (
            normalized_name
            == "buildpaperstrategyrecommendationqueuesummaryreport"
        )
        assert "order" not in normalized_name
        assert "execution" not in normalized_name
        assert "trade" not in normalized_name
