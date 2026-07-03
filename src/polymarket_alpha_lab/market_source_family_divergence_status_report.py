"""Pure Phase 1 market source-family divergence status report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_STATUS_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-status-report-v0"
)

WORKFLOW_STATES = ("open", "blocked", "acknowledged", "cleared")
ROW_STATUSES = (
    "blocked",
    "overdue",
    "stale_official",
    "proxy_only",
    "open",
    "acknowledged",
    "cleared",
)
REPORT_STATUSES = ("clear", "watch", "blocked")
ROW_STATUS_RANK = {
    "blocked": 0,
    "overdue": 1,
    "stale_official": 2,
    "proxy_only": 3,
    "open": 4,
    "acknowledged": 5,
    "cleared": 6,
}
ACTIONABLE_ROW_STATUSES = frozenset(
    ("blocked", "overdue", "stale_official", "proxy_only", "open"),
)

BLOCKED_REASON = "market_source_family_divergence_status_blocked"
OVERDUE_REASON = "market_source_family_divergence_status_overdue"
STALE_OFFICIAL_REASON = "market_source_family_divergence_status_stale_official"
PROXY_ONLY_REASON = "market_source_family_divergence_status_proxy_only"
OPEN_REASON = "market_source_family_divergence_status_open"
ACKNOWLEDGED_REASON = "market_source_family_divergence_status_acknowledged"
CLEARED_REASON = "market_source_family_divergence_status_cleared"
CLEAR_REASON = "market_source_family_divergence_status_clear"
REASON_CODES = (
    BLOCKED_REASON,
    OVERDUE_REASON,
    STALE_OFFICIAL_REASON,
    PROXY_ONLY_REASON,
    OPEN_REASON,
    ACKNOWLEDGED_REASON,
    CLEARED_REASON,
    CLEAR_REASON,
)
ROW_STATUS_REASON = {
    "blocked": BLOCKED_REASON,
    "overdue": OVERDUE_REASON,
    "stale_official": STALE_OFFICIAL_REASON,
    "proxy_only": PROXY_ONLY_REASON,
    "open": OPEN_REASON,
    "acknowledged": ACKNOWLEDGED_REASON,
    "cleared": CLEARED_REASON,
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceStatusConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_STATUS_REPORT_CONFIG_VERSION
    )
    overdue_after_seconds: Decimal = Decimal("3600.000000")
    official_stale_after_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "overdue_after_seconds",
            _require_positive_decimal(
                "overdue_after_seconds",
                self.overdue_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "official_stale_after_seconds",
            _require_positive_decimal(
                "official_stale_after_seconds",
                self.official_stale_after_seconds,
            ),
        )
        require_paper_only_flags("market source family divergence status config", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceStatusInputRow:
    market_id: str
    category_id: str
    workflow_state: str
    detected_at: datetime
    updated_at: datetime
    official_observed_at: datetime | None = None
    proxy_observed_at: datetime | None = None
    acknowledged_at: datetime | None = None
    cleared_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        _require_workflow_state("workflow_state", self.workflow_state)
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        for field_name in (
            "official_observed_at",
            "proxy_observed_at",
            "acknowledged_at",
            "cleared_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        _validate_input_row(self)
        reject_unsafe_surface_fields(
            "market source family divergence status input row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence status input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceStatusRow:
    market_id: str
    category_id: str
    workflow_state: str
    row_status: str
    detected_at: datetime
    updated_at: datetime
    official_observed_at: datetime | None
    proxy_observed_at: datetime | None
    acknowledged_at: datetime | None
    cleared_at: datetime | None
    divergence_age_seconds: Decimal
    official_source_age_seconds: Decimal
    proxy_source_age_seconds: Decimal
    source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        _require_workflow_state("workflow_state", self.workflow_state)
        _require_row_status("row_status", self.row_status)
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        for field_name in (
            "official_observed_at",
            "proxy_observed_at",
            "acknowledged_at",
            "cleared_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        for field_name in (
            "divergence_age_seconds",
            "official_source_age_seconds",
            "proxy_source_age_seconds",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_status_row(self)
        reject_unsafe_surface_fields("market source family divergence status row", self)
        require_paper_only_flags("market source family divergence status row", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceStatusReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    open_count: Decimal
    overdue_count: Decimal
    blocked_count: Decimal
    acknowledged_count: Decimal
    cleared_count: Decimal
    stale_official_count: Decimal
    proxy_only_count: Decimal
    actionable_count: Decimal
    open_ratio: Decimal
    overdue_ratio: Decimal
    blocked_ratio: Decimal
    acknowledged_ratio: Decimal
    cleared_ratio: Decimal
    stale_official_ratio: Decimal
    proxy_only_ratio: Decimal
    actionable_ratio: Decimal
    max_divergence_age_seconds: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketSourceFamilyDivergenceStatusRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "open_count",
            "overdue_count",
            "blocked_count",
            "acknowledged_count",
            "cleared_count",
            "stale_official_count",
            "proxy_only_count",
            "actionable_count",
            "open_ratio",
            "overdue_ratio",
            "blocked_ratio",
            "acknowledged_ratio",
            "cleared_ratio",
            "stale_official_ratio",
            "proxy_only_ratio",
            "actionable_ratio",
            "max_divergence_age_seconds",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_status_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market source family divergence status report",
            self,
        )
        require_paper_only_flags("market source family divergence status report", self)


def build_market_source_family_divergence_status_report(
    input_rows: list[MarketSourceFamilyDivergenceStatusInputRow]
    | tuple[MarketSourceFamilyDivergenceStatusInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceStatusConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceStatusReport:
    if type(config) is not MarketSourceFamilyDivergenceStatusConfig:
        raise ValueError("config must be a MarketSourceFamilyDivergenceStatusConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _status_row(row, config=config, generated_at=generated_at_utc)
                for row in _normalize_input_rows(input_rows, generated_at=generated_at_utc)
            ),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    open_count = _count(sum(1 for row in rows if row.workflow_state == "open"))
    overdue_count = _status_count(rows, "overdue")
    blocked_count = _count(sum(1 for row in rows if row.workflow_state == "blocked"))
    acknowledged_count = _count(
        sum(1 for row in rows if row.workflow_state == "acknowledged"),
    )
    cleared_count = _count(sum(1 for row in rows if row.workflow_state == "cleared"))
    stale_official_count = _status_count(rows, "stale_official")
    proxy_only_count = _status_count(rows, "proxy_only")
    actionable_count = _count(
        sum(1 for row in rows if row.row_status in ACTIONABLE_ROW_STATUSES),
    )
    return MarketSourceFamilyDivergenceStatusReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        market_count=market_count,
        open_count=open_count,
        overdue_count=overdue_count,
        blocked_count=blocked_count,
        acknowledged_count=acknowledged_count,
        cleared_count=cleared_count,
        stale_official_count=stale_official_count,
        proxy_only_count=proxy_only_count,
        actionable_count=actionable_count,
        open_ratio=_ratio(open_count, market_count),
        overdue_ratio=_ratio(overdue_count, market_count),
        blocked_ratio=_ratio(blocked_count, market_count),
        acknowledged_ratio=_ratio(acknowledged_count, market_count),
        cleared_ratio=_ratio(cleared_count, market_count),
        stale_official_ratio=_ratio(stale_official_count, market_count),
        proxy_only_ratio=_ratio(proxy_only_count, market_count),
        actionable_ratio=_ratio(actionable_count, market_count),
        max_divergence_age_seconds=_max_decimal(
            tuple(row.divergence_age_seconds for row in rows),
        ),
        max_source_age_seconds=_max_decimal(tuple(row.source_age_seconds for row in rows)),
        rows=rows,
    )


def market_source_family_divergence_status_report_payload(
    report: MarketSourceFamilyDivergenceStatusReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceStatusReport:
        raise ValueError("report must be a MarketSourceFamilyDivergenceStatusReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("market source family divergence status report", report)
    return json_ready_no_floats(report)


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceFamilyDivergenceStatusInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceStatusInputRow:
            raise ValueError(
                "input rows must contain MarketSourceFamilyDivergenceStatusInputRow values",
            )
        require_paper_only_flags("input row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("input rows must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
        _require_not_after("detected_at", row.detected_at, generated_at)
        _require_not_after("updated_at", row.updated_at, generated_at)
        for field_name in (
            "official_observed_at",
            "proxy_observed_at",
            "acknowledged_at",
            "cleared_at",
        ):
            timestamp = getattr(row, field_name)
            if timestamp is not None:
                _require_not_after(field_name, timestamp, generated_at)
    return rows


def _status_row(
    row: MarketSourceFamilyDivergenceStatusInputRow,
    *,
    config: MarketSourceFamilyDivergenceStatusConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceStatusRow:
    divergence_age_seconds = _seconds_between(row.detected_at, generated_at)
    official_source_age_seconds = _optional_age(row.official_observed_at, generated_at)
    proxy_source_age_seconds = _optional_age(row.proxy_observed_at, generated_at)
    source_age_seconds = _max_decimal(
        (official_source_age_seconds, proxy_source_age_seconds),
    )
    row_status = _row_status(
        row,
        divergence_age_seconds=divergence_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        config=config,
    )
    return MarketSourceFamilyDivergenceStatusRow(
        market_id=row.market_id,
        category_id=row.category_id,
        workflow_state=row.workflow_state,
        row_status=row_status,
        detected_at=row.detected_at,
        updated_at=row.updated_at,
        official_observed_at=row.official_observed_at,
        proxy_observed_at=row.proxy_observed_at,
        acknowledged_at=row.acknowledged_at,
        cleared_at=row.cleared_at,
        divergence_age_seconds=divergence_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        proxy_source_age_seconds=proxy_source_age_seconds,
        source_age_seconds=source_age_seconds,
        reason_codes=(ROW_STATUS_REASON[row_status],),
    )


def _row_status(
    row: MarketSourceFamilyDivergenceStatusInputRow,
    *,
    divergence_age_seconds: Decimal,
    official_source_age_seconds: Decimal,
    config: MarketSourceFamilyDivergenceStatusConfig,
) -> str:
    if row.workflow_state == "blocked":
        return "blocked"
    if row.workflow_state == "cleared":
        return "cleared"
    if row.workflow_state == "acknowledged":
        return "acknowledged"
    if divergence_age_seconds > config.overdue_after_seconds:
        return "overdue"
    if (
        row.official_observed_at is not None
        and official_source_age_seconds > config.official_stale_after_seconds
    ):
        return "stale_official"
    if row.official_observed_at is None and row.proxy_observed_at is not None:
        return "proxy_only"
    return "open"


def _report_status(rows: tuple[MarketSourceFamilyDivergenceStatusRow, ...]) -> str:
    if any(row.row_status in ("blocked", "overdue") for row in rows):
        return "blocked"
    if any(row.row_status in ACTIONABLE_ROW_STATUSES for row in rows):
        return "watch"
    if any(row.row_status == "acknowledged" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceStatusRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (CLEAR_REASON,)
    codes: list[str] = []
    if any(row.row_status == "blocked" for row in rows):
        codes.append(BLOCKED_REASON)
    if any(row.row_status == "overdue" for row in rows):
        codes.append(OVERDUE_REASON)
    if any(row.row_status == "stale_official" for row in rows):
        codes.append(STALE_OFFICIAL_REASON)
    if any(row.row_status == "proxy_only" for row in rows):
        codes.append(PROXY_ONLY_REASON)
    if any(row.workflow_state == "open" for row in rows):
        codes.append(OPEN_REASON)
    if any(row.workflow_state == "acknowledged" for row in rows):
        codes.append(ACKNOWLEDGED_REASON)
    if any(row.workflow_state == "cleared" for row in rows):
        codes.append(CLEARED_REASON)
    if not codes:
        return (CLEAR_REASON,)
    return tuple(codes)


def _row_sort_key(
    row: MarketSourceFamilyDivergenceStatusRow,
) -> tuple[int, str, str]:
    return (ROW_STATUS_RANK[row.row_status], row.category_id, row.market_id)


def _normalize_status_rows(
    value: object,
) -> tuple[MarketSourceFamilyDivergenceStatusRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceStatusRow:
            raise ValueError(
                "rows must contain MarketSourceFamilyDivergenceStatusRow values",
            )
        require_paper_only_flags("row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("rows must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    return rows


def _validate_input_row(row: MarketSourceFamilyDivergenceStatusInputRow) -> None:
    if row.updated_at < row.detected_at:
        raise ValueError("updated_at must not be before detected_at")
    if row.acknowledged_at is not None and row.acknowledged_at < row.detected_at:
        raise ValueError("acknowledged_at must not be before detected_at")
    if row.cleared_at is not None and row.cleared_at < row.detected_at:
        raise ValueError("cleared_at must not be before detected_at")
    if row.workflow_state == "acknowledged" and row.acknowledged_at is None:
        raise ValueError("acknowledged rows require acknowledged_at")
    if row.workflow_state == "cleared" and row.cleared_at is None:
        raise ValueError("cleared rows require cleared_at")
    if row.workflow_state == "open" and row.cleared_at is not None:
        raise ValueError("open rows must not be cleared")
    if row.workflow_state == "cleared" and row.acknowledged_at is None:
        return
    if (
        row.acknowledged_at is not None
        and row.cleared_at is not None
        and row.cleared_at < row.acknowledged_at
    ):
        raise ValueError("cleared_at must not be before acknowledged_at")


def _validate_status_row(row: MarketSourceFamilyDivergenceStatusRow) -> None:
    if row.reason_codes != (ROW_STATUS_REASON[row.row_status],):
        raise ValueError("reason_codes must match row_status")
    if row.updated_at < row.detected_at:
        raise ValueError("updated_at must not be before detected_at")
    if row.source_age_seconds != _max_decimal(
        (row.official_source_age_seconds, row.proxy_source_age_seconds),
    ):
        raise ValueError("source_age_seconds must match source ages")
    if row.workflow_state == "acknowledged" and row.acknowledged_at is None:
        raise ValueError("acknowledged rows require acknowledged_at")
    if row.workflow_state == "cleared" and row.cleared_at is None:
        raise ValueError("cleared rows require cleared_at")


def _validate_report(report: MarketSourceFamilyDivergenceStatusReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sort")
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.open_count != _count(
        sum(1 for row in report.rows if row.workflow_state == "open"),
    ):
        raise ValueError("open_count must match rows")
    if report.overdue_count != _status_count(report.rows, "overdue"):
        raise ValueError("overdue_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in report.rows if row.workflow_state == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.acknowledged_count != _count(
        sum(1 for row in report.rows if row.workflow_state == "acknowledged"),
    ):
        raise ValueError("acknowledged_count must match rows")
    if report.cleared_count != _count(
        sum(1 for row in report.rows if row.workflow_state == "cleared"),
    ):
        raise ValueError("cleared_count must match rows")
    if report.stale_official_count != _status_count(report.rows, "stale_official"):
        raise ValueError("stale_official_count must match rows")
    if report.proxy_only_count != _status_count(report.rows, "proxy_only"):
        raise ValueError("proxy_only_count must match rows")
    if report.actionable_count != _count(
        sum(1 for row in report.rows if row.row_status in ACTIONABLE_ROW_STATUSES),
    ):
        raise ValueError("actionable_count must match rows")
    if report.open_ratio != _ratio(report.open_count, report.market_count):
        raise ValueError("open_ratio must match rows")
    if report.overdue_ratio != _ratio(report.overdue_count, report.market_count):
        raise ValueError("overdue_ratio must match rows")
    if report.blocked_ratio != _ratio(report.blocked_count, report.market_count):
        raise ValueError("blocked_ratio must match rows")
    if report.acknowledged_ratio != _ratio(
        report.acknowledged_count,
        report.market_count,
    ):
        raise ValueError("acknowledged_ratio must match rows")
    if report.cleared_ratio != _ratio(report.cleared_count, report.market_count):
        raise ValueError("cleared_ratio must match rows")
    if report.stale_official_ratio != _ratio(
        report.stale_official_count,
        report.market_count,
    ):
        raise ValueError("stale_official_ratio must match rows")
    if report.proxy_only_ratio != _ratio(report.proxy_only_count, report.market_count):
        raise ValueError("proxy_only_ratio must match rows")
    if report.actionable_ratio != _ratio(report.actionable_count, report.market_count):
        raise ValueError("actionable_ratio must match rows")
    if report.max_divergence_age_seconds != _max_decimal(
        tuple(row.divergence_age_seconds for row in report.rows),
    ):
        raise ValueError("max_divergence_age_seconds must match rows")
    if report.max_source_age_seconds != _max_decimal(
        tuple(row.source_age_seconds for row in report.rows),
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[MarketSourceFamilyDivergenceStatusRow, ...],
    row_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == row_status))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _optional_age(value: datetime | None, generated_at: datetime) -> Decimal:
    if value is None:
        return ZERO
    return _seconds_between(value, generated_at)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("timestamp must not be after generated_at")
    delta = end - start
    microseconds = (
        ((delta.days * int(SECONDS_PER_DAY)) + delta.seconds)
        * int(MICROSECONDS_PER_SECOND)
    ) + delta.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(microseconds) / MICROSECONDS_PER_SECOND).quantize(QUANT)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must use stable sequence")
    return reason_codes


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_not_after(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known row status")


def _require_workflow_state(field_name: str, value: object) -> None:
    if type(value) is not str or value not in WORKFLOW_STATES:
        raise ValueError(f"{field_name} must be a known workflow state")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_STATUS_REPORT_CONFIG_VERSION",
    "WORKFLOW_STATES",
    "ROW_STATUSES",
    "REPORT_STATUSES",
    "REASON_CODES",
    "MarketSourceFamilyDivergenceStatusConfig",
    "MarketSourceFamilyDivergenceStatusInputRow",
    "MarketSourceFamilyDivergenceStatusReport",
    "MarketSourceFamilyDivergenceStatusRow",
    "build_market_source_family_divergence_status_report",
    "market_source_family_divergence_status_report_payload",
)
