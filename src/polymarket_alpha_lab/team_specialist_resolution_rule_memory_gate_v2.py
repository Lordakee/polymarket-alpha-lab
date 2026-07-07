"""Readonly Phase 1 gate for specialist resolution-rule memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_SPECIALIST_RESOLUTION_RULE_MEMORY_GATE_V2_CONFIG_VERSION = (
    "team-specialist-resolution-rule-memory-gate-v2"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE_COUNT = Decimal("1").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)

ROW_STATUSES = ("blocked", "watch", "pass")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "category_match",
    "category_mismatch",
    "rule_template_match",
    "rule_template_mismatch",
    "outcome_sample_size_sufficient",
    "outcome_sample_size_watch",
    "outcome_sample_size_insufficient",
    "recent_error_rate_low",
    "recent_error_rate_watch",
    "recent_error_rate_high",
    "source_hierarchy_familiarity_strong",
    "source_hierarchy_familiarity_watch",
    "source_hierarchy_familiarity_weak",
    "resolution_rule_memory_recent",
    "resolution_rule_memory_watch",
    "resolution_rule_memory_stale",
)
REPORT_REASON_CODES = (
    "no_resolution_rule_memory_rows_supplied",
    "category_mismatch_present",
    "rule_template_mismatch_present",
    "outcome_sample_size_below_minimum_present",
    "recent_error_rate_above_limit_present",
    "source_hierarchy_familiarity_below_minimum_present",
    "stale_resolution_rule_memory_present",
    "resolution_rule_memory_experience_ready",
)
UNSAFE_PUBLIC_TERMS = (
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
    "DEFAULT_TEAM_SPECIALIST_RESOLUTION_RULE_MEMORY_GATE_V2_CONFIG_VERSION",
    "TeamSpecialistResolutionRuleMemoryGateV2Config",
    "TeamSpecialistResolutionRuleMemoryGateV2Memory",
    "TeamSpecialistResolutionRuleMemoryGateV2Row",
    "TeamSpecialistResolutionRuleMemoryGateV2Report",
    "build_team_specialist_resolution_rule_memory_gate_v2",
    "team_specialist_resolution_rule_memory_gate_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistResolutionRuleMemoryGateV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_RESOLUTION_RULE_MEMORY_GATE_V2_CONFIG_VERSION
    )
    target_team_id: str = "macro_rates"
    target_category_id: str = "finance.macro.rates"
    target_rule_template_id: str = "generic-resolution-rule-template"
    min_outcome_sample_size: Decimal = Decimal("12")
    watch_min_outcome_sample_size: Decimal = Decimal("6")
    max_recent_error_rate: Decimal = Decimal("0.150000")
    watch_max_recent_error_rate: Decimal = Decimal("0.250000")
    min_source_hierarchy_familiarity_score: Decimal = Decimal("0.750000")
    watch_min_source_hierarchy_familiarity_score: Decimal = Decimal("0.550000")
    max_resolution_rule_age_seconds: Decimal = Decimal("15552000.000000")
    watch_max_resolution_rule_age_seconds: Decimal = Decimal("31536000.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        target_team_id, target_category_id = require_team_category_pair(
            "target_team_id",
            self.target_team_id,
            "target_category_id",
            self.target_category_id,
        )
        object.__setattr__(self, "target_team_id", target_team_id)
        object.__setattr__(self, "target_category_id", target_category_id)
        _require_public_string("target_category_id", self.target_category_id)
        _require_public_string("target_rule_template_id", self.target_rule_template_id)
        for field_name in (
            "min_outcome_sample_size",
            "watch_min_outcome_sample_size",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_recent_error_rate",
            "watch_max_recent_error_rate",
            "min_source_hierarchy_familiarity_score",
            "watch_min_source_hierarchy_familiarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_resolution_rule_age_seconds",
            "watch_max_resolution_rule_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _reject_unsafe_public_payload("resolution rule memory gate config", self)
        _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Config", self)


@dataclass(frozen=True)
class TeamSpecialistResolutionRuleMemoryGateV2Memory:
    memory_id: str
    team_id: str
    category_id: str
    specialist_id: str
    rule_template_id: str
    outcome_sample_size: Decimal
    recent_error_rate: Decimal
    source_hierarchy_familiarity_score: Decimal
    latest_resolution_rule_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("memory_id", self.memory_id)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("rule_template_id", self.rule_template_id)
        object.__setattr__(
            self,
            "outcome_sample_size",
            _normalize_nonnegative_count(
                "outcome_sample_size",
                self.outcome_sample_size,
            ),
        )
        object.__setattr__(
            self,
            "recent_error_rate",
            _normalize_ratio("recent_error_rate", self.recent_error_rate),
        )
        object.__setattr__(
            self,
            "source_hierarchy_familiarity_score",
            _normalize_ratio(
                "source_hierarchy_familiarity_score",
                self.source_hierarchy_familiarity_score,
            ),
        )
        object.__setattr__(
            self,
            "latest_resolution_rule_at",
            _as_utc("latest_resolution_rule_at", self.latest_resolution_rule_at),
        )
        _reject_unsafe_public_payload("resolution rule memory row", self)
        _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Memory", self)


@dataclass(frozen=True)
class TeamSpecialistResolutionRuleMemoryGateV2Row:
    memory_id: str
    team_id: str
    category_id: str
    specialist_id: str
    rule_template_id: str
    target_team_id: str
    target_category_id: str
    target_rule_template_id: str
    row_status: str
    category_match: Decimal
    rule_template_match: Decimal
    outcome_sample_size: Decimal
    recent_error_rate: Decimal
    source_hierarchy_familiarity_score: Decimal
    resolution_rule_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("memory_id", self.memory_id)
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        target_team_id, target_category_id = require_team_category_pair(
            "target_team_id",
            self.target_team_id,
            "target_category_id",
            self.target_category_id,
        )
        object.__setattr__(self, "target_team_id", target_team_id)
        object.__setattr__(self, "target_category_id", target_category_id)
        _require_public_string("category_id", self.category_id)
        _require_public_string("target_category_id", self.target_category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("rule_template_id", self.rule_template_id)
        _require_public_string("target_rule_template_id", self.target_rule_template_id)
        _require_member("row_status", self.row_status, ROW_STATUSES)
        for field_name in ("category_match", "rule_template_match"):
            object.__setattr__(
                self,
                field_name,
                _normalize_binary_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_sample_size",
            _normalize_nonnegative_count(
                "outcome_sample_size",
                self.outcome_sample_size,
            ),
        )
        for field_name in (
            "recent_error_rate",
            "source_hierarchy_familiarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_rule_age_seconds",
            _normalize_nonnegative_seconds(
                "resolution_rule_age_seconds",
                self.resolution_rule_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("resolution rule memory gate row", self)
        _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Row", self)
        _validate_row(self)


@dataclass(frozen=True)
class TeamSpecialistResolutionRuleMemoryGateV2Report:
    generated_at: datetime
    config_version: str
    target_team_id: str
    target_category_id: str
    target_rule_template_id: str
    report_status: str
    source_memory_count: Decimal
    row_count: Decimal
    team_count: Decimal
    category_count: Decimal
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    category_mismatch_count: Decimal
    rule_template_mismatch_count: Decimal
    outcome_sample_size_below_minimum_count: Decimal
    recent_error_rate_above_limit_count: Decimal
    source_hierarchy_familiarity_below_minimum_count: Decimal
    stale_resolution_rule_memory_count: Decimal
    average_recent_error_rate: Decimal
    average_source_hierarchy_familiarity_score: Decimal
    rows: tuple[TeamSpecialistResolutionRuleMemoryGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        target_team_id, target_category_id = require_team_category_pair(
            "target_team_id",
            self.target_team_id,
            "target_category_id",
            self.target_category_id,
        )
        object.__setattr__(self, "target_team_id", target_team_id)
        object.__setattr__(self, "target_category_id", target_category_id)
        _require_public_string("target_category_id", self.target_category_id)
        _require_public_string("target_rule_template_id", self.target_rule_template_id)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "source_memory_count",
            "row_count",
            "team_count",
            "category_count",
            "specialist_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "category_mismatch_count",
            "rule_template_mismatch_count",
            "outcome_sample_size_below_minimum_count",
            "recent_error_rate_above_limit_count",
            "source_hierarchy_familiarity_below_minimum_count",
            "stale_resolution_rule_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_recent_error_rate",
            "average_source_hierarchy_familiarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("resolution rule memory gate report", self)
        _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_team_specialist_resolution_rule_memory_gate_v2(
    rows: list[TeamSpecialistResolutionRuleMemoryGateV2Memory]
    | tuple[TeamSpecialistResolutionRuleMemoryGateV2Memory, ...],
    *,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistResolutionRuleMemoryGateV2Report:
    if type(config) is not TeamSpecialistResolutionRuleMemoryGateV2Config:
        raise ValueError(
            "config must be a TeamSpecialistResolutionRuleMemoryGateV2Config",
        )
    _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_source_rows(rows)
    report_rows = tuple(
        sorted(
            (
                _row_for_memory(row, config=config, generated_at=generated_at_utc)
                for row in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    pass_count = _status_count(report_rows, "pass")
    watch_count = _status_count(report_rows, "watch")
    blocked_count = _status_count(report_rows, "blocked")
    category_mismatch_count = _reason_count(report_rows, "category_mismatch")
    rule_template_mismatch_count = _reason_count(report_rows, "rule_template_mismatch")
    outcome_below_count = _reason_count(report_rows, "outcome_sample_size_watch") + _reason_count(
        report_rows,
        "outcome_sample_size_insufficient",
    )
    error_above_count = _reason_count(report_rows, "recent_error_rate_watch") + _reason_count(
        report_rows,
        "recent_error_rate_high",
    )
    source_below_count = _reason_count(
        report_rows,
        "source_hierarchy_familiarity_watch",
    ) + _reason_count(report_rows, "source_hierarchy_familiarity_weak")
    stale_count = _reason_count(report_rows, "resolution_rule_memory_watch") + _reason_count(
        report_rows,
        "resolution_rule_memory_stale",
    )

    return TeamSpecialistResolutionRuleMemoryGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        target_team_id=config.target_team_id,
        target_category_id=config.target_category_id,
        target_rule_template_id=config.target_rule_template_id,
        report_status=_report_status(report_rows, blocked_count, watch_count),
        source_memory_count=_count(len(source_rows)),
        row_count=_count(len(report_rows)),
        team_count=_count(len({row.team_id for row in report_rows})),
        category_count=_count(len({row.category_id for row in report_rows})),
        specialist_count=_count(len({row.specialist_id for row in report_rows})),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        category_mismatch_count=category_mismatch_count,
        rule_template_mismatch_count=rule_template_mismatch_count,
        outcome_sample_size_below_minimum_count=outcome_below_count,
        recent_error_rate_above_limit_count=error_above_count,
        source_hierarchy_familiarity_below_minimum_count=source_below_count,
        stale_resolution_rule_memory_count=stale_count,
        average_recent_error_rate=_average_ratio(
            tuple(row.recent_error_rate for row in report_rows),
        ),
        average_source_hierarchy_familiarity_score=_average_ratio(
            tuple(row.source_hierarchy_familiarity_score for row in report_rows),
        ),
        rows=report_rows,
        reason_codes=_report_reason_codes(
            report_rows,
            len(source_rows),
            category_mismatch_count=category_mismatch_count,
            rule_template_mismatch_count=rule_template_mismatch_count,
            outcome_below_count=outcome_below_count,
            error_above_count=error_above_count,
            source_below_count=source_below_count,
            stale_count=stale_count,
        ),
    )


def team_specialist_resolution_rule_memory_gate_v2_payload(
    report: TeamSpecialistResolutionRuleMemoryGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistResolutionRuleMemoryGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("resolution rule memory gate report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("resolution rule memory gate payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamSpecialistResolutionRuleMemoryGateV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("resolution rule memory gate payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
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


def _validate_config(config: TeamSpecialistResolutionRuleMemoryGateV2Config) -> None:
    if config.watch_min_outcome_sample_size > config.min_outcome_sample_size:
        raise ValueError(
            "watch_min_outcome_sample_size must not exceed min_outcome_sample_size",
        )
    if config.max_recent_error_rate > config.watch_max_recent_error_rate:
        raise ValueError("max_recent_error_rate must not exceed watch_max_recent_error_rate")
    if (
        config.watch_min_source_hierarchy_familiarity_score
        > config.min_source_hierarchy_familiarity_score
    ):
        raise ValueError(
            "watch_min_source_hierarchy_familiarity_score must not exceed "
            "min_source_hierarchy_familiarity_score",
        )
    if config.max_resolution_rule_age_seconds > config.watch_max_resolution_rule_age_seconds:
        raise ValueError(
            "max_resolution_rule_age_seconds must not exceed "
            "watch_max_resolution_rule_age_seconds",
        )


def _normalize_source_rows(
    value: object,
) -> tuple[TeamSpecialistResolutionRuleMemoryGateV2Memory, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResolutionRuleMemoryGateV2Memory:
            raise ValueError(
                "rows must contain TeamSpecialistResolutionRuleMemoryGateV2Memory values",
            )
        _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Memory", row)
        if row.memory_id in seen_ids:
            raise ValueError("duplicate memory_id values are not allowed")
        seen_ids.add(row.memory_id)
    return rows


def _row_for_memory(
    row: TeamSpecialistResolutionRuleMemoryGateV2Memory,
    *,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
    generated_at: datetime,
) -> TeamSpecialistResolutionRuleMemoryGateV2Row:
    category_matches = (
        row.team_id == config.target_team_id and row.category_id == config.target_category_id
    )
    rule_template_matches = row.rule_template_id == config.target_rule_template_id
    resolution_rule_age_seconds = _age_seconds(row.latest_resolution_rule_at, generated_at)
    reason_codes = _row_reason_codes(
        category_matches=category_matches,
        rule_template_matches=rule_template_matches,
        outcome_sample_size=row.outcome_sample_size,
        recent_error_rate=row.recent_error_rate,
        source_hierarchy_familiarity_score=row.source_hierarchy_familiarity_score,
        resolution_rule_age_seconds=resolution_rule_age_seconds,
        config=config,
    )

    return TeamSpecialistResolutionRuleMemoryGateV2Row(
        memory_id=row.memory_id,
        team_id=row.team_id,
        category_id=row.category_id,
        specialist_id=row.specialist_id,
        rule_template_id=row.rule_template_id,
        target_team_id=config.target_team_id,
        target_category_id=config.target_category_id,
        target_rule_template_id=config.target_rule_template_id,
        row_status=_row_status(reason_codes),
        category_match=ONE_COUNT if category_matches else ZERO_COUNT,
        rule_template_match=ONE_COUNT if rule_template_matches else ZERO_COUNT,
        outcome_sample_size=row.outcome_sample_size,
        recent_error_rate=row.recent_error_rate,
        source_hierarchy_familiarity_score=row.source_hierarchy_familiarity_score,
        resolution_rule_age_seconds=resolution_rule_age_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    category_matches: bool,
    rule_template_matches: bool,
    outcome_sample_size: Decimal,
    recent_error_rate: Decimal,
    source_hierarchy_familiarity_score: Decimal,
    resolution_rule_age_seconds: Decimal,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
) -> tuple[str, ...]:
    codes = [
        "category_match" if category_matches else "category_mismatch",
        "rule_template_match" if rule_template_matches else "rule_template_mismatch",
        _outcome_sample_size_reason(outcome_sample_size, config),
        _recent_error_rate_reason(recent_error_rate, config),
        _source_hierarchy_familiarity_reason(
            source_hierarchy_familiarity_score,
            config,
        ),
        _resolution_rule_recency_reason(resolution_rule_age_seconds, config),
    ]
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _outcome_sample_size_reason(
    value: Decimal,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
) -> str:
    if value >= config.min_outcome_sample_size:
        return "outcome_sample_size_sufficient"
    if value >= config.watch_min_outcome_sample_size:
        return "outcome_sample_size_watch"
    return "outcome_sample_size_insufficient"


def _recent_error_rate_reason(
    value: Decimal,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
) -> str:
    if value <= config.max_recent_error_rate:
        return "recent_error_rate_low"
    if value <= config.watch_max_recent_error_rate:
        return "recent_error_rate_watch"
    return "recent_error_rate_high"


def _source_hierarchy_familiarity_reason(
    value: Decimal,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
) -> str:
    if value >= config.min_source_hierarchy_familiarity_score:
        return "source_hierarchy_familiarity_strong"
    if value >= config.watch_min_source_hierarchy_familiarity_score:
        return "source_hierarchy_familiarity_watch"
    return "source_hierarchy_familiarity_weak"


def _resolution_rule_recency_reason(
    value: Decimal,
    config: TeamSpecialistResolutionRuleMemoryGateV2Config,
) -> str:
    if value <= config.max_resolution_rule_age_seconds:
        return "resolution_rule_memory_recent"
    if value <= config.watch_max_resolution_rule_age_seconds:
        return "resolution_rule_memory_watch"
    return "resolution_rule_memory_stale"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code in reason_codes for code in _BLOCKING_ROW_REASONS):
        return "blocked"
    if any(code in reason_codes for code in _WATCH_ROW_REASONS):
        return "watch"
    return "pass"


_BLOCKING_ROW_REASONS = (
    "category_mismatch",
    "rule_template_mismatch",
    "outcome_sample_size_insufficient",
    "recent_error_rate_high",
    "source_hierarchy_familiarity_weak",
    "resolution_rule_memory_stale",
)
_WATCH_ROW_REASONS = (
    "outcome_sample_size_watch",
    "recent_error_rate_watch",
    "source_hierarchy_familiarity_watch",
    "resolution_rule_memory_watch",
)


def _row_sort_key(
    row: TeamSpecialistResolutionRuleMemoryGateV2Row,
) -> tuple[int, Decimal, Decimal, str, str, str, str]:
    return (
        ROW_STATUSES.index(row.row_status),
        row.outcome_sample_size,
        row.recent_error_rate,
        row.team_id,
        row.category_id,
        row.specialist_id,
        row.memory_id,
    )


def _report_reason_codes(
    rows: tuple[TeamSpecialistResolutionRuleMemoryGateV2Row, ...],
    source_row_count: int,
    *,
    category_mismatch_count: Decimal,
    rule_template_mismatch_count: Decimal,
    outcome_below_count: Decimal,
    error_above_count: Decimal,
    source_below_count: Decimal,
    stale_count: Decimal,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_resolution_rule_memory_rows_supplied",)
    codes: list[str] = []
    if category_mismatch_count > ZERO_COUNT:
        codes.append("category_mismatch_present")
    if rule_template_mismatch_count > ZERO_COUNT:
        codes.append("rule_template_mismatch_present")
    if outcome_below_count > ZERO_COUNT:
        codes.append("outcome_sample_size_below_minimum_present")
    if error_above_count > ZERO_COUNT:
        codes.append("recent_error_rate_above_limit_present")
    if source_below_count > ZERO_COUNT:
        codes.append("source_hierarchy_familiarity_below_minimum_present")
    if stale_count > ZERO_COUNT:
        codes.append("stale_resolution_rule_memory_present")
    if not codes and rows and all(row.row_status == "pass" for row in rows):
        codes.append("resolution_rule_memory_experience_ready")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _report_status(
    rows: tuple[TeamSpecialistResolutionRuleMemoryGateV2Row, ...],
    blocked_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not rows:
        return "blocked"
    if blocked_count > ZERO_COUNT:
        return "blocked"
    if watch_count > ZERO_COUNT:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[TeamSpecialistResolutionRuleMemoryGateV2Row, ...],
    row_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == row_status))


def _reason_count(
    rows: tuple[TeamSpecialistResolutionRuleMemoryGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_report_rows(
    value: object,
) -> tuple[TeamSpecialistResolutionRuleMemoryGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistResolutionRuleMemoryGateV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistResolutionRuleMemoryGateV2Row values",
            )
        _require_hard_flags("TeamSpecialistResolutionRuleMemoryGateV2Row", row)
        if row.memory_id in seen_ids:
            raise ValueError("duplicate memory_id values are not allowed")
        seen_ids.add(row.memory_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _validate_row(row: TeamSpecialistResolutionRuleMemoryGateV2Row) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.row_status != expected_status:
        raise ValueError("row_status must match reason_codes")
    if row.category_match == ONE_COUNT and "category_match" not in row.reason_codes:
        raise ValueError("category_match must match reason_codes")
    if row.category_match == ZERO_COUNT and "category_mismatch" not in row.reason_codes:
        raise ValueError("category_match must match reason_codes")
    if row.rule_template_match == ONE_COUNT and "rule_template_match" not in row.reason_codes:
        raise ValueError("rule_template_match must match reason_codes")
    if (
        row.rule_template_match == ZERO_COUNT
        and "rule_template_mismatch" not in row.reason_codes
    ):
        raise ValueError("rule_template_match must match reason_codes")


def _validate_report(report: TeamSpecialistResolutionRuleMemoryGateV2Report) -> None:
    if report.source_memory_count != report.row_count:
        raise ValueError("source_memory_count must match row_count")
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.category_count != _count(len({row.category_id for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.specialist_count != _count(len({row.specialist_id for row in report.rows})):
        raise ValueError("specialist_count must match rows")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "blocked_count": _status_count(report.rows, "blocked"),
        "category_mismatch_count": _reason_count(report.rows, "category_mismatch"),
        "rule_template_mismatch_count": _reason_count(
            report.rows,
            "rule_template_mismatch",
        ),
        "outcome_sample_size_below_minimum_count": _reason_count(
            report.rows,
            "outcome_sample_size_watch",
        )
        + _reason_count(report.rows, "outcome_sample_size_insufficient"),
        "recent_error_rate_above_limit_count": _reason_count(
            report.rows,
            "recent_error_rate_watch",
        )
        + _reason_count(report.rows, "recent_error_rate_high"),
        "source_hierarchy_familiarity_below_minimum_count": _reason_count(
            report.rows,
            "source_hierarchy_familiarity_watch",
        )
        + _reason_count(report.rows, "source_hierarchy_familiarity_weak"),
        "stale_resolution_rule_memory_count": _reason_count(
            report.rows,
            "resolution_rule_memory_watch",
        )
        + _reason_count(report.rows, "resolution_rule_memory_stale"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_recent_error_rate != _average_ratio(
        tuple(row.recent_error_rate for row in report.rows),
    ):
        raise ValueError("average_recent_error_rate must match rows")
    if report.average_source_hierarchy_familiarity_score != _average_ratio(
        tuple(row.source_hierarchy_familiarity_score for row in report.rows),
    ):
        raise ValueError("average_source_hierarchy_familiarity_score must match rows")
    if report.report_status != _report_status(
        report.rows,
        report.blocked_count,
        report.watch_count,
    ):
        raise ValueError("report_status must match rows")
    expected_reason_codes = _report_reason_codes(
        report.rows,
        int(report.source_memory_count),
        category_mismatch_count=report.category_mismatch_count,
        rule_template_mismatch_count=report.rule_template_mismatch_count,
        outcome_below_count=report.outcome_sample_size_below_minimum_count,
        error_above_count=report.recent_error_rate_above_limit_count,
        source_below_count=report.source_hierarchy_familiarity_below_minimum_count,
        stale_count=report.stale_resolution_rule_memory_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    for row in report.rows:
        if row.target_team_id != report.target_team_id:
            raise ValueError("row target_team_id must match report")
        if row.target_category_id != report.target_category_id:
            raise ValueError("row target_category_id must match report")
        if row.target_rule_template_id != report.target_rule_template_id:
            raise ValueError("row target_rule_template_id must match report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _report_digest(report: TeamSpecialistResolutionRuleMemoryGateV2Report) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / _count(len(values))).quantize(RATIO_QUANTUM)


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value > generated_at:
        return ZERO_SECONDS
    delta = generated_at - value
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * Decimal("86400")
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        ).quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_binary_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized not in (ZERO_COUNT, ONE_COUNT):
        raise ValueError(f"{field_name} must be 0 or 1")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in ROW_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
