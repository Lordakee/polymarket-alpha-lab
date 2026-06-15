import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow,
)


TREND_BATCH_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend batch "
    "artifact over supplied proposal evidence comparison history batch health trend "
    "reports, not an approval workflow, proposal approval, approved-proposal "
    "selector, latest-decision selector, decision-resolution process, investment "
    "ranking, trade recommendation, strategy-promotion signal, trade instruction, "
    "order instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution signal, "
    "credential workflow, external-history loader, JSONL reader, scraping workflow, "
    "outcome loader, settlement review, reconciliation process, compliance review, "
    "geographic access analysis, realized false-positive analysis, profitability "
    "analysis, or automatic order-placement authorization."
)

TREND_BATCH_HEALTH_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend batch health "
    "artifact over supplied proposal evidence comparison history batch health trend batch "
    "reports, not an approval workflow, proposal approval, approved-proposal "
    "selector, latest-decision selector, decision-resolution process, investment "
    "ranking, trade recommendation, strategy-promotion signal, trade instruction, "
    "order instruction, broker request, order request, account action, account "
    "authentication, private-key handling, wallet signature, live-execution signal, "
    "credential workflow, external-history loader, JSONL reader, scraping workflow, "
    "outcome loader, settlement review, reconciliation process, compliance review, "
    "geographic access analysis, realized false-positive analysis, profitability "
    "analysis, or automatic order-placement authorization."
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(Decimal("0.0001"))


def _health_rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def trend_batch_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
    index: int = 1,
    generated_at: datetime | None = None,
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport:
    generated_at = generated_at or datetime(2026, 9, 16, 12, index, tzinfo=UTC)
    trend_batch_count = 2
    status_counts = {
        "duplicate_fingerprint_batch_health_trend": 0,
        "duplicate_generated_at_batch_health_trend": 0,
        "incomplete_batch_health_trend": 0,
        "proposal_evidence_comparison_history_batch_health_trend_ready": 2,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "incomplete_batch_health_trend_batch":
        status_counts["incomplete_batch_health_trend"] = 1
        status_counts["proposal_evidence_comparison_history_batch_health_trend_ready"] = 1
    elif status == "duplicate_generated_at_batch_health_trend_batch":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health_trend_batch":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_trend_batch_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(
        trend_batch_count
        - status_counts["proposal_evidence_comparison_history_batch_health_trend_ready"],
        trend_batch_count,
    )
    duplicate_generated_at_ratio = _ratio(duplicate_generated_at_count, trend_batch_count)
    duplicate_fingerprint_ratio = _ratio(duplicate_fingerprint_count, trend_batch_count)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport(
        generated_at=generated_at,
        config_version="batch-health-trend-batch-v1",
        report_only=True,
        boundary_statement=TREND_BATCH_BOUNDARY,
        trend_report_count=trend_batch_count,
        ready_trend_report_count=status_counts[
            "proposal_evidence_comparison_history_batch_health_trend_ready"
        ],
        incomplete_trend_report_count=status_counts["incomplete_batch_health_trend"],
        duplicate_generated_at_trend_report_count=status_counts[
            "duplicate_generated_at_batch_health_trend"
        ],
        duplicate_fingerprint_trend_report_count=status_counts[
            "duplicate_fingerprint_batch_health_trend"
        ],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_trend_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_trend_generated_at=generated_at,
        last_trend_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateResult(
                "trend_sample",
                "pass",
                "trend_sample checked",
                trend_batch_count,
                1,
            ),
            _health_rate_gate("incomplete_trend_rate", incomplete_ratio),
            _health_rate_gate("duplicate_generated_at_rate", duplicate_generated_at_ratio),
            _health_rate_gate("duplicate_fingerprint_rate", duplicate_fingerprint_ratio),
        ),
        status_rows=tuple(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
                trend_status,
                trend_count,
                _ratio(trend_count, trend_batch_count),
            )
            for trend_status, trend_count in status_counts.items()
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchConfigVersionSummary(
                "batch-health-trend-v1",
                trend_batch_count,
            ),
        ),
        gate_status_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "batch_health_sample",
                "pass",
                trend_batch_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "duplicate_fingerprint_rate",
                "pass" if duplicate_fingerprint_count == 0 else "fail",
                trend_batch_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "duplicate_generated_at_rate",
                "pass" if duplicate_generated_at_count == 0 else "fail",
                trend_batch_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchGateStatusSummary(
                "incomplete_batch_health_rate",
                "pass" if status != "incomplete_batch_health_trend_batch" else "fail",
                trend_batch_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
                    generated_at,
                    duplicate_generated_at_count,
                ),
            )
            if duplicate_generated_at_count
            else ()
        ),
        duplicate_fingerprint_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary(
                    "fixture-trend-batch-fingerprint",
                    duplicate_fingerprint_count,
                ),
            )
            if duplicate_fingerprint_count
            else ()
        ),
    )


def trend_batch_health_config(**overrides):
    values = {
        "config_version": "batch-health-trend-batch-health-v1",
        "max_incomplete_trend_batch_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
        **values,
    )


def unsafe_trend_batch_health_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def _json_ready_for_test(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.astimezone(UTC).isoformat()
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        return {key: _json_ready_for_test(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready_for_test(item) for item in value]
    raise TypeError(f"unsupported test JSON value: {type(value).__name__}")


def test_trend_batch_health_empty_sample_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
            config_version="batch-health-trend-batch-health-v1",
        ),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    assert isinstance(
        report,
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    )
    assert report.status == "incomplete_batch_health_trend_batch_health"
    assert report.trend_batch_report_count == 0
    assert report.incomplete_trend_batch_ratio is None
    assert report.duplicate_generated_at_ratio is None
    assert report.duplicate_fingerprint_ratio is None
    assert report.first_trend_batch_generated_at is None
    assert report.last_trend_batch_generated_at is None
    assert tuple(row.trend_batch_ratio for row in report.status_rows) == (
        None,
        None,
        None,
        None,
    )
    assert tuple(row.status for row in report.gate_results) == (
        "incomplete",
        "incomplete",
        "incomplete",
        "incomplete",
    )


def test_trend_batch_health_nonempty_sample_below_configured_min_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1)],
        config=trend_batch_health_config(min_trend_batch_report_count=2),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert report.status == "incomplete_batch_health_trend_batch_health"
    assert gates["trend_batch_sample"].status == "incomplete"
    assert gates["trend_batch_sample"].observed_value == 1
    assert gates["trend_batch_sample"].threshold == 2
    assert gates["incomplete_trend_batch_rate"].status == "pass"
    assert gates["duplicate_generated_at_rate"].status == "pass"
    assert gates["duplicate_fingerprint_rate"].status == "pass"


def test_trend_batch_health_summarizes_supplied_trend_batch_reports():
    reports = [
        trend_batch_report_fixture(
            status="duplicate_fingerprint_batch_health_trend_batch",
            index=3,
        ),
        trend_batch_report_fixture(
            status=(
                "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
            ),
            index=1,
        ),
        trend_batch_report_fixture(status="incomplete_batch_health_trend_batch", index=4),
        trend_batch_report_fixture(
            status="duplicate_generated_at_batch_health_trend_batch",
            index=2,
        ),
    ]

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        reports,
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 9, 17, 12, tzinfo=UTC)
    assert report.config_version == "batch-health-trend-batch-health-v1"
    assert report.report_only is True
    assert (
        report.status
        == "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready"
    )
    assert report.trend_batch_report_count == 4
    assert report.ready_trend_batch_report_count == 1
    assert report.incomplete_trend_batch_report_count == 1
    assert report.duplicate_generated_at_trend_batch_report_count == 1
    assert report.duplicate_fingerprint_trend_batch_report_count == 1
    assert report.duplicate_generated_at_count == 0
    assert report.duplicate_fingerprint_count == 0
    assert report.incomplete_trend_batch_ratio == Decimal("0.7500")
    assert report.duplicate_generated_at_ratio == Decimal("0.0000")
    assert report.duplicate_fingerprint_ratio == Decimal("0.0000")
    assert tuple(row.gate_name for row in report.gate_results) == (
        "trend_batch_sample",
        "incomplete_trend_batch_rate",
        "duplicate_generated_at_rate",
        "duplicate_fingerprint_rate",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.trend_batch_status for row in report.status_rows) == (
        "duplicate_fingerprint_batch_health_trend_batch",
        "duplicate_generated_at_batch_health_trend_batch",
        "incomplete_batch_health_trend_batch",
        "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
    )
    assert tuple(row.trend_batch_count for row in report.status_rows) == (1, 1, 1, 1)
    assert tuple(
        (row.trend_batch_config_version, row.trend_batch_count)
        for row in report.config_version_summaries
    ) == (("batch-health-trend-batch-v1", 4),)
    assert tuple(
        (row.gate_name, row.gate_status, row.trend_batch_count)
        for row in report.gate_status_summaries
    ) == (
        ("duplicate_fingerprint_rate", "fail", 1),
        ("duplicate_fingerprint_rate", "pass", 3),
        ("duplicate_generated_at_rate", "fail", 1),
        ("duplicate_generated_at_rate", "pass", 3),
        ("incomplete_trend_rate", "fail", 1),
        ("incomplete_trend_rate", "pass", 3),
        ("trend_sample", "pass", 4),
    )


def test_trend_batch_health_status_priority_for_rate_failures():
    identical = trend_batch_report_fixture(index=4)
    duplicate_generated_at_wins = (
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [identical, identical],
            config=trend_batch_health_config(
                max_duplicate_generated_at_ratio=Decimal("0.0000"),
                max_duplicate_fingerprint_ratio=Decimal("0.0000"),
            ),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )
    )
    assert duplicate_generated_at_wins.status == (
        "duplicate_generated_at_batch_health_trend_batch_health"
    )

    duplicate_fingerprint = (
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [identical, identical],
            config=trend_batch_health_config(
                max_duplicate_generated_at_ratio=Decimal("1.0000"),
                max_duplicate_fingerprint_ratio=Decimal("0.0000"),
            ),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )
    )
    assert duplicate_fingerprint.status == (
        "duplicate_fingerprint_batch_health_trend_batch_health"
    )

    incomplete = (
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [
                trend_batch_report_fixture(index=1),
                trend_batch_report_fixture(
                    status="incomplete_batch_health_trend_batch",
                    index=2,
                ),
            ],
            config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
                config_version="batch-health-trend-batch-health-v1",
                max_duplicate_fingerprint_ratio=Decimal("1.0000"),
            ),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )
    )
    assert incomplete.status == "incomplete_batch_health_trend_batch_health"


def test_trend_batch_health_sample_incomplete_prioritizes_duplicate_rate_failures():
    first = trend_batch_report_fixture(index=7)
    second = trend_batch_report_fixture(index=7)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [first, second],
        config=trend_batch_health_config(
            min_trend_batch_report_count=3,
            max_duplicate_generated_at_ratio=Decimal("0.0000"),
            max_duplicate_fingerprint_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert gates["trend_batch_sample"].status == "incomplete"
    assert gates["duplicate_generated_at_rate"].status == "fail"
    assert gates["duplicate_fingerprint_rate"].status == "fail"
    assert report.status == "incomplete_batch_health_trend_batch_health"


def test_trend_batch_health_duplicate_counts_use_full_collision_groups():
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)
    two_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [
            replace(trend_batch_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    assert two_time.duplicate_generated_at_count == 2
    assert two_time.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
            shared_time,
            2,
        ),
    )

    three_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [
            replace(trend_batch_report_fixture(index=3), generated_at=shared_time),
            replace(trend_batch_report_fixture(index=4), generated_at=shared_time),
            replace(trend_batch_report_fixture(index=5), generated_at=shared_time),
        ],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    assert three_time.duplicate_generated_at_count == 3
    assert three_time.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
            shared_time,
            3,
        ),
    )

    identical = trend_batch_report_fixture(index=9)
    two_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [identical, identical],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    assert two_fingerprint.duplicate_fingerprint_count == 2
    assert two_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 2

    three_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [identical, identical, identical],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    assert three_fingerprint.duplicate_fingerprint_count == 3
    assert three_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 3


def test_trend_batch_health_duplicate_fingerprint_detection_is_structural():
    first = trend_batch_report_fixture(index=8)
    second = trend_batch_report_fixture(index=8)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [first, second],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    expected_fingerprint = json.dumps(
        _json_ready_for_test(asdict(first)),
        allow_nan=False,
        sort_keys=True,
    )
    assert first is not second
    assert report.duplicate_fingerprint_count == 2
    assert report.duplicate_fingerprint_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
            expected_fingerprint,
            2,
        ),
    )
    assert (
        report.duplicate_fingerprint_summaries[0].report_fingerprint
        == expected_fingerprint
    )


def test_trend_batch_health_gate_status_summaries_use_existing_trend_batch_gate_rows():
    first = trend_batch_report_fixture(index=1)
    second = trend_batch_report_fixture(
        status="duplicate_generated_at_batch_health_trend_batch",
        index=2,
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [second, first],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    rows = tuple(
        (row.gate_name, row.gate_status, row.trend_batch_count)
        for row in report.gate_status_summaries
    )
    assert ("duplicate_generated_at_rate", "fail", 1) in rows
    assert ("duplicate_generated_at_rate", "pass", 1) in rows
    assert ("trend_sample", "pass", 2) in rows
    assert sum(row.trend_batch_count for row in report.gate_status_summaries) == 8


def test_trend_batch_health_gate_status_summaries_count_each_upstream_gate_result():
    base = trend_batch_report_fixture(index=9)
    upstream = replace(
        base,
        status="duplicate_generated_at_batch_health_trend_batch",
        ready_trend_report_count=1,
        incomplete_trend_report_count=1,
        duplicate_generated_at_count=2,
        duplicate_fingerprint_count=2,
        incomplete_trend_ratio=Decimal("0.5000"),
        duplicate_generated_at_ratio=Decimal("1.0000"),
        duplicate_fingerprint_ratio=Decimal("1.0000"),
        gate_results=(
            base.gate_results[0],
            replace(
                base.gate_results[1],
                status="fail",
                observed_value=Decimal("0.5000"),
                threshold=Decimal("0.0000"),
            ),
            replace(
                base.gate_results[2],
                status="fail",
                observed_value=Decimal("1.0000"),
                threshold=Decimal("0.0000"),
            ),
            replace(
                base.gate_results[3],
                status="fail",
                observed_value=Decimal("1.0000"),
                threshold=Decimal("0.0000"),
            ),
        ),
        status_rows=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
                "duplicate_fingerprint_batch_health_trend",
                0,
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
                "duplicate_generated_at_batch_health_trend",
                0,
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
                "incomplete_batch_health_trend",
                1,
                Decimal("0.5000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchStatusRow(
                "proposal_evidence_comparison_history_batch_health_trend_ready",
                1,
                Decimal("0.5000"),
            ),
        ),
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateGeneratedAtSummary(
                base.generated_at,
                2,
            ),
        ),
        duplicate_fingerprint_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchDuplicateFingerprintSummary(
                "multiple-failing-upstream-gates",
                2,
            ),
        ),
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [upstream],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    assert tuple(
        (row.gate_name, row.gate_status, row.trend_batch_count)
        for row in report.gate_status_summaries
    ) == (
        ("duplicate_fingerprint_rate", "fail", 1),
        ("duplicate_generated_at_rate", "fail", 1),
        ("incomplete_trend_rate", "fail", 1),
        ("trend_sample", "pass", 1),
    )


def test_trend_batch_health_ordering_uses_normalized_generated_at():
    late = trend_batch_report_fixture(index=3)
    local_late = replace(
        trend_batch_report_fixture(index=1),
        generated_at=datetime(2026, 9, 16, 21, tzinfo=timezone(timedelta(hours=-4))),
    )
    middle = trend_batch_report_fixture(index=2)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [late, middle, local_late],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    assert report.first_trend_batch_generated_at == middle.generated_at
    assert report.last_trend_batch_generated_at == datetime(2026, 9, 17, 1, tzinfo=UTC)


def test_trend_batch_health_rejects_upstream_trend_sample_fail_payload():
    malformed = trend_batch_report_fixture(index=10)
    object.__setattr__(malformed.gate_results[0], "status", "fail")

    with pytest.raises(ValueError, match="trend_sample status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [malformed],
            config=trend_batch_health_config(),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )


def test_trend_batch_health_rejects_bad_inputs_before_iteration():
    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("trend-batch-health.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"report": trend_batch_report_fixture()},
        Path("trend-batch-health.jsonl"),
        '{"serialized": true}',
        (item for item in (trend_batch_report_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="trend_batch_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
                bad_input,
                config=trend_batch_health_config(),
                generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
            )


def test_trend_batch_health_rejects_subclasses_and_mutated_nested_rows(tmp_path):
    source = trend_batch_report_fixture(index=1)

    class TrendBatchSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport):
        pass

    subclass_value = TrendBatchSubclass(
        **{
            field_name: getattr(source, field_name)
            for field_name in source.__dataclass_fields__
        },
    )
    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchReport",
    ):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [subclass_value],
            config=trend_batch_health_config(),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )

    drift = trend_batch_report_fixture(index=2)
    object.__setattr__(drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
            [drift],
            config=trend_batch_health_config(),
            generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
        )

    valid = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [source],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    invalid = unsafe_trend_batch_health_report(
        valid,
        duplicate_generated_at_ratio=Decimal("NaN"),
    )
    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "trend-batch-health.jsonl",
    )
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)
    assert not log.path.exists()


def test_trend_batch_health_rejects_stale_or_wrong_typed_gate_payloads(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1), trend_batch_report_fixture(index=2)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    bad_sample_type = unsafe_trend_batch_health_report(
        report,
        gate_results=(
            replace(report.gate_results[0], observed_value=Decimal("2")),
            *report.gate_results[1:],
        ),
    )
    bad_sample_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "bad-sample.jsonl",
    )
    with pytest.raises(ValueError, match="trend_batch_sample observed_value"):
        bad_sample_log.append(bad_sample_type)
    assert not bad_sample_log.path.exists()

    bad_rate_type = unsafe_trend_batch_health_report(
        report,
        gate_results=(
            *report.gate_results[:1],
            replace(report.gate_results[1], observed_value=0),
            *report.gate_results[2:],
        ),
    )
    bad_rate_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "bad-rate.jsonl",
    )
    with pytest.raises(ValueError, match="observed_value must be a Decimal"):
        bad_rate_log.append(bad_rate_type)
    assert not bad_rate_log.path.exists()


def test_trend_batch_health_rejects_stale_summaries_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1), trend_batch_report_fixture(index=2)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    missing_summaries = unsafe_trend_batch_health_report(report, gate_status_summaries=())
    missing_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "missing-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        missing_log.append(missing_summaries)
    assert not missing_log.path.exists()

    stale_summaries = unsafe_trend_batch_health_report(
        report,
        gate_status_summaries=(
            replace(
                report.gate_status_summaries[0],
                trend_batch_count=report.gate_status_summaries[0].trend_batch_count - 1,
            ),
            *report.gate_status_summaries[1:],
        ),
    )
    stale_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "stale-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        stale_log.append(stale_summaries)
    assert not stale_log.path.exists()

    compensated_rows = [
        row
        for row in report.gate_status_summaries
        if row.gate_name != "duplicate_fingerprint_rate"
    ]
    compensated_rows.append(
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
            "trend_sample",
            "fail",
            report.trend_batch_report_count,
        ),
    )
    compensated_summaries = unsafe_trend_batch_health_report(
        report,
        gate_status_summaries=tuple(
            sorted(
                compensated_rows,
                key=lambda row: (row.gate_name, row.gate_status),
            ),
        ),
    )
    compensated_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "compensated-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        compensated_log.append(compensated_summaries)
    assert not compensated_log.path.exists()

    impossible_rows = tuple(
        sorted(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                    "trend_sample",
                    "fail",
                    report.trend_batch_report_count,
                )
                if row.gate_name == "trend_sample"
                else row
                for row in report.gate_status_summaries
            ),
            key=lambda row: (row.gate_name, row.gate_status),
        ),
    )
    impossible_report = unsafe_trend_batch_health_report(
        report,
        gate_status_summaries=impossible_rows,
    )
    impossible_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "impossible-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        impossible_log.append(impossible_report)
    assert not impossible_log.path.exists()


def test_trend_batch_health_boundary_statement_is_exact_and_config_rejects_mutation():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    assert report.boundary_statement == TREND_BATCH_HEALTH_BOUNDARY
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
            config_version="batch-health-trend-batch-health-v1",
            boundary_statement=TREND_BATCH_HEALTH_BOUNDARY.replace(
                "report-only",
                "report only",
            ),
        )


def test_trend_batch_health_rejects_boundary_mutation_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    same_alphanumeric_boundary = report.boundary_statement.replace("report-only", "report only")
    mutated_report = unsafe_trend_batch_health_report(
        report,
        boundary_statement=same_alphanumeric_boundary,
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "mutated-boundary.jsonl",
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        log.append(mutated_report)
    assert not log.path.exists()


def test_trend_batch_health_invalid_append_preserves_existing_log_bytes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "trend-batch-health.jsonl",
    )
    log.append(report)
    before = log.path.read_bytes()

    invalid = unsafe_trend_batch_health_report(
        report,
        duplicate_generated_at_ratio=Decimal("NaN"),
    )
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)
    assert log.path.read_bytes() == before


def test_trend_batch_health_rejects_nonquantized_ratio_values_before_append_writes(
    tmp_path,
):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [
            trend_batch_report_fixture(index=1),
            trend_batch_report_fixture(
                status="incomplete_batch_health_trend_batch",
                index=2,
            ),
        ],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    assert report.incomplete_trend_batch_ratio == Decimal("0.5000")

    nonquantized_status_rows = tuple(
        replace(row, trend_batch_ratio=Decimal("0.5"))
        if row.trend_batch_status == "incomplete_batch_health_trend_batch"
        else row
        for row in report.status_rows
    )
    nonquantized_gate_results = tuple(
        replace(row, observed_value=Decimal("0.5"))
        if row.gate_name == "incomplete_trend_batch_rate"
        else row
        for row in report.gate_results
    )
    invalid_reports = (
        unsafe_trend_batch_health_report(
            report,
            incomplete_trend_batch_ratio=Decimal("0.5"),
        ),
        unsafe_trend_batch_health_report(
            report,
            status_rows=nonquantized_status_rows,
        ),
        unsafe_trend_batch_health_report(
            report,
            gate_results=nonquantized_gate_results,
        ),
    )

    for index, invalid in enumerate(invalid_reports, start=1):
        log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
            tmp_path / f"nonquantized-ratio-{index}.jsonl",
        )
        with pytest.raises(
            ValueError,
            match="quantized|derived ratio|observed_value|expected ratios",
        ):
            log.append(invalid)
        assert not log.path.exists()


def test_trend_batch_health_rejects_duplicate_generated_at_summary_outside_bounds(
    tmp_path,
):
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [
            replace(trend_batch_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )
    out_of_bounds_report = unsafe_trend_batch_health_report(
        report,
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
                shared_time + timedelta(days=1),
                report.duplicate_generated_at_count,
            ),
        ),
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "out-of-bounds-duplicate-generated-at.jsonl",
    )
    with pytest.raises(ValueError, match="duplicate_generated_at_summaries"):
        log.append(out_of_bounds_report)
    assert not log.path.exists()


def test_trend_batch_health_gate_thresholds_preserve_caller_config_values():
    config = trend_batch_health_config(
        min_trend_batch_report_count=4,
        max_incomplete_trend_batch_ratio=Decimal("0.2500"),
        max_duplicate_generated_at_ratio=Decimal("0.5000"),
        max_duplicate_fingerprint_ratio=Decimal("0.7500"),
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1)],
        config=config,
        generated_at=datetime(2026, 9, 17, 12, tzinfo=UTC),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert gates["trend_batch_sample"].threshold == 4
    assert gates["incomplete_trend_batch_rate"].threshold == Decimal("0.2500")
    assert gates["duplicate_generated_at_rate"].threshold == Decimal("0.5000")
    assert gates["duplicate_fingerprint_rate"].threshold == Decimal("0.7500")


def test_trend_batch_health_config_dataclasses_and_log_validate_invariants(tmp_path):
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
            config_version="",
        )
    with pytest.raises(ValueError, match="min_trend_batch_report_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
            config_version="batch-health-trend-batch-health-v1",
            min_trend_batch_report_count=-1,
        )
    with pytest.raises(ValueError, match="max_duplicate_fingerprint_ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfig(
            config_version="batch-health-trend-batch-health-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0001"),
        )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_report(
        [trend_batch_report_fixture(index=1), trend_batch_report_fixture(index=2)],
        config=trend_batch_health_config(),
        generated_at=datetime(2026, 9, 17, 22, 30, tzinfo=timezone(timedelta(hours=8))),
    )
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(FrozenInstanceError):
        report.gate_results[0].status = "unknown"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
            "approval_workflow",
            "pass",
            "bad",
        )
    with pytest.raises(ValueError, match="trend_batch_sample cannot fail"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
            "trend_batch_sample",
            "fail",
            "bad",
        )
    with pytest.raises(ValueError, match="trend_batch_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
            "approval_workflow",
            1,
            Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="trend_batch_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary(
            "batch-health-trend-batch-v1",
            0,
        )
    with pytest.raises(ValueError, match="gate_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
            "trend_sample",
            "unknown",
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
            report.generated_at,
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
            "fingerprint",
            1,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=list(report.status_rows))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="too short")

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthLog(
        tmp_path / "nested" / "trend-batch-health.jsonl",
    )
    log.append(report)
    log.append(report)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"boundary_statement"')
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-17T14:30:00+00:00"
    assert stored["incomplete_trend_batch_ratio"] == "0.0000"
    assert stored["status_rows"][0]["trend_batch_ratio"] == "0.0000"
    assert stored["gate_results"][0]["observed_value"] == 2
