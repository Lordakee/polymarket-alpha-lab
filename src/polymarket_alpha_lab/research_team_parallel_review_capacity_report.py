"""Pure aggregate parallel review capacity report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_CAPACITY_REPORT_CONFIG_VERSION = (
    "research-team-parallel-review-capacity-report-v0"
)

STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CLEAR_REASON = "parallel_review_capacity_clear"
EMPTY_REASON = "parallel_review_capacity_no_inputs"
REPORT_PASS_REASON = "parallel_review_capacity_report_pass"
REPORT_WATCH_REASON = "parallel_review_capacity_report_watch"
REPORT_BLOCK_REASON = "parallel_review_capacity_report_block"

ACTIVE_LOAD_WATCH_REASON = "active_packet_load_watch"
ACTIVE_LOAD_BLOCK_REASON = "active_packet_load_block"
SLA_AGE_WATCH_REASON = "sla_age_watch"
SLA_AGE_BLOCK_REASON = "sla_age_block"
UNRESOLVED_ESCALATION_WATCH_REASON = "unresolved_escalation_watch"
UNRESOLVED_ESCALATION_BLOCK_REASON = "unresolved_escalation_block"
MEMORY_WRITEBACK_WATCH_REASON = "memory_writeback_delay_watch"
MEMORY_WRITEBACK_BLOCK_REASON = "memory_writeback_delay_block"
MANUAL_ESCALATION_WATCH_REASON = "manual_escalation_urgency_watch"
MANUAL_ESCALATION_BLOCK_REASON = "manual_escalation_urgency_block"

ROW_REASON_CODE_PRIORITY = (
    CLEAR_REASON,
    ACTIVE_LOAD_BLOCK_REASON,
    SLA_AGE_BLOCK_REASON,
    UNRESOLVED_ESCALATION_BLOCK_REASON,
    MEMORY_WRITEBACK_BLOCK_REASON,
    MANUAL_ESCALATION_BLOCK_REASON,
    ACTIVE_LOAD_WATCH_REASON,
    SLA_AGE_WATCH_REASON,
    UNRESOLVED_ESCALATION_WATCH_REASON,
    MEMORY_WRITEBACK_WATCH_REASON,
    MANUAL_ESCALATION_WATCH_REASON,
)
REASON_CODE_PRIORITY = (
    CLEAR_REASON,
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    ACTIVE_LOAD_BLOCK_REASON,
    SLA_AGE_BLOCK_REASON,
    UNRESOLVED_ESCALATION_BLOCK_REASON,
    MEMORY_WRITEBACK_BLOCK_REASON,
    MANUAL_ESCALATION_BLOCK_REASON,
    REPORT_WATCH_REASON,
    ACTIVE_LOAD_WATCH_REASON,
    SLA_AGE_WATCH_REASON,
    UNRESOLVED_ESCALATION_WATCH_REASON,
    MEMORY_WRITEBACK_WATCH_REASON,
    MANUAL_ESCALATION_WATCH_REASON,
    REPORT_PASS_REASON,
)
REASON_CODE_RANK = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)
}

PAPER_QUEUE_ACTIONS = {
    "pass": "paper_parallel_review_capacity_monitor",
    "watch": "paper_parallel_review_capacity_watch",
    "block": "paper_parallel_review_capacity_block",
}

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "network",
    "database",
    "recommendation",
    "sizing",
    "private",
    "secret",
    "credential",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_CAPACITY_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamParallelReviewCapacityConfig",
    "ResearchTeamParallelReviewCapacityInput",
    "ResearchTeamParallelReviewCapacityReasonCodeCount",
    "ResearchTeamParallelReviewCapacityReport",
    "ResearchTeamParallelReviewCapacityRow",
    "build_research_team_parallel_review_capacity_report",
    "research_team_parallel_review_capacity_report_digest",
    "research_team_parallel_review_capacity_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamParallelReviewCapacityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_CAPACITY_REPORT_CONFIG_VERSION
    )
    watch_active_load_ratio: Decimal = Decimal("0.700000")
    block_active_load_ratio: Decimal = Decimal("1.100000")
    watch_sla_age_seconds: Decimal = Decimal("1800")
    block_sla_age_seconds: Decimal = Decimal("3600")
    watch_unresolved_escalation_ratio: Decimal = Decimal("0.200000")
    block_unresolved_escalation_ratio: Decimal = Decimal("0.400000")
    watch_memory_writeback_delay_seconds: Decimal = Decimal("900")
    block_memory_writeback_delay_seconds: Decimal = Decimal("1800")
    watch_manual_escalation_urgency: Decimal = Decimal("0.500000")
    block_manual_escalation_urgency: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewCapacityConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "watch_active_load_ratio",
            "block_active_load_ratio",
            "watch_unresolved_escalation_ratio",
            "block_unresolved_escalation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_sla_age_seconds",
            "block_sla_age_seconds",
            "watch_memory_writeback_delay_seconds",
            "block_memory_writeback_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_manual_escalation_urgency",
            "block_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "watch_active_load_ratio",
            self.watch_active_load_ratio,
            "block_active_load_ratio",
            self.block_active_load_ratio,
        )
        _require_threshold_order(
            "watch_sla_age_seconds",
            self.watch_sla_age_seconds,
            "block_sla_age_seconds",
            self.block_sla_age_seconds,
        )
        _require_threshold_order(
            "watch_unresolved_escalation_ratio",
            self.watch_unresolved_escalation_ratio,
            "block_unresolved_escalation_ratio",
            self.block_unresolved_escalation_ratio,
        )
        _require_threshold_order(
            "watch_memory_writeback_delay_seconds",
            self.watch_memory_writeback_delay_seconds,
            "block_memory_writeback_delay_seconds",
            self.block_memory_writeback_delay_seconds,
        )
        _require_threshold_order(
            "watch_manual_escalation_urgency",
            self.watch_manual_escalation_urgency,
            "block_manual_escalation_urgency",
            self.block_manual_escalation_urgency,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewCapacityInput(_FinalPublicDataclass):
    review_team_key: str
    reviewer_pool_key: str
    available_reviewer_count: Decimal
    active_packet_count: Decimal
    oldest_sla_age_seconds: Decimal
    unresolved_escalation_count: Decimal
    memory_writeback_delay_seconds: Decimal
    manual_escalation_urgency: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewCapacityInput, "input")
        _require_public_label("review_team_key", self.review_team_key)
        _require_public_label("reviewer_pool_key", self.reviewer_pool_key)
        object.__setattr__(
            self,
            "available_reviewer_count",
            _require_positive_whole_decimal(
                "available_reviewer_count",
                self.available_reviewer_count,
            ),
        )
        for field_name in (
            "active_packet_count",
            "oldest_sla_age_seconds",
            "unresolved_escalation_count",
            "memory_writeback_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_escalation_urgency",
            _require_ratio_decimal(
                "manual_escalation_urgency",
                self.manual_escalation_urgency,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewCapacityRow(_FinalPublicDataclass):
    review_team_key: str
    reviewer_pool_key: str
    observed_at: datetime
    available_reviewer_count: Decimal
    active_packet_count: Decimal
    oldest_sla_age_seconds: Decimal
    unresolved_escalation_count: Decimal
    memory_writeback_delay_seconds: Decimal
    manual_escalation_urgency: Decimal
    active_load_ratio: Decimal
    reviewer_availability_ratio: Decimal
    escalation_load_ratio: Decimal
    capacity_pressure_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewCapacityRow, "row")
        _require_public_label("review_team_key", self.review_team_key)
        _require_public_label("reviewer_pool_key", self.reviewer_pool_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "available_reviewer_count",
            _require_positive_whole_decimal(
                "available_reviewer_count",
                self.available_reviewer_count,
            ),
        )
        for field_name in (
            "active_packet_count",
            "oldest_sla_age_seconds",
            "unresolved_escalation_count",
            "memory_writeback_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_escalation_urgency",
            _require_ratio_decimal(
                "manual_escalation_urgency",
                self.manual_escalation_urgency,
            ),
        )
        for field_name in (
            "active_load_ratio",
            "reviewer_availability_ratio",
            "escalation_load_ratio",
            "capacity_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewCapacityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    review_scope_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamParallelReviewCapacityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_label("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "review_scope_ratio",
            _require_nonnegative_decimal(
                "review_scope_ratio",
                self.review_scope_ratio,
            ),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewCapacityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    review_scope_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_available_reviewer_count: Decimal
    total_active_packet_count: Decimal
    total_unresolved_escalation_count: Decimal
    max_oldest_sla_age_seconds: Decimal
    max_memory_writeback_delay_seconds: Decimal
    max_manual_escalation_urgency: Decimal
    max_capacity_pressure_ratio: Decimal
    average_capacity_pressure_ratio: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamParallelReviewCapacityReasonCodeCount, ...]
    rows: tuple[ResearchTeamParallelReviewCapacityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewCapacityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "review_scope_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_available_reviewer_count",
            "total_active_packet_count",
            "total_unresolved_escalation_count",
            "max_oldest_sla_age_seconds",
            "max_memory_writeback_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_manual_escalation_urgency",
            "max_capacity_pressure_ratio",
            "average_capacity_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_label("paper_queue_action", self.paper_queue_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_status_fields(self)
        _require_hard_flags("report", self)
        expected_digest = _report_payload_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_parallel_review_capacity_report_payload(self)


def build_research_team_parallel_review_capacity_report(
    inputs: Iterable[object],
    *,
    config: ResearchTeamParallelReviewCapacityConfig,
    generated_at: datetime,
) -> ResearchTeamParallelReviewCapacityReport:
    if type(config) is not ResearchTeamParallelReviewCapacityConfig:
        raise ValueError("config must be a ResearchTeamParallelReviewCapacityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    reason_codes = _summary_reason_codes(rows)
    return ResearchTeamParallelReviewCapacityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        review_scope_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_available_reviewer_count=_sum_decimal(rows, "available_reviewer_count"),
        total_active_packet_count=_sum_decimal(rows, "active_packet_count"),
        total_unresolved_escalation_count=_sum_decimal(
            rows,
            "unresolved_escalation_count",
        ),
        max_oldest_sla_age_seconds=max(
            (row.oldest_sla_age_seconds for row in rows),
            default=ZERO,
        ),
        max_memory_writeback_delay_seconds=max(
            (row.memory_writeback_delay_seconds for row in rows),
            default=ZERO,
        ),
        max_manual_escalation_urgency=max(
            (row.manual_escalation_urgency for row in rows),
            default=ZERO,
        ),
        max_capacity_pressure_ratio=max(
            (row.capacity_pressure_ratio for row in rows),
            default=ZERO,
        ),
        average_capacity_pressure_ratio=_average_row_ratio(
            rows,
            "capacity_pressure_ratio",
        ),
        status=status,
        paper_queue_action=PAPER_QUEUE_ACTIONS[status],
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_parallel_review_capacity_report_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchTeamParallelReviewCapacityReport:
        _require_hard_flags("report", value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = _payload_value(value)
    else:
        raise ValueError(
            "value must be a ResearchTeamParallelReviewCapacityReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    _validate_payload_digest(payload)
    return payload


def research_team_parallel_review_capacity_report_digest(
    report: ResearchTeamParallelReviewCapacityReport,
) -> str:
    if type(report) is not ResearchTeamParallelReviewCapacityReport:
        raise ValueError("report must be a ResearchTeamParallelReviewCapacityReport")
    return report.derived_validation_digest


def _row_from_input(
    item: ResearchTeamParallelReviewCapacityInput,
    *,
    config: ResearchTeamParallelReviewCapacityConfig,
) -> ResearchTeamParallelReviewCapacityRow:
    active_load_ratio = _ratio(item.active_packet_count, item.available_reviewer_count)
    reviewer_availability_ratio = _ratio(
        item.available_reviewer_count,
        item.available_reviewer_count + item.active_packet_count,
    )
    escalation_load_ratio = _ratio_or_zero(
        item.unresolved_escalation_count,
        item.active_packet_count,
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        active_load_ratio=active_load_ratio,
        escalation_load_ratio=escalation_load_ratio,
    )
    status = _row_status(reason_codes)
    return ResearchTeamParallelReviewCapacityRow(
        review_team_key=item.review_team_key,
        reviewer_pool_key=item.reviewer_pool_key,
        observed_at=item.observed_at,
        available_reviewer_count=item.available_reviewer_count,
        active_packet_count=item.active_packet_count,
        oldest_sla_age_seconds=item.oldest_sla_age_seconds,
        unresolved_escalation_count=item.unresolved_escalation_count,
        memory_writeback_delay_seconds=item.memory_writeback_delay_seconds,
        manual_escalation_urgency=item.manual_escalation_urgency,
        active_load_ratio=active_load_ratio,
        reviewer_availability_ratio=reviewer_availability_ratio,
        escalation_load_ratio=escalation_load_ratio,
        capacity_pressure_ratio=_capacity_pressure_ratio(
            item,
            config=config,
            active_load_ratio=active_load_ratio,
            reason_codes=reason_codes,
            status=status,
        ),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamParallelReviewCapacityInput,
    *,
    config: ResearchTeamParallelReviewCapacityConfig,
    active_load_ratio: Decimal,
    escalation_load_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if active_load_ratio >= config.block_active_load_ratio:
        reason_codes.append(ACTIVE_LOAD_BLOCK_REASON)
    elif active_load_ratio >= config.watch_active_load_ratio:
        reason_codes.append(ACTIVE_LOAD_WATCH_REASON)
    if item.oldest_sla_age_seconds >= config.block_sla_age_seconds:
        reason_codes.append(SLA_AGE_BLOCK_REASON)
    elif item.oldest_sla_age_seconds >= config.watch_sla_age_seconds:
        reason_codes.append(SLA_AGE_WATCH_REASON)
    if escalation_load_ratio >= config.block_unresolved_escalation_ratio:
        reason_codes.append(UNRESOLVED_ESCALATION_BLOCK_REASON)
    elif escalation_load_ratio >= config.watch_unresolved_escalation_ratio:
        reason_codes.append(UNRESOLVED_ESCALATION_WATCH_REASON)
    if item.memory_writeback_delay_seconds >= config.block_memory_writeback_delay_seconds:
        reason_codes.append(MEMORY_WRITEBACK_BLOCK_REASON)
    elif item.memory_writeback_delay_seconds >= config.watch_memory_writeback_delay_seconds:
        reason_codes.append(MEMORY_WRITEBACK_WATCH_REASON)
    if item.manual_escalation_urgency >= config.block_manual_escalation_urgency:
        reason_codes.append(MANUAL_ESCALATION_BLOCK_REASON)
    elif item.manual_escalation_urgency >= config.watch_manual_escalation_urgency:
        reason_codes.append(MANUAL_ESCALATION_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _capacity_pressure_ratio(
    item: ResearchTeamParallelReviewCapacityInput,
    *,
    config: ResearchTeamParallelReviewCapacityConfig,
    active_load_ratio: Decimal,
    reason_codes: tuple[str, ...],
    status: str,
) -> Decimal:
    if status == "block":
        return ONE
    if status == "pass":
        return _clamp_ratio(active_load_ratio)
    manual_reserve_count = (
        ONE
        if item.manual_escalation_urgency >= config.watch_manual_escalation_urgency
        else ZERO
    )
    return _ratio(
        item.active_packet_count + item.unresolved_escalation_count,
        item.available_reviewer_count
        + item.active_packet_count
        + item.unresolved_escalation_count
        + manual_reserve_count,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamParallelReviewCapacityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchTeamParallelReviewCapacityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append(REPORT_BLOCK_REASON)
        reason_codes.extend(
            reason_code
            for reason_code in ROW_REASON_CODE_PRIORITY
            if reason_code.endswith("_block")
            and any(reason_code in row.reason_codes for row in rows)
        )
    if any(row.status == "watch" for row in rows):
        reason_codes.append(REPORT_WATCH_REASON)
        reason_codes.extend(
            reason_code
            for reason_code in ROW_REASON_CODE_PRIORITY
            if reason_code.endswith("_watch")
            and any(reason_code in row.reason_codes for row in rows)
        )
    if not reason_codes:
        reason_codes.append(REPORT_PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamParallelReviewCapacityRow, ...],
) -> tuple[ResearchTeamParallelReviewCapacityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamParallelReviewCapacityReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            review_scope_ratio=_ratio(Decimal(counter[reason_code]), row_count),
        )
        for reason_code in ROW_REASON_CODE_PRIORITY
        if counter.get(reason_code, 0) > 0
    )


def _normalize_inputs(
    inputs: Iterable[object],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamParallelReviewCapacityInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized: list[ResearchTeamParallelReviewCapacityInput] = []
    seen_keys: set[tuple[str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchTeamParallelReviewCapacityInput:
            raise ValueError("inputs must contain ResearchTeamParallelReviewCapacityInput")
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        key = (item.review_team_key, item.reviewer_pool_key)
        if key in seen_keys:
            raise ValueError("review team and reviewer pool keys must be unique")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Iterable[object],
) -> tuple[ResearchTeamParallelReviewCapacityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized: list[ResearchTeamParallelReviewCapacityRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamParallelReviewCapacityRow:
            raise ValueError("rows must contain ResearchTeamParallelReviewCapacityRow")
        _require_hard_flags("row", row)
        key = (row.review_team_key, row.reviewer_pool_key)
        if key in seen_keys:
            raise ValueError("rows review team and reviewer pool keys must be unique")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[object],
) -> tuple[ResearchTeamParallelReviewCapacityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized: list[ResearchTeamParallelReviewCapacityReasonCodeCount] = []
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not ResearchTeamParallelReviewCapacityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamParallelReviewCapacityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
        normalized.append(count)
    return tuple(
        sorted(normalized, key=lambda count: REASON_CODE_RANK[count.reason_code]),
    )


def _row_sort_key(row: ResearchTeamParallelReviewCapacityRow) -> tuple[int, Decimal, str, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.capacity_pressure_ratio,
        row.review_team_key,
        row.reviewer_pool_key,
    )


def _status_count(
    rows: tuple[ResearchTeamParallelReviewCapacityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_decimal(
    rows: tuple[ResearchTeamParallelReviewCapacityRow, ...],
    field_name: str,
) -> Decimal:
    return _count(sum((getattr(row, field_name) for row in rows), ZERO))


def _average_row_ratio(
    rows: tuple[ResearchTeamParallelReviewCapacityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _ratio(
            sum((getattr(row, field_name) for row in rows), ZERO),
            Decimal(len(rows)),
        )


def _validate_input_counts(item: ResearchTeamParallelReviewCapacityInput) -> None:
    if item.unresolved_escalation_count > item.active_packet_count:
        raise ValueError("unresolved_escalation_count must not exceed active_packet_count")


def _validate_row_consistency(row: ResearchTeamParallelReviewCapacityRow) -> None:
    _validate_input_counts(
        ResearchTeamParallelReviewCapacityInput(
            review_team_key=row.review_team_key,
            reviewer_pool_key=row.reviewer_pool_key,
            available_reviewer_count=row.available_reviewer_count,
            active_packet_count=row.active_packet_count,
            oldest_sla_age_seconds=row.oldest_sla_age_seconds,
            unresolved_escalation_count=row.unresolved_escalation_count,
            memory_writeback_delay_seconds=row.memory_writeback_delay_seconds,
            manual_escalation_urgency=row.manual_escalation_urgency,
            observed_at=row.observed_at,
        ),
    )
    if row.active_load_ratio != _ratio(
        row.active_packet_count,
        row.available_reviewer_count,
    ):
        raise ValueError("active_load_ratio must match counts")
    if row.reviewer_availability_ratio != _ratio(
        row.available_reviewer_count,
        row.available_reviewer_count + row.active_packet_count,
    ):
        raise ValueError("reviewer_availability_ratio must match counts")
    if row.escalation_load_ratio != _ratio_or_zero(
        row.unresolved_escalation_count,
        row.active_packet_count,
    ):
        raise ValueError("escalation_load_ratio must match counts")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("row status must match reason codes")


def _validate_report_status_fields(
    report: ResearchTeamParallelReviewCapacityReport,
) -> None:
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_QUEUE_ACTIONS[report.status]:
        raise ValueError("paper_queue_action must match status")


def _validate_report_consistency(
    report: ResearchTeamParallelReviewCapacityReport,
) -> None:
    if report.review_scope_count != _count(len(report.rows)):
        raise ValueError("review_scope_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_available_reviewer_count != _sum_decimal(
        report.rows,
        "available_reviewer_count",
    ):
        raise ValueError("total_available_reviewer_count must match rows")
    if report.total_active_packet_count != _sum_decimal(
        report.rows,
        "active_packet_count",
    ):
        raise ValueError("total_active_packet_count must match rows")
    if report.total_unresolved_escalation_count != _sum_decimal(
        report.rows,
        "unresolved_escalation_count",
    ):
        raise ValueError("total_unresolved_escalation_count must match rows")
    if report.max_oldest_sla_age_seconds != max(
        (row.oldest_sla_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_oldest_sla_age_seconds must match rows")
    if report.max_memory_writeback_delay_seconds != max(
        (row.memory_writeback_delay_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_memory_writeback_delay_seconds must match rows")
    if report.max_manual_escalation_urgency != max(
        (row.manual_escalation_urgency for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_manual_escalation_urgency must match rows")
    if report.max_capacity_pressure_ratio != max(
        (row.capacity_pressure_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_capacity_pressure_ratio must match rows")
    if report.average_capacity_pressure_ratio != _average_row_ratio(
        report.rows,
        "capacity_pressure_ratio",
    ):
        raise ValueError("average_capacity_pressure_ratio must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    _require_public_label("config_version", value)
    if value != DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_CAPACITY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must not exceed 128 characters")
    _reject_unsafe_public_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: Mapping[str, object]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"{flag} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _ratio(decimal_value, ONE)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    if decimal_value != quantized:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_threshold_order(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must not exceed {block_name}")


def _normalize_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_label("reason_code", reason_code)
        if reason_code not in REASON_CODE_RANK:
            raise ValueError(f"{field_name} must contain known reason codes")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=lambda reason_code: REASON_CODE_RANK[reason_code]))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(
            RATIO_QUANTUM,
            rounding=ROUND_HALF_EVEN,
        )


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _ratio(numerator, denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _ratio(value, ONE)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _report_payload_digest(report: ResearchTeamParallelReviewCapacityReport) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    return _digest_payload(payload_without_digest)


def _validate_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    if digest != _digest_payload(payload_without_digest):
        raise ValueError("derived_validation_digest must match report payload")


def _digest_payload(payload: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_public_numeric_values(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
            _reject_unsafe_public_key(f"{label}.{key}", key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public field")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{label} has unsafe public value")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public value")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)
