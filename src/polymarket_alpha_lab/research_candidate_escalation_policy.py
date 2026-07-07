"""Pure report-only escalation policy for candidate research events.

Callers supply typed candidate observations. This module returns deterministic,
sanitized report rows for ordinary observation, team review, expert review, and
research pause handling. It performs no network, trading, or persistence work.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchCandidateEscalationConfig",
    "ResearchCandidateEscalationReasonCodeCount",
    "ResearchCandidateEscalationReport",
    "ResearchCandidateEscalationRow",
    "ResearchCandidateObservation",
    "build_research_candidate_escalation_report",
    "research_candidate_escalation_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-candidate-escalation-policy-v0"

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)

ORDINARY_OBSERVATION_STAGE = "ordinary_observation"
TEAM_REVIEW_STAGE = "team_review"
EXPERT_REVIEW_STAGE = "expert_review"
PAUSE_RESEARCH_STAGE = "pause_research"
REVIEW_STAGES = (
    ORDINARY_OBSERVATION_STAGE,
    TEAM_REVIEW_STAGE,
    EXPERT_REVIEW_STAGE,
    PAUSE_RESEARCH_STAGE,
)

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")

NO_CANDIDATE_EVENTS_REASON_CODE = "no_candidate_events"
PASS_REASON_CODE = "candidate_escalation_pass"
WATCH_REASON_CODE = "candidate_escalation_watch"
BLOCK_REASON_CODE = "candidate_escalation_block"

COLLECT_OBSERVATIONS_STEP = "collect_candidate_observations"
CONTINUE_OBSERVATION_STEP = "continue_standard_observation"
CONTINUE_WATCH_STEP = "continue_candidate_observation"
TEAM_REVIEW_STEP = "route_to_team_review"
EXPERT_REVIEW_STEP = "route_to_expert_review"
PAUSE_RESEARCH_STEP = "pause_research_until_resolved"

_SENSITIVE_PUBLIC_TERMS = (
    "raw",
    "market",
    "source",
    "url",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "buy",
    "sell",
    "position",
    "recommend",
)


@dataclass(frozen=True)
class ResearchCandidateEscalationConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_min_evidence_support_score: Decimal = Decimal("0.750000")
    pass_min_quality_support_score: Decimal = Decimal("0.700000")
    continuation_min_evidence_support_score: Decimal = Decimal("0.300000")
    continuation_min_quality_support_score: Decimal = Decimal("0.300000")
    team_review_conflict_signal_score: Decimal = Decimal("0.250000")
    expert_review_conflict_signal_score: Decimal = Decimal("0.550000")
    watch_sensitivity_signal_score: Decimal = Decimal("0.300000")
    block_sensitivity_signal_score: Decimal = Decimal("0.650000")
    max_pass_unresolved_issue_count: Decimal = Decimal("0")
    max_watch_unresolved_issue_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEscalationConfig:
            raise TypeError("ResearchCandidateEscalationConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateEscalationConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_evidence_support_score",
            "pass_min_quality_support_score",
            "continuation_min_evidence_support_score",
            "continuation_min_quality_support_score",
            "team_review_conflict_signal_score",
            "expert_review_conflict_signal_score",
            "watch_sensitivity_signal_score",
            "block_sensitivity_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_unresolved_issue_count",
            "max_watch_unresolved_issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_min_evidence_support_score
            < self.continuation_min_evidence_support_score
        ):
            raise ValueError(
                "pass_min_evidence_support_score must be at least "
                "continuation_min_evidence_support_score",
            )
        if self.pass_min_quality_support_score < self.continuation_min_quality_support_score:
            raise ValueError(
                "pass_min_quality_support_score must be at least "
                "continuation_min_quality_support_score",
            )
        if self.expert_review_conflict_signal_score < self.team_review_conflict_signal_score:
            raise ValueError(
                "expert_review_conflict_signal_score must be at least "
                "team_review_conflict_signal_score",
            )
        if self.block_sensitivity_signal_score < self.watch_sensitivity_signal_score:
            raise ValueError(
                "block_sensitivity_signal_score must be at least "
                "watch_sensitivity_signal_score",
            )
        if self.max_watch_unresolved_issue_count < self.max_pass_unresolved_issue_count:
            raise ValueError(
                "max_watch_unresolved_issue_count must be at least "
                "max_pass_unresolved_issue_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateObservation:
    raw_candidate_id: str
    raw_market_ref: str
    raw_source_ref: str | None
    observed_at: datetime
    review_stage: str
    evidence_support_score: Decimal
    quality_support_score: Decimal
    conflict_signal_score: Decimal
    sensitivity_signal_score: Decimal
    unresolved_issue_count: Decimal
    team_review_count: Decimal
    expert_review_count: Decimal
    pause_requested: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateObservation:
            raise TypeError("ResearchCandidateObservation does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateObservation, "observation")
        for field_name in ("raw_candidate_id", "raw_market_ref"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "raw_source_ref",
            _require_optional_canonical_string("raw_source_ref", self.raw_source_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_enum("review_stage", self.review_stage, REVIEW_STAGES)
        for field_name in (
            "evidence_support_score",
            "quality_support_score",
            "conflict_signal_score",
            "sensitivity_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_issue_count",
            "team_review_count",
            "expert_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.pause_requested) is not bool:
            raise ValueError("pause_requested must be a bool")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchCandidateEscalationRow:
    redacted_candidate_ref: str
    observed_at: datetime
    status: str
    escalation_stage: str
    evidence_support_score: Decimal
    quality_support_score: Decimal
    conflict_signal_score: Decimal
    sensitivity_signal_score: Decimal
    unresolved_issue_count: Decimal
    team_review_count: Decimal
    expert_review_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEscalationRow:
            raise TypeError("ResearchCandidateEscalationRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateEscalationRow, "row")
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_enum("status", self.status, STATUSES)
        _require_enum("escalation_stage", self.escalation_stage, REVIEW_STAGES)
        for field_name in (
            "evidence_support_score",
            "quality_support_score",
            "conflict_signal_score",
            "sensitivity_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unresolved_issue_count",
            "team_review_count",
            "expert_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchCandidateEscalationReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEscalationReasonCodeCount:
            raise TypeError(
                "ResearchCandidateEscalationReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCandidateEscalationReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchCandidateEscalationReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    next_review_step: str
    rows: tuple[ResearchCandidateEscalationRow, ...]
    reason_code_counts: tuple[ResearchCandidateEscalationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateEscalationReport:
            raise TypeError("ResearchCandidateEscalationReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCandidateEscalationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_enum("status", self.status, STATUSES)
        _require_canonical_string("next_review_step", self.next_review_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_candidate_escalation_report(
    observations: Iterable[object],
    *,
    config: ResearchCandidateEscalationConfig,
    generated_at: datetime,
) -> ResearchCandidateEscalationReport:
    if type(config) is not ResearchCandidateEscalationConfig:
        raise ValueError("config must be a ResearchCandidateEscalationConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for observation in normalized:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
    _require_unique_raw_candidates(normalized)

    ordered = tuple(
        sorted(
            normalized,
            key=lambda value: (
                value.raw_candidate_id,
                value.raw_market_ref,
                value.raw_source_ref or "",
                value.observed_at.isoformat(),
            ),
        ),
    )
    rows = tuple(
        _row_from_observation(
            observation,
            redacted_candidate_ref=f"candidate-{index:03d}",
            config=config,
        )
        for index, observation in enumerate(ordered, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    status = _summary_status(rows)
    return ResearchCandidateEscalationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        status=status,
        next_review_step=_next_review_step(rows, status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def research_candidate_escalation_report_payload(
    report: ResearchCandidateEscalationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCandidateEscalationReport:
        raise ValueError("report must be a ResearchCandidateEscalationReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _row_from_observation(
    observation: ResearchCandidateObservation,
    *,
    redacted_candidate_ref: str,
    config: ResearchCandidateEscalationConfig,
) -> ResearchCandidateEscalationRow:
    status, escalation_stage = _status_and_stage(observation, config)
    return ResearchCandidateEscalationRow(
        redacted_candidate_ref=redacted_candidate_ref,
        observed_at=observation.observed_at,
        status=status,
        escalation_stage=escalation_stage,
        evidence_support_score=observation.evidence_support_score,
        quality_support_score=observation.quality_support_score,
        conflict_signal_score=observation.conflict_signal_score,
        sensitivity_signal_score=observation.sensitivity_signal_score,
        unresolved_issue_count=observation.unresolved_issue_count,
        team_review_count=observation.team_review_count,
        expert_review_count=observation.expert_review_count,
        reason_codes=_row_reason_codes(
            observation,
            status=status,
            escalation_stage=escalation_stage,
            config=config,
        ),
    )


def _status_and_stage(
    observation: ResearchCandidateObservation,
    config: ResearchCandidateEscalationConfig,
) -> tuple[str, str]:
    if (
        observation.pause_requested
        or observation.review_stage == PAUSE_RESEARCH_STAGE
        or observation.sensitivity_signal_score >= config.block_sensitivity_signal_score
        or observation.evidence_support_score
        < config.continuation_min_evidence_support_score
        or observation.quality_support_score < config.continuation_min_quality_support_score
        or observation.unresolved_issue_count > config.max_watch_unresolved_issue_count
    ):
        return BLOCK_STATUS, PAUSE_RESEARCH_STAGE
    if (
        observation.review_stage == EXPERT_REVIEW_STAGE
        or observation.expert_review_count > ZERO
        or observation.conflict_signal_score >= config.expert_review_conflict_signal_score
    ):
        return WATCH_STATUS, EXPERT_REVIEW_STAGE
    if (
        observation.review_stage == TEAM_REVIEW_STAGE
        or observation.team_review_count > ZERO
        or observation.conflict_signal_score >= config.team_review_conflict_signal_score
        or observation.sensitivity_signal_score >= config.watch_sensitivity_signal_score
        or observation.evidence_support_score < config.pass_min_evidence_support_score
        or observation.quality_support_score < config.pass_min_quality_support_score
        or observation.unresolved_issue_count > config.max_pass_unresolved_issue_count
    ):
        return WATCH_STATUS, TEAM_REVIEW_STAGE
    return PASS_STATUS, ORDINARY_OBSERVATION_STAGE


def _row_reason_codes(
    observation: ResearchCandidateObservation,
    *,
    status: str,
    escalation_stage: str,
    config: ResearchCandidateEscalationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == PASS_STATUS:
        reason_codes.extend((PASS_REASON_CODE, "routine_observation_clear"))
        return tuple(reason_codes)
    if status == WATCH_STATUS:
        reason_codes.append(WATCH_REASON_CODE)
        if escalation_stage == EXPERT_REVIEW_STAGE:
            reason_codes.append("expert_review_required")
        else:
            reason_codes.append("team_review_required")
        if observation.evidence_support_score < config.pass_min_evidence_support_score:
            reason_codes.append("evidence_support_below_pass")
        if observation.quality_support_score < config.pass_min_quality_support_score:
            reason_codes.append("quality_support_below_pass")
        if observation.unresolved_issue_count > config.max_pass_unresolved_issue_count:
            reason_codes.append("open_review_issue")
        if observation.conflict_signal_score >= config.expert_review_conflict_signal_score:
            reason_codes.append("material_conflict_signal")
        elif observation.conflict_signal_score > ZERO:
            reason_codes.append("conflict_signal_present")
        if observation.sensitivity_signal_score >= config.watch_sensitivity_signal_score:
            reason_codes.append("sensitive_signal_present")
        return _dedupe(reason_codes)

    reason_codes.extend((BLOCK_REASON_CODE, "research_paused"))
    if observation.pause_requested:
        reason_codes.append("research_pause_requested")
    if observation.review_stage == PAUSE_RESEARCH_STAGE:
        reason_codes.append("research_pause_stage_observed")
    if observation.evidence_support_score < config.continuation_min_evidence_support_score:
        reason_codes.append("evidence_support_too_low")
    if observation.quality_support_score < config.continuation_min_quality_support_score:
        reason_codes.append("quality_support_too_low")
    if observation.unresolved_issue_count > config.max_watch_unresolved_issue_count:
        reason_codes.append("unresolved_issues_exceed_limit")
    if observation.conflict_signal_score >= config.expert_review_conflict_signal_score:
        reason_codes.append("material_conflict_signal")
    if observation.sensitivity_signal_score >= config.block_sensitivity_signal_score:
        reason_codes.append("material_sensitive_signal")
    return _dedupe(reason_codes)


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchCandidateObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchCandidateObservation:
            raise ValueError("observations must contain ResearchCandidateObservation values")
        _require_hard_flags("observation", value)
    return values


def _require_unique_raw_candidates(
    observations: tuple[ResearchCandidateObservation, ...],
) -> None:
    seen: set[str] = set()
    for observation in observations:
        if observation.raw_candidate_id in seen:
            raise ValueError("raw_candidate_id values must be unique")
        seen.add(observation.raw_candidate_id)


def _report_reason_codes(
    rows: tuple[ResearchCandidateEscalationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATE_EVENTS_REASON_CODE,)
    values: list[str] = []
    for row in rows:
        values.extend(row.reason_codes)
    return _dedupe(values)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchCandidateEscalationRow, ...],
) -> tuple[ResearchCandidateEscalationReasonCodeCount, ...]:
    if not rows and reason_codes == (NO_CANDIDATE_EVENTS_REASON_CODE,):
        return (
            ResearchCandidateEscalationReasonCodeCount(
                reason_code=NO_CANDIDATE_EVENTS_REASON_CODE,
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchCandidateEscalationReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in sorted(reason_codes)
        if counts[reason_code] > 0
    )


def _summary_status(rows: tuple[ResearchCandidateEscalationRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _next_review_step(
    rows: tuple[ResearchCandidateEscalationRow, ...],
    status: str,
) -> str:
    if not rows:
        return COLLECT_OBSERVATIONS_STEP
    if status == BLOCK_STATUS:
        return PAUSE_RESEARCH_STEP
    if any(row.escalation_stage == EXPERT_REVIEW_STAGE for row in rows):
        return EXPERT_REVIEW_STEP
    if any(row.escalation_stage == TEAM_REVIEW_STAGE for row in rows):
        return TEAM_REVIEW_STEP
    if status == WATCH_STATUS:
        return CONTINUE_WATCH_STEP
    return CONTINUE_OBSERVATION_STEP


def _status_count(
    rows: tuple[ResearchCandidateEscalationRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _normalize_rows(value: object) -> tuple[ResearchCandidateEscalationRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    previous_ref: str | None = None
    for row in rows:
        if type(row) is not ResearchCandidateEscalationRow:
            raise ValueError("rows must contain ResearchCandidateEscalationRow values")
        _require_hard_flags("row", row)
        if previous_ref is not None and row.redacted_candidate_ref <= previous_ref:
            raise ValueError("rows must be sorted by redacted_candidate_ref")
        previous_ref = row.redacted_candidate_ref
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchCandidateEscalationReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    previous_reason_code: str | None = None
    for count in counts:
        if type(count) is not ResearchCandidateEscalationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCandidateEscalationReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        if previous_reason_code is not None and count.reason_code <= previous_reason_code:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        previous_reason_code = count.reason_code
    return counts


def _validate_row_consistency(row: ResearchCandidateEscalationRow) -> None:
    if f"candidate_escalation_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS:
        if row.escalation_stage != ORDINARY_OBSERVATION_STAGE:
            raise ValueError("pass rows must stay in ordinary observation")
        if row.reason_codes != (PASS_REASON_CODE, "routine_observation_clear"):
            raise ValueError("pass rows must use clear routine reasons")
    if row.status == WATCH_STATUS and row.escalation_stage == PAUSE_RESEARCH_STAGE:
        raise ValueError("watch rows must not use pause_research")
    if row.status == BLOCK_STATUS and row.escalation_stage != PAUSE_RESEARCH_STAGE:
        raise ValueError("block rows must use pause_research")
    if (
        row.escalation_stage == TEAM_REVIEW_STAGE
        and "team_review_required" not in row.reason_codes
    ):
        raise ValueError("team_review rows must include team_review_required")
    if (
        row.escalation_stage == EXPERT_REVIEW_STAGE
        and "expert_review_required" not in row.reason_codes
    ):
        raise ValueError("expert_review rows must include expert_review_required")
    if row.escalation_stage == PAUSE_RESEARCH_STAGE and "research_paused" not in row.reason_codes:
        raise ValueError("pause_research rows must include research_paused")


def _validate_report_consistency(report: ResearchCandidateEscalationReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("rows must match row_count")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match row_count")
    expected_status = _summary_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.reason_codes, report.rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_next_step = _next_review_step(report.rows, report.status)
    if report.next_review_step != expected_next_step:
        raise ValueError("next_review_step must match rows")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _validate_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_public_string(key)
            _validate_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_payload(item)
        return
    if type(value) is str:
        _validate_public_string(value)


def _validate_public_string(value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _SENSITIVE_PUBLIC_TERMS):
        raise ValueError("public payload contains sensitive string")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized.quantize(RATIO_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_optional_canonical_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        if value not in normalized:
            normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if not all(character.isalnum() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain only lowercase letters, digits, or _")


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        _require_reason_code("reason_codes", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
