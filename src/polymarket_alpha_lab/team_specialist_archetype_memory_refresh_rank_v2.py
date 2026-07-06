"""Readonly archetype memory refresh ranking for specialist teams."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_TEAM_SPECIALIST_ARCHETYPE_MEMORY_REFRESH_RANK_V2_CONFIG_VERSION = (
    "team-specialist-archetype-memory-refresh-rank-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

ROW_REASON_CODES = (
    "refresh_rank_ready",
    "refresh_rank_watch",
    "refresh_rank_blocked",
    "archetype_match_strong",
    "archetype_match_watch",
    "archetype_match_gap",
    "playbook_fresh",
    "playbook_stale_watch",
    "playbook_stale_penalty",
    "lesson_impact_high",
    "lesson_impact_watch",
    "lesson_impact_gap",
    "evidence_quality_strong",
    "evidence_quality_watch",
    "evidence_quality_gap",
)
REPORT_REASON_CODES = (
    "memory_refresh_rank_ready",
    "memory_refresh_rank_watch",
    "memory_refresh_rank_blocked",
    "memory_refresh_rank_empty",
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

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_ARCHETYPE_MEMORY_REFRESH_RANK_V2_CONFIG_VERSION",
    "TeamSpecialistArchetypeMemoryRefreshRankV2Config",
    "TeamSpecialistArchetypeMemoryRefreshRankV2Observation",
    "TeamSpecialistArchetypeMemoryRefreshRankV2Row",
    "TeamSpecialistArchetypeMemoryRefreshRankV2Report",
    "build_team_specialist_archetype_memory_refresh_rank_v2",
    "team_specialist_archetype_memory_refresh_rank_v2_payload",
    "validate_team_specialist_archetype_memory_refresh_rank_v2_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__name__.startswith("TeamSpecialistArchetypeMemoryRefreshRankV2"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class TeamSpecialistArchetypeMemoryRefreshRankV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_ARCHETYPE_MEMORY_REFRESH_RANK_V2_CONFIG_VERSION
    )
    max_playbook_age_days: Decimal = Decimal("30.000000")
    archetype_match_weight: Decimal = Decimal("0.350000")
    playbook_freshness_weight: Decimal = Decimal("0.200000")
    lesson_impact_weight: Decimal = Decimal("0.250000")
    evidence_quality_weight: Decimal = Decimal("0.200000")
    high_impact_lesson_boost: Decimal = Decimal("0.100000")
    high_impact_lesson_floor: Decimal = Decimal("0.800000")
    ready_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistArchetypeMemoryRefreshRankV2Config,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "max_playbook_age_days",
            _require_positive_decimal(
                "max_playbook_age_days",
                self.max_playbook_age_days,
            ),
        )
        for field_name in (
            "archetype_match_weight",
            "playbook_freshness_weight",
            "lesson_impact_weight",
            "evidence_quality_weight",
            "high_impact_lesson_boost",
            "high_impact_lesson_floor",
            "ready_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_decimal_equal(
            "refresh rank weights",
            self.archetype_match_weight
            + self.playbook_freshness_weight
            + self.lesson_impact_weight
            + self.evidence_quality_weight,
            ONE,
        )
        if self.ready_score_floor < self.watch_score_floor:
            raise ValueError("ready_score_floor must be at least watch_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistArchetypeMemoryRefreshRankV2Observation(_FinalPublicDataclass):
    team_id: str
    archetype_id: str
    memory_id: str
    observed_at: datetime
    archetype_match_score: Decimal
    playbook_age_days: Decimal
    lesson_impact_score: Decimal
    evidence_quality_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistArchetypeMemoryRefreshRankV2Observation,
            "observation",
        )
        for field_name in (
            "team_id",
            "archetype_id",
            "memory_id",
            "source_config_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "archetype_match_score",
            "lesson_impact_score",
            "evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "playbook_age_days",
            _require_nonnegative_decimal("playbook_age_days", self.playbook_age_days),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistArchetypeMemoryRefreshRankV2Row(_FinalPublicDataclass):
    rank: Decimal
    team_id: str
    archetype_id: str
    memory_id: str
    observed_at: datetime
    archetype_match_score: Decimal
    playbook_age_days: Decimal
    playbook_freshness_score: Decimal
    lesson_impact_score: Decimal
    high_impact_lesson_boost_score: Decimal
    evidence_quality_score: Decimal
    refresh_rank_score: Decimal
    refresh_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistArchetypeMemoryRefreshRankV2Row, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in (
            "team_id",
            "archetype_id",
            "memory_id",
            "source_config_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "archetype_match_score",
            "playbook_freshness_score",
            "lesson_impact_score",
            "high_impact_lesson_boost_score",
            "evidence_quality_score",
            "refresh_rank_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "playbook_age_days",
            _require_nonnegative_decimal("playbook_age_days", self.playbook_age_days),
        )
        _require_status("refresh_status", self.refresh_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class TeamSpecialistArchetypeMemoryRefreshRankV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    refresh_status: str
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_archetype_match_score: Decimal
    average_playbook_freshness_score: Decimal
    average_lesson_impact_score: Decimal
    average_high_impact_lesson_boost_score: Decimal
    average_evidence_quality_score: Decimal
    average_refresh_rank_score: Decimal
    max_playbook_age_days: Decimal
    high_impact_lesson_count: Decimal
    stale_playbook_penalty_count: Decimal
    rows: tuple[TeamSpecialistArchetypeMemoryRefreshRankV2Row, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistArchetypeMemoryRefreshRankV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("refresh_status", self.refresh_status)
        for field_name in (
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "high_impact_lesson_count",
            "stale_playbook_penalty_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_archetype_match_score",
            "average_playbook_freshness_score",
            "average_lesson_impact_score",
            "average_high_impact_lesson_boost_score",
            "average_evidence_quality_score",
            "average_refresh_rank_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_playbook_age_days",
            _require_nonnegative_decimal(
                "max_playbook_age_days",
                self.max_playbook_age_days,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _require_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_team_specialist_archetype_memory_refresh_rank_v2(
    observations: Iterable[TeamSpecialistArchetypeMemoryRefreshRankV2Observation],
    *,
    config: TeamSpecialistArchetypeMemoryRefreshRankV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistArchetypeMemoryRefreshRankV2Report:
    cfg = config or TeamSpecialistArchetypeMemoryRefreshRankV2Config()
    if type(cfg) is not TeamSpecialistArchetypeMemoryRefreshRankV2Config:
        raise ValueError(
            "config must be exactly TeamSpecialistArchetypeMemoryRefreshRankV2Config",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    scored = tuple(_scored_observation(item, cfg) for item in normalized)
    rows = tuple(
        _row_for_scored_observation(rank=index, scored=item)
        for index, item in enumerate(_sorted_scored_observations(scored), start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "refresh_status": status,
        "row_count": _count_decimal(len(rows)),
        "ready_count": _status_count(rows, STATUS_READY),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "blocked_count": _status_count(rows, STATUS_BLOCKED),
        "average_archetype_match_score": _average(
            row.archetype_match_score for row in rows
        ),
        "average_playbook_freshness_score": _average(
            row.playbook_freshness_score for row in rows
        ),
        "average_lesson_impact_score": _average(row.lesson_impact_score for row in rows),
        "average_high_impact_lesson_boost_score": _average(
            row.high_impact_lesson_boost_score for row in rows
        ),
        "average_evidence_quality_score": _average(
            row.evidence_quality_score for row in rows
        ),
        "average_refresh_rank_score": _average(row.refresh_rank_score for row in rows),
        "max_playbook_age_days": max(
            (row.playbook_age_days for row in rows),
            default=ZERO,
        ),
        "high_impact_lesson_count": _count_decimal(
            sum(row.high_impact_lesson_boost_score > ZERO for row in rows),
        ),
        "stale_playbook_penalty_count": _count_decimal(
            sum(row.playbook_freshness_score == ZERO for row in rows),
        ),
        "rows": rows,
        "source_config_versions": tuple(
            sorted((item.memory_id, item.source_config_version) for item in normalized),
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return TeamSpecialistArchetypeMemoryRefreshRankV2Report(**values)


def team_specialist_archetype_memory_refresh_rank_v2_payload(
    report: TeamSpecialistArchetypeMemoryRefreshRankV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistArchetypeMemoryRefreshRankV2Report:
        raise ValueError(
            "report must be exactly TeamSpecialistArchetypeMemoryRefreshRankV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_team_specialist_archetype_memory_refresh_rank_v2_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return True


def _scored_observation(
    observation: TeamSpecialistArchetypeMemoryRefreshRankV2Observation,
    config: TeamSpecialistArchetypeMemoryRefreshRankV2Config,
) -> dict[str, object]:
    playbook_freshness_score = _playbook_freshness_score(
        observation.playbook_age_days,
        config.max_playbook_age_days,
    )
    high_impact_boost = (
        config.high_impact_lesson_boost
        if observation.lesson_impact_score >= config.high_impact_lesson_floor
        else ZERO
    )
    refresh_rank_score = _refresh_rank_score(
        archetype_match_score=observation.archetype_match_score,
        playbook_freshness_score=playbook_freshness_score,
        lesson_impact_score=observation.lesson_impact_score,
        evidence_quality_score=observation.evidence_quality_score,
        high_impact_lesson_boost_score=high_impact_boost,
        config=config,
    )
    return {
        "observation": observation,
        "playbook_freshness_score": playbook_freshness_score,
        "high_impact_lesson_boost_score": high_impact_boost,
        "refresh_rank_score": refresh_rank_score,
        "refresh_status": _row_status(refresh_rank_score, config),
    }


def _row_for_scored_observation(
    *,
    rank: int,
    scored: dict[str, object],
) -> TeamSpecialistArchetypeMemoryRefreshRankV2Row:
    observation = scored["observation"]
    if type(observation) is not TeamSpecialistArchetypeMemoryRefreshRankV2Observation:
        raise ValueError("scored observation must contain an observation")
    playbook_freshness_score = scored["playbook_freshness_score"]
    high_impact_lesson_boost_score = scored["high_impact_lesson_boost_score"]
    refresh_rank_score = scored["refresh_rank_score"]
    refresh_status = scored["refresh_status"]
    if type(playbook_freshness_score) is not Decimal:
        raise ValueError("playbook_freshness_score must be a Decimal")
    if type(high_impact_lesson_boost_score) is not Decimal:
        raise ValueError("high_impact_lesson_boost_score must be a Decimal")
    if type(refresh_rank_score) is not Decimal:
        raise ValueError("refresh_rank_score must be a Decimal")
    if type(refresh_status) is not str:
        raise ValueError("refresh_status must be a string")
    return TeamSpecialistArchetypeMemoryRefreshRankV2Row(
        rank=_count_decimal(rank),
        team_id=observation.team_id,
        archetype_id=observation.archetype_id,
        memory_id=observation.memory_id,
        observed_at=observation.observed_at,
        archetype_match_score=observation.archetype_match_score,
        playbook_age_days=observation.playbook_age_days,
        playbook_freshness_score=playbook_freshness_score,
        lesson_impact_score=observation.lesson_impact_score,
        high_impact_lesson_boost_score=high_impact_lesson_boost_score,
        evidence_quality_score=observation.evidence_quality_score,
        refresh_rank_score=refresh_rank_score,
        refresh_status=refresh_status,
        reason_codes=_row_reason_codes(
            archetype_match_score=observation.archetype_match_score,
            playbook_freshness_score=playbook_freshness_score,
            lesson_impact_score=observation.lesson_impact_score,
            evidence_quality_score=observation.evidence_quality_score,
            refresh_status=refresh_status,
        ),
        source_config_version=observation.source_config_version,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _sorted_scored_observations(
    values: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                -_sort_decimal(item["refresh_rank_score"]),
                _sort_text_from_scored(item, "team_id"),
                _sort_text_from_scored(item, "archetype_id"),
                _sort_text_from_scored(item, "memory_id"),
            ),
        ),
    )


def _sort_decimal(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("sort value must be a Decimal")
    return value


def _sort_text_from_scored(item: dict[str, object], field_name: str) -> str:
    observation = item["observation"]
    if type(observation) is not TeamSpecialistArchetypeMemoryRefreshRankV2Observation:
        raise ValueError("scored observation must contain an observation")
    value = getattr(observation, field_name)
    if type(value) is not str:
        raise ValueError("sort value must be a string")
    return value


def _playbook_freshness_score(age_days: Decimal, max_age_days: Decimal) -> Decimal:
    if age_days >= max_age_days:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - (age_days / max_age_days))


def _refresh_rank_score(
    *,
    archetype_match_score: Decimal,
    playbook_freshness_score: Decimal,
    lesson_impact_score: Decimal,
    evidence_quality_score: Decimal,
    high_impact_lesson_boost_score: Decimal,
    config: TeamSpecialistArchetypeMemoryRefreshRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_score = (
            archetype_match_score * config.archetype_match_weight
            + playbook_freshness_score * config.playbook_freshness_weight
            + lesson_impact_score * config.lesson_impact_weight
            + evidence_quality_score * config.evidence_quality_weight
            + high_impact_lesson_boost_score
        )
    return _clamp_ratio(weighted_score)


def _row_status(
    refresh_rank_score: Decimal,
    config: TeamSpecialistArchetypeMemoryRefreshRankV2Config,
) -> str:
    if refresh_rank_score >= config.ready_score_floor:
        return STATUS_READY
    if refresh_rank_score >= config.watch_score_floor:
        return STATUS_WATCH
    return STATUS_BLOCKED


def _row_reason_codes(
    *,
    archetype_match_score: Decimal,
    playbook_freshness_score: Decimal,
    lesson_impact_score: Decimal,
    evidence_quality_score: Decimal,
    refresh_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if refresh_status == STATUS_READY:
        codes.append("refresh_rank_ready")
    elif refresh_status == STATUS_WATCH:
        codes.append("refresh_rank_watch")
    else:
        codes.append("refresh_rank_blocked")

    if archetype_match_score >= Decimal("0.750000"):
        codes.append("archetype_match_strong")
    elif archetype_match_score >= Decimal("0.500000"):
        codes.append("archetype_match_watch")
    else:
        codes.append("archetype_match_gap")

    if playbook_freshness_score >= Decimal("0.750000"):
        codes.append("playbook_fresh")
    elif playbook_freshness_score > ZERO:
        codes.append("playbook_stale_watch")
    else:
        codes.append("playbook_stale_penalty")

    if lesson_impact_score >= Decimal("0.800000"):
        codes.append("lesson_impact_high")
    elif lesson_impact_score >= Decimal("0.500000"):
        codes.append("lesson_impact_watch")
    else:
        codes.append("lesson_impact_gap")

    if evidence_quality_score >= Decimal("0.750000"):
        codes.append("evidence_quality_strong")
    elif evidence_quality_score >= Decimal("0.500000"):
        codes.append("evidence_quality_watch")
    else:
        codes.append("evidence_quality_gap")
    return tuple(codes)


def _report_status(
    rows: tuple[TeamSpecialistArchetypeMemoryRefreshRankV2Row, ...],
) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.refresh_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.refresh_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    rows: tuple[TeamSpecialistArchetypeMemoryRefreshRankV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("memory_refresh_rank_empty",)
    if status == STATUS_READY:
        return ("memory_refresh_rank_ready",)
    if status == STATUS_WATCH:
        return ("memory_refresh_rank_watch",)
    return ("memory_refresh_rank_blocked",)


def _status_count(
    rows: tuple[TeamSpecialistArchetypeMemoryRefreshRankV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(row.refresh_status == status for row in rows))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(sum(items, ZERO) / Decimal(len(items)))


def _normalize_observations(
    observations: Iterable[TeamSpecialistArchetypeMemoryRefreshRankV2Observation],
) -> tuple[TeamSpecialistArchetypeMemoryRefreshRankV2Observation, ...]:
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc
    for item in items:
        if type(item) is not TeamSpecialistArchetypeMemoryRefreshRankV2Observation:
            raise ValueError(
                "observations must contain "
                "TeamSpecialistArchetypeMemoryRefreshRankV2Observation",
            )
    keys = [(item.team_id, item.archetype_id, item.memory_id) for item in items]
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate team archetype memory keys")
    return items


def _validate_report(report: TeamSpecialistArchetypeMemoryRefreshRankV2Report) -> None:
    rows = report.rows
    _require_decimal_equal("row_count", report.row_count, _count_decimal(len(rows)))
    _require_decimal_equal("ready_count", report.ready_count, _status_count(rows, STATUS_READY))
    _require_decimal_equal("watch_count", report.watch_count, _status_count(rows, STATUS_WATCH))
    _require_decimal_equal(
        "blocked_count",
        report.blocked_count,
        _status_count(rows, STATUS_BLOCKED),
    )
    _require_decimal_equal(
        "average_archetype_match_score",
        report.average_archetype_match_score,
        _average(row.archetype_match_score for row in rows),
    )
    _require_decimal_equal(
        "average_playbook_freshness_score",
        report.average_playbook_freshness_score,
        _average(row.playbook_freshness_score for row in rows),
    )
    _require_decimal_equal(
        "average_lesson_impact_score",
        report.average_lesson_impact_score,
        _average(row.lesson_impact_score for row in rows),
    )
    _require_decimal_equal(
        "average_high_impact_lesson_boost_score",
        report.average_high_impact_lesson_boost_score,
        _average(row.high_impact_lesson_boost_score for row in rows),
    )
    _require_decimal_equal(
        "average_evidence_quality_score",
        report.average_evidence_quality_score,
        _average(row.evidence_quality_score for row in rows),
    )
    _require_decimal_equal(
        "average_refresh_rank_score",
        report.average_refresh_rank_score,
        _average(row.refresh_rank_score for row in rows),
    )
    _require_decimal_equal(
        "max_playbook_age_days",
        report.max_playbook_age_days,
        max((row.playbook_age_days for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "high_impact_lesson_count",
        report.high_impact_lesson_count,
        _count_decimal(sum(row.high_impact_lesson_boost_score > ZERO for row in rows)),
    )
    _require_decimal_equal(
        "stale_playbook_penalty_count",
        report.stale_playbook_penalty_count,
        _count_decimal(sum(row.playbook_freshness_score == ZERO for row in rows)),
    )
    expected_versions = tuple(
        sorted((row.memory_id, row.source_config_version) for row in rows),
    )
    if report.source_config_versions != expected_versions:
        raise ValueError("source_config_versions must equal row source config versions")
    if report.refresh_status != _report_status(rows):
        raise ValueError("refresh_status must equal derived report status")
    if report.reason_codes != _report_reason_codes(rows, report.refresh_status):
        raise ValueError("reason_codes must equal derived report reason codes")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("public payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public surface")
            _require_safe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _require_safe_public_text(label, value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("public payload contains unsupported value")


def _require_safe_public_text(name: str, value: str) -> None:
    lower = value.lower()
    if any(fragment in lower for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public surface")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived_validation_digest", material)
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    _require_safe_public_text(name, value)
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_decimal_equal(name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != _six(expected):
        raise ValueError(f"{name} must equal derived value")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SIX)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SIX)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _six(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of {STATUSES}")
    return value


def _require_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{name} contains an unsupported reason code")
        normalized.append(item)
    return tuple(normalized)


def _require_rows(
    value: object,
) -> tuple[TeamSpecialistArchetypeMemoryRefreshRankV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not TeamSpecialistArchetypeMemoryRefreshRankV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistArchetypeMemoryRefreshRankV2Row",
            )
    ranks = tuple(item.rank for item in value)
    if ranks != tuple(_count_decimal(index) for index in range(1, len(value) + 1)):
        raise ValueError("rows must have sequential ranks")
    keys = [(item.team_id, item.archetype_id, item.memory_id) for item in value]
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate team archetype memory keys")
    expected = tuple(
        sorted(
            value,
            key=lambda row: (
                -row.refresh_rank_score,
                row.team_id,
                row.archetype_id,
                row.memory_id,
            ),
        ),
    )
    if value != expected:
        raise ValueError("rows must be sorted by refresh rank")
    return value


def _require_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions entries must be pairs")
        memory_id, config_version = item
        normalized.append(
            (
                _require_public_string("memory_id", memory_id),
                _require_public_string("source_config_version", config_version),
            ),
        )
    result = tuple(normalized)
    if tuple(sorted(result)) != result:
        raise ValueError("source_config_versions must be sorted")
    return result


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {name}")
