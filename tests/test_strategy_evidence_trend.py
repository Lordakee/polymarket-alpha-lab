from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_evidence import PaperStrategyEvidenceSnapshotReport
from polymarket_alpha_lab.strategy_evidence_trend import (
    PaperStrategyEvidenceTrendConfig,
    PaperStrategyEvidenceTrendGapRow,
    PaperStrategyEvidenceTrendReport,
    PaperStrategyEvidenceTrendStatusRow,
    build_paper_strategy_evidence_trend_report,
)


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
SNAPSHOT_STATUSES = (
    "no_local_evidence",
    "local_evidence_gaps",
    "local_risk_flags",
    "local_evidence_observed",
)
EVIDENCE_GAP_NAMES = (
    "missing_cycles",
    "missing_paper_trades",
    "missing_nav_snapshots",
    "missing_outcome_evidence",
    "missing_strategy_audit_history",
    "latest_strategy_audit_not_ready",
    "negative_cost_adjusted_edges",
    "unexecutable_open_positions",
)


def _config(**overrides) -> PaperStrategyEvidenceTrendConfig:
    values = {"config_version": "strategy-evidence-trend-v0"}
    values.update(overrides)
    return PaperStrategyEvidenceTrendConfig(**values)


def _snapshot(
    status: str,
    *,
    generated_at: datetime = GENERATED_AT,
    evidence_gap_names: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
) -> PaperStrategyEvidenceSnapshotReport:
    return PaperStrategyEvidenceSnapshotReport(
        generated_at=generated_at,
        config_version="strategy-evidence-snapshot-v0",
        status=status,
        cycle_count=0 if status == "no_local_evidence" else 12,
        paper_trade_count=0 if status == "no_local_evidence" else 18,
        nav_snapshot_count=0 if status == "no_local_evidence" else 5,
        outcome_checked_count=None if status == "no_local_evidence" else 18,
        outcome_pending_count=None if status == "no_local_evidence" else 8,
        outcome_resolved_count=None if status == "no_local_evidence" else 10,
        outcome_unresolved_count=None if status == "no_local_evidence" else 8,
        audit_report_count=None if status == "no_local_evidence" else 1,
        latest_audit_status=None if status == "no_local_evidence" else "audit_ready",
        negative_cost_adjusted_edge_count=(
            1 if "negative_cost_adjusted_edges" in evidence_gap_names else 0
        ),
        unexecutable_open_position_count=(
            1 if "unexecutable_open_positions" in evidence_gap_names else 0
        ),
        evidence_gap_names=evidence_gap_names,
        paper_only=paper_only,
        report_only=report_only,
    )


def test_strategy_evidence_trend_reports_empty_snapshot_sequence():
    report = build_paper_strategy_evidence_trend_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperStrategyEvidenceTrendReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-evidence-trend-v0"
    assert report.snapshot_report_count == 0
    assert report.latest_status is None
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.consecutive_local_risk_flags_count == 0
    assert report.consecutive_non_observed_count == 0
    assert report.latest_evidence_gap_names == ()
    assert report.status_rows == tuple(
        PaperStrategyEvidenceTrendStatusRow(status, 0, None)
        for status in SNAPSHOT_STATUSES
    )
    assert report.gap_rows == tuple(
        PaperStrategyEvidenceTrendGapRow(gap_name, 0, None)
        for gap_name in EVIDENCE_GAP_NAMES
    )


def test_strategy_evidence_trend_aggregates_status_rows_and_latest_gap_state():
    first = datetime(2026, 6, 17, 13, 0, tzinfo=UTC)
    second = datetime(2026, 6, 17, 14, 0, tzinfo=UTC)
    third = datetime(2026, 6, 17, 15, 0, tzinfo=UTC)
    fourth = datetime(2026, 6, 17, 16, 0, tzinfo=UTC)
    snapshots = (
        _snapshot("local_evidence_observed", generated_at=first),
        _snapshot(
            "local_evidence_gaps",
            generated_at=second,
            evidence_gap_names=("missing_outcome_evidence",),
        ),
        _snapshot(
            "local_risk_flags",
            generated_at=third,
            evidence_gap_names=("negative_cost_adjusted_edges",),
        ),
        _snapshot(
            "local_evidence_gaps",
            generated_at=fourth,
            evidence_gap_names=("latest_strategy_audit_not_ready",),
        ),
    )

    report = build_paper_strategy_evidence_trend_report(
        snapshots,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.snapshot_report_count == 4
    assert report.latest_status == "local_evidence_gaps"
    assert report.first_report_generated_at == first
    assert report.latest_report_generated_at == fourth
    assert report.consecutive_local_risk_flags_count == 0
    assert report.consecutive_non_observed_count == 3
    assert report.latest_evidence_gap_names == ("latest_strategy_audit_not_ready",)
    assert report.status_rows == (
        PaperStrategyEvidenceTrendStatusRow(
            "no_local_evidence",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategyEvidenceTrendStatusRow(
            "local_evidence_gaps",
            2,
            Decimal("0.500000"),
        ),
        PaperStrategyEvidenceTrendStatusRow(
            "local_risk_flags",
            1,
            Decimal("0.250000"),
        ),
        PaperStrategyEvidenceTrendStatusRow(
            "local_evidence_observed",
            1,
            Decimal("0.250000"),
        ),
    )
    assert report.gap_rows == (
        PaperStrategyEvidenceTrendGapRow(
            "missing_cycles",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "missing_paper_trades",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "missing_nav_snapshots",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "missing_outcome_evidence",
            1,
            Decimal("0.250000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "missing_strategy_audit_history",
            0,
            Decimal("0.000000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "latest_strategy_audit_not_ready",
            1,
            Decimal("0.250000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "negative_cost_adjusted_edges",
            1,
            Decimal("0.250000"),
        ),
        PaperStrategyEvidenceTrendGapRow(
            "unexecutable_open_positions",
            0,
            Decimal("0.000000"),
        ),
    )


def test_strategy_evidence_trend_resets_non_observed_streak_when_latest_observed():
    snapshots = (
        _snapshot(
            "local_risk_flags",
            generated_at=datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
            evidence_gap_names=("unexecutable_open_positions",),
        ),
        _snapshot(
            "local_evidence_observed",
            generated_at=datetime(2026, 6, 17, 15, 0, tzinfo=UTC),
        ),
    )

    report = build_paper_strategy_evidence_trend_report(
        snapshots,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.latest_status == "local_evidence_observed"
    assert report.consecutive_local_risk_flags_count == 0
    assert report.consecutive_non_observed_count == 0
    assert report.latest_evidence_gap_names == ()


def test_strategy_evidence_trend_counts_consecutive_local_risk_flags():
    snapshots = (
        _snapshot(
            "local_evidence_gaps",
            generated_at=datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
            evidence_gap_names=("missing_outcome_evidence",),
        ),
        _snapshot(
            "local_risk_flags",
            generated_at=datetime(2026, 6, 17, 14, 0, tzinfo=UTC),
            evidence_gap_names=("negative_cost_adjusted_edges",),
        ),
        _snapshot(
            "local_risk_flags",
            generated_at=datetime(2026, 6, 17, 15, 0, tzinfo=UTC),
            evidence_gap_names=("unexecutable_open_positions",),
        ),
    )

    report = build_paper_strategy_evidence_trend_report(
        snapshots,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.latest_status == "local_risk_flags"
    assert report.consecutive_local_risk_flags_count == 2
    assert report.consecutive_non_observed_count == 3


def test_strategy_evidence_trend_preserves_append_order_and_normalizes_datetimes_to_utc():
    generated_at = datetime(2026, 6, 17, 13, 0, tzinfo=timezone(timedelta(hours=-5)))
    later_timestamp_first = datetime(
        2026,
        6,
        17,
        10,
        0,
        tzinfo=timezone(timedelta(hours=-7)),
    )
    earlier_timestamp_latest = datetime(2026, 6, 17, 9, 0, tzinfo=UTC)

    report = build_paper_strategy_evidence_trend_report(
        [
            _snapshot("local_evidence_observed", generated_at=later_timestamp_first),
            _snapshot("local_evidence_observed", generated_at=earlier_timestamp_latest),
        ],
        config=_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
    assert report.first_report_generated_at == datetime(2026, 6, 17, 17, 0, tzinfo=UTC)
    assert report.latest_report_generated_at == earlier_timestamp_latest


def test_strategy_evidence_trend_rejects_invalid_builder_inputs():
    invalid_snapshots = (
        "not snapshots",
        b"not snapshots",
        {"snapshot": _snapshot("local_evidence_observed")},
        iter((_snapshot("local_evidence_observed"),)),
    )
    for value in invalid_snapshots:
        with pytest.raises(ValueError, match="snapshots"):
            build_paper_strategy_evidence_trend_report(
                value,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="PaperStrategyEvidenceSnapshotReport"):
        build_paper_strategy_evidence_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_strategy_evidence_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_evidence_trend_report(
            (),
            config=_config(),
            generated_at="now",
        )


@pytest.mark.parametrize(
    ("flag_name", "flag_value"),
    (("paper_only", False), ("report_only", False)),
)
def test_strategy_evidence_trend_rejects_mutated_non_report_snapshot_flags(
    flag_name,
    flag_value,
):
    snapshot = _snapshot("local_evidence_observed")
    object.__setattr__(snapshot, flag_name, flag_value)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_strategy_evidence_trend_report(
            (snapshot,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_strategy_evidence_trend_dataclasses_are_frozen_and_revalidate_invariants():
    report = build_paper_strategy_evidence_trend_report(
        (_snapshot("local_evidence_observed"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.snapshot_report_count = 2
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="snapshot_report_count"):
        replace(report, snapshot_report_count=-1)
    with pytest.raises(ValueError, match="latest_status"):
        replace(report, latest_status="unknown")
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(report, latest_evidence_gap_names=("unknown_gap",))
    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=tuple(reversed(report.status_rows)))
    with pytest.raises(ValueError, match="gap_rows"):
        replace(report, gap_rows=tuple(reversed(report.gap_rows)))


def test_strategy_evidence_trend_rejects_inconsistent_latest_gap_state():
    gap_report = build_paper_strategy_evidence_trend_report(
        (
            _snapshot(
                "local_evidence_gaps",
                evidence_gap_names=("missing_outcome_evidence",),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    risk_report = build_paper_strategy_evidence_trend_report(
        (
            _snapshot(
                "local_risk_flags",
                evidence_gap_names=("negative_cost_adjusted_edges",),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(gap_report, latest_evidence_gap_names=())
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(
            gap_report,
            latest_evidence_gap_names=("missing_strategy_audit_history",),
        )
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(
            risk_report,
            latest_evidence_gap_names=("missing_outcome_evidence",),
        )


def test_strategy_evidence_trend_keeps_compatibility_aliases():
    report = build_paper_strategy_evidence_trend_report(
        (_snapshot("local_evidence_observed"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.snapshot_count == report.snapshot_report_count
    assert report.latest_snapshot_status == report.latest_status
    assert report.first_snapshot_generated_at == report.first_report_generated_at
    assert report.latest_snapshot_generated_at == report.latest_report_generated_at
    assert report.latest_gap_names == report.latest_evidence_gap_names


def test_strategy_evidence_trend_rejects_nonquantized_status_row_ratios():
    report = build_paper_strategy_evidence_trend_report(
        (
            _snapshot(
                "local_evidence_gaps",
                evidence_gap_names=("missing_outcome_evidence",),
            ),
            _snapshot("local_evidence_observed"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    mutated_row = replace(report.status_rows[-1])
    object.__setattr__(mutated_row, "snapshot_ratio", Decimal("0.5"))
    status_rows = (*report.status_rows[:-1], mutated_row)

    with pytest.raises(ValueError, match="snapshot_ratio|status_rows ratios"):
        replace(report, status_rows=status_rows)


def test_strategy_evidence_trend_row_dataclasses_require_quantized_ratios():
    with pytest.raises(ValueError, match="snapshot_ratio"):
        PaperStrategyEvidenceTrendStatusRow(
            "local_evidence_observed",
            1,
            Decimal("0.5"),
        )
    with pytest.raises(ValueError, match="gap_ratio"):
        PaperStrategyEvidenceTrendGapRow(
            "missing_outcome_evidence",
            1,
            Decimal("0.5"),
        )


def test_strategy_evidence_trend_rejects_nonquantized_gap_row_ratios():
    report = build_paper_strategy_evidence_trend_report(
        (
            _snapshot(
                "local_evidence_gaps",
                evidence_gap_names=("missing_outcome_evidence",),
            ),
            _snapshot("local_evidence_observed"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    mutated_row = replace(report.gap_rows[3])
    object.__setattr__(mutated_row, "gap_ratio", Decimal("0.5"))
    gap_rows = (
        *report.gap_rows[:3],
        mutated_row,
        *report.gap_rows[4:],
    )

    with pytest.raises(ValueError, match="gap_ratio|gap_rows ratios"):
        replace(report, gap_rows=gap_rows)
