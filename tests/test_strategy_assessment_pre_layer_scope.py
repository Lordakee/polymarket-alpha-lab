import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

MODULE_SPECS = (
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "candidate_assessment.py",
        (
            "PaperCandidateAssessmentConfig",
            "PaperCandidateAssessmentReport",
            "PaperCandidateAssessmentRow",
            "build_paper_candidate_assessment_report",
        ),
        {
            "__future__",
            "collections.abc",
            "dataclasses",
            "datetime",
            "decimal",
            "polymarket_alpha_lab.cost_aware_event_strategy",
            "polymarket_alpha_lab.project_screening",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "calibration_gate.py",
        (
            "PaperCalibrationGateConfig",
            "PaperCalibrationGateRow",
            "PaperCalibrationGateReport",
            "build_paper_calibration_gate_report",
        ),
        {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
            "polymarket_alpha_lab.forecast_calibration",
            "polymarket_alpha_lab.forecast_calibration_trend",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "cost_health_gate.py",
        (
            "PaperCostHealthGateConfig",
            "PaperCostHealthSummaryRow",
            "PaperCostHealthGateRow",
            "PaperCostHealthGateReport",
            "build_paper_cost_health_gate_report",
        ),
        {
            "__future__",
            "collections.abc",
            "dataclasses",
            "datetime",
            "decimal",
            "polymarket_alpha_lab.edge_cost_summary_trend",
            "polymarket_alpha_lab.paper_trade_cost_trend",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "cost_sensitivity.py",
        (
            "PaperCostSensitivityConfig",
            "PaperCostSensitivityReport",
            "PaperCostSensitivityRow",
            "build_paper_cost_sensitivity_report",
        ),
        {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "polymarket_alpha_lab.cost_aware_event_strategy",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "exposure_gate.py",
        (
            "PaperExposureGateConfig",
            "PaperExposureGateRow",
            "PaperExposureGateReport",
            "build_paper_exposure_gate_report",
        ),
        {
            "__future__",
            "collections.abc",
            "dataclasses",
            "datetime",
            "decimal",
            "polymarket_alpha_lab.positions",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "liquidity_gate.py",
        (
            "PaperLiquidityGateConfig",
            "PaperLiquidityGateReport",
            "PaperLiquidityGateRow",
            "build_paper_liquidity_gate_report",
        ),
        {
            "__future__",
            "collections.abc",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
            "polymarket_alpha_lab.cost_aware_event_strategy",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "market_context_freshness.py",
        (
            "PaperMarketContextFreshnessConfig",
            "PaperMarketContextFreshnessReport",
            "PaperMarketContextFreshnessRow",
            "build_paper_market_context_freshness_report",
        ),
        {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
            "polymarket_alpha_lab.cost_aware_event_strategy",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_attribution.py",
        (
            "PaperTradeAttributionConfig",
            "PaperTradeAttributionReport",
            "PaperTradeAttributionRow",
            "build_paper_trade_attribution_report",
        ),
        {
            "__future__",
            "collections.abc",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
            "polymarket_alpha_lab.forecast_evidence",
            "polymarket_alpha_lab.journal",
            "polymarket_alpha_lab.outcome_tracker",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "settlement_freshness_gate.py",
        (
            "PaperSettlementFreshnessGateConfig",
            "PaperSettlementFreshnessGateRow",
            "PaperSettlementFreshnessGateReport",
            "build_paper_settlement_freshness_gate_report",
        ),
        {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
            "polymarket_alpha_lab.outcome_freshness",
            "polymarket_alpha_lab.outcome_tracker",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_readiness_state.py",
        (
            "PaperStrategyReadinessSignal",
            "PaperStrategyReadinessStateReport",
            "build_paper_strategy_readiness_state_report",
        ),
        {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "typing",
        },
    ),
    (
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_signal_adapter.py",
        (
            "build_paper_strategy_readiness_signals",
            "signals_from_calibration_gate_report",
            "signals_from_cost_health_gate_report",
            "signals_from_exposure_gate_report",
            "signals_from_liquidity_gate_report",
            "signals_from_market_context_freshness_report",
            "signals_from_settlement_freshness_gate_report",
        ),
        {
            "__future__",
            "decimal",
            "polymarket_alpha_lab.calibration_gate",
            "polymarket_alpha_lab.cost_health_gate",
            "polymarket_alpha_lab.exposure_gate",
            "polymarket_alpha_lab.liquidity_gate",
            "polymarket_alpha_lab.market_context_freshness",
            "polymarket_alpha_lab.settlement_freshness_gate",
            "polymarket_alpha_lab.strategy_readiness_state",
        },
    ),
)

FORBIDDEN_IMPORT_PREFIXES = (
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
)

FORBIDDEN_NAME_FRAGMENTS = (
    "advice",
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "browser",
    "client",
    "credential",
    "fetch",
    "golive",
    "live",
    "loader",
    "placeorder",
    "privatekey",
    "rank",
    "recommend",
    "sdk",
    "signorder",
    "submitorder",
    "transport",
    "wallet",
    "websocket",
)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


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


def assert_module_scope(
    path: Path,
    *,
    expected_exports: tuple[str, ...],
    allowed_import_modules: set[str],
) -> None:
    tree = parse_module(path)
    exported_names = module_exports(tree)

    assert exported_names == expected_exports
    for module_name in imported_modules(tree):
        assert module_name in allowed_import_modules, (path.name, module_name)
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), (path.name, module_name)

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
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            names.add(node.value)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(normalize_identifier(fragment) in name for name in lowered), (
            path.name,
            fragment,
            lowered,
        )


def test_strategy_assessment_pre_layer_modules_keep_module_level_api_boundaries():
    for path, expected_exports, allowed_import_modules in MODULE_SPECS:
        assert_module_scope(
            path,
            expected_exports=expected_exports,
            allowed_import_modules=allowed_import_modules,
        )


def test_strategy_assessment_pre_layer_public_api_is_not_exported_from_package_root():
    package_root_exports = set(module_exports(parse_module(PACKAGE_ROOT_PATH)))

    for _path, expected_exports, _allowed_import_modules in MODULE_SPECS:
        for export_name in expected_exports:
            assert export_name not in package_root_exports, export_name
