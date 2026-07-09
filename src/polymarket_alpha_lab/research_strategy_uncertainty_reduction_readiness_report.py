"""Pure public uncertainty reduction readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_UNCERTAINTY_REDUCTION_READINESS_CONFIG_VERSION",
    "ResearchStrategyUncertaintyReductionReadinessCandidate",
    "ResearchStrategyUncertaintyReductionReadinessConfig",
    "ResearchStrategyUncertaintyReductionReadinessReasonCodeCount",
    "ResearchStrategyUncertaintyReductionReadinessReport",
    "ResearchStrategyUncertaintyReductionReadinessRow",
    "build_research_strategy_uncertainty_reduction_readiness_report",
    "research_strategy_uncertainty_reduction_readiness_digest",
    "research_strategy_uncertainty_reduction_readiness_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_UNCERTAINTY_REDUCTION_READINESS_CONFIG_VERSION = (
    "research-strategy-uncertainty-reduction-readiness-report-v0"
)
STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {"block": 2, "watch": 1, "pass": 0}
LOW_CURRENT_UNCERTAINTY_WATCH_SCORE = Decimal("0.300000")
LOW_CURRENT_UNCERTAINTY_BLOCK_SCORE = Decimal("0.200000")

NO_CANDIDATES_REASON = "no_uncertainty_reduction_readiness_candidates"

ROW_REASON_CODES = (
    "uncertainty_reduction_readiness_clear",
    "current_uncertainty_too_low_watch",
    "current_uncertainty_too_low_blocking",
    "source_freshness_watch",
    "source_freshness_blocking",
    "evidence_quality_watch",
    "evidence_quality_blocking",
    "liquidity_reliability_watch",
    "liquidity_reliability_blocking",
    "cost_drag_watch",
    "cost_drag_blocking",
    "resolution_clarity_watch",
    "resolution_clarity_blocking",
    "specialist_memory_confidence_watch",
    "specialist_memory_confidence_blocking",
    "composite_reduction_readiness_watch",
    "composite_reduction_readiness_blocking",
)
REPORT_REASON_CODES = (
    NO_CANDIDATES_REASON,
    "uncertainty_reduction_readiness_report_clear",
    "current_uncertainty_gap_detected",
    "source_freshness_gap_detected",
    "evidence_quality_gap_detected",
    "liquidity_reliability_gap_detected",
    "cost_drag_gap_detected",
    "resolution_clarity_gap_detected",
    "specialist_memory_confidence_gap_detected",
    "composite_reduction_readiness_gap_detected",
)
REASON_CODES = tuple(sorted(ROW_REASON_CODES + REPORT_REASON_CODES))


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyUncertaintyReductionReadinessConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_UNCERTAINTY_REDUCTION_READINESS_CONFIG_VERSION
    )
    pass_min_reduction_readiness_score: Decimal = Decimal("0.700000")
    watch_min_reduction_readiness_score: Decimal = Decimal("0.400000")
    current_uncertainty_weight: Decimal = Decimal("0.200000")
    source_freshness_weight: Decimal = Decimal("0.150000")
    evidence_quality_weight: Decimal = Decimal("0.150000")
    liquidity_reliability_weight: Decimal = Decimal("0.150000")
    cost_drag_weight: Decimal = Decimal("0.100000")
    resolution_clarity_weight: Decimal = Decimal("0.150000")
    specialist_memory_confidence_weight: Decimal = Decimal("0.100000")
    source_freshness_watch_age_seconds: Decimal = Decimal("3600.000000")
    source_freshness_block_age_seconds: Decimal = Decimal("14400.000000")
    cost_drag_watch_score: Decimal = Decimal("0.300000")
    cost_drag_block_score: Decimal = Decimal("0.700000")
    evidence_quality_watch_score: Decimal = Decimal("0.500000")
    evidence_quality_block_score: Decimal = Decimal("0.350000")
    liquidity_reliability_watch_score: Decimal = Decimal("0.450000")
    liquidity_reliability_block_score: Decimal = Decimal("0.200000")
    resolution_clarity_watch_score: Decimal = Decimal("0.500000")
    resolution_clarity_block_score: Decimal = Decimal("0.250000")
    memory_confidence_watch_score: Decimal = Decimal("0.450000")
    memory_confidence_block_score: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyUncertaintyReductionReadinessConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_min_reduction_readiness_score",
            "watch_min_reduction_readiness_score",
            "current_uncertainty_weight",
            "source_freshness_weight",
            "evidence_quality_weight",
            "liquidity_reliability_weight",
            "cost_drag_weight",
            "resolution_clarity_weight",
            "specialist_memory_confidence_weight",
            "cost_drag_watch_score",
            "cost_drag_block_score",
            "evidence_quality_watch_score",
            "evidence_quality_block_score",
            "liquidity_reliability_watch_score",
            "liquidity_reliability_block_score",
            "resolution_clarity_watch_score",
            "resolution_clarity_block_score",
            "memory_confidence_watch_score",
            "memory_confidence_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_watch_age_seconds",
            "source_freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_descending_threshold_pair(
            "pass_min_reduction_readiness_score",
            self.pass_min_reduction_readiness_score,
            "watch_min_reduction_readiness_score",
            self.watch_min_reduction_readiness_score,
        )
        _require_threshold_pair(
            "source_freshness_watch_age_seconds",
            self.source_freshness_watch_age_seconds,
            "source_freshness_block_age_seconds",
            self.source_freshness_block_age_seconds,
        )
        _require_threshold_pair(
            "cost_drag_watch_score",
            self.cost_drag_watch_score,
            "cost_drag_block_score",
            self.cost_drag_block_score,
        )
        _require_descending_threshold_pair(
            "evidence_quality_watch_score",
            self.evidence_quality_watch_score,
            "evidence_quality_block_score",
            self.evidence_quality_block_score,
        )
        _require_descending_threshold_pair(
            "liquidity_reliability_watch_score",
            self.liquidity_reliability_watch_score,
            "liquidity_reliability_block_score",
            self.liquidity_reliability_block_score,
        )
        _require_descending_threshold_pair(
            "resolution_clarity_watch_score",
            self.resolution_clarity_watch_score,
            "resolution_clarity_block_score",
            self.resolution_clarity_block_score,
        )
        _require_descending_threshold_pair(
            "memory_confidence_watch_score",
            self.memory_confidence_watch_score,
            "memory_confidence_block_score",
            self.memory_confidence_block_score,
        )
        _require_weights_total_one(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyReductionReadinessCandidate(_FinalPublicDataclass):
    raw_candidate_id: str
    observed_at: datetime
    current_uncertainty: Decimal
    source_age_seconds: Decimal
    evidence_quality: Decimal
    liquidity_reliability: Decimal
    cost_drag: Decimal
    resolution_clarity: Decimal
    specialist_memory_confidence: Decimal
    sensitive_context: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyUncertaintyReductionReadinessCandidate,
            "candidate",
        )
        _require_nonblank_string("raw_candidate_id", self.raw_candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "current_uncertainty",
            "evidence_quality",
            "liquidity_reliability",
            "cost_drag",
            "resolution_clarity",
            "specialist_memory_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sensitive_context",
            _normalize_optional_string("sensitive_context", self.sensitive_context),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyReductionReadinessRow(_FinalPublicDataclass):
    row_number: Decimal
    observed_at: datetime
    current_uncertainty_score: Decimal
    source_age_seconds: Decimal
    source_freshness_score: Decimal
    evidence_quality_score: Decimal
    liquidity_reliability_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    reduction_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyUncertaintyReductionReadinessRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "current_uncertainty_score",
            "source_freshness_score",
            "evidence_quality_score",
            "liquidity_reliability_score",
            "cost_drag_score",
            "cost_efficiency_score",
            "resolution_clarity_score",
            "specialist_memory_confidence_score",
            "reduction_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyReductionReadinessReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyUncertaintyReductionReadinessReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyUncertaintyReductionReadinessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_source_count: Decimal
    evidence_quality_gap_count: Decimal
    liquidity_reliability_gap_count: Decimal
    cost_drag_gap_count: Decimal
    resolution_clarity_gap_count: Decimal
    memory_confidence_gap_count: Decimal
    mean_reduction_readiness_score: Decimal
    mean_current_uncertainty: Decimal
    max_cost_drag_score: Decimal
    status: str
    reason_code_counts: tuple[
        ResearchStrategyUncertaintyReductionReadinessReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyUncertaintyReductionReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_source_count",
            "evidence_quality_gap_count",
            "liquidity_reliability_gap_count",
            "cost_drag_gap_count",
            "resolution_clarity_gap_count",
            "memory_confidence_gap_count",
            "mean_reduction_readiness_score",
            "mean_current_uncertainty",
            "max_cost_drag_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
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
        _require_digest("public_report_digest", self.public_report_digest)
        _validate_report(self)
        if self.public_report_digest != _expected_public_report_digest(self):
            raise ValueError("public_report_digest must match public report payload")
        _require_hard_flags("report", self)


@dataclass(frozen=True)
class _RowDraft:
    observed_at: datetime
    current_uncertainty_score: Decimal
    source_age_seconds: Decimal
    source_freshness_score: Decimal
    evidence_quality_score: Decimal
    liquidity_reliability_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    resolution_clarity_score: Decimal
    specialist_memory_confidence_score: Decimal
    reduction_readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def build_research_strategy_uncertainty_reduction_readiness_report(
    candidates: Iterable[ResearchStrategyUncertaintyReductionReadinessCandidate],
    *,
    config: ResearchStrategyUncertaintyReductionReadinessConfig,
    generated_at: datetime,
) -> ResearchStrategyUncertaintyReductionReadinessReport:
    if type(config) is not ResearchStrategyUncertaintyReductionReadinessConfig:
        raise ValueError(
            "config must be a ResearchStrategyUncertaintyReductionReadinessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates(candidates)
    for row in candidate_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be less than or equal to generated_at")
    drafts = tuple(_row_draft(row, config=config) for row in candidate_rows)
    rows = tuple(
        _row_from_draft(row_number=_count(index), draft=draft)
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "stale_source_count": _reason_count(
            rows,
            ("source_freshness_watch", "source_freshness_blocking"),
        ),
        "evidence_quality_gap_count": _reason_count(
            rows,
            ("evidence_quality_watch", "evidence_quality_blocking"),
        ),
        "liquidity_reliability_gap_count": _reason_count(
            rows,
            ("liquidity_reliability_watch", "liquidity_reliability_blocking"),
        ),
        "cost_drag_gap_count": _reason_count(
            rows,
            ("cost_drag_watch", "cost_drag_blocking"),
        ),
        "resolution_clarity_gap_count": _reason_count(
            rows,
            ("resolution_clarity_watch", "resolution_clarity_blocking"),
        ),
        "memory_confidence_gap_count": _reason_count(
            rows,
            (
                "specialist_memory_confidence_watch",
                "specialist_memory_confidence_blocking",
            ),
        ),
        "mean_reduction_readiness_score": _mean(
            tuple(row.reduction_readiness_score for row in rows),
        ),
        "mean_current_uncertainty": _mean(
            tuple(row.current_uncertainty_score for row in rows),
        ),
        "max_cost_drag_score": _max_decimal(tuple(row.cost_drag_score for row in rows)),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchStrategyUncertaintyReductionReadinessReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_strategy_uncertainty_reduction_readiness_report_payload(
    report: ResearchStrategyUncertaintyReductionReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyUncertaintyReductionReadinessReport:
        raise ValueError(
            "report must be a ResearchStrategyUncertaintyReductionReadinessReport",
        )
    _validate_report(report)
    if report.public_report_digest != _expected_public_report_digest(report):
        raise ValueError("public_report_digest must match public report payload")
    payload = _report_payload_without_digest_from_report(report)
    payload["public_report_digest"] = report.public_report_digest
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return ready


def research_strategy_uncertainty_reduction_readiness_digest(
    report: ResearchStrategyUncertaintyReductionReadinessReport,
) -> str:
    payload = research_strategy_uncertainty_reduction_readiness_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchStrategyUncertaintyReductionReadinessCandidate,
    *,
    config: ResearchStrategyUncertaintyReductionReadinessConfig,
) -> _RowDraft:
    source_freshness_score = _freshness_score(
        candidate.source_age_seconds,
        config.source_freshness_block_age_seconds,
    )
    cost_efficiency_score = _inverse_probability(candidate.cost_drag)
    reduction_readiness_score = _weighted_score(
        current_uncertainty_score=candidate.current_uncertainty,
        source_freshness_score=source_freshness_score,
        evidence_quality_score=candidate.evidence_quality,
        liquidity_reliability_score=candidate.liquidity_reliability,
        cost_efficiency_score=cost_efficiency_score,
        resolution_clarity_score=candidate.resolution_clarity,
        specialist_memory_confidence_score=candidate.specialist_memory_confidence,
        config=config,
    )
    status = _row_status(
        candidate=candidate,
        source_freshness_score=source_freshness_score,
        reduction_readiness_score=reduction_readiness_score,
        config=config,
    )
    return _RowDraft(
        observed_at=candidate.observed_at,
        current_uncertainty_score=candidate.current_uncertainty,
        source_age_seconds=candidate.source_age_seconds,
        source_freshness_score=source_freshness_score,
        evidence_quality_score=candidate.evidence_quality,
        liquidity_reliability_score=candidate.liquidity_reliability,
        cost_drag_score=candidate.cost_drag,
        cost_efficiency_score=cost_efficiency_score,
        resolution_clarity_score=candidate.resolution_clarity,
        specialist_memory_confidence_score=candidate.specialist_memory_confidence,
        reduction_readiness_score=reduction_readiness_score,
        status=status,
        reason_codes=_row_reason_codes(
            candidate=candidate,
            source_freshness_score=source_freshness_score,
            reduction_readiness_score=reduction_readiness_score,
            config=config,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
) -> ResearchStrategyUncertaintyReductionReadinessRow:
    return ResearchStrategyUncertaintyReductionReadinessRow(
        row_number=row_number,
        observed_at=draft.observed_at,
        current_uncertainty_score=draft.current_uncertainty_score,
        source_age_seconds=draft.source_age_seconds,
        source_freshness_score=draft.source_freshness_score,
        evidence_quality_score=draft.evidence_quality_score,
        liquidity_reliability_score=draft.liquidity_reliability_score,
        cost_drag_score=draft.cost_drag_score,
        cost_efficiency_score=draft.cost_efficiency_score,
        resolution_clarity_score=draft.resolution_clarity_score,
        specialist_memory_confidence_score=draft.specialist_memory_confidence_score,
        reduction_readiness_score=draft.reduction_readiness_score,
        status=draft.status,
        reason_codes=draft.reason_codes,
    )


def _weighted_score(
    *,
    current_uncertainty_score: Decimal,
    source_freshness_score: Decimal,
    evidence_quality_score: Decimal,
    liquidity_reliability_score: Decimal,
    cost_efficiency_score: Decimal,
    resolution_clarity_score: Decimal,
    specialist_memory_confidence_score: Decimal,
    config: ResearchStrategyUncertaintyReductionReadinessConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            current_uncertainty_score * config.current_uncertainty_weight
            + source_freshness_score * config.source_freshness_weight
            + evidence_quality_score * config.evidence_quality_weight
            + liquidity_reliability_score * config.liquidity_reliability_weight
            + cost_efficiency_score * config.cost_drag_weight
            + resolution_clarity_score * config.resolution_clarity_weight
            + specialist_memory_confidence_score
            * config.specialist_memory_confidence_weight
        )
    return _normalize_probability("reduction_readiness_score", score)


def _freshness_score(age_seconds: Decimal, block_age_seconds: Decimal) -> Decimal:
    if block_age_seconds <= ZERO:
        raise ValueError("source freshness denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        decay = age_seconds / block_age_seconds
        score = ONE - decay
    if score <= ZERO:
        return ZERO
    return _normalize_probability("source_freshness_score", score)


def _inverse_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("inverse_probability", ONE - value)


def _row_status(
    *,
    candidate: ResearchStrategyUncertaintyReductionReadinessCandidate,
    source_freshness_score: Decimal,
    reduction_readiness_score: Decimal,
    config: ResearchStrategyUncertaintyReductionReadinessConfig,
) -> str:
    if (
        candidate.current_uncertainty <= LOW_CURRENT_UNCERTAINTY_BLOCK_SCORE
        or candidate.source_age_seconds >= config.source_freshness_block_age_seconds
        or candidate.evidence_quality <= config.evidence_quality_block_score
        or candidate.liquidity_reliability <= config.liquidity_reliability_block_score
        or candidate.cost_drag >= config.cost_drag_block_score
        or candidate.resolution_clarity <= config.resolution_clarity_block_score
        or candidate.specialist_memory_confidence <= config.memory_confidence_block_score
        or reduction_readiness_score < config.watch_min_reduction_readiness_score
    ):
        return "block"
    if (
        candidate.current_uncertainty <= LOW_CURRENT_UNCERTAINTY_WATCH_SCORE
        or candidate.source_age_seconds >= config.source_freshness_watch_age_seconds
        or source_freshness_score <= _freshness_score(
            config.source_freshness_watch_age_seconds,
            config.source_freshness_block_age_seconds,
        )
        or candidate.evidence_quality <= config.evidence_quality_watch_score
        or candidate.liquidity_reliability <= config.liquidity_reliability_watch_score
        or candidate.cost_drag >= config.cost_drag_watch_score
        or candidate.resolution_clarity <= config.resolution_clarity_watch_score
        or candidate.specialist_memory_confidence <= config.memory_confidence_watch_score
        or reduction_readiness_score < config.pass_min_reduction_readiness_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    candidate: ResearchStrategyUncertaintyReductionReadinessCandidate,
    source_freshness_score: Decimal,
    reduction_readiness_score: Decimal,
    config: ResearchStrategyUncertaintyReductionReadinessConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_low_value_code(
        codes,
        candidate.current_uncertainty,
        LOW_CURRENT_UNCERTAINTY_WATCH_SCORE,
        LOW_CURRENT_UNCERTAINTY_BLOCK_SCORE,
        "current_uncertainty_too_low_watch",
        "current_uncertainty_too_low_blocking",
    )
    _append_high_value_code(
        codes,
        candidate.source_age_seconds,
        config.source_freshness_watch_age_seconds,
        config.source_freshness_block_age_seconds,
        "source_freshness_watch",
        "source_freshness_blocking",
    )
    _append_low_value_code(
        codes,
        candidate.evidence_quality,
        config.evidence_quality_watch_score,
        config.evidence_quality_block_score,
        "evidence_quality_watch",
        "evidence_quality_blocking",
    )
    _append_low_value_code(
        codes,
        candidate.liquidity_reliability,
        config.liquidity_reliability_watch_score,
        config.liquidity_reliability_block_score,
        "liquidity_reliability_watch",
        "liquidity_reliability_blocking",
    )
    _append_high_value_code(
        codes,
        candidate.cost_drag,
        config.cost_drag_watch_score,
        config.cost_drag_block_score,
        "cost_drag_watch",
        "cost_drag_blocking",
    )
    _append_low_value_code(
        codes,
        candidate.resolution_clarity,
        config.resolution_clarity_watch_score,
        config.resolution_clarity_block_score,
        "resolution_clarity_watch",
        "resolution_clarity_blocking",
    )
    _append_low_value_code(
        codes,
        candidate.specialist_memory_confidence,
        config.memory_confidence_watch_score,
        config.memory_confidence_block_score,
        "specialist_memory_confidence_watch",
        "specialist_memory_confidence_blocking",
    )
    _append_low_value_code(
        codes,
        reduction_readiness_score,
        config.pass_min_reduction_readiness_score,
        config.watch_min_reduction_readiness_score,
        "composite_reduction_readiness_watch",
        "composite_reduction_readiness_blocking",
    )
    if source_freshness_score == ZERO and "source_freshness_blocking" not in codes:
        codes.append("source_freshness_blocking")
    if not codes:
        return ("uncertainty_reduction_readiness_clear",)
    return tuple(codes)


def _append_low_value_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value <= block_threshold:
        codes.append(block_code)
    elif value <= watch_threshold:
        codes.append(watch_code)


def _append_high_value_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block_threshold:
        codes.append(block_code)
    elif value >= watch_threshold:
        codes.append(watch_code)


def _report_status(
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    if all(row.status == "pass" for row in rows):
        return ("uncertainty_reduction_readiness_report_clear",)
    codes: list[str] = []
    if _has_any_row_reason(
        rows,
        ("current_uncertainty_too_low_watch", "current_uncertainty_too_low_blocking"),
    ):
        codes.append("current_uncertainty_gap_detected")
    if _has_any_row_reason(rows, ("source_freshness_watch", "source_freshness_blocking")):
        codes.append("source_freshness_gap_detected")
    if _has_any_row_reason(rows, ("evidence_quality_watch", "evidence_quality_blocking")):
        codes.append("evidence_quality_gap_detected")
    if _has_any_row_reason(
        rows,
        ("liquidity_reliability_watch", "liquidity_reliability_blocking"),
    ):
        codes.append("liquidity_reliability_gap_detected")
    if _has_any_row_reason(rows, ("cost_drag_watch", "cost_drag_blocking")):
        codes.append("cost_drag_gap_detected")
    if _has_any_row_reason(rows, ("resolution_clarity_watch", "resolution_clarity_blocking")):
        codes.append("resolution_clarity_gap_detected")
    if _has_any_row_reason(
        rows,
        (
            "specialist_memory_confidence_watch",
            "specialist_memory_confidence_blocking",
        ),
    ):
        codes.append("specialist_memory_confidence_gap_detected")
    if _has_any_row_reason(
        rows,
        ("composite_reduction_readiness_watch", "composite_reduction_readiness_blocking"),
    ):
        codes.append("composite_reduction_readiness_gap_detected")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...],
) -> tuple[ResearchStrategyUncertaintyReductionReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyUncertaintyReductionReadinessReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        ResearchStrategyUncertaintyReductionReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyUncertaintyReductionReadinessCandidate],
) -> tuple[ResearchStrategyUncertaintyReductionReadinessCandidate, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Iterable):
        raise ValueError("candidates must be an iterable")
    normalized = tuple(candidates)
    for row in normalized:
        if type(row) is not ResearchStrategyUncertaintyReductionReadinessCandidate:
            raise ValueError(
                "candidates must contain "
                "ResearchStrategyUncertaintyReductionReadinessCandidate",
            )
        _require_hard_flags("candidate", row)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyUncertaintyReductionReadinessRow],
) -> tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyUncertaintyReductionReadinessRow:
            raise ValueError(
                "rows must contain ResearchStrategyUncertaintyReductionReadinessRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategyUncertaintyReductionReadinessReasonCodeCount],
) -> tuple[ResearchStrategyUncertaintyReductionReadinessReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not ResearchStrategyUncertaintyReductionReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyUncertaintyReductionReadinessReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _validate_row(row: ResearchStrategyUncertaintyReductionReadinessRow) -> None:
    if row.status == "block" and not any(code.endswith("_blocking") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("uncertainty_reduction_readiness_clear",):
        raise ValueError("status must match reason_codes")
    if row.cost_efficiency_score != _inverse_probability(row.cost_drag_score):
        raise ValueError("cost_efficiency_score must match cost_drag_score")


def _validate_report(report: ResearchStrategyUncertaintyReductionReadinessReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.candidate_count:
        raise ValueError("status counts must match candidate_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        ("source_freshness_watch", "source_freshness_blocking"),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.evidence_quality_gap_count != _reason_count(
        report.rows,
        ("evidence_quality_watch", "evidence_quality_blocking"),
    ):
        raise ValueError("evidence_quality_gap_count must match rows")
    if report.liquidity_reliability_gap_count != _reason_count(
        report.rows,
        ("liquidity_reliability_watch", "liquidity_reliability_blocking"),
    ):
        raise ValueError("liquidity_reliability_gap_count must match rows")
    if report.cost_drag_gap_count != _reason_count(
        report.rows,
        ("cost_drag_watch", "cost_drag_blocking"),
    ):
        raise ValueError("cost_drag_gap_count must match rows")
    if report.resolution_clarity_gap_count != _reason_count(
        report.rows,
        ("resolution_clarity_watch", "resolution_clarity_blocking"),
    ):
        raise ValueError("resolution_clarity_gap_count must match rows")
    if report.memory_confidence_gap_count != _reason_count(
        report.rows,
        (
            "specialist_memory_confidence_watch",
            "specialist_memory_confidence_blocking",
        ),
    ):
        raise ValueError("memory_confidence_gap_count must match rows")
    if report.mean_reduction_readiness_score != _mean(
        tuple(row.reduction_readiness_score for row in report.rows),
    ):
        raise ValueError("mean_reduction_readiness_score must match rows")
    if report.mean_current_uncertainty != _mean(
        tuple(row.current_uncertainty_score for row in report.rows),
    ):
        raise ValueError("mean_current_uncertainty must match rows")
    if report.max_cost_drag_score != _max_decimal(
        tuple(row.cost_drag_score for row in report.rows),
    ):
        raise ValueError("max_cost_drag_score must match rows")


def _report_payload_without_digest_from_report(
    report: ResearchStrategyUncertaintyReductionReadinessReport,
) -> dict[str, Any]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        stale_source_count=report.stale_source_count,
        evidence_quality_gap_count=report.evidence_quality_gap_count,
        liquidity_reliability_gap_count=report.liquidity_reliability_gap_count,
        cost_drag_gap_count=report.cost_drag_gap_count,
        resolution_clarity_gap_count=report.resolution_clarity_gap_count,
        memory_confidence_gap_count=report.memory_confidence_gap_count,
        mean_reduction_readiness_score=report.mean_reduction_readiness_score,
        mean_current_uncertainty=report.mean_current_uncertainty,
        max_cost_drag_score=report.max_cost_drag_score,
        status=report.status,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_payload_without_digest(**values: Any) -> dict[str, Any]:
    return {
        "generated_at": values["generated_at"],
        "config_version": values["config_version"],
        "candidate_count": values["candidate_count"],
        "pass_count": values["pass_count"],
        "watch_count": values["watch_count"],
        "block_count": values["block_count"],
        "stale_source_count": values["stale_source_count"],
        "evidence_quality_gap_count": values["evidence_quality_gap_count"],
        "liquidity_reliability_gap_count": values["liquidity_reliability_gap_count"],
        "cost_drag_gap_count": values["cost_drag_gap_count"],
        "resolution_clarity_gap_count": values["resolution_clarity_gap_count"],
        "memory_confidence_gap_count": values["memory_confidence_gap_count"],
        "mean_reduction_readiness_score": values["mean_reduction_readiness_score"],
        "mean_current_uncertainty": values["mean_current_uncertainty"],
        "max_cost_drag_score": values["max_cost_drag_score"],
        "status": values["status"],
        "reason_code_counts": values["reason_code_counts"],
        "reason_codes": values["reason_codes"],
        "rows": values["rows"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchStrategyUncertaintyReductionReadinessReport,
) -> str:
    return _public_digest(_report_payload_without_digest_from_report(report))


def _public_digest(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, ".6f")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) is ResearchStrategyUncertaintyReductionReadinessReasonCodeCount:
        return {
            "reason_code": value.reason_code,
            "count": _json_ready(value.count),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) is ResearchStrategyUncertaintyReductionReadinessRow:
        return {
            "row_number": _json_ready(value.row_number),
            "observed_at": _json_ready(value.observed_at),
            "current_uncertainty_score": _json_ready(value.current_uncertainty_score),
            "source_age_seconds": _json_ready(value.source_age_seconds),
            "source_freshness_score": _json_ready(value.source_freshness_score),
            "evidence_quality_score": _json_ready(value.evidence_quality_score),
            "liquidity_reliability_score": _json_ready(value.liquidity_reliability_score),
            "cost_drag_score": _json_ready(value.cost_drag_score),
            "cost_efficiency_score": _json_ready(value.cost_efficiency_score),
            "resolution_clarity_score": _json_ready(value.resolution_clarity_score),
            "specialist_memory_confidence_score": _json_ready(
                value.specialist_memory_confidence_score,
            ),
            "reduction_readiness_score": _json_ready(value.reduction_readiness_score),
            "status": value.status,
            "reason_codes": _json_ready(value.reason_codes),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")


def _status_count(
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)))


def _has_any_row_reason(
    rows: tuple[ResearchStrategyUncertaintyReductionReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> bool:
    return any(any(code in row.reason_codes for code in reason_codes) for row in rows)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(max(values))


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_member(field_name, value, allowed)
    return tuple(dict.fromkeys(normalized))


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_nonblank_string(field_name, value)
    return value


def _require_nonblank_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_nonblank_string(field_name, value)
    if not all(ch.islower() or ch.isdigit() or ch in "-_" for ch in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or not all(ch in "0123456789abcdef" for ch in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_weights_total_one(
    config: ResearchStrategyUncertaintyReductionReadinessConfig,
) -> None:
    total = _quantize_decimal(
        config.current_uncertainty_weight
        + config.source_freshness_weight
        + config.evidence_quality_weight
        + config.liquidity_reliability_weight
        + config.cost_drag_weight
        + config.resolution_clarity_weight
        + config.specialist_memory_confidence_weight,
    )
    if total != ONE:
        raise ValueError("component weights must sum to one")


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_descending_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value >= watch_value:
        raise ValueError(f"{watch_name} must exceed {block_name}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _draft_sort_key(row: _RowDraft) -> tuple[Any, ...]:
    return (
        -STATUS_WEIGHT[row.status],
        row.reduction_readiness_score,
        -row.cost_drag_score,
        row.observed_at.isoformat(),
        row.current_uncertainty_score,
        row.source_age_seconds,
        row.source_freshness_score,
        row.evidence_quality_score,
        row.liquidity_reliability_score,
        row.cost_efficiency_score,
        row.resolution_clarity_score,
        row.specialist_memory_confidence_score,
        row.reason_codes,
    )


def _row_sort_key(
    row: ResearchStrategyUncertaintyReductionReadinessRow,
) -> tuple[Any, ...]:
    return (
        -STATUS_WEIGHT[row.status],
        row.reduction_readiness_score,
        -row.cost_drag_score,
        row.observed_at.isoformat(),
        row.current_uncertainty_score,
        row.source_age_seconds,
        row.source_freshness_score,
        row.evidence_quality_score,
        row.liquidity_reliability_score,
        row.cost_efficiency_score,
        row.resolution_clarity_score,
        row.specialist_memory_confidence_score,
        row.reason_codes,
        row.row_number,
    )
