"""Pure expected value quality digest reducer for recommendations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationExpectedValueDigestConfig",
    "StrategyRecommendationExpectedValueDigestInput",
    "StrategyRecommendationExpectedValueDigestReasonCodeCount",
    "StrategyRecommendationExpectedValueDigestReport",
    "StrategyRecommendationExpectedValueDigestRow",
    "build_strategy_recommendation_expected_value_digest_report",
    "strategy_recommendation_expected_value_digest_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-expected-value-digest-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_DIGEST_CONFIG_VERSION
    )
    minimum_positive_expected_value: Decimal = Decimal("0.010000")
    watch_expected_value: Decimal = Decimal("0.000000")
    minimum_price_buffer: Decimal = Decimal("0.020000")
    minimum_confidence_adjustment: Decimal = Decimal("0.500000")
    stale_evidence_age_seconds: Decimal = Decimal("3600.000000")
    minimum_liquidity_depth: Decimal = Decimal("100.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_positive_expected_value",
            "watch_expected_value",
            "minimum_price_buffer",
            "stale_evidence_age_seconds",
            "minimum_liquidity_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_confidence_adjustment",
            _normalize_ratio(
                "minimum_confidence_adjustment",
                self.minimum_confidence_adjustment,
            ),
        )
        _require_at_most(
            "watch_expected_value",
            self.watch_expected_value,
            self.minimum_positive_expected_value,
        )
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueDigestConfig",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueDigestInput:
    recommendation_id: str
    estimated_probability: Decimal
    market_price: Decimal
    estimated_cost: Decimal
    confidence_adjustment: Decimal
    evidence_observed_at: datetime
    liquidity_depth: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        for field_name in ("estimated_probability", "market_price"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "estimated_cost",
            _normalize_nonnegative_decimal("estimated_cost", self.estimated_cost),
        )
        object.__setattr__(
            self,
            "confidence_adjustment",
            _normalize_ratio("confidence_adjustment", self.confidence_adjustment),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "liquidity_depth",
            _normalize_nonnegative_decimal("liquidity_depth", self.liquidity_depth),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueDigestInput",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueDigestRow:
    recommendation_id: str
    quality_status: str
    estimated_probability: Decimal
    market_price: Decimal
    estimated_cost: Decimal
    confidence_adjustment: Decimal
    probability_edge: Decimal
    price_cost_buffer: Decimal
    confidence_adjusted_edge: Decimal
    expected_value: Decimal
    confidence_adjusted_expected_value: Decimal
    evidence_observed_at: datetime
    evidence_age_seconds: Decimal
    liquidity_depth: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_status("quality_status", self.quality_status)
        for field_name in (
            "estimated_probability",
            "market_price",
            "confidence_adjustment",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "estimated_cost",
            "liquidity_depth",
            "evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_edge",
            "price_cost_buffer",
            "confidence_adjusted_edge",
            "expected_value",
            "confidence_adjusted_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.quality_status != _row_status(self.reason_codes):
            raise ValueError("quality_status must match reason_codes")
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueDigestRow",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueDigestReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_expected_value: Decimal
    min_confidence_adjusted_expected_value: Decimal
    stale_evidence_count: Decimal
    liquidity_guard_blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyRecommendationExpectedValueDigestReasonCodeCount, ...]
    recommendation_rows: tuple[StrategyRecommendationExpectedValueDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_evidence_count",
            "liquidity_guard_blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_expected_value",
            "min_confidence_adjusted_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "recommendation_rows",
            _normalize_rows(self.recommendation_rows),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("expected value digest report", self)
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueDigestReport",
            self,
        )


def build_strategy_recommendation_expected_value_digest_report(
    recommendations: Iterable[StrategyRecommendationExpectedValueDigestInput],
    *,
    config: StrategyRecommendationExpectedValueDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationExpectedValueDigestReport:
    if type(config) is not StrategyRecommendationExpectedValueDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationExpectedValueDigestConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(recommendations)
    rows = tuple(
        sorted(
            (
                _digest_row(
                    recommendation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for recommendation in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationExpectedValueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_expected_value=_max_decimal(tuple(row.expected_value for row in rows)),
        min_confidence_adjusted_expected_value=_min_decimal(
            tuple(row.confidence_adjusted_expected_value for row in rows),
        ),
        stale_evidence_count=_count(
            sum(1 for row in rows if "ev_evidence_stale_watch" in row.reason_codes),
        ),
        liquidity_guard_blocked_count=_count(
            sum(1 for row in rows if "ev_liquidity_depth_blocked" in row.reason_codes),
        ),
        status=_rollup_status(tuple(row.quality_status for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        recommendation_rows=rows,
    )


def strategy_recommendation_expected_value_digest_payload(
    report: StrategyRecommendationExpectedValueDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationExpectedValueDigestReport:
        require_paper_only_flags("report", report)
        reject_unsafe_surface_fields("expected value digest report", report)
        return json_ready_no_floats(report)
    if type(report) is dict:
        reject_unsafe_surface_fields("expected value digest payload", report)
        _reject_flag_downgrades("payload", report)
        _reject_risky_text_values("payload", report)
        ready = json_ready_no_floats(report)
        require_paper_only_flags("payload", _DictFlags(ready))
        return ready
    raise ValueError("report must be a StrategyRecommendationExpectedValueDigestReport")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _digest_row(
    recommendation: StrategyRecommendationExpectedValueDigestInput,
    *,
    config: StrategyRecommendationExpectedValueDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationExpectedValueDigestRow:
    probability_edge = _quantize(
        recommendation.estimated_probability - recommendation.market_price,
    )
    price_cost_buffer = _quantize(recommendation.estimated_cost - recommendation.market_price)
    confidence_adjusted_edge = _quantize(
        probability_edge * recommendation.confidence_adjustment,
    )
    expected_value = _quantize(confidence_adjusted_edge - price_cost_buffer)
    confidence_adjusted_expected_value = _quantize(
        expected_value * recommendation.confidence_adjustment,
    )
    evidence_age_seconds = _evidence_age_seconds(
        recommendation.evidence_observed_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        recommendation,
        probability_edge=probability_edge,
        price_cost_buffer=price_cost_buffer,
        threshold_expected_value=_quantize(probability_edge - price_cost_buffer),
        evidence_age_seconds=evidence_age_seconds,
        config=config,
    )
    return StrategyRecommendationExpectedValueDigestRow(
        recommendation_id=recommendation.recommendation_id,
        quality_status=_row_status(reason_codes),
        estimated_probability=recommendation.estimated_probability,
        market_price=recommendation.market_price,
        estimated_cost=recommendation.estimated_cost,
        confidence_adjustment=recommendation.confidence_adjustment,
        probability_edge=probability_edge,
        price_cost_buffer=price_cost_buffer,
        confidence_adjusted_edge=confidence_adjusted_edge,
        expected_value=expected_value,
        confidence_adjusted_expected_value=confidence_adjusted_expected_value,
        evidence_observed_at=recommendation.evidence_observed_at,
        evidence_age_seconds=evidence_age_seconds,
        liquidity_depth=recommendation.liquidity_depth,
        reason_codes=reason_codes,
    )


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_risky_text_values(label: str, value: object) -> None:
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_risky_text_values(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_risky_text_values(label, item)


def _row_reason_codes(
    recommendation: StrategyRecommendationExpectedValueDigestInput,
    *,
    probability_edge: Decimal,
    price_cost_buffer: Decimal,
    threshold_expected_value: Decimal,
    evidence_age_seconds: Decimal,
    config: StrategyRecommendationExpectedValueDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(recommendation.reason_codes)
    if probability_edge < ZERO:
        reason_codes.append("ev_probability_edge_blocked")
    elif threshold_expected_value < config.watch_expected_value:
        reason_codes.append("ev_expected_value_watch")
    elif threshold_expected_value < config.minimum_positive_expected_value:
        reason_codes.append("ev_expected_value_below_minimum_watch")
    if price_cost_buffer > config.minimum_price_buffer:
        reason_codes.append("ev_price_cost_buffer_watch")
    if recommendation.confidence_adjustment < config.minimum_confidence_adjustment:
        reason_codes.append("ev_confidence_adjustment_watch")
    if evidence_age_seconds > config.stale_evidence_age_seconds:
        reason_codes.append("ev_evidence_stale_watch")
    if recommendation.liquidity_depth < config.minimum_liquidity_depth:
        reason_codes.append("ev_liquidity_depth_blocked")
    if not _has_quality_guard(reason_codes):
        reason_codes.append("ev_quality_clear")
    return _normalize_reason_codes(tuple(reason_codes))


def _has_quality_guard(reason_codes: list[str]) -> bool:
    return any(
        reason_code.startswith("ev_")
        and reason_code not in ("ev_quality_clear",)
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[StrategyRecommendationExpectedValueDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("expected_value_digest_clear",)
    status = _rollup_status(tuple(row.quality_status for row in rows))
    reason_codes = [f"expected_value_digest_{'clear' if status == 'pass' else status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "ev_confidence_adjustment_watch",
        "ev_evidence_stale_watch",
        "ev_expected_value_below_minimum_watch",
        "ev_expected_value_watch",
        "ev_liquidity_depth_blocked",
        "ev_price_cost_buffer_watch",
        "ev_probability_edge_blocked",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationExpectedValueDigestRow, ...],
) -> tuple[StrategyRecommendationExpectedValueDigestReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _evidence_age_seconds(
    evidence_observed_at: datetime,
    generated_at: datetime,
) -> Decimal:
    seconds = Decimal(
        str(
            (
                generated_at - _as_utc("evidence_observed_at", evidence_observed_at)
            ).total_seconds(),
        ),
    )
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("evidence_observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    recommendations: Iterable[StrategyRecommendationExpectedValueDigestInput],
) -> tuple[StrategyRecommendationExpectedValueDigestInput, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        rows = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationExpectedValueDigestInput:
            raise ValueError(
                "recommendations must contain StrategyRecommendationExpectedValueDigestInput values",
            )
        require_paper_only_flags("recommendation", row)
        if row.recommendation_id in seen_ids:
            raise ValueError("recommendations must not contain duplicate ids")
        seen_ids.add(row.recommendation_id)
    return rows


def _normalize_rows(
    rows: Iterable[StrategyRecommendationExpectedValueDigestRow],
) -> tuple[StrategyRecommendationExpectedValueDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("recommendation_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("recommendation_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in values:
        if type(row) is not StrategyRecommendationExpectedValueDigestRow:
            raise ValueError(
                "recommendation_rows must contain StrategyRecommendationExpectedValueDigestRow values",
            )
        require_paper_only_flags("recommendation_row", row)
        if row.recommendation_id in seen_ids:
            raise ValueError("recommendation_rows must not contain duplicate ids")
        seen_ids.add(row.recommendation_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("recommendation_rows must use stable sequence")
    return values


def _normalize_reason_code_counts(
    value: Iterable[StrategyRecommendationExpectedValueDigestReasonCodeCount],
) -> tuple[StrategyRecommendationExpectedValueDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not StrategyRecommendationExpectedValueDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("reason_code_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use stable sequence")
        previous_key = key
        seen_codes.add(row.reason_code)
    return rows


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return reason_codes


def _validate_report(report: StrategyRecommendationExpectedValueDigestReport) -> None:
    rows = report.recommendation_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match recommendation_rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match recommendation_rows")
    if report.max_expected_value != _max_decimal(
        tuple(row.expected_value for row in rows),
    ):
        raise ValueError("max_expected_value must match recommendation_rows")
    if report.min_confidence_adjusted_expected_value != _min_decimal(
        tuple(row.confidence_adjusted_expected_value for row in rows),
    ):
        raise ValueError(
            "min_confidence_adjusted_expected_value must match recommendation_rows",
        )
    if report.stale_evidence_count != _count(
        sum(1 for row in rows if "ev_evidence_stale_watch" in row.reason_codes),
    ):
        raise ValueError("stale_evidence_count must match recommendation_rows")
    if report.liquidity_guard_blocked_count != _count(
        sum(1 for row in rows if "ev_liquidity_depth_blocked" in row.reason_codes),
    ):
        raise ValueError("liquidity_guard_blocked_count must match recommendation_rows")
    if report.status != _rollup_status(tuple(row.quality_status for row in rows)):
        raise ValueError("status must match recommendation_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match recommendation_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match recommendation_rows")


def _row_sort_key(
    row: StrategyRecommendationExpectedValueDigestRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.quality_status],
        -_row_severity(row),
        row.recommendation_id,
    )


def _row_severity(row: StrategyRecommendationExpectedValueDigestRow) -> Decimal:
    if row.quality_status == "blocked":
        return _count(
            sum(1 for reason_code in row.reason_codes if reason_code.endswith("_blocked")),
        )
    if row.quality_status == "watch":
        return _count(
            sum(1 for reason_code in row.reason_codes if reason_code.endswith("_watch")),
        )
    return ZERO


def _status_count(
    rows: tuple[StrategyRecommendationExpectedValueDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.quality_status == status))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("max_decimal", max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("min_decimal", min(values))


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be less than or equal to threshold")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe surface text")


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
        _require_canonical_string("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return tuple(sorted(reason_codes))


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
