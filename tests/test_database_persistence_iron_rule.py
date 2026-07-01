from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
)

FORBIDDEN_IMPORT_ROOTS = frozenset(
    (
        "pymongo",
        "redis",
        "sqlalchemy",
        "sqlite3",
    ),
)
FORBIDDEN_DYNAMIC_IMPORTS = FORBIDDEN_IMPORT_ROOTS
FORBIDDEN_CALL_NAMES = frozenset(("create_engine",))
SMOKE_TEST_PATH_FRAGMENT = "_supabase_smoke"
LOCAL_DSN_VALIDATOR = "validate_local_postgres_dsn"
PSYCOPG_ADAPTER_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"
PSYCOPG_SETUP_CALLS_REQUIRING_DSN_VALIDATION = frozenset(
    (
        "_connect",
        "_jsonb_adapter",
        "_PsycopgJsonConnection",
    ),
)


@dataclass(frozen=True)
class StaticViolation:
    path: Path
    line_number: int
    kind: str
    name: str

    def render(self) -> str:
        relative_path = self.path.relative_to(REPO_ROOT)
        return f"{relative_path}:{self.line_number}: {self.kind} {self.name}"


def _python_files() -> tuple[Path, ...]:
    paths: list[Path] = []
    for scan_root in SCAN_ROOTS:
        paths.extend(scan_root.rglob("*.py"))
    return tuple(sorted(paths))


def _parse_file(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _forbidden_backend_violations(path: Path, tree: ast.Module) -> tuple[StaticViolation, ...]:
    violations: list[StaticViolation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_root = alias.name.split(".", 1)[0]
                if import_root in FORBIDDEN_IMPORT_ROOTS:
                    violations.append(
                        StaticViolation(path, node.lineno, "forbidden import", alias.name),
                    )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            import_root = module_name.split(".", 1)[0]
            if import_root in FORBIDDEN_IMPORT_ROOTS:
                violations.append(
                    StaticViolation(path, node.lineno, "forbidden import", module_name),
                )
        elif isinstance(node, ast.Call):
            violations.extend(_forbidden_call_violations(path, node))
    return tuple(violations)


def _forbidden_call_violations(path: Path, node: ast.Call) -> tuple[StaticViolation, ...]:
    call_name = _call_name(node.func)
    if call_name in FORBIDDEN_CALL_NAMES:
        return (StaticViolation(path, node.lineno, "forbidden call", call_name),)
    if call_name in {"__import__", "import_module"}:
        imported_name = _first_constant_string_arg(node)
        if imported_name is not None:
            import_root = imported_name.split(".", 1)[0]
            if import_root in FORBIDDEN_DYNAMIC_IMPORTS:
                return (
                    StaticViolation(
                        path,
                        node.lineno,
                        "forbidden dynamic import",
                        imported_name,
                    ),
                )
    return ()


def _call_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _call_qualname(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parent_name = _call_qualname(func.value)
        if parent_name is None:
            return func.attr
        return f"{parent_name}.{func.attr}"
    return None


def _first_constant_string_arg(node: ast.Call) -> str | None:
    if not node.args:
        return None
    first_arg = node.args[0]
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return first_arg.value
    return None


def _called_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                names.add(call_name)
    return names


def _format_violations(violations: tuple[StaticViolation, ...]) -> str:
    return "\n".join(violation.render() for violation in violations)


def _psycopg_adapter_paths() -> tuple[Path, ...]:
    return tuple(
        sorted(
            (
                *PSYCOPG_ADAPTER_ROOT.glob("*_psycopg.py"),
                *PSYCOPG_ADAPTER_ROOT.glob("*_psycopg_read.py"),
                PSYCOPG_ADAPTER_ROOT / "autonomous_market_scorer_load.py",
            ),
        ),
    )


def _contains_dsn_reference(node: ast.AST) -> bool:
    return any(isinstance(child, ast.Name) and child.id == "dsn" for child in ast.walk(node))


def _iter_immediate_function_calls(function_node: ast.FunctionDef) -> tuple[ast.Call, ...]:
    calls: list[ast.Call] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(node, ast.Call):
            calls.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in function_node.body:
        visit(statement)
    return tuple(calls)


def _local_dsn_validation_lines(function_node: ast.FunctionDef) -> tuple[int, ...]:
    return tuple(
        node.lineno
        for node in _iter_immediate_function_calls(function_node)
        if (
            _call_name(node.func) in (LOCAL_DSN_VALIDATOR, "_validate_local_dsn")
            and _contains_dsn_reference(node)
        )
    )


def _is_psycopg_setup_call_requiring_dsn_validation(node: ast.Call) -> bool:
    call_name = _call_name(node.func)
    if call_name not in PSYCOPG_SETUP_CALLS_REQUIRING_DSN_VALIDATION:
        return False
    if call_name == "_jsonb_adapter":
        return True
    if call_name == "_PsycopgJsonConnection":
        return _contains_dsn_reference(node)
    return _contains_dsn_reference(node) or call_name == "connection_factory"


def _is_connection_wrapper(function_node: ast.FunctionDef) -> bool:
    return function_node.name.startswith("_with_") and any(
        arg.arg == "dsn" for arg in function_node.args.args
    )


def _is_wrapper_connector_call_requiring_dsn_validation(node: ast.Call) -> bool:
    call_name = _call_name(node.func)
    if call_name == "_connect_with":
        return _contains_dsn_reference(node)
    if call_name == "connection_factory":
        return True
    if call_name == "connect" and _call_qualname(node.func) in {"connect", "psycopg.connect"}:
        return _contains_dsn_reference(node)
    return False


def _psycopg_setup_validation_violations(
    path: Path,
    function_node: ast.FunctionDef,
) -> tuple[StaticViolation, ...]:
    validator_lines = _local_dsn_validation_lines(function_node)
    violations: list[StaticViolation] = []
    guard_wrapper_connectors = _is_connection_wrapper(function_node)
    for node in _iter_immediate_function_calls(function_node):
        call_name = _call_name(node.func)
        requires_validation = _is_psycopg_setup_call_requiring_dsn_validation(node)
        if guard_wrapper_connectors:
            requires_validation = (
                requires_validation
                or _is_wrapper_connector_call_requiring_dsn_validation(node)
            )
        if not requires_validation:
            continue
        if not validator_lines or min(validator_lines) > node.lineno:
            violations.append(
                StaticViolation(
                    path,
                    node.lineno,
                    "psycopg setup before local dsn validation",
                    call_name,
                ),
            )
    return tuple(violations)


def _psycopg_adapter_validation_violations(
    path: Path,
    tree: ast.Module,
) -> tuple[StaticViolation, ...]:
    violations: list[StaticViolation] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            violations.extend(_psycopg_setup_validation_violations(path, node))
    return tuple(violations)


def test_src_and_tests_do_not_import_or_create_nonlocal_persistence_backends() -> None:
    violations: list[StaticViolation] = []
    for path in _python_files():
        violations.extend(_forbidden_backend_violations(path, _parse_file(path)))

    assert violations == [], _format_violations(tuple(violations))


def test_negative_strings_fake_psycopg_and_remote_dsn_fixtures_are_not_flagged() -> None:
    fixture_tree = ast.parse(
        """
REMOTE_DSN = "postgresql://postgres:super-secret-token@db.remote.example.com/postgres"
NEGATIVE_BACKEND_NAMES = ("sqlite3", "redis", "pymongo", "sqlalchemy", "create_engine")

class FakePsycopg:
    def connect(self, dsn: str) -> object:
        return object()

def test_remote_dsn_is_rejected_without_leaking_secret() -> None:
    message = "must point to local Supabase/Postgres"
    assert "super-secret-token" not in message
""",
    )

    assert _forbidden_backend_violations(REPO_ROOT / "tests" / "fixture.py", fixture_tree) == ()


def test_forbidden_backend_static_guard_catches_real_imports_and_engine_calls() -> None:
    fixture_tree = ast.parse(
        """
import redis
from sqlalchemy import create_engine

engine = create_engine("postgresql://localhost/postgres")
""",
    )

    violations = _forbidden_backend_violations(REPO_ROOT / "src" / "fixture.py", fixture_tree)

    assert [violation.name for violation in violations] == [
        "redis",
        "sqlalchemy",
        "create_engine",
    ]


def test_supabase_smoke_tests_validate_local_postgres_dsn_before_live_connect() -> None:
    smoke_paths = tuple(
        path for path in _python_files() if SMOKE_TEST_PATH_FRAGMENT in path.stem
    )
    assert smoke_paths, "expected at least one local Supabase smoke test"

    missing_validator_paths: list[Path] = []
    for path in smoke_paths:
        called_names = _called_names(_parse_file(path))
        if LOCAL_DSN_VALIDATOR not in called_names:
            missing_validator_paths.append(path)

    assert missing_validator_paths == [], "\n".join(
        str(path.relative_to(REPO_ROOT)) for path in missing_validator_paths
    )


def test_psycopg_adapters_validate_local_postgres_dsn_before_connection_setup() -> None:
    violations: list[StaticViolation] = []
    for path in _psycopg_adapter_paths():
        violations.extend(_psycopg_adapter_validation_violations(path, _parse_file(path)))

    assert violations == [], _format_violations(tuple(violations))


def test_psycopg_adapter_validation_guard_catches_setup_before_validation() -> None:
    fixture_tree = ast.parse(
        """
def _with_owned_connection(dsn, operation, connection_factory):
    first = connect(dsn)
    second = _connect_with(dsn, connect)
    third = psycopg.connect(dsn)
    connection = connection_factory()
    jsonb_adapter = _jsonb_adapter()
    wrapped = _PsycopgJsonConnection(_connect(dsn), jsonb_adapter)
    validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN")
    return operation(connection, first, second, third, wrapped)
""",
    )

    violations = _psycopg_adapter_validation_violations(
        REPO_ROOT / "src" / "fixture_psycopg.py",
        fixture_tree,
    )

    assert [violation.name for violation in violations] == [
        "connect",
        "_connect_with",
        "connect",
        "connection_factory",
        "_jsonb_adapter",
        "_PsycopgJsonConnection",
        "_connect",
    ]


def test_psycopg_adapter_validation_guard_allows_unrelated_connect_calls() -> None:
    fixture_tree = ast.parse(
        """
def unrelated_network_setup(dsn, connector, connection_factory):
    connector.connect()
    other.connect(dsn)
    connection_factory
    return dsn
""",
    )

    violations = _psycopg_adapter_validation_violations(
        REPO_ROOT / "src" / "fixture_psycopg.py",
        fixture_tree,
    )

    assert violations == ()
