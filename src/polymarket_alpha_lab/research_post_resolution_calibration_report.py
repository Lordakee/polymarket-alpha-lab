from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_POST_RESOLUTION_CALIBRATION_REPORT_CONFIG_VERSION = (
    "research-post-resolution-calibration-report-v1"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_NO_INPUTS = "research_post_resolution_calibration_no_inputs"
REASON_PASS = "research_post_resolution_calibration_pass"
REASON_WATCH_ABSOLUTE_BIAS = (
    "research_post_resolution_calibration_absolute_bias_watch"
)
REASON_BLOCK_ABSOLUTE_BIAS = (
    "research_post_resolution_calibration_absolute_bias_block"
)
REASON_WATCH_MEAN_BIAS = "research_post_resolution_calibration_mean_bias_watch"
REASON_BLOCK_MEAN_BIAS = "research_post_resolution_calibration_mean_bias_block"
REASON_WATCH_BRIER = "research_post_resolution_calibration_brier_watch"
REASON_BLOCK_BRIER = "research_post_resolution_calibration_brier_block"
REASON_THIN_SAMPLE = "research_post_resolution_calibration_thin_sample"
REASON_MEMORY_PLAN = "research_post_resolution_calibration_local_memory_plan"

REASON_CODE_SEQUENCE = (
    REASON_BLOCK_ABSOLUTE_BIAS,
    REASON_BLOCK_MEAN_BIAS,
    REASON_BLOCK_BRIER,
    REASON_WATCH_ABSOLUTE_BIAS,
    REASON_WATCH_MEAN_BIAS,
    REASON_WATCH_BRIER,
    REASON_THIN_SAMPLE,
    REASON_MEMORY_PLAN,
    REASON_PASS,
    REASON_NO_INPUTS,
)

NEXT_STEPS = {
    STATUS_PASS: (
        "pass_report_only_post_resolution_calibration_review_without_action"
    ),
    STATUS_WATCH: (
        "watch_report_only_post_resolution_calibration_review_adjust_research_notes"
    ),
    STATUS_BLOCK: (
        "block_report_only_post_resolution_calibration_review_until_bias_reviewed"
    ),
}

IMPROVEMENT_ACTIONS = {
    REASON_BLOCK_ABSOLUTE_BIAS: (
        "review_probability_bin_with_large_absolute_bias_using_public_resolution_notes"
    ),
    REASON_BLOCK_MEAN_BIAS: (
        "review_directional_probability_bias_before_updating_future_research_checklists"
    ),
    REASON_BLOCK_BRIER: (
        "compare_forecast_confidence_to_realized_outcomes_before_reusing_template"
    ),
    REASON_WATCH_ABSOLUTE_BIAS: (
        "add_calibration_note_for_probability_bin_before_next_research_cycle"
    ),
    REASON_WATCH_MEAN_BIAS: (
        "add_directional_bias_note_to_future_research_review_checklist"
    ),
    REASON_WATCH_BRIER: (
        "add_confidence_quality_note_for_future_forecast_reviews"
    ),
    REASON_THIN_SAMPLE: (
        "collect_more_resolved_public_events_before_drawing_stronger_lessons"
    ),
    REASON_MEMORY_PLAN: (
        "plan_local_supabase_postgres_memory_write_after_operator_review_only"
    ),
    REASON_PASS: (
        "keep_current_research_calibration_notes_and_continue_passive_review"
    ),
    REASON_NO_INPUTS: (
        "collect_resolved_public_events_before_calibration_review"
    ),
}

SAFE_MEMORY_TARGETS = (
    "local_supabase_postgres_research_memory",
    "local_postgres_research_memory",
)

UNSAFE_FRAGMENTS = (
    "api" + "_" + "key",
    "au" + "th",
    "b" + "et",
    "bro" + "ker",
    "can" + "cel",
    "cli" + "ent",
    "credential",
    "du" + "rable",
    "ht" + "tp",
    "invest",
    "market" + "_" + "slug",
    "mutation",
    "net" + "work",
    "or" + "der",
    "password",
    "pos" + "ition",
    "private",
    "ques" + "tion",
    "sec" + "ret",
    "sign" + "ing",
    "sta" + "ke",
    "tra" + "de",
    "wal" + "let",
)

_QUANT = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchPostResolutionCalibrationReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_POST_RESOLUTION_CALIBRATION_REPORT_CONFIG_VERSION
    )
    min_resolved_event_count: Decimal = Decimal("3")
    absolute_bias_watch_threshold: Decimal = Decimal("0.080000")
    absolute_bias_block_threshold: Decimal = Decimal("0.500000")
    mean_bias_watch_threshold: Decimal = Decimal("0.050000")
    mean_bias_block_threshold: Decimal = Decimal("0.100000")
    brier_watch_threshold: Decimal = Decimal("0.220000")
    brier_block_threshold: Decimal = Decimal("0.300000")
    local_memory_write_planning_enabled: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPostResolutionCalibrationReportConfig:
            raise TypeError(
                "ResearchPostResolutionCalibrationReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPostResolutionCalibrationReportConfig:
            raise ValueError(
                "config must be exactly ResearchPostResolutionCalibrationReportConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_resolved_event_count",
            _require_nonnegative_count_decimal(
                "min_resolved_event_count",
                self.min_resolved_event_count,
            ),
        )
        for field_name in (
            "absolute_bias_watch_threshold",
            "absolute_bias_block_threshold",
            "mean_bias_watch_threshold",
            "mean_bias_block_threshold",
            "brier_watch_threshold",
            "brier_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.absolute_bias_watch_threshold > self.absolute_bias_block_threshold:
            raise ValueError(
                "absolute_bias_block_threshold must be at least absolute_bias_watch_threshold",
            )
        if self.mean_bias_watch_threshold > self.mean_bias_block_threshold:
            raise ValueError(
                "mean_bias_block_threshold must be at least mean_bias_watch_threshold",
            )
        if self.brier_watch_threshold > self.brier_block_threshold:
            raise ValueError(
                "brier_block_threshold must be at least brier_watch_threshold",
            )
        if type(self.local_memory_write_planning_enabled) is not bool:
            raise ValueError("local_memory_write_planning_enabled must be a bool")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPostResolutionCalibrationResolvedEvent:
    research_key: str
    condition_id: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    resolved_at: datetime
    public_resolution_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPostResolutionCalibrationResolvedEvent:
            raise TypeError(
                "ResearchPostResolutionCalibrationResolvedEvent does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPostResolutionCalibrationResolvedEvent:
            raise ValueError(
                "event must be exactly ResearchPostResolutionCalibrationResolvedEvent",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _require_probability_decimal(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "resolved_probability",
            _require_binary_probability_decimal(
                "resolved_probability",
                self.resolved_probability,
            ),
        )
        object.__setattr__(
            self,
            "resolved_at",
            _as_utc("resolved_at", self.resolved_at),
        )
        _require_reference("public_resolution_reference", self.public_resolution_reference)
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class ResearchPostResolutionCalibrationRow:
    research_key: str
    condition_id: str
    resolved_at: datetime
    forecast_probability: Decimal
    resolved_probability: Decimal
    signed_bias: Decimal
    absolute_bias: Decimal
    squared_error: Decimal
    status: str
    redacted_resolution_reference: str
    improvement_items: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: ResearchPostResolutionCalibrationReportConfig | None = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPostResolutionCalibrationRow:
            raise TypeError(
                "ResearchPostResolutionCalibrationRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPostResolutionCalibrationRow:
            raise ValueError("row must be exactly ResearchPostResolutionCalibrationRow")
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        object.__setattr__(
            self,
            "resolved_at",
            _as_utc("resolved_at", self.resolved_at),
        )
        for field_name in ("forecast_probability", "resolved_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "signed_bias",
            _require_signed_probability_delta("signed_bias", self.signed_bias),
        )
        object.__setattr__(
            self,
            "absolute_bias",
            _require_probability_decimal("absolute_bias", self.absolute_bias),
        )
        object.__setattr__(
            self,
            "squared_error",
            _require_probability_decimal("squared_error", self.squared_error),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "redacted_resolution_reference",
            _require_redacted_reference(
                "redacted_resolution_reference",
                self.redacted_resolution_reference,
            ),
        )
        object.__setattr__(
            self,
            "improvement_items",
            _normalize_improvement_items(self.improvement_items),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        if self.validation_config is not None:
            if type(self.validation_config) is not ResearchPostResolutionCalibrationReportConfig:
                raise ValueError(
                    "validation_config must be a ResearchPostResolutionCalibrationReportConfig",
                )
            _validate_row_against_config(self, self.validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPostResolutionCalibrationReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPostResolutionCalibrationReasonCodeCount:
            raise TypeError(
                "ResearchPostResolutionCalibrationReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPostResolutionCalibrationReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPostResolutionCalibrationReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_probability_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchPostResolutionCalibrationMemoryWritePlan:
    target: str
    planned_operation: str
    payload_family: str
    row_count: Decimal
    requires_operator_review: bool = True
    execute_write: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPostResolutionCalibrationMemoryWritePlan:
            raise TypeError(
                "ResearchPostResolutionCalibrationMemoryWritePlan does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPostResolutionCalibrationMemoryWritePlan:
            raise ValueError(
                "memory write plan must be exactly "
                "ResearchPostResolutionCalibrationMemoryWritePlan",
            )
        _require_member("target", self.target, SAFE_MEMORY_TARGETS)
        _require_member("planned_operation", self.planned_operation, ("insert_review_rows",))
        _require_member(
            "payload_family",
            self.payload_family,
            ("post_resolution_calibration_review",),
        )
        object.__setattr__(
            self,
            "row_count",
            _require_nonnegative_count_decimal("row_count", self.row_count),
        )
        if self.requires_operator_review is not True:
            raise ValueError("requires_operator_review must be True")
        if self.execute_write is not False:
            raise ValueError("execute_write must be False")
        _require_hard_flags("memory write plan", self)


@dataclass(frozen=True)
class ResearchPostResolutionCalibrationReport:
    generated_at: datetime
    config_version: str
    status: str
    next_step: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_signed_bias: Decimal
    mean_absolute_bias: Decimal
    max_absolute_bias: Decimal
    brier_score: Decimal
    rows: tuple[ResearchPostResolutionCalibrationRow, ...]
    reason_code_counts: tuple[ResearchPostResolutionCalibrationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    improvement_items: tuple[str, ...]
    memory_write_plan: ResearchPostResolutionCalibrationMemoryWritePlan | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPostResolutionCalibrationReport:
            raise TypeError(
                "ResearchPostResolutionCalibrationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPostResolutionCalibrationReport:
            raise ValueError("report must be exactly ResearchPostResolutionCalibrationReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_public_string("next_step", self.next_step)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_signed_bias",
            "mean_absolute_bias",
            "max_absolute_bias",
            "brier_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_report_metric_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "improvement_items",
            _normalize_improvement_items(self.improvement_items),
        )
        if self.memory_write_plan is not None:
            if type(self.memory_write_plan) is not ResearchPostResolutionCalibrationMemoryWritePlan:
                raise ValueError(
                    "memory_write_plan must be a ResearchPostResolutionCalibrationMemoryWritePlan",
                )
            _require_hard_flags("memory write plan", self.memory_write_plan)
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_post_resolution_calibration_report(
    resolved_events: list[ResearchPostResolutionCalibrationResolvedEvent]
    | tuple[ResearchPostResolutionCalibrationResolvedEvent, ...],
    *,
    config: ResearchPostResolutionCalibrationReportConfig | None = None,
    generated_at: datetime,
) -> ResearchPostResolutionCalibrationReport:
    cfg = config or ResearchPostResolutionCalibrationReportConfig()
    if type(cfg) is not ResearchPostResolutionCalibrationReportConfig:
        raise ValueError("config must be a ResearchPostResolutionCalibrationReportConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    events = _normalize_events(resolved_events)
    rows = tuple(
        sorted(
            (_row_from_event(event, cfg) for event in events),
            key=_row_sort_key,
        ),
    )
    event_count = _count(len(rows))
    report_reason_codes = _report_reason_codes(rows, cfg)
    status = _status_from_reason_codes(report_reason_codes)
    return ResearchPostResolutionCalibrationReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=status,
        next_step=NEXT_STEPS[status],
        event_count=event_count,
        pass_count=_count(sum(1 for row in rows if row.status == STATUS_PASS)),
        watch_count=_count(sum(1 for row in rows if row.status == STATUS_WATCH)),
        block_count=_count(sum(1 for row in rows if row.status == STATUS_BLOCK)),
        mean_signed_bias=_mean(row.signed_bias for row in rows),
        mean_absolute_bias=_mean(row.absolute_bias for row in rows),
        max_absolute_bias=max((row.absolute_bias for row in rows), default=ZERO),
        brier_score=_mean(row.squared_error for row in rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, report_reason_codes),
        reason_codes=report_reason_codes,
        improvement_items=_improvement_items(report_reason_codes),
        memory_write_plan=_memory_write_plan(rows, cfg),
    )


def research_post_resolution_calibration_report_payload(
    report: ResearchPostResolutionCalibrationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPostResolutionCalibrationReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPostResolutionCalibrationReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _row_from_event(
    event: ResearchPostResolutionCalibrationResolvedEvent,
    config: ResearchPostResolutionCalibrationReportConfig,
) -> ResearchPostResolutionCalibrationRow:
    signed_bias = _quantize(event.forecast_probability - event.resolved_probability)
    absolute_bias = _abs_decimal(signed_bias)
    squared_error = _quantize(signed_bias * signed_bias)
    reason_codes = _row_reason_codes(
        absolute_bias=absolute_bias,
        squared_error=squared_error,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchPostResolutionCalibrationRow(
        research_key=event.research_key,
        condition_id=event.condition_id,
        resolved_at=event.resolved_at,
        forecast_probability=event.forecast_probability,
        resolved_probability=event.resolved_probability,
        signed_bias=signed_bias,
        absolute_bias=absolute_bias,
        squared_error=squared_error,
        status=status,
        redacted_resolution_reference=_redacted_reference(
            event.public_resolution_reference,
        ),
        improvement_items=_improvement_items(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    absolute_bias: Decimal,
    squared_error: Decimal,
    config: ResearchPostResolutionCalibrationReportConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if absolute_bias >= config.absolute_bias_block_threshold:
        codes.append(REASON_BLOCK_ABSOLUTE_BIAS)
    elif absolute_bias >= config.absolute_bias_watch_threshold:
        codes.append(REASON_WATCH_ABSOLUTE_BIAS)
    if squared_error >= config.brier_block_threshold:
        codes.append(REASON_BLOCK_BRIER)
    elif squared_error >= config.brier_watch_threshold:
        codes.append(REASON_WATCH_BRIER)
    if not codes:
        codes.append(REASON_PASS)
    return _sort_reason_codes(codes)


def _report_reason_codes(
    rows: tuple[ResearchPostResolutionCalibrationRow, ...],
    config: ResearchPostResolutionCalibrationReportConfig,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_NO_INPUTS,)
    codes: list[str] = []
    mean_signed_bias = _mean(row.signed_bias for row in rows)
    absolute_mean_bias = _abs_decimal(mean_signed_bias)
    brier_score = _mean(row.squared_error for row in rows)
    if absolute_mean_bias >= config.mean_bias_block_threshold:
        codes.append(REASON_BLOCK_MEAN_BIAS)
    elif absolute_mean_bias >= config.mean_bias_watch_threshold:
        codes.append(REASON_WATCH_MEAN_BIAS)
    if brier_score >= config.brier_block_threshold:
        codes.append(REASON_BLOCK_BRIER)
    elif brier_score >= config.brier_watch_threshold:
        codes.append(REASON_WATCH_BRIER)
    for row in rows:
        codes.extend(row.reason_codes)
    if _count(len(rows)) < config.min_resolved_event_count:
        codes.append(REASON_THIN_SAMPLE)
    if config.local_memory_write_planning_enabled:
        codes.append(REASON_MEMORY_PLAN)
    if not codes or set(codes) == {REASON_PASS}:
        codes = [REASON_PASS]
    return _sort_reason_codes(codes)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any("_block" in reason_code for reason_code in reason_codes):
        return STATUS_BLOCK
    if any("_watch" in reason_code for reason_code in reason_codes):
        return STATUS_WATCH
    if REASON_THIN_SAMPLE in reason_codes or REASON_NO_INPUTS in reason_codes:
        return STATUS_BLOCK
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchPostResolutionCalibrationRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchPostResolutionCalibrationReasonCodeCount, ...]:
    denominator = _count(len(rows))
    if not rows:
        return (
            ResearchPostResolutionCalibrationReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                event_ratio=ONE,
            ),
        )
    counts = []
    for reason_code in report_reason_codes:
        if reason_code == REASON_MEMORY_PLAN:
            count = denominator
        elif reason_code in (REASON_BLOCK_MEAN_BIAS, REASON_WATCH_MEAN_BIAS):
            count = denominator
        elif reason_code in (REASON_BLOCK_BRIER, REASON_WATCH_BRIER):
            count = _count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            )
            if count == ZERO:
                count = denominator
        elif reason_code == REASON_THIN_SAMPLE:
            count = denominator
        else:
            count = _count(sum(1 for row in rows if reason_code in row.reason_codes))
        counts.append(
            ResearchPostResolutionCalibrationReasonCodeCount(
                reason_code=reason_code,
                count=count,
                event_ratio=_ratio(count, denominator),
            ),
        )
    return tuple(counts)


def _memory_write_plan(
    rows: tuple[ResearchPostResolutionCalibrationRow, ...],
    config: ResearchPostResolutionCalibrationReportConfig,
) -> ResearchPostResolutionCalibrationMemoryWritePlan | None:
    if not config.local_memory_write_planning_enabled:
        return None
    return ResearchPostResolutionCalibrationMemoryWritePlan(
        target="local_supabase_postgres_research_memory",
        planned_operation="insert_review_rows",
        payload_family="post_resolution_calibration_review",
        row_count=_count(len(rows)),
    )


def _normalize_events(
    events: list[ResearchPostResolutionCalibrationResolvedEvent]
    | tuple[ResearchPostResolutionCalibrationResolvedEvent, ...],
) -> tuple[ResearchPostResolutionCalibrationResolvedEvent, ...]:
    if type(events) not in (list, tuple):
        raise ValueError("resolved_events must be a list or tuple")
    normalized: list[ResearchPostResolutionCalibrationResolvedEvent] = []
    seen: set[str] = set()
    for event in events:
        if type(event) is not ResearchPostResolutionCalibrationResolvedEvent:
            raise ValueError(
                "resolved_events must contain ResearchPostResolutionCalibrationResolvedEvent",
            )
        _require_hard_flags("event", event)
        if event.condition_id in seen:
            raise ValueError("condition_id values must be unique")
        seen.add(event.condition_id)
        normalized.append(event)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchPostResolutionCalibrationRow, ...],
) -> tuple[ResearchPostResolutionCalibrationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPostResolutionCalibrationRow:
            raise ValueError("rows must contain ResearchPostResolutionCalibrationRow")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchPostResolutionCalibrationReasonCodeCount, ...],
) -> tuple[ResearchPostResolutionCalibrationReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPostResolutionCalibrationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPostResolutionCalibrationReasonCodeCount",
            )
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
        _require_hard_flags("reason code count", row)
    if tuple(row.reason_code for row in rows) != _sort_reason_codes(
        tuple(row.reason_code for row in rows),
    ):
        raise ValueError("reason_code_counts must be sorted")
    return rows


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    sorted_codes = _sort_reason_codes(reason_codes)
    if reason_codes != sorted_codes:
        raise ValueError("reason_codes must be sorted")
    return reason_codes


def _normalize_improvement_items(items: tuple[str, ...]) -> tuple[str, ...]:
    if type(items) is not tuple:
        raise ValueError("improvement_items must be a tuple")
    if len(set(items)) != len(items):
        raise ValueError("improvement_items must be unique")
    for item in items:
        _require_safe_action("improvement_items", item)
    return items


def _improvement_items(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    items: list[str] = []
    for reason_code in reason_codes:
        item = IMPROVEMENT_ACTIONS[reason_code]
        if item not in items:
            items.append(item)
    return tuple(items)


def _validate_row_against_config(
    row: ResearchPostResolutionCalibrationRow,
    config: ResearchPostResolutionCalibrationReportConfig,
) -> None:
    if row.signed_bias != _quantize(row.forecast_probability - row.resolved_probability):
        raise ValueError("signed_bias must match forecast and resolved probability")
    if row.absolute_bias != _abs_decimal(row.signed_bias):
        raise ValueError("absolute_bias must match signed_bias")
    if row.squared_error != _quantize(row.signed_bias * row.signed_bias):
        raise ValueError("squared_error must match signed_bias")
    expected_reason_codes = _row_reason_codes(
        absolute_bias=row.absolute_bias,
        squared_error=row.squared_error,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.improvement_items != _improvement_items(row.reason_codes):
        raise ValueError("improvement_items must match reason_codes")


def _validate_report(report: ResearchPostResolutionCalibrationReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.status == STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.mean_signed_bias != _mean(row.signed_bias for row in report.rows):
        raise ValueError("mean_signed_bias must match rows")
    if report.mean_absolute_bias != _mean(row.absolute_bias for row in report.rows):
        raise ValueError("mean_absolute_bias must match rows")
    if report.max_absolute_bias != max(
        (row.absolute_bias for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_absolute_bias must match rows")
    if report.brier_score != _mean(row.squared_error for row in report.rows):
        raise ValueError("brier_score must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.next_step != NEXT_STEPS[report.status]:
        raise ValueError("next_step must match status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.improvement_items != _improvement_items(report.reason_codes):
        raise ValueError("improvement_items must match reason_codes")
    if report.memory_write_plan is not None:
        if report.memory_write_plan.row_count != report.event_count:
            raise ValueError("memory_write_plan row_count must match event_count")


def _row_sort_key(row: ResearchPostResolutionCalibrationRow) -> tuple[str, str]:
    return (row.status, row.condition_id)


def _sort_reason_codes(reason_codes: Any) -> tuple[str, ...]:
    unique = tuple(dict.fromkeys(reason_codes))
    rank_by_code = {
        reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)
    }
    return tuple(sorted(unique, key=lambda reason_code: rank_by_code[reason_code]))


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value)
            for key, nested_value in asdict(value).items()
            if key != "validation_config"
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == "validation_config":
                continue
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if type(value) is dict:
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{key} has unsafe public field")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(
                label,
                nested_value,
                key if not path else f"{path}.{key}",
            )
        return
    if type(value) in (tuple, list):
        for index, nested_value in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                nested_value,
                f"{current_path}[{index}]",
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_FRAGMENTS)


def _redacted_reference(value: str) -> str:
    if _is_safe_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_redacted_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.startswith("sha256:"):
        suffix = value.removeprefix("sha256:")
        if len(suffix) != 12 or any(char not in "0123456789abcdef" for char in suffix):
            raise ValueError(f"{field_name} must be a safe redacted reference")
        return value
    _require_reference(field_name, value)
    if not _is_safe_reference(value):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public reference")
    return value


def _is_safe_reference(value: str) -> bool:
    return (
        value.startswith("public-")
        and "://" not in value
        and "?" not in value
        and not _has_unsafe_public_fragment(value)
    )


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if not all(char.islower() or char.isdigit() or char in "._-" for char in value):
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_safe_action(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value.startswith(("buy_", "sell_", "hold_", "recommend_")):
        raise ValueError(f"{field_name} must not contain investment action text")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} has unsupported reason code")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")
    return value


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, STATUSES)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in range 0 to 1")
    return decimal_value


def _require_binary_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_probability_decimal(field_name, value)
    if decimal_value not in (ZERO, ONE):
        raise ValueError(f"{field_name} must be 0 or 1 for resolved events")
    return decimal_value


def _require_signed_probability_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in range -1 to 1")
    return decimal_value


def _require_report_metric_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if field_name == "mean_signed_bias":
        if decimal_value < -ONE or decimal_value > ONE:
            raise ValueError(f"{field_name} must be in range -1 to 1")
        return decimal_value
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in range 0 to 1")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return decimal_value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _mean(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _ratio(_sum_decimal(items), _count(len(items)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(abs(value))
