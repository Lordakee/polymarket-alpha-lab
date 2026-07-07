"""Pure Phase 1 information quality gate."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_RECOMMENDATION_INFORMATION_QUALITY_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-information-quality-gate-v2"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIVE = Decimal("5.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_REDACTED_SOURCE_REFERENCE = "<redacted>"
_STATUSES = ("blocked", "watch", "pass")
_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_HEX_CHARS = frozenset("0123456789abcdef")
_BLOCK_REASONS = frozenset(
    (
        "source_coverage_blocked",
        "primary_source_missing",
        "source_recency_blocked",
        "contradiction_severity_blocked",
        "resolution_rule_specificity_blocked",
        "market_close_urgency_blocked",
    ),
)
_PASS_REASONS = frozenset(("information_quality_gate_pass",))
_REASON_PRIORITY = (
    "source_coverage_blocked",
    "source_coverage_weak",
    "primary_source_missing",
    "source_recency_blocked",
    "source_recency_stale",
    "contradiction_severity_blocked",
    "contradiction_severity_watch",
    "resolution_rule_specificity_blocked",
    "resolution_rule_specificity_watch",
    "market_close_urgency_blocked",
    "market_close_urgency_watch",
    "information_quality_gate_pass",
    "strategy_recommendation_information_quality_gate_v2_empty",
)
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
    "live" " trading",
    "data" "base",
    "db" " write",
    "net" "work",
    "://",
)


@dataclass(frozen=True)
class StrategyRecommendationInformationQualityGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_INFORMATION_QUALITY_GATE_V2_CONFIG_VERSION
    )
    min_source_count: Decimal = Decimal("3")
    source_count_pass_floor: Decimal = Decimal("4")
    min_primary_source_count: Decimal = Decimal("1")
    source_recency_pass_minutes: Decimal = Decimal("60.000000")
    max_source_age_minutes: Decimal = Decimal("180.000000")
    contradiction_severity_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_severity_block_threshold: Decimal = Decimal("0.600000")
    resolution_rule_specificity_block_threshold: Decimal = Decimal("0.400000")
    resolution_rule_specificity_pass_threshold: Decimal = Decimal("0.750000")
    market_close_urgency_minutes: Decimal = Decimal("45.000000")
    urgent_source_count_pass_floor: Decimal = Decimal("5")
    urgent_source_recency_pass_minutes: Decimal = Decimal("30.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "min_source_count",
            "source_count_pass_floor",
            "min_primary_source_count",
            "urgent_source_count_pass_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_recency_pass_minutes",
            "max_source_age_minutes",
            "market_close_urgency_minutes",
            "urgent_source_recency_pass_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_severity_watch_threshold",
            "contradiction_severity_block_threshold",
            "resolution_rule_specificity_block_threshold",
            "resolution_rule_specificity_pass_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_source_count > self.source_count_pass_floor:
            raise ValueError("min_source_count must not exceed source_count_pass_floor")
        if self.min_primary_source_count > self.source_count_pass_floor:
            raise ValueError(
                "min_primary_source_count must not exceed source_count_pass_floor",
            )
        if self.source_recency_pass_minutes > self.max_source_age_minutes:
            raise ValueError(
                "source_recency_pass_minutes must not exceed max_source_age_minutes",
            )
        if (
            self.contradiction_severity_watch_threshold
            > self.contradiction_severity_block_threshold
        ):
            raise ValueError(
                "contradiction watch threshold must not exceed block threshold",
            )
        if (
            self.resolution_rule_specificity_block_threshold
            > self.resolution_rule_specificity_pass_threshold
        ):
            raise ValueError(
                "resolution block threshold must not exceed pass threshold",
            )
        if self.urgent_source_count_pass_floor < self.source_count_pass_floor:
            raise ValueError(
                "urgent_source_count_pass_floor must not be below source_count_pass_floor",
            )
        if self.urgent_source_recency_pass_minutes > self.source_recency_pass_minutes:
            raise ValueError(
                "urgent_source_recency_pass_minutes must not exceed "
                "source_recency_pass_minutes",
            )
        require_paper_only_flags("information quality config", self)


@dataclass(frozen=True)
class StrategyRecommendationInformationQualityGateV2Input:
    recommendation_id: str
    market_slug: str
    source_count: Decimal
    primary_source_count: Decimal
    latest_source_age_minutes: Decimal
    contradiction_severity: Decimal
    resolution_rule_specificity: Decimal
    minutes_until_market_close: Decimal
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("recommendation_id", self.recommendation_id)
        _require_public_text("market_slug", self.market_slug)
        for field_name in ("source_count", "primary_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.primary_source_count > self.source_count:
            raise ValueError("primary_source_count must not exceed source_count")
        for field_name in ("latest_source_age_minutes", "minutes_until_market_close"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("contradiction_severity", "resolution_rule_specificity"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_text("source_reference", self.source_reference)
        require_paper_only_flags("information quality input", self)


@dataclass(frozen=True)
class StrategyRecommendationInformationQualityGateV2Result:
    recommendation_id: str
    market_slug: str
    source_count: Decimal
    primary_source_count: Decimal
    latest_source_age_minutes: Decimal
    contradiction_severity: Decimal
    resolution_rule_specificity: Decimal
    minutes_until_market_close: Decimal
    source_coverage_ratio: Decimal
    primary_source_ratio: Decimal
    source_recency_score: Decimal
    contradiction_score: Decimal
    information_quality_score: Decimal
    market_close_urgent: bool
    gate_status: str
    reason_codes: tuple[str, ...]
    redacted_source_reference: str
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("recommendation_id", self.recommendation_id)
        _require_public_text("market_slug", self.market_slug)
        for field_name in ("source_count", "primary_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.primary_source_count > self.source_count:
            raise ValueError("primary_source_count must not exceed source_count")
        for field_name in ("latest_source_age_minutes", "minutes_until_market_close"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_severity",
            "resolution_rule_specificity",
            "source_coverage_ratio",
            "primary_source_ratio",
            "source_recency_score",
            "contradiction_score",
            "information_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.market_close_urgent) is not bool:
            raise ValueError("market_close_urgent must be a bool")
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_result_reason_codes("reason_codes", self.reason_codes),
        )
        if self.redacted_source_reference != _REDACTED_SOURCE_REFERENCE:
            raise ValueError("redacted_source_reference must be redacted")
        _require_digest("validation_digest", self.validation_digest)
        _validate_result(self)
        require_paper_only_flags("information quality result", self)


@dataclass(frozen=True)
class StrategyRecommendationInformationQualityGateV2Report:
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_information_quality_score: Decimal | None
    gate_status: str
    reason_codes: tuple[str, ...]
    results: tuple[StrategyRecommendationInformationQualityGateV2Result, ...]
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
        if self.min_information_quality_score is not None:
            object.__setattr__(
                self,
                "min_information_quality_score",
                _normalize_unit_decimal(
                    "min_information_quality_score",
                    self.min_information_quality_score,
                ),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        require_paper_only_flags("information quality report", self)


def build_strategy_recommendation_information_quality_gate_v2(
    recommendations: Iterable[StrategyRecommendationInformationQualityGateV2Input],
    *,
    config: StrategyRecommendationInformationQualityGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationInformationQualityGateV2Report:
    if type(config) is not StrategyRecommendationInformationQualityGateV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationInformationQualityGateV2Config",
        )
    require_paper_only_flags("information quality config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_recommendations = _normalize_recommendations(recommendations)
    results = tuple(
        sorted(
            (
                _result_from_recommendation(recommendation, config=config)
                for recommendation in normalized_recommendations
            ),
            key=_result_sort_key,
        ),
    )
    recommendation_count = _count(len(results))
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "recommendation_count": recommendation_count,
        "pass_count": _result_status_count(results, "pass"),
        "watch_count": _result_status_count(results, "watch"),
        "blocked_count": _result_status_count(results, "blocked"),
        "min_information_quality_score": (
            None if not results else min(result.information_quality_score for result in results)
        ),
        "gate_status": _report_status(results),
        "reason_codes": _report_reason_codes(results),
        "results": results,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationInformationQualityGateV2Report(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def strategy_recommendation_information_quality_gate_v2_payload(
    report: StrategyRecommendationInformationQualityGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationInformationQualityGateV2Report:
        require_paper_only_flags("information quality report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyRecommendationInformationQualityGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags("information quality payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _normalize_recommendations(
    recommendations: Iterable[StrategyRecommendationInformationQualityGateV2Input],
) -> tuple[StrategyRecommendationInformationQualityGateV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationInformationQualityGateV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationInformationQualityGateV2Input",
            )
        require_paper_only_flags("information quality input", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendation_id values must be unique")
        seen.add(item.recommendation_id)
    return items


def _result_from_recommendation(
    recommendation: StrategyRecommendationInformationQualityGateV2Input,
    *,
    config: StrategyRecommendationInformationQualityGateV2Config,
) -> StrategyRecommendationInformationQualityGateV2Result:
    source_coverage_ratio = _capped_ratio(
        recommendation.source_count,
        config.source_count_pass_floor,
    )
    primary_source_ratio = _capped_ratio(
        recommendation.primary_source_count,
        config.min_primary_source_count,
    )
    source_recency_score = _source_recency_score(
        recommendation.latest_source_age_minutes,
        config.max_source_age_minutes,
    )
    contradiction_score = _quantize(_ONE - recommendation.contradiction_severity)
    reason_codes = _result_reason_codes(recommendation, config)
    component_values = (
        source_coverage_ratio,
        primary_source_ratio,
        source_recency_score,
        contradiction_score,
        recommendation.resolution_rule_specificity,
    )
    result_values = {
        "recommendation_id": recommendation.recommendation_id,
        "market_slug": recommendation.market_slug,
        "source_count": recommendation.source_count,
        "primary_source_count": recommendation.primary_source_count,
        "latest_source_age_minutes": recommendation.latest_source_age_minutes,
        "contradiction_severity": recommendation.contradiction_severity,
        "resolution_rule_specificity": recommendation.resolution_rule_specificity,
        "minutes_until_market_close": recommendation.minutes_until_market_close,
        "source_coverage_ratio": source_coverage_ratio,
        "primary_source_ratio": primary_source_ratio,
        "source_recency_score": source_recency_score,
        "contradiction_score": contradiction_score,
        "information_quality_score": _information_quality_score(component_values),
        "market_close_urgent": _is_market_close_urgent(recommendation, config),
        "gate_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "redacted_source_reference": _REDACTED_SOURCE_REFERENCE,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationInformationQualityGateV2Result(
        **result_values,
        validation_digest=_validation_digest(result_values),
    )


def _result_reason_codes(
    recommendation: StrategyRecommendationInformationQualityGateV2Input,
    config: StrategyRecommendationInformationQualityGateV2Config,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if recommendation.source_count < config.min_source_count:
        block_reasons.append("source_coverage_blocked")
    elif recommendation.source_count < config.source_count_pass_floor:
        watch_reasons.append("source_coverage_weak")
    if recommendation.primary_source_count < config.min_primary_source_count:
        block_reasons.append("primary_source_missing")
    if recommendation.latest_source_age_minutes > config.max_source_age_minutes:
        block_reasons.append("source_recency_blocked")
    elif recommendation.latest_source_age_minutes > config.source_recency_pass_minutes:
        watch_reasons.append("source_recency_stale")
    if (
        recommendation.contradiction_severity
        >= config.contradiction_severity_block_threshold
    ):
        block_reasons.append("contradiction_severity_blocked")
    elif (
        recommendation.contradiction_severity
        >= config.contradiction_severity_watch_threshold
    ):
        watch_reasons.append("contradiction_severity_watch")
    if (
        recommendation.resolution_rule_specificity
        < config.resolution_rule_specificity_block_threshold
    ):
        block_reasons.append("resolution_rule_specificity_blocked")
    elif (
        recommendation.resolution_rule_specificity
        < config.resolution_rule_specificity_pass_threshold
    ):
        watch_reasons.append("resolution_rule_specificity_watch")
    if _is_market_close_urgent(recommendation, config):
        if block_reasons:
            block_reasons.append("market_close_urgency_blocked")
        elif (
            recommendation.source_count < config.urgent_source_count_pass_floor
            or recommendation.latest_source_age_minutes
            > config.urgent_source_recency_pass_minutes
        ):
            watch_reasons.append("market_close_urgency_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("information_quality_gate_pass",)
    return _normalize_result_reason_codes("reason_codes", reasons)


def _is_market_close_urgent(
    recommendation: StrategyRecommendationInformationQualityGateV2Input,
    config: StrategyRecommendationInformationQualityGateV2Config,
) -> bool:
    return recommendation.minutes_until_market_close <= config.market_close_urgency_minutes


def _source_recency_score(source_age: Decimal, max_source_age: Decimal) -> Decimal:
    score = _ONE - _ratio(source_age, max_source_age)
    if score < _ZERO:
        return _ZERO
    if score > _ONE:
        return _ONE
    return _quantize(score)


def _information_quality_score(component_values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(component_values), _FIVE)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "blocked"
    if reason_codes == ("information_quality_gate_pass",):
        return "pass"
    return "watch"


def _report_status(
    results: tuple[StrategyRecommendationInformationQualityGateV2Result, ...],
) -> str:
    if not results:
        return "blocked"
    if any(result.gate_status == "blocked" for result in results):
        return "blocked"
    if any(result.gate_status == "watch" for result in results):
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[StrategyRecommendationInformationQualityGateV2Result, ...],
) -> tuple[str, ...]:
    if not results:
        return ("strategy_recommendation_information_quality_gate_v2_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for result in results for reason in result.reason_codes),
    )


def _result_status_count(
    results: tuple[StrategyRecommendationInformationQualityGateV2Result, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for result in results if result.gate_status == status))


def _normalize_results(
    results: object,
) -> tuple[StrategyRecommendationInformationQualityGateV2Result, ...]:
    if isinstance(results, (str, bytes)):
        raise ValueError("results must be an iterable")
    try:
        normalized = tuple(results)
    except TypeError as exc:
        raise ValueError("results must be an iterable") from exc
    for result in normalized:
        if type(result) is not StrategyRecommendationInformationQualityGateV2Result:
            raise ValueError(
                "results must contain StrategyRecommendationInformationQualityGateV2Result",
            )
        require_paper_only_flags("information quality result", result)
    if normalized != tuple(sorted(normalized, key=_result_sort_key)):
        raise ValueError("results must be sorted deterministically")
    return normalized


def _validate_result(result: StrategyRecommendationInformationQualityGateV2Result) -> None:
    expected_score = _information_quality_score(
        (
            result.source_coverage_ratio,
            result.primary_source_ratio,
            result.source_recency_score,
            result.contradiction_score,
            result.resolution_rule_specificity,
        ),
    )
    if result.information_quality_score != expected_score:
        raise ValueError("information_quality_score must match component scores")
    if result.gate_status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if result.validation_digest != _validation_digest(_result_digest_values(result)):
        raise ValueError("validation_digest must match result payload")


def _validate_report(report: StrategyRecommendationInformationQualityGateV2Report) -> None:
    if report.recommendation_count != _count(len(report.results)):
        raise ValueError("recommendation_count must match results")
    if report.pass_count != _result_status_count(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _result_status_count(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.blocked_count != _result_status_count(report.results, "blocked"):
        raise ValueError("blocked_count must match results")
    expected_min = (
        None
        if not report.results
        else min(result.information_quality_score for result in report.results)
    )
    if report.min_information_quality_score != expected_min:
        raise ValueError("min_information_quality_score must match results")
    if report.gate_status != _report_status(report.results):
        raise ValueError("gate_status must match results")
    if report.reason_codes != _report_reason_codes(report.results):
        raise ValueError("reason_codes must match results")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _result_digest_values(
    result: StrategyRecommendationInformationQualityGateV2Result,
) -> dict[str, Any]:
    return {
        "recommendation_id": result.recommendation_id,
        "market_slug": result.market_slug,
        "source_count": result.source_count,
        "primary_source_count": result.primary_source_count,
        "latest_source_age_minutes": result.latest_source_age_minutes,
        "contradiction_severity": result.contradiction_severity,
        "resolution_rule_specificity": result.resolution_rule_specificity,
        "minutes_until_market_close": result.minutes_until_market_close,
        "source_coverage_ratio": result.source_coverage_ratio,
        "primary_source_ratio": result.primary_source_ratio,
        "source_recency_score": result.source_recency_score,
        "contradiction_score": result.contradiction_score,
        "information_quality_score": result.information_quality_score,
        "market_close_urgent": result.market_close_urgent,
        "gate_status": result.gate_status,
        "reason_codes": result.reason_codes,
        "redacted_source_reference": result.redacted_source_reference,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }


def _report_digest_values(
    report: StrategyRecommendationInformationQualityGateV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "recommendation_count": report.recommendation_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "blocked_count": report.blocked_count,
        "min_information_quality_score": report.min_information_quality_score,
        "gate_status": report.gate_status,
        "reason_codes": report.reason_codes,
        "results": report.results,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _result_sort_key(
    result: StrategyRecommendationInformationQualityGateV2Result,
) -> tuple[int, Decimal, str]:
    return (
        _STATUS_WEIGHT[result.gate_status],
        result.information_quality_score,
        result.recommendation_id,
    )


def _normalize_result_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if "information_quality_gate_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if codes == ("information_quality_gate_pass",):
        return codes
    if any(code in _PASS_REASONS for code in codes):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("strategy_recommendation_information_quality_gate_v2_empty",):
        return codes
    if "strategy_recommendation_information_quality_gate_v2_empty" in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
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


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
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
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
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
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_INFORMATION_QUALITY_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationInformationQualityGateV2Config",
    "StrategyRecommendationInformationQualityGateV2Input",
    "StrategyRecommendationInformationQualityGateV2Report",
    "StrategyRecommendationInformationQualityGateV2Result",
    "build_strategy_recommendation_information_quality_gate_v2",
    "strategy_recommendation_information_quality_gate_v2_payload",
)
