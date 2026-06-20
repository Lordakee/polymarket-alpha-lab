import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "edge_cost_summary.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

EXPECTED_EXPORTS = (
    "PaperEdgeCostSummaryConfig",
    "PaperEdgeCostSummaryReport",
    "build_paper_edge_cost_summary_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.forecast_evidence",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "api",
    "auth",
    "wallet",
    "account",
    "client",
    "network",
    "request",
    "http",
    "urllib",
    "pathlib",
    "sqlite3",
}

FORBIDDEN_SURFACE_FRAGMENTS = {
    "account",
    "advice",
    "api",
    "auth",
    "client",
    "command",
    "database",
    "fromfile",
    "http",
    "instruction",
    "live",
    "network",
    "order",
    "protocol",
    "rank",
    "recommend",
    "replay",
    "request",
    "selection",
    "sqlite",
    "trade",
    "urllib",
    "wallet",
}

ALLOWED_SURFACE_MATCHES = {
    "paperforecastevidenceobservation",
    "observations",
    "observation",
    "normalizeobservations",
    "edgeobservationcount",
    "readonly",
}

FORBIDDEN_CALL_NAMES = {
    "open",
    "read",
    "write",
}

FORBIDDEN_ATTR_NAMES = {
    "auth",
    "client",
    "delete",
    "fetch",
    "get",
    "list_markets",
    "open",
    "rank",
    "read",
    "recommend",
    "request",
    "sign",
    "submit",
    "write",
}


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


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


def module_surface_tokens(tree):
    tokens = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            tokens.add(node.name)
        elif isinstance(node, ast.Name):
            tokens.add(node.id)
        elif isinstance(node, ast.Attribute):
            tokens.add(node.attr)
        elif isinstance(node, ast.arg):
            tokens.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg is not None:
            tokens.add(node.arg)
        elif isinstance(node, ast.alias):
            tokens.add(node.name)
            if node.asname is not None:
                tokens.add(node.asname)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            tokens.add(node.value)
    return tokens


def test_edge_cost_summary_imports_only_stdlib_and_forecast_evidence():
    tree = parse_module()

    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_edge_cost_summary_public_exports_are_exactly_module_local_api():
    tree = parse_module()

    assert module_exports(tree) == EXPECTED_EXPORTS


def test_package_root_does_not_export_edge_cost_summary_api():
    tree = parse_module(PACKAGE_ROOT_PATH)
    package_exports = module_exports(tree)

    for name in EXPECTED_EXPORTS:
        assert name not in package_exports

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "polymarket_alpha_lab.edge_cost_summary"
        ):
            raise AssertionError("edge_cost_summary must remain module-local")


def test_edge_cost_summary_has_no_live_cli_or_advice_surfaces():
    tree = parse_module()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            if callee_name in FORBIDDEN_CALL_NAMES:
                raise AssertionError(callee_name)
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr

    lowered = {normalize_identifier(token) for token in module_surface_tokens(tree)}
    for fragment in FORBIDDEN_SURFACE_FRAGMENTS:
        normalized_fragment = normalize_identifier(fragment)
        assert not any(
            normalized_fragment in token
            for token in lowered
            if token not in ALLOWED_SURFACE_MATCHES
        ), fragment

    source_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    assert "from_file" not in source_text
    assert "cli" not in source_text
