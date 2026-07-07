"""Readonly Decimal coaching report for specialist research quality memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_RESEARCH_QUALITY_COACH_V2_CONFIG_VERSION = (
    "team-specialist-research-quality-coach-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

COACH_STATUSES = ("pass", "watch", "blocked")
COACHING_ACTIONS = (
    "refresh_playbook",
    "expand_source_families",
    "tighten_contradiction_checks",
    "review_resolution_rules",
    "close_postmortem_actions",
    "triage_upcoming_event_load",
    "recalibrate_probability_ranges",
)
ROW_REASON_CODES = (
    "team_specialist_research_quality_pass",
    "team_specialist_research_quality_watch",
    "team_specialist_research_quality_blocked",
    "calibration_miss_low",
    "calibration_miss_watch",
    "calibration_miss_high",
    "source_family_gaps_clear",
    "source_family_gaps_watch",
    "source_family_gaps_high",
    "playbook_recent",
    "playbook_stale_watch",
    "playbook_stale_high",
    "contradiction_misses_clear",
    "contradiction_misses_watch",
    "contradiction_misses_high",
    "resolution_rule_errors_clear",
    "resolution_rule_errors_watch",
    "resolution_rule_errors_high",
    "postmortem_actions_recent",
    "postmortem_actions_watch",
    "postmortem_actions_overdue",
    "upcoming_event_load_low",
    "upcoming_event_load_watch",
    "upcoming_event_load_high",
)
REPORT_REASON_CODES = (
    "team_specialist_research_quality_coach_passed",
    "team_specialist_research_quality_coach_watch_rows",
    "team_specialist_research_quality_coach_blocked_rows",
    "team_specialist_research_quality_coach_empty",
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
    "DEFAULT_TEAM_SPECIALIST_RESEARCH_QUALITY_COACH_V2_CONFIG_VERSION",
    "TeamSpecialistResearchQualityCoachV2Config",
    "TeamSpecialistResearchQualityMemoryV2Input",
    "TeamSpecialistResearchQualityCoachV2Row",
    "TeamSpecialistResearchQualityCoachV2Report",
    "build_team_specialist_research_quality_coach_v2",
)


@dataclass(frozen=True)
class TeamSpecialistResearchQualityCoachV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_RESEARCH_QUALITY_COACH_V2_CONFIG_VERSION
    calibration_miss_weight: Decimal = Decimal("0.300000")
    source_family_gap_weight: Decimal = Decimal("0.147510")
    stale_playbook_weight: Decimal = Decimal("0.143328")
    contradiction_miss_weight: Decimal = Decimal("0.184162")
    resolution_rule_error_weight: Decimal = Decimal("0.100000")
    postmortem_action_age_weight: Decimal = Decimal("0.075000")
    upcoming_event_load_weight: Decimal = Decimal("0.050000")
    max_source_family_gap_count: Decimal = Decimal("4")
    stale_playbook_block_days: Decimal = Decimal("60")
    max_contradiction_miss_count: Decimal = Decimal("3")
    max_resolution_rule_error_count: Decimal = Decimal("2")
    postmortem_action_block_days: Decimal = Decimal("60")
    high_upcoming_event_load_count: Decimal = Decimal("8")
    pass_risk_ceiling: Decimal = Decimal("0.150000")
    watch_risk_ceiling: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "calibration_miss_weight",
            "source_family_gap_weight",
            "stale_playbook_weight",
            "contradiction_miss_weight",
            "resolution_rule_error_weight",
            "postmortem_action_age_weight",
            "upcoming_event_load_weight",
            "pass_risk_ceiling",
            "watch_risk_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_source_family_gap_count",
            "stale_playbook_block_days",
            "max_contradiction_miss_count",
            "max_resolution_rule_error_count",
            "postmortem_action_block_days",
            "high_upcoming_event_load_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistResearchQualityCoachV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResearchQualityCoachV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistResearchQualityMemoryV2Input:
    team_id: str
    specialist_id: str
    research_lane: str
    calibration_miss_severity: Decimal
    source_family_gap_count: Decimal
    stale_playbook_age_days: Decimal
    contradiction_miss_count: Decimal
    resolution_rule_error_count: Decimal
    oldest_postmortem_action_age_days: Decimal
    upcoming_event_load: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "research_lane"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_miss_severity",
            _normalize_ratio(
                "calibration_miss_severity",
                self.calibration_miss_severity,
            ),
        )
        for field_name in (
            "source_family_gap_count",
            "contradiction_miss_count",
            "resolution_rule_error_count",
            "upcoming_event_load",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "stale_playbook_age_days",
            "oldest_postmortem_action_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("TeamSpecialistResearchQualityMemoryV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResearchQualityMemoryV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistResearchQualityCoachV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    research_lane: str
    calibration_miss_severity: Decimal
    calibration_miss_risk: Decimal
    source_family_gap_count: Decimal
    source_family_gap_risk: Decimal
    stale_playbook_age_days: Decimal
    stale_playbook_risk: Decimal
    contradiction_miss_count: Decimal
    contradiction_miss_risk: Decimal
    resolution_rule_error_count: Decimal
    resolution_rule_error_risk: Decimal
    oldest_postmortem_action_age_days: Decimal
    postmortem_action_age_risk: Decimal
    upcoming_event_load: Decimal
    upcoming_event_load_risk: Decimal
    quality_risk_score: Decimal
    coaching_status: str
    recommended_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("team_id", "specialist_id", "research_lane"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_miss_severity",
            "calibration_miss_risk",
            "source_family_gap_risk",
            "stale_playbook_risk",
            "contradiction_miss_risk",
            "resolution_rule_error_risk",
            "postmortem_action_age_risk",
            "upcoming_event_load_risk",
            "quality_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_gap_count",
            "contradiction_miss_count",
            "resolution_rule_error_count",
            "upcoming_event_load",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "stale_playbook_age_days",
            "oldest_postmortem_action_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_coach_status("coaching_status", self.coaching_status)
        object.__setattr__(
            self,
            "recommended_actions",
            _normalize_known_strings(
                "recommended_actions",
                self.recommended_actions,
                COACHING_ACTIONS,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_known_strings(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_hard_flags("TeamSpecialistResearchQualityCoachV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResearchQualityCoachV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistResearchQualityCoachV2Report:
    generated_at: datetime
    config_version: str
    coach_status: str
    memory_count: Decimal
    pass_memory_count: Decimal
    watch_memory_count: Decimal
    blocked_memory_count: Decimal
    average_quality_risk_score: Decimal
    top_quality_risk_score: Decimal
    bottom_quality_risk_score: Decimal
    rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_coach_status("coach_status", self.coach_status)
        for field_name in (
            "memory_count",
            "pass_memory_count",
            "watch_memory_count",
            "blocked_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_quality_risk_score",
            "top_quality_risk_score",
            "bottom_quality_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_known_strings(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistResearchQualityCoachV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResearchQualityCoachV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistResearchQualityCoachV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_research_quality_coach_v2(
    quality_memories: object,
    *,
    config: TeamSpecialistResearchQualityCoachV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistResearchQualityCoachV2Report:
    if config is None:
        config = TeamSpecialistResearchQualityCoachV2Config()
    if type(config) is not TeamSpecialistResearchQualityCoachV2Config:
        raise ValueError(
            "config must be a TeamSpecialistResearchQualityCoachV2Config",
        )
    _require_hard_flags("TeamSpecialistResearchQualityCoachV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    memories = _normalize_quality_memories(quality_memories)

    rows = tuple(
        _row_for_memory(rank=index, memory=item, config=config)
        for index, item in enumerate(_sorted_memories(memories, config), start=1)
    )
    status = _coach_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "coach_status": status,
        "memory_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_memory_count": _status_count(rows, "pass"),
        "watch_memory_count": _status_count(rows, "watch"),
        "blocked_memory_count": _status_count(rows, "blocked"),
        "average_quality_risk_score": _average_risk(rows),
        "top_quality_risk_score": _top_risk(rows),
        "bottom_quality_risk_score": _bottom_risk(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistResearchQualityCoachV2Report(**values)


def _sorted_memories(
    memories: tuple[TeamSpecialistResearchQualityMemoryV2Input, ...],
    config: TeamSpecialistResearchQualityCoachV2Config,
) -> tuple[TeamSpecialistResearchQualityMemoryV2Input, ...]:
    return tuple(
        sorted(
            memories,
            key=lambda item: (
                -_quality_risk_score(item, config),
                item.team_id,
                item.specialist_id,
                item.research_lane,
            ),
        ),
    )


def _row_for_memory(
    *,
    rank: int,
    memory: TeamSpecialistResearchQualityMemoryV2Input,
    config: TeamSpecialistResearchQualityCoachV2Config,
) -> TeamSpecialistResearchQualityCoachV2Row:
    calibration_risk = memory.calibration_miss_severity
    source_risk = _count_risk(
        memory.source_family_gap_count,
        config.max_source_family_gap_count,
    )
    playbook_risk = _count_risk(
        memory.stale_playbook_age_days,
        config.stale_playbook_block_days,
    )
    contradiction_risk = _count_risk(
        memory.contradiction_miss_count,
        config.max_contradiction_miss_count,
    )
    rule_risk = _count_risk(
        memory.resolution_rule_error_count,
        config.max_resolution_rule_error_count,
    )
    postmortem_risk = _count_risk(
        memory.oldest_postmortem_action_age_days,
        config.postmortem_action_block_days,
    )
    event_risk = _count_risk(
        memory.upcoming_event_load,
        config.high_upcoming_event_load_count,
    )
    score = _quality_risk_score(memory, config)
    status = _row_status(score, config)
    return TeamSpecialistResearchQualityCoachV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=memory.team_id,
        specialist_id=memory.specialist_id,
        research_lane=memory.research_lane,
        calibration_miss_severity=memory.calibration_miss_severity,
        calibration_miss_risk=calibration_risk,
        source_family_gap_count=memory.source_family_gap_count,
        source_family_gap_risk=source_risk,
        stale_playbook_age_days=memory.stale_playbook_age_days,
        stale_playbook_risk=playbook_risk,
        contradiction_miss_count=memory.contradiction_miss_count,
        contradiction_miss_risk=contradiction_risk,
        resolution_rule_error_count=memory.resolution_rule_error_count,
        resolution_rule_error_risk=rule_risk,
        oldest_postmortem_action_age_days=memory.oldest_postmortem_action_age_days,
        postmortem_action_age_risk=postmortem_risk,
        upcoming_event_load=memory.upcoming_event_load,
        upcoming_event_load_risk=event_risk,
        quality_risk_score=score,
        coaching_status=status,
        recommended_actions=_recommended_actions(
            calibration_risk=calibration_risk,
            source_risk=source_risk,
            playbook_risk=playbook_risk,
            contradiction_risk=contradiction_risk,
            rule_risk=rule_risk,
            postmortem_risk=postmortem_risk,
            event_risk=event_risk,
        ),
        reason_codes=_row_reason_codes(
            status=status,
            calibration_risk=calibration_risk,
            source_risk=source_risk,
            playbook_risk=playbook_risk,
            contradiction_risk=contradiction_risk,
            rule_risk=rule_risk,
            postmortem_risk=postmortem_risk,
            event_risk=event_risk,
        ),
    )


def _quality_risk_score(
    memory: TeamSpecialistResearchQualityMemoryV2Input,
    config: TeamSpecialistResearchQualityCoachV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            memory.calibration_miss_severity * config.calibration_miss_weight
            + _count_risk(
                memory.source_family_gap_count,
                config.max_source_family_gap_count,
            )
            * config.source_family_gap_weight
            + _count_risk(
                memory.stale_playbook_age_days,
                config.stale_playbook_block_days,
            )
            * config.stale_playbook_weight
            + _count_risk(
                memory.contradiction_miss_count,
                config.max_contradiction_miss_count,
            )
            * config.contradiction_miss_weight
            + _count_risk(
                memory.resolution_rule_error_count,
                config.max_resolution_rule_error_count,
            )
            * config.resolution_rule_error_weight
            + _count_risk(
                memory.oldest_postmortem_action_age_days,
                config.postmortem_action_block_days,
            )
            * config.postmortem_action_age_weight
            + _count_risk(
                memory.upcoming_event_load,
                config.high_upcoming_event_load_count,
            )
            * config.upcoming_event_load_weight
        )
        return _clamp_ratio(score)


def _count_risk(value: Decimal, maximum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / maximum)


def _row_status(
    score: Decimal,
    config: TeamSpecialistResearchQualityCoachV2Config,
) -> str:
    if score <= config.pass_risk_ceiling:
        return "pass"
    if score <= config.watch_risk_ceiling:
        return "watch"
    return "blocked"


def _coach_status(rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.coaching_status == "blocked" for row in rows):
        return "blocked"
    if any(row.coaching_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_actions(
    *,
    calibration_risk: Decimal,
    source_risk: Decimal,
    playbook_risk: Decimal,
    contradiction_risk: Decimal,
    rule_risk: Decimal,
    postmortem_risk: Decimal,
    event_risk: Decimal,
) -> tuple[str, ...]:
    actions: list[str] = []
    if playbook_risk >= Decimal("0.500000"):
        actions.append("refresh_playbook")
    if source_risk >= Decimal("0.500000"):
        actions.append("expand_source_families")
    if contradiction_risk >= Decimal("0.333333"):
        actions.append("tighten_contradiction_checks")
    if rule_risk >= Decimal("0.500000"):
        actions.append("review_resolution_rules")
    if postmortem_risk >= Decimal("0.333333"):
        actions.append("close_postmortem_actions")
    if event_risk >= Decimal("0.500000"):
        actions.append("triage_upcoming_event_load")
    if calibration_risk >= Decimal("0.200000"):
        actions.append("recalibrate_probability_ranges")
    return tuple(actions)


def _row_reason_codes(
    *,
    status: str,
    calibration_risk: Decimal,
    source_risk: Decimal,
    playbook_risk: Decimal,
    contradiction_risk: Decimal,
    rule_risk: Decimal,
    postmortem_risk: Decimal,
    event_risk: Decimal,
) -> tuple[str, ...]:
    return (
        f"team_specialist_research_quality_{status}",
        _risk_reason(
            calibration_risk,
            watch=Decimal("0.120000"),
            high=Decimal("0.250000"),
            low_reason="calibration_miss_low",
            watch_reason="calibration_miss_watch",
            high_reason="calibration_miss_high",
        ),
        _risk_reason(
            source_risk,
            watch=Decimal("0.250000"),
            high=Decimal("0.500000"),
            low_reason="source_family_gaps_clear",
            watch_reason="source_family_gaps_watch",
            high_reason="source_family_gaps_high",
        ),
        _risk_reason(
            playbook_risk,
            watch=Decimal("0.250000"),
            high=Decimal("0.500000"),
            low_reason="playbook_recent",
            watch_reason="playbook_stale_watch",
            high_reason="playbook_stale_high",
        ),
        _risk_reason(
            contradiction_risk,
            watch=Decimal("0.333333"),
            high=Decimal("0.666667"),
            low_reason="contradiction_misses_clear",
            watch_reason="contradiction_misses_watch",
            high_reason="contradiction_misses_high",
        ),
        _risk_reason(
            rule_risk,
            watch=Decimal("0.500000"),
            high=Decimal("1.000000"),
            low_reason="resolution_rule_errors_clear",
            watch_reason="resolution_rule_errors_watch",
            high_reason="resolution_rule_errors_high",
        ),
        _risk_reason(
            postmortem_risk,
            watch=Decimal("0.333333"),
            high=Decimal("0.666667"),
            low_reason="postmortem_actions_recent",
            watch_reason="postmortem_actions_watch",
            high_reason="postmortem_actions_overdue",
        ),
        _risk_reason(
            event_risk,
            watch=Decimal("0.500000"),
            high=Decimal("0.750000"),
            low_reason="upcoming_event_load_low",
            watch_reason="upcoming_event_load_watch",
            high_reason="upcoming_event_load_high",
        ),
    )


def _risk_reason(
    value: Decimal,
    *,
    watch: Decimal,
    high: Decimal,
    low_reason: str,
    watch_reason: str,
    high_reason: str,
) -> str:
    if value >= high:
        return high_reason
    if value >= watch:
        return watch_reason
    return low_reason


def _report_reason_codes(
    rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_research_quality_coach_empty",)
    reasons: list[str] = []
    if any(row.coaching_status == "blocked" for row in rows):
        reasons.append("team_specialist_research_quality_coach_blocked_rows")
    if any(row.coaching_status == "watch" for row in rows):
        reasons.append("team_specialist_research_quality_coach_watch_rows")
    if not reasons and status == "pass":
        reasons.append("team_specialist_research_quality_coach_passed")
    return tuple(reasons)


def _status_count(
    rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.coaching_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_risk(rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.quality_risk_score for row in rows) / Decimal(len(rows)),
        )


def _top_risk(rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.quality_risk_score for row in rows)


def _bottom_risk(rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.quality_risk_score for row in rows)


def _normalize_quality_memories(
    value: object,
) -> tuple[TeamSpecialistResearchQualityMemoryV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("quality_memories must be an iterable")
    memories = tuple(value)
    for item in memories:
        if type(item) is not TeamSpecialistResearchQualityMemoryV2Input:
            raise ValueError(
                "quality memory items must be TeamSpecialistResearchQualityMemoryV2Input",
            )
        _require_hard_flags("TeamSpecialistResearchQualityMemoryV2Input", item)
    keys = tuple((item.team_id, item.specialist_id, item.research_lane) for item in memories)
    if len(set(keys)) != len(keys):
        raise ValueError("quality memory items must not contain duplicate team entries")
    return memories


def _normalize_rows(value: object) -> tuple[TeamSpecialistResearchQualityCoachV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistResearchQualityCoachV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistResearchQualityCoachV2Row",
            )
    return value


def _validate_config(config: TeamSpecialistResearchQualityCoachV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.calibration_miss_weight
            + config.source_family_gap_weight
            + config.stale_playbook_weight
            + config.contradiction_miss_weight
            + config.resolution_rule_error_weight
            + config.postmortem_action_age_weight
            + config.upcoming_event_load_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("coach weights must sum to 1.000000")
    if config.pass_risk_ceiling > config.watch_risk_ceiling:
        raise ValueError("pass_risk_ceiling must not exceed watch_risk_ceiling")


def _validate_row_consistency(row: TeamSpecialistResearchQualityCoachV2Row) -> None:
    if row.calibration_miss_risk != row.calibration_miss_severity:
        raise ValueError("calibration_miss_risk must match calibration_miss_severity")
    expected_actions = _recommended_actions(
        calibration_risk=row.calibration_miss_risk,
        source_risk=row.source_family_gap_risk,
        playbook_risk=row.stale_playbook_risk,
        contradiction_risk=row.contradiction_miss_risk,
        rule_risk=row.resolution_rule_error_risk,
        postmortem_risk=row.postmortem_action_age_risk,
        event_risk=row.upcoming_event_load_risk,
    )
    if row.recommended_actions != expected_actions:
        raise ValueError("recommended_actions must match row risks")
    expected_reasons = _row_reason_codes(
        status=row.coaching_status,
        calibration_risk=row.calibration_miss_risk,
        source_risk=row.source_family_gap_risk,
        playbook_risk=row.stale_playbook_risk,
        contradiction_risk=row.contradiction_miss_risk,
        rule_risk=row.resolution_rule_error_risk,
        postmortem_risk=row.postmortem_action_age_risk,
        event_risk=row.upcoming_event_load_risk,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row risks")


def _validate_report_consistency(report: TeamSpecialistResearchQualityCoachV2Report) -> None:
    rows = report.rows
    if report.memory_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("memory_count must match rows")
    if (
        report.pass_memory_count != _status_count(rows, "pass")
        or report.watch_memory_count != _status_count(rows, "watch")
        or report.blocked_memory_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_memory_count
        + report.watch_memory_count
        + report.blocked_memory_count
        != report.memory_count
    ):
        raise ValueError("status counts must sum to memory_count")
    _validate_rows_sorted(rows)
    expected_status = _coach_status(rows)
    if report.coach_status != expected_status:
        raise ValueError("coach_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.coach_status):
        raise ValueError("reason_codes must match coach_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_quality_risk_score != _average_risk(rows):
        raise ValueError("average_quality_risk_score must match rows")
    if report.top_quality_risk_score != _top_risk(rows):
        raise ValueError("top_quality_risk_score must match rows")
    if report.bottom_quality_risk_score != _bottom_risk(rows):
        raise ValueError("bottom_quality_risk_score must match rows")


def _validate_rows_sorted(rows: tuple[TeamSpecialistResearchQualityCoachV2Row, ...]) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.quality_risk_score,
                row.team_id,
                row.specialist_id,
                row.research_lane,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by quality risk and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_coach_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in COACH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_known_strings(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known values")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
