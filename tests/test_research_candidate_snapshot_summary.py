from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_candidate_snapshot_summary import (
    DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION,
    ResearchCandidateSnapshotSummaryConfig,
    ResearchCandidateSnapshotSummaryInput,
    ResearchCandidateSnapshotSummaryReport,
    ResearchCandidateSnapshotSummaryRow,
    build_research_candidate_snapshot_summary,
    research_candidate_snapshot_summary_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def test_builds_full_pass_snapshot_with_decimal_payload_strings() -> None:
    report = build_research_candidate_snapshot_summary(
        (
            _input("case-b"),
            _input("case-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )

    assert type(report) is ResearchCandidateSnapshotSummaryReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION
    )
    assert report.public_status == "pass"
    assert report.snapshot_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.average_queue_priority_score == Decimal("0.400000")
    assert report.average_evidence_package_quality_score == Decimal("0.900000")
    assert report.average_cost_threshold_score == Decimal("0.850000")
    assert report.average_team_capacity_score == Decimal("0.800000")
    assert report.total_missing_required_field_count == Decimal("0.000000")
    assert report.max_screening_priority_score == Decimal("0.250000")
    assert report.reason_codes == ("snapshot_pass",)
    assert tuple(row.snapshot_key for row in report.rows) == ("case-a", "case-b")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_candidate_snapshot_summary_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["public_status"] == "pass"
    assert payload["snapshot_count"] == "2.000000"
    assert payload["rows"][0]["event_type_route"] == "standard_event_review"
    assert payload["rows"][0]["screening_priority_score"] == "0.250000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)
    _assert_no_forbidden_public_terms(payload)


def test_missing_required_fields_watch_without_blocking_snapshot() -> None:
    report = build_research_candidate_snapshot_summary(
        (
            _input(
                "case-missing",
                event_type="deadline_event",
                missing_required_field_count=Decimal("1.000000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )

    assert report.public_status == "watch"
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.total_missing_required_field_count == Decimal("1.000000")
    assert report.rows[0].public_status == "watch"
    assert report.rows[0].event_type_route == "time_sensitive_review"
    assert report.rows[0].human_screening_bucket == "priority_screen"
    assert report.rows[0].reason_codes == ("missing_required_fields_watch",)
    assert report.reason_codes == ("missing_required_fields_watch",)


def test_risk_inputs_block_snapshot_for_human_rework() -> None:
    report = build_research_candidate_snapshot_summary(
        (
            _input("case-pass"),
            _input(
                "case-risk",
                evidence_package_quality_score=Decimal("0.300000"),
                cost_threshold_score=Decimal("0.200000"),
                team_capacity_score=Decimal("0.250000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )

    assert report.public_status == "block"
    assert report.block_count == Decimal("1.000000")
    assert tuple(row.public_status for row in report.rows) == ("block", "pass")
    assert report.rows[0].human_screening_bucket == "hold_for_rework"
    assert report.rows[0].reason_codes == (
        "evidence_package_quality_block",
        "cost_threshold_block",
        "team_capacity_block",
    )
    assert report.reason_codes == (
        "evidence_package_quality_block",
        "cost_threshold_block",
        "team_capacity_block",
        "snapshot_pass",
    )


def test_type_rejection_is_strict_and_decimal_only() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchCandidateSnapshotSummaryConfig(config_version="bad version")
    with pytest.raises(ValueError, match="queue_priority_score"):
        _input("case-a", queue_priority_score=1)
    with pytest.raises(ValueError, match="queue_priority_score"):
        _input("case-a", queue_priority_score=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="evidence_package_quality_score"):
        _input("case-a", evidence_package_quality_score="0.900000")
    with pytest.raises(ValueError, match="cost_threshold_score"):
        _input("case-a", cost_threshold_score=Decimal("0.85"))
    with pytest.raises(ValueError, match="team_capacity_score"):
        _input("case-a", team_capacity_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="missing_required_field_count"):
        _input("case-a", missing_required_field_count=Decimal("1.100000"))
    with pytest.raises(ValueError, match="event_type"):
        _input("case-a", event_type="unknown_event")
    with pytest.raises(ValueError, match="generated_at"):
        build_research_candidate_snapshot_summary(
            (_input("case-a"),),
            generated_at=datetime(2026, 7, 7, 12, 0),
            config=ResearchCandidateSnapshotSummaryConfig(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_candidate_snapshot_summary(
            (_input("case-a"),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
            config=ResearchCandidateSnapshotSummaryConfig(),
        )
    with pytest.raises(ValueError, match="public_status"):
        ResearchCandidateSnapshotSummaryRow(
            snapshot_key="case-a",
            queue_priority_score=Decimal("0.400000"),
            event_type="binary_event",
            event_type_route="standard_event_review",
            evidence_package_quality_score=Decimal("0.900000"),
            cost_threshold_score=Decimal("0.850000"),
            team_capacity_score=Decimal("0.800000"),
            missing_required_field_count=Decimal("0.000000"),
            screening_priority_score=Decimal("0.250000"),
            public_status="blocked",
            human_screening_bucket="hold_for_rework",
            reason_codes=("snapshot_pass",),
        )


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("input", "snapshot_key", "raw-candidate-123"),
        ("input", "snapshot_key", "candidate_id_123"),
        ("input", "snapshot_key", "market-abc"),
        ("input", "snapshot_key", "market_slug_abc"),
        ("payload", "market_id", "hidden"),
        ("payload", "market_slug", "hidden"),
        ("payload", "market_question", "Will this resolve?"),
        ("payload", "source_ref", "hidden"),
        ("payload", "source_url", "https://example.test/ref"),
        ("payload", "source_text", "copied private evidence"),
        ("payload", "dsn", "postgres://user:pass@host/db"),
        ("payload", "table", "private_table"),
        ("payload", "token", "secret-token"),
        ("payload", "wallet", "0xabc"),
        ("payload", "auth", "bearer"),
        ("payload", "order", "place order"),
        ("payload", "trade", "trade language"),
        ("payload", "position", "position language"),
        ("payload", "value", "buy sell recommendation"),
    ),
)
def test_leak_rejection_for_inputs_and_public_payload(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    if factory_name == "input":
        with pytest.raises(ValueError, match="unsafe public"):
            _input("case-a", **{field_name: field_value})
        return

    report = build_research_candidate_snapshot_summary(
        (_input("case-a"),),
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )
    tampered = dict(research_candidate_snapshot_summary_payload(report))
    tampered[field_name] = field_value
    with pytest.raises(ValueError, match="unsafe public"):
        research_candidate_snapshot_summary_payload(tampered)


def test_hard_flags_are_enforced_and_dataclasses_are_frozen() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input("case-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchCandidateSnapshotSummaryConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchCandidateSnapshotSummaryConfig(readonly=False)

    report = build_research_candidate_snapshot_summary(
        (_input("case-a"),),
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].public_status = "block"

    payload = research_candidate_snapshot_summary_payload(report)
    payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        research_candidate_snapshot_summary_payload(payload)


def test_output_is_deterministic_for_input_order_and_payload_serialization() -> None:
    rows = (
        _input("case-c", evidence_package_quality_score=Decimal("0.300000")),
        _input("case-a"),
        _input("case-b", missing_required_field_count=Decimal("1.000000")),
    )

    report_a = build_research_candidate_snapshot_summary(
        rows,
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )
    report_b = build_research_candidate_snapshot_summary(
        tuple(reversed(rows)),
        generated_at=GENERATED_AT,
        config=ResearchCandidateSnapshotSummaryConfig(),
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_candidate_snapshot_summary_payload(
        report_a,
    ) == research_candidate_snapshot_summary_payload(report_b)
    assert json.dumps(
        research_candidate_snapshot_summary_payload(report_a),
        sort_keys=True,
    ) == json.dumps(
        research_candidate_snapshot_summary_payload(report_b),
        sort_keys=True,
    )
    assert tuple(row.snapshot_key for row in report_a.rows) == (
        "case-c",
        "case-b",
        "case-a",
    )


def _input(item_key: str, **overrides: object) -> ResearchCandidateSnapshotSummaryInput:
    values = {
        "snapshot_key": item_key,
        "queue_priority_score": Decimal("0.400000"),
        "event_type": "binary_event",
        "evidence_package_quality_score": Decimal("0.900000"),
        "cost_threshold_score": Decimal("0.850000"),
        "team_capacity_score": Decimal("0.800000"),
        "missing_required_field_count": Decimal("0.000000"),
    }
    values.update(overrides)
    return ResearchCandidateSnapshotSummaryInput(**values)


def _decimal_values_are_strings(value: object) -> bool:
    if isinstance(value, dict):
        return all(_decimal_values_are_strings(item) for item in value.values())
    if isinstance(value, list):
        return all(_decimal_values_are_strings(item) for item in value)
    return not isinstance(value, Decimal) and not isinstance(value, float)


def _assert_no_forbidden_public_terms(payload: dict[str, object]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    for term in (
        "raw_candidate",
        "candidate_id",
        "candidate-",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
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
        "recommendation",
    ):
        assert term not in rendered
