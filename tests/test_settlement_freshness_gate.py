from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.settlement_freshness_gate import (
    PaperSettlementFreshnessGateConfig,
    PaperSettlementFreshnessGateReport,
    PaperSettlementFreshnessGateRow,
    build_paper_settlement_freshness_gate_report,
)


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _config(**overrides) -> PaperSettlementFreshnessGateConfig:
    values = {
        "config_version": "settlement-freshness-gate-v0",
        "max_pending_count": 1,
        "max_unresolved_age_hours": 4,
        "min_checked_market_count": 2,
    }
    values.update(overrides)
    return PaperSettlementFreshnessGateConfig(**values)


def _observation(
    generated_at: datetime,
    suffix: str,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=generated_at,
        source_packet_id=f"pkt-{suffix}",
        condition_id=f"0x{suffix}",
        token_id=f"tok-{suffix}",
        market_slug=f"market-{suffix}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.6000"),
        actual_outcome_value=Decimal("1"),
    )


def _tracking_report(
    *,
    generated_at: datetime = GENERATED_AT,
    total_markets_checked: int,
    resolved_count: int,
    pending_count: int,
    suffix: str,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OutcomeTrackingReport:
    observations = tuple(
        _observation(generated_at, f"{suffix}-{index}")
        for index in range(resolved_count)
    )
    forecast_evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=generated_at,
        )
        if observations
        else None
    )
    return OutcomeTrackingReport(
        generated_at=generated_at,
        config_version="outcome-tracker-v1",
        total_markets_checked=total_markets_checked,
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=forecast_evidence_report,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _freshness_report(
    *reports: OutcomeTrackingReport,
    generated_at: datetime = GENERATED_AT,
):
    return build_outcome_freshness_report(
        reports,
        config=OutcomeFreshnessConfig(
            config_version="outcome-freshness-v0",
            stale_after_seconds=86_400,
        ),
        generated_at=generated_at,
    )


def _build(source, **config_overrides) -> PaperSettlementFreshnessGateReport:
    return build_paper_settlement_freshness_gate_report(
        source,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _row_statuses(report: PaperSettlementFreshnessGateReport) -> dict[str, str]:
    return {row.gate_name: row.status for row in report.gate_rows}


def _direct_report(
    *,
    source_report_count: int,
    latest_check_generated_at: datetime | None,
    checked_market_count: int,
    pending_count: int,
    stale_pending_count: int,
    latest_check_age_hours: Decimal | None,
    gate_rows: tuple[PaperSettlementFreshnessGateRow, ...],
) -> PaperSettlementFreshnessGateReport:
    block_reasons = tuple(row.reason for row in gate_rows if row.status == "block")
    watch_reasons = tuple(row.reason for row in gate_rows if row.status == "watch")
    block_count = len(block_reasons)
    watch_count = len(watch_reasons)
    return PaperSettlementFreshnessGateReport(
        generated_at=GENERATED_AT,
        config_version="settlement-freshness-gate-v0",
        source_kind="outcome_freshness",
        source_report_count=source_report_count,
        latest_check_generated_at=latest_check_generated_at,
        checked_market_count=checked_market_count,
        pending_count=pending_count,
        stale_pending_count=stale_pending_count,
        latest_check_age_hours=latest_check_age_hours,
        status="block" if block_count > 0 else "watch" if watch_count > 0 else "pass",
        gate_count=len(gate_rows),
        pass_count=sum(1 for row in gate_rows if row.status == "pass"),
        watch_count=watch_count,
        block_count=block_count,
        gate_rows=gate_rows,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
    )


def test_settlement_freshness_gate_passes_when_source_is_current_and_covered():
    source = _freshness_report(
        _tracking_report(
            generated_at=datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
            total_markets_checked=5,
            resolved_count=5,
            pending_count=0,
            suffix="pass",
        ),
    )

    report = _build(source, min_checked_market_count=5)

    assert isinstance(report, PaperSettlementFreshnessGateReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "settlement-freshness-gate-v0"
    assert report.source_kind == "outcome_freshness"
    assert report.source_report_count == 1
    assert report.latest_check_generated_at == datetime(2026, 6, 17, 17, 0, tzinfo=UTC)
    assert report.checked_market_count == 5
    assert report.pending_count == 0
    assert report.stale_pending_count == 0
    assert report.latest_check_age_hours == Decimal("1.000000")
    assert report.status == "pass"
    assert report.gate_count == 3
    assert report.pass_count == 3
    assert report.watch_count == 0
    assert report.block_count == 0
    assert _row_statuses(report) == {
        "checking_coverage": "pass",
        "pending_count": "pass",
        "unresolved_age": "pass",
    }
    assert report.block_reasons == ()
    assert report.watch_reasons == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_settlement_freshness_gate_blocks_stale_pending_outcomes():
    source = _freshness_report(
        _tracking_report(
            generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
            total_markets_checked=4,
            resolved_count=1,
            pending_count=3,
            suffix="stale-pending",
        ),
    )

    report = _build(source, min_checked_market_count=1)

    assert report.status == "block"
    assert report.checked_market_count == 4
    assert report.pending_count == 3
    assert report.stale_pending_count == 3
    assert report.latest_check_age_hours == Decimal("6.000000")
    assert report.block_count == 2
    assert report.watch_count == 0
    assert _row_statuses(report) == {
        "checking_coverage": "pass",
        "pending_count": "block",
        "unresolved_age": "block",
    }
    assert report.block_reasons == (
        "Pending settlement count exceeds the configured maximum.",
        "Pending settlement outcomes are older than the configured maximum age.",
    )


def test_settlement_freshness_gate_watches_empty_and_insufficient_checking_coverage():
    empty = _build(_freshness_report())

    assert empty.status == "watch"
    assert empty.source_report_count == 0
    assert empty.checked_market_count == 0
    assert empty.pending_count == 0
    assert empty.latest_check_generated_at is None
    assert empty.latest_check_age_hours is None
    assert _row_statuses(empty)["checking_coverage"] == "watch"
    assert empty.watch_reasons == (
        "No settlement freshness source checks are available.",
    )

    insufficient = _build(
        _freshness_report(
            _tracking_report(
                total_markets_checked=1,
                resolved_count=1,
                pending_count=0,
                suffix="low-coverage",
            ),
        ),
    )

    assert insufficient.status == "watch"
    assert insufficient.checked_market_count == 1
    assert _row_statuses(insufficient)["checking_coverage"] == "watch"
    assert insufficient.watch_reasons == (
        "Settlement checking coverage is below the configured floor.",
    )


def test_settlement_freshness_gate_accepts_tracking_source_and_normalizes_utc():
    generated_at = datetime(2026, 6, 17, 13, 0, tzinfo=timezone(timedelta(hours=-5)))
    source_generated_at = datetime(
        2026,
        6,
        17,
        10,
        0,
        tzinfo=timezone(timedelta(hours=-7)),
    )
    source = _tracking_report(
        generated_at=source_generated_at,
        total_markets_checked=2,
        resolved_count=1,
        pending_count=1,
        suffix="tracking-source",
    )

    report = build_paper_settlement_freshness_gate_report(
        source,
        config=_config(max_pending_count=1, max_unresolved_age_hours=2),
        generated_at=generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
    assert report.latest_check_generated_at == datetime(2026, 6, 17, 17, 0, tzinfo=UTC)
    assert report.latest_check_age_hours == Decimal("1.000000")
    assert report.source_kind == "outcome_tracking"
    assert report.source_report_count == 1
    assert report.status == "pass"


def test_settlement_freshness_gate_rejects_invalid_inputs_and_source_flags():
    source = _freshness_report(
        _tracking_report(
            total_markets_checked=2,
            resolved_count=2,
            pending_count=0,
            suffix="valid-source",
        ),
    )

    with pytest.raises(ValueError, match="source"):
        build_paper_settlement_freshness_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_settlement_freshness_gate_report(
            source,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_settlement_freshness_gate_report(
            source,
            config=_config(),
            generated_at="2026-06-17",
        )

    non_paper = replace(source)
    object.__setattr__(non_paper, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _build(non_paper)

    non_report = replace(source)
    object.__setattr__(non_report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _build(non_report)

    writable = replace(source)
    object.__setattr__(writable, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _build(writable)

    for flag_name in ("paper_only", "report_only", "readonly"):
        tampered_tracking = _tracking_report(
            total_markets_checked=2,
            resolved_count=2,
            pending_count=0,
            suffix=f"tampered-tracking-{flag_name}",
        )
        object.__setattr__(tampered_tracking, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            _build(tampered_tracking)


def test_settlement_freshness_gate_rejects_direct_report_passing_low_coverage():
    gate_rows = (
        PaperSettlementFreshnessGateRow(
            gate_name="checking_coverage",
            status="pass",
            reason="Settlement checking coverage meets the configured floor.",
            observed_value=1,
            threshold=2,
        ),
        PaperSettlementFreshnessGateRow(
            gate_name="pending_count",
            status="pass",
            reason="Pending settlement count is within the configured maximum.",
            observed_value=0,
            threshold=1,
        ),
        PaperSettlementFreshnessGateRow(
            gate_name="unresolved_age",
            status="pass",
            reason="Pending settlement outcomes are within the configured age.",
            observed_value=Decimal("1.000000"),
            threshold=Decimal("4.000000"),
        ),
    )

    with pytest.raises(ValueError, match="checking_coverage"):
        _direct_report(
            source_report_count=1,
            latest_check_generated_at=datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
            checked_market_count=1,
            pending_count=0,
            stale_pending_count=0,
            latest_check_age_hours=Decimal("1.000000"),
            gate_rows=gate_rows,
        )


def test_settlement_freshness_gate_rejects_direct_report_passing_excess_pending_count():
    gate_rows = (
        PaperSettlementFreshnessGateRow(
            gate_name="checking_coverage",
            status="pass",
            reason="Settlement checking coverage meets the configured floor.",
            observed_value=3,
            threshold=2,
        ),
        PaperSettlementFreshnessGateRow(
            gate_name="pending_count",
            status="pass",
            reason="Pending settlement count is within the configured maximum.",
            observed_value=2,
            threshold=1,
        ),
        PaperSettlementFreshnessGateRow(
            gate_name="unresolved_age",
            status="pass",
            reason="Pending settlement outcomes are within the configured age.",
            observed_value=Decimal("1.000000"),
            threshold=Decimal("4.000000"),
        ),
    )

    with pytest.raises(ValueError, match="pending_count"):
        _direct_report(
            source_report_count=1,
            latest_check_generated_at=datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
            checked_market_count=3,
            pending_count=2,
            stale_pending_count=0,
            latest_check_age_hours=Decimal("1.000000"),
            gate_rows=gate_rows,
        )


def test_settlement_freshness_gate_rejects_direct_report_passing_stale_unresolved_age():
    gate_rows = (
        PaperSettlementFreshnessGateRow(
            gate_name="checking_coverage",
            status="pass",
            reason="Settlement checking coverage meets the configured floor.",
            observed_value=3,
            threshold=2,
        ),
        PaperSettlementFreshnessGateRow(
            gate_name="pending_count",
            status="pass",
            reason="Pending settlement count is within the configured maximum.",
            observed_value=1,
            threshold=1,
        ),
        PaperSettlementFreshnessGateRow(
            gate_name="unresolved_age",
            status="pass",
            reason="Pending settlement outcomes are within the configured age.",
            observed_value=Decimal("5.000000"),
            threshold=Decimal("4.000000"),
        ),
    )

    with pytest.raises(ValueError, match="unresolved_age"):
        _direct_report(
            source_report_count=1,
            latest_check_generated_at=datetime(2026, 6, 17, 13, 0, tzinfo=UTC),
            checked_market_count=3,
            pending_count=1,
            stale_pending_count=1,
            latest_check_age_hours=Decimal("5.000000"),
            gate_rows=gate_rows,
        )


def test_settlement_freshness_gate_dataclasses_are_frozen_and_hard_flagged():
    config = _config()
    report = _build(
        _freshness_report(
            _tracking_report(
                total_markets_checked=2,
                resolved_count=2,
                pending_count=0,
                suffix="frozen",
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.max_pending_count = 2
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.gate_rows[0].status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


@pytest.mark.parametrize(
    ("factory", "match"),
    (
        (
            lambda: _config(
                config_version=_StringSubclass("settlement-freshness-gate-v0"),
            ),
            "config_version",
        ),
        (lambda: _config(max_pending_count=True), "max_pending_count"),
        (lambda: _config(max_pending_count=_IntSubclass(1)), "max_pending_count"),
        (lambda: _config(max_unresolved_age_hours="4"), "max_unresolved_age_hours"),
        (
            lambda: _config(min_checked_market_count=Decimal("2")),
            "min_checked_market_count",
        ),
        (
            lambda: build_paper_settlement_freshness_gate_report(
                _freshness_report(),
                config=_config(),
                generated_at=_DatetimeSubclass(2026, 6, 17, 18, 0, tzinfo=UTC),
            ),
            "generated_at",
        ),
        (
            lambda: replace(
                _build(
                    _freshness_report(
                        _tracking_report(
                            total_markets_checked=2,
                            resolved_count=2,
                            pending_count=0,
                            suffix="scalar",
                        ),
                    ),
                ),
                checked_market_count=_IntSubclass(2),
            ),
            "checked_market_count",
        ),
        (
            lambda: replace(
                _build(
                    _freshness_report(
                        _tracking_report(
                            total_markets_checked=2,
                            resolved_count=2,
                            pending_count=0,
                            suffix="decimal-subclass",
                        ),
                    ),
                ),
                latest_check_age_hours=_DecimalSubclass("1.000000"),
            ),
            "latest_check_age_hours",
        ),
        (
            lambda: PaperSettlementFreshnessGateRow(
                gate_name="checking_coverage",
                status="pass",
                reason="Coverage is sufficient.",
                observed_value=True,
                threshold=1,
            ),
            "observed_value",
        ),
        (
            lambda: PaperSettlementFreshnessGateRow(
                gate_name="checking_coverage",
                status="pass",
                reason="Coverage is sufficient.",
                observed_value=1,
                threshold=1.0,
            ),
            "threshold",
        ),
    ),
)
def test_settlement_freshness_gate_rejects_exact_scalar_type_violations(
    factory,
    match,
):
    with pytest.raises(ValueError, match=match):
        factory()
