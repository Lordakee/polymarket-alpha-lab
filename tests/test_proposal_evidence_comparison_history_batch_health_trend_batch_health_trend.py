import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import pytest

from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health_trend import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow,
    build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report,
)
from polymarket_alpha_lab.proposal_evidence_comparison_history_batch_health_trend_batch_health import (
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport,
    TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow,
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

TREND_BATCH_HEALTH_TREND_BOUNDARY = (
    "This is a report-only proposal evidence comparison history batch health trend batch health trend "
    "artifact over supplied proposal evidence comparison history batch health trend batch health "
    "reports, not an approval workflow, proposal approval, approved-proposal "
    "selector, latest-decision selector, decision-resolution process, investment "
    "ranking, trade recommendation, financial advice, strategy-promotion signal, "
    "trade instruction, order instruction, broker request, order request, API clients, "
    "account action, account automation, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflows, external-history "
    "loader, JSONL reader, scraping workflow, browser automation, outcome loaders, "
    "settlement review, reconciliation process, compliance review, legal analysis, "
    "geographic access analysis, realized false-positive analysis, profitability "
    "analysis, live execution, or automatic order-placement authorization."
)


def _ratio(count: int, total: int) -> Decimal | None:
    if total == 0:
        return None
    return (Decimal(count) / Decimal(total)).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_EVEN,
    )


def _node14_rate_gate(
    gate_name: str,
    observed_value: Decimal | None,
    threshold: Decimal = Decimal("0.0000"),
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult:
    if observed_value is None:
        status = "incomplete"
    elif observed_value <= threshold:
        status = "pass"
    else:
        status = "fail"
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
        gate_name,
        status,
        f"{gate_name} checked",
        observed_value,
        threshold,
    )


def trend_batch_health_report_fixture(
    *,
    status: str = "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
    index: int = 1,
    generated_at: datetime | None = None,
    config_version: str = "batch-health-trend-batch-health-v1",
) -> TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport:
    generated_at = generated_at or datetime(2026, 9, 17, 12, index, tzinfo=UTC)
    trend_batch_report_count = 2
    status_counts = {
        "duplicate_fingerprint_batch_health_trend_batch": 0,
        "duplicate_generated_at_batch_health_trend_batch": 0,
        "incomplete_batch_health_trend_batch": 0,
        "proposal_evidence_comparison_history_batch_health_trend_batch_ready": 2,
    }
    duplicate_generated_at_count = 0
    duplicate_fingerprint_count = 0
    if status == "incomplete_batch_health_trend_batch_health":
        status_counts["incomplete_batch_health_trend_batch"] = 1
        status_counts[
            "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
        ] = 1
    elif status == "duplicate_generated_at_batch_health_trend_batch_health":
        duplicate_generated_at_count = 2
    elif status == "duplicate_fingerprint_batch_health_trend_batch_health":
        duplicate_fingerprint_count = 2
    elif status != "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready":
        raise AssertionError(f"unknown fixture status: {status}")

    incomplete_ratio = _ratio(
        trend_batch_report_count
        - status_counts[
            "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
        ],
        trend_batch_report_count,
    )
    duplicate_generated_at_ratio = _ratio(
        duplicate_generated_at_count,
        trend_batch_report_count,
    )
    duplicate_fingerprint_ratio = _ratio(
        duplicate_fingerprint_count,
        trend_batch_report_count,
    )
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport(
        generated_at=generated_at,
        config_version=config_version,
        report_only=True,
        boundary_statement=TREND_BATCH_HEALTH_BOUNDARY,
        trend_batch_report_count=trend_batch_report_count,
        ready_trend_batch_report_count=status_counts[
            "proposal_evidence_comparison_history_batch_health_trend_batch_ready"
        ],
        incomplete_trend_batch_report_count=status_counts[
            "incomplete_batch_health_trend_batch"
        ],
        duplicate_generated_at_trend_batch_report_count=status_counts[
            "duplicate_generated_at_batch_health_trend_batch"
        ],
        duplicate_fingerprint_trend_batch_report_count=status_counts[
            "duplicate_fingerprint_batch_health_trend_batch"
        ],
        duplicate_generated_at_count=duplicate_generated_at_count,
        duplicate_fingerprint_count=duplicate_fingerprint_count,
        incomplete_trend_batch_ratio=incomplete_ratio,
        duplicate_generated_at_ratio=duplicate_generated_at_ratio,
        duplicate_fingerprint_ratio=duplicate_fingerprint_ratio,
        first_trend_batch_generated_at=generated_at,
        last_trend_batch_generated_at=generated_at,
        status=status,
        gate_results=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateResult(
                "trend_batch_sample",
                "pass",
                "trend_batch_sample checked",
                trend_batch_report_count,
                1,
            ),
            _node14_rate_gate("incomplete_trend_batch_rate", incomplete_ratio),
            _node14_rate_gate("duplicate_generated_at_rate", duplicate_generated_at_ratio),
            _node14_rate_gate("duplicate_fingerprint_rate", duplicate_fingerprint_ratio),
        ),
        status_rows=tuple(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
                trend_batch_status,
                trend_batch_count,
                _ratio(trend_batch_count, trend_batch_report_count),
            )
            for trend_batch_status, trend_batch_count in status_counts.items()
        ),
        config_version_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthConfigVersionSummary(
                "batch-health-trend-batch-v1",
                trend_batch_report_count,
            ),
        ),
        gate_status_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "duplicate_fingerprint_rate",
                "pass",
                trend_batch_report_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "duplicate_generated_at_rate",
                "pass",
                trend_batch_report_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "incomplete_trend_rate",
                "pass",
                trend_batch_report_count,
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthGateStatusSummary(
                "trend_sample",
                "pass",
                trend_batch_report_count,
            ),
        ),
        duplicate_generated_at_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
                    generated_at,
                    duplicate_generated_at_count,
                ),
            )
            if duplicate_generated_at_count
            else ()
        ),
        duplicate_fingerprint_summaries=(
            (
                TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
                    "fixture-trend-batch-health-fingerprint",
                    duplicate_fingerprint_count,
                ),
            )
            if duplicate_fingerprint_count
            else ()
        ),
    )


def trend_batch_health_trend_config(**overrides):
    values = {
        "config_version": "batch-health-trend-batch-health-trend-v1",
        "max_incomplete_trend_batch_health_ratio": Decimal("1.0000"),
        "max_duplicate_generated_at_ratio": Decimal("1.0000"),
        "max_duplicate_fingerprint_ratio": Decimal("1.0000"),
    }
    values.update(overrides)
    return TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
        **values,
    )


def unsafe_trend_batch_health_trend_report(report, **changes):
    clone = object.__new__(type(report))
    for field_name in report.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(report, field_name))
    for field_name, value in changes.items():
        object.__setattr__(clone, field_name, value)
    return clone


def unsafe_gate_status_summary(row, **changes):
    clone = object.__new__(type(row))
    for field_name in row.__dataclass_fields__:
        object.__setattr__(clone, field_name, getattr(row, field_name))
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


def test_trend_batch_health_trend_empty_sample_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [],
        config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
            config_version="batch-health-trend-batch-health-trend-v1",
        ),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert isinstance(
        report,
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendReport,
    )
    assert report.status == "incomplete_batch_health_trend_batch_health_trend"
    assert report.trend_batch_health_report_count == 0
    assert report.incomplete_trend_batch_health_ratio is None
    assert report.duplicate_generated_at_ratio is None
    assert report.duplicate_fingerprint_ratio is None
    assert report.first_trend_batch_health_generated_at is None
    assert report.last_trend_batch_health_generated_at is None
    assert tuple(row.trend_batch_health_ratio for row in report.status_rows) == (
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


def test_trend_batch_health_trend_nonempty_sample_below_configured_min_is_incomplete():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1)],
        config=trend_batch_health_trend_config(min_trend_batch_health_report_count=2),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert report.status == "incomplete_batch_health_trend_batch_health_trend"
    assert gates["trend_batch_health_sample"].status == "incomplete"
    assert gates["trend_batch_health_sample"].observed_value == 1
    assert gates["trend_batch_health_sample"].threshold == 2
    assert gates["incomplete_trend_batch_health_rate"].status == "pass"
    assert gates["duplicate_generated_at_rate"].status == "pass"
    assert gates["duplicate_fingerprint_rate"].status == "pass"


def test_trend_batch_health_trend_summarizes_supplied_node14_reports():
    reports = [
        trend_batch_health_report_fixture(
            status="duplicate_fingerprint_batch_health_trend_batch_health",
            index=3,
        ),
        trend_batch_health_report_fixture(
            status=(
                "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready"
            ),
            index=1,
        ),
        trend_batch_health_report_fixture(status="incomplete_batch_health_trend_batch_health", index=4),
        trend_batch_health_report_fixture(
            status="duplicate_generated_at_batch_health_trend_batch_health",
            index=2,
        ),
    ]

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        reports,
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 9, 18, 12, tzinfo=UTC)
    assert report.config_version == "batch-health-trend-batch-health-trend-v1"
    assert report.report_only is True
    assert (
        report.status
        == "proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_ready"
    )
    assert report.trend_batch_health_report_count == 4
    assert report.ready_trend_batch_health_report_count == 1
    assert report.incomplete_trend_batch_health_report_count == 1
    assert report.duplicate_generated_at_trend_batch_health_report_count == 1
    assert report.duplicate_fingerprint_trend_batch_health_report_count == 1
    assert report.duplicate_generated_at_count == 0
    assert report.duplicate_fingerprint_count == 0
    assert report.incomplete_trend_batch_health_ratio == Decimal("0.7500")
    assert report.duplicate_generated_at_ratio == Decimal("0.0000")
    assert report.duplicate_fingerprint_ratio == Decimal("0.0000")
    assert tuple(row.gate_name for row in report.gate_results) == (
        "trend_batch_health_sample",
        "incomplete_trend_batch_health_rate",
        "duplicate_generated_at_rate",
        "duplicate_fingerprint_rate",
    )
    assert all(row.status == "pass" for row in report.gate_results)
    assert tuple(row.trend_batch_health_status for row in report.status_rows) == (
        "duplicate_fingerprint_batch_health_trend_batch_health",
        "duplicate_generated_at_batch_health_trend_batch_health",
        "incomplete_batch_health_trend_batch_health",
        "proposal_evidence_comparison_history_batch_health_trend_batch_health_ready",
    )
    assert tuple(row.trend_batch_health_count for row in report.status_rows) == (1, 1, 1, 1)
    assert tuple(
        (row.trend_batch_health_config_version, row.trend_batch_health_count)
        for row in report.config_version_summaries
    ) == (("batch-health-trend-batch-health-v1", 4),)
    assert tuple(
        (row.gate_name, row.gate_status, row.trend_batch_health_count)
        for row in report.gate_status_summaries
    ) == (
        ("duplicate_fingerprint_rate", "fail", 1),
        ("duplicate_fingerprint_rate", "pass", 3),
        ("duplicate_generated_at_rate", "fail", 1),
        ("duplicate_generated_at_rate", "pass", 3),
        ("incomplete_trend_batch_rate", "fail", 1),
        ("incomplete_trend_batch_rate", "pass", 3),
        ("trend_batch_sample", "pass", 4),
    )


def test_trend_batch_health_trend_status_priority_for_rate_failures():
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)

    sample_report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [],
        config=trend_batch_health_trend_config(min_trend_batch_health_report_count=1),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert sample_report.status == "incomplete_batch_health_trend_batch_health_trend"

    duplicate_generated_at_wins = (
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [
                replace(trend_batch_health_report_fixture(index=1), generated_at=shared_time),
                replace(trend_batch_health_report_fixture(index=2), generated_at=shared_time),
            ],
            config=trend_batch_health_trend_config(
                max_duplicate_generated_at_ratio=Decimal("0.0000"),
            ),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )
    )
    assert duplicate_generated_at_wins.status == (
        "duplicate_generated_at_batch_health_trend_batch_health_trend"
    )

    duplicate_fingerprint = (
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [
                trend_batch_health_report_fixture(index=1),
                trend_batch_health_report_fixture(index=1),
            ],
            config=trend_batch_health_trend_config(
                max_duplicate_generated_at_ratio=Decimal("1.0000"),
                max_duplicate_fingerprint_ratio=Decimal("0.0000"),
            ),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )
    )
    assert duplicate_fingerprint.status == (
        "duplicate_fingerprint_batch_health_trend_batch_health_trend"
    )

    incomplete = (
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [
                trend_batch_health_report_fixture(index=1),
                trend_batch_health_report_fixture(
                    status="incomplete_batch_health_trend_batch_health",
                    index=2,
                ),
            ],
            config=TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
                config_version="batch-health-trend-batch-health-trend-v1",
                max_duplicate_fingerprint_ratio=Decimal("1.0000"),
            ),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )
    )
    assert incomplete.status == "incomplete_batch_health_trend_batch_health_trend"


def test_trend_batch_health_trend_sample_incomplete_prioritizes_duplicate_rate_failures():
    first = trend_batch_health_report_fixture(index=7)
    second = trend_batch_health_report_fixture(index=7)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [first, second],
        config=trend_batch_health_trend_config(
            min_trend_batch_health_report_count=3,
            max_duplicate_generated_at_ratio=Decimal("0.0000"),
            max_duplicate_fingerprint_ratio=Decimal("0.0000"),
        ),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert gates["trend_batch_health_sample"].status == "incomplete"
    assert gates["duplicate_generated_at_rate"].status == "fail"
    assert gates["duplicate_fingerprint_rate"].status == "fail"
    assert report.status == "incomplete_batch_health_trend_batch_health_trend"


def test_trend_batch_health_trend_duplicate_counts_use_full_collision_groups():
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)
    two_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            replace(trend_batch_health_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_health_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert two_time.duplicate_generated_at_count == 2
    assert two_time.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary(
            shared_time,
            2,
        ),
    )

    three_time = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            replace(trend_batch_health_report_fixture(index=3), generated_at=shared_time),
            replace(trend_batch_health_report_fixture(index=4), generated_at=shared_time),
            replace(trend_batch_health_report_fixture(index=5), generated_at=shared_time),
        ],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert three_time.duplicate_generated_at_count == 3
    assert three_time.duplicate_generated_at_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary(
            shared_time,
            3,
        ),
    )

    identical = trend_batch_health_report_fixture(index=9)
    two_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [identical, identical],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert two_fingerprint.duplicate_fingerprint_count == 2
    assert two_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 2

    three_fingerprint = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [identical, identical, identical],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert three_fingerprint.duplicate_fingerprint_count == 3
    assert three_fingerprint.duplicate_fingerprint_summaries[0].duplicate_count == 3


def test_trend_batch_health_trend_duplicate_fingerprint_detection_is_structural():
    first = trend_batch_health_report_fixture(index=8)
    second = trend_batch_health_report_fixture(index=8)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [first, second],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    expected_fingerprint = json.dumps(
        _json_ready_for_test(asdict(first)),
        allow_nan=False,
        sort_keys=True,
    )
    assert first is not second
    assert report.duplicate_fingerprint_count == 2
    assert report.duplicate_fingerprint_summaries == (
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary(
            expected_fingerprint,
            2,
        ),
    )
    assert (
        report.duplicate_fingerprint_summaries[0].report_fingerprint
        == expected_fingerprint
    )


def test_trend_batch_health_trend_gate_status_summaries_use_existing_node14_gate_rows():
    first = trend_batch_health_report_fixture(index=1)
    second = trend_batch_health_report_fixture(
        status="duplicate_generated_at_batch_health_trend_batch_health",
        index=2,
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [second, first],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    rows = tuple(
        (row.gate_name, row.gate_status, row.trend_batch_health_count)
        for row in report.gate_status_summaries
    )
    assert ("duplicate_generated_at_rate", "fail", 1) in rows
    assert ("duplicate_generated_at_rate", "pass", 1) in rows
    assert ("trend_batch_sample", "pass", 2) in rows
    assert sum(row.trend_batch_health_count for row in report.gate_status_summaries) == 8


def test_trend_batch_health_trend_gate_status_summaries_count_each_upstream_gate_result():
    base = trend_batch_health_report_fixture(index=9)
    upstream = replace(
        base,
        status="duplicate_generated_at_batch_health_trend_batch_health",
        ready_trend_batch_report_count=1,
        incomplete_trend_batch_report_count=1,
        duplicate_generated_at_count=2,
        duplicate_fingerprint_count=2,
        incomplete_trend_batch_ratio=Decimal("0.5000"),
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
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
                "duplicate_fingerprint_batch_health_trend_batch",
                0,
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
                "duplicate_generated_at_batch_health_trend_batch",
                0,
                Decimal("0.0000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
                "incomplete_batch_health_trend_batch",
                1,
                Decimal("0.5000"),
            ),
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthStatusRow(
                "proposal_evidence_comparison_history_batch_health_trend_batch_ready",
                1,
                Decimal("0.5000"),
            ),
        ),
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateGeneratedAtSummary(
                base.generated_at,
                2,
            ),
        ),
        duplicate_fingerprint_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthDuplicateFingerprintSummary(
                "multiple-failing-upstream-gates",
                2,
            ),
        ),
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [upstream],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert tuple(
        (row.gate_name, row.gate_status, row.trend_batch_health_count)
        for row in report.gate_status_summaries
    ) == (
        ("duplicate_fingerprint_rate", "fail", 1),
        ("duplicate_generated_at_rate", "fail", 1),
        ("incomplete_trend_batch_rate", "fail", 1),
        ("trend_batch_sample", "pass", 1),
    )


def test_trend_batch_health_trend_ordering_uses_normalized_generated_at():
    late = trend_batch_health_report_fixture(index=3)
    local_late = replace(
        trend_batch_health_report_fixture(index=1),
        generated_at=datetime(2026, 9, 16, 21, tzinfo=timezone(timedelta(hours=-4))),
    )
    middle = trend_batch_health_report_fixture(index=2)

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [late, middle, local_late],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert report.first_trend_batch_health_generated_at == datetime(2026, 9, 17, 1, tzinfo=UTC)
    assert report.last_trend_batch_health_generated_at == late.generated_at


def test_trend_batch_health_trend_rejects_upstream_trend_batch_sample_fail_payload():
    malformed = trend_batch_health_report_fixture(index=10)
    object.__setattr__(malformed.gate_results[0], "status", "fail")

    with pytest.raises(ValueError, match="trend_batch_sample cannot fail"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [malformed],
            config=trend_batch_health_trend_config(),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )


def test_trend_batch_health_trend_rejects_bad_inputs_before_iteration():
    class ExplodingIterable:
        def __iter__(self):
            raise AssertionError("loader-shaped iterable was consumed")

    class LogShapedInput:
        path = Path("trend-batch-health-trend.jsonl")

        def append(self, report):
            raise AssertionError("append-only log was consumed")

    for bad_input in (
        "[]",
        b"[]",
        {"report": trend_batch_health_report_fixture()},
        Path("trend-batch-health-trend.jsonl"),
        '{"serialized": true}',
        (item for item in (trend_batch_health_report_fixture(),)),
        ExplodingIterable(),
        LogShapedInput(),
        object(),
    ):
        with pytest.raises(ValueError, match="trend_batch_health_reports"):
            build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
                bad_input,
                config=trend_batch_health_trend_config(),
                generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
            )


def test_trend_batch_health_trend_rejects_subclasses_and_mutated_nested_rows(tmp_path):
    source = trend_batch_health_report_fixture(index=1)

    class TrendBatchHealthSubclass(TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport):
        pass

    subclass_value = TrendBatchHealthSubclass(
        **{
            field_name: getattr(source, field_name)
            for field_name in source.__dataclass_fields__
        },
    )
    with pytest.raises(
        ValueError,
        match="TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthReport",
    ):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [subclass_value],
            config=trend_batch_health_trend_config(),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )

    drift = trend_batch_health_report_fixture(index=2)
    object.__setattr__(drift.gate_results[0], "status", "unknown")
    with pytest.raises(ValueError, match="status"):
        build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
            [drift],
            config=trend_batch_health_trend_config(),
            generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
        )

    valid = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [source],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    invalid = unsafe_trend_batch_health_trend_report(
        valid,
        duplicate_generated_at_ratio=Decimal("NaN"),
    )
    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "trend-batch-health-trend.jsonl",
    )
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)
    assert not log.path.exists()


def test_trend_batch_health_trend_rejects_stale_or_wrong_typed_gate_payloads(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1), trend_batch_health_report_fixture(index=2)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    bad_sample_type = unsafe_trend_batch_health_trend_report(
        report,
        gate_results=(
            replace(report.gate_results[0], observed_value=Decimal("2")),
            *report.gate_results[1:],
        ),
    )
    bad_sample_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "bad-sample.jsonl",
    )
    with pytest.raises(ValueError, match="trend_batch_health_sample observed_value"):
        bad_sample_log.append(bad_sample_type)
    assert not bad_sample_log.path.exists()

    bad_rate_type = unsafe_trend_batch_health_trend_report(
        report,
        gate_results=(
            *report.gate_results[:1],
            replace(report.gate_results[1], observed_value=0),
            *report.gate_results[2:],
        ),
    )
    bad_rate_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "bad-rate.jsonl",
    )
    with pytest.raises(ValueError, match="observed_value must be a Decimal"):
        bad_rate_log.append(bad_rate_type)
    assert not bad_rate_log.path.exists()


def test_trend_batch_health_trend_rejects_stale_summaries_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1), trend_batch_health_report_fixture(index=2)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    missing_summaries = unsafe_trend_batch_health_trend_report(report, gate_status_summaries=())
    missing_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "missing-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="gate_status_summaries"):
        missing_log.append(missing_summaries)
    assert not missing_log.path.exists()

    stale_summaries = unsafe_trend_batch_health_trend_report(
        report,
        gate_status_summaries=(
            replace(
                report.gate_status_summaries[0],
                trend_batch_health_count=report.gate_status_summaries[0].trend_batch_health_count - 1,
            ),
            *report.gate_status_summaries[1:],
        ),
    )
    stale_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
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
    sample_row = next(
        row for row in report.gate_status_summaries if row.gate_name == "trend_batch_sample"
    )
    compensated_rows.append(
        unsafe_gate_status_summary(sample_row, gate_status="fail"),
    )
    compensated_summaries = unsafe_trend_batch_health_trend_report(
        report,
        gate_status_summaries=tuple(
            sorted(
                compensated_rows,
                key=lambda row: (row.gate_name, row.gate_status),
            ),
        ),
    )
    compensated_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "compensated-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="trend_batch_sample cannot fail"):
        compensated_log.append(compensated_summaries)
    assert not compensated_log.path.exists()

    impossible_rows = tuple(
        sorted(
            (
                unsafe_gate_status_summary(row, gate_status="fail")
                if row.gate_name == "trend_batch_sample"
                else row
                for row in report.gate_status_summaries
            ),
            key=lambda row: (row.gate_name, row.gate_status),
        ),
    )
    impossible_report = unsafe_trend_batch_health_trend_report(
        report,
        gate_status_summaries=impossible_rows,
    )
    impossible_log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "impossible-gate-status.jsonl",
    )
    with pytest.raises(ValueError, match="trend_batch_sample cannot fail"):
        impossible_log.append(impossible_report)
    assert not impossible_log.path.exists()


def test_trend_batch_health_trend_boundary_statement_is_exact_and_config_rejects_mutation():
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    assert report.boundary_statement == TREND_BATCH_HEALTH_TREND_BOUNDARY
    with pytest.raises(ValueError, match="boundary_statement"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
            config_version="batch-health-trend-batch-health-trend-v1",
            boundary_statement=TREND_BATCH_HEALTH_TREND_BOUNDARY.replace(
                "report-only",
                "report only",
            ),
        )


def test_trend_batch_health_trend_rejects_boundary_mutation_before_append_writes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    same_alphanumeric_boundary = report.boundary_statement.replace("report-only", "report only")
    mutated_report = unsafe_trend_batch_health_trend_report(
        report,
        boundary_statement=same_alphanumeric_boundary,
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "mutated-boundary.jsonl",
    )
    with pytest.raises(ValueError, match="boundary_statement"):
        log.append(mutated_report)
    assert not log.path.exists()


def test_trend_batch_health_trend_invalid_append_preserves_existing_log_bytes(tmp_path):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "trend-batch-health-trend.jsonl",
    )
    log.append(report)
    before = log.path.read_bytes()

    invalid = unsafe_trend_batch_health_trend_report(
        report,
        duplicate_generated_at_ratio=Decimal("NaN"),
    )
    with pytest.raises(ValueError, match="finite|duplicate_generated_at_ratio"):
        log.append(invalid)
    assert log.path.read_bytes() == before


def test_trend_batch_health_trend_rejects_nonquantized_ratio_values_before_append_writes(
    tmp_path,
):
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            trend_batch_health_report_fixture(index=1),
            trend_batch_health_report_fixture(
                status="incomplete_batch_health_trend_batch_health",
                index=2,
            ),
        ],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    assert report.incomplete_trend_batch_health_ratio == Decimal("0.5000")

    nonquantized_status_rows = tuple(
        replace(row, trend_batch_health_ratio=Decimal("0.5"))
        if row.trend_batch_health_status == "incomplete_batch_health_trend_batch_health"
        else row
        for row in report.status_rows
    )
    nonquantized_gate_results = tuple(
        replace(row, observed_value=Decimal("0.5"))
        if row.gate_name == "incomplete_trend_batch_health_rate"
        else row
        for row in report.gate_results
    )
    invalid_reports = (
        unsafe_trend_batch_health_trend_report(
            report,
            incomplete_trend_batch_health_ratio=Decimal("0.5"),
        ),
        unsafe_trend_batch_health_trend_report(
            report,
            status_rows=nonquantized_status_rows,
        ),
        unsafe_trend_batch_health_trend_report(
            report,
            gate_results=nonquantized_gate_results,
        ),
    )

    for index, invalid in enumerate(invalid_reports, start=1):
        log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
            tmp_path / f"nonquantized-ratio-{index}.jsonl",
        )
        with pytest.raises(
            ValueError,
            match="quantized|derived ratio|observed_value|expected ratios",
        ):
            log.append(invalid)
        assert not log.path.exists()


def test_trend_batch_health_trend_rejects_duplicate_generated_at_summary_outside_bounds(
    tmp_path,
):
    shared_time = datetime(2026, 9, 17, 1, tzinfo=UTC)
    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [
            replace(trend_batch_health_report_fixture(index=1), generated_at=shared_time),
            replace(trend_batch_health_report_fixture(index=2), generated_at=shared_time),
        ],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )
    out_of_bounds_report = unsafe_trend_batch_health_trend_report(
        report,
        duplicate_generated_at_summaries=(
            TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary(
                shared_time + timedelta(days=1),
                report.duplicate_generated_at_count,
            ),
        ),
    )

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "out-of-bounds-duplicate-generated-at.jsonl",
    )
    with pytest.raises(ValueError, match="duplicate_generated_at_summaries"):
        log.append(out_of_bounds_report)
    assert not log.path.exists()


def test_trend_batch_health_trend_gate_thresholds_preserve_caller_config_values():
    config = trend_batch_health_trend_config(
        min_trend_batch_health_report_count=4,
        max_incomplete_trend_batch_health_ratio=Decimal("0.2500"),
        max_duplicate_generated_at_ratio=Decimal("0.5000"),
        max_duplicate_fingerprint_ratio=Decimal("0.7500"),
    )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1)],
        config=config,
        generated_at=datetime(2026, 9, 18, 12, tzinfo=UTC),
    )

    gates = {row.gate_name: row for row in report.gate_results}
    assert gates["trend_batch_health_sample"].threshold == 4
    assert gates["incomplete_trend_batch_health_rate"].threshold == Decimal("0.2500")
    assert gates["duplicate_generated_at_rate"].threshold == Decimal("0.5000")
    assert gates["duplicate_fingerprint_rate"].threshold == Decimal("0.7500")


def test_trend_batch_health_trend_config_dataclasses_and_log_validate_invariants(tmp_path):
    with pytest.raises(ValueError, match="config_version"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
            config_version="",
        )
    with pytest.raises(ValueError, match="min_trend_batch_health_report_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
            config_version="batch-health-trend-batch-health-trend-v1",
            min_trend_batch_health_report_count=-1,
        )
    with pytest.raises(ValueError, match="max_duplicate_fingerprint_ratio"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfig(
            config_version="batch-health-trend-batch-health-trend-v1",
            max_duplicate_fingerprint_ratio=Decimal("1.0001"),
        )

    report = build_trade_proposal_evidence_comparison_history_batch_health_trend_batch_health_trend_report(
        [trend_batch_health_report_fixture(index=1), trend_batch_health_report_fixture(index=2)],
        config=trend_batch_health_trend_config(),
        generated_at=datetime(2026, 9, 18, 22, 30, tzinfo=timezone(timedelta(hours=8))),
    )
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(FrozenInstanceError):
        report.gate_results[0].status = "unknown"
    with pytest.raises(ValueError, match="gate_name"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult(
            "approval_workflow",
            "pass",
            "bad",
        )
    with pytest.raises(ValueError, match="trend_batch_health_sample cannot fail"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateResult(
            "trend_batch_health_sample",
            "fail",
            "bad",
        )
    with pytest.raises(ValueError, match="trend_batch_health_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendStatusRow(
            "approval_workflow",
            1,
            Decimal("1.0000"),
        )
    with pytest.raises(ValueError, match="trend_batch_health_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendConfigVersionSummary(
            "batch-health-trend-batch-health-v1",
            0,
        )
    with pytest.raises(ValueError, match="gate_status"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary(
            "trend_batch_sample",
            "unknown",
            1,
        )
    with pytest.raises(ValueError, match="trend_batch_sample cannot fail"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendGateStatusSummary(
            "trend_batch_sample",
            "fail",
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateGeneratedAtSummary(
            report.generated_at,
            1,
        )
    with pytest.raises(ValueError, match="duplicate_count"):
        TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendDuplicateFingerprintSummary(
            "fingerprint",
            1,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=list(report.status_rows))
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="too short")

    log = TradeProposalEvidenceComparisonHistoryBatchHealthTrendBatchHealthTrendLog(
        tmp_path / "nested" / "trend-batch-health-trend.jsonl",
    )
    log.append(report)
    log.append(report)
    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].startswith('{"boundary_statement"')
    stored = json.loads(lines[0])
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-09-18T14:30:00+00:00"
    assert stored["incomplete_trend_batch_health_ratio"] == "0.0000"
    assert stored["status_rows"][0]["trend_batch_health_ratio"] == "0.0000"
    assert stored["gate_results"][0]["observed_value"] == 2
