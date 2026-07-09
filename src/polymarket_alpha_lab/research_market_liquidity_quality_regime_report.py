"""Pure manual research liquidity quality regime report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_QUALITY_REGIME_REPORT_CONFIG_VERSION",
    "LIQUIDITY_QUALITY_REGIME_STATUSES",
    "LIQUIDITY_QUALITY_REGIMES",
    "ResearchMarketLiquidityQualityRegimeConfig",
    "ResearchMarketLiquidityQualityRegimeInput",
    "ResearchMarketLiquidityQualityRegimeReasonCodeCount",
    "ResearchMarketLiquidityQualityRegimeReport",
    "ResearchMarketLiquidityQualityRegimeRow",
    "build_research_market_liquidity_quality_regime_report",
    "research_market_liquidity_quality_regime_report_digest",
    "research_market_liquidity_quality_regime_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_QUALITY_REGIME_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-quality-regime-report-v0"
)
LIQUIDITY_QUALITY_REGIME_STATUSES = ("pass", "watch", "block")
LIQUIDITY_QUALITY_REGIMES = (
    "high_quality_liquidity",
    "degraded_liquidity",
    "fragile_liquidity",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
COMPONENT_REASON_PRIORITY = (
    "spread_block",
    "depth_block",
    "depth_decay_block",
    "volatility_block",
    "book_age_block",
    "fee_drag_block",
    "settlement_friction_block",
    "spread_watch",
    "depth_watch",
    "depth_decay_watch",
    "volatility_watch",
    "book_age_watch",
    "fee_drag_watch",
    "settlement_friction_watch",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketLiquidityQualityRegimeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_QUALITY_REGIME_REPORT_CONFIG_VERSION
    )
    max_pass_spread_rate: Decimal = Decimal("0.015000")
    max_watch_spread_rate: Decimal = Decimal("0.040000")
    min_pass_depth_score: Decimal = Decimal("0.750000")
    min_watch_depth_score: Decimal = Decimal("0.500000")
    max_pass_depth_decay_rate: Decimal = Decimal("0.150000")
    max_watch_depth_decay_rate: Decimal = Decimal("0.350000")
    max_pass_volatility_rate: Decimal = Decimal("0.100000")
    max_watch_volatility_rate: Decimal = Decimal("0.250000")
    max_pass_book_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_book_age_seconds: Decimal = Decimal("21600.000000")
    max_pass_fee_drag_rate: Decimal = Decimal("0.010000")
    max_watch_fee_drag_rate: Decimal = Decimal("0.030000")
    max_pass_settlement_friction_rate: Decimal = Decimal("0.005000")
    max_watch_settlement_friction_rate: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityQualityRegimeConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_QUALITY_REGIME_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "max_pass_depth_decay_rate",
            "max_watch_depth_decay_rate",
            "max_pass_volatility_rate",
            "max_watch_volatility_rate",
            "max_pass_fee_drag_rate",
            "max_watch_fee_drag_rate",
            "max_pass_settlement_friction_rate",
            "max_watch_settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_pass_book_age_seconds", "max_watch_book_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_spread_rate > self.max_watch_spread_rate:
            raise ValueError("pass spread threshold must not exceed watch")
        if self.min_watch_depth_score > self.min_pass_depth_score:
            raise ValueError("watch depth threshold must not exceed pass")
        if self.max_pass_depth_decay_rate > self.max_watch_depth_decay_rate:
            raise ValueError("pass depth decay threshold must not exceed watch")
        if self.max_pass_volatility_rate > self.max_watch_volatility_rate:
            raise ValueError("pass volatility threshold must not exceed watch")
        if self.max_pass_book_age_seconds > self.max_watch_book_age_seconds:
            raise ValueError("pass book age threshold must not exceed watch")
        if self.max_pass_fee_drag_rate > self.max_watch_fee_drag_rate:
            raise ValueError("pass fee drag threshold must not exceed watch")
        if (
            self.max_pass_settlement_friction_rate
            > self.max_watch_settlement_friction_rate
        ):
            raise ValueError("pass settlement friction threshold must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityQualityRegimeInput:
    research_key: str
    spread_rate: Decimal
    depth_score: Decimal
    depth_decay_rate: Decimal
    volatility_rate: Decimal
    book_age_seconds: Decimal
    fee_drag_rate: Decimal
    settlement_friction_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityQualityRegimeInput, "input")
        _require_public_label("research_key", self.research_key)
        for field_name in (
            "spread_rate",
            "depth_score",
            "depth_decay_rate",
            "volatility_rate",
            "fee_drag_rate",
            "settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityQualityRegimeRow:
    research_key: str
    spread_rate: Decimal
    depth_score: Decimal
    depth_decay_rate: Decimal
    volatility_rate: Decimal
    book_age_seconds: Decimal
    book_age_risk: Decimal
    fee_drag_rate: Decimal
    settlement_friction_rate: Decimal
    liquidity_quality_score: Decimal
    liquidity_quality_regime: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityQualityRegimeRow, "row")
        _require_public_label("research_key", self.research_key)
        for field_name in (
            "spread_rate",
            "depth_score",
            "depth_decay_rate",
            "volatility_rate",
            "book_age_risk",
            "fee_drag_rate",
            "settlement_friction_rate",
            "liquidity_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_decimal("book_age_seconds", self.book_age_seconds),
        )
        _require_regime("liquidity_quality_regime", self.liquidity_quality_regime)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityQualityRegimeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
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
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityQualityRegimeReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_liquidity_quality_score: Decimal | None
    max_spread_rate: Decimal
    min_depth_score: Decimal
    max_depth_decay_rate: Decimal
    max_volatility_rate: Decimal
    max_book_age_risk: Decimal
    max_fee_drag_rate: Decimal
    max_settlement_friction_rate: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...]
    reason_code_counts: tuple[
        ResearchMarketLiquidityQualityRegimeReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityQualityRegimeReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_liquidity_quality_score",
            _require_optional_ratio_decimal(
                "average_liquidity_quality_score",
                self.average_liquidity_quality_score,
            ),
        )
        for field_name in (
            "max_spread_rate",
            "min_depth_score",
            "max_depth_decay_rate",
            "max_volatility_rate",
            "max_book_age_risk",
            "max_fee_drag_rate",
            "max_settlement_friction_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_liquidity_quality_regime_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketLiquidityQualityRegimeConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityQualityRegimeReport:
    if type(config) is not ResearchMarketLiquidityQualityRegimeConfig:
        raise ValueError("config must be a ResearchMarketLiquidityQualityRegimeConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketLiquidityQualityRegimeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_liquidity_quality_score=_average_quality_score(rows),
        max_spread_rate=_maximum_row_value(rows, "spread_rate"),
        min_depth_score=_minimum_row_value(rows, "depth_score"),
        max_depth_decay_rate=_maximum_row_value(rows, "depth_decay_rate"),
        max_volatility_rate=_maximum_row_value(rows, "volatility_rate"),
        max_book_age_risk=_maximum_row_value(rows, "book_age_risk"),
        max_fee_drag_rate=_maximum_row_value(rows, "fee_drag_rate"),
        max_settlement_friction_rate=_maximum_row_value(
            rows,
            "settlement_friction_rate",
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_quality_regime_report_payload(
    report: ResearchMarketLiquidityQualityRegimeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityQualityRegimeReport:
        raise ValueError("report must be a ResearchMarketLiquidityQualityRegimeReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_surface_values("payload", payload)
    return payload


def research_market_liquidity_quality_regime_report_digest(
    report: ResearchMarketLiquidityQualityRegimeReport,
) -> str:
    payload = research_market_liquidity_quality_regime_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchMarketLiquidityQualityRegimeInput,
    *,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> ResearchMarketLiquidityQualityRegimeRow:
    book_age_risk = _book_age_risk(item.book_age_seconds, config)
    quality_score = _liquidity_quality_score(
        spread_rate=item.spread_rate,
        depth_score=item.depth_score,
        depth_decay_rate=item.depth_decay_rate,
        volatility_rate=item.volatility_rate,
        book_age_risk=book_age_risk,
        fee_drag_rate=item.fee_drag_rate,
        settlement_friction_rate=item.settlement_friction_rate,
    )
    status = _row_status(item, config=config)
    return ResearchMarketLiquidityQualityRegimeRow(
        research_key=item.research_key,
        spread_rate=item.spread_rate,
        depth_score=item.depth_score,
        depth_decay_rate=item.depth_decay_rate,
        volatility_rate=item.volatility_rate,
        book_age_seconds=item.book_age_seconds,
        book_age_risk=book_age_risk,
        fee_drag_rate=item.fee_drag_rate,
        settlement_friction_rate=item.settlement_friction_rate,
        liquidity_quality_score=quality_score,
        liquidity_quality_regime=_regime_from_status(status),
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _book_age_risk(
    book_age_seconds: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        risk = book_age_seconds / config.max_watch_book_age_seconds
    if risk > ONE:
        return ONE
    return _quantize(risk)


def _liquidity_quality_score(
    *,
    spread_rate: Decimal,
    depth_score: Decimal,
    depth_decay_rate: Decimal,
    volatility_rate: Decimal,
    book_age_risk: Decimal,
    fee_drag_rate: Decimal,
    settlement_friction_rate: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = (
            (ONE - spread_rate)
            + depth_score
            + (ONE - depth_decay_rate)
            + (ONE - volatility_rate)
            + (ONE - book_age_risk)
            + (ONE - fee_drag_rate)
            + (ONE - settlement_friction_rate)
        ) / Decimal("7")
    return _quantize(score)


def _row_status(
    item: ResearchMarketLiquidityQualityRegimeInput,
    *,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if (
        item.spread_rate > config.max_watch_spread_rate
        or item.depth_score < config.min_watch_depth_score
        or item.depth_decay_rate > config.max_watch_depth_decay_rate
        or item.volatility_rate > config.max_watch_volatility_rate
        or item.book_age_seconds > config.max_watch_book_age_seconds
        or item.fee_drag_rate > config.max_watch_fee_drag_rate
        or item.settlement_friction_rate > config.max_watch_settlement_friction_rate
    ):
        return "block"
    if (
        item.spread_rate > config.max_pass_spread_rate
        or item.depth_score < config.min_pass_depth_score
        or item.depth_decay_rate > config.max_pass_depth_decay_rate
        or item.volatility_rate > config.max_pass_volatility_rate
        or item.book_age_seconds > config.max_pass_book_age_seconds
        or item.fee_drag_rate > config.max_pass_fee_drag_rate
        or item.settlement_friction_rate > config.max_pass_settlement_friction_rate
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketLiquidityQualityRegimeInput,
    *,
    status: str,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> tuple[str, ...]:
    codes = {
        f"market_liquidity_quality_regime_{status}",
        f"manual_research_liquidity_quality_{status}",
        f"spread_{_spread_status(item.spread_rate, config)}",
        f"depth_{_depth_status(item.depth_score, config)}",
        f"depth_decay_{_depth_decay_status(item.depth_decay_rate, config)}",
        f"volatility_{_volatility_status(item.volatility_rate, config)}",
        f"book_age_{_book_age_status(item.book_age_seconds, config)}",
        f"fee_drag_{_fee_drag_status(item.fee_drag_rate, config)}",
        (
            "settlement_friction_"
            f"{_settlement_status(item.settlement_friction_rate, config)}"
        ),
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _spread_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value > config.max_watch_spread_rate:
        return "block"
    if value > config.max_pass_spread_rate:
        return "watch"
    return "pass"


def _depth_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value < config.min_watch_depth_score:
        return "block"
    if value < config.min_pass_depth_score:
        return "watch"
    return "pass"


def _depth_decay_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value > config.max_watch_depth_decay_rate:
        return "block"
    if value > config.max_pass_depth_decay_rate:
        return "watch"
    return "pass"


def _volatility_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value > config.max_watch_volatility_rate:
        return "block"
    if value > config.max_pass_volatility_rate:
        return "watch"
    return "pass"


def _book_age_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value > config.max_watch_book_age_seconds:
        return "block"
    if value > config.max_pass_book_age_seconds:
        return "watch"
    return "pass"


def _fee_drag_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value > config.max_watch_fee_drag_rate:
        return "block"
    if value > config.max_pass_fee_drag_rate:
        return "watch"
    return "pass"


def _settlement_status(
    value: Decimal,
    config: ResearchMarketLiquidityQualityRegimeConfig,
) -> str:
    if value > config.max_watch_settlement_friction_rate:
        return "block"
    if value > config.max_pass_settlement_friction_rate:
        return "watch"
    return "pass"


def _regime_from_status(status: str) -> str:
    if status == "block":
        return "fragile_liquidity"
    if status == "watch":
        return "degraded_liquidity"
    return "high_quality_liquidity"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketLiquidityQualityRegimeInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketLiquidityQualityRegimeInput:
    if type(value) is ResearchMarketLiquidityQualityRegimeInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketLiquidityQualityRegimeInput(
        research_key=_field_value(value, "research_key"),
        spread_rate=_field_value(value, "spread_rate"),
        depth_score=_field_value(value, "depth_score"),
        depth_decay_rate=_field_value(value, "depth_decay_rate"),
        volatility_rate=_field_value(value, "volatility_rate"),
        book_age_seconds=_field_value(value, "book_age_seconds"),
        fee_drag_rate=_field_value(value, "fee_drag_rate"),
        settlement_friction_rate=_field_value(value, "settlement_friction_rate"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_quality_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("market_liquidity_quality_regime_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("market_liquidity_quality_regime_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("market_liquidity_quality_regime_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_liquidity_quality_inputs",):
        return "block"
    if "market_liquidity_quality_regime_block" in reason_codes:
        return "block"
    if "market_liquidity_quality_regime_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketLiquidityQualityRegimeReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityQualityRegimeReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchMarketLiquidityQualityRegimeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_quality_score(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.liquidity_quality_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _minimum_row_value(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityQualityRegimeRow, ...],
) -> tuple[ResearchMarketLiquidityQualityRegimeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityQualityRegimeRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityQualityRegimeRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketLiquidityQualityRegimeReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityQualityRegimeReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketLiquidityQualityRegimeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityQualityRegimeReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchMarketLiquidityQualityRegimeRow) -> None:
    expected_score = _liquidity_quality_score(
        spread_rate=row.spread_rate,
        depth_score=row.depth_score,
        depth_decay_rate=row.depth_decay_rate,
        volatility_rate=row.volatility_rate,
        book_age_risk=row.book_age_risk,
        fee_drag_rate=row.fee_drag_rate,
        settlement_friction_rate=row.settlement_friction_rate,
    )
    if row.liquidity_quality_score != expected_score:
        raise ValueError("liquidity_quality_score must match components")
    if row.liquidity_quality_regime != _regime_from_status(row.status):
        raise ValueError("liquidity_quality_regime must match status")
    expected_status_code = f"market_liquidity_quality_regime_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(
        code.endswith(("_watch", "_block")) for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")
    if row.status == "watch" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("status must match component reason_codes")


def _validate_report_consistency(
    report: ResearchMarketLiquidityQualityRegimeReport,
) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_liquidity_quality_score != _average_quality_score(report.rows):
        raise ValueError("average_liquidity_quality_score must match rows")
    if report.max_spread_rate != _maximum_row_value(report.rows, "spread_rate"):
        raise ValueError("max_spread_rate must match rows")
    if report.min_depth_score != _minimum_row_value(report.rows, "depth_score"):
        raise ValueError("min_depth_score must match rows")
    if report.max_depth_decay_rate != _maximum_row_value(
        report.rows,
        "depth_decay_rate",
    ):
        raise ValueError("max_depth_decay_rate must match rows")
    if report.max_volatility_rate != _maximum_row_value(report.rows, "volatility_rate"):
        raise ValueError("max_volatility_rate must match rows")
    if report.max_book_age_risk != _maximum_row_value(report.rows, "book_age_risk"):
        raise ValueError("max_book_age_risk must match rows")
    if report.max_fee_drag_rate != _maximum_row_value(report.rows, "fee_drag_rate"):
        raise ValueError("max_fee_drag_rate must match rows")
    if report.max_settlement_friction_rate != _maximum_row_value(
        report.rows,
        "settlement_friction_rate",
    ):
        raise ValueError("max_settlement_friction_rate must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
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
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if type(value) is bool or value is None or type(value) is str:
        return value
    if isinstance(value, (int, float)):
        raise ValueError("payload numerics must be Decimal-derived strings")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(RATIO_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LIQUIDITY_QUALITY_REGIME_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_regime(field_name: str, value: object) -> None:
    if type(value) is not str or value not in LIQUIDITY_QUALITY_REGIMES:
        raise ValueError(f"{field_name} must be a supported liquidity quality regime")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        reason_code = _require_reason_code(field_name, value)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not value or value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must contain normalized reason codes")
    if not all(character.isalnum() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain normalized reason codes")
    _reject_public_surface_values(field_name, value)
    return value


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must be a normalized public label")
    if not all(character.isalnum() or character in {"-", "_"} for character in value):
        raise ValueError(f"{field_name} must be a normalized public label")
    _reject_public_surface_values(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_public_surface_values(label: str, value: object) -> None:
    if type(value) is str:
        if _has_public_surface_fragment(value):
            raise ValueError(f"unsafe public surface value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"JSON object keys must be strings in {label}")
            _reject_public_surface_values(label, key)
            _reject_public_surface_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_surface_values(label, item)


def _has_public_surface_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _public_surface_fragments())


def _public_surface_fragments() -> tuple[str, ...]:
    return (
        "candi" + "date" + "_id",
        "candi" + "date" + "-",
        "market" + "_id",
        "market" + "_sl" + "ug",
        "condition" + "_id",
        "to" + "ken",
        "sl" + "ug",
        "ques" + "tion",
        "ur" + "l",
        "http" + "://",
        "https" + "://",
        "d" + "sn",
        "ta" + "ble",
        "wal" + "let",
        "or" + "der",
        "tra" + "de",
        "li" + "ve",
        "source" + "_text",
        "raw" + "_text",
    )
