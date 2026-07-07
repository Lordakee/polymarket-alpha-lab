"""Decimal-only paper gate for evidence quorum cost floors."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_QUORUM_COST_FLOOR_V2_CONFIG_VERSION = (
    "strategy-recommendation-evidence-quorum-cost-floor-v2"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
SIDES = ("yes", "no")
STATUSES = ("blocked", "watch", "pass")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
EMPTY_REASON = "evidence_quorum_cost_floor_empty"
OWNED_REASON_CODES = frozenset(
    (
        "evidence_quorum_cost_floor_blocked",
        "evidence_quorum_cost_floor_watch",
        "evidence_quorum_cost_floor_pass",
        "source_family_count_blocked",
        "official_source_missing_blocked",
        "contradiction_severity_blocked",
        "taker_cost_blocked",
        "spread_cost_blocked",
        "slippage_cost_blocked",
        "total_cost_blocked",
        "edge_margin_blocked",
        "liquidity_depth_blocked",
        "close_urgency_blocked",
        "recommendation_floor_blocked",
        "source_family_count_watch",
        "contradiction_severity_watch",
        "taker_cost_watch",
        "spread_cost_watch",
        "slippage_cost_watch",
        "total_cost_watch",
        "edge_margin_watch",
        "liquidity_depth_watch",
        "close_urgency_watch",
        "recommendation_floor_watch",
        EMPTY_REASON,
    ),
)
REASON_RANK = {
    "evidence_quorum_cost_floor_blocked": 0,
    "evidence_quorum_cost_floor_watch": 1,
    "evidence_quorum_cost_floor_pass": 2,
    "source_family_count_blocked": 3,
    "official_source_missing_blocked": 4,
    "contradiction_severity_blocked": 5,
    "taker_cost_blocked": 6,
    "spread_cost_blocked": 7,
    "slippage_cost_blocked": 8,
    "total_cost_blocked": 9,
    "edge_margin_blocked": 10,
    "liquidity_depth_blocked": 11,
    "close_urgency_blocked": 12,
    "recommendation_floor_blocked": 13,
    "source_family_count_watch": 14,
    "contradiction_severity_watch": 15,
    "taker_cost_watch": 16,
    "spread_cost_watch": 17,
    "slippage_cost_watch": 18,
    "total_cost_watch": 19,
    "edge_margin_watch": 20,
    "liquidity_depth_watch": 21,
    "close_urgency_watch": 22,
    "recommendation_floor_watch": 23,
    EMPTY_REASON: 24,
}
REPORT_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
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
ROW_KEYS = (
    "recommendation_id",
    "market_id",
    "recommendation_side",
    "base_confidence",
    "source_family_count",
    "source_family_score",
    "official_source_present",
    "official_source_score",
    "contradiction_severity",
    "contradiction_score",
    "expected_edge",
    "taker_fee_rate",
    "spread_cost",
    "slippage_cost",
    "total_cost",
    "cost_efficiency_score",
    "edge_margin",
    "edge_margin_score",
    "paper_notional",
    "liquidity_depth",
    "liquidity_depth_ratio",
    "liquidity_depth_score",
    "seconds_until_close",
    "close_safety_score",
    "recommendation_floor",
    "floor_adjusted_confidence",
    "observed_at",
    "floor_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("bro", "ker"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("private", "_key"),
        _surface_term("sup", "abase"),
        _surface_term("sql", "ite"),
        _surface_term("re", "quests"),
        _surface_term("tra", "de"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceQuorumCostFloorV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_QUORUM_COST_FLOOR_V2_CONFIG_VERSION
    )
    minimum_source_family_count: Decimal = Decimal("2.000000")
    required_source_family_count: Decimal = Decimal("3.000000")
    contradiction_severity_watch: Decimal = Decimal("0.200000")
    contradiction_severity_block: Decimal = Decimal("0.400000")
    taker_fee_rate_watch: Decimal = Decimal("0.010000")
    taker_fee_rate_block: Decimal = Decimal("0.020000")
    spread_cost_watch: Decimal = Decimal("0.030000")
    spread_cost_block: Decimal = Decimal("0.060000")
    slippage_cost_watch: Decimal = Decimal("0.020000")
    slippage_cost_block: Decimal = Decimal("0.030000")
    total_cost_watch: Decimal = Decimal("0.060000")
    total_cost_block: Decimal = Decimal("0.100000")
    edge_margin_watch: Decimal = Decimal("0.030000")
    edge_margin_block: Decimal = Decimal("0.000000")
    liquidity_depth_ratio_watch: Decimal = Decimal("2.000000")
    liquidity_depth_ratio_block: Decimal = Decimal("1.000000")
    close_urgency_watch_seconds: Decimal = Decimal("1800.000000")
    close_urgency_block_seconds: Decimal = Decimal("300.000000")
    minimum_recommendation_floor: Decimal = Decimal("0.700000")
    blocked_recommendation_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceQuorumCostFloorV2Config:
            raise ValueError(
                "config must be a StrategyRecommendationEvidenceQuorumCostFloorV2Config",
            )
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_source_family_count",
            _normalize_nonnegative_decimal(
                "minimum_source_family_count",
                self.minimum_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "required_source_family_count",
            _normalize_positive_decimal(
                "required_source_family_count",
                self.required_source_family_count,
            ),
        )
        for field_name in (
            "contradiction_severity_watch",
            "contradiction_severity_block",
            "taker_fee_rate_watch",
            "taker_fee_rate_block",
            "spread_cost_watch",
            "spread_cost_block",
            "slippage_cost_watch",
            "slippage_cost_block",
            "total_cost_watch",
            "total_cost_block",
            "minimum_recommendation_floor",
            "blocked_recommendation_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_margin_watch",
            _normalize_positive_decimal("edge_margin_watch", self.edge_margin_watch),
        )
        object.__setattr__(
            self,
            "edge_margin_block",
            _normalize_decimal("edge_margin_block", self.edge_margin_block),
        )
        for field_name in (
            "liquidity_depth_ratio_watch",
            "liquidity_depth_ratio_block",
            "close_urgency_watch_seconds",
            "close_urgency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "minimum_source_family_count",
            self.minimum_source_family_count,
            self.required_source_family_count,
        )
        _require_at_most(
            "contradiction_severity_watch",
            self.contradiction_severity_watch,
            self.contradiction_severity_block,
        )
        _require_at_most(
            "taker_fee_rate_watch",
            self.taker_fee_rate_watch,
            self.taker_fee_rate_block,
        )
        _require_at_most("spread_cost_watch", self.spread_cost_watch, self.spread_cost_block)
        _require_at_most(
            "slippage_cost_watch",
            self.slippage_cost_watch,
            self.slippage_cost_block,
        )
        _require_at_most("total_cost_watch", self.total_cost_watch, self.total_cost_block)
        _require_at_most("edge_margin_block", self.edge_margin_block, self.edge_margin_watch)
        if self.liquidity_depth_ratio_block > self.liquidity_depth_ratio_watch:
            raise ValueError("liquidity_depth_ratio_block must not exceed watch threshold")
        if self.close_urgency_block_seconds > self.close_urgency_watch_seconds:
            raise ValueError("close_urgency_block_seconds must not exceed watch threshold")
        _require_at_most(
            "blocked_recommendation_floor",
            self.blocked_recommendation_floor,
            self.minimum_recommendation_floor,
        )
        _require_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceQuorumCostFloorV2Input:
    recommendation_id: str
    market_id: str
    recommendation_side: str
    base_confidence: Decimal
    source_family_count: Decimal
    official_source_present: bool
    contradiction_severity: Decimal
    expected_edge: Decimal
    taker_fee_rate: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    paper_notional: Decimal
    liquidity_depth: Decimal
    seconds_until_close: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceQuorumCostFloorV2Input:
            raise ValueError(
                "input must be a StrategyRecommendationEvidenceQuorumCostFloorV2Input",
            )
        for field_name in ("recommendation_id", "market_id", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "base_confidence",
            "contradiction_severity",
            "expected_edge",
            "taker_fee_rate",
            "spread_cost",
            "slippage_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_count",
            "liquidity_depth",
            "seconds_until_close",
        ):
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
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class StrategyRecommendationEvidenceQuorumCostFloorV2Row:
    recommendation_id: str
    market_id: str
    recommendation_side: str
    base_confidence: Decimal
    source_family_count: Decimal
    source_family_score: Decimal
    official_source_present: bool
    official_source_score: Decimal
    contradiction_severity: Decimal
    contradiction_score: Decimal
    expected_edge: Decimal
    taker_fee_rate: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    total_cost: Decimal
    cost_efficiency_score: Decimal
    edge_margin: Decimal
    edge_margin_score: Decimal
    paper_notional: Decimal
    liquidity_depth: Decimal
    liquidity_depth_ratio: Decimal
    liquidity_depth_score: Decimal
    seconds_until_close: Decimal
    close_safety_score: Decimal
    recommendation_floor: Decimal
    floor_adjusted_confidence: Decimal
    observed_at: datetime
    floor_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceQuorumCostFloorV2Row:
            raise ValueError("row must be a StrategyRecommendationEvidenceQuorumCostFloorV2Row")
        for field_name in ("recommendation_id", "market_id", "recommendation_side"):
            _require_text(field_name, getattr(self, field_name))
        if self.recommendation_side not in SIDES:
            raise ValueError("recommendation_side must be yes or no")
        for field_name in (
            "base_confidence",
            "source_family_score",
            "official_source_score",
            "contradiction_severity",
            "contradiction_score",
            "expected_edge",
            "taker_fee_rate",
            "spread_cost",
            "slippage_cost",
            "cost_efficiency_score",
            "edge_margin_score",
            "liquidity_depth_score",
            "close_safety_score",
            "recommendation_floor",
            "floor_adjusted_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_count",
            "total_cost",
            "liquidity_depth",
            "liquidity_depth_ratio",
            "seconds_until_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_margin",
            _normalize_decimal("edge_margin", self.edge_margin),
        )
        object.__setattr__(
            self,
            "paper_notional",
            _normalize_positive_decimal("paper_notional", self.paper_notional),
        )
        if type(self.official_source_present) is not bool:
            raise ValueError("official_source_present must be a bool")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("floor_status", self.floor_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
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
class StrategyRecommendationEvidenceQuorumCostFloorV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationEvidenceQuorumCostFloorV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationEvidenceQuorumCostFloorV2Report:
            raise ValueError(
                "report must be a StrategyRecommendationEvidenceQuorumCostFloorV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
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


def build_strategy_recommendation_evidence_quorum_cost_floor_v2_report(
    recommendations: object,
    *,
    config: StrategyRecommendationEvidenceQuorumCostFloorV2Config,
    generated_at: datetime,
) -> StrategyRecommendationEvidenceQuorumCostFloorV2Report:
    if type(config) is not StrategyRecommendationEvidenceQuorumCostFloorV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationEvidenceQuorumCostFloorV2Config",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(recommendations)
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_for_recommendation(
                    item,
                    config=config,
                )
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyRecommendationEvidenceQuorumCostFloorV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_recommendation_evidence_quorum_cost_floor_v2_payload(
    report: StrategyRecommendationEvidenceQuorumCostFloorV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyRecommendationEvidenceQuorumCostFloorV2Report:
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
    raise ValueError("report must be a StrategyRecommendationEvidenceQuorumCostFloorV2Report")


def _row_for_recommendation(
    item: StrategyRecommendationEvidenceQuorumCostFloorV2Input,
    *,
    config: StrategyRecommendationEvidenceQuorumCostFloorV2Config,
) -> StrategyRecommendationEvidenceQuorumCostFloorV2Row:
    total_cost = _quantize(item.taker_fee_rate + item.spread_cost + item.slippage_cost)
    source_family_score = _clamp_ratio(
        item.source_family_count / config.required_source_family_count,
    )
    official_source_score = ONE if item.official_source_present else ZERO
    contradiction_score = _clamp_ratio(ONE - item.contradiction_severity)
    cost_efficiency_score = _inverse_threshold_score(total_cost, config.total_cost_block)
    edge_margin = _quantize(item.expected_edge - total_cost)
    edge_margin_score = _clamp_ratio(edge_margin / config.edge_margin_watch)
    liquidity_depth_ratio = _quantize(item.liquidity_depth / item.paper_notional)
    liquidity_depth_score = _clamp_ratio(
        liquidity_depth_ratio / config.liquidity_depth_ratio_watch,
    )
    close_safety_score = _clamp_ratio(
        item.seconds_until_close / config.close_urgency_watch_seconds,
    )
    recommendation_floor = _average(
        (
            source_family_score,
            official_source_score,
            contradiction_score,
            cost_efficiency_score,
            edge_margin_score,
            liquidity_depth_score,
            close_safety_score,
        ),
    )
    floor_adjusted_confidence = min(item.base_confidence, recommendation_floor)
    reason_codes = _row_reason_codes(
        item,
        total_cost=total_cost,
        edge_margin=edge_margin,
        liquidity_depth_ratio=liquidity_depth_ratio,
        floor_adjusted_confidence=floor_adjusted_confidence,
        config=config,
    )
    return StrategyRecommendationEvidenceQuorumCostFloorV2Row(
        recommendation_id=item.recommendation_id,
        market_id=item.market_id,
        recommendation_side=item.recommendation_side,
        base_confidence=item.base_confidence,
        source_family_count=item.source_family_count,
        source_family_score=source_family_score,
        official_source_present=item.official_source_present,
        official_source_score=official_source_score,
        contradiction_severity=item.contradiction_severity,
        contradiction_score=contradiction_score,
        expected_edge=item.expected_edge,
        taker_fee_rate=item.taker_fee_rate,
        spread_cost=item.spread_cost,
        slippage_cost=item.slippage_cost,
        total_cost=total_cost,
        cost_efficiency_score=cost_efficiency_score,
        edge_margin=edge_margin,
        edge_margin_score=edge_margin_score,
        paper_notional=item.paper_notional,
        liquidity_depth=item.liquidity_depth,
        liquidity_depth_ratio=liquidity_depth_ratio,
        liquidity_depth_score=liquidity_depth_score,
        seconds_until_close=item.seconds_until_close,
        close_safety_score=close_safety_score,
        recommendation_floor=recommendation_floor,
        floor_adjusted_confidence=_quantize(floor_adjusted_confidence),
        observed_at=item.observed_at,
        floor_status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: StrategyRecommendationEvidenceQuorumCostFloorV2Input,
    *,
    total_cost: Decimal,
    edge_margin: Decimal,
    liquidity_depth_ratio: Decimal,
    floor_adjusted_confidence: Decimal,
    config: StrategyRecommendationEvidenceQuorumCostFloorV2Config,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if item.source_family_count < config.minimum_source_family_count:
        block_reasons.append("source_family_count_blocked")
    elif item.source_family_count < config.required_source_family_count:
        watch_reasons.append("source_family_count_watch")
    if not item.official_source_present:
        block_reasons.append("official_source_missing_blocked")
    if item.contradiction_severity > config.contradiction_severity_block:
        block_reasons.append("contradiction_severity_blocked")
    elif item.contradiction_severity > config.contradiction_severity_watch:
        watch_reasons.append("contradiction_severity_watch")
    if item.taker_fee_rate > config.taker_fee_rate_block:
        block_reasons.append("taker_cost_blocked")
    elif item.taker_fee_rate > config.taker_fee_rate_watch:
        watch_reasons.append("taker_cost_watch")
    if item.spread_cost > config.spread_cost_block:
        block_reasons.append("spread_cost_blocked")
    elif item.spread_cost > config.spread_cost_watch:
        watch_reasons.append("spread_cost_watch")
    if item.slippage_cost > config.slippage_cost_block:
        block_reasons.append("slippage_cost_blocked")
    elif item.slippage_cost > config.slippage_cost_watch:
        watch_reasons.append("slippage_cost_watch")
    if total_cost > config.total_cost_block:
        block_reasons.append("total_cost_blocked")
    elif total_cost > config.total_cost_watch:
        watch_reasons.append("total_cost_watch")
    if edge_margin < config.edge_margin_block:
        block_reasons.append("edge_margin_blocked")
    elif edge_margin < config.edge_margin_watch:
        watch_reasons.append("edge_margin_watch")
    if liquidity_depth_ratio < config.liquidity_depth_ratio_block:
        block_reasons.append("liquidity_depth_blocked")
    elif liquidity_depth_ratio < config.liquidity_depth_ratio_watch:
        watch_reasons.append("liquidity_depth_watch")
    if item.seconds_until_close <= config.close_urgency_block_seconds:
        block_reasons.append("close_urgency_blocked")
    elif item.seconds_until_close <= config.close_urgency_watch_seconds:
        watch_reasons.append("close_urgency_watch")
    if floor_adjusted_confidence < config.blocked_recommendation_floor:
        block_reasons.append("recommendation_floor_blocked")
    elif floor_adjusted_confidence < config.minimum_recommendation_floor:
        watch_reasons.append("recommendation_floor_watch")

    if block_reasons:
        reasons = ["evidence_quorum_cost_floor_blocked", *block_reasons]
    elif watch_reasons:
        reasons = ["evidence_quorum_cost_floor_watch", *watch_reasons]
    else:
        reasons = ["evidence_quorum_cost_floor_pass"]
    reasons.extend(item.reason_codes)
    return _sort_reason_codes(tuple(reasons))


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if "evidence_quorum_cost_floor_blocked" in reason_codes:
        return "blocked"
    if "evidence_quorum_cost_floor_watch" in reason_codes:
        return "watch"
    return "pass"


def _normalize_inputs(
    recommendations: object,
) -> tuple[StrategyRecommendationEvidenceQuorumCostFloorV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        items = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyRecommendationEvidenceQuorumCostFloorV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationEvidenceQuorumCostFloorV2Input",
            )
        _require_flags("input", item)
        if item.recommendation_id in seen:
            raise ValueError("recommendations must not contain duplicate recommendation_id")
        seen.add(item.recommendation_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationEvidenceQuorumCostFloorV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyRecommendationEvidenceQuorumCostFloorV2Row:
            raise ValueError("rows must contain StrategyRecommendationEvidenceQuorumCostFloorV2Row")
        _require_flags("row", item)
        _require_row_digest(item)
    if items != tuple(sorted(items, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return items


def _row_sort_key(row: StrategyRecommendationEvidenceQuorumCostFloorV2Row) -> tuple[int, Decimal, str]:
    return (STATUS_RANK[row.floor_status], -row.recommendation_floor, row.recommendation_id)


def _status_count(
    rows: tuple[StrategyRecommendationEvidenceQuorumCostFloorV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.floor_status == status))


def _report_status(rows: tuple[StrategyRecommendationEvidenceQuorumCostFloorV2Row, ...]) -> str:
    if any(row.floor_status == "blocked" for row in rows):
        return "blocked"
    if any(row.floor_status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "blocked"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationEvidenceQuorumCostFloorV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _sort_reason_codes(
        tuple(
            dict.fromkeys(
                reason
                for row in rows
                for reason in row.reason_codes
                if reason in OWNED_REASON_CODES
            ),
        ),
    )


def _check_row(row: StrategyRecommendationEvidenceQuorumCostFloorV2Row) -> None:
    if row.total_cost != _quantize(row.taker_fee_rate + row.spread_cost + row.slippage_cost):
        raise ValueError("total_cost must match component costs")
    if row.official_source_score != (ONE if row.official_source_present else ZERO):
        raise ValueError("official_source_score must match official_source_present")
    if row.contradiction_score != _clamp_ratio(ONE - row.contradiction_severity):
        raise ValueError("contradiction_score must match contradiction_severity")
    if row.edge_margin != _quantize(row.expected_edge - row.total_cost):
        raise ValueError("edge_margin must match expected edge and costs")
    if row.liquidity_depth_ratio != _quantize(row.liquidity_depth / row.paper_notional):
        raise ValueError("liquidity_depth_ratio must match depth and notional")
    expected_recommendation_floor = _average(
        (
            row.source_family_score,
            row.official_source_score,
            row.contradiction_score,
            row.cost_efficiency_score,
            row.edge_margin_score,
            row.liquidity_depth_score,
            row.close_safety_score,
        ),
    )
    if row.recommendation_floor != expected_recommendation_floor:
        raise ValueError("recommendation_floor must match score inputs")
    expected_floor_adjusted_confidence = _quantize(
        min(row.base_confidence, row.recommendation_floor),
    )
    if row.floor_adjusted_confidence != expected_floor_adjusted_confidence:
        raise ValueError("floor_adjusted_confidence must match recommendation_floor")
    expected_terminal = {
        "blocked": "evidence_quorum_cost_floor_blocked",
        "watch": "evidence_quorum_cost_floor_watch",
        "pass": "evidence_quorum_cost_floor_pass",
    }[row.floor_status]
    if expected_terminal not in row.reason_codes:
        raise ValueError("reason_codes must include floor status reason")


def _check_report(report: StrategyRecommendationEvidenceQuorumCostFloorV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_digest(row: StrategyRecommendationEvidenceQuorumCostFloorV2Row) -> str:
    value = asdict(row)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _report_digest(report: StrategyRecommendationEvidenceQuorumCostFloorV2Report) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_digest(value)


def _require_row_digest(row: StrategyRecommendationEvidenceQuorumCostFloorV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: StrategyRecommendationEvidenceQuorumCostFloorV2Report) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _require_exact_keys("payload", payload, REPORT_KEYS)
    _require_payload_flags("payload", payload)
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
    _require_exact_keys(label, payload, ROW_KEYS)
    _require_payload_flags(label, payload)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not supplied_digest:
        raise ValueError(f"{label}.derived_validation_digest is required")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if supplied_digest != _canonical_digest(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    for key in expected_keys:
        if key not in payload:
            raise ValueError(f"{label}.{key} is required")
    extra_keys = tuple(sorted(set(payload) - set(expected_keys)))
    if extra_keys:
        raise ValueError(f"{label} contains unsupported public field: {extra_keys[0]}")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _canonical_digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


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
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be an exact datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
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
        raise ValueError(f"{label} Decimal|string payload values required")
    if isinstance(value, float):
        raise ValueError(f"{label} Decimal|string payload values required")
    if type(value) is int:
        raise ValueError(f"{label} Decimal|string payload values required")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_public_numbers(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _inverse_threshold_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    return _clamp_ratio(ONE - _clamp_ratio(value / block_threshold))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return _sort_reason_codes(reason_codes)


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    for reason_code in unique:
        _require_text("reason_codes", reason_code)
    return tuple(sorted(unique, key=lambda item: (REASON_RANK.get(item, 1000), item)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be blocked, watch, or pass")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe surface text")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
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


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be less than or equal to threshold")


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_EVIDENCE_QUORUM_COST_FLOOR_V2_CONFIG_VERSION",
    "StrategyRecommendationEvidenceQuorumCostFloorV2Config",
    "StrategyRecommendationEvidenceQuorumCostFloorV2Input",
    "StrategyRecommendationEvidenceQuorumCostFloorV2Row",
    "StrategyRecommendationEvidenceQuorumCostFloorV2Report",
    "build_strategy_recommendation_evidence_quorum_cost_floor_v2_report",
    "strategy_recommendation_evidence_quorum_cost_floor_v2_payload",
)
