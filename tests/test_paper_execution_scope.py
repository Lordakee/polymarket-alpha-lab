"""Scope contract for ``polymarket_alpha_lab.paper_execution``.

Stage 4 Task 1 leaf: paper-only in-memory execution. Pure function turning a
screening-ready candidate + in-cycle context into a ``PaperTradeRecord`` via
``simulate_order_book_fill``. No live/auth/wallet/order-placement surfaces.

Six canonical scope tests plus the package-root export check and the README
section boundary check (both wired by Stage 4 Task 2-4).
"""

import ast
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "paper_execution.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
README_PATH = REPO_ROOT / "README.md"

EXPECTED_EXPORTS = (
    "PaperExecutionConfig",
    "PaperExecutionResult",
    "PaperExecutionLog",
    "execute_paper_trade_from_screening",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "hashlib",
    "json",
    "pathlib",
    "typing",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.cost_aware_event_strategy",
    "polymarket_alpha_lab.project_screening",
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
    "polymarket_alpha_lab.forecast_evidence",
    "polymarket_alpha_lab.manual_review_queue",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal_packet",
    "polymarket_alpha_lab.proposal_review",
    "polymarket_alpha_lab.rejections",
    "polymarket_alpha_lab.risk",
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

# NOTE: bare "execution" is intentionally NOT forbidden here -- the module is
# named ``paper_execution`` and its mandated public API is
# ``execute_paper_trade_from_screening`` plus the ``PaperExecution*`` types.
# Bare "order" is also NOT forbidden -- the leaf legitimately handles paper
# orders via ``PaperOrder`` / ``PaperFill`` / ``simulate_order_book_fill``
# (the pure paper simulate surface). Only the concrete LIVE surfaces are
# forbidden so no real execution/broker/credential client can slip in.
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
    "credential",
    "credentialloader",
    "credentialmanager",
    "credentials",
    "dataloader",
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
    "orderplacement",
    "placeorder",
    "privatekey",
    "rank",
    "rankinvestment",
    "ranking",
    "recommend",
    "recommendation",
    "sdk",
    "signorder",
    "sign",
    "submitorder",
    "tradeinstruction",
    "transport",
    "transportclient",
    "wallet",
    "websocket",
}

FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS = {
    "advice",
    "advisor",
    "auth",
    "broker",
    "browser",
    "client",
    "credential",
    "financialadvice",
    "investment",
    "killswitch",
    "live",
    "liveexecution",
    "orderplacement",
    "placeorder",
    "privatekey",
    "rank",
    "ranking",
    "recommend",
    "recommendation",
    "submitorder",
    "transport",
    "wallet",
    "websocket",
}

# Names this leaf is permitted to reference even though they overlap with
# paper-domain vocabulary (PaperOrder/PaperFill/simulate_order_book_fill are
# the pure paper simulate surface imported from ``polymarket_alpha_lab.paper``).
ALLOWED_REQUIRED_DOMAIN_NAMES = {
    "OrderBookSnapshot",
    "OrderBookLevel",
    "NormalizedMarket",
    "PaperOrder",
    "PaperFill",
    "PaperTradeRecord",
    "ResearchPacket",
    "PaperCostAwareEventStrategyReport",
    "PaperCostAwareEventSideResult",
    "PaperProjectScreeningCandidate",
    "simulate_order_book_fill",
    "RawArchiveEntry",
    "TYPE_CHECKING",
}


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name: str, prefix: str) -> bool:
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module(path: Path = MODULE_PATH) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"))


def _is_type_checking_guard(node: ast.AST) -> bool:
    # Matches `if TYPE_CHECKING:` (the canonical runtime-false guard).
    if not isinstance(node, ast.If):
        return False
    test = node.test
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def imported_modules(tree: ast.AST) -> list[str]:
    """Return runtime-imported module names.

    Imports guarded by ``if TYPE_CHECKING:`` are SKIPPED -- they never execute
    at runtime, so they are invisible to the runtime dependency boundary. This
    mirrors how the leaf legitimately references ``RawArchiveEntry`` for the
    ``raw_book_archive_entry`` / ``raw_market_archive_entry`` annotations
    (duck-typed at runtime) without importing ``archive`` at runtime.
    """
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


def paper_execution_exports(exports: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        name
        for name in exports
        if name.startswith("PaperExecution") or name == "execute_paper_trade_from_screening"
    )


def public_export_fragment_matches(name: str) -> bool:
    normalized = normalize_identifier(name)
    return any(
        normalize_identifier(fragment) in normalized
        for fragment in FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS
    )


def test_paper_execution_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_paper_execution_does_not_import_live_or_loader_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_paper_execution_public_exports_exactly_paper_report_api():
    tree = parse_module()
    assigned_exports = module_exports(tree)

    assert assigned_exports == EXPECTED_EXPORTS
    for name in assigned_exports:
        assert not public_export_fragment_matches(name), name


def test_paper_execution_does_not_define_forbidden_live_or_advice_surface_names():
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


def test_paper_execution_archive_reference_is_type_checking_only():
    # MINOR (a): archive import MUST live under `if TYPE_CHECKING:` only so it
    # never executes at runtime (duck-typed payload_path/payload_sha256).
    tree = parse_module()
    runtime_imports = imported_modules(tree)
    assert not any(
        module_matches_prefix(name, "polymarket_alpha_lab.archive")
        for name in runtime_imports
    ), runtime_imports
    # And TYPE_CHECKING must be imported (used for the guard).
    assert "typing" in runtime_imports


def test_package_root_exports_paper_execution_api_only():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    assert paper_execution_exports(package_exports) == EXPECTED_EXPORTS
    for name in paper_execution_exports(package_exports):
        assert not public_export_fragment_matches(name), name

    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.paper_execution"
        ):
            imported_names.update(alias.name for alias in node.names)
    assert imported_names == set(EXPECTED_EXPORTS)


def test_readme_paper_execution_sections_keep_paper_boundaries():
    readme = README_PATH.read_text(encoding="utf-8")
    status_start = readme.index("## Paper Execution v0 Status")
    api_start = readme.index("## Paper Execution v0 Python API", status_start)
    next_section = readme.find("\n## ", api_start + 1)
    if next_section == -1:
        next_section = len(readme)
    normalized = normalize_identifier(readme[status_start:next_section])

    required_fragments = (
        "paperexecutionv0status",
        "paperexecutionv0pythonapi",
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
