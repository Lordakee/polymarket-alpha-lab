"""Pure liquidity cost sensitivity report for caller-supplied research inputs.

The module is deterministic and side-effect free. Callers provide typed scenario
rows; the policy returns report-only friction scores, statuses, and reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "LiquidityCostSensitivityConfig",
    "LiquidityCostSensitivityReasonCodeCount",
    "LiquidityCostSensitivityReport",
    "LiquidityCostSensitivityRow",
    "LiquidityCostSensitivityScenario",
    "build_research_liquidity_cost_sensitivity_report",
    "research_liquidity_cost_sensitivity_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-liquidity-cost-sensitivity-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_RESEARCH_NOTE = (
    "Research-only liquidity cost sensitivity report; no execution instruction, "
    "exposure sizing, or market direction is provided."
)
_PUBLIC_TEXT_DENYLIST = ("buy", "sell", "position", "recommend")
_PUBLIC_PAYLOAD_IDENTITY_FIELD_DENYLIST = frozenset(
    ("scenario_id", "market_slug", "outcome_name"),
)
_REPORT_PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "scenario_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_total_cost_rate",
    "max_total_cost_rate",
    "status",
    "reason_codes",
    "research_note",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PUBLIC_PAYLOAD_FIELDS = (
    "bid_ask_spread_rate",
    "available_depth",
    "research_notional",
    "taker_fee_rate",
    "settlement_friction_rate",
    "depth_coverage_ratio",
    "depth_shortfall",
    "depth_shortfall_ratio",
    "explicit_cost_rate",
    "depth_shortfall_cost_rate",
    "total_cost_rate",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_CODE_COUNT_PUBLIC_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class LiquidityCostSensitivityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_max_total_cost_rate: Decimal = Decimal("0.030000")
    watch_max_total_cost_rate: Decimal = Decimal("0.060000")
    pass_min_depth_coverage_ratio: Decimal = Decimal("1.000000")
    watch_min_depth_coverage_ratio: Decimal = Decimal("0.500000")
    depth_shortfall_cost_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_max_total_cost_rate",
            "watch_max_total_cost_rate",
            "depth_shortfall_cost_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_min_depth_coverage_ratio",
            "watch_min_depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_max_total_cost_rate >= self.watch_max_total_cost_rate:
            raise ValueError(
                "watch_max_total_cost_rate must be greater than pass_max_total_cost_rate",
            )
        if self.watch_min_depth_coverage_ratio > self.pass_min_depth_coverage_ratio:
            raise ValueError(
                "watch depth coverage threshold must not exceed pass depth coverage threshold",
            )
        if self.pass_min_depth_coverage_ratio > ONE:
            raise ValueError("pass depth coverage threshold must not exceed 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class LiquidityCostSensitivityScenario:
    scenario_id: str
    market_slug: str
    outcome_name: str
    bid_ask_spread_rate: Decimal
    available_depth: Decimal
    research_notional: Decimal
    taker_fee_rate: Decimal
    settlement_friction_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("scenario_id", "market_slug", "outcome_name"):
            _require_safe_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "bid_ask_spread_rate",
            "taker_fee_rate",
            "settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        object.__setattr__(
            self,
            "research_notional",
            _require_positive_decimal("research_notional", self.research_notional),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("scenario", self)


@dataclass(frozen=True)
class LiquidityCostSensitivityRow:
    scenario_id: str
    market_slug: str
    outcome_name: str
    bid_ask_spread_rate: Decimal
    available_depth: Decimal
    research_notional: Decimal
    taker_fee_rate: Decimal
    settlement_friction_rate: Decimal
    depth_coverage_ratio: Decimal
    depth_shortfall: Decimal
    depth_shortfall_ratio: Decimal
    explicit_cost_rate: Decimal
    depth_shortfall_cost_rate: Decimal
    total_cost_rate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("scenario_id", "market_slug", "outcome_name"):
            _require_safe_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "bid_ask_spread_rate",
            "taker_fee_rate",
            "settlement_friction_rate",
            "depth_coverage_ratio",
            "depth_shortfall_ratio",
            "explicit_cost_rate",
            "depth_shortfall_cost_rate",
            "total_cost_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        object.__setattr__(
            self,
            "research_notional",
            _require_positive_decimal("research_notional", self.research_notional),
        )
        object.__setattr__(
            self,
            "depth_shortfall",
            _require_nonnegative_decimal("depth_shortfall", self.depth_shortfall),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class LiquidityCostSensitivityReasonCodeCount:
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
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class LiquidityCostSensitivityReport:
    generated_at: datetime
    config_version: str
    scenario_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_total_cost_rate: Decimal | None
    max_total_cost_rate: Decimal | None
    status: str
    rows: tuple[LiquidityCostSensitivityRow, ...]
    reason_code_counts: tuple[LiquidityCostSensitivityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    research_note: str = DEFAULT_RESEARCH_NOTE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("scenario_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_total_cost_rate", "max_total_cost_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
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
        _require_safe_public_note("research_note", self.research_note)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_liquidity_cost_sensitivity_report(
    scenarios: Iterable[object],
    *,
    config: LiquidityCostSensitivityConfig,
    generated_at: datetime,
) -> LiquidityCostSensitivityReport:
    if type(config) is not LiquidityCostSensitivityConfig:
        raise ValueError("config must be a LiquidityCostSensitivityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    scenario_items = _normalize_scenarios(scenarios)
    rows = tuple(_row_from_scenario(item, config=config) for item in scenario_items)
    reason_codes = _summary_reason_codes(rows)

    return LiquidityCostSensitivityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        scenario_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_total_cost_rate=_average_total_cost_rate(rows),
        max_total_cost_rate=_max_total_cost_rate(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_liquidity_cost_sensitivity_report_payload(
    report: LiquidityCostSensitivityReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is LiquidityCostSensitivityReport:
        _require_hard_flags("report", report)
        payload = _public_report_payload(report)
    elif isinstance(report, Mapping):
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a LiquidityCostSensitivityReport or payload mapping")
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def _public_report_payload(report: LiquidityCostSensitivityReport) -> dict[str, Any]:
    payload = {
        field_name: _payload_value(getattr(report, field_name))
        for field_name in _REPORT_PUBLIC_PAYLOAD_FIELDS
    }
    payload["rows"] = [
        _public_dataclass_payload(row, _ROW_PUBLIC_PAYLOAD_FIELDS)
        for row in report.rows
    ]
    payload["reason_code_counts"] = [
        _public_dataclass_payload(count, _REASON_CODE_COUNT_PUBLIC_PAYLOAD_FIELDS)
        for count in report.reason_code_counts
    ]
    return payload


def _public_dataclass_payload(
    value: object,
    field_names: tuple[str, ...],
) -> dict[str, Any]:
    return {
        field_name: _payload_value(getattr(value, field_name))
        for field_name in field_names
    }


def _row_from_scenario(
    scenario: LiquidityCostSensitivityScenario,
    *,
    config: LiquidityCostSensitivityConfig,
) -> LiquidityCostSensitivityRow:
    depth_coverage_ratio = _quantize(min(ONE, scenario.available_depth / scenario.research_notional))
    depth_shortfall = max(ZERO, scenario.research_notional - scenario.available_depth)
    depth_shortfall_ratio = _quantize(depth_shortfall / scenario.research_notional)
    explicit_cost_rate = _quantize(
        scenario.bid_ask_spread_rate
        + scenario.taker_fee_rate
        + scenario.settlement_friction_rate,
    )
    depth_shortfall_cost_rate = _quantize(
        depth_shortfall_ratio * config.depth_shortfall_cost_weight,
    )
    total_cost_rate = _quantize(explicit_cost_rate + depth_shortfall_cost_rate)
    status = _row_status(
        total_cost_rate=total_cost_rate,
        depth_coverage_ratio=depth_coverage_ratio,
        config=config,
    )
    return LiquidityCostSensitivityRow(
        scenario_id=scenario.scenario_id,
        market_slug=scenario.market_slug,
        outcome_name=scenario.outcome_name,
        bid_ask_spread_rate=scenario.bid_ask_spread_rate,
        available_depth=scenario.available_depth,
        research_notional=scenario.research_notional,
        taker_fee_rate=scenario.taker_fee_rate,
        settlement_friction_rate=scenario.settlement_friction_rate,
        depth_coverage_ratio=depth_coverage_ratio,
        depth_shortfall=depth_shortfall,
        depth_shortfall_ratio=depth_shortfall_ratio,
        explicit_cost_rate=explicit_cost_rate,
        depth_shortfall_cost_rate=depth_shortfall_cost_rate,
        total_cost_rate=total_cost_rate,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            total_cost_rate=total_cost_rate,
            depth_coverage_ratio=depth_coverage_ratio,
            scenario=scenario,
            config=config,
        ),
    )


def _normalize_scenarios(
    scenarios: Iterable[object],
) -> tuple[LiquidityCostSensitivityScenario, ...]:
    if isinstance(scenarios, (str, bytes)):
        raise ValueError("scenarios must be an iterable")
    try:
        values = tuple(scenarios)
    except TypeError as exc:
        raise ValueError("scenarios must be an iterable") from exc
    normalized = tuple(_coerce_scenario(value) for value in values)
    return tuple(sorted(normalized, key=lambda item: item.scenario_id))


def _coerce_scenario(value: object) -> LiquidityCostSensitivityScenario:
    if type(value) is LiquidityCostSensitivityScenario:
        _require_hard_flags("scenario", value)
        return value
    _require_hard_flags("scenario", value)
    return LiquidityCostSensitivityScenario(
        scenario_id=_field_value(value, "scenario_id"),
        market_slug=_field_value(value, "market_slug"),
        outcome_name=_field_value(value, "outcome_name"),
        bid_ask_spread_rate=_field_value(value, "bid_ask_spread_rate"),
        available_depth=_field_value(value, "available_depth"),
        research_notional=_field_value(value, "research_notional"),
        taker_fee_rate=_field_value(value, "taker_fee_rate"),
        settlement_friction_rate=_field_value(value, "settlement_friction_rate"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_status(
    *,
    total_cost_rate: Decimal,
    depth_coverage_ratio: Decimal,
    config: LiquidityCostSensitivityConfig,
) -> str:
    if (
        total_cost_rate > config.watch_max_total_cost_rate
        or depth_coverage_ratio < config.watch_min_depth_coverage_ratio
    ):
        return "block"
    if (
        total_cost_rate > config.pass_max_total_cost_rate
        or depth_coverage_ratio < config.pass_min_depth_coverage_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    total_cost_rate: Decimal,
    depth_coverage_ratio: Decimal,
    scenario: LiquidityCostSensitivityScenario,
    config: LiquidityCostSensitivityConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if depth_coverage_ratio < config.watch_min_depth_coverage_ratio:
        codes.append("insufficient_depth")
    elif depth_coverage_ratio < config.pass_min_depth_coverage_ratio:
        codes.append("limited_depth")
    else:
        codes.append("adequate_depth")

    codes.append(f"liquidity_cost_{status}")

    if total_cost_rate > config.watch_max_total_cost_rate:
        codes.append("excessive_cost_friction")
    elif total_cost_rate > config.pass_max_total_cost_rate:
        codes.append("elevated_cost_friction")
    else:
        codes.append("low_cost_friction")

    if scenario.bid_ask_spread_rate > ZERO:
        codes.append("spread_cost_present")
    if scenario.taker_fee_rate > ZERO:
        codes.append("taker_fee_present")
    if scenario.settlement_friction_rate > ZERO:
        codes.append("settlement_friction_present")
    for reason_code in scenario.reason_codes:
        codes.append(f"input_{reason_code}")
    return tuple(dict.fromkeys(codes))


def _summary_reason_codes(
    rows: tuple[LiquidityCostSensitivityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_cost_scenarios",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("liquidity_cost_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_liquidity_cost_scenarios",):
        return "block"
    if "liquidity_cost_block" in reason_codes:
        return "block"
    if "liquidity_cost_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[LiquidityCostSensitivityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[LiquidityCostSensitivityReasonCodeCount, ...]:
    if not rows:
        return (
            LiquidityCostSensitivityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        LiquidityCostSensitivityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_total_cost_rate(
    rows: tuple[LiquidityCostSensitivityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.total_cost_rate for row in rows), ZERO) / Decimal(len(rows)))


def _max_total_cost_rate(
    rows: tuple[LiquidityCostSensitivityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.total_cost_rate for row in rows)


def _status_count(rows: tuple[LiquidityCostSensitivityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[LiquidityCostSensitivityRow, ...],
) -> tuple[LiquidityCostSensitivityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not LiquidityCostSensitivityRow:
            raise ValueError("rows must contain LiquidityCostSensitivityRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.scenario_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by scenario_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[LiquidityCostSensitivityReasonCodeCount, ...],
) -> tuple[LiquidityCostSensitivityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not LiquidityCostSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain LiquidityCostSensitivityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: LiquidityCostSensitivityRow) -> None:
    if row.available_depth + row.depth_shortfall != row.research_notional:
        if not (
            row.available_depth > row.research_notional
            and row.depth_shortfall == ZERO
        ):
            raise ValueError("depth_shortfall must match available_depth and research_notional")
    expected_depth_coverage_ratio = _quantize(min(ONE, row.available_depth / row.research_notional))
    expected_depth_shortfall_ratio = _quantize(row.depth_shortfall / row.research_notional)
    expected_explicit_cost_rate = _quantize(
        row.bid_ask_spread_rate + row.taker_fee_rate + row.settlement_friction_rate,
    )
    expected_total_cost_rate = _quantize(
        row.explicit_cost_rate + row.depth_shortfall_cost_rate,
    )
    if row.depth_coverage_ratio != expected_depth_coverage_ratio:
        raise ValueError("depth_coverage_ratio must match scenario values")
    if row.depth_shortfall_ratio != expected_depth_shortfall_ratio:
        raise ValueError("depth_shortfall_ratio must match depth_shortfall")
    if row.explicit_cost_rate != expected_explicit_cost_rate:
        raise ValueError("explicit_cost_rate must match spread, fee, and settlement friction")
    if row.total_cost_rate != expected_total_cost_rate:
        raise ValueError("total_cost_rate must match cost components")
    if f"liquidity_cost_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include status code")


def _validate_report_consistency(report: LiquidityCostSensitivityReport) -> None:
    if report.scenario_count != _decimal_count(len(report.rows)):
        raise ValueError("scenario_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_total_cost_rate != _average_total_cost_rate(report.rows):
        raise ValueError("average_total_cost_rate must match rows")
    if report.max_total_cost_rate != _max_total_cost_rate(report.rows):
        raise ValueError("max_total_cost_rate must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


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


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, str):
        _reject_public_text(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text in _PUBLIC_PAYLOAD_IDENTITY_FIELD_DENYLIST:
                raise ValueError(f"public payload must not include {key_text}")
            _reject_public_text(key_text)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)


def _as_utc(field_name: str, value: datetime) -> datetime:
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


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


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


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_safe_canonical_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_directional_or_guidance_term(value):
        raise ValueError(f"{field_name} contains a directional or guidance term")


def _require_safe_public_note(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_public_text(value)
    if not value.startswith("Research-only"):
        raise ValueError(f"{field_name} must be a research-only note")


def _reject_public_text(value: str) -> None:
    if _contains_directional_or_guidance_term(value):
        raise ValueError("public text contains a directional or guidance term")


def _contains_directional_or_guidance_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _PUBLIC_TEXT_DENYLIST)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


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
        _reject_public_text(value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(dict.fromkeys(normalized))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain lowercase snake_case reason codes")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")
