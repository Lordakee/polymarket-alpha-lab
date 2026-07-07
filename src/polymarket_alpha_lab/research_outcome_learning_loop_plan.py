"""Pure report-only learning-loop plan for settled prediction outcomes."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any


__all__ = (
    "ResearchOutcomeLearningLoopConfig",
    "ResearchOutcomeLearningLoopEvent",
    "ResearchOutcomeLearningLoopPlanRow",
    "ResearchOutcomeLearningLoopPublicPayloadItem",
    "ResearchOutcomeLearningLoopReasonCodeCount",
    "ResearchOutcomeLearningLoopReport",
    "build_research_outcome_learning_loop_plan",
    "research_outcome_learning_loop_plan_payload",
)


DEFAULT_CONFIG_VERSION = "research-outcome-learning-loop-plan-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
LOCAL_WRITE_PLAN_READY_STEPS = (
    "stage_redacted_outcome_delta",
    "upsert_team_memory_rollup",
    "append_evidence_gap_backlog",
)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "dsn",
    "source_url",
    "source-url",
    "source.text",
    "source_text",
    "raw_market",
    "raw-market",
    "market-raw",
    "http",
    "https",
    "api_key",
    "private-key",
    "secret",
    "token",
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "mu" + "tation",
    "b" + "uy",
    "s" + "ell",
    "tra" + "de",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchOutcomeLearningLoopConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_learning_score: Decimal = Decimal("0.700000")
    watch_learning_score: Decimal = Decimal("0.400000")
    forecast_bias_weight: Decimal = Decimal("0.350000")
    evidence_gap_weight: Decimal = Decimal("0.250000")
    memory_update_weight: Decimal = Decimal("0.200000")
    write_plan_weight: Decimal = Decimal("0.200000")
    forecast_bias_watch_threshold: Decimal = Decimal("0.150000")
    forecast_bias_block_threshold: Decimal = Decimal("0.350000")
    minimum_write_plan_items: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningLoopConfig:
            raise TypeError(
                "ResearchOutcomeLearningLoopConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningLoopConfig:
            raise ValueError("config must be exactly ResearchOutcomeLearningLoopConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_learning_score",
            "watch_learning_score",
            "forecast_bias_weight",
            "evidence_gap_weight",
            "memory_update_weight",
            "write_plan_weight",
            "forecast_bias_watch_threshold",
            "forecast_bias_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_write_plan_items",
            _require_positive_count_decimal(
                "minimum_write_plan_items",
                self.minimum_write_plan_items,
            ),
        )
        if self.pass_learning_score <= self.watch_learning_score:
            raise ValueError("pass_learning_score must be greater than watch_learning_score")
        if self.forecast_bias_watch_threshold > self.forecast_bias_block_threshold:
            raise ValueError(
                "forecast_bias_watch_threshold must not exceed "
                "forecast_bias_block_threshold",
            )
        weight_sum = _quantize(
            self.forecast_bias_weight
            + self.evidence_gap_weight
            + self.memory_update_weight
            + self.write_plan_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "forecast_bias_weight, evidence_gap_weight, memory_update_weight, "
                "and write_plan_weight must sum to 1",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningLoopEvent:
    event_ref: str
    team_ref: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    evidence_gap_score: Decimal
    memory_update_score: Decimal
    write_plan_score: Decimal
    resolved_at: datetime
    evidence_gap_count: Decimal = ZERO
    memory_item_count: Decimal = ZERO
    write_plan_item_count: Decimal = ZERO
    has_resolution_evidence: bool = True
    has_team_memory_update: bool = True
    has_local_write_plan: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningLoopEvent:
            raise TypeError(
                "ResearchOutcomeLearningLoopEvent does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningLoopEvent:
            raise ValueError("event must be exactly ResearchOutcomeLearningLoopEvent")
        _require_public_identifier("event_ref", self.event_ref)
        _require_public_identifier("team_ref", self.team_ref)
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "evidence_gap_score",
            "memory_update_score",
            "write_plan_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "evidence_gap_count",
            "memory_item_count",
            "write_plan_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "has_resolution_evidence",
            "has_team_memory_update",
            "has_local_write_plan",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("event", self)
        _reject_unsafe_public_payload("event", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningLoopPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningLoopPublicPayloadItem:
            raise TypeError(
                "ResearchOutcomeLearningLoopPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningLoopPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchOutcomeLearningLoopPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningLoopPlanRow:
    event_ref: str
    team_ref: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    forecast_bias: Decimal
    bias_score: Decimal
    evidence_gap_score: Decimal
    evidence_coverage_score: Decimal
    memory_update_score: Decimal
    write_plan_score: Decimal
    evidence_gap_count: Decimal
    memory_item_count: Decimal
    write_plan_item_count: Decimal
    has_resolution_evidence: bool
    has_team_memory_update: bool
    has_local_write_plan: bool
    learning_score: Decimal
    status: str
    resolved_at: datetime
    local_write_plan: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningLoopPlanRow:
            raise TypeError(
                "ResearchOutcomeLearningLoopPlanRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningLoopPlanRow:
            raise ValueError("row must be exactly ResearchOutcomeLearningLoopPlanRow")
        _require_public_identifier("event_ref", self.event_ref)
        _require_public_identifier("team_ref", self.team_ref)
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "forecast_bias",
            "bias_score",
            "evidence_gap_score",
            "evidence_coverage_score",
            "memory_update_score",
            "write_plan_score",
            "learning_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_gap_count",
            "memory_item_count",
            "write_plan_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "has_resolution_evidence",
            "has_team_memory_update",
            "has_local_write_plan",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        object.__setattr__(
            self,
            "local_write_plan",
            _normalize_string_tuple("local_write_plan", self.local_write_plan),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningLoopReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningLoopReasonCodeCount:
            raise TypeError(
                "ResearchOutcomeLearningLoopReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningLoopReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchOutcomeLearningLoopReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchOutcomeLearningLoopReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_learning_score: Decimal | None
    status: str
    rows: tuple[ResearchOutcomeLearningLoopPlanRow, ...]
    reason_code_counts: tuple[ResearchOutcomeLearningLoopReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchOutcomeLearningLoopPublicPayloadItem, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchOutcomeLearningLoopReport:
            raise TypeError(
                "ResearchOutcomeLearningLoopReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchOutcomeLearningLoopReport:
            raise ValueError("report must be exactly ResearchOutcomeLearningLoopReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("event_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_learning_score",
            _require_optional_ratio_decimal(
                "average_learning_score",
                self.average_learning_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchOutcomeLearningLoopReport.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


def build_research_outcome_learning_loop_plan(
    events: Iterable[object],
    *,
    config: ResearchOutcomeLearningLoopConfig,
    generated_at: datetime,
) -> ResearchOutcomeLearningLoopReport:
    if type(config) is not ResearchOutcomeLearningLoopConfig:
        raise ValueError("config must be a ResearchOutcomeLearningLoopConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events)
    for item in normalized_events:
        _reject_unsettled_event(item, generated)

    rows = tuple(
        sorted(
            (_row_from_event(item, config=config) for item in normalized_events),
            key=lambda row: (row.event_ref, row.team_ref),
        ),
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchOutcomeLearningLoopReport(
        generated_at=generated,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_learning_score=_average_learning_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
        public_payload=(),
    )


def research_outcome_learning_loop_plan_payload(
    report: ResearchOutcomeLearningLoopReport,
) -> dict[str, Any]:
    if type(report) is not ResearchOutcomeLearningLoopReport:
        raise ValueError("report must be a ResearchOutcomeLearningLoopReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = report.payload
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_from_event(
    event: ResearchOutcomeLearningLoopEvent,
    *,
    config: ResearchOutcomeLearningLoopConfig,
) -> ResearchOutcomeLearningLoopPlanRow:
    forecast_bias = _quantize(abs(event.forecast_probability - event.resolved_probability))
    bias_score = _quantize(max(ZERO, ONE - forecast_bias))
    evidence_coverage_score = _quantize(max(ZERO, ONE - event.evidence_gap_score))
    effective_memory_score = (
        event.memory_update_score if event.has_team_memory_update else ZERO
    )
    effective_write_plan_score = event.write_plan_score if event.has_local_write_plan else ZERO
    learning_score = _learning_score(
        bias_score=bias_score,
        evidence_coverage_score=evidence_coverage_score,
        memory_update_score=effective_memory_score,
        write_plan_score=effective_write_plan_score,
        config=config,
    )
    status = _row_status(
        learning_score=learning_score,
        has_resolution_evidence=event.has_resolution_evidence,
        has_local_write_plan=event.has_local_write_plan,
        has_team_memory_update=event.has_team_memory_update,
        write_plan_item_count=event.write_plan_item_count,
        forecast_bias=forecast_bias,
        config=config,
    )
    return ResearchOutcomeLearningLoopPlanRow(
        event_ref=event.event_ref,
        team_ref=event.team_ref,
        forecast_probability=event.forecast_probability,
        resolved_probability=event.resolved_probability,
        forecast_bias=forecast_bias,
        bias_score=bias_score,
        evidence_gap_score=event.evidence_gap_score,
        evidence_coverage_score=evidence_coverage_score,
        memory_update_score=event.memory_update_score,
        write_plan_score=event.write_plan_score,
        evidence_gap_count=event.evidence_gap_count,
        memory_item_count=event.memory_item_count,
        write_plan_item_count=event.write_plan_item_count,
        has_resolution_evidence=event.has_resolution_evidence,
        has_team_memory_update=event.has_team_memory_update,
        has_local_write_plan=event.has_local_write_plan,
        learning_score=learning_score,
        status=status,
        resolved_at=event.resolved_at,
        local_write_plan=(
            LOCAL_WRITE_PLAN_READY_STEPS if event.has_local_write_plan else ()
        ),
        reason_codes=_row_reason_codes(
            status=status,
            forecast_bias=forecast_bias,
            evidence_gap_score=event.evidence_gap_score,
            evidence_gap_count=event.evidence_gap_count,
            memory_item_count=event.memory_item_count,
            write_plan_item_count=event.write_plan_item_count,
            has_resolution_evidence=event.has_resolution_evidence,
            has_team_memory_update=event.has_team_memory_update,
            has_local_write_plan=event.has_local_write_plan,
            config=config,
            input_reason_codes=event.reason_codes,
        ),
    )


def _normalize_events(events: Iterable[object]) -> tuple[ResearchOutcomeLearningLoopEvent, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    return tuple(_coerce_event(value) for value in values)


def _coerce_event(value: object) -> ResearchOutcomeLearningLoopEvent:
    if type(value) is ResearchOutcomeLearningLoopEvent:
        _require_hard_flags("event", value)
        return value
    _require_hard_flags("event", value)
    return ResearchOutcomeLearningLoopEvent(
        event_ref=_field_value(value, "event_ref"),
        team_ref=_field_value(value, "team_ref"),
        forecast_probability=_field_value(value, "forecast_probability"),
        resolved_probability=_field_value(value, "resolved_probability"),
        evidence_gap_score=_field_value(value, "evidence_gap_score"),
        memory_update_score=_field_value(value, "memory_update_score"),
        write_plan_score=_field_value(value, "write_plan_score"),
        resolved_at=_field_value(value, "resolved_at"),
        evidence_gap_count=_field_value(value, "evidence_gap_count", default=ZERO),
        memory_item_count=_field_value(value, "memory_item_count", default=ZERO),
        write_plan_item_count=_field_value(
            value,
            "write_plan_item_count",
            default=ZERO,
        ),
        has_resolution_evidence=_field_value(
            value,
            "has_resolution_evidence",
            default=True,
        ),
        has_team_memory_update=_field_value(
            value,
            "has_team_memory_update",
            default=True,
        ),
        has_local_write_plan=_field_value(value, "has_local_write_plan", default=True),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _learning_score(
    *,
    bias_score: Decimal,
    evidence_coverage_score: Decimal,
    memory_update_score: Decimal,
    write_plan_score: Decimal,
    config: ResearchOutcomeLearningLoopConfig,
) -> Decimal:
    return _quantize(
        (bias_score * config.forecast_bias_weight)
        + (evidence_coverage_score * config.evidence_gap_weight)
        + (memory_update_score * config.memory_update_weight)
        + (write_plan_score * config.write_plan_weight),
    )


def _row_status(
    *,
    learning_score: Decimal,
    has_resolution_evidence: bool,
    has_local_write_plan: bool,
    has_team_memory_update: bool,
    write_plan_item_count: Decimal,
    forecast_bias: Decimal,
    config: ResearchOutcomeLearningLoopConfig,
) -> str:
    if (
        learning_score < config.watch_learning_score
        or not has_resolution_evidence
        or not has_local_write_plan
    ):
        return "blocked"
    if learning_score < config.pass_learning_score:
        return "watch"
    if not has_team_memory_update:
        return "watch"
    if write_plan_item_count < config.minimum_write_plan_items:
        return "watch"
    if forecast_bias >= config.forecast_bias_watch_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    forecast_bias: Decimal,
    evidence_gap_score: Decimal,
    evidence_gap_count: Decimal,
    memory_item_count: Decimal,
    write_plan_item_count: Decimal,
    has_resolution_evidence: bool,
    has_team_memory_update: bool,
    has_local_write_plan: bool,
    config: ResearchOutcomeLearningLoopConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = {f"research_outcome_learning_loop_{status}"}
    if forecast_bias >= config.forecast_bias_block_threshold:
        reason_codes.add("prediction_bias_block_threshold_exceeded")
    elif forecast_bias >= config.forecast_bias_watch_threshold:
        reason_codes.add("prediction_bias_watch_threshold_exceeded")
    else:
        reason_codes.add("prediction_bias_within_watch_threshold")
    reason_codes.add(
        "resolution_evidence_present"
        if has_resolution_evidence
        else "resolution_evidence_missing",
    )
    if evidence_gap_count > ZERO or evidence_gap_score > ZERO:
        reason_codes.add("evidence_gap_backlog_needed")
    if has_team_memory_update and memory_item_count > ZERO:
        reason_codes.add("memory_update_ready")
    else:
        reason_codes.add("memory_update_missing")
    if not has_local_write_plan:
        reason_codes.add("local_postgres_write_plan_missing")
    elif write_plan_item_count < config.minimum_write_plan_items:
        reason_codes.add("local_postgres_write_plan_incomplete")
    else:
        reason_codes.add("local_postgres_write_plan_ready")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchOutcomeLearningLoopPlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_settled_prediction_events",)
    if all(row.status == "pass" for row in rows):
        return ("research_outcome_learning_loop_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_settled_prediction_events",):
        return "blocked"
    if "research_outcome_learning_loop_blocked" in reason_codes:
        return "blocked"
    if "research_outcome_learning_loop_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchOutcomeLearningLoopPlanRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchOutcomeLearningLoopReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchOutcomeLearningLoopReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchOutcomeLearningLoopReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_learning_score(
    rows: tuple[ResearchOutcomeLearningLoopPlanRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.learning_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(rows: tuple[ResearchOutcomeLearningLoopPlanRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _reject_unsettled_event(
    event: ResearchOutcomeLearningLoopEvent,
    generated_at: datetime,
) -> None:
    if event.resolved_at >= generated_at:
        raise ValueError("resolved_at must be before generated_at")


def _normalize_rows(
    rows: tuple[ResearchOutcomeLearningLoopPlanRow, ...],
) -> tuple[ResearchOutcomeLearningLoopPlanRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchOutcomeLearningLoopPlanRow:
            raise ValueError("rows must contain ResearchOutcomeLearningLoopPlanRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.event_ref, row.team_ref)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_ref and team_ref")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchOutcomeLearningLoopReasonCodeCount, ...],
) -> tuple[ResearchOutcomeLearningLoopReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchOutcomeLearningLoopReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchOutcomeLearningLoopReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_public_payload(
    public_payload: tuple[ResearchOutcomeLearningLoopPublicPayloadItem, ...],
) -> tuple[ResearchOutcomeLearningLoopPublicPayloadItem, ...]:
    if type(public_payload) is not tuple:
        raise ValueError("public_payload must be a tuple")
    for item in public_payload:
        if type(item) is not ResearchOutcomeLearningLoopPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchOutcomeLearningLoopPublicPayloadItem values",
            )
        _require_hard_flags("public_payload item", item)
    sorted_payload = tuple(sorted(public_payload, key=lambda item: item.key))
    if public_payload != sorted_payload:
        raise ValueError("public_payload must be sorted by key")
    return public_payload


def _validate_row_consistency(row: ResearchOutcomeLearningLoopPlanRow) -> None:
    expected_bias = _quantize(abs(row.forecast_probability - row.resolved_probability))
    if row.forecast_bias != expected_bias:
        raise ValueError("forecast_bias must match forecast and resolution")
    if row.bias_score != _quantize(max(ZERO, ONE - row.forecast_bias)):
        raise ValueError("bias_score must match forecast_bias")
    if row.evidence_coverage_score != _quantize(max(ZERO, ONE - row.evidence_gap_score)):
        raise ValueError("evidence_coverage_score must match evidence_gap_score")
    if row.local_write_plan not in ((), LOCAL_WRITE_PLAN_READY_STEPS):
        raise ValueError("local_write_plan must use supported readonly steps")
    if row.has_local_write_plan and row.local_write_plan != LOCAL_WRITE_PLAN_READY_STEPS:
        raise ValueError("local_write_plan must be present when local plan is available")
    if not row.has_local_write_plan and row.local_write_plan != ():
        raise ValueError("local_write_plan must be empty when local plan is missing")
    _validate_learning_score_and_status(row)


def _validate_learning_score_and_status(row: ResearchOutcomeLearningLoopPlanRow) -> None:
    effective_memory_score = (
        row.memory_update_score if row.has_team_memory_update else ZERO
    )
    effective_write_plan_score = row.write_plan_score if row.has_local_write_plan else ZERO
    expected_score = _quantize(
        (row.bias_score * Decimal("0.350000"))
        + (row.evidence_coverage_score * Decimal("0.250000"))
        + (effective_memory_score * Decimal("0.200000"))
        + (effective_write_plan_score * Decimal("0.200000")),
    )
    if row.learning_score != expected_score:
        raise ValueError("learning_score must match row components")
    if row.status == "pass" and row.learning_score < Decimal("0.700000"):
        raise ValueError("learning_score must support pass status")
    if row.status == "watch" and not (
        Decimal("0.400000") <= row.learning_score < Decimal("0.700000")
        or row.forecast_bias >= Decimal("0.150000")
        or not row.has_team_memory_update
    ):
        raise ValueError("learning_score must support watch status")
    if row.status == "blocked" and row.learning_score >= Decimal("0.400000"):
        if row.has_resolution_evidence and row.has_local_write_plan:
            raise ValueError("learning_score must support blocked status")


def _validate_report_consistency(report: ResearchOutcomeLearningLoopReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_learning_score != _average_learning_score(report.rows):
        raise ValueError("average_learning_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: datetime) -> datetime:
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
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must contain public identifiers")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    _reject_unsafe_public_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_string_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier(field_name, value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label}.{field_name} is required")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("payload key", key)
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _json_ready(value: Any) -> Any:
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
