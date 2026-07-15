from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_memory_context_readiness_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/candidate_memory_context_readiness_report.py",
)
GENERATED_AT = datetime(2026, 7, 11, 16, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def load_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    module: Any,
    candidate_ref: str = "candidate-alpha",
    *,
    team_route_ready: bool = True,
    memory_readiness_digest_ready: bool = True,
    event_category_memory_ready: bool = True,
    source_family_feedback_ready: bool = True,
    settled_outcome_calibration_ready: bool = True,
    specialist_memory_ready: bool = True,
    domain_memory_ready: bool = True,
    observed_at: datetime = GENERATED_AT,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.CandidateMemoryContextReadinessSignal(
        candidate_ref=candidate_ref,
        team_route_ready=team_route_ready,
        memory_readiness_digest_ready=memory_readiness_digest_ready,
        event_category_memory_ready=event_category_memory_ready,
        source_family_feedback_ready=source_family_feedback_ready,
        settled_outcome_calibration_ready=settled_outcome_calibration_ready,
        specialist_memory_ready=specialist_memory_ready,
        domain_memory_ready=domain_memory_ready,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(module: Any, *signals: Any, generated_at: datetime = GENERATED_AT) -> Any:
    return module.build_candidate_memory_context_readiness_report(
        signals,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_memory_context_readiness_aggregates_rows_payload_and_ratios() -> None:
    module = load_module()
    ready = signal(module, "candidate-ready")
    attention = signal(
        module,
        "candidate-attention",
        domain_memory_ready=False,
        reason_codes=("manual_memory_refresh_attention",),
    )
    blocker = signal(
        module,
        "candidate-blocker",
        team_route_ready=False,
        memory_readiness_digest_ready=False,
        event_category_memory_ready=False,
        source_family_feedback_ready=False,
        settled_outcome_calibration_ready=False,
        specialist_memory_ready=False,
        domain_memory_ready=False,
    )

    first = report(module, attention, blocker, ready)
    second = report(module, ready, blocker, attention)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_CANDIDATE_MEMORY_CONTEXT_READINESS_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.ready_count == ONE
    assert first.attention_count == ONE
    assert first.blocker_count == ONE
    assert first.memory_context_ready_count == ONE
    assert first.ready_ratio == d("0.333333")
    assert first.status == "blocker"
    assert first.missing_context_count == d("8.000000")
    assert first.reason_codes == (
        "team_route_missing_blocker",
        "memory_readiness_digest_missing_blocker",
        "event_category_memory_missing_blocker",
        "source_family_feedback_missing_blocker",
        "settled_outcome_calibration_missing_blocker",
        "specialist_memory_missing_blocker",
        "domain_memory_missing_attention",
        "manual_memory_refresh_attention",
        "memory_context_ready",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.public_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("blocker", "attention", "ready")
    assert tuple(row.memory_context_ready for row in first.rows) == (False, False, True)
    assert first.rows[0].ready_context_count == ZERO
    assert first.rows[0].missing_context_count == d("7.000000")
    assert first.rows[0].readiness_ratio == ZERO
    assert first.rows[1].ready_context_count == d("6.000000")
    assert first.rows[1].missing_context_count == ONE
    assert first.rows[1].readiness_ratio == d("0.857143")
    assert first.rows[2].reason_codes == ("memory_context_ready",)
    assert not hasattr(first.rows[0], "candidate_ref")

    payload = module.candidate_memory_context_readiness_report_payload(first)
    assert payload == module.candidate_memory_context_readiness_report_payload(second)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["ready_ratio"] == "0.333333"
    assert payload["rows"][0]["public_row_number"] == "1.000000"
    assert payload["rows"][0]["missing_context_count"] == "7.000000"
    assert "candidate-blocker" not in json.dumps(payload, sort_keys=True)
    assert "candidate_ref" not in json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)


def test_empty_inputs_block_with_no_candidates_reason_count() -> None:
    module = load_module()

    readiness = report(module)

    assert readiness.status == "blocker"
    assert readiness.candidate_count == ZERO
    assert readiness.ready_count == ZERO
    assert readiness.attention_count == ZERO
    assert readiness.blocker_count == ZERO
    assert readiness.ready_ratio == ZERO
    assert readiness.missing_context_count == ZERO
    assert readiness.reason_codes == ("candidate_memory_context_no_candidates_blocker",)
    assert readiness.reason_code_counts == (
        module.CandidateMemoryContextReadinessReasonCodeCount(
            reason_code="candidate_memory_context_no_candidates_blocker",
            count=ONE,
            ratio=ONE,
        ),
    )
    assert readiness.rows == ()


def test_decimal_datetime_candidate_public_boundary_validation() -> None:
    module = load_module()

    readiness = report(
        module,
        signal(module),
        generated_at=datetime(
            2026,
            7,
            11,
            12,
            30,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert readiness.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="candidate_ref"):
        signal(module, "candidate ref with spaces")
    with pytest.raises(ValueError, match="candidate_ref"):
        signal(module, "")
    with pytest.raises(ValueError, match="team_route_ready"):
        signal(module, team_route_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        signal(module, reason_codes=["manual_memory_refresh_attention"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        signal(module, observed_at=datetime(2026, 7, 11, 16, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(module, signal(module), generated_at=datetime(2026, 7, 11, 16, 30))
    with pytest.raises(ValueError, match="duplicate candidate_ref"):
        report(module, signal(module, "duplicate"), signal(module, "duplicate"))
    with pytest.raises(ValueError, match="observed_at"):
        report(
            module,
            signal(
                module,
                "future-observation",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(readiness, ready_ratio=_DecimalSubclass("1.000000"))

    for public_value in (readiness, *readiness.rows, *readiness.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_hard_flags_frozen_dataclasses_and_payload_revalidation() -> None:
    module = load_module()
    readiness = report(module, signal(module, "frozen-candidate"))

    assert is_dataclass(module.CandidateMemoryContextReadinessSignal)
    assert is_dataclass(module.CandidateMemoryContextReadinessRow)
    assert is_dataclass(module.CandidateMemoryContextReadinessReasonCodeCount)
    assert is_dataclass(module.CandidateMemoryContextReadinessReport)
    with pytest.raises(FrozenInstanceError):
        readiness.status = "ready"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        readiness.rows[0].readiness_ratio = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        signal(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)

    object.__setattr__(readiness.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.candidate_memory_context_readiness_report_payload(readiness)


def test_reason_counts_public_exports_and_report_validation() -> None:
    module = load_module()

    readiness = report(
        module,
        signal(module, "attention-one", domain_memory_ready=False),
        signal(module, "attention-two", domain_memory_ready=False),
        signal(module, "ready-one"),
    )

    assert tuple(row.status for row in readiness.rows) == (
        "attention",
        "attention",
        "ready",
    )
    assert readiness.status == "attention"
    assert readiness.reason_code_counts == (
        module.CandidateMemoryContextReadinessReasonCodeCount(
            reason_code="domain_memory_missing_attention",
            count=d("2.000000"),
            ratio=d("0.666667"),
        ),
        module.CandidateMemoryContextReadinessReasonCodeCount(
            reason_code="memory_context_ready",
            count=ONE,
            ratio=d("0.333333"),
        ),
    )
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_MEMORY_CONTEXT_READINESS_REPORT_CONFIG_VERSION",
        "CANDIDATE_MEMORY_CONTEXT_READINESS_STATUSES",
        "CandidateMemoryContextReadinessReasonCodeCount",
        "CandidateMemoryContextReadinessReport",
        "CandidateMemoryContextReadinessRow",
        "CandidateMemoryContextReadinessSignal",
        "build_candidate_memory_context_readiness_report",
        "candidate_memory_context_readiness_report_payload",
    )

    with pytest.raises(ValueError, match="candidate_count"):
        replace(readiness, candidate_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(readiness, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(readiness.rows[0], status="review")


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "auth",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
