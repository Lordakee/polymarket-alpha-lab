import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_attribution.py"

EXPECTED_EXPORTS = (
    "PaperTradeAttributionConfig",
    "PaperTradeAttributionReport",
    "PaperTradeAttributionRow",
    "build_paper_trade_attribution_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.outcome_tracker",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
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
    "playwright",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.llm_forecast",
    "polymarket_alpha_lab.llm_research_transport",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_portfolio_nav",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_cycle",
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
    "accountstate",
    "advice",
    "advisor",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "client",
    "credential",
    "executionclient",
    "financialadvice",
    "fetch",
    "golive",
    "liveclient",
    "orderclient",
    "orderinstruction",
    "orderpayload",
    "orderplacement",
    "orderrequest",
    "placeorder",
    "privatekey",
    "rankinvestment",
    "ranking",
    "recommend",
    "recommendation",
    "routeorder",
    "sdk",
    "signorder",
    "submitorder",
    "transport",
    "wallet",
    "websocket",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "orderrequestedsize",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path: Path = MODULE_PATH) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree: ast.AST) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def test_paper_trade_attribution_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_paper_trade_attribution_does_not_import_live_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_paper_trade_attribution_public_exports_exactly_paper_report_api():
    assert module_exports(parse_module()) == EXPECTED_EXPORTS


def test_paper_trade_attribution_does_not_define_forbidden_live_or_advice_names():
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
        assert not any(
            normalize_identifier(fragment) in name
            for name in lowered
            if name not in ALLOWED_FORBIDDEN_NAME_MATCHES
        ), (
            fragment,
            lowered,
        )
