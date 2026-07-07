"""Pure Phase 1 specialist learning priority report."""

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


DEFAULT_TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_CONFIG_VERSION = (
    "team-specialist-learning-priority-report-v2-phase-1"
)
TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_STATUSES = (
    "clear",
    "watch",
    "critical",
)

RECENT_FORECAST_ERROR_REASON = "recent_forecast_error"
STALE_PLAYBOOK_REASON = "stale_playbook"
LOW_SOURCE_DIVERSITY_REASON = "low_source_diversity"
LOW_SAMPLE_SIZE_REASON = "low_sample_size"
UNRESOLVED_POSTMORTEM_ACTIONS_REASON = "unresolved_postmortem_actions"
LEARNING_PRIORITY_CLEAR_REASON = "learning_priority_clear"
REPORT_CRITICAL_REASON = "team_specialist_learning_priority_critical"
REPORT_WATCH_REASON = "team_specialist_learning_priority_watch"
EMPTY_SOURCES_REASON = "team_specialist_learning_priority_empty_sources"

ROW_REASON_CODES = (
    RECENT_FORECAST_ERROR_REASON,
    STALE_PLAYBOOK_REASON,
    LOW_SOURCE_DIVERSITY_REASON,
    LOW_SAMPLE_SIZE_REASON,
    UNRESOLVED_POSTMORTEM_ACTIONS_REASON,
    LEARNING_PRIORITY_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    REPORT_CRITICAL_REASON,
    REPORT_WATCH_REASON,
    RECENT_FORECAST_ERROR_REASON,
    STALE_PLAYBOOK_REASON,
    LOW_SOURCE_DIVERSITY_REASON,
    LOW_SAMPLE_SIZE_REASON,
    UNRESOLVED_POSTMORTEM_ACTIONS_REASON,
    LEARNING_PRIORITY_CLEAR_REASON,
    EMPTY_SOURCES_REASON,
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_REF_PREFIXES = ("public:", "memory:", "source:", "lesson:")
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
class TeamSpecialistLearningPriorityReportV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_CONFIG_VERSION
    recent_error_weight: Decimal = Decimal("0.350000")
    stale_playbook_weight: Decimal = Decimal("0.200000")
    source_diversity_weight: Decimal = Decimal("0.150000")
    sample_size_weight: Decimal = Decimal("0.150000")
    postmortem_action_weight: Decimal = Decimal("0.150000")
    max_recent_error_age_seconds: Decimal = Decimal("604800.000000")
    max_playbook_age_seconds: Decimal = Decimal("1209600.000000")
    min_source_family_count: Decimal = Decimal("3")
    min_sample_count: Decimal = Decimal("5")
    watch_priority_score: Decimal = Decimal("0.300000")
    critical_priority_score: Decimal = Decimal("0.700000")
    unresolved_postmortem_action_block_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "recent_error_weight",
            "stale_playbook_weight",
            "source_diversity_weight",
            "sample_size_weight",
            "postmortem_action_weight",
            "watch_priority_score",
            "critical_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_recent_error_age_seconds",
            "max_playbook_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_family_count",
            "min_sample_count",
            "unresolved_postmortem_action_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        _require_ratio_total(
            self.recent_error_weight,
            self.stale_playbook_weight,
            self.source_diversity_weight,
            self.sample_size_weight,
            self.postmortem_action_weight,
        )
        if self.watch_priority_score > self.critical_priority_score:
            raise ValueError("watch_priority_score must be less than or equal to critical_priority_score")
        require_paper_only_flags("specialist learning priority config", self)


@dataclass(frozen=True)
class TeamSpecialistLearningPriorityInputV2:
    team_id: str
    specialist_id: str
    memory_key: str
    observed_at: datetime
    playbook_last_reviewed_at: datetime
    forecast_error_ratio: Decimal
    source_family_count: Decimal
    sample_count: Decimal
    unresolved_postmortem_action_count: Decimal
    public_memory_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "memory_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "playbook_last_reviewed_at",
            _as_utc("playbook_last_reviewed_at", self.playbook_last_reviewed_at),
        )
        object.__setattr__(
            self,
            "forecast_error_ratio",
            _normalize_ratio("forecast_error_ratio", self.forecast_error_ratio),
        )
        for field_name in (
            "source_family_count",
            "sample_count",
            "unresolved_postmortem_action_count",
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
        require_paper_only_flags("specialist learning priority input", self)


@dataclass(frozen=True)
class TeamSpecialistLearningPriorityRowV2:
    team_id: str
    specialist_id: str
    memory_count: Decimal
    latest_observed_at: datetime
    oldest_playbook_last_reviewed_at: datetime
    max_forecast_error_ratio: Decimal
    min_source_family_count: Decimal
    min_sample_count: Decimal
    unresolved_postmortem_action_count: Decimal
    recent_forecast_error_component: Decimal
    stale_playbook_component: Decimal
    source_diversity_gap: Decimal
    sample_size_gap: Decimal
    postmortem_action_component: Decimal
    priority_score: Decimal
    row_status: str
    public_memory_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "memory_count",
            "min_source_family_count",
            "min_sample_count",
            "unresolved_postmortem_action_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "oldest_playbook_last_reviewed_at",
            _as_utc(
                "oldest_playbook_last_reviewed_at",
                self.oldest_playbook_last_reviewed_at,
            ),
        )
        for field_name in (
            "max_forecast_error_ratio",
            "recent_forecast_error_component",
            "stale_playbook_component",
            "source_diversity_gap",
            "sample_size_gap",
            "postmortem_action_component",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
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
        require_paper_only_flags("specialist learning priority row", self)


@dataclass(frozen=True)
class TeamSpecialistLearningPriorityReportV2:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    specialist_team_count: Decimal
    memory_count: Decimal
    critical_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[TeamSpecialistLearningPriorityRowV2, ...]
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
            "memory_count",
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
        require_paper_only_flags("specialist learning priority report", self)


def build_team_specialist_learning_priority_report_v2(
    inputs: list[TeamSpecialistLearningPriorityInputV2]
    | tuple[TeamSpecialistLearningPriorityInputV2, ...],
    *,
    config: TeamSpecialistLearningPriorityReportV2Config,
    generated_at: datetime,
) -> TeamSpecialistLearningPriorityReportV2:
    if type(config) is not TeamSpecialistLearningPriorityReportV2Config:
        raise ValueError("config must be a TeamSpecialistLearningPriorityReportV2Config")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    _validate_input_dates(rows, generated_at_utc)
    priority_rows = tuple(
        sorted(
            (
                _priority_row(team_id, specialist_id, group, config, generated_at_utc)
                for team_id, specialist_id, group in _input_groups(rows)
            ),
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
        memory_count=_sum_rows(priority_rows, "memory_count"),
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
    return TeamSpecialistLearningPriorityReportV2(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_learning_priority_report_v2_payload(
    report: TeamSpecialistLearningPriorityReportV2,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistLearningPriorityReportV2:
        raise ValueError("report must be a TeamSpecialistLearningPriorityReportV2")
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_public_payload("specialist learning priority payload", payload)
    return _tupleify_payload_collections(payload)


def _normalize_inputs(
    inputs: list[TeamSpecialistLearningPriorityInputV2]
    | tuple[TeamSpecialistLearningPriorityInputV2, ...],
) -> tuple[TeamSpecialistLearningPriorityInputV2, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    for row in rows:
        if type(row) is not TeamSpecialistLearningPriorityInputV2:
            raise ValueError("inputs must contain TeamSpecialistLearningPriorityInputV2 values")
        require_paper_only_flags("input", row)
    return rows


def _validate_input_dates(
    rows: tuple[TeamSpecialistLearningPriorityInputV2, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if row.playbook_last_reviewed_at > generated_at:
            raise ValueError("playbook_last_reviewed_at must be on or before generated_at")


def _input_groups(
    rows: tuple[TeamSpecialistLearningPriorityInputV2, ...],
) -> tuple[
    tuple[str, str, tuple[TeamSpecialistLearningPriorityInputV2, ...]],
    ...,
]:
    keys = tuple(sorted({(row.team_id, row.specialist_id) for row in rows}))
    return tuple(
        (
            team_id,
            specialist_id,
            tuple(
                row
                for row in rows
                if row.team_id == team_id and row.specialist_id == specialist_id
            ),
        )
        for team_id, specialist_id in keys
    )


def _priority_row(
    team_id: str,
    specialist_id: str,
    rows: tuple[TeamSpecialistLearningPriorityInputV2, ...],
    config: TeamSpecialistLearningPriorityReportV2Config,
    generated_at: datetime,
) -> TeamSpecialistLearningPriorityRowV2:
    recent_component = max(_recent_error_component(row, config, generated_at) for row in rows)
    stale_component = max(_stale_playbook_component(row, config, generated_at) for row in rows)
    source_gap = max(_count_gap(row.source_family_count, config.min_source_family_count) for row in rows)
    sample_gap = max(_count_gap(row.sample_count, config.min_sample_count) for row in rows)
    postmortem_component = _postmortem_action_component(rows, config)
    priority_score = _priority_score(
        recent_component,
        stale_component,
        source_gap,
        sample_gap,
        postmortem_component,
        config,
    )
    row_status = _row_status(priority_score, config)
    public_memory_refs = tuple(
        sorted({reference for row in rows for reference in row.public_memory_refs}),
    )
    row_parts = dict(
        team_id=team_id,
        specialist_id=specialist_id,
        memory_count=_count(len({row.memory_key for row in rows})),
        latest_observed_at=max(row.observed_at for row in rows),
        oldest_playbook_last_reviewed_at=min(row.playbook_last_reviewed_at for row in rows),
        max_forecast_error_ratio=max(row.forecast_error_ratio for row in rows),
        min_source_family_count=min(row.source_family_count for row in rows),
        min_sample_count=min(row.sample_count for row in rows),
        unresolved_postmortem_action_count=_sum_inputs(
            rows,
            "unresolved_postmortem_action_count",
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
        recent_forecast_error_component=recent_component,
        stale_playbook_component=stale_component,
        source_diversity_gap=source_gap,
        sample_size_gap=sample_gap,
        postmortem_action_component=postmortem_component,
        priority_score=priority_score,
        row_status=row_status,
        public_memory_refs=public_memory_refs,
        reason_codes=_row_reason_codes(
            row_status,
            recent_component,
            stale_component,
            source_gap,
            sample_gap,
            postmortem_component,
        ),
    )
    return TeamSpecialistLearningPriorityRowV2(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _recent_error_component(
    row: TeamSpecialistLearningPriorityInputV2,
    config: TeamSpecialistLearningPriorityReportV2Config,
    generated_at: datetime,
) -> Decimal:
    age_seconds = _age_seconds(generated_at, row.observed_at)
    if age_seconds >= config.max_recent_error_age_seconds:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        freshness = (config.max_recent_error_age_seconds - age_seconds) / config.max_recent_error_age_seconds
        return _clamp_ratio(row.forecast_error_ratio * freshness)


def _stale_playbook_component(
    row: TeamSpecialistLearningPriorityInputV2,
    config: TeamSpecialistLearningPriorityReportV2Config,
    generated_at: datetime,
) -> Decimal:
    age_seconds = _age_seconds(generated_at, row.playbook_last_reviewed_at)
    if age_seconds <= config.max_playbook_age_seconds:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (age_seconds - config.max_playbook_age_seconds)
            / config.max_playbook_age_seconds,
        )


def _count_gap(value: Decimal, target: Decimal) -> Decimal:
    if value >= target:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((target - value) / target)


def _postmortem_action_component(
    rows: tuple[TeamSpecialistLearningPriorityInputV2, ...],
    config: TeamSpecialistLearningPriorityReportV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            _sum_inputs(rows, "unresolved_postmortem_action_count")
            / config.unresolved_postmortem_action_block_count,
        )


def _priority_score(
    recent_component: Decimal,
    stale_component: Decimal,
    source_gap: Decimal,
    sample_gap: Decimal,
    postmortem_component: Decimal,
    config: TeamSpecialistLearningPriorityReportV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            recent_component * config.recent_error_weight
            + stale_component * config.stale_playbook_weight
            + source_gap * config.source_diversity_weight
            + sample_gap * config.sample_size_weight
            + postmortem_component * config.postmortem_action_weight,
        )


def _row_reason_codes(
    row_status: str,
    recent_component: Decimal,
    stale_component: Decimal,
    source_gap: Decimal,
    sample_gap: Decimal,
    postmortem_component: Decimal,
) -> tuple[str, ...]:
    if row_status == "clear":
        return (LEARNING_PRIORITY_CLEAR_REASON,)
    codes: set[str] = set()
    if recent_component > ZERO_RATIO:
        codes.add(RECENT_FORECAST_ERROR_REASON)
    if stale_component > ZERO_RATIO:
        codes.add(STALE_PLAYBOOK_REASON)
    if source_gap > ZERO_RATIO:
        codes.add(LOW_SOURCE_DIVERSITY_REASON)
    if sample_gap > ZERO_RATIO:
        codes.add(LOW_SAMPLE_SIZE_REASON)
    if postmortem_component > ZERO_RATIO:
        codes.add(UNRESOLVED_POSTMORTEM_ACTIONS_REASON)
    if not codes:
        codes.add(LEARNING_PRIORITY_CLEAR_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistLearningPriorityRowV2, ...],
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
        codes.add(LEARNING_PRIORITY_CLEAR_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _row_status(
    priority_score: Decimal,
    config: TeamSpecialistLearningPriorityReportV2Config,
) -> str:
    if priority_score >= config.critical_priority_score:
        return "critical"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "clear"


def _report_status(rows: tuple[TeamSpecialistLearningPriorityRowV2, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.row_status == "critical" for row in rows):
        return "critical"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _priority_row_sort_key(
    row: TeamSpecialistLearningPriorityRowV2,
) -> tuple[int, Decimal, str, str]:
    return (
        -_status_rank(row.row_status),
        -row.priority_score,
        row.team_id,
        row.specialist_id,
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


def _sum_inputs(
    rows: tuple[TeamSpecialistLearningPriorityInputV2, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _sum_rows(
    rows: tuple[TeamSpecialistLearningPriorityRowV2, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _average_priority_score(rows: tuple[TeamSpecialistLearningPriorityRowV2, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.priority_score for row in rows), ZERO_RATIO) / Decimal(len(rows)),
        )


def _validate_row(row: TeamSpecialistLearningPriorityRowV2) -> None:
    if row.memory_count <= ZERO_COUNT:
        raise ValueError("memory_count must be positive")
    expected_score = _clamp_ratio(
        row.recent_forecast_error_component * Decimal("0.350000")
        + row.stale_playbook_component * Decimal("0.200000")
        + row.source_diversity_gap * Decimal("0.150000")
        + row.sample_size_gap * Decimal("0.150000")
        + row.postmortem_action_component * Decimal("0.150000"),
    )
    if row.priority_score != expected_score:
        raise ValueError("priority_score must match priority components")
    if row.row_status != _row_status(
        row.priority_score,
        TeamSpecialistLearningPriorityReportV2Config(),
    ):
        raise ValueError("row_status must match priority_score")
    if row.reason_codes != _row_reason_codes(
        row.row_status,
        row.recent_forecast_error_component,
        row.stale_playbook_component,
        row.source_diversity_gap,
        row.sample_size_gap,
        row.postmortem_action_component,
    ):
        raise ValueError("reason_codes must match priority components")


def _validate_report(report: TeamSpecialistLearningPriorityReportV2) -> None:
    if report.team_count != _count(len({row.team_id for row in report.priority_rows})):
        raise ValueError("team_count must match priority_rows")
    if report.specialist_team_count != _count(
        len({(row.team_id, row.specialist_id) for row in report.priority_rows}),
    ):
        raise ValueError("specialist_team_count must match priority_rows")
    if report.memory_count != _sum_rows(report.priority_rows, "memory_count"):
        raise ValueError("memory_count must match priority_rows")
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
    rows: tuple[TeamSpecialistLearningPriorityRowV2, ...],
) -> tuple[TeamSpecialistLearningPriorityRowV2, ...]:
    if type(rows) is not tuple:
        raise ValueError("priority_rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistLearningPriorityRowV2:
            raise ValueError("priority_rows must contain TeamSpecialistLearningPriorityRowV2 values")
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


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return value.quantize(RATIO_QUANTUM)


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
    if value not in TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or critical")


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


def _row_digest(row: TeamSpecialistLearningPriorityRowV2) -> str:
    return _digest_public(_row_digest_parts(row))


def _report_digest(report: TeamSpecialistLearningPriorityReportV2) -> str:
    return _digest_public(_report_digest_parts(report))


def _row_digest_parts(row: TeamSpecialistLearningPriorityRowV2) -> dict[str, object]:
    return {
        "team_id": row.team_id,
        "specialist_id": row.specialist_id,
        "memory_count": row.memory_count,
        "latest_observed_at": row.latest_observed_at,
        "oldest_playbook_last_reviewed_at": row.oldest_playbook_last_reviewed_at,
        "max_forecast_error_ratio": row.max_forecast_error_ratio,
        "min_source_family_count": row.min_source_family_count,
        "min_sample_count": row.min_sample_count,
        "unresolved_postmortem_action_count": row.unresolved_postmortem_action_count,
        "recent_forecast_error_component": row.recent_forecast_error_component,
        "stale_playbook_component": row.stale_playbook_component,
        "source_diversity_gap": row.source_diversity_gap,
        "sample_size_gap": row.sample_size_gap,
        "postmortem_action_component": row.postmortem_action_component,
        "priority_score": row.priority_score,
        "row_status": row.row_status,
        "public_memory_refs": row.public_memory_refs,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_parts(report: TeamSpecialistLearningPriorityReportV2) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "team_count": report.team_count,
        "specialist_team_count": report.specialist_team_count,
        "memory_count": report.memory_count,
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


def _digest_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    if isinstance(value, dict):
        return {
            key: _digest_ready(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, (list, tuple)):
        return [_digest_ready(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ValueError("value is not digest serializable")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"public payload keys must be strings for {label}")
            _reject_public_text("public key", key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_public_text("public value", value)


def _reject_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_TEXT_BLOCKS):
        raise ValueError(f"unsafe public value in {field_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _tupleify_payload_collections(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _tupleify_payload_collections(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_tupleify_payload_collections(item) for item in value)
    return value


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_LEARNING_PRIORITY_REPORT_V2_STATUSES",
    "TeamSpecialistLearningPriorityReportV2Config",
    "TeamSpecialistLearningPriorityInputV2",
    "TeamSpecialistLearningPriorityRowV2",
    "TeamSpecialistLearningPriorityReportV2",
    "build_team_specialist_learning_priority_report_v2",
    "team_specialist_learning_priority_report_v2_payload",
)
