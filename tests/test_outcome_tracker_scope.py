"""Scope contract for ``polymarket_alpha_lab.outcome_tracker``.

Stage 9 live-layer leaf: closes the self-judge verification loop. Reads paper
trades from the journal, re-fetches closed markets via a Protocol-only client,
reads ``outcomePrices`` from the RAW Gamma payload (never ``resolutionStatus``),
maps outcome labels through YES_NAMES/NO_NAMES alias sets (never string
equality), and builds one ``PaperForecastEvidenceObservation`` per resolved
trade LEG (never deduplicated by ``condition_id``). Pure computation on top of
a read-only Gamma re-fetch; no live/auth/wallet/order surfaces.

Six canonical scope tests plus the package-root export check and the README
section boundary check (both wired by Stage 9 Tasks 4-5).
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "outcome_tracker.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"

EXPECTED_EXPORTS = (
    "OutcomeTrackingConfig",
    "OutcomeTrackingReport",
    "check_outcomes",
)

# ALLOWED = stdlib + {domain, normalize, journal, forecast_evidence}. The leaf
# deliberately imports ONLY ``forecast_evidence`` + ``journal`` from the package
# (it reads outcomePrices from the raw payload directly, so it does NOT need
# ``normalize`` or ``domain``), but the ceiling permits the full Stage 9 set so
# a future additive field can reuse normalize/domain without re-scoping.
ALLOWED_IMPORT_MODULES = {
    "__future__",
    "json",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.forecast_evidence",
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
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.book_imbalance_forecast",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.cost_aware_event_strategy",
    "polymarket_alpha_lab.cost_aware_snapshot_builder",
    "polymarket_alpha_lab.forecast_provider",
    "polymarket_alpha_lab.json_recovery",
    "polymarket_alpha_lab.llm_forecast",
    "polymarket_alpha_lab.llm_research_transport",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_portfolio_nav",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
    "polymarket_alpha_lab.proposal_review_coverage",
    "polymarket_alpha_lab.proposal_review_diagnostics",
    "polymarket_alpha_lab.proposal_review_dossier",
    "polymarket_alpha_lab.proposal_review_dossier_batch",
    "polymarket_alpha_lab.proposal_review_quality",
    "polymarket_alpha_lab.proposal_review_summary",
    "polymarket_alpha_lab.proposal_evidence_comparison",
    "polymarket_alpha_lab.proposal_evidence_comparison_artifact_registry",
    "polymarket_alpha_lab.proposal_evidence_comparison_history",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health",
    "polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend",
    "polymarket_alpha_lab.project_screening",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.scoring",
    "polymarket_alpha_lab.strategy_cycle",
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
# public API is check_outcomes(*, client: OutcomeTrackerClient, ...) and the
# local Protocol is named OutcomeTrackerClient (Q5, mirroring strategy_cycle's
# MarketDataClient). Only the dangerous COMPOSED client surfaces
# (liveclient, executionclient, transportclient, orderclient) remain forbidden
# so no real execution/broker/credential/transport client can slip in. Bare
# "outcome" is also intentionally NOT forbidden -- the module's whole job is
# outcome tracking, so forbidding it would make the leaf unnameable.
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

# Names this leaf is permitted to reference even though they overlap with
# otherwise-forbidden vocabulary. ``OutcomeTrackerClient`` carries the
# "client" fragment; the public Protocol surface is the leaf's mandated
# MarketData client contract (Q5), and it is NOT exported in __all__ (kept
# private to the module). ``list_markets`` is the Protocol's only method and
# reuses the SAME verb as strategy_cycle.MarketDataClient / api.PolymarketPublicClient.
ALLOWED_REQUIRED_DOMAIN_NAMES = {
    "OutcomeTrackerClient",
    "list_markets",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path: Path = MODULE_PATH) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(tree: ast.AST) -> list[str]:
    """Return runtime-imported module names (TYPE_CHECKING-guarded imports
    would be skipped the same way as in test_paper_execution_scope, but this
    leaf has no TYPE_CHECKING block, so a plain walk suffices)."""
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


def outcome_tracker_exports(exports: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        name
        for name in exports
        if name.startswith("OutcomeTracking") or name == "check_outcomes"
    )


def public_export_fragment_matches(name: str) -> bool:
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_outcome_tracker_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_outcome_tracker_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_outcome_tracker_public_exports_exactly_paper_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_outcome_tracker_does_not_define_forbidden_live_or_advice_surface_names():
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


def test_package_root_exports_outcome_tracker_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert outcome_tracker_exports(package_exports) == EXPECTED_EXPORTS
    for name in outcome_tracker_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.outcome_tracker"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_outcome_tracker_sections_keep_paper_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    status_start = readme.index("## Outcome Tracker v0 Status")
    api_start = readme.index("## Outcome Tracker v0 Python API", status_start)
    next_section = readme.find("\n## ", api_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[status_start:next_section])

    required_fragments = (
        "outcometrackerv0status",
        "outcometrackerv0pythonapi",
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
