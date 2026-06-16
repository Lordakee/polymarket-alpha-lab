import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cost_aware_event_strategy.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"

EXPECTED_EXPORTS = (
    "PaperCostAwareEventCostAssumptions",
    "PaperCostAwareEventMarketSnapshot",
    "PaperCostAwareEventSideResult",
    "PaperCostAwareEventStrategyConfig",
    "PaperCostAwareEventStrategyGateResult",
    "PaperCostAwareEventStrategyLog",
    "PaperCostAwareEventStrategyReport",
    "build_paper_cost_aware_event_strategy_report",
    "polymarket_default_cost_assumptions",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "json",
    "dataclasses",
    "datetime",
    "decimal",
    "pathlib",
    "typing",
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
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal_evidence_comparison",
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
    "apikey",
    "apitoken",
    "auth",
    "authenticate",
    "broker",
    "brokerrequest",
    "browser",
    "client",
    "credential",
    "credentialloader",
    "credentialmanager",
    "credentials",
    "dataloader",
    "execution",
    "executionclient",
    "fetch",
    "golive",
    "historyloader",
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
    "ranking",
    "recommend",
    "recommendation",
    "routeorder",
    "sdk",
    "signorder",
    "submitorder",
    "transport",
    "transportclient",
    "wallet",
    "websocket",
}

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = {
    "account",
    "auth",
    "broker",
    "browser",
    "client",
    "credential",
    "execution",
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


def cost_aware_exports(exports):
    return tuple(
        name
        for name in exports
        if name.startswith("PaperCostAwareEvent")
        or name == "build_paper_cost_aware_event_strategy_report"
        or name == "polymarket_default_cost_assumptions"
    )


def public_export_fragment_matches(name):
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_cost_aware_event_strategy_imports_only_allowed_stdlib_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_cost_aware_event_strategy_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_cost_aware_event_strategy_public_exports_exactly_paper_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_cost_aware_event_strategy_does_not_define_forbidden_live_surface_names():
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


def test_package_root_exports_cost_aware_event_strategy_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert cost_aware_exports(package_exports) == EXPECTED_EXPORTS
    for name in cost_aware_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.cost_aware_event_strategy"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_cost_aware_event_strategy_sections_keep_paper_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    status_start = readme.index("## Cost-Aware Event Strategy v0 Status")
    api_start = readme.index("## Cost-Aware Event Strategy v0 Python API", status_start)
    next_section = readme.find("\n## ", api_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[status_start:next_section])

    required_fragments = (
        "costawareeventstrategyv0status",
        "costawareeventstrategyv0pythonapi",
        "paperonly",
        "reportonly",
        "callersupplied",
        "executableyesnoaskprices",
        "takerfees",
        "nonfeecosts",
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
