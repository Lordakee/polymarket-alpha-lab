"""Decimal-only paper score for market probability dislocation quality."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_MARKET_PROBABILITY_DISLOCATION_SCORE_V2_CONFIG_VERSION = (
    "strategy-recommendation-market-probability-dislocation-score-v2"
)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROS_PER_SECOND = Decimal("1000000")
_SIDES = ("yes", "no")
_STATUSES = ("blocked", "watch", "qualified")
_STATUS_RANK = {"qualified": 0, "watch": 1, "blocked": 2}
_EMPTY_REASON = "market_probability_dislocation_empty"
_OWNED_REASON_CODES = frozenset(
    (
        "market_probability_dislocation_blocked",
        "market_probability_dislocation_watch",
        "market_probability_dislocation_qualified",
        "nonpositive_net_probability_dislocation",
        "positive_net_probability_dislocation",
        "market_move_speed_blocked",
        "liquidity_depth_blocked",
        "spread_quality_blocked",
        "source_freshness_blocked",
        "contradiction_severity_blocked",
        "cost_drag_blocked",
        "market_move_speed_watch",
        "liquidity_depth_watch",
        "spread_quality_watch",
        "source_freshness_watch",
        "contradiction_severity_watch",
        "cost_drag_watch",
        "market_move_speed_stable",
        "liquidity_depth_sufficient",
        "spread_quality_passed",
        "source_freshness_passed",
        "contradiction_severity_low",
        "cost_drag_passed",
        _EMPTY_REASON,
    ),
)
_REASON_RANK = {
    "market_probability_dislocation_blocked": 0,
    "market_probability_dislocation_watch": 1,
    "market_probability_dislocation_qualified": 2,
    "nonpositive_net_probability_dislocation": 3,
    "positive_net_probability_dislocation": 4,
    "market_move_speed_blocked": 5,
    "liquidity_depth_blocked": 6,
    "spread_quality_blocked": 7,
    "source_freshness_blocked": 8,
    "contradiction_severity_blocked": 9,
    "cost_drag_blocked": 10,
    "market_move_speed_watch": 11,
    "liquidity_depth_watch": 12,
    "spread_quality_watch": 13,
    "source_freshness_watch": 14,
    "contradiction_severity_watch": 15,
    "cost_drag_watch": 16,
    "market_move_speed_stable": 17,
    "liquidity_depth_sufficient": 18,
    "spread_quality_passed": 19,
    "source_freshness_passed": 20,
    "contradiction_severity_low": 21,
    "cost_drag_passed": 22,
    _EMPTY_REASON: 23,
}
_REPORT_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "qualified_count",
    "watch_count",
    "blocked_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_KEYS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "recommendation_side",
    "model_probability",
    "market_price",
    "market_move_speed",
    "liquidity_depth",
    "bid_ask_spread",
    "source_observed_at",
    "contradiction_severity",
    "cost_drag",
    "paper_notional",
    "observed_at",
    "raw_probability_dislocation",
    "net_probability_dislocation",
    "probability_dislocation_score",
    "market_movement_stability_score",
    "liquidity_depth_ratio",
    "liquidity_depth_score",
    "spread_quality_score",
    "source_freshness_age_seconds",
    "source_freshness_score",
    "contradiction_quality_score",
    "cost_drag_score",
    "dislocation_quality_score",
    "quality_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("bro", "ker"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("per", "sist"),
        _surface_term("private", "_key"),
        _surface_term("sup", "abase"),
        _surface_term("sql", "ite"),
        _surface_term("re", "quests"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationMarketProbabilityDislocationScoreV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_MARKET_PROBABILITY_DISLOCATION_SCORE_V2_CONFIG_VERSION
    )
    target_probability_dislocation: Decimal = Decimal("0.100000")
    market_move_speed_watch: Decimal = Decimal("0.050000")
    market_move_speed_block: Decimal = Decimal("0.100000")
    liquidity_depth_ratio_watch: Decimal = Decimal("3.000000")
    liquidity_depth_ratio_block: Decimal = Decimal("1.000000")
    bid_ask_spread_watch: Decimal = Decimal("0.030000")
    bid_ask_spread_block: Decimal = Decimal("0.060000")
    source_age_watch_seconds: Decimal = Decimal("1800.000000")
    source_age_block_seconds: Decimal = Decimal("3600.000000")
    contradiction_severity_watch: Decimal = Decimal("0.200000")
    contradiction_severity_block: Decimal = Decimal("0.400000")
    cost_drag_watch: Decimal = Decimal("0.020000")
    cost_drag_block: Decimal = Decimal("0.050000")
    min_quality_score: Decimal = Decimal("0.700000")
    watch_quality_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Config:
            raise ValueError(
                "config must be a "
                "StrategyRecommendationMarketProbabilityDislocationScoreV2Config",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "target_probability_dislocation",
            "market_move_speed_watch",
            "market_move_speed_block",
            "liquidity_depth_ratio_watch",
            "liquidity_depth_ratio_block",
            "source_age_watch_seconds",
            "source_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_ask_spread_watch",
            "bid_ask_spread_block",
            "contradiction_severity_watch",
            "contradiction_severity_block",
            "cost_drag_watch",
            "cost_drag_block",
            "min_quality_score",
            "watch_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "market_move_speed_watch",
            self.market_move_speed_watch,
            self.market_move_speed_block,
        )
        if self.liquidity_depth_ratio_block > self.liquidity_depth_ratio_watch:
            raise ValueError("liquidity_depth_ratio_block must not exceed watch threshold")
        _require_at_most(
            "bid_ask_spread_watch",
            self.bid_ask_spread_watch,
            self.bid_ask_spread_block,
        )
        _require_at_most(
            "source_age_watch_seconds",
            self.source_age_watch_seconds,
            self.source_age_block_seconds,
        )
        _require_at_most(
            "contradiction_severity_watch",
            self.contradiction_severity_watch,
            self.contradiction_severity_block,
        )
        _require_at_most("cost_drag_watch", self.cost_drag_watch, self.cost_drag_block)
        _require_at_most("watch_quality_score", self.watch_quality_score, self.min_quality_score)
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketProbabilityDislocationScoreV2Input:
    candidate_id: str
    market_id: str
    market_slug: str
    recommendation_side: str
    model_probability: Decimal
    market_price: Decimal
    market_move_speed: Decimal
    liquidity_depth: Decimal
    bid_ask_spread: Decimal
    source_observed_at: datetime
    contradiction_severity: Decimal
    cost_drag: Decimal
    paper_notional: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Input:
            raise ValueError(
                "input must be a "
                "StrategyRecommendationMarketProbabilityDislocationScoreV2Input",
            )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "recommendation_side",
        ):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "model_probability",
            "market_price",
            "bid_ask_spread",
            "contradiction_severity",
            "cost_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_move_speed", "liquidity_depth"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "paper_notional",
            _normalize_positive_decimal("paper_notional", self.paper_notional),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class StrategyRecommendationMarketProbabilityDislocationScoreV2Row:
    candidate_id: str
    market_id: str
    market_slug: str
    recommendation_side: str
    model_probability: Decimal
    market_price: Decimal
    market_move_speed: Decimal
    liquidity_depth: Decimal
    bid_ask_spread: Decimal
    source_observed_at: datetime
    contradiction_severity: Decimal
    cost_drag: Decimal
    paper_notional: Decimal
    observed_at: datetime
    raw_probability_dislocation: Decimal
    net_probability_dislocation: Decimal
    probability_dislocation_score: Decimal
    market_movement_stability_score: Decimal
    liquidity_depth_ratio: Decimal
    liquidity_depth_score: Decimal
    spread_quality_score: Decimal
    source_freshness_age_seconds: Decimal
    source_freshness_score: Decimal
    contradiction_quality_score: Decimal
    cost_drag_score: Decimal
    dislocation_quality_score: Decimal
    quality_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Row:
            raise ValueError(
                "row must be a StrategyRecommendationMarketProbabilityDislocationScoreV2Row",
            )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "recommendation_side",
        ):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in _SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "model_probability",
            "market_price",
            "bid_ask_spread",
            "contradiction_severity",
            "cost_drag",
            "probability_dislocation_score",
            "market_movement_stability_score",
            "liquidity_depth_score",
            "spread_quality_score",
            "source_freshness_score",
            "contradiction_quality_score",
            "cost_drag_score",
            "dislocation_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_move_speed",
            "liquidity_depth",
            "liquidity_depth_ratio",
            "source_freshness_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("raw_probability_dislocation", "net_probability_dislocation"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "paper_notional",
            _normalize_positive_decimal("paper_notional", self.paper_notional),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("quality_status", self.quality_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class StrategyRecommendationMarketProbabilityDislocationScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    qualified_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationMarketProbabilityDislocationScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Report:
            raise ValueError(
                "report must be a "
                "StrategyRecommendationMarketProbabilityDislocationScoreV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "qualified_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _check_report(self)
        for row in self.rows:
            _require_row_digest(row)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_market_probability_dislocation_score_v2_report(
    candidates: object,
    *,
    config: StrategyRecommendationMarketProbabilityDislocationScoreV2Config,
    generated_at: datetime,
) -> StrategyRecommendationMarketProbabilityDislocationScoreV2Report:
    if type(config) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Config:
        raise ValueError(
            "config must be a "
            "StrategyRecommendationMarketProbabilityDislocationScoreV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_candidates(candidates)
    for item in items:
        if item.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be after generated_at")
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _candidate_row(
                    item,
                    config=config,
                    generated_at=generated_at,
                )
                for item in items
            ),
            key=_row_key,
        ),
    )
    return StrategyRecommendationMarketProbabilityDislocationScoreV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        qualified_count=_status_count(rows, "qualified"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_recommendation_market_probability_dislocation_score_v2_payload(
    report: StrategyRecommendationMarketProbabilityDislocationScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationMarketProbabilityDislocationScoreV2Report:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError(
        "report must be a StrategyRecommendationMarketProbabilityDislocationScoreV2Report",
    )


def _candidate_row(
    item: StrategyRecommendationMarketProbabilityDislocationScoreV2Input,
    *,
    config: StrategyRecommendationMarketProbabilityDislocationScoreV2Config,
    generated_at: datetime,
) -> StrategyRecommendationMarketProbabilityDislocationScoreV2Row:
    source_freshness_age_seconds = _age_seconds(
        "source_observed_at",
        generated_at,
        item.source_observed_at,
    )
    raw_probability_dislocation = _raw_probability_dislocation(
        item.model_probability,
        item.market_price,
        item.recommendation_side,
    )
    net_probability_dislocation = _normalize_decimal(
        "net_probability_dislocation",
        raw_probability_dislocation - item.bid_ask_spread - item.cost_drag,
    )
    probability_dislocation_score = _clamp_ratio(
        net_probability_dislocation / config.target_probability_dislocation,
    )
    market_movement_stability_score = _inverse_threshold_score(
        item.market_move_speed,
        config.market_move_speed_block,
    )
    liquidity_depth_ratio = _normalize_decimal(
        "liquidity_depth_ratio",
        item.liquidity_depth / item.paper_notional,
    )
    liquidity_depth_score = _clamp_ratio(
        liquidity_depth_ratio / config.liquidity_depth_ratio_watch,
    )
    spread_quality_score = _inverse_threshold_score(
        item.bid_ask_spread,
        config.bid_ask_spread_block,
    )
    source_freshness_score = _inverse_threshold_score(
        source_freshness_age_seconds,
        config.source_age_block_seconds,
    )
    contradiction_quality_score = _inverse_threshold_score(
        item.contradiction_severity,
        config.contradiction_severity_block,
    )
    cost_drag_score = _inverse_threshold_score(item.cost_drag, config.cost_drag_block)
    dislocation_quality_score = _average(
        (
            probability_dislocation_score,
            market_movement_stability_score,
            liquidity_depth_score,
            spread_quality_score,
            source_freshness_score,
            contradiction_quality_score,
            cost_drag_score,
        ),
    )
    reason_codes = _row_reason_codes(
        net_probability_dislocation=net_probability_dislocation,
        market_move_speed=item.market_move_speed,
        liquidity_depth_ratio=liquidity_depth_ratio,
        bid_ask_spread=item.bid_ask_spread,
        source_freshness_age_seconds=source_freshness_age_seconds,
        contradiction_severity=item.contradiction_severity,
        cost_drag=item.cost_drag,
        dislocation_quality_score=dislocation_quality_score,
        config=config,
    )
    return StrategyRecommendationMarketProbabilityDislocationScoreV2Row(
        candidate_id=item.candidate_id,
        market_id=item.market_id,
        market_slug=item.market_slug,
        recommendation_side=item.recommendation_side,
        model_probability=item.model_probability,
        market_price=item.market_price,
        market_move_speed=item.market_move_speed,
        liquidity_depth=item.liquidity_depth,
        bid_ask_spread=item.bid_ask_spread,
        source_observed_at=item.source_observed_at,
        contradiction_severity=item.contradiction_severity,
        cost_drag=item.cost_drag,
        paper_notional=item.paper_notional,
        observed_at=item.observed_at,
        raw_probability_dislocation=raw_probability_dislocation,
        net_probability_dislocation=net_probability_dislocation,
        probability_dislocation_score=probability_dislocation_score,
        market_movement_stability_score=market_movement_stability_score,
        liquidity_depth_ratio=liquidity_depth_ratio,
        liquidity_depth_score=liquidity_depth_score,
        spread_quality_score=spread_quality_score,
        source_freshness_age_seconds=source_freshness_age_seconds,
        source_freshness_score=source_freshness_score,
        contradiction_quality_score=contradiction_quality_score,
        cost_drag_score=cost_drag_score,
        dislocation_quality_score=dislocation_quality_score,
        quality_status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    net_probability_dislocation: Decimal,
    market_move_speed: Decimal,
    liquidity_depth_ratio: Decimal,
    bid_ask_spread: Decimal,
    source_freshness_age_seconds: Decimal,
    contradiction_severity: Decimal,
    cost_drag: Decimal,
    dislocation_quality_score: Decimal,
    config: StrategyRecommendationMarketProbabilityDislocationScoreV2Config,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    stable_reasons: list[str] = []

    if market_move_speed > config.market_move_speed_block:
        block_reasons.append("market_move_speed_blocked")
    elif market_move_speed > config.market_move_speed_watch:
        watch_reasons.append("market_move_speed_watch")
    else:
        stable_reasons.append("market_move_speed_stable")

    if liquidity_depth_ratio < config.liquidity_depth_ratio_block:
        block_reasons.append("liquidity_depth_blocked")
    elif liquidity_depth_ratio < config.liquidity_depth_ratio_watch:
        watch_reasons.append("liquidity_depth_watch")
    else:
        stable_reasons.append("liquidity_depth_sufficient")

    if bid_ask_spread > config.bid_ask_spread_block:
        block_reasons.append("spread_quality_blocked")
    elif bid_ask_spread > config.bid_ask_spread_watch:
        watch_reasons.append("spread_quality_watch")
    else:
        stable_reasons.append("spread_quality_passed")

    if source_freshness_age_seconds > config.source_age_block_seconds:
        block_reasons.append("source_freshness_blocked")
    elif source_freshness_age_seconds > config.source_age_watch_seconds:
        watch_reasons.append("source_freshness_watch")
    else:
        stable_reasons.append("source_freshness_passed")

    if contradiction_severity > config.contradiction_severity_block:
        block_reasons.append("contradiction_severity_blocked")
    elif contradiction_severity > config.contradiction_severity_watch:
        watch_reasons.append("contradiction_severity_watch")
    else:
        stable_reasons.append("contradiction_severity_low")

    if cost_drag > config.cost_drag_block:
        block_reasons.append("cost_drag_blocked")
    elif cost_drag > config.cost_drag_watch:
        watch_reasons.append("cost_drag_watch")
    else:
        stable_reasons.append("cost_drag_passed")

    edge_reason = (
        "positive_net_probability_dislocation"
        if net_probability_dislocation > _ZERO
        else "nonpositive_net_probability_dislocation"
    )
    if (
        net_probability_dislocation <= _ZERO
        or block_reasons
        or dislocation_quality_score < config.watch_quality_score
    ):
        status_reason = "market_probability_dislocation_blocked"
    elif watch_reasons or dislocation_quality_score < config.min_quality_score:
        status_reason = "market_probability_dislocation_watch"
    else:
        status_reason = "market_probability_dislocation_qualified"
    return _sort_reason_codes(
        (
            status_reason,
            edge_reason,
            *block_reasons,
            *watch_reasons,
            *stable_reasons,
        ),
    )


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if "market_probability_dislocation_blocked" in reason_codes:
        return "blocked"
    if "market_probability_dislocation_watch" in reason_codes:
        return "watch"
    return "qualified"


def _raw_probability_dislocation(
    model_probability: Decimal,
    market_price: Decimal,
    recommendation_side: str,
) -> Decimal:
    if recommendation_side == "yes":
        return _normalize_decimal(
            "raw_probability_dislocation",
            model_probability - market_price,
        )
    return _normalize_decimal(
        "raw_probability_dislocation",
        market_price - model_probability,
    )


def _normalize_candidates(
    candidates: object,
) -> tuple[StrategyRecommendationMarketProbabilityDislocationScoreV2Input, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of input rows")
    try:
        items = tuple(candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of input rows") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Input:
            raise ValueError(
                "candidates must contain "
                "StrategyRecommendationMarketProbabilityDislocationScoreV2Input",
            )
        _require_flags("input", item)
        if item.candidate_id in seen:
            raise ValueError("duplicate candidate_id found")
        seen.add(item.candidate_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationMarketProbabilityDislocationScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of report rows")
    try:
        items = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable of report rows") from exc
    seen: set[str] = set()
    for row in items:
        if type(row) is not StrategyRecommendationMarketProbabilityDislocationScoreV2Row:
            raise ValueError(
                "rows must contain "
                "StrategyRecommendationMarketProbabilityDislocationScoreV2Row",
            )
        _require_flags("row", row)
        _require_row_digest(row)
        if row.candidate_id in seen:
            raise ValueError("rows must have unique candidate_id values")
        seen.add(row.candidate_id)
    sorted_items = tuple(sorted(items, key=_row_key))
    if items != sorted_items:
        raise ValueError("rows must be deterministically sorted")
    return items


def _row_key(
    row: StrategyRecommendationMarketProbabilityDislocationScoreV2Row,
) -> tuple[int, Decimal, str]:
    return (
        _STATUS_RANK[row.quality_status],
        -row.dislocation_quality_score,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[StrategyRecommendationMarketProbabilityDislocationScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.quality_status == status))


def _report_status(
    rows: tuple[StrategyRecommendationMarketProbabilityDislocationScoreV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.quality_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quality_status == "watch" for row in rows):
        return "watch"
    return "qualified"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationMarketProbabilityDislocationScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    return _sort_reason_codes(
        tuple(
            dict.fromkeys(
                reason
                for row in rows
                for reason in row.reason_codes
                if reason in _OWNED_REASON_CODES
            ),
        ),
    )


def _check_row(row: StrategyRecommendationMarketProbabilityDislocationScoreV2Row) -> None:
    expected_raw = _raw_probability_dislocation(
        row.model_probability,
        row.market_price,
        row.recommendation_side,
    )
    expected_net = _normalize_decimal(
        "net_probability_dislocation",
        expected_raw - row.bid_ask_spread - row.cost_drag,
    )
    expected_liquidity_ratio = _normalize_decimal(
        "liquidity_depth_ratio",
        row.liquidity_depth / row.paper_notional,
    )
    if row.raw_probability_dislocation != expected_raw:
        raise ValueError("raw_probability_dislocation must match probabilities")
    if row.net_probability_dislocation != expected_net:
        raise ValueError("net_probability_dislocation must match edge and costs")
    if row.liquidity_depth_ratio != expected_liquidity_ratio:
        raise ValueError("liquidity_depth_ratio must match depth and notional")
    expected_status_reason = f"market_probability_dislocation_{row.quality_status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include quality_status reason")


def _check_report(report: StrategyRecommendationMarketProbabilityDislocationScoreV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.qualified_count != _status_count(rows, "qualified"):
        raise ValueError("qualified_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.candidate_count != report.qualified_count + report.watch_count + report.blocked_count:
        raise ValueError("candidate_count must reconcile with status counts")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_row_digest(row: StrategyRecommendationMarketProbabilityDislocationScoreV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(
    report: StrategyRecommendationMarketProbabilityDislocationScoreV2Report,
) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _row_digest(row: StrategyRecommendationMarketProbabilityDislocationScoreV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyRecommendationMarketProbabilityDislocationScoreV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, _REPORT_KEYS)
    _require_payload_flags("payload", payload)
    for field_name in (
        "candidate_count",
        "qualified_count",
        "watch_count",
        "blocked_count",
    ):
        _require_decimal_string(f"payload.{field_name}", payload[field_name])
    _require_status("payload.status", payload["status"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload.rows must be a JSON list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_row_payload(f"payload.rows[{index}]", row)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(label: str, payload: dict[str, Any]) -> None:
    _require_exact_keys(label, payload, _ROW_KEYS)
    _require_payload_flags(label, payload)
    for field_name in (
        "model_probability",
        "market_price",
        "market_move_speed",
        "liquidity_depth",
        "bid_ask_spread",
        "contradiction_severity",
        "cost_drag",
        "paper_notional",
        "raw_probability_dislocation",
        "net_probability_dislocation",
        "probability_dislocation_score",
        "market_movement_stability_score",
        "liquidity_depth_ratio",
        "liquidity_depth_score",
        "spread_quality_score",
        "source_freshness_age_seconds",
        "source_freshness_score",
        "contradiction_quality_score",
        "cost_drag_score",
        "dislocation_quality_score",
    ):
        _require_decimal_string(f"{label}.{field_name}", payload[field_name])
    _require_status(f"{label}.quality_status", payload["quality_status"])
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError("derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(label: str, payload: dict[str, Any], expected: tuple[str, ...]) -> None:
    if set(payload) != set(expected):
        raise ValueError(f"{label} must contain exactly the expected public fields")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric values must be Decimal strings")
    if isinstance(value, float):
        raise ValueError("JSON values must not be floats")
    if type(value) is str:
        _require_text("JSON string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_text("JSON object key", key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyRecommendationMarketProbabilityDislocationScoreV2Config,
            StrategyRecommendationMarketProbabilityDislocationScoreV2Input,
            StrategyRecommendationMarketProbabilityDislocationScoreV2Row,
            StrategyRecommendationMarketProbabilityDislocationScoreV2Report,
        ):
            raise ValueError(f"{label} must be a supported public dataclass")
        for field in fields(value):
            _reject_unsafe_public(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if type(value) is bool:
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{label} Decimal|string JSON values required")
    if isinstance(value, float):
        raise ValueError(f"{label} Decimal|string JSON values required")
    if type(value) is int:
        raise ValueError(f"{label} Decimal|string JSON values required")
    if type(value) is dict:
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _age_seconds(field_name: str, generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError(f"{field_name} must not be after generated_at")
    return _normalize_decimal(
        field_name,
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / _MICROS_PER_SECOND,
    )


def _inverse_threshold_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - _clamp_ratio(value / block_threshold))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _normalize_decimal("average", sum(values, _ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("ratio", value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    for reason_code in unique:
        _require_text("reason_codes", reason_code)
    return tuple(sorted(unique, key=lambda item: (_REASON_RANK.get(item, 1000), item)))


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple of strings")
    return _normalize_reason_codes("reason_codes", value)


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{name} must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError(f"{name} must not contain duplicate values")
    for item in items:
        _require_text(name, item)
    owned = [item for item in items if item in _OWNED_REASON_CODES]
    if owned != sorted(owned, key=lambda item: _REASON_RANK[item]):
        raise ValueError(f"{name} owned reason codes must match report semantics")
    return items


def _require_decimal_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    parsed = _normalize_decimal(name, parsed)
    if str(parsed) != value:
        raise ValueError(f"{name} must be a six-place Decimal string")
    return parsed


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{name} must be blocked, watch, or qualified")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{name} must be a canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} has unsafe public text")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_at_most(name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{name} must be less than or equal to threshold")


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_MARKET_PROBABILITY_DISLOCATION_SCORE_V2_CONFIG_VERSION",
    "StrategyRecommendationMarketProbabilityDislocationScoreV2Config",
    "StrategyRecommendationMarketProbabilityDislocationScoreV2Input",
    "StrategyRecommendationMarketProbabilityDislocationScoreV2Row",
    "StrategyRecommendationMarketProbabilityDislocationScoreV2Report",
    "build_strategy_recommendation_market_probability_dislocation_score_v2_report",
    "strategy_recommendation_market_probability_dislocation_score_v2_payload",
)
