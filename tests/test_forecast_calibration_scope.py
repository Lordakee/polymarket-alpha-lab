import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FORECAST_CALIBRATION_PATH = (
    REPO_ROOT / "src" / "polymarket_alpha_lab" / "forecast_calibration.py"
)
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

EXPECTED_FORECAST_CALIBRATION_EXPORTS = (
    "PaperForecastCalibrationBucket",
    "PaperForecastCalibrationConfig",
    "PaperForecastCalibrationReport",
    "build_paper_forecast_calibration_report",
)

ALLOWED_IMPORTS = {
    "__future__",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.forecast_evidence",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "csv",
    "http",
    "httpx",
    "json",
    "os",
    "pathlib",
    "pickle",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.proposal",
    "polymarket_alpha_lab.research",
    "py_clob_client",
    "requests",
    "socket",
    "sqlite3",
    "ssl",
    "subprocess",
    "urllib",
    "web3",
    "websocket",
)

FORBIDDEN_NAME_FRAGMENTS = (
    "advice",
    "apikey",
    "auth",
    "backfill",
    "broker",
    "cancelorder",
    "client",
    "credential",
    "download",
    "executiondecision",
    "fetch",
    "historicalloader",
    "journal",
    "liveexecution",
    "network",
    "orderrouter",
    "placeorder",
    "privatekey",
    "recommend",
    "request",
    "scrape",
    "secret",
    "session",
    "signer",
    "submitorder",
    "transport",
    "wallet",
    "websocket",
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


def parse_forecast_calibration() -> ast.AST:
    return ast.parse(FORECAST_CALIBRATION_PATH.read_text(encoding="utf-8"))


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def imported_modules(tree: ast.AST) -> tuple[str, ...]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative imports are not allowed"
            if node.module is not None:
                modules.append(node.module)
    return tuple(modules)


def module_exports(tree: ast.AST) -> tuple[str, ...]:
    assigned_exports = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    assigned_exports = ast.literal_eval(node.value)
    assert assigned_exports is not None
    return tuple(assigned_exports)


def assert_no_decimal_boundary_regressions(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float), node.value
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id != "float", node.func.id
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr != "from_float", node.func.attr


def assert_no_forbidden_status_label_advice_string_constants(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        normalized = normalize_identifier(node.value)
        for token in BANNED_STATUS_LABEL_TOKENS:
            assert token not in normalized, (node.value, token)


def assert_no_forbidden_operations(tree: ast.AST) -> None:
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


def assert_scope_guard_fails(source: str, guard) -> None:
    try:
        guard(ast.parse(source))
    except AssertionError:
        return
    raise AssertionError("scope guard accepted forbidden source")


def test_forecast_calibration_scope_guard_rejects_relative_forbidden_imports():
    assert_scope_guard_fails(
        "from . import cli",
        lambda tree: set(imported_modules(tree)) <= ALLOWED_IMPORTS,
    )


def test_forecast_calibration_scope_guard_rejects_file_operation_spelling():
    bad_sources = (
        "path.read_text()",
        "path.write_text('x')",
        "path.rename(other)",
        "path.touch()",
    )

    for source in bad_sources:
        assert_scope_guard_fails(source, assert_no_forbidden_operations)


def test_forecast_calibration_scope_guard_rejects_decimal_boundary_regressions():
    bad_sources = (
        "ratio = 0.1000",
        "ratio = float(Decimal('0.1000'))",
        "ratio = Decimal.from_float(external_probability)",
    )

    for source in bad_sources:
        assert_scope_guard_fails(source, assert_no_decimal_boundary_regressions)


def test_forecast_calibration_scope_guard_rejects_forbidden_string_constants():
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


def test_forecast_calibration_imports_only_allowed_dependencies():
    tree = parse_forecast_calibration()

    assert set(imported_modules(tree)) <= ALLOWED_IMPORTS


def test_forecast_calibration_does_not_import_forbidden_surfaces():
    tree = parse_forecast_calibration()

    for module_name in imported_modules(tree):
        assert not any(
            module_name == forbidden or module_name.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_forecast_calibration_does_not_define_forbidden_names_or_operations():
    tree = parse_forecast_calibration()
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
    lowered = {normalize_identifier(name) for name in names}
    for fragment in FORBIDDEN_NAME_FRAGMENTS:
        assert not any(fragment in name for name in lowered), fragment


def test_forecast_calibration_does_not_define_banned_status_or_label_strings():
    tree = parse_forecast_calibration()

    assert_no_forbidden_status_label_advice_string_constants(tree)


def test_forecast_calibration_public_exports_are_exact():
    tree = parse_forecast_calibration()

    assert module_exports(tree) == EXPECTED_FORECAST_CALIBRATION_EXPORTS


def test_forecast_calibration_public_api_is_not_exported_from_package_root():
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

    for export_name in EXPECTED_FORECAST_CALIBRATION_EXPORTS:
        assert export_name not in package_root_names, export_name
