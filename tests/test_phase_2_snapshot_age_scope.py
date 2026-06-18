import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "phase_2_snapshot_age.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"
EXPECTED_EXPORTS = (
    "PaperPhase2SnapshotAgeConfig",
    "PaperPhase2SnapshotAgeReport",
    "build_paper_phase_2_snapshot_age_report",
)
EXPECTED_FIRST_PARTY_IMPORTS = {
    "polymarket_alpha_lab.phase_2_evidence_snapshot": {
        "PaperPhase2EvidenceSnapshotReport",
    },
}
ALLOWED_IMPORT_PREFIXES = {
    "__future__",
    "dataclasses",
    "datetime",
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
    "polymarket_alpha_lab.__init__",
    "csv",
    "decimal",
    "duckdb",
    "http",
    "httpx",
    "io",
    "json",
    "os",
    "pandas",
    "pathlib",
    "polars",
    "py_clob_client",
    "requests",
    "socket",
    "sqlite3",
    "ssl",
    "subprocess",
    "sys",
    "urllib",
    "web3",
    "websocket",
    "websockets",
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
    "financialadvice",
    "http",
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
FORBIDDEN_CALL_NAMES = {
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
    "rank",
    "recommend",
    "setattr",
}
FORBIDDEN_ATTR_NAMES = {
    "auth",
    "client",
    "connect",
    "delete",
    "fetch",
    "get",
    "list_markets",
    "open",
    "order",
    "post",
    "rank",
    "recommend",
    "request",
    "send",
    "sign",
    "submit",
    "wallet",
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


def parse_age_module():
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


def assert_no_forbidden_source_strings(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        normalized = normalize_identifier(node.value)
        for token in BANNED_SOURCE_STRING_TOKENS:
            assert token not in normalized, (node.value, token)


def test_phase_2_snapshot_age_module_imports_only_allowed_dependencies():
    tree = parse_age_module()
    for module_name in imported_modules(tree):
        assert any(
            module_matches_prefix(module_name, allowed)
            for allowed in ALLOWED_IMPORT_PREFIXES
        ), module_name


def test_phase_2_snapshot_age_module_does_not_import_forbidden_surfaces():
    tree = parse_age_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_phase_2_snapshot_age_uses_only_allowed_first_party_symbols():
    tree = parse_age_module()
    assert imported_first_party_symbols(tree) == EXPECTED_FIRST_PARTY_IMPORTS


def test_phase_2_snapshot_age_does_not_import_first_party_modules_wholesale():
    tree = parse_age_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            assert alias.name not in EXPECTED_FIRST_PARTY_IMPORTS, alias.name


def test_phase_2_snapshot_age_does_not_define_forbidden_names():
    tree = parse_age_module()
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

    for name in names:
        normalized = normalize_identifier(name)
        for forbidden in FORBIDDEN_NAME_FRAGMENTS:
            assert normalize_identifier(forbidden) not in normalized, (name, forbidden)


def test_phase_2_snapshot_age_does_not_call_forbidden_runtime_surfaces():
    tree = parse_age_module()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        else:
            callee_name = None
        assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name


def test_phase_2_snapshot_age_does_not_reference_forbidden_attributes():
    tree = parse_age_module()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr


def test_phase_2_snapshot_age_source_strings_do_not_cross_phase_boundaries():
    assert_no_forbidden_source_strings(parse_age_module())


def test_phase_2_snapshot_age_exports_only_local_report_api():
    assert module_exports(parse_age_module()) == EXPECTED_EXPORTS


def test_phase_2_snapshot_age_is_not_exported_from_package_root():
    package_root = PACKAGE_ROOT_PATH.read_text(encoding="utf-8")
    assert "phase_2_snapshot_age" not in package_root
    for export_name in EXPECTED_EXPORTS:
        assert export_name not in package_root
