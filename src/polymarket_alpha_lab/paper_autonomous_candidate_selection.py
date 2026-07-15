"""Pure paper-only candidate selection reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)
DEFAULT_PAPER_AUTONOMOUS_CANDIDATE_SELECTION_CONFIG_VERSION = (
    "paper-autonomous-candidate-selection-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")

SELECTION_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_STATUS = {
    "pass": "review_paper_candidate_selection",
    "watch": "review_paper_candidate_selection_warnings",
    "blocked": "repair_paper_candidate_selection_inputs",
}
SOURCE_ACTION_STATUSES = ("research_ready", "watch", "blocked")
SOURCE_STATUSES = ("ready", "watch", "blocked")
ACTIONS = ("recommend", "watch", "reject")
DECISIONS = ("selected", "skipped", "not_selected")
SIDES = ("yes", "no", "none")
ROW_SELECTION_STATUSES = ("selected", "not_selected")

PASS_REASON_CODE = "paper_autonomous_candidate_selection_pass"
NO_SELECTED_REASON_CODE = "paper_autonomous_candidate_selection_no_selected_candidates"
SOURCE_WARNING_REASON_CODE = "paper_autonomous_candidate_selection_source_warning"
DUPLICATE_REASON_CODE = "paper_autonomous_candidate_selection_duplicate_suppressed"
MAX_SELECTED_REASON_CODE = (
    "paper_autonomous_candidate_selection_max_selected_candidate_count_reached"
)
DECISION_MATRIX_SUPPRESSED_REASON_CODE = (
    "paper_autonomous_candidate_selection_decision_matrix_suppressed"
)

ROW_SELECTED_REASON_CODE = "candidate_selection_selected"
ROW_DUPLICATE_REASON_CODE = "candidate_selection_duplicate_suppressed"
ROW_MAX_SELECTED_REASON_CODE = (
    "candidate_selection_max_selected_candidate_count_reached"
)
ROW_DECISION_MATRIX_SUPPRESSED_REASON_CODE = (
    "candidate_selection_decision_matrix_suppressed"
)
ROW_DECISION_MATRIX_STATUS_REASON_PREFIX = "candidate_selection_decision_matrix_"


@dataclass(frozen=True)
class PaperAutonomousCandidateSelectionConfig:
    config_version: str = DEFAULT_PAPER_AUTONOMOUS_CANDIDATE_SELECTION_CONFIG_VERSION
    min_net_edge_per_share: Decimal = Decimal("0.000001")
    min_research_priority_score: Decimal = Decimal("0.000000")
    max_selected_candidate_count: int = 25
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousCandidateSelectionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousCandidateSelectionConfig:
            raise ValueError(
                "config must be exactly PaperAutonomousCandidateSelectionConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_net_edge_per_share",
            _quantize_nonnegative_decimal(
                "min_net_edge_per_share",
                self.min_net_edge_per_share,
            ),
        )
        object.__setattr__(
            self,
            "min_research_priority_score",
            _quantize_score(
                "min_research_priority_score",
                self.min_research_priority_score,
            ),
        )
        _require_positive_int(
            "max_selected_candidate_count",
            self.max_selected_candidate_count,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperAutonomousCandidateSelectionSourceSummary:
    source_number: int
    generated_at: datetime
    config_version: str
    upstream_source_config_version: str
    action_status: str
    research_status: str
    recommended_next_step: str
    candidate_count: int
    research_ready_count: int
    selected_candidate_count: int
    source_warning: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousCandidateSelectionSourceSummary "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousCandidateSelectionSourceSummary:
            raise ValueError(
                "source summary must be exactly "
                "PaperAutonomousCandidateSelectionSourceSummary",
            )
        _require_positive_int("source_number", self.source_number)
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "upstream_source_config_version",
            self.upstream_source_config_version,
        )
        _require_action_status("action_status", self.action_status)
        _require_status("research_status", self.research_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("candidate_count", self.candidate_count)
        _require_nonnegative_int("research_ready_count", self.research_ready_count)
        _require_nonnegative_int(
            "selected_candidate_count",
            self.selected_candidate_count,
        )
        if type(self.source_warning) is not bool:
            raise ValueError("source_warning must be a bool")
        _require_hard_flags("source summary", self)


@dataclass(frozen=True)
class PaperAutonomousCandidateSelectionReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousCandidateSelectionReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousCandidateSelectionReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperAutonomousCandidateSelectionReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperAutonomousCandidateSelectionRow:
    row_number: int
    source_number: int
    source_generated_at: datetime
    source_config_version: str
    upstream_source_config_version: str
    source_action_status: str
    source_recommended_next_step: str
    source_research_status: str
    research_rank: int
    queue_rank: int
    market_slug: str
    question: str
    selected_side: str
    scoring_side: str
    source_action: str
    source_decision: str
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
    source_selected_position_notional: Decimal
    primary_reason_code: str
    research_priority_score: Decimal
    evidence_gap_codes: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    explanation: str
    selection_status: str
    selected_notional: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousCandidateSelectionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousCandidateSelectionRow:
            raise ValueError(
                "row must be exactly PaperAutonomousCandidateSelectionRow",
            )
        _require_positive_int("row_number", self.row_number)
        _require_positive_int("source_number", self.source_number)
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc(self.source_generated_at),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_canonical_string(
            "upstream_source_config_version",
            self.upstream_source_config_version,
        )
        _require_action_status("source_action_status", self.source_action_status)
        _require_canonical_string(
            "source_recommended_next_step",
            self.source_recommended_next_step,
        )
        _require_status("source_research_status", self.source_research_status)
        _require_positive_int("research_rank", self.research_rank)
        _require_positive_int("queue_rank", self.queue_rank)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_side("selected_side", self.selected_side)
        _require_side("scoring_side", self.scoring_side)
        _require_action("source_action", self.source_action)
        _require_decision("source_decision", self.source_decision)
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
            _quantize_nonnegative_decimal(
                "suggested_notional",
                self.suggested_notional,
            ),
        )
        object.__setattr__(
            self,
            "source_selected_position_notional",
            _quantize_nonnegative_decimal(
                "source_selected_position_notional",
                self.source_selected_position_notional,
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
            "source_reason_codes",
            _normalize_reason_codes("source_reason_codes", self.source_reason_codes),
        )
        _require_canonical_string("explanation", self.explanation)
        _require_row_selection_status("selection_status", self.selection_status)
        object.__setattr__(
            self,
            "selected_notional",
            _quantize_nonnegative_decimal("selected_notional", self.selected_notional),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("selection row", self)


@dataclass(frozen=True)
class PaperAutonomousCandidateSelectionReport:
    generated_at: datetime
    config_version: str
    selection_status: str
    recommended_next_step: str
    source_report_count: int
    source_config_versions: tuple[str, ...]
    source_summaries: tuple[PaperAutonomousCandidateSelectionSourceSummary, ...]
    candidate_count: int
    selected_candidate_count: int
    not_selected_candidate_count: int
    duplicate_suppressed_count: int
    max_selected_candidate_count_suppressed_count: int
    source_warning_count: int
    total_selected_notional: Decimal
    total_suggested_notional: Decimal
    rows: tuple[PaperAutonomousCandidateSelectionRow, ...]
    reason_code_counts: tuple[PaperAutonomousCandidateSelectionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperAutonomousCandidateSelectionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperAutonomousCandidateSelectionReport:
            raise ValueError(
                "report must be exactly PaperAutonomousCandidateSelectionReport",
            )
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_selection_status("selection_status", self.selection_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_source_summaries(self.source_summaries),
        )
        for field_name in (
            "candidate_count",
            "selected_candidate_count",
            "not_selected_candidate_count",
            "duplicate_suppressed_count",
            "max_selected_candidate_count_suppressed_count",
            "source_warning_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
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
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("selection report", self)


def build_paper_autonomous_candidate_selection_report(
    source_reports: object,
    *,
    config: PaperAutonomousCandidateSelectionConfig,
    generated_at: datetime,
    decision_matrix_report: object | None = None,
) -> PaperAutonomousCandidateSelectionReport:
    if type(source_reports) is not tuple:
        raise ValueError("source_reports must be a tuple")
    if type(config) is not PaperAutonomousCandidateSelectionConfig:
        raise ValueError(
            "config must be exactly PaperAutonomousCandidateSelectionConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc(generated_at)
    decision_matrix_rows_by_slug = _decision_matrix_rows_by_slug(
        decision_matrix_report,
        source_reports,
    )

    selected_keys: set[tuple[str, str]] = set()
    selected_count = 0
    rows: list[PaperAutonomousCandidateSelectionRow] = []
    summaries: list[PaperAutonomousCandidateSelectionSourceSummary] = []

    for source_number, source_report in enumerate(source_reports, start=1):
        if type(source_report) is not PaperStrategyCandidateResearchQueueReport:
            raise ValueError(
                "source_reports must contain exact "
                "PaperStrategyCandidateResearchQueueReport values",
            )
        _require_hard_flags("source_report", source_report)
        _validate_source_rows(source_report.rows)
        source_selected_count = 0
        for source_row in source_report.rows:
            selected, reason_codes = _row_selection_result(
                source_report,
                source_row,
                config=config,
                selected_keys=selected_keys,
                selected_count=selected_count,
                decision_matrix_rows_by_slug=decision_matrix_rows_by_slug,
            )
            if selected:
                selected_count += 1
                source_selected_count += 1
                selected_keys.add((source_row.market_slug, source_row.selected_side))
            rows.append(
                _selection_row_from_source_row(
                    row_number=len(rows) + 1,
                    source_number=source_number,
                    source_report=source_report,
                    source_row=source_row,
                    selected=selected,
                    reason_codes=reason_codes,
                ),
            )
        summaries.append(
            _source_summary(
                source_number=source_number,
                source_report=source_report,
                selected_candidate_count=source_selected_count,
            ),
        )

    rows_tuple = tuple(rows)
    summaries_tuple = tuple(summaries)
    source_warning_count = sum(1 for item in summaries_tuple if item.source_warning)
    duplicate_count = _rows_with_reason(rows_tuple, ROW_DUPLICATE_REASON_CODE)
    max_count = _rows_with_reason(rows_tuple, ROW_MAX_SELECTED_REASON_CODE)
    decision_matrix_suppressed_count = _rows_with_reason(
        rows_tuple,
        ROW_DECISION_MATRIX_SUPPRESSED_REASON_CODE,
    )
    reason_codes = _report_reason_codes(
        selected_candidate_count=selected_count,
        source_warning_count=source_warning_count,
        duplicate_suppressed_count=duplicate_count,
        max_selected_candidate_count_suppressed_count=max_count,
        decision_matrix_suppressed_count=decision_matrix_suppressed_count,
    )
    selection_status = _selection_status(
        selected_candidate_count=selected_count,
        source_warning_count=source_warning_count,
        duplicate_suppressed_count=duplicate_count,
        max_selected_candidate_count_suppressed_count=max_count,
        decision_matrix_suppressed_count=decision_matrix_suppressed_count,
    )

    return PaperAutonomousCandidateSelectionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        selection_status=selection_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[selection_status],
        source_report_count=len(source_reports),
        source_config_versions=tuple(report.config_version for report in source_reports),
        source_summaries=summaries_tuple,
        candidate_count=len(rows_tuple),
        selected_candidate_count=selected_count,
        not_selected_candidate_count=len(rows_tuple) - selected_count,
        duplicate_suppressed_count=duplicate_count,
        max_selected_candidate_count_suppressed_count=max_count,
        source_warning_count=source_warning_count,
        total_selected_notional=_total_selected_notional(rows_tuple),
        total_suggested_notional=_total_suggested_notional(rows_tuple),
        rows=rows_tuple,
        reason_code_counts=_reason_code_counts(reason_codes),
        reason_codes=reason_codes,
    )


def _row_selection_result(
    source_report: PaperStrategyCandidateResearchQueueReport,
    source_row: PaperStrategyCandidateResearchQueueRow,
    *,
    config: PaperAutonomousCandidateSelectionConfig,
    selected_keys: set[tuple[str, str]],
    selected_count: int,
    decision_matrix_rows_by_slug: dict[str, object] | None,
) -> tuple[bool, tuple[str, ...]]:
    reason_codes = _base_not_selected_reason_codes(source_report, source_row, config)
    if reason_codes:
        return False, reason_codes
    decision_matrix_reason_codes = _decision_matrix_not_selected_reason_codes(
        source_row,
        decision_matrix_rows_by_slug,
    )
    if decision_matrix_reason_codes:
        return False, decision_matrix_reason_codes
    key = (source_row.market_slug, source_row.selected_side)
    if key in selected_keys:
        return False, (ROW_DUPLICATE_REASON_CODE,)
    if selected_count >= config.max_selected_candidate_count:
        return False, (ROW_MAX_SELECTED_REASON_CODE,)
    return True, (ROW_SELECTED_REASON_CODE,)


def _decision_matrix_not_selected_reason_codes(
    source_row: PaperStrategyCandidateResearchQueueRow,
    decision_matrix_rows_by_slug: dict[str, object] | None,
) -> tuple[str, ...]:
    if decision_matrix_rows_by_slug is None:
        return ()
    decision_row = decision_matrix_rows_by_slug[source_row.market_slug]
    if decision_row.decision_status == "candidate":
        return ()
    return (
        ROW_DECISION_MATRIX_SUPPRESSED_REASON_CODE,
        f"{ROW_DECISION_MATRIX_STATUS_REASON_PREFIX}{decision_row.decision_status}",
        *decision_row.reason_codes,
    )


def _base_not_selected_reason_codes(
    source_report: PaperStrategyCandidateResearchQueueReport,
    source_row: PaperStrategyCandidateResearchQueueRow,
    config: PaperAutonomousCandidateSelectionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_report.action_status != "research_ready":
        reason_codes.append("source_action_status_not_research_ready")
    if source_report.research_status != "ready":
        reason_codes.append("source_research_status_not_ready")
    if source_row.research_status != "ready":
        reason_codes.append("candidate_selection_research_status_not_ready")
    if source_row.source_action != "recommend":
        reason_codes.append("candidate_selection_source_action_not_recommend")
    if source_row.decision != "selected":
        reason_codes.append("candidate_selection_source_decision_not_selected")
    if source_row.selected_side not in ("yes", "no"):
        reason_codes.append("candidate_selection_no_selected_side")
    if source_row.suggested_notional <= ZERO:
        reason_codes.append("candidate_selection_nonpositive_suggested_notional")
    if source_row.net_edge_per_share is None:
        reason_codes.append("candidate_selection_missing_net_edge")
    elif source_row.net_edge_per_share < config.min_net_edge_per_share:
        reason_codes.append("candidate_selection_net_edge_below_threshold")
    if source_row.research_priority_score < config.min_research_priority_score:
        reason_codes.append("candidate_selection_research_priority_below_threshold")
    return tuple(reason_codes)


def _selection_row_from_source_row(
    *,
    row_number: int,
    source_number: int,
    source_report: PaperStrategyCandidateResearchQueueReport,
    source_row: PaperStrategyCandidateResearchQueueRow,
    selected: bool,
    reason_codes: tuple[str, ...],
) -> PaperAutonomousCandidateSelectionRow:
    return PaperAutonomousCandidateSelectionRow(
        row_number=row_number,
        source_number=source_number,
        source_generated_at=source_report.generated_at,
        source_config_version=source_report.config_version,
        upstream_source_config_version=source_report.source_config_version,
        source_action_status=source_report.action_status,
        source_recommended_next_step=source_report.recommended_next_step,
        source_research_status=source_report.research_status,
        research_rank=source_row.research_rank,
        queue_rank=source_row.queue_rank,
        market_slug=source_row.market_slug,
        question=source_row.question,
        selected_side=source_row.selected_side,
        scoring_side=source_row.scoring_side,
        source_action=source_row.source_action,
        source_decision=source_row.decision,
        queue_status=source_row.queue_status,
        research_status=source_row.research_status,
        research_bucket=source_row.research_bucket,
        assessment_status=source_row.assessment_status,
        source_status=source_row.source_status,
        readiness_status=source_row.readiness_status,
        recommendation_score=source_row.recommendation_score,
        readiness_score=source_row.readiness_score,
        screening_score=source_row.screening_score,
        net_edge_per_share=source_row.net_edge_per_share,
        total_cost_per_share=source_row.total_cost_per_share,
        confidence=source_row.confidence,
        spread=source_row.spread,
        resolution_risk=source_row.resolution_risk,
        suggested_notional=source_row.suggested_notional,
        source_selected_position_notional=source_row.selected_position_notional,
        primary_reason_code=source_row.primary_reason_code,
        research_priority_score=source_row.research_priority_score,
        evidence_gap_codes=source_row.evidence_gap_codes,
        source_reason_codes=source_row.reason_codes,
        explanation=source_row.explanation,
        selection_status="selected" if selected else "not_selected",
        selected_notional=source_row.suggested_notional if selected else ZERO.quantize(QUANTUM),
        reason_codes=reason_codes,
    )


def _source_summary(
    *,
    source_number: int,
    source_report: PaperStrategyCandidateResearchQueueReport,
    selected_candidate_count: int,
) -> PaperAutonomousCandidateSelectionSourceSummary:
    return PaperAutonomousCandidateSelectionSourceSummary(
        source_number=source_number,
        generated_at=source_report.generated_at,
        config_version=source_report.config_version,
        upstream_source_config_version=source_report.source_config_version,
        action_status=source_report.action_status,
        research_status=source_report.research_status,
        recommended_next_step=source_report.recommended_next_step,
        candidate_count=source_report.candidate_count,
        research_ready_count=source_report.research_ready_count,
        selected_candidate_count=selected_candidate_count,
        source_warning=_source_warning(source_report),
    )


def _source_warning(source_report: PaperStrategyCandidateResearchQueueReport) -> bool:
    return (
        source_report.action_status != "research_ready"
        or source_report.research_status != "ready"
        or source_report.watch_count > 0
        or source_report.blocked_count > 0
    )


def _selection_status(
    *,
    selected_candidate_count: int,
    source_warning_count: int,
    duplicate_suppressed_count: int,
    max_selected_candidate_count_suppressed_count: int,
    decision_matrix_suppressed_count: int,
) -> str:
    if selected_candidate_count == 0:
        return "blocked"
    if (
        source_warning_count > 0
        or duplicate_suppressed_count > 0
        or max_selected_candidate_count_suppressed_count > 0
        or decision_matrix_suppressed_count > 0
    ):
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    selected_candidate_count: int,
    source_warning_count: int,
    duplicate_suppressed_count: int,
    max_selected_candidate_count_suppressed_count: int,
    decision_matrix_suppressed_count: int,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if decision_matrix_suppressed_count > 0:
        reason_codes.append(DECISION_MATRIX_SUPPRESSED_REASON_CODE)
    if selected_candidate_count == 0:
        reason_codes.append(NO_SELECTED_REASON_CODE)
        return tuple(sorted(reason_codes))
    if duplicate_suppressed_count > 0:
        reason_codes.append(DUPLICATE_REASON_CODE)
    if max_selected_candidate_count_suppressed_count > 0:
        reason_codes.append(MAX_SELECTED_REASON_CODE)
    if source_warning_count > 0:
        reason_codes.append(SOURCE_WARNING_REASON_CODE)
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperAutonomousCandidateSelectionReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperAutonomousCandidateSelectionReasonCodeCount(reason_code, report_count)
        for reason_code, report_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _rows_with_reason(
    rows: tuple[PaperAutonomousCandidateSelectionRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _decision_matrix_rows_by_slug(
    decision_matrix_report: object | None,
    source_reports: tuple[PaperStrategyCandidateResearchQueueReport, ...],
) -> dict[str, object] | None:
    if decision_matrix_report is None:
        return None
    try:
        decision_rows = getattr(decision_matrix_report, "decision_rows")
    except AttributeError:
        raise ValueError(
            "decision_matrix_report must be exactly "
            "PaperStrategyCandidateDecisionMatrixReport",
        ) from None
    if type(decision_rows) is not tuple:
        raise ValueError(
            "decision_matrix_report must be exactly "
            "PaperStrategyCandidateDecisionMatrixReport",
        )
    _require_hard_flags("decision_matrix_report", decision_matrix_report)
    source_market_slugs = _source_market_slugs(source_reports)
    matrix_rows_by_slug: dict[str, object] = {}
    for row in decision_rows:
        if (
            type(getattr(row, "market_slug", None)) is not str
            or type(getattr(row, "decision_status", None)) is not str
            or type(getattr(row, "reason_codes", None)) is not tuple
            or any(
                type(reason_code) is not str
                for reason_code in getattr(row, "reason_codes", ())
            )
        ):
            raise ValueError(
                "decision_matrix_report rows must be exact "
                "PaperStrategyCandidateDecisionRow values",
            )
        _require_hard_flags("decision_matrix_report row", row)
        if row.market_slug in matrix_rows_by_slug:
            raise ValueError("decision_matrix_report must not duplicate market_slug")
        matrix_rows_by_slug[row.market_slug] = row
    missing_market_slugs = tuple(
        market_slug
        for market_slug in source_market_slugs
        if market_slug not in matrix_rows_by_slug
    )
    if missing_market_slugs:
        raise ValueError("decision_matrix_report missing market_slug coverage")
    extra_market_slugs = tuple(
        market_slug
        for market_slug in matrix_rows_by_slug
        if market_slug not in source_market_slugs
    )
    if extra_market_slugs:
        raise ValueError("decision_matrix_report has extra market_slug coverage")
    return matrix_rows_by_slug


def _source_market_slugs(
    source_reports: tuple[PaperStrategyCandidateResearchQueueReport, ...],
) -> tuple[str, ...]:
    market_slugs: set[str] = set()
    for source_report in source_reports:
        if type(source_report) is not PaperStrategyCandidateResearchQueueReport:
            raise ValueError(
                "source_reports must contain exact "
                "PaperStrategyCandidateResearchQueueReport values",
            )
        for source_row in source_report.rows:
            if type(source_row) is not PaperStrategyCandidateResearchQueueRow:
                raise ValueError(
                    "source_report rows must contain exact "
                    "PaperStrategyCandidateResearchQueueRow values",
                )
            market_slugs.add(source_row.market_slug)
    return tuple(sorted(market_slugs))


def _total_selected_notional(
    rows: tuple[PaperAutonomousCandidateSelectionRow, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_selected_notional",
        sum((row.selected_notional for row in rows), ZERO),
    )


def _total_suggested_notional(
    rows: tuple[PaperAutonomousCandidateSelectionRow, ...],
) -> Decimal:
    return _quantize_nonnegative_decimal(
        "total_suggested_notional",
        sum((row.suggested_notional for row in rows), ZERO),
    )


def _validate_source_rows(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> None:
    for row in rows:
        if type(row) is not PaperStrategyCandidateResearchQueueRow:
            raise ValueError(
                "source rows must contain exact "
                "PaperStrategyCandidateResearchQueueRow values",
            )
        _require_hard_flags("source_row", row)


def _normalize_source_config_versions(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    for item in value:
        _require_canonical_string("source_config_versions", item)
    return value


def _normalize_source_summaries(
    value: object,
) -> tuple[PaperAutonomousCandidateSelectionSourceSummary, ...]:
    if type(value) is not tuple:
        raise ValueError("source_summaries must be a tuple")
    for item in value:
        if type(item) is not PaperAutonomousCandidateSelectionSourceSummary:
            raise ValueError(
                "source_summaries must contain exact "
                "PaperAutonomousCandidateSelectionSourceSummary values",
            )
        _require_hard_flags("source summary", item)
    return value


def _normalize_rows(
    value: object,
) -> tuple[PaperAutonomousCandidateSelectionRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not PaperAutonomousCandidateSelectionRow:
            raise ValueError(
                "rows must contain exact PaperAutonomousCandidateSelectionRow values",
            )
        _require_hard_flags("selection row", item)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperAutonomousCandidateSelectionReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not PaperAutonomousCandidateSelectionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exact "
                "PaperAutonomousCandidateSelectionReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _validate_row_consistency(row: PaperAutonomousCandidateSelectionRow) -> None:
    if row.selection_status == "selected":
        if row.selected_notional != row.suggested_notional:
            raise ValueError("selected rows must use suggested_notional")
        if row.suggested_notional <= ZERO:
            raise ValueError("selected rows must have positive suggested_notional")
    elif row.selected_notional != ZERO.quantize(QUANTUM):
        raise ValueError("non-selected rows must have zero selected_notional")
    if not row.reason_codes:
        raise ValueError("selection rows must include reason_codes")


def _validate_report_consistency(
    report: PaperAutonomousCandidateSelectionReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.selection_status]:
        raise ValueError("recommended_next_step must match selection_status")
    if report.source_report_count != len(report.source_summaries):
        raise ValueError("source_report_count must match source_summaries")
    if report.source_report_count != len(report.source_config_versions):
        raise ValueError("source_report_count must match source_config_versions")
    if report.source_config_versions != tuple(
        item.config_version for item in report.source_summaries
    ):
        raise ValueError("source_config_versions must match source_summaries")
    if report.candidate_count != len(report.rows):
        raise ValueError("candidate_count must match rows")
    selected_candidate_count = sum(
        1 for row in report.rows if row.selection_status == "selected"
    )
    if report.selected_candidate_count != selected_candidate_count:
        raise ValueError("selected_candidate_count must match rows")
    if report.not_selected_candidate_count != (
        report.candidate_count - report.selected_candidate_count
    ):
        raise ValueError("not_selected_candidate_count must match rows")
    if report.duplicate_suppressed_count != _rows_with_reason(
        report.rows,
        ROW_DUPLICATE_REASON_CODE,
    ):
        raise ValueError("duplicate_suppressed_count must match rows")
    if report.max_selected_candidate_count_suppressed_count != _rows_with_reason(
        report.rows,
        ROW_MAX_SELECTED_REASON_CODE,
    ):
        raise ValueError(
            "max_selected_candidate_count_suppressed_count must match rows",
        )
    if report.source_warning_count != sum(
        1 for item in report.source_summaries if item.source_warning
    ):
        raise ValueError("source_warning_count must match source_summaries")
    if report.total_selected_notional != _total_selected_notional(report.rows):
        raise ValueError("total_selected_notional must match rows")
    if report.total_suggested_notional != _total_suggested_notional(report.rows):
        raise ValueError("total_suggested_notional must match rows")
    decision_matrix_suppressed_count = _rows_with_reason(
        report.rows,
        ROW_DECISION_MATRIX_SUPPRESSED_REASON_CODE,
    )
    expected_status = _selection_status(
        selected_candidate_count=report.selected_candidate_count,
        source_warning_count=report.source_warning_count,
        duplicate_suppressed_count=report.duplicate_suppressed_count,
        max_selected_candidate_count_suppressed_count=(
            report.max_selected_candidate_count_suppressed_count
        ),
        decision_matrix_suppressed_count=decision_matrix_suppressed_count,
    )
    if report.selection_status != expected_status:
        raise ValueError("selection_status must match diagnostics")
    expected_reason_codes = _report_reason_codes(
        selected_candidate_count=report.selected_candidate_count,
        source_warning_count=report.source_warning_count,
        duplicate_suppressed_count=report.duplicate_suppressed_count,
        max_selected_candidate_count_suppressed_count=(
            report.max_selected_candidate_count_suppressed_count
        ),
        decision_matrix_suppressed_count=decision_matrix_suppressed_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match diagnostics")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _as_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=UTC,
            fold=value.fold,
        )
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


def _require_selection_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SELECTION_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_row_selection_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ROW_SELECTION_STATUSES:
        raise ValueError(f"{field_name} must be selected or not_selected")


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_STATUSES:
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
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "DEFAULT_PAPER_AUTONOMOUS_CANDIDATE_SELECTION_CONFIG_VERSION",
    "PaperAutonomousCandidateSelectionConfig",
    "PaperAutonomousCandidateSelectionReasonCodeCount",
    "PaperAutonomousCandidateSelectionReport",
    "PaperAutonomousCandidateSelectionRow",
    "PaperAutonomousCandidateSelectionSourceSummary",
    "build_paper_autonomous_candidate_selection_report",
)
