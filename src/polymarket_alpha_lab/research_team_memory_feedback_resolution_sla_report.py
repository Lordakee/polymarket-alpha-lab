"""Pure in-memory report for team memory feedback resolution SLA."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_RESEARCH_TEAM_MEMORY_FEEDBACK_RESOLUTION_SLA_CONFIG_VERSION = (
    "research-team-memory-feedback-resolution-sla-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "feedback_resolution_sla_empty"
CLEAR_REASON = "feedback_resolution_sla_clear"
UNRESOLVED_AGE_BLOCK_REASON = "feedback_resolution_sla_unresolved_age_block"
UNRESOLVED_AGE_WATCH_REASON = "feedback_resolution_sla_unresolved_age_watch"
WRITEBACK_COMPLETENESS_BLOCK_REASON = (
    "feedback_resolution_sla_writeback_completeness_block"
)
WRITEBACK_COMPLETENESS_WATCH_REASON = (
    "feedback_resolution_sla_writeback_completeness_watch"
)
CALIBRATION_BACKLOG_BLOCK_REASON = "feedback_resolution_sla_calibration_backlog_block"
CALIBRATION_BACKLOG_WATCH_REASON = "feedback_resolution_sla_calibration_backlog_watch"
IMPACTED_DOMAIN_BLOCK_REASON = "feedback_resolution_sla_impacted_domain_block"
IMPACTED_DOMAIN_WATCH_REASON = "feedback_resolution_sla_impacted_domain_watch"
REVIEWER_AVAILABILITY_BLOCK_REASON = (
    "feedback_resolution_sla_reviewer_availability_block"
)
REVIEWER_AVAILABILITY_WATCH_REASON = (
    "feedback_resolution_sla_reviewer_availability_watch"
)
MANUAL_ESCALATION_BLOCK_REASON = "feedback_resolution_sla_manual_escalation_block"
MANUAL_ESCALATION_WATCH_REASON = "feedback_resolution_sla_manual_escalation_watch"

REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    UNRESOLVED_AGE_BLOCK_REASON,
    UNRESOLVED_AGE_WATCH_REASON,
    WRITEBACK_COMPLETENESS_BLOCK_REASON,
    WRITEBACK_COMPLETENESS_WATCH_REASON,
    CALIBRATION_BACKLOG_BLOCK_REASON,
    CALIBRATION_BACKLOG_WATCH_REASON,
    IMPACTED_DOMAIN_BLOCK_REASON,
    IMPACTED_DOMAIN_WATCH_REASON,
    REVIEWER_AVAILABILITY_BLOCK_REASON,
    REVIEWER_AVAILABILITY_WATCH_REASON,
    MANUAL_ESCALATION_BLOCK_REASON,
    MANUAL_ESCALATION_WATCH_REASON,
    CLEAR_REASON,
)
BLOCK_REASONS = frozenset(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code.endswith("_block")
) | frozenset((EMPTY_REASON,))
WATCH_REASONS = frozenset(
    reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code.endswith("_watch")
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "private",
    "token",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "private",
    "token",
)

_PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "team_category_count",
        "feedback_count",
        "unresolved_feedback_count",
        "max_unresolved_feedback_age_seconds",
        "writeback_completed_count",
        "writeback_completeness_ratio",
        "calibration_backlog_count",
        "impacted_domain_count",
        "min_reviewer_availability_ratio",
        "manual_escalation_urgency_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_FIELDS = frozenset(
    (
        "category_id",
        "team_id",
        "row_status",
        "feedback_count",
        "unresolved_feedback_count",
        "max_unresolved_feedback_age_seconds",
        "writeback_completed_count",
        "writeback_completeness_ratio",
        "calibration_backlog_count",
        "impacted_domain_count",
        "min_reviewer_availability_ratio",
        "manual_escalation_urgency_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamMemoryFeedbackResolutionSlaConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_MEMORY_FEEDBACK_RESOLUTION_SLA_CONFIG_VERSION
    unresolved_watch_age_seconds: Decimal = Decimal("86400.000000")
    unresolved_block_age_seconds: Decimal = Decimal("259200.000000")
    writeback_watch_ratio_floor: Decimal = Decimal("0.800000")
    writeback_block_ratio_floor: Decimal = Decimal("0.500000")
    calibration_backlog_watch_count: Decimal = Decimal("1")
    calibration_backlog_block_count: Decimal = Decimal("3")
    impacted_domain_watch_count: Decimal = Decimal("2")
    impacted_domain_block_count: Decimal = Decimal("3")
    reviewer_availability_watch_ratio_floor: Decimal = Decimal("0.500000")
    reviewer_availability_block_ratio_floor: Decimal = Decimal("0.250000")
    manual_escalation_watch_urgency: Decimal = Decimal("0.500000")
    manual_escalation_block_urgency: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "unresolved_watch_age_seconds",
            "unresolved_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "writeback_watch_ratio_floor",
            "writeback_block_ratio_floor",
            "reviewer_availability_watch_ratio_floor",
            "reviewer_availability_block_ratio_floor",
            "manual_escalation_watch_urgency",
            "manual_escalation_block_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_backlog_watch_count",
            "calibration_backlog_block_count",
            "impacted_domain_watch_count",
            "impacted_domain_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryFeedbackResolutionSlaInput(_FinalPublicDataclass):
    feedback_key: str
    team_id: str
    category_id: str
    feedback_created_at: datetime
    resolved_at: datetime | None
    writeback_completed_at: datetime | None
    calibration_required: bool
    calibration_completed_at: datetime | None
    impacted_domain_ids: tuple[str, ...]
    required_reviewer_count: Decimal
    available_reviewer_count: Decimal
    manual_escalation_requested: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feedback_key",
            _require_canonical_string("feedback_key", self.feedback_key),
        )
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(
            self,
            "feedback_created_at",
            _as_utc("feedback_created_at", self.feedback_created_at),
        )
        object.__setattr__(self, "resolved_at", _as_optional_utc("resolved_at", self.resolved_at))
        object.__setattr__(
            self,
            "writeback_completed_at",
            _as_optional_utc("writeback_completed_at", self.writeback_completed_at),
        )
        object.__setattr__(
            self,
            "calibration_completed_at",
            _as_optional_utc("calibration_completed_at", self.calibration_completed_at),
        )
        object.__setattr__(
            self,
            "impacted_domain_ids",
            _normalize_domain_ids(self.impacted_domain_ids),
        )
        object.__setattr__(
            self,
            "required_reviewer_count",
            _require_nonnegative_integral_decimal(
                "required_reviewer_count",
                self.required_reviewer_count,
            ),
        )
        object.__setattr__(
            self,
            "available_reviewer_count",
            _require_nonnegative_integral_decimal(
                "available_reviewer_count",
                self.available_reviewer_count,
            ),
        )
        if type(self.calibration_required) is not bool:
            raise ValueError("calibration_required must be a bool")
        if type(self.manual_escalation_requested) is not bool:
            raise ValueError("manual_escalation_requested must be a bool")
        _validate_input_time_sequence(self)
        if self.available_reviewer_count > self.required_reviewer_count:
            raise ValueError("available_reviewer_count must not exceed required_reviewer_count")
        if not self.calibration_required and self.calibration_completed_at is not None:
            raise ValueError("calibration_completed_at requires calibration_required")
        require_paper_only_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow(_FinalPublicDataclass):
    category_id: str
    team_id: str
    row_status: str
    feedback_count: Decimal
    unresolved_feedback_count: Decimal
    max_unresolved_feedback_age_seconds: Decimal
    writeback_completed_count: Decimal
    writeback_completeness_ratio: Decimal
    calibration_backlog_count: Decimal
    impacted_domain_count: Decimal
    min_reviewer_availability_ratio: Decimal
    manual_escalation_urgency_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "row_status", _require_status("row_status", self.row_status))
        for field_name in (
            "feedback_count",
            "unresolved_feedback_count",
            "writeback_completed_count",
            "calibration_backlog_count",
            "impacted_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_feedback_age_seconds",
            _require_nonnegative_seconds_decimal(
                "max_unresolved_feedback_age_seconds",
                self.max_unresolved_feedback_age_seconds,
            ),
        )
        for field_name in (
            "writeback_completeness_ratio",
            "min_reviewer_availability_ratio",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _validate_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("team category row", self)


@dataclass(frozen=True)
class ResearchTeamMemoryFeedbackResolutionSlaReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    team_category_count: Decimal
    feedback_count: Decimal
    unresolved_feedback_count: Decimal
    max_unresolved_feedback_age_seconds: Decimal
    writeback_completed_count: Decimal
    writeback_completeness_ratio: Decimal
    calibration_backlog_count: Decimal
    impacted_domain_count: Decimal
    min_reviewer_availability_ratio: Decimal
    manual_escalation_urgency_score: Decimal
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow, ...]
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
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "team_category_count",
            "feedback_count",
            "unresolved_feedback_count",
            "writeback_completed_count",
            "calibration_backlog_count",
            "impacted_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_feedback_age_seconds",
            _require_nonnegative_seconds_decimal(
                "max_unresolved_feedback_age_seconds",
                self.max_unresolved_feedback_age_seconds,
            ),
        )
        for field_name in (
            "writeback_completeness_ratio",
            "min_reviewer_availability_ratio",
            "manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        if type(self) is not ResearchTeamMemoryFeedbackResolutionSlaReport:
            raise ValueError(
                "report must be exactly ResearchTeamMemoryFeedbackResolutionSlaReport",
            )
        require_paper_only_flags("report", self)
        _validate_report(self)
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _validate_public_payload(payload)
        return payload


def build_research_team_memory_feedback_resolution_sla_report(
    input_rows: object,
    *,
    config: ResearchTeamMemoryFeedbackResolutionSlaConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamMemoryFeedbackResolutionSlaReport:
    if config is None:
        config = ResearchTeamMemoryFeedbackResolutionSlaConfig()
    if type(config) is not ResearchTeamMemoryFeedbackResolutionSlaConfig:
        raise ValueError("config must be a ResearchTeamMemoryFeedbackResolutionSlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    team_rows = _team_category_rows(rows, config=config, generated_at=generated_at_utc)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _status_from_reason_codes(_report_reason_codes(team_rows)),
        "team_category_count": _decimal_count(len(team_rows)),
        "feedback_count": _sum_decimal(team_rows, "feedback_count"),
        "unresolved_feedback_count": _sum_decimal(team_rows, "unresolved_feedback_count"),
        "max_unresolved_feedback_age_seconds": _max_decimal(
            team_rows,
            "max_unresolved_feedback_age_seconds",
        ),
        "writeback_completed_count": _sum_decimal(team_rows, "writeback_completed_count"),
        "writeback_completeness_ratio": _ratio(
            _sum_decimal(team_rows, "writeback_completed_count"),
            _sum_decimal(team_rows, "feedback_count"),
        ),
        "calibration_backlog_count": _sum_decimal(team_rows, "calibration_backlog_count"),
        "impacted_domain_count": _decimal_count(_total_impacted_domain_count(team_rows, rows)),
        "min_reviewer_availability_ratio": _min_ratio(
            team_rows,
            "min_reviewer_availability_ratio",
        ),
        "manual_escalation_urgency_score": _max_decimal(
            team_rows,
            "manual_escalation_urgency_score",
        ),
        "rows": team_rows,
        "reason_codes": _report_reason_codes(team_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchTeamMemoryFeedbackResolutionSlaReport(**values)


def research_team_memory_feedback_resolution_sla_report_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchTeamMemoryFeedbackResolutionSlaReport:
        return value.payload
    if type(value) is not dict:
        raise ValueError("payload source must be a report or dict")
    _validate_public_payload(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _team_category_rows(
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaInput, ...],
    *,
    config: ResearchTeamMemoryFeedbackResolutionSlaConfig,
    generated_at: datetime,
) -> tuple[ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow, ...]:
    groups: dict[tuple[str, str], list[ResearchTeamMemoryFeedbackResolutionSlaInput]] = {}
    for row in rows:
        groups.setdefault((row.category_id, row.team_id), []).append(row)
    return tuple(
        sorted(
            (
                _team_category_row(
                    category_id=category_id,
                    team_id=team_id,
                    rows=tuple(group_rows),
                    config=config,
                    generated_at=generated_at,
                )
                for (category_id, team_id), group_rows in groups.items()
            ),
            key=lambda row: (
                STATUS_RANK[row.row_status],
                row.category_id,
                row.team_id,
            ),
        ),
    )


def _team_category_row(
    *,
    category_id: str,
    team_id: str,
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaInput, ...],
    config: ResearchTeamMemoryFeedbackResolutionSlaConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow:
    unresolved_rows = tuple(row for row in rows if row.resolved_at is None)
    max_unresolved_age = _max_unresolved_age_seconds(unresolved_rows, generated_at)
    writeback_completed_count = _decimal_count(
        sum(row.writeback_completed_at is not None for row in rows),
    )
    feedback_count = _decimal_count(len(rows))
    calibration_backlog_count = _decimal_count(
        sum(
            row.calibration_required and row.calibration_completed_at is None
            for row in rows
        ),
    )
    impacted_domain_count = _decimal_count(
        len({domain_id for row in rows for domain_id in row.impacted_domain_ids}),
    )
    min_reviewer_ratio = _min_feedback_reviewer_availability_ratio(rows)
    urgency_score = _manual_escalation_urgency_score(
        unresolved_feedback_count=_decimal_count(len(unresolved_rows)),
        calibration_backlog_count=calibration_backlog_count,
        impacted_domain_count=impacted_domain_count,
        min_reviewer_availability_ratio=min_reviewer_ratio,
        manual_escalation_requested=any(row.manual_escalation_requested for row in rows),
        config=config,
    )
    reason_codes = _row_reason_codes(
        max_unresolved_feedback_age_seconds=max_unresolved_age,
        writeback_completeness_ratio=_ratio(writeback_completed_count, feedback_count),
        unresolved_feedback_count=_decimal_count(len(unresolved_rows)),
        calibration_backlog_count=calibration_backlog_count,
        impacted_domain_count=impacted_domain_count,
        min_reviewer_availability_ratio=min_reviewer_ratio,
        manual_escalation_urgency_score=urgency_score,
        config=config,
    )
    return ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow(
        category_id=category_id,
        team_id=team_id,
        row_status=_status_from_reason_codes(reason_codes),
        feedback_count=feedback_count,
        unresolved_feedback_count=_decimal_count(len(unresolved_rows)),
        max_unresolved_feedback_age_seconds=max_unresolved_age,
        writeback_completed_count=writeback_completed_count,
        writeback_completeness_ratio=_ratio(writeback_completed_count, feedback_count),
        calibration_backlog_count=calibration_backlog_count,
        impacted_domain_count=impacted_domain_count,
        min_reviewer_availability_ratio=min_reviewer_ratio,
        manual_escalation_urgency_score=urgency_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    max_unresolved_feedback_age_seconds: Decimal,
    writeback_completeness_ratio: Decimal,
    unresolved_feedback_count: Decimal,
    calibration_backlog_count: Decimal,
    impacted_domain_count: Decimal,
    min_reviewer_availability_ratio: Decimal,
    manual_escalation_urgency_score: Decimal,
    config: ResearchTeamMemoryFeedbackResolutionSlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if max_unresolved_feedback_age_seconds >= config.unresolved_block_age_seconds:
        reasons.append(UNRESOLVED_AGE_BLOCK_REASON)
    elif max_unresolved_feedback_age_seconds >= config.unresolved_watch_age_seconds:
        reasons.append(UNRESOLVED_AGE_WATCH_REASON)
    if unresolved_feedback_count == ZERO:
        if writeback_completeness_ratio < config.writeback_block_ratio_floor:
            reasons.append(WRITEBACK_COMPLETENESS_BLOCK_REASON)
        elif writeback_completeness_ratio < config.writeback_watch_ratio_floor:
            reasons.append(WRITEBACK_COMPLETENESS_WATCH_REASON)
    if calibration_backlog_count >= config.calibration_backlog_block_count:
        reasons.append(CALIBRATION_BACKLOG_BLOCK_REASON)
    elif calibration_backlog_count >= config.calibration_backlog_watch_count:
        reasons.append(CALIBRATION_BACKLOG_WATCH_REASON)
    if impacted_domain_count >= config.impacted_domain_block_count:
        reasons.append(IMPACTED_DOMAIN_BLOCK_REASON)
    elif impacted_domain_count >= config.impacted_domain_watch_count:
        reasons.append(IMPACTED_DOMAIN_WATCH_REASON)
    if min_reviewer_availability_ratio <= config.reviewer_availability_block_ratio_floor:
        reasons.append(REVIEWER_AVAILABILITY_BLOCK_REASON)
    elif min_reviewer_availability_ratio < config.reviewer_availability_watch_ratio_floor:
        reasons.append(REVIEWER_AVAILABILITY_WATCH_REASON)
    if manual_escalation_urgency_score >= config.manual_escalation_block_urgency:
        reasons.append(MANUAL_ESCALATION_BLOCK_REASON)
    elif manual_escalation_urgency_score >= config.manual_escalation_watch_urgency:
        reasons.append(MANUAL_ESCALATION_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code not in (EMPTY_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _manual_escalation_urgency_score(
    *,
    unresolved_feedback_count: Decimal,
    calibration_backlog_count: Decimal,
    impacted_domain_count: Decimal,
    min_reviewer_availability_ratio: Decimal,
    manual_escalation_requested: bool,
    config: ResearchTeamMemoryFeedbackResolutionSlaConfig,
) -> Decimal:
    if manual_escalation_requested:
        return ONE
    if unresolved_feedback_count == ZERO:
        return ZERO
    if (
        calibration_backlog_count >= config.calibration_backlog_watch_count
        or impacted_domain_count >= config.impacted_domain_watch_count
        or min_reviewer_availability_ratio <= config.reviewer_availability_watch_ratio_floor
    ):
        return config.manual_escalation_watch_urgency
    return ZERO


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamMemoryFeedbackResolutionSlaInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("input rows must be an iterable")
    rows = tuple(value)
    seen_feedback_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamMemoryFeedbackResolutionSlaInput:
            raise ValueError(
                "input rows must contain ResearchTeamMemoryFeedbackResolutionSlaInput",
            )
        require_paper_only_flags("input row", row)
        if row.feedback_created_at > generated_at:
            raise ValueError("feedback_created_at must not be in the future")
        for field_name in (
            "resolved_at",
            "writeback_completed_at",
            "calibration_completed_at",
        ):
            value_at = getattr(row, field_name)
            if value_at is not None and value_at > generated_at:
                raise ValueError(f"{field_name} must not be in the future")
        if row.feedback_key in seen_feedback_keys:
            raise ValueError("feedback_key values must be unique")
        seen_feedback_keys.add(row.feedback_key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.category_id,
                row.team_id,
                row.feedback_created_at,
                row.feedback_key,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    previous_key: tuple[int, str, str] | None = None
    for row in rows:
        if type(row) is not ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow:
            raise ValueError(
                "rows must contain ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow",
            )
        require_paper_only_flags("team category row", row)
        _validate_row(row)
        key = (row.category_id, row.team_id)
        if key in seen:
            raise ValueError("rows must contain unique team and category pairs")
        seen.add(key)
        sort_key = (STATUS_RANK[row.row_status], row.category_id, row.team_id)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _normalize_domain_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("impacted_domain_ids must be an iterable")
    items = tuple(_require_canonical_string("impacted_domain_id", item) for item in value)
    if not items:
        raise ValueError("impacted_domain_ids must not be empty")
    if len(set(items)) != len(items):
        raise ValueError("impacted_domain_ids must be unique")
    return tuple(sorted(items))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        index = REASON_CODE_SEQUENCE.index(reason_code)
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        seen.add(reason_code)
        previous_index = index
    return reason_codes


def _validate_row_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(value)
    if EMPTY_REASON in reason_codes:
        raise ValueError("empty reason is not valid for a team category row")
    if CLEAR_REASON in reason_codes and reason_codes != (CLEAR_REASON,):
        raise ValueError("clear reason must be the only team category row reason")
    for block_reason, watch_reason in (
        (UNRESOLVED_AGE_BLOCK_REASON, UNRESOLVED_AGE_WATCH_REASON),
        (
            WRITEBACK_COMPLETENESS_BLOCK_REASON,
            WRITEBACK_COMPLETENESS_WATCH_REASON,
        ),
        (CALIBRATION_BACKLOG_BLOCK_REASON, CALIBRATION_BACKLOG_WATCH_REASON),
        (IMPACTED_DOMAIN_BLOCK_REASON, IMPACTED_DOMAIN_WATCH_REASON),
        (
            REVIEWER_AVAILABILITY_BLOCK_REASON,
            REVIEWER_AVAILABILITY_WATCH_REASON,
        ),
        (MANUAL_ESCALATION_BLOCK_REASON, MANUAL_ESCALATION_WATCH_REASON),
    ):
        if block_reason in reason_codes and watch_reason in reason_codes:
            raise ValueError("row reason codes must not mix block and watch variants")
    return reason_codes


def _validate_config(config: ResearchTeamMemoryFeedbackResolutionSlaConfig) -> None:
    if config.unresolved_watch_age_seconds > config.unresolved_block_age_seconds:
        raise ValueError("unresolved_watch_age_seconds must not exceed block threshold")
    if config.writeback_block_ratio_floor > config.writeback_watch_ratio_floor:
        raise ValueError("writeback_block_ratio_floor must not exceed watch floor")
    if config.calibration_backlog_watch_count > config.calibration_backlog_block_count:
        raise ValueError("calibration_backlog_watch_count must not exceed block count")
    if config.impacted_domain_watch_count > config.impacted_domain_block_count:
        raise ValueError("impacted_domain_watch_count must not exceed block count")
    if (
        config.reviewer_availability_block_ratio_floor
        > config.reviewer_availability_watch_ratio_floor
    ):
        raise ValueError("reviewer_availability_block_ratio_floor must not exceed watch floor")
    if config.manual_escalation_watch_urgency > config.manual_escalation_block_urgency:
        raise ValueError("manual_escalation_watch_urgency must not exceed block urgency")


def _validate_input_time_sequence(
    row: ResearchTeamMemoryFeedbackResolutionSlaInput,
) -> None:
    if row.resolved_at is not None and row.resolved_at < row.feedback_created_at:
        raise ValueError("resolved_at must not precede feedback_created_at")
    if (
        row.writeback_completed_at is not None
        and row.writeback_completed_at < row.feedback_created_at
    ):
        raise ValueError("writeback_completed_at must not precede feedback_created_at")
    if (
        row.calibration_completed_at is not None
        and row.calibration_completed_at < row.feedback_created_at
    ):
        raise ValueError("calibration_completed_at must not precede feedback_created_at")


def _validate_row(row: ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow) -> None:
    if type(row) is not ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow:
        raise ValueError(
            "row must be exactly ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow",
        )
    require_team_category_pair(
        "team_id",
        row.team_id,
        "category_id",
        row.category_id,
    )
    _require_status("row_status", row.row_status)
    for field_name in (
        "feedback_count",
        "unresolved_feedback_count",
        "writeback_completed_count",
        "calibration_backlog_count",
        "impacted_domain_count",
    ):
        _require_nonnegative_integral_decimal(field_name, getattr(row, field_name))
    _require_nonnegative_seconds_decimal(
        "max_unresolved_feedback_age_seconds",
        row.max_unresolved_feedback_age_seconds,
    )
    for field_name in (
        "writeback_completeness_ratio",
        "min_reviewer_availability_ratio",
        "manual_escalation_urgency_score",
    ):
        _require_ratio(field_name, getattr(row, field_name))
    if type(row.reason_codes) is not tuple:
        raise ValueError("reason_codes must remain a tuple")
    _validate_row_reason_codes(row.reason_codes)
    require_paper_only_flags("team category row", row)
    if row.unresolved_feedback_count > row.feedback_count:
        raise ValueError("unresolved_feedback_count must not exceed feedback_count")
    if row.writeback_completed_count > row.feedback_count:
        raise ValueError("writeback_completed_count must not exceed feedback_count")
    if row.calibration_backlog_count > row.feedback_count:
        raise ValueError("calibration_backlog_count must not exceed feedback_count")
    if row.writeback_completeness_ratio != _ratio(
        row.writeback_completed_count,
        row.feedback_count,
    ):
        raise ValueError("writeback_completeness_ratio must match counts")
    if (
        row.unresolved_feedback_count == ZERO
        and row.max_unresolved_feedback_age_seconds != ZERO
    ):
        raise ValueError("max_unresolved_feedback_age_seconds must match unresolved count")
    if row.row_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row_status must match reason_codes")


def _validate_report(report: ResearchTeamMemoryFeedbackResolutionSlaReport) -> None:
    if type(report) is not ResearchTeamMemoryFeedbackResolutionSlaReport:
        raise ValueError(
            "report must be exactly ResearchTeamMemoryFeedbackResolutionSlaReport",
        )
    normalized_generated_at = _as_utc("generated_at", report.generated_at)
    if report.generated_at.isoformat() != normalized_generated_at.isoformat():
        raise ValueError("generated_at must remain normalized to UTC")
    _require_canonical_string("config_version", report.config_version)
    _require_status("report_status", report.report_status)
    for field_name in (
        "team_category_count",
        "feedback_count",
        "unresolved_feedback_count",
        "writeback_completed_count",
        "calibration_backlog_count",
        "impacted_domain_count",
    ):
        _require_nonnegative_integral_decimal(field_name, getattr(report, field_name))
    _require_nonnegative_seconds_decimal(
        "max_unresolved_feedback_age_seconds",
        report.max_unresolved_feedback_age_seconds,
    )
    for field_name in (
        "writeback_completeness_ratio",
        "min_reviewer_availability_ratio",
        "manual_escalation_urgency_score",
    ):
        _require_ratio(field_name, getattr(report, field_name))
    if type(report.rows) is not tuple:
        raise ValueError("rows must remain a tuple")
    rows = _normalize_rows(report.rows)
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must remain a tuple")
    _normalize_reason_codes(report.reason_codes)
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    require_paper_only_flags("report", report)
    if report.team_category_count != _decimal_count(len(rows)):
        raise ValueError("team_category_count must match rows")
    if report.feedback_count != _sum_decimal(rows, "feedback_count"):
        raise ValueError("feedback_count must match rows")
    if report.unresolved_feedback_count != _sum_decimal(rows, "unresolved_feedback_count"):
        raise ValueError("unresolved_feedback_count must match rows")
    if report.max_unresolved_feedback_age_seconds != _max_decimal(
        rows,
        "max_unresolved_feedback_age_seconds",
    ):
        raise ValueError("max_unresolved_feedback_age_seconds must match rows")
    if report.writeback_completed_count != _sum_decimal(rows, "writeback_completed_count"):
        raise ValueError("writeback_completed_count must match rows")
    if report.writeback_completeness_ratio != _ratio(
        report.writeback_completed_count,
        report.feedback_count,
    ):
        raise ValueError("writeback_completeness_ratio must match counts")
    if report.calibration_backlog_count != _sum_decimal(rows, "calibration_backlog_count"):
        raise ValueError("calibration_backlog_count must match rows")
    if not rows:
        if report.impacted_domain_count != ZERO:
            raise ValueError("impacted_domain_count must be zero without rows")
    else:
        minimum_impacted_domain_count = max(row.impacted_domain_count for row in rows)
        maximum_impacted_domain_count = _sum_decimal(rows, "impacted_domain_count")
        if not (
            minimum_impacted_domain_count
            <= report.impacted_domain_count
            <= maximum_impacted_domain_count
        ):
            raise ValueError("impacted_domain_count must be consistent with rows")
    if report.min_reviewer_availability_ratio != _min_ratio(
        rows,
        "min_reviewer_availability_ratio",
    ):
        raise ValueError("min_reviewer_availability_ratio must match rows")
    if report.manual_escalation_urgency_score != _max_decimal(
        rows,
        "manual_escalation_urgency_score",
    ):
        raise ValueError("manual_escalation_urgency_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    _reject_unsafe_public_payload(
        "ResearchTeamMemoryFeedbackResolutionSlaReport",
        _payload_value(asdict(report)),
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _max_unresolved_age_seconds(
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaInput, ...],
    generated_at: datetime,
) -> Decimal:
    if not rows:
        return ZERO
    return max(_age_seconds(generated_at, row.feedback_created_at) for row in rows).quantize(
        SECONDS_QUANT,
    )


def _min_feedback_reviewer_availability_ratio(
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaInput, ...],
) -> Decimal:
    if not rows:
        return ONE
    return min(_reviewer_availability_ratio(row) for row in rows).quantize(RATIO_QUANT)


def _reviewer_availability_ratio(
    row: ResearchTeamMemoryFeedbackResolutionSlaInput,
) -> Decimal:
    if row.required_reviewer_count == ZERO:
        return ONE
    return _ratio(row.available_reviewer_count, row.required_reviewer_count)


def _total_impacted_domain_count(
    rows: tuple[ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow, ...],
    inputs: tuple[ResearchTeamMemoryFeedbackResolutionSlaInput, ...],
) -> int:
    if not rows:
        return 0
    return len({domain_id for row in inputs for domain_id in row.impacted_domain_ids})


def _age_seconds(generated_at: datetime, value: datetime) -> Decimal:
    delta = generated_at - value
    if delta.days < 0:
        raise ValueError("age seconds must be nonnegative")
    total_microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(SECONDS_QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(RATIO_QUANT)


def _sum_decimal(values: tuple[object, ...], field_name: str) -> Decimal:
    total = sum((getattr(value, field_name) for value in values), ZERO)
    return _require_nonnegative_decimal(field_name, total).quantize(COUNT_QUANT)


def _max_decimal(values: tuple[object, ...], field_name: str) -> Decimal:
    if not values:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(value, field_name))
        for value in values
    )


def _min_ratio(values: tuple[object, ...], field_name: str) -> Decimal:
    if not values:
        return ZERO
    return min(_require_ratio(field_name, getattr(value, field_name)) for value in values)


def _require_status(field_name: str, value: object) -> str:
    normalized = _require_canonical_string(field_name, value)
    if normalized not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = value.quantize(RATIO_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if normalized == ZERO:
        return ZERO
    return normalized


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value).quantize(SECONDS_QUANT)


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    decimal_value = _require_nonnegative_decimal(field_name, value)
    return decimal_value.quantize(COUNT_QUANT)


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio.quantize(RATIO_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _validate_public_payload(payload: dict[str, object]) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload(
        "research_team_memory_feedback_resolution_sla_report_payload",
        payload,
    )
    _require_exact_public_fields("public payload", payload, _PUBLIC_REPORT_FIELDS)
    _require_payload_hard_flags(payload)
    digest = _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list in the public payload")
    report = ResearchTeamMemoryFeedbackResolutionSlaReport(
        generated_at=_require_public_datetime("generated_at", payload["generated_at"]),
        config_version=_require_canonical_string(
            "config_version",
            payload["config_version"],
        ),
        report_status=_require_status("report_status", payload["report_status"]),
        team_category_count=_require_public_count(
            "team_category_count",
            payload["team_category_count"],
        ),
        feedback_count=_require_public_count(
            "feedback_count",
            payload["feedback_count"],
        ),
        unresolved_feedback_count=_require_public_count(
            "unresolved_feedback_count",
            payload["unresolved_feedback_count"],
        ),
        max_unresolved_feedback_age_seconds=_require_public_seconds(
            "max_unresolved_feedback_age_seconds",
            payload["max_unresolved_feedback_age_seconds"],
        ),
        writeback_completed_count=_require_public_count(
            "writeback_completed_count",
            payload["writeback_completed_count"],
        ),
        writeback_completeness_ratio=_require_public_ratio(
            "writeback_completeness_ratio",
            payload["writeback_completeness_ratio"],
        ),
        calibration_backlog_count=_require_public_count(
            "calibration_backlog_count",
            payload["calibration_backlog_count"],
        ),
        impacted_domain_count=_require_public_count(
            "impacted_domain_count",
            payload["impacted_domain_count"],
        ),
        min_reviewer_availability_ratio=_require_public_ratio(
            "min_reviewer_availability_ratio",
            payload["min_reviewer_availability_ratio"],
        ),
        manual_escalation_urgency_score=_require_public_ratio(
            "manual_escalation_urgency_score",
            payload["manual_escalation_urgency_score"],
        ),
        rows=tuple(
            _public_row(row_value, index=index)
            for index, row_value in enumerate(rows_value)
        ),
        reason_codes=_require_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        derived_validation_digest=digest,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    canonical_payload = _payload_value(asdict(report))
    if canonical_payload != payload:
        raise ValueError("public payload must use canonical fields and values")


def _public_row(
    value: object,
    *,
    index: int,
) -> ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow:
    label = f"rows[{index}]"
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    _require_exact_public_fields(label, value, _PUBLIC_ROW_FIELDS)
    _require_payload_hard_flags(value)
    return ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow(
        category_id=_require_canonical_string(
            f"{label}.category_id",
            value["category_id"],
        ),
        team_id=_require_canonical_string(f"{label}.team_id", value["team_id"]),
        row_status=_require_status(f"{label}.row_status", value["row_status"]),
        feedback_count=_require_public_count(
            f"{label}.feedback_count",
            value["feedback_count"],
        ),
        unresolved_feedback_count=_require_public_count(
            f"{label}.unresolved_feedback_count",
            value["unresolved_feedback_count"],
        ),
        max_unresolved_feedback_age_seconds=_require_public_seconds(
            f"{label}.max_unresolved_feedback_age_seconds",
            value["max_unresolved_feedback_age_seconds"],
        ),
        writeback_completed_count=_require_public_count(
            f"{label}.writeback_completed_count",
            value["writeback_completed_count"],
        ),
        writeback_completeness_ratio=_require_public_ratio(
            f"{label}.writeback_completeness_ratio",
            value["writeback_completeness_ratio"],
        ),
        calibration_backlog_count=_require_public_count(
            f"{label}.calibration_backlog_count",
            value["calibration_backlog_count"],
        ),
        impacted_domain_count=_require_public_count(
            f"{label}.impacted_domain_count",
            value["impacted_domain_count"],
        ),
        min_reviewer_availability_ratio=_require_public_ratio(
            f"{label}.min_reviewer_availability_ratio",
            value["min_reviewer_availability_ratio"],
        ),
        manual_escalation_urgency_score=_require_public_ratio(
            f"{label}.manual_escalation_urgency_score",
            value["manual_escalation_urgency_score"],
        ),
        reason_codes=_require_public_reason_codes(
            f"{label}.reason_codes",
            value["reason_codes"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_exact_public_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    if frozenset(payload) != expected_fields:
        raise ValueError(f"{label} must contain exactly the supported fields")


def _require_public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    return normalized


def _require_public_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_public_decimal(field_name, value)
    normalized = _require_nonnegative_integral_decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_public_decimal(field_name, value)
    normalized = _require_nonnegative_seconds_decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_public_decimal(field_name, value)
    normalized = _require_ratio(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc


def _require_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(value)


def _payload_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal payload values must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime payload values must be exactly datetime")
        if value.tzinfo is None:
            raise ValueError("datetime payload values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, int):
        raise ValueError("payload numerics must be Decimal")
    if isinstance(value, float):
        raise ValueError("payload numerics must not be float")
    raise ValueError("payload value is not JSON ready")


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload = dict(payload)
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    reject_unsafe_surface_fields(label, payload)
    for key, item in _iter_public_items(payload):
        lowered_key = key.lower()
        if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"unsafe public payload field in {label}: {key}")
        if type(item) is str:
            lowered_value = item.lower()
            if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
                raise ValueError(f"unsafe public payload value in {label}: {key}")


def _iter_public_items(value: object) -> tuple[tuple[str, object], ...]:
    if isinstance(value, dict):
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            items.append((key, item))
            items.extend(_iter_public_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_items(item))
        return tuple(items)
    return ()


__all__ = (
    "CALIBRATION_BACKLOG_BLOCK_REASON",
    "CALIBRATION_BACKLOG_WATCH_REASON",
    "CLEAR_REASON",
    "DEFAULT_RESEARCH_TEAM_MEMORY_FEEDBACK_RESOLUTION_SLA_CONFIG_VERSION",
    "EMPTY_REASON",
    "IMPACTED_DOMAIN_BLOCK_REASON",
    "IMPACTED_DOMAIN_WATCH_REASON",
    "MANUAL_ESCALATION_BLOCK_REASON",
    "MANUAL_ESCALATION_WATCH_REASON",
    "REASON_CODE_SEQUENCE",
    "REVIEWER_AVAILABILITY_BLOCK_REASON",
    "REVIEWER_AVAILABILITY_WATCH_REASON",
    "ResearchTeamMemoryFeedbackResolutionSlaConfig",
    "ResearchTeamMemoryFeedbackResolutionSlaInput",
    "ResearchTeamMemoryFeedbackResolutionSlaReport",
    "ResearchTeamMemoryFeedbackResolutionSlaTeamCategoryRow",
    "UNRESOLVED_AGE_BLOCK_REASON",
    "UNRESOLVED_AGE_WATCH_REASON",
    "WRITEBACK_COMPLETENESS_BLOCK_REASON",
    "WRITEBACK_COMPLETENESS_WATCH_REASON",
    "build_research_team_memory_feedback_resolution_sla_report",
    "research_team_memory_feedback_resolution_sla_report_payload",
)
