import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "phase_2_evidence_snapshot.py"
PACKAGE_ROOT_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "__init__.py"

EXPECTED_EXPORTS = (
    "PaperPhase2EvidenceSnapshotConfig",
    "PaperPhase2EvidenceGapRow",
    "PaperPhase2EvidenceSnapshotReport",
    "build_paper_phase_2_evidence_snapshot_report",
)

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "typing",
    "polymarket_alpha_lab.forecast_calibration",
    "polymarket_alpha_lab.strategy_segment_summary",
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
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.domain",
    "polymarket_alpha_lab.forecast_calibration_trend",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.pipeline",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.research",
    "polymarket_alpha_lab.runner",
    "polymarket_alpha_lab.strategy_cycle",
    "polymarket_alpha_lab.strategy_segment_summary_trend",
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
    "live",
    "liveexecution",
    "network",
    "order",
    "orderrouter",
    "placeorder",
    "privatekey",
    "rank",
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
    "order",
    "rank",
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
    "live",
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
    return tuple(modules)


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


def test_phase_2_evidence_snapshot_scope_guard_rejects_relative_forbidden_imports():
    assert_scope_guard_fails(
        "from . import cli",
        lambda tree: set(imported_modules(tree)) <= ALLOWED_IMPORT_MODULES,
    )


def test_phase_2_evidence_snapshot_scope_guard_rejects_forbidden_operations():
    bad_sources = (
        "client.connect()",
        "response = get(url)",
        "session.post(url)",
        "path.read_text()",
        "router.submit(order)",
    )

    for source in bad_sources:
        assert_scope_guard_fails(source, assert_no_forbidden_operations)


def test_phase_2_evidence_snapshot_scope_guard_rejects_boundary_names():
    bad_sources = (
        "def rank_segments():\n    return ()",
        "live_report = object()",
        "def build_order():\n    return None",
    )

    for source in bad_sources:
        assert_scope_guard_fails(
            source,
            lambda tree: [
                (
                    (_ for _ in ()).throw(AssertionError(name))
                    if any(
                        fragment in normalize_identifier(name)
                        for fragment in FORBIDDEN_NAME_FRAGMENTS
                    )
                    else None
                )
                for node in ast.walk(tree)
                for name in (
                    [node.name]
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    else [node.id]
                    if isinstance(node, ast.Name)
                    else [node.arg]
                    if isinstance(node, ast.arg)
                    else []
                )
            ],
        )


def test_phase_2_evidence_snapshot_scope_guard_rejects_decimal_boundary_regressions():
    bad_sources = (
        "ratio = 0.1000",
        "ratio = float(Decimal('0.1000'))",
        "ratio = Decimal.from_float(external_probability)",
    )

    for source in bad_sources:
        assert_scope_guard_fails(source, assert_no_decimal_boundary_regressions)


def test_phase_2_evidence_snapshot_scope_guard_rejects_forbidden_string_constants():
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


def test_phase_2_evidence_snapshot_imports_only_allowed_dependencies():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert module_name in ALLOWED_IMPORT_MODULES, module_name


def test_phase_2_evidence_snapshot_does_not_import_forbidden_surfaces():
    tree = parse_module()
    for module_name in imported_modules(tree):
        assert not any(
            module_matches_prefix(module_name, forbidden)
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), module_name


def test_phase_2_evidence_snapshot_public_exports_are_exact_report_api():
    assert module_exports(parse_module()) == EXPECTED_EXPORTS


def test_phase_2_evidence_snapshot_does_not_define_forbidden_surfaces():
    tree = parse_module()
    names = set()
    assert_no_decimal_boundary_regressions(tree)
    assert_no_forbidden_operations(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    for name in names:
        normalized = normalize_identifier(name)
        for fragment in FORBIDDEN_NAME_FRAGMENTS:
            assert fragment not in normalized, name
    assert_no_forbidden_status_label_advice_string_constants(tree)


def test_phase_2_evidence_snapshot_is_not_exported_from_package_root():
    package_tree = ast.parse(PACKAGE_ROOT_PATH.read_text(encoding="utf-8"))
    imported = imported_modules(package_tree)
    assert "polymarket_alpha_lab.phase_2_evidence_snapshot" not in imported

    root_source = PACKAGE_ROOT_PATH.read_text(encoding="utf-8")
    for export_name in EXPECTED_EXPORTS:
        assert export_name not in root_source
