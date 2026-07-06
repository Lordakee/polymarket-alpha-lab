"""Pure Phase 1 readonly paper event-category risk budget allocator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_EVENT_CATEGORY_RISK_BUDGET_ALLOCATOR_V2_CONFIG_VERSION = (
    "strategy-event-category-risk-budget-allocator-v2"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("sign", "ing")),
    "".join(("muta", "tion")),
    "".join(("b", "uy")),
    "".join(("s", "ell")),
    "".join(("tr", "ade")),
)

_ALLOCATION_STATUSES = ("pass", "watch", "blocked")
_STATUS_RANK = {"pass": 0, "watch": 1, "blocked": 2}

_ALLOCATED_REASON = "category_risk_budget_allocated"
_CONSTRAINED_REASON = "category_risk_budget_constrained"
_BLOCKED_REASON = "category_risk_budget_blocked"
_HARD_RISK_REASON = "category_hard_risk_limit_breached"
_EMPTY_REASON = "category_risk_budget_allocator_empty"
_COMPLETE_REASON = "category_risk_budget_allocator_complete"

_CALIBRATION_WEIGHT = Decimal("0.350000")
_LIQUIDITY_WEIGHT = Decimal("0.300000")
_INFORMATION_WEIGHT = Decimal("0.350000")
_CORRELATION_RISK_WEIGHT = Decimal("0.400000")
_SETTLEMENT_CLUSTER_RISK_WEIGHT = Decimal("0.300000")
_RESOLUTION_RISK_WEIGHT = Decimal("0.300000")


__all__ = (
    "DEFAULT_STRATEGY_EVENT_CATEGORY_RISK_BUDGET_ALLOCATOR_V2_CONFIG_VERSION",
    "StrategyEventCategoryRiskBudgetAllocatorV2Config",
    "StrategyEventCategoryRiskBudgetAllocatorV2Signal",
    "StrategyEventCategoryRiskBudgetAllocatorV2Row",
    "StrategyEventCategoryRiskBudgetAllocatorV2Report",
    "build_strategy_event_category_risk_budget_allocator_v2_report",
    "strategy_event_category_risk_budget_allocator_v2_payload",
    "validate_strategy_event_category_risk_budget_allocator_v2_payload",
)


@dataclass(frozen=True)
class StrategyEventCategoryRiskBudgetAllocatorV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_EVENT_CATEGORY_RISK_BUDGET_ALLOCATOR_V2_CONFIG_VERSION
    )
    total_paper_risk_budget: Decimal = Decimal("0.000000")
    watch_allocation_score_threshold: Decimal = Decimal("0.400000")
    block_allocation_score_threshold: Decimal = Decimal("0.150000")
    hard_risk_score_threshold: Decimal = Decimal("0.850000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyEventCategoryRiskBudgetAllocatorV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyEventCategoryRiskBudgetAllocatorV2Config)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "total_paper_risk_budget",
            _normalize_nonnegative_decimal(
                "total_paper_risk_budget",
                self.total_paper_risk_budget,
            ),
        )
        for field_name in (
            "watch_allocation_score_threshold",
            "block_allocation_score_threshold",
            "hard_risk_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_allocation_score_threshold > self.watch_allocation_score_threshold:
            raise ValueError(
                "block_allocation_score_threshold must be at most watch threshold",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class StrategyEventCategoryRiskBudgetAllocatorV2Signal:
    event_category: str
    observed_at: datetime
    calibration_score: Decimal
    liquidity_score: Decimal
    correlation_risk_score: Decimal
    settlement_cluster_risk_score: Decimal
    resolution_risk_score: Decimal
    information_quality_score: Decimal
    reason_codes: tuple[str, ...] = ("category_signal_reviewed",)
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyEventCategoryRiskBudgetAllocatorV2Signal does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("signal", self, StrategyEventCategoryRiskBudgetAllocatorV2Signal)
        _require_canonical_string("event_category", self.event_category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibration_score",
            "liquidity_score",
            "correlation_risk_score",
            "settlement_cluster_risk_score",
            "resolution_risk_score",
            "information_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("signal", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class StrategyEventCategoryRiskBudgetAllocatorV2Row:
    event_category: str
    observed_at: datetime
    calibration_score: Decimal
    liquidity_score: Decimal
    correlation_risk_score: Decimal
    settlement_cluster_risk_score: Decimal
    resolution_risk_score: Decimal
    information_quality_score: Decimal
    positive_signal_score: Decimal
    risk_pressure_score: Decimal
    allocation_score: Decimal
    allocation_weight: Decimal
    paper_risk_budget: Decimal
    signal_age_seconds: Decimal
    allocation_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyEventCategoryRiskBudgetAllocatorV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyEventCategoryRiskBudgetAllocatorV2Row)
        _require_canonical_string("event_category", self.event_category)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibration_score",
            "liquidity_score",
            "correlation_risk_score",
            "settlement_cluster_risk_score",
            "resolution_risk_score",
            "information_quality_score",
            "positive_signal_score",
            "risk_pressure_score",
            "allocation_score",
            "allocation_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "paper_risk_budget",
            _normalize_nonnegative_decimal("paper_risk_budget", self.paper_risk_budget),
        )
        object.__setattr__(
            self,
            "signal_age_seconds",
            _normalize_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        _require_status("allocation_status", self.allocation_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class StrategyEventCategoryRiskBudgetAllocatorV2Report:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    category_count: Decimal
    allocated_category_count: Decimal
    blocked_category_count: Decimal
    watch_category_count: Decimal
    pass_category_count: Decimal
    total_paper_risk_budget: Decimal
    allocated_paper_risk_budget: Decimal
    unallocated_paper_risk_budget: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyEventCategoryRiskBudgetAllocatorV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyEventCategoryRiskBudgetAllocatorV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyEventCategoryRiskBudgetAllocatorV2Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "category_count",
            "allocated_category_count",
            "blocked_category_count",
            "watch_category_count",
            "pass_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_paper_risk_budget",
            "allocated_paper_risk_budget",
            "unallocated_paper_risk_budget",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes_preserving_sequence(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_strategy_event_category_risk_budget_allocator_v2_report(
    signals: Iterable[StrategyEventCategoryRiskBudgetAllocatorV2Signal],
    *,
    config: StrategyEventCategoryRiskBudgetAllocatorV2Config,
    generated_at: datetime,
) -> StrategyEventCategoryRiskBudgetAllocatorV2Report:
    if type(config) is not StrategyEventCategoryRiskBudgetAllocatorV2Config:
        raise ValueError("config must be a StrategyEventCategoryRiskBudgetAllocatorV2Config")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_signals(signals)
    _validate_generated_at_covers_values(generated_at, values)

    metrics = tuple(_metrics_from_signal(value, config=config) for value in values)
    allocation_score_sum = _quantize(
        sum(
            (metric.allocation_score for metric in metrics if metric.status != "blocked"),
            _ZERO,
        ),
    )
    rows = _rows_from_metrics(
        metrics,
        allocation_score_sum=allocation_score_sum,
        total_paper_risk_budget=config.total_paper_risk_budget,
        generated_at=generated_at,
    )
    allocated_budget = _quantize(sum((row.paper_risk_budget for row in rows), _ZERO))

    return StrategyEventCategoryRiskBudgetAllocatorV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_decimal_count(len(values)),
        category_count=_decimal_count(len(rows)),
        allocated_category_count=_status_count(rows, "pass")
        + _status_count(rows, "watch"),
        blocked_category_count=_status_count(rows, "blocked"),
        watch_category_count=_status_count(rows, "watch"),
        pass_category_count=_status_count(rows, "pass"),
        total_paper_risk_budget=config.total_paper_risk_budget,
        allocated_paper_risk_budget=allocated_budget,
        unallocated_paper_risk_budget=_quantize(
            config.total_paper_risk_budget - allocated_budget,
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_event_category_risk_budget_allocator_v2_payload(
    report: StrategyEventCategoryRiskBudgetAllocatorV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyEventCategoryRiskBudgetAllocatorV2Report:
        raise ValueError("report must be a StrategyEventCategoryRiskBudgetAllocatorV2Report")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_strategy_event_category_risk_budget_allocator_v2_payload(payload)
    return payload


def validate_strategy_event_category_risk_budget_allocator_v2_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


@dataclass(frozen=True)
class _CategoryMetrics:
    signal: StrategyEventCategoryRiskBudgetAllocatorV2Signal
    positive_signal_score: Decimal
    risk_pressure_score: Decimal
    allocation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _metrics_from_signal(
    value: StrategyEventCategoryRiskBudgetAllocatorV2Signal,
    *,
    config: StrategyEventCategoryRiskBudgetAllocatorV2Config,
) -> _CategoryMetrics:
    positive_signal_score = _weighted_average(
        (
            (value.calibration_score, _CALIBRATION_WEIGHT),
            (value.liquidity_score, _LIQUIDITY_WEIGHT),
            (value.information_quality_score, _INFORMATION_WEIGHT),
        ),
    )
    risk_pressure_score = _weighted_average(
        (
            (value.correlation_risk_score, _CORRELATION_RISK_WEIGHT),
            (value.settlement_cluster_risk_score, _SETTLEMENT_CLUSTER_RISK_WEIGHT),
            (value.resolution_risk_score, _RESOLUTION_RISK_WEIGHT),
        ),
    )
    allocation_score = _quantize(positive_signal_score * (_ONE - risk_pressure_score))
    status = _allocation_status(value, allocation_score=allocation_score, config=config)
    return _CategoryMetrics(
        signal=value,
        positive_signal_score=positive_signal_score,
        risk_pressure_score=risk_pressure_score,
        allocation_score=allocation_score,
        status=status,
        reason_codes=_row_reason_codes(value, status),
    )


def _rows_from_metrics(
    metrics: tuple[_CategoryMetrics, ...],
    *,
    allocation_score_sum: Decimal,
    total_paper_risk_budget: Decimal,
    generated_at: datetime,
) -> tuple[StrategyEventCategoryRiskBudgetAllocatorV2Row, ...]:
    sorted_metrics = tuple(sorted(metrics, key=_metrics_sort_key))
    rows: list[StrategyEventCategoryRiskBudgetAllocatorV2Row] = []
    eligible_metrics = tuple(metric for metric in sorted_metrics if metric.status != "blocked")
    eligible_seen = 0
    allocated_budget = _ZERO
    for metric in sorted_metrics:
        allocation_weight = _ZERO
        paper_risk_budget = _ZERO
        if metric.status != "blocked" and allocation_score_sum > _ZERO:
            eligible_seen += 1
            allocation_weight = _ratio(metric.allocation_score, allocation_score_sum)
            if eligible_seen == len(eligible_metrics):
                paper_risk_budget = _quantize(total_paper_risk_budget - allocated_budget)
            else:
                with localcontext(_DECIMAL_CONTEXT):
                    paper_risk_budget = _quantize(
                        total_paper_risk_budget
                        * metric.allocation_score
                        / allocation_score_sum,
                    )
                allocated_budget = _quantize(allocated_budget + paper_risk_budget)
        rows.append(
            StrategyEventCategoryRiskBudgetAllocatorV2Row(
                event_category=metric.signal.event_category,
                observed_at=metric.signal.observed_at,
                calibration_score=metric.signal.calibration_score,
                liquidity_score=metric.signal.liquidity_score,
                correlation_risk_score=metric.signal.correlation_risk_score,
                settlement_cluster_risk_score=(
                    metric.signal.settlement_cluster_risk_score
                ),
                resolution_risk_score=metric.signal.resolution_risk_score,
                information_quality_score=metric.signal.information_quality_score,
                positive_signal_score=metric.positive_signal_score,
                risk_pressure_score=metric.risk_pressure_score,
                allocation_score=metric.allocation_score,
                allocation_weight=allocation_weight,
                paper_risk_budget=paper_risk_budget,
                signal_age_seconds=_seconds_between(metric.signal.observed_at, generated_at),
                allocation_status=metric.status,
                reason_codes=metric.reason_codes,
            ),
        )
    return tuple(rows)


def _weighted_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum((value * weight for value, weight in values), _ZERO))


def _allocation_status(
    value: StrategyEventCategoryRiskBudgetAllocatorV2Signal,
    *,
    allocation_score: Decimal,
    config: StrategyEventCategoryRiskBudgetAllocatorV2Config,
) -> str:
    if _has_hard_risk_pressure(value, config.hard_risk_score_threshold):
        return "blocked"
    if allocation_score < config.block_allocation_score_threshold:
        return "blocked"
    if allocation_score < config.watch_allocation_score_threshold:
        return "watch"
    return "pass"


def _has_hard_risk_pressure(
    value: StrategyEventCategoryRiskBudgetAllocatorV2Signal,
    threshold: Decimal,
) -> bool:
    return any(
        risk_score >= threshold
        for risk_score in (
            value.correlation_risk_score,
            value.settlement_cluster_risk_score,
            value.resolution_risk_score,
        )
    )


def _row_reason_codes(
    value: StrategyEventCategoryRiskBudgetAllocatorV2Signal,
    status: str,
) -> tuple[str, ...]:
    if status == "blocked":
        reasons: list[str] = []
        if _has_hard_risk_pressure(value, Decimal("0.850000")):
            reasons.append(_HARD_RISK_REASON)
        reasons.append(_BLOCKED_REASON)
        return tuple(reasons)
    if status == "watch":
        return (_CONSTRAINED_REASON,)
    return (_ALLOCATED_REASON,)


def _report_reason_codes(
    rows: tuple[StrategyEventCategoryRiskBudgetAllocatorV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if present == {_ALLOCATED_REASON}:
        return (_COMPLETE_REASON,)
    ordered_reasons = (_HARD_RISK_REASON, _BLOCKED_REASON, _CONSTRAINED_REASON)
    return tuple(reason_code for reason_code in ordered_reasons if reason_code in present)


def _normalize_signals(
    values: Iterable[StrategyEventCategoryRiskBudgetAllocatorV2Signal],
) -> tuple[StrategyEventCategoryRiskBudgetAllocatorV2Signal, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen_categories: set[str] = set()
    for value in normalized:
        if type(value) is not StrategyEventCategoryRiskBudgetAllocatorV2Signal:
            raise ValueError(
                "signals must contain StrategyEventCategoryRiskBudgetAllocatorV2Signal values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("signal", value)
        _require_or_set_digest(value)
        if value.event_category in seen_categories:
            raise ValueError("signals must not contain duplicate event_category values")
        seen_categories.add(value.event_category)
    return normalized


def _normalize_rows(
    values: Iterable[StrategyEventCategoryRiskBudgetAllocatorV2Row],
) -> tuple[StrategyEventCategoryRiskBudgetAllocatorV2Row, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain StrategyEventCategoryRiskBudgetAllocatorV2Row values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain StrategyEventCategoryRiskBudgetAllocatorV2Row values",
        ) from exc
    for row in rows:
        if type(row) is not StrategyEventCategoryRiskBudgetAllocatorV2Row:
            raise ValueError("rows must contain StrategyEventCategoryRiskBudgetAllocatorV2Row values")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic category allocation sort")
    if len(set(row.event_category for row in rows)) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_generated_at_covers_values(
    generated_at: datetime,
    values: tuple[StrategyEventCategoryRiskBudgetAllocatorV2Signal, ...],
) -> None:
    for value in values:
        if _seconds_between(value.observed_at, generated_at) < _ZERO:
            raise ValueError("generated_at must be at or after every observed_at")


def _validate_row_consistency(row: StrategyEventCategoryRiskBudgetAllocatorV2Row) -> None:
    if row.allocation_status == "blocked":
        if row.allocation_weight != _ZERO:
            raise ValueError("allocation_weight must be zero for blocked rows")
        if row.paper_risk_budget != _ZERO:
            raise ValueError("paper_risk_budget must be zero for blocked rows")
    if row.allocation_status != "blocked" and row.allocation_score <= _ZERO:
        raise ValueError("allocation_score must be positive for allocated rows")
    if row.allocation_status == "blocked" and _BLOCKED_REASON not in row.reason_codes:
        raise ValueError("reason_codes must include blocked reason for blocked rows")
    if row.allocation_status == "watch" and row.reason_codes != (_CONSTRAINED_REASON,):
        raise ValueError("reason_codes must match watch allocation status")
    if row.allocation_status == "pass" and row.reason_codes != (_ALLOCATED_REASON,):
        raise ValueError("reason_codes must match pass allocation status")


def _validate_report_consistency(
    report: StrategyEventCategoryRiskBudgetAllocatorV2Report,
) -> None:
    if report.category_count != _decimal_count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.input_count != report.category_count:
        raise ValueError("input_count must match rows")
    if report.allocated_category_count != (
        _status_count(report.rows, "pass") + _status_count(report.rows, "watch")
    ):
        raise ValueError("allocated_category_count must match rows")
    if report.blocked_category_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_category_count must match rows")
    if report.watch_category_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_category_count must match rows")
    if report.pass_category_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_category_count must match rows")
    allocated_budget = _quantize(sum((row.paper_risk_budget for row in report.rows), _ZERO))
    if report.allocated_paper_risk_budget != allocated_budget:
        raise ValueError("allocated_paper_risk_budget must match rows")
    if report.unallocated_paper_risk_budget != _quantize(
        report.total_paper_risk_budget - report.allocated_paper_risk_budget,
    ):
        raise ValueError("unallocated_paper_risk_budget must match total and allocated")
    if report.allocated_paper_risk_budget > report.total_paper_risk_budget:
        raise ValueError("allocated_paper_risk_budget must be at most total")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    if len(set(row.event_category for row in report.rows)) != len(report.rows):
        raise ValueError("rows must be unique")


def _metrics_sort_key(metric: _CategoryMetrics) -> tuple[int, Decimal, str]:
    if metric.status == "blocked":
        return (_STATUS_RANK[metric.status], _ZERO, metric.signal.event_category)
    return (_STATUS_RANK[metric.status], -metric.allocation_score, metric.signal.event_category)


def _row_sort_key(
    row: StrategyEventCategoryRiskBudgetAllocatorV2Row,
) -> tuple[int, Decimal, str]:
    if row.allocation_status == "blocked":
        return (_STATUS_RANK[row.allocation_status], _ZERO, row.event_category)
    return (
        _STATUS_RANK[row.allocation_status],
        -row.allocation_score,
        row.event_category,
    )


def _status_count(
    rows: tuple[StrategyEventCategoryRiskBudgetAllocatorV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.allocation_status == status))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(whole_seconds + microseconds)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    normalized = _normalize_reason_code_iterable(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes_preserving_sequence(value: Iterable[str]) -> tuple[str, ...]:
    return _normalize_reason_code_iterable(value)


def _normalize_reason_code_iterable(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _ALLOCATION_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}: {item}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("public payload contains unsupported value")


def _require_public_payload_values(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_values(item)
        return
    raise ValueError("public payload contains unsupported value")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        if _DIGEST_FIELD in value:
            current = value[_DIGEST_FIELD]
            if type(current) is not str:
                raise ValueError("derived_validation_digest must be a string")
            expected = _derived_digest(value)
            if current != expected or not _is_sha256_hex(current):
                raise ValueError("derived_validation_digest does not match payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)
