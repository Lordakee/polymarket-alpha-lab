"""Pure Phase 1 strategy recommendation and research quality join."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_QUALITY_JOIN_V2_CONFIG_VERSION = (
    "strategy-recommendation-research-quality-join-v2"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("blocked", "watch", "pass", "empty")
_ROW_STATUSES = ("blocked", "watch", "pass")
_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")
_BLOCK_REASONS = frozenset(
    (
        "research_quality_blocked",
        "counterevidence_quorum_blocked",
        "source_authority_low",
        "source_freshness_stale",
    ),
)
_PASS_REASONS = frozenset(("research_quality_join_pass",))
_EMPTY_REASON = "strategy_recommendation_research_quality_join_v2_empty"
_REASON_PRIORITY = (
    "research_quality_blocked",
    "research_quality_watch",
    "counterevidence_quorum_blocked",
    "counterevidence_quorum_watch",
    "source_authority_low",
    "source_freshness_stale",
    "source_authority_watch",
    "source_freshness_watch",
    "research_quality_join_pass",
    _EMPTY_REASON,
)
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_UNSAFE_TEXT_FRAGMENTS = (
    "sec" "ret",
    "tok" "en",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "au" "thorization",
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
_UNSAFE_PAYLOAD_KEYS = (
    "sec" "ret",
    "tok" "en",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "au" "thorization",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "live" "_" "trading",
    "live" " trading",
    "data" "base",
    "db" "_" "write",
    "db" " write",
    "net" "work",
)


@dataclass(frozen=True)
class StrategyRecommendationResearchQualityJoinV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_QUALITY_JOIN_V2_CONFIG_VERSION
    )
    min_research_quality_score: Decimal = Decimal("0.650000")
    watch_research_quality_score: Decimal = Decimal("0.800000")
    min_counterevidence_quorum_ratio: Decimal = Decimal("0.500000")
    watch_counterevidence_quorum_ratio: Decimal = Decimal("0.750000")
    min_source_authority_score: Decimal = Decimal("0.500000")
    min_source_freshness_score: Decimal = Decimal("0.550000")
    watch_source_authority_score: Decimal = Decimal("0.700000")
    watch_source_freshness_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "min_research_quality_score",
            "watch_research_quality_score",
            "min_counterevidence_quorum_ratio",
            "watch_counterevidence_quorum_ratio",
            "min_source_authority_score",
            "min_source_freshness_score",
            "watch_source_authority_score",
            "watch_source_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_research_quality_score > self.watch_research_quality_score:
            raise ValueError("minimum quality threshold must not exceed watch threshold")
        if (
            self.min_counterevidence_quorum_ratio
            > self.watch_counterevidence_quorum_ratio
        ):
            raise ValueError(
                "minimum counterevidence threshold must not exceed watch threshold",
            )
        if self.min_source_authority_score > self.watch_source_authority_score:
            raise ValueError("minimum authority threshold must not exceed watch threshold")
        if self.min_source_freshness_score > self.watch_source_freshness_score:
            raise ValueError("minimum freshness threshold must not exceed watch threshold")
        require_paper_only_flags("research quality join config", self)


@dataclass(frozen=True)
class StrategyRecommendationResearchQualityJoinV2Input:
    recommendation_id: str
    candidate_id: str
    market_id: str
    event_slug: str
    category: str
    net_edge: Decimal
    research_quality_score: Decimal
    counterevidence_quorum_ratio: Decimal
    source_authority_score: Decimal
    source_freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "market_id",
            "event_slug",
            "category",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "net_edge",
            _normalize_nonnegative_decimal("net_edge", self.net_edge),
        )
        for field_name in (
            "research_quality_score",
            "counterevidence_quorum_ratio",
            "source_authority_score",
            "source_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("research quality join input", self)


@dataclass(frozen=True)
class StrategyRecommendationResearchQualityJoinV2Result:
    recommendation_id: str
    candidate_id: str
    market_id: str
    event_slug: str
    category: str
    net_edge: Decimal
    research_quality_score: Decimal
    counterevidence_quorum_ratio: Decimal
    source_authority_score: Decimal
    source_freshness_score: Decimal
    quality_adjusted_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "market_id",
            "event_slug",
            "category",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "net_edge",
            _normalize_nonnegative_decimal("net_edge", self.net_edge),
        )
        for field_name in (
            "research_quality_score",
            "counterevidence_quorum_ratio",
            "source_authority_score",
            "source_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quality_adjusted_edge",
            _normalize_nonnegative_decimal(
                "quality_adjusted_edge",
                self.quality_adjusted_edge,
            ),
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_result_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_result(self)
        require_paper_only_flags("research quality join result", self)


@dataclass(frozen=True)
class StrategyRecommendationResearchQualityJoinV2Report:
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    low_quality_count: Decimal
    weak_counterevidence_count: Decimal
    stale_or_low_authority_count: Decimal
    max_quality_adjusted_edge: Decimal
    report_status: str
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    results: tuple[StrategyRecommendationResearchQualityJoinV2Result, ...]
    derived_validation_digest: str
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
            "low_quality_count",
            "weak_counterevidence_count",
            "stale_or_low_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_quality_adjusted_edge",
            _normalize_nonnegative_decimal(
                "max_quality_adjusted_edge",
                self.max_quality_adjusted_edge,
            ),
        )
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        require_paper_only_flags("research quality join report", self)


def build_strategy_recommendation_research_quality_join_v2_report(
    recommendations: Iterable[StrategyRecommendationResearchQualityJoinV2Input],
    *,
    config: StrategyRecommendationResearchQualityJoinV2Config,
    generated_at: datetime,
) -> StrategyRecommendationResearchQualityJoinV2Report:
    if type(config) is not StrategyRecommendationResearchQualityJoinV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationResearchQualityJoinV2Config",
        )
    require_paper_only_flags("research quality join config", config)
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
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "recommendation_count": _count(len(results)),
        "pass_count": _result_status_count(results, "pass"),
        "watch_count": _result_status_count(results, "watch"),
        "blocked_count": _result_status_count(results, "blocked"),
        "low_quality_count": _count(
            sum(
                1
                for result in results
                if result.research_quality_score < config.watch_research_quality_score
            ),
        ),
        "weak_counterevidence_count": _count(
            sum(
                1
                for result in results
                if result.counterevidence_quorum_ratio
                < config.watch_counterevidence_quorum_ratio
            ),
        ),
        "stale_or_low_authority_count": _count(
            sum(
                1
                for result in results
                if result.source_authority_score < config.watch_source_authority_score
                or result.source_freshness_score < config.watch_source_freshness_score
            ),
        ),
        "max_quality_adjusted_edge": _max_quality_adjusted_edge(results),
        "report_status": _report_status(results),
        "reason_code_counts": _reason_code_counts(results),
        "results": results,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationResearchQualityJoinV2Report(
        **report_values,
        derived_validation_digest=_validation_digest(report_values),
    )


def strategy_recommendation_research_quality_join_v2_payload(
    report: StrategyRecommendationResearchQualityJoinV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationResearchQualityJoinV2Report:
        require_paper_only_flags("research quality join report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyRecommendationResearchQualityJoinV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    _reject_numeric_payload_values(payload)
    require_paper_only_flags("research quality join payload", _PayloadFlags(payload))
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
    recommendations: Iterable[StrategyRecommendationResearchQualityJoinV2Input],
) -> tuple[StrategyRecommendationResearchQualityJoinV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationResearchQualityJoinV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationResearchQualityJoinV2Input",
            )
        require_paper_only_flags("research quality join input", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendation_id values must be unique")
        seen.add(item.recommendation_id)
    return items


def _result_from_recommendation(
    recommendation: StrategyRecommendationResearchQualityJoinV2Input,
    *,
    config: StrategyRecommendationResearchQualityJoinV2Config,
) -> StrategyRecommendationResearchQualityJoinV2Result:
    reason_codes = _result_reason_codes(recommendation, config)
    result_values = {
        "recommendation_id": recommendation.recommendation_id,
        "candidate_id": recommendation.candidate_id,
        "market_id": recommendation.market_id,
        "event_slug": recommendation.event_slug,
        "category": recommendation.category,
        "net_edge": recommendation.net_edge,
        "research_quality_score": recommendation.research_quality_score,
        "counterevidence_quorum_ratio": recommendation.counterevidence_quorum_ratio,
        "source_authority_score": recommendation.source_authority_score,
        "source_freshness_score": recommendation.source_freshness_score,
        "quality_adjusted_edge": _quality_adjusted_edge(recommendation),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationResearchQualityJoinV2Result(
        **result_values,
        derived_validation_digest=_validation_digest(result_values),
    )


def _result_reason_codes(
    recommendation: StrategyRecommendationResearchQualityJoinV2Input,
    config: StrategyRecommendationResearchQualityJoinV2Config,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if recommendation.research_quality_score < config.min_research_quality_score:
        block_reasons.append("research_quality_blocked")
    elif recommendation.research_quality_score < config.watch_research_quality_score:
        watch_reasons.append("research_quality_watch")
    if (
        recommendation.counterevidence_quorum_ratio
        < config.min_counterevidence_quorum_ratio
    ):
        block_reasons.append("counterevidence_quorum_blocked")
    elif (
        recommendation.counterevidence_quorum_ratio
        < config.watch_counterevidence_quorum_ratio
    ):
        watch_reasons.append("counterevidence_quorum_watch")
    if recommendation.source_authority_score < config.min_source_authority_score:
        block_reasons.append("source_authority_low")
    elif recommendation.source_authority_score < config.watch_source_authority_score:
        watch_reasons.append("source_authority_watch")
    if recommendation.source_freshness_score < config.min_source_freshness_score:
        block_reasons.append("source_freshness_stale")
    elif recommendation.source_freshness_score < config.watch_source_freshness_score:
        watch_reasons.append("source_freshness_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("research_quality_join_pass",)
    return _normalize_result_reason_codes("reason_codes", reasons)


def _quality_adjusted_edge(
    recommendation: StrategyRecommendationResearchQualityJoinV2Input,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            recommendation.net_edge
            * recommendation.research_quality_score
            * recommendation.counterevidence_quorum_ratio
            * recommendation.source_authority_score
            * recommendation.source_freshness_score,
        )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "blocked"
    if reason_codes == ("research_quality_join_pass",):
        return "pass"
    return "watch"


def _report_status(
    results: tuple[StrategyRecommendationResearchQualityJoinV2Result, ...],
) -> str:
    if not results:
        return "empty"
    if any(result.status == "blocked" for result in results):
        return "blocked"
    if any(result.status == "watch" for result in results):
        return "watch"
    return "pass"


def _result_status_count(
    results: tuple[StrategyRecommendationResearchQualityJoinV2Result, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for result in results if result.status == status))


def _max_quality_adjusted_edge(
    results: tuple[StrategyRecommendationResearchQualityJoinV2Result, ...],
) -> Decimal:
    if not results:
        return _ZERO
    return max(result.quality_adjusted_edge for result in results)


def _reason_code_counts(
    results: tuple[StrategyRecommendationResearchQualityJoinV2Result, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for result in results:
        for reason_code in result.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(counts[reason_code]))
        for reason_code in sorted(counts, key=_reason_sort_key)
    )


def _normalize_results(
    results: object,
) -> tuple[StrategyRecommendationResearchQualityJoinV2Result, ...]:
    if isinstance(results, (str, bytes)):
        raise ValueError("results must be an iterable")
    try:
        normalized = tuple(results)
    except TypeError as exc:
        raise ValueError("results must be an iterable") from exc
    for result in normalized:
        if type(result) is not StrategyRecommendationResearchQualityJoinV2Result:
            raise ValueError(
                "results must contain StrategyRecommendationResearchQualityJoinV2Result",
            )
        require_paper_only_flags("research quality join result", result)
    if normalized != tuple(sorted(normalized, key=_result_sort_key)):
        raise ValueError("results must be sorted deterministically")
    return normalized


def _validate_result(result: StrategyRecommendationResearchQualityJoinV2Result) -> None:
    expected_edge = _quality_adjusted_edge(
        StrategyRecommendationResearchQualityJoinV2Input(
            recommendation_id=result.recommendation_id,
            candidate_id=result.candidate_id,
            market_id=result.market_id,
            event_slug=result.event_slug,
            category=result.category,
            net_edge=result.net_edge,
            research_quality_score=result.research_quality_score,
            counterevidence_quorum_ratio=result.counterevidence_quorum_ratio,
            source_authority_score=result.source_authority_score,
            source_freshness_score=result.source_freshness_score,
        ),
    )
    if result.quality_adjusted_edge != expected_edge:
        raise ValueError("quality_adjusted_edge must match input scores")
    if result.status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("status must match reason_codes")
    if result.derived_validation_digest != _validation_digest(_result_digest_values(result)):
        raise ValueError("derived_validation_digest must match result payload")


def _validate_report(report: StrategyRecommendationResearchQualityJoinV2Report) -> None:
    if report.recommendation_count != _count(len(report.results)):
        raise ValueError("recommendation_count must match results")
    if report.pass_count != _result_status_count(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _result_status_count(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.blocked_count != _result_status_count(report.results, "blocked"):
        raise ValueError("blocked_count must match results")
    if report.max_quality_adjusted_edge != _max_quality_adjusted_edge(report.results):
        raise ValueError("max_quality_adjusted_edge must match results")
    if report.report_status != _report_status(report.results):
        raise ValueError("report_status must match results")
    if report.reason_code_counts != _reason_code_counts(report.results):
        raise ValueError("reason_code_counts must match results")
    if report.derived_validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("derived_validation_digest must match report payload")


def _result_digest_values(
    result: StrategyRecommendationResearchQualityJoinV2Result,
) -> dict[str, Any]:
    return {
        "recommendation_id": result.recommendation_id,
        "candidate_id": result.candidate_id,
        "market_id": result.market_id,
        "event_slug": result.event_slug,
        "category": result.category,
        "net_edge": result.net_edge,
        "research_quality_score": result.research_quality_score,
        "counterevidence_quorum_ratio": result.counterevidence_quorum_ratio,
        "source_authority_score": result.source_authority_score,
        "source_freshness_score": result.source_freshness_score,
        "quality_adjusted_edge": result.quality_adjusted_edge,
        "status": result.status,
        "reason_codes": result.reason_codes,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }


def _report_digest_values(
    report: StrategyRecommendationResearchQualityJoinV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "recommendation_count": report.recommendation_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "blocked_count": report.blocked_count,
        "low_quality_count": report.low_quality_count,
        "weak_counterevidence_count": report.weak_counterevidence_count,
        "stale_or_low_authority_count": report.stale_or_low_authority_count,
        "max_quality_adjusted_edge": report.max_quality_adjusted_edge,
        "report_status": report.report_status,
        "reason_code_counts": report.reason_code_counts,
        "results": report.results,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _result_sort_key(
    result: StrategyRecommendationResearchQualityJoinV2Result,
) -> tuple[int, Decimal, str, str]:
    return (
        _STATUS_WEIGHT[result.status],
        result.quality_adjusted_edge,
        result.recommendation_id,
        result.candidate_id,
    )


def _normalize_result_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if "research_quality_join_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if codes == ("research_quality_join_pass",):
        return codes
    if any(code in _PASS_REASONS for code in codes):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_reason_code_counts(values: object) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        pairs = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code, count = pair
        _require_public_text("reason_code_counts", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reasons")
        seen.add(reason_code)
        normalized.append(
            (reason_code, _normalize_nonnegative_count("reason_code_counts", count)),
        )
    result = tuple(sorted(normalized, key=lambda item: _reason_sort_key(item[0])))
    if result != tuple(normalized):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return result


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


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


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


def _require_row_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _ROW_STATUSES:
        raise ValueError(f"{name} must be blocked, watch, or pass")


def _require_report_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be blocked, watch, pass, or empty")


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
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("numeric JSON values must be encoded as Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: object) -> None:
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in _UNSAFE_PAYLOAD_KEYS):
            raise ValueError("unsafe live surface value in payload")
        return
    for key in _payload_keys(value):
        normalized = key.lower()
        if any(fragment in normalized for fragment in _UNSAFE_PAYLOAD_KEYS):
            raise ValueError(f"unsafe live surface field in payload: {key}")
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)


def _payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_payload_keys(item))
        return tuple(keys)
    return ()


def _reject_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("numeric JSON values must be encoded as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_numeric_payload_values(item)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_QUALITY_JOIN_V2_CONFIG_VERSION",
    "StrategyRecommendationResearchQualityJoinV2Config",
    "StrategyRecommendationResearchQualityJoinV2Input",
    "StrategyRecommendationResearchQualityJoinV2Report",
    "StrategyRecommendationResearchQualityJoinV2Result",
    "build_strategy_recommendation_research_quality_join_v2_report",
    "strategy_recommendation_research_quality_join_v2_payload",
)
