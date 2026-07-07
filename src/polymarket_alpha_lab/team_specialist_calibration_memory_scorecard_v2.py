"""Readonly Decimal scorecard for specialist team calibration memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CALIBRATION_MEMORY_SCORECARD_V2_CONFIG_VERSION = (
    "team-specialist-calibration-memory-scorecard-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MEMORY_STATUSES = ("pass", "watch", "blocked")
SCORECARD_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "team_specialist_memory_pass",
    "team_specialist_memory_watch",
    "team_specialist_memory_blocked",
    "domain_calibration_strong",
    "domain_calibration_watch",
    "domain_calibration_weak",
    "forecast_error_low",
    "forecast_error_watch",
    "forecast_error_high",
    "evidence_quality_strong",
    "evidence_quality_watch",
    "evidence_quality_weak",
    "source_diversity_strong",
    "source_diversity_watch",
    "source_diversity_weak",
    "stale_lessons_clear",
    "stale_lessons_watch",
    "stale_lessons_stale",
    "postmortem_actions_clear",
    "postmortem_actions_watch",
    "postmortem_actions_unresolved",
)
REPORT_REASON_CODES = (
    "team_specialist_memory_scorecard_passed",
    "team_specialist_memory_scorecard_watch_rows",
    "team_specialist_memory_scorecard_blocked_rows",
    "team_specialist_memory_scorecard_empty",
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
    "DEFAULT_TEAM_SPECIALIST_CALIBRATION_MEMORY_SCORECARD_V2_CONFIG_VERSION",
    "TeamSpecialistCalibrationMemoryScorecardV2Config",
    "TeamSpecialistCalibrationMemoryV2Input",
    "TeamSpecialistCalibrationMemoryScorecardV2Row",
    "TeamSpecialistCalibrationMemoryScorecardV2Report",
    "build_team_specialist_calibration_memory_scorecard_v2",
)


@dataclass(frozen=True)
class TeamSpecialistCalibrationMemoryScorecardV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CALIBRATION_MEMORY_SCORECARD_V2_CONFIG_VERSION
    )
    domain_calibration_weight: Decimal = Decimal("0.369643")
    recent_forecast_error_weight: Decimal = Decimal("0.210714")
    evidence_quality_weight: Decimal = Decimal("0.150000")
    source_diversity_weight: Decimal = Decimal("0.150000")
    stale_lessons_weight: Decimal = Decimal("0.076516")
    unresolved_postmortem_actions_weight: Decimal = Decimal("0.043127")
    max_stale_lesson_count: Decimal = Decimal("5")
    max_unresolved_postmortem_action_count: Decimal = Decimal("3")
    pass_score_floor: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.600000")
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
            "domain_calibration_weight",
            "recent_forecast_error_weight",
            "evidence_quality_weight",
            "source_diversity_weight",
            "stale_lessons_weight",
            "unresolved_postmortem_actions_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_stale_lesson_count",
            "max_unresolved_postmortem_action_count",
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
        _require_hard_flags("TeamSpecialistCalibrationMemoryScorecardV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationMemoryScorecardV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationMemoryV2Input:
    team_id: str
    domain_id: str
    domain_calibration_score: Decimal
    recent_forecast_error: Decimal
    evidence_quality_score: Decimal
    source_diversity_score: Decimal
    stale_lesson_count: Decimal
    unresolved_postmortem_action_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "domain_id",
            _require_non_empty_string("domain_id", self.domain_id),
        )
        for field_name in (
            "domain_calibration_score",
            "recent_forecast_error",
            "evidence_quality_score",
            "source_diversity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_lesson_count",
            "unresolved_postmortem_action_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("TeamSpecialistCalibrationMemoryV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationMemoryV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationMemoryScorecardV2Row:
    rank: Decimal
    team_id: str
    domain_id: str
    domain_calibration_score: Decimal
    recent_forecast_error: Decimal
    forecast_accuracy_score: Decimal
    evidence_quality_score: Decimal
    source_diversity_score: Decimal
    stale_lesson_count: Decimal
    stale_lesson_score: Decimal
    unresolved_postmortem_action_count: Decimal
    postmortem_action_score: Decimal
    calibration_memory_score: Decimal
    memory_status: str
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
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "domain_id",
            _require_non_empty_string("domain_id", self.domain_id),
        )
        for field_name in (
            "domain_calibration_score",
            "recent_forecast_error",
            "forecast_accuracy_score",
            "evidence_quality_score",
            "source_diversity_score",
            "stale_lesson_score",
            "postmortem_action_score",
            "calibration_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_lesson_count",
            "unresolved_postmortem_action_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_memory_status("memory_status", self.memory_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistCalibrationMemoryScorecardV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationMemoryScorecardV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistCalibrationMemoryScorecardV2Report:
    generated_at: datetime
    config_version: str
    scorecard_status: str
    team_count: Decimal
    pass_team_count: Decimal
    watch_team_count: Decimal
    blocked_team_count: Decimal
    average_calibration_memory_score: Decimal
    top_calibration_memory_score: Decimal
    bottom_calibration_memory_score: Decimal
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...]
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
        _require_scorecard_status("scorecard_status", self.scorecard_status)
        for field_name in (
            "team_count",
            "pass_team_count",
            "watch_team_count",
            "blocked_team_count",
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
            "average_calibration_memory_score",
            "top_calibration_memory_score",
            "bottom_calibration_memory_score",
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
        _require_hard_flags("TeamSpecialistCalibrationMemoryScorecardV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationMemoryScorecardV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationMemoryScorecardV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_calibration_memory_scorecard_v2(
    team_memories: object,
    *,
    config: TeamSpecialistCalibrationMemoryScorecardV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistCalibrationMemoryScorecardV2Report:
    if config is None:
        config = TeamSpecialistCalibrationMemoryScorecardV2Config()
    if type(config) is not TeamSpecialistCalibrationMemoryScorecardV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCalibrationMemoryScorecardV2Config",
        )
    _require_hard_flags("TeamSpecialistCalibrationMemoryScorecardV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    memories = _normalize_team_memories(team_memories)

    rows = tuple(
        _row_for_memory(rank=index, memory=item, config=config)
        for index, item in enumerate(_sorted_memories(memories, config), start=1)
    )
    status = _scorecard_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "scorecard_status": status,
        "team_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_team_count": _status_count(rows, "pass"),
        "watch_team_count": _status_count(rows, "watch"),
        "blocked_team_count": _status_count(rows, "blocked"),
        "average_calibration_memory_score": _average_score(rows),
        "top_calibration_memory_score": _top_score(rows),
        "bottom_calibration_memory_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCalibrationMemoryScorecardV2Report(**values)


def _sorted_memories(
    memories: tuple[TeamSpecialistCalibrationMemoryV2Input, ...],
    config: TeamSpecialistCalibrationMemoryScorecardV2Config,
) -> tuple[TeamSpecialistCalibrationMemoryV2Input, ...]:
    return tuple(
        sorted(
            memories,
            key=lambda item: (
                -_score_for_memory(item, config),
                item.team_id,
                item.domain_id,
            ),
        ),
    )


def _row_for_memory(
    *,
    rank: int,
    memory: TeamSpecialistCalibrationMemoryV2Input,
    config: TeamSpecialistCalibrationMemoryScorecardV2Config,
) -> TeamSpecialistCalibrationMemoryScorecardV2Row:
    score = _score_for_memory(memory, config)
    status = _memory_status(score, config)
    return TeamSpecialistCalibrationMemoryScorecardV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=memory.team_id,
        domain_id=memory.domain_id,
        domain_calibration_score=memory.domain_calibration_score,
        recent_forecast_error=memory.recent_forecast_error,
        forecast_accuracy_score=_forecast_accuracy_score(memory.recent_forecast_error),
        evidence_quality_score=memory.evidence_quality_score,
        source_diversity_score=memory.source_diversity_score,
        stale_lesson_count=memory.stale_lesson_count,
        stale_lesson_score=_count_health_score(
            memory.stale_lesson_count,
            config.max_stale_lesson_count,
        ),
        unresolved_postmortem_action_count=memory.unresolved_postmortem_action_count,
        postmortem_action_score=_count_health_score(
            memory.unresolved_postmortem_action_count,
            config.max_unresolved_postmortem_action_count,
        ),
        calibration_memory_score=score,
        memory_status=status,
        reason_codes=_row_reason_codes(memory, status, config),
    )


def _score_for_memory(
    memory: TeamSpecialistCalibrationMemoryV2Input,
    config: TeamSpecialistCalibrationMemoryScorecardV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            memory.domain_calibration_score * config.domain_calibration_weight
            + _forecast_accuracy_score(memory.recent_forecast_error)
            * config.recent_forecast_error_weight
            + memory.evidence_quality_score * config.evidence_quality_weight
            + memory.source_diversity_score * config.source_diversity_weight
            + _count_health_score(
                memory.stale_lesson_count,
                config.max_stale_lesson_count,
            )
            * config.stale_lessons_weight
            + _count_health_score(
                memory.unresolved_postmortem_action_count,
                config.max_unresolved_postmortem_action_count,
            )
            * config.unresolved_postmortem_actions_weight
        )
        return _clamp_ratio(score)


def _forecast_accuracy_score(recent_forecast_error: Decimal) -> Decimal:
    return _clamp_ratio(ONE - recent_forecast_error)


def _count_health_score(count: Decimal, maximum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - count / maximum)


def _memory_status(
    score: Decimal,
    config: TeamSpecialistCalibrationMemoryScorecardV2Config,
) -> str:
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _scorecard_status(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.memory_status == "blocked" for row in rows):
        return "blocked"
    if any(row.memory_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    memory: TeamSpecialistCalibrationMemoryV2Input,
    status: str,
    config: TeamSpecialistCalibrationMemoryScorecardV2Config,
) -> tuple[str, ...]:
    return (
        f"team_specialist_memory_{status}",
        _tier_reason(
            memory.domain_calibration_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="domain_calibration_strong",
            watch_reason="domain_calibration_watch",
            weak_reason="domain_calibration_weak",
        ),
        _forecast_error_reason(memory.recent_forecast_error),
        _tier_reason(
            memory.evidence_quality_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="evidence_quality_strong",
            watch_reason="evidence_quality_watch",
            weak_reason="evidence_quality_weak",
        ),
        _tier_reason(
            memory.source_diversity_score,
            strong=Decimal("0.700000"),
            watch=Decimal("0.500000"),
            strong_reason="source_diversity_strong",
            watch_reason="source_diversity_watch",
            weak_reason="source_diversity_weak",
        ),
        _count_reason(
            memory.stale_lesson_count,
            watch_floor=Decimal("1"),
            stale_floor=config.max_stale_lesson_count,
            clear_reason="stale_lessons_clear",
            watch_reason="stale_lessons_watch",
            stale_reason="stale_lessons_stale",
        ),
        _count_reason(
            memory.unresolved_postmortem_action_count,
            watch_floor=Decimal("1"),
            stale_floor=config.max_unresolved_postmortem_action_count,
            clear_reason="postmortem_actions_clear",
            watch_reason="postmortem_actions_watch",
            stale_reason="postmortem_actions_unresolved",
        ),
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_memory_scorecard_empty",)
    reasons: list[str] = []
    if any(row.memory_status == "blocked" for row in rows):
        reasons.append("team_specialist_memory_scorecard_blocked_rows")
    if any(row.memory_status == "watch" for row in rows):
        reasons.append("team_specialist_memory_scorecard_watch_rows")
    if not reasons and status == "pass":
        reasons.append("team_specialist_memory_scorecard_passed")
    return tuple(reasons)


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _forecast_error_reason(value: Decimal) -> str:
    if value <= Decimal("0.120000"):
        return "forecast_error_low"
    if value <= Decimal("0.250000"):
        return "forecast_error_watch"
    return "forecast_error_high"


def _count_reason(
    value: Decimal,
    *,
    watch_floor: Decimal,
    stale_floor: Decimal,
    clear_reason: str,
    watch_reason: str,
    stale_reason: str,
) -> str:
    if value < watch_floor:
        return clear_reason
    if value < stale_floor:
        return watch_reason
    return stale_reason


def _status_count(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.memory_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.calibration_memory_score for row in rows) / Decimal(len(rows)),
        )


def _top_score(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.calibration_memory_score for row in rows)


def _bottom_score(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.calibration_memory_score for row in rows)


def _normalize_team_memories(
    value: object,
) -> tuple[TeamSpecialistCalibrationMemoryV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("team_memories must be an iterable")
    memories = tuple(value)
    for item in memories:
        if type(item) is not TeamSpecialistCalibrationMemoryV2Input:
            raise ValueError(
                "team memory items must be TeamSpecialistCalibrationMemoryV2Input",
            )
        _require_hard_flags("TeamSpecialistCalibrationMemoryV2Input", item)
    keys = tuple((item.team_id, item.domain_id) for item in memories)
    if len(set(keys)) != len(keys):
        raise ValueError("team memory items must not contain duplicate team/domain keys")
    return memories


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistCalibrationMemoryScorecardV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCalibrationMemoryScorecardV2Row",
            )
    return value


def _validate_config(
    config: TeamSpecialistCalibrationMemoryScorecardV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.domain_calibration_weight
            + config.recent_forecast_error_weight
            + config.evidence_quality_weight
            + config.source_diversity_weight
            + config.stale_lessons_weight
            + config.unresolved_postmortem_actions_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("scorecard weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_row_consistency(
    row: TeamSpecialistCalibrationMemoryScorecardV2Row,
) -> None:
    if row.forecast_accuracy_score != _forecast_accuracy_score(row.recent_forecast_error):
        raise ValueError("forecast_accuracy_score must match recent_forecast_error")


def _validate_report_consistency(
    report: TeamSpecialistCalibrationMemoryScorecardV2Report,
) -> None:
    rows = report.rows
    if report.team_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("team_count must match rows")
    if (
        report.pass_team_count != _status_count(rows, "pass")
        or report.watch_team_count != _status_count(rows, "watch")
        or report.blocked_team_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_team_count
        + report.watch_team_count
        + report.blocked_team_count
        != report.team_count
    ):
        raise ValueError("status counts must sum to team_count")
    _validate_rows_sorted(rows)
    expected_status = _scorecard_status(rows)
    if report.scorecard_status != expected_status:
        raise ValueError("scorecard_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.scorecard_status):
        raise ValueError("reason_codes must match scorecard_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_calibration_memory_score != _average_score(rows):
        raise ValueError("average_calibration_memory_score must match rows")
    if report.top_calibration_memory_score != _top_score(rows):
        raise ValueError("top_calibration_memory_score must match rows")
    if report.bottom_calibration_memory_score != _bottom_score(rows):
        raise ValueError("bottom_calibration_memory_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCalibrationMemoryScorecardV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.calibration_memory_score,
                row.team_id,
                row.domain_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


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


def _require_memory_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in MEMORY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_scorecard_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in SCORECARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


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
