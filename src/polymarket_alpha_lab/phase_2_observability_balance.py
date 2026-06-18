"""Pure balance reducer for Phase 2 observability state reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN

from polymarket_alpha_lab.phase_2_observability_state import (
    BLOCKING_REASON_NAMES,
    PaperPhase2ObservabilityStateReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class PaperPhase2ObservabilityBalanceConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperPhase2ObservabilityBalanceReasonRow:
    blocking_reason_name: str
    occurrence_count: int
    occurrence_ratio: Decimal | None
    latest_present: bool

    def __post_init__(self) -> None:
        if self.blocking_reason_name not in BLOCKING_REASON_NAMES:
            raise ValueError("blocking_reason_name must be a known phase 2 reason")
        _require_nonnegative_int("occurrence_count", self.occurrence_count)
        _require_optional_probability_decimal(
            "occurrence_ratio",
            self.occurrence_ratio,
        )
        _require_bool("latest_present", self.latest_present)


@dataclass(frozen=True)
class PaperPhase2ObservabilityBalanceReport:
    generated_at: datetime
    config_version: str
    state_report_count: int
    ready_report_count: int
    not_ready_report_count: int
    ready_ratio: Decimal | None
    latest_phase_2_ready: bool | None
    latest_blocking_reason_names: tuple[str, ...]
    reason_rows: tuple[PaperPhase2ObservabilityBalanceReasonRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("state_report_count", self.state_report_count)
        _require_nonnegative_int("ready_report_count", self.ready_report_count)
        _require_nonnegative_int("not_ready_report_count", self.not_ready_report_count)
        _require_optional_probability_decimal("ready_ratio", self.ready_ratio)
        if self.latest_phase_2_ready is not None and type(self.latest_phase_2_ready) is not bool:
            raise ValueError("latest_phase_2_ready must be a bool or None")
        object.__setattr__(
            self,
            "latest_blocking_reason_names",
            _normalize_names(
                "latest_blocking_reason_names",
                self.latest_blocking_reason_names,
                BLOCKING_REASON_NAMES,
            ),
        )
        object.__setattr__(self, "reason_rows", _normalize_reason_rows(self.reason_rows))
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_phase_2_observability_balance_report(
    state_reports: list[PaperPhase2ObservabilityStateReport]
    | tuple[PaperPhase2ObservabilityStateReport, ...],
    *,
    config: PaperPhase2ObservabilityBalanceConfig,
    generated_at: datetime,
) -> PaperPhase2ObservabilityBalanceReport:
    if type(config) is not PaperPhase2ObservabilityBalanceConfig:
        raise ValueError("config must be a PaperPhase2ObservabilityBalanceConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    reports = _normalize_state_reports(state_reports)
    latest = reports[-1] if reports else None
    ready_report_count = sum(1 for report in reports if report.phase_2_ready)
    not_ready_report_count = len(reports) - ready_report_count
    reason_counts = {reason_name: 0 for reason_name in BLOCKING_REASON_NAMES}
    for report in reports:
        for reason_name in report.blocking_reason_names:
            reason_counts[reason_name] += 1
    latest_blocking_reason_names = (
        () if latest is None else latest.blocking_reason_names
    )
    latest_blocking_reason_names_set = set(latest_blocking_reason_names)

    return PaperPhase2ObservabilityBalanceReport(
        generated_at=generated_at,
        config_version=config.config_version,
        state_report_count=len(reports),
        ready_report_count=ready_report_count,
        not_ready_report_count=not_ready_report_count,
        ready_ratio=_ratio(ready_report_count, len(reports)),
        latest_phase_2_ready=None if latest is None else latest.phase_2_ready,
        latest_blocking_reason_names=latest_blocking_reason_names,
        reason_rows=tuple(
            PaperPhase2ObservabilityBalanceReasonRow(
                blocking_reason_name=reason_name,
                occurrence_count=reason_counts[reason_name],
                occurrence_ratio=_ratio(reason_counts[reason_name], len(reports)),
                latest_present=reason_name in latest_blocking_reason_names_set,
            )
            for reason_name in BLOCKING_REASON_NAMES
        ),
    )


def _normalize_state_reports(
    state_reports: list[PaperPhase2ObservabilityStateReport]
    | tuple[PaperPhase2ObservabilityStateReport, ...],
) -> tuple[PaperPhase2ObservabilityStateReport, ...]:
    if type(state_reports) not in (list, tuple):
        raise ValueError("state_reports must be a list or tuple")
    reports = tuple(state_reports)
    for report in reports:
        if type(report) is not PaperPhase2ObservabilityStateReport:
            raise ValueError(
                "state_reports must contain PaperPhase2ObservabilityStateReport values",
            )
        if report.paper_only is not True:
            raise ValueError("state_reports must contain paper_only reports")
        if report.report_only is not True:
            raise ValueError("state_reports must contain report_only reports")
        if report.readonly is not True:
            raise ValueError("state_reports must contain readonly reports")
    return reports


def _validate_report_consistency(
    report: PaperPhase2ObservabilityBalanceReport,
) -> None:
    if report.state_report_count == 0:
        if report.ready_report_count != 0:
            raise ValueError("ready_report_count must be zero without reports")
        if report.not_ready_report_count != 0:
            raise ValueError("not_ready_report_count must be zero without reports")
        if report.ready_ratio is not None:
            raise ValueError("ready_ratio must be absent without reports")
        if report.latest_phase_2_ready is not None:
            raise ValueError("latest_phase_2_ready must be absent without reports")
        if report.latest_blocking_reason_names:
            raise ValueError(
                "latest_blocking_reason_names must be absent without reports",
            )
        for row in report.reason_rows:
            if row.occurrence_count != 0:
                raise ValueError("reason_rows counts must be zero without reports")
            if row.occurrence_ratio is not None:
                raise ValueError("reason_rows ratios must be absent without reports")
            if row.latest_present:
                raise ValueError("reason_rows latest_present must be False without reports")
        return

    if report.ready_report_count + report.not_ready_report_count != report.state_report_count:
        raise ValueError("ready_report_count and not_ready_report_count must match state_report_count")
    if not _ratio_value_matches(
        report.ready_ratio,
        _ratio(report.ready_report_count, report.state_report_count),
    ):
        raise ValueError("ready_ratio must match ready_report_count")
    if report.latest_phase_2_ready is None:
        raise ValueError("latest_phase_2_ready is required with reports")
    if report.latest_phase_2_ready != (report.latest_blocking_reason_names == ()):
        raise ValueError("latest_phase_2_ready must match latest_blocking_reason_names")
    if report.latest_phase_2_ready is True and report.latest_blocking_reason_names:
        raise ValueError("latest_blocking_reason_names must be absent for ready reports")
    if report.latest_phase_2_ready is False and not report.latest_blocking_reason_names:
        raise ValueError("latest_blocking_reason_names must be present for blocked reports")

    latest_blocking_reason_names = set(report.latest_blocking_reason_names)
    if tuple(row.blocking_reason_name for row in report.reason_rows) != BLOCKING_REASON_NAMES:
        raise ValueError("reason_rows must cover phase 2 blocking reasons")
    if sum(row.occurrence_count for row in report.reason_rows) < 0:
        raise ValueError("reason_rows must be nonnegative")
    for row in report.reason_rows:
        if not _ratio_value_matches(
            row.occurrence_ratio,
            _ratio(row.occurrence_count, report.state_report_count),
        ):
            raise ValueError("reason_rows ratios must match occurrence counts")
        if row.latest_present != (row.blocking_reason_name in latest_blocking_reason_names):
            raise ValueError("reason_rows latest_present must match latest state")
        if row.latest_present and row.occurrence_count == 0:
            raise ValueError("reason_rows latest_present requires occurrences")


def _normalize_reason_rows(
    rows: tuple[PaperPhase2ObservabilityBalanceReasonRow, ...],
) -> tuple[PaperPhase2ObservabilityBalanceReasonRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperPhase2ObservabilityBalanceReasonRow:
            raise ValueError(
                "reason_rows must contain PaperPhase2ObservabilityBalanceReasonRow values",
            )
    if tuple(row.blocking_reason_name for row in normalized) != BLOCKING_REASON_NAMES:
        raise ValueError("reason_rows must cover phase 2 blocking reasons")
    return normalized


def _normalize_names(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in items:
        if item not in allowed_values:
            raise ValueError(f"{field_name} must contain known names")
    expected_items = tuple(item for item in allowed_values if item in items)
    if items != expected_items:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return items


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _ratio_value_matches(value: Decimal | None, expected: Decimal | None) -> bool:
    if value != expected:
        return False
    if expected is None:
        return value is None
    if type(value) is not Decimal:
        return False
    return (
        value == value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        and value.as_tuple().exponent == RATIO_QUANTUM.as_tuple().exponent
    )


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if (
        value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
        or value.as_tuple().exponent != RATIO_QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must align to {RATIO_QUANTUM}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None without reports")


__all__ = (
    "PaperPhase2ObservabilityBalanceConfig",
    "PaperPhase2ObservabilityBalanceReasonRow",
    "PaperPhase2ObservabilityBalanceReport",
    "build_paper_phase_2_observability_balance_report",
)
