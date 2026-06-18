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
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.forecast_evidence",
}

FORBIDDEN_IMPORT_PREFIXES = {
    "api",
    "auth",
    "wallet",
    "private_key",
    "client",
    "network",
    "request",
    "http",
    "urllib",
    "journal",
    "log",
    "pathlib",
}

FORBIDDEN_NAME_FRAGMENTS = {
    "api",
    "auth",
    "wallet",
    "privatekey",
    "client",
    "network",
    "request",
    "http",
    "urllib",
    "journal",
    "log",
    "order",
    "trade",
    "position",
    "rank",
    "recommend",
    "instruction",
    "advice",
    "eligible",
    "approved",
    "actionable",
    "validated",
    "ready",
    "live",
}

ALLOWED_FORBIDDEN_NAME_MATCHES = {
    "paperforecastevidenceobservation",
    "observations",
    "observation",
    "edgeobservationcount",
    "minedgeobservationcount",
    "edgestatus",
    "status",
    "statuses",
    "readonly",
}

FORBIDDEN_CALL_NAMES = {
    "open",
    "read",
    "write",
    "rank",
    "recommend",
    "instruction",
    "advice",
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


def test_edge_cost_summary_imports_only_allowed_dependencies():
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


def test_edge_cost_summary_does_not_define_forbidden_surfaces_or_operations():
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

    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(
            normalize_identifier(fragment) in name
            for name in lowered
            if name not in ALLOWED_FORBIDDEN_NAME_MATCHES
        ), fragment
