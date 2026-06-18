import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "strategy_segment_summary.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.forecast_evidence",
}

EXPECTED_EXPORTS = (
    "PaperStrategySegmentSummaryConfig",
    "PaperStrategySegmentRow",
    "PaperStrategySegmentSummaryReport",
    "build_paper_strategy_segment_summary_report",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "http",
    "os",
    "pathlib",
    "polymarket_alpha_lab.archive",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.clob",
    "polymarket_alpha_lab.data",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_cycle",
    "requests",
    "socket",
    "subprocess",
    "urllib",
)

FORBIDDEN_NAME_FRAGMENTS = (
    "advice",
    "apikey",
    "auth",
    "client",
    "credential",
    "execute",
    "fetch",
    "investment",
    "network",
    "order",
    "privatekey",
    "rank",
    "request",
    "secret",
    "submit",
    "trade",
    "wallet",
)

FORBIDDEN_CALL_NAMES = {
    "connect",
    "delete",
    "download",
    "fetch",
    "float",
    "get",
    "mkdir",
    "open",
    "post",
    "put",
    "read",
    "read_text",
    "rename",
    "request",
    "send",
    "submit",
    "touch",
    "unlink",
    "write",
    "write_text",
}

FORBIDDEN_ATTR_NAMES = FORBIDDEN_CALL_NAMES | {
    "client",
    "parent",
    "path",
    "sign",
}

BANNED_STATUS_LABEL_TOKENS = (
    "advice",
    "ready",
    "approved",
    "eligible",
    "rank",
    "recommend",
    "live",
    "validated",
    "actionable",
    "promotion",
    "promoted",
)


def normalize_identifier(value):
    return "".join(character for character in value.lower() if character.isalnum())


def module_matches_prefix(module_name, prefix):
    return module_name == prefix or module_name.startswith(f"{prefix}.")


def parse_module():
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def imported_modules(tree):
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative imports are not allowed"
            if node.module is not None:
                modules.append(node.module)
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


def assert_no_decimal_boundary_regressions(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float), node.value
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id != "float", node.func.id
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr != "from_float", node.func.attr


def assert_no_forbidden_status_label_advice_string_constants(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        normalized = normalize_identifier(node.value)
        for token in BANNED_STATUS_LABEL_TOKENS:
            assert token not in normalized, (node.value, token)


def assert_no_forbidden_operations(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_ATTR_NAMES, node.attr
        if not isinstance(node, ast.Call):
            continue
        callee_name = None
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        assert callee_name not in FORBIDDEN_CALL_NAMES, callee_name


def assert_scope_guard_fails(source, guard):
    try:
        guard(ast.parse(source))
    except AssertionError:
        return
    raise AssertionError("scope guard accepted forbidden source")


def test_strategy_segment_summary_scope_guard_rejects_relative_forbidden_imports():
    assert_scope_guard_fails(
        "from . import cli",
        lambda tree: set(imported_modules(tree)) <= ALLOWED_IMPORT_MODULES,
    )


def test_strategy_segment_summary_scope_guard_rejects_forbidden_operations():
    bad_sources = (
        "client.connect()",
        "response = get(url)",
        "session.post(url)",
        "path.read_text()",
        "router.submit(order)",
    )

    for source in bad_sources:
        assert_scope_guard_fails(source, assert_no_forbidden_operations)


def test_strategy_segment_summary_scope_guard_rejects_decimal_boundary_regressions():
    bad_sources = (
        "ratio = 0.1000",
        "ratio = float(Decimal('0.1000'))",
        "ratio = Decimal.from_float(external_probability)",
    )

    for source in bad_sources:
        assert_scope_guard_fails(source, assert_no_decimal_boundary_regressions)


def test_strategy_segment_summary_scope_guard_rejects_forbidden_string_constants():
    bad_sources = (
        'status = "ready_for_live_execution"',
        'label = "approved_strategy_promotion"',
        'message = "provide financial advice"',
    )

    for source in bad_sources:
        assert_scope_guard_fails(
            source,
            assert_no_forbidden_status_label_advice_string_constants,
        )


def test_strategy_segment_summary_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_strategy_segment_summary_does_not_import_forbidden_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_strategy_segment_summary_public_exports_are_exact_report_api():
    assert module_exports(parse_module()) == EXPECTED_EXPORTS


def test_strategy_segment_summary_does_not_define_forbidden_surfaces():
    tree = parse_module()
    names = set()
    assert_no_decimal_boundary_regressions(tree)
    assert_no_forbidden_operations(tree)
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


def test_strategy_segment_summary_has_no_forbidden_operations():
    tree = parse_module()

    assert_no_forbidden_operations(tree)


def test_strategy_segment_summary_does_not_define_banned_status_or_label_strings():
    tree = parse_module()

    assert_no_forbidden_status_label_advice_string_constants(tree)


def test_strategy_segment_summary_public_api_is_not_exported_from_package_root():
    package_root_tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    package_root_names = set()

    for node in ast.walk(package_root_tree):
        if isinstance(node, ast.Name):
            package_root_names.add(node.id)
        elif isinstance(node, ast.alias):
            package_root_names.add(node.name)
            if node.asname is not None:
                package_root_names.add(node.asname)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            package_root_names.add(node.value)

    for export_name in EXPECTED_EXPORTS:
        assert export_name not in package_root_names, export_name
