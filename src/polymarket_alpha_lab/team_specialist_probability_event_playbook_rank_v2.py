"""Phase 1 paper-only rank for probability-event specialist playbooks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_PROBABILITY_EVENT_PLAYBOOK_RANK_V2_CONFIG_VERSION = (
    "team-specialist-probability-event-playbook-rank-v2-phase1"
)

STATUS_VALUES = ("apply", "watch", "skip")
ROW_REASON_CODES = (
    "team_specialist_probability_event_playbook_category_match",
    "team_specialist_probability_event_playbook_category_mismatch",
    "team_specialist_probability_event_playbook_archetype_recurring",
    "team_specialist_probability_event_playbook_archetype_gap",
    "team_specialist_probability_event_playbook_calibration_memory_strong",
    "team_specialist_probability_event_playbook_calibration_memory_weak",
    "team_specialist_probability_event_playbook_source_coverage_complete",
    "team_specialist_probability_event_playbook_source_coverage_gap",
    "team_specialist_probability_event_playbook_recent_error_low",
    "team_specialist_probability_event_playbook_recent_error_high",
    "team_specialist_probability_event_playbook_apply",
    "team_specialist_probability_event_playbook_watch",
    "team_specialist_probability_event_playbook_skip",
)
REPORT_REASON_CODES = (
    "team_specialist_probability_event_playbook_rank_apply_rows",
    "team_specialist_probability_event_playbook_rank_watch_rows",
    "team_specialist_probability_event_playbook_rank_skip_rows",
    "team_specialist_probability_event_playbook_rank_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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

DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
LOW_RECENT_ERROR_FLOOR = Decimal("0.100000")
HIGH_RECENT_ERROR_FLOOR = Decimal("0.500000")


@dataclass(frozen=True)
class TeamSpecialistProbabilityEventPlaybookRankV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_PROBABILITY_EVENT_PLAYBOOK_RANK_V2_CONFIG_VERSION
    )
    category_match_weight: Decimal = Decimal("0.250000")
    archetype_recurrence_weight: Decimal = Decimal("0.200000")
    calibration_memory_weight: Decimal = Decimal("0.250000")
    source_coverage_weight: Decimal = Decimal("0.150000")
    forecast_accuracy_weight: Decimal = Decimal("0.150000")
    max_archetype_recurrence_count: Decimal = Decimal("8")
    apply_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_PROBABILITY_EVENT_PLAYBOOK_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "category_match_weight",
            "archetype_recurrence_weight",
            "calibration_memory_weight",
            "source_coverage_weight",
            "forecast_accuracy_weight",
            "apply_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_archetype_recurrence_count",
            _normalize_positive_count(
                "max_archetype_recurrence_count",
                self.max_archetype_recurrence_count,
            ),
        )
        _require_ratio_total(
            self.category_match_weight,
            self.archetype_recurrence_weight,
            self.calibration_memory_weight,
            self.source_coverage_weight,
            self.forecast_accuracy_weight,
        )
        if self.watch_score_floor > self.apply_score_floor:
            raise ValueError("watch_score_floor must not exceed apply_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistProbabilityEventCandidateV2:
    candidate_id: str
    category_id: str
    event_archetype: str
    required_source_families: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "category_id", "event_archetype"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_public_refs(
                "required_source_families",
                self.required_source_families,
            ),
        )
        _require_hard_flags("event_candidate", self)
        _reject_unsafe_public_payload("event_candidate", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistProbabilityEventPlaybookV2:
    team_id: str
    specialist_id: str
    playbook_id: str
    category_ids: tuple[str, ...]
    event_archetypes: tuple[str, ...]
    archetype_recurrence_count: Decimal
    calibration_memory_score: Decimal
    source_family_ids: tuple[str, ...]
    recent_forecast_error: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "playbook_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "category_ids",
            _normalize_public_refs("category_ids", self.category_ids),
        )
        object.__setattr__(
            self,
            "event_archetypes",
            _normalize_public_refs("event_archetypes", self.event_archetypes),
        )
        object.__setattr__(
            self,
            "archetype_recurrence_count",
            _normalize_count(
                "archetype_recurrence_count",
                self.archetype_recurrence_count,
            ),
        )
        object.__setattr__(
            self,
            "calibration_memory_score",
            _normalize_ratio("calibration_memory_score", self.calibration_memory_score),
        )
        object.__setattr__(
            self,
            "source_family_ids",
            _normalize_public_refs("source_family_ids", self.source_family_ids),
        )
        object.__setattr__(
            self,
            "recent_forecast_error",
            _normalize_ratio("recent_forecast_error", self.recent_forecast_error),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("playbook", self)
        _reject_unsafe_public_payload("playbook", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistProbabilityEventPlaybookRankV2Row:
    rank: Decimal
    candidate_id: str
    team_id: str
    specialist_id: str
    playbook_id: str
    category_match_score: Decimal
    archetype_recurrence_score: Decimal
    calibration_memory_score: Decimal
    source_coverage_score: Decimal
    recent_forecast_error: Decimal
    forecast_accuracy_score: Decimal
    matched_source_family_count: Decimal
    required_source_family_count: Decimal
    matched_source_families: tuple[str, ...]
    playbook_apply_score: Decimal
    playbook_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_count("rank", self.rank))
        for field_name in ("candidate_id", "team_id", "specialist_id", "playbook_id"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "category_match_score",
            "archetype_recurrence_score",
            "calibration_memory_score",
            "source_coverage_score",
            "recent_forecast_error",
            "forecast_accuracy_score",
            "playbook_apply_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("matched_source_family_count", "required_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "matched_source_families",
            _normalize_optional_public_refs(
                "matched_source_families",
                self.matched_source_families,
            ),
        )
        _require_status("playbook_status", self.playbook_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        _validate_row_counts(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistProbabilityEventPlaybookRankV2Report:
    generated_at: datetime
    config_version: str
    candidate_id: str
    category_id: str
    event_archetype: str
    playbook_count: Decimal
    apply_count: Decimal
    watch_count: Decimal
    skip_count: Decimal
    average_playbook_apply_score: Decimal
    top_playbook_apply_score: Decimal
    rank_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistProbabilityEventPlaybookRankV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_PROBABILITY_EVENT_PLAYBOOK_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("candidate_id", "category_id", "event_archetype"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("playbook_count", "apply_count", "watch_count", "skip_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_playbook_apply_score", "top_playbook_apply_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("rank_status", self.rank_status)
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
        _validate_report_counts_status_and_reasons(self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_scores(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_probability_event_playbook_rank_v2_payload(self)


def build_team_specialist_probability_event_playbook_rank_v2_report(
    *,
    event_candidate: TeamSpecialistProbabilityEventCandidateV2,
    playbooks: object,
    generated_at: datetime,
    config: TeamSpecialistProbabilityEventPlaybookRankV2Config | None = None,
) -> TeamSpecialistProbabilityEventPlaybookRankV2Report:
    if type(event_candidate) is not TeamSpecialistProbabilityEventCandidateV2:
        raise ValueError(
            "event_candidate must be TeamSpecialistProbabilityEventCandidateV2",
        )
    _require_hard_flags("event_candidate", event_candidate)
    if config is None:
        config = TeamSpecialistProbabilityEventPlaybookRankV2Config()
    if type(config) is not TeamSpecialistProbabilityEventPlaybookRankV2Config:
        raise ValueError(
            "config must be a TeamSpecialistProbabilityEventPlaybookRankV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_playbooks = _normalize_playbooks(playbooks)
    for playbook in normalized_playbooks:
        if playbook.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")

    rows_without_rank = tuple(
        _row_parts(event_candidate, playbook, config)
        for playbook in normalized_playbooks
    )
    ranked_rows = tuple(
        TeamSpecialistProbabilityEventPlaybookRankV2Row(
            **parts,
            rank=_count(index),
            derived_validation_digest=_digest_public({**parts, "rank": _count(index)}),
        )
        for index, parts in enumerate(
            sorted(rows_without_rank, key=_row_parts_sort_key),
            start=1,
        )
    )
    report_parts = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_id": event_candidate.candidate_id,
        "category_id": event_candidate.category_id,
        "event_archetype": event_candidate.event_archetype,
        "playbook_count": _count(len(ranked_rows)),
        "apply_count": _count(
            sum(1 for row in ranked_rows if row.playbook_status == "apply"),
        ),
        "watch_count": _count(
            sum(1 for row in ranked_rows if row.playbook_status == "watch"),
        ),
        "skip_count": _count(
            sum(1 for row in ranked_rows if row.playbook_status == "skip"),
        ),
        "average_playbook_apply_score": _average_playbook_apply_score(ranked_rows),
        "top_playbook_apply_score": _top_playbook_apply_score(ranked_rows),
        "rank_status": _report_status(ranked_rows),
        "reason_codes": _report_reason_codes(ranked_rows),
        "rows": ranked_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistProbabilityEventPlaybookRankV2Report(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_probability_event_playbook_rank_v2_payload(
    report: TeamSpecialistProbabilityEventPlaybookRankV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistProbabilityEventPlaybookRankV2Report:
        raise ValueError(
            "report must be a TeamSpecialistProbabilityEventPlaybookRankV2Report",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_parts(
    event_candidate: TeamSpecialistProbabilityEventCandidateV2,
    playbook: TeamSpecialistProbabilityEventPlaybookV2,
    config: TeamSpecialistProbabilityEventPlaybookRankV2Config,
) -> dict[str, object]:
    category_match_score = (
        ONE.quantize(RATIO_QUANTUM)
        if event_candidate.category_id in playbook.category_ids
        else ZERO.quantize(RATIO_QUANTUM)
    )
    archetype_recurrence_score = (
        _count_ratio(
            playbook.archetype_recurrence_count,
            config.max_archetype_recurrence_count,
        )
        if event_candidate.event_archetype in playbook.event_archetypes
        else ZERO.quantize(RATIO_QUANTUM)
    )
    matched_source_families = tuple(
        source_family
        for source_family in event_candidate.required_source_families
        if source_family in playbook.source_family_ids
    )
    matched_source_family_count = _count(len(matched_source_families))
    required_source_family_count = _count(len(event_candidate.required_source_families))
    source_coverage_score = _count_ratio(
        matched_source_family_count,
        required_source_family_count,
    )
    forecast_accuracy_score = _clamp_ratio(ONE - playbook.recent_forecast_error)
    playbook_apply_score = _playbook_apply_score(
        category_match_score,
        archetype_recurrence_score,
        playbook.calibration_memory_score,
        source_coverage_score,
        forecast_accuracy_score,
        config,
    )
    playbook_status = _row_status(playbook_apply_score, config)
    return {
        "candidate_id": event_candidate.candidate_id,
        "team_id": playbook.team_id,
        "specialist_id": playbook.specialist_id,
        "playbook_id": playbook.playbook_id,
        "category_match_score": category_match_score,
        "archetype_recurrence_score": archetype_recurrence_score,
        "calibration_memory_score": playbook.calibration_memory_score,
        "source_coverage_score": source_coverage_score,
        "recent_forecast_error": playbook.recent_forecast_error,
        "forecast_accuracy_score": forecast_accuracy_score,
        "matched_source_family_count": matched_source_family_count,
        "required_source_family_count": required_source_family_count,
        "matched_source_families": matched_source_families,
        "playbook_apply_score": playbook_apply_score,
        "playbook_status": playbook_status,
        "reason_codes": _row_reason_codes(
            playbook_status,
            category_match_score,
            archetype_recurrence_score,
            playbook.calibration_memory_score,
            source_coverage_score,
            playbook.recent_forecast_error,
            config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_parts_sort_key(parts: dict[str, object]) -> tuple[Decimal, str, str, str]:
    score = parts["playbook_apply_score"]
    if type(score) is not Decimal:
        raise ValueError("playbook_apply_score must be a Decimal")
    return (
        -score,
        str(parts["team_id"]),
        str(parts["specialist_id"]),
        str(parts["playbook_id"]),
    )


def _row_sort_key(
    row: TeamSpecialistProbabilityEventPlaybookRankV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -row.playbook_apply_score,
        row.rank,
        row.team_id,
        row.specialist_id,
        row.playbook_id,
    )


def _playbook_apply_score(
    category_match_score: Decimal,
    archetype_recurrence_score: Decimal,
    calibration_memory_score: Decimal,
    source_coverage_score: Decimal,
    forecast_accuracy_score: Decimal,
    config: TeamSpecialistProbabilityEventPlaybookRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            category_match_score * config.category_match_weight
            + archetype_recurrence_score * config.archetype_recurrence_weight
            + calibration_memory_score * config.calibration_memory_weight
            + source_coverage_score * config.source_coverage_weight
            + forecast_accuracy_score * config.forecast_accuracy_weight,
        )


def _row_reason_codes(
    playbook_status: str,
    category_match_score: Decimal,
    archetype_recurrence_score: Decimal,
    calibration_memory_score: Decimal,
    source_coverage_score: Decimal,
    recent_forecast_error: Decimal,
    config: TeamSpecialistProbabilityEventPlaybookRankV2Config,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if category_match_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_probability_event_playbook_category_match")
    else:
        reason_codes.add("team_specialist_probability_event_playbook_category_mismatch")
    if archetype_recurrence_score > ZERO:
        reason_codes.add("team_specialist_probability_event_playbook_archetype_recurring")
    else:
        reason_codes.add("team_specialist_probability_event_playbook_archetype_gap")
    if calibration_memory_score >= config.apply_score_floor:
        reason_codes.add(
            "team_specialist_probability_event_playbook_calibration_memory_strong",
        )
    elif calibration_memory_score < config.watch_score_floor:
        reason_codes.add("team_specialist_probability_event_playbook_calibration_memory_weak")
    if source_coverage_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add(
            "team_specialist_probability_event_playbook_source_coverage_complete",
        )
    else:
        reason_codes.add("team_specialist_probability_event_playbook_source_coverage_gap")
    if recent_forecast_error <= LOW_RECENT_ERROR_FLOOR:
        reason_codes.add("team_specialist_probability_event_playbook_recent_error_low")
    elif recent_forecast_error >= HIGH_RECENT_ERROR_FLOOR:
        reason_codes.add("team_specialist_probability_event_playbook_recent_error_high")
    if playbook_status == "apply":
        reason_codes.add("team_specialist_probability_event_playbook_apply")
    elif playbook_status == "watch":
        reason_codes.add("team_specialist_probability_event_playbook_watch")
    else:
        reason_codes.add("team_specialist_probability_event_playbook_skip")
    return tuple(reason for reason in ROW_REASON_CODES if reason in reason_codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistProbabilityEventPlaybookRankV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_probability_event_playbook_rank_empty",)
    reason_codes: list[str] = []
    if any(row.playbook_status == "apply" for row in rows):
        reason_codes.append("team_specialist_probability_event_playbook_rank_apply_rows")
    if any(row.playbook_status == "watch" for row in rows):
        reason_codes.append("team_specialist_probability_event_playbook_rank_watch_rows")
    if any(row.playbook_status == "skip" for row in rows):
        reason_codes.append("team_specialist_probability_event_playbook_rank_skip_rows")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _row_status(
    playbook_apply_score: Decimal,
    config: TeamSpecialistProbabilityEventPlaybookRankV2Config,
) -> str:
    if playbook_apply_score >= config.apply_score_floor:
        return "apply"
    if playbook_apply_score >= config.watch_score_floor:
        return "watch"
    return "skip"


def _report_status(
    rows: tuple[TeamSpecialistProbabilityEventPlaybookRankV2Row, ...],
) -> str:
    if not rows:
        return "skip"
    if any(row.playbook_status == "apply" for row in rows):
        return "apply"
    if any(row.playbook_status == "watch" for row in rows):
        return "watch"
    return "skip"


def _average_playbook_apply_score(
    rows: tuple[TeamSpecialistProbabilityEventPlaybookRankV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.playbook_apply_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _top_playbook_apply_score(
    rows: tuple[TeamSpecialistProbabilityEventPlaybookRankV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(row.playbook_apply_score for row in rows).quantize(RATIO_QUANTUM)


def _normalize_playbooks(
    playbooks: object,
) -> tuple[TeamSpecialistProbabilityEventPlaybookV2, ...]:
    if type(playbooks) not in (list, tuple):
        raise ValueError("playbooks must be a list or tuple")
    normalized = tuple(playbooks)
    seen_keys: set[tuple[str, str, str]] = set()
    for playbook in normalized:
        if type(playbook) is not TeamSpecialistProbabilityEventPlaybookV2:
            raise ValueError(
                "playbooks must contain TeamSpecialistProbabilityEventPlaybookV2 values",
            )
        _require_hard_flags("playbook", playbook)
        key = (playbook.team_id, playbook.specialist_id, playbook.playbook_id)
        if key in seen_keys:
            raise ValueError("playbooks must have unique public keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistProbabilityEventPlaybookRankV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not TeamSpecialistProbabilityEventPlaybookRankV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistProbabilityEventPlaybookRankV2Row "
                "values",
            )
        _require_hard_flags("row", row)
        key = (row.team_id, row.specialist_id, row.playbook_id)
        if key in seen_keys:
            raise ValueError("rows must have unique public keys")
        seen_keys.add(key)
    return normalized


def _validate_row_counts(
    row: TeamSpecialistProbabilityEventPlaybookRankV2Row,
) -> None:
    if row.matched_source_family_count > row.required_source_family_count:
        raise ValueError("matched_source_family_count must not exceed required")
    if row.matched_source_family_count != _count(len(row.matched_source_families)):
        raise ValueError("matched_source_family_count must match matched_source_families")


def _validate_report_counts_status_and_reasons(
    report: TeamSpecialistProbabilityEventPlaybookRankV2Report,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by apply score and rank")
    if tuple(row.rank for row in report.rows) != tuple(
        _count(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("rows must be sorted by apply score and rank")
    if report.playbook_count != _count(len(report.rows)):
        raise ValueError("playbook_count must match rows")
    if (
        report.apply_count
        != _count(sum(1 for row in report.rows if row.playbook_status == "apply"))
        or report.watch_count
        != _count(sum(1 for row in report.rows if row.playbook_status == "watch"))
        or report.skip_count
        != _count(sum(1 for row in report.rows if row.playbook_status == "skip"))
    ):
        raise ValueError("status counts must match rows")
    if report.rank_status != _report_status(report.rows):
        raise ValueError("rank_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rank_status")


def _validate_report_scores(
    report: TeamSpecialistProbabilityEventPlaybookRankV2Report,
) -> None:
    if report.average_playbook_apply_score != _average_playbook_apply_score(report.rows):
        raise ValueError("average_playbook_apply_score must match rows")
    if report.top_playbook_apply_score != _top_playbook_apply_score(report.rows):
        raise ValueError("top_playbook_apply_score must match rows")


def _row_digest(row: TeamSpecialistProbabilityEventPlaybookRankV2Row) -> str:
    return _digest_public(asdict(row))


def _report_digest(report: TeamSpecialistProbabilityEventPlaybookRankV2Report) -> str:
    return _digest_public(asdict(report))


def _digest_public(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(value)
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {
            key: _payload_value(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("payload numeric values must be Decimal-derived strings")
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        for field in fields(payload):
            _reject_unsafe_text(field.name)
            _reject_unsafe_public_payload(label, getattr(payload, field.name))
        return
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_text(key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) in (list, tuple):
        for value in payload:
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is Decimal:
        if not payload.is_finite():
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(payload) is datetime:
        _as_utc("payload datetime", payload)
        return
    if payload is None or type(payload) is bool:
        return
    if type(payload) is float or type(payload) is int:
        raise ValueError(f"unsafe public payload in {label}")
    if type(payload) is str:
        _reject_unsafe_text(payload)
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_text(value: str) -> None:
    normalized = value.lower()
    if value.strip() != value or "://" in normalized or "?" in normalized:
        raise ValueError("unsafe public payload")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    normalized = _normalize_optional_public_refs(field_name, value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _normalize_optional_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    for item in normalized:
        _require_public_string(field_name, item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if tuple(reason for reason in allowed if reason in normalized) != normalized:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be apply, watch, or skip")


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_ratio_total(*values: Decimal) -> None:
    total = sum(values, ZERO).quantize(RATIO_QUANTUM)
    if total != ONE.quantize(RATIO_QUANTUM):
        raise ValueError("rank weights must sum to 1.000000")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(RATIO_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _count_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO:
        raise ValueError("ratio limit must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / limit)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = value.quantize(RATIO_QUANTUM)
    if normalized < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if normalized > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_PROBABILITY_EVENT_PLAYBOOK_RANK_V2_CONFIG_VERSION",
    "TeamSpecialistProbabilityEventCandidateV2",
    "TeamSpecialistProbabilityEventPlaybookRankV2Config",
    "TeamSpecialistProbabilityEventPlaybookRankV2Report",
    "TeamSpecialistProbabilityEventPlaybookRankV2Row",
    "TeamSpecialistProbabilityEventPlaybookV2",
    "build_team_specialist_probability_event_playbook_rank_v2_report",
    "team_specialist_probability_event_playbook_rank_v2_payload",
)
