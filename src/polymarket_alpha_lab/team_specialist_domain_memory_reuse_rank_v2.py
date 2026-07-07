"""Phase 1 paper-only rank for domain/category specialist memory reuse."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_DOMAIN_MEMORY_REUSE_RANK_V2_CONFIG_VERSION = (
    "team-specialist-domain-memory-reuse-rank-v2-phase1"
)

STATUS_VALUES = ("reuse", "watch", "skip")
ROW_REASON_CODES = (
    "team_specialist_domain_memory_reuse_domain_match",
    "team_specialist_domain_memory_reuse_domain_gap",
    "team_specialist_domain_memory_reuse_category_match",
    "team_specialist_domain_memory_reuse_category_gap",
    "team_specialist_domain_memory_reuse_outcome_calibration_strong",
    "team_specialist_domain_memory_reuse_outcome_calibration_watch",
    "team_specialist_domain_memory_reuse_outcome_calibration_weak",
    "team_specialist_domain_memory_reuse_recent",
    "team_specialist_domain_memory_reuse_recency_watch",
    "team_specialist_domain_memory_reuse_stale",
    "team_specialist_domain_memory_reuse_source_overlap_complete",
    "team_specialist_domain_memory_reuse_source_overlap_gap",
    "team_specialist_domain_memory_reuse_event_archetype_match",
    "team_specialist_domain_memory_reuse_event_archetype_gap",
    "team_specialist_domain_memory_reuse_contradiction_history_clean",
    "team_specialist_domain_memory_reuse_contradiction_history_present",
    "team_specialist_domain_memory_reuse_resolved_postmortem_useful",
    "team_specialist_domain_memory_reuse_resolved_postmortem_gap",
    "team_specialist_domain_memory_reuse_reuse",
    "team_specialist_domain_memory_reuse_watch",
    "team_specialist_domain_memory_reuse_skip",
)
REPORT_REASON_CODES = (
    "team_specialist_domain_memory_reuse_rank_reuse_rows",
    "team_specialist_domain_memory_reuse_rank_watch_rows",
    "team_specialist_domain_memory_reuse_rank_skip_rows",
    "team_specialist_domain_memory_reuse_rank_empty",
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
PUBLIC_DATACLASS_NAMES = (
    "TeamSpecialistDomainMemoryReuseRankV2Config",
    "TeamSpecialistDomainMemoryReuseContextV2",
    "TeamSpecialistDomainMemoryReuseItemV2",
    "TeamSpecialistDomainMemoryReuseRankV2Row",
    "TeamSpecialistDomainMemoryReuseRankV2Report",
)

DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryReuseRankV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_DOMAIN_MEMORY_REUSE_RANK_V2_CONFIG_VERSION
    )
    outcome_calibration_weight: Decimal = Decimal("0.250000")
    recency_weight: Decimal = Decimal("0.200000")
    source_overlap_weight: Decimal = Decimal("0.150000")
    event_archetype_match_weight: Decimal = Decimal("0.150000")
    contradiction_history_weight: Decimal = Decimal("0.100000")
    resolved_postmortem_usefulness_weight: Decimal = Decimal("0.150000")
    max_memory_age_days: Decimal = Decimal("90.000000")
    max_contradiction_count: Decimal = Decimal("5")
    reuse_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistDomainMemoryReuseRankV2Config,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_DOMAIN_MEMORY_REUSE_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "outcome_calibration_weight",
            "recency_weight",
            "source_overlap_weight",
            "event_archetype_match_weight",
            "contradiction_history_weight",
            "resolved_postmortem_usefulness_weight",
            "reuse_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_days",
            _normalize_positive_decimal("max_memory_age_days", self.max_memory_age_days),
        )
        object.__setattr__(
            self,
            "max_contradiction_count",
            _normalize_positive_count(
                "max_contradiction_count",
                self.max_contradiction_count,
            ),
        )
        _require_ratio_total(
            "reuse rank weights",
            self.outcome_calibration_weight,
            self.recency_weight,
            self.source_overlap_weight,
            self.event_archetype_match_weight,
            self.contradiction_history_weight,
            self.resolved_postmortem_usefulness_weight,
        )
        if self.watch_score_floor > self.reuse_score_floor:
            raise ValueError("watch_score_floor must not exceed reuse_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryReuseContextV2(_FinalPublicDataclass):
    context_id: str
    domain_id: str
    category_id: str
    event_archetype: str
    required_source_families: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistDomainMemoryReuseContextV2, "context")
        for field_name in ("context_id", "domain_id", "category_id", "event_archetype"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_public_refs(
                "required_source_families",
                self.required_source_families,
            ),
        )
        _require_hard_flags("context", self)
        _reject_unsafe_public_payload("context", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryReuseItemV2(_FinalPublicDataclass):
    team_id: str
    specialist_id: str
    memory_id: str
    domain_ids: tuple[str, ...]
    category_ids: tuple[str, ...]
    event_archetypes: tuple[str, ...]
    source_family_ids: tuple[str, ...]
    outcome_calibration_score: Decimal
    memory_age_days: Decimal
    contradiction_count: Decimal
    resolved_postmortem_usefulness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistDomainMemoryReuseItemV2, "memory_item")
        for field_name in ("team_id", "specialist_id", "memory_id"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "domain_ids",
            "category_ids",
            "event_archetypes",
            "source_family_ids",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_public_refs(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_calibration_score",
            _normalize_ratio(
                "outcome_calibration_score",
                self.outcome_calibration_score,
            ),
        )
        object.__setattr__(
            self,
            "memory_age_days",
            _normalize_nonnegative_decimal("memory_age_days", self.memory_age_days),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_count("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "resolved_postmortem_usefulness_score",
            _normalize_ratio(
                "resolved_postmortem_usefulness_score",
                self.resolved_postmortem_usefulness_score,
            ),
        )
        _require_hard_flags("memory_item", self)
        _reject_unsafe_public_payload("memory_item", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryReuseRankV2Row(_FinalPublicDataclass):
    rank: Decimal
    context_id: str
    team_id: str
    specialist_id: str
    memory_id: str
    domain_match_score: Decimal
    category_match_score: Decimal
    outcome_calibration_score: Decimal
    memory_age_days: Decimal
    recency_score: Decimal
    source_overlap_score: Decimal
    event_archetype_match_score: Decimal
    contradiction_count: Decimal
    contradiction_history_score: Decimal
    resolved_postmortem_usefulness_score: Decimal
    required_source_family_count: Decimal
    matched_source_family_count: Decimal
    matched_source_families: tuple[str, ...]
    reuse_score: Decimal
    reuse_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistDomainMemoryReuseRankV2Row, "row")
        object.__setattr__(self, "rank", _normalize_count("rank", self.rank))
        for field_name in ("context_id", "team_id", "specialist_id", "memory_id"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "domain_match_score",
            "category_match_score",
            "outcome_calibration_score",
            "recency_score",
            "source_overlap_score",
            "event_archetype_match_score",
            "contradiction_history_score",
            "resolved_postmortem_usefulness_score",
            "reuse_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_days",
            _normalize_nonnegative_decimal("memory_age_days", self.memory_age_days),
        )
        for field_name in (
            "contradiction_count",
            "required_source_family_count",
            "matched_source_family_count",
        ):
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
        _require_status("reuse_status", self.reuse_status)
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
        _reject_unsafe_public_payload("row", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


@dataclass(frozen=True)
class TeamSpecialistDomainMemoryReuseRankV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    context_id: str
    domain_id: str
    category_id: str
    event_archetype: str
    memory_count: Decimal
    reuse_count: Decimal
    watch_count: Decimal
    skip_count: Decimal
    average_reuse_score: Decimal
    top_reuse_score: Decimal
    reuse_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistDomainMemoryReuseRankV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, TeamSpecialistDomainMemoryReuseRankV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_DOMAIN_MEMORY_REUSE_RANK_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("context_id", "domain_id", "category_id", "event_archetype"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("memory_count", "reuse_count", "watch_count", "skip_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_reuse_score", "top_reuse_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("reuse_status", self.reuse_status)
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
        _validate_report_counts_status_reasons_and_scores(self)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_domain_memory_reuse_rank_v2_payload(self)


def build_team_specialist_domain_memory_reuse_rank_v2_report(
    *,
    reuse_context: TeamSpecialistDomainMemoryReuseContextV2,
    memory_items: object,
    generated_at: datetime,
    config: TeamSpecialistDomainMemoryReuseRankV2Config | None = None,
) -> TeamSpecialistDomainMemoryReuseRankV2Report:
    if type(reuse_context) is not TeamSpecialistDomainMemoryReuseContextV2:
        raise ValueError(
            "reuse_context must be TeamSpecialistDomainMemoryReuseContextV2",
        )
    _require_hard_flags("reuse_context", reuse_context)
    if config is None:
        config = TeamSpecialistDomainMemoryReuseRankV2Config()
    if type(config) is not TeamSpecialistDomainMemoryReuseRankV2Config:
        raise ValueError(
            "config must be a TeamSpecialistDomainMemoryReuseRankV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_memory_items(memory_items)
    rows_without_rank = tuple(
        _row_parts(reuse_context, item, config) for item in normalized_items
    )
    ranked_rows = tuple(
        TeamSpecialistDomainMemoryReuseRankV2Row(
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
        "context_id": reuse_context.context_id,
        "domain_id": reuse_context.domain_id,
        "category_id": reuse_context.category_id,
        "event_archetype": reuse_context.event_archetype,
        "memory_count": _count(len(ranked_rows)),
        "reuse_count": _count(
            sum(1 for row in ranked_rows if row.reuse_status == "reuse"),
        ),
        "watch_count": _count(
            sum(1 for row in ranked_rows if row.reuse_status == "watch"),
        ),
        "skip_count": _count(
            sum(1 for row in ranked_rows if row.reuse_status == "skip"),
        ),
        "average_reuse_score": _average_reuse_score(ranked_rows),
        "top_reuse_score": _top_reuse_score(ranked_rows),
        "reuse_status": _report_status(ranked_rows),
        "reason_codes": _report_reason_codes(ranked_rows),
        "rows": ranked_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistDomainMemoryReuseRankV2Report(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_domain_memory_reuse_rank_v2_payload(
    report: TeamSpecialistDomainMemoryReuseRankV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistDomainMemoryReuseRankV2Report:
        raise ValueError("report must be a TeamSpecialistDomainMemoryReuseRankV2Report")
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_parts(
    reuse_context: TeamSpecialistDomainMemoryReuseContextV2,
    item: TeamSpecialistDomainMemoryReuseItemV2,
    config: TeamSpecialistDomainMemoryReuseRankV2Config,
) -> dict[str, object]:
    domain_match_score = _binary_score(reuse_context.domain_id in item.domain_ids)
    category_match_score = _binary_score(reuse_context.category_id in item.category_ids)
    recency_score = _recency_score(item.memory_age_days, config)
    matched_source_families = tuple(
        source_family
        for source_family in reuse_context.required_source_families
        if source_family in item.source_family_ids
    )
    required_source_family_count = _count(len(reuse_context.required_source_families))
    matched_source_family_count = _count(len(matched_source_families))
    source_overlap_score = _count_ratio(
        matched_source_family_count,
        required_source_family_count,
    )
    event_archetype_match_score = _binary_score(
        reuse_context.event_archetype in item.event_archetypes,
    )
    contradiction_history_score = _contradiction_history_score(
        item.contradiction_count,
        config,
    )
    reuse_score = _reuse_score(
        outcome_calibration_score=item.outcome_calibration_score,
        recency_score=recency_score,
        source_overlap_score=source_overlap_score,
        event_archetype_match_score=event_archetype_match_score,
        contradiction_history_score=contradiction_history_score,
        resolved_postmortem_usefulness_score=(
            item.resolved_postmortem_usefulness_score
        ),
        config=config,
    )
    reuse_status = _row_status(reuse_score, config)
    return {
        "context_id": reuse_context.context_id,
        "team_id": item.team_id,
        "specialist_id": item.specialist_id,
        "memory_id": item.memory_id,
        "domain_match_score": domain_match_score,
        "category_match_score": category_match_score,
        "outcome_calibration_score": item.outcome_calibration_score,
        "memory_age_days": item.memory_age_days,
        "recency_score": recency_score,
        "source_overlap_score": source_overlap_score,
        "event_archetype_match_score": event_archetype_match_score,
        "contradiction_count": item.contradiction_count,
        "contradiction_history_score": contradiction_history_score,
        "resolved_postmortem_usefulness_score": (
            item.resolved_postmortem_usefulness_score
        ),
        "required_source_family_count": required_source_family_count,
        "matched_source_family_count": matched_source_family_count,
        "matched_source_families": matched_source_families,
        "reuse_score": reuse_score,
        "reuse_status": reuse_status,
        "reason_codes": _row_reason_codes(
            reuse_status=reuse_status,
            domain_match_score=domain_match_score,
            category_match_score=category_match_score,
            outcome_calibration_score=item.outcome_calibration_score,
            recency_score=recency_score,
            source_overlap_score=source_overlap_score,
            event_archetype_match_score=event_archetype_match_score,
            contradiction_history_score=contradiction_history_score,
            resolved_postmortem_usefulness_score=(
                item.resolved_postmortem_usefulness_score
            ),
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_parts_sort_key(parts: dict[str, object]) -> tuple[Decimal, Decimal, str, str, str]:
    reuse_score = parts["reuse_score"]
    memory_age_days = parts["memory_age_days"]
    if type(reuse_score) is not Decimal or type(memory_age_days) is not Decimal:
        raise ValueError("reuse_score and memory_age_days must be Decimal")
    return (
        -reuse_score,
        memory_age_days,
        str(parts["team_id"]),
        str(parts["specialist_id"]),
        str(parts["memory_id"]),
    )


def _row_sort_key(
    row: TeamSpecialistDomainMemoryReuseRankV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    return (
        -row.reuse_score,
        row.memory_age_days,
        row.rank,
        row.team_id,
        row.specialist_id,
        row.memory_id,
    )


def _binary_score(value: bool) -> Decimal:
    if value:
        return ONE.quantize(RATIO_QUANTUM)
    return ZERO.quantize(RATIO_QUANTUM)


def _recency_score(
    memory_age_days: Decimal,
    config: TeamSpecialistDomainMemoryReuseRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - memory_age_days / config.max_memory_age_days)


def _contradiction_history_score(
    contradiction_count: Decimal,
    config: TeamSpecialistDomainMemoryReuseRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            ONE - contradiction_count / config.max_contradiction_count,
        )


def _reuse_score(
    *,
    outcome_calibration_score: Decimal,
    recency_score: Decimal,
    source_overlap_score: Decimal,
    event_archetype_match_score: Decimal,
    contradiction_history_score: Decimal,
    resolved_postmortem_usefulness_score: Decimal,
    config: TeamSpecialistDomainMemoryReuseRankV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            outcome_calibration_score * config.outcome_calibration_weight
            + recency_score * config.recency_weight
            + source_overlap_score * config.source_overlap_weight
            + event_archetype_match_score * config.event_archetype_match_weight
            + contradiction_history_score * config.contradiction_history_weight
            + resolved_postmortem_usefulness_score
            * config.resolved_postmortem_usefulness_weight,
        )


def _row_status(
    reuse_score: Decimal,
    config: TeamSpecialistDomainMemoryReuseRankV2Config,
) -> str:
    if reuse_score >= config.reuse_score_floor:
        return "reuse"
    if reuse_score >= config.watch_score_floor:
        return "watch"
    return "skip"


def _report_status(rows: tuple[TeamSpecialistDomainMemoryReuseRankV2Row, ...]) -> str:
    if not rows:
        return "skip"
    if any(row.reuse_status == "reuse" for row in rows):
        return "reuse"
    if any(row.reuse_status == "watch" for row in rows):
        return "watch"
    return "skip"


def _row_reason_codes(
    *,
    reuse_status: str,
    domain_match_score: Decimal,
    category_match_score: Decimal,
    outcome_calibration_score: Decimal,
    recency_score: Decimal,
    source_overlap_score: Decimal,
    event_archetype_match_score: Decimal,
    contradiction_history_score: Decimal,
    resolved_postmortem_usefulness_score: Decimal,
    config: TeamSpecialistDomainMemoryReuseRankV2Config,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if domain_match_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_domain_memory_reuse_domain_match")
    else:
        reason_codes.add("team_specialist_domain_memory_reuse_domain_gap")
    if category_match_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_domain_memory_reuse_category_match")
    else:
        reason_codes.add("team_specialist_domain_memory_reuse_category_gap")
    if outcome_calibration_score >= config.reuse_score_floor:
        reason_codes.add(
            "team_specialist_domain_memory_reuse_outcome_calibration_strong",
        )
    elif outcome_calibration_score >= config.watch_score_floor:
        reason_codes.add(
            "team_specialist_domain_memory_reuse_outcome_calibration_watch",
        )
    else:
        reason_codes.add("team_specialist_domain_memory_reuse_outcome_calibration_weak")
    if recency_score >= config.reuse_score_floor:
        reason_codes.add("team_specialist_domain_memory_reuse_recent")
    elif recency_score >= config.watch_score_floor:
        reason_codes.add("team_specialist_domain_memory_reuse_recency_watch")
    else:
        reason_codes.add("team_specialist_domain_memory_reuse_stale")
    if source_overlap_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_domain_memory_reuse_source_overlap_complete")
    else:
        reason_codes.add("team_specialist_domain_memory_reuse_source_overlap_gap")
    if event_archetype_match_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_domain_memory_reuse_event_archetype_match")
    else:
        reason_codes.add("team_specialist_domain_memory_reuse_event_archetype_gap")
    if contradiction_history_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add(
            "team_specialist_domain_memory_reuse_contradiction_history_clean",
        )
    else:
        reason_codes.add(
            "team_specialist_domain_memory_reuse_contradiction_history_present",
        )
    if resolved_postmortem_usefulness_score >= config.watch_score_floor:
        reason_codes.add(
            "team_specialist_domain_memory_reuse_resolved_postmortem_useful",
        )
    else:
        reason_codes.add(
            "team_specialist_domain_memory_reuse_resolved_postmortem_gap",
        )
    reason_codes.add(f"team_specialist_domain_memory_reuse_{reuse_status}")
    return tuple(reason for reason in ROW_REASON_CODES if reason in reason_codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistDomainMemoryReuseRankV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_domain_memory_reuse_rank_empty",)
    reason_codes: list[str] = []
    if any(row.reuse_status == "reuse" for row in rows):
        reason_codes.append("team_specialist_domain_memory_reuse_rank_reuse_rows")
    if any(row.reuse_status == "watch" for row in rows):
        reason_codes.append("team_specialist_domain_memory_reuse_rank_watch_rows")
    if any(row.reuse_status == "skip" for row in rows):
        reason_codes.append("team_specialist_domain_memory_reuse_rank_skip_rows")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _average_reuse_score(
    rows: tuple[TeamSpecialistDomainMemoryReuseRankV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.reuse_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _top_reuse_score(
    rows: tuple[TeamSpecialistDomainMemoryReuseRankV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(row.reuse_score for row in rows).quantize(RATIO_QUANTUM)


def _normalize_memory_items(
    memory_items: object,
) -> tuple[TeamSpecialistDomainMemoryReuseItemV2, ...]:
    if type(memory_items) not in (list, tuple):
        raise ValueError("memory_items must be a list or tuple")
    normalized = tuple(memory_items)
    seen_keys: set[tuple[str, str, str]] = set()
    for item in normalized:
        if type(item) is not TeamSpecialistDomainMemoryReuseItemV2:
            raise ValueError(
                "memory_items must contain TeamSpecialistDomainMemoryReuseItemV2 "
                "values",
            )
        _require_hard_flags("memory_item", item)
        key = (item.team_id, item.specialist_id, item.memory_id)
        if key in seen_keys:
            raise ValueError("memory_items must have unique public keys")
        seen_keys.add(key)
    return normalized


def _normalize_rows(rows: object) -> tuple[TeamSpecialistDomainMemoryReuseRankV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not TeamSpecialistDomainMemoryReuseRankV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistDomainMemoryReuseRankV2Row values",
            )
        _require_hard_flags("row", row)
        key = (row.team_id, row.specialist_id, row.memory_id)
        if key in seen_keys:
            raise ValueError("rows must have unique public keys")
        seen_keys.add(key)
    return normalized


def _validate_row_counts(row: TeamSpecialistDomainMemoryReuseRankV2Row) -> None:
    if row.matched_source_family_count > row.required_source_family_count:
        raise ValueError("matched_source_family_count must not exceed required")
    if row.matched_source_family_count != _count(len(row.matched_source_families)):
        raise ValueError("matched_source_family_count must match matched_source_families")


def _validate_report_counts_status_reasons_and_scores(
    report: TeamSpecialistDomainMemoryReuseRankV2Report,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by reuse score and rank")
    if tuple(row.rank for row in report.rows) != tuple(
        _count(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("rows must be sorted by reuse score and rank")
    if report.memory_count != _count(len(report.rows)):
        raise ValueError("memory_count must match rows")
    if (
        report.reuse_count
        != _count(sum(1 for row in report.rows if row.reuse_status == "reuse"))
        or report.watch_count
        != _count(sum(1 for row in report.rows if row.reuse_status == "watch"))
        or report.skip_count
        != _count(sum(1 for row in report.rows if row.reuse_status == "skip"))
    ):
        raise ValueError("status counts must match rows")
    if report.reuse_status != _report_status(report.rows):
        raise ValueError("reuse_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match reuse_status")
    if report.average_reuse_score != _average_reuse_score(report.rows):
        raise ValueError("average_reuse_score must match rows")
    if report.top_reuse_score != _top_reuse_score(report.rows):
        raise ValueError("top_reuse_score must match rows")


def _row_digest(row: TeamSpecialistDomainMemoryReuseRankV2Row) -> str:
    return _digest_public(asdict(row))


def _report_digest(report: TeamSpecialistDomainMemoryReuseRankV2Report) -> str:
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
    if type(payload) is int or type(payload) is float:
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
    return tuple(reason for reason in allowed if reason in normalized)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of {STATUS_VALUES!r}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    for character in value:
        if not (
            "a" <= character <= "z"
            or "A" <= character <= "Z"
            or "0" <= character <= "9"
            or character in "_.-"
        ):
            raise ValueError(f"{field_name} must be a public string")
    _reject_unsafe_text(value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_ratio_total(label: str, *values: Decimal) -> None:
    if _quantize(sum(values, ZERO)) != ONE.quantize(RATIO_QUANTUM):
        raise ValueError(f"{label} must sum to 1.000000")


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _count_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if normalized > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_DOMAIN_MEMORY_REUSE_RANK_V2_CONFIG_VERSION",
    "TeamSpecialistDomainMemoryReuseContextV2",
    "TeamSpecialistDomainMemoryReuseItemV2",
    "TeamSpecialistDomainMemoryReuseRankV2Config",
    "TeamSpecialistDomainMemoryReuseRankV2Report",
    "TeamSpecialistDomainMemoryReuseRankV2Row",
    "build_team_specialist_domain_memory_reuse_rank_v2_report",
    "team_specialist_domain_memory_reuse_rank_v2_payload",
)
