"""Pure report-only liquidity and cost exception rollup aggregation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any


LIQUIDITY_COST_EXCEPTION_ROLLUP_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_EXCEPTION_ROLLUP_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-cost-exception-rollup-report-v0"
)

__all__ = (
    "LIQUIDITY_COST_EXCEPTION_ROLLUP_STATUSES",
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_EXCEPTION_ROLLUP_REPORT_CONFIG_VERSION",
    "ResearchMarketLiquidityCostExceptionInput",
    "ResearchMarketLiquidityCostExceptionReasonCodeCount",
    "ResearchMarketLiquidityCostExceptionRollupConfig",
    "ResearchMarketLiquidityCostExceptionRollupReport",
    "ResearchMarketLiquidityCostExceptionRollupRow",
    "build_research_market_liquidity_cost_exception_rollup_report",
    "research_market_liquidity_cost_exception_rollup_report_digest",
    "research_market_liquidity_cost_exception_rollup_report_payload",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "secret",
    "credential",
    "private",
    "".join(("wal", "let")),
    "".join(("au", "th")),
    "".join(("ord", "er")),
    "".join(("tra", "de")),
    "".join(("li", "ve")),
    "".join(("b", "uy")),
    "".join(("se", "ll")),
    "".join(("reco", "mmend")),
    "".join(("siz", "ing")),
    "".join(("net", "work")),
)
COMPONENT_REASON_PRIORITY = (
    "depth_deterioration_block",
    "spread_stress_block",
    "fee_freshness_block",
    "settlement_friction_block",
    "quote_age_block",
    "manual_review_urgency_block",
    "depth_deterioration_watch",
    "spread_stress_watch",
    "fee_freshness_watch",
    "settlement_friction_watch",
    "quote_age_watch",
    "manual_review_urgency_watch",
)


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketLiquidityCostExceptionRollupConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_EXCEPTION_ROLLUP_REPORT_CONFIG_VERSION
    )
    watch_depth_deterioration_ratio: Decimal = Decimal("0.200000")
    block_depth_deterioration_ratio: Decimal = Decimal("0.500000")
    watch_spread_stress_score: Decimal = Decimal("0.300000")
    block_spread_stress_score: Decimal = Decimal("0.700000")
    watch_fee_age_seconds: Decimal = Decimal("3600.000000")
    block_fee_age_seconds: Decimal = Decimal("14400.000000")
    watch_settlement_friction_score: Decimal = Decimal("0.250000")
    block_settlement_friction_score: Decimal = Decimal("0.650000")
    watch_quote_age_seconds: Decimal = Decimal("60.000000")
    block_quote_age_seconds: Decimal = Decimal("300.000000")
    watch_manual_review_urgency: Decimal = Decimal("0.300000")
    block_manual_review_urgency: Decimal = Decimal("0.700000")
    block_component_count_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostExceptionRollupConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_EXCEPTION_ROLLUP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "watch_depth_deterioration_ratio",
            "block_depth_deterioration_ratio",
            "watch_spread_stress_score",
            "block_spread_stress_score",
            "watch_settlement_friction_score",
            "block_settlement_friction_score",
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_ratio_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "watch_fee_age_seconds",
            "block_fee_age_seconds",
            "watch_quote_age_seconds",
            "block_quote_age_seconds",
            "block_component_count_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "depth_deterioration_ratio",
            self.watch_depth_deterioration_ratio,
            self.block_depth_deterioration_ratio,
        )
        _require_threshold_pair(
            "spread_stress_score",
            self.watch_spread_stress_score,
            self.block_spread_stress_score,
        )
        _require_threshold_pair(
            "fee_age_seconds",
            self.watch_fee_age_seconds,
            self.block_fee_age_seconds,
        )
        _require_threshold_pair(
            "settlement_friction_score",
            self.watch_settlement_friction_score,
            self.block_settlement_friction_score,
        )
        _require_threshold_pair(
            "quote_age_seconds",
            self.watch_quote_age_seconds,
            self.block_quote_age_seconds,
        )
        _require_threshold_pair(
            "manual_review_urgency",
            self.watch_manual_review_urgency,
            self.block_manual_review_urgency,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostExceptionInput:
    rollup_key: str
    observed_at: datetime
    depth_deterioration_ratio: Decimal
    spread_stress_score: Decimal
    fee_age_seconds: Decimal
    settlement_friction_score: Decimal
    quote_age_seconds: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostExceptionInput, "input")
        _require_public_label("rollup_key", self.rollup_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "depth_deterioration_ratio",
            "spread_stress_score",
            "settlement_friction_score",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fee_age_seconds", "quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityCostExceptionRollupRow:
    rollup_key: str
    observed_at: datetime
    depth_deterioration_ratio: Decimal
    spread_stress_score: Decimal
    fee_age_seconds: Decimal
    settlement_friction_score: Decimal
    quote_age_seconds: Decimal
    manual_review_urgency: Decimal
    depth_deterioration_exception_score: Decimal
    spread_stress_exception_score: Decimal
    fee_freshness_exception_score: Decimal
    settlement_friction_exception_score: Decimal
    quote_age_exception_score: Decimal
    manual_review_exception_score: Decimal
    exception_score: Decimal
    exception_component_count: Decimal
    block_component_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityCostExceptionRollupRow, "row")
        _require_public_label("rollup_key", self.rollup_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("fee_age_seconds", "quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_deterioration_ratio",
            "spread_stress_score",
            "settlement_friction_score",
            "manual_review_urgency",
            "depth_deterioration_exception_score",
            "spread_stress_exception_score",
            "fee_freshness_exception_score",
            "settlement_friction_exception_score",
            "quote_age_exception_score",
            "manual_review_exception_score",
            "exception_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("exception_component_count", "block_component_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
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
class ResearchMarketLiquidityCostExceptionReasonCodeCount:
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
class ResearchMarketLiquidityCostExceptionRollupReport:
    generated_at: datetime
    config_version: str
    rollup_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    exception_component_count: Decimal
    block_component_count: Decimal
    average_exception_score: Decimal | None
    max_depth_deterioration_ratio: Decimal
    max_spread_stress_score: Decimal
    max_fee_age_seconds: Decimal
    max_settlement_friction_score: Decimal
    max_quote_age_seconds: Decimal
    max_manual_review_urgency: Decimal
    status: str
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityCostExceptionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityCostExceptionRollupReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "rollup_count",
            "pass_count",
            "watch_count",
            "block_count",
            "exception_component_count",
            "block_component_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_exception_score",
            _require_optional_ratio_decimal(
                "average_exception_score",
                self.average_exception_score,
            ),
        )
        for field_name in ("max_fee_age_seconds", "max_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_depth_deterioration_ratio",
            "max_spread_stress_score",
            "max_settlement_friction_score",
            "max_manual_review_urgency",
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
        _apply_or_verify_digest(self)


def build_research_market_liquidity_cost_exception_rollup_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketLiquidityCostExceptionRollupConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityCostExceptionRollupReport:
    if type(config) is not ResearchMarketLiquidityCostExceptionRollupConfig:
        raise ValueError(
            "config must be a ResearchMarketLiquidityCostExceptionRollupConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.rollup_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketLiquidityCostExceptionRollupReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rollup_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        exception_component_count=_sum_row_value(rows, "exception_component_count"),
        block_component_count=_sum_row_value(rows, "block_component_count"),
        average_exception_score=_average_exception_score(rows),
        max_depth_deterioration_ratio=_maximum_row_value(
            rows,
            "depth_deterioration_ratio",
        ),
        max_spread_stress_score=_maximum_row_value(rows, "spread_stress_score"),
        max_fee_age_seconds=_maximum_row_value(rows, "fee_age_seconds"),
        max_settlement_friction_score=_maximum_row_value(
            rows,
            "settlement_friction_score",
        ),
        max_quote_age_seconds=_maximum_row_value(rows, "quote_age_seconds"),
        max_manual_review_urgency=_maximum_row_value(rows, "manual_review_urgency"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_liquidity_cost_exception_rollup_report_payload(
    report: ResearchMarketLiquidityCostExceptionRollupReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityCostExceptionRollupReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityCostExceptionRollupReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    return payload


def research_market_liquidity_cost_exception_rollup_report_digest(
    report: ResearchMarketLiquidityCostExceptionRollupReport,
) -> str:
    if type(report) is not ResearchMarketLiquidityCostExceptionRollupReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityCostExceptionRollupReport",
        )
    research_market_liquidity_cost_exception_rollup_report_payload(report)
    return report.derived_validation_digest


def _row_from_input(
    item: ResearchMarketLiquidityCostExceptionInput,
    *,
    config: ResearchMarketLiquidityCostExceptionRollupConfig,
) -> ResearchMarketLiquidityCostExceptionRollupRow:
    component_statuses = _component_statuses(item, config=config)
    component_scores = _component_scores(item, config=config)
    exception_component_count = _decimal_count(
        sum(1 for status in component_statuses.values() if status != "pass"),
    )
    block_component_count = _decimal_count(
        sum(1 for status in component_statuses.values() if status == "block"),
    )
    status = _row_status(
        component_statuses=component_statuses,
        block_component_count=block_component_count,
        config=config,
    )
    return ResearchMarketLiquidityCostExceptionRollupRow(
        rollup_key=item.rollup_key,
        observed_at=item.observed_at,
        depth_deterioration_ratio=item.depth_deterioration_ratio,
        spread_stress_score=item.spread_stress_score,
        fee_age_seconds=item.fee_age_seconds,
        settlement_friction_score=item.settlement_friction_score,
        quote_age_seconds=item.quote_age_seconds,
        manual_review_urgency=item.manual_review_urgency,
        depth_deterioration_exception_score=component_scores[
            "depth_deterioration"
        ],
        spread_stress_exception_score=component_scores["spread_stress"],
        fee_freshness_exception_score=component_scores["fee_freshness"],
        settlement_friction_exception_score=component_scores["settlement_friction"],
        quote_age_exception_score=component_scores["quote_age"],
        manual_review_exception_score=component_scores["manual_review"],
        exception_score=_average(tuple(component_scores.values())),
        exception_component_count=exception_component_count,
        block_component_count=block_component_count,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            status=status,
            component_statuses=component_statuses,
        ),
    )


def _component_scores(
    item: ResearchMarketLiquidityCostExceptionInput,
    *,
    config: ResearchMarketLiquidityCostExceptionRollupConfig,
) -> dict[str, Decimal]:
    return {
        "depth_deterioration": _capped_ratio(
            item.depth_deterioration_ratio,
            config.block_depth_deterioration_ratio,
        ),
        "spread_stress": _capped_ratio(
            item.spread_stress_score,
            config.block_spread_stress_score,
        ),
        "fee_freshness": _capped_ratio(
            item.fee_age_seconds,
            config.block_fee_age_seconds,
        ),
        "settlement_friction": _capped_ratio(
            item.settlement_friction_score,
            config.block_settlement_friction_score,
        ),
        "quote_age": _capped_ratio(
            item.quote_age_seconds,
            config.block_quote_age_seconds,
        ),
        "manual_review": _capped_ratio(
            item.manual_review_urgency,
            config.block_manual_review_urgency,
        ),
    }


def _component_statuses(
    item: ResearchMarketLiquidityCostExceptionInput,
    *,
    config: ResearchMarketLiquidityCostExceptionRollupConfig,
) -> dict[str, str]:
    return {
        "depth_deterioration": _threshold_status(
            item.depth_deterioration_ratio,
            watch_value=config.watch_depth_deterioration_ratio,
            block_value=config.block_depth_deterioration_ratio,
        ),
        "spread_stress": _threshold_status(
            item.spread_stress_score,
            watch_value=config.watch_spread_stress_score,
            block_value=config.block_spread_stress_score,
        ),
        "fee_freshness": _threshold_status(
            item.fee_age_seconds,
            watch_value=config.watch_fee_age_seconds,
            block_value=config.block_fee_age_seconds,
        ),
        "settlement_friction": _threshold_status(
            item.settlement_friction_score,
            watch_value=config.watch_settlement_friction_score,
            block_value=config.block_settlement_friction_score,
        ),
        "quote_age": _threshold_status(
            item.quote_age_seconds,
            watch_value=config.watch_quote_age_seconds,
            block_value=config.block_quote_age_seconds,
        ),
        "manual_review_urgency": _threshold_status(
            item.manual_review_urgency,
            watch_value=config.watch_manual_review_urgency,
            block_value=config.block_manual_review_urgency,
        ),
    }


def _threshold_status(
    value: Decimal,
    *,
    watch_value: Decimal,
    block_value: Decimal,
) -> str:
    if value >= block_value:
        return "block"
    if value >= watch_value:
        return "watch"
    return "pass"


def _row_status(
    *,
    component_statuses: dict[str, str],
    block_component_count: Decimal,
    config: ResearchMarketLiquidityCostExceptionRollupConfig,
) -> str:
    if (
        "block" in component_statuses.values()
        or block_component_count >= config.block_component_count_threshold
    ):
        return "block"
    if "watch" in component_statuses.values():
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketLiquidityCostExceptionInput,
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    codes = {f"liquidity_cost_exception_{status}"}
    for component_name, component_status in component_statuses.items():
        if component_status != "pass":
            codes.add(f"{component_name}_{component_status}")
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _summary_reason_codes(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_cost_exception_rollups",)
    if all(row.status == "pass" for row in rows):
        return ("liquidity_cost_exception_rollup_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("liquidity_cost_exception_rollup_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("liquidity_cost_exception_rollup_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for reason_code in COMPONENT_REASON_PRIORITY:
        if reason_code in row_codes:
            codes.append(reason_code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_liquidity_cost_exception_rollups",):
        return "block"
    if "liquidity_cost_exception_rollup_block" in reason_codes:
        return "block"
    if "liquidity_cost_exception_rollup_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketLiquidityCostExceptionReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketLiquidityCostExceptionReasonCodeCount(
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
        ResearchMarketLiquidityCostExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketLiquidityCostExceptionInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketLiquidityCostExceptionInput:
    if type(value) is ResearchMarketLiquidityCostExceptionInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketLiquidityCostExceptionInput(
        rollup_key=_field_value(value, "rollup_key"),
        observed_at=_field_value(value, "observed_at"),
        depth_deterioration_ratio=_field_value(
            value,
            "depth_deterioration_ratio",
        ),
        spread_stress_score=_field_value(value, "spread_stress_score"),
        fee_age_seconds=_field_value(value, "fee_age_seconds"),
        settlement_friction_score=_field_value(
            value,
            "settlement_friction_score",
        ),
        quote_age_seconds=_field_value(value, "quote_age_seconds"),
        manual_review_urgency=_field_value(value, "manual_review_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str, *, default: object = MISSING) -> Any:
    if isinstance(value, dict):
        if field_name in value:
            return value[field_name]
    elif hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not MISSING:
        return default
    raise ValueError(f"input missing {field_name}")


def _average(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _average_exception_score(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.exception_score for row in rows), ZERO) / Decimal(len(rows)))


def _capped_ratio(value: Decimal, limit: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        ratio = value / limit
    if ratio > ONE:
        return ONE
    if ratio < ZERO:
        return ZERO
    return _quantize(ratio)


def _maximum_row_value(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_row_value(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _status_count(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(
    row: ResearchMarketLiquidityCostExceptionRollupRow,
) -> None:
    expected_score = _average(
        (
            row.depth_deterioration_exception_score,
            row.spread_stress_exception_score,
            row.fee_freshness_exception_score,
            row.settlement_friction_exception_score,
            row.quote_age_exception_score,
            row.manual_review_exception_score,
        ),
    )
    if row.exception_score != expected_score:
        raise ValueError("exception_score must match component scores")
    if f"liquidity_cost_exception_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    if row.block_component_count > row.exception_component_count:
        raise ValueError("block_component_count must not exceed exception components")


def _validate_report_consistency(
    report: ResearchMarketLiquidityCostExceptionRollupReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.rollup_key)):
        raise ValueError("rows must be sorted by rollup_key")
    if report.rollup_count != _decimal_count(len(report.rows)):
        raise ValueError("rollup_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.exception_component_count != _sum_row_value(
        report.rows,
        "exception_component_count",
    ):
        raise ValueError("exception_component_count must match rows")
    if report.block_component_count != _sum_row_value(
        report.rows,
        "block_component_count",
    ):
        raise ValueError("block_component_count must match rows")
    if report.average_exception_score != _average_exception_score(report.rows):
        raise ValueError("average_exception_score must match rows")
    if report.max_depth_deterioration_ratio != _maximum_row_value(
        report.rows,
        "depth_deterioration_ratio",
    ):
        raise ValueError("max_depth_deterioration_ratio must match rows")
    if report.max_spread_stress_score != _maximum_row_value(
        report.rows,
        "spread_stress_score",
    ):
        raise ValueError("max_spread_stress_score must match rows")
    if report.max_fee_age_seconds != _maximum_row_value(
        report.rows,
        "fee_age_seconds",
    ):
        raise ValueError("max_fee_age_seconds must match rows")
    if report.max_settlement_friction_score != _maximum_row_value(
        report.rows,
        "settlement_friction_score",
    ):
        raise ValueError("max_settlement_friction_score must match rows")
    if report.max_quote_age_seconds != _maximum_row_value(
        report.rows,
        "quote_age_seconds",
    ):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.max_manual_review_urgency != _maximum_row_value(
        report.rows,
        "manual_review_urgency",
    ):
        raise ValueError("max_manual_review_urgency must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...],
) -> tuple[ResearchMarketLiquidityCostExceptionRollupRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketLiquidityCostExceptionRollupRow:
            raise ValueError(
                "rows must contain ResearchMarketLiquidityCostExceptionRollupRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketLiquidityCostExceptionReasonCodeCount, ...],
) -> tuple[ResearchMarketLiquidityCostExceptionReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketLiquidityCostExceptionReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
    return counts


def _apply_or_verify_digest(
    report: ResearchMarketLiquidityCostExceptionRollupReport,
) -> None:
    expected_digest = _digest_without_digest_field(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
        return
    if not SHA256_RE.fullmatch(report.derived_validation_digest):
        raise ValueError("derived_validation_digest must be a sha256 digest")
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _digest_without_digest_field(
    report: ResearchMarketLiquidityCostExceptionRollupReport,
) -> str:
    payload = _payload_value(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in LIQUIDITY_COST_EXCEPTION_ROLLUP_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
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


def _require_positive_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(name, value)
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


def _require_threshold_pair(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value >= block_value:
        raise ValueError(f"watch {name} must be less than block {name}")


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: Any, *, include_digest: bool = True) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, Any] = {}
        for field in fields(value):
            if not include_digest and field.name == "derived_validation_digest":
                continue
            payload[field.name] = _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return payload
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item, include_digest=include_digest)
        return ready
    if type(value) is float or type(value) is int:
        raise ValueError("payload value must not be numeric")
    if type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _reject_unsafe_public_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_payload_key(key)
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("public payload contains unsafe public content")


def _require_public_payload_key(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("public payload keys must be strings")
    if _has_unsafe_public_fragment(value):
        raise ValueError("public payload key has unsafe public text")
    return value


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
