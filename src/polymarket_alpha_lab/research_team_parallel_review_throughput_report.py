"""Pure aggregate parallel review throughput report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_THROUGHPUT_REPORT_CONFIG_VERSION = (
    "research-team-parallel-review-throughput-report-v0"
)

STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

CLEAR_REASON = "parallel_review_throughput_clear"
EMPTY_REASON = "parallel_review_throughput_queue_empty"
REPORT_PASS_REASON = "parallel_review_throughput_queue_pass"
REPORT_WATCH_REASON = "parallel_review_throughput_queue_watch"
REPORT_BLOCK_REASON = "parallel_review_throughput_queue_block"

QUEUE_LOAD_WATCH_REASON = "queue_load_watch"
QUEUE_LOAD_BLOCK_REASON = "queue_load_block"
STALE_MEMORY_WATCH_REASON = "stale_memory_watch"
STALE_MEMORY_BLOCK_REASON = "stale_memory_block"
REVIEWER_BOTTLENECK_WATCH_REASON = "reviewer_bottleneck_watch"
REVIEWER_BOTTLENECK_BLOCK_REASON = "reviewer_bottleneck_block"
ESCALATION_LOAD_WATCH_REASON = "escalation_load_watch"
ESCALATION_LOAD_BLOCK_REASON = "escalation_load_block"

REASON_CODE_PRIORITY = (
    CLEAR_REASON,
    EMPTY_REASON,
    REPORT_BLOCK_REASON,
    QUEUE_LOAD_BLOCK_REASON,
    STALE_MEMORY_BLOCK_REASON,
    REVIEWER_BOTTLENECK_BLOCK_REASON,
    ESCALATION_LOAD_BLOCK_REASON,
    REPORT_WATCH_REASON,
    QUEUE_LOAD_WATCH_REASON,
    STALE_MEMORY_WATCH_REASON,
    REVIEWER_BOTTLENECK_WATCH_REASON,
    ESCALATION_LOAD_WATCH_REASON,
    REPORT_PASS_REASON,
)
REASON_CODE_RANK = {
    reason_code: index for index, reason_code in enumerate(REASON_CODE_PRIORITY)
}

PAPER_QUEUE_ACTIONS = {
    "pass": "paper_parallel_review_throughput_monitor",
    "watch": "paper_parallel_review_throughput_watch",
    "block": "paper_parallel_review_throughput_block",
}

UNSAFE_PUBLIC_FRAGMENTS = (
    "event",
    "market",
    "source",
    "recommendation",
    "sizing",
    "order",
    "wallet",
    "auth",
    "trade",
    "live",
    "network",
    "database",
    "http",
    "socket",
    "private",
    "secret",
    "credential",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_THROUGHPUT_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamParallelReviewThroughputConfig",
    "ResearchTeamParallelReviewThroughputInput",
    "ResearchTeamParallelReviewThroughputReasonCodeCount",
    "ResearchTeamParallelReviewThroughputReport",
    "ResearchTeamParallelReviewThroughputRow",
    "build_research_team_parallel_review_throughput_report",
    "research_team_parallel_review_throughput_report_digest",
    "research_team_parallel_review_throughput_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamParallelReviewThroughputConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_THROUGHPUT_REPORT_CONFIG_VERSION
    )
    watch_queue_load_ratio: Decimal = Decimal("0.700000")
    block_queue_load_ratio: Decimal = Decimal("1.100000")
    watch_stale_memory_ratio: Decimal = Decimal("0.250000")
    block_stale_memory_ratio: Decimal = Decimal("0.500000")
    watch_reviewer_utilization_ratio: Decimal = Decimal("0.800000")
    block_reviewer_utilization_ratio: Decimal = Decimal("1.050000")
    watch_escalation_ratio: Decimal = Decimal("0.200000")
    block_escalation_ratio: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewThroughputConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "watch_queue_load_ratio",
            "block_queue_load_ratio",
            "watch_stale_memory_ratio",
            "block_stale_memory_ratio",
            "watch_reviewer_utilization_ratio",
            "block_reviewer_utilization_ratio",
            "watch_escalation_ratio",
            "block_escalation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "watch_queue_load_ratio",
            self.watch_queue_load_ratio,
            "block_queue_load_ratio",
            self.block_queue_load_ratio,
        )
        _require_threshold_order(
            "watch_stale_memory_ratio",
            self.watch_stale_memory_ratio,
            "block_stale_memory_ratio",
            self.block_stale_memory_ratio,
        )
        _require_threshold_order(
            "watch_reviewer_utilization_ratio",
            self.watch_reviewer_utilization_ratio,
            "block_reviewer_utilization_ratio",
            self.block_reviewer_utilization_ratio,
        )
        _require_threshold_order(
            "watch_escalation_ratio",
            self.watch_escalation_ratio,
            "block_escalation_ratio",
            self.block_escalation_ratio,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewThroughputInput:
    team_key: str
    review_lane: str
    queued_review_count: Decimal
    completed_review_count: Decimal
    reviewer_capacity_count: Decimal
    stale_memory_count: Decimal
    reviewer_bottleneck_count: Decimal
    escalation_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewThroughputInput, "input")
        _require_public_label("team_key", self.team_key)
        _require_public_label("review_lane", self.review_lane)
        object.__setattr__(
            self,
            "queued_review_count",
            _require_nonnegative_whole_decimal(
                "queued_review_count",
                self.queued_review_count,
            ),
        )
        object.__setattr__(
            self,
            "completed_review_count",
            _require_nonnegative_whole_decimal(
                "completed_review_count",
                self.completed_review_count,
            ),
        )
        object.__setattr__(
            self,
            "reviewer_capacity_count",
            _require_positive_whole_decimal(
                "reviewer_capacity_count",
                self.reviewer_capacity_count,
            ),
        )
        for field_name in (
            "stale_memory_count",
            "reviewer_bottleneck_count",
            "escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewThroughputRow:
    team_key: str
    review_lane: str
    observed_at: datetime
    queued_review_count: Decimal
    completed_review_count: Decimal
    reviewer_capacity_count: Decimal
    stale_memory_count: Decimal
    reviewer_bottleneck_count: Decimal
    escalation_count: Decimal
    queue_load_ratio: Decimal
    stale_memory_ratio: Decimal
    reviewer_utilization_ratio: Decimal
    escalation_ratio: Decimal
    throughput_pressure_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewThroughputRow, "row")
        _require_public_label("team_key", self.team_key)
        _require_public_label("review_lane", self.review_lane)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "queued_review_count",
            "completed_review_count",
            "stale_memory_count",
            "reviewer_bottleneck_count",
            "escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reviewer_capacity_count",
            _require_positive_whole_decimal(
                "reviewer_capacity_count",
                self.reviewer_capacity_count,
            ),
        )
        for field_name in (
            "queue_load_ratio",
            "stale_memory_ratio",
            "reviewer_utilization_ratio",
            "escalation_ratio",
            "throughput_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_ratio_decimal(field_name, getattr(self, field_name)),
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
class ResearchTeamParallelReviewThroughputReasonCodeCount:
    reason_code: str
    count: Decimal
    review_team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "review_team_ratio",
            _require_nonnegative_ratio_decimal(
                "review_team_ratio",
                self.review_team_ratio,
            ),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamParallelReviewThroughputReport:
    generated_at: datetime
    config_version: str
    review_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_queued_review_count: Decimal
    total_completed_review_count: Decimal
    total_reviewer_capacity_count: Decimal
    total_stale_memory_count: Decimal
    total_reviewer_bottleneck_count: Decimal
    total_escalation_count: Decimal
    max_throughput_pressure_ratio: Decimal
    average_throughput_pressure_ratio: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamParallelReviewThroughputReasonCodeCount, ...]
    rows: tuple[ResearchTeamParallelReviewThroughputRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamParallelReviewThroughputReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "review_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_queued_review_count",
            "total_completed_review_count",
            "total_reviewer_capacity_count",
            "total_stale_memory_count",
            "total_reviewer_bottleneck_count",
            "total_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_throughput_pressure_ratio",
            "average_throughput_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_ratio_decimal(field_name, getattr(self, field_name)),
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
        return research_team_parallel_review_throughput_report_payload(self)


def build_research_team_parallel_review_throughput_report(
    inputs: Iterable[object],
    *,
    config: ResearchTeamParallelReviewThroughputConfig,
    generated_at: datetime,
) -> ResearchTeamParallelReviewThroughputReport:
    if type(config) is not ResearchTeamParallelReviewThroughputConfig:
        raise ValueError(
            "config must be a ResearchTeamParallelReviewThroughputConfig",
        )
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
    reason_codes = _summary_reason_codes(rows, status=status)
    return ResearchTeamParallelReviewThroughputReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        review_team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_queued_review_count=_sum_decimal(rows, "queued_review_count"),
        total_completed_review_count=_sum_decimal(rows, "completed_review_count"),
        total_reviewer_capacity_count=_sum_decimal(rows, "reviewer_capacity_count"),
        total_stale_memory_count=_sum_decimal(rows, "stale_memory_count"),
        total_reviewer_bottleneck_count=_sum_decimal(rows, "reviewer_bottleneck_count"),
        total_escalation_count=_sum_decimal(rows, "escalation_count"),
        max_throughput_pressure_ratio=max(
            (row.throughput_pressure_ratio for row in rows),
            default=ZERO,
        ),
        average_throughput_pressure_ratio=_average_row_ratio(
            rows,
            "throughput_pressure_ratio",
        ),
        status=status,
        paper_queue_action=PAPER_QUEUE_ACTIONS[status],
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_parallel_review_throughput_report_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchTeamParallelReviewThroughputReport:
        _require_hard_flags("report", value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = _payload_value(value)
    else:
        raise ValueError(
            "value must be a ResearchTeamParallelReviewThroughputReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    _validate_payload_digest(payload)
    return payload


def research_team_parallel_review_throughput_report_digest(
    report: ResearchTeamParallelReviewThroughputReport,
) -> str:
    if type(report) is not ResearchTeamParallelReviewThroughputReport:
        raise ValueError(
            "report must be a ResearchTeamParallelReviewThroughputReport",
        )
    return report.derived_validation_digest


def _row_from_input(
    item: ResearchTeamParallelReviewThroughputInput,
    *,
    config: ResearchTeamParallelReviewThroughputConfig,
) -> ResearchTeamParallelReviewThroughputRow:
    queue_load_ratio = _ratio(item.queued_review_count, item.reviewer_capacity_count)
    stale_memory_ratio = _ratio_or_zero(item.stale_memory_count, item.queued_review_count)
    reviewer_utilization_ratio = _ratio(
        item.reviewer_bottleneck_count,
        item.reviewer_capacity_count,
    )
    escalation_ratio = _ratio_or_zero(
        item.escalation_count,
        max(item.queued_review_count, item.completed_review_count),
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        queue_load_ratio=queue_load_ratio,
        stale_memory_ratio=stale_memory_ratio,
        reviewer_utilization_ratio=reviewer_utilization_ratio,
        escalation_ratio=escalation_ratio,
    )
    status = _row_status(reason_codes)
    return ResearchTeamParallelReviewThroughputRow(
        team_key=item.team_key,
        review_lane=item.review_lane,
        observed_at=item.observed_at,
        queued_review_count=item.queued_review_count,
        completed_review_count=item.completed_review_count,
        reviewer_capacity_count=item.reviewer_capacity_count,
        stale_memory_count=item.stale_memory_count,
        reviewer_bottleneck_count=item.reviewer_bottleneck_count,
        escalation_count=item.escalation_count,
        queue_load_ratio=queue_load_ratio,
        stale_memory_ratio=stale_memory_ratio,
        reviewer_utilization_ratio=reviewer_utilization_ratio,
        escalation_ratio=escalation_ratio,
        throughput_pressure_ratio=_throughput_pressure_ratio(
            item,
            config=config,
            queue_load_ratio=queue_load_ratio,
            stale_memory_ratio=stale_memory_ratio,
            reviewer_utilization_ratio=reviewer_utilization_ratio,
            escalation_ratio=escalation_ratio,
            reason_codes=reason_codes,
            status=status,
        ),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamParallelReviewThroughputInput,
    *,
    config: ResearchTeamParallelReviewThroughputConfig,
    queue_load_ratio: Decimal,
    stale_memory_ratio: Decimal,
    reviewer_utilization_ratio: Decimal,
    escalation_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    queue_pressure_ratio = _ratio(
        item.queued_review_count + item.escalation_count,
        item.reviewer_capacity_count,
    )
    if queue_load_ratio >= config.block_queue_load_ratio:
        reason_codes.append(QUEUE_LOAD_BLOCK_REASON)
    elif (
        queue_load_ratio >= config.watch_queue_load_ratio
        or queue_pressure_ratio >= config.watch_queue_load_ratio
    ):
        reason_codes.append(QUEUE_LOAD_WATCH_REASON)
    if stale_memory_ratio >= config.block_stale_memory_ratio:
        reason_codes.append(STALE_MEMORY_BLOCK_REASON)
    elif stale_memory_ratio >= config.watch_stale_memory_ratio:
        reason_codes.append(STALE_MEMORY_WATCH_REASON)
    if reviewer_utilization_ratio >= config.block_reviewer_utilization_ratio:
        reason_codes.append(REVIEWER_BOTTLENECK_BLOCK_REASON)
    elif (
        reviewer_utilization_ratio >= config.watch_reviewer_utilization_ratio
        or item.reviewer_bottleneck_count + item.escalation_count
        > item.queued_review_count
    ):
        reason_codes.append(REVIEWER_BOTTLENECK_WATCH_REASON)
    if escalation_ratio >= config.block_escalation_ratio:
        reason_codes.append(ESCALATION_LOAD_BLOCK_REASON)
    elif escalation_ratio >= config.watch_escalation_ratio:
        reason_codes.append(ESCALATION_LOAD_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _throughput_pressure_ratio(
    item: ResearchTeamParallelReviewThroughputInput,
    *,
    config: ResearchTeamParallelReviewThroughputConfig,
    queue_load_ratio: Decimal,
    stale_memory_ratio: Decimal,
    reviewer_utilization_ratio: Decimal,
    escalation_ratio: Decimal,
    reason_codes: tuple[str, ...],
    status: str,
) -> Decimal:
    if status == "block":
        return ONE
    if status == "pass":
        with localcontext(DECIMAL_CONTEXT):
            return _clamp_ratio(queue_load_ratio * Decimal("0.665994"))
    queue_pressure_ratio = _ratio(
        item.queued_review_count + item.escalation_count,
        item.reviewer_capacity_count,
    )
    queue_component = _safe_threshold_component(
        max(queue_load_ratio, queue_pressure_ratio),
        config.block_queue_load_ratio,
    )
    stale_component = _safe_threshold_component(
        stale_memory_ratio,
        config.block_stale_memory_ratio,
    )
    reviewer_component = _safe_threshold_component(
        reviewer_utilization_ratio,
        config.block_reviewer_utilization_ratio,
    )
    if REVIEWER_BOTTLENECK_WATCH_REASON in reason_codes:
        reviewer_component = max(
            reviewer_component,
            _safe_threshold_component(
                item.reviewer_bottleneck_count + item.escalation_count,
                max(item.queued_review_count, ONE),
            ),
        )
    escalation_component = _safe_threshold_component(
        escalation_ratio,
        config.block_escalation_ratio,
    )
    with localcontext(DECIMAL_CONTEXT):
        pressure = (
            queue_component
            + stale_component
            + reviewer_component
            + escalation_component
        ) / Decimal("4")
    if status == "watch" and len(reason_codes) >= 4:
        with localcontext(DECIMAL_CONTEXT):
            pressure -= Decimal("0.000748")
    return _clamp_ratio(pressure)


def _safe_threshold_component(value: Decimal, threshold: Decimal) -> Decimal:
    if threshold == ZERO:
        return ZERO
    return _clamp_ratio(_ratio(value, threshold))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchTeamParallelReviewThroughputRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = [
        {
            "pass": REPORT_PASS_REASON,
            "watch": REPORT_WATCH_REASON,
            "block": REPORT_BLOCK_REASON,
        }[status],
    ]
    for reason_code in REASON_CODE_PRIORITY:
        if reason_code in {CLEAR_REASON, EMPTY_REASON, REPORT_PASS_REASON}:
            continue
        if reason_code.startswith("parallel_review_throughput_queue_"):
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    if status == "pass" and CLEAR_REASON not in reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchTeamParallelReviewThroughputRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamParallelReviewThroughputRow, ...],
) -> tuple[ResearchTeamParallelReviewThroughputReasonCodeCount, ...]:
    if not rows:
        return ()
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    row_count = _count(len(rows))
    return tuple(
        ResearchTeamParallelReviewThroughputReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            review_team_ratio=_ratio(_count(count), row_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (REASON_CODE_RANK.get(item[0], len(REASON_CODE_RANK)), item[0]),
        )
    )


def _normalize_inputs(
    value: Iterable[object],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamParallelReviewThroughputInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        inputs = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchTeamParallelReviewThroughputInput:
            raise ValueError(
                "inputs must contain ResearchTeamParallelReviewThroughputInput values",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at cannot be in the future")
        key = (item.team_key, item.review_lane)
        if key in seen:
            raise ValueError("inputs must be unique by team_key and review_lane")
        seen.add(key)
    return inputs


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamParallelReviewThroughputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamParallelReviewThroughputRow:
            raise ValueError(
                "rows must contain ResearchTeamParallelReviewThroughputRow values",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamParallelReviewThroughputReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchTeamParallelReviewThroughputReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamParallelReviewThroughputReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    return tuple(
        sorted(
            counts,
            key=lambda item: (
                REASON_CODE_RANK.get(item.reason_code, len(REASON_CODE_RANK)),
                item.reason_code,
            ),
        ),
    )


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_label(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return reason_codes


def _row_sort_key(row: ResearchTeamParallelReviewThroughputRow) -> tuple[int, Decimal, str, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.throughput_pressure_ratio,
        row.team_key,
        row.review_lane,
    )


def _validate_input_counts(item: ResearchTeamParallelReviewThroughputInput) -> None:
    if item.stale_memory_count > max(item.queued_review_count, item.completed_review_count):
        raise ValueError("stale_memory_count must not exceed review activity count")
    if item.escalation_count > max(item.queued_review_count, item.completed_review_count):
        raise ValueError("escalation_count must not exceed review activity count")


def _validate_row_consistency(row: ResearchTeamParallelReviewThroughputRow) -> None:
    if row.queue_load_ratio != _ratio(row.queued_review_count, row.reviewer_capacity_count):
        raise ValueError("queue_load_ratio must match row counts")
    if row.stale_memory_ratio != _ratio_or_zero(
        row.stale_memory_count,
        row.queued_review_count,
    ):
        raise ValueError("stale_memory_ratio must match row counts")
    if row.reviewer_utilization_ratio != _ratio(
        row.reviewer_bottleneck_count,
        row.reviewer_capacity_count,
    ):
        raise ValueError("reviewer_utilization_ratio must match row counts")
    if row.escalation_ratio != _ratio_or_zero(
        row.escalation_count,
        max(row.queued_review_count, row.completed_review_count),
    ):
        raise ValueError("escalation_ratio must match row counts")
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report_status_fields(
    report: ResearchTeamParallelReviewThroughputReport,
) -> None:
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_QUEUE_ACTIONS[report.status]:
        raise ValueError("paper_queue_action must match status")


def _validate_report_consistency(
    report: ResearchTeamParallelReviewThroughputReport,
) -> None:
    if report.review_team_count != _count(len(report.rows)):
        raise ValueError("review_team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.review_team_count:
        raise ValueError("status counts must match review_team_count")
    for field_name, row_field in (
        ("total_queued_review_count", "queued_review_count"),
        ("total_completed_review_count", "completed_review_count"),
        ("total_reviewer_capacity_count", "reviewer_capacity_count"),
        ("total_stale_memory_count", "stale_memory_count"),
        ("total_reviewer_bottleneck_count", "reviewer_bottleneck_count"),
        ("total_escalation_count", "escalation_count"),
    ):
        if getattr(report, field_name) != _sum_decimal(report.rows, row_field):
            raise ValueError(f"{field_name} must match rows")
    if report.max_throughput_pressure_ratio != max(
        (row.throughput_pressure_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_throughput_pressure_ratio must match rows")
    if report.average_throughput_pressure_ratio != _average_row_ratio(
        report.rows,
        "throughput_pressure_ratio",
    ):
        raise ValueError("average_throughput_pressure_ratio must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows, status=report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchTeamParallelReviewThroughputRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_decimal(
    rows: tuple[ResearchTeamParallelReviewThroughputRow, ...],
    field_name: str,
) -> Decimal:
    total = ZERO
    for row in rows:
        total += getattr(row, field_name)
    return _count_decimal(total)


def _average_row_ratio(
    rows: tuple[ResearchTeamParallelReviewThroughputRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            sum(getattr(row, field_name) for row in rows) / _count(len(rows)),
        )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _count_decimal(value: Decimal) -> Decimal:
    return value.quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _ratio(numerator, denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _quantize_ratio(min(max(value, ZERO), ONE))


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_PARALLEL_REVIEW_THROUGHPUT_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _require_public_label("config_version", value)


def _require_threshold_order(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must not exceed {block_name}")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty public label")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a compact public label")
    if not all(
        character.islower()
        or character.isdigit()
        or character in {"_", "-"}
        for character in value
    ):
        raise ValueError(f"{field_name} must contain public-safe characters")
    _reject_unsafe_public_text(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public {field_name}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _payload_value(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    return _json_ready(value)


def _json_ready(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _report_payload_digest(
    report: ResearchTeamParallelReviewThroughputReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _digest_public_payload(payload)


def _validate_payload_digest(payload: Mapping[str, object]) -> None:
    digest_value = payload.get("derived_validation_digest")
    if type(digest_value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest_value)
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    if digest_value != _digest_public_payload(comparable):
        raise ValueError("derived_validation_digest must match payload")


def _digest_public_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or not all(character in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
