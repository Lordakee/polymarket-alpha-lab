"""Pure review capacity forecast report reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "PUBLIC_STATUSES",
    "ResearchTeamReviewCapacityForecastConfig",
    "ResearchTeamReviewCapacityForecastInput",
    "ResearchTeamReviewCapacityForecastReasonCodeCount",
    "ResearchTeamReviewCapacityForecastReport",
    "ResearchTeamReviewCapacityForecastRow",
    "build_research_team_review_capacity_forecast_report",
    "research_team_review_capacity_forecast_report_payload",
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

DEFAULT_CONFIG_VERSION = "research_team_review_capacity_forecast_report.v1"

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

CLEAR_REASON = "review_capacity_clear"
NO_INPUTS_REASON = "no_review_queues"
CAPACITY_BLOCK_PRESENT_REASON = "capacity_block_present"
CAPACITY_WATCH_PRESENT_REASON = "capacity_watch_present"
CAPACITY_OVER_REASON = "capacity_over_committed"
CAPACITY_NEAR_REASON = "capacity_near_limit"
SLA_BLOCK_REASON = "sla_pressure_block"
SLA_WATCH_REASON = "sla_pressure_watch"
EVENT_BLOCK_REASON = "event_timing_block"
EVENT_WATCH_REASON = "event_timing_watch"
EXPERTISE_BLOCK_REASON = "expertise_fit_block"
EXPERTISE_WATCH_REASON = "expertise_fit_watch"
OVERDUE_REASON = "overdue_tasks_present"
DUE_SOON_REASON = "due_soon_tasks_present"

REASON_CODE_SEQUENCE = (
    CAPACITY_BLOCK_PRESENT_REASON,
    CAPACITY_WATCH_PRESENT_REASON,
    CAPACITY_OVER_REASON,
    CAPACITY_NEAR_REASON,
    SLA_BLOCK_REASON,
    SLA_WATCH_REASON,
    EVENT_BLOCK_REASON,
    EVENT_WATCH_REASON,
    EXPERTISE_BLOCK_REASON,
    EXPERTISE_WATCH_REASON,
    OVERDUE_REASON,
    DUE_SOON_REASON,
    CLEAR_REASON,
    NO_INPUTS_REASON,
)

SENSITIVE_MARKERS = (
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_key",
    "access_token",
    "bearer ",
    "://",
    "@",
)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_capacity_utilization: Decimal = Decimal("0.850000")
    block_capacity_utilization: Decimal = Decimal("1.000000")
    watch_sla_pressure_score: Decimal = Decimal("0.600000")
    block_sla_pressure_score: Decimal = Decimal("0.850000")
    event_watch_window_hours: Decimal = Decimal("24.000000")
    event_block_window_hours: Decimal = Decimal("6.000000")
    watch_event_timing_pressure: Decimal = Decimal("0.500000")
    block_event_timing_pressure: Decimal = Decimal("0.800000")
    watch_expertise_fit_score: Decimal = Decimal("0.700000")
    block_expertise_fit_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCapacityForecastConfig:
            raise TypeError(
                "ResearchTeamReviewCapacityForecastConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewCapacityForecastConfig:
            raise ValueError(
                "config must be exactly ResearchTeamReviewCapacityForecastConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_capacity_utilization",
            "block_capacity_utilization",
            "event_watch_window_hours",
            "event_block_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_sla_pressure_score",
            "block_sla_pressure_score",
            "watch_event_timing_pressure",
            "block_event_timing_pressure",
            "watch_expertise_fit_score",
            "block_expertise_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_capacity_utilization < self.watch_capacity_utilization:
            raise ValueError("block_capacity_utilization must meet or exceed watch")
        if self.block_sla_pressure_score < self.watch_sla_pressure_score:
            raise ValueError("block_sla_pressure_score must meet or exceed watch")
        if self.event_block_window_hours > self.event_watch_window_hours:
            raise ValueError("event_block_window_hours must not exceed watch window")
        if self.block_event_timing_pressure < self.watch_event_timing_pressure:
            raise ValueError("block_event_timing_pressure must meet or exceed watch")
        if self.block_expertise_fit_score > self.watch_expertise_fit_score:
            raise ValueError("block_expertise_fit_score must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastInput:
    team_id: str
    queue_id: str
    market_group: str
    pending_task_count: Decimal
    available_review_slot_count: Decimal
    due_soon_task_count: Decimal
    overdue_task_count: Decimal
    sla_pressure_score: Decimal
    hours_until_nearest_event: Decimal
    event_importance_score: Decimal
    expertise_fit_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCapacityForecastInput:
            raise TypeError(
                "ResearchTeamReviewCapacityForecastInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewCapacityForecastInput:
            raise ValueError(
                "input must be exactly ResearchTeamReviewCapacityForecastInput",
            )
        for field_name in ("team_id", "queue_id", "market_group"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "pending_task_count",
            "due_soon_task_count",
            "overdue_task_count",
            "hours_until_nearest_event",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_review_slot_count",
            _require_positive_decimal(
                "available_review_slot_count",
                self.available_review_slot_count,
            ),
        )
        for field_name in (
            "sla_pressure_score",
            "event_importance_score",
            "expertise_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastRow:
    team_id: str
    queue_id: str
    market_group: str
    pending_task_count: Decimal
    available_review_slot_count: Decimal
    due_soon_task_count: Decimal
    overdue_task_count: Decimal
    sla_pressure_score: Decimal
    hours_until_nearest_event: Decimal
    event_importance_score: Decimal
    expertise_fit_score: Decimal
    capacity_utilization: Decimal
    event_timing_pressure: Decimal
    expertise_gap_score: Decimal
    capacity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCapacityForecastRow:
            raise TypeError(
                "ResearchTeamReviewCapacityForecastRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewCapacityForecastRow:
            raise ValueError("row must be exactly ResearchTeamReviewCapacityForecastRow")
        for field_name in ("team_id", "queue_id", "market_group"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "pending_task_count",
            "due_soon_task_count",
            "overdue_task_count",
            "hours_until_nearest_event",
            "capacity_utilization",
            "event_timing_pressure",
            "expertise_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_review_slot_count",
            _require_positive_decimal(
                "available_review_slot_count",
                self.available_review_slot_count,
            ),
        )
        for field_name in (
            "sla_pressure_score",
            "event_importance_score",
            "expertise_fit_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("capacity_status", self.capacity_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastReasonCodeCount:
    reason_code: str
    count: Decimal
    queue_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCapacityForecastReasonCodeCount:
            raise TypeError(
                "ResearchTeamReviewCapacityForecastReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewCapacityForecastReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchTeamReviewCapacityForecastReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "queue_ratio",
            _require_ratio_decimal("queue_ratio", self.queue_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastReport:
    generated_at: datetime
    config_version: str
    capacity_status: str
    team_queue_count: Decimal
    pass_queue_count: Decimal
    watch_queue_count: Decimal
    block_queue_count: Decimal
    bottleneck_queue_count: Decimal
    total_pending_task_count: Decimal
    total_available_review_slot_count: Decimal
    weighted_capacity_utilization: Decimal
    max_sla_pressure_score: Decimal
    min_expertise_fit_score: Decimal
    max_event_timing_pressure: Decimal
    rows: tuple[ResearchTeamReviewCapacityForecastRow, ...]
    reason_code_counts: tuple[ResearchTeamReviewCapacityForecastReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCapacityForecastReport:
            raise TypeError(
                "ResearchTeamReviewCapacityForecastReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamReviewCapacityForecastReport:
            raise ValueError(
                "report must be exactly ResearchTeamReviewCapacityForecastReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("capacity_status", self.capacity_status)
        for field_name in (
            "team_queue_count",
            "pass_queue_count",
            "watch_queue_count",
            "block_queue_count",
            "bottleneck_queue_count",
            "total_pending_task_count",
            "total_available_review_slot_count",
            "weighted_capacity_utilization",
            "max_sla_pressure_score",
            "min_expertise_fit_score",
            "max_event_timing_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchTeamReviewCapacityForecastRow:
                raise ValueError(
                    "rows must contain ResearchTeamReviewCapacityForecastRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for item in self.reason_code_counts:
            if type(item) is not ResearchTeamReviewCapacityForecastReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchTeamReviewCapacityForecastReasonCodeCount",
                )
            _require_hard_flags("reason count", item)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if type(self.payload_digest) is not str:
            raise ValueError("payload_digest must be a public digest string")
        current_digest = self.payload_digest
        object.__setattr__(self, "payload_digest", "")
        derived_digest = _report_digest(self)
        if current_digest and current_digest != derived_digest:
            raise ValueError("payload_digest does not match report payload")
        object.__setattr__(self, "payload_digest", derived_digest)
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_review_capacity_forecast_report_payload(self)


def build_research_team_review_capacity_forecast_report(
    input_rows: list[ResearchTeamReviewCapacityForecastInput]
    | tuple[ResearchTeamReviewCapacityForecastInput, ...],
    *,
    generated_at: datetime,
    config: ResearchTeamReviewCapacityForecastConfig | None = None,
) -> ResearchTeamReviewCapacityForecastReport:
    cfg = config or ResearchTeamReviewCapacityForecastConfig()
    if type(cfg) is not ResearchTeamReviewCapacityForecastConfig:
        raise ValueError("config must be a ResearchTeamReviewCapacityForecastConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = tuple(_row_from_input(row, cfg) for row in _normalize_input_rows(input_rows))
    ranked_rows = tuple(sorted(rows, key=_row_rank_key))
    team_queue_count = _count(len(ranked_rows))
    pass_queue_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status == STATUS_PASS),
    )
    watch_queue_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status == STATUS_WATCH),
    )
    block_queue_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status == STATUS_BLOCK),
    )
    bottleneck_queue_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status != STATUS_PASS),
    )
    total_pending_task_count = _sum_decimal(row.pending_task_count for row in ranked_rows)
    total_available_review_slot_count = _sum_decimal(
        row.available_review_slot_count for row in ranked_rows
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = _report_reason_codes(ranked_rows)
    return ResearchTeamReviewCapacityForecastReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        capacity_status=_report_status(
            has_inputs=bool(ranked_rows),
            block_queue_count=block_queue_count,
            watch_queue_count=watch_queue_count,
        ),
        team_queue_count=team_queue_count,
        pass_queue_count=pass_queue_count,
        watch_queue_count=watch_queue_count,
        block_queue_count=block_queue_count,
        bottleneck_queue_count=bottleneck_queue_count,
        total_pending_task_count=total_pending_task_count,
        total_available_review_slot_count=total_available_review_slot_count,
        weighted_capacity_utilization=_ratio(
            total_pending_task_count,
            total_available_review_slot_count,
        ),
        max_sla_pressure_score=max(
            (row.sla_pressure_score for row in ranked_rows),
            default=ZERO,
        ),
        min_expertise_fit_score=min(
            (row.expertise_fit_score for row in ranked_rows),
            default=ZERO,
        ),
        max_event_timing_pressure=max(
            (row.event_timing_pressure for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_review_capacity_forecast_report_payload(
    report: ResearchTeamReviewCapacityForecastReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamReviewCapacityForecastReport:
        raise ValueError("report must be a ResearchTeamReviewCapacityForecastReport")
    _require_hard_flags("report", report)
    payload = _report_payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    _reject_bad_payload(payload)
    return payload


def _row_from_input(
    row: ResearchTeamReviewCapacityForecastInput,
    config: ResearchTeamReviewCapacityForecastConfig,
) -> ResearchTeamReviewCapacityForecastRow:
    if type(row) is not ResearchTeamReviewCapacityForecastInput:
        raise ValueError("input_rows must contain ResearchTeamReviewCapacityForecastInput")
    _require_hard_flags("input", row)
    capacity_utilization = _ratio(
        row.pending_task_count,
        row.available_review_slot_count,
    )
    event_timing_pressure = _event_timing_pressure(row, config)
    expertise_gap_score = _quantize_decimal(
        "expertise_gap_score",
        ONE - row.expertise_fit_score,
    )
    capacity_status = _row_status(
        row,
        config,
        capacity_utilization=capacity_utilization,
        event_timing_pressure=event_timing_pressure,
    )
    return ResearchTeamReviewCapacityForecastRow(
        team_id=row.team_id,
        queue_id=row.queue_id,
        market_group=row.market_group,
        pending_task_count=row.pending_task_count,
        available_review_slot_count=row.available_review_slot_count,
        due_soon_task_count=row.due_soon_task_count,
        overdue_task_count=row.overdue_task_count,
        sla_pressure_score=row.sla_pressure_score,
        hours_until_nearest_event=row.hours_until_nearest_event,
        event_importance_score=row.event_importance_score,
        expertise_fit_score=row.expertise_fit_score,
        capacity_utilization=capacity_utilization,
        event_timing_pressure=event_timing_pressure,
        expertise_gap_score=expertise_gap_score,
        capacity_status=capacity_status,
        reason_codes=_row_reason_codes(
            row,
            config,
            capacity_utilization=capacity_utilization,
            event_timing_pressure=event_timing_pressure,
            capacity_status=capacity_status,
        ),
    )


def _event_timing_pressure(
    row: ResearchTeamReviewCapacityForecastInput,
    config: ResearchTeamReviewCapacityForecastConfig,
) -> Decimal:
    if row.hours_until_nearest_event <= config.event_watch_window_hours:
        return row.event_importance_score
    return ZERO


def _row_status(
    row: ResearchTeamReviewCapacityForecastInput,
    config: ResearchTeamReviewCapacityForecastConfig,
    *,
    capacity_utilization: Decimal,
    event_timing_pressure: Decimal,
) -> str:
    if (
        capacity_utilization >= config.block_capacity_utilization
        or row.sla_pressure_score >= config.block_sla_pressure_score
        or event_timing_pressure >= config.block_event_timing_pressure
        or row.expertise_fit_score <= config.block_expertise_fit_score
        or row.overdue_task_count > ZERO
    ):
        return STATUS_BLOCK
    if (
        capacity_utilization >= config.watch_capacity_utilization
        or row.sla_pressure_score >= config.watch_sla_pressure_score
        or event_timing_pressure >= config.watch_event_timing_pressure
        or row.expertise_fit_score <= config.watch_expertise_fit_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    row: ResearchTeamReviewCapacityForecastInput,
    config: ResearchTeamReviewCapacityForecastConfig,
    *,
    capacity_utilization: Decimal,
    event_timing_pressure: Decimal,
    capacity_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if capacity_status == STATUS_BLOCK:
        if capacity_utilization >= config.block_capacity_utilization:
            reason_codes.append(CAPACITY_OVER_REASON)
        if row.sla_pressure_score >= config.block_sla_pressure_score:
            reason_codes.append(SLA_BLOCK_REASON)
        if event_timing_pressure >= config.block_event_timing_pressure:
            reason_codes.append(EVENT_BLOCK_REASON)
        if row.expertise_fit_score <= config.block_expertise_fit_score:
            reason_codes.append(EXPERTISE_BLOCK_REASON)
        if row.overdue_task_count > ZERO:
            reason_codes.append(OVERDUE_REASON)
    elif capacity_status == STATUS_WATCH:
        if capacity_utilization >= config.watch_capacity_utilization:
            reason_codes.append(CAPACITY_NEAR_REASON)
        if row.sla_pressure_score >= config.watch_sla_pressure_score:
            reason_codes.append(SLA_WATCH_REASON)
        if event_timing_pressure >= config.watch_event_timing_pressure:
            reason_codes.append(EVENT_WATCH_REASON)
        if row.expertise_fit_score <= config.watch_expertise_fit_score:
            reason_codes.append(EXPERTISE_WATCH_REASON)
        if row.due_soon_task_count > ZERO:
            reason_codes.append(DUE_SOON_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _row_rank_key(row: ResearchTeamReviewCapacityForecastRow) -> tuple[object, ...]:
    severity = {
        STATUS_BLOCK: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }[row.capacity_status]
    return (
        severity,
        -row.capacity_utilization,
        -row.sla_pressure_score,
        -row.event_timing_pressure,
        -row.expertise_gap_score,
        row.team_id,
        row.queue_id,
    )


def _report_status(
    *,
    has_inputs: bool,
    block_queue_count: Decimal,
    watch_queue_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_WATCH
    if block_queue_count > ZERO:
        return STATUS_BLOCK
    if watch_queue_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamReviewCapacityForecastRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    if any(row.capacity_status == STATUS_BLOCK for row in rows):
        reason_codes = [CAPACITY_BLOCK_PRESENT_REASON]
    elif any(row.capacity_status == STATUS_WATCH for row in rows):
        reason_codes = [CAPACITY_WATCH_PRESENT_REASON]
    else:
        return (CLEAR_REASON,)
    seen = set(reason_codes)
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code == CLEAR_REASON or reason_code in seen:
                continue
            seen.add(reason_code)
            reason_codes.append(reason_code)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _reason_code_counts(
    rows: tuple[ResearchTeamReviewCapacityForecastRow, ...],
) -> tuple[ResearchTeamReviewCapacityForecastReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamReviewCapacityForecastReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                queue_ratio=ONE,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    total = _count(len(rows))
    return tuple(
        ResearchTeamReviewCapacityForecastReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            queue_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_input_rows(
    input_rows: list[ResearchTeamReviewCapacityForecastInput]
    | tuple[ResearchTeamReviewCapacityForecastInput, ...],
) -> tuple[ResearchTeamReviewCapacityForecastInput, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    normalized: list[ResearchTeamReviewCapacityForecastInput] = []
    for row in input_rows:
        if type(row) is not ResearchTeamReviewCapacityForecastInput:
            raise ValueError(
                "input_rows must contain ResearchTeamReviewCapacityForecastInput",
            )
        _require_hard_flags("input", row)
        normalized.append(row)
    return tuple(normalized)


def _validate_report(report: ResearchTeamReviewCapacityForecastReport) -> None:
    row_count = _count(len(report.rows))
    if report.team_queue_count != row_count:
        raise ValueError("team_queue_count must match rows")
    if report.pass_queue_count + report.watch_queue_count + report.block_queue_count != row_count:
        raise ValueError("status counts must match rows")
    if report.bottleneck_queue_count != report.watch_queue_count + report.block_queue_count:
        raise ValueError("bottleneck_queue_count must match watch and block queues")
    if report.capacity_status != _report_status(
        has_inputs=bool(report.rows),
        block_queue_count=report.block_queue_count,
        watch_queue_count=report.watch_queue_count,
    ):
        raise ValueError("capacity_status must match row statuses")


def _report_payload_without_digest(
    report: ResearchTeamReviewCapacityForecastReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "capacity_status": report.capacity_status,
        "team_queue_count": _decimal_payload(report.team_queue_count),
        "pass_queue_count": _decimal_payload(report.pass_queue_count),
        "watch_queue_count": _decimal_payload(report.watch_queue_count),
        "block_queue_count": _decimal_payload(report.block_queue_count),
        "bottleneck_queue_count": _decimal_payload(report.bottleneck_queue_count),
        "total_pending_task_count": _decimal_payload(report.total_pending_task_count),
        "total_available_review_slot_count": _decimal_payload(
            report.total_available_review_slot_count,
        ),
        "weighted_capacity_utilization": _decimal_payload(
            report.weighted_capacity_utilization,
        ),
        "max_sla_pressure_score": _decimal_payload(report.max_sla_pressure_score),
        "min_expertise_fit_score": _decimal_payload(report.min_expertise_fit_score),
        "max_event_timing_pressure": _decimal_payload(report.max_event_timing_pressure),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchTeamReviewCapacityForecastRow) -> dict[str, Any]:
    return {
        "team_id": row.team_id,
        "queue_id": row.queue_id,
        "market_group": row.market_group,
        "pending_task_count": _decimal_payload(row.pending_task_count),
        "available_review_slot_count": _decimal_payload(
            row.available_review_slot_count,
        ),
        "due_soon_task_count": _decimal_payload(row.due_soon_task_count),
        "overdue_task_count": _decimal_payload(row.overdue_task_count),
        "sla_pressure_score": _decimal_payload(row.sla_pressure_score),
        "hours_until_nearest_event": _decimal_payload(row.hours_until_nearest_event),
        "event_importance_score": _decimal_payload(row.event_importance_score),
        "expertise_fit_score": _decimal_payload(row.expertise_fit_score),
        "capacity_utilization": _decimal_payload(row.capacity_utilization),
        "event_timing_pressure": _decimal_payload(row.event_timing_pressure),
        "expertise_gap_score": _decimal_payload(row.expertise_gap_score),
        "capacity_status": row.capacity_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: ResearchTeamReviewCapacityForecastReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "queue_ratio": _decimal_payload(item.queue_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_digest(report: ResearchTeamReviewCapacityForecastReport) -> str:
    encoded = json.dumps(
        _report_payload_without_digest(report),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal("sum", total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value))


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(DECIMAL_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a public nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a public nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a public nonblank string")
    _reject_bad_text(value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")


def _reject_bad_payload(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    if isinstance(value, str):
        _reject_bad_text(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_bad_text(str(key))
            _reject_bad_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_bad_payload(item)


def _reject_bad_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")
