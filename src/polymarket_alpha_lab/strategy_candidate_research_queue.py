"""Pure paper-only candidate research queue reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable

from polymarket_alpha_lab.action_gated_strategy_recommendation_queue import (
    PaperActionGatedStrategyRecommendationQueueReport,
)
from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
)
from polymarket_alpha_lab.paper_strategy_selection_policy import (
    PaperStrategySelectionPolicyReport,
    PaperStrategySelectionPolicyRow,
)
from polymarket_alpha_lab.strategy_candidate_recommendation import (
    PaperStrategyCandidateRecommendationReport,
    PaperStrategyCandidateRecommendationRow,
)
from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    PaperStrategyRecommendationExplanationReport,
    PaperStrategyRecommendationExplanationRow,
)
from polymarket_alpha_lab.strategy_recommendation_queue import (
    PaperStrategyRecommendationQueueRow,
    PaperStrategyRecommendationQueueSummaryReport,
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")

ACTION_STATUSES = ("research_ready", "watch", "blocked")
NEXT_STEPS = (
    "review_candidate_research_queue",
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
RESEARCH_STATUSES = ("ready", "watch", "blocked")
QUEUE_STATUSES = ("ready", "watch", "blocked")
ACTIONS = ("recommend", "watch", "reject")
DECISIONS = ("selected", "skipped", "not_selected")
SIDES = ("yes", "no", "none")
NO_REASON_CODE = "no_reason_code"
EMPTY_REASON_CODE = "no_candidate_research_rows"

EVIDENCE_GAP_REASON_CODES = (
    "missing_cost_report",
    "missing_net_edge",
    "nonpositive_net_edge",
    "high_cost",
    "low_net_edge",
    "low_screening_score",
    "no_selected_side",
    "below_recommendation_threshold",
    "high_resolution_risk",
    "wide_spread",
    "low_confidence",
    "blocked_source",
    "readiness_watch",
    "readiness_blocked",
    "total_notional_cap_reached",
)


@dataclass(frozen=True)
class PaperStrategyCandidateResearchQueueConfig:
    config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperStrategyCandidateResearchQueueRow:
    research_rank: int
    queue_rank: int
    market_slug: str
    question: str
    selected_side: str
    scoring_side: str
    source_action: str
    decision: str
    queue_status: str
    research_status: str
    research_bucket: str
    assessment_status: str
    source_status: str
    readiness_status: str
    recommendation_score: Decimal
    readiness_score: Decimal
    screening_score: Decimal
    net_edge_per_share: Decimal | None
    total_cost_per_share: Decimal | None
    confidence: Decimal | None
    spread: Decimal | None
    resolution_risk: Decimal | None
    suggested_notional: Decimal
    selected_position_notional: Decimal
    primary_reason_code: str
    research_priority_score: Decimal
    evidence_gap_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    explanation: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("research_rank", self.research_rank)
        _require_positive_int("queue_rank", self.queue_rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("selected_side", self.selected_side)
        _require_side("scoring_side", self.scoring_side)
        _require_action("source_action", self.source_action)
        _require_decision("decision", self.decision)
        _require_status("queue_status", self.queue_status)
        _require_status("research_status", self.research_status)
        _require_canonical_string("research_bucket", self.research_bucket)
        _require_status("assessment_status", self.assessment_status)
        _require_canonical_string("source_status", self.source_status)
        _require_canonical_string("readiness_status", self.readiness_status)
        object.__setattr__(
            self,
            "recommendation_score",
            _quantize_score("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(
            self,
            "readiness_score",
            _quantize_score("readiness_score", self.readiness_score),
        )
        object.__setattr__(
            self,
            "screening_score",
            _quantize_nonnegative_decimal("screening_score", self.screening_score),
        )
        object.__setattr__(
            self,
            "net_edge_per_share",
            _quantize_optional_decimal("net_edge_per_share", self.net_edge_per_share),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _quantize_optional_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _quantize_optional_score("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "spread",
            _quantize_optional_nonnegative_decimal("spread", self.spread),
        )
        object.__setattr__(
            self,
            "resolution_risk",
            _quantize_optional_nonnegative_decimal(
                "resolution_risk",
                self.resolution_risk,
            ),
        )
        object.__setattr__(
            self,
            "suggested_notional",
            _quantize_nonnegative_decimal("suggested_notional", self.suggested_notional),
        )
        object.__setattr__(
            self,
            "selected_position_notional",
            _quantize_nonnegative_decimal(
                "selected_position_notional",
                self.selected_position_notional,
            ),
        )
        _require_canonical_string("primary_reason_code", self.primary_reason_code)
        object.__setattr__(
            self,
            "research_priority_score",
            _quantize_score("research_priority_score", self.research_priority_score),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_reason_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_canonical_string("explanation", self.explanation)
        _validate_row_consistency(self)
        _require_hard_flags("research_row", self)


@dataclass(frozen=True)
class PaperStrategyCandidateResearchQueueReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    action_status: str
    recommended_next_step: str
    source_reason_code_counts: tuple[object, ...]
    research_status: str
    candidate_count: int
    research_ready_count: int
    watch_count: int
    blocked_count: int
    selected_count: int
    skipped_count: int
    not_selected_count: int
    total_ready_notional: Decimal
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    top_research_priority_score: Decimal
    average_research_ready_score: Decimal
    primary_reason_code_counts: tuple[tuple[str, int], ...]
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_action_status("action_status", self.action_status)
        _require_next_step("recommended_next_step", self.recommended_next_step)
        _require_status("research_status", self.research_status)
        for field_name in (
            "candidate_count",
            "research_ready_count",
            "watch_count",
            "blocked_count",
            "selected_count",
            "skipped_count",
            "not_selected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_ready_notional",
            _quantize_nonnegative_decimal(
                "total_ready_notional",
                self.total_ready_notional,
            ),
        )
        object.__setattr__(
            self,
            "total_selected_notional",
            _quantize_nonnegative_decimal(
                "total_selected_notional",
                self.total_selected_notional,
            ),
        )
        object.__setattr__(
            self,
            "total_suggested_notional",
            _quantize_nonnegative_decimal(
                "total_suggested_notional",
                self.total_suggested_notional,
            ),
        )
        object.__setattr__(
            self,
            "top_research_priority_score",
            _quantize_score(
                "top_research_priority_score",
                self.top_research_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "average_research_ready_score",
            _quantize_score(
                "average_research_ready_score",
                self.average_research_ready_score,
            ),
        )
        object.__setattr__(
            self,
            "primary_reason_code_counts",
            _normalize_reason_code_counts(self.primary_reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("research_report", self)


def build_paper_strategy_candidate_research_queue_report(
    source_report: object,
    *,
    config: PaperStrategyCandidateResearchQueueConfig,
    generated_at: datetime,
) -> PaperStrategyCandidateResearchQueueReport:
    """Build a readonly research work queue from an action-gated paper queue."""

    if type(source_report) is not PaperActionGatedStrategyRecommendationQueueReport:
        raise ValueError(
            "source_report must be a "
            "PaperActionGatedStrategyRecommendationQueueReport",
        )
    if type(config) is not PaperStrategyCandidateResearchQueueConfig:
        raise ValueError(
            "config must be a PaperStrategyCandidateResearchQueueConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("source_report", source_report)
    _require_hard_flags("config", config)

    if source_report.action_status != "research_ready":
        return _empty_report(
            source_report,
            config=config,
            generated_at=generated_at,
            research_status=source_report.action_status,
            reason_code=f"source_action_status_{source_report.action_status}",
        )

    assessment_report = _required_nested_report(
        "candidate_assessment_report",
        source_report.candidate_assessment_report,
        PaperCandidateAssessmentReport,
    )
    bundle_report = _required_nested_report(
        "bundle_report",
        source_report.bundle_report,
        PaperStrategyRecommendationBundleReport,
    )
    queue_summary_report = _required_nested_report(
        "queue_summary_report",
        source_report.queue_summary_report,
        PaperStrategyRecommendationQueueSummaryReport,
    )
    _validate_nested_reports(
        assessment_report=assessment_report,
        bundle_report=bundle_report,
        queue_summary_report=queue_summary_report,
    )

    joined = _joined_rows(
        assessment_report=assessment_report,
        bundle_report=bundle_report,
        queue_summary_report=queue_summary_report,
    )
    rows = tuple(
        _research_row_from_joined_values(index, values)
        for index, values in enumerate(joined, start=1)
    )
    if not rows:
        return _empty_report(
            source_report,
            config=config,
            generated_at=generated_at,
            research_status="watch",
            reason_code=EMPTY_REASON_CODE,
        )

    return PaperStrategyCandidateResearchQueueReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=source_report.config_version,
        action_status=source_report.action_status,
        recommended_next_step=source_report.recommended_next_step,
        source_reason_code_counts=source_report.reason_code_counts,
        research_status="ready",
        candidate_count=len(rows),
        research_ready_count=_research_status_count(rows, "ready"),
        watch_count=_research_status_count(rows, "watch"),
        blocked_count=_research_status_count(rows, "blocked"),
        selected_count=_decision_count(rows, "selected"),
        skipped_count=_decision_count(rows, "skipped"),
        not_selected_count=_decision_count(rows, "not_selected"),
        total_ready_notional=_total_ready_notional(rows),
        total_selected_notional=_total_selected_notional(rows),
        total_suggested_notional=_total_suggested_notional(rows),
        top_research_priority_score=rows[0].research_priority_score,
        average_research_ready_score=_average_ready_score(rows),
        primary_reason_code_counts=_primary_reason_code_counts(rows),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def _empty_report(
    source_report: PaperActionGatedStrategyRecommendationQueueReport,
    *,
    config: PaperStrategyCandidateResearchQueueConfig,
    generated_at: datetime,
    research_status: str,
    reason_code: str,
) -> PaperStrategyCandidateResearchQueueReport:
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=source_report.config_version,
        action_status=source_report.action_status,
        recommended_next_step=source_report.recommended_next_step,
        source_reason_code_counts=source_report.reason_code_counts,
        research_status=research_status,
        candidate_count=0,
        research_ready_count=0,
        watch_count=0,
        blocked_count=0,
        selected_count=0,
        skipped_count=0,
        not_selected_count=0,
        total_ready_notional=ZERO.quantize(QUANTUM),
        total_selected_notional=ZERO.quantize(QUANTUM),
        total_suggested_notional=ZERO.quantize(QUANTUM),
        top_research_priority_score=ZERO.quantize(QUANTUM),
        average_research_ready_score=ZERO.quantize(QUANTUM),
        primary_reason_code_counts=(),
        rows=(),
        reason_codes=(reason_code,),
    )


def _required_nested_report(
    field_name: str,
    value: object,
    expected_type: type[object],
):
    if value is None:
        raise ValueError(f"{field_name} is required for research_ready sources")
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)
    return value


def _validate_nested_reports(
    *,
    assessment_report: PaperCandidateAssessmentReport,
    bundle_report: PaperStrategyRecommendationBundleReport,
    queue_summary_report: PaperStrategyRecommendationQueueSummaryReport,
) -> None:
    _require_hard_flags("candidate_assessment_report", assessment_report)
    _require_hard_flags("bundle_report", bundle_report)
    _require_hard_flags("recommendation_report", bundle_report.recommendation_report)
    _require_hard_flags("selection_policy_report", bundle_report.selection_policy_report)
    _require_hard_flags("explanation_report", bundle_report.explanation_report)
    _require_hard_flags("queue_summary_report", queue_summary_report)
    _validate_assessment_rows(assessment_report.assessment_rows)
    _validate_recommendation_rows(bundle_report.recommendation_report.recommendation_rows)
    _validate_selection_rows(bundle_report.selection_policy_report.selection_rows)
    _validate_explanation_rows(bundle_report.explanation_report.explanation_rows)
    _validate_queue_rows(queue_summary_report.queue_rows)


def _joined_rows(
    *,
    assessment_report: PaperCandidateAssessmentReport,
    bundle_report: PaperStrategyRecommendationBundleReport,
    queue_summary_report: PaperStrategyRecommendationQueueSummaryReport,
) -> tuple[dict[str, object], ...]:
    queue_by_slug = _rows_by_slug(
        "queue_summary_report rows",
        queue_summary_report.queue_rows,
    )
    assessment_by_slug = _rows_by_slug(
        "candidate_assessment_report rows",
        assessment_report.assessment_rows,
    )
    recommendation_by_slug = _rows_by_slug(
        "recommendation_report rows",
        bundle_report.recommendation_report.recommendation_rows,
    )
    selection_by_slug = _rows_by_slug(
        "selection_policy_report rows",
        bundle_report.selection_policy_report.selection_rows,
    )
    explanation_by_slug = _rows_by_slug(
        "explanation_report rows",
        bundle_report.explanation_report.explanation_rows,
    )
    _require_matching_slug_sets(
        queue_by_slug,
        assessment_by_slug,
        recommendation_by_slug,
        selection_by_slug,
        explanation_by_slug,
    )

    joined: list[dict[str, object]] = []
    for queue_row in queue_summary_report.queue_rows:
        assessment_row = assessment_by_slug[queue_row.market_slug]
        recommendation_row = recommendation_by_slug[queue_row.market_slug]
        selection_row = selection_by_slug[queue_row.market_slug]
        explanation_row = explanation_by_slug[queue_row.market_slug]
        _validate_joined_row(
            queue_row=queue_row,
            assessment_row=assessment_row,
            recommendation_row=recommendation_row,
            selection_row=selection_row,
            explanation_row=explanation_row,
        )
        joined.append(
            {
                "queue_row": queue_row,
                "assessment_row": assessment_row,
                "recommendation_row": recommendation_row,
                "selection_row": selection_row,
                "explanation_row": explanation_row,
            },
        )
    return tuple(joined)


def _research_row_from_joined_values(
    research_rank: int,
    values: dict[str, object],
) -> PaperStrategyCandidateResearchQueueRow:
    queue_row = values["queue_row"]
    assessment_row = values["assessment_row"]
    recommendation_row = values["recommendation_row"]
    selection_row = values["selection_row"]
    explanation_row = values["explanation_row"]
    if (
        type(queue_row) is not PaperStrategyRecommendationQueueRow
        or type(assessment_row) is not PaperCandidateAssessmentRow
        or type(recommendation_row) is not PaperStrategyCandidateRecommendationRow
        or type(selection_row) is not PaperStrategySelectionPolicyRow
        or type(explanation_row) is not PaperStrategyRecommendationExplanationRow
    ):
        raise ValueError("joined rows must contain expected row values")
    reason_codes = _combined_reason_codes(
        assessment_row.reason_codes,
        recommendation_row.reason_codes,
        selection_row.reason_codes,
        explanation_row.reason_codes,
    )
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=queue_row.rank,
        market_slug=queue_row.market_slug,
        question=assessment_row.question,
        selected_side=queue_row.selected_side,
        scoring_side=assessment_row.scoring_side,
        source_action=queue_row.action,
        decision=queue_row.decision,
        queue_status=queue_row.queue_status,
        research_status=_research_status_from_queue_status(queue_row.queue_status),
        research_bucket=assessment_row.research_bucket,
        assessment_status=assessment_row.assessment_status,
        source_status=assessment_row.source_status,
        readiness_status=recommendation_row.readiness_status,
        recommendation_score=queue_row.recommendation_score,
        readiness_score=assessment_row.readiness_score,
        screening_score=assessment_row.screening_score,
        net_edge_per_share=assessment_row.net_edge_per_share,
        total_cost_per_share=assessment_row.total_cost_per_share,
        confidence=assessment_row.confidence,
        spread=assessment_row.spread,
        resolution_risk=assessment_row.resolution_risk,
        suggested_notional=queue_row.suggested_notional,
        selected_position_notional=selection_row.selected_position_notional,
        primary_reason_code=queue_row.primary_reason_code,
        research_priority_score=_research_priority_score(
            queue_row.recommendation_score,
            assessment_row.readiness_score,
        ),
        evidence_gap_codes=_evidence_gap_codes(reason_codes),
        reason_codes=reason_codes,
        explanation=explanation_row.explanation,
    )


def _validate_joined_row(
    *,
    queue_row: PaperStrategyRecommendationQueueRow,
    assessment_row: PaperCandidateAssessmentRow,
    recommendation_row: PaperStrategyCandidateRecommendationRow,
    selection_row: PaperStrategySelectionPolicyRow,
    explanation_row: PaperStrategyRecommendationExplanationRow,
) -> None:
    if assessment_row.question != recommendation_row.question:
        raise ValueError("candidate research rows must match question")
    if assessment_row.question != selection_row.question:
        raise ValueError("candidate research rows must match question")
    if queue_row.selected_side != recommendation_row.selected_side:
        raise ValueError("candidate research rows must match selected_side")
    if queue_row.selected_side != selection_row.selected_side:
        raise ValueError("candidate research rows must match selected_side")
    if queue_row.selected_side != explanation_row.selected_side:
        raise ValueError("candidate research rows must match selected_side")
    if queue_row.action != recommendation_row.action:
        raise ValueError("candidate research rows must match action")
    if queue_row.action != selection_row.source_action:
        raise ValueError("candidate research rows must match action")
    if queue_row.action != explanation_row.action:
        raise ValueError("candidate research rows must match action")
    if queue_row.decision != selection_row.decision:
        raise ValueError("candidate research rows must match decision")
    if queue_row.recommendation_score != recommendation_row.recommendation_score:
        raise ValueError("candidate research rows must match recommendation_score")
    if queue_row.recommendation_score != selection_row.recommendation_score:
        raise ValueError("candidate research rows must match recommendation_score")
    if queue_row.recommendation_score != explanation_row.recommendation_score:
        raise ValueError("candidate research rows must match recommendation_score")
    if queue_row.suggested_notional != selection_row.suggested_position_notional:
        raise ValueError("candidate research rows must match suggested_notional")
    if queue_row.primary_reason_code != explanation_row.primary_reason_code:
        raise ValueError("candidate research rows must match primary_reason_code")
    if recommendation_row.reason_codes != explanation_row.reason_codes:
        raise ValueError("candidate research rows must match reason_codes")


def _rows_by_slug(field_name: str, rows: Iterable[object]) -> dict[str, object]:
    by_slug: dict[str, object] = {}
    for row in rows:
        slug = getattr(row, "market_slug", None)
        _require_canonical_string("market_slug", slug)
        if slug in by_slug:
            raise ValueError(f"{field_name} must have unique market_slug values")
        by_slug[slug] = row
    return by_slug


def _require_matching_slug_sets(*maps: dict[str, object]) -> None:
    if not maps:
        return
    expected = set(maps[0])
    for item in maps[1:]:
        if set(item) != expected:
            raise ValueError("candidate research row sources must match market_slug values")


def _validate_assessment_rows(rows: Iterable[object]) -> None:
    for row in rows:
        if type(row) is not PaperCandidateAssessmentRow:
            raise ValueError(
                "candidate_assessment_report rows must contain "
                "PaperCandidateAssessmentRow values",
            )
        _require_optional_hard_flags("candidate_assessment_row", row)


def _validate_recommendation_rows(rows: Iterable[object]) -> None:
    for row in rows:
        if type(row) is not PaperStrategyCandidateRecommendationRow:
            raise ValueError(
                "recommendation_report rows must contain "
                "PaperStrategyCandidateRecommendationRow values",
            )
        _require_optional_hard_flags("recommendation_row", row)


def _validate_selection_rows(rows: Iterable[object]) -> None:
    for row in rows:
        if type(row) is not PaperStrategySelectionPolicyRow:
            raise ValueError(
                "selection_policy_report rows must contain "
                "PaperStrategySelectionPolicyRow values",
            )
        _require_optional_hard_flags("selection_row", row)


def _validate_explanation_rows(rows: Iterable[object]) -> None:
    for row in rows:
        if type(row) is not PaperStrategyRecommendationExplanationRow:
            raise ValueError(
                "explanation_report rows must contain "
                "PaperStrategyRecommendationExplanationRow values",
            )
        _require_optional_hard_flags("explanation_row", row)


def _validate_queue_rows(rows: Iterable[object]) -> None:
    for row in rows:
        if type(row) is not PaperStrategyRecommendationQueueRow:
            raise ValueError(
                "queue_summary_report rows must contain "
                "PaperStrategyRecommendationQueueRow values",
            )
        _require_optional_hard_flags("queue_row", row)


def _research_priority_score(
    recommendation_score: Decimal,
    readiness_score: Decimal,
) -> Decimal:
    return _quantize_score(
        "research_priority_score",
        (recommendation_score + readiness_score) / Decimal("2"),
    )


def _research_status_from_queue_status(queue_status: str) -> str:
    if queue_status == "ready":
        return "ready"
    if queue_status == "watch":
        return "watch"
    return "blocked"


def _combined_reason_codes(*values: Iterable[str]) -> tuple[str, ...]:
    combined: list[str] = []
    for item in values:
        for reason_code in item:
            _require_canonical_string("reason_codes", reason_code)
            if reason_code not in combined:
                combined.append(reason_code)
    if not combined:
        combined.append(NO_REASON_CODE)
    return tuple(combined)


def _evidence_gap_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    gaps: list[str] = []
    for reason_code in reason_codes:
        if reason_code in EVIDENCE_GAP_REASON_CODES and reason_code not in gaps:
            gaps.append(reason_code)
    return tuple(gaps)


def _validate_row_consistency(row: PaperStrategyCandidateResearchQueueRow) -> None:
    if row.research_status != _research_status_from_queue_status(row.queue_status):
        raise ValueError("research_status must match queue_status")
    if row.research_priority_score != _research_priority_score(
        row.recommendation_score,
        row.readiness_score,
    ):
        raise ValueError("research_priority_score must match row scores")
    if row.primary_reason_code not in row.reason_codes:
        raise ValueError("primary_reason_code must be represented in reason_codes")
    for gap_code in row.evidence_gap_codes:
        if gap_code not in row.reason_codes:
            raise ValueError("evidence_gap_codes must be represented in reason_codes")
    if row.research_status == "ready":
        if row.selected_side == "none":
            raise ValueError("ready rows must have a selected side")
        if row.suggested_notional <= ZERO:
            raise ValueError("ready rows must have positive suggested_notional")
    if row.decision == "selected":
        if row.selected_position_notional != row.suggested_notional:
            raise ValueError("selected rows must use suggested_notional")
    elif row.selected_position_notional != ZERO.quantize(QUANTUM):
        raise ValueError("unselected rows must have zero selected_position_notional")


def _validate_report_consistency(report: PaperStrategyCandidateResearchQueueReport) -> None:
    if report.candidate_count != len(report.rows):
        raise ValueError("candidate_count must match rows")
    if report.research_ready_count != _research_status_count(report.rows, "ready"):
        raise ValueError("research_ready_count must match rows")
    if report.watch_count != _research_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _research_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if (
        report.research_ready_count + report.watch_count + report.blocked_count
        != report.candidate_count
    ):
        raise ValueError("research status counts must match candidate_count")
    if report.selected_count != _decision_count(report.rows, "selected"):
        raise ValueError("selected_count must match rows")
    if report.skipped_count != _decision_count(report.rows, "skipped"):
        raise ValueError("skipped_count must match rows")
    if report.not_selected_count != _decision_count(report.rows, "not_selected"):
        raise ValueError("not_selected_count must match rows")
    if (
        report.selected_count + report.skipped_count + report.not_selected_count
        != report.candidate_count
    ):
        raise ValueError("decision counts must match candidate_count")
    if tuple(row.research_rank for row in report.rows) != tuple(
        range(1, len(report.rows) + 1),
    ):
        raise ValueError("research_rank values must be contiguous")
    if tuple(row.queue_rank for row in report.rows) != tuple(
        range(1, len(report.rows) + 1),
    ):
        raise ValueError("queue_rank values must be contiguous")
    if report.total_ready_notional != _total_ready_notional(report.rows):
        raise ValueError("total_ready_notional must match rows")
    if report.total_selected_notional != _total_selected_notional(report.rows):
        raise ValueError("total_selected_notional must match rows")
    if report.total_suggested_notional != _total_suggested_notional(report.rows):
        raise ValueError("total_suggested_notional must match rows")
    if report.top_research_priority_score != _top_score(report.rows):
        raise ValueError("top_research_priority_score must match rows")
    if report.average_research_ready_score != _average_ready_score(report.rows):
        raise ValueError("average_research_ready_score must match rows")
    if report.primary_reason_code_counts != _primary_reason_code_counts(report.rows):
        raise ValueError("primary_reason_code_counts must match rows")
    if not report.rows:
        if report.reason_codes != (EMPTY_REASON_CODE,) and not all(
            reason_code.startswith("source_action_status_")
            for reason_code in report.reason_codes
        ):
            raise ValueError("empty reports must explain their empty queue")
    elif report.research_status != "ready":
        raise ValueError("reports with rows must be ready for research review")


def _normalize_rows(value: object) -> tuple[PaperStrategyCandidateResearchQueueRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperStrategyCandidateResearchQueueRow:
            raise ValueError("rows must contain PaperStrategyCandidateResearchQueueRow values")
        _require_hard_flags("research_row", row)
    return rows


def _research_status_count(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.research_status == status)


def _decision_count(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
    decision: str,
) -> int:
    return sum(1 for row in rows if row.decision == decision)


def _total_ready_notional(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_ready_notional",
        sum(
            (
                row.suggested_notional
                for row in rows
                if row.research_status == "ready"
            ),
            ZERO,
        ),
    )


def _total_selected_notional(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_selected_notional",
        sum((row.selected_position_notional for row in rows), ZERO),
    )


def _total_suggested_notional(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_suggested_notional",
        sum(
            (
                row.suggested_notional
                for row in rows
                if row.source_action == "recommend"
            ),
            ZERO,
        ),
    )


def _top_score(rows: tuple[PaperStrategyCandidateResearchQueueRow, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANTUM)
    return rows[0].research_priority_score


def _average_ready_score(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> Decimal:
    ready_rows = tuple(row for row in rows if row.research_status == "ready")
    if not ready_rows:
        return ZERO.quantize(QUANTUM)
    return _quantize_score(
        "average_research_ready_score",
        sum((row.research_priority_score for row in ready_rows), ZERO)
        / Decimal(len(ready_rows)),
    )


def _primary_reason_code_counts(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("primary_reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("primary_reason_code_counts must be an iterable") from exc
    for item in counts:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("primary_reason_code_counts must contain tuple rows")
        reason_code, count = item
        _require_canonical_string("primary_reason_code", reason_code)
        _require_nonnegative_int("primary_reason_code count", count)
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    normalized: list[str] = []
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _quantize_decimal(field_name, value)


def _quantize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _quantize_nonnegative_decimal(field_name, value)


def _quantize_score(field_name: str, value: object) -> Decimal:
    score = _quantize_nonnegative_decimal(field_name, value)
    if score > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return score


def _quantize_optional_score(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _quantize_score(field_name, value)


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known candidate research next step")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_decision(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DECISIONS:
        raise ValueError(f"{field_name} must be selected, skipped, or not_selected")


def _require_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _require_optional_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if hasattr(value, flag_name) and getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


__all__ = (
    "PaperStrategyCandidateResearchQueueConfig",
    "PaperStrategyCandidateResearchQueueReport",
    "PaperStrategyCandidateResearchQueueRow",
    "build_paper_strategy_candidate_research_queue_report",
)
