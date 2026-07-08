"""Pure report-only domain feedback loop latency reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_FEEDBACK_LOOP_LATENCY_REPORT_CONFIG_VERSION",
    "FEEDBACK_LOOP_LATENCY_STATUSES",
    "ResearchTeamDomainFeedbackLoopLatencyConfig",
    "ResearchTeamDomainFeedbackLoopLatencyInput",
    "ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount",
    "ResearchTeamDomainFeedbackLoopLatencyReport",
    "ResearchTeamDomainFeedbackLoopLatencyRow",
    "build_research_team_domain_feedback_loop_latency_report",
    "research_team_domain_feedback_loop_latency_report_payload",
    "validate_research_team_domain_feedback_loop_latency_report_payload",
)


DEFAULT_RESEARCH_TEAM_DOMAIN_FEEDBACK_LOOP_LATENCY_REPORT_CONFIG_VERSION = (
    "research-team-domain-feedback-loop-latency-report-v0"
)
FEEDBACK_LOOP_LATENCY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

ROW_STATUS_REASON_CODES = (
    "feedback_loop_latency_block",
    "feedback_loop_latency_watch",
    "feedback_loop_latency_pass",
)
BLOCK_REASON_CODES = (
    "feedback_age_block",
    "calibration_uptake_delay_block",
    "conflict_carry_forward_block",
    "review_backlog_pressure_block",
    "latency_pressure_block",
)
WATCH_REASON_CODES = (
    "feedback_age_watch",
    "calibration_uptake_delay_watch",
    "conflict_carry_forward_watch",
    "review_backlog_pressure_watch",
    "latency_pressure_watch",
)
EMPTY_REPORT_REASON_CODE = "feedback_loop_latency_empty"
REPORT_REASON_PRIORITY = (
    "feedback_loop_latency_block",
    *BLOCK_REASON_CODES,
    "feedback_loop_latency_watch",
    *WATCH_REASON_CODES,
    "feedback_loop_latency_pass",
)
ROW_REASON_CODES = (
    "feedback_loop_latency_pass",
    "feedback_loop_latency_watch",
    "feedback_loop_latency_block",
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "candi" + "date",
        "mar" + "ket",
        "sl" + "ug",
        "quest" + "ion",
        "u" + "rl",
        "src_" + "text",
        "source " + "text",
        "source_" + "text",
        "raw_" + "src",
        "raw_" + "source",
        "d" + "sn",
        "ta" + "ble",
        "to" + "ken",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "tr" + "ade",
        "li" + "ve",
        "data" + "base",
        "net" + "work",
        "requ" + "ests",
        "u" + "rl" + "lib",
        "sock" + "et",
        "sql" + "ite",
        "private_" + "key",
        "acco" + "unt",
        "sig" + "ning",
        "pos" + "ition",
        "reco" + "mmend",
        "siz" + "ing",
        "ht" + "tp",
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
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainFeedbackLoopLatencyConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_FEEDBACK_LOOP_LATENCY_REPORT_CONFIG_VERSION
    )
    watch_feedback_age_hours: Decimal = Decimal("24.000000")
    block_feedback_age_hours: Decimal = Decimal("72.000000")
    watch_calibration_uptake_delay_hours: Decimal = Decimal("48.000000")
    block_calibration_uptake_delay_hours: Decimal = Decimal("168.000000")
    watch_conflict_carry_forward_ratio: Decimal = Decimal("0.250000")
    block_conflict_carry_forward_ratio: Decimal = Decimal("0.600000")
    watch_review_backlog_pressure: Decimal = Decimal("0.600000")
    block_review_backlog_pressure: Decimal = Decimal("0.900000")
    watch_latency_pressure: Decimal = Decimal("0.500000")
    block_latency_pressure: Decimal = Decimal("0.850000")
    feedback_age_weight: Decimal = Decimal("0.250000")
    calibration_delay_weight: Decimal = Decimal("0.250000")
    conflict_carry_forward_weight: Decimal = Decimal("0.250000")
    review_backlog_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainFeedbackLoopLatencyConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "watch_feedback_age_hours",
            "block_feedback_age_hours",
            "watch_calibration_uptake_delay_hours",
            "block_calibration_uptake_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_carry_forward_ratio",
            "block_conflict_carry_forward_ratio",
            "watch_review_backlog_pressure",
            "block_review_backlog_pressure",
            "watch_latency_pressure",
            "block_latency_pressure",
            "feedback_age_weight",
            "calibration_delay_weight",
            "conflict_carry_forward_weight",
            "review_backlog_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainFeedbackLoopLatencyInput(_FinalPublicDataclass):
    domain_key: str
    feedback_signal_count: Decimal
    total_feedback_age_hours: Decimal
    calibration_update_count: Decimal
    total_calibration_uptake_delay_hours: Decimal
    unresolved_conflict_count: Decimal
    carried_forward_conflict_count: Decimal
    review_backlog_count: Decimal
    review_capacity_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainFeedbackLoopLatencyInput, "input")
        _require_public_code("domain_key", self.domain_key)
        for field_name in (
            "feedback_signal_count",
            "calibration_update_count",
            "unresolved_conflict_count",
            "carried_forward_conflict_count",
            "review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_feedback_age_hours",
            "total_calibration_uptake_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_capacity_count",
            _require_positive_count_decimal(
                "review_capacity_count",
                self.review_capacity_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainFeedbackLoopLatencyRow(_FinalPublicDataclass):
    domain_key: str
    feedback_signal_count: Decimal
    mean_feedback_age_hours: Decimal
    calibration_update_count: Decimal
    mean_calibration_uptake_delay_hours: Decimal
    unresolved_conflict_count: Decimal
    carried_forward_conflict_count: Decimal
    conflict_carry_forward_ratio: Decimal
    review_backlog_count: Decimal
    review_capacity_count: Decimal
    review_backlog_pressure: Decimal
    latency_pressure: Decimal
    latency_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainFeedbackLoopLatencyRow, "row")
        _require_public_code("domain_key", self.domain_key)
        for field_name in (
            "feedback_signal_count",
            "calibration_update_count",
            "unresolved_conflict_count",
            "carried_forward_conflict_count",
            "review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_feedback_age_hours",
            "mean_calibration_uptake_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_capacity_count",
            _require_positive_count_decimal(
                "review_capacity_count",
                self.review_capacity_count,
            ),
        )
        for field_name in (
            "conflict_carry_forward_ratio",
            "review_backlog_pressure",
            "latency_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("latency_status", self.latency_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "domain_ratio",
            _require_unit_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainFeedbackLoopLatencyReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    total_feedback_signal_count: Decimal
    total_calibration_update_count: Decimal
    total_unresolved_conflict_count: Decimal
    total_carried_forward_conflict_count: Decimal
    total_review_backlog_count: Decimal
    total_review_capacity_count: Decimal
    aggregate_feedback_age_hours: Decimal
    aggregate_calibration_uptake_delay_hours: Decimal
    aggregate_conflict_carry_forward_ratio: Decimal
    aggregate_review_backlog_pressure: Decimal
    max_latency_pressure: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainFeedbackLoopLatencyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "domain_count",
            "total_feedback_signal_count",
            "total_calibration_update_count",
            "total_unresolved_conflict_count",
            "total_carried_forward_conflict_count",
            "total_review_backlog_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_review_capacity_count",
            _require_nonnegative_count_decimal(
                "total_review_capacity_count",
                self.total_review_capacity_count,
            ),
        )
        for field_name in (
            "aggregate_feedback_age_hours",
            "aggregate_calibration_uptake_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_conflict_carry_forward_ratio",
            "aggregate_review_backlog_pressure",
            "max_latency_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_feedback_loop_latency_report_payload(self)


def build_research_team_domain_feedback_loop_latency_report(
    feedback_items: Iterable[ResearchTeamDomainFeedbackLoopLatencyInput],
    *,
    config: ResearchTeamDomainFeedbackLoopLatencyConfig,
    generated_at: datetime,
) -> ResearchTeamDomainFeedbackLoopLatencyReport:
    if type(config) is not ResearchTeamDomainFeedbackLoopLatencyConfig:
        raise ValueError("config must be a ResearchTeamDomainFeedbackLoopLatencyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(feedback_items)
    _reject_future_inputs(inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            _rows_for_inputs(inputs, config=config),
            key=_row_sort_key,
        ),
    )
    totals = _report_totals(rows)
    return ResearchTeamDomainFeedbackLoopLatencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_count(len(rows)),
        total_feedback_signal_count=totals["feedback_signal_count"],
        total_calibration_update_count=totals["calibration_update_count"],
        total_unresolved_conflict_count=totals["unresolved_conflict_count"],
        total_carried_forward_conflict_count=totals["carried_forward_conflict_count"],
        total_review_backlog_count=totals["review_backlog_count"],
        total_review_capacity_count=totals["review_capacity_count"],
        aggregate_feedback_age_hours=_aggregate_feedback_age(inputs),
        aggregate_calibration_uptake_delay_hours=_aggregate_calibration_delay(inputs),
        aggregate_conflict_carry_forward_ratio=_ratio_or_zero(
            totals["carried_forward_conflict_count"],
            totals["unresolved_conflict_count"],
        ),
        aggregate_review_backlog_pressure=_ratio_or_zero(
            totals["review_backlog_count"],
            totals["review_capacity_count"],
        ),
        max_latency_pressure=max((row.latency_pressure for row in rows), default=ZERO),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_feedback_loop_latency_report_payload(
    report: ResearchTeamDomainFeedbackLoopLatencyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainFeedbackLoopLatencyReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _report_derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report")
        payload = _report_public_payload_for_digest(report)
        payload["derived_validation_digest"] = report.derived_validation_digest
        validate_research_team_domain_feedback_loop_latency_report_payload(payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        validate_research_team_domain_feedback_loop_latency_report_payload(payload)
        return payload
    raise ValueError("report must be a ResearchTeamDomainFeedbackLoopLatencyReport")


def validate_research_team_domain_feedback_loop_latency_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(ready)
    _reject_unsafe_public_payload("payload", ready)
    _reject_public_numeric_values(ready)
    supplied_digest = _payload_required_string(ready, "derived_validation_digest")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _public_payload_derived_validation_digest(ready):
        raise ValueError("derived_validation_digest does not match payload")
    return True


def _normalize_inputs(
    feedback_items: Iterable[ResearchTeamDomainFeedbackLoopLatencyInput],
) -> tuple[ResearchTeamDomainFeedbackLoopLatencyInput, ...]:
    if isinstance(feedback_items, (str, bytes)):
        raise ValueError("feedback_items must be an iterable")
    try:
        items = tuple(feedback_items)
    except TypeError as exc:
        raise ValueError("feedback_items must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchTeamDomainFeedbackLoopLatencyInput:
            raise ValueError(
                "feedback_items must contain "
                "ResearchTeamDomainFeedbackLoopLatencyInput",
            )
        _require_hard_flags("input", item)
    return items


def _reject_future_inputs(
    inputs: tuple[ResearchTeamDomainFeedbackLoopLatencyInput, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows_for_inputs(
    inputs: tuple[ResearchTeamDomainFeedbackLoopLatencyInput, ...],
    *,
    config: ResearchTeamDomainFeedbackLoopLatencyConfig,
) -> tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...]:
    grouped: dict[str, list[ResearchTeamDomainFeedbackLoopLatencyInput]] = {}
    for item in inputs:
        grouped.setdefault(item.domain_key, []).append(item)
    return tuple(
        _row_for_domain(domain_key, tuple(grouped[domain_key]), config=config)
        for domain_key in sorted(grouped)
    )


def _row_for_domain(
    domain_key: str,
    items: tuple[ResearchTeamDomainFeedbackLoopLatencyInput, ...],
    *,
    config: ResearchTeamDomainFeedbackLoopLatencyConfig,
) -> ResearchTeamDomainFeedbackLoopLatencyRow:
    feedback_count = _sum_decimal(tuple(item.feedback_signal_count for item in items))
    feedback_age = _sum_decimal(tuple(item.total_feedback_age_hours for item in items))
    update_count = _sum_decimal(tuple(item.calibration_update_count for item in items))
    update_delay = _sum_decimal(
        tuple(item.total_calibration_uptake_delay_hours for item in items),
    )
    conflict_count = _sum_decimal(tuple(item.unresolved_conflict_count for item in items))
    carried_count = _sum_decimal(
        tuple(item.carried_forward_conflict_count for item in items),
    )
    backlog_count = _sum_decimal(tuple(item.review_backlog_count for item in items))
    capacity_count = _sum_decimal(tuple(item.review_capacity_count for item in items))
    mean_feedback_age = _ratio_or_zero(feedback_age, feedback_count)
    mean_update_delay = _ratio_or_zero(update_delay, update_count)
    conflict_ratio = _ratio_or_zero(carried_count, conflict_count)
    backlog_pressure = _ratio_or_zero(backlog_count, capacity_count)
    latency_pressure = _latency_pressure(
        mean_feedback_age_hours=mean_feedback_age,
        mean_calibration_uptake_delay_hours=mean_update_delay,
        conflict_carry_forward_ratio=conflict_ratio,
        review_backlog_pressure=backlog_pressure,
        config=config,
    )
    latency_status = _latency_status(
        mean_feedback_age_hours=mean_feedback_age,
        mean_calibration_uptake_delay_hours=mean_update_delay,
        conflict_carry_forward_ratio=conflict_ratio,
        review_backlog_pressure=backlog_pressure,
        latency_pressure=latency_pressure,
        config=config,
    )
    return ResearchTeamDomainFeedbackLoopLatencyRow(
        domain_key=domain_key,
        feedback_signal_count=feedback_count,
        mean_feedback_age_hours=mean_feedback_age,
        calibration_update_count=update_count,
        mean_calibration_uptake_delay_hours=mean_update_delay,
        unresolved_conflict_count=conflict_count,
        carried_forward_conflict_count=carried_count,
        conflict_carry_forward_ratio=conflict_ratio,
        review_backlog_count=backlog_count,
        review_capacity_count=capacity_count,
        review_backlog_pressure=backlog_pressure,
        latency_pressure=latency_pressure,
        latency_status=latency_status,
        observed_at=max(item.observed_at for item in items),
        reason_codes=_row_reason_codes(
            mean_feedback_age_hours=mean_feedback_age,
            mean_calibration_uptake_delay_hours=mean_update_delay,
            conflict_carry_forward_ratio=conflict_ratio,
            review_backlog_pressure=backlog_pressure,
            latency_pressure=latency_pressure,
            latency_status=latency_status,
            config=config,
        ),
    )


def _latency_pressure(
    *,
    mean_feedback_age_hours: Decimal,
    mean_calibration_uptake_delay_hours: Decimal,
    conflict_carry_forward_ratio: Decimal,
    review_backlog_pressure: Decimal,
    config: ResearchTeamDomainFeedbackLoopLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        pressure = (
            _weighted_pressure_component(
                mean_feedback_age_hours,
                config.block_feedback_age_hours,
                config.feedback_age_weight,
            )
            + _weighted_pressure_component(
                mean_calibration_uptake_delay_hours,
                config.block_calibration_uptake_delay_hours,
                config.calibration_delay_weight,
            )
            + _weighted_pressure_component(
                conflict_carry_forward_ratio,
                config.block_conflict_carry_forward_ratio,
                config.conflict_carry_forward_weight,
            )
            + _weighted_pressure_component(
                review_backlog_pressure,
                config.block_review_backlog_pressure,
                config.review_backlog_weight,
            )
        )
    return _clamp_unit(_quantize(pressure))


def _weighted_pressure_component(
    value: Decimal,
    block_value: Decimal,
    weight: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(_pressure_fraction(value, block_value) * weight)


def _pressure_fraction(value: Decimal, block_value: Decimal) -> Decimal:
    if block_value <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(_quantize(value / block_value))


def _latency_status(
    *,
    mean_feedback_age_hours: Decimal,
    mean_calibration_uptake_delay_hours: Decimal,
    conflict_carry_forward_ratio: Decimal,
    review_backlog_pressure: Decimal,
    latency_pressure: Decimal,
    config: ResearchTeamDomainFeedbackLoopLatencyConfig,
) -> str:
    if (
        mean_feedback_age_hours >= config.block_feedback_age_hours
        or mean_calibration_uptake_delay_hours
        >= config.block_calibration_uptake_delay_hours
        or conflict_carry_forward_ratio >= config.block_conflict_carry_forward_ratio
        or review_backlog_pressure >= config.block_review_backlog_pressure
        or latency_pressure >= config.block_latency_pressure
    ):
        return "block"
    if (
        mean_feedback_age_hours >= config.watch_feedback_age_hours
        or mean_calibration_uptake_delay_hours
        >= config.watch_calibration_uptake_delay_hours
        or conflict_carry_forward_ratio >= config.watch_conflict_carry_forward_ratio
        or review_backlog_pressure >= config.watch_review_backlog_pressure
        or latency_pressure >= config.watch_latency_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    mean_feedback_age_hours: Decimal,
    mean_calibration_uptake_delay_hours: Decimal,
    conflict_carry_forward_ratio: Decimal,
    review_backlog_pressure: Decimal,
    latency_pressure: Decimal,
    latency_status: str,
    config: ResearchTeamDomainFeedbackLoopLatencyConfig,
) -> tuple[str, ...]:
    reason_codes = [f"feedback_loop_latency_{latency_status}"]
    if mean_feedback_age_hours >= config.block_feedback_age_hours:
        reason_codes.append("feedback_age_block")
    elif mean_feedback_age_hours >= config.watch_feedback_age_hours:
        reason_codes.append("feedback_age_watch")
    if (
        mean_calibration_uptake_delay_hours
        >= config.block_calibration_uptake_delay_hours
    ):
        reason_codes.append("calibration_uptake_delay_block")
    elif (
        mean_calibration_uptake_delay_hours
        >= config.watch_calibration_uptake_delay_hours
    ):
        reason_codes.append("calibration_uptake_delay_watch")
    if conflict_carry_forward_ratio >= config.block_conflict_carry_forward_ratio:
        reason_codes.append("conflict_carry_forward_block")
    elif conflict_carry_forward_ratio >= config.watch_conflict_carry_forward_ratio:
        reason_codes.append("conflict_carry_forward_watch")
    if review_backlog_pressure >= config.block_review_backlog_pressure:
        reason_codes.append("review_backlog_pressure_block")
    elif review_backlog_pressure >= config.watch_review_backlog_pressure:
        reason_codes.append("review_backlog_pressure_watch")
    if latency_pressure >= config.block_latency_pressure:
        reason_codes.append("latency_pressure_block")
    elif latency_pressure >= config.watch_latency_pressure:
        reason_codes.append("latency_pressure_watch")
    return _require_row_reason_codes(tuple(reason_codes))


def _report_totals(
    rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...],
) -> dict[str, Decimal]:
    return {
        "feedback_signal_count": _sum_decimal(
            tuple(row.feedback_signal_count for row in rows),
        ),
        "calibration_update_count": _sum_decimal(
            tuple(row.calibration_update_count for row in rows),
        ),
        "unresolved_conflict_count": _sum_decimal(
            tuple(row.unresolved_conflict_count for row in rows),
        ),
        "carried_forward_conflict_count": _sum_decimal(
            tuple(row.carried_forward_conflict_count for row in rows),
        ),
        "review_backlog_count": _sum_decimal(
            tuple(row.review_backlog_count for row in rows),
        ),
        "review_capacity_count": _sum_decimal(
            tuple(row.review_capacity_count for row in rows),
        ),
    }


def _aggregate_feedback_age(
    inputs: tuple[ResearchTeamDomainFeedbackLoopLatencyInput, ...],
) -> Decimal:
    return _ratio_or_zero(
        _sum_decimal(tuple(item.total_feedback_age_hours for item in inputs)),
        _sum_decimal(tuple(item.feedback_signal_count for item in inputs)),
    )


def _aggregate_calibration_delay(
    inputs: tuple[ResearchTeamDomainFeedbackLoopLatencyInput, ...],
) -> Decimal:
    return _ratio_or_zero(
        _sum_decimal(tuple(item.total_calibration_uptake_delay_hours for item in inputs)),
        _sum_decimal(tuple(item.calibration_update_count for item in inputs)),
    )


def _status_count(
    rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.latency_status == status))


def _report_status(rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...]) -> str:
    if any(row.latency_status == "block" for row in rows):
        return "block"
    if any(row.latency_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    reason_codes = [f"feedback_loop_latency_report_{_report_status(rows)}"]
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in present:
            reason_codes.append(reason_code)
    return _require_report_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...],
) -> tuple[ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)}
    return tuple(
        ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount(
            reason_code=reason_code,
            count=count,
            domain_ratio=_ratio_or_zero(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchTeamDomainFeedbackLoopLatencyRow,
) -> tuple[Decimal, Decimal, str]:
    return (-STATUS_WEIGHT[row.latency_status], -row.latency_pressure, row.domain_key)


def _validate_config(config: ResearchTeamDomainFeedbackLoopLatencyConfig) -> None:
    if config.block_feedback_age_hours <= ZERO:
        raise ValueError("block_feedback_age_hours must be greater than zero")
    if config.block_calibration_uptake_delay_hours <= ZERO:
        raise ValueError(
            "block_calibration_uptake_delay_hours must be greater than zero",
        )
    if config.block_conflict_carry_forward_ratio <= ZERO:
        raise ValueError(
            "block_conflict_carry_forward_ratio must be greater than zero",
        )
    if config.block_review_backlog_pressure <= ZERO:
        raise ValueError("block_review_backlog_pressure must be greater than zero")
    if config.block_latency_pressure <= ZERO:
        raise ValueError("block_latency_pressure must be greater than zero")
    if config.watch_feedback_age_hours > config.block_feedback_age_hours:
        raise ValueError("watch_feedback_age_hours must not exceed block_feedback_age_hours")
    if (
        config.watch_calibration_uptake_delay_hours
        > config.block_calibration_uptake_delay_hours
    ):
        raise ValueError(
            "watch_calibration_uptake_delay_hours must not exceed "
            "block_calibration_uptake_delay_hours",
        )
    if (
        config.watch_conflict_carry_forward_ratio
        > config.block_conflict_carry_forward_ratio
    ):
        raise ValueError(
            "watch_conflict_carry_forward_ratio must not exceed "
            "block_conflict_carry_forward_ratio",
        )
    if config.watch_review_backlog_pressure > config.block_review_backlog_pressure:
        raise ValueError(
            "watch_review_backlog_pressure must not exceed block_review_backlog_pressure",
        )
    if config.watch_latency_pressure > config.block_latency_pressure:
        raise ValueError("watch_latency_pressure must not exceed block_latency_pressure")
    weight_sum = _sum_decimal(
        (
            config.feedback_age_weight,
            config.calibration_delay_weight,
            config.conflict_carry_forward_weight,
            config.review_backlog_weight,
        ),
    )
    if weight_sum != ONE:
        raise ValueError("latency pressure weights must sum to one")


def _validate_input(item: ResearchTeamDomainFeedbackLoopLatencyInput) -> None:
    if item.feedback_signal_count == ZERO and item.total_feedback_age_hours != ZERO:
        raise ValueError("total_feedback_age_hours requires feedback_signal_count")
    if (
        item.calibration_update_count == ZERO
        and item.total_calibration_uptake_delay_hours != ZERO
    ):
        raise ValueError(
            "total_calibration_uptake_delay_hours requires calibration_update_count",
        )
    if item.carried_forward_conflict_count > item.unresolved_conflict_count:
        raise ValueError(
            "carried_forward_conflict_count must not exceed unresolved_conflict_count",
        )


def _validate_row(row: ResearchTeamDomainFeedbackLoopLatencyRow) -> None:
    if row.carried_forward_conflict_count > row.unresolved_conflict_count:
        raise ValueError(
            "carried_forward_conflict_count must not exceed unresolved_conflict_count",
        )
    expected_status_reason = f"feedback_loop_latency_{row.latency_status}"
    if not row.reason_codes or row.reason_codes[0] != expected_status_reason:
        raise ValueError("latency_status must match reason_codes")
    if row.latency_status == "pass" and row.reason_codes != (
        "feedback_loop_latency_pass",
    ):
        raise ValueError("pass rows require feedback_loop_latency_pass")
    if row.latency_status != "pass" and "feedback_loop_latency_pass" in row.reason_codes:
        raise ValueError("queued rows must not contain pass reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamDomainFeedbackLoopLatencyReport,
) -> None:
    rows = report.rows
    totals = _report_totals(rows)
    checks = {
        "domain_count": _count(len(rows)),
        "total_feedback_signal_count": totals["feedback_signal_count"],
        "total_calibration_update_count": totals["calibration_update_count"],
        "total_unresolved_conflict_count": totals["unresolved_conflict_count"],
        "total_carried_forward_conflict_count": totals["carried_forward_conflict_count"],
        "total_review_backlog_count": totals["review_backlog_count"],
        "total_review_capacity_count": totals["review_capacity_count"],
        "aggregate_conflict_carry_forward_ratio": _ratio_or_zero(
            totals["carried_forward_conflict_count"],
            totals["unresolved_conflict_count"],
        ),
        "aggregate_review_backlog_pressure": _ratio_or_zero(
            totals["review_backlog_count"],
            totals["review_capacity_count"],
        ),
        "max_latency_pressure": max((row.latency_pressure for row in rows), default=ZERO),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...],
) -> tuple[ResearchTeamDomainFeedbackLoopLatencyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamDomainFeedbackLoopLatencyRow:
            raise ValueError("rows must contain ResearchTeamDomainFeedbackLoopLatencyRow")
        _require_hard_flags("row", row)
        if row.domain_key in seen:
            raise ValueError("rows must contain unique domain_key values")
        seen.add(row.domain_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _require_reason_code_counts(
    counts: tuple[ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    priority = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)}
    for item in normalized:
        if type(item) is not ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainFeedbackLoopLatencyReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason_code values")
        seen.add(item.reason_code)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (priority.get(item.reason_code, 999), item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_FEEDBACK_LOOP_LATENCY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _reject_unsafe_public_text("config_version", value)


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FEEDBACK_LOOP_LATENCY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must be non-empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must be non-empty")
    supported = {
        EMPTY_REPORT_REASON_CODE,
        "feedback_loop_latency_report_pass",
        "feedback_loop_latency_report_watch",
        "feedback_loop_latency_report_block",
        *REPORT_REASON_PRIORITY,
    }
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code("reason_code", reason_code)
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize(normalized)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_count_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize(normalized)


def _require_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be non-negative")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _clamp_unit(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_derived_validation_digest(
    report: ResearchTeamDomainFeedbackLoopLatencyReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _report_public_payload_for_digest(
    report: ResearchTeamDomainFeedbackLoopLatencyReport,
) -> dict[str, Any]:
    payload = _json_ready_without_digest(report)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    return payload


def _json_ready_without_digest(
    report: ResearchTeamDomainFeedbackLoopLatencyReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime value", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must use Decimal strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value
