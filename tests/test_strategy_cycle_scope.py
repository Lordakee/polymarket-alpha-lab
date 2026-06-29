"""First live-layer scope contract for strategy_cycle.py.

First live-layer scope contract (pipeline.py has none); strategy_cycle.py is
Protocol-only (does NOT import api -- depends on a local MarketDataClient
Protocol; cli.py constructs the concrete client and injects it), setting a
tighter live-layer precedent than pipeline.py.
"""

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_cycle.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"

EXPECTED_EXPORTS = (
    "PaperStrategyCycleConfig",
    "PaperStrategyCycleReport",
    "PaperStrategyCycleLog",
    "run_strategy_cycle",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "json",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    # Q5: strategy_cycle.py is Protocol-only -- it does NOT import api. It reuses
    # pipeline.MarketScanConfig (live-layer precedent), and wires the frozen
    # Stage 1a leaves + cost-aware + screening + read-only normalize/archive/
    # scoring/domain helpers. The concrete MarketDataClient is injected by cli.py.
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.book_imbalance_forecast",
    "polymarket_alpha_lab.cost_aware_event_strategy",
    "polymarket_alpha_lab.cost_aware_snapshot_builder",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_provider",
    # Stage 4: the inline paper-execution pass journals a PaperTradeRecord per
    # screening_ready candidate. ``journal`` (PaperTradeJournal) and
    # ``paper_execution`` (PaperExecutionConfig + execute_paper_trade_from_screening)
    # are now permitted because journaling paper trades IS the cycle's new Stage
    # 4 responsibility (previously forbidden under Stage 1b read-only boundary).
    "polymarket_alpha_lab.journal",
    # Stage 6: PaperStrategyCycleLog.read reuses the shared recursive
    # json_recovery.from_jsonable helper to reconstruct the nested report tree.
    "polymarket_alpha_lab.json_recovery",
    # Stage 8: the LLM forecast provider routes each binary market through a
    # caller-supplied read-only probability-model transport (Zhipu GLM via stdlib
    # urllib, same research-fetch class as api.py) and the pure transform leaf.
    # ``llm_research_transport`` is permitted because the read-only GLM estimate
    # IS the cycle's Stage 8 job; ``llm_forecast`` is the network-free leaf.
    "polymarket_alpha_lab.llm_forecast",
    "polymarket_alpha_lab.llm_research_transport",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.project_screening",
    "polymarket_alpha_lab.scoring",
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
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.analytics_history",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.forecast_evidence",
    # NOTE: ``polymarket_alpha_lab.journal`` is intentionally NOT forbidden
    # here -- Stage 4 wires an inline paper-execution pass that journals a
    # PaperTradeRecord per screening_ready candidate via PaperTradeJournal
    # (permitted in ALLOWED_IMPORT_MODULES; was forbidden under Stage 1b).
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
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

# NOTE: bare "client" is intentionally NOT forbidden here -- the mandated
# public API is run_strategy_cycle(*, client: MarketDataClient, ...) and the
# local Protocol is named MarketDataClient (Q5). The dangerous composed client
# surfaces (liveclient, executionclient, transportclient, orderclient) remain
# forbidden so no real execution/broker client type can slip in.
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
    "execution",
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


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path=MODULE_PATH):
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            modules.append(node.module or "")
    return modules


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def strategy_cycle_exports(exports):
    return tuple(
        name
        for name in exports
        if name in EXPECTED_EXPORTS
    )


def public_export_fragment_matches(name):
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


# Names the Stage 4 inline paper-execution pass legitimately references even
# though they overlap with the otherwise-forbidden "execution" fragment. The
# leaf is ``paper_execution`` (paper-only/report-only); ``PaperExecutionConfig``
# is its frozen config and ``paper_execution_config`` is the optional cycle
# field that enables the default-off inline pass. Mirrors the
# ALLOWED_REQUIRED_DOMAIN_NAMES carve-out in test_paper_execution_scope.
ALLOWED_REQUIRED_DOMAIN_NAMES = {
    "PaperExecutionConfig",
    "paper_execution_config",
    # Stage 8: the LLM forecast provider injects a GLMChatTransport and the LLM
    # forecast config. ``llm_transport`` and ``GLMChatTransport`` carry the
    # otherwise-forbidden "transport" fragment; this carve-out authorizes them
    # because the read-only GLM estimate is the cycle's Stage 8 job (analogous
    # to how Stage 4 carved out PaperExecutionConfig / paper_execution_config).
    "GLMChatTransport",
    "llm_transport",
}


def test_strategy_cycle_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_strategy_cycle_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_strategy_cycle_public_exports_exactly_paper_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_strategy_cycle_does_not_define_forbidden_live_or_advice_surface_names():
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


def test_package_root_exports_strategy_cycle_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert strategy_cycle_exports(package_exports) == EXPECTED_EXPORTS
    for name in strategy_cycle_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.strategy_cycle"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_strategy_cycle_sections_keep_paper_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    status_start = readme.index("## Strategy Cycle v0 Status")
    api_start = readme.index("## Strategy Cycle v0 Python API", status_start)
    next_section = readme.find("\n## ", api_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[status_start:next_section])

    required_fragments = (
        "strategycyclev0status",
        "strategycyclev0pythonapi",
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
