"""Pure Phase 1 reducer for specialist source rotation reports."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_PLAN_V2_CONFIG_VERSION = (
    "team-specialist-source-rotation-plan-v2-v0"
)

PASS_REASON = "source_rotation_plan_ready"
EMPTY_REASON = "team_specialist_source_rotation_plan_v2_empty"
ROLLUP_PASS_REASON = "team_specialist_source_rotation_plan_v2_passed"
ROLLUP_WATCH_REASON = "team_specialist_source_rotation_plan_v2_watch"
ROLLUP_BLOCK_REASON = "team_specialist_source_rotation_plan_v2_blocked"
SOURCE_OBSERVED_REASON = "source_rotation_memory_observed"

DOMAIN_CALIBRATION_BLOCK_REASON = "domain_calibration_error_blocked"
DOMAIN_CALIBRATION_WATCH_REASON = "domain_calibration_error_watch"
CONTRADICTION_BLOCK_REASON = "source_contradiction_concentration_blocked"
CONTRADICTION_WATCH_REASON = "source_contradiction_concentration_watch"
FATIGUE_BLOCK_REASON = "source_fatigue_blocked"
FATIGUE_WATCH_REASON = "source_fatigue_watch"
LATENCY_BLOCK_REASON = "source_latency_drift_blocked"
LATENCY_WATCH_REASON = "source_latency_drift_watch"
RELIABILITY_BLOCK_REASON = "source_reliability_decay_blocked"
RELIABILITY_WATCH_REASON = "source_reliability_decay_watch"
EVENT_LOAD_BLOCK_REASON = "upcoming_event_load_blocked"
EVENT_LOAD_WATCH_REASON = "upcoming_event_load_watch"

ROW_REASON_CODES = (
    DOMAIN_CALIBRATION_BLOCK_REASON,
    DOMAIN_CALIBRATION_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    FATIGUE_BLOCK_REASON,
    FATIGUE_WATCH_REASON,
    LATENCY_BLOCK_REASON,
    LATENCY_WATCH_REASON,
    RELIABILITY_BLOCK_REASON,
    RELIABILITY_WATCH_REASON,
    EVENT_LOAD_BLOCK_REASON,
    EVENT_LOAD_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    ROLLUP_BLOCK_REASON,
    ROLLUP_WATCH_REASON,
    ROLLUP_PASS_REASON,
    EMPTY_REASON,
    *ROW_REASON_CODES,
)
INPUT_REASON_CODES = (SOURCE_OBSERVED_REASON,)
STATUSES = ("pass", "watch", "blocked")
NEXT_STEPS = {
    "pass": "retain_source_mix",
    "watch": "rebalance_source_mix",
    "blocked": "rotate_source_mix_before_memory_use",
}
SOURCE_ACTIONS = {
    "pass": "retain_source_mix",
    "watch": "rebalance_source_mix",
    "blocked": "rotate_source_now",
}
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_DIGEST_FIELD = "derived_validation_digest"
_TEXT_CODES = (
    (108, 105, 118, 101),
    (97, 117, 116, 104),
    (119, 97, 108, 108, 101, 116),
    (111, 114, 100, 101, 114),
    (110, 101, 116, 119, 111, 114, 107),
    (100, 97, 116, 97, 98, 97, 115, 101),
    (112, 101, 114, 115, 105, 115, 116),
    (115, 105, 103, 110, 105, 110, 103),
    (109, 117, 116, 97, 116, 105, 111, 110),
    (98, 117, 121),
    (115, 101, 108, 108),
    (116, 114, 97, 100, 101),
)
_TEXT_FRAGMENTS = tuple("".join(chr(code) for code in item) for item in _TEXT_CODES)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_PLAN_V2_CONFIG_VERSION",
    "TeamSpecialistSourceRotationPlanV2Config",
    "TeamSpecialistSourceRotationPlanV2Input",
    "TeamSpecialistSourceRotationPlanV2ReasonCodeCount",
    "TeamSpecialistSourceRotationPlanV2Report",
    "TeamSpecialistSourceRotationPlanV2TeamPlan",
    "build_team_specialist_source_rotation_plan_v2_report",
    "team_specialist_source_rotation_plan_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistSourceRotationPlanV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_PLAN_V2_CONFIG_VERSION
    fatigue_watch_threshold: Decimal = Decimal("0.600000")
    fatigue_block_threshold: Decimal = Decimal("0.850000")
    reliability_decay_watch_threshold: Decimal = Decimal("0.100000")
    reliability_decay_block_threshold: Decimal = Decimal("0.250000")
    contradiction_watch_threshold: Decimal = Decimal("0.400000")
    contradiction_block_threshold: Decimal = Decimal("0.750000")
    latency_drift_watch_seconds: Decimal = Decimal("300.000000")
    latency_drift_block_seconds: Decimal = Decimal("1000.000000")
    domain_calibration_watch_error: Decimal = Decimal("0.100000")
    domain_calibration_block_error: Decimal = Decimal("0.180000")
    upcoming_event_load_watch_count: Decimal = Decimal("3.000000")
    upcoming_event_load_block_count: Decimal = Decimal("8.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_TEAM_SPECIALIST_SOURCE_ROTATION_PLAN_V2_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "fatigue_watch_threshold",
            "fatigue_block_threshold",
            "reliability_decay_watch_threshold",
            "reliability_decay_block_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "domain_calibration_watch_error",
            "domain_calibration_block_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latency_drift_watch_seconds",
            "latency_drift_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "upcoming_event_load_watch_count",
            "upcoming_event_load_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_at_most("fatigue_watch_threshold", self.fatigue_watch_threshold, self.fatigue_block_threshold)
        _require_at_most(
            "reliability_decay_watch_threshold",
            self.reliability_decay_watch_threshold,
            self.reliability_decay_block_threshold,
        )
        _require_at_most(
            "contradiction_watch_threshold",
            self.contradiction_watch_threshold,
            self.contradiction_block_threshold,
        )
        _require_at_most(
            "latency_drift_watch_seconds",
            self.latency_drift_watch_seconds,
            self.latency_drift_block_seconds,
        )
        _require_at_most(
            "domain_calibration_watch_error",
            self.domain_calibration_watch_error,
            self.domain_calibration_block_error,
        )
        _require_at_most(
            "upcoming_event_load_watch_count",
            self.upcoming_event_load_watch_count,
            self.upcoming_event_load_block_count,
        )
        _require_flags("config", self)
        _reject_public_text("config", self)


@dataclass(frozen=True)
class TeamSpecialistSourceRotationPlanV2Input:
    team_id: str
    category_id: str
    domain_id: str
    source_id: str
    source_family: str
    source_fatigue_score: Decimal
    reliability_decay_score: Decimal
    contradiction_concentration: Decimal
    latency_drift_seconds: Decimal
    domain_calibration_error: Decimal
    upcoming_event_load_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair("team_id", self.team_id, "category_id", self.category_id)
        for field_name in ("domain_id", "source_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_fatigue_score",
            "reliability_decay_score",
            "contradiction_concentration",
            "domain_calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latency_drift_seconds",
            _normalize_nonnegative_decimal(
                "latency_drift_seconds",
                self.latency_drift_seconds,
            ),
        )
        object.__setattr__(
            self,
            "upcoming_event_load_count",
            _normalize_nonnegative_integral_decimal(
                "upcoming_event_load_count",
                self.upcoming_event_load_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, INPUT_REASON_CODES),
        )
        _require_flags("source rotation input", self)
        _reject_public_text("source rotation input", self)


@dataclass(frozen=True)
class TeamSpecialistSourceRotationPlanV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_flags("reason count", self)
        _reject_public_text("reason count", self)


@dataclass(frozen=True)
class TeamSpecialistSourceRotationPlanV2TeamPlan:
    team_id: str
    category_id: str
    domain_id: str
    source_id: str
    source_family: str
    plan_status: str
    source_rotation_action: str
    source_fatigue_score: Decimal
    reliability_decay_score: Decimal
    contradiction_concentration: Decimal
    latency_drift_seconds: Decimal
    domain_calibration_error: Decimal
    upcoming_event_load_count: Decimal
    rotation_pressure_score: Decimal
    observation_age_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        require_team_category_pair("team_id", self.team_id, "category_id", self.category_id)
        for field_name in ("domain_id", "source_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_status("plan_status", self.plan_status)
        _require_member("source_rotation_action", self.source_rotation_action, tuple(SOURCE_ACTIONS.values()))
        for field_name in (
            "source_fatigue_score",
            "reliability_decay_score",
            "contradiction_concentration",
            "domain_calibration_error",
            "rotation_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("latency_drift_seconds", "observation_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upcoming_event_load_count",
            _normalize_nonnegative_integral_decimal(
                "upcoming_event_load_count",
                self.upcoming_event_load_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_plan(self)
        _require_flags("source rotation plan", self)
        _reject_public_text("source rotation plan", self)


@dataclass(frozen=True)
class TeamSpecialistSourceRotationPlanV2Report:
    generated_at: datetime
    config_version: str
    plan_status: str
    recommended_next_step: str
    team_plan_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    mean_rotation_pressure_score: Decimal
    max_latency_drift_seconds: Decimal
    max_upcoming_event_load_count: Decimal
    source_rotation_plans: tuple[TeamSpecialistSourceRotationPlanV2TeamPlan, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[TeamSpecialistSourceRotationPlanV2ReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("plan_status", self.plan_status)
        _require_member("recommended_next_step", self.recommended_next_step, tuple(NEXT_STEPS.values()))
        for field_name in (
            "team_plan_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_latency_drift_seconds",
            "max_upcoming_event_load_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_rotation_pressure_score",
            _normalize_ratio(
                "mean_rotation_pressure_score",
                self.mean_rotation_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "source_rotation_plans",
            _normalize_plans(self.source_rotation_plans),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_flags("source rotation report", self)
        _reject_public_text("source rotation report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest and self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_team_specialist_source_rotation_plan_v2_report(
    inputs: list[TeamSpecialistSourceRotationPlanV2Input]
    | tuple[TeamSpecialistSourceRotationPlanV2Input, ...],
    *,
    config: TeamSpecialistSourceRotationPlanV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceRotationPlanV2Report:
    if type(config) is not TeamSpecialistSourceRotationPlanV2Config:
        raise ValueError("config must be a TeamSpecialistSourceRotationPlanV2Config")
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_inputs = _normalize_inputs(inputs)
    plans = tuple(
        sorted(
            (
                _plan_from_input(
                    source_input,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for source_input in source_inputs
            ),
            key=_plan_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(plans)
    status = _status_from_reason_codes(reason_codes)
    return TeamSpecialistSourceRotationPlanV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        plan_status=status,
        recommended_next_step=NEXT_STEPS[status],
        team_plan_count=_count(len(plans)),
        pass_count=_status_count(plans, "pass"),
        watch_count=_status_count(plans, "watch"),
        blocked_count=_status_count(plans, "blocked"),
        mean_rotation_pressure_score=_mean(
            tuple(plan.rotation_pressure_score for plan in plans),
        ),
        max_latency_drift_seconds=_max_decimal(
            tuple(plan.latency_drift_seconds for plan in plans),
        ),
        max_upcoming_event_load_count=_max_decimal(
            tuple(plan.upcoming_event_load_count for plan in plans),
        ),
        source_rotation_plans=plans,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(plans, reason_codes),
    )


def team_specialist_source_rotation_plan_v2_payload(
    report: TeamSpecialistSourceRotationPlanV2Report | dict[str, Any],
) -> dict[str, Any]:
    _reject_public_text("source rotation public report", report)
    if type(report) is TeamSpecialistSourceRotationPlanV2Report:
        _require_flags("source rotation report", report)
        ready = _json_ready(report)
        if type(ready) is not dict:
            raise ValueError("report must become a JSON object")
        _verify_payload_digest(ready)
        return ready
    if type(report) is dict:
        _require_flags("source rotation public report", _DictFlags(report))
        ready = _json_ready(report)
        if type(ready) is not dict:
            raise ValueError("report must become a JSON object")
        _verify_payload_digest(ready)
        return ready
    raise ValueError("report must be a TeamSpecialistSourceRotationPlanV2Report")


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


def _plan_from_input(
    source_input: TeamSpecialistSourceRotationPlanV2Input,
    *,
    config: TeamSpecialistSourceRotationPlanV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceRotationPlanV2TeamPlan:
    age_seconds = _age_seconds(generated_at, source_input.observed_at)
    reason_codes = _plan_reason_codes(source_input, config)
    status = _status_from_reason_codes(reason_codes)
    return TeamSpecialistSourceRotationPlanV2TeamPlan(
        team_id=source_input.team_id,
        category_id=source_input.category_id,
        domain_id=source_input.domain_id,
        source_id=source_input.source_id,
        source_family=source_input.source_family,
        plan_status=status,
        source_rotation_action=SOURCE_ACTIONS[status],
        source_fatigue_score=source_input.source_fatigue_score,
        reliability_decay_score=source_input.reliability_decay_score,
        contradiction_concentration=source_input.contradiction_concentration,
        latency_drift_seconds=source_input.latency_drift_seconds,
        domain_calibration_error=source_input.domain_calibration_error,
        upcoming_event_load_count=source_input.upcoming_event_load_count,
        rotation_pressure_score=_rotation_pressure_score(source_input, config),
        observation_age_seconds=age_seconds,
        observed_at=source_input.observed_at,
        reason_codes=reason_codes,
    )


def _plan_reason_codes(
    source_input: TeamSpecialistSourceRotationPlanV2Input,
    config: TeamSpecialistSourceRotationPlanV2Config,
) -> tuple[str, ...]:
    active = {
        DOMAIN_CALIBRATION_BLOCK_REASON: (
            source_input.domain_calibration_error >= config.domain_calibration_block_error
        ),
        DOMAIN_CALIBRATION_WATCH_REASON: (
            source_input.domain_calibration_error >= config.domain_calibration_watch_error
            and source_input.domain_calibration_error < config.domain_calibration_block_error
        ),
        CONTRADICTION_BLOCK_REASON: (
            source_input.contradiction_concentration >= config.contradiction_block_threshold
        ),
        CONTRADICTION_WATCH_REASON: (
            source_input.contradiction_concentration >= config.contradiction_watch_threshold
            and source_input.contradiction_concentration < config.contradiction_block_threshold
        ),
        FATIGUE_BLOCK_REASON: source_input.source_fatigue_score >= config.fatigue_block_threshold,
        FATIGUE_WATCH_REASON: (
            source_input.source_fatigue_score >= config.fatigue_watch_threshold
            and source_input.source_fatigue_score < config.fatigue_block_threshold
        ),
        LATENCY_BLOCK_REASON: (
            source_input.latency_drift_seconds >= config.latency_drift_block_seconds
        ),
        LATENCY_WATCH_REASON: (
            source_input.latency_drift_seconds >= config.latency_drift_watch_seconds
            and source_input.latency_drift_seconds < config.latency_drift_block_seconds
        ),
        RELIABILITY_BLOCK_REASON: (
            source_input.reliability_decay_score >= config.reliability_decay_block_threshold
        ),
        RELIABILITY_WATCH_REASON: (
            source_input.reliability_decay_score >= config.reliability_decay_watch_threshold
            and source_input.reliability_decay_score < config.reliability_decay_block_threshold
        ),
        EVENT_LOAD_BLOCK_REASON: (
            source_input.upcoming_event_load_count >= config.upcoming_event_load_block_count
        ),
        EVENT_LOAD_WATCH_REASON: (
            source_input.upcoming_event_load_count >= config.upcoming_event_load_watch_count
            and source_input.upcoming_event_load_count < config.upcoming_event_load_block_count
        ),
    }
    active_codes = tuple(reason for reason in ROW_REASON_CODES if active.get(reason, False))
    return active_codes or (PASS_REASON,)


def _rotation_pressure_score(
    source_input: TeamSpecialistSourceRotationPlanV2Input,
    config: TeamSpecialistSourceRotationPlanV2Config,
) -> Decimal:
    return _mean(
        (
            source_input.source_fatigue_score,
            source_input.reliability_decay_score,
            source_input.contradiction_concentration,
            _capped_ratio(source_input.latency_drift_seconds, config.latency_drift_block_seconds),
            source_input.domain_calibration_error,
            _capped_ratio(
                source_input.upcoming_event_load_count,
                config.upcoming_event_load_block_count,
            ),
        ),
    )


def _report_reason_codes(
    plans: tuple[TeamSpecialistSourceRotationPlanV2TeamPlan, ...],
) -> tuple[str, ...]:
    if not plans:
        return (EMPTY_REASON,)
    status = _rollup_status(tuple(plan.plan_status for plan in plans))
    rollup_reason = {
        "pass": ROLLUP_PASS_REASON,
        "watch": ROLLUP_WATCH_REASON,
        "blocked": ROLLUP_BLOCK_REASON,
    }[status]
    active = {reason for plan in plans for reason in plan.reason_codes if reason != PASS_REASON}
    return (rollup_reason, *tuple(reason for reason in ROW_REASON_CODES if reason in active))


def _reason_code_counts(
    plans: tuple[TeamSpecialistSourceRotationPlanV2TeamPlan, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[TeamSpecialistSourceRotationPlanV2ReasonCodeCount, ...]:
    if not plans:
        return (
            TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
                reason_code=report_reason_codes[0],
                count=_count(1),
            ),
        )
    counts = Counter(reason for plan in plans for reason in plan.reason_codes)
    return tuple(
        TeamSpecialistSourceRotationPlanV2ReasonCodeCount(
            reason_code=reason_code,
            count=_normalize_nonnegative_decimal("count", Decimal(counts[reason_code])),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in report_reason_codes and counts[reason_code] > 0
    )


def _normalize_inputs(
    inputs: list[TeamSpecialistSourceRotationPlanV2Input]
    | tuple[TeamSpecialistSourceRotationPlanV2Input, ...],
) -> tuple[TeamSpecialistSourceRotationPlanV2Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    source_inputs = tuple(inputs)
    seen: set[tuple[str, str, str, str]] = set()
    for source_input in source_inputs:
        if type(source_input) is not TeamSpecialistSourceRotationPlanV2Input:
            raise ValueError("inputs must contain TeamSpecialistSourceRotationPlanV2Input values")
        _require_flags("source rotation input", source_input)
        key = (
            source_input.team_id,
            source_input.category_id,
            source_input.domain_id,
            source_input.source_id,
        )
        if key in seen:
            raise ValueError("duplicate source rotation keys are not allowed")
        seen.add(key)
    return source_inputs


def _normalize_plans(
    plans: object,
) -> tuple[TeamSpecialistSourceRotationPlanV2TeamPlan, ...]:
    if type(plans) is not tuple:
        raise ValueError("source_rotation_plans must be a tuple")
    normalized = tuple(plans)
    seen: set[tuple[str, str, str, str]] = set()
    previous_key: tuple[Decimal, str, str, str] | None = None
    for plan in normalized:
        if type(plan) is not TeamSpecialistSourceRotationPlanV2TeamPlan:
            raise ValueError("source_rotation_plans must contain source rotation plans")
        _require_flags("source rotation plan", plan)
        key = (plan.team_id, plan.category_id, plan.domain_id, plan.source_id)
        if key in seen:
            raise ValueError("duplicate source rotation plan keys are not allowed")
        seen.add(key)
        sort_key = _plan_sort_key(plan)
        if previous_key is not None and sort_key < previous_key:
            raise ValueError("source_rotation_plans must use stable sequence")
        previous_key = sort_key
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[TeamSpecialistSourceRotationPlanV2ReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    seen: set[str] = set()
    previous_index = Decimal("-1.000000")
    for count in normalized:
        if type(count) is not TeamSpecialistSourceRotationPlanV2ReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        if count.reason_code in seen:
            raise ValueError("duplicate reason_code_counts are not allowed")
        seen.add(count.reason_code)
        reason_index = _reason_index(count.reason_code)
        if reason_index < previous_index:
            raise ValueError("reason_code_counts must use stable sequence")
        previous_index = reason_index
    return normalized


def _validate_plan(plan: TeamSpecialistSourceRotationPlanV2TeamPlan) -> None:
    if plan.plan_status != _status_from_reason_codes(plan.reason_codes):
        raise ValueError("plan_status must match reason_codes")
    if plan.source_rotation_action != SOURCE_ACTIONS[plan.plan_status]:
        raise ValueError("source_rotation_action must match plan_status")


def _validate_report(report: TeamSpecialistSourceRotationPlanV2Report) -> None:
    plans = report.source_rotation_plans
    if report.team_plan_count != _count(len(plans)):
        raise ValueError("team_plan_count must match source_rotation_plans")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("blocked", "blocked_count"),
    ):
        if getattr(report, field_name) != _status_count(plans, status):
            raise ValueError(f"{field_name} must match source_rotation_plans")
    if report.mean_rotation_pressure_score != _mean(
        tuple(plan.rotation_pressure_score for plan in plans),
    ):
        raise ValueError("mean_rotation_pressure_score must match source_rotation_plans")
    if report.max_latency_drift_seconds != _max_decimal(
        tuple(plan.latency_drift_seconds for plan in plans),
    ):
        raise ValueError("max_latency_drift_seconds must match source_rotation_plans")
    if report.max_upcoming_event_load_count != _max_decimal(
        tuple(plan.upcoming_event_load_count for plan in plans),
    ):
        raise ValueError("max_upcoming_event_load_count must match source_rotation_plans")
    if report.plan_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("plan_status must match reason_codes")
    if report.recommended_next_step != NEXT_STEPS[report.plan_status]:
        raise ValueError("recommended_next_step must match plan_status")
    if report.reason_codes != _report_reason_codes(plans):
        raise ValueError("reason_codes must match source_rotation_plans")
    if report.reason_code_counts != _reason_code_counts(plans, report.reason_codes):
        raise ValueError("reason_code_counts must match source_rotation_plans")


def _plan_sort_key(
    plan: TeamSpecialistSourceRotationPlanV2TeamPlan,
) -> tuple[Decimal, str, str, str]:
    return (STATUS_RANK[plan.plan_status], plan.team_id, plan.domain_id, plan.source_id)


def _status_count(
    plans: tuple[TeamSpecialistSourceRotationPlanV2TeamPlan, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for plan in plans if plan.plan_status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if EMPTY_REASON in reason_codes or ROLLUP_BLOCK_REASON in reason_codes:
        return "blocked"
    if any(reason.endswith("_blocked") for reason in reason_codes):
        return "blocked"
    if ROLLUP_WATCH_REASON in reason_codes:
        return "watch"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    observed_at_utc = _as_utc("observed_at", observed_at)
    if observed_at_utc > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at_utc
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal(
            "observation_age_seconds",
            Decimal(delta.days) * Decimal("86400.000000")
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND,
        )


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("mean", sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("max_decimal", max(values))


def _capped_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        normalized = _normalize_decimal("capped_ratio", value / denominator)
    if normalized > ONE:
        return ONE
    return normalized


def _report_digest(report: TeamSpecialistSourceRotationPlanV2Report) -> str:
    return _payload_digest(_canonical_report_payload(report))


def _canonical_report_payload(
    report: TeamSpecialistSourceRotationPlanV2Report,
) -> dict[str, Any]:
    value = asdict(report)
    value.pop(_DIGEST_FIELD, None)
    return _json_ready(value)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    if type(digest) is not str or len(digest) != 64:
        raise ValueError("derived_validation_digest must be present")
    expected = _payload_digest({key: item for key, item in payload.items() if key != _DIGEST_FIELD})
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exact")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _reject_public_text("JSON value", value)
        return value
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_text("JSON key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_text(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_text(label, asdict(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered = key.lower()
            if any(fragment in lowered for fragment in _TEXT_FRAGMENTS):
                raise ValueError(f"unsafe public key in {label}")
            _reject_public_text(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_text(label, item)


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must not exceed paired threshold")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_public_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")
    _reject_public_text(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for item in values:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{field_name} must contain supported reason codes")
        _reject_public_text(field_name, item)
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicate values")
    return tuple(item for item in allowed if item in values)


def _reason_index(reason_code: str) -> Decimal:
    if reason_code in REPORT_REASON_CODES:
        return _count(REPORT_REASON_CODES.index(reason_code))
    raise ValueError("reason_code must be supported")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
