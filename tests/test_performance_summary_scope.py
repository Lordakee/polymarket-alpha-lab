"""Scope contract for ``polymarket_alpha_lab.performance_summary`` (Stage 6).

Pure leaf: aggregate the three persisted history streams (cycle reports, paper
trades, NAV snapshots) into a single performance summary. Read-only data
analysis over already-typed tuples; no fetch, no api, no live surfaces.

ALLOWED stdlib + ``polymarket_alpha_lab.{strategy_cycle, journal, positions}``
(it imports the report types). NO api. Six canonical scope tests plus the
package-root export check.
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "performance_summary.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"

EXPECTED_EXPORTS = (
    "PerformanceSummaryConfig",
    "PerformanceSummary",
    "build_performance_summary",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    # performance_summary imports only the report types it aggregates.
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.strategy_cycle",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "aiohttp",
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
    "mechanize",
    "os",
    "pandas",
    "playwright",
    "polars",
    "polymarket",
    # Everything polymarket_alpha_lab.* EXCEPT the three allowed report leaves
    # (journal, positions, strategy_cycle) is forbidden -- notably api.
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.book_imbalance_forecast",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.cost_aware_event_strategy",
    "polymarket_alpha_lab.cost_aware_snapshot_builder",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.forecast_provider",
    "polymarket_alpha_lab.json_recovery",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_portfolio_nav",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.project_screening",
    "polymarket_alpha_lab.proposal_evidence_comparison",
    "polymarket_alpha_lab.proposal_evidence_comparison_history",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "polymarket_alpha_lab.scoring",
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
    "credentialloader",
    "credentialmanager",
    "credentials",
    "dataloader",
    "executionclient",
    "fetch",
    "financialadvice",
    "fromfile",
    "golive",
    "historyloader",
    "investmentranking",
    "jsonlloader",
    "jsonlreader",
    "killswitch",
    "live",
    "liveclient",
    "liveexecution",
    "loader",
    "orderclient",
    "orderinstruction",
    "orderpayload",
    "orderplacement",
    "orderrequest",
    "placeorder",
    "privatekey",
    "rank",
    "rankinvestment",
    "ranking",
    "recommend",
    "recommendation",
    "routeorder",
    "sdk",
    "sign",
    "signorder",
    "submitorder",
    "tradeinstruction",
    "transport",
    "transportclient",
    "wallet",
    "websocket",
}

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = {
    "account",
    "advice",
    "advisor",
    "auth",
    "broker",
    "browser",
    "client",
    "credential",
    "financialadvice",
    "investment",
    "live",
    "loader",
    "orderclient",
    "orderinstruction",
    "orderplacement",
    "orderrequest",
    "placeorder",
    "rank",
    "ranking",
    "recommend",
    "recommendation",
    "transport",
    "wallet",
    "websocket",
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


def public_export_fragment_matches(name: str) -> bool:
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_performance_summary_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_performance_summary_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    runtime_imports = imported_modules(tree)
    for module_name in runtime_imports:
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name
    # The live-layer headline: this module MUST NOT import api.
    assert not any(
        module_matches_prefix(name, "polymarket_alpha_lab.api")
        for name in runtime_imports
    ), runtime_imports


def test_performance_summary_public_exports_exactly_summary_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_performance_summary_does_not_define_forbidden_live_or_advice_surface_names():
    tree = parse_module()
    names: set[str] = set()
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


def test_package_root_exports_performance_summary_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    summary_exports = tuple(
        name for name in package_exports if name in EXPECTED_EXPORTS
    )
    assert set(summary_exports) == set(EXPECTED_EXPORTS)
    for name in summary_exports:
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.performance_summary"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_performance_summary_sections_keep_paper_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    status_start = readme.index("## Performance Summary v0 Status")
    api_start = readme.index("## Performance Summary v0 Python API", status_start)
    next_section = readme.find("\n## ", api_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[status_start:next_section])

    required_fragments = (
        "performancesummaryv0status",
        "performancesummaryv0pythonapi",
        "paperonly",
        "reportonly",
        "nofetch",
        "noauth",
        "nowallet",
        "noorder",
        "norank",
        "norecommend",
        "nofinancialadvice",
    )
    for fragment in required_fragments:
        assert fragment in normalized, fragment
