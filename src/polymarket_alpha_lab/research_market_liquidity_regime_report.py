"""Pure report-only liquidity-regime report for caller-supplied observations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "MarketLiquidityRegimeConfig",
    "MarketLiquidityRegimeInputRow",
    "MarketLiquidityRegimeReasonCodeCount",
    "MarketLiquidityRegimeReport",
    "MarketLiquidityRegimeReportRow",
    "build_research_market_liquidity_regime_report",
    "research_market_liquidity_regime_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-liquidity-regime-report-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
RATE_QUANTUM = Decimal("0.000001")
MONEY_QUANTUM = Decimal("0.01")
COUNT_QUANTUM = Decimal("1")


@dataclass(frozen=True)
class MarketLiquidityRegimeConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_depth_usdc: Decimal = Decimal("2500.00")
    min_watch_depth_usdc: Decimal = Decimal("500.00")
    max_pass_spread_rate: Decimal = Decimal("0.020000")
    max_watch_spread_rate: Decimal = Decimal("0.070000")
    min_pass_activity_usdc: Decimal = Decimal("1000.00")
    min_watch_activity_usdc: Decimal = Decimal("100.00")
    min_pass_activity_count: Decimal = Decimal("10")
    min_watch_activity_count: Decimal = Decimal("2")
    near_settlement_window_hours: Decimal = Decimal("6.000000")
    max_pass_near_settlement_change_rate: Decimal = Decimal("0.030000")
    max_watch_near_settlement_change_rate: Decimal = Decimal("0.120000")
    max_pass_fee_friction_rate: Decimal = Decimal("0.010000")
    max_watch_fee_friction_rate: Decimal = Decimal("0.030000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("min_pass_depth_usdc", "min_watch_depth_usdc"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_money_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_activity_usdc", "min_watch_activity_usdc"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_money_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_activity_count", "min_watch_activity_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "near_settlement_window_hours",
            _quantize_rate(
                _require_nonnegative_decimal(
                    "near_settlement_window_hours",
                    self.near_settlement_window_hours,
                ),
            ),
        )
        for field_name in (
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "max_pass_near_settlement_change_rate",
            "max_watch_near_settlement_change_rate",
            "max_pass_fee_friction_rate",
            "max_watch_fee_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_rate_decimal(field_name, getattr(self, field_name)),
            )
        _require_pass_watch_ceiling(
            "max_pass_spread_rate",
            self.max_pass_spread_rate,
            "max_watch_spread_rate",
            self.max_watch_spread_rate,
        )
        _require_pass_watch_ceiling(
            "max_pass_near_settlement_change_rate",
            self.max_pass_near_settlement_change_rate,
            "max_watch_near_settlement_change_rate",
            self.max_watch_near_settlement_change_rate,
        )
        _require_pass_watch_ceiling(
            "max_pass_fee_friction_rate",
            self.max_pass_fee_friction_rate,
            "max_watch_fee_friction_rate",
            self.max_watch_fee_friction_rate,
        )
        if self.min_watch_depth_usdc >= self.min_pass_depth_usdc:
            raise ValueError("min_watch_depth_usdc must be less than min_pass_depth_usdc")
        if self.min_watch_activity_usdc >= self.min_pass_activity_usdc:
            raise ValueError("min_watch_activity_usdc must be less than min_pass_activity_usdc")
        if self.min_watch_activity_count >= self.min_pass_activity_count:
            raise ValueError(
                "min_watch_activity_count must be less than min_pass_activity_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketLiquidityRegimeInputRow:
    raw_market_id: str
    raw_source_id: str | None
    observed_at: datetime
    settlement_at: datetime
    depth_usdc: Decimal
    spread_rate: Decimal
    activity_usdc: Decimal
    activity_count: Decimal
    near_settlement_change_rate: Decimal
    fee_friction_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeInputRow, "input row")
        _require_canonical_string("raw_market_id", self.raw_market_id)
        object.__setattr__(
            self,
            "raw_source_id",
            _require_optional_canonical_string("raw_source_id", self.raw_source_id),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "settlement_at",
            _as_utc("settlement_at", self.settlement_at),
        )
        if self.settlement_at < self.observed_at:
            raise ValueError("settlement_at must not be before observed_at")
        object.__setattr__(
            self,
            "depth_usdc",
            _require_nonnegative_money_decimal("depth_usdc", self.depth_usdc),
        )
        object.__setattr__(
            self,
            "activity_usdc",
            _require_nonnegative_money_decimal("activity_usdc", self.activity_usdc),
        )
        object.__setattr__(
            self,
            "activity_count",
            _require_nonnegative_whole_decimal("activity_count", self.activity_count),
        )
        for field_name in (
            "spread_rate",
            "near_settlement_change_rate",
            "fee_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_rate_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketLiquidityRegimeReportRow:
    row_number: Decimal
    observed_at: datetime
    settlement_at: datetime
    hours_to_settlement: Decimal
    depth_usdc: Decimal
    spread_rate: Decimal
    activity_usdc: Decimal
    activity_count: Decimal
    near_settlement_change_rate: Decimal
    fee_friction_rate: Decimal
    depth_status: str
    spread_status: str
    activity_status: str
    near_settlement_status: str
    fee_friction_status: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeReportRow, "report row")
        object.__setattr__(
            self,
            "row_number",
            _require_positive_whole_decimal("row_number", self.row_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "settlement_at",
            _as_utc("settlement_at", self.settlement_at),
        )
        object.__setattr__(
            self,
            "hours_to_settlement",
            _require_nonnegative_decimal("hours_to_settlement", self.hours_to_settlement),
        )
        object.__setattr__(
            self,
            "depth_usdc",
            _require_nonnegative_money_decimal("depth_usdc", self.depth_usdc),
        )
        object.__setattr__(
            self,
            "activity_usdc",
            _require_nonnegative_money_decimal("activity_usdc", self.activity_usdc),
        )
        object.__setattr__(
            self,
            "activity_count",
            _require_nonnegative_whole_decimal("activity_count", self.activity_count),
        )
        for field_name in (
            "spread_rate",
            "near_settlement_change_rate",
            "fee_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_rate_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_status",
            "spread_status",
            "activity_status",
            "near_settlement_status",
            "fee_friction_status",
            "status",
        ):
            _require_status(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report row", self)
        _validate_report_row_consistency(self)


@dataclass(frozen=True)
class MarketLiquidityRegimeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketLiquidityRegimeReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    minimum_depth_usdc: Decimal | None
    maximum_spread_rate: Decimal | None
    total_activity_usdc: Decimal
    maximum_fee_friction_rate: Decimal | None
    minimum_hours_to_settlement: Decimal | None
    status: str
    rows: tuple[MarketLiquidityRegimeReportRow, ...]
    reason_code_counts: tuple[MarketLiquidityRegimeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketLiquidityRegimeReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("observation_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_depth_usdc",
            _require_optional_money_decimal("minimum_depth_usdc", self.minimum_depth_usdc),
        )
        object.__setattr__(
            self,
            "maximum_spread_rate",
            _require_optional_rate_decimal("maximum_spread_rate", self.maximum_spread_rate),
        )
        object.__setattr__(
            self,
            "total_activity_usdc",
            _require_nonnegative_money_decimal("total_activity_usdc", self.total_activity_usdc),
        )
        object.__setattr__(
            self,
            "maximum_fee_friction_rate",
            _require_optional_rate_decimal(
                "maximum_fee_friction_rate",
                self.maximum_fee_friction_rate,
            ),
        )
        object.__setattr__(
            self,
            "minimum_hours_to_settlement",
            _require_optional_nonnegative_decimal(
                "minimum_hours_to_settlement",
                self.minimum_hours_to_settlement,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_liquidity_regime_report(
    rows: Iterable[object],
    *,
    config: MarketLiquidityRegimeConfig,
    generated_at: datetime,
) -> MarketLiquidityRegimeReport:
    if type(config) is not MarketLiquidityRegimeConfig:
        raise ValueError("config must be a MarketLiquidityRegimeConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = tuple(
        sorted(
            _normalize_input_rows(rows),
            key=lambda row: (row.raw_market_id, row.raw_source_id or "", row.observed_at),
        ),
    )
    for row in input_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    report_rows = tuple(
        _report_row_from_input(
            row,
            row_number=_decimal_count(index),
            config=config,
        )
        for index, row in enumerate(input_rows, start=1)
    )
    reason_codes = _summary_reason_codes(report_rows)

    return MarketLiquidityRegimeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(report_rows)),
        pass_count=_decimal_count(_status_count(report_rows, "pass")),
        watch_count=_decimal_count(_status_count(report_rows, "watch")),
        blocked_count=_decimal_count(_status_count(report_rows, "blocked")),
        minimum_depth_usdc=_minimum_depth(report_rows),
        maximum_spread_rate=_maximum_spread(report_rows),
        total_activity_usdc=_total_activity(report_rows),
        maximum_fee_friction_rate=_maximum_fee_friction(report_rows),
        minimum_hours_to_settlement=_minimum_hours_to_settlement(report_rows),
        status=_summary_status(reason_codes),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_regime_report_payload(
    report: MarketLiquidityRegimeReport,
) -> dict[str, Any]:
    if type(report) is not MarketLiquidityRegimeReport:
        raise ValueError("report must be a MarketLiquidityRegimeReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_row_from_input(
    row: MarketLiquidityRegimeInputRow,
    *,
    row_number: Decimal,
    config: MarketLiquidityRegimeConfig,
) -> MarketLiquidityRegimeReportRow:
    hours_to_settlement = _hours_between(row.settlement_at, row.observed_at)
    depth_status = _floor_status(
        row.depth_usdc,
        pass_limit=config.min_pass_depth_usdc,
        watch_limit=config.min_watch_depth_usdc,
    )
    spread_status = _ceiling_status(
        row.spread_rate,
        pass_limit=config.max_pass_spread_rate,
        watch_limit=config.max_watch_spread_rate,
    )
    activity_status = _combined_status(
        (
            _floor_status(
                row.activity_usdc,
                pass_limit=config.min_pass_activity_usdc,
                watch_limit=config.min_watch_activity_usdc,
            ),
            _floor_status(
                row.activity_count,
                pass_limit=config.min_pass_activity_count,
                watch_limit=config.min_watch_activity_count,
            ),
        ),
    )
    near_settlement_status = _near_settlement_status(
        hours_to_settlement=hours_to_settlement,
        change_rate=row.near_settlement_change_rate,
        config=config,
    )
    fee_friction_status = _ceiling_status(
        row.fee_friction_rate,
        pass_limit=config.max_pass_fee_friction_rate,
        watch_limit=config.max_watch_fee_friction_rate,
    )
    status = _combined_status(
        (
            depth_status,
            spread_status,
            activity_status,
            near_settlement_status,
            fee_friction_status,
        ),
    )
    return MarketLiquidityRegimeReportRow(
        row_number=row_number,
        observed_at=row.observed_at,
        settlement_at=row.settlement_at,
        hours_to_settlement=hours_to_settlement,
        depth_usdc=row.depth_usdc,
        spread_rate=row.spread_rate,
        activity_usdc=row.activity_usdc,
        activity_count=row.activity_count,
        near_settlement_change_rate=row.near_settlement_change_rate,
        fee_friction_rate=row.fee_friction_rate,
        depth_status=depth_status,
        spread_status=spread_status,
        activity_status=activity_status,
        near_settlement_status=near_settlement_status,
        fee_friction_status=fee_friction_status,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            depth_status=depth_status,
            spread_status=spread_status,
            activity_status=activity_status,
            near_settlement_status=near_settlement_status,
            fee_friction_status=fee_friction_status,
            input_reason_codes=row.reason_codes,
        ),
    )


def _row_reason_codes(
    *,
    status: str,
    depth_status: str,
    spread_status: str,
    activity_status: str,
    near_settlement_status: str,
    fee_friction_status: str,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = {
        f"liquidity_regime_{status}",
        _depth_reason_code(depth_status),
        "tight_spread" if spread_status == "pass" else "wide_spread",
        _activity_reason_code(activity_status),
        _near_settlement_reason_code(near_settlement_status),
        _fee_friction_reason_code(fee_friction_status),
    }
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _depth_reason_code(status: str) -> str:
    if status == "pass":
        return "deep_depth"
    if status == "watch":
        return "moderate_depth"
    return "thin_depth"


def _activity_reason_code(status: str) -> str:
    if status == "pass":
        return "active_activity"
    if status == "watch":
        return "moderate_activity"
    return "inactive_activity"


def _near_settlement_reason_code(status: str) -> str:
    if status == "pass":
        return "stable_near_settlement"
    if status == "watch":
        return "near_settlement_liquidity_watch"
    return "near_settlement_liquidity_shift"


def _fee_friction_reason_code(status: str) -> str:
    if status == "pass":
        return "low_fee_friction"
    if status == "watch":
        return "moderate_fee_friction"
    return "high_fee_friction"


def _near_settlement_status(
    *,
    hours_to_settlement: Decimal,
    change_rate: Decimal,
    config: MarketLiquidityRegimeConfig,
) -> str:
    if hours_to_settlement > config.near_settlement_window_hours:
        return "pass"
    return _ceiling_status(
        change_rate,
        pass_limit=config.max_pass_near_settlement_change_rate,
        watch_limit=config.max_watch_near_settlement_change_rate,
    )


def _ceiling_status(value: Decimal, *, pass_limit: Decimal, watch_limit: Decimal) -> str:
    if value <= pass_limit:
        return "pass"
    if value <= watch_limit:
        return "watch"
    return "blocked"


def _floor_status(value: Decimal, *, pass_limit: Decimal, watch_limit: Decimal) -> str:
    if value >= pass_limit:
        return "pass"
    if value >= watch_limit:
        return "watch"
    return "blocked"


def _combined_status(statuses: tuple[str, ...]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[MarketLiquidityRegimeReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_regime_observations",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("liquidity_regime_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_liquidity_regime_observations",):
        return "blocked"
    if "liquidity_regime_blocked" in reason_codes:
        return "blocked"
    if "liquidity_regime_watch" in reason_codes:
        return "watch"
    return "pass"


def _normalize_input_rows(
    rows: Iterable[object],
) -> tuple[MarketLiquidityRegimeInputRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketLiquidityRegimeInputRow:
            raise ValueError("rows must contain MarketLiquidityRegimeInputRow")
        _require_hard_flags("input row", row)
    return normalized


def _normalize_report_rows(
    rows: Iterable[MarketLiquidityRegimeReportRow],
) -> tuple[MarketLiquidityRegimeReportRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketLiquidityRegimeReportRow:
            raise ValueError("rows must contain MarketLiquidityRegimeReportRow")
        _require_hard_flags("report row", row)
    return normalized


def _normalize_reason_code_counts(
    rows: Iterable[MarketLiquidityRegimeReasonCodeCount],
) -> tuple[MarketLiquidityRegimeReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketLiquidityRegimeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MarketLiquidityRegimeReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return tuple(sorted(normalized, key=lambda row: row.reason_code))


def _validate_report_row_consistency(row: MarketLiquidityRegimeReportRow) -> None:
    if row.settlement_at < row.observed_at:
        raise ValueError("settlement_at must not be before observed_at")
    if row.hours_to_settlement != _hours_between(row.settlement_at, row.observed_at):
        raise ValueError("hours_to_settlement must match observed_at and settlement_at")
    if row.status != _combined_status(
        (
            row.depth_status,
            row.spread_status,
            row.activity_status,
            row.near_settlement_status,
            row.fee_friction_status,
        ),
    ):
        raise ValueError("status must match component statuses")
    if f"liquidity_regime_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: MarketLiquidityRegimeReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.minimum_depth_usdc != _minimum_depth(report.rows):
        raise ValueError("minimum_depth_usdc must match rows")
    if report.maximum_spread_rate != _maximum_spread(report.rows):
        raise ValueError("maximum_spread_rate must match rows")
    if report.total_activity_usdc != _total_activity(report.rows):
        raise ValueError("total_activity_usdc must match rows")
    if report.maximum_fee_friction_rate != _maximum_fee_friction(report.rows):
        raise ValueError("maximum_fee_friction_rate must match rows")
    if report.minimum_hours_to_settlement != _minimum_hours_to_settlement(report.rows):
        raise ValueError("minimum_hours_to_settlement must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _status_count(rows: tuple[MarketLiquidityRegimeReportRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _minimum_depth(rows: tuple[MarketLiquidityRegimeReportRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return min(row.depth_usdc for row in rows)


def _maximum_spread(rows: tuple[MarketLiquidityRegimeReportRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return max(row.spread_rate for row in rows)


def _total_activity(rows: tuple[MarketLiquidityRegimeReportRow, ...]) -> Decimal:
    return _quantize_money(sum((row.activity_usdc for row in rows), ZERO))


def _maximum_fee_friction(
    rows: tuple[MarketLiquidityRegimeReportRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.fee_friction_rate for row in rows)


def _minimum_hours_to_settlement(
    rows: tuple[MarketLiquidityRegimeReportRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return min(row.hours_to_settlement for row in rows)


def _reason_code_counts(
    rows: tuple[MarketLiquidityRegimeReportRow, ...],
    summary_reason_codes: tuple[str, ...],
) -> tuple[MarketLiquidityRegimeReasonCodeCount, ...]:
    if not rows:
        return (
            MarketLiquidityRegimeReasonCodeCount(
                reason_code=summary_reason_codes[0],
                count=_decimal_count(1),
            ),
        )
    counts: Counter[str] = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        MarketLiquidityRegimeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(counts)
    )


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("settlement_at must not be before observed_at")
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_rate(seconds / Decimal("3600"))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_optional_money_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_money_decimal(field_name, value)


def _require_optional_rate_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_rate_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_rate_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > Decimal("1"):
        raise ValueError(f"{field_name} must be at most 1")
    return _quantize_rate(normalized)


def _require_positive_money_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_money_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_money_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_money(_require_nonnegative_decimal(field_name, value))


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_rate(value: Decimal) -> Decimal:
    try:
        return value.quantize(RATE_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _quantize_money(value: Decimal) -> Decimal:
    try:
        return value.quantize(MONEY_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _require_reason_token(field_name, value)


def _require_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_reason_token(field_name: str, value: str) -> None:
    for character in value:
        if not (character.islower() or character.isdigit() or character in "-_/."):
            raise ValueError(f"{field_name} must use lowercase public tokens")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: set[str] = set()
    for reason_code in value:
        try:
            _require_reason_code("reason_code", reason_code)
        except ValueError as exc:
            raise ValueError(f"{field_name} must contain canonical reason codes") from exc
        normalized.add(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _require_pass_watch_ceiling(
    pass_field_name: str,
    pass_value: Decimal,
    watch_field_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{watch_field_name} must be greater than or equal to {pass_field_name}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
