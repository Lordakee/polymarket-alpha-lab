"""Pure report-only research journal summary reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "research-journal-summary-v1"

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
TWO_RATIO = Decimal("2.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SUMMARY_STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "journal_summary_passed",
    "evidence_change_missing",
    "evidence_confidence_weakened",
    "evidence_change_score_low",
    "team_view_alignment_weakened",
    "team_view_score_low",
    "unresolved_conflicts_present",
    "refresh_records_missing",
    "stale_refresh_records_present",
    "retrospective_todos_open",
    "journal_summary_watch_score",
    "journal_summary_block_score",
)
PUBLIC_PAYLOAD_FORBIDDEN_KEY_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "source",
    "url",
    "uri",
    "dsn",
    "table",
    "token",
    "text",
)


@dataclass(frozen=True)
class ResearchCandidateResearchJournalSummaryConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_evidence_change_score: Decimal = Decimal("0.500000")
    minimum_team_view_score: Decimal = Decimal("0.500000")
    minimum_refresh_record_count: Decimal = Decimal("1")
    maximum_unresolved_conflict_count: Decimal = Decimal("0")
    maximum_stale_refresh_count: Decimal = Decimal("0")
    maximum_open_retro_todo_count: Decimal = Decimal("1")
    pass_score_threshold: Decimal = Decimal("0.800000")
    watch_score_threshold: Decimal = Decimal("0.550000")
    evidence_change_weight: Decimal = Decimal("0.300000")
    team_view_weight: Decimal = Decimal("0.200000")
    conflict_handling_weight: Decimal = Decimal("0.200000")
    refresh_record_weight: Decimal = Decimal("0.150000")
    retrospective_todo_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchCandidateResearchJournalSummaryConfig,
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "minimum_evidence_change_score",
            "minimum_team_view_score",
            "pass_score_threshold",
            "watch_score_threshold",
            "evidence_change_weight",
            "team_view_weight",
            "conflict_handling_weight",
            "refresh_record_weight",
            "retrospective_todo_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_refresh_record_count",
            "maximum_unresolved_conflict_count",
            "maximum_stale_refresh_count",
            "maximum_open_retro_todo_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.watch_score_threshold > self.pass_score_threshold:
            raise ValueError("watch_score_threshold must be <= pass_score_threshold")
        _validate_score_weights(self)
        reject_unsafe_surface_fields("research journal summary config", self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateResearchJournalSummaryInput:
    research_ref: str
    evidence_added_count: Decimal
    evidence_revised_count: Decimal
    evidence_retired_count: Decimal
    evidence_confidence_delta: Decimal
    team_view_change_count: Decimal
    team_alignment_delta: Decimal
    unresolved_conflict_count: Decimal
    resolved_conflict_count: Decimal
    refresh_record_count: Decimal
    stale_refresh_count: Decimal
    open_retro_todo_count: Decimal
    completed_retro_todo_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "journal",
            self,
            ResearchCandidateResearchJournalSummaryInput,
        )
        _require_public_string("research_ref", self.research_ref)
        for field_name in (
            "evidence_added_count",
            "evidence_revised_count",
            "evidence_retired_count",
            "team_view_change_count",
            "unresolved_conflict_count",
            "resolved_conflict_count",
            "refresh_record_count",
            "stale_refresh_count",
            "open_retro_todo_count",
            "completed_retro_todo_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_confidence_delta", "team_alignment_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        if self.stale_refresh_count > self.refresh_record_count:
            raise ValueError("stale_refresh_count must not exceed refresh_record_count")
        reject_unsafe_surface_fields("research journal summary input", self)
        require_paper_only_flags("journal", self)


@dataclass(frozen=True)
class ResearchCandidateResearchJournalSummaryResult:
    config_version: str
    research_ref: str
    evidence_added_count: Decimal
    evidence_revised_count: Decimal
    evidence_retired_count: Decimal
    evidence_confidence_delta: Decimal
    team_view_change_count: Decimal
    team_alignment_delta: Decimal
    unresolved_conflict_count: Decimal
    resolved_conflict_count: Decimal
    refresh_record_count: Decimal
    stale_refresh_count: Decimal
    open_retro_todo_count: Decimal
    completed_retro_todo_count: Decimal
    evidence_change_score: Decimal
    team_view_score: Decimal
    conflict_handling_score: Decimal
    refresh_record_score: Decimal
    retrospective_todo_score: Decimal
    journal_summary_score: Decimal
    summary_status: str
    follow_up_required: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "result",
            self,
            ResearchCandidateResearchJournalSummaryResult,
        )
        _require_public_string("config_version", self.config_version)
        _require_public_string("research_ref", self.research_ref)
        for field_name in (
            "evidence_added_count",
            "evidence_revised_count",
            "evidence_retired_count",
            "team_view_change_count",
            "unresolved_conflict_count",
            "resolved_conflict_count",
            "refresh_record_count",
            "stale_refresh_count",
            "open_retro_todo_count",
            "completed_retro_todo_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_confidence_delta", "team_alignment_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_change_score",
            "team_view_score",
            "conflict_handling_score",
            "refresh_record_score",
            "retrospective_todo_score",
            "journal_summary_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("summary_status", self.summary_status, SUMMARY_STATUSES)
        _require_bool("follow_up_required", self.follow_up_required)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.stale_refresh_count > self.refresh_record_count:
            raise ValueError("stale_refresh_count must not exceed refresh_record_count")
        _validate_result(self)
        reject_unsafe_surface_fields("research journal summary result", self)
        require_paper_only_flags("result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_candidate_research_journal_summary_payload(self)


def summarize_research_candidate_research_journal(
    journal: ResearchCandidateResearchJournalSummaryInput,
    *,
    config: ResearchCandidateResearchJournalSummaryConfig | None = None,
) -> ResearchCandidateResearchJournalSummaryResult:
    if type(journal) is not ResearchCandidateResearchJournalSummaryInput:
        raise ValueError(
            "journal must be a ResearchCandidateResearchJournalSummaryInput",
        )
    reject_unsafe_surface_fields("research journal summary input", journal)
    require_paper_only_flags("journal", journal)

    active_config = config or ResearchCandidateResearchJournalSummaryConfig()
    if type(active_config) is not ResearchCandidateResearchJournalSummaryConfig:
        raise ValueError(
            "config must be a ResearchCandidateResearchJournalSummaryConfig",
        )
    reject_unsafe_surface_fields("research journal summary config", active_config)
    require_paper_only_flags("config", active_config)

    evidence_change_score = _evidence_change_score(journal)
    team_view_score = _team_view_score(journal)
    conflict_handling_score = _conflict_handling_score(journal)
    refresh_record_score = _refresh_record_score(journal)
    retrospective_todo_score = _retrospective_todo_score(journal)
    journal_summary_score = _journal_summary_score(
        config=active_config,
        evidence_change_score=evidence_change_score,
        team_view_score=team_view_score,
        conflict_handling_score=conflict_handling_score,
        refresh_record_score=refresh_record_score,
        retrospective_todo_score=retrospective_todo_score,
    )
    summary_status = _summary_status(
        journal=journal,
        config=active_config,
        evidence_change_score=evidence_change_score,
        team_view_score=team_view_score,
        journal_summary_score=journal_summary_score,
    )
    return ResearchCandidateResearchJournalSummaryResult(
        config_version=active_config.config_version,
        research_ref=journal.research_ref,
        evidence_added_count=journal.evidence_added_count,
        evidence_revised_count=journal.evidence_revised_count,
        evidence_retired_count=journal.evidence_retired_count,
        evidence_confidence_delta=journal.evidence_confidence_delta,
        team_view_change_count=journal.team_view_change_count,
        team_alignment_delta=journal.team_alignment_delta,
        unresolved_conflict_count=journal.unresolved_conflict_count,
        resolved_conflict_count=journal.resolved_conflict_count,
        refresh_record_count=journal.refresh_record_count,
        stale_refresh_count=journal.stale_refresh_count,
        open_retro_todo_count=journal.open_retro_todo_count,
        completed_retro_todo_count=journal.completed_retro_todo_count,
        evidence_change_score=evidence_change_score,
        team_view_score=team_view_score,
        conflict_handling_score=conflict_handling_score,
        refresh_record_score=refresh_record_score,
        retrospective_todo_score=retrospective_todo_score,
        journal_summary_score=journal_summary_score,
        summary_status=summary_status,
        follow_up_required=summary_status != "pass",
        reason_codes=_reason_codes(
            journal=journal,
            config=active_config,
            evidence_change_score=evidence_change_score,
            team_view_score=team_view_score,
            journal_summary_score=journal_summary_score,
        ),
    )


def research_candidate_research_journal_summary_payload(
    result: ResearchCandidateResearchJournalSummaryResult,
) -> dict[str, Any]:
    if type(result) is not ResearchCandidateResearchJournalSummaryResult:
        raise ValueError(
            "result must be a ResearchCandidateResearchJournalSummaryResult",
        )
    reject_unsafe_surface_fields("research journal summary result", result)
    require_paper_only_flags("result", result)
    payload = {
        "config_version": result.config_version,
        "research_ref": result.research_ref,
        "evidence_added_count": _decimal_payload(result.evidence_added_count),
        "evidence_revised_count": _decimal_payload(result.evidence_revised_count),
        "evidence_retired_count": _decimal_payload(result.evidence_retired_count),
        "evidence_confidence_delta": _decimal_payload(
            result.evidence_confidence_delta,
        ),
        "team_view_change_count": _decimal_payload(result.team_view_change_count),
        "team_alignment_delta": _decimal_payload(result.team_alignment_delta),
        "unresolved_conflict_count": _decimal_payload(
            result.unresolved_conflict_count,
        ),
        "resolved_conflict_count": _decimal_payload(result.resolved_conflict_count),
        "refresh_record_count": _decimal_payload(result.refresh_record_count),
        "stale_refresh_count": _decimal_payload(result.stale_refresh_count),
        "open_retro_todo_count": _decimal_payload(result.open_retro_todo_count),
        "completed_retro_todo_count": _decimal_payload(
            result.completed_retro_todo_count,
        ),
        "evidence_change_score": _decimal_payload(result.evidence_change_score),
        "team_view_score": _decimal_payload(result.team_view_score),
        "conflict_handling_score": _decimal_payload(result.conflict_handling_score),
        "refresh_record_score": _decimal_payload(result.refresh_record_score),
        "retrospective_todo_score": _decimal_payload(result.retrospective_todo_score),
        "journal_summary_score": _decimal_payload(result.journal_summary_score),
        "summary_status": result.summary_status,
        "follow_up_required": result.follow_up_required,
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_forbidden_public_payload(payload)
    return payload


def _evidence_change_score(
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
) -> Decimal:
    observed_count = (
        journal.evidence_added_count
        + journal.evidence_revised_count
        + journal.evidence_retired_count
    )
    if observed_count <= ZERO_COUNT:
        return ZERO_RATIO
    constructive_count = journal.evidence_added_count + journal.evidence_revised_count
    with localcontext(DECIMAL_CONTEXT):
        constructive_share = _clamp_ratio(constructive_count / observed_count)
        confidence_component = _signed_ratio_to_quality(
            journal.evidence_confidence_delta,
        )
        return _quantize_ratio(
            "evidence_change_score",
            constructive_share * Decimal("0.600000")
            + confidence_component * Decimal("0.400000"),
        )


def _team_view_score(
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
) -> Decimal:
    return _signed_ratio_to_quality(journal.team_alignment_delta)


def _conflict_handling_score(
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
) -> Decimal:
    if journal.unresolved_conflict_count == ZERO_COUNT:
        return ONE_RATIO
    conflict_count = journal.resolved_conflict_count + journal.unresolved_conflict_count
    if conflict_count == ZERO_COUNT:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(journal.resolved_conflict_count / conflict_count)


def _refresh_record_score(
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
) -> Decimal:
    if journal.refresh_record_count == ZERO_COUNT:
        return ZERO_RATIO
    current_count = journal.refresh_record_count - journal.stale_refresh_count
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(current_count / journal.refresh_record_count)


def _retrospective_todo_score(
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
) -> Decimal:
    todo_count = journal.open_retro_todo_count + journal.completed_retro_todo_count
    if todo_count == ZERO_COUNT:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(journal.completed_retro_todo_count / todo_count)


def _journal_summary_score(
    *,
    config: ResearchCandidateResearchJournalSummaryConfig,
    evidence_change_score: Decimal,
    team_view_score: Decimal,
    conflict_handling_score: Decimal,
    refresh_record_score: Decimal,
    retrospective_todo_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            "journal_summary_score",
            evidence_change_score * config.evidence_change_weight
            + team_view_score * config.team_view_weight
            + conflict_handling_score * config.conflict_handling_weight
            + refresh_record_score * config.refresh_record_weight
            + retrospective_todo_score * config.retrospective_todo_weight,
        )


def _summary_status(
    *,
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
    config: ResearchCandidateResearchJournalSummaryConfig,
    evidence_change_score: Decimal,
    team_view_score: Decimal,
    journal_summary_score: Decimal,
) -> str:
    if (
        journal.unresolved_conflict_count > config.maximum_unresolved_conflict_count
        or journal_summary_score < config.watch_score_threshold
    ):
        return "block"
    if (
        evidence_change_score < config.minimum_evidence_change_score
        or team_view_score < config.minimum_team_view_score
        or journal.refresh_record_count < config.minimum_refresh_record_count
        or journal.stale_refresh_count > config.maximum_stale_refresh_count
        or journal.open_retro_todo_count > config.maximum_open_retro_todo_count
        or journal_summary_score < config.pass_score_threshold
    ):
        return "watch"
    return "pass"


def _reason_codes(
    *,
    journal: ResearchCandidateResearchJournalSummaryInput
    | ResearchCandidateResearchJournalSummaryResult,
    config: ResearchCandidateResearchJournalSummaryConfig,
    evidence_change_score: Decimal,
    team_view_score: Decimal,
    journal_summary_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    evidence_change_count = (
        journal.evidence_added_count
        + journal.evidence_revised_count
        + journal.evidence_retired_count
    )
    if evidence_change_count == ZERO_COUNT:
        codes.append("evidence_change_missing")
    if journal.evidence_confidence_delta < ZERO_RATIO:
        codes.append("evidence_confidence_weakened")
    if evidence_change_score < config.minimum_evidence_change_score:
        codes.append("evidence_change_score_low")
    if journal.team_alignment_delta < ZERO_RATIO:
        codes.append("team_view_alignment_weakened")
    if team_view_score < config.minimum_team_view_score:
        codes.append("team_view_score_low")
    if journal.unresolved_conflict_count > config.maximum_unresolved_conflict_count:
        codes.append("unresolved_conflicts_present")
    if journal.refresh_record_count < config.minimum_refresh_record_count:
        codes.append("refresh_records_missing")
    if journal.stale_refresh_count > config.maximum_stale_refresh_count:
        codes.append("stale_refresh_records_present")
    if journal.open_retro_todo_count > config.maximum_open_retro_todo_count:
        codes.append("retrospective_todos_open")
    if journal_summary_score < config.watch_score_threshold:
        codes.append("journal_summary_block_score")
    elif journal_summary_score < config.pass_score_threshold:
        codes.append("journal_summary_watch_score")
    if not codes:
        codes.append("journal_summary_passed")
    return _normalize_reason_codes(tuple(codes))


def _validate_result(result: ResearchCandidateResearchJournalSummaryResult) -> None:
    config = ResearchCandidateResearchJournalSummaryConfig(
        config_version=result.config_version,
    )
    if result.evidence_change_score != _evidence_change_score(result):
        raise ValueError("evidence_change_score must match journal inputs")
    if result.team_view_score != _team_view_score(result):
        raise ValueError("team_view_score must match journal inputs")
    if result.conflict_handling_score != _conflict_handling_score(result):
        raise ValueError("conflict_handling_score must match journal inputs")
    if result.refresh_record_score != _refresh_record_score(result):
        raise ValueError("refresh_record_score must match journal inputs")
    if result.retrospective_todo_score != _retrospective_todo_score(result):
        raise ValueError("retrospective_todo_score must match journal inputs")
    if result.journal_summary_score != _journal_summary_score(
        config=config,
        evidence_change_score=result.evidence_change_score,
        team_view_score=result.team_view_score,
        conflict_handling_score=result.conflict_handling_score,
        refresh_record_score=result.refresh_record_score,
        retrospective_todo_score=result.retrospective_todo_score,
    ):
        raise ValueError("journal_summary_score must match journal inputs")
    expected_status = _summary_status(
        journal=result,
        config=config,
        evidence_change_score=result.evidence_change_score,
        team_view_score=result.team_view_score,
        journal_summary_score=result.journal_summary_score,
    )
    if result.summary_status != expected_status:
        raise ValueError("summary_status must match journal inputs")
    expected_reason_codes = _reason_codes(
        journal=result,
        config=config,
        evidence_change_score=result.evidence_change_score,
        team_view_score=result.team_view_score,
        journal_summary_score=result.journal_summary_score,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match journal inputs")
    if result.follow_up_required != (result.summary_status != "pass"):
        raise ValueError("follow_up_required must match summary_status")


def _validate_score_weights(
    config: ResearchCandidateResearchJournalSummaryConfig,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total_weight = (
            config.evidence_change_weight
            + config.team_view_weight
            + config.conflict_handling_weight
            + config.refresh_record_weight
            + config.retrospective_todo_weight
        ).quantize(RATIO_QUANTUM)
    if total_weight != ONE_RATIO:
        raise ValueError("score component weights must sum to 1.000000")


def _signed_ratio_to_quality(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((value + ONE_RATIO) / TWO_RATIO)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    return _quantize_ratio("ratio", value)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_signed_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < -ONE_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _quantize_ratio(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(_require_decimal("payload decimal", value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_public_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    lowered = value.lower()
    if "://" in lowered or any(
        fragment in lowered for fragment in PUBLIC_PAYLOAD_FORBIDDEN_KEY_FRAGMENTS
    ):
        raise ValueError(f"{field_name} must not expose restricted public material")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _reject_forbidden_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if any(
                fragment in lowered_key
                for fragment in PUBLIC_PAYLOAD_FORBIDDEN_KEY_FRAGMENTS
            ):
                raise ValueError(f"public payload exposes restricted key: {key}")
            _reject_forbidden_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_forbidden_public_payload(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        if "://" in lowered_value or any(
            fragment in lowered_value
            for fragment in ("raw_", "candidate_", "market_", "dsn", "token")
        ):
            raise ValueError("public payload exposes restricted value")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "PUBLIC_PAYLOAD_FORBIDDEN_KEY_FRAGMENTS",
    "REASON_CODES",
    "SUMMARY_STATUSES",
    "ResearchCandidateResearchJournalSummaryConfig",
    "ResearchCandidateResearchJournalSummaryInput",
    "ResearchCandidateResearchJournalSummaryResult",
    "research_candidate_research_journal_summary_payload",
    "summarize_research_candidate_research_journal",
)
