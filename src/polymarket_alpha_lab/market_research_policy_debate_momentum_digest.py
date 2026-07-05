"""Pure Phase 1 policy debate momentum risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MOMENTUM_DIGEST_CONFIG_VERSION",
    "PolicyDebateMomentumDigestConfig",
    "PolicyDebateMomentumObservation",
    "PolicyDebateMomentumDigestRow",
    "PolicyDebateMomentumReasonCodeCount",
    "PolicyDebateMomentumDigestReport",
    "build_market_research_policy_debate_momentum_digest",
    "market_research_policy_debate_momentum_digest_payload",
)


DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MOMENTUM_DIGEST_CONFIG_VERSION = (
    "market-research-policy-debate-momentum-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
MOMENTUM_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
MOMENTUM_DIRECTIONS = ("negative", "flat", "positive")
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_policy_debate_momentum_screening",
    WATCH_STATUS: "monitor_report_only_policy_debate_momentum_screening",
    PASS_STATUS: "allow_report_only_policy_debate_momentum_screening",
}

SUPPORT_MOVE_RISK_WEIGHT = Decimal("0.400000")
MENTION_VELOCITY_RISK_WEIGHT = Decimal("0.250000")
SENTIMENT_RISK_WEIGHT = Decimal("0.250000")
FRESH_DEBATE_WINDOW_RISK_WEIGHT = Decimal("0.100000")

GENERATED_REASON_CODE_PREFIX = "policy_debate_momentum_"
EMPTY_REASON_CODE = "policy_debate_momentum_digest_empty"
BLOCKED_REASON_CODE = "policy_debate_momentum_blocked"
WATCH_REASON_CODE = "policy_debate_momentum_watch"
BELOW_THRESHOLD_REASON_CODE = "policy_debate_momentum_below_threshold"
SOURCE_FRESH_REASON_CODE = "policy_debate_momentum_source_fresh"
SOURCE_STALE_REASON_CODE = "policy_debate_momentum_source_stale"
SUPPORT_MOVE_MATERIAL_REASON_CODE = "policy_debate_momentum_support_move_material"
SUPPORT_MOVE_HIGH_REASON_CODE = "policy_debate_momentum_support_move_high"
MENTION_VELOCITY_SHIFT_REASON_CODE = "policy_debate_momentum_mention_velocity_shift"
MENTION_VELOCITY_HIGH_REASON_CODE = "policy_debate_momentum_mention_velocity_high"
SENTIMENT_SHIFT_REASON_CODE = "policy_debate_momentum_sentiment_shift"
SENTIMENT_HIGH_REASON_CODE = "policy_debate_momentum_sentiment_high"
FRESH_DEBATE_WINDOW_REASON_CODE = "policy_debate_momentum_fresh_debate_window"


@dataclass(frozen=True)
class PolicyDebateMomentumDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MOMENTUM_DIGEST_CONFIG_VERSION
    watch_policy_debate_momentum_score: Decimal = Decimal("0.350000")
    blocked_policy_debate_momentum_score: Decimal = Decimal("0.700000")
    material_support_move_share: Decimal = Decimal("0.030000")
    high_support_move_share: Decimal = Decimal("0.062805")
    material_mention_velocity_delta: Decimal = Decimal("0.200000")
    high_mention_velocity_delta: Decimal = Decimal("0.512178")
    material_sentiment_delta: Decimal = Decimal("0.150000")
    high_sentiment_delta: Decimal = Decimal("0.400000")
    fresh_debate_window_hours: Decimal = Decimal("48.000000")
    max_source_age_seconds: Decimal = Decimal("172800.000000")
    stale_confidence_cap: Decimal = Decimal("0.300000")
    clear_confidence_cap: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyDebateMomentumDigestConfig:
            raise TypeError(
                "PolicyDebateMomentumDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyDebateMomentumDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MOMENTUM_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_policy_debate_momentum_score",
            "blocked_policy_debate_momentum_score",
            "stale_confidence_cap",
            "clear_confidence_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_support_move_share",
            "high_support_move_share",
            "material_mention_velocity_delta",
            "high_mention_velocity_delta",
            "material_sentiment_delta",
            "high_sentiment_delta",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fresh_debate_window_hours",
            _normalize_nonnegative_decimal(
                "fresh_debate_window_hours",
                self.fresh_debate_window_hours,
            ),
        )
        _validate_config_thresholds(self)
        _require_hard_flags(self, "config")


@dataclass(frozen=True)
class PolicyDebateMomentumObservation:
    source_id: str
    event_key: str
    debate_id: str
    candidate_id: str
    policy_topic: str
    pre_debate_support_share: Decimal
    post_debate_support_share: Decimal
    mention_velocity_delta: Decimal
    sentiment_delta: Decimal
    hours_since_debate: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyDebateMomentumObservation:
            raise TypeError(
                "PolicyDebateMomentumObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyDebateMomentumObservation, "observation")
        for field_name in (
            "source_id",
            "event_key",
            "debate_id",
            "candidate_id",
            "policy_topic",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("pre_debate_support_share", "post_debate_support_share"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("mention_velocity_delta", "sentiment_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hours_since_debate",
            _normalize_nonnegative_decimal("hours_since_debate", self.hours_since_debate),
        )
        object.__setattr__(
            self,
            "evidence_confidence",
            _normalize_probability("evidence_confidence", self.evidence_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _require_canonical_reason_codes(
                self.upstream_reason_codes,
                "upstream_reason_codes",
            ),
        )
        _require_hard_flags(self, "observation")


@dataclass(frozen=True)
class PolicyDebateMomentumDigestRow:
    source_id: str
    event_key: str
    debate_id: str
    candidate_id: str
    policy_topic: str
    pre_debate_support_share: Decimal
    post_debate_support_share: Decimal
    support_delta_share: Decimal
    absolute_support_move_share: Decimal
    mention_velocity_delta: Decimal
    sentiment_delta: Decimal
    hours_since_debate: Decimal
    evidence_confidence: Decimal
    observed_at: datetime
    source_age_seconds: Decimal
    watch_policy_debate_momentum_score: Decimal
    blocked_policy_debate_momentum_score: Decimal
    material_support_move_share: Decimal
    high_support_move_share: Decimal
    material_mention_velocity_delta: Decimal
    high_mention_velocity_delta: Decimal
    material_sentiment_delta: Decimal
    high_sentiment_delta: Decimal
    fresh_debate_window_hours: Decimal
    max_source_age_seconds: Decimal
    stale_confidence_cap: Decimal
    clear_confidence_cap: Decimal
    policy_debate_momentum_score: Decimal
    confidence_cap: Decimal
    capped_confidence: Decimal
    momentum_direction: str
    momentum_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyDebateMomentumDigestRow:
            raise TypeError(
                "PolicyDebateMomentumDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyDebateMomentumDigestRow, "row")
        for field_name in (
            "source_id",
            "event_key",
            "debate_id",
            "candidate_id",
            "policy_topic",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("pre_debate_support_share", "post_debate_support_share"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "support_delta_share",
            "mention_velocity_delta",
            "sentiment_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_support_move_share",
            "hours_since_debate",
            "source_age_seconds",
            "fresh_debate_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_confidence",
            "watch_policy_debate_momentum_score",
            "blocked_policy_debate_momentum_score",
            "stale_confidence_cap",
            "clear_confidence_cap",
            "policy_debate_momentum_score",
            "confidence_cap",
            "capped_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_support_move_share",
            "high_support_move_share",
            "material_mention_velocity_delta",
            "high_mention_velocity_delta",
            "material_sentiment_delta",
            "high_sentiment_delta",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("momentum_direction", self.momentum_direction, MOMENTUM_DIRECTIONS)
        _require_member("momentum_status", self.momentum_status, MOMENTUM_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _require_canonical_reason_codes(self.reason_codes, "reason_codes"),
        )
        _validate_row(self)
        _require_hard_flags(self, "row")


@dataclass(frozen=True)
class PolicyDebateMomentumReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyDebateMomentumReasonCodeCount:
            raise TypeError(
                "PolicyDebateMomentumReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyDebateMomentumReasonCodeCount, "reason_code_count")
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        if self.count == ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self, "reason_code_count")


@dataclass(frozen=True)
class PolicyDebateMomentumDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_count: Decimal
    positive_momentum_count: Decimal
    negative_momentum_count: Decimal
    material_support_move_count: Decimal
    mention_velocity_shift_count: Decimal
    sentiment_shift_count: Decimal
    fresh_debate_window_count: Decimal
    max_policy_debate_momentum_score: Decimal
    average_policy_debate_momentum_score: Decimal
    max_absolute_support_move_share: Decimal
    average_absolute_support_move_share: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[PolicyDebateMomentumDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[PolicyDebateMomentumReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PolicyDebateMomentumDigestReport:
            raise TypeError(
                "PolicyDebateMomentumDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, PolicyDebateMomentumDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_RESEARCH_POLICY_DEBATE_MOMENTUM_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "stale_source_count",
            "positive_momentum_count",
            "negative_momentum_count",
            "material_support_move_count",
            "mention_velocity_shift_count",
            "sentiment_shift_count",
            "fresh_debate_window_count",
            "max_policy_debate_momentum_score",
            "average_policy_debate_momentum_score",
            "max_absolute_support_move_share",
            "average_absolute_support_move_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, MOMENTUM_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _require_canonical_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_canonical_reason_codes(self.reason_codes, "reason_codes"),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_canonical_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self, "report")


def build_market_research_policy_debate_momentum_digest(
    observations: Iterable[PolicyDebateMomentumObservation],
    *,
    config: PolicyDebateMomentumDigestConfig,
    generated_at: datetime,
) -> PolicyDebateMomentumDigestReport:
    if type(config) is not PolicyDebateMomentumDigestConfig:
        raise ValueError("config must be exactly PolicyDebateMomentumDigestConfig")
    _require_hard_flags(config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    row_count = _count_decimal(len(rows))
    digest_status = _digest_status(rows)
    return PolicyDebateMomentumDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON_CODE),
        positive_momentum_count=_direction_count(rows, "positive"),
        negative_momentum_count=_direction_count(rows, "negative"),
        material_support_move_count=_reason_count(rows, SUPPORT_MOVE_MATERIAL_REASON_CODE),
        mention_velocity_shift_count=_reason_count(
            rows,
            MENTION_VELOCITY_SHIFT_REASON_CODE,
        ),
        sentiment_shift_count=_reason_count(rows, SENTIMENT_SHIFT_REASON_CODE),
        fresh_debate_window_count=_reason_count(rows, FRESH_DEBATE_WINDOW_REASON_CODE),
        max_policy_debate_momentum_score=_max_row_decimal(
            rows,
            "policy_debate_momentum_score",
        ),
        average_policy_debate_momentum_score=_ratio(
            _sum_decimal(row.policy_debate_momentum_score for row in rows),
            row_count,
        ),
        max_absolute_support_move_share=_max_row_decimal(
            rows,
            "absolute_support_move_share",
        ),
        average_absolute_support_move_share=_ratio(
            _sum_decimal(row.absolute_support_move_share for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_policy_debate_momentum_digest_payload(
    report: PolicyDebateMomentumDigestReport,
) -> dict[str, Any]:
    if type(report) is not PolicyDebateMomentumDigestReport:
        raise ValueError("report must be exactly PolicyDebateMomentumDigestReport")
    value = _payload_value(report, "report")
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    return value


def _row_from_observation(
    value: PolicyDebateMomentumObservation,
    *,
    config: PolicyDebateMomentumDigestConfig,
    generated_at: datetime,
) -> PolicyDebateMomentumDigestRow:
    support_delta_share = _support_delta_share(
        value.pre_debate_support_share,
        value.post_debate_support_share,
    )
    absolute_support_move_share = _quantize_decimal(abs(support_delta_share))
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    fresh_debate_window = value.hours_since_debate <= config.fresh_debate_window_hours
    risk_score = _policy_debate_momentum_score(
        absolute_support_move_share=absolute_support_move_share,
        mention_velocity_delta=value.mention_velocity_delta,
        sentiment_delta=value.sentiment_delta,
        fresh_debate_window=fresh_debate_window,
        high_support_move_share=config.high_support_move_share,
        high_mention_velocity_delta=config.high_mention_velocity_delta,
        high_sentiment_delta=config.high_sentiment_delta,
    )
    momentum_status = _momentum_status(risk_score, config=config)
    confidence_cap = _confidence_cap(
        momentum_status=momentum_status,
        source_fresh=source_fresh,
        config=config,
    )
    return PolicyDebateMomentumDigestRow(
        source_id=value.source_id,
        event_key=value.event_key,
        debate_id=value.debate_id,
        candidate_id=value.candidate_id,
        policy_topic=value.policy_topic,
        pre_debate_support_share=value.pre_debate_support_share,
        post_debate_support_share=value.post_debate_support_share,
        support_delta_share=support_delta_share,
        absolute_support_move_share=absolute_support_move_share,
        mention_velocity_delta=value.mention_velocity_delta,
        sentiment_delta=value.sentiment_delta,
        hours_since_debate=value.hours_since_debate,
        evidence_confidence=value.evidence_confidence,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        watch_policy_debate_momentum_score=config.watch_policy_debate_momentum_score,
        blocked_policy_debate_momentum_score=config.blocked_policy_debate_momentum_score,
        material_support_move_share=config.material_support_move_share,
        high_support_move_share=config.high_support_move_share,
        material_mention_velocity_delta=config.material_mention_velocity_delta,
        high_mention_velocity_delta=config.high_mention_velocity_delta,
        material_sentiment_delta=config.material_sentiment_delta,
        high_sentiment_delta=config.high_sentiment_delta,
        fresh_debate_window_hours=config.fresh_debate_window_hours,
        max_source_age_seconds=config.max_source_age_seconds,
        stale_confidence_cap=config.stale_confidence_cap,
        clear_confidence_cap=config.clear_confidence_cap,
        policy_debate_momentum_score=risk_score,
        confidence_cap=confidence_cap,
        capped_confidence=min(value.evidence_confidence, confidence_cap),
        momentum_direction=_momentum_direction(support_delta_share),
        momentum_status=momentum_status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            momentum_status=momentum_status,
            absolute_support_move_share=absolute_support_move_share,
            mention_velocity_delta=value.mention_velocity_delta,
            sentiment_delta=value.sentiment_delta,
            fresh_debate_window=fresh_debate_window,
            source_fresh=source_fresh,
            config=config,
        ),
    )


def _policy_debate_momentum_score(
    *,
    absolute_support_move_share: Decimal,
    mention_velocity_delta: Decimal,
    sentiment_delta: Decimal,
    fresh_debate_window: bool,
    high_support_move_share: Decimal,
    high_mention_velocity_delta: Decimal,
    high_sentiment_delta: Decimal,
) -> Decimal:
    support_component = (
        min(ONE, _ratio(absolute_support_move_share, high_support_move_share))
        * SUPPORT_MOVE_RISK_WEIGHT
    )
    mention_component = (
        min(ONE, _ratio(_absolute_decimal(mention_velocity_delta), high_mention_velocity_delta))
        * MENTION_VELOCITY_RISK_WEIGHT
    )
    sentiment_component = (
        min(ONE, _ratio(_absolute_decimal(sentiment_delta), high_sentiment_delta))
        * SENTIMENT_RISK_WEIGHT
    )
    fresh_component = FRESH_DEBATE_WINDOW_RISK_WEIGHT if fresh_debate_window else ZERO
    return _quantize_decimal(
        min(
            ONE,
            support_component + mention_component + sentiment_component + fresh_component,
        ),
    )


def _momentum_status(
    risk_score: Decimal,
    *,
    config: PolicyDebateMomentumDigestConfig,
) -> str:
    if risk_score >= config.blocked_policy_debate_momentum_score:
        return BLOCKED_STATUS
    if risk_score >= config.watch_policy_debate_momentum_score:
        return WATCH_STATUS
    return PASS_STATUS


def _confidence_cap(
    *,
    momentum_status: str,
    source_fresh: bool,
    config: PolicyDebateMomentumDigestConfig,
) -> Decimal:
    caps = [ONE]
    if momentum_status == PASS_STATUS:
        caps.append(config.clear_confidence_cap)
    if not source_fresh:
        caps.append(config.stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    momentum_status: str,
    absolute_support_move_share: Decimal,
    mention_velocity_delta: Decimal,
    sentiment_delta: Decimal,
    fresh_debate_window: bool,
    source_fresh: bool,
    config: PolicyDebateMomentumDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.extend(
        _generated_row_reason_codes(
            momentum_status=momentum_status,
            absolute_support_move_share=absolute_support_move_share,
            mention_velocity_delta=mention_velocity_delta,
            sentiment_delta=sentiment_delta,
            fresh_debate_window=fresh_debate_window,
            source_fresh=source_fresh,
            material_support_move_share=config.material_support_move_share,
            high_support_move_share=config.high_support_move_share,
            material_mention_velocity_delta=config.material_mention_velocity_delta,
            high_mention_velocity_delta=config.high_mention_velocity_delta,
            material_sentiment_delta=config.material_sentiment_delta,
            high_sentiment_delta=config.high_sentiment_delta,
        ),
    )
    return _canonical_reason_codes(tuple(reason_codes))


def _generated_row_reason_codes(
    *,
    momentum_status: str,
    absolute_support_move_share: Decimal,
    mention_velocity_delta: Decimal,
    sentiment_delta: Decimal,
    fresh_debate_window: bool,
    source_fresh: bool,
    material_support_move_share: Decimal,
    high_support_move_share: Decimal,
    material_mention_velocity_delta: Decimal,
    high_mention_velocity_delta: Decimal,
    material_sentiment_delta: Decimal,
    high_sentiment_delta: Decimal,
) -> tuple[str, ...]:
    if momentum_status == BLOCKED_STATUS:
        reason_codes = [BLOCKED_REASON_CODE]
    elif momentum_status == WATCH_STATUS:
        reason_codes = [WATCH_REASON_CODE]
    else:
        reason_codes = [BELOW_THRESHOLD_REASON_CODE]
    reason_codes.append(SOURCE_FRESH_REASON_CODE if source_fresh else SOURCE_STALE_REASON_CODE)
    if absolute_support_move_share >= material_support_move_share:
        reason_codes.append(SUPPORT_MOVE_MATERIAL_REASON_CODE)
    if absolute_support_move_share >= high_support_move_share:
        reason_codes.append(SUPPORT_MOVE_HIGH_REASON_CODE)
    if _absolute_decimal(mention_velocity_delta) >= material_mention_velocity_delta:
        reason_codes.append(MENTION_VELOCITY_SHIFT_REASON_CODE)
    if _absolute_decimal(mention_velocity_delta) >= high_mention_velocity_delta:
        reason_codes.append(MENTION_VELOCITY_HIGH_REASON_CODE)
    if _absolute_decimal(sentiment_delta) >= material_sentiment_delta:
        reason_codes.append(SENTIMENT_SHIFT_REASON_CODE)
    if _absolute_decimal(sentiment_delta) >= high_sentiment_delta:
        reason_codes.append(SENTIMENT_HIGH_REASON_CODE)
    if fresh_debate_window:
        reason_codes.append(FRESH_DEBATE_WINDOW_REASON_CODE)
    return _canonical_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _canonical_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
) -> tuple[PolicyDebateMomentumReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON_CODE,):
        return (
            PolicyDebateMomentumReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        PolicyDebateMomentumReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_observations(
    observations: Iterable[PolicyDebateMomentumObservation],
) -> tuple[PolicyDebateMomentumObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain PolicyDebateMomentumObservation")
    normalized = tuple(observations)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyDebateMomentumObservation:
            raise ValueError("observations must contain PolicyDebateMomentumObservation")
        _require_hard_flags(value, "observation")
        if value.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(value.source_id)
    return normalized


def _require_canonical_rows(
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
) -> tuple[PolicyDebateMomentumDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = rows
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not PolicyDebateMomentumDigestRow:
            raise ValueError("rows must contain PolicyDebateMomentumDigestRow")
        _require_hard_flags(row, "row")
        _validate_row(row)
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id values")
        seen.add(row.source_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be canonical")
    return normalized


def _require_canonical_reason_code_counts(
    values: tuple[PolicyDebateMomentumReasonCodeCount, ...],
) -> tuple[PolicyDebateMomentumReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = values
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not PolicyDebateMomentumReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain PolicyDebateMomentumReasonCodeCount",
            )
        _require_hard_flags(value, "reason_code_count")
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen.add(value.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda value: value.reason_code)):
        raise ValueError("reason_code_counts must be canonical")
    return normalized


def _validate_row(row: PolicyDebateMomentumDigestRow) -> None:
    _validate_row_config_thresholds(row)
    expected_support_delta = _support_delta_share(
        row.pre_debate_support_share,
        row.post_debate_support_share,
    )
    if row.support_delta_share != expected_support_delta:
        raise ValueError("support_delta_share must match support shares")
    if row.absolute_support_move_share != _absolute_decimal(row.support_delta_share):
        raise ValueError("absolute_support_move_share must match support_delta_share")
    expected_score = _policy_debate_momentum_score(
        absolute_support_move_share=row.absolute_support_move_share,
        mention_velocity_delta=row.mention_velocity_delta,
        sentiment_delta=row.sentiment_delta,
        fresh_debate_window=row.hours_since_debate <= row.fresh_debate_window_hours,
        high_support_move_share=row.high_support_move_share,
        high_mention_velocity_delta=row.high_mention_velocity_delta,
        high_sentiment_delta=row.high_sentiment_delta,
    )
    if row.policy_debate_momentum_score != expected_score:
        raise ValueError("policy_debate_momentum_score must match row factors")
    expected_status = _row_momentum_status(
        row.policy_debate_momentum_score,
        watch_policy_debate_momentum_score=row.watch_policy_debate_momentum_score,
        blocked_policy_debate_momentum_score=row.blocked_policy_debate_momentum_score,
    )
    if row.momentum_status != expected_status:
        raise ValueError("momentum_status must match policy_debate_momentum_score")
    expected_confidence_cap = _row_confidence_cap(
        momentum_status=row.momentum_status,
        source_fresh=row.source_age_seconds <= row.max_source_age_seconds,
        stale_confidence_cap=row.stale_confidence_cap,
        clear_confidence_cap=row.clear_confidence_cap,
    )
    if row.confidence_cap != expected_confidence_cap:
        raise ValueError("confidence_cap must match row factors")
    if row.capped_confidence != min(row.evidence_confidence, row.confidence_cap):
        raise ValueError("capped_confidence must match evidence_confidence")
    if row.momentum_direction != _momentum_direction(row.support_delta_share):
        raise ValueError("momentum_direction must match support_delta_share")
    expected_generated_reason_codes = _generated_row_reason_codes(
        momentum_status=row.momentum_status,
        absolute_support_move_share=row.absolute_support_move_share,
        mention_velocity_delta=row.mention_velocity_delta,
        sentiment_delta=row.sentiment_delta,
        fresh_debate_window=row.hours_since_debate <= row.fresh_debate_window_hours,
        source_fresh=row.source_age_seconds <= row.max_source_age_seconds,
        material_support_move_share=row.material_support_move_share,
        high_support_move_share=row.high_support_move_share,
        material_mention_velocity_delta=row.material_mention_velocity_delta,
        high_mention_velocity_delta=row.high_mention_velocity_delta,
        material_sentiment_delta=row.material_sentiment_delta,
        high_sentiment_delta=row.high_sentiment_delta,
    )
    actual_generated_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code.startswith(GENERATED_REASON_CODE_PREFIX)
    )
    if actual_generated_reason_codes != expected_generated_reason_codes:
        raise ValueError("reason_codes must match row factors")


def _validate_config_thresholds(config: PolicyDebateMomentumDigestConfig) -> None:
    if config.watch_policy_debate_momentum_score > config.blocked_policy_debate_momentum_score:
        raise ValueError(
            "watch_policy_debate_momentum_score must not exceed "
            "blocked_policy_debate_momentum_score",
        )
    if config.material_support_move_share > config.high_support_move_share:
        raise ValueError(
            "material_support_move_share must not exceed high_support_move_share",
        )
    if config.material_mention_velocity_delta > config.high_mention_velocity_delta:
        raise ValueError(
            "material_mention_velocity_delta must not exceed "
            "high_mention_velocity_delta",
        )
    if config.material_sentiment_delta > config.high_sentiment_delta:
        raise ValueError(
            "material_sentiment_delta must not exceed high_sentiment_delta",
        )


def _validate_row_config_thresholds(row: PolicyDebateMomentumDigestRow) -> None:
    if row.watch_policy_debate_momentum_score > row.blocked_policy_debate_momentum_score:
        raise ValueError(
            "watch_policy_debate_momentum_score must not exceed "
            "blocked_policy_debate_momentum_score",
        )
    if row.material_support_move_share > row.high_support_move_share:
        raise ValueError(
            "material_support_move_share must not exceed high_support_move_share",
        )
    if row.material_mention_velocity_delta > row.high_mention_velocity_delta:
        raise ValueError(
            "material_mention_velocity_delta must not exceed "
            "high_mention_velocity_delta",
        )
    if row.material_sentiment_delta > row.high_sentiment_delta:
        raise ValueError(
            "material_sentiment_delta must not exceed high_sentiment_delta",
        )


def _validate_report(report: PolicyDebateMomentumDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.blocked_count != _status_count(report.rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON_CODE):
        raise ValueError("stale_source_count must match rows")
    if report.positive_momentum_count != _direction_count(report.rows, "positive"):
        raise ValueError("positive_momentum_count must match rows")
    if report.negative_momentum_count != _direction_count(report.rows, "negative"):
        raise ValueError("negative_momentum_count must match rows")
    if report.material_support_move_count != _reason_count(
        report.rows,
        SUPPORT_MOVE_MATERIAL_REASON_CODE,
    ):
        raise ValueError("material_support_move_count must match rows")
    if report.mention_velocity_shift_count != _reason_count(
        report.rows,
        MENTION_VELOCITY_SHIFT_REASON_CODE,
    ):
        raise ValueError("mention_velocity_shift_count must match rows")
    if report.sentiment_shift_count != _reason_count(
        report.rows,
        SENTIMENT_SHIFT_REASON_CODE,
    ):
        raise ValueError("sentiment_shift_count must match rows")
    if report.fresh_debate_window_count != _reason_count(
        report.rows,
        FRESH_DEBATE_WINDOW_REASON_CODE,
    ):
        raise ValueError("fresh_debate_window_count must match rows")
    if report.max_policy_debate_momentum_score != _max_row_decimal(
        report.rows,
        "policy_debate_momentum_score",
    ):
        raise ValueError("max_policy_debate_momentum_score must match rows")
    if report.average_policy_debate_momentum_score != _ratio(
        _sum_decimal(row.policy_debate_momentum_score for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_policy_debate_momentum_score must match rows")
    if report.max_absolute_support_move_share != _max_row_decimal(
        report.rows,
        "absolute_support_move_share",
    ):
        raise ValueError("max_absolute_support_move_share must match rows")
    if report.average_absolute_support_move_share != _ratio(
        _sum_decimal(row.absolute_support_move_share for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_absolute_support_move_share must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _row_momentum_status(
    risk_score: Decimal,
    *,
    watch_policy_debate_momentum_score: Decimal,
    blocked_policy_debate_momentum_score: Decimal,
) -> str:
    if risk_score >= blocked_policy_debate_momentum_score:
        return BLOCKED_STATUS
    if risk_score >= watch_policy_debate_momentum_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_confidence_cap(
    *,
    momentum_status: str,
    source_fresh: bool,
    stale_confidence_cap: Decimal,
    clear_confidence_cap: Decimal,
) -> Decimal:
    caps = [ONE]
    if momentum_status == PASS_STATUS:
        caps.append(clear_confidence_cap)
    if not source_fresh:
        caps.append(stale_confidence_cap)
    return _quantize_decimal(min(caps))


def _digest_status(rows: tuple[PolicyDebateMomentumDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.momentum_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.momentum_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.momentum_status == status))


def _direction_count(
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
    direction: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.momentum_direction == direction))


def _reason_count(
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[PolicyDebateMomentumDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _support_delta_share(pre_debate_support_share: Decimal, post_debate_support_share: Decimal) -> Decimal:
    return _quantize_decimal(post_debate_support_share - pre_debate_support_share)


def _momentum_direction(support_delta_share: Decimal) -> str:
    if support_delta_share > ZERO:
        return "positive"
    if support_delta_share < ZERO:
        return "negative"
    return "flat"


def _absolute_decimal(value: Decimal) -> Decimal:
    return _quantize_decimal(abs(value))


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_signed_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_signed_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must use six-decimal precision")
    quantized = _quantize_decimal(value)
    if value != quantized or value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must use six-decimal precision")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_payload_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC at payload time")
    return value


ZERO_TIME_OFFSET = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _canonical_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_canonical_reason_codes(
    reason_codes: tuple[str, ...],
    field_name: str,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    original = reason_codes
    canonical = _canonical_reason_codes(original)
    if original != canonical:
        raise ValueError(f"{field_name} must be canonical")
    return original


def _require_hard_flags(value: object, label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: PolicyDebateMomentumDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.momentum_status],
        -row.policy_debate_momentum_score,
        row.event_key,
        row.source_id,
    )


def _payload_value(value: object, field_name: str) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{field_name} must be a Decimal at payload time")
        return f"{value:.6f}"
    if type(value) is datetime:
        return _require_payload_utc(field_name, value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name), field.name)
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item, field_name) for item in value]
    return value


def _revalidate_public_dataclass(value: object) -> None:
    if type(value) not in (
        PolicyDebateMomentumDigestConfig,
        PolicyDebateMomentumObservation,
        PolicyDebateMomentumDigestRow,
        PolicyDebateMomentumReasonCodeCount,
        PolicyDebateMomentumDigestReport,
    ):
        raise ValueError("payload contains unsupported dataclass")
    for field in fields(value):
        field_value = getattr(value, field.name)
        if type(field_value) is datetime:
            _require_payload_utc(field.name, field_value)
    rebuilt = type(value)(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )
    if rebuilt != value:
        raise ValueError("public dataclass must be canonical at payload time")
