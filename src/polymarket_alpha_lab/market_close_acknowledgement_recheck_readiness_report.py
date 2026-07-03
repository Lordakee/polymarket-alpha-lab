"""Pure in-memory market close acknowledgement recheck readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_READINESS_CONFIG_VERSION = (
    "market-close-ack-recheck-readiness-v0"
)

READINESS_STATUSES = ("ready", "watch", "blocked")
OUTCOME_SOURCES = ("acknowledgement", "resolver", "manual", "unknown")
ROW_REASON_CODES = (
    "market_close_ack_recheck_ready",
    "missing_close_evidence",
    "missing_acknowledgement",
    "stale_recheck",
    "stale_close_evidence",
    "outcome_source_not_acknowledgement",
)
REPORT_REASON_CODES = (
    "market_close_ack_recheck_ready",
    "empty_market_close_ack_recheck_inputs",
    "missing_close_evidence",
    "missing_acknowledgement",
    "stale_recheck",
    "stale_close_evidence",
    "outcome_source_not_acknowledgement",
)

COUNT_QUANTUM = Decimal("1")
SECONDS_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SECONDS = Decimal("0.000000")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "ready": Decimal("2"),
}
REASON_SORT_WEIGHT = {
    "missing_close_evidence": Decimal("0"),
    "missing_acknowledgement": Decimal("1"),
    "stale_recheck": Decimal("2"),
    "stale_close_evidence": Decimal("3"),
    "outcome_source_not_acknowledgement": Decimal("4"),
    "market_close_ack_recheck_ready": Decimal("5"),
}


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckReadinessConfig:
    config_version: str = (
        DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_READINESS_CONFIG_VERSION
    )
    max_recheck_age_seconds: Decimal = Decimal("3600")
    max_close_evidence_age_seconds: Decimal = Decimal("7200")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_recheck_age_seconds",
            _normalize_nonnegative_seconds(
                "max_recheck_age_seconds",
                self.max_recheck_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_close_evidence_age_seconds",
            _normalize_nonnegative_seconds(
                "max_close_evidence_age_seconds",
                self.max_close_evidence_age_seconds,
            ),
        )
        require_paper_only_flags(
            "MarketCloseAcknowledgementRecheckReadinessConfig",
            self,
        )


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckInput:
    condition_id: str
    close_time: datetime | None
    close_evidence_observed_at: datetime | None
    acknowledgement_observed_at: datetime | None
    rechecked_at: datetime | None
    outcome_source: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        for field_name in (
            "close_time",
            "close_evidence_observed_at",
            "acknowledgement_observed_at",
            "rechecked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        _require_member("outcome_source", self.outcome_source, OUTCOME_SOURCES)
        require_paper_only_flags("MarketCloseAcknowledgementRecheckInput", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckReadinessRow:
    condition_id: str
    close_time: datetime | None
    close_time_known: bool
    close_evidence_observed_at: datetime | None
    close_evidence_fresh: bool
    acknowledgement_observed_at: datetime | None
    acknowledgement_present: bool
    rechecked_at: datetime | None
    recheck_fresh: bool
    outcome_source: str
    outcome_source_acknowledged: bool
    close_age_seconds: Decimal | None
    close_evidence_age_seconds: Decimal | None
    acknowledgement_age_seconds: Decimal | None
    recheck_age_seconds: Decimal | None
    readiness_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("condition_id", self.condition_id)
        for field_name in (
            "close_time",
            "close_evidence_observed_at",
            "acknowledgement_observed_at",
            "rechecked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "close_time_known",
            "close_evidence_fresh",
            "acknowledgement_present",
            "recheck_fresh",
            "outcome_source_acknowledged",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_member("outcome_source", self.outcome_source, OUTCOME_SOURCES)
        for field_name in (
            "close_age_seconds",
            "close_evidence_age_seconds",
            "acknowledgement_age_seconds",
            "recheck_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_seconds(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags(
            "MarketCloseAcknowledgementRecheckReadinessRow",
            self,
        )


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckReadinessReport:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    readiness_ratio: Decimal
    max_recheck_age_seconds: Decimal
    max_close_evidence_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketCloseAcknowledgementRecheckReadinessRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("market_count", "ready_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "readiness_ratio",
            _normalize_ratio("readiness_ratio", self.readiness_ratio),
        )
        for field_name in ("max_recheck_age_seconds", "max_close_evidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market close acknowledgement recheck readiness report",
            self,
        )
        require_paper_only_flags(
            "MarketCloseAcknowledgementRecheckReadinessReport",
            self,
        )


def build_market_close_acknowledgement_recheck_readiness_report(
    inputs: Iterable[MarketCloseAcknowledgementRecheckInput],
    *,
    config: MarketCloseAcknowledgementRecheckReadinessConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckReadinessReport:
    if type(config) is not MarketCloseAcknowledgementRecheckReadinessConfig:
        raise ValueError(
            "config must be a MarketCloseAcknowledgementRecheckReadinessConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    ready_count = _status_count(rows, "ready")
    return MarketCloseAcknowledgementRecheckReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        ready_count=ready_count,
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        readiness_ratio=_readiness_ratio(ready_count, len(rows)),
        max_recheck_age_seconds=config.max_recheck_age_seconds,
        max_close_evidence_age_seconds=config.max_close_evidence_age_seconds,
        status=_status_rollup(tuple(row.readiness_status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_close_acknowledgement_recheck_readiness_payload(
    report: MarketCloseAcknowledgementRecheckReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckReadinessReport:
        raise ValueError(
            "report must be a MarketCloseAcknowledgementRecheckReadinessReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields(
        "market close acknowledgement recheck readiness report",
        report,
    )
    return json_ready_no_floats(report)


def _normalize_inputs(
    inputs: Iterable[MarketCloseAcknowledgementRecheckInput],
) -> tuple[MarketCloseAcknowledgementRecheckInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of acknowledgement recheck rows")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of acknowledgement recheck rows",
        ) from exc
    seen_condition_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckInput:
            raise ValueError(
                "inputs must contain MarketCloseAcknowledgementRecheckInput values",
            )
        require_paper_only_flags("input", row)
        if row.condition_id in seen_condition_ids:
            raise ValueError("inputs must not contain duplicate condition_id values")
        seen_condition_ids.add(row.condition_id)
    return rows


def _row_from_input(
    item: MarketCloseAcknowledgementRecheckInput,
    *,
    config: MarketCloseAcknowledgementRecheckReadinessConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckReadinessRow:
    close_age_seconds = _optional_age_seconds(item.close_time, generated_at)
    close_evidence_age_seconds = _optional_age_seconds(
        item.close_evidence_observed_at,
        generated_at,
    )
    acknowledgement_age_seconds = _optional_age_seconds(
        item.acknowledgement_observed_at,
        generated_at,
    )
    recheck_age_seconds = _optional_age_seconds(item.rechecked_at, generated_at)

    close_time_known = item.close_time is not None
    acknowledgement_present = item.acknowledgement_observed_at is not None
    outcome_source_acknowledged = item.outcome_source == "acknowledgement"
    close_evidence_fresh = (
        item.close_evidence_observed_at is not None
        and close_evidence_age_seconds is not None
        and close_evidence_age_seconds <= config.max_close_evidence_age_seconds
    )
    recheck_fresh = (
        item.rechecked_at is not None
        and recheck_age_seconds is not None
        and recheck_age_seconds <= config.max_recheck_age_seconds
    )
    reason_codes = _row_reason_codes(
        close_time_known=close_time_known,
        close_evidence_fresh=close_evidence_fresh,
        acknowledgement_present=acknowledgement_present,
        recheck_fresh=recheck_fresh,
        outcome_source_acknowledged=outcome_source_acknowledged,
    )
    return MarketCloseAcknowledgementRecheckReadinessRow(
        condition_id=item.condition_id,
        close_time=item.close_time,
        close_time_known=close_time_known,
        close_evidence_observed_at=item.close_evidence_observed_at,
        close_evidence_fresh=close_evidence_fresh,
        acknowledgement_observed_at=item.acknowledgement_observed_at,
        acknowledgement_present=acknowledgement_present,
        rechecked_at=item.rechecked_at,
        recheck_fresh=recheck_fresh,
        outcome_source=item.outcome_source,
        outcome_source_acknowledged=outcome_source_acknowledged,
        close_age_seconds=close_age_seconds,
        close_evidence_age_seconds=close_evidence_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        recheck_age_seconds=recheck_age_seconds,
        readiness_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    close_time_known: bool,
    close_evidence_fresh: bool,
    acknowledgement_present: bool,
    recheck_fresh: bool,
    outcome_source_acknowledged: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not close_time_known:
        codes.append("missing_close_evidence")
    if not acknowledgement_present:
        codes.append("missing_acknowledgement")
    if acknowledgement_present and not recheck_fresh:
        codes.append("stale_recheck")
    if close_time_known and not close_evidence_fresh:
        codes.append("stale_close_evidence")
    if not outcome_source_acknowledged:
        codes.append("outcome_source_not_acknowledgement")
    if not codes:
        return ("market_close_ack_recheck_ready",)
    return tuple(codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "missing_close_evidence" in reason_codes:
        return "blocked"
    if "missing_acknowledgement" in reason_codes:
        return "blocked"
    if "outcome_source_not_acknowledgement" in reason_codes:
        return "blocked"
    if reason_codes == ("market_close_ack_recheck_ready",):
        return "ready"
    return "watch"


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_market_close_ack_recheck_inputs",)
    codes: list[str] = []
    for allowed_code in REPORT_REASON_CODES:
        if allowed_code in (
            "market_close_ack_recheck_ready",
            "empty_market_close_ack_recheck_inputs",
        ):
            continue
        if any(allowed_code in row.reason_codes for row in rows):
            codes.append(allowed_code)
    if not codes:
        return ("market_close_ack_recheck_ready",)
    return tuple(codes)


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "ready"


def _row_sort_key(
    row: MarketCloseAcknowledgementRecheckReadinessRow,
) -> tuple[Decimal, Decimal, datetime, str]:
    close_time = row.close_time or datetime.max.replace(tzinfo=UTC)
    return (
        STATUS_WEIGHT[row.readiness_status],
        min(REASON_SORT_WEIGHT[reason_code] for reason_code in row.reason_codes),
        close_time,
        row.condition_id,
    )


def _status_count(
    rows: tuple[MarketCloseAcknowledgementRecheckReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _readiness_ratio(ready_count: Decimal, market_count: int) -> Decimal:
    if market_count == 0:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (ready_count / Decimal(market_count)).quantize(RATIO_QUANTUM)


def _optional_age_seconds(observed_at: datetime | None, generated_at: datetime) -> Decimal | None:
    if observed_at is None:
        return None
    return _seconds_between(observed_at, generated_at)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = _as_utc("end", end) - _as_utc("start", start)
    microseconds = (
        (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
    )
    if microseconds < 0:
        raise ValueError("age seconds must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(microseconds) / Decimal("1000000")).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_row(row: MarketCloseAcknowledgementRecheckReadinessRow) -> None:
    if row.close_time_known != (row.close_time is not None):
        raise ValueError("close_time_known must match close_time")
    if row.acknowledgement_present != (row.acknowledgement_observed_at is not None):
        raise ValueError("acknowledgement_present must match acknowledgement_observed_at")
    if row.outcome_source_acknowledged != (row.outcome_source == "acknowledgement"):
        raise ValueError("outcome_source_acknowledged must match outcome_source")
    if row.close_time is None and row.close_age_seconds is not None:
        raise ValueError("missing close_time must not have close_age_seconds")
    if (
        row.close_evidence_observed_at is None
        and row.close_evidence_age_seconds is not None
    ):
        raise ValueError(
            "missing close_evidence_observed_at must not have close_evidence_age_seconds",
        )
    if (
        row.acknowledgement_observed_at is None
        and row.acknowledgement_age_seconds is not None
    ):
        raise ValueError(
            "missing acknowledgement_observed_at must not have acknowledgement_age_seconds",
        )
    if row.rechecked_at is None and row.recheck_age_seconds is not None:
        raise ValueError("missing rechecked_at must not have recheck_age_seconds")
    if row.reason_codes != _row_reason_codes(
        close_time_known=row.close_time_known,
        close_evidence_fresh=row.close_evidence_fresh,
        acknowledgement_present=row.acknowledgement_present,
        recheck_fresh=row.recheck_fresh,
        outcome_source_acknowledged=row.outcome_source_acknowledged,
    ):
        raise ValueError("reason_codes must match readiness evidence")
    if row.readiness_status != _row_status(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")


def _validate_report(report: MarketCloseAcknowledgementRecheckReadinessReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.readiness_ratio != _readiness_ratio(report.ready_count, len(report.rows)):
        raise ValueError("readiness_ratio must match rows")
    if report.status != _status_rollup(tuple(row.readiness_status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic readiness sort")


def _normalize_rows(
    rows: Iterable[MarketCloseAcknowledgementRecheckReadinessRow],
) -> tuple[MarketCloseAcknowledgementRecheckReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not MarketCloseAcknowledgementRecheckReadinessRow:
            raise ValueError(
                "rows must contain MarketCloseAcknowledgementRecheckReadinessRow values",
            )
        require_paper_only_flags("row", row)
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECONDS_QUANTUM)


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_READINESS_CONFIG_VERSION",
    "MarketCloseAcknowledgementRecheckInput",
    "MarketCloseAcknowledgementRecheckReadinessConfig",
    "MarketCloseAcknowledgementRecheckReadinessReport",
    "MarketCloseAcknowledgementRecheckReadinessRow",
    "build_market_close_acknowledgement_recheck_readiness_report",
    "market_close_acknowledgement_recheck_readiness_payload",
)
