from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessSignal,
    PaperStrategyReadinessStateReport,
    build_paper_strategy_readiness_state_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-readiness-state-v0"
HARD_FLAGS = (
    ("paper_only", True),
    ("report_only", True),
    ("readonly", True),
)


def _signal(
    source_name: str = "calibration_gate",
    status: str = "pass",
    reason_codes: tuple[str, ...] = ("calibration_ready",),
    severity: int = 1,
    observed_value: Decimal | int | str | None = Decimal("0.120000"),
    threshold: Decimal | int | str | None = Decimal("0.150000"),
) -> PaperStrategyReadinessSignal:
    return PaperStrategyReadinessSignal(
        source_name=source_name,
        status=status,
        reason_codes=reason_codes,
        severity=severity,
        observed_value=observed_value,
        threshold=threshold,
    )


def _report(
    *signals: PaperStrategyReadinessSignal,
    generated_at: datetime = GENERATED_AT,
) -> PaperStrategyReadinessStateReport:
    return build_paper_strategy_readiness_state_report(
        signals,
        config_version=CONFIG_VERSION,
        generated_at=generated_at,
    )


def test_strategy_readiness_state_aggregates_status_counts_and_orders_signals():
    pass_signal = _signal(
        source_name="zeta_gate",
        status="pass",
        reason_codes=("zeta_ready",),
        severity=3,
        observed_value=7,
        threshold=5,
    )
    watch_signal = _signal(
        source_name="watch_gate",
        status="watch",
        reason_codes=("spread_near_limit",),
        severity=30,
        observed_value=Decimal("0.140000"),
        threshold=Decimal("0.150000"),
    )
    blocking_signal = _signal(
        source_name="alpha_gate",
        status="blocked",
        reason_codes=("insufficient_sample",),
        severity=30,
        observed_value="sample_count=2",
        threshold="sample_count>=5",
    )

    report = _report(pass_signal, watch_signal, blocking_signal)

    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.signal_count == 3
    assert report.blocking_count == 1
    assert report.watch_count == 1
    assert report.passed_count == 1
    assert report.overall_status == "blocked"
    assert tuple(signal.source_name for signal in report.signals) == (
        "alpha_gate",
        "watch_gate",
        "zeta_gate",
    )
    assert report.flags == HARD_FLAGS
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_strategy_readiness_state_watches_without_blockers_and_passes_with_pass_signals():
    watch_report = _report(
        _signal(
            source_name="calibration_gate",
            status="pass",
            reason_codes=("calibration_ready",),
            severity=1,
        ),
        _signal(
            source_name="liquidity_gate",
            status="watch",
            reason_codes=("liquidity_near_floor",),
            severity=10,
        ),
    )
    pass_report = _report(
        _signal(
            source_name="calibration_gate",
            status="pass",
            reason_codes=("calibration_ready",),
            severity=1,
        ),
        _signal(
            source_name="liquidity_gate",
            status="pass",
            reason_codes=("liquidity_ready",),
            severity=2,
        ),
    )

    assert watch_report.overall_status == "watch"
    assert watch_report.blocking_count == 0
    assert watch_report.watch_count == 1
    assert watch_report.passed_count == 1

    assert pass_report.overall_status == "pass"
    assert pass_report.blocking_count == 0
    assert pass_report.watch_count == 0
    assert pass_report.passed_count == 2


def test_strategy_readiness_state_empty_input_is_blocked_with_no_signals_reason():
    report = _report()

    assert report.signal_count == 1
    assert report.blocking_count == 1
    assert report.watch_count == 0
    assert report.passed_count == 0
    assert report.overall_status == "blocked"
    assert report.signals == (
        PaperStrategyReadinessSignal(
            source_name="strategy_readiness_state",
            status="blocked",
            reason_codes=("no_signals",),
            severity=100,
            observed_value=None,
            threshold=None,
        ),
    )
    assert report.flags == HARD_FLAGS


def test_strategy_readiness_state_normalizes_generated_at_to_utc():
    report = _report(
        _signal(),
        generated_at=datetime(2026, 6, 18, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)


def test_strategy_readiness_state_rejects_invalid_builder_inputs():
    valid_signal = _signal()

    for invalid_signals in (
        object(),
        "signals",
        b"signals",
        {"signal": valid_signal},
        (signal for signal in (valid_signal,)),
    ):
        with pytest.raises(ValueError, match="signals"):
            build_paper_strategy_readiness_state_report(
                invalid_signals,
                config_version=CONFIG_VERSION,
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperStrategyReadinessSignal"):
        build_paper_strategy_readiness_state_report(
            (object(),),
            config_version=CONFIG_VERSION,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config_version"):
        build_paper_strategy_readiness_state_report(
            (),
            config_version=" strategy-readiness-state-v0 ",
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_strategy_readiness_state_report(
            (),
            config_version=CONFIG_VERSION,
            generated_at="now",
        )


def test_strategy_readiness_signal_rejects_invalid_exact_scalar_types():
    class DerivedDecimal(Decimal):
        pass

    class DerivedInt(int):
        pass

    class DerivedString(str):
        pass

    with pytest.raises(ValueError, match="source_name"):
        _signal(source_name=DerivedString("calibration_gate"))
    with pytest.raises(ValueError, match="source_name"):
        _signal(source_name=" calibration_gate ")
    with pytest.raises(ValueError, match="status"):
        _signal(status="ready")
    with pytest.raises(ValueError, match="reason_codes"):
        _signal(reason_codes=("ready", "ready"))
    with pytest.raises(ValueError, match="reason_codes"):
        _signal(reason_codes=("ready ",))
    with pytest.raises(ValueError, match="severity"):
        _signal(severity=True)
    with pytest.raises(ValueError, match="severity"):
        _signal(severity=DerivedInt(1))
    with pytest.raises(ValueError, match="observed_value"):
        _signal(observed_value=True)
    with pytest.raises(ValueError, match="observed_value"):
        _signal(observed_value=DerivedDecimal("0.1"))
    with pytest.raises(ValueError, match="observed_value"):
        _signal(observed_value=DerivedString("sample_count=2"))
    with pytest.raises(ValueError, match="threshold"):
        _signal(threshold=0.1)


def test_strategy_readiness_state_dataclasses_are_frozen_and_revalidate_flags():
    signal = _signal()
    report = _report(
        signal,
        _signal(
            source_name="liquidity_gate",
            status="watch",
            reason_codes=("liquidity_near_floor",),
            severity=10,
        ),
    )

    with pytest.raises(FrozenInstanceError):
        signal.severity = 99
    with pytest.raises(FrozenInstanceError):
        report.overall_status = "blocked"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="flags"):
        replace(
            report,
            flags=(
                ("paper_only", True),
                ("readonly", True),
                ("report_only", True),
            ),
    )
    with pytest.raises(ValueError, match="signal_count"):
        replace(report, signal_count=3)
    with pytest.raises(ValueError, match="signals"):
        replace(report, signals=tuple(reversed(report.signals)))
