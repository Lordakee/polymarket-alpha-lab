"""Phase 1 market close acknowledgement recheck SLA report."""

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


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_SLA_REPORT_CONFIG_VERSION = (
    "market-close-acknowledgement-recheck-sla-report-v0"
)

OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON = "overdue_close_acknowledgement"
MISSING_OWNER_REASON = "missing_owner"
STALE_SOURCE_REASON = "stale_source"
CONTRADICTORY_SOURCE_REASON = "contradictory_source"
TEAM_REPEATED_MISS_REASON = "team_repeated_miss"
CATEGORY_REPEATED_MISS_REASON = "category_repeated_miss"
CLEAR_REASON = "market_close_acknowledgement_recheck_sla_clear"
EMPTY_REASON = "market_close_acknowledgement_recheck_sla_empty"

ROW_REASON_CODES = (
    OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
    MISSING_OWNER_REASON,
    STALE_SOURCE_REASON,
    CONTRADICTORY_SOURCE_REASON,
    CLEAR_REASON,
)
REPORT_REASON_CODES = (
    OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
    MISSING_OWNER_REASON,
    STALE_SOURCE_REASON,
    CONTRADICTORY_SOURCE_REASON,
    TEAM_REPEATED_MISS_REASON,
    CATEGORY_REPEATED_MISS_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BREACH_REASONS = (
    OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
    MISSING_OWNER_REASON,
    CONTRADICTORY_SOURCE_REASON,
)
REPORT_STATUSES = ("empty", "clear", "watch", "breached")
ROW_STATUSES = ("clear", "watch", "breached")
MISS_SCOPES = ("team", "category")
ROW_STATUS_RANK = {"breached": 0, "watch": 1, "clear": 2}
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckSlaConfig:
    config_version: str = DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_SLA_REPORT_CONFIG_VERSION
    acknowledgement_sla_seconds: Decimal = Decimal("3600.000000")
    source_stale_seconds: Decimal = Decimal("1800.000000")
    team_repeated_miss_threshold: Decimal = Decimal("2.000000")
    category_repeated_miss_threshold: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "acknowledgement_sla_seconds",
            "source_stale_seconds",
            "team_repeated_miss_threshold",
            "category_repeated_miss_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("market close acknowledgement recheck SLA config", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckSlaInputRow:
    market_id: str
    category_id: str
    owner_team_id: str | None
    source_id: str
    market_closed_at: datetime
    close_acknowledged_at: datetime | None
    source_observed_at: datetime
    source_contradicts_close: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "owner_team_id",
            _require_optional_canonical_string("owner_team_id", self.owner_team_id),
        )
        object.__setattr__(self, "source_id", _require_canonical_string("source_id", self.source_id))
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "close_acknowledged_at",
            _as_optional_utc("close_acknowledged_at", self.close_acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        _require_bool("source_contradicts_close", self.source_contradicts_close)
        if (
            self.close_acknowledged_at is not None
            and self.close_acknowledged_at < self.market_closed_at
        ):
            raise ValueError("close_acknowledged_at must not be before market_closed_at")
        require_paper_only_flags("market close acknowledgement recheck SLA input row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckSlaRow:
    market_id: str
    category_id: str
    owner_team_id: str | None
    source_id: str
    market_closed_at: datetime
    close_acknowledged_at: datetime | None
    source_observed_at: datetime
    source_contradicts_close: bool
    acknowledgement_sla_seconds: Decimal
    source_stale_seconds: Decimal
    close_age_seconds: Decimal
    source_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    sla_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_canonical_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "category_id",
            _require_canonical_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "owner_team_id",
            _require_optional_canonical_string("owner_team_id", self.owner_team_id),
        )
        object.__setattr__(self, "source_id", _require_canonical_string("source_id", self.source_id))
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "close_acknowledged_at",
            _as_optional_utc("close_acknowledged_at", self.close_acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        _require_bool("source_contradicts_close", self.source_contradicts_close)
        for field_name in ("acknowledgement_sla_seconds", "source_stale_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("close_age_seconds", "source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_age_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _normalize_optional_age_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        _require_status("sla_status", self.sla_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_sla_row(self)
        require_paper_only_flags("market close acknowledgement recheck SLA row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckSlaRepeatedMissRow:
    miss_scope: str
    miss_id: str
    market_count: Decimal
    miss_count: Decimal
    overdue_close_acknowledgement_count: Decimal
    missing_owner_count: Decimal
    stale_source_count: Decimal
    contradictory_source_count: Decimal
    max_close_age_seconds: Decimal
    repeated_miss: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_status("miss_scope", self.miss_scope, MISS_SCOPES)
        object.__setattr__(self, "miss_id", _require_canonical_string("miss_id", self.miss_id))
        for field_name in (
            "market_count",
            "miss_count",
            "overdue_close_acknowledgement_count",
            "missing_owner_count",
            "stale_source_count",
            "contradictory_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_close_age_seconds",
            _require_age_decimal("max_close_age_seconds", self.max_close_age_seconds),
        )
        _require_bool("repeated_miss", self.repeated_miss)
        if self.miss_count > self.market_count:
            raise ValueError("miss_count must not exceed market_count")
        require_paper_only_flags("market close acknowledgement recheck SLA repeated miss row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckSlaReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    breached_market_count: Decimal
    exception_market_count: Decimal
    overdue_close_acknowledgement_count: Decimal
    missing_owner_count: Decimal
    stale_source_count: Decimal
    contradictory_source_count: Decimal
    team_repeated_miss_count: Decimal
    category_repeated_miss_count: Decimal
    exception_ratio: Decimal
    max_close_age_seconds: Decimal
    max_source_age_seconds: Decimal
    max_acknowledgement_lag_seconds: Decimal
    rows: tuple[MarketCloseAcknowledgementRecheckSlaRow, ...]
    team_repeated_miss_rows: tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...]
    category_repeated_miss_rows: tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        for field_name in (
            "market_count",
            "clear_market_count",
            "watch_market_count",
            "breached_market_count",
            "exception_market_count",
            "overdue_close_acknowledgement_count",
            "missing_owner_count",
            "stale_source_count",
            "contradictory_source_count",
            "team_repeated_miss_count",
            "category_repeated_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exception_ratio",
            _require_ratio_decimal("exception_ratio", self.exception_ratio),
        )
        for field_name in (
            "max_close_age_seconds",
            "max_source_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_age_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "team_repeated_miss_rows",
            _normalize_repeated_miss_rows(
                "team_repeated_miss_rows",
                self.team_repeated_miss_rows,
                "team",
            ),
        )
        object.__setattr__(
            self,
            "category_repeated_miss_rows",
            _normalize_repeated_miss_rows(
                "category_repeated_miss_rows",
                self.category_repeated_miss_rows,
                "category",
            ),
        )
        _validate_report(self)
        require_paper_only_flags("market close acknowledgement recheck SLA report", self)


def build_market_close_acknowledgement_recheck_sla_report(
    input_rows: list[MarketCloseAcknowledgementRecheckSlaInputRow]
    | tuple[MarketCloseAcknowledgementRecheckSlaInputRow, ...],
    *,
    config: MarketCloseAcknowledgementRecheckSlaConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckSlaReport:
    if type(config) is not MarketCloseAcknowledgementRecheckSlaConfig:
        raise ValueError("config must be a MarketCloseAcknowledgementRecheckSlaConfig")
    require_paper_only_flags("market close acknowledgement recheck SLA config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(row, config=config, generated_at=generated_at_utc)
                for row in _normalize_input_rows(input_rows, generated_at=generated_at_utc)
            ),
            key=_row_sort_key,
        ),
    )
    team_repeated_miss_rows = _repeated_miss_rows(
        rows,
        miss_scope="team",
        threshold=config.team_repeated_miss_threshold,
    )
    category_repeated_miss_rows = _repeated_miss_rows(
        rows,
        miss_scope="category",
        threshold=config.category_repeated_miss_threshold,
    )
    reason_codes = _report_reason_codes(
        rows,
        team_repeated_miss_rows=team_repeated_miss_rows,
        category_repeated_miss_rows=category_repeated_miss_rows,
    )

    return MarketCloseAcknowledgementRecheckSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(reason_codes),
        reason_codes=reason_codes,
        market_count=_decimal_count(len(rows)),
        clear_market_count=_status_count(rows, "clear"),
        watch_market_count=_status_count(rows, "watch"),
        breached_market_count=_status_count(rows, "breached"),
        exception_market_count=_exception_count(rows),
        overdue_close_acknowledgement_count=_reason_count(
            rows,
            OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
        ),
        missing_owner_count=_reason_count(rows, MISSING_OWNER_REASON),
        stale_source_count=_reason_count(rows, STALE_SOURCE_REASON),
        contradictory_source_count=_reason_count(rows, CONTRADICTORY_SOURCE_REASON),
        team_repeated_miss_count=_repeated_count(team_repeated_miss_rows),
        category_repeated_miss_count=_repeated_count(category_repeated_miss_rows),
        exception_ratio=_ratio(_exception_count(rows), _decimal_count(len(rows))),
        max_close_age_seconds=_max_decimal(tuple(row.close_age_seconds for row in rows)),
        max_source_age_seconds=_max_decimal(tuple(row.source_age_seconds for row in rows)),
        max_acknowledgement_lag_seconds=_max_decimal(
            tuple(
                row.acknowledgement_lag_seconds
                for row in rows
                if row.acknowledgement_lag_seconds is not None
            ),
        ),
        rows=rows,
        team_repeated_miss_rows=team_repeated_miss_rows,
        category_repeated_miss_rows=category_repeated_miss_rows,
    )


def market_close_acknowledgement_recheck_sla_report_to_payload(
    report: MarketCloseAcknowledgementRecheckSlaReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckSlaReport:
        raise ValueError("report must be a MarketCloseAcknowledgementRecheckSlaReport")
    require_paper_only_flags("market close acknowledgement recheck SLA report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields("market close acknowledgement recheck SLA report", payload)
    return payload


def _normalize_input_rows(
    input_rows: object,
    *,
    generated_at: datetime,
) -> tuple[MarketCloseAcknowledgementRecheckSlaInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckSlaInputRow:
            raise ValueError(
                "input_rows must contain MarketCloseAcknowledgementRecheckSlaInputRow values",
            )
        require_paper_only_flags("market close acknowledgement recheck SLA input row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("input_rows must be unique by market_id")
        seen_market_ids.add(row.market_id)
        _validate_input_times(row, generated_at=generated_at)
    return tuple(sorted(rows, key=lambda row: row.market_id))


def _row_from_input(
    row: MarketCloseAcknowledgementRecheckSlaInputRow,
    *,
    config: MarketCloseAcknowledgementRecheckSlaConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckSlaRow:
    close_age_seconds = _age_seconds(generated_at, row.market_closed_at)
    source_age_seconds = _age_seconds(generated_at, row.source_observed_at)
    acknowledgement_lag_seconds = (
        None
        if row.close_acknowledged_at is None
        else _age_seconds(row.close_acknowledged_at, row.market_closed_at)
    )
    reason_codes = _row_reason_codes(
        row,
        config=config,
        close_age_seconds=close_age_seconds,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
    )
    return MarketCloseAcknowledgementRecheckSlaRow(
        market_id=row.market_id,
        category_id=row.category_id,
        owner_team_id=row.owner_team_id,
        source_id=row.source_id,
        market_closed_at=row.market_closed_at,
        close_acknowledged_at=row.close_acknowledged_at,
        source_observed_at=row.source_observed_at,
        source_contradicts_close=row.source_contradicts_close,
        acknowledgement_sla_seconds=config.acknowledgement_sla_seconds,
        source_stale_seconds=config.source_stale_seconds,
        close_age_seconds=close_age_seconds,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        sla_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketCloseAcknowledgementRecheckSlaInputRow,
    *,
    config: MarketCloseAcknowledgementRecheckSlaConfig,
    close_age_seconds: Decimal,
    source_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if _close_acknowledgement_overdue(
        row,
        close_age_seconds=close_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        acknowledgement_sla_seconds=config.acknowledgement_sla_seconds,
    ):
        reasons.append(OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON)
    if row.owner_team_id is None:
        reasons.append(MISSING_OWNER_REASON)
    if source_age_seconds > config.source_stale_seconds:
        reasons.append(STALE_SOURCE_REASON)
    if row.source_contradicts_close:
        reasons.append(CONTRADICTORY_SOURCE_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _close_acknowledgement_overdue(
    row: MarketCloseAcknowledgementRecheckSlaInputRow,
    *,
    close_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    acknowledgement_sla_seconds: Decimal,
) -> bool:
    if row.close_acknowledged_at is None:
        return close_age_seconds >= acknowledgement_sla_seconds
    if acknowledgement_lag_seconds is None:
        return False
    return acknowledgement_lag_seconds > acknowledgement_sla_seconds


def _repeated_miss_rows(
    rows: tuple[MarketCloseAcknowledgementRecheckSlaRow, ...],
    *,
    miss_scope: str,
    threshold: Decimal,
) -> tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...]:
    scoped_rows: dict[str, list[MarketCloseAcknowledgementRecheckSlaRow]] = {}
    miss_rows_by_scope: dict[str, list[MarketCloseAcknowledgementRecheckSlaRow]] = {}
    for row in rows:
        miss_id = _miss_id(row, miss_scope)
        if miss_id is None:
            continue
        scoped_rows.setdefault(miss_id, []).append(row)
        if _has_exception(row):
            miss_rows_by_scope.setdefault(miss_id, []).append(row)
    miss_rows = tuple(
        MarketCloseAcknowledgementRecheckSlaRepeatedMissRow(
            miss_scope=miss_scope,
            miss_id=miss_id,
            market_count=_decimal_count(len(scoped_rows[miss_id])),
            miss_count=_decimal_count(len(group_rows)),
            overdue_close_acknowledgement_count=_reason_count(
                tuple(group_rows),
                OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
            ),
            missing_owner_count=_reason_count(tuple(group_rows), MISSING_OWNER_REASON),
            stale_source_count=_reason_count(tuple(group_rows), STALE_SOURCE_REASON),
            contradictory_source_count=_reason_count(
                tuple(group_rows),
                CONTRADICTORY_SOURCE_REASON,
            ),
            max_close_age_seconds=_max_decimal(
                tuple(group_row.close_age_seconds for group_row in group_rows),
            ),
            repeated_miss=_decimal_count(len(group_rows)) >= threshold,
        )
        for miss_id, group_rows in sorted(miss_rows_by_scope.items())
    )
    return tuple(sorted(miss_rows, key=lambda row: (not row.repeated_miss, row.miss_id)))


def _miss_id(
    row: MarketCloseAcknowledgementRecheckSlaRow,
    miss_scope: str,
) -> str | None:
    if miss_scope == "team":
        return row.owner_team_id
    if miss_scope == "category":
        return row.category_id
    raise ValueError("miss_scope is invalid")


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckSlaRow, ...],
    *,
    team_repeated_miss_rows: tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...],
    category_repeated_miss_rows: tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    for reason in (
        OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
        MISSING_OWNER_REASON,
        STALE_SOURCE_REASON,
        CONTRADICTORY_SOURCE_REASON,
    ):
        if _reason_count(rows, reason) > ZERO:
            reasons.append(reason)
    if _repeated_count(team_repeated_miss_rows) > ZERO:
        reasons.append(TEAM_REPEATED_MISS_REASON)
    if _repeated_count(category_repeated_miss_rows) > ZERO:
        reasons.append(CATEGORY_REPEATED_MISS_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (EMPTY_REASON,):
        return "empty"
    if reason_codes == (CLEAR_REASON,):
        return "clear"
    if any(
        reason in reason_codes
        for reason in (
            OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
            MISSING_OWNER_REASON,
            CONTRADICTORY_SOURCE_REASON,
            TEAM_REPEATED_MISS_REASON,
            CATEGORY_REPEATED_MISS_REASON,
        )
    ):
        return "breached"
    return "watch"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "clear"
    if any(reason in reason_codes for reason in BREACH_REASONS):
        return "breached"
    return "watch"


def _status_count(
    rows: tuple[MarketCloseAcknowledgementRecheckSlaRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.sla_status == status))


def _reason_count(
    rows: tuple[MarketCloseAcknowledgementRecheckSlaRow, ...],
    reason: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason in row.reason_codes))


def _exception_count(rows: tuple[MarketCloseAcknowledgementRecheckSlaRow, ...]) -> Decimal:
    return _decimal_count(sum(1 for row in rows if _has_exception(row)))


def _has_exception(row: MarketCloseAcknowledgementRecheckSlaRow) -> bool:
    return row.reason_codes != (CLEAR_REASON,)


def _repeated_count(
    rows: tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.repeated_miss))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO).quantize(QUANT)


def _row_sort_key(row: MarketCloseAcknowledgementRecheckSlaRow) -> tuple[int, str]:
    return (ROW_STATUS_RANK[row.sla_status], row.market_id)


def _validate_input_times(
    row: MarketCloseAcknowledgementRecheckSlaInputRow,
    *,
    generated_at: datetime,
) -> None:
    if row.market_closed_at > generated_at:
        raise ValueError("market_closed_at must not be in the future")
    if row.source_observed_at > generated_at:
        raise ValueError("source_observed_at must not be in the future")
    if row.close_acknowledged_at is not None and row.close_acknowledged_at > generated_at:
        raise ValueError("close_acknowledged_at must not be in the future")


def _validate_sla_row(row: MarketCloseAcknowledgementRecheckSlaRow) -> None:
    if (
        row.close_acknowledged_at is not None
        and row.close_acknowledged_at < row.market_closed_at
    ):
        raise ValueError("close_acknowledged_at must not be before market_closed_at")
    if row.close_acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError("acknowledgement_lag_seconds requires close_acknowledged_at")
    elif row.acknowledgement_lag_seconds is None:
        raise ValueError("acknowledgement_lag_seconds is required after acknowledgement")
    if row.reason_codes == (CLEAR_REASON,):
        if row.sla_status != "clear":
            raise ValueError("clear rows must use clear status")
    elif row.sla_status != _row_status(row.reason_codes):
        raise ValueError("sla_status must match reason_codes")
    if row.sla_status == "watch" and row.reason_codes != (STALE_SOURCE_REASON,):
        raise ValueError("watch rows require stale source only")
    if row.sla_status == "breached" and not any(
        reason in row.reason_codes for reason in BREACH_REASONS
    ):
        raise ValueError("breached rows require breach reason")


def _validate_report(report: MarketCloseAcknowledgementRecheckSlaReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.clear_market_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.breached_market_count != _status_count(report.rows, "breached"):
        raise ValueError("breached_market_count must match rows")
    if report.exception_market_count != _exception_count(report.rows):
        raise ValueError("exception_market_count must match rows")
    if report.overdue_close_acknowledgement_count != _reason_count(
        report.rows,
        OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON,
    ):
        raise ValueError("overdue_close_acknowledgement_count must match rows")
    if report.missing_owner_count != _reason_count(report.rows, MISSING_OWNER_REASON):
        raise ValueError("missing_owner_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, STALE_SOURCE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.contradictory_source_count != _reason_count(
        report.rows,
        CONTRADICTORY_SOURCE_REASON,
    ):
        raise ValueError("contradictory_source_count must match rows")
    if report.team_repeated_miss_count != _repeated_count(report.team_repeated_miss_rows):
        raise ValueError("team_repeated_miss_count must match rows")
    if report.category_repeated_miss_count != _repeated_count(
        report.category_repeated_miss_rows,
    ):
        raise ValueError("category_repeated_miss_count must match rows")
    if report.exception_ratio != _ratio(report.exception_market_count, report.market_count):
        raise ValueError("exception_ratio must match counts")
    if report.max_close_age_seconds != _max_decimal(
        tuple(row.close_age_seconds for row in report.rows),
    ):
        raise ValueError("max_close_age_seconds must match rows")
    if report.max_source_age_seconds != _max_decimal(
        tuple(row.source_age_seconds for row in report.rows),
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_acknowledgement_lag_seconds != _max_decimal(
        tuple(
            row.acknowledgement_lag_seconds
            for row in report.rows
            if row.acknowledgement_lag_seconds is not None
        ),
    ):
        raise ValueError("max_acknowledgement_lag_seconds must match rows")
    expected_reason_codes = _report_reason_codes(
        report.rows,
        team_repeated_miss_rows=report.team_repeated_miss_rows,
        category_repeated_miss_rows=report.category_repeated_miss_rows,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report state")
    if report.report_status != _report_status(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _normalize_rows(value: object) -> tuple[MarketCloseAcknowledgementRecheckSlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckSlaRow:
            raise ValueError("rows must contain MarketCloseAcknowledgementRecheckSlaRow values")
        require_paper_only_flags("market close acknowledgement recheck SLA row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_repeated_miss_rows(
    field_name: str,
    value: object,
    miss_scope: str,
) -> tuple[MarketCloseAcknowledgementRecheckSlaRepeatedMissRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckSlaRepeatedMissRow:
            raise ValueError(f"{field_name} must contain repeated miss rows")
        if row.miss_scope != miss_scope:
            raise ValueError(f"{field_name} must contain {miss_scope} rows")
        require_paper_only_flags("market close acknowledgement recheck SLA repeated miss row", row)
    return tuple(sorted(rows, key=lambda row: (not row.repeated_miss, row.miss_id)))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_status(field_name, reason_code, allowed)
    if tuple(reason for reason in allowed if reason in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must use canonical sequence")
    return reason_codes


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty canonical text")
    if any(character < " " for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _require_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_canonical_string(field_name, value)


def _require_status(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} is invalid")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _require_age_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _normalize_optional_age_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_age_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANT)
    if normalized != value:
        raise ValueError(f"{field_name} must use six or fewer decimal places")
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = _as_utc("later", later) - _as_utc("earlier", earlier)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "CATEGORY_REPEATED_MISS_REASON",
    "CLEAR_REASON",
    "CONTRADICTORY_SOURCE_REASON",
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_SLA_REPORT_CONFIG_VERSION",
    "EMPTY_REASON",
    "MISSING_OWNER_REASON",
    "OVERDUE_CLOSE_ACKNOWLEDGEMENT_REASON",
    "STALE_SOURCE_REASON",
    "TEAM_REPEATED_MISS_REASON",
    "MarketCloseAcknowledgementRecheckSlaConfig",
    "MarketCloseAcknowledgementRecheckSlaInputRow",
    "MarketCloseAcknowledgementRecheckSlaRepeatedMissRow",
    "MarketCloseAcknowledgementRecheckSlaReport",
    "MarketCloseAcknowledgementRecheckSlaRow",
    "build_market_close_acknowledgement_recheck_sla_report",
    "market_close_acknowledgement_recheck_sla_report_to_payload",
)
