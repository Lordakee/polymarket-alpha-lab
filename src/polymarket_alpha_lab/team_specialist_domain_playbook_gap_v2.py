"""Phase 1 paper-only report for specialist domain playbook gaps."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_SPECIALIST_DOMAIN_PLAYBOOK_GAP_V2_CONFIG_VERSION = (
    "team-specialist-domain-playbook-gap-v2-phase1"
)

STATUS_VALUES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "team_specialist_domain_playbook_gap_passed",
    "team_specialist_domain_playbook_calibration_decay",
    "team_specialist_domain_playbook_stale_lessons",
    "team_specialist_domain_playbook_missing_source_families",
    "team_specialist_domain_playbook_contradiction_misses",
    "team_specialist_domain_playbook_resolution_rule_errors",
    "team_specialist_domain_playbook_recent_forecast_error",
    "team_specialist_domain_playbook_upcoming_event_load",
)
REPORT_REASON_CODES = (
    "team_specialist_domain_playbook_gap_passed",
    "team_specialist_domain_playbook_gap_blocked_rows",
    "team_specialist_domain_playbook_gap_watch_rows",
    "team_specialist_domain_playbook_gap_empty",
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


@dataclass(frozen=True)
class TeamSpecialistDomainPlaybookGapV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_DOMAIN_PLAYBOOK_GAP_V2_CONFIG_VERSION
    calibration_decay_weight: Decimal = Decimal("0.200000")
    stale_lesson_weight: Decimal = Decimal("0.150000")
    missing_source_family_weight: Decimal = Decimal("0.150000")
    contradiction_miss_weight: Decimal = Decimal("0.150000")
    resolution_rule_error_weight: Decimal = Decimal("0.150000")
    recent_forecast_error_weight: Decimal = Decimal("0.100000")
    upcoming_event_load_weight: Decimal = Decimal("0.100000")
    max_stale_lesson_count: Decimal = Decimal("5")
    max_contradiction_miss_count: Decimal = Decimal("3")
    max_resolution_rule_error_count: Decimal = Decimal("2")
    max_upcoming_event_count: Decimal = Decimal("8")
    pass_gap_score_floor: Decimal = Decimal("0.100000")
    watch_gap_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "calibration_decay_weight",
            "stale_lesson_weight",
            "missing_source_family_weight",
            "contradiction_miss_weight",
            "resolution_rule_error_weight",
            "recent_forecast_error_weight",
            "upcoming_event_load_weight",
            "pass_gap_score_floor",
            "watch_gap_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_stale_lesson_count",
            "max_contradiction_miss_count",
            "max_resolution_rule_error_count",
            "max_upcoming_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        _require_ratio_total(
            self.calibration_decay_weight,
            self.stale_lesson_weight,
            self.missing_source_family_weight,
            self.contradiction_miss_weight,
            self.resolution_rule_error_weight,
            self.recent_forecast_error_weight,
            self.upcoming_event_load_weight,
        )
        if self.pass_gap_score_floor > self.watch_gap_score_floor:
            raise ValueError("pass_gap_score_floor must not exceed watch_gap_score_floor")
        require_paper_only_flags("specialist domain playbook gap config", self)


@dataclass(frozen=True)
class TeamSpecialistDomainPlaybookGapV2Memory:
    team_id: str
    specialist_id: str
    domain_id: str
    memory_key: str
    observed_at: datetime
    last_lesson_reviewed_at: datetime
    baseline_calibration_score: Decimal
    current_calibration_score: Decimal
    stale_lesson_count: Decimal
    required_source_family_count: Decimal
    observed_source_family_count: Decimal
    contradiction_miss_count: Decimal
    resolution_rule_error_count: Decimal
    recent_forecast_error: Decimal
    upcoming_event_count: Decimal
    public_memory_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "domain_id", "memory_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_lesson_reviewed_at",
            _as_utc("last_lesson_reviewed_at", self.last_lesson_reviewed_at),
        )
        for field_name in (
            "baseline_calibration_score",
            "current_calibration_score",
            "recent_forecast_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_lesson_count",
            "required_source_family_count",
            "observed_source_family_count",
            "contradiction_miss_count",
            "resolution_rule_error_count",
            "upcoming_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_memory_refs",
            _normalize_public_refs("public_memory_refs", self.public_memory_refs),
        )
        if self.current_calibration_score > self.baseline_calibration_score:
            raise ValueError(
                "current_calibration_score must not exceed baseline_calibration_score",
            )
        require_paper_only_flags("specialist domain playbook gap memory", self)
        _reject_unsafe_public_payload("specialist domain playbook gap memory", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistDomainPlaybookGapV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    domain_id: str
    memory_key: str
    observed_at: datetime
    last_lesson_reviewed_at: datetime
    calibration_decay_gap: Decimal
    stale_lesson_gap: Decimal
    missing_source_family_count: Decimal
    missing_source_family_gap: Decimal
    contradiction_miss_gap: Decimal
    resolution_rule_error_gap: Decimal
    recent_forecast_error_gap: Decimal
    upcoming_event_load_gap: Decimal
    playbook_gap_score: Decimal
    gap_status: str
    public_memory_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_count("rank", self.rank))
        for field_name in ("team_id", "specialist_id", "domain_id", "memory_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_lesson_reviewed_at",
            _as_utc("last_lesson_reviewed_at", self.last_lesson_reviewed_at),
        )
        for field_name in (
            "calibration_decay_gap",
            "stale_lesson_gap",
            "missing_source_family_gap",
            "contradiction_miss_gap",
            "resolution_rule_error_gap",
            "recent_forecast_error_gap",
            "upcoming_event_load_gap",
            "playbook_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_source_family_count",
            _normalize_count(
                "missing_source_family_count",
                self.missing_source_family_count,
            ),
        )
        _require_status("gap_status", self.gap_status)
        object.__setattr__(
            self,
            "public_memory_refs",
            _normalize_public_refs("public_memory_refs", self.public_memory_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        require_paper_only_flags("specialist domain playbook gap row", self)
        _reject_unsafe_public_payload("specialist domain playbook gap row", asdict(self))


@dataclass(frozen=True)
class TeamSpecialistDomainPlaybookGapV2Report:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    domain_count: Decimal
    memory_count: Decimal
    pass_memory_count: Decimal
    watch_memory_count: Decimal
    blocked_memory_count: Decimal
    average_playbook_gap_score: Decimal
    max_playbook_gap_score: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistDomainPlaybookGapV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "domain_count",
            "memory_count",
            "pass_memory_count",
            "watch_memory_count",
            "blocked_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_playbook_gap_score", "max_playbook_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("gap_status", self.gap_status)
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
        require_paper_only_flags("specialist domain playbook gap report", self)
        _reject_unsafe_public_payload("specialist domain playbook gap report", self.payload)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_domain_playbook_gap_v2_payload(self)


def build_team_specialist_domain_playbook_gap_v2_report(
    team_memories: object,
    *,
    config: TeamSpecialistDomainPlaybookGapV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistDomainPlaybookGapV2Report:
    if config is None:
        config = TeamSpecialistDomainPlaybookGapV2Config()
    if type(config) is not TeamSpecialistDomainPlaybookGapV2Config:
        raise ValueError("config must be a TeamSpecialistDomainPlaybookGapV2Config")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    memories = _normalize_memories(team_memories)
    for memory in memories:
        if memory.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")
        if memory.last_lesson_reviewed_at > generated_at_utc:
            raise ValueError("last_lesson_reviewed_at must be on or before generated_at")

    rows_without_rank = tuple(_row_parts(memory, config) for memory in memories)
    ranked_rows = tuple(
        TeamSpecialistDomainPlaybookGapV2Row(
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
        "team_count": _count(len({row.team_id for row in ranked_rows})),
        "domain_count": _count(len({row.domain_id for row in ranked_rows})),
        "memory_count": _count(len(ranked_rows)),
        "pass_memory_count": _count(
            sum(1 for row in ranked_rows if row.gap_status == "pass"),
        ),
        "watch_memory_count": _count(
            sum(1 for row in ranked_rows if row.gap_status == "watch"),
        ),
        "blocked_memory_count": _count(
            sum(1 for row in ranked_rows if row.gap_status == "blocked"),
        ),
        "average_playbook_gap_score": _average_gap_score(ranked_rows),
        "max_playbook_gap_score": _max_gap_score(ranked_rows),
        "gap_status": _report_status(ranked_rows),
        "reason_codes": _report_reason_codes(ranked_rows),
        "rows": ranked_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistDomainPlaybookGapV2Report(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_domain_playbook_gap_v2_payload(
    report: TeamSpecialistDomainPlaybookGapV2Report,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistDomainPlaybookGapV2Report:
        raise ValueError("report must be a TeamSpecialistDomainPlaybookGapV2Report")
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("specialist domain playbook gap payload", payload)
    return payload


def _row_parts(
    memory: TeamSpecialistDomainPlaybookGapV2Memory,
    config: TeamSpecialistDomainPlaybookGapV2Config,
) -> dict[str, object]:
    missing_source_family_count = max(
        ZERO,
        memory.required_source_family_count - memory.observed_source_family_count,
    ).quantize(COUNT_QUANTUM)
    calibration_decay_gap = _clamp_ratio(
        memory.baseline_calibration_score - memory.current_calibration_score,
    )
    stale_lesson_gap = _count_ratio(
        memory.stale_lesson_count,
        config.max_stale_lesson_count,
    )
    missing_source_family_gap = (
        ZERO
        if memory.required_source_family_count == ZERO
        else _count_ratio(missing_source_family_count, memory.required_source_family_count)
    )
    contradiction_miss_gap = _count_ratio(
        memory.contradiction_miss_count,
        config.max_contradiction_miss_count,
    )
    resolution_rule_error_gap = _count_ratio(
        memory.resolution_rule_error_count,
        config.max_resolution_rule_error_count,
    )
    recent_forecast_error_gap = memory.recent_forecast_error
    upcoming_event_load_gap = _count_ratio(
        memory.upcoming_event_count,
        config.max_upcoming_event_count,
    )
    playbook_gap_score = _playbook_gap_score(
        calibration_decay_gap,
        stale_lesson_gap,
        missing_source_family_gap,
        contradiction_miss_gap,
        resolution_rule_error_gap,
        recent_forecast_error_gap,
        upcoming_event_load_gap,
        config,
    )
    gap_status = _row_status(playbook_gap_score, config)
    return {
        "team_id": memory.team_id,
        "specialist_id": memory.specialist_id,
        "domain_id": memory.domain_id,
        "memory_key": memory.memory_key,
        "observed_at": memory.observed_at,
        "last_lesson_reviewed_at": memory.last_lesson_reviewed_at,
        "calibration_decay_gap": calibration_decay_gap,
        "stale_lesson_gap": stale_lesson_gap,
        "missing_source_family_count": missing_source_family_count,
        "missing_source_family_gap": missing_source_family_gap,
        "contradiction_miss_gap": contradiction_miss_gap,
        "resolution_rule_error_gap": resolution_rule_error_gap,
        "recent_forecast_error_gap": recent_forecast_error_gap,
        "upcoming_event_load_gap": upcoming_event_load_gap,
        "playbook_gap_score": playbook_gap_score,
        "gap_status": gap_status,
        "public_memory_refs": memory.public_memory_refs,
        "reason_codes": _row_reason_codes(
            gap_status,
            calibration_decay_gap,
            stale_lesson_gap,
            missing_source_family_gap,
            contradiction_miss_gap,
            resolution_rule_error_gap,
            recent_forecast_error_gap,
            upcoming_event_load_gap,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_parts_sort_key(parts: dict[str, object]) -> tuple[Decimal, str, str, str]:
    score = parts["playbook_gap_score"]
    if type(score) is not Decimal:
        raise ValueError("playbook_gap_score must be a Decimal")
    return (-score, str(parts["team_id"]), str(parts["domain_id"]), str(parts["memory_key"]))


def _row_sort_key(
    row: TeamSpecialistDomainPlaybookGapV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -row.playbook_gap_score,
        row.rank,
        row.team_id,
        row.domain_id,
        row.memory_key,
    )


def _playbook_gap_score(
    calibration_decay_gap: Decimal,
    stale_lesson_gap: Decimal,
    missing_source_family_gap: Decimal,
    contradiction_miss_gap: Decimal,
    resolution_rule_error_gap: Decimal,
    recent_forecast_error_gap: Decimal,
    upcoming_event_load_gap: Decimal,
    config: TeamSpecialistDomainPlaybookGapV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            calibration_decay_gap * config.calibration_decay_weight
            + stale_lesson_gap * config.stale_lesson_weight
            + missing_source_family_gap * config.missing_source_family_weight
            + contradiction_miss_gap * config.contradiction_miss_weight
            + resolution_rule_error_gap * config.resolution_rule_error_weight
            + recent_forecast_error_gap * config.recent_forecast_error_weight
            + upcoming_event_load_gap * config.upcoming_event_load_weight,
        )


def _row_reason_codes(
    gap_status: str,
    calibration_decay_gap: Decimal,
    stale_lesson_gap: Decimal,
    missing_source_family_gap: Decimal,
    contradiction_miss_gap: Decimal,
    resolution_rule_error_gap: Decimal,
    recent_forecast_error_gap: Decimal,
    upcoming_event_load_gap: Decimal,
) -> tuple[str, ...]:
    if gap_status == "pass":
        return ("team_specialist_domain_playbook_gap_passed",)
    reason_codes: set[str] = set()
    if calibration_decay_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_calibration_decay")
    if stale_lesson_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_stale_lessons")
    if missing_source_family_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_missing_source_families")
    if contradiction_miss_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_contradiction_misses")
    if resolution_rule_error_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_resolution_rule_errors")
    if recent_forecast_error_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_recent_forecast_error")
    if upcoming_event_load_gap > ZERO:
        reason_codes.add("team_specialist_domain_playbook_upcoming_event_load")
    return tuple(reason for reason in ROW_REASON_CODES if reason in reason_codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistDomainPlaybookGapV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_specialist_domain_playbook_gap_empty",)
    reason_codes: list[str] = []
    if any(row.gap_status == "blocked" for row in rows):
        reason_codes.append("team_specialist_domain_playbook_gap_blocked_rows")
    if any(row.gap_status == "watch" for row in rows):
        reason_codes.append("team_specialist_domain_playbook_gap_watch_rows")
    if not reason_codes:
        reason_codes.append("team_specialist_domain_playbook_gap_passed")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _row_status(
    playbook_gap_score: Decimal,
    config: TeamSpecialistDomainPlaybookGapV2Config,
) -> str:
    if playbook_gap_score <= config.pass_gap_score_floor:
        return "pass"
    if playbook_gap_score <= config.watch_gap_score_floor:
        return "watch"
    return "blocked"


def _report_status(rows: tuple[TeamSpecialistDomainPlaybookGapV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _average_gap_score(rows: tuple[TeamSpecialistDomainPlaybookGapV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.playbook_gap_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _max_gap_score(rows: tuple[TeamSpecialistDomainPlaybookGapV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(row.playbook_gap_score for row in rows).quantize(RATIO_QUANTUM)


def _normalize_memories(
    team_memories: object,
) -> tuple[TeamSpecialistDomainPlaybookGapV2Memory, ...]:
    if isinstance(team_memories, (str, bytes)) or type(team_memories) not in (list, tuple):
        raise ValueError("team_memories must be an iterable")
    memories = tuple(team_memories)
    seen_keys: set[tuple[str, str, str, str]] = set()
    for memory in memories:
        if type(memory) is not TeamSpecialistDomainPlaybookGapV2Memory:
            raise ValueError(
                "team memory items must be TeamSpecialistDomainPlaybookGapV2Memory",
            )
        require_paper_only_flags("team memory", memory)
        key = (memory.team_id, memory.specialist_id, memory.domain_id, memory.memory_key)
        if key in seen_keys:
            raise ValueError("team memory items must have unique public keys")
        seen_keys.add(key)
    return memories


def _normalize_rows(
    rows: object,
) -> tuple[TeamSpecialistDomainPlaybookGapV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str, str]] = set()
    for row in normalized:
        if type(row) is not TeamSpecialistDomainPlaybookGapV2Row:
            raise ValueError("rows must contain TeamSpecialistDomainPlaybookGapV2Row values")
        require_paper_only_flags("row", row)
        key = (row.team_id, row.specialist_id, row.domain_id, row.memory_key)
        if key in seen_keys:
            raise ValueError("rows must have unique public keys")
        seen_keys.add(key)
    return normalized


def _validate_report_counts_status_and_reasons(
    report: TeamSpecialistDomainPlaybookGapV2Report,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by gap score and rank")
    if tuple(row.rank for row in report.rows) != tuple(
        _count(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("rows must be sorted by gap score and rank")
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.domain_count != _count(len({row.domain_id for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.memory_count != _count(len(report.rows)):
        raise ValueError("memory_count must match rows")
    if (
        report.pass_memory_count
        != _count(sum(1 for row in report.rows if row.gap_status == "pass"))
        or report.watch_memory_count
        != _count(sum(1 for row in report.rows if row.gap_status == "watch"))
        or report.blocked_memory_count
        != _count(sum(1 for row in report.rows if row.gap_status == "blocked"))
    ):
        raise ValueError("status counts must match rows")
    if report.gap_status != _report_status(report.rows):
        raise ValueError("gap_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match gap_status")


def _validate_report_scores(report: TeamSpecialistDomainPlaybookGapV2Report) -> None:
    if report.average_playbook_gap_score != _average_gap_score(report.rows):
        raise ValueError("average_playbook_gap_score must match rows")
    if report.max_playbook_gap_score != _max_gap_score(report.rows):
        raise ValueError("max_playbook_gap_score must match rows")


def _row_digest(row: TeamSpecialistDomainPlaybookGapV2Row) -> str:
    return _digest_public(asdict(row))


def _report_digest(report: TeamSpecialistDomainPlaybookGapV2Report) -> str:
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
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    return value


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
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
    if type(payload) is float or type(payload) is int:
        raise ValueError(f"unsafe public payload in {label}")
    if type(payload) is str:
        _reject_unsafe_text(payload)


def _reject_unsafe_text(value: str) -> None:
    normalized = value.lower()
    if value.strip() != value or "://" in normalized or "?" in normalized:
        raise ValueError("unsafe public payload")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload")


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
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


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(value)


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_ratio_total(*values: Decimal) -> None:
    total = sum(values, ZERO).quantize(RATIO_QUANTUM)
    if total != ONE.quantize(RATIO_QUANTUM):
        raise ValueError("gap weights must sum to 1.000000")


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
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_DOMAIN_PLAYBOOK_GAP_V2_CONFIG_VERSION",
    "TeamSpecialistDomainPlaybookGapV2Config",
    "TeamSpecialistDomainPlaybookGapV2Memory",
    "TeamSpecialistDomainPlaybookGapV2Report",
    "TeamSpecialistDomainPlaybookGapV2Row",
    "build_team_specialist_domain_playbook_gap_v2_report",
    "team_specialist_domain_playbook_gap_v2_payload",
)
