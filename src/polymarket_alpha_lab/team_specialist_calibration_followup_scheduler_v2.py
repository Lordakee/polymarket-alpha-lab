"""Readonly Decimal scheduler for specialist calibration followups."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CALIBRATION_FOLLOWUP_SCHEDULER_V2_CONFIG_VERSION = (
    "team-specialist-calibration-followup-scheduler-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

FOLLOWUP_STATUSES = ("urgent", "watch", "routine")
ROW_REASON_CODES = (
    "team_specialist_calibration_followup_urgent",
    "team_specialist_calibration_followup_watch",
    "team_specialist_calibration_followup_routine",
    "recent_forecast_miss_severity_high",
    "recent_forecast_miss_severity_watch",
    "recent_forecast_miss_severity_low",
    "domain_calibration_decay_high",
    "domain_calibration_decay_watch",
    "domain_calibration_decay_low",
    "stale_playbook_risk_high",
    "stale_playbook_risk_watch",
    "stale_playbook_risk_low",
    "source_quality_failure_rate_high",
    "source_quality_failure_rate_watch",
    "source_quality_failure_rate_low",
    "unresolved_postmortem_pressure_high",
    "unresolved_postmortem_pressure_watch",
    "unresolved_postmortem_pressure_low",
    "upcoming_event_load_high",
    "upcoming_event_load_watch",
    "upcoming_event_load_low",
)
REPORT_REASON_CODES = (
    "urgent_specialist_calibration_followups_present",
    "watch_specialist_calibration_followups_present",
    "routine_specialist_calibration_followups_present",
    "team_specialist_calibration_followup_scheduler_empty",
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
    "DEFAULT_TEAM_SPECIALIST_CALIBRATION_FOLLOWUP_SCHEDULER_V2_CONFIG_VERSION",
    "TeamSpecialistCalibrationFollowupSchedulerV2Config",
    "TeamSpecialistCalibrationFollowupMemoryV2Input",
    "TeamSpecialistCalibrationFollowupSchedulerV2Row",
    "TeamSpecialistCalibrationFollowupSchedulerV2Report",
    "build_team_specialist_calibration_followup_scheduler_v2",
)


@dataclass(frozen=True)
class TeamSpecialistCalibrationFollowupSchedulerV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CALIBRATION_FOLLOWUP_SCHEDULER_V2_CONFIG_VERSION
    )
    recent_forecast_miss_severity_weight: Decimal = Decimal("0.260000")
    domain_calibration_decay_weight: Decimal = Decimal("0.190000")
    stale_playbook_risk_weight: Decimal = Decimal("0.170000")
    source_quality_failure_rate_weight: Decimal = Decimal("0.150000")
    unresolved_postmortem_pressure_weight: Decimal = Decimal("0.130000")
    upcoming_event_load_weight: Decimal = Decimal("0.100000")
    max_domain_calibration_age_seconds: Decimal = Decimal("2592000.000000")
    max_unresolved_postmortem_count: Decimal = Decimal("4")
    max_upcoming_event_count: Decimal = Decimal("8")
    urgent_priority_floor: Decimal = Decimal("0.700000")
    watch_priority_floor: Decimal = Decimal("0.400000")
    urgent_followup_due_after_seconds: Decimal = Decimal("86400.000000")
    watch_followup_due_after_seconds: Decimal = Decimal("259200.000000")
    routine_followup_due_after_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistCalibrationFollowupSchedulerV2Config "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "recent_forecast_miss_severity_weight",
            "domain_calibration_decay_weight",
            "stale_playbook_risk_weight",
            "source_quality_failure_rate_weight",
            "unresolved_postmortem_pressure_weight",
            "upcoming_event_load_weight",
            "urgent_priority_floor",
            "watch_priority_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_domain_calibration_age_seconds",
            "urgent_followup_due_after_seconds",
            "watch_followup_due_after_seconds",
            "routine_followup_due_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_unresolved_postmortem_count",
            "max_upcoming_event_count",
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
        _require_hard_flags("TeamSpecialistCalibrationFollowupSchedulerV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFollowupSchedulerV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFollowupMemoryV2Input:
    team_id: str
    specialist_id: str
    domain_id: str
    recent_forecast_miss_severity: Decimal
    domain_calibration_age_seconds: Decimal
    stale_playbook_risk: Decimal
    source_quality_failure_rate: Decimal
    unresolved_postmortem_count: Decimal
    upcoming_event_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistCalibrationFollowupMemoryV2Input "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_forecast_miss_severity",
            "stale_playbook_risk",
            "source_quality_failure_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_calibration_age_seconds",
            _normalize_nonnegative_seconds(
                "domain_calibration_age_seconds",
                self.domain_calibration_age_seconds,
            ),
        )
        for field_name in ("unresolved_postmortem_count", "upcoming_event_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("TeamSpecialistCalibrationFollowupMemoryV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFollowupMemoryV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFollowupSchedulerV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    domain_id: str
    recent_forecast_miss_severity: Decimal
    domain_calibration_age_seconds: Decimal
    domain_calibration_decay_score: Decimal
    stale_playbook_risk: Decimal
    source_quality_failure_rate: Decimal
    unresolved_postmortem_count: Decimal
    unresolved_postmortem_pressure_score: Decimal
    upcoming_event_count: Decimal
    upcoming_event_load_score: Decimal
    followup_priority_score: Decimal
    followup_status: str
    scheduled_followup_due_at: datetime
    scheduled_followup_lag_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistCalibrationFollowupSchedulerV2Row "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("team_id", "specialist_id", "domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_forecast_miss_severity",
            "domain_calibration_decay_score",
            "stale_playbook_risk",
            "source_quality_failure_rate",
            "unresolved_postmortem_pressure_score",
            "upcoming_event_load_score",
            "followup_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_calibration_age_seconds",
            "scheduled_followup_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("unresolved_postmortem_count", "upcoming_event_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_followup_status("followup_status", self.followup_status)
        object.__setattr__(
            self,
            "scheduled_followup_due_at",
            _as_utc("scheduled_followup_due_at", self.scheduled_followup_due_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistCalibrationFollowupSchedulerV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFollowupSchedulerV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFollowupSchedulerV2Report:
    generated_at: datetime
    config_version: str
    schedule_status: str
    specialist_count: Decimal
    urgent_followup_count: Decimal
    watch_followup_count: Decimal
    routine_followup_count: Decimal
    average_followup_priority_score: Decimal
    top_followup_priority_score: Decimal
    bottom_followup_priority_score: Decimal
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamSpecialistCalibrationFollowupSchedulerV2Report "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_followup_status("schedule_status", self.schedule_status)
        for field_name in (
            "specialist_count",
            "urgent_followup_count",
            "watch_followup_count",
            "routine_followup_count",
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
            "average_followup_priority_score",
            "top_followup_priority_score",
            "bottom_followup_priority_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistCalibrationFollowupSchedulerV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFollowupSchedulerV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFollowupSchedulerV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_calibration_followup_scheduler_v2(
    team_memories: object,
    *,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
    generated_at: datetime,
) -> TeamSpecialistCalibrationFollowupSchedulerV2Report:
    if type(config) is not TeamSpecialistCalibrationFollowupSchedulerV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCalibrationFollowupSchedulerV2Config",
        )
    _require_hard_flags("TeamSpecialistCalibrationFollowupSchedulerV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    memories = _normalize_team_memories(team_memories)
    rows = tuple(
        _row_for_memory(
            rank=index,
            memory=memory,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, memory in enumerate(_sorted_memories(memories, config), start=1)
    )
    status = _schedule_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "schedule_status": status,
        "specialist_count": _count(len(rows)),
        "urgent_followup_count": _status_count(rows, "urgent"),
        "watch_followup_count": _status_count(rows, "watch"),
        "routine_followup_count": _status_count(rows, "routine"),
        "average_followup_priority_score": _average_priority(rows),
        "top_followup_priority_score": _top_priority(rows),
        "bottom_followup_priority_score": _bottom_priority(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCalibrationFollowupSchedulerV2Report(**values)


def _sorted_memories(
    memories: tuple[TeamSpecialistCalibrationFollowupMemoryV2Input, ...],
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> tuple[TeamSpecialistCalibrationFollowupMemoryV2Input, ...]:
    return tuple(
        sorted(
            memories,
            key=lambda item: (
                -_priority_score(item, config),
                item.team_id,
                item.specialist_id,
                item.domain_id,
            ),
        ),
    )


def _row_for_memory(
    *,
    rank: int,
    memory: TeamSpecialistCalibrationFollowupMemoryV2Input,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
    generated_at: datetime,
) -> TeamSpecialistCalibrationFollowupSchedulerV2Row:
    priority = _priority_score(memory, config)
    status = _followup_status(priority, config)
    lag_seconds = _lag_seconds_for_status(status, config)
    return TeamSpecialistCalibrationFollowupSchedulerV2Row(
        rank=_count(rank),
        team_id=memory.team_id,
        specialist_id=memory.specialist_id,
        domain_id=memory.domain_id,
        recent_forecast_miss_severity=memory.recent_forecast_miss_severity,
        domain_calibration_age_seconds=memory.domain_calibration_age_seconds,
        domain_calibration_decay_score=_domain_calibration_decay_score(
            memory.domain_calibration_age_seconds,
            config,
        ),
        stale_playbook_risk=memory.stale_playbook_risk,
        source_quality_failure_rate=memory.source_quality_failure_rate,
        unresolved_postmortem_count=memory.unresolved_postmortem_count,
        unresolved_postmortem_pressure_score=_count_pressure_score(
            memory.unresolved_postmortem_count,
            config.max_unresolved_postmortem_count,
        ),
        upcoming_event_count=memory.upcoming_event_count,
        upcoming_event_load_score=_count_pressure_score(
            memory.upcoming_event_count,
            config.max_upcoming_event_count,
        ),
        followup_priority_score=priority,
        followup_status=status,
        scheduled_followup_due_at=_datetime_after_lag(generated_at, lag_seconds),
        scheduled_followup_lag_seconds=lag_seconds,
        reason_codes=_row_reason_codes(memory, status, config),
    )


def _priority_score(
    memory: TeamSpecialistCalibrationFollowupMemoryV2Input,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            memory.recent_forecast_miss_severity
            * config.recent_forecast_miss_severity_weight
            + _domain_calibration_decay_score(
                memory.domain_calibration_age_seconds,
                config,
            )
            * config.domain_calibration_decay_weight
            + memory.stale_playbook_risk * config.stale_playbook_risk_weight
            + memory.source_quality_failure_rate
            * config.source_quality_failure_rate_weight
            + _count_pressure_score(
                memory.unresolved_postmortem_count,
                config.max_unresolved_postmortem_count,
            )
            * config.unresolved_postmortem_pressure_weight
            + _count_pressure_score(
                memory.upcoming_event_count,
                config.max_upcoming_event_count,
            )
            * config.upcoming_event_load_weight
        )
        return _clamp_ratio(value)


def _domain_calibration_decay_score(
    age_seconds: Decimal,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(age_seconds / config.max_domain_calibration_age_seconds)


def _count_pressure_score(count: Decimal, maximum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(count / maximum)


def _followup_status(
    priority: Decimal,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> str:
    if priority >= config.urgent_priority_floor:
        return "urgent"
    if priority >= config.watch_priority_floor:
        return "watch"
    return "routine"


def _schedule_status(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
) -> str:
    if any(row.followup_status == "urgent" for row in rows):
        return "urgent"
    if any(row.followup_status == "watch" for row in rows):
        return "watch"
    return "routine"


def _lag_seconds_for_status(
    status: str,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> Decimal:
    if status == "urgent":
        return config.urgent_followup_due_after_seconds
    if status == "watch":
        return config.watch_followup_due_after_seconds
    return config.routine_followup_due_after_seconds


def _datetime_after_lag(value: datetime, lag_seconds: Decimal) -> datetime:
    seconds = int(lag_seconds)
    microseconds = int(
        ((lag_seconds - Decimal(seconds)) * MICROSECONDS_PER_SECOND).quantize(
            COUNT_QUANT,
        ),
    )
    return value + timedelta(seconds=seconds, microseconds=microseconds)


def _row_reason_codes(
    memory: TeamSpecialistCalibrationFollowupMemoryV2Input,
    status: str,
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> tuple[str, ...]:
    return (
        f"team_specialist_calibration_followup_{status}",
        _tier_reason(
            memory.recent_forecast_miss_severity,
            high=Decimal("0.700000"),
            watch=Decimal("0.300000"),
            high_reason="recent_forecast_miss_severity_high",
            watch_reason="recent_forecast_miss_severity_watch",
            low_reason="recent_forecast_miss_severity_low",
        ),
        _tier_reason(
            _domain_calibration_decay_score(memory.domain_calibration_age_seconds, config),
            high=Decimal("0.750000"),
            watch=Decimal("0.250000"),
            high_reason="domain_calibration_decay_high",
            watch_reason="domain_calibration_decay_watch",
            low_reason="domain_calibration_decay_low",
        ),
        _tier_reason(
            memory.stale_playbook_risk,
            high=Decimal("0.700000"),
            watch=Decimal("0.300000"),
            high_reason="stale_playbook_risk_high",
            watch_reason="stale_playbook_risk_watch",
            low_reason="stale_playbook_risk_low",
        ),
        _tier_reason(
            memory.source_quality_failure_rate,
            high=Decimal("0.500000"),
            watch=Decimal("0.200000"),
            high_reason="source_quality_failure_rate_high",
            watch_reason="source_quality_failure_rate_watch",
            low_reason="source_quality_failure_rate_low",
        ),
        _tier_reason(
            _count_pressure_score(
                memory.unresolved_postmortem_count,
                config.max_unresolved_postmortem_count,
            ),
            high=Decimal("0.750000"),
            watch=Decimal("0.250000"),
            high_reason="unresolved_postmortem_pressure_high",
            watch_reason="unresolved_postmortem_pressure_watch",
            low_reason="unresolved_postmortem_pressure_low",
        ),
        _tier_reason(
            _count_pressure_score(
                memory.upcoming_event_count,
                config.max_upcoming_event_count,
            ),
            high=Decimal("0.750000"),
            watch=Decimal("0.250000"),
            high_reason="upcoming_event_load_high",
            watch_reason="upcoming_event_load_watch",
            low_reason="upcoming_event_load_low",
        ),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_calibration_followup_scheduler_empty",)
    candidate_codes = {
        "urgent_specialist_calibration_followups_present": any(
            row.followup_status == "urgent" for row in rows
        ),
        "watch_specialist_calibration_followups_present": any(
            row.followup_status == "watch" for row in rows
        ),
        "routine_specialist_calibration_followups_present": any(
            row.followup_status == "routine" for row in rows
        ),
    }
    return tuple(
        code for code in REPORT_REASON_CODES[:-1] if candidate_codes.get(code, False)
    )


def _tier_reason(
    value: Decimal,
    *,
    high: Decimal,
    watch: Decimal,
    high_reason: str,
    watch_reason: str,
    low_reason: str,
) -> str:
    if value >= high:
        return high_reason
    if value >= watch:
        return watch_reason
    return low_reason


def _status_count(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.followup_status == status))


def _average_priority(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.followup_priority_score for row in rows) / Decimal(len(rows)),
        )


def _top_priority(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.followup_priority_score for row in rows)


def _bottom_priority(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.followup_priority_score for row in rows)


def _normalize_team_memories(
    value: object,
) -> tuple[TeamSpecialistCalibrationFollowupMemoryV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("team_memories must be an iterable")
    memories = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for item in memories:
        if type(item) is not TeamSpecialistCalibrationFollowupMemoryV2Input:
            raise ValueError(
                "team memory items must be "
                "TeamSpecialistCalibrationFollowupMemoryV2Input",
            )
        _require_hard_flags("TeamSpecialistCalibrationFollowupMemoryV2Input", item)
        key = (item.team_id, item.specialist_id, item.domain_id)
        if key in seen_keys:
            raise ValueError("team_memories must not contain duplicate team/specialist/domain")
        seen_keys.add(key)
    return memories


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_keys: set[tuple[str, str, str]] = set()
    for row in value:
        if type(row) is not TeamSpecialistCalibrationFollowupSchedulerV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCalibrationFollowupSchedulerV2Row",
            )
        _require_hard_flags("TeamSpecialistCalibrationFollowupSchedulerV2Row", row)
        key = (row.team_id, row.specialist_id, row.domain_id)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate team/specialist/domain")
        seen_keys.add(key)
    return value


def _validate_config(
    config: TeamSpecialistCalibrationFollowupSchedulerV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.recent_forecast_miss_severity_weight
            + config.domain_calibration_decay_weight
            + config.stale_playbook_risk_weight
            + config.source_quality_failure_rate_weight
            + config.unresolved_postmortem_pressure_weight
            + config.upcoming_event_load_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("scheduler weights must sum to 1.000000")
    if config.watch_priority_floor > config.urgent_priority_floor:
        raise ValueError("watch_priority_floor must not exceed urgent_priority_floor")
    if (
        config.urgent_followup_due_after_seconds
        > config.watch_followup_due_after_seconds
        or config.watch_followup_due_after_seconds
        > config.routine_followup_due_after_seconds
    ):
        raise ValueError("followup due lags must be urgent <= watch <= routine")


def _validate_report_consistency(
    report: TeamSpecialistCalibrationFollowupSchedulerV2Report,
) -> None:
    rows = report.rows
    if report.specialist_count != _count(len(rows)):
        raise ValueError("specialist_count must match rows")
    if (
        report.urgent_followup_count != _status_count(rows, "urgent")
        or report.watch_followup_count != _status_count(rows, "watch")
        or report.routine_followup_count != _status_count(rows, "routine")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.urgent_followup_count
        + report.watch_followup_count
        + report.routine_followup_count
        != report.specialist_count
    ):
        raise ValueError("status counts must sum to specialist_count")
    _validate_rows_sorted(rows)
    if report.schedule_status != _schedule_status(rows):
        raise ValueError("schedule_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_followup_priority_score != _average_priority(rows):
        raise ValueError("average_followup_priority_score must match rows")
    if report.top_followup_priority_score != _top_priority(rows):
        raise ValueError("top_followup_priority_score must match rows")
    if report.bottom_followup_priority_score != _bottom_priority(rows):
        raise ValueError("bottom_followup_priority_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCalibrationFollowupSchedulerV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.followup_priority_score,
                row.team_id,
                row.specialist_id,
                row.domain_id,
            ),
        ),
    )
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by priority and rank")


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


def _require_followup_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in FOLLOWUP_STATUSES:
        raise ValueError(f"{field_name} must be urgent, watch, or routine")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
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


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SECONDS_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_seconds(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


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


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


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
