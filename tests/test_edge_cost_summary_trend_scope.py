import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TREND_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "edge_cost_summary_trend.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

EXPECTED_EXPORTS = (
    "PaperEdgeCostSummaryTrendConfig",
    "PaperEdgeCostSummaryTrendStatusRow",
    "PaperEdgeCostSummaryTrendReport",
    "build_paper_edge_cost_summary_trend_report",
)
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.edge_cost_summary": {
        "EMPTY_STATUS",
        "OBSERVED_STATUS",
        "PaperEdgeCostSummaryReport",
    },
}
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    "polymarket_alpha_lab.edge_cost_summary",
}
FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "urllib",
    "urllib3",
    "http",
    "socket",
    "ssl",
    "websocket",
    "websockets",
    "requests",
    "httpx",
    "aiohttp",
    "importlib",
    "runpy",
    "subprocess",
    "py_clob_client",
    "clob_client",
    "web3",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "selenium",
    "playwright",
    "bs4",
    "scrapy",
    "requests_html",
    "mechanize",
    "cloudscraper",
    "curl_cffi",
    "csv",
    "sqlite3",
    "pandas",
    "polars",
    "duckdb",
    "os",
}
FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "advice",
    "api",
    "auth",
    "broker",
    "browser",
    "client",
    "credential",
    "execution",
    "fetch",
    "file",
    "financialadvice",
    "fromlog",
    "glob",
    "heartbeat",
    "http",
    "jsonl",
    "loader",
    "marketrequest",
    "network",
    "order",
    "privatekey",
    "rank",
    "recommend",
    "request",
    "scrape",
    "session",
    "submit",
    "tradeinstruction",
    "wallet",
    "websocket",
}
BANNED_SOURCE_STRING_TOKENS = {
    "advice",
    "approved",
    "eligible",
    "live",
    "promotion",
    "promoted",
    "rank",
    "recommend",
    "validated",
}


def parse_trend_module():
    return ast.parse(TREND_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            modules.extend(alias.asname for alias in node.names if alias.asname)
    return modules


def imported_first_party_symbols(tree):
    symbols = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in EXPECTED_FIRST_PARTY_IMPORTS:
            symbols.setdefault(node.module, set()).update(alias.name for alias in node.names)
    return symbols


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def assert_no_forbidden_source_strings(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        normalized = normalize_identifier(node.value)
        for token in BANNED_SOURCE_STRING_TOKENS:
            assert token not in normalized, (node.value, token)


def test_edge_cost_summary_trend_module_imports_only_allowed_dependencies():
    tree = parse_trend_module()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_edge_cost_summary_trend_module_does_not_import_forbidden_surfaces():
    tree = parse_trend_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_edge_cost_summary_trend_uses_only_allowed_first_party_symbols():
    tree = parse_trend_module()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_edge_cost_summary_trend_does_not_import_first_party_modules_wholesale():
    tree = parse_trend_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert alias.name not in EXPECTED_FIRST_PARTY_IMPORTS, alias.name


def test_edge_cost_summary_trend_does_not_define_forbidden_names():
    tree = parse_trend_module()
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
    assert_no_forbidden_source_strings(tree)


def test_edge_cost_summary_trend_public_exports_are_exact_and_report_only():
    tree = parse_trend_module()
    assert module_exports(tree) == EXPECTED_EXPORTS


def test_package_root_does_not_export_edge_cost_summary_trend_names():
    tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    exports = module_exports(tree)
    for name in EXPECTED_EXPORTS:
        assert name not in exports
