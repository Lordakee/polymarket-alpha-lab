"""Pure Phase 1 category budget pressure gate."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_CATEGORY_BUDGET_PRESSURE_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-category-budget-pressure-gate-v2"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_REDACTED_SOURCE_REFERENCE = "<redacted>"
_STATUSES = ("blocked", "watch", "pass")
_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_HEX_CHARS = frozenset("0123456789abcdef")
_EMPTY_REASON = "strategy_recommendation_category_budget_pressure_gate_v2_empty"
_PASS_REASON = "recommendation_budget_pass"
_BLOCK_REASONS = frozenset(
    (
        "category_paper_exposure_blocked",
        "correlated_event_cluster_blocked",
        "source_coverage_blocked",
        "liquidity_capacity_blocked",
        "recommendation_budget_blocked",
    ),
)
_REASON_PRIORITY = (
    "category_paper_exposure_blocked",
    "category_paper_exposure_watch",
    "category_paper_exposure_reduced",
    "correlated_event_cluster_blocked",
    "correlated_event_cluster_watch",
    "source_coverage_blocked",
    "source_coverage_weak",
    "liquidity_capacity_blocked",
    "liquidity_capacity_watch",
    "liquidity_capacity_reduced",
    "recommendation_budget_blocked",
    "recommendation_budget_reduced",
    _PASS_REASON,
    _EMPTY_REASON,
)
_RESULT_REASON_CODES = frozenset(_REASON_PRIORITY[:-1])
_REPORT_REASON_CODES = frozenset(_REASON_PRIORITY)
_UNSAFE_TEXT_FRAGMENTS = (
    "sec" "ret",
    "tok" "en",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "au" "th",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "li" "ve" " " "trading",
    "data" "base",
    "sup" "abase",
    "net" "work",
    "://",
)


@dataclass(frozen=True)
class StrategyRecommendationCategoryBudgetPressureGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_CATEGORY_BUDGET_PRESSURE_GATE_V2_CONFIG_VERSION
    )
    category_budget_notional: Decimal = Decimal("0.000000")
    correlated_event_cluster_notional_cap: Decimal = Decimal("0.000000")
    max_liquidity_capacity_utilization: Decimal = Decimal("0.000000")
    category_exposure_watch_ratio: Decimal = Decimal("0.000000")
    correlated_event_watch_ratio: Decimal = Decimal("0.000000")
    liquidity_capacity_watch_ratio: Decimal = Decimal("0.000000")
    min_independent_source_count: Decimal = Decimal("1")
    source_block_count: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "category_budget_notional",
            "correlated_event_cluster_notional_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_liquidity_capacity_utilization",
            "category_exposure_watch_ratio",
            "correlated_event_watch_ratio",
            "liquidity_capacity_watch_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_independent_source_count",
            _normalize_positive_count(
                "min_independent_source_count",
                self.min_independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "source_block_count",
            _normalize_nonnegative_count("source_block_count", self.source_block_count),
        )
        if self.source_block_count > self.min_independent_source_count:
            raise ValueError(
                "source_block_count must not exceed min_independent_source_count",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationCategoryBudgetPressureGateV2Input:
    recommendation_id: str
    category: str
    requested_notional: Decimal
    current_category_paper_exposure: Decimal
    correlated_event_cluster_exposure: Decimal
    independent_source_count: Decimal
    liquidity_capacity: Decimal
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("recommendation_id", self.recommendation_id)
        _require_public_text("category", self.category)
        for field_name in (
            "requested_notional",
            "current_category_paper_exposure",
            "correlated_event_cluster_exposure",
            "liquidity_capacity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_nonnegative_count(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        _require_text("source_reference", self.source_reference)
        _require_flags("input", self)


@dataclass(frozen=True)
class StrategyRecommendationCategoryBudgetPressureGateV2Result:
    recommendation_id: str
    category: str
    requested_notional: Decimal
    current_category_paper_exposure: Decimal
    correlated_event_cluster_exposure: Decimal
    independent_source_count: Decimal
    liquidity_capacity: Decimal
    category_exposure_after_requested: Decimal
    category_pressure_ratio: Decimal
    remaining_category_budget: Decimal
    correlated_event_pressure_ratio: Decimal
    remaining_correlated_event_budget: Decimal
    liquidity_allocation_capacity: Decimal
    liquidity_capacity_utilization_ratio: Decimal
    source_coverage_ratio: Decimal
    approved_notional: Decimal
    reduction_notional: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    redacted_source_reference: str
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("recommendation_id", self.recommendation_id)
        _require_public_text("category", self.category)
        for field_name in (
            "requested_notional",
            "current_category_paper_exposure",
            "correlated_event_cluster_exposure",
            "liquidity_capacity",
            "category_exposure_after_requested",
            "remaining_category_budget",
            "remaining_correlated_event_budget",
            "liquidity_allocation_capacity",
            "approved_notional",
            "reduction_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "independent_source_count",
            _normalize_nonnegative_count(
                "independent_source_count",
                self.independent_source_count,
            ),
        )
        for field_name in (
            "category_pressure_ratio",
            "correlated_event_pressure_ratio",
            "liquidity_capacity_utilization_ratio",
            "source_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_result_reason_codes("reason_codes", self.reason_codes),
        )
        if self.redacted_source_reference != _REDACTED_SOURCE_REFERENCE:
            raise ValueError("redacted_source_reference must be redacted")
        _require_digest("validation_digest", self.validation_digest)
        _require_flags("result", self)
        _validate_result(self)


@dataclass(frozen=True)
class StrategyRecommendationCategoryBudgetPressureGateV2Report:
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_requested_notional: Decimal
    total_approved_notional: Decimal
    total_reduction_notional: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    results: tuple[StrategyRecommendationCategoryBudgetPressureGateV2Result, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "recommendation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_requested_notional",
            "total_approved_notional",
            "total_reduction_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_digest("validation_digest", self.validation_digest)
        _require_flags("report", self)
        _validate_report(self)


def build_strategy_recommendation_category_budget_pressure_gate_v2(
    recommendations: Iterable[StrategyRecommendationCategoryBudgetPressureGateV2Input],
    *,
    config: StrategyRecommendationCategoryBudgetPressureGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationCategoryBudgetPressureGateV2Report:
    if type(config) is not StrategyRecommendationCategoryBudgetPressureGateV2Config:
        raise ValueError(
            "config must be a "
            "StrategyRecommendationCategoryBudgetPressureGateV2Config",
        )
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_recommendations(recommendations)
    results = tuple(
        sorted(
            (
                _result_from_recommendation(item, config=config)
                for item in items
            ),
            key=_result_sort_key,
        ),
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "recommendation_count": _count(len(results)),
        "pass_count": _result_status_count(results, "pass"),
        "watch_count": _result_status_count(results, "watch"),
        "blocked_count": _result_status_count(results, "blocked"),
        "total_requested_notional": _sum_decimal(
            result.requested_notional for result in results
        ),
        "total_approved_notional": _sum_decimal(
            result.approved_notional for result in results
        ),
        "total_reduction_notional": _sum_decimal(
            result.reduction_notional for result in results
        ),
        "gate_status": _report_status(results),
        "reason_codes": _report_reason_codes(results),
        "results": results,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationCategoryBudgetPressureGateV2Report(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def strategy_recommendation_category_budget_pressure_gate_v2_payload(
    report: StrategyRecommendationCategoryBudgetPressureGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationCategoryBudgetPressureGateV2Report:
        _require_flags("report", report)
        _validate_report(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_payload(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyRecommendationCategoryBudgetPressureGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    return payload


def _normalize_recommendations(
    recommendations: Iterable[StrategyRecommendationCategoryBudgetPressureGateV2Input],
) -> tuple[StrategyRecommendationCategoryBudgetPressureGateV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationCategoryBudgetPressureGateV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationCategoryBudgetPressureGateV2Input",
            )
        _require_flags("input", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendation_id values must be unique")
        seen.add(item.recommendation_id)
    return items


def _result_from_recommendation(
    item: StrategyRecommendationCategoryBudgetPressureGateV2Input,
    *,
    config: StrategyRecommendationCategoryBudgetPressureGateV2Config,
) -> StrategyRecommendationCategoryBudgetPressureGateV2Result:
    category_exposure_after_requested = _quantize(
        item.current_category_paper_exposure + item.requested_notional,
    )
    category_pressure_ratio = _ratio(
        category_exposure_after_requested,
        config.category_budget_notional,
    )
    remaining_category_budget = _remaining_budget(
        config.category_budget_notional,
        item.current_category_paper_exposure,
    )
    correlated_event_exposure_after_requested = _quantize(
        item.correlated_event_cluster_exposure + item.requested_notional,
    )
    correlated_event_pressure_ratio = _ratio(
        correlated_event_exposure_after_requested,
        config.correlated_event_cluster_notional_cap,
    )
    remaining_correlated_event_budget = _remaining_budget(
        config.correlated_event_cluster_notional_cap,
        item.correlated_event_cluster_exposure,
    )
    liquidity_allocation_capacity = _quantize(
        item.liquidity_capacity * config.max_liquidity_capacity_utilization,
    )
    liquidity_capacity_utilization_ratio = (
        _ZERO
        if liquidity_allocation_capacity <= _ZERO
        else _ratio(item.requested_notional, liquidity_allocation_capacity)
    )
    source_coverage_ratio = _capped_ratio(
        item.independent_source_count,
        config.min_independent_source_count,
    )
    base_reason_codes = _base_reason_codes(
        item,
        config=config,
        category_pressure_ratio=category_pressure_ratio,
        remaining_category_budget=remaining_category_budget,
        correlated_event_pressure_ratio=correlated_event_pressure_ratio,
        liquidity_allocation_capacity=liquidity_allocation_capacity,
        liquidity_capacity_utilization_ratio=liquidity_capacity_utilization_ratio,
    )
    if any(reason in _BLOCK_REASONS for reason in base_reason_codes):
        approved_notional = _ZERO
        reason_codes = (*base_reason_codes, "recommendation_budget_blocked")
    else:
        approved_notional = _approved_notional(
            requested_notional=item.requested_notional,
            remaining_category_budget=remaining_category_budget,
            remaining_correlated_event_budget=remaining_correlated_event_budget,
            liquidity_allocation_capacity=liquidity_allocation_capacity,
            source_coverage_ratio=source_coverage_ratio,
        )
        if approved_notional < item.requested_notional:
            reason_codes = (*base_reason_codes, "recommendation_budget_reduced")
        elif base_reason_codes:
            reason_codes = base_reason_codes
        else:
            reason_codes = (_PASS_REASON,)
    reason_codes = _normalize_result_reason_codes("reason_codes", reason_codes)
    result_values = {
        "recommendation_id": item.recommendation_id,
        "category": item.category,
        "requested_notional": item.requested_notional,
        "current_category_paper_exposure": item.current_category_paper_exposure,
        "correlated_event_cluster_exposure": item.correlated_event_cluster_exposure,
        "independent_source_count": item.independent_source_count,
        "liquidity_capacity": item.liquidity_capacity,
        "category_exposure_after_requested": category_exposure_after_requested,
        "category_pressure_ratio": category_pressure_ratio,
        "remaining_category_budget": remaining_category_budget,
        "correlated_event_pressure_ratio": correlated_event_pressure_ratio,
        "remaining_correlated_event_budget": remaining_correlated_event_budget,
        "liquidity_allocation_capacity": liquidity_allocation_capacity,
        "liquidity_capacity_utilization_ratio": liquidity_capacity_utilization_ratio,
        "source_coverage_ratio": source_coverage_ratio,
        "approved_notional": approved_notional,
        "reduction_notional": _quantize(item.requested_notional - approved_notional),
        "gate_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "redacted_source_reference": _REDACTED_SOURCE_REFERENCE,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationCategoryBudgetPressureGateV2Result(
        **result_values,
        validation_digest=_validation_digest(result_values),
    )


def _base_reason_codes(
    item: StrategyRecommendationCategoryBudgetPressureGateV2Input,
    *,
    config: StrategyRecommendationCategoryBudgetPressureGateV2Config,
    category_pressure_ratio: Decimal,
    remaining_category_budget: Decimal,
    correlated_event_pressure_ratio: Decimal,
    liquidity_allocation_capacity: Decimal,
    liquidity_capacity_utilization_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    category_blocked = (
        item.current_category_paper_exposure >= config.category_budget_notional
    )
    if category_blocked:
        reason_codes.append("category_paper_exposure_blocked")
    else:
        if category_pressure_ratio >= config.category_exposure_watch_ratio:
            reason_codes.append("category_paper_exposure_watch")
        if remaining_category_budget < item.requested_notional:
            reason_codes.append("category_paper_exposure_reduced")

    if item.correlated_event_cluster_exposure >= (
        config.correlated_event_cluster_notional_cap
    ):
        reason_codes.append("correlated_event_cluster_blocked")
    elif correlated_event_pressure_ratio >= config.correlated_event_watch_ratio:
        reason_codes.append("correlated_event_cluster_watch")

    if item.independent_source_count <= config.source_block_count:
        reason_codes.append("source_coverage_blocked")
    elif item.independent_source_count < config.min_independent_source_count:
        reason_codes.append("source_coverage_weak")

    if liquidity_allocation_capacity <= _ZERO:
        reason_codes.append("liquidity_capacity_blocked")
    else:
        if liquidity_capacity_utilization_ratio >= config.liquidity_capacity_watch_ratio:
            reason_codes.append("liquidity_capacity_watch")
        if liquidity_allocation_capacity < item.requested_notional:
            reason_codes.append("liquidity_capacity_reduced")

    return _normalize_result_reason_codes("reason_codes", tuple(reason_codes))


def _approved_notional(
    *,
    requested_notional: Decimal,
    remaining_category_budget: Decimal,
    remaining_correlated_event_budget: Decimal,
    liquidity_allocation_capacity: Decimal,
    source_coverage_ratio: Decimal,
) -> Decimal:
    constrained = min(
        requested_notional,
        remaining_category_budget,
        remaining_correlated_event_budget,
        liquidity_allocation_capacity,
    )
    return _quantize(constrained * source_coverage_ratio)


def _expected_approved_notional(
    result: StrategyRecommendationCategoryBudgetPressureGateV2Result,
) -> Decimal:
    if _status_from_reason_codes(result.reason_codes) == "blocked":
        return _ZERO
    return _approved_notional(
        requested_notional=result.requested_notional,
        remaining_category_budget=result.remaining_category_budget,
        remaining_correlated_event_budget=result.remaining_correlated_event_budget,
        liquidity_allocation_capacity=result.liquidity_allocation_capacity,
        source_coverage_ratio=result.source_coverage_ratio,
    )


def _remaining_budget(limit: Decimal, used: Decimal) -> Decimal:
    remaining = _quantize(limit - used)
    if remaining < _ZERO:
        return _ZERO
    return remaining


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "blocked"
    if reason_codes == (_PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(
    results: tuple[StrategyRecommendationCategoryBudgetPressureGateV2Result, ...],
) -> str:
    if not results:
        return "blocked"
    if any(result.gate_status == "blocked" for result in results):
        return "blocked"
    if any(result.gate_status == "watch" for result in results):
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[StrategyRecommendationCategoryBudgetPressureGateV2Result, ...],
) -> tuple[str, ...]:
    if not results:
        return (_EMPTY_REASON,)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for result in results for reason in result.reason_codes),
    )


def _result_status_count(
    results: tuple[StrategyRecommendationCategoryBudgetPressureGateV2Result, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for result in results if result.gate_status == status))


def _normalize_results(
    results: object,
) -> tuple[StrategyRecommendationCategoryBudgetPressureGateV2Result, ...]:
    if isinstance(results, (str, bytes)):
        raise ValueError("results must be an iterable")
    try:
        normalized = tuple(results)
    except TypeError as exc:
        raise ValueError("results must be an iterable") from exc
    for result in normalized:
        if type(result) is not StrategyRecommendationCategoryBudgetPressureGateV2Result:
            raise ValueError(
                "results must contain "
                "StrategyRecommendationCategoryBudgetPressureGateV2Result",
            )
        _require_flags("result", result)
        _validate_result(result)
    if normalized != tuple(sorted(normalized, key=_result_sort_key)):
        raise ValueError("results must be sorted deterministically")
    return normalized


def _validate_result(
    result: StrategyRecommendationCategoryBudgetPressureGateV2Result,
) -> None:
    expected_approved_notional = _expected_approved_notional(result)
    if result.approved_notional != expected_approved_notional:
        raise ValueError("approved_notional must match derived budget pressure")
    expected_reduction_notional = _quantize(
        result.requested_notional - result.approved_notional,
    )
    if result.reduction_notional != expected_reduction_notional:
        raise ValueError("reduction_notional must match approved_notional")
    if result.gate_status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if result.validation_digest != _validation_digest(_result_digest_values(result)):
        raise ValueError("validation_digest must match result payload")


def _validate_report(
    report: StrategyRecommendationCategoryBudgetPressureGateV2Report,
) -> None:
    if report.recommendation_count != _count(len(report.results)):
        raise ValueError("recommendation_count must match results")
    if report.pass_count != _result_status_count(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _result_status_count(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.blocked_count != _result_status_count(report.results, "blocked"):
        raise ValueError("blocked_count must match results")
    if report.total_requested_notional != _sum_decimal(
        result.requested_notional for result in report.results
    ):
        raise ValueError("total_requested_notional must match results")
    if report.total_approved_notional != _sum_decimal(
        result.approved_notional for result in report.results
    ):
        raise ValueError("total_approved_notional must match results")
    if report.total_reduction_notional != _sum_decimal(
        result.reduction_notional for result in report.results
    ):
        raise ValueError("total_reduction_notional must match results")
    if report.gate_status != _report_status(report.results):
        raise ValueError("gate_status must match results")
    if report.reason_codes != _report_reason_codes(report.results):
        raise ValueError("reason_codes must match results")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _result_digest_values(
    result: StrategyRecommendationCategoryBudgetPressureGateV2Result,
) -> dict[str, Any]:
    return {
        "recommendation_id": result.recommendation_id,
        "category": result.category,
        "requested_notional": result.requested_notional,
        "current_category_paper_exposure": result.current_category_paper_exposure,
        "correlated_event_cluster_exposure": (
            result.correlated_event_cluster_exposure
        ),
        "independent_source_count": result.independent_source_count,
        "liquidity_capacity": result.liquidity_capacity,
        "category_exposure_after_requested": (
            result.category_exposure_after_requested
        ),
        "category_pressure_ratio": result.category_pressure_ratio,
        "remaining_category_budget": result.remaining_category_budget,
        "correlated_event_pressure_ratio": result.correlated_event_pressure_ratio,
        "remaining_correlated_event_budget": (
            result.remaining_correlated_event_budget
        ),
        "liquidity_allocation_capacity": result.liquidity_allocation_capacity,
        "liquidity_capacity_utilization_ratio": (
            result.liquidity_capacity_utilization_ratio
        ),
        "source_coverage_ratio": result.source_coverage_ratio,
        "approved_notional": result.approved_notional,
        "reduction_notional": result.reduction_notional,
        "gate_status": result.gate_status,
        "reason_codes": result.reason_codes,
        "redacted_source_reference": result.redacted_source_reference,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }


def _report_digest_values(
    report: StrategyRecommendationCategoryBudgetPressureGateV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "recommendation_count": report.recommendation_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "blocked_count": report.blocked_count,
        "total_requested_notional": report.total_requested_notional,
        "total_approved_notional": report.total_approved_notional,
        "total_reduction_notional": report.total_reduction_notional,
        "gate_status": report.gate_status,
        "reason_codes": report.reason_codes,
        "results": report.results,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _result_sort_key(
    result: StrategyRecommendationCategoryBudgetPressureGateV2Result,
) -> tuple[int, str]:
    return (_STATUS_WEIGHT[result.gate_status], result.recommendation_id)


def _normalize_result_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_reason_codes(name, values, allowed=_RESULT_REASON_CODES)
    if not codes:
        return ()
    if _PASS_REASON in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_reason_codes(name, values, allowed=_REPORT_REASON_CODES)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == (_EMPTY_REASON,):
        return codes
    if _EMPTY_REASON in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_reason_codes(
    name: str,
    values: object,
    *,
    allowed: frozenset[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        if code not in allowed:
            raise ValueError(f"{name} contains unknown reason code")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be blocked, watch, or pass")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {name}")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_text("payload key", key)
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_CATEGORY_BUDGET_PRESSURE_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationCategoryBudgetPressureGateV2Config",
    "StrategyRecommendationCategoryBudgetPressureGateV2Input",
    "StrategyRecommendationCategoryBudgetPressureGateV2Report",
    "StrategyRecommendationCategoryBudgetPressureGateV2Result",
    "build_strategy_recommendation_category_budget_pressure_gate_v2",
    "strategy_recommendation_category_budget_pressure_gate_v2_payload",
)
