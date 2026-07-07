from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.research_operational_readiness_report import (
    INFORMATION_COLLECTION_PLAN_SURFACE,
    REQUIRED_OPERATIONAL_READINESS_SURFACES,
    ResearchOperationalReadinessConfig,
    ResearchOperationalReadinessReport,
    ResearchOperationalReadinessSignal,
    build_research_operational_readiness_report,
    research_operational_readiness_report_payload,
)


NOW = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def _signal(
    surface_code: str,
    *,
    status: str = "pass",
    coverage_score: Decimal = ONE,
    pending_item_count: Decimal = ZERO,
    block_item_count: Decimal = ZERO,
    public_note: str | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchOperationalReadinessSignal:
    return ResearchOperationalReadinessSignal(
        surface_code=surface_code,
        status=status,
        coverage_score=coverage_score,
        pending_item_count=pending_item_count,
        block_item_count=block_item_count,
        public_note=public_note,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _complete_signals() -> tuple[ResearchOperationalReadinessSignal, ...]:
    return tuple(_signal(surface) for surface in REQUIRED_OPERATIONAL_READINESS_SURFACES)


def _report(
    signals: tuple[ResearchOperationalReadinessSignal, ...],
    *,
    config: ResearchOperationalReadinessConfig | None = None,
) -> ResearchOperationalReadinessReport:
    return build_research_operational_readiness_report(
        signals,
        generated_at=NOW,
        config=config,
    )


def test_all_operational_surfaces_pass_with_hard_readonly_flags() -> None:
    report = _report(_complete_signals())

    assert report.report_status == "pass"
    assert report.surface_count == Decimal("4.000000")
    assert report.pass_count == Decimal("4.000000")
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.min_coverage_score == ONE
    assert report.total_pending_item_count == ZERO
    assert report.total_block_item_count == ZERO
    assert report.reason_codes == ("operational_readiness_pass",)
    assert tuple(row.surface_code for row in report.rows) == REQUIRED_OPERATIONAL_READINESS_SURFACES
    assert all(row.status == "pass" for row in report.rows)
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload == research_operational_readiness_report_payload(report)
    assert payload["surface_count"] == "4.000000"
    assert payload["min_coverage_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    json.dumps(payload, sort_keys=True)
    _assert_no_forbidden_public_surface(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_watch_rollup_preserves_pending_information_collection_plan() -> None:
    signals = tuple(
        _signal(
            surface,
            status="watch",
            coverage_score=Decimal("0.750000"),
            pending_item_count=Decimal("2.000000"),
        )
        if surface == INFORMATION_COLLECTION_PLAN_SURFACE
        else _signal(surface)
        for surface in REQUIRED_OPERATIONAL_READINESS_SURFACES
    )

    report = _report(signals)

    assert report.report_status == "watch"
    assert report.pass_count == Decimal("3.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == ZERO
    assert report.min_coverage_score == Decimal("0.750000")
    assert report.total_pending_item_count == Decimal("2.000000")
    info_row = report.rows[-1]
    assert info_row.surface_code == INFORMATION_COLLECTION_PLAN_SURFACE
    assert info_row.status == "watch"
    assert info_row.reason_codes == (
        "information_collection_plan_watch",
        "pending_items_watch",
        "coverage_incomplete_watch",
    )
    assert report.reason_codes == (
        "information_collection_plan_watch",
        "pending_items_watch",
        "coverage_incomplete_watch",
        "operational_readiness_watch",
    )


def test_block_rollup_on_execution_boundary_and_missing_surfaces() -> None:
    report = _report(
        (
            _signal("manual_review_checklist"),
            _signal(
                "execution_boundary_guard",
                status="block",
                block_item_count=Decimal("1.000000"),
                coverage_score=Decimal("0.500000"),
            ),
        ),
    )

    assert report.report_status == "block"
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == ZERO
    assert report.block_count == Decimal("3.000000")
    assert report.total_block_item_count == Decimal("3.000000")
    assert tuple(row.surface_code for row in report.rows) == REQUIRED_OPERATIONAL_READINESS_SURFACES
    assert [row.status for row in report.rows] == ["pass", "block", "block", "block"]
    assert "execution_boundary_guard_block" in report.reason_codes
    assert "missing_team_capacity" in report.reason_codes
    assert "missing_information_collection_plan" in report.reason_codes
    assert report.reason_codes[-1] == "operational_readiness_block"


def test_strict_type_validation_rejects_non_decimal_and_subclasses() -> None:
    with pytest.raises(ValueError, match="coverage_score must be a Decimal"):
        ResearchOperationalReadinessSignal(
            surface_code="manual_review_checklist",
            status="pass",
            coverage_score=1,  # type: ignore[arg-type]
            pending_item_count=ZERO,
            block_item_count=ZERO,
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_operational_readiness_report(
            _complete_signals(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadSignal(ResearchOperationalReadinessSignal):
            pass

    with pytest.raises(FrozenInstanceError):
        _complete_signals()[0].status = "block"  # type: ignore[misc]


def test_public_leaks_are_rejected_for_inputs_reports_and_payload_dicts() -> None:
    forbidden_inputs = (
        "raw_candidate_abc",
        "candidate_id abc",
        "market_id abc",
        "market_slug abc",
        "question text",
        "source_ref abc",
        "source_url abc",
        "source_text abc",
        "https://example.invalid/path",
        "DSN abc",
        "table name",
        "token abc",
        "wallet abc",
        "auth abc",
        "order abc",
        "trade abc",
        "position abc",
        "buy abc",
        "sell abc",
        "recommendation abc",
    )
    for value in forbidden_inputs:
        with pytest.raises(ValueError, match="unsafe public"):
            _signal("manual_review_checklist", public_note=value)

    report = _report(_complete_signals())
    with pytest.raises(ValueError, match="unsafe public"):
        replace(report.rows[0], reason_codes=("market_id",))

    with pytest.raises(ValueError, match="unsafe public"):
        research_operational_readiness_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "market_id": "abc",
            },
        )

    with pytest.raises(ValueError, match="unsafe public"):
        research_operational_readiness_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "safe": "source_url abc",
            },
        )


def test_hard_flags_are_required_everywhere() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchOperationalReadinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        _signal("manual_review_checklist", report_only=False)  # type: ignore[call-arg]

    report = _report(_complete_signals())

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        research_operational_readiness_report_payload(
            {
                **report.payload,
                "report_only": False,
            },
        )


def test_output_is_deterministic_and_digest_is_tamper_evident() -> None:
    signals = _complete_signals()
    report = _report(signals)
    reordered_report = _report(tuple(reversed(signals)))

    assert reordered_report == report
    assert reordered_report.payload == report.payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    changed = replace(report.rows[0], public_note="Needs human follow up")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, rows=(changed, *report.rows[1:]))


def _assert_no_forbidden_public_surface(value: object) -> None:
    serialized = json.dumps(value, sort_keys=True).lower()
    forbidden = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    for fragment in forbidden:
        assert fragment not in serialized


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) in (int, float):
        raise AssertionError(f"non-Decimal numeric public value: {value!r}")
    if hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
            _assert_no_non_decimal_public_numbers(getattr(value, field_name))
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_non_decimal_public_numbers(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
