from __future__ import annotations

import ast
import importlib
import inspect
import py_compile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.candidate_decision_score import (
    CandidateDecisionScoreConfig,
    CandidateDecisionScoreInput,
    CandidateDecisionScoreReport,
    build_candidate_decision_score_report,
)


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_score_history_payload"
SOURCE_PATH = Path("src/polymarket_alpha_lab/candidate_decision_score_history_payload.py")
GENERATED_AT = datetime(2026, 7, 7, 12, 30, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing candidate decision score history payload module: {exc}")


def history_api() -> Any:
    return importlib.import_module("polymarket_alpha_lab.candidate_decision_score_history")


def d(value: str) -> Decimal:
    return Decimal(value)


def source_report(
    *,
    generated_at: datetime = GENERATED_AT,
    candidate_id: str = "candidate-alpha",
    market_id: str = "market-alpha",
    primary_team_id: str = "politics",
    gross_edge: Decimal | None = d("0.060000"),
    evidence_score: Decimal = d("0.850000"),
    team_memory_policy: str = "allow",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CandidateDecisionScoreReport:
    report = build_candidate_decision_score_report(
        CandidateDecisionScoreInput(
            candidate_id=candidate_id,
            market_id=market_id,
            normalized_market_question=f"Will {candidate_id} resolve yes?",
            primary_team_id=primary_team_id,
            secondary_team_ids=("crypto_btc",),
            selected_side="yes",
            forecast_probability=d("0.620000"),
            executable_price=d("0.560000"),
            gross_edge=gross_edge,
            estimated_cost_drag=d("0.010000"),
            cost_score=d("0.800000"),
            liquidity_score=d("0.900000"),
            evidence_score=evidence_score,
            resolution_score=d("0.700000"),
            team_memory_score=d("0.750000"),
            team_memory_policy=team_memory_policy,
            source_report_refs=(
                f"candidate-decision-team-memory:{candidate_id}:2026-07-07",
                f"candidate-resolution-risk:{market_id}:2026-07-07",
            ),
            adapter_reason_codes=(
                "team_memory_adapter_allow",
                "resolution_risk_adapter_passed",
            ),
        ),
        config=CandidateDecisionScoreConfig(config_version="candidate-decision-score-v1"),
        generated_at=generated_at,
    )
    object.__setattr__(report, "paper_only", paper_only)
    object.__setattr__(report, "report_only", report_only)
    object.__setattr__(report, "readonly", readonly)
    return report


def history_report(*reports: CandidateDecisionScoreReport) -> object:
    return history_api().build_candidate_decision_score_history_report(
        reports,
        generated_at=datetime(2026, 7, 7, 13, 0, tzinfo=UTC),
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def flattened_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(flattened_text(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(flattened_text(item) for item in value)
    return str(value)


def test_empty_history_payload_is_json_ready_aggregate_summary() -> None:
    module = api()
    report = history_report()

    payload = module.candidate_decision_score_history_payload(report)

    assert payload == {
        "generated_at": "2026-07-07T13:00:00+00:00",
        "status": "empty",
        "report_count": "0.000000",
        "latest_generated_at": None,
        "action_counts": [],
        "reason_counts": [],
        "primary_team_counts": [],
        "source_report_count": "0.000000",
        "candidate_count": "0.000000",
        "action_reject_count": "0.000000",
        "action_watch_count": "0.000000",
        "action_research_more_count": "0.000000",
        "action_paper_recommend_count": "0.000000",
        "hard_blocked_count": "0.000000",
        "blocked_total": "0.000000",
        "watch_total": "0.000000",
        "paper_recommend_total": "0.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)


def test_nonempty_history_payload_contains_only_public_aggregate_values() -> None:
    module = api()
    report = history_report(
        source_report(
            generated_at=datetime(2026, 7, 7, 11, 0, tzinfo=UTC),
            candidate_id="candidate-alpha",
            market_id="market-alpha",
            gross_edge=d("0.012000"),
        ),
        source_report(
            generated_at=datetime(2026, 7, 7, 11, 5, tzinfo=UTC),
            candidate_id="candidate-beta",
            market_id="market-beta",
            evidence_score=d("0.100000"),
            primary_team_id="macro_rates",
        ),
        source_report(
            generated_at=datetime(2026, 7, 7, 11, 10, tzinfo=UTC),
            candidate_id="candidate-alpha",
            market_id="market-alpha",
        ),
    )

    payload = module.candidate_decision_score_history_payload(report)

    assert payload == {
        "generated_at": "2026-07-07T13:00:00+00:00",
        "status": "observed",
        "report_count": "3.000000",
        "latest_generated_at": "2026-07-07T11:10:00+00:00",
        "action_counts": [
            {"action": "paper_recommend", "count": "1.000000"},
            {"action": "reject", "count": "1.000000"},
            {"action": "watch", "count": "1.000000"},
        ],
        "reason_counts": [
            {"reason_code": "resolution_risk_adapter_passed", "count": "2.000000"},
            {"reason_code": "team_memory_adapter_allow", "count": "2.000000"},
            {"reason_code": "candidate_decision_paper_recommend", "count": "1.000000"},
            {"reason_code": "candidate_decision_reject", "count": "1.000000"},
            {"reason_code": "candidate_decision_watch", "count": "1.000000"},
            {
                "reason_code": "evidence_score_below_blocking_threshold",
                "count": "1.000000",
            },
            {
                "reason_code": "net_edge_below_paper_recommend_threshold",
                "count": "1.000000",
            },
        ],
        "primary_team_counts": [
            {"team_id": "politics", "count": "2.000000"},
            {"team_id": "macro_rates", "count": "1.000000"},
        ],
        "source_report_count": "3.000000",
        "candidate_count": "2.000000",
        "action_reject_count": "1.000000",
        "action_watch_count": "1.000000",
        "action_research_more_count": "0.000000",
        "action_paper_recommend_count": "1.000000",
        "hard_blocked_count": "1.000000",
        "blocked_total": "1.000000",
        "watch_total": "1.000000",
        "paper_recommend_total": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)


def test_history_payload_does_not_leak_rows_ids_questions_refs_digests_or_storage_details() -> None:
    module = api()
    report = history_report(
        source_report(
            candidate_id="candidate-secret-alpha",
            market_id="market-secret-alpha",
            primary_team_id="macro_rates",
        ),
    )

    payload = module.candidate_decision_score_history_payload(report)

    forbidden_keys = {
        "rows",
        "candidate_id",
        "market_id",
        "question",
        "normalized_market_question",
        "source_report_refs",
        "derived_validation_digest",
        "dsn",
        "table",
        "table_name",
        "payload",
        "raw_payload",
    }
    assert forbidden_keys.isdisjoint(payload.keys())
    public_text = flattened_text(payload)
    for forbidden_fragment in (
        "candidate-secret-alpha",
        "market-secret-alpha",
        "Will candidate-secret-alpha resolve yes?",
        "candidate-decision-team-memory",
        "candidate-resolution-risk",
        "digest",
        "postgres",
        "table",
        "raw_payload",
    ):
        assert forbidden_fragment not in public_text


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_history_payload_fails_closed_on_false_hard_flags(flag_name: str) -> None:
    module = api()
    report = history_report(source_report())
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=f"history_report must be {flag_name}"):
        module.candidate_decision_score_history_payload(report)


def test_history_payload_rejects_non_history_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="CandidateDecisionScoreHistoryReport"):
        module.candidate_decision_score_history_payload(object())


def test_history_payload_source_has_no_forbidden_imports_calls_or_public_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "argparse",
        "asyncpg",
        "click",
        "dotenv",
        "os",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "create_order",
        "cancel_order",
        "replace_order",
        "getenv",
        "open",
        "run",
        "Popen",
        "Client",
        "write",
    }
    forbidden_public_surfaces = {
        "market_id",
        "candidate_id",
        "normalized_market_question",
        "question",
        "source_report_refs",
        "derived_validation_digest",
        "dsn",
        "table_name",
        "raw_payload",
    }

    imported_roots: set[str] = set()
    call_names: set[str] = set()
    public_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.partition(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                public_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    public_names.add(target.id)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert call_names.isdisjoint(forbidden_calls)
    for public_name in public_names:
        for forbidden_surface in forbidden_public_surfaces:
            assert forbidden_surface not in public_name


def test_history_payload_module_py_compiles(tmp_path: Path) -> None:
    assert SOURCE_PATH.exists(), "missing candidate decision score history payload module"
    py_compile.compile(str(SOURCE_PATH), cfile=str(tmp_path / "history_payload.pyc"), doraise=True)
