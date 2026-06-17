import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_trade_cost_audit.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs"
    / "superpowers"
    / "specs"
    / "2026-06-17-paper-trade-cost-audit-v0.md"
)

EXPECTED_EXPORTS = (
    "PaperTradeCostAuditConfig",
    "PaperTradeCostAuditReport",
    "build_paper_trade_cost_audit_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.journal",
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
    "polymarket_alpha_lab.outcome_tracker",
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

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    # Local journal field on PaperTradeRecord, not an order-request surface.
    "orderrequestedsize",
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


def cost_audit_exports(exports):
    return tuple(
        name
        for name in exports
        if name.startswith("PaperTradeCostAudit")
        or name == "build_paper_trade_cost_audit_report"
    )


def public_export_fragment_matches(name):
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_paper_trade_cost_audit_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_paper_trade_cost_audit_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_paper_trade_cost_audit_public_exports_exactly_paper_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_paper_trade_cost_audit_does_not_define_forbidden_live_or_advice_names():
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


def test_package_root_exports_paper_trade_cost_audit_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert cost_audit_exports(package_exports) == EXPECTED_EXPORTS
    for name in cost_audit_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.paper_trade_cost_audit"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_paper_trade_cost_audit_section_keeps_phase_1_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    section_start = readme.index("## Paper Trade Cost Audit v0")
    next_section = readme.find("\n## ", section_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[section_start:next_section])

    required_fragments = (
        "papertradecostauditv0",
        "paperonly",
        "reportonly",
        "readonly",
        "localpapertradejournal",
        "costdrag",
        "slippage",
        "nofetch",
        "noauth",
        "nowallet",
        "noorder",
        "norank",
        "norecommend",
        "notradeinstruction",
        "nofinancialadvice",
    )
    for fragment in required_fragments:
        assert fragment in normalized, fragment


def test_paper_trade_cost_audit_spec_keeps_local_paper_journal_only_scope():
    normalized = normalize_identifier(SPEC_PATH.read_text(encoding="utf-8"))

    required_fragments = (
        "papertradecostauditv0spec",
        "paperonly",
        "reportonly",
        "papertraderecord",
        "papertradejournalread",
        "localpapertradejsonl",
        "mustnotfetchmarkets",
        "mustnotconstructapiclients",
        "mustnotauthenticate",
        "mustnotreadwallets",
        "mustnotreadprivatekeys",
        "mustnotplacesignsubmitcancelorders",
        "mustnotrankinvestments",
        "mustnotrecommendtrades",
        "mustnotprovidetradeinstructions",
        "mustnotprovidefinancialadvice",
    )
    for fragment in required_fragments:
        assert fragment in normalized, fragment
