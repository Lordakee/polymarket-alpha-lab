"""Pure typed market staleness SLA v6 report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_CONFIG_VERSION = "strategy-market-staleness-sla-v6"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

SOURCE_CRITICALITIES = ("critical", "normal", "low")
SLA_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = SLA_STATUSES
EMPTY_REASON_CODE = "market_staleness_sla_empty"
STATE_REASON_CODES = (
    "refresh_within_sla",
    "last_refresh_watch",
    "last_refresh_blocked",
)
SOURCE_REASON_CODES = (
    "critical_source",
    "normal_source",
    "low_source",
)
RESOLUTION_REASON_CODES = (
    "resolution_imminent",
    "resolution_near",
    "resolution_standard",
    "resolution_distant",
)
REASON_CODES = tuple(
    sorted((*STATE_REASON_CODES, *SOURCE_REASON_CODES, *RESOLUTION_REASON_CODES, EMPTY_REASON_CODE)),
)
STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class StrategyMarketStalenessSlaV6Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    imminent_resolution_minutes: Decimal = Decimal("60.000000")
    near_resolution_minutes: Decimal = Decimal("360.000000")
    standard_resolution_minutes: Decimal = Decimal("1440.000000")
    imminent_refresh_minutes: Decimal = Decimal("5.000000")
    near_refresh_minutes: Decimal = Decimal("15.000000")
    standard_refresh_minutes: Decimal = Decimal("60.000000")
    distant_refresh_minutes: Decimal = Decimal("240.000000")
    critical_source_multiplier: Decimal = Decimal("0.500000")
    normal_source_multiplier: Decimal = Decimal("1.000000")
    low_source_multiplier: Decimal = Decimal("2.000000")
    watch_multiple: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "imminent_resolution_minutes",
            "near_resolution_minutes",
            "standard_resolution_minutes",
            "imminent_refresh_minutes",
            "near_refresh_minutes",
            "standard_refresh_minutes",
            "distant_refresh_minutes",
            "critical_source_multiplier",
            "normal_source_multiplier",
            "low_source_multiplier",
            "watch_multiple",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.imminent_resolution_minutes >= self.near_resolution_minutes:
            raise ValueError("near_resolution_minutes must exceed imminent_resolution_minutes")
        if self.near_resolution_minutes >= self.standard_resolution_minutes:
            raise ValueError("standard_resolution_minutes must exceed near_resolution_minutes")
        if self.watch_multiple <= ONE:
            raise ValueError("watch_multiple must exceed 1.000000")
        reject_unsafe_surface_fields("strategy market staleness SLA v6 config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketStalenessSlaV6Input:
    market_slug: str
    team_id: str
    category_id: str
    time_to_resolution_minutes: Decimal
    source_criticality: str
    last_refresh_age_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _require_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_source_criticality("source_criticality", self.source_criticality)
        object.__setattr__(
            self,
            "last_refresh_age_minutes",
            _require_nonnegative_decimal(
                "last_refresh_age_minutes",
                self.last_refresh_age_minutes,
            ),
        )
        reject_unsafe_surface_fields("strategy market staleness SLA v6 input", self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketStalenessSlaV6Row:
    market_slug: str
    team_id: str
    category_id: str
    time_to_resolution_minutes: Decimal
    source_criticality: str
    last_refresh_age_minutes: Decimal
    sla_refresh_minutes: Decimal
    sla_status: str
    next_refresh_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _require_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_source_criticality("source_criticality", self.source_criticality)
        for field_name in (
            "last_refresh_age_minutes",
            "sla_refresh_minutes",
            "next_refresh_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("sla_status", self.sla_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        reject_unsafe_surface_fields("strategy market staleness SLA v6 row", self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class StrategyMarketStalenessSlaV6Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyMarketStalenessSlaV6Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("market_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        reject_unsafe_surface_fields("strategy market staleness SLA v6 report", self)
        require_paper_only_flags("report", self)


def build_strategy_market_staleness_sla_v6_report(
    markets: Iterable[object],
    *,
    config: StrategyMarketStalenessSlaV6Config,
    generated_at: datetime,
) -> StrategyMarketStalenessSlaV6Report:
    if type(config) is not StrategyMarketStalenessSlaV6Config:
        raise ValueError("config must be a StrategyMarketStalenessSlaV6Config")
    require_paper_only_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_from_input(input_row, config=config) for input_row in _normalize_inputs(markets)),
            key=_row_sort_key,
        ),
    )
    return StrategyMarketStalenessSlaV6Report(
        generated_at=generated_at,
        config_version=config.config_version,
        market_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_market_staleness_sla_v6_report_payload(
    report: StrategyMarketStalenessSlaV6Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketStalenessSlaV6Report:
        raise ValueError("report must be a StrategyMarketStalenessSlaV6Report")
    return json_ready_no_floats(report)


def _row_from_input(
    input_row: StrategyMarketStalenessSlaV6Input,
    *,
    config: StrategyMarketStalenessSlaV6Config,
) -> StrategyMarketStalenessSlaV6Row:
    resolution_reason, base_refresh_minutes = _resolution_bucket(input_row, config)
    source_reason, source_multiplier = _source_multiplier(input_row, config)
    sla_refresh_minutes = _multiply_decimal(base_refresh_minutes, source_multiplier)
    sla_status = _sla_status(
        last_refresh_age_minutes=input_row.last_refresh_age_minutes,
        sla_refresh_minutes=sla_refresh_minutes,
        watch_multiple=config.watch_multiple,
    )
    next_refresh_minutes = _next_refresh_minutes(
        status=sla_status,
        last_refresh_age_minutes=input_row.last_refresh_age_minutes,
        sla_refresh_minutes=sla_refresh_minutes,
    )
    return StrategyMarketStalenessSlaV6Row(
        market_slug=input_row.market_slug,
        team_id=input_row.team_id,
        category_id=input_row.category_id,
        time_to_resolution_minutes=input_row.time_to_resolution_minutes,
        source_criticality=input_row.source_criticality,
        last_refresh_age_minutes=input_row.last_refresh_age_minutes,
        sla_refresh_minutes=sla_refresh_minutes,
        sla_status=sla_status,
        next_refresh_minutes=next_refresh_minutes,
        reason_codes=tuple(
            sorted(
                (
                    _state_reason(sla_status),
                    source_reason,
                    resolution_reason,
                ),
            ),
        ),
    )


def _normalize_inputs(
    markets: Iterable[object],
) -> tuple[StrategyMarketStalenessSlaV6Input, ...]:
    if isinstance(markets, (str, bytes)):
        raise ValueError("markets must be an iterable")
    try:
        items = tuple(markets)
    except TypeError as exc:
        raise ValueError("markets must be an iterable") from exc
    return tuple(_input_from_supplied_shape(item) for item in items)


def _input_from_supplied_shape(item: object) -> StrategyMarketStalenessSlaV6Input:
    if type(item) is StrategyMarketStalenessSlaV6Input:
        reject_unsafe_surface_fields("strategy market staleness SLA v6 input", item)
        require_paper_only_flags("input", item)
        return item
    reject_unsafe_surface_fields("strategy market staleness SLA v6 input", item)
    require_paper_only_flags("input", item)
    return StrategyMarketStalenessSlaV6Input(
        market_slug=_required_attr(item, "market_slug"),
        team_id=_required_attr(item, "team_id"),
        category_id=_required_attr(item, "category_id"),
        time_to_resolution_minutes=_required_attr(item, "time_to_resolution_minutes"),
        source_criticality=_required_attr(item, "source_criticality"),
        last_refresh_age_minutes=_required_attr(item, "last_refresh_age_minutes"),
    )


def _normalize_rows(
    rows: Iterable[StrategyMarketStalenessSlaV6Row],
) -> tuple[StrategyMarketStalenessSlaV6Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not StrategyMarketStalenessSlaV6Row:
            raise ValueError("rows must contain StrategyMarketStalenessSlaV6Row values")
        reject_unsafe_surface_fields("strategy market staleness SLA v6 row", row)
        require_paper_only_flags("row", row)
    return items


def _resolution_bucket(
    row: StrategyMarketStalenessSlaV6Input,
    config: StrategyMarketStalenessSlaV6Config,
) -> tuple[str, Decimal]:
    if row.time_to_resolution_minutes <= config.imminent_resolution_minutes:
        return "resolution_imminent", config.imminent_refresh_minutes
    if row.time_to_resolution_minutes <= config.near_resolution_minutes:
        return "resolution_near", config.near_refresh_minutes
    if row.time_to_resolution_minutes <= config.standard_resolution_minutes:
        return "resolution_standard", config.standard_refresh_minutes
    return "resolution_distant", config.distant_refresh_minutes


def _source_multiplier(
    row: StrategyMarketStalenessSlaV6Input,
    config: StrategyMarketStalenessSlaV6Config,
) -> tuple[str, Decimal]:
    if row.source_criticality == "critical":
        return "critical_source", config.critical_source_multiplier
    if row.source_criticality == "normal":
        return "normal_source", config.normal_source_multiplier
    return "low_source", config.low_source_multiplier


def _sla_status(
    *,
    last_refresh_age_minutes: Decimal,
    sla_refresh_minutes: Decimal,
    watch_multiple: Decimal,
) -> str:
    if last_refresh_age_minutes > _multiply_decimal(sla_refresh_minutes, watch_multiple):
        return "blocked"
    if last_refresh_age_minutes > sla_refresh_minutes:
        return "watch"
    return "pass"


def _next_refresh_minutes(
    *,
    status: str,
    last_refresh_age_minutes: Decimal,
    sla_refresh_minutes: Decimal,
) -> Decimal:
    if status != "pass":
        return ZERO
    remaining = sla_refresh_minutes - last_refresh_age_minutes
    if remaining < ZERO:
        return ZERO
    return _quantize(remaining)


def _state_reason(status: str) -> str:
    if status == "blocked":
        return "last_refresh_blocked"
    if status == "watch":
        return "last_refresh_watch"
    return "refresh_within_sla"


def _status_count(rows: tuple[StrategyMarketStalenessSlaV6Row, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.sla_status == status))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _report_status(rows: tuple[StrategyMarketStalenessSlaV6Row, ...]) -> str:
    if any(row.sla_status == "blocked" for row in rows):
        return "blocked"
    if any(row.sla_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[StrategyMarketStalenessSlaV6Row, ...]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(sorted(reason_codes))


def _row_sort_key(row: StrategyMarketStalenessSlaV6Row) -> tuple[int, str]:
    return STATUS_SORT_PRIORITY[row.sla_status], row.market_slug


def _validate_row_consistency(row: StrategyMarketStalenessSlaV6Row) -> None:
    expected_state_reason = _state_reason(row.sla_status)
    if expected_state_reason not in row.reason_codes:
        raise ValueError("reason_codes must match row state")
    if row.source_criticality == "critical" and "critical_source" not in row.reason_codes:
        raise ValueError("reason_codes must match source criticality")
    if row.source_criticality == "normal" and "normal_source" not in row.reason_codes:
        raise ValueError("reason_codes must match source criticality")
    if row.source_criticality == "low" and "low_source" not in row.reason_codes:
        raise ValueError("reason_codes must match source criticality")
    if not any(reason_code in row.reason_codes for reason_code in RESOLUTION_REASON_CODES):
        raise ValueError("reason_codes must include a resolution bucket")
    if row.sla_status in ("watch", "blocked") and row.next_refresh_minutes != ZERO:
        raise ValueError("next_refresh_minutes must be zero for stale rows")
    if row.sla_status == "pass" and row.next_refresh_minutes != _next_refresh_minutes(
        status=row.sla_status,
        last_refresh_age_minutes=row.last_refresh_age_minutes,
        sla_refresh_minutes=row.sla_refresh_minutes,
    ):
        raise ValueError("next_refresh_minutes must match remaining SLA")


def _validate_report_consistency(report: StrategyMarketStalenessSlaV6Report) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.market_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("market_count must match status counts")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    market_slugs = tuple(row.market_slug for row in report.rows)
    if len(set(market_slugs)) != len(market_slugs):
        raise ValueError("rows must contain unique market_slug values")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_source_criticality(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_CRITICALITIES:
        raise ValueError(f"{field_name} must be one of critical, normal, or low")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SLA_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be sorted")
    return reason_codes


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "StrategyMarketStalenessSlaV6Config",
    "StrategyMarketStalenessSlaV6Input",
    "StrategyMarketStalenessSlaV6Report",
    "StrategyMarketStalenessSlaV6Row",
    "build_strategy_market_staleness_sla_v6_report",
    "strategy_market_staleness_sla_v6_report_payload",
)
