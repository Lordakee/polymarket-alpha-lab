"""Pure Polymarket fee-assumption report for caller-supplied research rows."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "PolymarketFeeAssumptionConfig",
    "PolymarketFeeAssumptionInputRow",
    "PolymarketFeeAssumptionReasonCodeCount",
    "PolymarketFeeAssumptionReport",
    "PolymarketFeeAssumptionReportRow",
    "build_research_polymarket_fee_assumption_report",
    "research_polymarket_fee_assumption_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-polymarket-fee-assumption-report-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
RATE_QUANTUM = Decimal("0.000001")
MONEY_QUANTUM = Decimal("0.01")


@dataclass(frozen=True)
class PolymarketFeeAssumptionConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_pass_taker_fee_rate: Decimal = Decimal("0.000000")
    max_watch_taker_fee_rate: Decimal = Decimal("0.020000")
    max_pass_spread_rate: Decimal = Decimal("0.030000")
    max_watch_spread_rate: Decimal = Decimal("0.080000")
    min_pass_depth_usdc: Decimal = Decimal("2500.00")
    min_watch_depth_usdc: Decimal = Decimal("500.00")
    max_pass_settlement_friction_rate: Decimal = Decimal("0.010000")
    max_watch_settlement_friction_rate: Decimal = Decimal("0.030000")
    max_pass_refresh_age_seconds: Decimal = Decimal("900")
    max_watch_refresh_age_seconds: Decimal = Decimal("3600")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_pass_taker_fee_rate",
            "max_watch_taker_fee_rate",
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "max_pass_settlement_friction_rate",
            "max_watch_settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_rate_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_depth_usdc", "min_watch_depth_usdc"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_money_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_pass_refresh_age_seconds", "max_watch_refresh_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_pass_watch_ceiling(
            "max_pass_taker_fee_rate",
            self.max_pass_taker_fee_rate,
            "max_watch_taker_fee_rate",
            self.max_watch_taker_fee_rate,
        )
        _require_pass_watch_ceiling(
            "max_pass_spread_rate",
            self.max_pass_spread_rate,
            "max_watch_spread_rate",
            self.max_watch_spread_rate,
        )
        _require_pass_watch_ceiling(
            "max_pass_settlement_friction_rate",
            self.max_pass_settlement_friction_rate,
            "max_watch_settlement_friction_rate",
            self.max_watch_settlement_friction_rate,
        )
        _require_pass_watch_ceiling(
            "max_pass_refresh_age_seconds",
            self.max_pass_refresh_age_seconds,
            "max_watch_refresh_age_seconds",
            self.max_watch_refresh_age_seconds,
        )
        if self.min_watch_depth_usdc >= self.min_pass_depth_usdc:
            raise ValueError("min_watch_depth_usdc must be less than min_pass_depth_usdc")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PolymarketFeeAssumptionInputRow:
    market_id: str
    source_id: str | None
    observed_at: datetime
    taker_fee_rate: Decimal
    spread_rate: Decimal
    depth_usdc: Decimal
    settlement_friction_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "source_id",
            _require_optional_canonical_string("source_id", self.source_id),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("taker_fee_rate", "spread_rate", "settlement_friction_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_rate_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "depth_usdc",
            _require_nonnegative_money_decimal("depth_usdc", self.depth_usdc),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class PolymarketFeeAssumptionReportRow:
    row_number: Decimal
    observed_at: datetime
    refresh_age_seconds: Decimal
    taker_fee_rate: Decimal
    spread_rate: Decimal
    depth_usdc: Decimal
    settlement_friction_rate: Decimal
    total_cost_rate: Decimal
    taker_fee_status: str
    spread_status: str
    depth_status: str
    settlement_friction_status: str
    refresh_cadence_status: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "row_number",
            _require_positive_whole_decimal("row_number", self.row_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "refresh_age_seconds",
            _require_nonnegative_decimal("refresh_age_seconds", self.refresh_age_seconds),
        )
        for field_name in (
            "taker_fee_rate",
            "spread_rate",
            "settlement_friction_rate",
            "total_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_rate_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "depth_usdc",
            _require_nonnegative_money_decimal("depth_usdc", self.depth_usdc),
        )
        for field_name in (
            "taker_fee_status",
            "spread_status",
            "depth_status",
            "settlement_friction_status",
            "refresh_cadence_status",
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
class PolymarketFeeAssumptionReasonCodeCount:
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
class PolymarketFeeAssumptionReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_total_cost_rate: Decimal | None
    minimum_depth_usdc: Decimal | None
    maximum_refresh_age_seconds: Decimal | None
    status: str
    rows: tuple[PolymarketFeeAssumptionReportRow, ...]
    reason_code_counts: tuple[PolymarketFeeAssumptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
            "average_total_cost_rate",
            _require_optional_rate_decimal(
                "average_total_cost_rate",
                self.average_total_cost_rate,
            ),
        )
        object.__setattr__(
            self,
            "minimum_depth_usdc",
            _require_optional_money_decimal("minimum_depth_usdc", self.minimum_depth_usdc),
        )
        object.__setattr__(
            self,
            "maximum_refresh_age_seconds",
            _require_optional_nonnegative_decimal(
                "maximum_refresh_age_seconds",
                self.maximum_refresh_age_seconds,
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


def build_research_polymarket_fee_assumption_report(
    rows: Iterable[object],
    *,
    config: PolymarketFeeAssumptionConfig,
    generated_at: datetime,
) -> PolymarketFeeAssumptionReport:
    if type(config) is not PolymarketFeeAssumptionConfig:
        raise ValueError("config must be a PolymarketFeeAssumptionConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = tuple(
        sorted(
            _normalize_input_rows(rows),
            key=lambda row: (row.market_id, row.source_id or "", row.observed_at),
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
            generated_at=generated_at_utc,
        )
        for index, row in enumerate(input_rows, start=1)
    )
    reason_codes = _summary_reason_codes(report_rows)

    return PolymarketFeeAssumptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(report_rows)),
        pass_count=_decimal_count(_status_count(report_rows, "pass")),
        watch_count=_decimal_count(_status_count(report_rows, "watch")),
        blocked_count=_decimal_count(_status_count(report_rows, "blocked")),
        average_total_cost_rate=_average_rate(report_rows),
        minimum_depth_usdc=_minimum_depth(report_rows),
        maximum_refresh_age_seconds=_maximum_refresh_age(report_rows),
        status=_summary_status(reason_codes),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_polymarket_fee_assumption_report_payload(
    report: PolymarketFeeAssumptionReport,
) -> dict[str, Any]:
    if type(report) is not PolymarketFeeAssumptionReport:
        raise ValueError("report must be a PolymarketFeeAssumptionReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_row_from_input(
    row: PolymarketFeeAssumptionInputRow,
    *,
    row_number: Decimal,
    config: PolymarketFeeAssumptionConfig,
    generated_at: datetime,
) -> PolymarketFeeAssumptionReportRow:
    refresh_age_seconds = _age_seconds(generated_at, row.observed_at)
    taker_fee_status = _ceiling_status(
        row.taker_fee_rate,
        pass_limit=config.max_pass_taker_fee_rate,
        watch_limit=config.max_watch_taker_fee_rate,
    )
    spread_status = _ceiling_status(
        row.spread_rate,
        pass_limit=config.max_pass_spread_rate,
        watch_limit=config.max_watch_spread_rate,
    )
    depth_status = _depth_status(
        row.depth_usdc,
        pass_limit=config.min_pass_depth_usdc,
        watch_limit=config.min_watch_depth_usdc,
    )
    settlement_friction_status = _ceiling_status(
        row.settlement_friction_rate,
        pass_limit=config.max_pass_settlement_friction_rate,
        watch_limit=config.max_watch_settlement_friction_rate,
    )
    refresh_cadence_status = _ceiling_status(
        refresh_age_seconds,
        pass_limit=config.max_pass_refresh_age_seconds,
        watch_limit=config.max_watch_refresh_age_seconds,
    )
    status = _combined_status(
        (
            taker_fee_status,
            spread_status,
            depth_status,
            settlement_friction_status,
            refresh_cadence_status,
        ),
    )
    return PolymarketFeeAssumptionReportRow(
        row_number=row_number,
        observed_at=row.observed_at,
        refresh_age_seconds=refresh_age_seconds,
        taker_fee_rate=row.taker_fee_rate,
        spread_rate=row.spread_rate,
        depth_usdc=row.depth_usdc,
        settlement_friction_rate=row.settlement_friction_rate,
        total_cost_rate=_quantize_rate(
            row.taker_fee_rate + row.spread_rate + row.settlement_friction_rate,
        ),
        taker_fee_status=taker_fee_status,
        spread_status=spread_status,
        depth_status=depth_status,
        settlement_friction_status=settlement_friction_status,
        refresh_cadence_status=refresh_cadence_status,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            taker_fee_status=taker_fee_status,
            spread_status=spread_status,
            depth_status=depth_status,
            settlement_friction_status=settlement_friction_status,
            refresh_cadence_status=refresh_cadence_status,
            input_reason_codes=row.reason_codes,
        ),
    )


def _row_reason_codes(
    *,
    status: str,
    taker_fee_status: str,
    spread_status: str,
    depth_status: str,
    settlement_friction_status: str,
    refresh_cadence_status: str,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = {
        f"fee_assumption_{status}",
        "low_taker_fee" if taker_fee_status == "pass" else "high_taker_fee",
        "tight_spread_assumption" if spread_status == "pass" else "wide_spread_assumption",
        _depth_reason_code(depth_status),
        _settlement_friction_reason_code(settlement_friction_status),
        _refresh_reason_code(refresh_cadence_status),
    }
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _depth_reason_code(status: str) -> str:
    if status == "pass":
        return "deep_depth_assumption"
    if status == "watch":
        return "moderate_depth_assumption"
    return "thin_depth_assumption"


def _settlement_friction_reason_code(status: str) -> str:
    if status == "pass":
        return "low_settlement_friction"
    if status == "watch":
        return "moderate_settlement_friction"
    return "high_settlement_friction"


def _refresh_reason_code(status: str) -> str:
    if status == "pass":
        return "fresh_refresh_cadence"
    if status == "watch":
        return "refresh_cadence_lag"
    return "stale_refresh_cadence"


def _ceiling_status(value: Decimal, *, pass_limit: Decimal, watch_limit: Decimal) -> str:
    if value <= pass_limit:
        return "pass"
    if value <= watch_limit:
        return "watch"
    return "blocked"


def _depth_status(value: Decimal, *, pass_limit: Decimal, watch_limit: Decimal) -> str:
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
    rows: tuple[PolymarketFeeAssumptionReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_fee_assumptions",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("fee_assumption_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_fee_assumptions",):
        return "blocked"
    if "fee_assumption_blocked" in reason_codes:
        return "blocked"
    if "fee_assumption_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[PolymarketFeeAssumptionReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[PolymarketFeeAssumptionReasonCodeCount, ...]:
    if not rows:
        return (
            PolymarketFeeAssumptionReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        PolymarketFeeAssumptionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_input_rows(
    rows: Iterable[object],
) -> tuple[PolymarketFeeAssumptionInputRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not PolymarketFeeAssumptionInputRow:
            raise ValueError("rows must contain PolymarketFeeAssumptionInputRow values")
        _require_hard_flags("input row", row)
    return values


def _normalize_report_rows(
    rows: object,
) -> tuple[PolymarketFeeAssumptionReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not PolymarketFeeAssumptionReportRow:
            raise ValueError("rows must contain PolymarketFeeAssumptionReportRow values")
        _require_hard_flags("report row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.row_number))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by row_number")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[PolymarketFeeAssumptionReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not PolymarketFeeAssumptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain PolymarketFeeAssumptionReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_report_row_consistency(row: PolymarketFeeAssumptionReportRow) -> None:
    expected_total_cost_rate = _quantize_rate(
        row.taker_fee_rate + row.spread_rate + row.settlement_friction_rate,
    )
    if row.total_cost_rate != expected_total_cost_rate:
        raise ValueError("total_cost_rate must match component rates")
    expected_status = _combined_status(
        (
            row.taker_fee_status,
            row.spread_status,
            row.depth_status,
            row.settlement_friction_status,
            row.refresh_cadence_status,
        ),
    )
    if row.status != expected_status:
        raise ValueError("status must match component statuses")
    expected_reason_codes = _row_reason_codes(
        status=row.status,
        taker_fee_status=row.taker_fee_status,
        spread_status=row.spread_status,
        depth_status=row.depth_status,
        settlement_friction_status=row.settlement_friction_status,
        refresh_cadence_status=row.refresh_cadence_status,
        input_reason_codes=tuple(
            code.removeprefix("input_")
            for code in row.reason_codes
            if code.startswith("input_")
        ),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row status")


def _validate_report_consistency(report: PolymarketFeeAssumptionReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_total_cost_rate != _average_rate(report.rows):
        raise ValueError("average_total_cost_rate must match rows")
    if report.minimum_depth_usdc != _minimum_depth(report.rows):
        raise ValueError("minimum_depth_usdc must match rows")
    if report.maximum_refresh_age_seconds != _maximum_refresh_age(report.rows):
        raise ValueError("maximum_refresh_age_seconds must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _status_count(rows: tuple[PolymarketFeeAssumptionReportRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_rate(rows: tuple[PolymarketFeeAssumptionReportRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return _quantize_rate(
        sum((row.total_cost_rate for row in rows), ZERO) / Decimal(len(rows)),
    )


def _minimum_depth(rows: tuple[PolymarketFeeAssumptionReportRow, ...]) -> Decimal | None:
    if not rows:
        return None
    return min(row.depth_usdc for row in rows)


def _maximum_refresh_age(
    rows: tuple[PolymarketFeeAssumptionReportRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.refresh_age_seconds for row in rows)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_rate_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return _quantize_rate(normalized)


def _require_optional_rate_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_rate_decimal(field_name, value)


def _require_nonnegative_money_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_money(_require_nonnegative_decimal(field_name, value))


def _require_positive_money_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_money(_require_positive_decimal(field_name, value))


def _require_optional_money_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_money_decimal(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_pass_watch_ceiling(
    pass_field_name: str,
    pass_limit: Decimal,
    watch_field_name: str,
    watch_limit: Decimal,
) -> None:
    if watch_limit < pass_limit:
        raise ValueError(f"{watch_field_name} must be at least {pass_field_name}")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize_rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_QUANTUM)


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use snake_case")
    if value.startswith("_") or value.endswith("_") or "__" in value:
        raise ValueError(f"{field_name} must use snake_case")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")
