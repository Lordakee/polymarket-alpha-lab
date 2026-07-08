"""Pure manual queue priority exception report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_REPORT_CONFIG_VERSION = (
    "research-strategy-manual-queue-priority-exception-report-v0"
)
RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
ROW_REASON_CODES = (
    "manual_queue_priority_exception_pass",
    "manual_queue_priority_exception_watch",
    "manual_queue_priority_exception_block",
    "evidence_maturity_watch",
    "evidence_maturity_block",
    "cost_freshness_watch",
    "cost_freshness_block",
    "specialist_consensus_watch",
    "specialist_consensus_block",
    "source_conflict_pressure_watch",
    "source_conflict_pressure_block",
    "queue_age_watch",
    "queue_age_block",
    "manual_escalation_urgency_watch",
    "manual_escalation_urgency_block",
)
REPORT_REASON_CODES = (
    "manual_queue_priority_exception_report_empty",
    "manual_queue_priority_exception_report_pass",
    "manual_queue_priority_exception_report_watch",
    "manual_queue_priority_exception_report_block",
    "evidence_maturity_exception",
    "cost_freshness_exception",
    "specialist_consensus_exception",
    "source_conflict_pressure_exception",
    "queue_age_exception",
    "manual_escalation_urgency_exception",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate" + "_id",
    "market" + "_id",
    "market" + "_slug",
    "que" + "stion",
    "source" + "_url",
    "source" + "_text",
    "d" + "sn",
    "table" + "_name",
    "private" + "_token",
    "secret",
    "credential",
)


@dataclass(frozen=True)
class ResearchStrategyManualQueuePriorityExceptionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_REPORT_CONFIG_VERSION
    )
    min_pass_evidence_maturity_score: Decimal = Decimal("0.800000")
    min_watch_evidence_maturity_score: Decimal = Decimal("0.600000")
    min_pass_cost_freshness_score: Decimal = Decimal("0.800000")
    min_watch_cost_freshness_score: Decimal = Decimal("0.600000")
    min_pass_specialist_consensus_score: Decimal = Decimal("0.750000")
    min_watch_specialist_consensus_score: Decimal = Decimal("0.500000")
    max_pass_source_conflict_pressure: Decimal = Decimal("0.300000")
    max_watch_source_conflict_pressure: Decimal = Decimal("0.700000")
    max_pass_queue_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_queue_age_seconds: Decimal = Decimal("259200.000000")
    max_pass_manual_escalation_urgency: Decimal = Decimal("0.300000")
    max_watch_manual_escalation_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualQueuePriorityExceptionConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "min_pass_evidence_maturity_score",
            "min_watch_evidence_maturity_score",
            "min_pass_cost_freshness_score",
            "min_watch_cost_freshness_score",
            "min_pass_specialist_consensus_score",
            "min_watch_specialist_consensus_score",
            "max_pass_source_conflict_pressure",
            "max_watch_source_conflict_pressure",
            "max_pass_manual_escalation_urgency",
            "max_watch_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_queue_age_seconds",
            "max_watch_queue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "min_watch_evidence_maturity_score",
            self.min_watch_evidence_maturity_score,
            self.min_pass_evidence_maturity_score,
        )
        _require_floor_pair(
            "min_watch_cost_freshness_score",
            self.min_watch_cost_freshness_score,
            self.min_pass_cost_freshness_score,
        )
        _require_floor_pair(
            "min_watch_specialist_consensus_score",
            self.min_watch_specialist_consensus_score,
            self.min_pass_specialist_consensus_score,
        )
        _require_ceiling_pair(
            "max_pass_source_conflict_pressure",
            self.max_pass_source_conflict_pressure,
            self.max_watch_source_conflict_pressure,
        )
        _require_ceiling_pair(
            "max_pass_queue_age_seconds",
            self.max_pass_queue_age_seconds,
            self.max_watch_queue_age_seconds,
        )
        _require_ceiling_pair(
            "max_pass_manual_escalation_urgency",
            self.max_pass_manual_escalation_urgency,
            self.max_watch_manual_escalation_urgency,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyManualQueuePriorityExceptionInput:
    aggregation_key: str
    evidence_maturity_score: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    source_conflict_pressure: Decimal
    queue_age_seconds: Decimal
    manual_escalation_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualQueuePriorityExceptionInput,
            "input",
        )
        _require_input_key("aggregation_key", self.aggregation_key)
        for field_name in (
            "evidence_maturity_score",
            "cost_freshness_score",
            "specialist_consensus_score",
            "source_conflict_pressure",
            "manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_age_seconds",
            _normalize_nonnegative_decimal("queue_age_seconds", self.queue_age_seconds),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyManualQueuePriorityExceptionReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyManualQueuePriorityExceptionRow:
    aggregate_row_number: Decimal
    aggregate_hash: str
    evidence_maturity_score: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    source_conflict_pressure: Decimal
    queue_age_seconds: Decimal
    manual_escalation_urgency: Decimal
    priority_exception_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualQueuePriorityExceptionRow,
            "row",
        )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_whole_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_digest("aggregate_hash", self.aggregate_hash)
        for field_name in (
            "evidence_maturity_score",
            "cost_freshness_score",
            "specialist_consensus_score",
            "source_conflict_pressure",
            "manual_escalation_urgency",
            "priority_exception_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_age_seconds",
            _normalize_nonnegative_decimal("queue_age_seconds", self.queue_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyManualQueuePriorityExceptionReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_evidence_maturity_score: Decimal
    mean_cost_freshness_score: Decimal
    mean_specialist_consensus_score: Decimal
    max_source_conflict_pressure: Decimal
    mean_queue_age_seconds: Decimal
    max_queue_age_seconds: Decimal
    max_manual_escalation_urgency: Decimal
    mean_priority_exception_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyManualQueuePriorityExceptionReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyManualQueuePriorityExceptionRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualQueuePriorityExceptionReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("input_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_maturity_score",
            "mean_cost_freshness_score",
            "mean_specialist_consensus_score",
            "max_source_conflict_pressure",
            "max_manual_escalation_urgency",
            "mean_priority_exception_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_queue_age_seconds", "max_queue_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_manual_queue_priority_exception_report(
    inputs: Iterable[ResearchStrategyManualQueuePriorityExceptionInput],
    *,
    config: ResearchStrategyManualQueuePriorityExceptionConfig,
    generated_at: datetime,
) -> ResearchStrategyManualQueuePriorityExceptionReport:
    if type(config) is not ResearchStrategyManualQueuePriorityExceptionConfig:
        raise ValueError(
            "config must be a ResearchStrategyManualQueuePriorityExceptionConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    row_values = tuple(_row_value_from_input(value, config=config) for value in normalized_inputs)
    row_values = tuple(sorted(row_values, key=_row_value_sort_key))
    rows = tuple(
        _row_from_value(index=index, value=value)
        for index, value in enumerate(row_values, start=1)
    )
    return ResearchStrategyManualQueuePriorityExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_evidence_maturity_score=_mean(
            tuple(row.evidence_maturity_score for row in rows),
        ),
        mean_cost_freshness_score=_mean(
            tuple(row.cost_freshness_score for row in rows),
        ),
        mean_specialist_consensus_score=_mean(
            tuple(row.specialist_consensus_score for row in rows),
        ),
        max_source_conflict_pressure=_maximum(
            tuple(row.source_conflict_pressure for row in rows),
        ),
        mean_queue_age_seconds=_mean(tuple(row.queue_age_seconds for row in rows)),
        max_queue_age_seconds=_maximum(tuple(row.queue_age_seconds for row in rows)),
        max_manual_escalation_urgency=_maximum(
            tuple(row.manual_escalation_urgency for row in rows),
        ),
        mean_priority_exception_score=_mean(
            tuple(row.priority_exception_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_manual_queue_priority_exception_report_payload(
    report: ResearchStrategyManualQueuePriorityExceptionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyManualQueuePriorityExceptionReport:
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyManualQueuePriorityExceptionReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_manual_queue_priority_exception_report_digest(
    report: ResearchStrategyManualQueuePriorityExceptionReport,
) -> str:
    payload = research_strategy_manual_queue_priority_exception_report_payload(report)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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


@dataclass(frozen=True)
class _RowValue:
    aggregate_hash: str
    evidence_maturity_score: Decimal
    cost_freshness_score: Decimal
    specialist_consensus_score: Decimal
    source_conflict_pressure: Decimal
    queue_age_seconds: Decimal
    manual_escalation_urgency: Decimal
    priority_exception_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _row_value_from_input(
    value: ResearchStrategyManualQueuePriorityExceptionInput,
    *,
    config: ResearchStrategyManualQueuePriorityExceptionConfig,
) -> _RowValue:
    component_statuses = {
        "evidence_maturity": _floor_status(
            value.evidence_maturity_score,
            watch_value=config.min_watch_evidence_maturity_score,
            pass_value=config.min_pass_evidence_maturity_score,
        ),
        "cost_freshness": _floor_status(
            value.cost_freshness_score,
            watch_value=config.min_watch_cost_freshness_score,
            pass_value=config.min_pass_cost_freshness_score,
        ),
        "specialist_consensus": _floor_status(
            value.specialist_consensus_score,
            watch_value=config.min_watch_specialist_consensus_score,
            pass_value=config.min_pass_specialist_consensus_score,
        ),
        "source_conflict_pressure": _ceiling_status(
            value.source_conflict_pressure,
            pass_value=config.max_pass_source_conflict_pressure,
            watch_value=config.max_watch_source_conflict_pressure,
        ),
        "queue_age": _ceiling_status(
            value.queue_age_seconds,
            pass_value=config.max_pass_queue_age_seconds,
            watch_value=config.max_watch_queue_age_seconds,
        ),
        "manual_escalation_urgency": _ceiling_status(
            value.manual_escalation_urgency,
            pass_value=config.max_pass_manual_escalation_urgency,
            watch_value=config.max_watch_manual_escalation_urgency,
        ),
    }
    status = _row_status(tuple(component_statuses.values()))
    return _RowValue(
        aggregate_hash=sha256(value.aggregation_key.encode("utf-8")).hexdigest(),
        evidence_maturity_score=value.evidence_maturity_score,
        cost_freshness_score=value.cost_freshness_score,
        specialist_consensus_score=value.specialist_consensus_score,
        source_conflict_pressure=value.source_conflict_pressure,
        queue_age_seconds=value.queue_age_seconds,
        manual_escalation_urgency=value.manual_escalation_urgency,
        priority_exception_score=_priority_exception_score(value=value, config=config),
        status=status,
        reason_codes=_row_reason_codes(status=status, component_statuses=component_statuses),
    )


def _row_from_value(
    *,
    index: int,
    value: _RowValue,
) -> ResearchStrategyManualQueuePriorityExceptionRow:
    return ResearchStrategyManualQueuePriorityExceptionRow(
        aggregate_row_number=_count(index),
        aggregate_hash=value.aggregate_hash,
        evidence_maturity_score=value.evidence_maturity_score,
        cost_freshness_score=value.cost_freshness_score,
        specialist_consensus_score=value.specialist_consensus_score,
        source_conflict_pressure=value.source_conflict_pressure,
        queue_age_seconds=value.queue_age_seconds,
        manual_escalation_urgency=value.manual_escalation_urgency,
        priority_exception_score=value.priority_exception_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _priority_exception_score(
    *,
    value: ResearchStrategyManualQueuePriorityExceptionInput,
    config: ResearchStrategyManualQueuePriorityExceptionConfig,
) -> Decimal:
    return _mean(
        (
            _floor_exception_component(
                value.evidence_maturity_score,
                watch_value=config.min_watch_evidence_maturity_score,
                pass_value=config.min_pass_evidence_maturity_score,
            ),
            _floor_exception_component(
                value.cost_freshness_score,
                watch_value=config.min_watch_cost_freshness_score,
                pass_value=config.min_pass_cost_freshness_score,
            ),
            _floor_exception_component(
                value.specialist_consensus_score,
                watch_value=config.min_watch_specialist_consensus_score,
                pass_value=config.min_pass_specialist_consensus_score,
            ),
            _ceiling_exception_component(
                value.source_conflict_pressure,
                pass_value=config.max_pass_source_conflict_pressure,
                watch_value=config.max_watch_source_conflict_pressure,
            ),
            _ceiling_exception_component(
                value.queue_age_seconds,
                pass_value=config.max_pass_queue_age_seconds,
                watch_value=config.max_watch_queue_age_seconds,
            ),
            _ceiling_exception_component(
                value.manual_escalation_urgency,
                pass_value=config.max_pass_manual_escalation_urgency,
                watch_value=config.max_watch_manual_escalation_urgency,
            ),
        ),
    )


def _floor_exception_component(
    value: Decimal,
    *,
    watch_value: Decimal,
    pass_value: Decimal,
) -> Decimal:
    if value >= pass_value:
        return ZERO
    if value <= watch_value:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((pass_value - value) / (pass_value - watch_value))


def _ceiling_exception_component(
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO
    if value >= watch_value:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize((value - pass_value) / (watch_value - pass_value))


def _floor_status(value: Decimal, *, watch_value: Decimal, pass_value: Decimal) -> str:
    if value < watch_value:
        return "block"
    if value < pass_value:
        return "watch"
    return "pass"


def _ceiling_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value > watch_value:
        return "block"
    if value > pass_value:
        return "watch"
    return "pass"


def _row_status(component_statuses: tuple[str, ...]) -> str:
    if "block" in component_statuses:
        return "block"
    if "watch" in component_statuses:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    component_statuses: dict[str, str],
) -> tuple[str, ...]:
    if status == "pass":
        return ("manual_queue_priority_exception_pass",)
    codes = [f"manual_queue_priority_exception_{status}"]
    for component_name in (
        "evidence_maturity",
        "cost_freshness",
        "specialist_consensus",
        "source_conflict_pressure",
        "queue_age",
        "manual_escalation_urgency",
    ):
        component_status = component_statuses[component_name]
        if component_status != "pass":
            codes.append(f"{component_name}_{component_status}")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyManualQueuePriorityExceptionRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyManualQueuePriorityExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("manual_queue_priority_exception_report_empty",)
    report_status = _report_status(rows)
    codes = [f"manual_queue_priority_exception_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    for component_name, report_reason in (
        ("evidence_maturity_", "evidence_maturity_exception"),
        ("cost_freshness_", "cost_freshness_exception"),
        ("specialist_consensus_", "specialist_consensus_exception"),
        ("source_conflict_pressure_", "source_conflict_pressure_exception"),
        ("queue_age_", "queue_age_exception"),
        ("manual_escalation_urgency_", "manual_escalation_urgency_exception"),
    ):
        if any(code.startswith(component_name) for code in row_codes):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_value_sort_key(value: _RowValue) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[value.status],
        -value.priority_exception_score,
        value.aggregate_hash,
    )


def _row_sort_key(
    row: ResearchStrategyManualQueuePriorityExceptionRow,
) -> tuple[int, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.priority_exception_score,
        row.aggregate_hash,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyManualQueuePriorityExceptionInput],
) -> tuple[ResearchStrategyManualQueuePriorityExceptionInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyManualQueuePriorityExceptionInput:
            raise ValueError(
                "inputs must contain ResearchStrategyManualQueuePriorityExceptionInput values",
            )
        _require_hard_flags("input", value)
        if value.aggregation_key in seen_keys:
            raise ValueError("inputs must not contain duplicate aggregation_key values")
        seen_keys.add(value.aggregation_key)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyManualQueuePriorityExceptionRow],
) -> tuple[ResearchStrategyManualQueuePriorityExceptionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyManualQueuePriorityExceptionRow:
            raise ValueError(
                "rows must contain ResearchStrategyManualQueuePriorityExceptionRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.aggregate_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_hash values")
        seen_hashes.add(row.aggregate_hash)
    return normalized


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyManualQueuePriorityExceptionReasonCodeCount],
) -> tuple[ResearchStrategyManualQueuePriorityExceptionReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyManualQueuePriorityExceptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyManualQueuePriorityExceptionReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _validate_row_consistency(row: ResearchStrategyManualQueuePriorityExceptionRow) -> None:
    if row.status == "pass" and row.reason_codes != (
        "manual_queue_priority_exception_pass",
    ):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyManualQueuePriorityExceptionReport,
) -> None:
    if report.input_row_count != _count(len(report.rows)):
        raise ValueError("input_row_count must match rows")
    if report.input_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be deterministically sorted")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.mean_evidence_maturity_score != _mean(
        tuple(row.evidence_maturity_score for row in report.rows),
    ):
        raise ValueError("mean_evidence_maturity_score must match rows")
    if report.mean_cost_freshness_score != _mean(
        tuple(row.cost_freshness_score for row in report.rows),
    ):
        raise ValueError("mean_cost_freshness_score must match rows")
    if report.mean_specialist_consensus_score != _mean(
        tuple(row.specialist_consensus_score for row in report.rows),
    ):
        raise ValueError("mean_specialist_consensus_score must match rows")
    if report.max_source_conflict_pressure != _maximum(
        tuple(row.source_conflict_pressure for row in report.rows),
    ):
        raise ValueError("max_source_conflict_pressure must match rows")
    if report.mean_queue_age_seconds != _mean(
        tuple(row.queue_age_seconds for row in report.rows),
    ):
        raise ValueError("mean_queue_age_seconds must match rows")
    if report.max_queue_age_seconds != _maximum(
        tuple(row.queue_age_seconds for row in report.rows),
    ):
        raise ValueError("max_queue_age_seconds must match rows")
    if report.max_manual_escalation_urgency != _maximum(
        tuple(row.manual_escalation_urgency for row in report.rows),
    ):
        raise ValueError("max_manual_escalation_urgency must match rows")
    if report.mean_priority_exception_score != _mean(
        tuple(row.priority_exception_score for row in report.rows),
    ):
        raise ValueError("mean_priority_exception_score must match rows")


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyManualQueuePriorityExceptionRow, ...],
) -> tuple[ResearchStrategyManualQueuePriorityExceptionReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchStrategyManualQueuePriorityExceptionReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_ratio(_count(count), total),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _status_count(
    rows: tuple[ResearchStrategyManualQueuePriorityExceptionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _ratio(count: Decimal, total: Decimal) -> Decimal:
    if total == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(count / total)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _require_floor_pair(name: str, watch_value: Decimal, pass_value: Decimal) -> None:
    if watch_value >= pass_value:
        raise ValueError(f"{name} must be less than the matching pass value")


def _require_ceiling_pair(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value >= watch_value:
        raise ValueError(f"{name} must be less than the matching watch value")


def _normalize_probability(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be no greater than one")
    return normalized


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _normalize_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be a {expected_type.__name__}")


def _require_public_string(name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical string")
    _reject_unsafe_text(name, value)


def _require_input_key(name: str, value: str) -> None:
    _require_public_string(name, value)


def _require_reason_code(name: str, value: str) -> None:
    _require_public_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{name} must be a nonempty tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(name, value)
        if value not in allowed_values:
            raise ValueError(f"{name} contains unsupported values")
        normalized.append(value)
    if len(frozenset(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(normalized)


def _require_status(name: str, value: str) -> None:
    if value not in RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_digest(name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a SHA-256 digest")
    allowed = frozenset("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name}.{field_name} must be True")


def _reject_unsafe_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _reject_unsafe_public_payload(name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_text(f"{name}.{field.name}", field.name)
            _reject_unsafe_public_payload(f"{name}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is str:
                _reject_unsafe_text(f"{name}.key", key)
            _reject_unsafe_public_payload(f"{name}.item", item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(f"{name}.item", item)
        return
    if type(value) is str:
        _reject_unsafe_text(name, value)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value")


def _digest_for_value(value: object) -> str:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("digest value must be a mapping")
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _apply_or_verify_digest(value: object) -> None:
    expected = _digest_for_value(value)
    current = getattr(value, "derived_validation_digest")
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
    elif current != expected:
        raise ValueError("derived_validation_digest does not match values")
    _require_digest("derived_validation_digest", getattr(value, "derived_validation_digest"))


def _verify_digest(value: object) -> None:
    if getattr(value, "derived_validation_digest") != _digest_for_value(value):
        raise ValueError("derived_validation_digest does not match values")


def _verify_report_integrity(
    report: ResearchStrategyManualQueuePriorityExceptionReport,
) -> None:
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    for row in payload.get("rows", ()):
        if type(row) is dict:
            _verify_payload_digest(row)
    _verify_payload_digest(payload)


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    current = payload.get("derived_validation_digest")
    if type(current) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", current)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload_without_digest),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    if sha256(encoded).hexdigest() != current:
        raise ValueError("derived_validation_digest does not match values")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_MANUAL_QUEUE_PRIORITY_EXCEPTION_STATUSES",
    "ResearchStrategyManualQueuePriorityExceptionConfig",
    "ResearchStrategyManualQueuePriorityExceptionInput",
    "ResearchStrategyManualQueuePriorityExceptionReasonCodeCount",
    "ResearchStrategyManualQueuePriorityExceptionRow",
    "ResearchStrategyManualQueuePriorityExceptionReport",
    "build_research_strategy_manual_queue_priority_exception_report",
    "research_strategy_manual_queue_priority_exception_report_payload",
    "research_strategy_manual_queue_priority_exception_report_digest",
)
