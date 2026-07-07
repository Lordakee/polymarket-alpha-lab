"""In-memory report-only Polymarket probability-event surface quality scorer."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


CONFIG_VERSION = "market_research_probability_event_surface_quality_v2"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

SURFACE_QUALITY_READY = "surface_quality_ready"
SURFACE_QUALITY_WATCH = "surface_quality_watch"
SURFACE_QUALITY_REVIEW = "surface_quality_review"

REASON_VAGUE_QUESTION = "vague_question"
REASON_UNCLEAR_RESOLUTION = "unclear_resolution_criteria"
REASON_LIMITED_SOURCE = "limited_source_availability"
REASON_CATALYST_TIMING_GAP = "catalyst_timing_gap"
REASON_THIN_LIQUIDITY = "thin_liquidity_depth"
REASON_HIGH_CONTRADICTION = "high_contradiction_risk"
REASON_LOW_SCORE = "low_surface_quality_score"


@dataclass(frozen=True)
class MarketResearchProbabilityEventSurfaceQualityConfig:
    config_version: str = CONFIG_VERSION
    question_specificity_weight: Decimal = Decimal("0.2000")
    resolution_criteria_weight: Decimal = Decimal("0.2000")
    source_availability_weight: Decimal = Decimal("0.2000")
    catalyst_timing_weight: Decimal = Decimal("0.1500")
    liquidity_depth_weight: Decimal = Decimal("0.1500")
    contradiction_risk_weight: Decimal = Decimal("0.1000")
    ready_quality_threshold: Decimal = Decimal("0.8000")
    watch_quality_threshold: Decimal = Decimal("0.6500")
    min_question_specificity_score: Decimal = Decimal("0.5500")
    min_resolution_criteria_clarity_score: Decimal = Decimal("0.6000")
    min_source_availability_score: Decimal = Decimal("0.5000")
    min_catalyst_timing_score: Decimal = Decimal("0.5000")
    min_liquidity_depth_score: Decimal = Decimal("0.5000")
    max_contradiction_risk_score: Decimal = Decimal("0.4000")
    question_specificity_target_words: Decimal = Decimal("12")
    resolution_criteria_target_words: Decimal = Decimal("14")
    source_reference_target_count: Decimal = Decimal("3")
    ideal_liquidity_depth_usd: Decimal = Decimal("5000")
    min_catalyst_hours: Decimal = Decimal("6")
    max_catalyst_hours: Decimal = Decimal("720")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchProbabilityEventSurfaceQualityConfig:
            raise TypeError(
                "MarketResearchProbabilityEventSurfaceQualityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchProbabilityEventSurfaceQualityConfig:
            raise ValueError(
                "config must be exactly MarketResearchProbabilityEventSurfaceQualityConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "question_specificity_weight",
            "resolution_criteria_weight",
            "source_availability_weight",
            "catalyst_timing_weight",
            "liquidity_depth_weight",
            "contradiction_risk_weight",
            "ready_quality_threshold",
            "watch_quality_threshold",
            "min_question_specificity_score",
            "min_resolution_criteria_clarity_score",
            "min_source_availability_score",
            "min_catalyst_timing_score",
            "min_liquidity_depth_score",
            "max_contradiction_risk_score",
        ):
            object.__setattr__(self, field_name, _normalize_probability(field_name, getattr(self, field_name)))
        for field_name in (
            "question_specificity_target_words",
            "resolution_criteria_target_words",
            "source_reference_target_count",
            "ideal_liquidity_depth_usd",
            "min_catalyst_hours",
            "max_catalyst_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_weight_total(self)
        if self.ready_quality_threshold < self.watch_quality_threshold:
            raise ValueError("ready_quality_threshold must be at least watch_quality_threshold")
        if self.max_catalyst_hours < self.min_catalyst_hours:
            raise ValueError("max_catalyst_hours must be at least min_catalyst_hours")
        require_paper_only_flags("probability event surface quality config", self)


@dataclass(frozen=True)
class MarketResearchProbabilityEventSurfaceQualityInput:
    surface_id: str
    market_slug: str
    category: str
    question: str
    resolution_criteria: str
    observed_at: datetime
    catalyst_at: datetime | None
    source_references: tuple[str, ...]
    official_source_count: Decimal
    bid_depth_usd: Decimal
    ask_depth_usd: Decimal
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchProbabilityEventSurfaceQualityInput:
            raise TypeError(
                "MarketResearchProbabilityEventSurfaceQualityInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchProbabilityEventSurfaceQualityInput:
            raise ValueError("input must be exactly MarketResearchProbabilityEventSurfaceQualityInput")
        for field_name in ("surface_id", "market_slug", "category", "question", "resolution_criteria"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.catalyst_at is not None:
            object.__setattr__(self, "catalyst_at", _as_utc("catalyst_at", self.catalyst_at))
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        object.__setattr__(
            self,
            "official_source_count",
            _normalize_count_decimal("official_source_count", self.official_source_count),
        )
        if self.official_source_count > Decimal(len(self.source_references)):
            raise ValueError("official_source_count must not exceed source_references length")
        for field_name in ("bid_depth_usd", "ask_depth_usd"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_count_decimal("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "highest_contradiction_severity",
            _normalize_probability(
                "highest_contradiction_severity",
                self.highest_contradiction_severity,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("probability event surface quality input", self)


@dataclass(frozen=True)
class MarketResearchProbabilityEventSurfaceQualityRow:
    surface_id: str
    market_slug: str
    category: str
    question: str
    resolution_criteria: str
    observed_at: datetime
    catalyst_at: datetime | None
    source_references: tuple[str, ...]
    source_reference_count: Decimal
    official_source_count: Decimal
    bid_depth_usd: Decimal
    ask_depth_usd: Decimal
    total_depth_usd: Decimal
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    catalyst_hours_until: Decimal | None
    question_specificity_score: Decimal
    resolution_criteria_clarity_score: Decimal
    source_availability_score: Decimal
    catalyst_timing_score: Decimal
    liquidity_depth_score: Decimal
    contradiction_risk_score: Decimal
    quality_score: Decimal
    quality_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchProbabilityEventSurfaceQualityRow:
            raise TypeError(
                "MarketResearchProbabilityEventSurfaceQualityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchProbabilityEventSurfaceQualityRow:
            raise ValueError("row must be exactly MarketResearchProbabilityEventSurfaceQualityRow")
        for field_name in ("surface_id", "market_slug", "category", "question", "resolution_criteria"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.catalyst_at is not None:
            object.__setattr__(self, "catalyst_at", _as_utc("catalyst_at", self.catalyst_at))
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        for field_name in (
            "source_reference_count",
            "official_source_count",
            "contradiction_count",
        ):
            object.__setattr__(self, field_name, _normalize_count_decimal(field_name, getattr(self, field_name)))
        for field_name in (
            "bid_depth_usd",
            "ask_depth_usd",
            "total_depth_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_contradiction_severity",
            "question_specificity_score",
            "resolution_criteria_clarity_score",
            "source_availability_score",
            "catalyst_timing_score",
            "liquidity_depth_score",
            "contradiction_risk_score",
            "quality_score",
        ):
            object.__setattr__(self, field_name, _normalize_probability(field_name, getattr(self, field_name)))
        if self.catalyst_hours_until is not None:
            object.__setattr__(
                self,
                "catalyst_hours_until",
                _normalize_nonnegative_decimal("catalyst_hours_until", self.catalyst_hours_until),
            )
        if self.quality_status not in (
            SURFACE_QUALITY_READY,
            SURFACE_QUALITY_WATCH,
            SURFACE_QUALITY_REVIEW,
        ):
            raise ValueError("quality_status must be known")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        require_paper_only_flags("probability event surface quality row", self)


@dataclass(frozen=True)
class MarketResearchProbabilityEventSurfaceQualityReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    surface_count: Decimal
    category_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    review_count: Decimal
    average_quality_score: Decimal
    weakest_quality_score: Decimal
    rows: tuple[MarketResearchProbabilityEventSurfaceQualityRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchProbabilityEventSurfaceQualityReport:
            raise TypeError(
                "MarketResearchProbabilityEventSurfaceQualityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchProbabilityEventSurfaceQualityReport:
            raise ValueError("report must be exactly MarketResearchProbabilityEventSurfaceQualityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "surface_count",
            "category_count",
            "ready_count",
            "watch_count",
            "review_count",
        ):
            object.__setattr__(self, field_name, _normalize_count_decimal(field_name, getattr(self, field_name)))
        for field_name in ("average_quality_score", "weakest_quality_score"):
            object.__setattr__(self, field_name, _normalize_probability(field_name, getattr(self, field_name)))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        require_paper_only_flags("probability event surface quality report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "probability event surface quality report",
            _payload_value(asdict(self)),
        )


def build_market_research_probability_event_surface_quality_report(
    surfaces: tuple[MarketResearchProbabilityEventSurfaceQualityInput, ...],
    *,
    generated_at: datetime,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> MarketResearchProbabilityEventSurfaceQualityReport:
    if type(surfaces) is not tuple:
        raise ValueError("surfaces must be a tuple")
    if type(config) is not MarketResearchProbabilityEventSurfaceQualityConfig:
        raise ValueError("config must be a MarketResearchProbabilityEventSurfaceQualityConfig")
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_build_row(surface=surface, config=config) for surface in surfaces),
            key=lambda row: (row.category, row.surface_id, row.market_slug, row.observed_at),
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    return MarketResearchProbabilityEventSurfaceQualityReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        surface_count=Decimal(len({row.surface_id for row in rows})),
        category_count=Decimal(len({row.category for row in rows})),
        ready_count=_count_status(rows, SURFACE_QUALITY_READY),
        watch_count=_count_status(rows, SURFACE_QUALITY_WATCH),
        review_count=_count_status(rows, SURFACE_QUALITY_REVIEW),
        average_quality_score=_average(row.quality_score for row in rows),
        weakest_quality_score=_minimum(row.quality_score for row in rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_probability_event_surface_quality_payload(
    report: MarketResearchProbabilityEventSurfaceQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketResearchProbabilityEventSurfaceQualityReport:
        require_paper_only_flags("probability event surface quality report", report)
        _validate_report_consistency(report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a MarketResearchProbabilityEventSurfaceQualityReport or object")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    *,
    surface: MarketResearchProbabilityEventSurfaceQualityInput,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> MarketResearchProbabilityEventSurfaceQualityRow:
    if type(surface) is not MarketResearchProbabilityEventSurfaceQualityInput:
        raise ValueError("surfaces must contain MarketResearchProbabilityEventSurfaceQualityInput values")
    source_reference_count = Decimal(len(surface.source_references))
    total_depth_usd = _quantize(surface.bid_depth_usd + surface.ask_depth_usd)
    catalyst_hours_until = _catalyst_hours_until(surface.observed_at, surface.catalyst_at)
    question_specificity_score = _question_specificity_score(surface.question, config)
    resolution_criteria_clarity_score = _resolution_criteria_clarity_score(
        surface.resolution_criteria,
        config,
    )
    source_availability_score = _source_availability_score(
        source_reference_count,
        surface.official_source_count,
        config,
    )
    catalyst_timing_score = _catalyst_timing_score(catalyst_hours_until, config)
    liquidity_depth_score = _capped_ratio(total_depth_usd, config.ideal_liquidity_depth_usd)
    contradiction_risk_score = _contradiction_risk_score(
        contradiction_count=surface.contradiction_count,
        highest_contradiction_severity=surface.highest_contradiction_severity,
        source_reference_count=source_reference_count,
    )
    quality_score = _quality_score(
        question_specificity_score=question_specificity_score,
        resolution_criteria_clarity_score=resolution_criteria_clarity_score,
        source_availability_score=source_availability_score,
        catalyst_timing_score=catalyst_timing_score,
        liquidity_depth_score=liquidity_depth_score,
        contradiction_risk_score=contradiction_risk_score,
        config=config,
    )
    quality_status = _quality_status(
        question_specificity_score=question_specificity_score,
        resolution_criteria_clarity_score=resolution_criteria_clarity_score,
        contradiction_count=surface.contradiction_count,
        contradiction_risk_score=contradiction_risk_score,
        quality_score=quality_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        surface.reason_codes,
        question_specificity_score=question_specificity_score,
        resolution_criteria_clarity_score=resolution_criteria_clarity_score,
        source_availability_score=source_availability_score,
        catalyst_timing_score=catalyst_timing_score,
        liquidity_depth_score=liquidity_depth_score,
        contradiction_risk_score=contradiction_risk_score,
        quality_score=quality_score,
        quality_status=quality_status,
        config=config,
    )
    return MarketResearchProbabilityEventSurfaceQualityRow(
        surface_id=surface.surface_id,
        market_slug=surface.market_slug,
        category=surface.category,
        question=surface.question,
        resolution_criteria=surface.resolution_criteria,
        observed_at=surface.observed_at,
        catalyst_at=surface.catalyst_at,
        source_references=surface.source_references,
        source_reference_count=source_reference_count,
        official_source_count=surface.official_source_count,
        bid_depth_usd=surface.bid_depth_usd,
        ask_depth_usd=surface.ask_depth_usd,
        total_depth_usd=total_depth_usd,
        contradiction_count=surface.contradiction_count,
        highest_contradiction_severity=surface.highest_contradiction_severity,
        catalyst_hours_until=catalyst_hours_until,
        question_specificity_score=question_specificity_score,
        resolution_criteria_clarity_score=resolution_criteria_clarity_score,
        source_availability_score=source_availability_score,
        catalyst_timing_score=catalyst_timing_score,
        liquidity_depth_score=liquidity_depth_score,
        contradiction_risk_score=contradiction_risk_score,
        quality_score=quality_score,
        quality_status=quality_status,
        reason_codes=reason_codes,
    )


def _question_specificity_score(
    question: str,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> Decimal:
    normalized = _normalized_text(question)
    word_score = _capped_ratio(
        Decimal(len(_word_tokens(question))),
        config.question_specificity_target_words,
    )
    question_mark_score = ONE if "?" in question else ZERO
    outcome_marker_score = ONE if _contains_any(
        normalized,
        (
            "will ",
            " at least ",
            " above ",
            " below ",
            " between ",
            " exactly ",
            " over ",
            " under ",
        ),
    ) else ZERO
    timing_marker_score = ONE if _contains_any(
        normalized,
        (
            " by ",
            " before ",
            " after ",
            " on ",
            " during ",
            " in 202",
        ),
    ) else ZERO
    return _quantize(
        word_score * Decimal("0.4000")
        + question_mark_score * Decimal("0.2000")
        + outcome_marker_score * Decimal("0.2000")
        + timing_marker_score * Decimal("0.2000"),
    )


def _resolution_criteria_clarity_score(
    resolution_criteria: str,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> Decimal:
    normalized = _normalized_text(resolution_criteria)
    word_score = _capped_ratio(
        Decimal(len(_word_tokens(resolution_criteria))),
        config.resolution_criteria_target_words,
    )
    source_marker_score = ONE if _contains_any(
        normalized,
        (
            " official ",
            " source ",
            " reported ",
            " according ",
            " certified ",
        ),
    ) or "rules" in _word_tokens(resolution_criteria) else ZERO
    settlement_marker_score = ONE if _contains_any(
        normalized,
        (
            " resolve ",
            " resolves ",
            " settle ",
            " criteria ",
            " final ",
            " yes ",
            " no ",
        ),
    ) else ZERO
    boundary_marker_score = ONE if _contains_any(
        normalized,
        (
            " if ",
            " by ",
            " before ",
            " after ",
            " at least ",
            " greater than ",
            " less than ",
        ),
    ) else ZERO
    return _quantize(
        word_score * Decimal("0.4000")
        + source_marker_score * Decimal("0.3000")
        + settlement_marker_score * Decimal("0.1500")
        + boundary_marker_score * Decimal("0.1500"),
    )


def _source_availability_score(
    source_reference_count: Decimal,
    official_source_count: Decimal,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> Decimal:
    reference_score = _capped_ratio(source_reference_count, config.source_reference_target_count)
    official_target = _maximum(ONE, config.source_reference_target_count / Decimal("2"))
    official_score = _capped_ratio(official_source_count, official_target)
    return _quantize(reference_score * Decimal("0.7000") + official_score * Decimal("0.3000"))


def _catalyst_timing_score(
    catalyst_hours_until: Decimal | None,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> Decimal:
    if catalyst_hours_until is None or catalyst_hours_until == ZERO:
        return ZERO
    if catalyst_hours_until < config.min_catalyst_hours:
        return _quantize(
            _capped_ratio(catalyst_hours_until, config.min_catalyst_hours) * Decimal("0.5000"),
        )
    if catalyst_hours_until <= config.max_catalyst_hours:
        return ONE
    return _capped_ratio(config.max_catalyst_hours, catalyst_hours_until)


def _contradiction_risk_score(
    *,
    contradiction_count: Decimal,
    highest_contradiction_severity: Decimal,
    source_reference_count: Decimal,
) -> Decimal:
    reference_floor = _maximum(ONE, source_reference_count)
    count_score = _capped_ratio(contradiction_count, reference_floor)
    return _quantize((count_score + highest_contradiction_severity) / Decimal("2"))


def _quality_score(
    *,
    question_specificity_score: Decimal,
    resolution_criteria_clarity_score: Decimal,
    source_availability_score: Decimal,
    catalyst_timing_score: Decimal,
    liquidity_depth_score: Decimal,
    contradiction_risk_score: Decimal,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> Decimal:
    return _quantize(
        question_specificity_score * config.question_specificity_weight
        + resolution_criteria_clarity_score * config.resolution_criteria_weight
        + source_availability_score * config.source_availability_weight
        + catalyst_timing_score * config.catalyst_timing_weight
        + liquidity_depth_score * config.liquidity_depth_weight
        + (ONE - contradiction_risk_score) * config.contradiction_risk_weight,
    )


def _quality_status(
    *,
    question_specificity_score: Decimal,
    resolution_criteria_clarity_score: Decimal,
    contradiction_count: Decimal,
    contradiction_risk_score: Decimal,
    quality_score: Decimal,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> str:
    if (
        question_specificity_score < config.min_question_specificity_score
        or resolution_criteria_clarity_score < config.min_resolution_criteria_clarity_score
        or contradiction_count > ZERO
        or contradiction_risk_score >= config.max_contradiction_risk_score
    ):
        return SURFACE_QUALITY_REVIEW
    if quality_score >= config.ready_quality_threshold:
        return SURFACE_QUALITY_READY
    if quality_score >= config.watch_quality_threshold:
        return SURFACE_QUALITY_WATCH
    return SURFACE_QUALITY_REVIEW


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    question_specificity_score: Decimal,
    resolution_criteria_clarity_score: Decimal,
    source_availability_score: Decimal,
    catalyst_timing_score: Decimal,
    liquidity_depth_score: Decimal,
    contradiction_risk_score: Decimal,
    quality_score: Decimal,
    quality_status: str,
    config: MarketResearchProbabilityEventSurfaceQualityConfig,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(quality_status)
    if question_specificity_score < config.min_question_specificity_score:
        codes.add(REASON_VAGUE_QUESTION)
    if resolution_criteria_clarity_score < config.min_resolution_criteria_clarity_score:
        codes.add(REASON_UNCLEAR_RESOLUTION)
    if source_availability_score < config.min_source_availability_score:
        codes.add(REASON_LIMITED_SOURCE)
    if catalyst_timing_score < config.min_catalyst_timing_score:
        codes.add(REASON_CATALYST_TIMING_GAP)
    if liquidity_depth_score < config.min_liquidity_depth_score:
        codes.add(REASON_THIN_LIQUIDITY)
    if contradiction_risk_score >= config.max_contradiction_risk_score:
        codes.add(REASON_HIGH_CONTRADICTION)
    if quality_score < config.watch_quality_threshold:
        codes.add(REASON_LOW_SCORE)
    return tuple(sorted(codes))


def _catalyst_hours_until(observed_at: datetime, catalyst_at: datetime | None) -> Decimal | None:
    if catalyst_at is None:
        return None
    delta = catalyst_at - observed_at
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    if seconds <= ZERO:
        return ZERO
    return _quantize(seconds / Decimal("3600"))


def _word_tokens(value: str) -> tuple[str, ...]:
    normalized = _normalized_text(value)
    for character in "?!.,:;()[]{}":
        normalized = normalized.replace(character, " ")
    return tuple(token for token in normalized.split() if token)


def _normalized_text(value: str) -> str:
    return " " + " ".join(value.lower().split()) + " "


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def _reason_code_counts(
    rows: tuple[MarketResearchProbabilityEventSurfaceQualityRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, Decimal(counter[code])) for code in sorted(counter))


def _count_status(rows: tuple[MarketResearchProbabilityEventSurfaceQualityRow, ...], status: str) -> Decimal:
    return Decimal(sum(1 for row in rows if row.quality_status == status))


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _minimum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(min(items))


def _maximum(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    if numerator >= denominator:
        return ONE
    return _quantize(numerator / denominator)


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchProbabilityEventSurfaceQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is MarketResearchProbabilityEventSurfaceQualityRow for row in rows):
        raise ValueError("rows must contain MarketResearchProbabilityEventSurfaceQualityRow values")
    if rows != tuple(sorted(rows, key=lambda row: (row.category, row.surface_id, row.market_slug, row.observed_at))):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_source_references(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("source_references must be a tuple")
    references = tuple(value)
    for source_reference in references:
        _require_canonical_string("source_references", source_reference)
    if len(set(references)) != len(references):
        raise ValueError("source_references must be unique")
    return tuple(sorted(references))


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts values must be pairs")
        code, count = item
        _require_canonical_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_reason_codes(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_canonical_string("reason_codes", code)
    return tuple(sorted(codes))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_weight_total(config: MarketResearchProbabilityEventSurfaceQualityConfig) -> None:
    total = _quantize(
        config.question_specificity_weight
        + config.resolution_criteria_weight
        + config.source_availability_weight
        + config.catalyst_timing_weight
        + config.liquidity_depth_weight
        + config.contradiction_risk_weight,
    )
    if total != ONE:
        raise ValueError("quality weights must sum to 1")


def _validate_row_consistency(row: MarketResearchProbabilityEventSurfaceQualityRow) -> None:
    if row.source_reference_count != Decimal(len(row.source_references)):
        raise ValueError("source_reference_count must equal source_references length")
    if row.official_source_count > row.source_reference_count:
        raise ValueError("official_source_count must not exceed source_reference_count")
    if row.total_depth_usd != _quantize(row.bid_depth_usd + row.ask_depth_usd):
        raise ValueError("total_depth_usd must equal bid_depth_usd plus ask_depth_usd")


def _validate_report_consistency(report: MarketResearchProbabilityEventSurfaceQualityReport) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must equal rows length")
    if report.surface_count != Decimal(len({row.surface_id for row in report.rows})):
        raise ValueError("surface_count must match rows")
    if report.category_count != Decimal(len({row.category for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.ready_count != _count_status(report.rows, SURFACE_QUALITY_READY):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count_status(report.rows, SURFACE_QUALITY_WATCH):
        raise ValueError("watch_count must match rows")
    if report.review_count != _count_status(report.rows, SURFACE_QUALITY_REVIEW):
        raise ValueError("review_count must match rows")
    if report.average_quality_score != _average(row.quality_score for row in report.rows):
        raise ValueError("average_quality_score must match rows")
    if report.weakest_quality_score != _minimum(row.quality_score for row in report.rows):
        raise ValueError("weakest_quality_score must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_validation_digest(report: MarketResearchProbabilityEventSurfaceQualityReport) -> str:
    return _derived_validation_digest(asdict(report))


def _require_report_validation_digest(report: MarketResearchProbabilityEventSurfaceQualityReport) -> None:
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = {
        key: _payload_value(value)
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _payload_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            _require_canonical_string("payload key", key)
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type) and type(value).__module__ == __name__:
        return _payload_value(asdict(value))
    raise ValueError("public payload contains unsupported value")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("probability event surface quality payload", payload)
    _require_public_payload_flags("probability event surface quality payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _require_public_payload_flags(label: str, value: object) -> None:
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{label} {field_name} must be True")
        for child in value.values():
            _require_public_payload_flags(label, child)
        return
    if type(value) is list:
        for child in value:
            _require_public_payload_flags(label, child)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{label} must use safe serialized scalars")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)


__all__ = (
    "MarketResearchProbabilityEventSurfaceQualityConfig",
    "MarketResearchProbabilityEventSurfaceQualityInput",
    "MarketResearchProbabilityEventSurfaceQualityReport",
    "MarketResearchProbabilityEventSurfaceQualityRow",
    "build_market_research_probability_event_surface_quality_report",
    "market_research_probability_event_surface_quality_payload",
)
