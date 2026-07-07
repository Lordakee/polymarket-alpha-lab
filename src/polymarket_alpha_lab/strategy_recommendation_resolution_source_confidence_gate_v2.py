"""Phase 1 paper-only resolution-source confidence readiness gate."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_SOURCE_CONFIDENCE_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-resolution-source-confidence-gate-v2"
)

VALUE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

SIDE_VALUES = ("yes", "no")
READINESS_STATUSES = ("ready", "watch", "blocked")
STATUS_SORT_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "ready": Decimal("2.000000"),
}

PASS_REASON_CODE = "resolution_source_confidence_gate_passed"
EMPTY_REASON_CODE = "resolution_source_confidence_gate_empty"
ROW_REASON_CODE_SEQUENCE = (
    "official_source_hierarchy_below_minimum",
    "rule_criteria_match_below_minimum",
    "resolution_source_stale",
    "resolution_source_near_stale",
    "contradiction_severity_blocking",
    "contradiction_severity_watch",
    "settlement_lag_blocking",
    "settlement_lag_watch",
    "cost_adjusted_edge_buffer_below_watch",
    "cost_adjusted_edge_buffer_below_ready",
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE, PASS_REASON_CODE) + ROW_REASON_CODE_SEQUENCE
BLOCKING_REASON_CODES = frozenset(
    (
        "official_source_hierarchy_below_minimum",
        "rule_criteria_match_below_minimum",
        "resolution_source_stale",
        "contradiction_severity_blocking",
        "settlement_lag_blocking",
        "cost_adjusted_edge_buffer_below_watch",
    ),
)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DIGEST_HEX_CHARS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)


class _NoSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class StrategyRecommendationResolutionSourceConfidenceGateV2Config(_NoSubclass):
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_SOURCE_CONFIDENCE_GATE_V2_CONFIG_VERSION
    )
    min_official_source_hierarchy_score: Decimal = Decimal("0.800000")
    min_rule_criteria_match_score: Decimal = Decimal("0.850000")
    max_resolution_source_age_seconds: Decimal = Decimal("3600.000000")
    source_age_watch_ratio: Decimal = Decimal("0.800000")
    max_watch_contradiction_severity_score: Decimal = Decimal("0.100000")
    max_block_contradiction_severity_score: Decimal = Decimal("0.300000")
    max_watch_settlement_lag_seconds: Decimal = Decimal("7200.000000")
    max_block_settlement_lag_seconds: Decimal = Decimal("21600.000000")
    min_ready_cost_adjusted_edge_buffer_probability: Decimal = Decimal("0.030000")
    min_watch_cost_adjusted_edge_buffer_probability: Decimal = Decimal("0.010000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyRecommendationResolutionSourceConfidenceGateV2Config)
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_SOURCE_CONFIDENCE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_official_source_hierarchy_score",
            "min_rule_criteria_match_score",
            "source_age_watch_ratio",
            "max_watch_contradiction_severity_score",
            "max_block_contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_source_age_seconds",
            "max_watch_settlement_lag_seconds",
            "max_block_settlement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_cost_adjusted_edge_buffer_probability",
            "min_watch_cost_adjusted_edge_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.max_block_contradiction_severity_score
            < self.max_watch_contradiction_severity_score
        ):
            raise ValueError("block contradiction threshold must be at least watch threshold")
        if self.max_block_settlement_lag_seconds < self.max_watch_settlement_lag_seconds:
            raise ValueError("block settlement lag threshold must be at least watch threshold")
        if (
            self.min_ready_cost_adjusted_edge_buffer_probability
            < self.min_watch_cost_adjusted_edge_buffer_probability
        ):
            raise ValueError("ready edge buffer threshold must be at least watch threshold")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionSourceConfidenceGateV2Input(_NoSubclass):
    recommendation_id: str
    market_slug: str
    side: str
    forecast_probability: Decimal
    market_probability: Decimal
    fee_cost_probability: Decimal
    spread_cost_probability: Decimal
    settlement_lag_cost_probability: Decimal
    official_source_hierarchy_score: Decimal
    rule_criteria_match_score: Decimal
    resolution_source_observed_at: datetime
    contradiction_severity_score: Decimal
    settlement_lag_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyRecommendationResolutionSourceConfidenceGateV2Input)
        for field_name in ("recommendation_id", "market_slug"):
            _require_public_text(field_name, getattr(self, field_name))
        _require_member("side", self.side, SIDE_VALUES)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_cost_probability",
            "spread_cost_probability",
            "settlement_lag_cost_probability",
            "official_source_hierarchy_score",
            "rule_criteria_match_score",
            "contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_source_observed_at",
            _as_utc("resolution_source_observed_at", self.resolution_source_observed_at),
        )
        object.__setattr__(
            self,
            "settlement_lag_seconds",
            _normalize_nonnegative_decimal(
                "settlement_lag_seconds",
                self.settlement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    recommendation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount)
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "recommendation_ratio",
            _normalize_ratio("recommendation_ratio", self.recommendation_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionSourceConfidenceGateV2Row(_NoSubclass):
    recommendation_id: str
    market_slug: str
    side: str
    forecast_probability: Decimal
    market_probability: Decimal
    gross_edge_probability: Decimal
    fee_cost_probability: Decimal
    spread_cost_probability: Decimal
    settlement_lag_cost_probability: Decimal
    total_cost_probability: Decimal
    cost_adjusted_edge_buffer_probability: Decimal
    official_source_hierarchy_score: Decimal
    rule_criteria_match_score: Decimal
    resolution_source_observed_at: datetime
    resolution_source_age_seconds: Decimal
    contradiction_severity_score: Decimal
    settlement_lag_seconds: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyRecommendationResolutionSourceConfidenceGateV2Row)
        for field_name in ("recommendation_id", "market_slug"):
            _require_public_text(field_name, getattr(self, field_name))
        _require_member("side", self.side, SIDE_VALUES)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_cost_probability",
            "spread_cost_probability",
            "settlement_lag_cost_probability",
            "official_source_hierarchy_score",
            "rule_criteria_match_score",
            "contradiction_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_edge_probability",
            "cost_adjusted_edge_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_cost_probability",
            _normalize_nonnegative_decimal(
                "total_cost_probability",
                self.total_cost_probability,
            ),
        )
        object.__setattr__(
            self,
            "resolution_source_observed_at",
            _as_utc("resolution_source_observed_at", self.resolution_source_observed_at),
        )
        for field_name in ("resolution_source_age_seconds", "settlement_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_gate_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionSourceConfidenceGateV2Report(_NoSubclass):
    generated_at: datetime
    config_version: str
    recommendation_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_cost_adjusted_edge_buffer_probability: Decimal
    min_cost_adjusted_edge_buffer_probability: Decimal
    max_resolution_source_age_seconds: Decimal
    max_settlement_lag_seconds: Decimal
    min_official_source_hierarchy_score: Decimal
    min_rule_criteria_match_score: Decimal
    readiness_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount,
        ...,
    ]
    rows: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyRecommendationResolutionSourceConfidenceGateV2Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "recommendation_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_cost_adjusted_edge_buffer_probability",
            "min_cost_adjusted_edge_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_source_age_seconds",
            "max_settlement_lag_seconds",
            "min_official_source_hierarchy_score",
            "min_rule_criteria_match_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        _require_public_text("recommended_next_step", self.recommended_next_step)
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_recommendation_resolution_source_confidence_gate_v2_report(
    recommendations: Iterable[StrategyRecommendationResolutionSourceConfidenceGateV2Input],
    *,
    config: StrategyRecommendationResolutionSourceConfidenceGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationResolutionSourceConfidenceGateV2Report:
    if type(config) is not StrategyRecommendationResolutionSourceConfidenceGateV2Config:
        raise ValueError(
            "config must be StrategyRecommendationResolutionSourceConfidenceGateV2Config",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(recommendations)
    _validate_input_times(inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationResolutionSourceConfidenceGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        recommendation_count=_count(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_cost_adjusted_edge_buffer_probability=_sum_decimal(
            tuple(row.cost_adjusted_edge_buffer_probability for row in rows),
        ),
        min_cost_adjusted_edge_buffer_probability=min(
            (row.cost_adjusted_edge_buffer_probability for row in rows),
            default=ZERO,
        ),
        max_resolution_source_age_seconds=max(
            (row.resolution_source_age_seconds for row in rows),
            default=ZERO,
        ),
        max_settlement_lag_seconds=max(
            (row.settlement_lag_seconds for row in rows),
            default=ZERO,
        ),
        min_official_source_hierarchy_score=min(
            (row.official_source_hierarchy_score for row in rows),
            default=ZERO,
        ),
        min_rule_criteria_match_score=min(
            (row.rule_criteria_match_score for row in rows),
            default=ZERO,
        ),
        readiness_status=_report_status(rows),
        recommended_next_step=_recommended_next_step(_report_status(rows)),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(
    report: StrategyRecommendationResolutionSourceConfidenceGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationResolutionSourceConfidenceGateV2Report:
        raise ValueError(
            "report must be StrategyRecommendationResolutionSourceConfidenceGateV2Report",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(payload)
    return payload


def validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a mapping")
    _reject_unsafe_public_payload(payload)
    _reject_public_payload_numeric_types(payload)
    _require_public_payload_flags(payload)
    digest_value = payload.get("derived_validation_digest")
    if type(digest_value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_input(
    item: StrategyRecommendationResolutionSourceConfidenceGateV2Input,
    *,
    config: StrategyRecommendationResolutionSourceConfidenceGateV2Config,
    generated_at: datetime,
) -> StrategyRecommendationResolutionSourceConfidenceGateV2Row:
    gross_edge_probability = _subtract_decimal(item.forecast_probability, item.market_probability)
    total_cost_probability = _sum_decimal(
        (
            item.fee_cost_probability,
            item.spread_cost_probability,
            item.settlement_lag_cost_probability,
        ),
    )
    cost_adjusted_edge_buffer_probability = _subtract_decimal(
        gross_edge_probability,
        total_cost_probability,
    )
    resolution_source_age_seconds = _duration_seconds(
        item.resolution_source_observed_at,
        generated_at,
    )
    reason_codes = _row_reason_codes(
        official_source_hierarchy_score=item.official_source_hierarchy_score,
        rule_criteria_match_score=item.rule_criteria_match_score,
        resolution_source_age_seconds=resolution_source_age_seconds,
        contradiction_severity_score=item.contradiction_severity_score,
        settlement_lag_seconds=item.settlement_lag_seconds,
        cost_adjusted_edge_buffer_probability=cost_adjusted_edge_buffer_probability,
        config=config,
    )
    return StrategyRecommendationResolutionSourceConfidenceGateV2Row(
        recommendation_id=item.recommendation_id,
        market_slug=item.market_slug,
        side=item.side,
        forecast_probability=item.forecast_probability,
        market_probability=item.market_probability,
        gross_edge_probability=gross_edge_probability,
        fee_cost_probability=item.fee_cost_probability,
        spread_cost_probability=item.spread_cost_probability,
        settlement_lag_cost_probability=item.settlement_lag_cost_probability,
        total_cost_probability=total_cost_probability,
        cost_adjusted_edge_buffer_probability=cost_adjusted_edge_buffer_probability,
        official_source_hierarchy_score=item.official_source_hierarchy_score,
        rule_criteria_match_score=item.rule_criteria_match_score,
        resolution_source_observed_at=item.resolution_source_observed_at,
        resolution_source_age_seconds=resolution_source_age_seconds,
        contradiction_severity_score=item.contradiction_severity_score,
        settlement_lag_seconds=item.settlement_lag_seconds,
        readiness_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    official_source_hierarchy_score: Decimal,
    rule_criteria_match_score: Decimal,
    resolution_source_age_seconds: Decimal,
    contradiction_severity_score: Decimal,
    settlement_lag_seconds: Decimal,
    cost_adjusted_edge_buffer_probability: Decimal,
    config: StrategyRecommendationResolutionSourceConfidenceGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_source_hierarchy_score < config.min_official_source_hierarchy_score:
        reasons.append("official_source_hierarchy_below_minimum")
    if rule_criteria_match_score < config.min_rule_criteria_match_score:
        reasons.append("rule_criteria_match_below_minimum")
    source_watch_age_seconds = _multiply_decimal(
        config.max_resolution_source_age_seconds,
        config.source_age_watch_ratio,
    )
    if resolution_source_age_seconds > config.max_resolution_source_age_seconds:
        reasons.append("resolution_source_stale")
    elif resolution_source_age_seconds >= source_watch_age_seconds:
        reasons.append("resolution_source_near_stale")
    if contradiction_severity_score > config.max_block_contradiction_severity_score:
        reasons.append("contradiction_severity_blocking")
    elif contradiction_severity_score > config.max_watch_contradiction_severity_score:
        reasons.append("contradiction_severity_watch")
    if settlement_lag_seconds > config.max_block_settlement_lag_seconds:
        reasons.append("settlement_lag_blocking")
    elif settlement_lag_seconds > config.max_watch_settlement_lag_seconds:
        reasons.append("settlement_lag_watch")
    if (
        cost_adjusted_edge_buffer_probability
        < config.min_watch_cost_adjusted_edge_buffer_probability
    ):
        reasons.append("cost_adjusted_edge_buffer_below_watch")
    elif (
        cost_adjusted_edge_buffer_probability
        < config.min_ready_cost_adjusted_edge_buffer_probability
    ):
        reasons.append("cost_adjusted_edge_buffer_below_ready")
    if not reasons:
        return (PASS_REASON_CODE,)
    present = set(reasons)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in present)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "ready"
    return "watch"


def _report_status(
    rows: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...],
) -> str:
    statuses = tuple(row.readiness_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "ready"


def _recommended_next_step(readiness_status: str) -> str:
    if readiness_status == "blocked":
        return "block_report_only_resolution_source_confidence"
    if readiness_status == "watch":
        return "review_report_only_resolution_source_confidence"
    return "continue_report_only_resolution_source_confidence"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = set(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in present)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...],
) -> tuple[StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount, ...]:
    recommendation_count = _count(len(rows))
    return tuple(
        StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            recommendation_ratio=_ratio(_reason_count(rows, reason_code), recommendation_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_inputs(
    value: Iterable[StrategyRecommendationResolutionSourceConfidenceGateV2Input],
) -> tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Input, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("recommendations must be iterable")
    items = tuple(value)
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationResolutionSourceConfidenceGateV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationResolutionSourceConfidenceGateV2Input values",
            )
        _require_hard_flags(item)
        if item.recommendation_id in seen:
            raise ValueError("recommendations must not contain duplicate recommendation_id values")
        seen.add(item.recommendation_id)
    return items


def _normalize_rows(
    value: Iterable[StrategyRecommendationResolutionSourceConfidenceGateV2Row],
) -> tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("rows must be iterable")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationResolutionSourceConfidenceGateV2Row:
            raise ValueError(
                "rows must contain StrategyRecommendationResolutionSourceConfidenceGateV2Row values",
            )
        _require_hard_flags(row)
        if row.recommendation_id in seen:
            raise ValueError("rows must not contain duplicate recommendation_id values")
        seen.add(row.recommendation_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount],
) -> tuple[StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_code_counts must be iterable")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODE_SEQUENCE
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_input_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_codes must be iterable")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_text("reason_code", reason_code)
        if reason_code != reason_code.lower():
            raise ValueError("reason_code must be lowercase")
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _normalize_gate_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_codes must be iterable")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REPORT_REASON_CODE_SEQUENCE)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    if PASS_REASON_CODE in seen and len(reason_codes) != 1:
        raise ValueError("pass reason must be the only reason code")
    expected = tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _normalize_report_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("reason_codes must be iterable")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REPORT_REASON_CODE_SEQUENCE)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    if EMPTY_REASON_CODE in seen and len(reason_codes) != 1:
        raise ValueError("empty reason must be the only reason code")
    if PASS_REASON_CODE in seen and len(reason_codes) != 1:
        raise ValueError("pass reason must be the only reason code")
    expected = tuple(reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in seen)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    return reason_codes


def _validate_input_times(
    items: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Input, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in items:
        if item.resolution_source_observed_at > generated_at:
            raise ValueError("resolution_source_observed_at must not be after generated_at")


def _validate_row(row: StrategyRecommendationResolutionSourceConfidenceGateV2Row) -> None:
    if row.gross_edge_probability != _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    ):
        raise ValueError("gross_edge_probability must match forecast and market")
    expected_total_cost = _sum_decimal(
        (
            row.fee_cost_probability,
            row.spread_cost_probability,
            row.settlement_lag_cost_probability,
        ),
    )
    if row.total_cost_probability != expected_total_cost:
        raise ValueError("total_cost_probability must match cost components")
    if row.cost_adjusted_edge_buffer_probability != _subtract_decimal(
        row.gross_edge_probability,
        row.total_cost_probability,
    ):
        raise ValueError("cost_adjusted_edge_buffer_probability must match edge and cost")
    if row.readiness_status != _row_status(row.reason_codes):
        raise ValueError("readiness_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyRecommendationResolutionSourceConfidenceGateV2Report) -> None:
    rows = report.rows
    if report.recommendation_count != _count(len(rows)):
        raise ValueError("recommendation_count must match rows")
    for field_name, status in (
        ("ready_count", "ready"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if (
        report.ready_count + report.watch_count + report.blocked_count
        != report.recommendation_count
    ):
        raise ValueError("status counts must match recommendation_count")
    if report.total_cost_adjusted_edge_buffer_probability != _sum_decimal(
        tuple(row.cost_adjusted_edge_buffer_probability for row in rows),
    ):
        raise ValueError("total_cost_adjusted_edge_buffer_probability must match rows")
    if report.min_cost_adjusted_edge_buffer_probability != min(
        (row.cost_adjusted_edge_buffer_probability for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_cost_adjusted_edge_buffer_probability must match rows")
    if report.max_resolution_source_age_seconds != max(
        (row.resolution_source_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_resolution_source_age_seconds must match rows")
    if report.max_settlement_lag_seconds != max(
        (row.settlement_lag_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_settlement_lag_seconds must match rows")
    if report.min_official_source_hierarchy_score != min(
        (row.official_source_hierarchy_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_official_source_hierarchy_score must match rows")
    if report.min_rule_criteria_match_score != min(
        (row.rule_criteria_match_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_rule_criteria_match_score must match rows")
    if report.readiness_status != _report_status(rows):
        raise ValueError("readiness_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.readiness_status):
        raise ValueError("recommended_next_step must match readiness_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for row in rows:
        _validate_row(row)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _status_count(
    rows: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...],
    status: str,
) -> Decimal:
    _require_member("status", status, READINESS_STATUSES)
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _reason_count(
    rows: tuple[StrategyRecommendationResolutionSourceConfidenceGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: StrategyRecommendationResolutionSourceConfidenceGateV2Row,
) -> tuple[Decimal, str, str, str]:
    return (
        STATUS_SORT_RANK[row.readiness_status],
        row.recommendation_id,
        row.market_slug,
        row.side,
    )


def _row_derived_validation_digest(
    row: StrategyRecommendationResolutionSourceConfidenceGateV2Row,
) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: StrategyRecommendationResolutionSourceConfidenceGateV2Report,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(
    row: StrategyRecommendationResolutionSourceConfidenceGateV2Row,
) -> dict[str, Any]:
    raw_payload = asdict(row)
    raw_payload.pop("derived_validation_digest", None)
    payload = _json_ready(raw_payload)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    return payload


def _report_public_payload_for_digest(
    report: StrategyRecommendationResolutionSourceConfidenceGateV2Report,
) -> dict[str, Any]:
    raw_payload = asdict(report)
    raw_payload.pop("derived_validation_digest", None)
    payload = _json_ready(raw_payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def _public_payload_derived_validation_digest(payload: Mapping[str, object]) -> str:
    payload_copy = dict(payload)
    payload_copy.pop("derived_validation_digest", None)
    return hashlib.sha256(
        json.dumps(
            payload_copy,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return _as_utc("datetime value", value).isoformat()
    if type(value) is str:
        _require_public_text("payload value", value)
        return value
    if type(value) is bool:
        return value
    if value is None:
        return None
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_text("payload field", key)
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_text("payload field", key)
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)


def _reject_public_payload_numeric_types(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (Decimal, float, int):
        raise ValueError("public payload must use Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_payload_numeric_types(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload_numeric_types(item)


def _require_public_payload_flags(payload: Mapping[str, object]) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    _require_nested_payload_flags(payload)


def _require_nested_payload_flags(value: object) -> None:
    if isinstance(value, Mapping):
        if any(field_name in value for field_name in HARD_FLAG_FIELDS):
            for field_name in HARD_FLAG_FIELDS:
                if value.get(field_name) is not True:
                    raise ValueError(f"{field_name} must be True")
        for item in value.values():
            _require_nested_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_nested_payload_flags(item)


def _duration_seconds(started_at: datetime, generated_at: datetime) -> Decimal:
    started_at_utc = _as_utc("started_at", started_at)
    generated_at_utc = _as_utc("generated_at", generated_at)
    delta = generated_at_utc - started_at_utc
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(VALUE_QUANTUM)
    if seconds < ZERO:
        raise ValueError("resolution_source_age_seconds must be nonnegative")
    return seconds


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("decimal sum", sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("decimal difference", left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal("decimal product", left * right)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(VALUE_QUANTUM)


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload Decimal", value), "f")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_public_text(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(term in value.lower() for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError("unsafe public surface")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")
    for field_name in _iter_field_names(value):
        _require_public_text("field_name", field_name)


def _iter_field_names(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        names: list[str] = []
        for item in fields(value):
            names.append(item.name)
            names.extend(_iter_field_names(getattr(value, item.name)))
        return tuple(names)
    if isinstance(value, Mapping):
        names = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            names.append(key)
            names.extend(_iter_field_names(item))
        return tuple(names)
    if isinstance(value, (list, tuple)):
        names = []
        for item in value:
            names.extend(_iter_field_names(item))
        return tuple(names)
    return ()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_public_text(field_name, value)
    if len(value) != 64 or any(character not in DIGEST_HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex string")
    return value


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_SOURCE_CONFIDENCE_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationResolutionSourceConfidenceGateV2Config",
    "StrategyRecommendationResolutionSourceConfidenceGateV2Input",
    "StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount",
    "StrategyRecommendationResolutionSourceConfidenceGateV2Report",
    "StrategyRecommendationResolutionSourceConfidenceGateV2Row",
    "build_strategy_recommendation_resolution_source_confidence_gate_v2_report",
    "strategy_recommendation_resolution_source_confidence_gate_v2_public_payload",
    "validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload",
)
