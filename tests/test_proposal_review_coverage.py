import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tests.test_proposal_review_summary import proposal_for_source, review_record
from polymarket_alpha_lab.proposal_review import TradeProposalReviewRecord
from polymarket_alpha_lab.proposal_review_coverage import (
    TradeProposalReviewCoverageBucketRow,
    TradeProposalReviewCoverageConfig,
    TradeProposalReviewCoverageGateResult,
    TradeProposalReviewCoverageLog,
    TradeProposalReviewCoveragePacketRow,
    TradeProposalReviewCoverageReport,
    build_trade_proposal_review_coverage_report,
)


DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT = (
    "This is a report-only proposal-review coverage artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, strategy-promotion signal, or automatic order-placement "
    "authorization."
)

SOURCE_FINGERPRINT_FIELDS = (
    "source_proposal_packet_id",
    "source_proposal_generated_at",
    "source_proposal_config_version",
    "source_proposal_boundary_statement",
    "source_queue_boundary_statement",
    "source_proposal_only",
    "source_human_approval_required",
    "source_queue_item_id",
    "source_queue_rank",
    "source_manual_review_status",
    "source_packet_id",
    "source_paper_only",
    "condition_id",
    "token_id",
    "market_slug",
    "market_url",
    "question",
    "outcome_name",
    "strategy_type",
    "side",
    "intended_order_type",
    "executable_price_assumption",
    "maximum_size",
    "source_max_executable_size",
    "cost_adjusted_edge",
    "theoretical_edge",
    "fair_value_estimate",
    "model_probability",
    "confidence",
    "source_score",
    "market_score_total",
    "exposure_after_trade",
    "exit_rule",
    "thesis",
    "invalidating_conditions",
    "rule_text_hash",
    "resolution_source",
    "risk_tags",
    "reason_trade_could_be_wrong",
    "readiness_summary",
    "risk_summary",
    "evidence_summary",
    "why_in_queue",
    "primary_reason_code",
    "supporting_reason_codes",
    "review_focus",
    "evidence_scope",
    "history_status",
    "forecast_status",
    "history_gate_pass_count",
    "forecast_gate_pass_count",
    "history_gate_fail_count",
    "forecast_gate_fail_count",
    "risk_gate_passed",
    "hard_block_count",
    "blocking_reason_codes",
)


def packet(index: int, **overrides):
    values = {
        "market_slug": f"market-{index}",
        "strategy_type": "relative_value",
        "risk_tags": ("liquidity", "event-risk"),
    }
    values.update(overrides)
    return proposal_for_source(index, **values)


def coverage_report(proposals, records=(), **overrides):
    values = {
        "proposals": proposals,
        "records": records,
        "config": TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            min_proposal_packet_count=1,
            max_duplicate_reviewed_proposal_packet_count=10,
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_count=10,
        ),
        "generated_at": datetime(2026, 9, 7, 9, tzinfo=timezone(timedelta(hours=-4))),
    }
    values.update(overrides)
    return build_trade_proposal_review_coverage_report(**values)


def approved_record(source, minute: int = 0, **overrides):
    values = {
        "proposal": source,
        "recorded_at": datetime(2026, 9, 7, 12, tzinfo=UTC)
        + timedelta(minutes=minute),
    }
    values.update(overrides)
    return review_record(**values)


def rejected_record(
    source,
    minute: int = 0,
    reason_codes=("liquidity_exit_risk",),
    **overrides,
):
    values = {
        "proposal": source,
        "decision": "rejected",
        "review_reason_codes": reason_codes,
        "review_rationale": "Rejected after checking proposal-review coverage inputs.",
        "recorded_at": datetime(2026, 9, 7, 12, tzinfo=UTC)
        + timedelta(minutes=minute),
    }
    values.update(overrides)
    return review_record(**values)


def _json_ready(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _source_proposal_fingerprint_from_values(values: dict) -> str:
    raw = json.dumps(
        _json_ready({field_name: values[field_name] for field_name in SOURCE_FINGERPRINT_FIELDS}),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"source-proposal-{digest}"


def _review_record_id_from_values(values: dict) -> str:
    raw = json.dumps(
        _json_ready(
            {
                "review_config_version": values["review_config_version"],
                "recorded_at": values["recorded_at"],
                "source_proposal_packet_id": values["source_proposal_packet_id"],
                "source_proposal_fingerprint": values["source_proposal_fingerprint"],
                "decision": values["decision"],
                "reviewer_label": values["reviewer_label"],
                "review_rationale": values["review_rationale"],
                "review_reason_codes": values["review_reason_codes"],
                "human_attestation": values["human_attestation"],
            }
        ),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"review-{digest}"


def _consistent_review_record(record: TradeProposalReviewRecord, **overrides):
    values = {field.name: getattr(record, field.name) for field in fields(record)}
    values.update(overrides)
    values["source_proposal_fingerprint"] = _source_proposal_fingerprint_from_values(
        values
    )
    values["review_record_id"] = _review_record_id_from_values(values)
    return TradeProposalReviewRecord(**values)


def _gates_by_name(report):
    return {row.gate_name: row for row in report.gate_results}


def test_build_trade_proposal_review_coverage_report_counts_review_coverage():
    reviewed = packet(1, market_slug="reviewed-market")
    unreviewed = packet(2, market_slug="unreviewed-market")
    duplicate = packet(3, market_slug="duplicate-market")
    conflict = packet(4, market_slug="conflict-market")
    orphan_source = packet(5, market_slug="orphan-market")
    records = [
        approved_record(reviewed, minute=1),
        approved_record(duplicate, minute=2),
        rejected_record(duplicate, minute=3),
        approved_record(conflict, minute=4),
        rejected_record(conflict, minute=5),
        rejected_record(orphan_source, minute=6),
    ]

    report = coverage_report([conflict, unreviewed, reviewed, duplicate], records)

    assert report.generated_at == datetime(2026, 9, 7, 13, tzinfo=UTC)
    assert report.config_version == "coverage-v1"
    assert report.report_only is True
    assert report.proposal_packet_count == 4
    assert report.review_record_count == 6
    assert report.reviewed_proposal_packet_count == 3
    assert report.unreviewed_proposal_packet_count == 1
    assert report.duplicate_reviewed_proposal_packet_count == 2
    assert report.conflicting_decision_proposal_packet_count == 2
    assert report.orphan_review_record_count == 1
    assert report.approved_decision_count == 3
    assert report.rejected_decision_count == 3
    assert report.review_coverage_ratio == Decimal("0.7500")
    assert report.unreviewed_proposal_packet_ratio == Decimal("0.2500")
    assert report.duplicate_reviewed_proposal_packet_ratio == Decimal("0.5000")
    assert report.conflicting_decision_proposal_packet_ratio == Decimal("0.5000")
    assert report.orphan_review_record_ratio == Decimal("0.1667")
    assert report.first_proposal_generated_at == datetime(2026, 9, 3, 12, 1, tzinfo=UTC)
    assert report.last_proposal_generated_at == datetime(2026, 9, 3, 12, 4, tzinfo=UTC)
    assert report.first_recorded_at == datetime(2026, 9, 7, 12, 1, tzinfo=UTC)
    assert report.last_recorded_at == datetime(2026, 9, 7, 12, 6, tzinfo=UTC)
    assert report.status == "incomplete_review_coverage"
    assert tuple(row.gate_name for row in report.gate_results) == (
        "data_integrity",
        "proposal_sample",
        "review_coverage",
        "duplicate_review_volume",
        "decision_consistency",
    )
    assert tuple(row.bucket_name for row in report.bucket_rows) == (
        "conflicting_decision",
        "duplicate_reviewed",
        "orphan_review_record",
        "reviewed",
        "unreviewed",
    )
    assert tuple(
        (
            row.bucket_name,
            row.proposal_packet_count,
            row.review_record_count,
            row.coverage_ratio,
        )
        for row in report.bucket_rows
    ) == (
        ("conflicting_decision", 2, 4, Decimal("0.5000")),
        ("duplicate_reviewed", 2, 4, Decimal("0.5000")),
        ("orphan_review_record", 0, 1, Decimal("0.1667")),
        ("reviewed", 1, 1, Decimal("0.2500")),
        ("unreviewed", 1, 0, Decimal("0.2500")),
    )
    assert {row.coverage_status for row in report.packet_rows} == {
        "reviewed",
        "unreviewed",
        "conflicting",
        "orphan",
    }
    assert tuple(row.coverage_status for row in report.packet_rows) == (
        "conflicting",
        "conflicting",
        "orphan",
        "reviewed",
        "unreviewed",
    )
    rows_by_id = {row.proposal_packet_id: row for row in report.packet_rows}
    assert rows_by_id[reviewed.proposal_packet_id].coverage_status == "reviewed"
    assert rows_by_id[reviewed.proposal_packet_id].review_record_count == 1
    assert rows_by_id[unreviewed.proposal_packet_id].coverage_status == "unreviewed"
    assert rows_by_id[unreviewed.proposal_packet_id].review_record_count == 0
    assert rows_by_id[duplicate.proposal_packet_id].coverage_status == "conflicting"
    assert rows_by_id[conflict.proposal_packet_id].coverage_status == "conflicting"
    assert rows_by_id[orphan_source.proposal_packet_id].coverage_status == "orphan"


def test_trade_proposal_review_coverage_statuses_cover_samples_and_thresholds():
    empty = coverage_report([])
    assert empty.proposal_packet_count == 0
    assert empty.review_record_count == 0
    assert empty.review_coverage_ratio is None
    assert empty.unreviewed_proposal_packet_ratio is None
    assert empty.duplicate_reviewed_proposal_packet_ratio is None
    assert empty.conflicting_decision_proposal_packet_ratio is None
    assert empty.orphan_review_record_ratio is None
    assert empty.first_proposal_generated_at is None
    assert empty.last_proposal_generated_at is None
    assert empty.first_recorded_at is None
    assert empty.last_recorded_at is None
    assert empty.bucket_rows == ()
    assert empty.packet_rows == ()
    assert tuple(row.gate_name for row in empty.gate_results) == (
        "data_integrity",
        "proposal_sample",
        "review_coverage",
        "duplicate_review_volume",
        "decision_consistency",
    )
    assert empty.status == "incomplete_proposal_sample"
    empty_gates = _gates_by_name(empty)
    assert empty_gates["data_integrity"].status == "pass"
    assert empty_gates["data_integrity"].observed_value is None
    assert empty_gates["proposal_sample"].status == "fail"
    assert empty_gates["proposal_sample"].observed_value == 0
    assert empty_gates["proposal_sample"].threshold == 1
    assert empty_gates["review_coverage"].status == "fail"
    assert empty_gates["review_coverage"].observed_value is None
    assert empty_gates["review_coverage"].threshold == Decimal("1.0000")
    assert empty_gates["duplicate_review_volume"].status == "pass"
    assert empty_gates["decision_consistency"].status == "pass"

    unreviewed = coverage_report([packet(10)])
    assert unreviewed.reviewed_proposal_packet_count == 0
    assert unreviewed.unreviewed_proposal_packet_count == 1
    assert unreviewed.review_coverage_ratio == Decimal("0.0000")
    assert unreviewed.status == "incomplete_review_coverage"

    below_minimum_sample_source = packet(51)
    below_minimum_sample = coverage_report(
        [below_minimum_sample_source],
        [approved_record(below_minimum_sample_source, minute=10)],
        config=TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            min_proposal_packet_count=2,
            max_duplicate_reviewed_proposal_packet_count=10,
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_count=10,
        ),
    )
    assert below_minimum_sample.review_coverage_ratio == Decimal("1.0000")
    assert below_minimum_sample.status == "inconsistent_review_coverage"
    below_minimum_gates = _gates_by_name(below_minimum_sample)
    assert below_minimum_gates["proposal_sample"].status == "fail"
    assert below_minimum_gates["proposal_sample"].observed_value == 1
    assert below_minimum_gates["proposal_sample"].threshold == 2
    assert below_minimum_gates["review_coverage"].status == "pass"

    duplicate_source = packet(11)
    duplicate = coverage_report(
        [
            duplicate_source,
        ],
        [
            approved_record(duplicate_source, minute=11),
            approved_record(duplicate_source, minute=12),
        ],
        config=TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            max_duplicate_reviewed_proposal_packet_count=0,
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_count=10,
        ),
    )
    assert duplicate.duplicate_reviewed_proposal_packet_count == 1
    assert duplicate.status == "inconsistent_review_coverage"
    duplicate_row = duplicate.packet_rows[0]
    assert duplicate_row.coverage_status == "duplicate_reviewed"
    assert duplicate_row.review_record_count == 2
    assert duplicate_row.approved_decision_count == 2
    assert duplicate_row.rejected_decision_count == 0
    assert len(duplicate_row.review_record_ids) == 2
    assert _gates_by_name(duplicate)["duplicate_review_volume"].status == "fail"

    conflict_source = packet(12)
    conflict = coverage_report(
        [conflict_source],
        [
            approved_record(conflict_source, minute=13),
            rejected_record(conflict_source, minute=14),
        ],
        config=TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            max_duplicate_reviewed_proposal_packet_count=10,
            max_conflicting_decision_proposal_packet_count=0,
            max_orphan_review_record_count=10,
        ),
    )
    assert conflict.conflicting_decision_proposal_packet_count == 1
    assert conflict.status == "inconsistent_review_coverage"

    reviewed_source = packet(13)
    orphan_source = packet(14)
    orphan = coverage_report(
        [reviewed_source],
        [
            approved_record(reviewed_source, minute=15),
            rejected_record(orphan_source, minute=16),
        ],
        config=TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            max_duplicate_reviewed_proposal_packet_count=10,
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_count=0,
        ),
    )
    assert orphan.orphan_review_record_count == 1
    assert orphan.status == "inconsistent_review_coverage"

    ready_source = packet(15)
    ready_orphan_source = packet(16)
    relaxed = coverage_report(
        [ready_source],
        [
            approved_record(ready_source, minute=17),
            rejected_record(ready_source, minute=18),
            rejected_record(ready_orphan_source, minute=19),
        ],
        config=TradeProposalReviewCoverageConfig(
            config_version="coverage-v1",
            max_duplicate_reviewed_proposal_packet_ratio=Decimal("1.0000"),
            max_duplicate_reviewed_proposal_packet_count=10,
            max_conflicting_decision_proposal_packet_ratio=Decimal("1.0000"),
            max_conflicting_decision_proposal_packet_count=10,
            max_orphan_review_record_ratio=Decimal("1.0000"),
            max_orphan_review_record_count=10,
        ),
    )
    assert relaxed.reviewed_proposal_packet_count == 1
    assert relaxed.unreviewed_proposal_packet_count == 0
    assert relaxed.status == "proposal_review_coverage_ready"
    assert all(row.status == "pass" for row in relaxed.gate_results)


def test_trade_proposal_review_coverage_reports_orphan_only_review_evidence():
    orphan_source = packet(17, market_slug="orphan-only-market")
    orphan_record = rejected_record(orphan_source, minute=20)

    report = coverage_report([], [orphan_record])

    assert report.proposal_packet_count == 0
    assert report.review_record_count == 1
    assert report.reviewed_proposal_packet_count == 0
    assert report.unreviewed_proposal_packet_count == 0
    assert report.orphan_review_record_count == 1
    assert report.review_coverage_ratio is None
    assert report.unreviewed_proposal_packet_ratio is None
    assert report.duplicate_reviewed_proposal_packet_ratio is None
    assert report.conflicting_decision_proposal_packet_ratio is None
    assert report.orphan_review_record_ratio == Decimal("1.0000")
    assert report.first_proposal_generated_at is None
    assert report.last_proposal_generated_at is None
    assert report.first_recorded_at == orphan_record.recorded_at
    assert report.last_recorded_at == orphan_record.recorded_at
    assert report.status == "incomplete_proposal_sample"
    assert tuple(row.bucket_name for row in report.bucket_rows) == (
        "conflicting_decision",
        "duplicate_reviewed",
        "orphan_review_record",
        "reviewed",
        "unreviewed",
    )
    assert report.bucket_rows[2].review_record_count == 1
    assert len(report.packet_rows) == 1
    orphan_row = report.packet_rows[0]
    assert orphan_row.coverage_status == "orphan"
    assert orphan_row.proposal_packet_id == orphan_source.proposal_packet_id
    assert orphan_row.source_proposal_fingerprint == (
        orphan_record.source_proposal_fingerprint
    )
    assert orphan_row.review_record_ids == (orphan_record.review_record_id,)


def test_trade_proposal_review_coverage_packet_rows_are_deterministically_ordered():
    reviewed_z = packet(20, market_slug="z-reviewed-market")
    reviewed_a = packet(21, market_slug="a-reviewed-market")
    unreviewed = packet(22, market_slug="unreviewed-market")
    conflict = packet(23, market_slug="conflict-market")
    orphan_source = packet(24, market_slug="orphan-market")

    report = coverage_report(
        [unreviewed, reviewed_z, conflict, reviewed_a],
        [
            rejected_record(orphan_source, minute=24),
            approved_record(reviewed_z, minute=21),
            approved_record(conflict, minute=22),
            approved_record(reviewed_a, minute=20),
            rejected_record(conflict, minute=23),
        ],
    )

    keys = tuple(
        (
            row.coverage_status,
            row.proposal_packet_id,
            row.source_proposal_fingerprint or "",
        )
        for row in report.packet_rows
    )
    assert keys == tuple(sorted(keys))
    assert tuple(row.proposal_packet_id for row in report.packet_rows) == tuple(
        row.proposal_packet_id
        for row in sorted(
            report.packet_rows,
            key=lambda row: (
                row.coverage_status,
                row.proposal_packet_id,
                row.source_proposal_fingerprint or "",
            ),
        )
    )


def test_trade_proposal_review_coverage_groups_orphans_by_packet_id_and_fingerprint():
    supplied = packet(25, market_slug="supplied-market")
    orphan_a = rejected_record(packet(26, market_slug="orphan-alpha"), minute=25)
    orphan_b_source = packet(27, market_slug="orphan-beta")
    orphan_b = _consistent_review_record(
        rejected_record(orphan_b_source, minute=26),
        source_proposal_packet_id=orphan_a.source_proposal_packet_id,
    )

    assert orphan_a.source_proposal_packet_id == orphan_b.source_proposal_packet_id
    assert orphan_a.source_proposal_fingerprint != orphan_b.source_proposal_fingerprint

    report = coverage_report([supplied], [orphan_b, orphan_a])
    orphan_rows = tuple(
        row for row in report.packet_rows if row.coverage_status == "orphan"
    )

    assert len(orphan_rows) == 2
    assert tuple(row.proposal_packet_id for row in orphan_rows) == (
        orphan_a.source_proposal_packet_id,
        orphan_a.source_proposal_packet_id,
    )
    assert tuple(row.source_proposal_fingerprint for row in orphan_rows) == tuple(
        sorted(
            (
                orphan_a.source_proposal_fingerprint,
                orphan_b.source_proposal_fingerprint,
            )
        )
    )
    assert all(row.review_record_count == 1 for row in orphan_rows)


def test_trade_proposal_review_coverage_rejects_bad_inputs_and_duplicates():
    with pytest.raises(ValueError, match="proposals"):
        coverage_report(object(), [])
    with pytest.raises(ValueError, match="proposals"):
        coverage_report("proposals", [])
    with pytest.raises(ValueError, match="proposals"):
        coverage_report(b"proposals", [])
    with pytest.raises(ValueError, match="TradeProposalPacket"):
        coverage_report([object()], [])
    with pytest.raises(ValueError, match="records"):
        coverage_report([], object())
    with pytest.raises(ValueError, match="records"):
        coverage_report([], "records")
    with pytest.raises(ValueError, match="records"):
        coverage_report([], b"records")
    with pytest.raises(ValueError, match="TradeProposalReviewRecord"):
        coverage_report([], [object()])
    with pytest.raises(ValueError, match="config"):
        coverage_report([], [], config=object())
    with pytest.raises(ValueError, match="generated_at"):
        coverage_report([], [], generated_at="2026-09-07")

    duplicate_proposal = packet(30)
    with pytest.raises(ValueError, match="duplicate proposal_packet_id"):
        coverage_report([duplicate_proposal, duplicate_proposal], [])

    record = approved_record(duplicate_proposal, minute=30)
    with pytest.raises(ValueError, match="duplicate review_record_id"):
        coverage_report([duplicate_proposal], [record, record])


def test_trade_proposal_review_coverage_revalidates_mutated_artifacts():
    bad_proposal = packet(31)
    object.__setattr__(bad_proposal, "maximum_size", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|maximum_size"):
        coverage_report([bad_proposal], [])

    bad_record = approved_record(packet(32), minute=31)
    object.__setattr__(bad_record, "maximum_size", Decimal("NaN"))
    with pytest.raises(ValueError, match="finite|maximum_size"):
        coverage_report([], [bad_record])

    stale_record = approved_record(packet(33), minute=32)
    object.__setattr__(stale_record, "source_proposal_fingerprint", "stale")
    with pytest.raises(ValueError, match="source_proposal_fingerprint"):
        coverage_report([], [stale_record])


def test_trade_proposal_review_coverage_detects_stale_source_fingerprint_mismatch():
    source = packet(34, market_slug="original-market")
    record = approved_record(source, minute=33)
    object.__setattr__(source, "market_slug", "renamed-market")

    with pytest.raises(ValueError, match="source_proposal_fingerprint|stale"):
        coverage_report([source], [record])


def test_trade_proposal_review_coverage_detects_source_snapshot_field_mismatch():
    source = packet(53, market_slug="original-market")
    record = _consistent_review_record(
        approved_record(source, minute=53),
        market_slug="renamed-market",
    )

    with pytest.raises(ValueError, match="source snapshot"):
        coverage_report([source], [record])


def test_trade_proposal_review_coverage_dataclasses_are_frozen_and_validate_invariants():
    source = packet(35)
    report = coverage_report([source], [approved_record(source, minute=34)])
    config = TradeProposalReviewCoverageConfig(config_version="coverage-v1")
    gate_row = report.gate_results[0]
    bucket_row = report.bucket_rows[0]
    packet_row = report.packet_rows[0]

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        gate_row.status = "other"
    with pytest.raises(FrozenInstanceError):
        bucket_row.bucket_name = "other"
    with pytest.raises(FrozenInstanceError):
        packet_row.coverage_status = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "other"

    with pytest.raises(ValueError, match="min_proposal_packet_count"):
        replace(config, min_proposal_packet_count=True)
    with pytest.raises(ValueError, match="max_duplicate_reviewed_proposal_packet_ratio"):
        replace(
            config,
            max_duplicate_reviewed_proposal_packet_ratio=Decimal("1.0001"),
        )
    with pytest.raises(ValueError, match="max_conflicting_decision_proposal_packet_ratio"):
        replace(
            config,
            max_conflicting_decision_proposal_packet_ratio=Decimal("-0.0001"),
        )
    with pytest.raises(ValueError, match="max_orphan_review_record_ratio"):
        replace(config, max_orphan_review_record_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="max_orphan_review_record_count"):
        replace(config, max_orphan_review_record_count=-1)
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(config, boundary_statement="coverage report")

    with pytest.raises(ValueError, match="gate_name"):
        replace(gate_row, gate_name="approval")
    with pytest.raises(ValueError, match="status"):
        replace(gate_row, status="ready")
    with pytest.raises(ValueError, match="message"):
        replace(gate_row, message=" ")
    with pytest.raises(ValueError, match="observed_value"):
        replace(gate_row, observed_value=0.5)
    with pytest.raises(ValueError, match="threshold"):
        replace(gate_row, threshold=True)

    with pytest.raises(ValueError, match="bucket_name"):
        replace(bucket_row, bucket_name="approval_queue")
    with pytest.raises(ValueError, match="proposal_packet_count"):
        replace(bucket_row, proposal_packet_count=-1)
    with pytest.raises(ValueError, match="review_record_count"):
        replace(bucket_row, review_record_count=-1)
    with pytest.raises(ValueError, match="coverage_ratio"):
        replace(bucket_row, coverage_ratio=Decimal("1.0001"))

    with pytest.raises(ValueError, match="coverage_status"):
        replace(packet_row, coverage_status="duplicate")
    with pytest.raises(ValueError, match="review_record_count"):
        replace(packet_row, review_record_count=-1)
    with pytest.raises(ValueError, match="approved_decision_count"):
        replace(packet_row, approved_decision_count=2)
    with pytest.raises(ValueError, match="first_recorded_at"):
        replace(
            packet_row,
            first_recorded_at=packet_row.last_recorded_at + timedelta(seconds=1),
        )
    multi_id_source = packet(42)
    multi_id_row = coverage_report(
        [multi_id_source],
        [
            approved_record(multi_id_source, minute=42),
            approved_record(multi_id_source, minute=43),
        ],
    ).packet_rows[0]
    with pytest.raises(ValueError, match="review_record_ids"):
        replace(
            multi_id_row,
            review_record_ids=tuple(reversed(multi_id_row.review_record_ids)),
        )
    with pytest.raises(ValueError, match="review_record_ids"):
        replace(packet_row, review_record_ids=())
    with pytest.raises(ValueError, match="review_record_ids"):
        replace(
            multi_id_row,
            review_record_ids=(multi_id_row.review_record_ids[0],)
            * len(multi_id_row.review_record_ids),
        )

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="proposal_packet_count"):
        replace(report, proposal_packet_count=2)
    with pytest.raises(ValueError, match="review_record_count"):
        replace(report, review_record_count=2)
    with pytest.raises(ValueError, match="review_coverage_ratio"):
        replace(report, review_coverage_ratio=Decimal("0.5000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="approved")
    with pytest.raises(ValueError, match="gate_results"):
        replace(report, gate_results=tuple(reversed(report.gate_results)))
    with pytest.raises(ValueError, match="bucket_rows"):
        replace(report, bucket_rows=tuple(reversed(report.bucket_rows)))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="coverage report")

    multi_row_report = coverage_report([source, packet(36)], [approved_record(source)])
    with pytest.raises(ValueError, match="packet_rows"):
        replace(
            multi_row_report,
            packet_rows=tuple(reversed(multi_row_report.packet_rows)),
        )


def test_trade_proposal_review_coverage_boundary_statement_contract():
    config = TradeProposalReviewCoverageConfig(config_version="coverage-v1")
    assert config.boundary_statement == DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT

    for boundary_statement in (
        "This is a report-only proposal-review coverage artifact.",
        "This is a report-only proposal-review coverage artifact, not an approval workflow.",
        (
            "This is a report-only proposal-review coverage artifact, not an approval "
            "workflow, trade instruction, order instruction, broker request, order "
            "request."
        ),
    ):
        with pytest.raises(ValueError, match="boundary_statement"):
            TradeProposalReviewCoverageConfig(
                config_version="coverage-v1",
                boundary_statement=boundary_statement,
            )


def test_trade_proposal_review_coverage_log_appends_jsonl_report(tmp_path):
    reviewed = packet(37)
    unreviewed = packet(38)
    report = coverage_report(
        [reviewed, unreviewed],
        [approved_record(reviewed, minute=37)],
    )
    log = TradeProposalReviewCoverageLog(path=tmp_path / "proposal-review-coverage.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["generated_at"] == "2026-09-07T13:00:00+00:00"
    assert stored["config_version"] == "coverage-v1"
    assert stored["report_only"] is True
    assert stored["proposal_packet_count"] == 2
    assert stored["review_record_count"] == 1
    assert stored["reviewed_proposal_packet_count"] == 1
    assert stored["unreviewed_proposal_packet_count"] == 1
    assert stored["review_coverage_ratio"] == "0.5000"
    assert stored["unreviewed_proposal_packet_ratio"] == "0.5000"
    assert stored["orphan_review_record_ratio"] == "0.0000"
    assert stored["status"] == "incomplete_review_coverage"
    assert [row["gate_name"] for row in stored["gate_results"]] == [
        "data_integrity",
        "proposal_sample",
        "review_coverage",
        "duplicate_review_volume",
        "decision_consistency",
    ]
    assert [row["bucket_name"] for row in stored["bucket_rows"]] == [
        "conflicting_decision",
        "duplicate_reviewed",
        "orphan_review_record",
        "reviewed",
        "unreviewed",
    ]
    assert [row["coverage_status"] for row in stored["packet_rows"]] == [
        "reviewed",
        "unreviewed",
    ]
    assert isinstance(stored["packet_rows"][0]["review_record_ids"], list)


def test_trade_proposal_review_coverage_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    source = packet(39)
    report = coverage_report([source], [approved_record(source, minute=38)])
    log = TradeProposalReviewCoverageLog(
        path=str(tmp_path / "nested" / "proposal-review-coverage.jsonl"),
    )

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["proposal_packet_count"] == 1
    assert json.loads(lines[1])["proposal_packet_count"] == 1


def test_trade_proposal_review_coverage_log_rejects_invalid_paths_and_inputs(tmp_path):
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewCoverageLog(path=object())
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewCoverageLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        TradeProposalReviewCoverageLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        TradeProposalReviewCoverageLog(path=existing_file / "coverage.jsonl")

    path = tmp_path / "proposal-review-coverage.jsonl"
    log = TradeProposalReviewCoverageLog(path=path)
    with pytest.raises(ValueError, match="TradeProposalReviewCoverageReport"):
        log.append(object())
    assert not path.exists()


def test_trade_proposal_review_coverage_log_preserves_existing_file_when_validation_fails(
    tmp_path,
):
    source = packet(40)
    report = coverage_report([source], [approved_record(source, minute=39)])
    nested_gate_row = report.gate_results[0]
    object.__setattr__(nested_gate_row, "observed_value", Decimal("NaN"))
    path = tmp_path / "proposal-review-coverage.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = TradeProposalReviewCoverageLog(path=path)

    with pytest.raises(ValueError, match="finite|observed_value"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_trade_proposal_review_coverage_log_rejects_inconsistent_report_rows_before_open(
    tmp_path,
):
    source = packet(52)
    report = coverage_report([source], [approved_record(source, minute=41)])

    with pytest.raises(ValueError, match="bucket_rows"):
        replace(report, bucket_rows=())

    object.__setattr__(report, "bucket_rows", ())
    log = TradeProposalReviewCoverageLog(path=tmp_path / "proposal-review-coverage.jsonl")
    with pytest.raises(ValueError, match="bucket_rows"):
        log.append(report)

    assert not log.path.exists()


def test_trade_proposal_review_coverage_report_rejects_mutated_packet_row_groups():
    first_source = packet(54)
    second_source = packet(55)
    report = coverage_report(
        [first_source, second_source],
        [
            approved_record(first_source, minute=54),
            approved_record(second_source, minute=55),
        ],
    )
    first_row, second_row = report.packet_rows

    with pytest.raises(ValueError, match="last_proposal_generated_at"):
        replace(
            report,
            packet_rows=(
                replace(
                    first_row,
                    last_proposal_generated_at=(
                        first_row.last_proposal_generated_at + timedelta(days=1)
                    ),
                ),
                second_row,
            ),
        )

    with pytest.raises(ValueError, match="proposal_packet_id"):
        replace(
            report,
            packet_rows=(
                first_row,
                replace(
                    second_row,
                    proposal_packet_id=first_row.proposal_packet_id,
                    source_proposal_fingerprint=first_row.source_proposal_fingerprint,
                ),
            ),
        )

    orphan_source = packet(56)
    first_orphan_record = approved_record(orphan_source, minute=56)
    second_orphan_record = approved_record(orphan_source, minute=57)
    orphan_report = coverage_report(
        [],
        [first_orphan_record, second_orphan_record],
    )
    orphan_row = orphan_report.packet_rows[0]

    with pytest.raises(ValueError, match="orphan"):
        replace(
            orphan_report,
            packet_rows=(
                replace(
                    orphan_row,
                    review_record_count=1,
                    approved_decision_count=1,
                    first_recorded_at=first_orphan_record.recorded_at,
                    last_recorded_at=first_orphan_record.recorded_at,
                    review_record_ids=(first_orphan_record.review_record_id,),
                ),
                replace(
                    orphan_row,
                    review_record_count=1,
                    approved_decision_count=1,
                    first_recorded_at=second_orphan_record.recorded_at,
                    last_recorded_at=second_orphan_record.recorded_at,
                    review_record_ids=(second_orphan_record.review_record_id,),
                ),
            ),
        )


def test_trade_proposal_review_coverage_log_rejects_mutated_packet_row_ids_before_open(
    tmp_path,
):
    source = packet(57)
    report = coverage_report([source], [approved_record(source, minute=58)])
    object.__setattr__(report.packet_rows[0], "review_record_ids", ())
    log = TradeProposalReviewCoverageLog(path=tmp_path / "proposal-review-coverage.jsonl")

    with pytest.raises(ValueError, match="review_record_ids"):
        log.append(report)

    assert not log.path.exists()


def test_trade_proposal_review_coverage_log_rejects_non_finite_decimal_before_open(
    tmp_path,
):
    source = packet(41)
    report = coverage_report([source], [approved_record(source, minute=40)])
    object.__setattr__(report, "review_coverage_ratio", Decimal("NaN"))
    log = TradeProposalReviewCoverageLog(path=tmp_path / "proposal-review-coverage.jsonl")

    with pytest.raises(ValueError, match="finite|review_coverage_ratio"):
        log.append(report)

    assert not log.path.exists()


def test_trade_proposal_review_coverage_public_dataclasses_reject_impossible_rows():
    with pytest.raises(ValueError, match="bucket_name"):
        TradeProposalReviewCoverageBucketRow(
            bucket_name="approval_queue",
            proposal_packet_count=1,
            review_record_count=1,
            coverage_ratio=Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="review_record_count"):
        TradeProposalReviewCoveragePacketRow(
            coverage_status="reviewed",
            proposal_packet_id="proposal-row",
            source_proposal_fingerprint="source-proposal-row",
            first_proposal_generated_at=datetime(2026, 9, 7, 12, tzinfo=UTC),
            last_proposal_generated_at=datetime(2026, 9, 7, 12, tzinfo=UTC),
            first_recorded_at=datetime(2026, 9, 7, 12, tzinfo=UTC),
            last_recorded_at=datetime(2026, 9, 7, 12, tzinfo=UTC),
            review_record_count=0,
            approved_decision_count=1,
            rejected_decision_count=0,
            market_slug="row-market",
            strategy_type="relative_value",
            risk_tags=("liquidity",),
            review_record_ids=("review-row",),
        )
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalReviewCoverageGateResult(
            gate_name="approval_queue",
            status="pass",
            message="Gate passed.",
            observed_value=1,
            threshold=1,
        )
    with pytest.raises(ValueError, match="packet_rows"):
        TradeProposalReviewCoverageReport(
            generated_at=datetime(2026, 9, 7, 13, tzinfo=UTC),
            config_version="coverage-v1",
            report_only=True,
            boundary_statement=DEFAULT_REVIEW_COVERAGE_BOUNDARY_STATEMENT,
            proposal_packet_count=0,
            review_record_count=0,
            reviewed_proposal_packet_count=0,
            unreviewed_proposal_packet_count=0,
            duplicate_reviewed_proposal_packet_count=0,
            conflicting_decision_proposal_packet_count=0,
            orphan_review_record_count=0,
            approved_decision_count=0,
            rejected_decision_count=0,
            review_coverage_ratio=None,
            unreviewed_proposal_packet_ratio=None,
            duplicate_reviewed_proposal_packet_ratio=None,
            conflicting_decision_proposal_packet_ratio=None,
            orphan_review_record_ratio=None,
            first_proposal_generated_at=None,
            last_proposal_generated_at=None,
            first_recorded_at=None,
            last_recorded_at=None,
            status="incomplete_proposal_sample",
            gate_results=(),
            bucket_rows=(),
            packet_rows=(
                TradeProposalReviewCoveragePacketRow(
                    coverage_status="orphan",
                    proposal_packet_id="proposal-row",
                    source_proposal_fingerprint="source-proposal-row",
                    first_proposal_generated_at=None,
                    last_proposal_generated_at=None,
                    first_recorded_at=datetime(2026, 9, 7, 12, tzinfo=UTC),
                    last_recorded_at=datetime(2026, 9, 7, 12, tzinfo=UTC),
                    review_record_count=1,
                    approved_decision_count=0,
                    rejected_decision_count=1,
                    market_slug="row-market",
                    strategy_type="relative_value",
                    risk_tags=("liquidity",),
                    review_record_ids=("review-row",),
                ),
            ),
        )
