from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.manual_review_workload_capacity_report as subject
from polymarket_alpha_lab.manual_review_workload_capacity_report import (
    DEFAULT_MANUAL_REVIEW_WORKLOAD_CAPACITY_REPORT_CONFIG_VERSION,
    ManualReviewWorkloadCapacityInputs,
    ManualReviewWorkloadCapacityReport,
    build_manual_review_workload_capacity_report,
    format_manual_review_workload_capacity_digest,
    manual_review_workload_capacity_public_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 16, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build(
    *,
    available_reviewer_count: Decimal = d("3.000000"),
    ready_candidate_count: Decimal = d("7.000000"),
    watch_candidate_count: Decimal = d("4.000000"),
    blocked_candidate_count: Decimal = d("1.000000"),
    average_review_minutes: Decimal = d("18.000000"),
    time_to_nearest_resolution_seconds: Decimal = d("14400.000000"),
    high_priority_candidate_count: Decimal = d("2.000000"),
    source_freshness_attention_count: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
    generated_at: datetime = GENERATED_AT,
) -> ManualReviewWorkloadCapacityReport:
    return build_manual_review_workload_capacity_report(
        available_reviewer_count=available_reviewer_count,
        ready_candidate_count=ready_candidate_count,
        watch_candidate_count=watch_candidate_count,
        blocked_candidate_count=blocked_candidate_count,
        average_review_minutes=average_review_minutes,
        time_to_nearest_resolution_seconds=time_to_nearest_resolution_seconds,
        high_priority_candidate_count=high_priority_candidate_count,
        source_freshness_attention_count=source_freshness_attention_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_public_numbers_are_decimals(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name in {"paper_only", "report_only", "readonly"}:
            assert type(item) is bool
        elif field.name in {"capacity_ready"}:
            assert type(item) is bool
        elif field.name in {"blocked_reason_codes", "attention_reason_codes"}:
            assert type(item) is tuple
        elif field.name in {"generated_at", "config_version", "public_digest"}:
            continue
        elif field.name.endswith(("_count", "_minutes", "_seconds", "_score", "_ratio")):
            assert type(item) is Decimal


def test_manual_review_workload_capacity_report_scores_read_only_queue_capacity() -> None:
    report = build(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))))

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == DEFAULT_MANUAL_REVIEW_WORKLOAD_CAPACITY_REPORT_CONFIG_VERSION
    assert report.available_reviewer_count == d("3.000000")
    assert report.ready_candidate_count == d("7.000000")
    assert report.watch_candidate_count == d("4.000000")
    assert report.blocked_candidate_count == d("1.000000")
    assert report.average_review_minutes == d("18.000000")
    assert report.time_to_nearest_resolution_seconds == d("14400.000000")
    assert report.high_priority_candidate_count == d("2.000000")
    assert report.source_freshness_attention_count == d("1.000000")
    assert report.estimated_backlog_minutes == d("126.000000")
    assert report.ready_ratio == d("0.583333")
    assert report.review_capacity_score == d("0.714286")
    assert report.capacity_ready is False
    assert report.blocked_reason_codes == ("review_capacity_score_below_ready",)
    assert report.attention_reason_codes == (
        "high_priority_candidates_present",
        "source_freshness_attention_present",
        "nearest_resolution_under_review_window",
        "watch_candidates_present",
        "blocked_candidates_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.public_digest.startswith("sha256:")
    assert_public_numbers_are_decimals(report)

    digest = format_manual_review_workload_capacity_digest(report)
    assert "capacity_ready=false" in digest
    assert "score=0.714286" in digest
    assert "backlog_minutes=126.000000" in digest
    assert f"public_digest={report.public_digest}" in digest


def test_manual_review_workload_capacity_ready_when_capacity_covers_ready_queue() -> None:
    report = build(
        available_reviewer_count=d("5.000000"),
        ready_candidate_count=d("6.000000"),
        watch_candidate_count=ZERO,
        blocked_candidate_count=ZERO,
        average_review_minutes=d("10.000000"),
        time_to_nearest_resolution_seconds=d("86400.000000"),
        high_priority_candidate_count=ZERO,
        source_freshness_attention_count=ZERO,
    )

    assert report.capacity_ready is True
    assert report.review_capacity_score == d("1.000000")
    assert report.estimated_backlog_minutes == d("60.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()


def test_manual_review_workload_capacity_payload_and_digest_are_deterministic() -> None:
    first = build()
    second = build(generated_at=GENERATED_AT)

    assert first.public_payload == second.public_payload
    assert first.public_digest == second.public_digest

    payload = manual_review_workload_capacity_public_payload(first)
    assert payload == first.public_payload
    assert payload["public_digest"] == first.public_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "126.000000" in walk_values(payload)
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert manual_review_workload_capacity_public_payload(payload) == payload

    tampered = dict(payload)
    tampered["review_capacity_score"] = "0.999999"
    with pytest.raises(ValueError, match="public_digest"):
        manual_review_workload_capacity_public_payload(tampered)


def test_manual_review_workload_capacity_rejects_mutating_or_unsafe_modes() -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        kwargs = {flag_name: False}
        with pytest.raises(ValueError, match=flag_name):
            build(**kwargs)

    with pytest.raises(ValueError, match="live trading"):
        subject._reject_unsafe_public_payload("unsafe", {"auth": "wallet_order_execution"})

    report = build()
    with pytest.raises(FrozenInstanceError):
        report.ready_candidate_count = ZERO  # type: ignore[misc]


def test_manual_review_workload_capacity_requires_decimal_only_public_numbers() -> None:
    with pytest.raises(TypeError, match="available_reviewer_count must be Decimal"):
        build(available_reviewer_count=3)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="ready_candidate_count must be exactly Decimal"):
        build(ready_candidate_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="available_reviewer_count must be nonnegative"):
        build(available_reviewer_count=d("-1.000000"))

    with pytest.raises(ValueError, match="average_review_minutes must be positive"):
        build(average_review_minutes=ZERO)


def test_manual_review_workload_capacity_inputs_are_frozen_and_buildable() -> None:
    inputs = ManualReviewWorkloadCapacityInputs(
        available_reviewer_count=d("2.000000"),
        ready_candidate_count=d("2.000000"),
        watch_candidate_count=ZERO,
        blocked_candidate_count=ZERO,
        average_review_minutes=d("15.000000"),
        time_to_nearest_resolution_seconds=d("7200.000000"),
        high_priority_candidate_count=ZERO,
        source_freshness_attention_count=ZERO,
    )

    report = build_manual_review_workload_capacity_report(inputs, generated_at=GENERATED_AT)

    assert report.capacity_ready is True
    assert report.review_capacity_score == d("1.000000")
    assert report.public_payload["available_reviewer_count"] == "2.000000"
    with pytest.raises(FrozenInstanceError):
        inputs.ready_candidate_count = ZERO  # type: ignore[misc]
