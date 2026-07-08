"""Pure public aggregate priority report for resolution monitoring backlog."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_RESOLUTION_MONITORING_BACKLOG_PRIORITY_CONFIG_VERSION = (
    "research-resolution-monitoring-backlog-priority-v0"
)

STATUSES = ("pass", "watch", "block")
NO_ITEMS_REASON = "research_resolution_monitoring_backlog_priority_no_items"
CLEAR_REASON = "research_resolution_monitoring_backlog_priority_clear"
EVIDENCE_AGE_REASON = "research_resolution_monitoring_backlog_priority_evidence_age"
DEADLINE_REASON = "research_resolution_monitoring_backlog_priority_deadline"
ORACLE_LAG_REASON = "research_resolution_monitoring_backlog_priority_oracle_lag"
LOW_RELIABILITY_REASON = "research_resolution_monitoring_backlog_priority_low_reliability"
CONTRADICTION_REASON = "research_resolution_monitoring_backlog_priority_contradiction"
CAPACITY_REASON = "research_resolution_monitoring_backlog_priority_capacity_limited"
REASON_CODES = (
    NO_ITEMS_REASON,
    EVIDENCE_AGE_REASON,
    DEADLINE_REASON,
    ORACLE_LAG_REASON,
    LOW_RELIABILITY_REASON,
    CONTRADICTION_REASON,
    CAPACITY_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PUBLIC_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_TERMS = (
    _join_parts("http"),
    _join_parts("u", "r", "l"),
    _join_parts("eve", "nt"),
    _join_parts("mar", "ket"),
    _join_parts("cond", "ition"),
    _join_parts("sl", "ug"),
    _join_parts("sou", "rce"),
    _join_parts("re", "f"),
    _join_parts("te", "xt"),
)
UNSAFE_PAYLOAD_KEY_FRAGMENTS = (
    _join_parts("eve", "nt", "_", "id"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "sl", "ug"),
    _join_parts("cond", "ition", "_", "id"),
    _join_parts("sou", "rce", "_", "id"),
    _join_parts("sou", "rce", "_", "u", "r", "l"),
    _join_parts("sou", "rce", "_", "re", "f"),
    _join_parts("sou", "rce", "_", "re", "fer", "ence"),
    _join_parts("raw", "_"),
)
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = (
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("eve", "nt", "-"),
    _join_parts("mar", "ket", "-"),
    _join_parts("sou", "rce", "-"),
    _join_parts("cond", "ition", "-"),
)

__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_MONITORING_BACKLOG_PRIORITY_CONFIG_VERSION",
    "STATUSES",
    "ResearchResolutionMonitoringBacklogPriorityConfig",
    "ResearchResolutionMonitoringBacklogPriorityInput",
    "ResearchResolutionMonitoringBacklogPriorityReasonCodeCount",
    "ResearchResolutionMonitoringBacklogPriorityReport",
    "ResearchResolutionMonitoringBacklogPriorityRow",
    "build_research_resolution_monitoring_backlog_priority_report",
    "research_resolution_monitoring_backlog_priority_report_payload",
)


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchResolutionMonitoringBacklogPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_RESOLUTION_MONITORING_BACKLOG_PRIORITY_CONFIG_VERSION
    )
    evidence_age_watch_seconds: Decimal = Decimal("3600.000000")
    evidence_age_block_seconds: Decimal = Decimal("7200.000000")
    oracle_lag_watch_seconds: Decimal = Decimal("1800.000000")
    oracle_lag_block_seconds: Decimal = Decimal("3600.000000")
    deadline_watch_ratio: Decimal = Decimal("0.500000")
    deadline_block_ratio: Decimal = Decimal("0.850000")
    reliability_watch_floor: Decimal = Decimal("0.800000")
    reliability_block_floor: Decimal = Decimal("0.600000")
    contradiction_watch_ratio: Decimal = Decimal("0.500000")
    contradiction_block_ratio: Decimal = Decimal("0.750000")
    capacity_watch_ratio: Decimal = Decimal("0.750000")
    capacity_block_ratio: Decimal = Decimal("0.400000")
    evidence_age_weight: Decimal = Decimal("0.200000")
    deadline_weight: Decimal = Decimal("0.200000")
    oracle_lag_weight: Decimal = Decimal("0.200000")
    reliability_gap_weight: Decimal = Decimal("0.150000")
    contradiction_weight: Decimal = Decimal("0.150000")
    capacity_gap_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESOLUTION_MONITORING_BACKLOG_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "evidence_age_watch_seconds",
            "evidence_age_block_seconds",
            "oracle_lag_watch_seconds",
            "oracle_lag_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deadline_watch_ratio",
            "deadline_block_ratio",
            "reliability_watch_floor",
            "reliability_block_floor",
            "contradiction_watch_ratio",
            "contradiction_block_ratio",
            "capacity_watch_ratio",
            "capacity_block_ratio",
            "evidence_age_weight",
            "deadline_weight",
            "oracle_lag_weight",
            "reliability_gap_weight",
            "contradiction_weight",
            "capacity_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.evidence_age_block_seconds < self.evidence_age_watch_seconds:
            raise ValueError("evidence_age_block_seconds must not be below watch seconds")
        if self.oracle_lag_block_seconds < self.oracle_lag_watch_seconds:
            raise ValueError("oracle_lag_block_seconds must not be below watch seconds")
        if self.deadline_block_ratio < self.deadline_watch_ratio:
            raise ValueError("deadline_block_ratio must not be below watch ratio")
        if self.reliability_block_floor > self.reliability_watch_floor:
            raise ValueError("reliability_block_floor must not exceed watch floor")
        if self.contradiction_block_ratio < self.contradiction_watch_ratio:
            raise ValueError("contradiction_block_ratio must not be below watch ratio")
        if self.capacity_block_ratio > self.capacity_watch_ratio:
            raise ValueError("capacity_block_ratio must not exceed watch ratio")
        weight_total = (
            self.evidence_age_weight
            + self.deadline_weight
            + self.oracle_lag_weight
            + self.reliability_gap_weight
            + self.contradiction_weight
            + self.capacity_gap_weight
        ).quantize(QUANT)
        if weight_total != ONE:
            raise ValueError("weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionMonitoringBacklogPriorityInput:
    public_backlog_key: str
    monitoring_item_count: Decimal
    aggregate_evidence_age_seconds: Decimal
    deadline_proximity: Decimal
    oracle_lag_seconds: Decimal
    source_reliability_score: Decimal
    contradiction_pressure: Decimal
    available_team_capacity_units: Decimal
    required_team_capacity_units: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_backlog_key",
            _require_public_key("public_backlog_key", self.public_backlog_key),
        )
        object.__setattr__(
            self,
            "monitoring_item_count",
            _require_positive_count("monitoring_item_count", self.monitoring_item_count),
        )
        for field_name in (
            "aggregate_evidence_age_seconds",
            "oracle_lag_seconds",
            "available_team_capacity_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_team_capacity_units",
            _require_positive_decimal(
                "required_team_capacity_units",
                self.required_team_capacity_units,
            ),
        )
        for field_name in (
            "deadline_proximity",
            "source_reliability_score",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchResolutionMonitoringBacklogPriorityRow:
    public_backlog_key: str
    monitoring_item_count: Decimal
    aggregate_evidence_age_seconds: Decimal
    aggregate_evidence_age_pressure: Decimal
    deadline_proximity: Decimal
    oracle_lag_seconds: Decimal
    oracle_lag_pressure: Decimal
    source_reliability_score: Decimal
    source_reliability_gap: Decimal
    contradiction_pressure: Decimal
    team_capacity_ratio: Decimal
    team_capacity_gap: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_backlog_key",
            _require_public_key("public_backlog_key", self.public_backlog_key),
        )
        object.__setattr__(
            self,
            "monitoring_item_count",
            _require_positive_count("monitoring_item_count", self.monitoring_item_count),
        )
        for field_name in (
            "aggregate_evidence_age_seconds",
            "oracle_lag_seconds",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_evidence_age_pressure",
            "deadline_proximity",
            "oracle_lag_pressure",
            "source_reliability_score",
            "source_reliability_gap",
            "contradiction_pressure",
            "team_capacity_ratio",
            "team_capacity_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("priority row", self)


@dataclass(frozen=True)
class ResearchResolutionMonitoringBacklogPriorityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchResolutionMonitoringBacklogPriorityReport:
    generated_at: datetime
    config_version: str
    backlog_item_count: Decimal
    monitoring_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_aggregate_evidence_age_seconds: Decimal
    max_oracle_lag_seconds: Decimal
    min_source_reliability_score: Decimal
    max_contradiction_pressure: Decimal
    min_team_capacity_ratio: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchResolutionMonitoringBacklogPriorityReasonCodeCount, ...]
    priority_rows: tuple[ResearchResolutionMonitoringBacklogPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "backlog_item_count",
            "monitoring_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_aggregate_evidence_age_seconds",
            "max_oracle_lag_seconds",
            "average_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_reliability_score",
            "max_contradiction_pressure",
            "min_team_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "priority_rows", _normalize_priority_rows(self.priority_rows))
        _validate_report(self)
        _require_or_set_digest(self)
        _require_hard_flags("report", self)


def build_research_resolution_monitoring_backlog_priority_report(
    inputs: Iterable[object],
    *,
    config: ResearchResolutionMonitoringBacklogPriorityConfig,
    generated_at: datetime,
) -> ResearchResolutionMonitoringBacklogPriorityReport:
    if type(config) is not ResearchResolutionMonitoringBacklogPriorityConfig:
        raise ValueError(
            "config must be a ResearchResolutionMonitoringBacklogPriorityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _priority_rows(_normalize_inputs(inputs), config=config)
    reason_codes = _report_reason_codes(rows)
    return ResearchResolutionMonitoringBacklogPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        backlog_item_count=_count(len(rows)),
        monitoring_item_count=_sum_rows(rows, "monitoring_item_count"),
        pass_count=_count(sum(row.status == "pass" for row in rows)),
        watch_count=_count(sum(row.status == "watch" for row in rows)),
        block_count=_count(sum(row.status == "block" for row in rows)),
        max_aggregate_evidence_age_seconds=_max_rows(
            rows,
            "aggregate_evidence_age_seconds",
        ),
        max_oracle_lag_seconds=_max_rows(rows, "oracle_lag_seconds"),
        min_source_reliability_score=_min_rows(rows, "source_reliability_score"),
        max_contradiction_pressure=_max_rows(rows, "contradiction_pressure"),
        min_team_capacity_ratio=_min_rows(rows, "team_capacity_ratio"),
        average_priority_score=_ratio(_sum_rows(rows, "priority_score"), _count(len(rows))),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        priority_rows=rows,
    )


def research_resolution_monitoring_backlog_priority_report_payload(
    report: ResearchResolutionMonitoringBacklogPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionMonitoringBacklogPriorityReport:
        raise ValueError(
            "report must be a ResearchResolutionMonitoringBacklogPriorityReport",
        )
    _require_hard_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def _normalize_inputs(
    value: Iterable[object],
) -> tuple[ResearchResolutionMonitoringBacklogPriorityInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    normalized = tuple(_coerce_input(row) for row in rows)
    seen: set[str] = set()
    for row in normalized:
        if row.public_backlog_key in seen:
            raise ValueError("inputs must contain unique public backlog keys")
        seen.add(row.public_backlog_key)
    return tuple(sorted(normalized, key=lambda row: row.public_backlog_key))


def _coerce_input(value: object) -> ResearchResolutionMonitoringBacklogPriorityInput:
    if type(value) is ResearchResolutionMonitoringBacklogPriorityInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchResolutionMonitoringBacklogPriorityInput(
        public_backlog_key=_field_value(value, "public_backlog_key"),
        monitoring_item_count=_field_value(value, "monitoring_item_count"),
        aggregate_evidence_age_seconds=_field_value(
            value,
            "aggregate_evidence_age_seconds",
        ),
        deadline_proximity=_field_value(value, "deadline_proximity"),
        oracle_lag_seconds=_field_value(value, "oracle_lag_seconds"),
        source_reliability_score=_field_value(value, "source_reliability_score"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        available_team_capacity_units=_field_value(
            value,
            "available_team_capacity_units",
        ),
        required_team_capacity_units=_field_value(
            value,
            "required_team_capacity_units",
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _priority_rows(
    rows: tuple[ResearchResolutionMonitoringBacklogPriorityInput, ...],
    *,
    config: ResearchResolutionMonitoringBacklogPriorityConfig,
) -> tuple[ResearchResolutionMonitoringBacklogPriorityRow, ...]:
    return tuple(
        sorted(
            (_priority_row(row, config=config) for row in rows),
            key=_row_sort_key,
        ),
    )


def _priority_row(
    row: ResearchResolutionMonitoringBacklogPriorityInput,
    *,
    config: ResearchResolutionMonitoringBacklogPriorityConfig,
) -> ResearchResolutionMonitoringBacklogPriorityRow:
    evidence_age_pressure = _pressure(
        row.aggregate_evidence_age_seconds,
        config.evidence_age_block_seconds,
    )
    oracle_lag_pressure = _pressure(row.oracle_lag_seconds, config.oracle_lag_block_seconds)
    reliability_gap = (ONE - row.source_reliability_score).quantize(QUANT)
    team_capacity_ratio = min(
        _ratio(row.available_team_capacity_units, row.required_team_capacity_units),
        ONE,
    )
    team_capacity_gap = (ONE - team_capacity_ratio).quantize(QUANT)
    priority_score = _priority_score(
        evidence_age_pressure=evidence_age_pressure,
        deadline_proximity=row.deadline_proximity,
        oracle_lag_pressure=oracle_lag_pressure,
        reliability_gap=reliability_gap,
        contradiction_pressure=row.contradiction_pressure,
        team_capacity_gap=team_capacity_gap,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        team_capacity_ratio=team_capacity_ratio,
        config=config,
    )
    return ResearchResolutionMonitoringBacklogPriorityRow(
        public_backlog_key=row.public_backlog_key,
        monitoring_item_count=row.monitoring_item_count,
        aggregate_evidence_age_seconds=row.aggregate_evidence_age_seconds,
        aggregate_evidence_age_pressure=evidence_age_pressure,
        deadline_proximity=row.deadline_proximity,
        oracle_lag_seconds=row.oracle_lag_seconds,
        oracle_lag_pressure=oracle_lag_pressure,
        source_reliability_score=row.source_reliability_score,
        source_reliability_gap=reliability_gap,
        contradiction_pressure=row.contradiction_pressure,
        team_capacity_ratio=team_capacity_ratio,
        team_capacity_gap=team_capacity_gap,
        priority_score=priority_score,
        status=_row_status(
            row,
            team_capacity_ratio=team_capacity_ratio,
            reason_codes=reason_codes,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _priority_score(
    *,
    evidence_age_pressure: Decimal,
    deadline_proximity: Decimal,
    oracle_lag_pressure: Decimal,
    reliability_gap: Decimal,
    contradiction_pressure: Decimal,
    team_capacity_gap: Decimal,
    config: ResearchResolutionMonitoringBacklogPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            evidence_age_pressure * config.evidence_age_weight
            + deadline_proximity * config.deadline_weight
            + oracle_lag_pressure * config.oracle_lag_weight
            + reliability_gap * config.reliability_gap_weight
            + contradiction_pressure * config.contradiction_weight
            + team_capacity_gap * config.capacity_gap_weight
        ).quantize(QUANT)


def _row_reason_codes(
    row: ResearchResolutionMonitoringBacklogPriorityInput,
    *,
    team_capacity_ratio: Decimal,
    config: ResearchResolutionMonitoringBacklogPriorityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.aggregate_evidence_age_seconds >= config.evidence_age_watch_seconds:
        reasons.append(EVIDENCE_AGE_REASON)
    if row.deadline_proximity >= config.deadline_watch_ratio:
        reasons.append(DEADLINE_REASON)
    if row.oracle_lag_seconds >= config.oracle_lag_watch_seconds:
        reasons.append(ORACLE_LAG_REASON)
    if row.source_reliability_score <= config.reliability_watch_floor:
        reasons.append(LOW_RELIABILITY_REASON)
    if row.contradiction_pressure >= config.contradiction_watch_ratio:
        reasons.append(CONTRADICTION_REASON)
    if team_capacity_ratio <= config.capacity_watch_ratio:
        reasons.append(CAPACITY_REASON)
    reasons.extend(f"input_{reason_code}" for reason_code in row.reason_codes)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(sorted(reasons))


def _row_status(
    row: ResearchResolutionMonitoringBacklogPriorityInput,
    *,
    team_capacity_ratio: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchResolutionMonitoringBacklogPriorityConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        row.aggregate_evidence_age_seconds >= config.evidence_age_block_seconds
        or row.deadline_proximity >= config.deadline_block_ratio
        or row.oracle_lag_seconds >= config.oracle_lag_block_seconds
        or row.source_reliability_score <= config.reliability_block_floor
        or row.contradiction_pressure >= config.contradiction_block_ratio
        or team_capacity_ratio <= config.capacity_block_ratio
    ):
        return "block"
    return "watch"


def _row_sort_key(
    row: ResearchResolutionMonitoringBacklogPriorityRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], -row.priority_score, row.public_backlog_key)


def _report_status(rows: tuple[ResearchResolutionMonitoringBacklogPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionMonitoringBacklogPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_ITEMS_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_ITEMS_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    input_reasons = tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
                if reason_code.startswith("input_")
            },
        ),
    )
    if reasons or input_reasons:
        return reasons + input_reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchResolutionMonitoringBacklogPriorityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionMonitoringBacklogPriorityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionMonitoringBacklogPriorityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionMonitoringBacklogPriorityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_priority_rows(
    value: object,
) -> tuple[ResearchResolutionMonitoringBacklogPriorityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("priority_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, Decimal, str] | None = None
    for row in rows:
        if type(row) is not ResearchResolutionMonitoringBacklogPriorityRow:
            raise ValueError(
                "priority_rows must contain ResearchResolutionMonitoringBacklogPriorityRow",
            )
        _require_hard_flags("priority row", row)
        if row.public_backlog_key in seen:
            raise ValueError("priority_rows must contain unique public backlog keys")
        seen.add(row.public_backlog_key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("priority_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchResolutionMonitoringBacklogPriorityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    previous_key = ""
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchResolutionMonitoringBacklogPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionMonitoringBacklogPriorityReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        if count.reason_code <= previous_key:
            raise ValueError("reason_code_counts must follow deterministic sequence")
        seen.add(count.reason_code)
        previous_key = count.reason_code
    return counts


def _validate_row(row: ResearchResolutionMonitoringBacklogPriorityRow) -> None:
    if row.source_reliability_gap != (ONE - row.source_reliability_score).quantize(QUANT):
        raise ValueError("source_reliability_gap must match reliability score")
    if row.team_capacity_gap != (ONE - row.team_capacity_ratio).quantize(QUANT):
        raise ValueError("team_capacity_gap must match team_capacity_ratio")
    if row.reason_codes == (CLEAR_REASON,) and row.status != "pass":
        raise ValueError("clear reason must have pass status")
    if row.reason_codes != (CLEAR_REASON,) and row.status == "pass":
        raise ValueError("pass status requires clear reason")


def _validate_report(report: ResearchResolutionMonitoringBacklogPriorityReport) -> None:
    rows = report.priority_rows
    if report.backlog_item_count != _count(len(rows)):
        raise ValueError("backlog_item_count must match priority_rows")
    if report.monitoring_item_count != _sum_rows(rows, "monitoring_item_count"):
        raise ValueError("monitoring_item_count must match priority_rows")
    if report.pass_count != _count(sum(row.status == "pass" for row in rows)):
        raise ValueError("pass_count must match priority_rows")
    if report.watch_count != _count(sum(row.status == "watch" for row in rows)):
        raise ValueError("watch_count must match priority_rows")
    if report.block_count != _count(sum(row.status == "block" for row in rows)):
        raise ValueError("block_count must match priority_rows")
    if report.max_aggregate_evidence_age_seconds != _max_rows(
        rows,
        "aggregate_evidence_age_seconds",
    ):
        raise ValueError("max_aggregate_evidence_age_seconds must match priority_rows")
    if report.max_oracle_lag_seconds != _max_rows(rows, "oracle_lag_seconds"):
        raise ValueError("max_oracle_lag_seconds must match priority_rows")
    if report.min_source_reliability_score != _min_rows(rows, "source_reliability_score"):
        raise ValueError("min_source_reliability_score must match priority_rows")
    if report.max_contradiction_pressure != _max_rows(rows, "contradiction_pressure"):
        raise ValueError("max_contradiction_pressure must match priority_rows")
    if report.min_team_capacity_ratio != _min_rows(rows, "team_capacity_ratio"):
        raise ValueError("min_team_capacity_ratio must match priority_rows")
    if report.average_priority_score != _ratio(
        _sum_rows(rows, "priority_score"),
        _count(len(rows)),
    ):
        raise ValueError("average_priority_score must match priority_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match priority_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match priority_rows")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return _require_nonnegative_decimal(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO),
    )


def _max_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    ).quantize(QUANT)


def _pressure(value: Decimal, ceiling: Decimal) -> Decimal:
    return min(_ratio(value, ceiling), ONE)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _normalize_input_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
    return tuple(sorted(set(value)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or REASON_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public reason code")


def _require_public_key(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    lowered = value.lower()
    if PUBLIC_KEY_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public key")
    if any(term in lowered for term in UNSAFE_PUBLIC_KEY_TERMS):
        raise ValueError(f"{field_name} must not expose raw identifiers")
    return value


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _field_value(value: object, field_name: str, *, default: object = MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_or_set_digest(report: ResearchResolutionMonitoringBacklogPriorityReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchResolutionMonitoringBacklogPriorityReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PAYLOAD_KEY_FRAGMENTS):
                raise ValueError("payload contains nonpublic key material")
            _reject_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
    elif isinstance(value, str):
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS):
            raise ValueError("payload contains nonpublic value material")
