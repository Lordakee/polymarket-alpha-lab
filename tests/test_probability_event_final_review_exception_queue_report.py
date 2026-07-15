from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_final_review_exception_queue_report import (
    FinalReviewExceptionQueueCandidate,
    ProbabilityEventFinalReviewExceptionQueueReport,
    build_probability_event_final_review_exception_queue_report,
    probability_event_final_review_exception_queue_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_final_review_exception_queue_report.py",
)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object) -> FinalReviewExceptionQueueCandidate:
    values = {
        "candidate_id": "candidate-ready",
        "event_id": "event-20260711",
        "exception_type": "source_gap",
        "blocking_stage": "final_review",
        "age_hours": d("2.000000"),
        "manual_owner": "operator-a",
        "retry_allowed": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FinalReviewExceptionQueueCandidate(**values)


def report(
    *candidates: FinalReviewExceptionQueueCandidate,
) -> ProbabilityEventFinalReviewExceptionQueueReport:
    return build_probability_event_final_review_exception_queue_report(candidates)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in ("wallet", "auth", "order", "database", "network"):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_blocked_and_watch_candidates_emit_ranked_manual_exception_rows() -> None:
    queue = report(
        candidate(
            candidate_id="old-blocked",
            exception_type="unsafe_payload",
            blocking_stage="operator_safety",
            age_hours=d("72.000000"),
            manual_owner="safety-lead",
            retry_allowed=False,
        ),
        candidate(
            candidate_id="watch-retry",
            exception_type="source_gap",
            blocking_stage="evidence_review",
            age_hours=d("8.500000"),
            manual_owner="researcher-a",
            retry_allowed=True,
        ),
    )

    assert isinstance(queue, ProbabilityEventFinalReviewExceptionQueueReport)
    assert queue.exception_status == "blocked"
    assert queue.total_exception_count == d("2.000000")
    assert queue.blocked_exception_count == d("1.000000")
    assert queue.watch_exception_count == d("1.000000")
    assert queue.manual_owner_missing_count == ZERO
    assert queue.retry_allowed_count == d("1.000000")
    assert queue.oldest_age_hours == d("72.000000")
    assert queue.reason_codes == (
        "unsafe_payload_exception_present",
        "operator_safety_blocking_stage_present",
        "retry_not_allowed_present",
        "age_over_24h",
        "source_gap_exception_present",
        "evidence_review_blocking_stage_present",
    )
    assert len(queue.digest) == 64

    assert tuple(row.candidate_id for row in queue.rows) == ("old-blocked", "watch-retry")
    assert queue.rows[0].exception_status == "blocked"
    assert queue.rows[0].priority_rank == d("1.000000")
    assert queue.rows[0].reason_codes == (
        "unsafe_payload_exception_present",
        "operator_safety_blocking_stage_present",
        "retry_not_allowed_present",
        "age_over_24h",
    )
    assert queue.rows[0].manual_next_step == "Escalate to safety owner; retry disabled."
    assert queue.rows[1].exception_status == "watch"
    assert queue.rows[1].priority_rank == d("2.000000")
    assert queue.rows[1].manual_next_step == "Refresh evidence and retry final review."

    payload = queue.public_payload
    assert payload == probability_event_final_review_exception_queue_report_payload(queue)
    assert payload["exception_status"] == "blocked"
    assert payload["total_exception_count"] == "2.000000"
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["age_hours"] == "72.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == queue.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_attention_status_prioritizes_missing_owner_and_stale_retryable_items() -> None:
    queue = report(
        candidate(
            candidate_id="missing-owner",
            exception_type="owner_missing",
            blocking_stage="manual_assignment",
            age_hours=d("25.000000"),
            manual_owner=None,
            retry_allowed=True,
        ),
        candidate(
            candidate_id="fresh-watch",
            exception_type="source_gap",
            blocking_stage="evidence_review",
            age_hours=d("1.000000"),
            manual_owner="researcher-a",
            retry_allowed=True,
        ),
    )

    assert queue.exception_status == "watch"
    assert queue.blocked_exception_count == ZERO
    assert queue.watch_exception_count == d("2.000000")
    assert queue.manual_owner_missing_count == d("1.000000")
    assert queue.retry_allowed_count == d("2.000000")
    assert tuple(row.candidate_id for row in queue.rows) == ("missing-owner", "fresh-watch")
    assert queue.rows[0].reason_codes == (
        "owner_missing_exception_present",
        "manual_assignment_blocking_stage_present",
        "manual_owner_missing",
        "age_over_24h",
    )
    assert queue.rows[0].manual_next_step == "Assign a manual owner before retry."
    assert queue.reason_codes == (
        "owner_missing_exception_present",
        "manual_assignment_blocking_stage_present",
        "manual_owner_missing",
        "age_over_24h",
        "source_gap_exception_present",
        "evidence_review_blocking_stage_present",
    )


def test_empty_exception_queue_is_clear_and_reportable() -> None:
    queue = report()

    assert queue.exception_status == "clear"
    assert queue.total_exception_count == ZERO
    assert queue.blocked_exception_count == ZERO
    assert queue.watch_exception_count == ZERO
    assert queue.manual_owner_missing_count == ZERO
    assert queue.retry_allowed_count == ZERO
    assert queue.oldest_age_hours == ZERO
    assert queue.rows == ()
    assert queue.reason_codes == ()


def test_frozen_flags_decimal_validation_and_candidate_consistency() -> None:
    queue = report(candidate())

    assert is_dataclass(FinalReviewExceptionQueueCandidate)
    assert is_dataclass(ProbabilityEventFinalReviewExceptionQueueReport)
    assert queue.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        queue.exception_status = "clear"  # type: ignore[misc]

    for public_record in (queue, *queue.rows):
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if field.name.endswith("_count") or field.name in {"age_hours", "oldest_age_hours", "priority_rank"}:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(queue, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(queue, readonly=False)
    with pytest.raises(ValueError, match="age_hours"):
        candidate(age_hours=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="age_hours"):
        candidate(age_hours=_DecimalSubclass("2.000000"))
    with pytest.raises(ValueError, match="retry_allowed"):
        candidate(retry_allowed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exception_type"):
        candidate(exception_type="unsupported_type")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="blocking_stage"):
        candidate(blocking_stage="execution")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report inputs"):
        replace(queue, total_exception_count=d("4.000000"))


def test_pure_readonly_report_only_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
