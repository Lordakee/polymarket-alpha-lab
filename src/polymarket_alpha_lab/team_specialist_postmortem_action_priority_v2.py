"""Pure Phase 1 specialist postmortem action priority report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_CONFIG_VERSION = (
    "team-specialist-postmortem-action-priority-v2-phase-1"
)
TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_STATUSES = (
    "clear",
    "watch",
    "critical",
)
TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_SOURCE_FAILURE_TYPES = (
    "none",
    "evidence_stale",
    "source_unavailable",
    "source_conflict",
    "resolution_source_missing",
)

CALIBRATION_ERROR_REASON = "calibration_error"
FORECAST_MISS_SEVERITY_REASON = "forecast_miss_severity"
SOURCE_FAILURE_STALE_REASON = "source_failure_evidence_stale"
SOURCE_FAILURE_UNAVAILABLE_REASON = "source_failure_source_unavailable"
SOURCE_FAILURE_CONFLICT_REASON = "source_failure_source_conflict"
SOURCE_FAILURE_MISSING_REASON = "source_failure_resolution_source_missing"
RESOLUTION_RULE_MISS_REASON = "resolution_rule_miss"
STALE_EVIDENCE_REASON = "stale_evidence"
UNRESOLVED_ACTION_AGE_REASON = "unresolved_action_age"
UPCOMING_EVENT_LOAD_REASON = "upcoming_event_load"
ACTION_PRIORITY_CLEAR_REASON = "postmortem_action_priority_clear"
REPORT_CRITICAL_REASON = "team_specialist_postmortem_action_priority_critical"
REPORT_WATCH_REASON = "team_specialist_postmortem_action_priority_watch"
EMPTY_SOURCES_REASON = "team_specialist_postmortem_action_priority_empty_sources"

ROW_REASON_CODES = (
    CALIBRATION_ERROR_REASON,
    FORECAST_MISS_SEVERITY_REASON,
    SOURCE_FAILURE_STALE_REASON,
    SOURCE_FAILURE_UNAVAILABLE_REASON,
    SOURCE_FAILURE_CONFLICT_REASON,
    SOURCE_FAILURE_MISSING_REASON,
    RESOLUTION_RULE_MISS_REASON,
    STALE_EVIDENCE_REASON,
    UNRESOLVED_ACTION_AGE_REASON,
    UPCOMING_EVENT_LOAD_REASON,
    ACTION_PRIORITY_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    REPORT_CRITICAL_REASON,
    REPORT_WATCH_REASON,
    CALIBRATION_ERROR_REASON,
    FORECAST_MISS_SEVERITY_REASON,
    SOURCE_FAILURE_STALE_REASON,
    SOURCE_FAILURE_UNAVAILABLE_REASON,
    SOURCE_FAILURE_CONFLICT_REASON,
    SOURCE_FAILURE_MISSING_REASON,
    RESOLUTION_RULE_MISS_REASON,
    STALE_EVIDENCE_REASON,
    UNRESOLVED_ACTION_AGE_REASON,
    UPCOMING_EVENT_LOAD_REASON,
    ACTION_PRIORITY_CLEAR_REASON,
    EMPTY_SOURCES_REASON,
)
SOURCE_FAILURE_REASON_BY_TYPE = {
    "evidence_stale": SOURCE_FAILURE_STALE_REASON,
    "source_unavailable": SOURCE_FAILURE_UNAVAILABLE_REASON,
    "source_conflict": SOURCE_FAILURE_CONFLICT_REASON,
    "resolution_source_missing": SOURCE_FAILURE_MISSING_REASON,
}
SOURCE_FAILURE_COMPONENT_BY_TYPE = {
    "none": Decimal("0.000000"),
    "evidence_stale": Decimal("0.250000"),
    "source_unavailable": Decimal("0.500000"),
    "source_conflict": Decimal("0.750000"),
    "resolution_source_missing": Decimal("1.000000"),
}

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_REF_PREFIXES = ("public:", "memory:", "source:", "lesson:", "postmortem:")
PUBLIC_TEXT_HEXES = (
    "6c697665",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "6e6574776f726b",
    "6461746162617365",
    "70657273697374",
    "7369676e696e67",
    "6d75746174696f6e",
    "627579",
    "73656c6c",
    "7472616465",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)


@dataclass(frozen=True)
class TeamSpecialistPostmortemActionPriorityReportV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_CONFIG_VERSION
    calibration_error_weight: Decimal = Decimal("0.200000")
    forecast_miss_severity_weight: Decimal = Decimal("0.200000")
    source_failure_weight: Decimal = Decimal("0.150000")
    resolution_rule_miss_weight: Decimal = Decimal("0.150000")
    evidence_staleness_weight: Decimal = Decimal("0.100000")
    unresolved_action_age_weight: Decimal = Decimal("0.100000")
    upcoming_event_load_weight: Decimal = Decimal("0.100000")
    stale_evidence_after_seconds: Decimal = Decimal("604800.000000")
    max_unresolved_action_age_seconds: Decimal = Decimal("2592000.000000")
    upcoming_event_load_block_count: Decimal = Decimal("5")
    watch_priority_score: Decimal = Decimal("0.350000")
    critical_priority_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "calibration_error_weight",
            "forecast_miss_severity_weight",
            "source_failure_weight",
            "resolution_rule_miss_weight",
            "evidence_staleness_weight",
            "unresolved_action_age_weight",
            "upcoming_event_load_weight",
            "watch_priority_score",
            "critical_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_evidence_after_seconds",
            "max_unresolved_action_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upcoming_event_load_block_count",
            _normalize_positive_count(
                "upcoming_event_load_block_count",
                self.upcoming_event_load_block_count,
            ),
        )
        _require_ratio_total(
            self.calibration_error_weight,
            self.forecast_miss_severity_weight,
            self.source_failure_weight,
            self.resolution_rule_miss_weight,
            self.evidence_staleness_weight,
            self.unresolved_action_age_weight,
            self.upcoming_event_load_weight,
        )
        if self.watch_priority_score > self.critical_priority_score:
            raise ValueError("watch_priority_score must be less than or equal to critical_priority_score")
        require_paper_only_flags("specialist postmortem action priority config", self)


@dataclass(frozen=True)
class TeamSpecialistPostmortemActionPriorityInputV2:
    team_id: str
    specialist_id: str
    action_item_id: str
    postmortem_id: str
    action_opened_at: datetime
    latest_evidence_at: datetime
    calibration_error_ratio: Decimal
    forecast_miss_severity_ratio: Decimal
    source_failure_type: str
    resolution_rule_missed: bool
    upcoming_event_count: Decimal
    public_memory_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_id",
            "action_item_id",
            "postmortem_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "action_opened_at",
            _as_utc("action_opened_at", self.action_opened_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        object.__setattr__(
            self,
            "calibration_error_ratio",
            _normalize_ratio("calibration_error_ratio", self.calibration_error_ratio),
        )
        object.__setattr__(
            self,
            "forecast_miss_severity_ratio",
            _normalize_ratio(
                "forecast_miss_severity_ratio",
                self.forecast_miss_severity_ratio,
            ),
        )
        _require_source_failure_type("source_failure_type", self.source_failure_type)
        if type(self.resolution_rule_missed) is not bool:
            raise ValueError("resolution_rule_missed must be a bool")
        object.__setattr__(
            self,
            "upcoming_event_count",
            _normalize_count("upcoming_event_count", self.upcoming_event_count),
        )
        object.__setattr__(
            self,
            "public_memory_refs",
            _normalize_public_refs("public_memory_refs", self.public_memory_refs),
        )
        require_paper_only_flags("specialist postmortem action priority input", self)


@dataclass(frozen=True)
class TeamSpecialistPostmortemActionPriorityRowV2:
    team_id: str
    specialist_id: str
    action_item_id: str
    postmortem_id: str
    action_opened_at: datetime
    latest_evidence_at: datetime
    evidence_age_seconds: Decimal
    unresolved_action_age_seconds: Decimal
    calibration_error_ratio: Decimal
    forecast_miss_severity_ratio: Decimal
    source_failure_type: str
    resolution_rule_missed: bool
    upcoming_event_count: Decimal
    source_failure_component: Decimal
    resolution_rule_miss_component: Decimal
    evidence_staleness_component: Decimal
    unresolved_action_age_component: Decimal
    upcoming_event_load_component: Decimal
    priority_score: Decimal
    row_status: str
    public_memory_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_id",
            "action_item_id",
            "postmortem_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "action_opened_at",
            _as_utc("action_opened_at", self.action_opened_at),
        )
        object.__setattr__(
            self,
            "latest_evidence_at",
            _as_utc("latest_evidence_at", self.latest_evidence_at),
        )
        for field_name in (
            "evidence_age_seconds",
            "unresolved_action_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error_ratio",
            "forecast_miss_severity_ratio",
            "source_failure_component",
            "resolution_rule_miss_component",
            "evidence_staleness_component",
            "unresolved_action_age_component",
            "upcoming_event_load_component",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_source_failure_type("source_failure_type", self.source_failure_type)
        if type(self.resolution_rule_missed) is not bool:
            raise ValueError("resolution_rule_missed must be a bool")
        object.__setattr__(
            self,
            "upcoming_event_count",
            _normalize_count("upcoming_event_count", self.upcoming_event_count),
        )
        _require_status("row_status", self.row_status)
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
        _validate_row(self)
        require_paper_only_flags("specialist postmortem action priority row", self)


@dataclass(frozen=True)
class TeamSpecialistPostmortemActionPriorityReportV2:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    specialist_team_count: Decimal
    action_item_count: Decimal
    critical_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[TeamSpecialistPostmortemActionPriorityRowV2, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "specialist_team_count",
            "action_item_count",
            "critical_count",
            "watch_count",
            "clear_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_priority_score",
            _normalize_ratio("average_priority_score", self.average_priority_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_priority_rows(self.priority_rows),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)
        require_paper_only_flags("specialist postmortem action priority report", self)


def build_team_specialist_postmortem_action_priority_report_v2(
    inputs: list[TeamSpecialistPostmortemActionPriorityInputV2]
    | tuple[TeamSpecialistPostmortemActionPriorityInputV2, ...],
    *,
    config: TeamSpecialistPostmortemActionPriorityReportV2Config,
    generated_at: datetime,
) -> TeamSpecialistPostmortemActionPriorityReportV2:
    if type(config) is not TeamSpecialistPostmortemActionPriorityReportV2Config:
        raise ValueError(
            "config must be a TeamSpecialistPostmortemActionPriorityReportV2Config",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    _validate_input_dates(rows, generated_at_utc)
    priority_rows = tuple(
        sorted(
            (_priority_row(row, config, generated_at_utc) for row in rows),
            key=_priority_row_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len({row.team_id for row in priority_rows})),
        specialist_team_count=_count(
            len({(row.team_id, row.specialist_id) for row in priority_rows}),
        ),
        action_item_count=_count(len(priority_rows)),
        critical_count=_count(sum(1 for row in priority_rows if row.row_status == "critical")),
        watch_count=_count(sum(1 for row in priority_rows if row.row_status == "watch")),
        clear_count=_count(sum(1 for row in priority_rows if row.row_status == "clear")),
        average_priority_score=_average_priority_score(priority_rows),
        status=_report_status(priority_rows),
        reason_codes=_report_reason_codes(priority_rows),
        priority_rows=priority_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistPostmortemActionPriorityReportV2(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_postmortem_action_priority_report_v2_payload(
    report: TeamSpecialistPostmortemActionPriorityReportV2,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistPostmortemActionPriorityReportV2:
        raise ValueError("report must be a TeamSpecialistPostmortemActionPriorityReportV2")
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_public_payload("specialist postmortem action priority payload", payload)
    return payload


def _normalize_inputs(
    inputs: list[TeamSpecialistPostmortemActionPriorityInputV2]
    | tuple[TeamSpecialistPostmortemActionPriorityInputV2, ...],
) -> tuple[TeamSpecialistPostmortemActionPriorityInputV2, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    for row in rows:
        if type(row) is not TeamSpecialistPostmortemActionPriorityInputV2:
            raise ValueError(
                "inputs must contain TeamSpecialistPostmortemActionPriorityInputV2 values",
            )
        require_paper_only_flags("input", row)
    return rows


def _validate_input_dates(
    rows: tuple[TeamSpecialistPostmortemActionPriorityInputV2, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.action_opened_at > generated_at:
            raise ValueError("action_opened_at must be on or before generated_at")
        if row.latest_evidence_at > generated_at:
            raise ValueError("latest_evidence_at must be on or before generated_at")


def _priority_row(
    row: TeamSpecialistPostmortemActionPriorityInputV2,
    config: TeamSpecialistPostmortemActionPriorityReportV2Config,
    generated_at: datetime,
) -> TeamSpecialistPostmortemActionPriorityRowV2:
    evidence_age_seconds = _age_seconds(generated_at, row.latest_evidence_at)
    unresolved_action_age_seconds = _age_seconds(generated_at, row.action_opened_at)
    source_failure_component = SOURCE_FAILURE_COMPONENT_BY_TYPE[row.source_failure_type]
    resolution_rule_miss_component = ONE_RATIO if row.resolution_rule_missed else ZERO_RATIO
    evidence_staleness_component = _staleness_component(
        evidence_age_seconds,
        config.stale_evidence_after_seconds,
    )
    unresolved_action_age_component = _ratio_to_target(
        unresolved_action_age_seconds,
        config.max_unresolved_action_age_seconds,
    )
    upcoming_event_load_component = _ratio_to_target(
        row.upcoming_event_count,
        config.upcoming_event_load_block_count,
    )
    priority_score = _priority_score(
        row.calibration_error_ratio,
        row.forecast_miss_severity_ratio,
        source_failure_component,
        resolution_rule_miss_component,
        evidence_staleness_component,
        unresolved_action_age_component,
        upcoming_event_load_component,
        config,
    )
    row_status = _row_status(priority_score, config)
    row_parts = dict(
        team_id=row.team_id,
        specialist_id=row.specialist_id,
        action_item_id=row.action_item_id,
        postmortem_id=row.postmortem_id,
        action_opened_at=row.action_opened_at,
        latest_evidence_at=row.latest_evidence_at,
        evidence_age_seconds=evidence_age_seconds,
        unresolved_action_age_seconds=unresolved_action_age_seconds,
        calibration_error_ratio=row.calibration_error_ratio,
        forecast_miss_severity_ratio=row.forecast_miss_severity_ratio,
        source_failure_type=row.source_failure_type,
        resolution_rule_missed=row.resolution_rule_missed,
        upcoming_event_count=row.upcoming_event_count,
        source_failure_component=source_failure_component,
        resolution_rule_miss_component=resolution_rule_miss_component,
        evidence_staleness_component=evidence_staleness_component,
        unresolved_action_age_component=unresolved_action_age_component,
        upcoming_event_load_component=upcoming_event_load_component,
        priority_score=priority_score,
        row_status=row_status,
        public_memory_refs=row.public_memory_refs,
        reason_codes=_row_reason_codes(
            row_status,
            row.calibration_error_ratio,
            row.forecast_miss_severity_ratio,
            row.source_failure_type,
            source_failure_component,
            resolution_rule_miss_component,
            evidence_staleness_component,
            unresolved_action_age_component,
            upcoming_event_load_component,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistPostmortemActionPriorityRowV2(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _staleness_component(age_seconds: Decimal, stale_after_seconds: Decimal) -> Decimal:
    if age_seconds <= stale_after_seconds:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((age_seconds - stale_after_seconds) / stale_after_seconds)


def _ratio_to_target(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _priority_score(
    calibration_error_ratio: Decimal,
    forecast_miss_severity_ratio: Decimal,
    source_failure_component: Decimal,
    resolution_rule_miss_component: Decimal,
    evidence_staleness_component: Decimal,
    unresolved_action_age_component: Decimal,
    upcoming_event_load_component: Decimal,
    config: TeamSpecialistPostmortemActionPriorityReportV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            calibration_error_ratio * config.calibration_error_weight
            + forecast_miss_severity_ratio * config.forecast_miss_severity_weight
            + source_failure_component * config.source_failure_weight
            + resolution_rule_miss_component * config.resolution_rule_miss_weight
            + evidence_staleness_component * config.evidence_staleness_weight
            + unresolved_action_age_component * config.unresolved_action_age_weight
            + upcoming_event_load_component * config.upcoming_event_load_weight,
        )


def _row_reason_codes(
    row_status: str,
    calibration_error_ratio: Decimal,
    forecast_miss_severity_ratio: Decimal,
    source_failure_type: str,
    source_failure_component: Decimal,
    resolution_rule_miss_component: Decimal,
    evidence_staleness_component: Decimal,
    unresolved_action_age_component: Decimal,
    upcoming_event_load_component: Decimal,
) -> tuple[str, ...]:
    if row_status == "clear":
        return (ACTION_PRIORITY_CLEAR_REASON,)
    codes: set[str] = set()
    if calibration_error_ratio > ZERO_RATIO:
        codes.add(CALIBRATION_ERROR_REASON)
    if forecast_miss_severity_ratio > ZERO_RATIO:
        codes.add(FORECAST_MISS_SEVERITY_REASON)
    if source_failure_component > ZERO_RATIO and source_failure_type in SOURCE_FAILURE_REASON_BY_TYPE:
        codes.add(SOURCE_FAILURE_REASON_BY_TYPE[source_failure_type])
    if resolution_rule_miss_component > ZERO_RATIO:
        codes.add(RESOLUTION_RULE_MISS_REASON)
    if evidence_staleness_component > ZERO_RATIO:
        codes.add(STALE_EVIDENCE_REASON)
    if unresolved_action_age_component > ZERO_RATIO:
        codes.add(UNRESOLVED_ACTION_AGE_REASON)
    if upcoming_event_load_component > ZERO_RATIO:
        codes.add(UPCOMING_EVENT_LOAD_REASON)
    if not codes:
        codes.add(ACTION_PRIORITY_CLEAR_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistPostmortemActionPriorityRowV2, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_SOURCES_REASON,)
    codes = {
        code
        for row in rows
        if row.row_status != "clear"
        for code in row.reason_codes
    }
    status = _report_status(rows)
    if status == "critical":
        codes.add(REPORT_CRITICAL_REASON)
    elif status == "watch":
        codes.add(REPORT_WATCH_REASON)
    if not codes:
        codes.add(ACTION_PRIORITY_CLEAR_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _row_status(
    priority_score: Decimal,
    config: TeamSpecialistPostmortemActionPriorityReportV2Config,
) -> str:
    if priority_score >= config.critical_priority_score:
        return "critical"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "clear"


def _report_status(rows: tuple[TeamSpecialistPostmortemActionPriorityRowV2, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.row_status == "critical" for row in rows):
        return "critical"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _priority_row_sort_key(
    row: TeamSpecialistPostmortemActionPriorityRowV2,
) -> tuple[int, Decimal, str, str, str]:
    return (
        -_status_rank(row.row_status),
        -row.priority_score,
        row.team_id,
        row.specialist_id,
        row.action_item_id,
    )


def _status_rank(status: str) -> int:
    if status == "critical":
        return 2
    if status == "watch":
        return 1
    return 0


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        ).quantize(RATIO_QUANTUM)


def _average_priority_score(
    rows: tuple[TeamSpecialistPostmortemActionPriorityRowV2, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.priority_score for row in rows), ZERO_RATIO) / Decimal(len(rows)),
        )


def _validate_row(row: TeamSpecialistPostmortemActionPriorityRowV2) -> None:
    if row.source_failure_component != SOURCE_FAILURE_COMPONENT_BY_TYPE[row.source_failure_type]:
        raise ValueError("source_failure_component must match source_failure_type")
    expected_rule_component = ONE_RATIO if row.resolution_rule_missed else ZERO_RATIO
    if row.resolution_rule_miss_component != expected_rule_component:
        raise ValueError("resolution_rule_miss_component must match resolution_rule_missed")
    expected_score = _priority_score(
        row.calibration_error_ratio,
        row.forecast_miss_severity_ratio,
        row.source_failure_component,
        row.resolution_rule_miss_component,
        row.evidence_staleness_component,
        row.unresolved_action_age_component,
        row.upcoming_event_load_component,
        TeamSpecialistPostmortemActionPriorityReportV2Config(),
    )
    if row.priority_score != expected_score:
        raise ValueError("priority_score must match priority components")
    if row.row_status != _row_status(
        row.priority_score,
        TeamSpecialistPostmortemActionPriorityReportV2Config(),
    ):
        raise ValueError("row_status must match priority_score")
    if row.reason_codes != _row_reason_codes(
        row.row_status,
        row.calibration_error_ratio,
        row.forecast_miss_severity_ratio,
        row.source_failure_type,
        row.source_failure_component,
        row.resolution_rule_miss_component,
        row.evidence_staleness_component,
        row.unresolved_action_age_component,
        row.upcoming_event_load_component,
    ):
        raise ValueError("reason_codes must match priority components")


def _validate_report(report: TeamSpecialistPostmortemActionPriorityReportV2) -> None:
    if report.team_count != _count(len({row.team_id for row in report.priority_rows})):
        raise ValueError("team_count must match priority_rows")
    if report.specialist_team_count != _count(
        len({(row.team_id, row.specialist_id) for row in report.priority_rows}),
    ):
        raise ValueError("specialist_team_count must match priority_rows")
    if report.action_item_count != _count(len(report.priority_rows)):
        raise ValueError("action_item_count must match priority_rows")
    if report.critical_count != _count(
        sum(1 for row in report.priority_rows if row.row_status == "critical"),
    ):
        raise ValueError("critical_count must match priority_rows")
    if report.watch_count != _count(
        sum(1 for row in report.priority_rows if row.row_status == "watch"),
    ):
        raise ValueError("watch_count must match priority_rows")
    if report.clear_count != _count(
        sum(1 for row in report.priority_rows if row.row_status == "clear"),
    ):
        raise ValueError("clear_count must match priority_rows")
    if report.average_priority_score != _average_priority_score(report.priority_rows):
        raise ValueError("average_priority_score must match priority_rows")
    if report.status != _report_status(report.priority_rows):
        raise ValueError("status must match priority_rows")
    if report.reason_codes != _report_reason_codes(report.priority_rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.priority_rows != tuple(sorted(report.priority_rows, key=_priority_row_sort_key)):
        raise ValueError("priority_rows must use deterministic sequence")


def _normalize_priority_rows(
    rows: tuple[TeamSpecialistPostmortemActionPriorityRowV2, ...],
) -> tuple[TeamSpecialistPostmortemActionPriorityRowV2, ...]:
    if type(rows) is not tuple:
        raise ValueError("priority_rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistPostmortemActionPriorityRowV2:
            raise ValueError(
                "priority_rows must contain TeamSpecialistPostmortemActionPriorityRowV2 values",
            )
        require_paper_only_flags("priority row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    expected = tuple(code for code in allowed_reason_codes if code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = []
    for item in value:
        _require_public_string(field_name, item)
        if not item.startswith(SAFE_REF_PREFIXES):
            raise ValueError(f"{field_name} contains an unsupported public reference")
        normalized.append(item)
    return tuple(normalized)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    value = _normalize_count(field_name, value)
    if value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(RATIO_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        value = ZERO_RATIO
    if value > ONE_RATIO:
        value = ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        if sum(values, ZERO_RATIO).quantize(RATIO_QUANTUM) != ONE_RATIO:
            raise ValueError("priority weights must sum to 1")


def _require_status(field_name: str, value: object) -> None:
    if value not in TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or critical")


def _require_source_failure_type(field_name: str, value: object) -> None:
    if value not in TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_SOURCE_FAILURE_TYPES:
        raise ValueError(f"{field_name} must be a known source failure type")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(field_name, value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _row_digest(row: TeamSpecialistPostmortemActionPriorityRowV2) -> str:
    return _digest_public(_row_digest_parts(row))


def _report_digest(report: TeamSpecialistPostmortemActionPriorityReportV2) -> str:
    return _digest_public(_report_digest_parts(report))


def _row_digest_parts(row: TeamSpecialistPostmortemActionPriorityRowV2) -> dict[str, object]:
    return {
        "team_id": row.team_id,
        "specialist_id": row.specialist_id,
        "action_item_id": row.action_item_id,
        "postmortem_id": row.postmortem_id,
        "action_opened_at": row.action_opened_at,
        "latest_evidence_at": row.latest_evidence_at,
        "evidence_age_seconds": row.evidence_age_seconds,
        "unresolved_action_age_seconds": row.unresolved_action_age_seconds,
        "calibration_error_ratio": row.calibration_error_ratio,
        "forecast_miss_severity_ratio": row.forecast_miss_severity_ratio,
        "source_failure_type": row.source_failure_type,
        "resolution_rule_missed": row.resolution_rule_missed,
        "upcoming_event_count": row.upcoming_event_count,
        "source_failure_component": row.source_failure_component,
        "resolution_rule_miss_component": row.resolution_rule_miss_component,
        "evidence_staleness_component": row.evidence_staleness_component,
        "unresolved_action_age_component": row.unresolved_action_age_component,
        "upcoming_event_load_component": row.upcoming_event_load_component,
        "priority_score": row.priority_score,
        "row_status": row.row_status,
        "public_memory_refs": row.public_memory_refs,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_parts(report: TeamSpecialistPostmortemActionPriorityReportV2) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "team_count": report.team_count,
        "specialist_team_count": report.specialist_team_count,
        "action_item_count": report.action_item_count,
        "critical_count": report.critical_count,
        "watch_count": report.watch_count,
        "clear_count": report.clear_count,
        "average_priority_score": report.average_priority_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "priority_rows": report.priority_rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_public(value: object) -> str:
    ready = _digest_ready(value)
    _reject_public_payload("derived validation payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _digest_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("digest datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("digest object keys must be strings")
            if key == "derived_validation_digest":
                continue
            ready[key] = _digest_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_digest_ready(item) for item in value]
    raise ValueError("value is not digest serializable")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"public payload key must be a string for {label}")
            if _public_text_has_block(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_public_text(label, value)


def _reject_public_text(label: str, value: str) -> None:
    if _public_text_has_block(value):
        raise ValueError(f"unsafe public value in {label}")


def _public_text_has_block(value: str) -> bool:
    normalized = value.lower()
    return any(block in normalized for block in PUBLIC_TEXT_BLOCKS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_REPORT_V2_STATUSES",
    "TEAM_SPECIALIST_POSTMORTEM_ACTION_PRIORITY_SOURCE_FAILURE_TYPES",
    "TeamSpecialistPostmortemActionPriorityReportV2Config",
    "TeamSpecialistPostmortemActionPriorityInputV2",
    "TeamSpecialistPostmortemActionPriorityRowV2",
    "TeamSpecialistPostmortemActionPriorityReportV2",
    "build_team_specialist_postmortem_action_priority_report_v2",
    "team_specialist_postmortem_action_priority_report_v2_payload",
)
