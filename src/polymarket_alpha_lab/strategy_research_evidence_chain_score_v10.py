"""Paper-only evidence-chain scoring for strategy research v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RESEARCH_EVIDENCE_CHAIN_SCORE_V10_CONFIG_VERSION = (
    "strategy-research-evidence-chain-score-v10"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EVIDENCE_CHAIN_STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "evidence_chain_passed",
    "insufficient_evidence_items",
    "insufficient_independent_sources",
    "missing_primary_source",
    "source_contradictions_present",
    "low_average_source_reliability",
    "stale_evidence_freshness",
    "weak_resolution_alignment",
    "evidence_chain_watch_score",
    "evidence_chain_blocked_score",
)


@dataclass(frozen=True)
class StrategyResearchEvidenceChainScoreV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_RESEARCH_EVIDENCE_CHAIN_SCORE_V10_CONFIG_VERSION
    )
    minimum_evidence_item_count: Decimal = Decimal("3")
    minimum_independent_source_count: Decimal = Decimal("2")
    minimum_primary_source_count: Decimal = Decimal("1")
    maximum_contradiction_count: Decimal = Decimal("0")
    minimum_average_source_reliability: Decimal = Decimal("0.650000")
    minimum_freshness_weight: Decimal = Decimal("0.600000")
    minimum_resolution_alignment_score: Decimal = Decimal("0.700000")
    pass_score_threshold: Decimal = Decimal("0.750000")
    watch_score_threshold: Decimal = Decimal("0.500000")
    evidence_item_weight: Decimal = Decimal("0.200000")
    independent_source_weight: Decimal = Decimal("0.200000")
    primary_source_weight: Decimal = Decimal("0.150000")
    reliability_weight: Decimal = Decimal("0.200000")
    freshness_weight_weight: Decimal = Decimal("0.100000")
    resolution_alignment_weight: Decimal = Decimal("0.150000")
    contradiction_penalty_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, StrategyResearchEvidenceChainScoreV10Config)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_evidence_item_count",
            "minimum_independent_source_count",
            "minimum_primary_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "maximum_contradiction_count",
            _normalize_nonnegative_count(
                "maximum_contradiction_count",
                self.maximum_contradiction_count,
            ),
        )
        for field_name in (
            "minimum_average_source_reliability",
            "minimum_freshness_weight",
            "minimum_resolution_alignment_score",
            "pass_score_threshold",
            "watch_score_threshold",
            "evidence_item_weight",
            "independent_source_weight",
            "primary_source_weight",
            "reliability_weight",
            "freshness_weight_weight",
            "resolution_alignment_weight",
            "contradiction_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold > self.pass_score_threshold:
            raise ValueError("watch_score_threshold must be <= pass_score_threshold")
        _validate_score_weights(self)
        require_paper_only_flags("StrategyResearchEvidenceChainScoreV10Config", self)


@dataclass(frozen=True)
class StrategyResearchEvidenceChainScoreV10Input:
    evidence_item_count: Decimal
    independent_source_count: Decimal
    primary_source_count: Decimal
    contradiction_count: Decimal
    average_source_reliability: Decimal
    freshness_weight: Decimal
    resolution_alignment_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, StrategyResearchEvidenceChainScoreV10Input)
        for field_name in (
            "evidence_item_count",
            "independent_source_count",
            "primary_source_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_reliability",
            "freshness_weight",
            "resolution_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.primary_source_count > self.evidence_item_count:
            raise ValueError("primary_source_count must not exceed evidence_item_count")
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError(
                "independent_source_count must not exceed evidence_item_count",
            )
        require_paper_only_flags("StrategyResearchEvidenceChainScoreV10Input", self)


@dataclass(frozen=True)
class StrategyResearchEvidenceChainScoreV10Result:
    config_version: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    primary_source_count: Decimal
    contradiction_count: Decimal
    average_source_reliability: Decimal
    freshness_weight: Decimal
    resolution_alignment_score: Decimal
    evidence_chain_score: Decimal
    evidence_chain_status: str
    needs_more_sources: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("result", self, StrategyResearchEvidenceChainScoreV10Result)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_item_count",
            "independent_source_count",
            "primary_source_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_reliability",
            "freshness_weight",
            "resolution_alignment_score",
            "evidence_chain_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("evidence_chain_status", self.evidence_chain_status)
        _require_bool("needs_more_sources", self.needs_more_sources)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        reject_unsafe_surface_fields("strategy research evidence chain score v10", self)
        require_paper_only_flags("StrategyResearchEvidenceChainScoreV10Result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_evidence_chain_score_v10_payload(self)


def score_strategy_research_evidence_chain_score_v10(
    evidence: StrategyResearchEvidenceChainScoreV10Input,
    *,
    config: StrategyResearchEvidenceChainScoreV10Config
    | None = None,
) -> StrategyResearchEvidenceChainScoreV10Result:
    if type(evidence) is not StrategyResearchEvidenceChainScoreV10Input:
        raise ValueError("evidence must be a StrategyResearchEvidenceChainScoreV10Input")
    require_paper_only_flags("evidence", evidence)
    active_config = config or StrategyResearchEvidenceChainScoreV10Config()
    if type(active_config) is not StrategyResearchEvidenceChainScoreV10Config:
        raise ValueError(
            "config must be a StrategyResearchEvidenceChainScoreV10Config",
        )
    require_paper_only_flags("config", active_config)

    evidence_chain_score = _evidence_chain_score(evidence, active_config)
    needs_more_sources = _needs_more_sources(evidence, active_config)
    quality_issue = _has_quality_issue(evidence, active_config)
    evidence_chain_status = _evidence_chain_status(
        evidence=evidence,
        config=active_config,
        evidence_chain_score=evidence_chain_score,
        needs_more_sources=needs_more_sources,
        quality_issue=quality_issue,
    )
    reason_codes = _result_reason_codes(
        evidence=evidence,
        config=active_config,
        evidence_chain_score=evidence_chain_score,
    )

    return StrategyResearchEvidenceChainScoreV10Result(
        config_version=active_config.config_version,
        evidence_item_count=evidence.evidence_item_count,
        independent_source_count=evidence.independent_source_count,
        primary_source_count=evidence.primary_source_count,
        contradiction_count=evidence.contradiction_count,
        average_source_reliability=evidence.average_source_reliability,
        freshness_weight=evidence.freshness_weight,
        resolution_alignment_score=evidence.resolution_alignment_score,
        evidence_chain_score=evidence_chain_score,
        evidence_chain_status=evidence_chain_status,
        needs_more_sources=needs_more_sources,
        reason_codes=reason_codes,
    )


def strategy_research_evidence_chain_score_v10_payload(
    result: StrategyResearchEvidenceChainScoreV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyResearchEvidenceChainScoreV10Result:
        raise ValueError("result must be a StrategyResearchEvidenceChainScoreV10Result")
    require_paper_only_flags("result", result)
    payload = {
        "config_version": result.config_version,
        "evidence_item_count": result.evidence_item_count,
        "independent_source_count": result.independent_source_count,
        "primary_source_count": result.primary_source_count,
        "contradiction_count": result.contradiction_count,
        "average_source_reliability": result.average_source_reliability,
        "freshness_weight": result.freshness_weight,
        "resolution_alignment_score": result.resolution_alignment_score,
        "evidence_chain_score": result.evidence_chain_score,
        "evidence_chain_status": result.evidence_chain_status,
        "needs_more_sources": result.needs_more_sources,
        "reason_codes": result.reason_codes,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }
    reject_unsafe_surface_fields(
        "strategy research evidence chain score v10 payload",
        payload,
    )
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _evidence_chain_score(
    evidence: StrategyResearchEvidenceChainScoreV10Input,
    config: StrategyResearchEvidenceChainScoreV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        depth_score = _coverage_ratio(
            evidence.evidence_item_count,
            config.minimum_evidence_item_count,
        )
        independence_score = _coverage_ratio(
            evidence.independent_source_count,
            config.minimum_independent_source_count,
        )
        primary_score = _coverage_ratio(
            evidence.primary_source_count,
            config.minimum_primary_source_count,
        )
        raw_score = (
            depth_score * config.evidence_item_weight
            + independence_score * config.independent_source_weight
            + primary_score * config.primary_source_weight
            + evidence.average_source_reliability * config.reliability_weight
            + evidence.freshness_weight * config.freshness_weight_weight
            + evidence.resolution_alignment_score * config.resolution_alignment_weight
        )
        penalty = evidence.contradiction_count * config.contradiction_penalty_weight
        return _clamp_ratio(raw_score - penalty)


def _coverage_ratio(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _needs_more_sources(
    evidence: StrategyResearchEvidenceChainScoreV10Input,
    config: StrategyResearchEvidenceChainScoreV10Config,
) -> bool:
    return (
        evidence.evidence_item_count < config.minimum_evidence_item_count
        or evidence.independent_source_count < config.minimum_independent_source_count
        or evidence.primary_source_count < config.minimum_primary_source_count
        or evidence.contradiction_count > config.maximum_contradiction_count
    )


def _has_quality_issue(
    evidence: StrategyResearchEvidenceChainScoreV10Input,
    config: StrategyResearchEvidenceChainScoreV10Config,
) -> bool:
    return (
        evidence.average_source_reliability < config.minimum_average_source_reliability
        or evidence.freshness_weight < config.minimum_freshness_weight
        or evidence.resolution_alignment_score < config.minimum_resolution_alignment_score
    )


def _evidence_chain_status(
    *,
    evidence: StrategyResearchEvidenceChainScoreV10Input,
    config: StrategyResearchEvidenceChainScoreV10Config,
    evidence_chain_score: Decimal,
    needs_more_sources: bool,
    quality_issue: bool,
) -> str:
    if (
        evidence.contradiction_count > config.maximum_contradiction_count
        or evidence_chain_score < config.watch_score_threshold
    ):
        return "blocked"
    if (
        needs_more_sources
        or quality_issue
        or evidence_chain_score < config.pass_score_threshold
    ):
        return "watch"
    return "pass"


def _result_reason_codes(
    *,
    evidence: StrategyResearchEvidenceChainScoreV10Input,
    config: StrategyResearchEvidenceChainScoreV10Config,
    evidence_chain_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if evidence.evidence_item_count < config.minimum_evidence_item_count:
        codes.append("insufficient_evidence_items")
    if evidence.independent_source_count < config.minimum_independent_source_count:
        codes.append("insufficient_independent_sources")
    if evidence.primary_source_count < config.minimum_primary_source_count:
        codes.append("missing_primary_source")
    if evidence.contradiction_count > config.maximum_contradiction_count:
        codes.append("source_contradictions_present")
    if evidence.average_source_reliability < config.minimum_average_source_reliability:
        codes.append("low_average_source_reliability")
    if evidence.freshness_weight < config.minimum_freshness_weight:
        codes.append("stale_evidence_freshness")
    if evidence.resolution_alignment_score < config.minimum_resolution_alignment_score:
        codes.append("weak_resolution_alignment")
    if evidence_chain_score < config.watch_score_threshold:
        codes.append("evidence_chain_blocked_score")
    elif evidence_chain_score < config.pass_score_threshold:
        codes.append("evidence_chain_watch_score")
    if not codes:
        codes.append("evidence_chain_passed")
    return _normalize_reason_codes(tuple(codes))


def _validate_score_weights(
    config: StrategyResearchEvidenceChainScoreV10Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            config.evidence_item_weight
            + config.independent_source_weight
            + config.primary_source_weight
            + config.reliability_weight
            + config.freshness_weight_weight
            + config.resolution_alignment_weight
        ).quantize(RATIO_QUANTUM)
    if total != ONE_RATIO:
        raise ValueError("score component weights must sum to 1.000000")


def _validate_result(result: StrategyResearchEvidenceChainScoreV10Result) -> None:
    if result.primary_source_count > result.evidence_item_count:
        raise ValueError("primary_source_count must not exceed evidence_item_count")
    if result.independent_source_count > result.evidence_item_count:
        raise ValueError("independent_source_count must not exceed evidence_item_count")
    if result.evidence_chain_status == "pass":
        if result.needs_more_sources:
            raise ValueError("pass result must not need more sources")
        if result.reason_codes != ("evidence_chain_passed",):
            raise ValueError("pass result reason_codes must be evidence_chain_passed")
    if "evidence_chain_passed" in result.reason_codes and result.evidence_chain_status != "pass":
        raise ValueError("evidence_chain_passed requires pass status")
    if result.needs_more_sources and not any(
        code
        in {
            "insufficient_evidence_items",
            "insufficient_independent_sources",
            "missing_primary_source",
            "source_contradictions_present",
        }
        for code in result.reason_codes
    ):
        raise ValueError("needs_more_sources must include a source gap reason")
    if result.evidence_chain_status == "blocked" and not any(
        code
        in {
            "source_contradictions_present",
            "evidence_chain_blocked_score",
        }
        for code in result.reason_codes
    ):
        raise ValueError("blocked result must include a blocking reason")


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _require_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in EVIDENCE_CHAIN_STATUSES:
        raise ValueError(f"{field_name} must be one of {EVIDENCE_CHAIN_STATUSES!r}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_EVIDENCE_CHAIN_SCORE_V10_CONFIG_VERSION",
    "EVIDENCE_CHAIN_STATUSES",
    "REASON_CODES",
    "StrategyResearchEvidenceChainScoreV10Config",
    "StrategyResearchEvidenceChainScoreV10Input",
    "StrategyResearchEvidenceChainScoreV10Result",
    "score_strategy_research_evidence_chain_score_v10",
    "strategy_research_evidence_chain_score_v10_payload",
)
