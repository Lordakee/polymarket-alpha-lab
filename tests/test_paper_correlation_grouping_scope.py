import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_correlation_grouping.py"
)

EXPECTED_EXPORTS = (
    "PaperCorrelationGroupingConfig",
    "PaperCorrelationInputRow",
    "PaperCorrelationGroupRow",
    "PaperCorrelationGroupingReport",
    "build_paper_correlation_grouping_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
    "asyncio",
    "bs4",
    "clob_client",
    "cloudscraper",
    "curl_cffi",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "mechanize",
    "os",
    "pathlib",
    "playwright",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_portfolio_nav",
    "polymarket_alpha_lab.runner",
    "py_clob_client",
    "requests",
    "requests_html",
    "scrapy",
    "selenium",
    "socket",
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
    "client",
    "credential",
    "executionclient",
    "fetch",
    "golive",
    "http",
    "liveclient",
    "network",
    "orderclient",
    "orderconstruction",
    "orderinstruction",
    "orderpayload",
    "orderplacement",
    "orderrequest",
    "placeorder",
    "privatekey",
    "routeorder",
    "sdk",
    "sign",
    "signorder",
    "submitorder",
    "transport",
    "wallet",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "open",
    "compile",
    "eval",
    "exec",
    "input",
    "print",
    "__import__",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree: ast.Module) -> list[str]:
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


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


def test_paper_correlation_grouping_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_paper_correlation_grouping_does_not_import_live_mutation_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_paper_correlation_grouping_exports_only_report_api():
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_paper_correlation_grouping_does_not_define_forbidden_surfaces():
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
        elif isinstance(node, ast.alias):
            names.add(node.name)
            if node.asname is not None:
                names.add(node.asname)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(normalize_identifier(fragment) in name for name in lowered), (
            fragment,
            lowered,
        )


def test_paper_correlation_grouping_does_not_perform_io_or_dynamic_execution():
    tree = parse_module()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
