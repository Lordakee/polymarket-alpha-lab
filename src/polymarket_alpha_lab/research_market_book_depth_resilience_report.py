"""Pure aggregate book depth resilience report for manual research."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
import re
from typing import Any


__all__ = (
    "BOOK_DEPTH_RESILIENCE_STATUSES",
    "DEFAULT_RESEARCH_MARKET_BOOK_DEPTH_RESILIENCE_REPORT_CONFIG_VERSION",
    "ResearchMarketBookDepthResilienceConfig",
    "ResearchMarketBookDepthResilienceInput",
    "ResearchMarketBookDepthResilienceReasonCodeCount",
    "ResearchMarketBookDepthResilienceReport",
    "ResearchMarketBookDepthResilienceRow",
    "build_research_market_book_depth_resilience_report",
    "research_market_book_depth_resilience_report_digest",
    "research_market_book_depth_resilience_report_payload",
)


DEFAULT_RESEARCH_MARKET_BOOK_DEPTH_RESILIENCE_REPORT_CONFIG_VERSION = (
    "research-market-book-depth-resilience-report-v0"
)
BOOK_DEPTH_RESILIENCE_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
COMPONENT_REASON_PRIORITY = (
    "depth_balance_block",
    "spread_stress_block",
    "freshness_age_block",
    "fee_friction_block",
    "manual_recheck_urgency_block",
    "depth_balance_watch",
    "spread_stress_watch",
    "freshness_age_watch",
    "fee_friction_watch",
    "manual_recheck_urgency_watch",
)


@dataclass(frozen=True)
class ResearchMarketBookDepthResilienceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_BOOK_DEPTH_RESILIENCE_REPORT_CONFIG_VERSION
    )
    min_pass_depth_balance: Decimal = Decimal("0.700000")
    min_watch_depth_balance: Decimal = Decimal("0.400000")
    max_pass_spread_stress: Decimal = Decimal("0.030000")
    max_watch_spread_stress: Decimal = Decimal("0.080000")
    max_pass_freshness_age_seconds: Decimal = Decimal("120.000000")
    max_watch_freshness_age_seconds: Decimal = Decimal("600.000000")
    max_pass_fee_rate: Decimal = Decimal("0.020000")
    max_watch_fee_rate: Decimal = Decimal("0.050000")
    max_pass_manual_recheck_urgency: Decimal = Decimal("0.300000")
    max_watch_manual_recheck_urgency: Decimal = Decimal("0.700000")
    depth_balance_weight: Decimal = Decimal("0.300000")
    spread_resilience_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    fee_friction_weight: Decimal = Decimal("0.150000")
    manual_recheck_weight: Decimal = Decimal("0.100000")
    pass_resilience_score: Decimal = Decimal("0.700000")
    watch_resilience_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookDepthResilienceConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_BOOK_DEPTH_RESILIENCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "min_pass_depth_balance",
            "min_watch_depth_balance",
            "max_pass_spread_stress",
            "max_watch_spread_stress",
            "max_pass_fee_rate",
            "max_watch_fee_rate",
            "max_pass_manual_recheck_urgency",
            "max_watch_manual_recheck_urgency",
            "depth_balance_weight",
            "spread_resilience_weight",
            "freshness_weight",
            "fee_friction_weight",
            "manual_recheck_weight",
            "pass_resilience_score",
            "watch_resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_freshness_age_seconds",
            "max_watch_freshness_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_depth_balance < self.min_watch_depth_balance:
            raise ValueError("min_pass_depth_balance must be at least watch")
        if self.max_pass_spread_stress > self.max_watch_spread_stress:
            raise ValueError("max_pass_spread_stress must not exceed watch")
        if self.max_pass_freshness_age_seconds > self.max_watch_freshness_age_seconds:
            raise ValueError("max_pass_freshness_age_seconds must not exceed watch")
        if self.max_pass_fee_rate > self.max_watch_fee_rate:
            raise ValueError("max_pass_fee_rate must not exceed watch")
        if self.max_pass_manual_recheck_urgency > self.max_watch_manual_recheck_urgency:
            raise ValueError("max_pass_manual_recheck_urgency must not exceed watch")
        if self.pass_resilience_score < self.watch_resilience_score:
            raise ValueError("pass_resilience_score must be at least watch")
        weight_sum = _quantize(
            self.depth_balance_weight
            + self.spread_resilience_weight
            + self.freshness_weight
            + self.fee_friction_weight
            + self.manual_recheck_weight,
        )
        if weight_sum != ONE:
            raise ValueError("resilience weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketBookDepthResilienceInput:
    research_key: str
    observed_at: datetime
    bid_depth: Decimal
    ask_depth: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    fee_rate: Decimal
    manual_recheck_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookDepthResilienceInput, "input")
        _require_public_label("research_key", self.research_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("bid_depth", "ask_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "fee_rate",
            "manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketBookDepthResilienceRow:
    research_key: str
    observed_at: datetime
    freshness_age_seconds: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    depth_balance_score: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    spread_stress: Decimal
    spread_resilience_score: Decimal
    fee_rate: Decimal
    fee_friction_score: Decimal
    manual_recheck_urgency: Decimal
    freshness_score: Decimal
    manual_recheck_score: Decimal
    resilience_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookDepthResilienceRow, "row")
        _require_public_label("research_key", self.research_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "freshness_age_seconds",
            "bid_depth",
            "ask_depth",
            "spread_stress",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_balance_score",
            "best_bid_price",
            "best_ask_price",
            "spread_resilience_score",
            "fee_rate",
            "fee_friction_score",
            "manual_recheck_urgency",
            "freshness_score",
            "manual_recheck_score",
            "resilience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketBookDepthResilienceReasonCodeCount:
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
class ResearchMarketBookDepthResilienceReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_resilience_score: Decimal | None
    min_depth_balance_score: Decimal
    max_spread_stress: Decimal
    max_freshness_age_seconds: Decimal
    max_fee_rate: Decimal
    max_manual_recheck_urgency: Decimal
    status: str
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...]
    reason_code_counts: tuple[ResearchMarketBookDepthResilienceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookDepthResilienceReport, "report")
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
            "average_resilience_score",
            _require_optional_ratio_decimal(
                "average_resilience_score",
                self.average_resilience_score,
            ),
        )
        for field_name in (
            "min_depth_balance_score",
            "max_spread_stress",
            "max_fee_rate",
            "max_manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_freshness_age_seconds",
            _require_nonnegative_decimal(
                "max_freshness_age_seconds",
                self.max_freshness_age_seconds,
            ),
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
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_book_depth_resilience_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketBookDepthResilienceConfig,
    generated_at: datetime,
) -> ResearchMarketBookDepthResilienceReport:
    if type(config) is not ResearchMarketBookDepthResilienceConfig:
        raise ValueError("config must be a ResearchMarketBookDepthResilienceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_from_input(item, config=config, generated_at=generated_at_utc)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketBookDepthResilienceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_resilience_score=_average_resilience_score(rows),
        min_depth_balance_score=_minimum_row_value(rows, "depth_balance_score"),
        max_spread_stress=_maximum_row_value(rows, "spread_stress"),
        max_freshness_age_seconds=_maximum_row_value(rows, "freshness_age_seconds"),
        max_fee_rate=_maximum_row_value(rows, "fee_rate"),
        max_manual_recheck_urgency=_maximum_row_value(rows, "manual_recheck_urgency"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_book_depth_resilience_report_payload(
    report: ResearchMarketBookDepthResilienceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketBookDepthResilienceReport:
        raise ValueError("report must be a ResearchMarketBookDepthResilienceReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def research_market_book_depth_resilience_report_digest(
    report: ResearchMarketBookDepthResilienceReport,
) -> str:
    if type(report) is not ResearchMarketBookDepthResilienceReport:
        raise ValueError("report must be a ResearchMarketBookDepthResilienceReport")
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_input(
    item: ResearchMarketBookDepthResilienceInput,
    *,
    config: ResearchMarketBookDepthResilienceConfig,
    generated_at: datetime,
) -> ResearchMarketBookDepthResilienceRow:
    freshness_age_seconds = _age_seconds(generated_at, item.observed_at)
    spread_stress = _quantize(item.best_ask_price - item.best_bid_price)
    depth_balance_score = _depth_balance_score(item.bid_depth, item.ask_depth)
    spread_resilience_score = _inverse_ratio_score(
        spread_stress,
        config.max_watch_spread_stress,
    )
    freshness_score = _inverse_ratio_score(
        freshness_age_seconds,
        config.max_watch_freshness_age_seconds,
    )
    fee_friction_score = _inverse_ratio_score(item.fee_rate, config.max_watch_fee_rate)
    manual_recheck_score = _quantize(ONE - item.manual_recheck_urgency)
    resilience_score = _resilience_score(
        depth_balance_score=depth_balance_score,
        spread_resilience_score=spread_resilience_score,
        freshness_score=freshness_score,
        fee_friction_score=fee_friction_score,
        manual_recheck_score=manual_recheck_score,
        config=config,
    )
    status = _row_status(
        depth_balance_score=depth_balance_score,
        spread_stress=spread_stress,
        freshness_age_seconds=freshness_age_seconds,
        fee_rate=item.fee_rate,
        manual_recheck_urgency=item.manual_recheck_urgency,
        resilience_score=resilience_score,
        config=config,
    )
    return ResearchMarketBookDepthResilienceRow(
        research_key=item.research_key,
        observed_at=item.observed_at,
        freshness_age_seconds=freshness_age_seconds,
        bid_depth=item.bid_depth,
        ask_depth=item.ask_depth,
        depth_balance_score=depth_balance_score,
        best_bid_price=item.best_bid_price,
        best_ask_price=item.best_ask_price,
        spread_stress=spread_stress,
        spread_resilience_score=spread_resilience_score,
        fee_rate=item.fee_rate,
        fee_friction_score=fee_friction_score,
        manual_recheck_urgency=item.manual_recheck_urgency,
        freshness_score=freshness_score,
        manual_recheck_score=manual_recheck_score,
        resilience_score=resilience_score,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            depth_balance_score=depth_balance_score,
            spread_stress=spread_stress,
            freshness_age_seconds=freshness_age_seconds,
            status=status,
            config=config,
        ),
    )


def _depth_balance_score(bid_depth: Decimal, ask_depth: Decimal) -> Decimal:
    larger_depth = max(bid_depth, ask_depth)
    if larger_depth <= ZERO:
        return ZERO
    return _quantize(min(bid_depth, ask_depth) / larger_depth)


def _inverse_ratio_score(value: Decimal, zero_at: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = ONE - (value / zero_at)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _resilience_score(
    *,
    depth_balance_score: Decimal,
    spread_resilience_score: Decimal,
    freshness_score: Decimal,
    fee_friction_score: Decimal,
    manual_recheck_score: Decimal,
    config: ResearchMarketBookDepthResilienceConfig,
) -> Decimal:
    return _quantize(
        depth_balance_score * config.depth_balance_weight
        + spread_resilience_score * config.spread_resilience_weight
        + freshness_score * config.freshness_weight
        + fee_friction_score * config.fee_friction_weight
        + manual_recheck_score * config.manual_recheck_weight,
    )


def _row_status(
    *,
    depth_balance_score: Decimal,
    spread_stress: Decimal,
    freshness_age_seconds: Decimal,
    fee_rate: Decimal,
    manual_recheck_urgency: Decimal,
    resilience_score: Decimal,
    config: ResearchMarketBookDepthResilienceConfig,
) -> str:
    if (
        depth_balance_score < config.min_watch_depth_balance
        or spread_stress > config.max_watch_spread_stress
        or freshness_age_seconds > config.max_watch_freshness_age_seconds
        or fee_rate > config.max_watch_fee_rate
        or manual_recheck_urgency > config.max_watch_manual_recheck_urgency
        or resilience_score < config.watch_resilience_score
    ):
        return "block"
    if (
        depth_balance_score < config.min_pass_depth_balance
        or spread_stress > config.max_pass_spread_stress
        or freshness_age_seconds > config.max_pass_freshness_age_seconds
        or fee_rate > config.max_pass_fee_rate
        or manual_recheck_urgency > config.max_pass_manual_recheck_urgency
        or resilience_score < config.pass_resilience_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketBookDepthResilienceInput,
    *,
    depth_balance_score: Decimal,
    spread_stress: Decimal,
    freshness_age_seconds: Decimal,
    status: str,
    config: ResearchMarketBookDepthResilienceConfig,
) -> tuple[str, ...]:
    codes = {
        f"market_book_depth_resilience_{status}",
        _low_value_component_reason(
            prefix="depth_balance",
            value=depth_balance_score,
            pass_threshold=config.min_pass_depth_balance,
            block_threshold=config.min_watch_depth_balance,
        ),
        _high_value_component_reason(
            prefix="spread_stress",
            value=spread_stress,
            pass_threshold=config.max_pass_spread_stress,
            block_threshold=config.max_watch_spread_stress,
        ),
        _high_value_component_reason(
            prefix="freshness_age",
            value=freshness_age_seconds,
            pass_threshold=config.max_pass_freshness_age_seconds,
            block_threshold=config.max_watch_freshness_age_seconds,
        ),
        _high_value_component_reason(
            prefix="fee_friction",
            value=item.fee_rate,
            pass_threshold=config.max_pass_fee_rate,
            block_threshold=config.max_watch_fee_rate,
        ),
        _high_value_component_reason(
            prefix="manual_recheck_urgency",
            value=item.manual_recheck_urgency,
            pass_threshold=config.max_pass_manual_recheck_urgency,
            block_threshold=config.max_watch_manual_recheck_urgency,
        ),
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _low_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _high_value_component_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value > block_threshold:
        return f"{prefix}_block"
    if value > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketBookDepthResilienceInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchMarketBookDepthResilienceInput:
            raise ValueError(
                "inputs must contain ResearchMarketBookDepthResilienceInput values",
            )
        _require_hard_flags("input", value)
    return values


def _summary_reason_codes(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_book_depth_resilience_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("market_book_depth_resilience_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("market_book_depth_resilience_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("market_book_depth_resilience_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_book_depth_resilience_inputs",):
        return "block"
    if "market_book_depth_resilience_block" in reason_codes:
        return "block"
    if "market_book_depth_resilience_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketBookDepthResilienceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketBookDepthResilienceReasonCodeCount(
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
        ResearchMarketBookDepthResilienceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_resilience_score(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.resilience_score for row in rows), ZERO) / Decimal(len(rows)))


def _maximum_row_value(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchMarketBookDepthResilienceRow) -> None:
    if row.spread_stress != _quantize(row.best_ask_price - row.best_bid_price):
        raise ValueError("spread_stress must match price gap")
    if row.depth_balance_score != _depth_balance_score(row.bid_depth, row.ask_depth):
        raise ValueError("depth_balance_score must match depth values")
    if row.manual_recheck_score != _quantize(ONE - row.manual_recheck_urgency):
        raise ValueError("manual_recheck_score must match urgency")
    expected_score = _quantize(
        row.depth_balance_score * Decimal("0.300000")
        + row.spread_resilience_score * Decimal("0.250000")
        + row.freshness_score * Decimal("0.200000")
        + row.fee_friction_score * Decimal("0.150000")
        + row.manual_recheck_score * Decimal("0.100000"),
    )
    if row.resilience_score != expected_score:
        raise ValueError("resilience_score must match component scores")
    if f"market_book_depth_resilience_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(report: ResearchMarketBookDepthResilienceReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.research_key)):
        raise ValueError("rows must be sorted by research_key")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_resilience_score != _average_resilience_score(report.rows):
        raise ValueError("average_resilience_score must match rows")
    if report.min_depth_balance_score != _minimum_row_value(
        report.rows,
        "depth_balance_score",
    ):
        raise ValueError("min_depth_balance_score must match rows")
    if report.max_spread_stress != _maximum_row_value(report.rows, "spread_stress"):
        raise ValueError("max_spread_stress must match rows")
    if report.max_freshness_age_seconds != _maximum_row_value(
        report.rows,
        "freshness_age_seconds",
    ):
        raise ValueError("max_freshness_age_seconds must match rows")
    if report.max_fee_rate != _maximum_row_value(report.rows, "fee_rate"):
        raise ValueError("max_fee_rate must match rows")
    if report.max_manual_recheck_urgency != _maximum_row_value(
        report.rows,
        "manual_recheck_urgency",
    ):
        raise ValueError("max_manual_recheck_urgency must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketBookDepthResilienceRow, ...],
) -> tuple[ResearchMarketBookDepthResilienceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketBookDepthResilienceRow:
            raise ValueError("rows must contain ResearchMarketBookDepthResilienceRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketBookDepthResilienceReasonCodeCount, ...],
) -> tuple[ResearchMarketBookDepthResilienceReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketBookDepthResilienceReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in BOOK_DEPTH_RESILIENCE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(_require_reason_code(name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be at most one")
    return decimal_value


def _require_optional_ratio_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(name, value)


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    if type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _derived_report_digest(report: ResearchMarketBookDepthResilienceReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload = dict(payload)
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_hex_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} must be a 64-character hex string")
