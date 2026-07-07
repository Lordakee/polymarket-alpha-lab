"""Pure Phase 1 team specialist learning feedback router."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_SPECIALIST_LEARNING_FEEDBACK_ROUTER_V2_CONFIG_VERSION = (
    "team-specialist-learning-feedback-router-v2"
)
TEAM_SPECIALIST_LEARNING_FEEDBACK_ROUTER_V2_STATUSES = ("pass", "watch", "blocked")

DOMAIN_ROUTE_MATCH_REASON = "domain_route_match"
DOMAIN_ROUTE_MISS_REASON = "domain_route_miss"
CALIBRATION_GAP_REASON = "calibration_gap"
SOURCE_QUALITY_FAILURE_REASON = "source_quality_failure"
RESOLUTION_RULE_MISS_REASON = "resolution_rule_miss"
FORECAST_ERROR_SEVERE_REASON = "forecast_error_severe"
FORECAST_ERROR_WATCH_REASON = "forecast_error_watch"
STALE_PLAYBOOK_RISK_REASON = "stale_playbook_risk"
UNRESOLVED_POSTMORTEM_PRESSURE_REASON = "unresolved_postmortem_pressure"
LEARNING_FEEDBACK_PASS_REASON = "learning_feedback_pass"
REPORT_BLOCKED_REASON = "specialist_feedback_router_blocked"
REPORT_WATCH_REASON = "specialist_feedback_router_watch"
EMPTY_FEEDBACK_REASON = "specialist_feedback_router_empty"

ROW_REASON_CODES = (
    DOMAIN_ROUTE_MATCH_REASON,
    DOMAIN_ROUTE_MISS_REASON,
    CALIBRATION_GAP_REASON,
    SOURCE_QUALITY_FAILURE_REASON,
    RESOLUTION_RULE_MISS_REASON,
    FORECAST_ERROR_SEVERE_REASON,
    FORECAST_ERROR_WATCH_REASON,
    STALE_PLAYBOOK_RISK_REASON,
    UNRESOLVED_POSTMORTEM_PRESSURE_REASON,
    LEARNING_FEEDBACK_PASS_REASON,
)
REPORT_REASON_CODES = (
    REPORT_BLOCKED_REASON,
    REPORT_WATCH_REASON,
    CALIBRATION_GAP_REASON,
    SOURCE_QUALITY_FAILURE_REASON,
    RESOLUTION_RULE_MISS_REASON,
    FORECAST_ERROR_SEVERE_REASON,
    FORECAST_ERROR_WATCH_REASON,
    STALE_PLAYBOOK_RISK_REASON,
    UNRESOLVED_POSTMORTEM_PRESSURE_REASON,
    DOMAIN_ROUTE_MISS_REASON,
    LEARNING_FEEDBACK_PASS_REASON,
    EMPTY_FEEDBACK_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

CALIBRATION_GAP_WEIGHT = Decimal("0.25")
SOURCE_QUALITY_FAILURE_WEIGHT = Decimal("0.15")
RESOLUTION_RULE_MISS_WEIGHT = Decimal("0.15")
FORECAST_ERROR_SEVERITY_WEIGHT = Decimal("0.25")
STALE_PLAYBOOK_RISK_WEIGHT = Decimal("0.10")
UNRESOLVED_POSTMORTEM_PRESSURE_WEIGHT = Decimal("0.15")

UNASSIGNED_SPECIALIST_TEAM_ID = "unassigned-specialist-feedback"
PRIVATE_REFERENCE_MARKER = "[redacted]"
SAFE_REFERENCE_PREFIXES = ("public:", "memory:", "source:", "lesson:")
PRIVATE_REFERENCE_FRAGMENTS = (
    "://",
    "@",
    "api_key",
    "bearer ",
    "credential",
    "private_key",
    "secret",
    "token",
    "key:",
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
SHA256_HEX_LENGTH = 64


@dataclass(frozen=True)
class TeamSpecialistLearningFeedbackRouterV2DomainRoute:
    domain: str
    specialist_team_id: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("domain", self.domain)
        _require_public_string("specialist_team_id", self.specialist_team_id)
        require_paper_only_flags("domain route", self)


@dataclass(frozen=True)
class TeamSpecialistLearningFeedbackRouterV2Config:
    domain_routes: tuple[TeamSpecialistLearningFeedbackRouterV2DomainRoute, ...]
    config_version: str = DEFAULT_TEAM_SPECIALIST_LEARNING_FEEDBACK_ROUTER_V2_CONFIG_VERSION
    calibration_gap_threshold: Decimal = Decimal("0.150000")
    source_quality_failure_threshold: Decimal = Decimal("0.300000")
    resolution_rule_miss_threshold: Decimal = Decimal("0.200000")
    forecast_error_watch_threshold: Decimal = Decimal("0.250000")
    forecast_error_block_threshold: Decimal = Decimal("0.800000")
    stale_playbook_risk_threshold: Decimal = Decimal("0.400000")
    unresolved_postmortem_pressure_threshold: Decimal = Decimal("0.500000")
    min_watch_priority_score: Decimal = Decimal("0.250000")
    min_block_priority_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "domain_routes",
            _normalize_domain_routes(self.domain_routes),
        )
        for field_name in (
            "calibration_gap_threshold",
            "source_quality_failure_threshold",
            "resolution_rule_miss_threshold",
            "forecast_error_watch_threshold",
            "forecast_error_block_threshold",
            "stale_playbook_risk_threshold",
            "unresolved_postmortem_pressure_threshold",
            "min_watch_priority_score",
            "min_block_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.forecast_error_watch_threshold > self.forecast_error_block_threshold:
            raise ValueError(
                "forecast_error_watch_threshold must be less than or equal to "
                "forecast_error_block_threshold",
            )
        if self.min_watch_priority_score > self.min_block_priority_score:
            raise ValueError(
                "min_watch_priority_score must be less than or equal to "
                "min_block_priority_score",
            )
        require_paper_only_flags("feedback router config", self)


@dataclass(frozen=True)
class TeamSpecialistLearningFeedbackRouterV2Feedback:
    feedback_id: str
    domain: str
    observed_at: datetime
    calibration_gap: Decimal
    source_quality_failure_score: Decimal
    resolution_rule_miss_score: Decimal
    forecast_error_severity: Decimal
    stale_playbook_risk: Decimal
    unresolved_postmortem_pressure: Decimal
    source_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("feedback_id", self.feedback_id)
        _require_public_string("domain", self.domain)
        _require_public_string("source_reference", self.source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibration_gap",
            "source_quality_failure_score",
            "resolution_rule_miss_score",
            "forecast_error_severity",
            "stale_playbook_risk",
            "unresolved_postmortem_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("feedback item", self)


@dataclass(frozen=True)
class TeamSpecialistLearningFeedbackRouterV2Assignment:
    feedback_id: str
    domain: str
    specialist_team_id: str
    observed_at: datetime
    calibration_gap: Decimal
    source_quality_failure_score: Decimal
    resolution_rule_miss_score: Decimal
    forecast_error_severity: Decimal
    stale_playbook_risk: Decimal
    unresolved_postmortem_pressure: Decimal
    priority_score: Decimal
    route_status: str
    redacted_source_reference: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("feedback_id", self.feedback_id)
        _require_public_string("domain", self.domain)
        _require_public_string("specialist_team_id", self.specialist_team_id)
        _require_public_string("redacted_source_reference", self.redacted_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibration_gap",
            "source_quality_failure_score",
            "resolution_rule_miss_score",
            "forecast_error_severity",
            "stale_playbook_risk",
            "unresolved_postmortem_pressure",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("route_status", self.route_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_assignment(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _assignment_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _assignment_derived_validation_digest(
                self,
            ):
                raise ValueError("derived_validation_digest must match assignment fields")
        _reject_unsafe_public_payload("feedback router assignment", json_ready_no_floats(self))
        require_paper_only_flags("feedback router assignment", self)


@dataclass(frozen=True)
class TeamSpecialistLearningFeedbackRouterV2Report:
    generated_at: datetime
    config_version: str
    feedback_count: Decimal
    specialist_team_count: Decimal
    assignment_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    average_priority_score: Decimal
    route_status: str
    reason_codes: tuple[str, ...]
    assignments: tuple[TeamSpecialistLearningFeedbackRouterV2Assignment, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "feedback_count",
            "specialist_team_count",
            "assignment_count",
            "blocked_count",
            "watch_count",
            "pass_count",
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
        _require_status("route_status", self.route_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "assignments",
            _normalize_assignments(self.assignments),
        )
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report fields")
        _reject_unsafe_public_payload("feedback router report", json_ready_no_floats(self))
        require_paper_only_flags("feedback router report", self)


def build_team_specialist_learning_feedback_router_v2_report(
    feedback_items: list[TeamSpecialistLearningFeedbackRouterV2Feedback]
    | tuple[TeamSpecialistLearningFeedbackRouterV2Feedback, ...],
    *,
    config: TeamSpecialistLearningFeedbackRouterV2Config,
    generated_at: datetime,
) -> TeamSpecialistLearningFeedbackRouterV2Report:
    if type(config) is not TeamSpecialistLearningFeedbackRouterV2Config:
        raise ValueError("config must be a TeamSpecialistLearningFeedbackRouterV2Config")
    require_paper_only_flags("feedback router config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_feedback_items(feedback_items)
    assignments = tuple(
        sorted(
            (_assignment_for_feedback(row, config) for row in rows),
            key=_assignment_sort_key,
        ),
    )
    return TeamSpecialistLearningFeedbackRouterV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        feedback_count=_count(len(rows)),
        specialist_team_count=_count(
            len({row.specialist_team_id for row in assignments}),
        ),
        assignment_count=_count(len(assignments)),
        blocked_count=_status_count(assignments, "blocked"),
        watch_count=_status_count(assignments, "watch"),
        pass_count=_status_count(assignments, "pass"),
        average_priority_score=_average_priority_score(assignments),
        route_status=_report_status(assignments),
        reason_codes=_report_reason_codes(assignments),
        assignments=assignments,
    )


def team_specialist_learning_feedback_router_v2_payload(
    value: TeamSpecialistLearningFeedbackRouterV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is TeamSpecialistLearningFeedbackRouterV2Report:
        require_paper_only_flags("feedback router report", value)
        _validate_report(value)
        payload = json_ready_no_floats(value)
    elif type(value) is dict:
        payload = json_ready_no_floats(value)
    else:
        raise ValueError(
            "value must be a TeamSpecialistLearningFeedbackRouterV2Report or JSON object",
        )
    if not isinstance(payload, dict):
        raise ValueError("feedback router payload must be a JSON object")
    validate_team_specialist_learning_feedback_router_v2_public_payload(payload)
    return payload


def validate_team_specialist_learning_feedback_router_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_values("public payload", payload)
    _require_public_payload_flags(payload, "public payload")
    assignments = payload.get("assignments")
    if type(assignments) is not list:
        raise ValueError("assignments must be a list in public payload")
    for index, row in enumerate(assignments):
        if type(row) is not dict:
            raise ValueError("assignments must contain JSON objects")
        _require_public_payload_flags(row, f"public payload assignment {index}")
        _validate_assignment_public_payload_digest(row)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_report_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _assignment_for_feedback(
    row: TeamSpecialistLearningFeedbackRouterV2Feedback,
    config: TeamSpecialistLearningFeedbackRouterV2Config,
) -> TeamSpecialistLearningFeedbackRouterV2Assignment:
    specialist_team_id = _specialist_team_for_domain(row.domain, config)
    reason_codes = _assignment_reason_codes(row, specialist_team_id, config)
    priority_score = _priority_score(row, reason_codes)
    return TeamSpecialistLearningFeedbackRouterV2Assignment(
        feedback_id=row.feedback_id,
        domain=row.domain,
        specialist_team_id=specialist_team_id,
        observed_at=row.observed_at,
        calibration_gap=row.calibration_gap,
        source_quality_failure_score=row.source_quality_failure_score,
        resolution_rule_miss_score=row.resolution_rule_miss_score,
        forecast_error_severity=row.forecast_error_severity,
        stale_playbook_risk=row.stale_playbook_risk,
        unresolved_postmortem_pressure=row.unresolved_postmortem_pressure,
        priority_score=priority_score,
        route_status=_assignment_status(
            priority_score,
            row.forecast_error_severity,
            reason_codes,
            config,
        ),
        redacted_source_reference=_redact_source_reference(row.source_reference),
        reason_codes=reason_codes,
    )


def _specialist_team_for_domain(
    domain: str,
    config: TeamSpecialistLearningFeedbackRouterV2Config,
) -> str:
    for route in config.domain_routes:
        if route.domain == domain:
            return route.specialist_team_id
    return UNASSIGNED_SPECIALIST_TEAM_ID


def _assignment_reason_codes(
    row: TeamSpecialistLearningFeedbackRouterV2Feedback,
    specialist_team_id: str,
    config: TeamSpecialistLearningFeedbackRouterV2Config,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if specialist_team_id == UNASSIGNED_SPECIALIST_TEAM_ID:
        codes.add(DOMAIN_ROUTE_MISS_REASON)
    else:
        codes.add(DOMAIN_ROUTE_MATCH_REASON)
    if row.calibration_gap >= config.calibration_gap_threshold:
        codes.add(CALIBRATION_GAP_REASON)
    if row.source_quality_failure_score >= config.source_quality_failure_threshold:
        codes.add(SOURCE_QUALITY_FAILURE_REASON)
    if row.resolution_rule_miss_score >= config.resolution_rule_miss_threshold:
        codes.add(RESOLUTION_RULE_MISS_REASON)
    if row.forecast_error_severity >= config.forecast_error_block_threshold:
        codes.add(FORECAST_ERROR_SEVERE_REASON)
    elif row.forecast_error_severity >= config.forecast_error_watch_threshold:
        codes.add(FORECAST_ERROR_WATCH_REASON)
    if row.stale_playbook_risk >= config.stale_playbook_risk_threshold:
        codes.add(STALE_PLAYBOOK_RISK_REASON)
    if (
        row.unresolved_postmortem_pressure
        >= config.unresolved_postmortem_pressure_threshold
    ):
        codes.add(UNRESOLVED_POSTMORTEM_PRESSURE_REASON)
    if codes == {DOMAIN_ROUTE_MATCH_REASON}:
        codes.add(LEARNING_FEEDBACK_PASS_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _assignment_status(
    priority_score: Decimal,
    forecast_error_severity: Decimal,
    reason_codes: tuple[str, ...],
    config: TeamSpecialistLearningFeedbackRouterV2Config,
) -> str:
    if DOMAIN_ROUTE_MISS_REASON in reason_codes:
        return "blocked"
    if forecast_error_severity >= config.forecast_error_block_threshold:
        return "blocked"
    if priority_score >= config.min_block_priority_score:
        return "blocked"
    if priority_score >= config.min_watch_priority_score:
        return "watch"
    if reason_codes != (DOMAIN_ROUTE_MATCH_REASON, LEARNING_FEEDBACK_PASS_REASON):
        return "watch"
    return "pass"


def _priority_score(
    row: TeamSpecialistLearningFeedbackRouterV2Feedback,
    reason_codes: tuple[str, ...],
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _scored_dimension(
                row.calibration_gap,
                CALIBRATION_GAP_WEIGHT,
                CALIBRATION_GAP_REASON,
                reason_codes,
            )
            + _scored_dimension(
                row.source_quality_failure_score,
                SOURCE_QUALITY_FAILURE_WEIGHT,
                SOURCE_QUALITY_FAILURE_REASON,
                reason_codes,
            )
            + _scored_dimension(
                row.resolution_rule_miss_score,
                RESOLUTION_RULE_MISS_WEIGHT,
                RESOLUTION_RULE_MISS_REASON,
                reason_codes,
            )
            + _scored_dimension(
                row.forecast_error_severity,
                FORECAST_ERROR_SEVERITY_WEIGHT,
                FORECAST_ERROR_WATCH_REASON,
                reason_codes,
            )
            + _scored_dimension(
                row.forecast_error_severity,
                FORECAST_ERROR_SEVERITY_WEIGHT,
                FORECAST_ERROR_SEVERE_REASON,
                reason_codes,
            )
            + _scored_dimension(
                row.stale_playbook_risk,
                STALE_PLAYBOOK_RISK_WEIGHT,
                STALE_PLAYBOOK_RISK_REASON,
                reason_codes,
            )
            + _scored_dimension(
                row.unresolved_postmortem_pressure,
                UNRESOLVED_POSTMORTEM_PRESSURE_WEIGHT,
                UNRESOLVED_POSTMORTEM_PRESSURE_REASON,
                reason_codes,
            )
        )
        if score > ONE_RATIO:
            score = ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _scored_dimension(
    value: Decimal,
    weight: Decimal,
    reason_code: str,
    reason_codes: tuple[str, ...],
) -> Decimal:
    if reason_code not in reason_codes:
        return ZERO_RATIO
    return value * weight


def _report_status(
    assignments: tuple[TeamSpecialistLearningFeedbackRouterV2Assignment, ...],
) -> str:
    if not assignments:
        return "blocked"
    if any(row.route_status == "blocked" for row in assignments):
        return "blocked"
    if any(row.route_status == "watch" for row in assignments):
        return "watch"
    return "pass"


def _report_reason_codes(
    assignments: tuple[TeamSpecialistLearningFeedbackRouterV2Assignment, ...],
) -> tuple[str, ...]:
    if not assignments:
        return (EMPTY_FEEDBACK_REASON,)
    codes = {
        code
        for row in assignments
        for code in row.reason_codes
        if code not in (DOMAIN_ROUTE_MATCH_REASON, LEARNING_FEEDBACK_PASS_REASON)
    }
    status = _report_status(assignments)
    if status == "blocked":
        codes.add(REPORT_BLOCKED_REASON)
    elif status == "watch":
        codes.add(REPORT_WATCH_REASON)
    if not codes:
        codes.add(LEARNING_FEEDBACK_PASS_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _validate_assignment(row: TeamSpecialistLearningFeedbackRouterV2Assignment) -> None:
    expected_priority_score = _priority_score_from_values(
        row.calibration_gap,
        row.source_quality_failure_score,
        row.resolution_rule_miss_score,
        row.forecast_error_severity,
        row.stale_playbook_risk,
        row.unresolved_postmortem_pressure,
        row.reason_codes,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match feedback pressure dimensions")
    if row.redacted_source_reference != PRIVATE_REFERENCE_MARKER and _is_private_reference(
        row.redacted_source_reference,
    ):
        raise ValueError("redacted_source_reference must not expose private references")
    if DOMAIN_ROUTE_MATCH_REASON in row.reason_codes and DOMAIN_ROUTE_MISS_REASON in (
        row.reason_codes
    ):
        raise ValueError("reason_codes cannot include both domain match and miss")


def _validate_report(report: TeamSpecialistLearningFeedbackRouterV2Report) -> None:
    if report.feedback_count != _count(len(report.assignments)):
        raise ValueError("feedback_count must match assignments")
    if report.specialist_team_count != _count(
        len({row.specialist_team_id for row in report.assignments}),
    ):
        raise ValueError("specialist_team_count must match assignments")
    if report.assignment_count != _count(len(report.assignments)):
        raise ValueError("assignment_count must match assignments")
    if report.blocked_count != _status_count(report.assignments, "blocked"):
        raise ValueError("blocked_count must match assignments")
    if report.watch_count != _status_count(report.assignments, "watch"):
        raise ValueError("watch_count must match assignments")
    if report.pass_count != _status_count(report.assignments, "pass"):
        raise ValueError("pass_count must match assignments")
    if report.average_priority_score != _average_priority_score(report.assignments):
        raise ValueError("average_priority_score must match assignments")
    if report.route_status != _report_status(report.assignments):
        raise ValueError("route_status must match assignments")
    if report.reason_codes != _report_reason_codes(report.assignments):
        raise ValueError("reason_codes must match assignments")
    if report.assignments != tuple(sorted(report.assignments, key=_assignment_sort_key)):
        raise ValueError("assignments must use deterministic sequence")


def _priority_score_from_values(
    calibration_gap: Decimal,
    source_quality_failure_score: Decimal,
    resolution_rule_miss_score: Decimal,
    forecast_error_severity: Decimal,
    stale_playbook_risk: Decimal,
    unresolved_postmortem_pressure: Decimal,
    reason_codes: tuple[str, ...],
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _scored_dimension(
                calibration_gap,
                CALIBRATION_GAP_WEIGHT,
                CALIBRATION_GAP_REASON,
                reason_codes,
            )
            + _scored_dimension(
                source_quality_failure_score,
                SOURCE_QUALITY_FAILURE_WEIGHT,
                SOURCE_QUALITY_FAILURE_REASON,
                reason_codes,
            )
            + _scored_dimension(
                resolution_rule_miss_score,
                RESOLUTION_RULE_MISS_WEIGHT,
                RESOLUTION_RULE_MISS_REASON,
                reason_codes,
            )
            + _scored_dimension(
                forecast_error_severity,
                FORECAST_ERROR_SEVERITY_WEIGHT,
                FORECAST_ERROR_WATCH_REASON,
                reason_codes,
            )
            + _scored_dimension(
                forecast_error_severity,
                FORECAST_ERROR_SEVERITY_WEIGHT,
                FORECAST_ERROR_SEVERE_REASON,
                reason_codes,
            )
            + _scored_dimension(
                stale_playbook_risk,
                STALE_PLAYBOOK_RISK_WEIGHT,
                STALE_PLAYBOOK_RISK_REASON,
                reason_codes,
            )
            + _scored_dimension(
                unresolved_postmortem_pressure,
                UNRESOLVED_POSTMORTEM_PRESSURE_WEIGHT,
                UNRESOLVED_POSTMORTEM_PRESSURE_REASON,
                reason_codes,
            )
        )
        if score > ONE_RATIO:
            score = ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _assignment_sort_key(
    row: TeamSpecialistLearningFeedbackRouterV2Assignment,
) -> tuple[int, Decimal, datetime, str]:
    return (
        -_status_rank(row.route_status),
        -row.priority_score,
        row.observed_at,
        row.feedback_id,
    )


def _status_rank(status: str) -> int:
    if status == "blocked":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    assignments: tuple[TeamSpecialistLearningFeedbackRouterV2Assignment, ...],
    status: str,
) -> Decimal:
    return _count(len(tuple(row for row in assignments if row.route_status == status)))


def _average_priority_score(
    assignments: tuple[TeamSpecialistLearningFeedbackRouterV2Assignment, ...],
) -> Decimal:
    if not assignments:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (
            sum((row.priority_score for row in assignments), ZERO_RATIO)
            / Decimal(len(assignments))
        ).quantize(RATIO_QUANTUM)


def _normalize_domain_routes(
    value: object,
) -> tuple[TeamSpecialistLearningFeedbackRouterV2DomainRoute, ...]:
    if type(value) is not tuple:
        raise ValueError("domain_routes must be a tuple")
    if not value:
        raise ValueError("domain_routes must not be empty")
    seen_domains: set[str] = set()
    seen_teams: set[str] = set()
    routes: list[TeamSpecialistLearningFeedbackRouterV2DomainRoute] = []
    for row in value:
        if type(row) is not TeamSpecialistLearningFeedbackRouterV2DomainRoute:
            raise ValueError(
                "domain_routes must contain "
                "TeamSpecialistLearningFeedbackRouterV2DomainRoute values",
            )
        require_paper_only_flags("domain route", row)
        if row.domain in seen_domains:
            raise ValueError("domain_routes must not contain duplicate domains")
        routes.append(row)
        seen_domains.add(row.domain)
        seen_teams.add(row.specialist_team_id)
    if len(seen_teams) != len(value):
        raise ValueError("domain_routes must not reuse specialist teams")
    return tuple(sorted(routes, key=lambda row: (row.domain, row.specialist_team_id)))


def _normalize_feedback_items(
    value: object,
) -> tuple[TeamSpecialistLearningFeedbackRouterV2Feedback, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("feedback_items must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not TeamSpecialistLearningFeedbackRouterV2Feedback:
            raise ValueError(
                "feedback_items must contain "
                "TeamSpecialistLearningFeedbackRouterV2Feedback values",
            )
        require_paper_only_flags("feedback item", row)
    return rows


def _normalize_assignments(
    value: object,
) -> tuple[TeamSpecialistLearningFeedbackRouterV2Assignment, ...]:
    if type(value) is not tuple:
        raise ValueError("assignments must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistLearningFeedbackRouterV2Assignment:
            raise ValueError(
                "assignments must contain "
                "TeamSpecialistLearningFeedbackRouterV2Assignment values",
            )
        _validate_assignment(row)
        require_paper_only_flags("assignment", row)
    return value


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


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if value not in TEAM_SPECIALIST_LEARNING_FEEDBACK_ROUTER_V2_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _redact_source_reference(value: str) -> str:
    if _is_private_reference(value):
        return PRIVATE_REFERENCE_MARKER
    return value


def _is_private_reference(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(SAFE_REFERENCE_PREFIXES):
        return False
    return any(fragment in lowered for fragment in PRIVATE_REFERENCE_FRAGMENTS)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            if any(term in key.lower() for term in UNSAFE_PUBLIC_TERMS):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_public_numeric_values(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must serialize numeric values as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(label, item)


def _require_public_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in {label}")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _assignment_derived_validation_digest(
    row: TeamSpecialistLearningFeedbackRouterV2Assignment,
) -> str:
    return _public_digest(_assignment_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: TeamSpecialistLearningFeedbackRouterV2Report,
) -> str:
    return _public_digest(_report_public_payload_for_digest(report))


def _assignment_public_payload_for_digest(
    row: TeamSpecialistLearningFeedbackRouterV2Assignment,
) -> dict[str, Any]:
    payload = json_ready_no_floats(row)
    if not isinstance(payload, dict):
        raise ValueError("assignment digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: TeamSpecialistLearningFeedbackRouterV2Report,
) -> dict[str, Any]:
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _validate_assignment_public_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    if digest_value != _public_digest(digest_payload):
        raise ValueError("derived_validation_digest must match assignment public payload")


def _public_report_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _public_digest(digest_payload)


def _public_digest(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_public_numeric_values("digest payload", payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_LEARNING_FEEDBACK_ROUTER_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_LEARNING_FEEDBACK_ROUTER_V2_STATUSES",
    "DOMAIN_ROUTE_MATCH_REASON",
    "DOMAIN_ROUTE_MISS_REASON",
    "CALIBRATION_GAP_REASON",
    "SOURCE_QUALITY_FAILURE_REASON",
    "RESOLUTION_RULE_MISS_REASON",
    "FORECAST_ERROR_SEVERE_REASON",
    "FORECAST_ERROR_WATCH_REASON",
    "STALE_PLAYBOOK_RISK_REASON",
    "UNRESOLVED_POSTMORTEM_PRESSURE_REASON",
    "LEARNING_FEEDBACK_PASS_REASON",
    "REPORT_BLOCKED_REASON",
    "REPORT_WATCH_REASON",
    "EMPTY_FEEDBACK_REASON",
    "TeamSpecialistLearningFeedbackRouterV2DomainRoute",
    "TeamSpecialistLearningFeedbackRouterV2Config",
    "TeamSpecialistLearningFeedbackRouterV2Feedback",
    "TeamSpecialistLearningFeedbackRouterV2Assignment",
    "TeamSpecialistLearningFeedbackRouterV2Report",
    "build_team_specialist_learning_feedback_router_v2_report",
    "team_specialist_learning_feedback_router_v2_payload",
    "validate_team_specialist_learning_feedback_router_v2_public_payload",
)
