"""Readonly market depth, cost, and volatility quality scorecard report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_DEPTH_COST_VOLATILITY_SCORECARD_CONFIG_VERSION = (
    "research-market-depth-cost-volatility-scorecard-v0"
)

RATIO_QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "depth_cost_volatility_scorecard_empty"
PASS_REASON = "depth_cost_volatility_quality_pass"
SPREAD_WIDTH_BLOCK_REASON = "spread_width_block"
FEE_DRAG_BLOCK_REASON = "fee_drag_block"
SLIPPAGE_CUSHION_BLOCK_REASON = "slippage_cushion_block"
BOOK_AGE_BLOCK_REASON = "book_age_block"
VOLATILITY_BLOCK_REASON = "volatility_block"
SETTLEMENT_FRICTION_BLOCK_REASON = "settlement_friction_block"
SPREAD_WIDTH_WATCH_REASON = "spread_width_watch"
FEE_DRAG_WATCH_REASON = "fee_drag_watch"
SLIPPAGE_CUSHION_WATCH_REASON = "slippage_cushion_watch"
BOOK_AGE_WATCH_REASON = "book_age_watch"
VOLATILITY_WATCH_REASON = "volatility_watch"
SETTLEMENT_FRICTION_WATCH_REASON = "settlement_friction_watch"
QUALITY_SCORE_BLOCK_REASON = "quality_score_block"
QUALITY_SCORE_WATCH_REASON = "quality_score_watch"

REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    SPREAD_WIDTH_BLOCK_REASON,
    FEE_DRAG_BLOCK_REASON,
    SLIPPAGE_CUSHION_BLOCK_REASON,
    BOOK_AGE_BLOCK_REASON,
    VOLATILITY_BLOCK_REASON,
    SETTLEMENT_FRICTION_BLOCK_REASON,
    SPREAD_WIDTH_WATCH_REASON,
    FEE_DRAG_WATCH_REASON,
    SLIPPAGE_CUSHION_WATCH_REASON,
    BOOK_AGE_WATCH_REASON,
    VOLATILITY_WATCH_REASON,
    SETTLEMENT_FRICTION_WATCH_REASON,
    QUALITY_SCORE_BLOCK_REASON,
    QUALITY_SCORE_WATCH_REASON,
)
REPORT_REASON_CODES = tuple(reason for reason in REASON_CODES if reason != PASS_REASON)

DEPTH_BAND_SCORES = {
    "deep": Decimal("1.000000"),
    "adequate": Decimal("0.750000"),
    "thin": Decimal("0.350000"),
}

UNSAFE_PUBLIC_FIELD_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "http://",
        "https://",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_COST_VOLATILITY_SCORECARD_CONFIG_VERSION",
    "ResearchMarketDepthCostVolatilityScorecardConfig",
    "ResearchMarketDepthCostVolatilityScorecardObservation",
    "ResearchMarketDepthCostVolatilityScorecardRow",
    "ResearchMarketDepthCostVolatilityScorecardReport",
    "build_research_market_depth_cost_volatility_scorecard_report",
    "research_market_depth_cost_volatility_scorecard_report_payload",
    "validate_research_market_depth_cost_volatility_scorecard_public_payload",
)


@dataclass(frozen=True)
class ResearchMarketDepthCostVolatilityScorecardConfig:
    spread_watch_threshold: Decimal = Decimal("0.030000")
    spread_block_threshold: Decimal = Decimal("0.060000")
    fee_drag_watch_threshold: Decimal = Decimal("0.010000")
    fee_drag_block_threshold: Decimal = Decimal("0.030000")
    slippage_cushion_watch_threshold: Decimal = Decimal("0.050000")
    slippage_cushion_block_threshold: Decimal = Decimal("0.020000")
    book_age_watch_seconds: Decimal = Decimal("300.000000")
    book_age_block_seconds: Decimal = Decimal("900.000000")
    volatility_watch_threshold: Decimal = Decimal("0.080000")
    volatility_block_threshold: Decimal = Decimal("0.160000")
    settlement_friction_watch_threshold: Decimal = Decimal("0.050000")
    settlement_friction_block_threshold: Decimal = Decimal("0.100000")
    quality_score_watch_threshold: Decimal = Decimal("0.700000")
    quality_score_block_threshold: Decimal = Decimal("0.400000")
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_COST_VOLATILITY_SCORECARD_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostVolatilityScorecardConfig, "config")
        for field_name in (
            "spread_watch_threshold",
            "spread_block_threshold",
            "fee_drag_watch_threshold",
            "fee_drag_block_threshold",
            "slippage_cushion_watch_threshold",
            "slippage_cushion_block_threshold",
            "volatility_watch_threshold",
            "volatility_block_threshold",
            "settlement_friction_watch_threshold",
            "settlement_friction_block_threshold",
            "quality_score_watch_threshold",
            "quality_score_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("book_age_watch_seconds", "book_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        _require_increasing_thresholds(
            "spread",
            self.spread_watch_threshold,
            self.spread_block_threshold,
        )
        _require_increasing_thresholds(
            "fee_drag",
            self.fee_drag_watch_threshold,
            self.fee_drag_block_threshold,
        )
        _require_decreasing_thresholds(
            "slippage_cushion",
            self.slippage_cushion_watch_threshold,
            self.slippage_cushion_block_threshold,
        )
        _require_increasing_thresholds(
            "book_age",
            self.book_age_watch_seconds,
            self.book_age_block_seconds,
        )
        _require_increasing_thresholds(
            "volatility",
            self.volatility_watch_threshold,
            self.volatility_block_threshold,
        )
        _require_increasing_thresholds(
            "settlement_friction",
            self.settlement_friction_watch_threshold,
            self.settlement_friction_block_threshold,
        )
        _require_decreasing_thresholds(
            "quality_score",
            self.quality_score_watch_threshold,
            self.quality_score_block_threshold,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string(
                "config_version",
                self.config_version,
                check_value_surface=False,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostVolatilityScorecardObservation:
    cohort_key: str
    depth_band: str
    spread_width: Decimal
    fee_drag: Decimal
    slippage_cushion: Decimal
    book_age_seconds: Decimal
    volatility: Decimal
    settlement_friction: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthCostVolatilityScorecardObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "cohort_key",
            _require_public_string("cohort_key", self.cohort_key),
        )
        object.__setattr__(
            self,
            "depth_band",
            _require_known_value("depth_band", self.depth_band, tuple(DEPTH_BAND_SCORES)),
        )
        for field_name in (
            "spread_width",
            "fee_drag",
            "slippage_cushion",
            "volatility",
            "settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_seconds("book_age_seconds", self.book_age_seconds),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostVolatilityScorecardRow:
    cohort_key: str
    depth_band: str
    spread_width: Decimal
    fee_drag: Decimal
    slippage_cushion: Decimal
    book_age_seconds: Decimal
    volatility: Decimal
    settlement_friction: Decimal
    depth_band_score: Decimal
    total_cost_drag: Decimal
    quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostVolatilityScorecardRow, "row")
        object.__setattr__(
            self,
            "cohort_key",
            _require_public_string("cohort_key", self.cohort_key),
        )
        object.__setattr__(
            self,
            "depth_band",
            _require_known_value("depth_band", self.depth_band, tuple(DEPTH_BAND_SCORES)),
        )
        for field_name in (
            "spread_width",
            "fee_drag",
            "slippage_cushion",
            "volatility",
            "settlement_friction",
            "depth_band_score",
            "total_cost_drag",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "book_age_seconds",
            _require_nonnegative_seconds("book_age_seconds", self.book_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        _require_known_value("status", self.status, STATUSES)
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        if self.depth_band_score != DEPTH_BAND_SCORES[self.depth_band]:
            raise ValueError("depth_band_score is inconsistent with depth_band")
        if self.total_cost_drag != _quantize_ratio(self.spread_width + self.fee_drag):
            raise ValueError("total_cost_drag is inconsistent with spread_width and fee_drag")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthCostVolatilityScorecardReport:
    generated_at: datetime
    config_version: str
    spread_watch_threshold: Decimal
    spread_block_threshold: Decimal
    fee_drag_watch_threshold: Decimal
    fee_drag_block_threshold: Decimal
    slippage_cushion_watch_threshold: Decimal
    slippage_cushion_block_threshold: Decimal
    book_age_watch_seconds: Decimal
    book_age_block_seconds: Decimal
    volatility_watch_threshold: Decimal
    volatility_block_threshold: Decimal
    settlement_friction_watch_threshold: Decimal
    settlement_friction_block_threshold: Decimal
    quality_score_watch_threshold: Decimal
    quality_score_block_threshold: Decimal
    cohort_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal
    average_quality_score: Decimal
    max_total_cost_drag: Decimal
    max_book_age_seconds: Decimal
    max_volatility: Decimal
    max_settlement_friction: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthCostVolatilityScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string(
                "config_version",
                self.config_version,
                check_value_surface=False,
            ),
        )
        for field_name in (
            "spread_watch_threshold",
            "spread_block_threshold",
            "fee_drag_watch_threshold",
            "fee_drag_block_threshold",
            "slippage_cushion_watch_threshold",
            "slippage_cushion_block_threshold",
            "volatility_watch_threshold",
            "volatility_block_threshold",
            "settlement_friction_watch_threshold",
            "settlement_friction_block_threshold",
            "quality_score_watch_threshold",
            "quality_score_block_threshold",
            "cohort_count",
            "pass_count",
            "watch_count",
            "block_count",
            "pass_ratio",
            "average_quality_score",
            "max_total_cost_drag",
            "max_volatility",
            "max_settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_or_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("book_age_watch_seconds", "book_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_book_age_seconds",
            _require_nonnegative_seconds("max_book_age_seconds", self.max_book_age_seconds),
        )
        _require_known_value("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_payload(_unsigned_payload(self)),
            )
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _digest_payload(_unsigned_payload(self)):
                raise ValueError("derived_validation_digest does not match report payload")


def build_research_market_depth_cost_volatility_scorecard_report(
    observations: tuple[ResearchMarketDepthCostVolatilityScorecardObservation, ...]
    | list[ResearchMarketDepthCostVolatilityScorecardObservation],
    *,
    config: ResearchMarketDepthCostVolatilityScorecardConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchMarketDepthCostVolatilityScorecardReport:
    cfg = config if config is not None else ResearchMarketDepthCostVolatilityScorecardConfig()
    if type(cfg) is not ResearchMarketDepthCostVolatilityScorecardConfig:
        raise ValueError("config must be a ResearchMarketDepthCostVolatilityScorecardConfig")
    if generated_at is None:
        raise ValueError("generated_at must be provided for deterministic report payload")
    report_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(_row_from_observation(observation, cfg) for observation in observations)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    cohort_count = _count_decimal(sorted_rows)
    pass_count = _status_count(sorted_rows, "pass")
    watch_count = _status_count(sorted_rows, "watch")
    block_count = _status_count(sorted_rows, "block")
    pass_ratio = _quantize_ratio(pass_count / cohort_count) if cohort_count > ZERO else ZERO
    average_quality_score = (
        _quantize_ratio(
            sum((row.quality_score for row in sorted_rows), start=ZERO) / cohort_count,
        )
        if cohort_count > ZERO
        else ZERO
    )
    reason_codes = _report_reason_codes(sorted_rows)
    return ResearchMarketDepthCostVolatilityScorecardReport(
        generated_at=report_generated_at,
        config_version=cfg.config_version,
        spread_watch_threshold=cfg.spread_watch_threshold,
        spread_block_threshold=cfg.spread_block_threshold,
        fee_drag_watch_threshold=cfg.fee_drag_watch_threshold,
        fee_drag_block_threshold=cfg.fee_drag_block_threshold,
        slippage_cushion_watch_threshold=cfg.slippage_cushion_watch_threshold,
        slippage_cushion_block_threshold=cfg.slippage_cushion_block_threshold,
        book_age_watch_seconds=cfg.book_age_watch_seconds,
        book_age_block_seconds=cfg.book_age_block_seconds,
        volatility_watch_threshold=cfg.volatility_watch_threshold,
        volatility_block_threshold=cfg.volatility_block_threshold,
        settlement_friction_watch_threshold=cfg.settlement_friction_watch_threshold,
        settlement_friction_block_threshold=cfg.settlement_friction_block_threshold,
        quality_score_watch_threshold=cfg.quality_score_watch_threshold,
        quality_score_block_threshold=cfg.quality_score_block_threshold,
        cohort_count=cohort_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        pass_ratio=pass_ratio,
        average_quality_score=average_quality_score,
        max_total_cost_drag=_max_row_decimal(sorted_rows, "total_cost_drag"),
        max_book_age_seconds=_max_row_decimal(sorted_rows, "book_age_seconds"),
        max_volatility=_max_row_decimal(sorted_rows, "volatility"),
        max_settlement_friction=_max_row_decimal(sorted_rows, "settlement_friction"),
        status=_report_status(sorted_rows),
        reason_codes=reason_codes,
        rows=sorted_rows,
    )


def research_market_depth_cost_volatility_scorecard_report_payload(
    report: ResearchMarketDepthCostVolatilityScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthCostVolatilityScorecardReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _PayloadFlags(report))
        _reject_unsafe_public_surface("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketDepthCostVolatilityScorecardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_market_depth_cost_volatility_scorecard_public_payload(payload)
    return payload


def validate_research_market_depth_cost_volatility_scorecard_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _validate_public_payload_statuses(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_observation(
    observation: ResearchMarketDepthCostVolatilityScorecardObservation,
    config: ResearchMarketDepthCostVolatilityScorecardConfig,
) -> ResearchMarketDepthCostVolatilityScorecardRow:
    if type(observation) is not ResearchMarketDepthCostVolatilityScorecardObservation:
        raise ValueError(
            "observation must be a ResearchMarketDepthCostVolatilityScorecardObservation",
        )
    _require_hard_flags("observation", observation)
    depth_band_score = DEPTH_BAND_SCORES[observation.depth_band]
    total_cost_drag = _quantize_ratio(observation.spread_width + observation.fee_drag)
    quality_score = _quality_score(observation, config, depth_band_score)
    reason_codes = _row_reason_codes(observation, config, quality_score)
    return ResearchMarketDepthCostVolatilityScorecardRow(
        cohort_key=observation.cohort_key,
        depth_band=observation.depth_band,
        spread_width=observation.spread_width,
        fee_drag=observation.fee_drag,
        slippage_cushion=observation.slippage_cushion,
        book_age_seconds=observation.book_age_seconds,
        volatility=observation.volatility,
        settlement_friction=observation.settlement_friction,
        depth_band_score=depth_band_score,
        total_cost_drag=total_cost_drag,
        quality_score=quality_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _quality_score(
    observation: ResearchMarketDepthCostVolatilityScorecardObservation,
    config: ResearchMarketDepthCostVolatilityScorecardConfig,
    depth_band_score: Decimal,
) -> Decimal:
    components = (
        depth_band_score,
        _upper_threshold_component(
            observation.spread_width,
            config.spread_watch_threshold,
            config.spread_block_threshold,
        ),
        _upper_threshold_component(
            observation.fee_drag,
            config.fee_drag_watch_threshold,
            config.fee_drag_block_threshold,
        ),
        _lower_threshold_component(
            observation.slippage_cushion,
            config.slippage_cushion_watch_threshold,
            config.slippage_cushion_block_threshold,
        ),
        _upper_threshold_component(
            observation.book_age_seconds,
            config.book_age_watch_seconds,
            config.book_age_block_seconds,
        ),
        _upper_threshold_component(
            observation.volatility,
            config.volatility_watch_threshold,
            config.volatility_block_threshold,
        ),
        _upper_threshold_component(
            observation.settlement_friction,
            config.settlement_friction_watch_threshold,
            config.settlement_friction_block_threshold,
        ),
    )
    return _quantize_ratio(sum(components, start=ZERO) / Decimal(len(components)))


def _upper_threshold_component(value: Decimal, watch: Decimal, block: Decimal) -> Decimal:
    if value <= watch:
        return ONE
    if value >= block:
        return ZERO
    return _quantize_ratio((block - value) / (block - watch))


def _lower_threshold_component(value: Decimal, watch: Decimal, block: Decimal) -> Decimal:
    if value >= watch:
        return ONE
    if value <= block:
        return ZERO
    return _quantize_ratio((value - block) / (watch - block))


def _row_reason_codes(
    observation: ResearchMarketDepthCostVolatilityScorecardObservation,
    config: ResearchMarketDepthCostVolatilityScorecardConfig,
    quality_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_upper_threshold_reason(
        reasons,
        observation.spread_width,
        config.spread_watch_threshold,
        config.spread_block_threshold,
        SPREAD_WIDTH_WATCH_REASON,
        SPREAD_WIDTH_BLOCK_REASON,
    )
    _append_upper_threshold_reason(
        reasons,
        observation.fee_drag,
        config.fee_drag_watch_threshold,
        config.fee_drag_block_threshold,
        FEE_DRAG_WATCH_REASON,
        FEE_DRAG_BLOCK_REASON,
    )
    _append_lower_threshold_reason(
        reasons,
        observation.slippage_cushion,
        config.slippage_cushion_watch_threshold,
        config.slippage_cushion_block_threshold,
        SLIPPAGE_CUSHION_WATCH_REASON,
        SLIPPAGE_CUSHION_BLOCK_REASON,
    )
    _append_upper_threshold_reason(
        reasons,
        observation.book_age_seconds,
        config.book_age_watch_seconds,
        config.book_age_block_seconds,
        BOOK_AGE_WATCH_REASON,
        BOOK_AGE_BLOCK_REASON,
    )
    _append_upper_threshold_reason(
        reasons,
        observation.volatility,
        config.volatility_watch_threshold,
        config.volatility_block_threshold,
        VOLATILITY_WATCH_REASON,
        VOLATILITY_BLOCK_REASON,
    )
    _append_upper_threshold_reason(
        reasons,
        observation.settlement_friction,
        config.settlement_friction_watch_threshold,
        config.settlement_friction_block_threshold,
        SETTLEMENT_FRICTION_WATCH_REASON,
        SETTLEMENT_FRICTION_BLOCK_REASON,
    )
    if not reasons:
        if quality_score <= config.quality_score_block_threshold:
            reasons.append(QUALITY_SCORE_BLOCK_REASON)
        elif quality_score < config.quality_score_watch_threshold:
            reasons.append(QUALITY_SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _append_upper_threshold_reason(
    reasons: list[str],
    value: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block:
        reasons.append(block_reason)
    elif value > watch:
        reasons.append(watch_reason)


def _append_lower_threshold_reason(
    reasons: list[str],
    value: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value <= block:
        reasons.append(block_reason)
    elif value < watch:
        reasons.append(watch_reason)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    row_reasons = {
        reason for row in rows for reason in row.reason_codes if reason != PASS_REASON
    }
    if not row_reasons:
        return ()
    return tuple(reason for reason in REPORT_REASON_CODES if reason in row_reasons)


def _row_sort_key(row: ResearchMarketDepthCostVolatilityScorecardRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        row.quality_score,
        -row.total_cost_drag,
        row.cohort_key,
    )


def _normalize_rows(
    rows: tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...],
) -> tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketDepthCostVolatilityScorecardRow:
            raise ValueError("rows must contain ResearchMarketDepthCostVolatilityScorecardRow")
    return rows


def _validate_report_consistency(
    report: ResearchMarketDepthCostVolatilityScorecardReport,
) -> None:
    rows = report.rows
    cohort_count = _count_decimal(rows)
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    if report.cohort_count != cohort_count:
        raise ValueError("cohort_count is inconsistent with rows")
    if report.pass_count != pass_count:
        raise ValueError("pass_count is inconsistent with rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count is inconsistent with rows")
    if report.block_count != block_count:
        raise ValueError("block_count is inconsistent with rows")
    expected_pass_ratio = (
        _quantize_ratio(pass_count / cohort_count) if cohort_count > ZERO else ZERO
    )
    if report.pass_ratio != expected_pass_ratio:
        raise ValueError("pass_ratio is inconsistent with rows")
    expected_average = (
        _quantize_ratio(sum((row.quality_score for row in rows), start=ZERO) / cohort_count)
        if cohort_count > ZERO
        else ZERO
    )
    if report.average_quality_score != expected_average:
        raise ValueError("average_quality_score is inconsistent with rows")
    if report.max_total_cost_drag != _max_row_decimal(rows, "total_cost_drag"):
        raise ValueError("max_total_cost_drag is inconsistent with rows")
    if report.max_book_age_seconds != _max_row_decimal(rows, "book_age_seconds"):
        raise ValueError("max_book_age_seconds is inconsistent with rows")
    if report.max_volatility != _max_row_decimal(rows, "volatility"):
        raise ValueError("max_volatility is inconsistent with rows")
    if report.max_settlement_friction != _max_row_decimal(rows, "settlement_friction"):
        raise ValueError("max_settlement_friction is inconsistent with rows")
    if report.status != _report_status(rows):
        raise ValueError("status is inconsistent with rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes are inconsistent with rows")


def _count_decimal(rows: tuple[object, ...]) -> Decimal:
    return _quantize_ratio(Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...],
    status: str,
) -> Decimal:
    return _quantize_ratio(Decimal(sum(1 for row in rows if row.status == status)))


def _max_row_decimal(
    rows: tuple[ResearchMarketDepthCostVolatilityScorecardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _unsigned_payload(report: ResearchMarketDepthCostVolatilityScorecardReport) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_value(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_field(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or type(value) is float or isinstance(value, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _validate_public_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_known_value("status", item, STATUSES)
            _validate_public_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_payload_statuses(item)


def _has_unsafe_public_field(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS)


def _has_unsafe_public_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_string(
    field_name: str,
    value: object,
    *,
    check_value_surface: bool = True,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > 96:
        raise ValueError(f"{field_name} is too long")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(f"{field_name} must be printable ASCII")
    if _has_unsafe_public_field(field_name):
        raise ValueError(f"unsafe public field: {field_name}")
    if check_value_surface and _has_unsafe_public_value(value):
        raise ValueError(f"unsafe public value for {field_name}")
    return value


def _require_known_value(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_known_value(field_name, value, allowed_values)
    normalized = tuple(dict.fromkeys(values))
    return tuple(reason for reason in allowed_values if reason in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_probability_or_count(field_name: str, value: object) -> Decimal:
    if field_name.endswith("_count"):
        return _require_nonnegative_decimal(field_name, value)
    return _require_probability(field_name, value)


def _require_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return normalized


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_seconds(field_name, value)
    if normalized == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value).quantize(
        SECOND_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(value)


def _require_increasing_thresholds(field_name: str, watch: Decimal, block: Decimal) -> None:
    if block <= watch:
        raise ValueError(f"{field_name}_block_threshold must exceed {field_name}_watch_threshold")


def _require_decreasing_thresholds(field_name: str, watch: Decimal, block: Decimal) -> None:
    if block >= watch:
        raise ValueError(f"{field_name}_block_threshold must be below {field_name}_watch_threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
