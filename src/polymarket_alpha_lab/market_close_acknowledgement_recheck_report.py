"""Phase 1 in-memory market close acknowledgement recheck report."""

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


DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_CONFIG_VERSION = (
    "market-close-acknowledgement-recheck-v0"
)

EMPTY_INPUT_REASON = "empty_market_close_acknowledgement_recheck_input"
CLEAR_REASON = "market_close_acknowledgement_recheck_clear"
STALE_ACKNOWLEDGEMENT_REASON = (
    "market_close_acknowledgement_recheck_stale_acknowledgement"
)
MISSING_TEAM_OWNER_REASON = "market_close_acknowledgement_recheck_missing_team_owner"
CONTRADICTORY_SOURCE_REASON = (
    "market_close_acknowledgement_recheck_contradictory_source"
)
CLOSE_AGE_PRESSURE_REASON = "market_close_acknowledgement_recheck_close_age_pressure"

REASON_CODES = (
    STALE_ACKNOWLEDGEMENT_REASON,
    MISSING_TEAM_OWNER_REASON,
    CONTRADICTORY_SOURCE_REASON,
    CLOSE_AGE_PRESSURE_REASON,
    CLEAR_REASON,
)
REPORT_REASON_CODES = (EMPTY_INPUT_REASON, *REASON_CODES)
BLOCKING_REASON_CODES = (
    MISSING_TEAM_OWNER_REASON,
    CONTRADICTORY_SOURCE_REASON,
)
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("empty", "pass", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
REASON_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckConfig:
    config_version: str = DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_CONFIG_VERSION
    stale_acknowledgement_seconds: Decimal = Decimal("3600.000000")
    close_age_pressure_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_acknowledgement_seconds",
            _require_positive_decimal(
                "stale_acknowledgement_seconds",
                self.stale_acknowledgement_seconds,
            ),
        )
        object.__setattr__(
            self,
            "close_age_pressure_seconds",
            _require_positive_decimal(
                "close_age_pressure_seconds",
                self.close_age_pressure_seconds,
            ),
        )
        require_paper_only_flags("market close acknowledgement recheck config", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckInputRow:
    market_id: str
    source_id: str
    latest_update_id: str
    market_closed_at: datetime
    latest_update_at: datetime
    team_owner_id: str | None = None
    acknowledged_update_id: str | None = None
    acknowledgement_at: datetime | None = None
    source_contradicts_outcome: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_public_string("market_id", self.market_id))
        object.__setattr__(self, "source_id", _require_public_string("source_id", self.source_id))
        object.__setattr__(
            self,
            "latest_update_id",
            _require_public_string("latest_update_id", self.latest_update_id),
        )
        object.__setattr__(
            self,
            "team_owner_id",
            _require_optional_public_string("team_owner_id", self.team_owner_id),
        )
        object.__setattr__(
            self,
            "acknowledged_update_id",
            _require_optional_public_string(
                "acknowledged_update_id",
                self.acknowledged_update_id,
            ),
        )
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "latest_update_at",
            _as_utc("latest_update_at", self.latest_update_at),
        )
        object.__setattr__(
            self,
            "acknowledgement_at",
            _as_optional_utc("acknowledgement_at", self.acknowledgement_at),
        )
        if type(self.source_contradicts_outcome) is not bool:
            raise ValueError("source_contradicts_outcome must be a bool")
        _validate_input_time_shape(self)
        require_paper_only_flags("market close acknowledgement recheck input row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckRow:
    market_id: str
    team_owner_id: str | None
    source_id: str
    latest_update_id: str
    acknowledged_update_id: str | None
    market_closed_at: datetime
    latest_update_at: datetime
    acknowledgement_at: datetime | None
    source_contradicts_outcome: bool
    stale_acknowledgement_seconds: Decimal
    close_age_pressure_seconds: Decimal
    market_close_age_seconds: Decimal
    update_age_seconds: Decimal
    acknowledgement_age_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal | None
    recheck_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "market_id", _require_public_string("market_id", self.market_id))
        object.__setattr__(
            self,
            "team_owner_id",
            _require_optional_public_string("team_owner_id", self.team_owner_id),
        )
        object.__setattr__(self, "source_id", _require_public_string("source_id", self.source_id))
        object.__setattr__(
            self,
            "latest_update_id",
            _require_public_string("latest_update_id", self.latest_update_id),
        )
        object.__setattr__(
            self,
            "acknowledged_update_id",
            _require_optional_public_string(
                "acknowledged_update_id",
                self.acknowledged_update_id,
            ),
        )
        object.__setattr__(
            self,
            "market_closed_at",
            _as_utc("market_closed_at", self.market_closed_at),
        )
        object.__setattr__(
            self,
            "latest_update_at",
            _as_utc("latest_update_at", self.latest_update_at),
        )
        object.__setattr__(
            self,
            "acknowledgement_at",
            _as_optional_utc("acknowledgement_at", self.acknowledgement_at),
        )
        if type(self.source_contradicts_outcome) is not bool:
            raise ValueError("source_contradicts_outcome must be a bool")
        for field_name in (
            "stale_acknowledgement_seconds",
            "close_age_pressure_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_close_age_seconds",
            "update_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "acknowledgement_age_seconds",
            "acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_status("recheck_status", self.recheck_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allowed=REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("market close acknowledgement recheck row", self)


@dataclass(frozen=True)
class MarketCloseAcknowledgementRecheckReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    recheck_market_count: Decimal
    stale_acknowledgement_count: Decimal
    missing_team_owner_count: Decimal
    contradictory_source_count: Decimal
    close_age_pressure_count: Decimal
    recheck_ratio: Decimal
    max_market_close_age_seconds: Decimal | None
    max_update_age_seconds: Decimal | None
    max_acknowledgement_age_seconds: Decimal | None
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...]
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
            _normalize_reason_codes(self.reason_codes, allowed=REPORT_REASON_CODES),
        )
        for field_name in (
            "market_count",
            "pass_market_count",
            "watch_market_count",
            "blocked_market_count",
            "recheck_market_count",
            "stale_acknowledgement_count",
            "missing_team_owner_count",
            "contradictory_source_count",
            "close_age_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recheck_ratio",
            _require_ratio_decimal("recheck_ratio", self.recheck_ratio),
        )
        for field_name in (
            "max_market_close_age_seconds",
            "max_update_age_seconds",
            "max_acknowledgement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("market close acknowledgement recheck report", self)


def build_market_close_acknowledgement_recheck_report(
    input_rows: list[MarketCloseAcknowledgementRecheckInputRow]
    | tuple[MarketCloseAcknowledgementRecheckInputRow, ...],
    *,
    config: MarketCloseAcknowledgementRecheckConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckReport:
    if type(config) is not MarketCloseAcknowledgementRecheckConfig:
        raise ValueError("config must be a MarketCloseAcknowledgementRecheckConfig")
    require_paper_only_flags("market close acknowledgement recheck config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    input_row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for input_row in inputs
            ),
            key=_row_sort_key,
        ),
    )

    return MarketCloseAcknowledgementRecheckReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        market_count=_decimal_count(len(rows)),
        pass_market_count=_status_count(rows, "pass"),
        watch_market_count=_status_count(rows, "watch"),
        blocked_market_count=_status_count(rows, "blocked"),
        recheck_market_count=_decimal_count(
            sum(1 for row in rows if row.recheck_status != "pass"),
        ),
        stale_acknowledgement_count=_reason_count(rows, STALE_ACKNOWLEDGEMENT_REASON),
        missing_team_owner_count=_reason_count(rows, MISSING_TEAM_OWNER_REASON),
        contradictory_source_count=_reason_count(rows, CONTRADICTORY_SOURCE_REASON),
        close_age_pressure_count=_reason_count(rows, CLOSE_AGE_PRESSURE_REASON),
        recheck_ratio=_ratio(
            _decimal_count(sum(1 for row in rows if row.recheck_status != "pass")),
            _decimal_count(len(rows)),
        ),
        max_market_close_age_seconds=_max_optional(
            tuple(row.market_close_age_seconds for row in rows),
        ),
        max_update_age_seconds=_max_optional(tuple(row.update_age_seconds for row in rows)),
        max_acknowledgement_age_seconds=_max_optional(
            tuple(row.acknowledgement_age_seconds for row in rows),
        ),
        rows=rows,
    )


def market_close_acknowledgement_recheck_report_payload(
    report: MarketCloseAcknowledgementRecheckReport,
) -> dict[str, Any]:
    if type(report) is not MarketCloseAcknowledgementRecheckReport:
        raise ValueError("report must be a MarketCloseAcknowledgementRecheckReport")
    require_paper_only_flags("market close acknowledgement recheck report", report)
    ready = json_ready_no_floats(report)
    if not isinstance(ready, dict):
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields("market close acknowledgement recheck report", ready)
    return ready


def _normalize_input_rows(
    input_rows: object,
    *,
    generated_at: datetime,
) -> tuple[MarketCloseAcknowledgementRecheckInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckInputRow:
            raise ValueError(
                "input_rows must contain MarketCloseAcknowledgementRecheckInputRow",
            )
        require_paper_only_flags("market close acknowledgement recheck input row", row)
        _validate_input_times_against_generated_at(row, generated_at=generated_at)
        key = (row.market_id, row.latest_update_id)
        if key in seen_keys:
            raise ValueError("input_rows must be unique by market_id and latest_update_id")
        seen_keys.add(key)
    return tuple(sorted(rows, key=lambda row: (row.market_id, row.latest_update_id, row.source_id)))


def _row_from_input(
    input_row: MarketCloseAcknowledgementRecheckInputRow,
    *,
    config: MarketCloseAcknowledgementRecheckConfig,
    generated_at: datetime,
) -> MarketCloseAcknowledgementRecheckRow:
    market_close_age_seconds = _age_seconds(
        generated_at,
        input_row.market_closed_at,
        earlier_field_name="market_closed_at",
    )
    update_age_seconds = _age_seconds(
        generated_at,
        input_row.latest_update_at,
        earlier_field_name="latest_update_at",
    )
    acknowledgement_age_seconds = (
        None
        if input_row.acknowledgement_at is None
        else _age_seconds(
            generated_at,
            input_row.acknowledgement_at,
            earlier_field_name="acknowledgement_at",
        )
    )
    acknowledgement_lag_seconds = _acknowledgement_lag_seconds(input_row)
    reason_codes = _input_reason_codes(
        input_row,
        stale_acknowledgement_seconds=config.stale_acknowledgement_seconds,
        close_age_pressure_seconds=config.close_age_pressure_seconds,
        market_close_age_seconds=market_close_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
    )

    return MarketCloseAcknowledgementRecheckRow(
        market_id=input_row.market_id,
        team_owner_id=input_row.team_owner_id,
        source_id=input_row.source_id,
        latest_update_id=input_row.latest_update_id,
        acknowledged_update_id=input_row.acknowledged_update_id,
        market_closed_at=input_row.market_closed_at,
        latest_update_at=input_row.latest_update_at,
        acknowledgement_at=input_row.acknowledgement_at,
        source_contradicts_outcome=input_row.source_contradicts_outcome,
        stale_acknowledgement_seconds=config.stale_acknowledgement_seconds,
        close_age_pressure_seconds=config.close_age_pressure_seconds,
        market_close_age_seconds=market_close_age_seconds,
        update_age_seconds=update_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        recheck_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _input_reason_codes(
    input_row: MarketCloseAcknowledgementRecheckInputRow,
    *,
    stale_acknowledgement_seconds: Decimal,
    close_age_pressure_seconds: Decimal,
    market_close_age_seconds: Decimal,
    acknowledgement_age_seconds: Decimal | None,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if _stale_acknowledgement(
        input_row,
        stale_acknowledgement_seconds=stale_acknowledgement_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
    ):
        reasons.add(STALE_ACKNOWLEDGEMENT_REASON)
    if input_row.team_owner_id is None:
        reasons.add(MISSING_TEAM_OWNER_REASON)
    if input_row.source_contradicts_outcome:
        reasons.add(CONTRADICTORY_SOURCE_REASON)
    if not reasons.intersection(BLOCKING_REASON_CODES):
        if market_close_age_seconds > close_age_pressure_seconds:
            reasons.add(CLOSE_AGE_PRESSURE_REASON)
    if not reasons:
        reasons.add(CLEAR_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _stale_acknowledgement(
    input_row: MarketCloseAcknowledgementRecheckInputRow,
    *,
    stale_acknowledgement_seconds: Decimal,
    acknowledgement_age_seconds: Decimal | None,
) -> bool:
    if input_row.acknowledgement_at is None:
        return True
    if input_row.acknowledged_update_id != input_row.latest_update_id:
        return True
    if input_row.acknowledgement_at < input_row.latest_update_at:
        return True
    if (
        acknowledgement_age_seconds is not None
        and acknowledgement_age_seconds > stale_acknowledgement_seconds
    ):
        return True
    return False


def _acknowledgement_lag_seconds(
    input_row: MarketCloseAcknowledgementRecheckInputRow,
) -> Decimal | None:
    if input_row.acknowledgement_at is None:
        return None
    if input_row.acknowledged_update_id != input_row.latest_update_id:
        return None
    if input_row.acknowledgement_at < input_row.latest_update_at:
        return None
    return _elapsed_seconds(input_row.latest_update_at, input_row.acknowledgement_at)


def _validate_input_time_shape(row: MarketCloseAcknowledgementRecheckInputRow) -> None:
    if row.latest_update_at < row.market_closed_at:
        raise ValueError("latest_update_at must not be before market_closed_at")
    if row.acknowledgement_at is not None and row.acknowledgement_at < row.market_closed_at:
        raise ValueError("acknowledgement_at must not be before market_closed_at")


def _validate_input_times_against_generated_at(
    row: MarketCloseAcknowledgementRecheckInputRow,
    *,
    generated_at: datetime,
) -> None:
    _age_seconds(
        generated_at,
        row.market_closed_at,
        earlier_field_name="market_closed_at",
    )
    _age_seconds(
        generated_at,
        row.latest_update_at,
        earlier_field_name="latest_update_at",
    )
    if row.acknowledgement_at is not None:
        _age_seconds(
            generated_at,
            row.acknowledgement_at,
            earlier_field_name="acknowledgement_at",
        )


def _validate_row(row: MarketCloseAcknowledgementRecheckRow) -> None:
    _validate_input_time_shape(
        MarketCloseAcknowledgementRecheckInputRow(
            market_id=row.market_id,
            team_owner_id=row.team_owner_id,
            source_id=row.source_id,
            latest_update_id=row.latest_update_id,
            acknowledged_update_id=row.acknowledged_update_id,
            market_closed_at=row.market_closed_at,
            latest_update_at=row.latest_update_at,
            acknowledgement_at=row.acknowledgement_at,
            source_contradicts_outcome=row.source_contradicts_outcome,
        ),
    )
    if row.acknowledgement_at is None:
        if row.acknowledgement_age_seconds is not None:
            raise ValueError("acknowledgement_age_seconds requires acknowledgement_at")
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError("acknowledgement_lag_seconds requires acknowledgement_at")
    else:
        if row.acknowledgement_lag_seconds != _expected_acknowledgement_lag_seconds(row):
            raise ValueError("acknowledgement_lag_seconds must match latest update")
    if row.market_close_age_seconds < row.update_age_seconds:
        raise ValueError("market_close_age_seconds must include update age")
    expected_reasons = _expected_reason_codes_from_row(row)
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row state")
    if row.recheck_status != _row_status(row.reason_codes):
        raise ValueError("recheck_status must match reason_codes")


def _expected_acknowledgement_lag_seconds(
    row: MarketCloseAcknowledgementRecheckRow,
) -> Decimal | None:
    if row.acknowledgement_at is None:
        return None
    if row.acknowledged_update_id != row.latest_update_id:
        return None
    if row.acknowledgement_at < row.latest_update_at:
        return None
    return _elapsed_seconds(row.latest_update_at, row.acknowledgement_at)


def _expected_reason_codes_from_row(
    row: MarketCloseAcknowledgementRecheckRow,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if row.acknowledgement_at is None:
        reasons.add(STALE_ACKNOWLEDGEMENT_REASON)
    elif row.acknowledged_update_id != row.latest_update_id:
        reasons.add(STALE_ACKNOWLEDGEMENT_REASON)
    elif row.acknowledgement_at < row.latest_update_at:
        reasons.add(STALE_ACKNOWLEDGEMENT_REASON)
    elif (
        row.acknowledgement_age_seconds is not None
        and row.acknowledgement_age_seconds > row.stale_acknowledgement_seconds
    ):
        reasons.add(STALE_ACKNOWLEDGEMENT_REASON)
    if row.team_owner_id is None:
        reasons.add(MISSING_TEAM_OWNER_REASON)
    if row.source_contradicts_outcome:
        reasons.add(CONTRADICTORY_SOURCE_REASON)
    if not reasons.intersection(BLOCKING_REASON_CODES):
        if row.market_close_age_seconds > row.close_age_pressure_seconds:
            reasons.add(CLOSE_AGE_PRESSURE_REASON)
    if not reasons:
        reasons.add(CLEAR_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _validate_report(report: MarketCloseAcknowledgementRecheckReport) -> None:
    rows = report.rows
    for row in rows:
        _validate_report_row_times(report.generated_at, row)
    if report.market_count != _decimal_count(len(rows)):
        raise ValueError("market_count must match rows")
    if report.pass_market_count != _status_count(rows, "pass"):
        raise ValueError("pass_market_count must match rows")
    if report.watch_market_count != _status_count(rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    expected_recheck_count = _decimal_count(
        sum(1 for row in rows if row.recheck_status != "pass"),
    )
    if report.recheck_market_count != expected_recheck_count:
        raise ValueError("recheck_market_count must match rows")
    if (
        report.pass_market_count + report.watch_market_count + report.blocked_market_count
        != report.market_count
    ):
        raise ValueError("status counts must match market_count")
    expected_reason_counts = (
        (STALE_ACKNOWLEDGEMENT_REASON, report.stale_acknowledgement_count),
        (MISSING_TEAM_OWNER_REASON, report.missing_team_owner_count),
        (CONTRADICTORY_SOURCE_REASON, report.contradictory_source_count),
        (CLOSE_AGE_PRESSURE_REASON, report.close_age_pressure_count),
    )
    for reason_code, expected_count in expected_reason_counts:
        if expected_count != _reason_count(rows, reason_code):
            raise ValueError("reason counts must match rows")
    if report.recheck_ratio != _ratio(report.recheck_market_count, report.market_count):
        raise ValueError("recheck_ratio must match rows")
    if report.max_market_close_age_seconds != _max_optional(
        tuple(row.market_close_age_seconds for row in rows),
    ):
        raise ValueError("max_market_close_age_seconds must match rows")
    if report.max_update_age_seconds != _max_optional(
        tuple(row.update_age_seconds for row in rows),
    ):
        raise ValueError("max_update_age_seconds must match rows")
    if report.max_acknowledgement_age_seconds != _max_optional(
        tuple(row.acknowledgement_age_seconds for row in rows),
    ):
        raise ValueError("max_acknowledgement_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")


def _validate_report_row_times(
    generated_at: datetime,
    row: MarketCloseAcknowledgementRecheckRow,
) -> None:
    if row.market_close_age_seconds != _age_seconds(
        generated_at,
        row.market_closed_at,
        earlier_field_name="market_closed_at",
    ):
        raise ValueError("market_close_age_seconds must match generated_at")
    if row.update_age_seconds != _age_seconds(
        generated_at,
        row.latest_update_at,
        earlier_field_name="latest_update_at",
    ):
        raise ValueError("update_age_seconds must match generated_at")
    if row.acknowledgement_at is not None:
        expected_acknowledgement_age = _age_seconds(
            generated_at,
            row.acknowledgement_at,
            earlier_field_name="acknowledgement_at",
        )
        if row.acknowledgement_age_seconds != expected_acknowledgement_age:
            raise ValueError("acknowledgement_age_seconds must match generated_at")


def _normalize_rows(
    value: object,
) -> tuple[MarketCloseAcknowledgementRecheckRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketCloseAcknowledgementRecheckRow:
            raise ValueError("rows must contain MarketCloseAcknowledgementRecheckRow")
        require_paper_only_flags("market close acknowledgement recheck row", row)
        key = (row.market_id, row.latest_update_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by market_id and latest_update_id")
        seen_keys.add(key)
    expected_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected_rows:
        raise ValueError("rows must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, allowed=allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _row_sort_key(
    row: MarketCloseAcknowledgementRecheckRow,
) -> tuple[int, int, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.recheck_status],
        REASON_RANK[row.reason_codes[0]],
        -_row_issue_age_seconds(row),
        row.market_id,
        row.latest_update_id,
        row.source_id,
    )


def _row_issue_age_seconds(row: MarketCloseAcknowledgementRecheckRow) -> Decimal:
    return max(
        tuple(
            value
            for value in (
                row.market_close_age_seconds,
                row.update_age_seconds,
                row.acknowledgement_age_seconds,
                row.acknowledgement_lag_seconds,
            )
            if value is not None
        ),
        default=ZERO,
    )


def _report_reason_codes(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    }
    if not reasons:
        reasons.add(CLEAR_REASON)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reasons)


def _report_status(rows: tuple[MarketCloseAcknowledgementRecheckRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.recheck_status == "blocked" for row in rows):
        return "blocked"
    if any(row.recheck_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _status_count(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.recheck_status == status))


def _reason_count(
    rows: tuple[MarketCloseAcknowledgementRecheckRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_optional(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return None
    return max(present_values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _age_seconds(
    later: datetime,
    earlier: datetime,
    *,
    later_field_name: str = "generated_at",
    earlier_field_name: str,
) -> Decimal:
    later_utc = _as_utc(later_field_name, later)
    earlier_utc = _as_utc(earlier_field_name, earlier)
    if earlier_utc > later_utc:
        raise ValueError(f"{earlier_field_name} must not be after {later_field_name}")
    return _elapsed_seconds(earlier_utc, later_utc)


def _elapsed_seconds(earlier: datetime, later: datetime) -> Decimal:
    earlier_utc = _as_utc("earlier", earlier)
    later_utc = _as_utc("later", later)
    if later_utc < earlier_utc:
        raise ValueError("elapsed seconds must be nonnegative")
    delta = later_utc - earlier_utc
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(QUANT)


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


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if value != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_status(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known status")


def _require_reason_code(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_string(field_name, value)


def _require_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


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
    "DEFAULT_MARKET_CLOSE_ACKNOWLEDGEMENT_RECHECK_CONFIG_VERSION",
    "MarketCloseAcknowledgementRecheckConfig",
    "MarketCloseAcknowledgementRecheckInputRow",
    "MarketCloseAcknowledgementRecheckReport",
    "MarketCloseAcknowledgementRecheckRow",
    "build_market_close_acknowledgement_recheck_report",
    "market_close_acknowledgement_recheck_report_payload",
)
