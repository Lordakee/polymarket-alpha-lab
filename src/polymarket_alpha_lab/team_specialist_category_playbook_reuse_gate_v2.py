"""Pure Phase 1 gate for specialist category playbook reuse."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_CATEGORY_PLAYBOOK_REUSE_GATE_V2_CONFIG_VERSION = (
    "team-specialist-category-playbook-reuse-gate-v2-phase1"
)

GATE_STATUSES = ("reuse", "watch", "skip")
REPORT_REASON_CODES = (
    "team_specialist_category_playbook_reuse_event_archetype_match",
    "team_specialist_category_playbook_reuse_event_archetype_gap",
    "team_specialist_category_playbook_reuse_calibration_strong",
    "team_specialist_category_playbook_reuse_calibration_watch",
    "team_specialist_category_playbook_reuse_calibration_weak",
    "team_specialist_category_playbook_reuse_outcome_sample_full",
    "team_specialist_category_playbook_reuse_outcome_sample_watch",
    "team_specialist_category_playbook_reuse_outcome_sample_thin",
    "team_specialist_category_playbook_reuse_source_family_match",
    "team_specialist_category_playbook_reuse_source_family_partial",
    "team_specialist_category_playbook_reuse_source_family_gap",
    "team_specialist_category_playbook_reuse_resolution_rule_match",
    "team_specialist_category_playbook_reuse_resolution_rule_gap",
    "team_specialist_category_playbook_reuse_recent",
    "team_specialist_category_playbook_reuse_recency_watch",
    "team_specialist_category_playbook_reuse_stale",
    "team_specialist_category_playbook_reuse_reuse",
    "team_specialist_category_playbook_reuse_watch",
    "team_specialist_category_playbook_reuse_skip",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sig" "ning",
    "muta" "tion",
    "b" "uy",
    "se" "ll",
    "tr" "ade",
)
PUBLIC_DATACLASS_NAMES = (
    "TeamSpecialistCategoryPlaybookReuseGateV2Config",
    "TeamSpecialistCategoryPlaybookReuseGateV2Context",
    "TeamSpecialistCategoryPlaybookReuseGateV2Playbook",
    "TeamSpecialistCategoryPlaybookReuseGateV2Report",
)

DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class TeamSpecialistCategoryPlaybookReuseGateV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CATEGORY_PLAYBOOK_REUSE_GATE_V2_CONFIG_VERSION
    )
    event_archetype_match_weight: Decimal = Decimal("0.200000")
    calibration_quality_weight: Decimal = Decimal("0.200000")
    outcome_sample_size_weight: Decimal = Decimal("0.150000")
    source_family_match_weight: Decimal = Decimal("0.150000")
    resolution_rule_match_weight: Decimal = Decimal("0.150000")
    recency_weight: Decimal = Decimal("0.150000")
    min_reuse_calibration_quality: Decimal = Decimal("0.800000")
    min_watch_calibration_quality: Decimal = Decimal("0.600000")
    min_reuse_outcome_sample_size: Decimal = Decimal("20")
    min_watch_outcome_sample_size: Decimal = Decimal("8")
    min_reuse_source_family_match_score: Decimal = Decimal("1.000000")
    min_watch_source_family_match_score: Decimal = Decimal("0.500000")
    max_reuse_playbook_age_days: Decimal = Decimal("30.000000")
    max_watch_playbook_age_days: Decimal = Decimal("90.000000")
    reuse_score_floor: Decimal = Decimal("0.800000")
    watch_score_floor: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistCategoryPlaybookReuseGateV2Config,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CATEGORY_PLAYBOOK_REUSE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "event_archetype_match_weight",
            "calibration_quality_weight",
            "outcome_sample_size_weight",
            "source_family_match_weight",
            "resolution_rule_match_weight",
            "recency_weight",
            "min_reuse_calibration_quality",
            "min_watch_calibration_quality",
            "min_reuse_source_family_match_score",
            "min_watch_source_family_match_score",
            "reuse_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_reuse_outcome_sample_size",
            "min_watch_outcome_sample_size",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_reuse_playbook_age_days",
            "max_watch_playbook_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryPlaybookReuseGateV2Context(_FinalPublicDataclass):
    event_id: str
    category_id: str
    event_archetype: str
    required_source_families: tuple[str, ...]
    resolution_rule_id: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistCategoryPlaybookReuseGateV2Context,
            "event_context",
        )
        for field_name in (
            "event_id",
            "category_id",
            "event_archetype",
            "resolution_rule_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_public_refs(
                "required_source_families",
                self.required_source_families,
            ),
        )
        _require_hard_flags("event_context", self)
        _reject_unsafe_public_payload("event_context", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryPlaybookReuseGateV2Playbook(_FinalPublicDataclass):
    team_id: str
    specialist_id: str
    playbook_id: str
    category_id: str
    event_archetypes: tuple[str, ...]
    calibration_quality_score: Decimal
    outcome_sample_size: Decimal
    source_family_ids: tuple[str, ...]
    resolution_rule_ids: tuple[str, ...]
    updated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistCategoryPlaybookReuseGateV2Playbook,
            "category_playbook",
        )
        for field_name in ("team_id", "specialist_id", "playbook_id", "category_id"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "event_archetypes",
            _normalize_public_refs("event_archetypes", self.event_archetypes),
        )
        object.__setattr__(
            self,
            "calibration_quality_score",
            _normalize_ratio(
                "calibration_quality_score",
                self.calibration_quality_score,
            ),
        )
        object.__setattr__(
            self,
            "outcome_sample_size",
            _normalize_count("outcome_sample_size", self.outcome_sample_size),
        )
        object.__setattr__(
            self,
            "source_family_ids",
            _normalize_public_refs("source_family_ids", self.source_family_ids),
        )
        object.__setattr__(
            self,
            "resolution_rule_ids",
            _normalize_public_refs("resolution_rule_ids", self.resolution_rule_ids),
        )
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        _require_hard_flags("category_playbook", self)
        _reject_unsafe_public_payload("category_playbook", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryPlaybookReuseGateV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    event_id: str
    team_id: str
    specialist_id: str
    category_id: str
    playbook_id: str
    gate_status: str
    event_archetype_match_score: Decimal
    calibration_quality_score: Decimal
    outcome_sample_size: Decimal
    outcome_sample_size_score: Decimal
    required_source_family_count: Decimal
    matched_source_family_count: Decimal
    matched_source_families: tuple[str, ...]
    source_family_match_score: Decimal
    resolution_rule_match_score: Decimal
    recency_age_days: Decimal
    recency_score: Decimal
    reuse_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistCategoryPlaybookReuseGateV2Report,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CATEGORY_PLAYBOOK_REUSE_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "event_id",
            "team_id",
            "specialist_id",
            "category_id",
            "playbook_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("gate_status", self.gate_status)
        for field_name in (
            "event_archetype_match_score",
            "calibration_quality_score",
            "outcome_sample_size_score",
            "source_family_match_score",
            "resolution_rule_match_score",
            "recency_score",
            "reuse_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "outcome_sample_size",
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
        object.__setattr__(
            self,
            "recency_age_days",
            _normalize_nonnegative_decimal("recency_age_days", self.recency_age_days),
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
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_category_playbook_reuse_gate_v2_payload(self)


def build_team_specialist_category_playbook_reuse_gate_v2(
    *,
    event_context: TeamSpecialistCategoryPlaybookReuseGateV2Context,
    category_playbook: TeamSpecialistCategoryPlaybookReuseGateV2Playbook,
    generated_at: datetime,
    config: TeamSpecialistCategoryPlaybookReuseGateV2Config | None = None,
) -> TeamSpecialistCategoryPlaybookReuseGateV2Report:
    if type(event_context) is not TeamSpecialistCategoryPlaybookReuseGateV2Context:
        raise ValueError(
            "event_context must be TeamSpecialistCategoryPlaybookReuseGateV2Context",
        )
    if type(category_playbook) is not TeamSpecialistCategoryPlaybookReuseGateV2Playbook:
        raise ValueError(
            "category_playbook must be TeamSpecialistCategoryPlaybookReuseGateV2Playbook",
        )
    if config is None:
        config = TeamSpecialistCategoryPlaybookReuseGateV2Config()
    if type(config) is not TeamSpecialistCategoryPlaybookReuseGateV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCategoryPlaybookReuseGateV2Config",
        )
    _require_hard_flags("event_context", event_context)
    _require_hard_flags("category_playbook", category_playbook)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if category_playbook.category_id != event_context.category_id:
        raise ValueError("category_id must match event_context category_id")
    if category_playbook.updated_at > generated_at_utc:
        raise ValueError("updated_at must be on or before generated_at")

    event_archetype_match_score = _binary_score(
        event_context.event_archetype in category_playbook.event_archetypes,
    )
    outcome_sample_size_score = _count_ratio(
        category_playbook.outcome_sample_size,
        config.min_reuse_outcome_sample_size,
    )
    matched_source_families = tuple(
        source_family
        for source_family in event_context.required_source_families
        if source_family in category_playbook.source_family_ids
    )
    required_source_family_count = _count(len(event_context.required_source_families))
    matched_source_family_count = _count(len(matched_source_families))
    source_family_match_score = _count_ratio(
        matched_source_family_count,
        required_source_family_count,
    )
    resolution_rule_match_score = _binary_score(
        event_context.resolution_rule_id in category_playbook.resolution_rule_ids,
    )
    recency_age_days = _age_days(generated_at_utc, category_playbook.updated_at)
    recency_score = _recency_score(recency_age_days, config)
    reuse_score = _reuse_score(
        event_archetype_match_score=event_archetype_match_score,
        calibration_quality_score=category_playbook.calibration_quality_score,
        outcome_sample_size_score=outcome_sample_size_score,
        source_family_match_score=source_family_match_score,
        resolution_rule_match_score=resolution_rule_match_score,
        recency_score=recency_score,
        config=config,
    )
    gate_status = _gate_status(
        event_archetype_match_score=event_archetype_match_score,
        calibration_quality_score=category_playbook.calibration_quality_score,
        outcome_sample_size=category_playbook.outcome_sample_size,
        source_family_match_score=source_family_match_score,
        resolution_rule_match_score=resolution_rule_match_score,
        recency_age_days=recency_age_days,
        reuse_score=reuse_score,
        config=config,
    )

    return TeamSpecialistCategoryPlaybookReuseGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_id=event_context.event_id,
        team_id=category_playbook.team_id,
        specialist_id=category_playbook.specialist_id,
        category_id=event_context.category_id,
        playbook_id=category_playbook.playbook_id,
        gate_status=gate_status,
        event_archetype_match_score=event_archetype_match_score,
        calibration_quality_score=category_playbook.calibration_quality_score,
        outcome_sample_size=category_playbook.outcome_sample_size,
        outcome_sample_size_score=outcome_sample_size_score,
        required_source_family_count=required_source_family_count,
        matched_source_family_count=matched_source_family_count,
        matched_source_families=matched_source_families,
        source_family_match_score=source_family_match_score,
        resolution_rule_match_score=resolution_rule_match_score,
        recency_age_days=recency_age_days,
        recency_score=recency_score,
        reuse_score=reuse_score,
        reason_codes=_report_reason_codes(
            gate_status=gate_status,
            event_archetype_match_score=event_archetype_match_score,
            calibration_quality_score=category_playbook.calibration_quality_score,
            outcome_sample_size=category_playbook.outcome_sample_size,
            source_family_match_score=source_family_match_score,
            resolution_rule_match_score=resolution_rule_match_score,
            recency_age_days=recency_age_days,
            config=config,
        ),
    )


def team_specialist_category_playbook_reuse_gate_v2_payload(
    report: TeamSpecialistCategoryPlaybookReuseGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistCategoryPlaybookReuseGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _report_digest(report):
            raise ValueError("derived_validation_digest must match report fields")
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamSpecialistCategoryPlaybookReuseGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _validate_config(config: TeamSpecialistCategoryPlaybookReuseGateV2Config) -> None:
    total = _ratio_sum(
        (
            config.event_archetype_match_weight,
            config.calibration_quality_weight,
            config.outcome_sample_size_weight,
            config.source_family_match_weight,
            config.resolution_rule_match_weight,
            config.recency_weight,
        ),
    )
    if total != ONE.quantize(RATIO_QUANTUM):
        raise ValueError("reuse gate weights must sum to 1.000000")
    if config.watch_score_floor > config.reuse_score_floor:
        raise ValueError("watch_score_floor must not exceed reuse_score_floor")
    if config.min_watch_calibration_quality > config.min_reuse_calibration_quality:
        raise ValueError(
            "min_watch_calibration_quality must not exceed "
            "min_reuse_calibration_quality",
        )
    if config.min_watch_outcome_sample_size > config.min_reuse_outcome_sample_size:
        raise ValueError(
            "min_watch_outcome_sample_size must not exceed "
            "min_reuse_outcome_sample_size",
        )
    if (
        config.min_watch_source_family_match_score
        > config.min_reuse_source_family_match_score
    ):
        raise ValueError(
            "min_watch_source_family_match_score must not exceed "
            "min_reuse_source_family_match_score",
        )
    if config.max_reuse_playbook_age_days > config.max_watch_playbook_age_days:
        raise ValueError(
            "max_reuse_playbook_age_days must not exceed max_watch_playbook_age_days",
        )


def _validate_report(report: TeamSpecialistCategoryPlaybookReuseGateV2Report) -> None:
    if report.event_archetype_match_score not in (
        ZERO.quantize(RATIO_QUANTUM),
        ONE.quantize(RATIO_QUANTUM),
    ):
        raise ValueError("event_archetype_match_score must be binary")
    if report.resolution_rule_match_score not in (
        ZERO.quantize(RATIO_QUANTUM),
        ONE.quantize(RATIO_QUANTUM),
    ):
        raise ValueError("resolution_rule_match_score must be binary")
    if report.required_source_family_count <= ZERO:
        raise ValueError("required_source_family_count must be positive")
    if report.matched_source_family_count > report.required_source_family_count:
        raise ValueError("matched_source_family_count must not exceed required")
    if report.matched_source_family_count != _count(len(report.matched_source_families)):
        raise ValueError("matched_source_family_count must match matched_source_families")
    if report.source_family_match_score != _count_ratio(
        report.matched_source_family_count,
        report.required_source_family_count,
    ):
        raise ValueError("source_family_match_score must match source counts")
    status_reason = f"team_specialist_category_playbook_reuse_{report.gate_status}"
    if status_reason not in report.reason_codes:
        raise ValueError("gate_status reason must be present")


def _report_reason_codes(
    *,
    gate_status: str,
    event_archetype_match_score: Decimal,
    calibration_quality_score: Decimal,
    outcome_sample_size: Decimal,
    source_family_match_score: Decimal,
    resolution_rule_match_score: Decimal,
    recency_age_days: Decimal,
    config: TeamSpecialistCategoryPlaybookReuseGateV2Config,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if event_archetype_match_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_category_playbook_reuse_event_archetype_match")
    else:
        reason_codes.add("team_specialist_category_playbook_reuse_event_archetype_gap")
    if calibration_quality_score >= config.min_reuse_calibration_quality:
        reason_codes.add("team_specialist_category_playbook_reuse_calibration_strong")
    elif calibration_quality_score >= config.min_watch_calibration_quality:
        reason_codes.add("team_specialist_category_playbook_reuse_calibration_watch")
    else:
        reason_codes.add("team_specialist_category_playbook_reuse_calibration_weak")
    if outcome_sample_size >= config.min_reuse_outcome_sample_size:
        reason_codes.add("team_specialist_category_playbook_reuse_outcome_sample_full")
    elif outcome_sample_size >= config.min_watch_outcome_sample_size:
        reason_codes.add("team_specialist_category_playbook_reuse_outcome_sample_watch")
    else:
        reason_codes.add("team_specialist_category_playbook_reuse_outcome_sample_thin")
    if source_family_match_score >= config.min_reuse_source_family_match_score:
        reason_codes.add("team_specialist_category_playbook_reuse_source_family_match")
    elif source_family_match_score >= config.min_watch_source_family_match_score:
        reason_codes.add("team_specialist_category_playbook_reuse_source_family_partial")
    else:
        reason_codes.add("team_specialist_category_playbook_reuse_source_family_gap")
    if resolution_rule_match_score == ONE.quantize(RATIO_QUANTUM):
        reason_codes.add("team_specialist_category_playbook_reuse_resolution_rule_match")
    else:
        reason_codes.add("team_specialist_category_playbook_reuse_resolution_rule_gap")
    if recency_age_days <= config.max_reuse_playbook_age_days:
        reason_codes.add("team_specialist_category_playbook_reuse_recent")
    elif recency_age_days <= config.max_watch_playbook_age_days:
        reason_codes.add("team_specialist_category_playbook_reuse_recency_watch")
    else:
        reason_codes.add("team_specialist_category_playbook_reuse_stale")
    reason_codes.add(f"team_specialist_category_playbook_reuse_{gate_status}")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _gate_status(
    *,
    event_archetype_match_score: Decimal,
    calibration_quality_score: Decimal,
    outcome_sample_size: Decimal,
    source_family_match_score: Decimal,
    resolution_rule_match_score: Decimal,
    recency_age_days: Decimal,
    reuse_score: Decimal,
    config: TeamSpecialistCategoryPlaybookReuseGateV2Config,
) -> str:
    if (
        event_archetype_match_score == ZERO.quantize(RATIO_QUANTUM)
        or resolution_rule_match_score == ZERO.quantize(RATIO_QUANTUM)
    ):
        return "skip"
    if (
        reuse_score >= config.reuse_score_floor
        and calibration_quality_score >= config.min_reuse_calibration_quality
        and outcome_sample_size >= config.min_reuse_outcome_sample_size
        and source_family_match_score >= config.min_reuse_source_family_match_score
        and recency_age_days <= config.max_reuse_playbook_age_days
    ):
        return "reuse"
    if (
        reuse_score >= config.watch_score_floor
        and calibration_quality_score >= config.min_watch_calibration_quality
        and outcome_sample_size >= config.min_watch_outcome_sample_size
        and source_family_match_score >= config.min_watch_source_family_match_score
        and recency_age_days <= config.max_watch_playbook_age_days
    ):
        return "watch"
    return "skip"


def _reuse_score(
    *,
    event_archetype_match_score: Decimal,
    calibration_quality_score: Decimal,
    outcome_sample_size_score: Decimal,
    source_family_match_score: Decimal,
    resolution_rule_match_score: Decimal,
    recency_score: Decimal,
    config: TeamSpecialistCategoryPlaybookReuseGateV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            event_archetype_match_score * config.event_archetype_match_weight
            + calibration_quality_score * config.calibration_quality_weight
            + outcome_sample_size_score * config.outcome_sample_size_weight
            + source_family_match_score * config.source_family_match_weight
            + resolution_rule_match_score * config.resolution_rule_match_weight
            + recency_score * config.recency_weight,
        )


def _recency_score(
    recency_age_days: Decimal,
    config: TeamSpecialistCategoryPlaybookReuseGateV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - recency_age_days / config.max_watch_playbook_age_days)


def _age_days(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    with localcontext(DECIMAL_CONTEXT):
        age_days = ((seconds + microseconds) / SECONDS_PER_DAY).quantize(RATIO_QUANTUM)
    if age_days < ZERO:
        raise ValueError("recency_age_days must be >= 0.000000")
    return age_days


def _binary_score(value: bool) -> Decimal:
    if value:
        return ONE.quantize(RATIO_QUANTUM)
    return ZERO.quantize(RATIO_QUANTUM)


def _count_ratio(value: Decimal, limit: Decimal) -> Decimal:
    if limit <= ZERO:
        raise ValueError("ratio limit must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / limit)


def _ratio_sum(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = value.quantize(RATIO_QUANTUM)
    if normalized < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if normalized > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


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


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(RATIO_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


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
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
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


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be reuse, watch, or skip")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError("unsafe public payload")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_digest(report: TeamSpecialistCategoryPlaybookReuseGateV2Report) -> str:
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
        return format(value, "f")
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
        return format(value, "f")
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
    if type(payload) is str:
        _reject_unsafe_text(payload)
        return
    if type(payload) is float or type(payload) is int:
        raise ValueError(f"unsafe public payload in {label}")
    raise ValueError(f"unsafe public payload in {label}")


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if digest is None:
        return
    _require_digest("derived_validation_digest", digest)
    if _digest_public(payload) != digest:
        raise ValueError("derived_validation_digest must match report fields")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CATEGORY_PLAYBOOK_REUSE_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistCategoryPlaybookReuseGateV2Config",
    "TeamSpecialistCategoryPlaybookReuseGateV2Context",
    "TeamSpecialistCategoryPlaybookReuseGateV2Playbook",
    "TeamSpecialistCategoryPlaybookReuseGateV2Report",
    "build_team_specialist_category_playbook_reuse_gate_v2",
    "team_specialist_category_playbook_reuse_gate_v2_payload",
)
