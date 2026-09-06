from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
)

FORBIDDEN_IMPORT_ROOTS = frozenset(
    (
        "mongoengine",
        "motor",
        "pymongo",
        "redis",
        "sqlalchemy",
        "sqlite3",
    ),
)
FORBIDDEN_DYNAMIC_IMPORTS = FORBIDDEN_IMPORT_ROOTS
FORBIDDEN_CALL_NAMES = frozenset(("create_engine",))
FORBIDDEN_BACKEND_SCOPE_NEEDLES = tuple(
    sorted(
        {
            "__import__",
            "import_module",
            *FORBIDDEN_CALL_NAMES,
            *(
                f"import {backend}"
                for backend in FORBIDDEN_IMPORT_ROOTS
            ),
            *(
                f"from {backend}"
                for backend in FORBIDDEN_IMPORT_ROOTS
            ),
        },
    )
)
SRC_ROOT = REPO_ROOT / "src"
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
DURABLE_APPEND_CONTAINER_SUFFIXES = ("Log", "Journal")
DURABLE_FILE_WRITE_METHODS = frozenset(("write_bytes", "write_text"))
DURABLE_FILE_WRITE_CONTEXT_TOKENS = frozenset(
    (
        "archive",
        "archives",
        "artifact",
        "artifacts",
        "data",
        "raw",
    ),
)
DURABLE_FILE_PERSISTENCE_NEEDLES = (
    "def append",
    ".open(",
    "open(",
    "write_bytes",
    "write_text",
)
LEGACY_DURABLE_FILE_PERSISTENCE_ALLOWLIST = frozenset(
    (
        "src/polymarket_alpha_lab/analytics.py:457: durable file-backed append method PaperAnalyticsLog.append",
        "src/polymarket_alpha_lab/analytics.py:464: durable file append open(a)",
        "src/polymarket_alpha_lab/analytics_history.py:240: durable file-backed append method PaperAnalyticsHistoryLog.append",
        "src/polymarket_alpha_lab/analytics_history.py:247: durable file append open(a)",
        "src/polymarket_alpha_lab/archive.py:45: durable file write write_text",
        "src/polymarket_alpha_lab/archive.py:49: durable file write write_text",
        "src/polymarket_alpha_lab/book_imbalance_forecast.py:132: durable file-backed append method PaperBookImbalanceForecastLog.append",
        "src/polymarket_alpha_lab/book_imbalance_forecast.py:143: durable file append open(a)",
        "src/polymarket_alpha_lab/cost_aware_event_strategy.py:270: durable file-backed append method PaperCostAwareEventStrategyLog.append",
        "src/polymarket_alpha_lab/cost_aware_event_strategy.py:277: durable file append open(a)",
        "src/polymarket_alpha_lab/cost_aware_snapshot_builder.py:131: durable file-backed append method PaperCostAwareSnapshotLog.append",
        "src/polymarket_alpha_lab/cost_aware_snapshot_builder.py:139: durable file append open(a)",
        "src/polymarket_alpha_lab/forecast_evidence.py:304: durable file-backed append method PaperForecastEvidenceLog.append",
        "src/polymarket_alpha_lab/forecast_evidence.py:311: durable file append open(a)",
        "src/polymarket_alpha_lab/forecast_provider.py:98: durable file-backed append method PaperForecastLog.append",
        "src/polymarket_alpha_lab/forecast_provider.py:106: durable file append open(a)",
        "src/polymarket_alpha_lab/journal.py:247: durable file-backed append method PaperTradeJournal.append",
        "src/polymarket_alpha_lab/journal.py:250: durable file append open(a)",
        "src/polymarket_alpha_lab/llm_forecast.py:175: durable file-backed append method PaperLLMForecastLog.append",
        "src/polymarket_alpha_lab/llm_forecast.py:186: durable file append open(a)",
        "src/polymarket_alpha_lab/manual_review_queue.py:391: durable file-backed append method PaperManualReviewLog.append",
        "src/polymarket_alpha_lab/manual_review_queue.py:398: durable file append open(a)",
        "src/polymarket_alpha_lab/outcome_tracker.py:210: durable file-backed append method OutcomeTrackingLog.append",
        "src/polymarket_alpha_lab/outcome_tracker.py:224: durable file append open(a)",
        "src/polymarket_alpha_lab/paper_execution.py:171: durable file-backed append method PaperExecutionLog.append",
        "src/polymarket_alpha_lab/paper_execution.py:179: durable file append open(a)",
        "src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_log.py:47: durable file append open(a)",
        "src/polymarket_alpha_lab/positions.py:281: durable file-backed append method PaperNavLog.append",
        "src/polymarket_alpha_lab/positions.py:287: durable file append open(a)",
        "src/polymarket_alpha_lab/project_screening.py:263: durable file-backed append method PaperProjectScreeningLog.append",
        "src/polymarket_alpha_lab/project_screening.py:270: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison.py:347: durable file-backed append method TradeProposalEvidenceComparisonLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison.py:355: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history.py:314: durable file-backed append method TradeProposalEvidenceComparisonHistoryLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history.py:324: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py:382: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py:396: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py:348: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py:362: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py:302: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py:316: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py:304: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py:318: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py:307: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog.append",
        "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py:321: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_packet.py:120: durable file-backed append method TradeProposalPacketLog.append",
        "src/polymarket_alpha_lab/proposal_packet.py:127: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review.py:206: durable file-backed append method TradeProposalReviewLog.append",
        "src/polymarket_alpha_lab/proposal_review.py:213: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review_coverage.py:564: durable file-backed append method TradeProposalReviewCoverageLog.append",
        "src/polymarket_alpha_lab/proposal_review_coverage.py:571: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review_diagnostics.py:465: durable file-backed append method TradeProposalReviewDiagnosticLog.append",
        "src/polymarket_alpha_lab/proposal_review_diagnostics.py:472: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review_dossier.py:344: durable file-backed append method TradeProposalReviewDossierLog.append",
        "src/polymarket_alpha_lab/proposal_review_dossier.py:351: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review_dossier_batch.py:325: durable file-backed append method TradeProposalReviewDossierBatchLog.append",
        "src/polymarket_alpha_lab/proposal_review_dossier_batch.py:333: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review_quality.py:365: durable file-backed append method TradeProposalReviewQualityLog.append",
        "src/polymarket_alpha_lab/proposal_review_quality.py:372: durable file append open(a)",
        "src/polymarket_alpha_lab/proposal_review_summary.py:254: durable file-backed append method TradeProposalReviewSummaryLog.append",
        "src/polymarket_alpha_lab/proposal_review_summary.py:261: durable file append open(a)",
        "src/polymarket_alpha_lab/rejections.py:111: durable file-backed append method RejectedCandidateLog.append",
        "src/polymarket_alpha_lab/rejections.py:117: durable file append open(a)",
        "src/polymarket_alpha_lab/strategy_cycle.py:337: durable file-backed append method PaperStrategyCycleLog.append",
        "src/polymarket_alpha_lab/strategy_cycle.py:352: durable file append open(a)",
        "src/polymarket_alpha_lab/strategy_recommendation_log.py:56: durable file append open(a)",
        "src/polymarket_alpha_lab/strategy_risk_audit_log.py:29: durable file-backed append method PaperStrategyRiskAuditLog.append",
        "src/polymarket_alpha_lab/strategy_risk_audit_log.py:43: durable file append open(a)",
    ),
)
IDENTIFIER_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


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


def _durable_file_persistence_violations(
    path: Path,
    tree: ast.Module,
) -> tuple[StaticViolation, ...]:
    if not _is_src_path(path):
        return ()
    visitor = _DurableFilePersistenceVisitor(path)
    visitor.visit(tree)
    return tuple(visitor.violations)


def _is_src_path(path: Path) -> bool:
    try:
        path.relative_to(SRC_ROOT)
    except ValueError:
        return False
    return True


class _DurableFilePersistenceVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[StaticViolation] = []
        self._class_stack: list[str] = []
        self._function_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        if node.name.endswith(DURABLE_APPEND_CONTAINER_SUFFIXES):
            for statement in node.body:
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if statement.name == "append":
                        qualified_name = f"{node.name}.append"
                        self.violations.append(
                            StaticViolation(
                                self.path,
                                statement.lineno,
                                "durable file-backed append method",
                                qualified_name,
                            ),
                        )
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function_stack.append(node.name)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        append_mode = _append_open_mode(node)
        if append_mode is not None:
            name = f"open({append_mode})"
            self.violations.append(
                StaticViolation(
                    self.path,
                    node.lineno,
                    "durable file append",
                    name,
                ),
            )
        write_method = _durable_file_write_method(node)
        if write_method is not None and self._is_contextual_durable_file_write(node):
            self.violations.append(
                StaticViolation(
                    self.path,
                    node.lineno,
                    "durable file write",
                    write_method,
                ),
            )
        self.generic_visit(node)

    def _is_contextual_durable_file_write(self, node: ast.Call) -> bool:
        context = " ".join(
            (
                self.path.relative_to(REPO_ROOT).as_posix(),
                " ".join(self._class_stack),
                " ".join(self._function_stack),
                _unparse(node.func.value) if isinstance(node.func, ast.Attribute) else "",
            ),
        )
        return bool(_identifier_tokens(context) & DURABLE_FILE_WRITE_CONTEXT_TOKENS)

def _append_open_mode(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        if node.func.id != "open":
            return None
        mode = _builtin_open_mode(node)
    elif isinstance(node.func, ast.Attribute):
        if node.func.attr != "open":
            return None
        mode = _constant_open_mode(node)
    else:
        return None
    if mode is None or "a" not in mode:
        return None
    return mode


def _constant_open_mode(node: ast.Call) -> str | None:
    if node.args:
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            return first_arg.value
    for keyword in node.keywords:
        if keyword.arg == "mode":
            value = keyword.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
    return None


def _builtin_open_mode(node: ast.Call) -> str | None:
    if len(node.args) >= 2:
        second_arg = node.args[1]
        if isinstance(second_arg, ast.Constant) and isinstance(second_arg.value, str):
            return second_arg.value
    for keyword in node.keywords:
        if keyword.arg == "mode":
            value = keyword.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return value.value
    return None


def _durable_file_write_method(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        if node.func.attr in DURABLE_FILE_WRITE_METHODS:
            return node.func.attr
    return None


def _identifier_tokens(value: str) -> frozenset[str]:
    return frozenset(token.lower() for token in IDENTIFIER_TOKEN_RE.findall(value))


def _unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except ValueError:
        return ""


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


def _iter_function_direct_calls(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[ast.Call, ...]:
    calls: list[ast.Call] = []

    def visit(node: ast.AST) -> None:
        if node is not function_node and isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            return
        if isinstance(node, ast.Call):
            calls.append(node)
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in function_node.body:
        visit(statement)
    return tuple(calls)


def _nested_functions_with_prior_validation(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[ast.FunctionDef | ast.AsyncFunctionDef]:
    validated: set[ast.FunctionDef | ast.AsyncFunctionDef] = set()
    validator_lines = tuple(
        node.lineno
        for node in _iter_function_direct_calls(function_node)
        if (
            _call_name(node.func) in (LOCAL_DSN_VALIDATOR, "_validate_local_dsn")
            and _contains_dsn_reference(node)
        )
    )
    if not validator_lines:
        return validated
    first_validator_line = min(validator_lines)

    for statement in function_node.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(arg.arg == "dsn" for arg in statement.args.args):
                continue
            if statement.lineno > first_validator_line:
                validated.add(statement)
    return validated


def _local_dsn_validation_lines(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[int, ...]:
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


def _is_connection_wrapper(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
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
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[StaticViolation, ...]:
    validator_lines = _local_dsn_validation_lines(function_node)
    violations: list[StaticViolation] = []
    guard_wrapper_connectors = _is_connection_wrapper(function_node)
    prior_validated_nested_functions = _nested_functions_with_prior_validation(function_node)
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
        if any(
            nested_function.lineno < node.lineno < nested_function.end_lineno
            for nested_function in prior_validated_nested_functions
            if nested_function.end_lineno is not None
        ):
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
    # Walk all scopes intentionally: psycopg setup in class methods and async
    # helpers must satisfy the same local-DSN validation rule as top-level code.
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            violations.extend(_psycopg_setup_validation_violations(path, node))
    return tuple(violations)


def test_src_and_tests_do_not_import_or_create_nonlocal_persistence_backends() -> None:
    violations: list[StaticViolation] = []
    for path in _python_files():
        source_text = path.read_text(encoding="utf-8")
        lowered_source_text = source_text.lower()
        if not any(needle in lowered_source_text for needle in FORBIDDEN_BACKEND_SCOPE_NEEDLES):
            continue
        violations.extend(_forbidden_backend_violations(path, ast.parse(source_text, filename=str(path))))

    assert violations == [], _format_violations(tuple(violations))


def test_src_durable_file_backed_persistence_stays_on_legacy_allowlist() -> None:
    violations: list[StaticViolation] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        source_text = path.read_text(encoding="utf-8")
        if not any(needle in source_text for needle in DURABLE_FILE_PERSISTENCE_NEEDLES):
            continue
        violations.extend(_durable_file_persistence_violations(path, ast.parse(source_text, filename=str(path))))

    unexpected = tuple(
        violation
        for violation in violations
        if violation.render() not in LEGACY_DURABLE_FILE_PERSISTENCE_ALLOWLIST
    )
    assert unexpected == (), _format_violations(unexpected)


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


def test_durable_file_persistence_guard_catches_file_backed_write_patterns() -> None:
    fixture_tree = ast.parse(
        """
class PaperThingLog:
    def append(self, report):
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("durable jsonl")
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write("durable jsonl")

def persist_artifact(artifacts_dir, raw_dir):
    (artifacts_dir / "packet.json").write_text("{}", encoding="utf-8")
    (raw_dir / "snapshot.bin").write_bytes(b"raw")
""",
    )

    violations = _durable_file_persistence_violations(
        REPO_ROOT / "src" / "polymarket_alpha_lab" / "fixture.py",
        fixture_tree,
    )

    assert [violation.name for violation in violations] == [
        "PaperThingLog.append",
        "open(a)",
        "open(a)",
        "write_text",
        "write_bytes",
    ]


def test_durable_file_persistence_guard_ignores_non_src_support_files() -> None:
    fixture_tree = ast.parse(
        """
class PaperThingLog:
    def append(self, report):
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("fixture jsonl")

def write_artifact(artifacts_dir):
    (artifacts_dir / "packet.json").write_text("{}", encoding="utf-8")
""",
    )

    violations = _durable_file_persistence_violations(
        REPO_ROOT / "tests" / "fixture.py",
        fixture_tree,
    )

    assert violations == ()


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

class Store:
    def _with_owned_connection(self, dsn, connection_factory):
        connection = connection_factory()
        validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN")
        return connection

async def _with_async_connection(dsn, connection_factory):
    connection = connection_factory()
    validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN")
    return connection
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
        "connection_factory",
        "connection_factory",
    ]


def test_psycopg_adapter_validation_guard_does_not_exempt_nested_dsn_parameters() -> None:
    fixture_tree = ast.parse(
        """
def _with_owned_connection(dsn, operation):
    validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN")

    def nested_accepts_new_dsn(dsn):
        return _connect(dsn)

    return operation(nested_accepts_new_dsn)
""",
    )

    violations = _psycopg_adapter_validation_violations(
        REPO_ROOT / "src" / "fixture_psycopg.py",
        fixture_tree,
    )

    assert [violation.name for violation in violations] == ["_connect"]


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
