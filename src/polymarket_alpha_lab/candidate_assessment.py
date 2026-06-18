"""Paper-only candidate assessment evidence reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.cost_aware_event_strategy import (
    PaperCostAwareEventStrategyReport,
)
from polymarket_alpha_lab.project_screening import (
    PaperProjectScreeningCandidate,
    PaperProjectScreeningQueueItem,
    PaperProjectScreeningReport,
)


__all__ = (
    "PaperCandidateAssessmentConfig",
    "PaperCandidateAssessmentReport",
    "PaperCandidateAssessmentRow",
    "build_paper_candidate_assessment_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")

ASSESSMENT_STATUSES = ("ready", "watch", "blocked")
RESEARCH_BUCKETS = ("research_ready", "watch", "defer", "blocked")
SIDES = ("yes", "no", "none")
BLOCKED_SOURCE_STATUSES = ("blocked_by_inputs", "blocked_by_risk")


@dataclass(frozen=True)
class PaperCandidateAssessmentConfig:
    config_version: str
    min_ready_score: Decimal = Decimal("0.010000")
    max_total_cost_per_share: Decimal = Decimal("0.050000")
    screening_score_weight: Decimal = Decimal("1.0000")
    net_edge_weight: Decimal = Decimal("1.0000")
    confidence_weight: Decimal = Decimal("0.1000")
    spread_penalty_weight: Decimal = Decimal("1.0000")
    resolution_risk_penalty_weight: Decimal = Decimal("1.0000")
    cost_penalty_weight: Decimal = Decimal("1.0000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal("min_ready_score", self.min_ready_score)
        _require_nonnegative_decimal(
            "max_total_cost_per_share",
            self.max_total_cost_per_share,
        )
        for field_name in (
            "screening_score_weight",
            "net_edge_weight",
            "confidence_weight",
            "spread_penalty_weight",
            "resolution_risk_penalty_weight",
            "cost_penalty_weight",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class PaperCandidateAssessmentRow:
    market_slug: str
    question: str
    research_bucket: str
    assessment_status: str
    source_status: str
    selected_side: str
    scoring_side: str
    screening_score: Decimal
    net_edge_per_share: Decimal | None
    total_cost_per_share: Decimal | None
    confidence: Decimal | None
    spread: Decimal | None
    resolution_risk: Decimal | None
    readiness_score: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if self.research_bucket not in RESEARCH_BUCKETS:
            raise ValueError("research_bucket must be a known research bucket")
        if self.assessment_status not in ASSESSMENT_STATUSES:
            raise ValueError("assessment_status must be a known assessment status")
        _require_canonical_string("source_status", self.source_status)
        if self.selected_side not in SIDES:
            raise ValueError("selected_side must be yes, no, or none")
        if self.scoring_side not in SIDES:
            raise ValueError("scoring_side must be yes, no, or none")
        _require_finite_decimal("screening_score", self.screening_score)
        _require_optional_finite_decimal("net_edge_per_share", self.net_edge_per_share)
        _require_optional_nonnegative_decimal(
            "total_cost_per_share",
            self.total_cost_per_share,
        )
        _require_optional_probability_decimal("confidence", self.confidence)
        _require_optional_nonnegative_decimal("spread", self.spread)
        _require_optional_nonnegative_decimal("resolution_risk", self.resolution_risk)
        _require_nonnegative_decimal("readiness_score", self.readiness_score)
        if self.readiness_score > ONE:
            raise ValueError("readiness_score must be at most 1")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperCandidateAssessmentReport:
    generated_at: datetime
    config_version: str
    candidate_count: int
    assessed_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    assessment_rows: tuple[PaperCandidateAssessmentRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "assessed_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "assessment_rows",
            _normalize_assessment_rows(self.assessment_rows),
        )
        if self.candidate_count != len(self.assessment_rows):
            raise ValueError("candidate_count must match assessment_rows")
        if self.assessed_count != len(self.assessment_rows):
            raise ValueError("assessed_count must match assessment_rows")
        if self.ready_count != _status_count(self.assessment_rows, "ready"):
            raise ValueError("ready_count must match assessment_rows")
        if self.watch_count != _status_count(self.assessment_rows, "watch"):
            raise ValueError("watch_count must match assessment_rows")
        if self.blocked_count != _status_count(self.assessment_rows, "blocked"):
            raise ValueError("blocked_count must match assessment_rows")
        slugs = tuple(row.market_slug for row in self.assessment_rows)
        if len(set(slugs)) != len(slugs):
            raise ValueError("assessment_rows must contain unique market_slug values")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_candidate_assessment_report(
    screening_report: PaperProjectScreeningReport,
    cost_reports: Iterable[PaperCostAwareEventStrategyReport],
    *,
    config: PaperCandidateAssessmentConfig,
    generated_at: datetime,
) -> PaperCandidateAssessmentReport:
    """Reduce screening candidates and paper cost evidence into readiness rows."""

    _validate_screening_report(screening_report)
    if type(config) is not PaperCandidateAssessmentConfig:
        raise ValueError("config must be a PaperCandidateAssessmentConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    evidence_reports = _normalize_cost_reports(cost_reports)
    evidence_by_slug = _cost_reports_by_slug(
        evidence_reports,
        screening_report.candidates,
    )
    queue_items_by_slug = _queue_items_by_slug(screening_report.queue_items)
    rows = tuple(
        _row_from_candidate(
            candidate=candidate,
            queue_item=queue_items_by_slug[candidate.market_slug],
            cost_report=evidence_by_slug.get(candidate.market_slug),
            config=config,
        )
        for candidate in screening_report.candidates
    )
    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (-row.readiness_score, row.market_slug),
        ),
    )

    return PaperCandidateAssessmentReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=screening_report.candidate_count,
        assessed_count=len(ordered_rows),
        ready_count=_status_count(ordered_rows, "ready"),
        watch_count=_status_count(ordered_rows, "watch"),
        blocked_count=_status_count(ordered_rows, "blocked"),
        assessment_rows=ordered_rows,
    )


def _row_from_candidate(
    *,
    candidate: PaperProjectScreeningCandidate,
    queue_item: PaperProjectScreeningQueueItem,
    cost_report: PaperCostAwareEventStrategyReport | None,
    config: PaperCandidateAssessmentConfig,
) -> PaperCandidateAssessmentRow:
    selected_side = cost_report.selected_side if cost_report is not None else "none"
    confidence = cost_report.confidence if cost_report is not None else None
    spread = cost_report.spread if cost_report is not None else None
    resolution_risk = cost_report.resolution_risk if cost_report is not None else None
    reason_codes = [*candidate.reason_codes, f"bucket_{queue_item.research_bucket}"]

    assessment_status = _assessment_status(
        candidate=candidate,
        queue_item=queue_item,
        cost_report=cost_report,
        config=config,
        reason_codes=reason_codes,
    )
    readiness_score = (
        ZERO
        if assessment_status == "blocked"
        else _readiness_score(
            screening_score=candidate.screening_score,
            net_edge_per_share=candidate.net_edge_per_share,
            total_cost_per_share=candidate.total_cost_per_share,
            confidence=confidence,
            spread=spread,
            resolution_risk=resolution_risk,
            config=config,
        )
    )

    return PaperCandidateAssessmentRow(
        market_slug=candidate.market_slug,
        question=candidate.question,
        research_bucket=queue_item.research_bucket,
        assessment_status=assessment_status,
        source_status=candidate.source_status,
        selected_side=selected_side,
        scoring_side=candidate.scoring_side,
        screening_score=candidate.screening_score,
        net_edge_per_share=candidate.net_edge_per_share,
        total_cost_per_share=candidate.total_cost_per_share,
        confidence=confidence,
        spread=spread,
        resolution_risk=resolution_risk,
        readiness_score=readiness_score,
        reason_codes=tuple(reason_codes),
    )


def _assessment_status(
    *,
    candidate: PaperProjectScreeningCandidate,
    queue_item: PaperProjectScreeningQueueItem,
    cost_report: PaperCostAwareEventStrategyReport | None,
    config: PaperCandidateAssessmentConfig,
    reason_codes: list[str],
) -> str:
    blocking_reasons: list[str] = []
    if cost_report is None:
        blocking_reasons.append("missing_cost_report")
    if candidate.source_status in BLOCKED_SOURCE_STATUSES:
        blocking_reasons.append("blocked_source")
    if candidate.net_edge_per_share is None:
        blocking_reasons.append("missing_net_edge")
    elif candidate.net_edge_per_share <= ZERO:
        blocking_reasons.append("nonpositive_net_edge")
    if (
        candidate.total_cost_per_share is not None
        and candidate.total_cost_per_share > config.max_total_cost_per_share
    ):
        blocking_reasons.append("high_cost")

    if blocking_reasons:
        reason_codes.extend(blocking_reasons)
        return "blocked"

    if (
        queue_item.research_bucket == "research_ready"
        and candidate.source_status == "paper_review_ready"
        and cost_report is not None
        and cost_report.selected_side != "none"
        and candidate.scoring_side == cost_report.selected_side
        and candidate.screening_score >= config.min_ready_score
        and candidate.net_edge_per_share is not None
        and candidate.net_edge_per_share >= config.min_ready_score
    ):
        reason_codes.append("assessment_ready")
        return "ready"

    if (
        candidate.net_edge_per_share is not None
        and candidate.net_edge_per_share < config.min_ready_score
    ):
        reason_codes.append("low_net_edge")
    if candidate.screening_score < config.min_ready_score:
        reason_codes.append("low_screening_score")
    if cost_report is not None and cost_report.selected_side == "none":
        reason_codes.append("no_selected_side")
    reason_codes.append("positive_edge_watch")
    return "watch"


def _readiness_score(
    *,
    screening_score: Decimal,
    net_edge_per_share: Decimal | None,
    total_cost_per_share: Decimal | None,
    confidence: Decimal | None,
    spread: Decimal | None,
    resolution_risk: Decimal | None,
    config: PaperCandidateAssessmentConfig,
) -> Decimal:
    raw_score = (
        screening_score * config.screening_score_weight
        + (net_edge_per_share if net_edge_per_share is not None else ZERO)
        * config.net_edge_weight
        + (confidence if confidence is not None else ZERO) * config.confidence_weight
        - (spread if spread is not None else ZERO) * config.spread_penalty_weight
        - (resolution_risk if resolution_risk is not None else ZERO)
        * config.resolution_risk_penalty_weight
        - (total_cost_per_share if total_cost_per_share is not None else ZERO)
        * config.cost_penalty_weight
    )
    if raw_score <= ZERO:
        return ZERO.quantize(SCORE_QUANTUM)
    if raw_score >= ONE:
        return ONE.quantize(SCORE_QUANTUM)
    return _quantize_score(raw_score)


def _validate_screening_report(report: PaperProjectScreeningReport) -> None:
    if type(report) is not PaperProjectScreeningReport:
        raise ValueError("screening_report must be a PaperProjectScreeningReport")
    if report.paper_only is not True:
        raise ValueError("screening_report must be paper_only")
    if report.report_only is not True:
        raise ValueError("screening_report must be report_only")


def _normalize_cost_reports(
    reports: Iterable[PaperCostAwareEventStrategyReport],
) -> tuple[PaperCostAwareEventStrategyReport, ...]:
    if isinstance(reports, (str, bytes)):
        raise ValueError("cost_reports must be an iterable of PaperCostAwareEventStrategyReport")
    try:
        items = tuple(reports)
    except TypeError as exc:
        raise ValueError(
            "cost_reports must be an iterable of PaperCostAwareEventStrategyReport",
        ) from exc
    for item in items:
        if type(item) is not PaperCostAwareEventStrategyReport:
            raise ValueError(
                "cost_reports must contain PaperCostAwareEventStrategyReport values",
            )
        if item.paper_only is not True:
            raise ValueError("cost_reports must contain paper_only reports")
        if item.report_only is not True:
            raise ValueError("cost_reports must contain report_only reports")
    return items


def _cost_reports_by_slug(
    reports: tuple[PaperCostAwareEventStrategyReport, ...],
    candidates: tuple[PaperProjectScreeningCandidate, ...],
) -> dict[str, PaperCostAwareEventStrategyReport]:
    candidate_by_slug = {candidate.market_slug: candidate for candidate in candidates}
    report_slugs = tuple(report.market_slug for report in reports)
    if len(set(report_slugs)) != len(report_slugs):
        raise ValueError("cost_reports must contain unique market_slug values")
    extra_slugs = set(report_slugs) - set(candidate_by_slug)
    if extra_slugs:
        raise ValueError("cost_reports must match screening candidates")

    reports_by_slug: dict[str, PaperCostAwareEventStrategyReport] = {}
    for report in reports:
        candidate = candidate_by_slug[report.market_slug]
        if report.question != candidate.question:
            raise ValueError("cost_reports must match screening candidates")
        reports_by_slug[report.market_slug] = report
    return reports_by_slug


def _queue_items_by_slug(
    queue_items: tuple[PaperProjectScreeningQueueItem, ...],
) -> dict[str, PaperProjectScreeningQueueItem]:
    return {item.market_slug: item for item in queue_items}


def _status_count(
    rows: tuple[PaperCandidateAssessmentRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.assessment_status == status)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_nonnegative_decimal(field_name, value)


def _require_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)
        if value < ZERO or value > ONE:
            raise ValueError(f"{field_name} must be between 0 and 1")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_assessment_rows(
    value: tuple[PaperCandidateAssessmentRow, ...],
) -> tuple[PaperCandidateAssessmentRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("assessment_rows must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("assessment_rows must be an iterable") from exc
    if not all(type(item) is PaperCandidateAssessmentRow for item in items):
        raise ValueError("assessment_rows must contain PaperCandidateAssessmentRow values")
    return items


def _quantize_score(value: Decimal) -> Decimal:
    _require_finite_decimal("score", value)
    return value.quantize(SCORE_QUANTUM)
