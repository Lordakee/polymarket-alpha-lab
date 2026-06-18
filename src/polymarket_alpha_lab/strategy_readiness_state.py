"""Pure paper-only reducer for strategy readiness gate signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


READINESS_STATUSES = ("blocked", "watch", "pass")
HARD_FLAGS = (
    ("paper_only", True),
    ("report_only", True),
    ("readonly", True),
)
NO_SIGNALS_SIGNAL = (
    "strategy_readiness_state",
    "blocked",
    ("no_signals",),
    100,
    None,
    None,
)


@dataclass(frozen=True)
class PaperStrategyReadinessSignal:
    source_name: str
    status: str
    reason_codes: tuple[str, ...]
    severity: int
    observed_value: Decimal | int | str | None = None
    threshold: Decimal | int | str | None = None

    def __post_init__(self) -> None:
        _require_canonical_string("source_name", self.source_name)
        if type(self.status) is not str or self.status not in READINESS_STATUSES:
            raise ValueError("status must be one of ('blocked', 'watch', 'pass')")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_nonnegative_int("severity", self.severity)
        _require_gate_scalar("observed_value", self.observed_value)
        _require_gate_scalar("threshold", self.threshold)


@dataclass(frozen=True)
class PaperStrategyReadinessStateReport:
    generated_at: datetime
    config_version: str
    signal_count: int
    blocking_count: int
    watch_count: int
    passed_count: int
    overall_status: str
    signals: tuple[PaperStrategyReadinessSignal, ...]
    flags: tuple[tuple[str, bool], ...] = HARD_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "blocking_count",
            "watch_count",
            "passed_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if type(self.overall_status) is not str or self.overall_status not in (
            READINESS_STATUSES
        ):
            raise ValueError("overall_status must be one of ('blocked', 'watch', 'pass')")
        object.__setattr__(self, "signals", _normalize_signals(self.signals))
        object.__setattr__(self, "flags", _normalize_flags(self.flags))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_readiness_state_report(
    signals: list[PaperStrategyReadinessSignal]
    | tuple[PaperStrategyReadinessSignal, ...],
    *,
    config_version: str,
    generated_at: datetime,
) -> PaperStrategyReadinessStateReport:
    """Aggregate pure readiness signals without external side effects."""

    _require_canonical_string("config_version", config_version)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_signals = _normalize_input_signals(signals)
    if not normalized_signals:
        normalized_signals = (PaperStrategyReadinessSignal(*NO_SIGNALS_SIGNAL),)
    ordered_signals = _order_signals(normalized_signals)

    blocking_count = _status_count(ordered_signals, "blocked")
    watch_count = _status_count(ordered_signals, "watch")
    passed_count = _status_count(ordered_signals, "pass")

    return PaperStrategyReadinessStateReport(
        generated_at=generated_at,
        config_version=config_version,
        signal_count=len(ordered_signals),
        blocking_count=blocking_count,
        watch_count=watch_count,
        passed_count=passed_count,
        overall_status=_overall_status(
            signal_count=len(ordered_signals),
            blocking_count=blocking_count,
            watch_count=watch_count,
        ),
        signals=ordered_signals,
        flags=HARD_FLAGS,
    )


def _normalize_input_signals(
    signals: list[PaperStrategyReadinessSignal]
    | tuple[PaperStrategyReadinessSignal, ...],
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple of PaperStrategyReadinessSignal")
    normalized = tuple(signals)
    for signal in normalized:
        if type(signal) is not PaperStrategyReadinessSignal:
            raise ValueError("signals must contain PaperStrategyReadinessSignal values")
    return normalized


def _normalize_signals(
    signals: tuple[PaperStrategyReadinessSignal, ...],
) -> tuple[PaperStrategyReadinessSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    for signal in normalized:
        if type(signal) is not PaperStrategyReadinessSignal:
            raise ValueError("signals must contain PaperStrategyReadinessSignal values")
    if normalized != _order_signals(normalized):
        raise ValueError("signals must use deterministic ordering")
    return normalized


def _order_signals(
    signals: tuple[PaperStrategyReadinessSignal, ...],
) -> tuple[PaperStrategyReadinessSignal, ...]:
    return tuple(
        sorted(
            signals,
            key=lambda signal: (-signal.severity, signal.source_name),
        ),
    )


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must include at least one code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return reason_codes


def _normalize_flags(flags: tuple[tuple[str, bool], ...]) -> tuple[tuple[str, bool], ...]:
    if isinstance(flags, (str, bytes)):
        raise ValueError("flags must be an iterable")
    try:
        normalized = tuple(flags)
    except TypeError as exc:
        raise ValueError("flags must be an iterable") from exc
    if normalized != HARD_FLAGS:
        raise ValueError("flags must exactly match paper_only/report_only/readonly")
    for flag_name, flag_value in normalized:
        if type(flag_name) is not str:
            raise ValueError("flags names must be strings")
        if type(flag_value) is not bool:
            raise ValueError("flags values must be bools")
    return normalized


def _validate_report_consistency(report: PaperStrategyReadinessStateReport) -> None:
    if report.signal_count != len(report.signals):
        raise ValueError("signal_count must match signals")
    if report.signal_count == 0:
        raise ValueError("signal_count must include the no_signals blocker")
    if (
        report.blocking_count + report.watch_count + report.passed_count
        != report.signal_count
    ):
        raise ValueError("status counts must sum to signal_count")
    if report.blocking_count != _status_count(report.signals, "blocked"):
        raise ValueError("blocking_count must match blocked signals")
    if report.watch_count != _status_count(report.signals, "watch"):
        raise ValueError("watch_count must match watch signals")
    if report.passed_count != _status_count(report.signals, "pass"):
        raise ValueError("passed_count must match pass signals")
    if report.overall_status != _overall_status(
        signal_count=report.signal_count,
        blocking_count=report.blocking_count,
        watch_count=report.watch_count,
    ):
        raise ValueError("overall_status must match signal statuses")


def _overall_status(
    *,
    signal_count: int,
    blocking_count: int,
    watch_count: int,
) -> str:
    if blocking_count > 0:
        return "blocked"
    if watch_count > 0:
        return "watch"
    if signal_count > 0:
        return "pass"
    return "blocked"


def _status_count(
    signals: tuple[PaperStrategyReadinessSignal, ...],
    status: str,
) -> int:
    return sum(1 for signal in signals if signal.status == status)


def _require_gate_scalar(field_name: str, value: Any) -> None:
    if value is None:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return
    if type(value) is int:
        return
    if type(value) is str:
        if not value or value.strip() != value:
            raise ValueError(f"{field_name} must be a canonical nonblank string")
        return
    raise ValueError(f"{field_name} must be a Decimal, int, str, or None")


def _as_utc(value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "PaperStrategyReadinessSignal",
    "PaperStrategyReadinessStateReport",
    "build_paper_strategy_readiness_state_report",
)
