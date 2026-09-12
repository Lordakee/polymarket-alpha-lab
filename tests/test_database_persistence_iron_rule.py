from __future__ import annotations

import ast
import re
import time
import weakref
from collections import Counter
from dataclasses import dataclass
from fnmatch import fnmatch
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.candidate_decision_score_store import candidate_decision_score_report_sink_from_config
from polymarket_alpha_lab.check_outcomes_paper_trade_source import load_check_outcomes_paper_trade_records
from polymarket_alpha_lab.strategy_candidate_research_queue_store import paper_strategy_candidate_research_queue_report_sink_from_config
from polymarket_alpha_lab.supabase_paper_trade_journal_config import SupabasePaperTradeJournalConfig
from polymarket_alpha_lab.supabase_strategy_candidate_research_queue_config import SupabaseStrategyCandidateResearchQueueConfig

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
LEGACY_DURABLE_FILE_PERSISTENCE_ALLOWLIST = frozenset((
        "src/polymarket_alpha_lab/analytics.py:457: durable file-backed append method PaperAnalyticsLog.append", "src/polymarket_alpha_lab/analytics.py:464: durable file append open(a)", "src/polymarket_alpha_lab/analytics_history.py:240: durable file-backed append method PaperAnalyticsHistoryLog.append", "src/polymarket_alpha_lab/analytics_history.py:247: durable file append open(a)", "src/polymarket_alpha_lab/archive.py:45: durable file write write_text", "src/polymarket_alpha_lab/archive.py:49: durable file write write_text", "src/polymarket_alpha_lab/book_imbalance_forecast.py:132: durable file-backed append method PaperBookImbalanceForecastLog.append", "src/polymarket_alpha_lab/book_imbalance_forecast.py:143: durable file append open(a)", "src/polymarket_alpha_lab/cost_aware_event_strategy.py:270: durable file-backed append method PaperCostAwareEventStrategyLog.append", "src/polymarket_alpha_lab/cost_aware_event_strategy.py:277: durable file append open(a)", "src/polymarket_alpha_lab/cost_aware_snapshot_builder.py:131: durable file-backed append method PaperCostAwareSnapshotLog.append", "src/polymarket_alpha_lab/cost_aware_snapshot_builder.py:139: durable file append open(a)", "src/polymarket_alpha_lab/forecast_evidence.py:304: durable file-backed append method PaperForecastEvidenceLog.append", "src/polymarket_alpha_lab/forecast_evidence.py:311: durable file append open(a)", "src/polymarket_alpha_lab/forecast_provider.py:98: durable file-backed append method PaperForecastLog.append", "src/polymarket_alpha_lab/forecast_provider.py:106: durable file append open(a)", "src/polymarket_alpha_lab/journal.py:247: durable file-backed append method PaperTradeJournal.append", "src/polymarket_alpha_lab/journal.py:250: durable file append open(a)", "src/polymarket_alpha_lab/llm_forecast.py:175: durable file-backed append method PaperLLMForecastLog.append", "src/polymarket_alpha_lab/llm_forecast.py:186: durable file append open(a)", "src/polymarket_alpha_lab/manual_review_queue.py:391: durable file-backed append method PaperManualReviewLog.append", "src/polymarket_alpha_lab/manual_review_queue.py:398: durable file append open(a)", "src/polymarket_alpha_lab/outcome_tracker.py:210: durable file-backed append method OutcomeTrackingLog.append", "src/polymarket_alpha_lab/outcome_tracker.py:224: durable file append open(a)", "src/polymarket_alpha_lab/paper_execution.py:171: durable file-backed append method PaperExecutionLog.append", "src/polymarket_alpha_lab/paper_execution.py:179: durable file append open(a)", "src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_log.py:47: durable file append open(a)", "src/polymarket_alpha_lab/positions.py:281: durable file-backed append method PaperNavLog.append", "src/polymarket_alpha_lab/positions.py:287: durable file append open(a)", "src/polymarket_alpha_lab/project_screening.py:263: durable file-backed append method PaperProjectScreeningLog.append", "src/polymarket_alpha_lab/project_screening.py:270: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison.py:347: durable file-backed append method TradeProposalEvidenceComparisonLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison.py:355: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison_history.py:314: durable file-backed append method TradeProposalEvidenceComparisonHistoryLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison_history.py:324: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py:382: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health.py:396: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py:348: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend.py:362: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py:302: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch.py:316: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py:304: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health.py:318: durable file append open(a)", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py:307: durable file-backed append method TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog.append", "src/polymarket_alpha_lab/proposal_evidence_comparison_history_batch_health_trend_batch_health_trend.py:321: durable file append open(a)", "src/polymarket_alpha_lab/proposal_packet.py:120: durable file-backed append method TradeProposalPacketLog.append", "src/polymarket_alpha_lab/proposal_packet.py:127: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review.py:206: durable file-backed append method TradeProposalReviewLog.append", "src/polymarket_alpha_lab/proposal_review.py:213: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review_coverage.py:564: durable file-backed append method TradeProposalReviewCoverageLog.append", "src/polymarket_alpha_lab/proposal_review_coverage.py:571: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review_diagnostics.py:465: durable file-backed append method TradeProposalReviewDiagnosticLog.append", "src/polymarket_alpha_lab/proposal_review_diagnostics.py:472: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review_dossier.py:344: durable file-backed append method TradeProposalReviewDossierLog.append", "src/polymarket_alpha_lab/proposal_review_dossier.py:351: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review_dossier_batch.py:325: durable file-backed append method TradeProposalReviewDossierBatchLog.append", "src/polymarket_alpha_lab/proposal_review_dossier_batch.py:333: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review_quality.py:365: durable file-backed append method TradeProposalReviewQualityLog.append", "src/polymarket_alpha_lab/proposal_review_quality.py:372: durable file append open(a)", "src/polymarket_alpha_lab/proposal_review_summary.py:254: durable file-backed append method TradeProposalReviewSummaryLog.append", "src/polymarket_alpha_lab/proposal_review_summary.py:261: durable file append open(a)", "src/polymarket_alpha_lab/rejections.py:111: durable file-backed append method RejectedCandidateLog.append", "src/polymarket_alpha_lab/rejections.py:117: durable file append open(a)", "src/polymarket_alpha_lab/strategy_cycle.py:327: durable file-backed append method PaperStrategyCycleLog.append", "src/polymarket_alpha_lab/strategy_cycle.py:342: durable file append open(a)", "src/polymarket_alpha_lab/strategy_recommendation_log.py:56: durable file append open(a)", "src/polymarket_alpha_lab/strategy_risk_audit_log.py:29: durable file-backed append method PaperStrategyRiskAuditLog.append", "src/polymarket_alpha_lab/strategy_risk_audit_log.py:43: durable file append open(a)",
    ),)
IDENTIFIER_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")

@dataclass(frozen=True)
class StaticViolation:
    path: Path
    line_number: int
    kind: str
    name: str
    def render(self) -> str:
        relative_path = self.path.relative_to(REPO_ROOT).as_posix()
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
    assert violations[0].render() == (
        "src/polymarket_alpha_lab/fixture.py:3: "
        "durable file-backed append method PaperThingLog.append"
    )
    assert all(
        violation.render() not in LEGACY_DURABLE_FILE_PERSISTENCE_ALLOWLIST
        for violation in violations
    )

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

# ---- Local DSN boundary pins (2026-09-09-dsn-hardening-finish-audit plan) ----

LOCAL_DSN_VALIDATOR_SHIM = "_validate_local_dsn"
LOCAL_DSN_VALIDATOR_NAMES = frozenset((LOCAL_DSN_VALIDATOR, LOCAL_DSN_VALIDATOR_SHIM))
SHARED_VALIDATOR_MODULE = "polymarket_alpha_lab.supabase_local_dsn"
DSN_ENV_KEY_RE = re.compile(r"dsn|database_url", re.IGNORECASE)
CONFIG_MODULE_PATTERN = "supabase_*config.py"
CLI_BOUNDARY_FILENAME, CLI_RELATIVE_PATH = "cli.py", "src/polymarket_alpha_lab/cli.py"
EXPECTED_CLI_CONNECT_SITE_COUNT = 35
EXPECTED_CLI_CONNECT_OPERANDS = {"agreement_dsn": 1, "dsn": 28, "operator_flow_dsn": 1, "quality_dsn": 1,
                                 "screening_gate_dsn": 2, "scorer_dsn": 1, "selection_summary_dsn": 1}
BOUNDARY_FILE_PATHS = ("src/polymarket_alpha_lab/candidate_decision_score_store.py", "src/polymarket_alpha_lab/check_outcomes_paper_trade_source.py",
                       "src/polymarket_alpha_lab/cli.py", "src/polymarket_alpha_lab/strategy_candidate_research_queue_store.py")
BOUNDARY_SCOPE_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
# Boundary specs: ("function", name, call, operand_mode, kind) or ("method", class, method, ...).
INTERMEDIARY_BOUNDARY_SPECS = {
    "candidate_decision_score_store.py": (
        ("function", "candidate_decision_score_report_sink_from_config", "_CandidateDecisionScoreReportSink", ("kw", "dsn"), "intermediary sink before local dsn validation"),
        ("method", "_CandidateDecisionScoreReportSink", "__call__", "connection_factory", ("arg", ""), "intermediary callback before local dsn validation")),
    "strategy_candidate_research_queue_store.py": (
        ("function", "paper_strategy_candidate_research_queue_report_sink_from_config", "_StrategyCandidateResearchQueueReportSink", ("kw", "dsn"), "intermediary sink before local dsn validation"),
        ("method", "_StrategyCandidateResearchQueueReportSink", "__call__", "_report_sink", ("kw", "dsn"), "intermediary callback before local dsn validation")),
    "check_outcomes_paper_trade_source.py": (
        ("function", "load_check_outcomes_paper_trade_records", "db_loader", ("kw", "dsn"), "intermediary loader before local dsn validation"),),
}
# Frozen literal connector allowlist (sorted): base 58 adapters + scorer_load + cli; globs approve nothing.
FROZEN_CONNECTOR_ALLOWLIST = frozenset((
    "src/polymarket_alpha_lab/research_capture_psycopg.py",
    "src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_psycopg.py", "src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_decision_support_trend_psycopg.py", "src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_history_psycopg.py", "src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_psycopg.py", "src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_psycopg_read.py", "src/polymarket_alpha_lab/autonomous_market_scorer_load.py", "src/polymarket_alpha_lab/autonomous_market_scorer_psycopg.py", "src/polymarket_alpha_lab/candidate_decision_score_psycopg.py", "src/polymarket_alpha_lab/cli.py", "src/polymarket_alpha_lab/local_observability_trends_psycopg.py", "src/polymarket_alpha_lab/outcome_tracking_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_health_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics_evaluation_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_psycopg_read.py", "src/polymarket_alpha_lab/paper_autonomous_investment_ledger_db_history_health_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_investment_ledger_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_proposal_risk_gate_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_readiness_digest_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_readiness_gate_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_psycopg_read.py", "src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_transition_psycopg.py", "src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_transition_trend_psycopg.py", "src/polymarket_alpha_lab/paper_broker_psycopg.py", "src/polymarket_alpha_lab/paper_execution_reconciliation_psycopg.py", "src/polymarket_alpha_lab/paper_nav_snapshot_psycopg.py", "src/polymarket_alpha_lab/paper_order_lifecycle_psycopg.py", "src/polymarket_alpha_lab/paper_probability_recommendation_queue_psycopg.py", "src/polymarket_alpha_lab/paper_probability_selection_summary_history_psycopg.py", "src/polymarket_alpha_lab/paper_probability_selection_summary_psycopg.py", "src/polymarket_alpha_lab/paper_project_screening_rank_stability_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_consistency_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_health_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_quality_history_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_quality_summary_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_readiness_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_reason_trend_health_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_reason_trend_psycopg.py", "src/polymarket_alpha_lab/paper_recommendation_risk_budget_psycopg.py", "src/polymarket_alpha_lab/paper_research_packet_operator_flow_psycopg.py", "src/polymarket_alpha_lab/paper_research_packet_psycopg.py", "src/polymarket_alpha_lab/paper_strategy_cycle_report_history_gate_psycopg.py", "src/polymarket_alpha_lab/paper_strategy_cycle_report_psycopg.py", "src/polymarket_alpha_lab/paper_trade_attribution_psycopg.py", "src/polymarket_alpha_lab/paper_trade_cost_audit_psycopg.py", "src/polymarket_alpha_lab/paper_trade_journal_psycopg.py", "src/polymarket_alpha_lab/probability_selection_scorer_agreement_psycopg.py", "src/polymarket_alpha_lab/probability_selection_scorer_agreement_trend_gate_psycopg.py", "src/polymarket_alpha_lab/strategy_candidate_research_queue_history_psycopg.py", "src/polymarket_alpha_lab/strategy_candidate_research_queue_psycopg.py", "src/polymarket_alpha_lab/strategy_candidate_research_queue_psycopg_read.py", "src/polymarket_alpha_lab/strategy_recommendation_rank_stability_psycopg.py", "src/polymarket_alpha_lab/strategy_recommendation_reason_trend_psycopg.py", "src/polymarket_alpha_lab/strategy_risk_audit_psycopg.py", "src/polymarket_alpha_lab/team_diagnostics_snapshot_psycopg.py", "src/polymarket_alpha_lab/team_evidence_aggregation_attempt_psycopg.py", "src/polymarket_alpha_lab/team_forecast_psycopg.py", "src/polymarket_alpha_lab/team_research_assignment_psycopg.py",
))

@lru_cache(maxsize=None)
def _parse_cached(relative_path):
    return ast.parse((REPO_ROOT / relative_path).read_text(encoding="utf-8"), filename=relative_path)

@lru_cache(maxsize=None)
def _src_relative_paths():
    return tuple(p.relative_to(REPO_ROOT).as_posix() for p in sorted(SRC_ROOT.rglob("*.py")))

def _parent_map(tree):
    return {id(child): parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

def _enclosing_statement(node, parents):
    current = node
    while current is not None and not isinstance(current, ast.stmt):
        current = parents.get(id(current))
    return current

def _enclosing_block(statement, parents):
    node = parents.get(id(statement))
    while node is not None:
        for field in ("body", "orelse", "finalbody"):
            if isinstance(block := getattr(node, field, None), list) and statement in block:
                return node, block.index(statement), field
        node = parents.get(id(node))
    return None, -1, None

def _containing_function(node, parents):
    current = node
    while current is not None:
        if isinstance(current, BOUNDARY_SCOPE_NODE_TYPES):
            return current
        current = parents.get(id(current))
    return None

def _path_profile(node, function_node, parents):
    """(if guards, solid blocks) to the function."""
    if_guards = []
    solid_blocks = []
    statement = _enclosing_statement(node, parents)
    while statement is not None and statement is not function_node:
        owner, _index, field = _enclosing_block(statement, parents)
        if owner is None:
            break
        if isinstance(owner, ast.If) and field == "body":
            if_guards.append((ast.dump(owner.test), owner.lineno, id(owner), frozenset(
                c.id for c in ast.walk(owner.test) if isinstance(c, ast.Name))))
        else: solid_blocks.append((id(owner), field))
        statement = owner if isinstance(owner, ast.stmt) else _enclosing_statement(owner, parents)
    return if_guards, solid_blocks

def _psycopg_inventory(tree):  # -> (module aliases, connect aliases, first import line, calls)
    module_aliases = set(); connect_aliases = set(); first_line = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "psycopg" or alias.name.startswith("psycopg."):
                    module_aliases.add(alias.asname or alias.name.split(".", 1)[0]); \
                    first_line = node.lineno if first_line is None else min(first_line, node.lineno)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".", 1)[0] == "psycopg":
            first_line = node.lineno if first_line is None else min(first_line, node.lineno)
            for alias in node.names:
                module_aliases.add(alias.asname or alias.name)
            connect_aliases.update(
                a.asname or a.name for a in node.names if a.name == "connect")
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and (
        (isinstance(node.func, ast.Attribute) and node.func.attr == "connect"
         and isinstance(node.func.value, ast.Name) and node.func.value.id in module_aliases)
        or (isinstance(node.func, ast.Name) and node.func.id in connect_aliases))]
    calls.sort(key=lambda site: (site.lineno, site.col_offset))
    return module_aliases, connect_aliases, first_line, calls

def _dsn_call_operand(call, operand_mode=("arg", "")):
    if operand_mode[0] == "arg":
        operand = call.args[0] if call.args else None
    else:
        operand = next((k.value for k in call.keywords if k.arg == operand_mode[1]), None)
    if operand is not None:
        return operand
    return next((k.value for k in call.keywords if k.arg in ("dsn", "conninfo")), None)

def _operand_dependency_tokens(operand):  # dsns[0] -> dsns; boxes[0].dsn -> boxes
    return frozenset(n.id for n in ast.walk(operand) if isinstance(n, ast.Name))

def _target_tokens(target):
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Attribute, ast.Subscript)):  # dsns[0] -> dsns;
        # boxes[0].config.dsn -> boxes; X.__dict__["k"] -> X (full text + deps)
        return {_unparse(target)} | _operand_dependency_tokens(target)
    if isinstance(target, (ast.Tuple, ast.List, ast.Set)):
        return set().union(*(_target_tokens(e) for e in target.elts))
    return _target_tokens(target.value) if isinstance(target, ast.Starred) else set()

def _bound_tokens(node):
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return {a.asname or a.name.split(".", 1)[0] for a in node.names}
    if isinstance(node, (ast.Assign, ast.Delete)):
        targets = list(node.targets)
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor,
                           ast.comprehension, ast.NamedExpr)):
        targets = [node.target]
    elif isinstance(node, (ast.With, ast.AsyncWith)):
        targets = [item.optional_vars for item in node.items]
    elif isinstance(node, (ast.Try, ast.TryStar, ast.Match, ast.match_case)):  # captures
        return ({n.name for n in ast.walk(node) if isinstance(
                    n, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and n.name}
                | {n.rest for n in ast.walk(node) if isinstance(n, ast.MatchMapping) and n.rest})
    else:
        return set()
    tokens = set()
    for target in targets:
        tokens.update(_target_tokens(target))
    return tokens

def _definition_time_rebinds(node):
    """(pos, tokens) for definition-time bindings: own name, defaults, decorators, bases, bodies."""
    hits = []
    def note_self(d):
        if getattr(d, "name", None): hits.append(((d.lineno, d.col_offset), {d.name}))
    def scan_expr(expr):
        stack = [expr]
        while stack:
            n = stack.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)): scan_def(n); continue
            if isinstance(n, ast.NamedExpr): hits.append(((n.lineno, n.col_offset), _target_tokens(n.target)))
            stack.extend(ast.iter_child_nodes(n))
    def scan_def(d):
        note_self(d); args = getattr(d, "args", None)
        if args is not None:
            for expr in list(args.defaults) + [k for k in args.kw_defaults if k]: scan_expr(expr)
        for dec in getattr(d, "decorator_list", []): scan_expr(dec)
    def scan_class(cls):
        note_self(cls)
        for expr in cls.decorator_list + cls.bases + [k.value for k in cls.keywords]:
            scan_expr(expr)
        scan_executed(cls.body)
    def scan_executed(stmts):  # class bodies run now; def/lambda bodies deferred
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                scan_def(stmt)
            elif isinstance(stmt, ast.ClassDef):
                scan_class(stmt)
            else:
                bound = _bound_tokens(stmt) | (set(stmt.names) if isinstance(
                    stmt, (ast.Nonlocal, ast.Global)) else set())
                if bound: hits.append(((stmt.lineno, stmt.col_offset), bound))
                hits.extend((pos, {nm}) for pos, nm in _capture_bindings(stmt))
                for child in ast.iter_child_nodes(stmt):
                    if isinstance(child, ast.expr):
                        scan_expr(child)
                    elif isinstance(child, ast.stmt):
                        scan_executed([child])
                    elif not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda,
                                                ast.ClassDef)):  # handler bodies
                        scan_executed([s for s in ast.iter_child_nodes(child) if isinstance(s, ast.stmt)])
                        for sub in ast.iter_child_nodes(child):
                            if isinstance(sub, ast.expr): scan_expr(sub)
    scan_class(node) if isinstance(node, ast.ClassDef) else scan_def(node); return hits

def _capture_bindings(node):
    """(binding pos, name) for implicit captures."""
    caps = [((h.type.end_lineno, h.type.end_col_offset) if h.type else (h.lineno, h.col_offset), h.name)
            for h in ast.walk(node) if isinstance(h, ast.ExceptHandler) and h.name]
    caps += [((n.end_lineno, n.end_col_offset), nm) for n in ast.walk(node)
             if isinstance(n, (ast.MatchAs, ast.MatchStar, ast.MatchMapping))
             for nm in (getattr(n, "name", None), getattr(n, "rest", None)) if nm]
    return tuple(caps)
def _outside_validator_deps(value):
    """Root names in the value OUTSIDE validator call args only."""
    skip: set[int] = set()
    for c in ast.walk(value):
        if isinstance(c, ast.Call) and _call_name(c.func) in (LOCAL_DSN_VALIDATOR, LOCAL_DSN_VALIDATOR_SHIM):
            skip.update(id(x) for x in ast.walk(c))
    deps: set[str] = set()
    for n in ast.walk(value):
        if id(n) in skip: continue
        if isinstance(n, ast.Name): deps.add(n.id)
        elif isinstance(n, ast.Attribute):
            root = n
            while isinstance(root, ast.Attribute): root = root.value
            if isinstance(root, ast.Name): deps.add(root.id)
    return deps
WRITE_METHOD_FAMILY = frozenset({"update", "__setattr__", "__setitem__", "pop", "popitem", "clear", "setdefault", "__ior__", "__iand__", "__isub__", "__ixor__"}); BUILTIN_WRITE_FUNCS = frozenset({"setattr", "dict", "object", "type"})
_ALIAS_CACHE: "weakref.WeakKeyDictionary[ast.AST, dict[frozenset, tuple]]" = weakref.WeakKeyDictionary()

def _alias_tokens(function_node, tokens):
    """Fixpoint (aliases, roots, wfa, wfa_unbound) over the WHOLE function: a
    binding referencing a protected name outside validator args creates an
    alias and roots its origins; wfa: write-func alias -> receiver deps;
    wfa_unbound: those callable UNBOUND (bare target = FIRST argument)."""
    if (key := frozenset(tokens)) in (per_fn := _ALIAS_CACHE.setdefault(function_node, {})): return per_fn[key]
    nodes = list(ast.walk(function_node)); aliases, roots = set(), set(); wfa: dict[str, frozenset] = {}; wfa_unbound: set[str] = set(); grew = True
    while grew:
        grew = False
        for n in nodes:
            pairs = []
            if isinstance(n, ast.Assign): pairs = [(n.value, t) for t in n.targets]
            elif isinstance(n, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)): pairs = [(getattr(n, "value", None), n.target)]
            elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)): pairs = [(n.iter, n.target)]
            elif isinstance(n, (ast.With, ast.AsyncWith)): pairs = [(i.context_expr, i.optional_vars) for i in n.items]
            elif isinstance(n, ast.ExceptHandler) and n.name and n.type is not None: pairs = [(n.type, ast.Name(id=n.name, ctx=ast.Load()))]
            elif isinstance(n, ast.Match):
                names = [p.name for c in n.cases for p in ast.walk(c.pattern) if isinstance(p, (ast.MatchAs, ast.MatchStar)) and p.name] + [
                    p.rest for c in n.cases for p in ast.walk(c.pattern) if isinstance(p, ast.MatchMapping) and p.rest]
                pairs = [(n.subject, ast.Name(id=nm, ctx=ast.Load())) for nm in names]
            for value, target in pairs:
                if value is None or target is None: continue
                odeps = _outside_validator_deps(value); ttoks = _target_tokens(target)
                wdep, wun = _write_source_deps(value, wfa, wfa_unbound)  # write-func alias (r27-r30)
                for t, ve in ([(target.id, value)] if isinstance(target, ast.Name) else _unpack_pairs(target, value)
                              if isinstance(target, (ast.Tuple, ast.List)) else []) if wdep is not None else []:
                    vd, vu = (wdep, wun) if ve is value else _write_source_deps(ve, wfa, wfa_unbound)
                    # r30: non-write unpack leaves (vd None) never merge
                    if vd is not None and (m := wfa.get(t, frozenset()) | vd) != wfa.get(t, frozenset()):
                        wfa[t] = m; grew = True
                    if vd is not None and vu and t not in wfa_unbound: wfa_unbound.add(t); grew = True
                if odeps & (tokens | aliases | roots):
                    grew |= bool((ttoks - aliases) | (odeps - roots)); aliases |= ttoks; roots |= odeps
                elif ttoks & (tokens | aliases | roots) and odeps - roots: roots |= odeps; grew = True
    per_fn[key] = (aliases, roots, wfa, wfa_unbound); return per_fn[key]
def _write_hit(node, toks, aliases, wfa, wunb):
    """Indirect write of the operand or an alias: setattr, write-family
    methods unbound through dict/type-name receivers (target = FIRST arg;
    bound dunders keep args[0] as KEY, r30-FP), a bare wfa call (BOUND forms
    hit receiver origins only), IfExp/IIFE callees, attr/subscript, for/comp/with."""
    if isinstance(node, ast.Call):
        f = node.func
        # r31: IIFE callee (direct or an IfExp branch): the called lambda body
        # runs NOW (value-position lambdas inside stay pruned — r31-FP); args,
        # kwarg values and the callee lambda's own DEFAULTS bind at call time,
        # so their dep names and — when any of them flows a protected value —
        # EVERY parameter name join the write-hit token set (conservative)
        for lf in ([f] if isinstance(f, ast.Lambda) else
                   [b for b in (f.body, f.orelse) if isinstance(b, ast.Lambda)] if isinstance(f, ast.IfExp) else []):
            srcs = [*node.args, *(k.value for k in node.keywords), *lf.args.defaults,
                    *(x for x in lf.args.kw_defaults if x is not None)]
            adeps = set().union(*map(_operand_dependency_tokens, srcs)) if srcs else frozenset()
            ht = toks | adeps | ({a.arg for a in [*lf.args.posonlyargs, *lf.args.args, *lf.args.kwonlyargs]}
                                 if adeps & (toks | aliases) else frozenset())
            # full call subtree scanned ONCE (r31): args, kwarg values and the
            # callee's DEFAULTS run NOW alongside the CALLED body — the root
            # lf.body included; nested IIFE calls are skipped (their bodies
            # already flatten into this same stream — no exponential rescan)
            stream = [*srcs, lf.body, *_immediate_subtree(lf.body)]
            if any(_write_hit(n, ht, aliases, wfa, wunb) for n in stream
                   if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Lambda))): return True
        # r28-r31: ANY callee expression resolves through _write_source_deps —
        # bound deps hit receiver origins, unbound hits the FIRST argument
        d, un = _write_source_deps(f, wfa, wunb)
        if d is not None and (d & (toks | aliases) or (un and node.args and
                _operand_dependency_tokens(node.args[0]) & (toks | aliases))): return True
        if _call_name(f) == "setattr" and node.args: return bool(_operand_dependency_tokens(node.args[0]) & (toks | aliases))
        return False
    targets = ([node.target] if isinstance(node, (ast.For, ast.AsyncFor, ast.AnnAssign,
                                                   ast.AugAssign, ast.comprehension)) else
               list(node.targets) if isinstance(node, (ast.Assign, ast.Delete)) else
               [i.optional_vars for i in node.items] if isinstance(node, (ast.With, ast.AsyncWith)) else [])
    return any(isinstance(t, (ast.Attribute, ast.Subscript)) and _operand_dependency_tokens(t) & (toks | aliases) for target in targets if target is not None for t in ast.walk(target))
def _immediate_subtree(root):
    """Nodes executed NOW: def/lambda/class expose only their immediate region
    — EXCEPT a callee-position lambda (IIFE), whose body runs now."""
    out, stack, full = [], [root], set()
    while stack:
        n = stack.pop()
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Lambda): full.add(id(n.func))
        kids = (list(ast.iter_child_nodes(n)) if id(n) in full or not isinstance(
                n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)) else
                [*getattr(n, "decorator_list", []), *n.args.defaults, *(x for x in n.args.kw_defaults if x is not None)]
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) else
                [*n.decorator_list, *n.bases, *(k.value for k in n.keywords)])
        out.extend(kids); stack.extend(kids)
    return out
def _unpack_pairs(t, v):
    """(name, value-leaf) pairs from positional unpacking at any depth."""
    if isinstance(t, ast.Starred): t = t.value
    if isinstance(t, (ast.Tuple, ast.List)):
        elts = v.elts if isinstance(v, (ast.Tuple, ast.List)) else [v]
        return ([p for te, ve in zip(t.elts, elts) for p in _unpack_pairs(te, ve)] if len(t.elts) == len(elts)
                else [(n.id, v) for n in ast.walk(t) if isinstance(n, ast.Name)])
    return [(t.id, v)] if isinstance(t, ast.Name) else []
def _write_source_deps(value, wfa, wunb):
    """(deps, unbound) when value IS a write function: write-family attribute
    (unbound iff rooted at dict/unbound type alias), builtin, chained, or an
    IfExp/tuple/list combining such sources."""
    if isinstance(value, ast.Name): return ((wfa[value.id], value.id in wunb) if value.id in wfa
        else (frozenset((value.id,)), True) if value.id in BUILTIN_WRITE_FUNCS else (None, False))
    if isinstance(value, ast.Attribute) and value.attr in WRITE_METHOD_FAMILY:
        root = value.value
        while isinstance(root, (ast.Attribute, ast.Subscript)): root = root.value
        return frozenset(_outside_validator_deps(value)), isinstance(root, ast.Name) and root.id in {"dict", "object", "type", *wunb}
    if isinstance(value, ast.Starred): value = value.value  # r31: *(...) unpack
    if isinstance(value, (ast.IfExp, ast.Tuple, ast.List, ast.BoolOp, ast.Subscript)):
        xs = ((value.body, value.orelse) if isinstance(value, ast.IfExp) else value.values if isinstance(value, ast.BoolOp)
              else value.elts if isinstance(value, (ast.Tuple, ast.List)) else value.value.elts
              if isinstance(value.value, (ast.Tuple, ast.List)) else [value.value])  # r31: (d.u,)[0]
        parts = [p for p in (_write_source_deps(x, wfa, wunb) for x in xs) if p[0] is not None]
        return (frozenset().union(*[p[0] for p in parts]), any(p[1] for p in parts)) if parts else (None, False)
    return None, False
def _rebinding_between(function_node, tokens, start_pos, end_pos):
    if not tokens: return False
    aliases, roots, wfa, wunb = _alias_tokens(function_node, tokens)
    write_toks = tokens | aliases | roots  # writes on aliases AND origin roots void
    def dt_writes(d):  # r28-r30: a def/lambda/class immediate region evaluates NOW
        return any(isinstance(w, ast.Call) and _write_hit(w, write_toks, aliases, wfa, wunb) and start_pos < (w.lineno, w.col_offset) < end_pos for w in _immediate_subtree(d))
    def visit(node):
        if node is not function_node and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            # class bodies execute NOW; nested defs/classes expose regions (r28/r29)
            if isinstance(node, ast.ClassDef):
                stack = list(node.body)
                while stack:
                    s = stack.pop()
                    if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                        if dt_writes(s): return True
                        if isinstance(s, ast.ClassDef): stack.extend(s.body)
                        continue
                    # r30: the STMT node itself counts (target writes need it)
                    if start_pos < (pos := (getattr(s, "lineno", -1), getattr(s, "col_offset", -1))) < end_pos and any(
                            _write_hit(n, write_toks, aliases, wfa, wunb) for n in (s, *_immediate_subtree(s))): return True
                    stack.extend(c for c in ast.iter_child_nodes(s) if isinstance(c, (ast.stmt, ast.ExceptHandler, ast.match_case)))  # r30
            # definition-time regions evaluate NOW (r28); bodies pruned (r29)
            if dt_writes(node): return True
            return any(tokens & bound and start_pos < pos < end_pos for pos, bound in _definition_time_rebinds(node))
        if isinstance(node, (ast.Try, ast.TryStar, ast.Match, ast.match_case, ast.ExceptHandler, ast.MatchAs, ast.MatchStar, ast.MatchMapping)):
            if any(name in tokens and start_pos < cap < end_pos for cap, name in _capture_bindings(node)): return True
        if isinstance(node, (ast.With, ast.AsyncWith)):  # ``as`` binds after the head
            for item in node.items:
                if (var := item.optional_vars) is not None and tokens & _target_tokens(var):
                    var_pos = max((n.end_lineno, n.end_col_offset) for n in ast.walk(var) if isinstance(n, ast.expr))
                    if start_pos < var_pos < end_pos: return True
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            value = getattr(node, "value", None)  # binds once the RHS finishes
            bind_pos = (value.end_lineno, value.end_col_offset) if value is not None else (node.lineno, node.col_offset)
            if tokens & _bound_tokens(node) and start_pos < bind_pos < end_pos: return True
        if isinstance(node, (ast.For, ast.AsyncFor)):
            bind_pos = (node.iter.end_lineno, node.iter.end_col_offset)  # binds after iter
            if tokens & _target_tokens(node.target) and start_pos < bind_pos < end_pos: return True
        node_pos = (getattr(node, "lineno", -1), getattr(node, "col_offset", -1))
        in_window = start_pos < node_pos < end_pos
        # write hits land at the BINDING point (with: per item; for: iter end;
        # else node END; comprehensions borrow their widest descendant end)
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for i in node.items:
                if i.optional_vars is None: continue
                ends = [(t.end_lineno, t.end_col_offset) for t in ast.walk(i.optional_vars) if isinstance(t, ast.expr)]
                item_pos = max(ends) if ends else (-1, -1)
                if start_pos < item_pos < end_pos and any(isinstance(t, (ast.Attribute, ast.Subscript))
                        and _operand_dependency_tokens(t) & (write_toks | aliases)
                        for t in ast.walk(i.optional_vars)): return True
            write_pos = (-1, -1)  # per-item checks already ran
        elif isinstance(node, (ast.For, ast.AsyncFor)): write_pos = (node.iter.end_lineno, node.iter.end_col_offset)
        else:
            write_pos = (getattr(node, "end_lineno", None), getattr(node, "end_col_offset", None))
            if write_pos[0] is None: write_pos = max([(d.end_lineno, d.end_col_offset) for d in
                    ast.walk(node) if getattr(d, "end_lineno", None) is not None] or [(-1, -1)])
        if start_pos < write_pos < end_pos and _write_hit(node, write_toks, aliases, wfa, wunb): return True
        if in_window and ((isinstance(node, (ast.Nonlocal, ast.Global)) and tokens & set(node.names))
                          or tokens & _bound_tokens(node)): return True
        return any(visit(child) for child in ast.iter_child_nodes(node))
    return visit(function_node)

def _with_target_call_guards(tree):  # -> (tokens, excluded call ids) per with
    guards = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)): continue
        trigger_tokens = set()
        for item in node.items:
            if item.optional_vars is not None and any(isinstance(n, ast.Call) for n in ast.walk(
                    item.optional_vars)): trigger_tokens.update(_target_tokens(item.optional_vars))
            for part in (item.context_expr, item.optional_vars):
                if part is not None: trigger_tokens.update(
                    *(_target_tokens(n.target) for n in ast.walk(part) if isinstance(n, ast.NamedExpr)))
        if trigger_tokens: guards.append((frozenset(trigger_tokens), frozenset(
            id(n) for n in ast.walk(node) if isinstance(n, ast.Call))))
    return tuple(guards)

def _validated_on_path(protected_call, operand, function_node, parents,
                       validator_state, connect_ids, with_guards):
    """True when the shared validator runs on every path reaching the call."""
    if isinstance(function_node, ast.Lambda): return False
    operand_text = _unparse(operand); operand_tokens = {operand_text} | _operand_dependency_tokens(operand)
    # a WRITE in the protected call's args voids the proof — but args evaluate
    # LEFT-TO-RIGHT (only writes BEFORE the operand's LAST direct read count,
    # r27-FP) and arg lambda/def BODIES never execute in the call (r29-FP)
    arg_aliases, arg_roots, arg_wfa, arg_wunb = _alias_tokens(function_node, operand_tokens)
    direct = [a for a in (*protected_call.args, *(k.value for k in protected_call.keywords)) if a is operand]
    read_pos = max((a.lineno, a.col_offset) for a in direct) if direct else (-1, -1)
    if any(operand_tokens & _target_tokens(n.target) for n in _immediate_subtree(protected_call) if isinstance(n, ast.NamedExpr) and (n.lineno, n.col_offset) < read_pos): return False
    if any((getattr(n, "lineno", -1), getattr(n, "col_offset", -1)) < read_pos and _write_hit(
            n, operand_tokens | arg_aliases | arg_roots, arg_aliases, arg_wfa, arg_wunb)
           for n in _immediate_subtree(protected_call)): return False
    for candidate in _iter_function_direct_calls(function_node):  # type: ignore[arg-type]
        if not _resolves_to_shared_validator(candidate, validator_state):
            continue
        if not _unconditionally_executed(candidate, parents):
            continue
        if any(n is protected_call or id(n) in connect_ids for n in ast.walk(candidate)): continue
        # a with rebind of this operand voids every validator in the statement
        if any(tokens & operand_tokens and id(candidate) in calls for tokens, calls in with_guards):
            continue
        validator_operand = _dsn_call_operand(candidate)
        if (validator_operand is None or _unparse(validator_operand) != operand_text or
                (candidate.lineno, candidate.col_offset) >= (protected_call.lineno, protected_call.col_offset)): continue
        guards_v, solid_v = _path_profile(candidate, function_node, parents)
        guards_c, solid_c = _path_profile(protected_call, function_node, parents)
        if not set(solid_v) <= set(solid_c):
            continue
        tokens = set(operand_tokens); unmatched = list(guards_c)
        for test_dump, guard_line, guard_id, test_names in guards_v:
            match = next((c for c in unmatched if c[0] == test_dump and (c[2] == guard_id or c[1] > guard_line)), None)
            if match is None:
                unmatched = None; break
            unmatched.remove(match)
            tokens.update(test_names)
        if unmatched is None:
            continue
        if _rebinding_between(
                function_node, tokens,
                (candidate.lineno, candidate.col_offset),
                (protected_call.lineno, protected_call.col_offset)):
            continue
        # a call in a loop needs that loop to never rebind the operand (r17)
        fn_aliases, fn_roots, fn_wfa, fn_wunb = _alias_tokens(function_node, operand_tokens)
        ancestor, uncovered = parents.get(id(protected_call)), False
        while ancestor is not None and ancestor is not function_node:
            scope = candidate
            while scope is not None and scope is not ancestor: scope = parents.get(id(scope))
            if isinstance(ancestor, (ast.For, ast.While, ast.AsyncFor)) and scope is not ancestor:
                if any(operand_tokens & (_bound_tokens(n) | {m for _, m in _capture_bindings(n)})
                       or _write_hit(n, operand_tokens | fn_aliases | fn_roots, fn_aliases, fn_wfa, fn_wunb)
                       for n in ast.walk(ancestor)):
                    uncovered = True; break
            ancestor = parents.get(id(ancestor))
        if uncovered: continue
        return True
    return False
def _boundary_validation_violations(path, tree):
    violations = []; parents = _parent_map(tree)
    validator_state = _shared_validator_bindings(tree); connect_ids = frozenset(
        id(c) for c in _psycopg_inventory(tree)[3]); with_guards = _with_target_call_guards(tree)
    if path.name == CLI_BOUNDARY_FILENAME:
        for call in _psycopg_inventory(tree)[3]:
            operand = _dsn_call_operand(call)
            function_node = _containing_function(call, parents)
            if (operand is None or function_node is None
                    or not _validated_on_path(
                        call, operand, function_node, parents, validator_state, connect_ids,
                        with_guards)):
                violations.append(StaticViolation(path, call.lineno, "cli connect before local dsn validation",
                    f"{getattr(function_node, 'name', '<lambda>')}:{_unparse(operand)}"))
        return tuple(violations)
    for spec in INTERMEDIARY_BOUNDARY_SPECS.get(path.name, ()):
        if spec[0] == "function":
            _, function_name, protected_name, operand_mode, kind = spec
            scoped = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and n.name == function_name]; name_prefix = function_name
        else:
            _, class_name, method_name, protected_name, operand_mode, kind = spec
            scoped = [method for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name
                      for method in n.body if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and method.name == method_name]; name_prefix = f"{class_name}.{method_name}"
        for function_node in scoped:
            for call in _iter_function_direct_calls(function_node):
                if _call_name(call.func) != protected_name:
                    continue
                operand = _dsn_call_operand(call, operand_mode)
                if operand is not None and not _validated_on_path(
                    call, operand, function_node, parents, validator_state, connect_ids, with_guards):
                    violations.append(StaticViolation(
                        path, call.lineno, kind, f"{name_prefix}:{_unparse(operand)}"))
    return tuple(violations)
def _environment_read_violations(path, tree, *, kind, dsn_keys_only):
    environ_names, getenv_names, os_names = {"environ"}, {"getenv"}, {"os"}
    def is_environ_base(base):
        if isinstance(base, ast.IfExp): return is_environ_base(base.body) or is_environ_base(base.orelse)
        return (isinstance(base, ast.Name) and base.id in environ_names) or (isinstance(base, ast.Attribute) and
                base.attr == "environ" and isinstance(base.value, ast.Name) and base.value.id in os_names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            os_names.update(a.asname or "os" for a in node.names if a.name == "os")
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            environ_names.update(a.asname or "environ" for a in node.names if a.name == "environ"); getenv_names.update(a.asname or "getenv" for a in node.names if a.name == "getenv")
        elif isinstance(node, ast.Assign) and is_environ_base(node.value):
            environ_names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    violations = []; key = None
    for node in ast.walk(tree):
        key = None
        if isinstance(node, ast.Call) and node.args and (
            (isinstance(node.func, ast.Name) and node.func.id in getenv_names)
            or (isinstance(node.func, ast.Attribute) and node.func.attr in {"get", "getenv"}
                and (is_environ_base(node.func.value) or (node.func.attr == "getenv"
                     and isinstance(node.func.value, ast.Name) and node.func.value.id in os_names)))):
            key = node.args[0]
        elif isinstance(node, ast.Subscript) and is_environ_base(node.value): key = node.slice
        if key is None:
            continue
        if dsn_keys_only and not DSN_ENV_KEY_RE.search(str(key.value) if isinstance(key, ast.Constant)
                else key.id if isinstance(key, ast.Name) else _unparse(key)): continue
        violations.append(StaticViolation(path, node.lineno, kind, _unparse(key)))
    return tuple(violations)

def _shared_validator_bindings(tree):
    """Return (imported names, module aliases, shadowed validator names)."""
    bindings, module_names, shadowed = set(), set(), set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): shadowed.add(node.name)
        elif isinstance(node, ast.arguments): shadowed.update(
            a.arg for a in ast.walk(node) if isinstance(a, ast.arg))
        elif isinstance(node, ast.ImportFrom) and node.module == SHARED_VALIDATOR_MODULE:
            bindings.update(a.asname or a.name for a in node.names if a.name == LOCAL_DSN_VALIDATOR); continue
        elif isinstance(node, ast.Import):  # shared-module imports bind, not shadow
            module_names.update(a.asname or a.name for a in node.names if a.name == SHARED_VALIDATOR_MODULE); \
            shadowed.update(a.asname or a.name.split(".", 1)[0] for a in node.names if a.name != SHARED_VALIDATOR_MODULE); \
            continue
        shadowed.update(_bound_tokens(node))
    return bindings, module_names, shadowed & (LOCAL_DSN_VALIDATOR_NAMES | bindings | module_names)

def _resolves_to_shared_validator(call, validator_state):
    """Callee resolves to the shared validator via an unshadowed import."""
    bindings, module_names, shadowed = validator_state; func = call.func
    return ((isinstance(func, ast.Name) and func.id in bindings and func.id not in shadowed)
            or (isinstance(func, ast.Attribute) and func.attr == LOCAL_DSN_VALIDATOR
                and isinstance(func.value, ast.Name) and func.value.id in module_names and func.value.id not in shadowed))

def _unconditionally_executed(node, parents):
    """False inside a short-circuited BoolOp operand or an IfExp."""
    current, parent = node, parents.get(id(node))
    while parent is not None:
        if (isinstance(parent, ast.BoolOp) and parent.values.index(current) != 0) or isinstance(
                parent, ast.IfExp): return False
        current, parent = parent, parents.get(id(parent))
    return True

def _is_self_dsn_not_none_guarded(node, post_init, parents):
    current = node
    while current is not None and current is not post_init:
        parent = parents.get(id(current))
        if (isinstance(parent, ast.If) and isinstance(current, ast.stmt)
                and isinstance(parent.test, ast.Compare)
                and any(
                    (isinstance(c, ast.Attribute) and _unparse(c) == "self.dsn")
                    or (isinstance(c, ast.Constant) and c.value is None)
                    for c in ast.walk(parent.test))
                and any(isinstance(o, (ast.IsNot, ast.NotEq)) for o in parent.test.ops)
                == (current in parent.body)):
            return True
        current = parent
    return False

def _config_module_validation_violations(path, tree):
    violations = []; validator_state = _shared_validator_bindings(tree)
    if not validator_state[0]: violations.append(StaticViolation(
        path, 1, "config missing shared dsn validator import", LOCAL_DSN_VALIDATOR))
    parents = _parent_map(tree); dsn_classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and any(
        isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.target.id == "dsn"
        for s in n.body)]
    if not dsn_classes:
        violations.append(StaticViolation(path, 1, "config missing __post_init__", path.name))
    for config_class in dsn_classes:
        post_inits = [
            m for m in config_class.body if isinstance(m, ast.FunctionDef) and m.name == "__post_init__"]
        if not post_inits:
            violations.append(StaticViolation(path, config_class.lineno, "config missing __post_init__", config_class.name))
            continue
        if not validator_state[0]:
            continue
        validated = any(
            _resolves_to_shared_validator(node, validator_state) and node.args
            and _unparse(node.args[0]) == "self.dsn"
            and _is_self_dsn_not_none_guarded(node, post_init, parents)
            for post_init in post_inits for node in _iter_function_direct_calls(post_init))
        if not validated:
            violations.append(StaticViolation(path, post_inits[0].lineno,
                "config __post_init__ missing guarded self.dsn validation", config_class.name))
    return tuple(violations)

def _connector_reference_violation(path, tree):
    if path.relative_to(REPO_ROOT).as_posix() in FROZEN_CONNECTOR_ALLOWLIST:
        return None
    module_aliases, connect_aliases, first_line, _calls = _psycopg_inventory(tree)
    if first_line is None:
        return None
    return StaticViolation(
        path, first_line, "connector outside frozen allowlist", sorted(module_aliases | connect_aliases)[0])

def _cli_dsn_option_violations(path, tree):
    violations = []; key = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_name(node.func) != "add_argument": continue
        tokens = [
            a.value for a in node.args
            if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        for keyword in node.keywords:
            if keyword.arg == "option_strings" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                tokens.extend(e.value for e in keyword.value.elts
                              if isinstance(e, ast.Constant) and isinstance(e.value, str))
            elif keyword.arg == "dest" and isinstance(keyword.value, ast.Constant):
                tokens.append(keyword.value.value)
        dsn_tokens = [t for t in tokens if "dsn" in str(t).lower()]
        if dsn_tokens:
            violations.append(StaticViolation(path, node.lineno, "cli dsn option", dsn_tokens[0]))
    return tuple(violations)

def _local_dsn_shim_violations(path, tree):
    violations = []; validator_state = _shared_validator_bindings(tree)
    for shim in ast.walk(tree):
        if not (isinstance(shim, ast.FunctionDef) and shim.name == LOCAL_DSN_VALIDATOR_SHIM): continue
        if not validator_state[0]:
            violations.append(StaticViolation(path, shim.lineno, "dsn shim without shared validator import", shim.name))
            continue
        parameter = shim.args.args[0].arg if shim.args.args else ""; body = shim.body
        delegated = (len(body) == 1 and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Call)
            and _resolves_to_shared_validator(body[0].value, validator_state) and body[0].value.args
            and isinstance(body[0].value.args[0], ast.Name) and body[0].value.args[0].id == parameter
            and any(kw.arg == "env_var_name" for kw in body[0].value.keywords))
        if not delegated:
            violations.append(StaticViolation(path, shim.lineno, "dsn shim not delegating to shared validator", shim.name))
    return tuple(violations)

def test_cli_and_intermediary_boundaries_validate_local_dsn_before_connection() -> None:
    violations: list[StaticViolation] = []; violation = None
    for relative_path in BOUNDARY_FILE_PATHS: violations.extend(_boundary_validation_violations(
        REPO_ROOT / relative_path, _parse_cached(relative_path)))
    assert violations == [], _format_violations(tuple(violations))

def test_repo_wide_pins_constrain_env_reads_configs_connectors_and_shims() -> None:
    env_violations, config_violations, connector_violations, shim_violations = [], [], [], []
    config_count = shim_count = 0
    for relative_path in _src_relative_paths():
        source_text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        if fnmatch(Path(relative_path).name, CONFIG_MODULE_PATTERN):
            config_count += 1; config_violations.extend(_config_module_validation_violations(
                REPO_ROOT / relative_path, _parse_cached(relative_path)))
        elif "environ" in source_text or "getenv" in source_text:
            env_violations.extend(_environment_read_violations(REPO_ROOT / relative_path, _parse_cached(relative_path),
                kind="dsn environment read outside config module", dsn_keys_only=True))
        if relative_path not in FROZEN_CONNECTOR_ALLOWLIST and "psycopg" in source_text:
            if (violation := _connector_reference_violation(REPO_ROOT / relative_path, _parse_cached(relative_path))):
                connector_violations.append(violation)
        if LOCAL_DSN_VALIDATOR_SHIM in source_text:
            tree = _parse_cached(relative_path); shims = [n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == LOCAL_DSN_VALIDATOR_SHIM]
            shim_count += len(shims); shim_violations.extend(_local_dsn_shim_violations(REPO_ROOT / relative_path, tree))
    assert config_count >= 56, "expected the discovered supabase config modules"; \
    assert env_violations == [], _format_violations(tuple(env_violations)); assert config_violations == [], _format_violations(tuple(config_violations)); \
    assert connector_violations == [], _format_violations(tuple(connector_violations)); assert shim_count >= 1, \
    "expected the existing _validate_local_dsn shim to remain"; assert shim_violations == [], _format_violations(tuple(shim_violations))

def test_cli_pins_connect_site_inventory_and_clean_option_surface() -> None:
    tree = _parse_cached(CLI_RELATIVE_PATH); assert len(sites := _psycopg_inventory(tree)[3]) == EXPECTED_CLI_CONNECT_SITE_COUNT; \
    operand_counts = Counter(_unparse(o) for o in (_dsn_call_operand(s) for s in sites) if o is not None)
    assert operand_counts == EXPECTED_CLI_CONNECT_OPERANDS; \
    assert _environment_read_violations(REPO_ROOT / CLI_RELATIVE_PATH, tree, kind="cli environment read", dsn_keys_only=False) == (); \
    assert _cli_dsn_option_violations(REPO_ROOT / CLI_RELATIVE_PATH, tree) == ()

def test_cli_boundary_and_pin_guards_catch_unguarded_and_mismatched_connects() -> None:
    fixture_tree = ast.parse("import argparse, os, psycopg\nimport psycopg as pg; from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\ndef build_parser(): parser = argparse.ArgumentParser(); parser.add_argument(\"--dsn\", dest=\"dsn\"); return parser\ndef missing_validation(dsn): primary = os.environ.get(\"POLYMARKET_ALPHA_LAB_FIXTURE_DB_DSN\"); return psycopg.connect(dsn)\ndef late_validation(dsn): psycopg.connect(dsn); validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\ndef wrong_operand(other_dsn, dsn): validate_local_postgres_dsn(other_dsn, env_var_name=\"EXAMPLE_DSN\"); return psycopg.connect(dsn)\ndef alternate_branch(dsn, use_backup):\n    if use_backup: validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(dsn)\ndef reassigned_operand(dsn, backup_dsn): validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"); dsn = backup_dsn; return psycopg.connect(dsn)\ndef nested_dsn_parameter(dsn):\n    def inner(dsn): return psycopg.connect(dsn)\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"); return inner(dsn)\ndef guarded_enabled_branch(dsn):\n    if dsn is not None: validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    if dsn is not None: return psycopg.connect(dsn)\ndef guarded_alias_connect(dsn): validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"); return pg.connect(dsn)\n")
    path = REPO_ROOT / "src" / "fixture_boundary" / "cli.py"; violations = _boundary_validation_violations(path, fixture_tree)
    assert [v.name for v in violations] == ["missing_validation:dsn", "late_validation:dsn", "wrong_operand:dsn", "alternate_branch:dsn", "reassigned_operand:dsn", "inner:dsn"]; assert {v.kind for v in violations} == {"cli connect before local dsn validation"}; assert [v.name for v in _environment_read_violations(path, fixture_tree, kind="cli environment read", dsn_keys_only=False)] == ["'POLYMARKET_ALPHA_LAB_FIXTURE_DB_DSN'"]
    assert [v.name for v in _cli_dsn_option_violations(path, fixture_tree)] == ["--dsn"]; assert len(_psycopg_inventory(fixture_tree)[3]) == 8
    forgery_tree = ast.parse("import psycopg\nfrom polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\ndef shadowed_validator(dsn, validate_local_postgres_dsn): validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"); return psycopg.connect(dsn)\ndef local_rebinding_validator(dsn):\n    def validate_local_postgres_dsn(value, env_var_name): return True\n    validate_local_postgres_dsn(dsn, \"EXAMPLE_DSN\"); return psycopg.connect(dsn)\ndef attribute_forgery(dsn, other): other.validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"); return psycopg.connect(dsn)\n")
    forgeries = _boundary_validation_violations(path, forgery_tree)
    assert [v.name for v in forgeries] == ["shadowed_validator:dsn", "local_rebinding_validator:dsn", "attribute_forgery:dsn"]; assert {v.kind for v in forgeries} == {"cli connect before local dsn validation"}
    short_circuit_tree = ast.parse(_CLI_FIXTURE_HEADER + 'def short_circuit_validation(dsn, flag): flag and validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN"); return psycopg.connect(dsn)\n'); assert [v.name for v in _boundary_validation_violations(path, short_circuit_tree)] == ["short_circuit_validation:dsn"]
    rebind_root_tree = ast.parse(_CLI_FIXTURE_HEADER + 'def rebinds_attribute_root(config, backup): validate_local_postgres_dsn(config.dsn, env_var_name="EXAMPLE_DSN"); config = backup; return psycopg.connect(config.dsn)\n'); assert [v.name for v in _boundary_validation_violations(path, rebind_root_tree)] == ["rebinds_attribute_root:config.dsn"]
    alias_shadow_tree = ast.parse("import psycopg\nimport polymarket_alpha_lab.supabase_local_dsn as s\nfrom polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn as v\n" + 'def alias_param_shadow(dsn, v): v(dsn, env_var_name="EXAMPLE_DSN"); return psycopg.connect(dsn)\n' + 'def module_alias_param_shadow(dsn, s): s.validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN"); return psycopg.connect(dsn)\n'); assert [v.name for v in _boundary_validation_violations(path, alias_shadow_tree)] == ["alias_param_shadow:dsn", "module_alias_param_shadow:dsn"]
    module_alias_positive = ast.parse(_CLI_FIXTURE_HEADER + "import polymarket_alpha_lab.supabase_local_dsn as s\n" + 'def guarded_module_alias(dsn): s.validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN"); return psycopg.connect(dsn)\n'); assert _boundary_validation_violations(path, module_alias_positive) == ()
    with_rebind_tree = ast.parse(_CLI_FIXTURE_HEADER + "import polymarket_alpha_lab.supabase_local_dsn as s\n" + "def with_rebind(dsn, ctx):\n    with ctx as s:\n" + '        s.validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN")\n    return psycopg.connect(dsn)\n'); assert [v.name for v in _boundary_validation_violations(path, with_rebind_tree)] == ["with_rebind:dsn"]
    async_with_rebind_tree = ast.parse(_CLI_FIXTURE_HEADER + "import polymarket_alpha_lab.supabase_local_dsn as s\n" + "async def with_async_rebind(dsn, ctx):\n    async with ctx as s:\n" + '        s.validate_local_postgres_dsn(dsn, env_var_name="EXAMPLE_DSN")\n    return psycopg.connect(dsn)\n'); assert [v.name for v in _boundary_validation_violations(path, async_with_rebind_tree)] == ["with_async_rebind:dsn"]
    with_head_rebind_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_head_rebind(dsn, ctx):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as dsn:\n        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_head_rebind_tree)] == ["with_head_rebind:dsn"]
    with_head_async_rebind_tree = ast.parse(_CLI_FIXTURE_HEADER + "async def with_head_async_rebind(dsn, ctx):\n    async with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as dsn:\n        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_head_async_rebind_tree)] == ["with_head_async_rebind:dsn"]
    with_head_tuple_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_head_tuple_rebind(dsn, ctx, box):\n    with ctx as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, dsn):\n" + "        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_head_tuple_tree)] == ["with_head_tuple_rebind:dsn"]
    with_head_starred_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_head_starred_rebind(dsn, ctx, box, others):\n    with ctx as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, *others, dsn):\n" + "        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_head_starred_tree)] == ["with_head_starred_rebind:dsn"]
    with_head_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_head_attr_rebind(box, ctx):\n    with ctx(validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")) as box.dsn:\n" + "        return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_head_attr_tree)] == ["with_head_attr_rebind:box.dsn"]
    with_head_async_tuple_tree = ast.parse(_CLI_FIXTURE_HEADER + "async def with_head_async_tuple_rebind(dsn, ctx, box):\n    async with ctx as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, dsn):\n" + "        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_head_async_tuple_tree)] == ["with_head_async_tuple_rebind:dsn"]
    with_target_connect_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_target_contains_connect(dsn, ctx, box):\n    with ctx as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, dsn, box(psycopg.connect(dsn)).slot):\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, with_target_connect_tree)] == ["with_target_contains_connect:dsn"]
    with_target_connect_starred_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_target_connect_starred(dsn, ctx, box, others):\n    with ctx as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, *others, dsn, box(psycopg.connect(dsn)).slot):\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, with_target_connect_starred_tree)] == ["with_target_connect_starred:dsn"]
    with_target_connect_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_target_connect_attr(box, ctx):\n    with ctx as (box(validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")).slot, box(psycopg.connect(box.dsn)).dsn):\n        return None\n"); assert [v.name for v in _boundary_validation_violations(path, with_target_connect_attr_tree)] == ["with_target_connect_attr:box.dsn"]
    with_target_connect_async_tree = ast.parse(_CLI_FIXTURE_HEADER + "async def with_target_connect_async(dsn, ctx, box):\n    async with ctx as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, dsn, box(psycopg.connect(dsn)).slot):\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, with_target_connect_async_tree)] == ["with_target_connect_async:dsn"]
    head_validate_target_connect_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_head_validate_target_connect(dsn, ctx, box):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as (dsn, box(psycopg.connect(dsn)).slot):\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, head_validate_target_connect_tree)] == ["with_head_validate_target_connect:dsn"]
    head_validate_target_starred_tree = ast.parse(_CLI_FIXTURE_HEADER + "def head_validate_target_starred(dsn, ctx, box, others):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as (*others, dsn, box(psycopg.connect(dsn)).slot):\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, head_validate_target_starred_tree)] == ["head_validate_target_starred:dsn"]
    head_validate_target_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def head_validate_target_attr(box, ctx):\n    with ctx(validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")) as box(psycopg.connect(box.dsn)).dsn:\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, head_validate_target_attr_tree)] == ["head_validate_target_attr:box.dsn"]
    head_validate_target_async_tree = ast.parse(_CLI_FIXTURE_HEADER + "async def head_validate_target_async(dsn, ctx, box):\n    async with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as (dsn, box(psycopg.connect(dsn)).slot):\n" + "        return None\n"); assert [v.name for v in _boundary_validation_violations(path, head_validate_target_async_tree)] == ["head_validate_target_async:dsn"]
    head_validate_other_target_tree = ast.parse(_CLI_FIXTURE_HEADER + "def head_validate_other_target(dsn, ctx, x):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as box(x).slot:\n" + "        return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, head_validate_other_target_tree) == (); assert _boundary_validation_violations(path, ast.parse(_CLI_FIXTURE_HEADER + "def head_no_as(dsn, ctx):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")):        return psycopg.connect(dsn)\n")) == ()
    with_no_rebind_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_no_rebind(dsn, ctx):\n    with ctx:\n        validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\");        return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, with_no_rebind_tree) == ()
    namedexpr_head_tree = ast.parse(_CLI_FIXTURE_HEADER + "def namedexpr_head_rebind(dsn, ctx, remote_dsn, box):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), (dsn := remote_dsn)) as box(psycopg.connect(dsn)).slot:\n        return None\n"); assert [v.name for v in _boundary_validation_violations(path, namedexpr_head_tree)] == ["namedexpr_head_rebind:dsn"]
    namedexpr_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def namedexpr_body_connect(dsn, ctx, remote_dsn):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), (dsn := remote_dsn)):\n        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, namedexpr_body_tree)] == ["namedexpr_body_connect:dsn"]
    namedexpr_head_connect_tree = ast.parse(_CLI_FIXTURE_HEADER + "def namedexpr_head_connect(dsn, ctx, remote_dsn):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), psycopg.connect(dsn), (dsn := remote_dsn)):\n        return None\n"); assert [v.name for v in _boundary_validation_violations(path, namedexpr_head_connect_tree)] == ["namedexpr_head_connect:dsn"]
    namedexpr_async_tree = ast.parse(_CLI_FIXTURE_HEADER + "async def namedexpr_async_rebind(dsn, ctx, remote_dsn, box):\n    async with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), (dsn := remote_dsn)) as box(psycopg.connect(dsn)).slot:\n        return None\n"); assert [v.name for v in _boundary_validation_violations(path, namedexpr_async_tree)] == ["namedexpr_async_rebind:dsn"]
    namedexpr_target_validate_tree = ast.parse(_CLI_FIXTURE_HEADER + "def namedexpr_target_validate(dsn, ctx, remote_dsn, box, other):\n    with ctx((dsn := remote_dsn)) as (box(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")).slot, other):\n        return psycopg.connect(dsn)\n")
    assert [v.name for v in _boundary_validation_violations(path, namedexpr_target_validate_tree)] == ["namedexpr_target_validate:dsn"]
    namedexpr_token_miss_tree = ast.parse(_CLI_FIXTURE_HEADER + "def namedexpr_token_miss(dsn, ctx, remote):\n    with ctx(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), (other := remote)) as conn:\n        return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, namedexpr_token_miss_tree) == ()
    arg_walrus_tree = ast.parse(_CLI_FIXTURE_HEADER + "def keyword_walrus_early_read_late(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(dsn := replacement), conninfo=dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, arg_walrus_tree)] == ["keyword_walrus_early_read_late:dsn"]
    arg_walrus_with_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_walrus_with(dsn, ctx, replacement):\n    with ctx:\n        validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n        return psycopg.connect(autocommit=bool(dsn := replacement), conninfo=dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, arg_walrus_with_tree)] == ["arg_walrus_with:dsn"]
    arg_walrus_async_tree = ast.parse(_CLI_FIXTURE_HEADER + "async def arg_walrus_async(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(dsn := replacement), conninfo=dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, arg_walrus_async_tree)] == ["arg_walrus_async:dsn"]
    arg_walrus_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_walrus_attr(box, other):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(box := other), conninfo=box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, arg_walrus_attr_tree)] == ["arg_walrus_attr:box.dsn"]
    arg_walrus_token_miss_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_walrus_token_miss(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(other := replacement), conninfo=dsn)\n"); assert _boundary_validation_violations(path, arg_walrus_token_miss_tree) == ()
    lambda_default_tree = ast.parse(_CLI_FIXTURE_HEADER + "def lambda_default_rebind(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    unused = lambda captured=(dsn := replacement): None\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, lambda_default_tree)] == ["lambda_default_rebind:dsn"]
    func_default_tree = ast.parse(_CLI_FIXTURE_HEADER + "def func_default_rebind(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    def helper(captured=(dsn := replacement)): return None\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, func_default_tree)] == ["func_default_rebind:dsn"]
    subscript_root_tree = ast.parse(_CLI_FIXTURE_HEADER + "def subscript_root_rebind(dsns, replacement):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(dsns := replacement), conninfo=dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, subscript_root_tree)] == ["subscript_root_rebind:dsns[0]"]
    indexed_tree = ast.parse(_CLI_FIXTURE_HEADER + "def indexed_rebind(dsns, index, replacement):\n    validate_local_postgres_dsn(dsns[index], env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(dsns := replacement), conninfo=dsns[index])\n"); assert [v.name for v in _boundary_validation_violations(path, indexed_tree)] == ["indexed_rebind:dsns[index]"]
    attr_subscript_tree = ast.parse(_CLI_FIXTURE_HEADER + "def attr_subscript_rebind(boxes, replacement):\n    validate_local_postgres_dsn(boxes[0].dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(boxes := replacement), conninfo=boxes[0].dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, attr_subscript_tree)] == ["attr_subscript_rebind:boxes[0].dsn"]
    unrelated_default_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_default(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    unused = lambda captured=(other := replacement): None\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_default_tree) == ()
    plain_subscript_tree = ast.parse(_CLI_FIXTURE_HEADER + "def plain_subscript(dsns):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(dsns[0])\n"); assert _boundary_validation_violations(path, plain_subscript_tree) == ()
    class_base_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_base_walrus(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    class H((dsn := replacement) and object): pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_base_tree)] == ["class_base_walrus:dsn"]
    decorator_walrus_tree = ast.parse(_CLI_FIXTURE_HEADER + "def decorator_walrus(dsn, replacement, ident):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    @((dsn := replacement) and ident)\n    def helper(): return None\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, decorator_walrus_tree)] == ["decorator_walrus:dsn"]
    class_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_nonlocal(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    class C:\n        nonlocal dsn\n        dsn = replacement\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_body_tree)] == ["class_body_nonlocal:dsn"]
    subscript_assign_tree = ast.parse(_CLI_FIXTURE_HEADER + "def subscript_assign(dsns, replacement):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    dsns[0] = replacement\n    return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, subscript_assign_tree)] == ["subscript_assign:dsns[0]"]
    with_as_subscript_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_as_subscript(dsns, ctx):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    with ctx as dsns[0]:\n        return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, with_as_subscript_tree)] == ["with_as_subscript:dsns[0]"]
    ancestor_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def ancestor_attr_assign(boxes, replacement):\n    validate_local_postgres_dsn(boxes[0].config.dsn, env_var_name=\"EXAMPLE_DSN\")\n    boxes[0].config.dsn = replacement\n    return psycopg.connect(boxes[0].config.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, ancestor_attr_tree)] == ["ancestor_attr_assign:boxes[0].config.dsn"]
    unrelated_class_base_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_class_base(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    class H((other := replacement) and object): pass\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_class_base_tree) == ()
    class_if_subscript_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_if_subscript_assign(dsns, replacement):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    class C:\n        if True: dsns[0] = replacement\n    return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, class_if_subscript_tree)] == ["class_body_if_subscript_assign:dsns[0]"]
    class_if_nonlocal_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_if_nonlocal(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    class C:\n        if True:\n            nonlocal dsn\n            dsn = replacement\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_if_nonlocal_tree)] == ["class_body_if_nonlocal:dsn"]
    class_nested_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_nested_class_write(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    class C:\n        class D:\n            dsn = replacement\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_nested_write_tree)] == ["class_body_nested_class_write:dsn"]
    class_if_dict_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_if_dict_dunder(self, replacement):\n    validate_local_postgres_dsn(self._dsn, env_var_name=\"EXAMPLE_DSN\")\n    class C:\n        if True: self.__dict__[\"_dsn\"] = replacement\n    return psycopg.connect(self._dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_if_dict_tree)] == ["class_body_if_dict_dunder:self._dsn"]
    subscript_delete_tree = ast.parse(_CLI_FIXTURE_HEADER + "def subscript_delete(dsns, replacement):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    del dsns[0]\n    return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, subscript_delete_tree)] == ["subscript_delete:dsns[0]"]
    slice_delete_tree = ast.parse(_CLI_FIXTURE_HEADER + "def slice_delete(dsns):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    del dsns[:]\n    return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, slice_delete_tree)] == ["slice_delete:dsns[0]"]
    with_body_delete_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_body_delete(dsns, ctx):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    with ctx:\n        del dsns[0]\n    return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, with_body_delete_tree)] == ["with_body_delete:dsns[0]"]
    unrelated_delete_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_delete(dsns, others):\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    del others[0]\n    return psycopg.connect(dsns[0])\n"); assert _boundary_validation_violations(path, unrelated_delete_tree) == ()
    except_as_tree = ast.parse(_CLI_FIXTURE_HEADER + "def except_as_rebind(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class C:\n        try: pass\n        except Exception as box: pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, except_as_tree)] == ["except_as_rebind:box.dsn"]
    match_case_tree = ast.parse(_CLI_FIXTURE_HEADER + "def match_case_rebind(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    match replacement:\n        case dsn: pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, match_case_tree)] == ["match_case_rebind:dsn"]
    decorated_def_tree = ast.parse(_CLI_FIXTURE_HEADER + "def decorated_def_rebind(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    @(lambda _: replacement)\n    def dsn(): pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, decorated_def_tree)] == ["decorated_def_rebind:dsn"]
    class_self_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_self_rebind(dsn):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    class dsn: pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_self_tree)] == ["class_self_rebind:dsn"]
    func_except_tree = ast.parse(_CLI_FIXTURE_HEADER + "def func_body_except_rebind(box):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    try: pass\n    except Exception as box: pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, func_except_tree)] == ["func_body_except_rebind:box.dsn"]
    unrelated_capture_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_capture(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    try: pass\n    except Exception as other: pass\n    match replacement:\n        case other2: pass\n    def other3(): pass\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, unrelated_capture_tree) == ()
    match_head_validate_tree = ast.parse(_CLI_FIXTURE_HEADER + "def match_head_validate_case_rebind(dsn, replacement):\n    match (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]:\n        case dsn: pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, match_head_validate_tree)] == ["match_head_validate_case_rebind:dsn"]
    except_head_validate_tree = ast.parse(_CLI_FIXTURE_HEADER + "def except_head_validate_rebind(dsn, replacement):\n    try: pass\n    except (lambda: Exception)(validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")) as dsn: pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, except_head_validate_tree)] == ["except_head_validate_rebind:dsn"]
    match_star_head_tree = ast.parse(_CLI_FIXTURE_HEADER + "def match_star_head_rebind(dsn, replacement):\n    match (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]:\n        case [*dsn]: pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, match_star_head_tree)] == ["match_star_head_rebind:dsn"]
    mapping_rest_head_tree = ast.parse(_CLI_FIXTURE_HEADER + "def mapping_rest_head_rebind(dsn, replacement):\n    match (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]:\n        case {**dsn}: pass\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, mapping_rest_head_tree)] == ["mapping_rest_head_rebind:dsn"]
    pre_validated_capture_tree = ast.parse(_CLI_FIXTURE_HEADER + "def pre_validated_capture(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    try: pass\n    except Exception as other: pass\n    match (replacement, replacement)[1]:\n        case other2: pass\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, pre_validated_capture_tree) == ()
    except_type_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def except_type_validate_body_call(dsn, replacement):\n    try: pass\n    except (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), Exception)[1] as dsn:\n        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, except_type_body_tree)] == ["except_type_validate_body_call:dsn"]
    except_capture_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def except_capture_body_connect(box):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    try: pass\n    except Exception as box:\n        return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, except_capture_body_tree)] == ["except_capture_body_connect:box.dsn"]
    assign_rhs_tree = ast.parse(_CLI_FIXTURE_HEADER + "def assign_rhs_validate_rebind(dsn, replacement):\n    dsn = (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, assign_rhs_tree)] == ["assign_rhs_validate_rebind:dsn"]
    for_iter_tree = ast.parse(_CLI_FIXTURE_HEADER + "def for_iter_validate_rebind(dsn, replacement):\n    for dsn in (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]:\n        return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, for_iter_tree)] == ["for_iter_validate_rebind:dsn"]
    tuple_unpack_tree = ast.parse(_CLI_FIXTURE_HEADER + "def tuple_unpack_validate_rebind(dsn, other, replacement):\n    dsn, other = (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, tuple_unpack_tree)] == ["tuple_unpack_validate_rebind:dsn"]
    unrelated_bind_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_bind(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    other = replacement\n    (other := (replacement, replacement)[1])\n    for other in (replacement, replacement)[1]: pass\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_bind_tree) == ()
    namedexpr_rhs_tree = ast.parse(_CLI_FIXTURE_HEADER + "def namedexpr_rhs_validate_rebind(dsn, replacement):\n    (dsn := (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1])\n    return psycopg.connect(dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, namedexpr_rhs_tree)] == ["namedexpr_rhs_validate_rebind:dsn"]
    loop_iteration_tree = ast.parse(_CLI_FIXTURE_HEADER + "def loop_iteration_rebind(dsn, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2):\n        connection = psycopg.connect(dsn)\n        (dsn := replacement)\n"); assert [v.name for v in _boundary_validation_violations(path, loop_iteration_tree)] == ["loop_iteration_rebind:dsn"]
    setattr_between_tree = ast.parse(_CLI_FIXTURE_HEADER + "def setattr_between(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    setattr(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, setattr_between_tree)] == ["setattr_between:box.dsn"]
    alias_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_attr_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias = box\n    alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_attr_tree)] == ["alias_attr_write:box.dsn"]
    benign_loop_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def benign_loop_and_unrelated_writes(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2): psycopg.connect(dsn)\n    setattr(other, \"x\", replacement)\n    alias2 = other\n    alias2.x = 1\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, benign_loop_attr_tree) == ()
    alias_chain_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_chain_two_hop(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias = box\n    alias2 = alias\n    alias2.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_chain_tree)] == ["alias_chain_two_hop:box.dsn"]
    alias_annassign_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_annassign(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias: object = box\n    alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_annassign_tree)] == ["alias_annassign:box.dsn"]
    alias_walrus_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_walrus(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (alias := box)\n    alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_walrus_tree)] == ["alias_walrus:box.dsn"]
    alias_unpack_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_unpack(box, extra, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (alias, other) = (box, extra)\n    alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_unpack_tree)] == ["alias_unpack:box.dsn"]
    alias_for_with_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_for_with(box, ctx, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for alias in [box]: alias.dsn = replacement\n    with box as alias_w: alias_w.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_for_with_tree)] == ["alias_for_with:box.dsn"]
    unrelated_chain_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_chain(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    a = other\n    b = a\n    b.f = replacement\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_chain_tree) == ()
    comp_for_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def comp_for_alias_attr(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    _ = [a for a in [box]]\n    a.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, comp_for_alias_tree)] == ["comp_for_alias_attr:box.dsn"]
    comp_nested_tree = ast.parse(_CLI_FIXTURE_HEADER + "def comp_nested_two_hop(box, other, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    _ = [b for row in [other] for b in [box]]\n    b.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, comp_nested_tree)] == ["comp_nested_two_hop:box.dsn"]
    gen_for_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def gen_for_alias(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    gen = (a for a in [box])\n    for a in gen: a.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, gen_for_alias_tree)] == ["gen_for_alias:box.dsn"]
    match_as_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def match_as_alias_attr(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    match box:\n        case alias:\n            alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, match_as_alias_tree)] == ["match_as_alias_attr:box.dsn"]
    match_as_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def match_as_alias_setattr(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    match box:\n        case alias:\n            setattr(alias, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, match_as_setattr_tree)] == ["match_as_alias_setattr:box.dsn"]
    unrelated_comp_match_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_comp_and_match(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    _ = [a for a in [other]]\n    a.f = replacement\n    match other:\n        case o2:\n            o2.g = replacement\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_comp_match_tree) == ()
    dunder_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def dunder_setattr_comp(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    [a.__setattr__(\"dsn\", replacement) for a in [box]]\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, dunder_setattr_tree)] == ["dunder_setattr_comp:box.dsn"]
    dunder_setitem_tree = ast.parse(_CLI_FIXTURE_HEADER + "def dunder_setitem_comp(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    [a.__dict__.__setitem__(\"dsn\", replacement) for a in [box]]\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, dunder_setitem_tree)] == ["dunder_setitem_comp:box.dsn"]
    pre_validated_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def pre_validation_alias_write(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, pre_validated_alias_tree)] == ["pre_validation_alias_write:box.dsn"]
    alias_unpack_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_unpack_write(box, spare, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias = box\n    alias.dsn, spare = replacement, None\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_unpack_write_tree)] == ["alias_unpack_write:box.dsn"]
    for_target_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def for_target_attr_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias = box\n    for alias.dsn in [replacement]: pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, for_target_attr_tree)] == ["for_target_attr_write:box.dsn"]
    loop_indirect_tree = ast.parse(_CLI_FIXTURE_HEADER + "def loop_indirect_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2):\n        connection = psycopg.connect(box.dsn)\n        match box:\n            case alias: alias.dsn = replacement\n"); assert [v.name for v in _boundary_validation_violations(path, loop_indirect_tree)] == ["loop_indirect_write:box.dsn"]
    loop_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def loop_setattr_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2):\n        connection = psycopg.connect(box.dsn)\n        setattr(box, \"dsn\", replacement)\n"); assert [v.name for v in _boundary_validation_violations(path, loop_setattr_tree)] == ["loop_setattr_write:box.dsn"]
    unrelated_dunder_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_dunder_and_alias_writes(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    other.__setattr__(\"f\", replacement)\n    a = other\n    a.g = replacement\n    setattr(other, \"h\", replacement)\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_dunder_tree) == ()
    loop_external_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def loop_external_alias_write(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2):\n        connection = psycopg.connect(box.dsn)\n        alias.dsn = replacement\n"); assert [v.name for v in _boundary_validation_violations(path, loop_external_alias_tree)] == ["loop_external_alias_write:box.dsn"]
    loop_external_dunder_tree = ast.parse(_CLI_FIXTURE_HEADER + "def loop_external_alias_dunder(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2):\n        connection = psycopg.connect(box.dsn)\n        alias.__setattr__(\"dsn\", replacement)\n"); assert [v.name for v in _boundary_validation_violations(path, loop_external_dunder_tree)] == ["loop_external_alias_dunder:box.dsn"]
    assign_rhs_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def assign_rhs_validate_write(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias.dsn = (validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, assign_rhs_write_tree)] == ["assign_rhs_validate_write:box.dsn"]
    unpack_rhs_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unpack_rhs_validate_write(box, spare, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    alias.dsn, spare = (validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unpack_rhs_write_tree)] == ["unpack_rhs_validate_write:box.dsn"]
    setattr_arg_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def setattr_arg_validate_write(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    setattr(alias, \"dsn\", (validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[0])\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, setattr_arg_write_tree)] == ["setattr_arg_validate_write:box.dsn"]
    comp_target_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def comp_target_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    _ = [None for box.dsn in [replacement]]\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, comp_target_write_tree)] == ["comp_target_write:box.dsn"]
    with_target_attr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_target_attr_write(box, ctx, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    with ctx(replacement) as box.dsn: pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_target_attr_tree)] == ["with_target_attr_write:box.dsn"]
    object_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def object_setattr_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    object.__setattr__(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, object_setattr_tree)] == ["object_setattr_write:box.dsn"]
    dict_update_tree = ast.parse(_CLI_FIXTURE_HEADER + "def dict_update_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    box.__dict__.update(dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, dict_update_tree)] == ["dict_update_write:box.dsn"]
    unrelated_inplace_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_inplace_writes(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    object.__setattr__(other, \"f\", replacement)\n    other.__dict__.update(g=replacement)\n    _ = [None for other.f in [replacement]]\n    with_ctx = None\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_inplace_tree) == ()
    with_target_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def with_target_body_connect(box, ctx, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    with ctx(replacement) as alias.dsn:\n        return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, with_target_body_tree)] == ["with_target_body_connect:box.dsn"]
    async_with_target_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def async_with_target_body_connect(dsns, ctx, replacement):\n    alias = dsns\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    async with ctx(replacement) as alias[0]:\n        return psycopg.connect(dsns[0])\n"); assert [v.name for v in _boundary_validation_violations(path, async_with_target_body_tree)] == ["async_with_target_body_connect:dsns[0]"]
    for_target_body_tree = ast.parse(_CLI_FIXTURE_HEADER + "def for_target_body_connect(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for alias.dsn in [replacement]:\n        return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, for_target_body_tree)] == ["for_target_body_connect:box.dsn"]
    alias_reverse_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_reverse_write(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(alias.dsn, env_var_name=\"EXAMPLE_DSN\")\n    box.dsn = replacement\n    return psycopg.connect(alias.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_reverse_tree)] == ["alias_reverse_write:alias.dsn"]
    alias_reverse_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def alias_reverse_setattr(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(alias.dsn, env_var_name=\"EXAMPLE_DSN\")\n    setattr(box, \"dsn\", replacement)\n    return psycopg.connect(alias.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, alias_reverse_setattr_tree)] == ["alias_reverse_setattr:alias.dsn"]
    unbound_update_kw_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unbound_dict_update_first_arg(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    dict.update(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unbound_update_kw_tree)] == ["unbound_dict_update_first_arg:box.dsn"]
    unbound_update_pos_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unbound_dict_update_positional(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    dict.update(box.__dict__, {\"dsn\": replacement})\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unbound_update_pos_tree)] == ["unbound_dict_update_positional:box.dsn"]
    unrelated_alias_rhs_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_alias_rhs_validate(dsn, other, extra, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    unrelated = (validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\"), extra)[1]\n    other.f = replacement\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_alias_rhs_tree) == ()
    multi_with_order_tree = ast.parse(_CLI_FIXTURE_HEADER + "def multi_with_bind_order(box, ctx, replacement):\n    alias = box\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    with ctx(replacement) as alias.dsn, ctx(psycopg.connect(box.dsn)) as spare:\n        return None\n"); assert [v.name for v in _boundary_validation_violations(path, multi_with_order_tree)] == ["multi_with_bind_order:box.dsn"]
    async_multi_with_tree = ast.parse(_CLI_FIXTURE_HEADER + "def async_multi_with_bind_order(dsns, ctx, replacement):\n    alias = dsns\n    validate_local_postgres_dsn(dsns[0], env_var_name=\"EXAMPLE_DSN\")\n    async with ctx(replacement) as alias[0], ctx(psycopg.connect(dsns[0])) as spare:\n        return None\n"); assert [v.name for v in _boundary_validation_violations(path, async_multi_with_tree)] == ["async_multi_with_bind_order:dsns[0]"]
    sibling_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def sibling_alias_write(box, replacement):\n    alias = box\n    sibling = box\n    validate_local_postgres_dsn(alias.dsn, env_var_name=\"EXAMPLE_DSN\")\n    sibling.dsn = replacement\n    return psycopg.connect(alias.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, sibling_alias_tree)] == ["sibling_alias_write:alias.dsn"]
    sibling_alias_dunder_tree = ast.parse(_CLI_FIXTURE_HEADER + "def sibling_alias_dunder(box, replacement):\n    alias = box\n    sibling = box\n    validate_local_postgres_dsn(alias.dsn, env_var_name=\"EXAMPLE_DSN\")\n    sibling.__setattr__(\"dsn\", replacement)\n    return psycopg.connect(alias.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, sibling_alias_dunder_tree)] == ["sibling_alias_dunder:alias.dsn"]
    call_result_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def call_result_alias_write(box, replacement):\n    alias = (validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\"), box)[1]\n    alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, call_result_alias_tree)] == ["call_result_alias_write:box.dsn"]
    call_result_for_tree = ast.parse(_CLI_FIXTURE_HEADER + "def call_result_for_alias(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for alias in (replacement, [box])[1]: alias.dsn = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, call_result_for_tree)] == ["call_result_for_alias:box.dsn"]
    unrelated_update_value_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unrelated_dict_update_value(dsn, other, replacement):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    other.__dict__.update({\"dsn\": dsn})\n    return psycopg.connect(dsn)\n"); assert _boundary_validation_violations(path, unrelated_update_value_tree) == ()
    guard_arg_tree = ast.parse(_CLI_FIXTURE_HEADER + 'def connect_inside_guard_argument(dsn): validate_local_postgres_dsn(dsn, env_var_name=str(psycopg.connect(dsn)))\n'); assert [v.name for v in _boundary_validation_violations(path, guard_arg_tree)] == ["connect_inside_guard_argument:dsn"]
    arg_inplace_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_inplace_setattr(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(setattr(box, \"dsn\", replacement)), conninfo=box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, arg_inplace_setattr_tree)] == ["arg_inplace_setattr:box.dsn"]
    arg_dict_update_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_dict_update(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(box.__dict__.update(dsn=replacement)), conninfo=box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, arg_dict_update_tree)] == ["arg_dict_update:box.dsn"]
    method_alias_call_tree = ast.parse(_CLI_FIXTURE_HEADER + "def method_alias_call(box, replacement):\n    update = box.__dict__.update\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    update(dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, method_alias_call_tree)] == ["method_alias_call:box.dsn"]
    type_alias_update_tree = ast.parse(_CLI_FIXTURE_HEADER + "def type_alias_update(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    mapping_type = dict\n    mapping_type.update(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, type_alias_update_tree)] == ["type_alias_update:box.dsn"]
    class_body_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_setattr(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner: setattr(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_body_setattr_tree)] == ["class_body_setattr:box.dsn"]
    class_body_alias_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_alias_write(box, replacement):\n    alias = box\n    validate_local_postgres_dsn(alias.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner: alias.dsn = replacement\n    return psycopg.connect(alias.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_body_alias_write_tree)] == ["class_body_alias_write:alias.dsn"]
    validator_arg_only_roots_tree = ast.parse(_CLI_FIXTURE_HEADER + "def validator_arg_only_roots(box, other, replacement):\n    alias = (validate_local_postgres_dsn(other.dsn, env_var_name=\"EXAMPLE_DSN\"), box)[1]\n    validate_local_postgres_dsn(alias.dsn, env_var_name=\"EXAMPLE_DSN\")\n    other.dsn = replacement\n    return psycopg.connect(alias.dsn)\n"); assert _boundary_validation_violations(path, validator_arg_only_roots_tree) == ()
    def_default_setattr_tree = ast.parse(_CLI_FIXTURE_HEADER + "def def_default_setattr(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    def inner(x=setattr(box, \"dsn\", replacement)): pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, def_default_setattr_tree)] == ["def_default_setattr:box.dsn"]
    lambda_default_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def lambda_default_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    f = lambda x=setattr(box, \"dsn\", replacement): x\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, lambda_default_write_tree)] == ["lambda_default_write:box.dsn"]
    class_base_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_base_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner(setattr(box, \"dsn\", replacement)): pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_base_write_tree)] == ["class_base_write:box.dsn"]
    unbound_update_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unbound_update_alias(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u = dict.update\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unbound_update_alias_tree)] == ["unbound_update_alias:box.dsn"]
    setattr_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def setattr_alias(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    s = setattr\n    s(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, setattr_alias_tree)] == ["setattr_alias:box.dsn"]
    unpack_type_update_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unpack_type_update(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    T, = (dict,)\n    T.update(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unpack_type_update_tree)] == ["unpack_type_update:box.dsn"]
    readonly_method_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def readonly_method_alias(box, other):\n    read = box.__dict__.get\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    value = read(\"dsn\")\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, readonly_method_alias_tree) == ()
    arg_order_read_before_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_order_read_before_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(box.dsn, autocommit=bool(setattr(box, \"dsn\", replacement)))\n"); assert _boundary_validation_violations(path, arg_order_read_before_write_tree) == ()
    class_body_def_default_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_def_default_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner:\n        def m(x=setattr(box, \"dsn\", replacement)): pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_body_def_default_write_tree)] == ["class_body_def_default_write:box.dsn"]
    nested_class_base_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def nested_class_base_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Outer:\n        class Inner(setattr(box, \"dsn\", replacement)): pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, nested_class_base_write_tree)] == ["nested_class_base_write:box.dsn"]
    unpack_wfa_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unpack_wfa_alias(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u, = (dict.update,)\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unpack_wfa_alias_tree)] == ["unpack_wfa_alias:box.dsn"]
    unpack_setattr_list_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unpack_setattr_list(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    s, = [setattr]\n    s(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unpack_setattr_list_tree)] == ["unpack_setattr_list:box.dsn"]
    chained_unpack_wfa_tree = ast.parse(_CLI_FIXTURE_HEADER + "def chained_unpack_wfa(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u, = (dict.update,)\n    v, = (u,)\n    v(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, chained_unpack_wfa_tree)] == ["chained_unpack_wfa:box.dsn"]
    unbound_pop_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unbound_pop_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    dict.pop(box.__dict__, \"dsn\")\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unbound_pop_write_tree)] == ["unbound_pop_write:box.dsn"]
    unbound_setdefault_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def unbound_setdefault_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    dict.setdefault(box.__dict__, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, unbound_setdefault_write_tree)] == ["unbound_setdefault_write:box.dsn"]
    readonly_chain_fp_tree = ast.parse(_CLI_FIXTURE_HEADER + "def readonly_chain_fp(box, other):\n    read = box.__dict__.get\n    read2 = read\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    value = read2(\"dsn\")\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, readonly_chain_fp_tree) == ()
    lambda_body_not_executed_fp_tree = ast.parse(_CLI_FIXTURE_HEADER + "def lambda_body_not_executed_fp(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    def inner(x=lambda: setattr(box, \"dsn\", replacement)): pass\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, lambda_body_not_executed_fp_tree) == ()
    nested_lambda_default_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def nested_lambda_default_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner: f = lambda y=setattr(box, \"dsn\", replacement): None\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, nested_lambda_default_write_tree)] == ["nested_lambda_default_write:box.dsn"]
    container_nested_lambda_default_tree = ast.parse(_CLI_FIXTURE_HEADER + "def container_nested_lambda_default(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner: f = [lambda y=setattr(box, \"dsn\", replacement): None]\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, container_nested_lambda_default_tree)] == ["container_nested_lambda_default:box.dsn"]
    class_except_method_default_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_except_method_default(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner:\n        try: pass\n        except Exception:\n            def m(x=setattr(box, \"dsn\", replacement)): pass\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_except_method_default_tree)] == ["class_except_method_default:box.dsn"]
    nested_unpack_wfa_tree = ast.parse(_CLI_FIXTURE_HEADER + "def nested_unpack_wfa(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    ((u,),) = ((dict.update,),)\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, nested_unpack_wfa_tree)] == ["nested_unpack_wfa:box.dsn"]
    ifexp_wfa_tree = ast.parse(_CLI_FIXTURE_HEADER + "def ifexp_wfa(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u = dict.update if True else dict.update\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, ifexp_wfa_tree)] == ["ifexp_wfa:box.dsn"]
    dunder_ior_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def dunder_ior_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    dict.__ior__(box.__dict__, {\"dsn\": replacement})\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, dunder_ior_write_tree)] == ["dunder_ior_write:box.dsn"]
    bound_method_first_arg_fp_tree = ast.parse(_CLI_FIXTURE_HEADER + "def bound_method_first_arg_fp(box, other, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u = other.__dict__.update\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, bound_method_first_arg_fp_tree) == ()
    arg_lambda_body_fp_tree = ast.parse(_CLI_FIXTURE_HEADER + "def arg_lambda_body_fp(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool(lambda: setattr(box, \"dsn\", replacement)), conninfo=box.dsn)\n"); assert _boundary_validation_violations(path, arg_lambda_body_fp_tree) == ()
    mixed_unpack_wfa_tree = ast.parse(_CLI_FIXTURE_HEADER + "def mixed_unpack_wfa(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u, n = (dict.update, 1)\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, mixed_unpack_wfa_tree)] == ["mixed_unpack_wfa:box.dsn"]
    starred_unpack_wfa_tree = ast.parse(_CLI_FIXTURE_HEADER + "def starred_unpack_wfa(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    *_, u = (None, dict.update)\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, starred_unpack_wfa_tree)] == ["starred_unpack_wfa:box.dsn"]
    class_body_subscript_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def class_body_subscript_write(box, replacement):\n    alias = box.__dict__\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner: alias[\"dsn\"] = replacement\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, class_body_subscript_write_tree)] == ["class_body_subscript_write:box.dsn"]
    except_nested_class_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def except_nested_class_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    class Inner:\n        try: pass\n        except Exception:\n            class Nested: marker = setattr(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, except_nested_class_write_tree)] == ["except_nested_class_write:box.dsn"]
    iife_lambda_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def iife_lambda_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (lambda: setattr(box, \"dsn\", replacement))()\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, iife_lambda_write_tree)] == ["iife_lambda_write:box.dsn"]
    iife_in_connect_arg_tree = ast.parse(_CLI_FIXTURE_HEADER + "def iife_in_connect_arg(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    return psycopg.connect(autocommit=bool((lambda: setattr(box, \"dsn\", replacement))()), conninfo=box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, iife_in_connect_arg_tree)] == ["iife_in_connect_arg:box.dsn"]
    ifexp_callee_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def ifexp_callee_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (dict.update if True else dict.update)(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, ifexp_callee_write_tree)] == ["ifexp_callee_write:box.dsn"]
    bound_dunder_first_arg_fp_tree = ast.parse(_CLI_FIXTURE_HEADER + "def bound_dunder_first_arg_fp(box, other, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    other.__dict__.__setitem__(box.dsn, replacement)\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, bound_dunder_first_arg_fp_tree) == ()
    starred_rhs_unpack_tree = ast.parse(_CLI_FIXTURE_HEADER + "def starred_rhs_unpack(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    u, = (*(dict.update,),)\n    u(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, starred_rhs_unpack_tree)] == ["starred_rhs_unpack:box.dsn"]
    iife_with_args_tree = ast.parse(_CLI_FIXTURE_HEADER + "def iife_with_args(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (lambda x: setattr(x, \"dsn\", replacement))(box)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, iife_with_args_tree)] == ["iife_with_args:box.dsn"]
    iife_default_arg_tree = ast.parse(_CLI_FIXTURE_HEADER + "def iife_default_arg(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (lambda x=box: setattr(x, \"dsn\", replacement))()\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, iife_default_arg_tree)] == ["iife_default_arg:box.dsn"]
    iife_arg_write_tree = ast.parse(_CLI_FIXTURE_HEADER + "def iife_arg_write(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (lambda: None)(setattr(box, \"dsn\", replacement))\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, iife_arg_write_tree)] == ["iife_arg_write:box.dsn"]
    ifexp_iife_tree = ast.parse(_CLI_FIXTURE_HEADER + "def ifexp_iife(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    ((lambda: setattr(box, \"dsn\", replacement)) if box else (lambda: None))()\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, ifexp_iife_tree)] == ["ifexp_iife:box.dsn"]
    object_setattr_alias_tree = ast.parse(_CLI_FIXTURE_HEADER + "def object_setattr_alias(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    s = object.__setattr__\n    s(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, object_setattr_alias_tree)] == ["object_setattr_alias:box.dsn"]
    object_alias_chain_tree = ast.parse(_CLI_FIXTURE_HEADER + "def object_alias_chain(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    T = object\n    T.__setattr__(box, \"dsn\", replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, object_alias_chain_tree)] == ["object_alias_chain:box.dsn"]
    subscript_callee_tree = ast.parse(_CLI_FIXTURE_HEADER + "def subscript_callee(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (dict.update,)[0](box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, subscript_callee_tree)] == ["subscript_callee:box.dsn"]
    boolop_callee_tree = ast.parse(_CLI_FIXTURE_HEADER + "def boolop_callee(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (dict.update or replacement)(box.__dict__, dsn=replacement)\n    return psycopg.connect(box.dsn)\n"); assert [v.name for v in _boundary_validation_violations(path, boolop_callee_tree)] == ["boolop_callee:box.dsn"]
    nested_inner_lambda_fp_tree = ast.parse(_CLI_FIXTURE_HEADER + "def nested_inner_lambda_fp(box, replacement):\n    validate_local_postgres_dsn(box.dsn, env_var_name=\"EXAMPLE_DSN\")\n    (lambda: (lambda: setattr(box, \"dsn\", replacement)))()\n    return psycopg.connect(box.dsn)\n"); assert _boundary_validation_violations(path, nested_inner_lambda_fp_tree) == ()
    deep_iife = _CLI_FIXTURE_HEADER + "def deep_iife_perf(box, dsn):\n    validate_local_postgres_dsn(dsn, env_var_name=\"EXAMPLE_DSN\")\n    " + "(lambda: " * 20 + 'setattr(box, "dsn", 1)' + ")()" * 20 + "\n    return psycopg.connect(dsn)\n"
    deep_start = time.perf_counter(); assert _boundary_validation_violations(path, ast.parse(deep_iife)) == (); assert time.perf_counter() - deep_start < 0.1
def test_intermediary_boundary_guard_catches_and_allows_validated_boundaries() -> None:
    candidate_fixture = ast.parse("from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\ndef candidate_decision_score_report_sink_from_config(config, connection_factory): return _CandidateDecisionScoreReportSink(dsn=config.dsn, table_name=\"t\", connection_factory=connection_factory)\ndef candidate_decision_score_report_sink_from_config(config, connection_factory): validate_local_postgres_dsn(config.dsn, env_var_name=\"EXAMPLE_DSN\"); return _CandidateDecisionScoreReportSink(dsn=config.dsn, table_name=\"t\", connection_factory=connection_factory)\nclass _CandidateDecisionScoreReportSink:\n    def __call__(self, report): return self.connection_factory(self.dsn)\nclass _CandidateDecisionScoreReportSink:\n    def __call__(self, report): validate_local_postgres_dsn(self.dsn, env_var_name=\"EXAMPLE_DSN\"); return self.connection_factory(self.dsn)\n")
    queue_fixture = ast.parse("from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\ndef paper_strategy_candidate_research_queue_report_sink_from_config(config, report_sink): return _StrategyCandidateResearchQueueReportSink(dsn=config.dsn, table_name=\"t\", report_sink=report_sink)\ndef paper_strategy_candidate_research_queue_report_sink_from_config(config, report_sink): validate_local_postgres_dsn(config.dsn, env_var_name=\"EXAMPLE_DSN\"); return _StrategyCandidateResearchQueueReportSink(dsn=config.dsn, table_name=\"t\", report_sink=report_sink)\nclass _StrategyCandidateResearchQueueReportSink:\n    def __call__(self, report): return self._report_sink(dsn=self._dsn, report=report, table_name=\"t\")\nclass _StrategyCandidateResearchQueueReportSink:\n    def __call__(self, report): validate_local_postgres_dsn(self.table_name, env_var_name=\"EXAMPLE_DSN\"); return self._report_sink(dsn=self._dsn, report=report, table_name=\"t\")\nclass _StrategyCandidateResearchQueueReportSink:\n    def __call__(self, report): validate_local_postgres_dsn(self._dsn, env_var_name=\"EXAMPLE_DSN\"); return self._report_sink(dsn=self._dsn, report=report, table_name=\"t\")\ndef paper_strategy_candidate_research_queue_report_sink_from_config(config, report_sink, backup): validate_local_postgres_dsn(config.dsn, env_var_name=\"EXAMPLE_DSN\"); return _StrategyCandidateResearchQueueReportSink(table_name=(config := backup), dsn=config.dsn, report_sink=report_sink)\nclass _StrategyCandidateResearchQueueReportSink:\n    def __call__(self, report, replacement): validate_local_postgres_dsn(self._dsn, env_var_name=\"EXAMPLE_DSN\"); self.__dict__[\"_dsn\"] = replacement; return self._report_sink(dsn=self._dsn, report=report, table_name=\"t\")\n")
    check_outcomes_fixture = ast.parse("from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader):\n    if db_config.enabled:\n        if db_config.dsn is None: raise ValueError(\"dsn required\")\n        return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader):\n    if db_config.enabled:\n        if db_config.dsn is None: raise ValueError(\"dsn required\")\n        validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"); return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, backup):\n    validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"); return db_loader(table_name=(db_config := backup), dsn=db_config.dsn)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, backup):\n    validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"); limit_cb = lambda offset=(db_config := backup): None; return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, replacement):\n    match (validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]:\n        case db_config: pass\n    return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, replacement):\n    try: pass\n    except (validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"), Exception)[1] as db_config:\n        return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, replacement):\n    db_config = (validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1]\n    return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, replacement):\n        (db_config := (validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\"), replacement)[1])\n        return db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\ndef load_check_outcomes_paper_trade_records(journal_path, db_config, db_loader, replacement):\n    validate_local_postgres_dsn(db_config.dsn, env_var_name=\"EXAMPLE_DSN\")\n    for _ in range(2):\n        records = db_loader(dsn=db_config.dsn, table_name=db_config.table_name)\n        (db_config := replacement)\n")
    candidate = _boundary_validation_violations(REPO_ROOT / "src" / "fixture_boundary" / "candidate_decision_score_store.py", candidate_fixture)
    queue = _boundary_validation_violations(REPO_ROOT / "src" / "fixture_boundary" / "strategy_candidate_research_queue_store.py", queue_fixture)
    check_outcomes = _boundary_validation_violations(REPO_ROOT / "src" / "fixture_boundary" / "check_outcomes_paper_trade_source.py", check_outcomes_fixture)
    assert [v.name for v in candidate] == ["candidate_decision_score_report_sink_from_config:config.dsn", "_CandidateDecisionScoreReportSink.__call__:self.dsn"]; assert {v.kind for v in candidate} == {"intermediary sink before local dsn validation", "intermediary callback before local dsn validation"}; assert [v.name for v in queue] == ["paper_strategy_candidate_research_queue_report_sink_from_config:config.dsn"] * 2 + ["_StrategyCandidateResearchQueueReportSink.__call__:self._dsn"] * 3; assert {v.kind for v in queue} == {"intermediary sink before local dsn validation", "intermediary callback before local dsn validation"}; assert [v.name for v in check_outcomes] == ["load_check_outcomes_paper_trade_records:db_config.dsn"] * 8; assert {v.kind for v in check_outcomes} == {"intermediary loader before local dsn validation"}
def test_repo_wide_pin_scanners_reject_their_counterexamples() -> None:
    env_fixture = ast.parse("import os\nfrom os import environ as env\n" + 'def read_dsn(FIXTURE_DB_DSN_ENV_VAR, OTHER_DSN_ENV_VAR): primary = os.environ["POLYMARKET_ALPHA_LAB_FIXTURE_DB_DSN"]; ' + 'secondary = env.get(FIXTURE_DB_DSN_ENV_VAR); tertiary = os.getenv("DATABASE_URL"); quaternary = env[OTHER_DSN_ENV_VAR]; unrelated = os.environ["SOME_TOKEN"]; return primary\n')
    config_fixture_path = REPO_ROOT / "src" / "polymarket_alpha_lab" / "supabase_fixture_config.py"; unvalidated_config = ast.parse(ast.parse("from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\nclass SupabaseFixtureConfig:\n    dsn: str | None\n    def __post_init__(self) -> None: object.__setattr__(self, \"dsn\", self.dsn or None)\ndef uses_validator_elsewhere(dsn): return validate_local_postgres_dsn(dsn, env_var_name=\"FIXTURE_DSN\")\n"))
    missing_import_config = ast.parse("class SupabaseFixtureConfig:\n    dsn: str | None\n    def __post_init__(self) -> None:\n        " + 'if self.dsn is not None: validate_local_postgres_dsn(self.dsn, env_var_name="FIXTURE_DSN")\n')
    fixture_source = "import psycopg\n\n\ndef connect(dsn):\n    return psycopg.connect(dsn)\n"; covered_and_reversed = ast.parse("from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\n" + "class SupabaseValidConfig:\n    dsn: str | None\n    def __post_init__(self) -> None:\n        if self.dsn is not None: validate_local_postgres_dsn(self.dsn, env_var_name=\"FIXTURE_DSN\")\nclass SupabaseReversedConfig:\n    dsn: str | None\n    def __post_init__(self) -> None:\n        if self.dsn is None: validate_local_postgres_dsn(self.dsn, env_var_name=\"FIXTURE_DSN\")\n")
    shim_path = REPO_ROOT / "src" / "fixture_shim.py"; alternate_shim = ast.parse('from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\n' + 'def _validate_local_dsn(dsn): return dsn.startswith("postgres://localhost")\n')
    wrong_operand_shim = ast.parse('from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\n' + 'def _validate_local_dsn(dsn): validate_local_postgres_dsn(dsn_backup, env_var_name="FIXTURE_DSN")\n')
    missing_import_shim = ast.parse('def _validate_local_dsn(dsn): validate_local_postgres_dsn(dsn, env_var_name="FIXTURE_DSN")')
    assert [v.name for v in _environment_read_violations(REPO_ROOT / "src" / "fixture_store.py", env_fixture, kind="dsn environment read outside config module", dsn_keys_only=True)] == ["'POLYMARKET_ALPHA_LAB_FIXTURE_DB_DSN'", "FIXTURE_DB_DSN_ENV_VAR", "'DATABASE_URL'", "OTHER_DSN_ENV_VAR"]
    ternary_fixture = ast.parse('from os import environ\ndef load(override, FIXTURE_DB_DSN_ENV_VAR): source = environ if override is None else override; ' + 'return source.get(FIXTURE_DB_DSN_ENV_VAR)\n'); assert [v.name for v in _environment_read_violations(REPO_ROOT / "src" / "fixture_store.py", ternary_fixture, kind="dsn environment read outside config module", dsn_keys_only=True)] == ["FIXTURE_DB_DSN_ENV_VAR"]
    assert [v.name for v in _config_module_validation_violations(config_fixture_path, unvalidated_config)] == ["SupabaseFixtureConfig"]; assert {v.kind for v in _config_module_validation_violations(config_fixture_path, unvalidated_config)} == {"config __post_init__ missing guarded self.dsn validation"}; assert [v.kind for v in _config_module_validation_violations(config_fixture_path, missing_import_config)] == ["config missing shared dsn validator import"]
    for source, expected_name in ((fixture_source, "psycopg"), ("import psycopg as pg\n\n\ndef connect(dsn):\n    return pg.connect(dsn)\n", "pg"), ("from psycopg import connect as pg_connect\n\n\ndef connect(dsn):\n    return pg_connect(dsn)\n", "pg_connect")):
        assert (violation := _connector_reference_violation(REPO_ROOT / "src" / "polymarket_alpha_lab" / "future_store_psycopg.py", ast.parse(source))) is not None
        assert (violation.kind, violation.name) == ("connector outside frozen allowlist", expected_name)
    assert _connector_reference_violation(REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py", ast.parse(fixture_source)) is None
    assert [v.name for v in _config_module_validation_violations(config_fixture_path, covered_and_reversed)] == ["SupabaseReversedConfig"]; missing_post_init = ast.parse("from polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\n" + "class SupabaseNoPostInitConfig: dsn: str | None"); assert [v.name for v in _config_module_validation_violations(config_fixture_path, missing_post_init)] == ["SupabaseNoPostInitConfig"]; assert [v.kind for v in _config_module_validation_violations(config_fixture_path, missing_post_init)] == ["config missing __post_init__"]
    for fixture in (alternate_shim, wrong_operand_shim): assert [v.kind for v in _local_dsn_shim_violations(shim_path, fixture)] == ["dsn shim not delegating to shared validator"]
    assert [v.kind for v in _local_dsn_shim_violations(shim_path, missing_import_shim)] == ["dsn shim without shared validator import"]
_CLI_FIXTURE_HEADER = "import psycopg\nfrom polymarket_alpha_lab.supabase_local_dsn import validate_local_postgres_dsn\n"
_INVALID_HOSTED_DSN = "postgresql://postgres:fixture-secret@db.hosted.example.com/postgres"
_VALID_LOCAL_DSN = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"
class _RecordingSpy:
    def __init__(self, result=None): self.calls, self.result = [], result
    def __call__(self, *args, **kwargs): self.calls.append((args, kwargs)); return self.result
def _corrupted_config(config):
    object.__setattr__(config, "dsn", _INVALID_HOSTED_DSN); return config
def test_intermediary_dsn_boundaries_never_reach_callbacks_with_invalid_dsn() -> None:
    candidate_spy = _RecordingSpy()
    with pytest.raises(ValueError): candidate_decision_score_report_sink_from_config(SimpleNamespace(enabled=True, dsn=_INVALID_HOSTED_DSN, table="candidate_decision_score_reports"), connection_factory=candidate_spy)
    assert candidate_spy.calls == [], "invalid DSN reached the connection callback"; queue_spy = _RecordingSpy()
    with pytest.raises(ValueError): paper_strategy_candidate_research_queue_report_sink_from_config(_corrupted_config(SupabaseStrategyCandidateResearchQueueConfig(enabled=True, dsn=_VALID_LOCAL_DSN)), report_sink=queue_spy)
    assert queue_spy.calls == [], "invalid DSN reached the report sink callback"; loader_spy = _RecordingSpy(result=())
    with pytest.raises(Exception): load_check_outcomes_paper_trade_records(journal_path="unused.jsonl", db_loader=loader_spy, db_config=_corrupted_config(SupabasePaperTradeJournalConfig(enabled=True, dsn=_VALID_LOCAL_DSN)))
    assert loader_spy.calls == [], "invalid DSN reached the db_loader callback"
def test_intermediary_dsn_boundaries_preserve_delegation_for_valid_dsn() -> None:
    candidate_spy = _RecordingSpy()
    with pytest.raises(Exception) as excinfo: candidate_decision_score_report_sink_from_config(SimpleNamespace(enabled=True, dsn=_VALID_LOCAL_DSN, table="candidate_decision_score_reports"), connection_factory=candidate_spy)(object())
    assert candidate_spy.calls and candidate_spy.calls[0][0] == (_VALID_LOCAL_DSN,); assert _VALID_LOCAL_DSN not in str(excinfo.value); queue_spy = _RecordingSpy(result=object())
    queue_result = paper_strategy_candidate_research_queue_report_sink_from_config(SupabaseStrategyCandidateResearchQueueConfig(enabled=True, dsn=_VALID_LOCAL_DSN), report_sink=queue_spy)(object())
    assert queue_spy.calls[0][1]["dsn"] == _VALID_LOCAL_DSN; assert queue_result is queue_spy.result; loader_spy = _RecordingSpy(result=())
    assert load_check_outcomes_paper_trade_records(journal_path="unused.jsonl", db_config=SupabasePaperTradeJournalConfig(enabled=True, dsn=_VALID_LOCAL_DSN), db_loader=loader_spy) == (); assert loader_spy.calls[0][1]["dsn"] == _VALID_LOCAL_DSN
