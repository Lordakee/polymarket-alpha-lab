"""Pure read-only source-family divergence SLA report for Phase 1 queues."""

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
from polymarket_alpha_lab.team_taxonomy import (
    require_team_category_pair,
    require_team_id,
)


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION = (
    "market-source-family-divergence-sla-report-v0"
)
ROW_STATUSES = ("ready", "watch", "blocked")
READY_REASON = "source_family_divergence_ready"
OVERDUE_RESOLUTION_REASON = "source_family_divergence_resolution_overdue"
STALE_OFFICIAL_SOURCE_REASON = "source_family_divergence_official_source_stale"
PROXY_ONLY_CONFIRMATION_REASON = "source_family_divergence_proxy_only_confirmation"
MISSING_OWNER_REASON = "source_family_divergence_missing_owner"
ACKNOWLEDGEMENT_LAG_REASON = "source_family_divergence_acknowledgement_lag"
REASON_CODES = (
    READY_REASON,
    OVERDUE_RESOLUTION_REASON,
    STALE_OFFICIAL_SOURCE_REASON,
    PROXY_ONLY_CONFIRMATION_REASON,
    MISSING_OWNER_REASON,
    ACKNOWLEDGEMENT_LAG_REASON,
)
BLOCKING_REASONS = frozenset((OVERDUE_RESOLUTION_REASON, MISSING_OWNER_REASON))
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "ready": 2}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceSlaConfig:
    config_version: str = DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION
    divergence_resolution_sla_seconds: Decimal = Decimal("3600.000000")
    official_source_freshness_sla_seconds: Decimal = Decimal("1800.000000")
    team_acknowledgement_sla_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "divergence_resolution_sla_seconds",
            _require_positive_decimal(
                "divergence_resolution_sla_seconds",
                self.divergence_resolution_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "official_source_freshness_sla_seconds",
            _require_positive_decimal(
                "official_source_freshness_sla_seconds",
                self.official_source_freshness_sla_seconds,
            ),
        )
        object.__setattr__(
            self,
            "team_acknowledgement_sla_seconds",
            _require_positive_decimal(
                "team_acknowledgement_sla_seconds",
                self.team_acknowledgement_sla_seconds,
            ),
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceSlaInputRow:
    team_id: str
    category_id: str
    source_family: str
    case_id: str
    divergence_detected_at: datetime
    divergence_resolved_at: datetime | None = None
    official_source_observed_at: datetime | None = None
    proxy_confirmed_at: datetime | None = None
    official_source_confirmed_at: datetime | None = None
    owner_id: str | None = None
    team_acknowledged_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("category_id", self.category_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_family", self.source_family)
        _require_public_string("case_id", self.case_id)
        object.__setattr__(
            self,
            "divergence_detected_at",
            _as_utc("divergence_detected_at", self.divergence_detected_at),
        )
        for field_name in (
            "divergence_resolved_at",
            "official_source_observed_at",
            "proxy_confirmed_at",
            "official_source_confirmed_at",
            "team_acknowledged_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        if self.owner_id is not None:
            _require_public_string("owner_id", self.owner_id)
        _validate_input_row_times(self)
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceSlaReportRow:
    category_id: str
    team_id: str
    source_family: str
    case_id: str
    row_status: str
    divergence_age_seconds: Decimal
    official_source_age_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("source_family", self.source_family)
        _require_public_string("case_id", self.case_id)
        _require_row_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "divergence_age_seconds",
            _require_nonnegative_decimal(
                "divergence_age_seconds",
                self.divergence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "official_source_age_seconds",
            _normalize_optional_decimal(
                "official_source_age_seconds",
                self.official_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_row(self)
        require_paper_only_flags("report row", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceSlaReport:
    generated_at: datetime
    config_version: str
    sla_status: str
    queue_item_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    overdue_resolution_count: Decimal
    stale_official_source_count: Decimal
    proxy_only_confirmation_count: Decimal
    missing_owner_count: Decimal
    acknowledgement_lag_count: Decimal
    blocked_ratio: Decimal
    watch_ratio: Decimal
    rows: tuple[MarketSourceFamilyDivergenceSlaReportRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_row_status("sla_status", self.sla_status)
        for field_name in (
            "queue_item_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "overdue_resolution_count",
            "stale_official_source_count",
            "proxy_only_confirmation_count",
            "missing_owner_count",
            "acknowledgement_lag_count",
            "blocked_ratio",
            "watch_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)


def build_market_source_family_divergence_sla_report(
    input_rows: list[MarketSourceFamilyDivergenceSlaInputRow]
    | tuple[MarketSourceFamilyDivergenceSlaInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceSlaConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceSlaReport:
    if type(config) is not MarketSourceFamilyDivergenceSlaConfig:
        raise ValueError("config must be a MarketSourceFamilyDivergenceSlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    report_rows = tuple(
        sorted(
            (
                _report_row(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in rows
            ),
            key=_report_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    return MarketSourceFamilyDivergenceSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        sla_status=_status_from_reason_codes(reason_codes),
        queue_item_count=_decimal_count(len(report_rows)),
        ready_count=_status_count(report_rows, "ready"),
        watch_count=_status_count(report_rows, "watch"),
        blocked_count=_status_count(report_rows, "blocked"),
        overdue_resolution_count=_reason_count(report_rows, OVERDUE_RESOLUTION_REASON),
        stale_official_source_count=_reason_count(
            report_rows,
            STALE_OFFICIAL_SOURCE_REASON,
        ),
        proxy_only_confirmation_count=_reason_count(
            report_rows,
            PROXY_ONLY_CONFIRMATION_REASON,
        ),
        missing_owner_count=_reason_count(report_rows, MISSING_OWNER_REASON),
        acknowledgement_lag_count=_reason_count(
            report_rows,
            ACKNOWLEDGEMENT_LAG_REASON,
        ),
        blocked_ratio=_ratio(_status_count(report_rows, "blocked"), len(report_rows)),
        watch_ratio=_ratio(_status_count(report_rows, "watch"), len(report_rows)),
        rows=report_rows,
        reason_codes=reason_codes,
    )


def market_source_family_divergence_sla_report_payload(
    report: MarketSourceFamilyDivergenceSlaReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceSlaReport:
        raise ValueError("report must be a MarketSourceFamilyDivergenceSlaReport")
    require_paper_only_flags("report", report)
    value = json_ready_no_floats(report)
    if type(value) is not dict:
        raise ValueError("report must produce a JSON object")
    reject_unsafe_surface_fields("source-family divergence SLA report", value)
    return value


def _report_row(
    row: MarketSourceFamilyDivergenceSlaInputRow,
    *,
    config: MarketSourceFamilyDivergenceSlaConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceSlaReportRow:
    divergence_end = row.divergence_resolved_at or generated_at
    divergence_age_seconds = _age_seconds(
        divergence_end,
        row.divergence_detected_at,
        field_name="divergence_age_seconds",
    )
    official_source_age_seconds = (
        _age_seconds(
            generated_at,
            row.official_source_observed_at,
            field_name="official_source_age_seconds",
        )
        if row.official_source_observed_at is not None
        else None
    )
    acknowledgement_lag_seconds = _age_seconds(
        row.team_acknowledged_at or generated_at,
        row.divergence_detected_at,
        field_name="acknowledgement_lag_seconds",
    )
    reason_codes = _row_reason_codes(
        row=row,
        divergence_age_seconds=divergence_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )
    return MarketSourceFamilyDivergenceSlaReportRow(
        category_id=row.category_id,
        team_id=row.team_id,
        source_family=row.source_family,
        case_id=row.case_id,
        row_status=_status_from_reason_codes(reason_codes),
        divergence_age_seconds=divergence_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    row: MarketSourceFamilyDivergenceSlaInputRow,
    divergence_age_seconds: Decimal,
    official_source_age_seconds: Decimal | None,
    acknowledgement_lag_seconds: Decimal,
    config: MarketSourceFamilyDivergenceSlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if divergence_age_seconds > config.divergence_resolution_sla_seconds:
        reasons.append(OVERDUE_RESOLUTION_REASON)
    if (
        official_source_age_seconds is None
        or official_source_age_seconds > config.official_source_freshness_sla_seconds
    ):
        reasons.append(STALE_OFFICIAL_SOURCE_REASON)
    if row.proxy_confirmed_at is not None and row.official_source_confirmed_at is None:
        reasons.append(PROXY_ONLY_CONFIRMATION_REASON)
    if row.owner_id is None:
        reasons.append(MISSING_OWNER_REASON)
    if acknowledgement_lag_seconds > config.team_acknowledgement_sla_seconds:
        reasons.append(ACKNOWLEDGEMENT_LAG_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceFamilyDivergenceSlaInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceSlaInputRow:
            raise ValueError("input rows must contain MarketSourceFamilyDivergenceSlaInputRow")
        require_paper_only_flags("input row", row)
        _reject_future_row_times(row, generated_at=generated_at)
        key = (row.team_id, row.case_id)
        if key in seen_keys:
            raise ValueError("case_id values must be unique per team")
        seen_keys.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.category_id,
                row.team_id,
                row.source_family,
                row.case_id,
            ),
        ),
    )


def _normalize_report_rows(
    value: object,
) -> tuple[MarketSourceFamilyDivergenceSlaReportRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceSlaReportRow:
            raise ValueError("rows must contain MarketSourceFamilyDivergenceSlaReportRow")
        require_paper_only_flags("report row", row)
        key = (row.team_id, row.case_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and case_id")
        seen_keys.add(key)
    return tuple(sorted(rows, key=_report_row_sort_key))


def _report_row_sort_key(
    row: MarketSourceFamilyDivergenceSlaReportRow,
) -> tuple[int, str, str, str, str]:
    return (
        STATUS_WEIGHT[row.row_status],
        row.category_id,
        row.team_id,
        row.source_family,
        row.case_id,
    )


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceSlaReportRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == READY_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (READY_REASON,):
        return "ready"
    return "watch"


def _validate_input_row_times(row: MarketSourceFamilyDivergenceSlaInputRow) -> None:
    if (
        row.divergence_resolved_at is not None
        and row.divergence_resolved_at < row.divergence_detected_at
    ):
        raise ValueError("divergence_resolved_at must not precede detection")
    if (
        row.team_acknowledged_at is not None
        and row.team_acknowledged_at < row.divergence_detected_at
    ):
        raise ValueError("team_acknowledged_at must not precede detection")


def _reject_future_row_times(
    row: MarketSourceFamilyDivergenceSlaInputRow,
    *,
    generated_at: datetime,
) -> None:
    for field_name in (
        "divergence_detected_at",
        "divergence_resolved_at",
        "official_source_observed_at",
        "proxy_confirmed_at",
        "official_source_confirmed_at",
        "team_acknowledged_at",
    ):
        value = getattr(row, field_name)
        if value is not None and value > generated_at:
            raise ValueError(f"{field_name} must not be in the future")


def _validate_report_row(row: MarketSourceFamilyDivergenceSlaReportRow) -> None:
    if row.reason_codes == (READY_REASON,):
        if row.row_status != "ready":
            raise ValueError("ready reason requires ready status")
        if row.official_source_age_seconds is None:
            raise ValueError("ready rows require official_source_age_seconds")
        return
    if READY_REASON in row.reason_codes:
        raise ValueError("ready reason cannot be mixed with queue reasons")
    if row.official_source_age_seconds is None and STALE_OFFICIAL_SOURCE_REASON not in (
        row.reason_codes
    ):
        raise ValueError("missing official_source_age_seconds requires stale reason")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report(report: MarketSourceFamilyDivergenceSlaReport) -> None:
    rows = report.rows
    if report.queue_item_count != _decimal_count(len(rows)):
        raise ValueError("queue_item_count must match rows")
    if report.ready_count != _status_count(rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if (
        report.ready_count + report.watch_count + report.blocked_count
        != report.queue_item_count
    ):
        raise ValueError("status counts must sum to queue_item_count")
    reason_count_fields = (
        (OVERDUE_RESOLUTION_REASON, "overdue_resolution_count"),
        (STALE_OFFICIAL_SOURCE_REASON, "stale_official_source_count"),
        (PROXY_ONLY_CONFIRMATION_REASON, "proxy_only_confirmation_count"),
        (MISSING_OWNER_REASON, "missing_owner_count"),
        (ACKNOWLEDGEMENT_LAG_REASON, "acknowledgement_lag_count"),
    )
    for reason_code, field_name in reason_count_fields:
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.blocked_ratio != _ratio(report.blocked_count, len(rows)):
        raise ValueError("blocked_ratio must match rows")
    if report.watch_ratio != _ratio(report.watch_count, len(rows)):
        raise ValueError("watch_ratio must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.sla_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("sla_status must match reason_codes")


def _status_count(
    rows: tuple[MarketSourceFamilyDivergenceSlaReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[MarketSourceFamilyDivergenceSlaReportRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _ratio(numerator: Decimal, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / Decimal(denominator)).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime, *, field_name: str) -> Decimal:
    end_at_utc = _as_utc(field_name, end_at)
    start_at_utc = _as_utc(field_name, start_at)
    delta = end_at_utc - start_at_utc
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


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
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six decimal places")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


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
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_SLA_CONFIG_VERSION",
    "MarketSourceFamilyDivergenceSlaConfig",
    "MarketSourceFamilyDivergenceSlaInputRow",
    "MarketSourceFamilyDivergenceSlaReport",
    "MarketSourceFamilyDivergenceSlaReportRow",
    "build_market_source_family_divergence_sla_report",
    "market_source_family_divergence_sla_report_payload",
)
