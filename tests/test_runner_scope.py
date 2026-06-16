"""Scope contract for ``polymarket_alpha_lab.runner`` (Stage 7 continuous run).

Stage 7 live-layer orchestrator: a thin synchronous ``time.sleep`` loop that
chains the already-tested Stage 1b/4/5 primitives -- ``run_strategy_cycle``,
``PaperStrategyCycleLog.append``, ``mark_paper_portfolio_nav`` -- manufacturing
the longitudinal data (cycles + paper trades + NAV marks) needed for promotion
gates and forecast calibration.

Protocol-only (Q5): this module does NOT import ``api``. It reuses
``strategy_cycle.MarketDataClient`` (a superset of
``paper_portfolio_nav.MarketNavClient``) as the injected client surface;
``cli.py`` constructs the concrete ``PolymarketPublicClient`` and injects it.

Phase 1 boundary: pure composition of paper-only + read-only primitives,
repeated. No live orders, auth, wallets, credentials, account/position reads,
or exchange writes. Synchronous ``time.sleep`` loop only (async/scheduler is a
later stage).

Six canonical scope tests plus the package-root export check and the README
section boundary check.
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "runner.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"

EXPECTED_EXPORTS = (
    "RunLoopSummary",
    "run_strategy_loop",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "time",
    # Q5: runner.py is Protocol-only -- it does NOT import api. It composes the
    # tested live-layer orchestrators: strategy_cycle (run_strategy_cycle +
    # PaperStrategyCycleLog + MarketDataClient + PaperStrategyCycleConfig),
    # paper_portfolio_nav (mark_paper_portfolio_nav), and reuses pipeline's
    # MarketScanConfig for the scan-config type. The concrete MarketDataClient
    # is injected by cli.py.
    "polymarket_alpha_lab.paper_portfolio_nav",
    "polymarket_alpha_lab.pipeline",
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
    # Everything polymarket_alpha_lab.* EXCEPT the three allowed live layers
    # (paper_portfolio_nav, pipeline, strategy_cycle) is forbidden -- notably
    # api, journal, positions, paper_execution (accessed transitively through
    # the composed orchestrators, never imported directly here).
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
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.json_recovery",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
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

# NOTE: bare "client" is intentionally NOT forbidden here -- the mandated public
# API is run_strategy_loop(*, client: MarketDataClient, ...) and the reused
# Protocol is named MarketDataClient (Q5). Only the concrete LIVE/broker/
# credential/order surfaces are forbidden so no real execution/credential
# client can slip in.
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
    "execution",
    "financialadvice",
    "investment",
    "live",
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

# Names this orchestrator legitimately references even though they overlap
# with otherwise-reserved vocabulary. "MarketDataClient" / "client" are the
# reused Protocol + injected param (Q5); the loop composes the paper-only /
# report-only cycle + NAV surface. "RunLoopSummary" / "run_strategy_loop" are
# the mandated public API (carrying no forbidden surface).
ALLOWED_REQUIRED_DOMAIN_NAMES = {
    "MarketDataClient",
    "RunLoopSummary",
    "PaperStrategyCycleConfig",
    "PaperStrategyCycleLog",
    "PaperStrategyCycleReport",
    "MarketScanConfig",
    "client",
    "cycle_config",
    "cycle_report_log_path",
    "nav_log_path",
    "on_cycle_error",
    "repeat_mode",
    "interval_seconds",
    "max_iterations",
    "starting_cash",
    "marked_at",
    "run_strategy_loop",
    "run_strategy_cycle",
    "mark_paper_portfolio_nav",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path: Path = MODULE_PATH) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> list[str]:
    """Return runtime-imported module names (skipping TYPE_CHECKING guards)."""
    modules: list[str] = []

    def visit(node: ast.AST, guarded: bool) -> None:
        if isinstance(node, ast.Import):
            if not guarded:
                modules.extend(alias.name for alias in node.names)
            return
        if isinstance(node, ast.ImportFrom):
            if not guarded:
                assert node.level == 0
                modules.append(node.module or "")
            return
        child_guarded = guarded or _is_type_checking_guard(node)
        for child in ast.iter_child_nodes(node):
            visit(child, child_guarded)

    visit(tree, False)
    return modules


def _is_type_checking_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


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


def runner_exports(exports: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        name
        for name in exports
        if name == "run_strategy_loop" or name == "RunLoopSummary"
    )


def public_export_fragment_matches(name: str) -> bool:
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_runner_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_runner_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    runtime_imports = imported_modules(tree)
    for module_name in runtime_imports:
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name
    # The live-layer headline: this module MUST NOT import api (Protocol-only).
    assert not any(
        module_matches_prefix(name, "polymarket_alpha_lab.api")
        for name in runtime_imports
    ), runtime_imports


def test_runner_public_exports_exactly_loop_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_runner_does_not_define_forbidden_live_or_advice_surface_names():
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

    lowered = {
        normalize_identifier(name)
        for name in names
        if name not in ALLOWED_REQUIRED_DOMAIN_NAMES
    }
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(normalize_identifier(fragment) in name for name in lowered), (
            fragment,
            lowered,
        )


def test_package_root_exports_runner_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert runner_exports(package_exports) == EXPECTED_EXPORTS
    for name in runner_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.runner"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_runner_sections_keep_paper_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    status_start = readme.index("## Continuous Run v0 Status")
    api_start = readme.index("## Continuous Run v0 Python API", status_start)
    next_section = readme.find("\n## ", api_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[status_start:next_section])

    required_fragments = (
        "continuousrunv0status",
        "continuousrunv0pythonapi",
        "paperonly",
        "reportonly",
        "noauth",
        "nowallet",
        "noorder",
        "norank",
        "norecommend",
        "nofinancialadvice",
    )
    for fragment in required_fragments:
        assert fragment in normalized, fragment
