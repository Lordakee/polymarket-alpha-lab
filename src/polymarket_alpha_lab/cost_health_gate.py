"""Pure paper-only cost health gate for the strategy pre-layer.

This reducer only evaluates already-built paper reports or caller-supplied
summary rows. It is side-effect free and only summarizes in-memory inputs.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.edge_cost_summary_trend import (
    PaperEdgeCostSummaryTrendReport,
)
from polymarket_alpha_lab.paper_trade_cost_trend import PaperTradeCostTrendReport


ZERO = Decimal("0")

GATE_NAMES = (
    "data_completeness",
    "average_cost_drag",
    "spread_drag",
    "net_edge_after_cost",
    "negative_net_edge_streak",
)
GATE_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = (
    "paper_cost_health_pass",
    "paper_cost_health_watch",
    "paper_cost_health_blocked",
)
SOURCE_REPORT_KINDS = (
    "summary_rows",
    "paper_trade_cost_trend",
    "paper_edge_cost_summary_trend",
)


@dataclass(frozen=True)
class PaperCostHealthGateConfig:
    config_version: str
    max_average_cost_drag: Decimal = Decimal("0.030000")
    max_spread_drag: Decimal = Decimal("0.010000")
    min_net_edge_after_cost: Decimal = Decimal("0.010000")
    max_consecutive_negative_net_edge_periods: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "max_average_cost_drag",
            self.max_average_cost_drag,
        )
        _require_nonnegative_decimal("max_spread_drag", self.max_spread_drag)
        _require_decimal("min_net_edge_after_cost", self.min_net_edge_after_cost)
        _require_nonnegative_int(
            "max_consecutive_negative_net_edge_periods",
            self.max_consecutive_negative_net_edge_periods,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperCostHealthSummaryRow:
    observed_at: datetime
    average_cost_drag: Decimal | None
    spread_drag: Decimal | None
    net_edge_after_cost: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_optional_nonnegative_decimal(
            "average_cost_drag",
            self.average_cost_drag,
        )
        _require_optional_nonnegative_decimal("spread_drag", self.spread_drag)
        _require_optional_decimal("net_edge_after_cost", self.net_edge_after_cost)
        _require_hard_flags(self)


@dataclass(frozen=True)
class PaperCostHealthGateRow:
    gate_name: str
    status: str
    observed_value: Decimal | int | str | None
    threshold_value: Decimal | int | str | None
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known cost health gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known cost health gate status")
        _require_gate_value("observed_value", self.observed_value)
        _require_gate_value("threshold_value", self.threshold_value)
        reason_codes = _normalize_reason_codes(self.reason_codes)
        _require_non_pass_row_reason_codes(self.status, reason_codes)
        object.__setattr__(
            self,
            "reason_codes",
            reason_codes,
        )


@dataclass(frozen=True)
class PaperCostHealthGateReport:
    generated_at: datetime
    config_version: str
    source_report_kind: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
    status: str
    gate_rows: tuple[PaperCostHealthGateRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.source_report_kind not in SOURCE_REPORT_KINDS:
            raise ValueError("source_report_kind must be a known source kind")
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "first_source_generated_at",
            _as_optional_utc(self.first_source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_source_generated_at",
            _as_optional_utc(self.latest_source_generated_at),
        )
        if self.status not in REPORT_STATUSES:
            raise ValueError("status must be a known cost health report status")
        object.__setattr__(self, "gate_rows", _normalize_gate_rows(self.gate_rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class _SourceMetrics:
    source_report_kind: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
    average_cost_drag: Decimal | None
    spread_drag: Decimal | None
    net_edge_after_cost: Decimal | None
    negative_net_edge_streak: int | None


def build_paper_cost_health_gate_report(
    source: (
        PaperTradeCostTrendReport
        | PaperEdgeCostSummaryTrendReport
        | Iterable[PaperCostHealthSummaryRow]
    ),
    *,
    config: PaperCostHealthGateConfig,
    generated_at: datetime,
) -> PaperCostHealthGateReport:
    """Evaluate paper cost health thresholds over already-reduced evidence."""

    if type(config) is not PaperCostHealthGateConfig:
        raise ValueError("config must be a PaperCostHealthGateConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    metrics = _extract_source_metrics(source)
    gate_rows = _build_gate_rows(metrics, config)
    return PaperCostHealthGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_kind=metrics.source_report_kind,
        source_report_count=metrics.source_report_count,
        first_source_generated_at=metrics.first_source_generated_at,
        latest_source_generated_at=metrics.latest_source_generated_at,
        status=_report_status(gate_rows),
        gate_rows=gate_rows,
        reason_codes=_report_reason_codes(gate_rows),
    )


def _extract_source_metrics(source: object) -> _SourceMetrics:
    if type(source) is PaperTradeCostTrendReport:
        _require_source_flags(source)
        return _trade_cost_trend_metrics(source)
    if type(source) is PaperEdgeCostSummaryTrendReport:
        _require_source_flags(source)
        return _edge_cost_summary_trend_metrics(source)
    return _summary_row_metrics(_normalize_summary_rows(source))


def _trade_cost_trend_metrics(report: PaperTradeCostTrendReport) -> _SourceMetrics:
    return _SourceMetrics(
        source_report_kind="paper_trade_cost_trend",
        source_report_count=report.cost_audit_report_count,
        first_source_generated_at=report.first_report_generated_at,
        latest_source_generated_at=report.latest_report_generated_at,
        average_cost_drag=report.worst_observed_mean_edge_cost_drag,
        spread_drag=None,
        net_edge_after_cost=report.latest_mean_cost_adjusted_edge,
        negative_net_edge_streak=report.consecutive_negative_cost_adjusted_edge_count,
    )


def _edge_cost_summary_trend_metrics(
    report: PaperEdgeCostSummaryTrendReport,
) -> _SourceMetrics:
    return _SourceMetrics(
        source_report_kind="paper_edge_cost_summary_trend",
        source_report_count=report.edge_cost_report_count,
        first_source_generated_at=report.first_report_generated_at,
        latest_source_generated_at=report.latest_report_generated_at,
        average_cost_drag=report.worst_observed_mean_edge_cost_drag,
        spread_drag=None,
        net_edge_after_cost=report.latest_mean_executable_edge_ratio,
        negative_net_edge_streak=None,
    )


def _summary_row_metrics(rows: tuple[PaperCostHealthSummaryRow, ...]) -> _SourceMetrics:
    negative_net_edge_streak = None
    if rows:
        negative_net_edge_streak = _negative_net_edge_streak(rows)
    return _SourceMetrics(
        source_report_kind="summary_rows",
        source_report_count=len(rows),
        first_source_generated_at=rows[0].observed_at if rows else None,
        latest_source_generated_at=rows[-1].observed_at if rows else None,
        average_cost_drag=_max_optional(row.average_cost_drag for row in rows),
        spread_drag=_max_optional(row.spread_drag for row in rows),
        net_edge_after_cost=rows[-1].net_edge_after_cost if rows else None,
        negative_net_edge_streak=negative_net_edge_streak,
    )


def _build_gate_rows(
    metrics: _SourceMetrics,
    config: PaperCostHealthGateConfig,
) -> tuple[PaperCostHealthGateRow, ...]:
    return (
        _data_completeness_row(metrics.source_report_count),
        _max_decimal_row(
            gate_name="average_cost_drag",
            observed_value=metrics.average_cost_drag,
            threshold_value=config.max_average_cost_drag,
            within_code="average_cost_drag_within_threshold",
            missing_code="average_cost_drag_missing",
            breach_code="average_cost_drag_above_threshold",
        ),
        _max_decimal_row(
            gate_name="spread_drag",
            observed_value=metrics.spread_drag,
            threshold_value=config.max_spread_drag,
            within_code="spread_drag_within_threshold",
            missing_code="spread_drag_missing",
            breach_code="spread_drag_above_threshold",
        ),
        _min_decimal_row(
            gate_name="net_edge_after_cost",
            observed_value=metrics.net_edge_after_cost,
            threshold_value=config.min_net_edge_after_cost,
            within_code="net_edge_after_cost_within_threshold",
            missing_code="net_edge_after_cost_missing",
            breach_code="net_edge_after_cost_below_threshold",
        ),
        _max_int_row(
            gate_name="negative_net_edge_streak",
            observed_value=metrics.negative_net_edge_streak,
            threshold_value=config.max_consecutive_negative_net_edge_periods,
            within_code="negative_net_edge_streak_within_threshold",
            missing_code="negative_net_edge_streak_unsupported",
            breach_code="negative_net_edge_streak_above_threshold",
        ),
    )


def _data_completeness_row(source_report_count: int) -> PaperCostHealthGateRow:
    if source_report_count == 0:
        return PaperCostHealthGateRow(
            gate_name="data_completeness",
            status="blocked",
            observed_value=0,
            threshold_value=">0",
            reason_codes=("empty_cost_health_source",),
        )
    return PaperCostHealthGateRow(
        gate_name="data_completeness",
        status="pass",
        observed_value=source_report_count,
        threshold_value=">0",
        reason_codes=("data_available",),
    )


def _max_decimal_row(
    *,
    gate_name: str,
    observed_value: Decimal | None,
    threshold_value: Decimal,
    within_code: str,
    missing_code: str,
    breach_code: str,
) -> PaperCostHealthGateRow:
    if observed_value is None:
        return PaperCostHealthGateRow(
            gate_name=gate_name,
            status="watch",
            observed_value=None,
            threshold_value=threshold_value,
            reason_codes=(missing_code,),
        )
    if observed_value > threshold_value:
        return PaperCostHealthGateRow(
            gate_name=gate_name,
            status="blocked",
            observed_value=observed_value,
            threshold_value=threshold_value,
            reason_codes=(breach_code,),
        )
    return PaperCostHealthGateRow(
        gate_name=gate_name,
        status="pass",
        observed_value=observed_value,
        threshold_value=threshold_value,
        reason_codes=(within_code,),
    )


def _min_decimal_row(
    *,
    gate_name: str,
    observed_value: Decimal | None,
    threshold_value: Decimal,
    within_code: str,
    missing_code: str,
    breach_code: str,
) -> PaperCostHealthGateRow:
    if observed_value is None:
        return PaperCostHealthGateRow(
            gate_name=gate_name,
            status="watch",
            observed_value=None,
            threshold_value=threshold_value,
            reason_codes=(missing_code,),
        )
    if observed_value < threshold_value:
        return PaperCostHealthGateRow(
            gate_name=gate_name,
            status="blocked",
            observed_value=observed_value,
            threshold_value=threshold_value,
            reason_codes=(breach_code,),
        )
    return PaperCostHealthGateRow(
        gate_name=gate_name,
        status="pass",
        observed_value=observed_value,
        threshold_value=threshold_value,
        reason_codes=(within_code,),
    )


def _max_int_row(
    *,
    gate_name: str,
    observed_value: int | None,
    threshold_value: int,
    within_code: str,
    missing_code: str,
    breach_code: str,
) -> PaperCostHealthGateRow:
    if observed_value is None:
        return PaperCostHealthGateRow(
            gate_name=gate_name,
            status="watch",
            observed_value=None,
            threshold_value=threshold_value,
            reason_codes=(missing_code,),
        )
    if observed_value > threshold_value:
        return PaperCostHealthGateRow(
            gate_name=gate_name,
            status="blocked",
            observed_value=observed_value,
            threshold_value=threshold_value,
            reason_codes=(breach_code,),
        )
    return PaperCostHealthGateRow(
        gate_name=gate_name,
        status="pass",
        observed_value=observed_value,
        threshold_value=threshold_value,
        reason_codes=(within_code,),
    )


def _report_status(gate_rows: tuple[PaperCostHealthGateRow, ...]) -> str:
    if any(row.status == "blocked" for row in gate_rows):
        return "paper_cost_health_blocked"
    if any(row.status == "watch" for row in gate_rows):
        return "paper_cost_health_watch"
    return "paper_cost_health_pass"


def _report_reason_codes(
    gate_rows: tuple[PaperCostHealthGateRow, ...],
) -> tuple[str, ...]:
    return tuple(
        code
        for row in gate_rows
        if row.status != "pass"
        for code in row.reason_codes
    )


def _normalize_summary_rows(source: object) -> tuple[PaperCostHealthSummaryRow, ...]:
    if isinstance(source, (str, bytes)) or not isinstance(source, Iterable):
        raise ValueError(
            "source must be a paper cost trend, edge cost summary trend, "
            "or iterable of PaperCostHealthSummaryRow values",
        )
    rows = tuple(source)
    for row in rows:
        if type(row) is not PaperCostHealthSummaryRow:
            raise ValueError("source must contain PaperCostHealthSummaryRow values")
        _require_source_flags(row)
    return rows


def _negative_net_edge_streak(
    rows: tuple[PaperCostHealthSummaryRow, ...],
) -> int | None:
    if any(row.net_edge_after_cost is None for row in rows):
        return None
    count = 0
    for row in reversed(rows):
        net_edge_after_cost = row.net_edge_after_cost
        if net_edge_after_cost is None or net_edge_after_cost >= ZERO:
            break
        count += 1
    return count


def _max_optional(values: Iterable[Decimal | None]) -> Decimal | None:
    available = tuple(value for value in values if value is not None)
    return max(available) if available else None


def _validate_report_consistency(report: PaperCostHealthGateReport) -> None:
    if tuple(row.gate_name for row in report.gate_rows) != GATE_NAMES:
        raise ValueError("gate_rows must cover cost health gates")
    if report.source_report_count == 0:
        _require_none(
            "first_source_generated_at",
            report.first_source_generated_at,
        )
        _require_none(
            "latest_source_generated_at",
            report.latest_source_generated_at,
        )
    else:
        if report.first_source_generated_at is None:
            raise ValueError("first_source_generated_at is required with source reports")
        if report.latest_source_generated_at is None:
            raise ValueError("latest_source_generated_at is required with source reports")
    if report.status != _report_status(report.gate_rows):
        raise ValueError("status must match gate rows")
    for row in report.gate_rows:
        _require_non_pass_row_reason_codes(row.status, row.reason_codes)
    if report.reason_codes != _report_reason_codes(report.gate_rows):
        raise ValueError("reason_codes must match non-passing gate rows")


def _normalize_gate_rows(
    gate_rows: tuple[PaperCostHealthGateRow, ...],
) -> tuple[PaperCostHealthGateRow, ...]:
    if isinstance(gate_rows, (str, bytes)):
        raise ValueError("gate_rows must be an iterable")
    try:
        rows = tuple(gate_rows)
    except TypeError as exc:
        raise ValueError("gate_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperCostHealthGateRow:
            raise ValueError("gate_rows must contain PaperCostHealthGateRow values")
    return rows


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        codes = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for code in codes:
        _require_canonical_string("reason_codes", code)
    return codes


def _require_non_pass_row_reason_codes(
    status: str,
    reason_codes: tuple[str, ...],
) -> None:
    if status != "pass" and not reason_codes:
        raise ValueError("non-passing gate rows must include reason_codes")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc("datetime", value)


def _require_source_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


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


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_gate_value(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return
    if type(value) in (int, str):
        if type(value) is str:
            _require_canonical_string(field_name, value)
        return
    raise ValueError(f"{field_name} must be a Decimal, int, string, or None")


def _require_none(field_name: str, value: object) -> None:
    if value is not None:
        raise ValueError(f"{field_name} must be None when there are no source reports")


__all__ = (
    "PaperCostHealthGateConfig",
    "PaperCostHealthSummaryRow",
    "PaperCostHealthGateRow",
    "PaperCostHealthGateReport",
    "build_paper_cost_health_gate_report",
)
