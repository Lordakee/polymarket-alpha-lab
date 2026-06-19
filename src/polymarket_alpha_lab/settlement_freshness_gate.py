from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.outcome_freshness import OutcomeFreshnessReport
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport


__all__ = (
    "PaperSettlementFreshnessGateConfig",
    "PaperSettlementFreshnessGateRow",
    "PaperSettlementFreshnessGateReport",
    "build_paper_settlement_freshness_gate_report",
)


HOUR_SECONDS = Decimal("3600")
RATIO_QUANTUM = Decimal("0.000001")
GATE_NAMES = ("checking_coverage", "pending_count", "unresolved_age")
GATE_STATUSES = ("pass", "watch", "block")
SOURCE_KINDS = ("outcome_freshness", "outcome_tracking")
EMPTY_SOURCE_REASON = "No settlement freshness source checks are available."
LOW_COVERAGE_REASON = "Settlement checking coverage is below the configured floor."
PENDING_LIMIT_REASON = "Pending settlement count exceeds the configured maximum."
STALE_PENDING_REASON = (
    "Pending settlement outcomes are older than the configured maximum age."
)
CHECKING_COVERAGE_PASS_REASON = "Settlement checking coverage meets the configured floor."
PENDING_COUNT_PASS_REASON = "Pending settlement count is within the configured maximum."
UNRESOLVED_AGE_PASS_REASON = (
    "Pending settlement outcomes are within the configured age."
)


@dataclass(frozen=True)
class PaperSettlementFreshnessGateConfig:
    config_version: str
    max_pending_count: int
    max_unresolved_age_hours: int
    min_checked_market_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("max_pending_count", self.max_pending_count)
        _require_nonnegative_int(
            "max_unresolved_age_hours",
            self.max_unresolved_age_hours,
        )
        _require_nonnegative_int(
            "min_checked_market_count",
            self.min_checked_market_count,
        )


@dataclass(frozen=True)
class PaperSettlementFreshnessGateRow:
    gate_name: str
    status: str
    reason: str
    observed_value: int | Decimal | None
    threshold: int | Decimal | None

    def __post_init__(self) -> None:
        if self.gate_name not in GATE_NAMES:
            raise ValueError("gate_name must be a known gate")
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known gate status")
        _require_canonical_string("reason", self.reason)
        _require_optional_scalar("observed_value", self.observed_value)
        _require_optional_scalar("threshold", self.threshold)


@dataclass(frozen=True)
class PaperSettlementFreshnessGateReport:
    generated_at: datetime
    config_version: str
    source_kind: str
    source_report_count: int
    latest_check_generated_at: datetime | None
    checked_market_count: int
    pending_count: int
    stale_pending_count: int
    latest_check_age_hours: Decimal | None
    status: str
    gate_count: int
    pass_count: int
    watch_count: int
    block_count: int
    gate_rows: tuple[PaperSettlementFreshnessGateRow, ...]
    block_reasons: tuple[str, ...]
    watch_reasons: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "latest_check_generated_at",
            _as_optional_utc(
                "latest_check_generated_at",
                self.latest_check_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        if self.source_kind not in SOURCE_KINDS:
            raise ValueError("source_kind must be a known source kind")
        for field_name in (
            "source_report_count",
            "checked_market_count",
            "pending_count",
            "stale_pending_count",
            "gate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_decimal("latest_check_age_hours", self.latest_check_age_hours)
        if self.status not in GATE_STATUSES:
            raise ValueError("status must be a known gate status")
        object.__setattr__(self, "gate_rows", _normalize_gate_rows(self.gate_rows))
        object.__setattr__(
            self,
            "block_reasons",
            _normalize_reasons("block_reasons", self.block_reasons),
        )
        object.__setattr__(
            self,
            "watch_reasons",
            _normalize_reasons("watch_reasons", self.watch_reasons),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_settlement_freshness_gate_report(
    source: OutcomeFreshnessReport | OutcomeTrackingReport,
    *,
    config: PaperSettlementFreshnessGateConfig,
    generated_at: datetime,
) -> PaperSettlementFreshnessGateReport:
    if type(config) is not PaperSettlementFreshnessGateConfig:
        raise ValueError("config must be a PaperSettlementFreshnessGateConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    generated_at_utc = _as_utc(generated_at)
    source_view = _source_view(source)
    latest_check_age_hours = (
        _age_hours(
            generated_at_utc=generated_at_utc,
            latest_check_generated_at=source_view.latest_check_generated_at,
        )
        if source_view.latest_check_generated_at is not None
        else None
    )
    stale_pending_count = (
        source_view.pending_count
        if _has_stale_pending(
            pending_count=source_view.pending_count,
            latest_check_age_hours=latest_check_age_hours,
            max_unresolved_age_hours=config.max_unresolved_age_hours,
        )
        else 0
    )
    gate_rows = _build_gate_rows(
        source_view=source_view,
        config=config,
        latest_check_age_hours=latest_check_age_hours,
        stale_pending_count=stale_pending_count,
    )
    block_reasons = tuple(row.reason for row in gate_rows if row.status == "block")
    watch_reasons = tuple(row.reason for row in gate_rows if row.status == "watch")
    block_count = len(block_reasons)
    watch_count = len(watch_reasons)
    pass_count = sum(1 for row in gate_rows if row.status == "pass")

    return PaperSettlementFreshnessGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_kind=source_view.source_kind,
        source_report_count=source_view.source_report_count,
        latest_check_generated_at=source_view.latest_check_generated_at,
        checked_market_count=source_view.checked_market_count,
        pending_count=source_view.pending_count,
        stale_pending_count=stale_pending_count,
        latest_check_age_hours=latest_check_age_hours,
        status=_overall_status(block_count=block_count, watch_count=watch_count),
        gate_count=len(gate_rows),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        gate_rows=gate_rows,
        block_reasons=block_reasons,
        watch_reasons=watch_reasons,
    )


@dataclass(frozen=True)
class _SourceView:
    source_kind: str
    source_report_count: int
    latest_check_generated_at: datetime | None
    checked_market_count: int
    pending_count: int


def _source_view(source: OutcomeFreshnessReport | OutcomeTrackingReport) -> _SourceView:
    if type(source) is OutcomeFreshnessReport:
        _require_source_flags(
            "source",
            paper_only=source.paper_only,
            report_only=source.report_only,
            readonly=source.readonly,
        )
        return _SourceView(
            source_kind="outcome_freshness",
            source_report_count=source.outcome_report_count,
            latest_check_generated_at=source.latest_report_generated_at,
            checked_market_count=source.latest_total_markets_checked,
            pending_count=source.latest_pending_count,
        )
    if type(source) is OutcomeTrackingReport:
        _require_source_flags(
            "source",
            paper_only=source.paper_only,
            report_only=source.report_only,
            readonly=source.readonly,
        )
        return _SourceView(
            source_kind="outcome_tracking",
            source_report_count=1,
            latest_check_generated_at=source.generated_at,
            checked_market_count=source.total_markets_checked,
            pending_count=source.pending_count,
        )
    raise ValueError("source must be an OutcomeFreshnessReport or OutcomeTrackingReport")


def _require_source_flags(
    field_name: str,
    *,
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> None:
    if paper_only is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if report_only is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if readonly is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _build_gate_rows(
    *,
    source_view: _SourceView,
    config: PaperSettlementFreshnessGateConfig,
    latest_check_age_hours: Decimal | None,
    stale_pending_count: int,
) -> tuple[PaperSettlementFreshnessGateRow, ...]:
    return (
        _checking_coverage_row(source_view=source_view, config=config),
        _pending_count_row(source_view=source_view, config=config),
        _unresolved_age_row(
            latest_check_age_hours=latest_check_age_hours,
            max_unresolved_age_hours=config.max_unresolved_age_hours,
            stale_pending_count=stale_pending_count,
        ),
    )


def _checking_coverage_row(
    *,
    source_view: _SourceView,
    config: PaperSettlementFreshnessGateConfig,
) -> PaperSettlementFreshnessGateRow:
    if source_view.source_report_count == 0:
        return PaperSettlementFreshnessGateRow(
            gate_name="checking_coverage",
            status="watch",
            reason=EMPTY_SOURCE_REASON,
            observed_value=source_view.checked_market_count,
            threshold=config.min_checked_market_count,
        )
    if source_view.checked_market_count < config.min_checked_market_count:
        return PaperSettlementFreshnessGateRow(
            gate_name="checking_coverage",
            status="watch",
            reason=LOW_COVERAGE_REASON,
            observed_value=source_view.checked_market_count,
            threshold=config.min_checked_market_count,
        )
    return PaperSettlementFreshnessGateRow(
        gate_name="checking_coverage",
        status="pass",
        reason=CHECKING_COVERAGE_PASS_REASON,
        observed_value=source_view.checked_market_count,
        threshold=config.min_checked_market_count,
    )


def _pending_count_row(
    *,
    source_view: _SourceView,
    config: PaperSettlementFreshnessGateConfig,
) -> PaperSettlementFreshnessGateRow:
    if source_view.pending_count > config.max_pending_count:
        return PaperSettlementFreshnessGateRow(
            gate_name="pending_count",
            status="block",
            reason=PENDING_LIMIT_REASON,
            observed_value=source_view.pending_count,
            threshold=config.max_pending_count,
        )
    return PaperSettlementFreshnessGateRow(
        gate_name="pending_count",
        status="pass",
        reason=PENDING_COUNT_PASS_REASON,
        observed_value=source_view.pending_count,
        threshold=config.max_pending_count,
    )


def _unresolved_age_row(
    *,
    latest_check_age_hours: Decimal | None,
    max_unresolved_age_hours: int,
    stale_pending_count: int,
) -> PaperSettlementFreshnessGateRow:
    max_age_hours = _decimal_hours(max_unresolved_age_hours)
    if stale_pending_count > 0:
        return PaperSettlementFreshnessGateRow(
            gate_name="unresolved_age",
            status="block",
            reason=STALE_PENDING_REASON,
            observed_value=latest_check_age_hours,
            threshold=max_age_hours,
        )
    return PaperSettlementFreshnessGateRow(
        gate_name="unresolved_age",
        status="pass",
        reason=UNRESOLVED_AGE_PASS_REASON,
        observed_value=latest_check_age_hours,
        threshold=max_age_hours,
    )


def _has_stale_pending(
    *,
    pending_count: int,
    latest_check_age_hours: Decimal | None,
    max_unresolved_age_hours: int,
) -> bool:
    return (
        pending_count > 0
        and latest_check_age_hours is not None
        and latest_check_age_hours > _decimal_hours(max_unresolved_age_hours)
    )


def _overall_status(*, block_count: int, watch_count: int) -> str:
    if block_count > 0:
        return "block"
    if watch_count > 0:
        return "watch"
    return "pass"


def _age_hours(
    *,
    generated_at_utc: datetime,
    latest_check_generated_at: datetime,
) -> Decimal:
    delta = generated_at_utc - _as_utc(latest_check_generated_at)
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    if seconds < Decimal("0"):
        raise ValueError("latest_check_age_hours must be nonnegative")
    return (seconds / HOUR_SECONDS).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _decimal_hours(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _validate_report_consistency(report: PaperSettlementFreshnessGateReport) -> None:
    if report.gate_count != len(report.gate_rows):
        raise ValueError("gate_count must match gate_rows")
    if tuple(row.gate_name for row in report.gate_rows) != GATE_NAMES:
        raise ValueError("gate_rows must use the known gate sequence")
    if report.pass_count != sum(1 for row in report.gate_rows if row.status == "pass"):
        raise ValueError("pass_count must match gate_rows")
    if report.watch_count != sum(1 for row in report.gate_rows if row.status == "watch"):
        raise ValueError("watch_count must match gate_rows")
    if report.block_count != sum(1 for row in report.gate_rows if row.status == "block"):
        raise ValueError("block_count must match gate_rows")
    if report.status != _overall_status(
        block_count=report.block_count,
        watch_count=report.watch_count,
    ):
        raise ValueError("status must match gate_rows")
    if report.block_reasons != tuple(
        row.reason for row in report.gate_rows if row.status == "block"
    ):
        raise ValueError("block_reasons must match gate_rows")
    if report.watch_reasons != tuple(
        row.reason for row in report.gate_rows if row.status == "watch"
    ):
        raise ValueError("watch_reasons must match gate_rows")
    if report.source_kind == "outcome_tracking" and report.source_report_count != 1:
        raise ValueError("source_report_count must be one for outcome_tracking source")
    if report.source_report_count == 0:
        if report.latest_check_generated_at is not None:
            raise ValueError("latest_check_generated_at must be absent without source")
        if report.latest_check_age_hours is not None:
            raise ValueError("latest_check_age_hours must be absent without source")
        if report.checked_market_count != 0:
            raise ValueError("checked_market_count must be zero without source")
        if report.pending_count != 0:
            raise ValueError("pending_count must be zero without source")
        if report.stale_pending_count != 0:
            raise ValueError("stale_pending_count must be zero without source")
    else:
        if report.latest_check_generated_at is None:
            raise ValueError("latest_check_generated_at is required with source")
        if report.latest_check_age_hours is None:
            raise ValueError("latest_check_age_hours is required with source")
    if report.pending_count > report.checked_market_count:
        raise ValueError("pending_count must not exceed checked_market_count")
    if report.stale_pending_count > report.pending_count:
        raise ValueError("stale_pending_count must not exceed pending_count")
    _validate_gate_row_semantics(report)
    if (
        report.source_report_count > 0
        and report.latest_check_generated_at is not None
        and report.latest_check_age_hours
        != _age_hours(
            generated_at_utc=report.generated_at,
            latest_check_generated_at=report.latest_check_generated_at,
        )
    ):
        raise ValueError(
            "latest_check_age_hours must match generated_at and latest_check_generated_at",
        )


def _validate_gate_row_semantics(report: PaperSettlementFreshnessGateReport) -> None:
    checking_coverage_row, pending_count_row, unresolved_age_row = report.gate_rows
    _validate_checking_coverage_row(report, checking_coverage_row)
    _validate_pending_count_row(report, pending_count_row)
    _validate_unresolved_age_row(report, unresolved_age_row)


def _validate_checking_coverage_row(
    report: PaperSettlementFreshnessGateReport,
    row: PaperSettlementFreshnessGateRow,
) -> None:
    _require_int_gate_value("checking_coverage observed_value", row.observed_value)
    _require_int_gate_value("checking_coverage threshold", row.threshold)
    if row.observed_value != report.checked_market_count:
        raise ValueError("checking_coverage observed_value must match checked_market_count")
    expected_status = (
        "watch"
        if report.source_report_count == 0
        or report.checked_market_count < row.threshold
        else "pass"
    )
    _require_gate_row_status("checking_coverage", row.status, expected_status)
    expected_reason = (
        EMPTY_SOURCE_REASON
        if report.source_report_count == 0
        else LOW_COVERAGE_REASON
        if report.checked_market_count < row.threshold
        else CHECKING_COVERAGE_PASS_REASON
    )
    _require_gate_row_reason("checking_coverage", row.reason, expected_reason)


def _validate_pending_count_row(
    report: PaperSettlementFreshnessGateReport,
    row: PaperSettlementFreshnessGateRow,
) -> None:
    _require_int_gate_value("pending_count observed_value", row.observed_value)
    _require_int_gate_value("pending_count threshold", row.threshold)
    if row.observed_value != report.pending_count:
        raise ValueError("pending_count observed_value must match pending_count")
    expected_status = "block" if report.pending_count > row.threshold else "pass"
    _require_gate_row_status("pending_count", row.status, expected_status)
    expected_reason = (
        PENDING_LIMIT_REASON
        if expected_status == "block"
        else PENDING_COUNT_PASS_REASON
    )
    _require_gate_row_reason("pending_count", row.reason, expected_reason)


def _validate_unresolved_age_row(
    report: PaperSettlementFreshnessGateReport,
    row: PaperSettlementFreshnessGateRow,
) -> None:
    _require_optional_decimal_gate_value(
        "unresolved_age observed_value",
        row.observed_value,
    )
    _require_decimal_gate_value("unresolved_age threshold", row.threshold)
    if row.observed_value != report.latest_check_age_hours:
        raise ValueError(
            "unresolved_age observed_value must match latest_check_age_hours",
        )
    expected_stale_pending_count = (
        report.pending_count
        if report.pending_count > 0
        and row.observed_value is not None
        and row.observed_value > row.threshold
        else 0
    )
    if report.stale_pending_count != expected_stale_pending_count:
        raise ValueError("stale_pending_count must match unresolved_age")
    expected_status = "block" if report.stale_pending_count > 0 else "pass"
    _require_gate_row_status("unresolved_age", row.status, expected_status)
    expected_reason = (
        STALE_PENDING_REASON
        if expected_status == "block"
        else UNRESOLVED_AGE_PASS_REASON
    )
    _require_gate_row_reason("unresolved_age", row.reason, expected_reason)


def _require_gate_row_status(
    gate_name: str,
    actual_status: str,
    expected_status: str,
) -> None:
    if actual_status != expected_status:
        raise ValueError(f"{gate_name} status must match observed values")


def _require_gate_row_reason(
    gate_name: str,
    actual_reason: str,
    expected_reason: str,
) -> None:
    if actual_reason != expected_reason:
        raise ValueError(f"{gate_name} reason must match observed values")


def _require_int_gate_value(field_name: str, value: int | Decimal | None) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an integer")


def _require_decimal_gate_value(field_name: str, value: int | Decimal | None) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_optional_decimal_gate_value(
    field_name: str,
    value: int | Decimal | None,
) -> None:
    if value is None:
        return
    _require_decimal_gate_value(field_name, value)


def _normalize_gate_rows(
    rows: tuple[PaperSettlementFreshnessGateRow, ...],
) -> tuple[PaperSettlementFreshnessGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("gate_rows must be a tuple")
    normalized: list[PaperSettlementFreshnessGateRow] = []
    for row in rows:
        if type(row) is not PaperSettlementFreshnessGateRow:
            raise ValueError("gate_rows must contain PaperSettlementFreshnessGateRow")
        normalized.append(
            PaperSettlementFreshnessGateRow(
                gate_name=row.gate_name,
                status=row.status,
                reason=row.reason,
                observed_value=row.observed_value,
                threshold=row.threshold,
            ),
        )
    return tuple(normalized)


def _normalize_reasons(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_canonical_string(field_name, value)
    return values


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime or None")
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
        raise ValueError(f"{field_name} must be a nonnegative integer")
    if value < 0:
        raise ValueError(f"{field_name} must be a nonnegative integer")


def _require_optional_decimal(field_name: str, value: Decimal | None) -> None:
    if value is None:
        return
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must use 0.000001 precision")


def _require_optional_scalar(field_name: str, value: int | Decimal | None) -> None:
    if value is None:
        return
    if type(value) is int:
        if value < 0:
            raise ValueError(f"{field_name} must be nonnegative")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        if value < Decimal("0"):
            raise ValueError(f"{field_name} must be nonnegative")
        return
    raise ValueError(f"{field_name} must be an int, Decimal, or None")
