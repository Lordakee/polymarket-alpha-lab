import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_risk_audit.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-06-16-strategy-risk-audit-v0.md"
)
COST_GATE_SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-06-17-strategy-risk-audit-cost-gate-v0.md"
)

EXPECTED_EXPORTS = (
    "PaperStrategyRiskAuditConfig",
    "PaperStrategyRiskAuditGateResult",
    "PaperStrategyRiskAuditReport",
    "build_paper_strategy_risk_audit_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.nav_risk_metrics",
    "polymarket_alpha_lab.outcome_tracker",
    "polymarket_alpha_lab.paper_nav_settlement_risk_overlay",
    "polymarket_alpha_lab.paper_trade_cost_audit",
    "polymarket_alpha_lab.performance_summary",
}

EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.nav_risk_metrics": {"PaperNavRiskMetricsReport"},
    "polymarket_alpha_lab.outcome_tracker": {"OutcomeTrackingReport"},
    "polymarket_alpha_lab.paper_nav_settlement_risk_overlay": {
        "PaperNavSettlementRiskOverlayReport",
    },
    "polymarket_alpha_lab.paper_trade_cost_audit": {"PaperTradeCostAuditReport"},
    "polymarket_alpha_lab.performance_summary": {"PerformanceSummary"},
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
    "pathlib",
    "playwright",
    "polymarket",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.paper_portfolio_nav",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_cycle",
    "py_clob_client",
    "requests",
    "selenium",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
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
    "rank",
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
    "order",
    "rank",
    "recommend",
    "transport",
    "wallet",
    "websocket",
}

FORBIDDEN_CALL_NAMES = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "open",
}

FORBIDDEN_ATTRIBUTE_CALLS = {
    "read",
    "read_bytes",
    "read_text",
    "write",
    "write_bytes",
    "write_text",
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


def first_party_imports(tree):
    imports = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module not in EXPECTED_FIRST_PARTY_IMPORTS:
            continue
        imports.setdefault(node.module, set()).update(alias.name for alias in node.names)
    return imports


def module_exports(tree):
    assigned_exports = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def strategy_risk_exports(exports):
    return tuple(
        name
        for name in exports
        if name.startswith("PaperStrategyRiskAudit")
        or name == "build_paper_strategy_risk_audit_report"
    )


def public_export_fragment_matches(name):
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_strategy_risk_audit_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_strategy_risk_audit_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_strategy_risk_audit_uses_only_allowed_first_party_symbols():
    tree = parse_module()

    assert first_party_imports(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_strategy_risk_audit_does_not_import_first_party_modules_wholesale():
    tree = parse_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert not alias.name.startswith("polymarket_alpha_lab"), alias.name


def test_strategy_risk_audit_public_exports_exactly_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_strategy_risk_audit_does_not_define_forbidden_surfaces():
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


def test_strategy_risk_audit_does_not_call_dynamic_or_file_surfaces():
    tree = parse_module()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALL_NAMES, node.func.id
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_ATTRIBUTE_CALLS, node.func.attr


def test_package_root_exports_strategy_risk_audit_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert strategy_risk_exports(package_exports) == EXPECTED_EXPORTS
    for name in strategy_risk_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.strategy_risk_audit"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_strategy_risk_audit_spec_documents_report_only_boundary():
    normalized = normalize_identifier(SPEC_PATH.read_text(encoding="utf-8"))

    required_fragments = (
        "strategyriskauditv0",
        "paperonly",
        "reportonly",
        "performancesummary",
        "papernavriskmetricsreport",
        "outcometrackingreport",
        "papertradecostauditreport",
        "forecastevidencereport",
        "forecastquality",
        "costdiscipline",
        "sixgates",
        "doesnotreadfiles",
        "nofilereaders",
        "nofetch",
        "noauth",
        "nowallets",
        "noorders",
        "nodirectimportofpolymarketalphalabforecastevidence",
        "norecommendation",
        "noranking",
        "nofinancialadvice",
    )
    for fragment in required_fragments:
        assert fragment in normalized, fragment


def test_strategy_risk_audit_cost_gate_spec_documents_report_only_boundary():
    normalized = normalize_identifier(COST_GATE_SPEC_PATH.read_text(encoding="utf-8"))

    required_fragments = (
        "strategyriskauditcostgatev0",
        "paperonly",
        "reportonly",
        "costdiscipline",
        "papertradecostauditreport",
        "mincostaudittradecount",
        "maxmeanedgecostdrag",
        "maxnegativecostadjustededgecount",
        "purereportmath",
        "mustnotimportpapertradejournal",
        "mustnotconstructapolymarketclient",
        "nofile",
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
