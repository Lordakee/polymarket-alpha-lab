import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "phase_2_status_matrix.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
EXPECTED_EXPORTS = (
    "PaperPhase2StatusMatrixConfig",
    "PaperPhase2StatusMatrixReport",
    "PaperPhase2StatusMatrixRow",
    "build_paper_phase_2_status_matrix_report",
)
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.phase_2_evidence_snapshot": {
        "SNAPSHOT_STATUSES",
        "PaperPhase2EvidenceSnapshotReport",
    },
}
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.phase_2_evidence_snapshot",
}
FORBIDDEN_IMPORT_PREFIXES = {
    "polymarket_alpha_lab.analytics",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.normalize",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.risk",
    "urllib",
    "urllib3",
    "http",
    "socket",
    "ssl",
    "websocket",
    "websockets",
    "requests",
    "httpx",
    "aiohttp",
    "importlib",
    "runpy",
    "subprocess",
    "py_clob_client",
    "clob_client",
    "web3",
    "eth_account",
    "eth_keys",
    "eth_utils",
    "selenium",
    "playwright",
    "bs4",
    "scrapy",
    "requests_html",
    "mechanize",
    "cloudscraper",
    "curl_cffi",
    "csv",
    "sqlite3",
    "pandas",
    "polars",
    "duckdb",
    "os",
}
FORBIDDEN_NAME_FRAGMENTS = {
    "account",
    "advice",
    "api",
    "auth",
    "broker",
    "browser",
    "client",
    "credential",
    "execution",
    "fetch",
    "file",
    "financialadvice",
    "fromlog",
    "glob",
    "heartbeat",
    "http",
    "jsonl",
    "loader",
    "marketrequest",
    "network",
    "order",
    "privatekey",
    "rank",
    "recommend",
    "request",
    "scrape",
    "session",
    "submit",
    "tradeinstruction",
    "wallet",
    "websocket",
}
BANNED_SOURCE_STRING_TOKENS = {
    "advice",
    "approved",
    "eligible",
    "live",
    "promotion",
    "promoted",
    "rank",
    "recommend",
    "validated",
}
FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "print",
    "setattr",
}


def parse_module():
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
            modules.extend(alias.asname for alias in node.names if alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.level == 0
            modules.append(node.module)
            modules.extend(alias.asname for alias in node.names if alias.asname)
    return modules


def imported_first_party_symbols(tree):
    symbols = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in EXPECTED_FIRST_PARTY_IMPORTS:
            symbols.setdefault(node.module, set()).update(alias.name for alias in node.names)
    return symbols


def module_exports(tree):
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def assert_no_forbidden_names_or_calls(tree):
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
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALLS, node.func.id
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALLS, node.func.attr
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            normalized = normalize_identifier(node.value)
            for token in BANNED_SOURCE_STRING_TOKENS:
                assert token not in normalized, (node.value, token)

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(normalize_identifier(fragment) in name for name in lowered), (
            fragment,
            lowered,
        )


def test_phase_2_status_matrix_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_phase_2_status_matrix_does_not_import_forbidden_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_phase_2_status_matrix_uses_only_allowed_first_party_symbols():
    assert imported_first_party_symbols(parse_module()) == EXPECTED_FIRST_PARTY_IMPORTS


def test_phase_2_status_matrix_does_not_import_first_party_modules_wholesale():
    tree = parse_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert alias.name not in EXPECTED_FIRST_PARTY_IMPORTS, alias.name


def test_phase_2_status_matrix_does_not_define_forbidden_names_or_calls():
    assert_no_forbidden_names_or_calls(parse_module())


def test_phase_2_status_matrix_scope_guard_catches_escape_hatches():
    tree = ast.parse(
        """
from polymarket_alpha_lab.paper import PaperOrder

def bad(value):
    print(value)
    open('/tmp/phase-2-status-matrix', 'w')
    __import__('os')
""",
    )
    try:
        assert_no_forbidden_names_or_calls(tree)
    except AssertionError:
        return
    raise AssertionError("forbidden operation guard accepted escape hatches")


def test_phase_2_status_matrix_public_exports_are_exact():
    assert module_exports(parse_module()) == EXPECTED_EXPORTS


def test_package_root_does_not_export_phase_2_status_matrix_names():
    exports = module_exports(ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8")))
    for name in EXPECTED_EXPORTS:
        assert name not in exports
