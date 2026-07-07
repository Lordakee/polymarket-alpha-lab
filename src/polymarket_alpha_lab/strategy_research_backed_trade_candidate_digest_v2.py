"""Readonly paper-only digest for research-backed final candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
from typing import Any, Iterable


__all__ = (
    "DEFAULT_STRATEGY_RESEARCH_BACKED_CANDIDATE_DIGEST_V2_CONFIG_VERSION",
    "StrategyResearchBackedTradeCandidateDigestV2Candidate",
    "StrategyResearchBackedTradeCandidateDigestV2Config",
    "StrategyResearchBackedTradeCandidateDigestV2Report",
    "StrategyResearchBackedTradeCandidateDigestV2Row",
    "build_strategy_research_backed_trade_candidate_digest_v2",
    "strategy_research_backed_trade_candidate_digest_v2_payload",
    "validate_strategy_research_backed_trade_candidate_digest_v2_payload",
)


DEFAULT_STRATEGY_RESEARCH_BACKED_CANDIDATE_DIGEST_V2_CONFIG_VERSION = (
    "strategy-research-backed-candidate-digest-v2"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_STATUSES = ("ready", "watch", "blocked", "empty")
ROW_STATUSES = ("ready", "watch", "blocked")
SIDES = ("yes", "no")
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "candidate_count",
    "ready_count",
    "watch_count",
    "blocked_count",
    "highest_cost_adjusted_edge",
    "lowest_liquidity_exit_ratio",
    "max_portfolio_impact_ratio",
    "top_candidate_reference",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
ROW_PAYLOAD_FIELDS = (
    "candidate_rank",
    "candidate_reference",
    "market_slug",
    "question",
    "outcome_name",
    "side",
    "evaluated_at",
    "research_readiness_score",
    "official_source_anchor_count",
    "official_source_anchors",
    "latest_official_source_at",
    "source_age_seconds",
    "model_probability",
    "market_probability",
    "entry_cost_probability",
    "exit_cost_probability",
    "cost_adjusted_edge",
    "expected_value_probability_edge",
    "expected_value_consistency_gap",
    "safety_status",
    "uncertainty_band_probability",
    "exit_depth_to_candidate_ratio",
    "portfolio_impact_ratio",
    "candidate_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class StrategyResearchBackedTradeCandidateDigestV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RESEARCH_BACKED_CANDIDATE_DIGEST_V2_CONFIG_VERSION
    )
    min_ready_research_readiness_score: Decimal = Decimal("0.800000")
    min_watch_research_readiness_score: Decimal = Decimal("0.650000")
    min_ready_official_source_anchor_count: Decimal = Decimal("2.000000")
    min_watch_official_source_anchor_count: Decimal = Decimal("1.000000")
    max_ready_source_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_source_age_seconds: Decimal = Decimal("7200.000000")
    min_ready_cost_adjusted_edge: Decimal = Decimal("0.030000")
    min_watch_cost_adjusted_edge: Decimal = Decimal("0.010000")
    max_ready_expected_value_gap: Decimal = Decimal("0.010000")
    max_watch_expected_value_gap: Decimal = Decimal("0.025000")
    max_ready_uncertainty_band_probability: Decimal = Decimal("0.040000")
    max_watch_uncertainty_band_probability: Decimal = Decimal("0.075000")
    min_ready_exit_depth_to_candidate_ratio: Decimal = Decimal("1.500000")
    min_watch_exit_depth_to_candidate_ratio: Decimal = Decimal("1.000000")
    max_ready_portfolio_impact_ratio: Decimal = Decimal("0.080000")
    max_watch_portfolio_impact_ratio: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyResearchBackedTradeCandidateDigestV2Config,
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_ready_research_readiness_score",
            "min_watch_research_readiness_score",
            "max_ready_uncertainty_band_probability",
            "max_watch_uncertainty_band_probability",
            "max_ready_portfolio_impact_ratio",
            "max_watch_portfolio_impact_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_ready_official_source_anchor_count",
            "min_watch_official_source_anchor_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_ready_source_age_seconds",
            "max_watch_source_age_seconds",
            "min_ready_cost_adjusted_edge",
            "min_watch_cost_adjusted_edge",
            "max_ready_expected_value_gap",
            "max_watch_expected_value_gap",
            "min_ready_exit_depth_to_candidate_ratio",
            "min_watch_exit_depth_to_candidate_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_min_ready_at_least_watch(
            "research readiness ready threshold must be at least watch threshold",
            self.min_ready_research_readiness_score,
            self.min_watch_research_readiness_score,
        )
        _require_min_ready_at_least_watch(
            "official source anchor ready threshold must be at least watch threshold",
            self.min_ready_official_source_anchor_count,
            self.min_watch_official_source_anchor_count,
        )
        _require_max_ready_at_most_watch(
            "source freshness ready threshold must not exceed watch threshold",
            self.max_ready_source_age_seconds,
            self.max_watch_source_age_seconds,
        )
        _require_min_ready_at_least_watch(
            "cost adjusted edge ready threshold must be at least watch threshold",
            self.min_ready_cost_adjusted_edge,
            self.min_watch_cost_adjusted_edge,
        )
        _require_max_ready_at_most_watch(
            "expected value gap ready threshold must not exceed watch threshold",
            self.max_ready_expected_value_gap,
            self.max_watch_expected_value_gap,
        )
        _require_max_ready_at_most_watch(
            "uncertainty band ready threshold must not exceed watch threshold",
            self.max_ready_uncertainty_band_probability,
            self.max_watch_uncertainty_band_probability,
        )
        _require_min_ready_at_least_watch(
            "liquidity exit ready threshold must be at least watch threshold",
            self.min_ready_exit_depth_to_candidate_ratio,
            self.min_watch_exit_depth_to_candidate_ratio,
        )
        _require_max_ready_at_most_watch(
            "portfolio impact ready threshold must not exceed watch threshold",
            self.max_ready_portfolio_impact_ratio,
            self.max_watch_portfolio_impact_ratio,
        )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyResearchBackedTradeCandidateDigestV2Candidate:
    candidate_reference: str
    market_slug: str
    question: str
    outcome_name: str
    side: str
    evaluated_at: datetime
    research_readiness_score: Decimal
    official_source_anchors: tuple[str, ...]
    latest_official_source_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    entry_cost_probability: Decimal
    exit_cost_probability: Decimal
    expected_value_probability_edge: Decimal
    uncertainty_band_probability: Decimal
    exit_depth_to_candidate_ratio: Decimal
    portfolio_impact_ratio: Decimal
    safety_gate_clear: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "candidate",
            self,
            StrategyResearchBackedTradeCandidateDigestV2Candidate,
        )
        for field_name in (
            "candidate_reference",
            "market_slug",
            "question",
            "outcome_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("side", self.side, SIDES)
        object.__setattr__(
            self,
            "evaluated_at",
            _as_utc("evaluated_at", self.evaluated_at),
        )
        object.__setattr__(
            self,
            "latest_official_source_at",
            _as_utc("latest_official_source_at", self.latest_official_source_at),
        )
        for field_name in (
            "research_readiness_score",
            "model_probability",
            "market_probability",
            "entry_cost_probability",
            "exit_cost_probability",
            "expected_value_probability_edge",
            "uncertainty_band_probability",
            "portfolio_impact_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exit_depth_to_candidate_ratio",
            _normalize_nonnegative_decimal(
                "exit_depth_to_candidate_ratio",
                self.exit_depth_to_candidate_ratio,
            ),
        )
        if type(self.safety_gate_clear) is not bool:
            raise ValueError("safety_gate_clear must be a bool")
        object.__setattr__(
            self,
            "official_source_anchors",
            _normalize_public_string_tuple(
                "official_source_anchors",
                self.official_source_anchors,
                require_nonempty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_string_tuple(
                "reason_codes",
                self.reason_codes,
                require_nonempty=True,
            ),
        )
        _reject_unsafe_public_payload("candidate", self)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyResearchBackedTradeCandidateDigestV2Row:
    candidate_rank: Decimal
    candidate_reference: str
    market_slug: str
    question: str
    outcome_name: str
    side: str
    evaluated_at: datetime
    research_readiness_score: Decimal
    official_source_anchor_count: Decimal
    official_source_anchors: tuple[str, ...]
    latest_official_source_at: datetime
    source_age_seconds: Decimal
    model_probability: Decimal
    market_probability: Decimal
    entry_cost_probability: Decimal
    exit_cost_probability: Decimal
    cost_adjusted_edge: Decimal
    expected_value_probability_edge: Decimal
    expected_value_consistency_gap: Decimal
    safety_status: str
    uncertainty_band_probability: Decimal
    exit_depth_to_candidate_ratio: Decimal
    portfolio_impact_ratio: Decimal
    candidate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyResearchBackedTradeCandidateDigestV2Row)
        object.__setattr__(
            self,
            "candidate_rank",
            _normalize_positive_whole_decimal("candidate_rank", self.candidate_rank),
        )
        for field_name in (
            "candidate_reference",
            "market_slug",
            "question",
            "outcome_name",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("side", self.side, SIDES)
        for field_name in ("evaluated_at", "latest_official_source_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "research_readiness_score",
            "model_probability",
            "market_probability",
            "entry_cost_probability",
            "exit_cost_probability",
            "expected_value_probability_edge",
            "uncertainty_band_probability",
            "portfolio_impact_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_anchor_count",
            "source_age_seconds",
            "expected_value_consistency_gap",
            "exit_depth_to_candidate_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        _require_member("safety_status", self.safety_status, ROW_STATUSES)
        _require_member("candidate_status", self.candidate_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "official_source_anchors",
            _normalize_public_string_tuple(
                "official_source_anchors",
                self.official_source_anchors,
                require_nonempty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_string_tuple(
                "reason_codes",
                self.reason_codes,
                require_nonempty=True,
            ),
        )
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyResearchBackedTradeCandidateDigestV2Report:
    generated_at: datetime
    config_version: str
    status: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    highest_cost_adjusted_edge: Decimal
    lowest_liquidity_exit_ratio: Decimal
    max_portfolio_impact_ratio: Decimal
    top_candidate_reference: str | None
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            StrategyResearchBackedTradeCandidateDigestV2Report,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_cost_adjusted_edge",
            "lowest_liquidity_exit_ratio",
            "max_portfolio_impact_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_reference is not None:
            _require_public_string("top_candidate_reference", self.top_candidate_reference)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_string_tuple(
                "reason_codes",
                self.reason_codes,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
            _validate_report_derived_validation_digest(self)
        _validate_report_consistency(self)
        _validate_report_derived_validation_digest(self)


def build_strategy_research_backed_trade_candidate_digest_v2(
    candidates: Iterable[StrategyResearchBackedTradeCandidateDigestV2Candidate],
    *,
    config: StrategyResearchBackedTradeCandidateDigestV2Config,
    generated_at: datetime,
) -> StrategyResearchBackedTradeCandidateDigestV2Report:
    """Summarize final candidates into a readonly paper-only digest."""

    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of candidate values")
    _require_exact_type("config", config, StrategyResearchBackedTradeCandidateDigestV2Config)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)

    normalized_candidates = tuple(candidates)
    seen_references: set[str] = set()
    unranked_rows: list[StrategyResearchBackedTradeCandidateDigestV2Row] = []
    for candidate in normalized_candidates:
        _require_exact_type(
            "candidate",
            candidate,
            StrategyResearchBackedTradeCandidateDigestV2Candidate,
            "candidates must contain StrategyResearchBackedTradeCandidateDigestV2Candidate values",
        )
        _require_hard_flags("candidate", candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference in candidates")
        seen_references.add(candidate.candidate_reference)
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")
        if candidate.latest_official_source_at > generated_at:
            raise ValueError("latest_official_source_at must not be after generated_at")
        unranked_rows.append(_build_unranked_row(candidate, config, generated_at))

    ranked_rows = tuple(
        _rank_row(rank, row)
        for rank, row in enumerate(sorted(unranked_rows, key=_row_sort_key), start=1)
    )
    ready_count = _count_status(ranked_rows, "ready")
    watch_count = _count_status(ranked_rows, "watch")
    blocked_count = _count_status(ranked_rows, "blocked")
    status = _report_status(ranked_rows, ready_count, watch_count, blocked_count)
    return StrategyResearchBackedTradeCandidateDigestV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        status=status,
        candidate_count=_count_decimal(len(normalized_candidates)),
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        highest_cost_adjusted_edge=_max_nonnegative_cost_adjusted_edge(ranked_rows),
        lowest_liquidity_exit_ratio=_min_exit_depth_to_candidate_ratio(ranked_rows),
        max_portfolio_impact_ratio=_max_portfolio_impact_ratio(ranked_rows),
        top_candidate_reference=ranked_rows[0].candidate_reference if ranked_rows else None,
        reason_codes=_report_reason_codes(status, ranked_rows),
        rows=ranked_rows,
    )


def strategy_research_backed_trade_candidate_digest_v2_payload(
    report: StrategyResearchBackedTradeCandidateDigestV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyResearchBackedTradeCandidateDigestV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        return _report_payload(report)
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a StrategyResearchBackedTradeCandidateDigestV2Report",
    )


def validate_strategy_research_backed_trade_candidate_digest_v2_payload(
    payload: dict[str, object],
) -> bool:
    strategy_research_backed_trade_candidate_digest_v2_payload(payload)
    return True


def _build_unranked_row(
    candidate: StrategyResearchBackedTradeCandidateDigestV2Candidate,
    config: StrategyResearchBackedTradeCandidateDigestV2Config,
    generated_at: datetime,
) -> StrategyResearchBackedTradeCandidateDigestV2Row:
    source_age_seconds = _seconds_between(candidate.latest_official_source_at, generated_at)
    cost_adjusted_edge = (
        candidate.model_probability
        - candidate.market_probability
        - candidate.entry_cost_probability
        - candidate.exit_cost_probability
    )
    cost_adjusted_edge = _normalize_decimal("cost_adjusted_edge", cost_adjusted_edge)
    expected_value_consistency_gap = abs(
        cost_adjusted_edge - candidate.expected_value_probability_edge,
    )
    expected_value_consistency_gap = _normalize_nonnegative_decimal(
        "expected_value_consistency_gap",
        expected_value_consistency_gap,
    )
    anchor_count = _count_decimal(len(candidate.official_source_anchors))
    criterion_statuses_and_reasons = (
        _min_threshold_status_and_reason(
            "research_readiness",
            candidate.research_readiness_score,
            config.min_ready_research_readiness_score,
            config.min_watch_research_readiness_score,
        ),
        _min_threshold_status_and_reason(
            "official_source_anchors",
            anchor_count,
            config.min_ready_official_source_anchor_count,
            config.min_watch_official_source_anchor_count,
        ),
        _max_threshold_status_and_reason(
            "source_freshness",
            source_age_seconds,
            config.max_ready_source_age_seconds,
            config.max_watch_source_age_seconds,
        ),
        _min_threshold_status_and_reason(
            "cost_adjusted_edge",
            cost_adjusted_edge,
            config.min_ready_cost_adjusted_edge,
            config.min_watch_cost_adjusted_edge,
        ),
        _max_threshold_status_and_reason(
            "expected_value_consistency",
            expected_value_consistency_gap,
            config.max_ready_expected_value_gap,
            config.max_watch_expected_value_gap,
        ),
        _safety_status_and_reason(candidate.safety_gate_clear),
        _max_threshold_status_and_reason(
            "uncertainty_band",
            candidate.uncertainty_band_probability,
            config.max_ready_uncertainty_band_probability,
            config.max_watch_uncertainty_band_probability,
        ),
        _min_threshold_status_and_reason(
            "liquidity_exit",
            candidate.exit_depth_to_candidate_ratio,
            config.min_ready_exit_depth_to_candidate_ratio,
            config.min_watch_exit_depth_to_candidate_ratio,
        ),
        _max_threshold_status_and_reason(
            "portfolio_impact",
            candidate.portfolio_impact_ratio,
            config.max_ready_portfolio_impact_ratio,
            config.max_watch_portfolio_impact_ratio,
        ),
    )
    criterion_statuses = tuple(status for status, _reason in criterion_statuses_and_reasons)
    candidate_status = _combined_status(criterion_statuses)
    return StrategyResearchBackedTradeCandidateDigestV2Row(
        candidate_rank=ONE,
        candidate_reference=candidate.candidate_reference,
        market_slug=candidate.market_slug,
        question=candidate.question,
        outcome_name=candidate.outcome_name,
        side=candidate.side,
        evaluated_at=candidate.evaluated_at,
        research_readiness_score=candidate.research_readiness_score,
        official_source_anchor_count=anchor_count,
        official_source_anchors=candidate.official_source_anchors,
        latest_official_source_at=candidate.latest_official_source_at,
        source_age_seconds=source_age_seconds,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        entry_cost_probability=candidate.entry_cost_probability,
        exit_cost_probability=candidate.exit_cost_probability,
        cost_adjusted_edge=cost_adjusted_edge,
        expected_value_probability_edge=candidate.expected_value_probability_edge,
        expected_value_consistency_gap=expected_value_consistency_gap,
        safety_status="ready" if candidate.safety_gate_clear else "blocked",
        uncertainty_band_probability=candidate.uncertainty_band_probability,
        exit_depth_to_candidate_ratio=candidate.exit_depth_to_candidate_ratio,
        portfolio_impact_ratio=candidate.portfolio_impact_ratio,
        candidate_status=candidate_status,
        reason_codes=tuple(
            dict.fromkeys(
                (
                    *candidate.reason_codes,
                    *(reason for _status, reason in criterion_statuses_and_reasons),
                ),
            ),
        ),
    )


def _rank_row(
    rank: int,
    row: StrategyResearchBackedTradeCandidateDigestV2Row,
) -> StrategyResearchBackedTradeCandidateDigestV2Row:
    return StrategyResearchBackedTradeCandidateDigestV2Row(
        candidate_rank=_count_decimal(rank),
        candidate_reference=row.candidate_reference,
        market_slug=row.market_slug,
        question=row.question,
        outcome_name=row.outcome_name,
        side=row.side,
        evaluated_at=row.evaluated_at,
        research_readiness_score=row.research_readiness_score,
        official_source_anchor_count=row.official_source_anchor_count,
        official_source_anchors=row.official_source_anchors,
        latest_official_source_at=row.latest_official_source_at,
        source_age_seconds=row.source_age_seconds,
        model_probability=row.model_probability,
        market_probability=row.market_probability,
        entry_cost_probability=row.entry_cost_probability,
        exit_cost_probability=row.exit_cost_probability,
        cost_adjusted_edge=row.cost_adjusted_edge,
        expected_value_probability_edge=row.expected_value_probability_edge,
        expected_value_consistency_gap=row.expected_value_consistency_gap,
        safety_status=row.safety_status,
        uncertainty_band_probability=row.uncertainty_band_probability,
        exit_depth_to_candidate_ratio=row.exit_depth_to_candidate_ratio,
        portfolio_impact_ratio=row.portfolio_impact_ratio,
        candidate_status=row.candidate_status,
        reason_codes=row.reason_codes,
    )


def _row_sort_key(
    row: StrategyResearchBackedTradeCandidateDigestV2Row,
) -> tuple[object, ...]:
    return (
        {"ready": 0, "watch": 1, "blocked": 2}[row.candidate_status],
        -row.cost_adjusted_edge,
        -row.research_readiness_score,
        row.source_age_seconds,
        row.portfolio_impact_ratio,
        row.candidate_reference,
    )


def _min_threshold_status_and_reason(
    label: str,
    value: Decimal,
    ready_threshold: Decimal,
    watch_threshold: Decimal,
) -> tuple[str, str]:
    if value >= ready_threshold:
        status = "ready"
    elif value >= watch_threshold:
        status = "watch"
    else:
        status = "blocked"
    return status, f"{label}_{status}"


def _max_threshold_status_and_reason(
    label: str,
    value: Decimal,
    ready_threshold: Decimal,
    watch_threshold: Decimal,
) -> tuple[str, str]:
    if value <= ready_threshold:
        status = "ready"
    elif value <= watch_threshold:
        status = "watch"
    else:
        status = "blocked"
    return status, f"{label}_{status}"


def _safety_status_and_reason(safety_gate_clear: bool) -> tuple[str, str]:
    status = "ready" if safety_gate_clear else "blocked"
    return status, f"safety_gate_{status}"


def _combined_status(statuses: tuple[str, ...]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "ready"


def _report_status(
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
    ready_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> str:
    if not rows:
        return "empty"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    if ready_count > ZERO:
        return "ready"
    raise ValueError("report status could not be derived")


def _report_reason_codes(
    status: str,
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
) -> tuple[str, ...]:
    if status == "empty":
        return ("digest_empty",)
    reason_codes = [f"digest_{status}"]
    for row in rows:
        if row.candidate_status != "ready":
            reason_codes.extend(
                reason_code
                for reason_code in row.reason_codes
                if reason_code.endswith(("_watch", "_blocked"))
            )
    return tuple(dict.fromkeys(reason_codes))


def _count_status(
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.candidate_status == status for row in rows))


def _max_nonnegative_cost_adjusted_edge(
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(ZERO, max(row.cost_adjusted_edge for row in rows)).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _min_exit_depth_to_candidate_ratio(
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.exit_depth_to_candidate_ratio for row in rows).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _max_portfolio_impact_ratio(
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.portfolio_impact_ratio for row in rows).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _report_payload(
    report: StrategyResearchBackedTradeCandidateDigestV2Report,
) -> dict[str, object]:
    payload = _report_payload_without_digest(report)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _report_payload_without_digest(
    report: StrategyResearchBackedTradeCandidateDigestV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "candidate_count": _decimal_payload(report.candidate_count),
        "ready_count": _decimal_payload(report.ready_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "highest_cost_adjusted_edge": _decimal_payload(report.highest_cost_adjusted_edge),
        "lowest_liquidity_exit_ratio": _decimal_payload(report.lowest_liquidity_exit_ratio),
        "max_portfolio_impact_ratio": _decimal_payload(report.max_portfolio_impact_ratio),
        "top_candidate_reference": report.top_candidate_reference,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyResearchBackedTradeCandidateDigestV2Row) -> dict[str, object]:
    return {
        "candidate_rank": _decimal_payload(row.candidate_rank),
        "candidate_reference": row.candidate_reference,
        "market_slug": row.market_slug,
        "question": row.question,
        "outcome_name": row.outcome_name,
        "side": row.side,
        "evaluated_at": row.evaluated_at.isoformat(),
        "research_readiness_score": _decimal_payload(row.research_readiness_score),
        "official_source_anchor_count": _decimal_payload(row.official_source_anchor_count),
        "official_source_anchors": list(row.official_source_anchors),
        "latest_official_source_at": row.latest_official_source_at.isoformat(),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "model_probability": _decimal_payload(row.model_probability),
        "market_probability": _decimal_payload(row.market_probability),
        "entry_cost_probability": _decimal_payload(row.entry_cost_probability),
        "exit_cost_probability": _decimal_payload(row.exit_cost_probability),
        "cost_adjusted_edge": _decimal_payload(row.cost_adjusted_edge),
        "expected_value_probability_edge": _decimal_payload(
            row.expected_value_probability_edge,
        ),
        "expected_value_consistency_gap": _decimal_payload(
            row.expected_value_consistency_gap,
        ),
        "safety_status": row.safety_status,
        "uncertainty_band_probability": _decimal_payload(row.uncertainty_band_probability),
        "exit_depth_to_candidate_ratio": _decimal_payload(
            row.exit_depth_to_candidate_ratio,
        ),
        "portfolio_impact_ratio": _decimal_payload(row.portfolio_impact_ratio),
        "candidate_status": row.candidate_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: StrategyResearchBackedTradeCandidateDigestV2Report,
) -> str:
    return _derived_validation_digest(_report_payload_without_digest(report))


def _validate_report_derived_validation_digest(
    report: StrategyResearchBackedTradeCandidateDigestV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("strategy_research_backed_candidate_digest_v2", values)


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_payload_value(value: object) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(value[key])}" for key in sorted(value)
        ) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    if value is None:
        return "None"
    return str(value)


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_payload_fields(payload, REPORT_PAYLOAD_FIELDS, "payload")
    _require_iso_datetime_string("generated_at", payload["generated_at"])
    for field_name in ("config_version", "status"):
        _require_public_string(field_name, payload[field_name])
    _require_member("status", payload["status"], REPORT_STATUSES)
    for field_name in (
        "candidate_count",
        "ready_count",
        "watch_count",
        "blocked_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in (
        "highest_cost_adjusted_edge",
        "lowest_liquidity_exit_ratio",
        "max_portfolio_impact_ratio",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    if payload["top_candidate_reference"] is not None:
        _require_public_string("top_candidate_reference", payload["top_candidate_reference"])
    _normalize_public_string_list("reason_codes", payload["reason_codes"], require_nonempty=True)
    rows = _normalize_public_rows(payload["rows"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    _validate_public_payload_counts(payload, rows)


def _normalize_public_rows(value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[dict[str, object]] = []
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain dict values")
        _validate_public_row_payload(row)
        rows.append(row)
    return tuple(rows)


def _validate_public_row_payload(row: dict[str, object]) -> None:
    _require_payload_fields(row, ROW_PAYLOAD_FIELDS, "row")
    for field_name in (
        "candidate_reference",
        "market_slug",
        "question",
        "outcome_name",
    ):
        _require_public_string(field_name, row[field_name])
    _require_member("side", row["side"], SIDES)
    for field_name in ("evaluated_at", "latest_official_source_at"):
        _require_iso_datetime_string(field_name, row[field_name])
    for field_name in (
        "candidate_rank",
        "official_source_anchor_count",
    ):
        _require_decimal_payload_string(field_name, row[field_name], whole=True)
    for field_name in (
        "research_readiness_score",
        "model_probability",
        "market_probability",
        "entry_cost_probability",
        "exit_cost_probability",
        "expected_value_probability_edge",
        "uncertainty_band_probability",
        "portfolio_impact_ratio",
    ):
        _require_decimal_payload_string(field_name, row[field_name], probability=True)
    for field_name in (
        "source_age_seconds",
        "cost_adjusted_edge",
        "expected_value_consistency_gap",
        "exit_depth_to_candidate_ratio",
    ):
        _require_decimal_payload_string(field_name, row[field_name])
    _normalize_public_string_list(
        "official_source_anchors",
        row["official_source_anchors"],
        require_nonempty=False,
    )
    _require_member("safety_status", row["safety_status"], ROW_STATUSES)
    _require_member("candidate_status", row["candidate_status"], ROW_STATUSES)
    _normalize_public_string_list("reason_codes", row["reason_codes"], require_nonempty=True)
    _require_hard_flags("row", _DictFlags(row))


def _validate_public_payload_counts(
    payload: dict[str, object],
    rows: tuple[dict[str, object], ...],
) -> None:
    if Decimal(str(payload["candidate_count"])) != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    for status, field_name in (
        ("ready", "ready_count"),
        ("watch", "watch_count"),
        ("blocked", "blocked_count"),
    ):
        if Decimal(str(payload[field_name])) != _count_decimal(
            sum(row["candidate_status"] == status for row in rows),
        ):
            raise ValueError(f"{field_name} must match rows")


def _validate_report_consistency(
    report: StrategyResearchBackedTradeCandidateDigestV2Report,
) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.ready_count != _count_status(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count_status(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count_status(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    expected_status = _report_status(
        report.rows,
        report.ready_count,
        report.watch_count,
        report.blocked_count,
    )
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.rows:
        if report.top_candidate_reference != report.rows[0].candidate_reference:
            raise ValueError("top_candidate_reference must match first row")
        expected_ranks = tuple(_count_decimal(index) for index in range(1, len(report.rows) + 1))
        if tuple(row.candidate_rank for row in report.rows) != expected_ranks:
            raise ValueError("candidate ranks must be consecutive")
    elif report.top_candidate_reference is not None:
        raise ValueError("top_candidate_reference must be absent without rows")


def _validate_row_consistency(row: StrategyResearchBackedTradeCandidateDigestV2Row) -> None:
    if row.official_source_anchor_count != _count_decimal(len(row.official_source_anchors)):
        raise ValueError("official_source_anchor_count must match official_source_anchors")
    if row.safety_status == "blocked" and row.candidate_status != "blocked":
        raise ValueError("candidate_status must block when safety_status is blocked")


def _require_payload_fields(
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
    label: str,
) -> None:
    for field_name in expected_fields:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unsafe public field: {label}.{extra_fields[0]}")


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
    message: str | None = None,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(message or f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must not contain control whitespace")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"unsafe public value: {field_name}")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_public_string_tuple(
    field_name: str,
    values: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if require_nonempty and not values:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        normalized.append(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _normalize_public_string_list(
    field_name: str,
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    if require_nonempty and not values:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        normalized.append(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_iso_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    _as_utc(field_name, parsed)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_decimal("source_age_seconds", whole_seconds + fractional_seconds)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_payload(value: Decimal) -> str:
    normalized = _normalize_decimal("payload decimal", value)
    return format(normalized, "f")


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if whole:
        return _normalize_nonnegative_whole_decimal(field_name, parsed)
    if probability:
        return _normalize_probability(field_name, parsed)
    return _normalize_decimal(field_name, parsed)


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_min_ready_at_least_watch(
    message: str,
    ready_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if ready_threshold < watch_threshold:
        raise ValueError(message)


def _require_max_ready_at_most_watch(
    message: str,
    ready_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if ready_threshold > watch_threshold:
        raise ValueError(message)


def _normalize_rows(
    rows: tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...],
) -> tuple[StrategyResearchBackedTradeCandidateDigestV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(
            "row",
            row,
            StrategyResearchBackedTradeCandidateDigestV2Row,
            "rows must contain StrategyResearchBackedTradeCandidateDigestV2Row values",
        )
    return rows


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if hasattr(value, "__dataclass_fields__"):
        for key in value.__dataclass_fields__:
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(f"{label}.{key}", getattr(value, key))
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public field: {label}")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(f"{label}.{key}", child)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", child)
        return
    if type(value) is str and _contains_unsafe_public_text(value):
        raise ValueError(f"unsafe public value: {label}")


def _reject_unsafe_public_key(label: str, key: str) -> None:
    if _contains_unsafe_public_text(key):
        raise ValueError(f"unsafe public field: {label}.{key}")


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


class _DictFlags:
    def __init__(self, values: dict[str, object]) -> None:
        self.paper_only = values.get("paper_only")
        self.report_only = values.get("report_only")
        self.readonly = values.get("readonly")
