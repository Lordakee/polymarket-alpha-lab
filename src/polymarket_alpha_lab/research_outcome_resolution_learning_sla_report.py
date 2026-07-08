from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_OUTCOME_RESOLUTION_LEARNING_SLA_CONFIG_VERSION",
    "ResearchOutcomeResolutionLearningSlaAggregate",
    "ResearchOutcomeResolutionLearningSlaConfig",
    "ResearchOutcomeResolutionLearningSlaReport",
    "ResearchOutcomeResolutionLearningSlaRow",
    "build_research_outcome_resolution_learning_sla_report",
    "research_outcome_resolution_learning_sla_report_payload",
    "validate_research_outcome_resolution_learning_sla_public_payload",
)


DEFAULT_RESEARCH_OUTCOME_RESOLUTION_LEARNING_SLA_CONFIG_VERSION = (
    "research-outcome-resolution-learning-sla-v1"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
HEX_CHARS = frozenset("0123456789abcdef")
STATUS_VALUES = ("block", "watch", "pass")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
SAFE_LABEL_PREFIXES = (
    "aggregate:all",
    "aggregate:cohort:",
    "aggregate:domain:",
    "aggregate:resolution_window:",
    "aggregate:source_family:",
    "aggregate:team:",
)
CLEAR_REASON_CODE = "learning_sla_clear"
EMPTY_REASON_CODE = "no_learning_aggregates"
READY_REASON_CODE = "learning_sla_ready"
REASON_CODE_WEIGHT = {
    "missing_memory_writeback_age": 0,
    "no_resolved_outcomes": 1,
    "memory_writeback_urgent": 2,
    "settlement_evidence_stale": 3,
    "calibration_feedback_incomplete": 4,
    "error_taxonomy_coverage_gap": 5,
    CLEAR_REASON_CODE: 6,
    READY_REASON_CODE: 7,
    EMPTY_REASON_CODE: 8,
}
UNSAFE_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("data", "base"),
        ("net", "work"),
        ("wal", "let"),
        ("ac", "count"),
        ("bro", "ker"),
        ("ord", "er"),
        ("sub", "mit"),
        ("can", "cel"),
        ("sig", "ning"),
        ("tra", "de"),
        ("pos", "ition"),
    )
)


@dataclass(frozen=True)
class ResearchOutcomeResolutionLearningSlaConfig:
    config_version: str = DEFAULT_RESEARCH_OUTCOME_RESOLUTION_LEARNING_SLA_CONFIG_VERSION
    settlement_evidence_stale_after_seconds: Decimal = Decimal("86400.000000")
    calibration_feedback_min_ratio: Decimal = Decimal("0.950000")
    error_taxonomy_min_ratio: Decimal = Decimal("0.950000")
    memory_writeback_due_after_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOutcomeResolutionLearningSlaConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "settlement_evidence_stale_after_seconds",
            "memory_writeback_due_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_feedback_min_ratio",
            "error_taxonomy_min_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchOutcomeResolutionLearningSlaAggregate:
    aggregate_label: str
    resolved_outcome_count: Decimal
    settlement_evidence_checked_at: datetime
    calibration_feedback_complete_count: Decimal
    error_taxonomy_mapped_count: Decimal
    memory_writeback_pending_count: Decimal
    oldest_memory_writeback_pending_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchOutcomeResolutionLearningSlaAggregate,
            "aggregate",
        )
        _require_aggregate_label("aggregate_label", self.aggregate_label)
        object.__setattr__(
            self,
            "settlement_evidence_checked_at",
            _as_utc("settlement_evidence_checked_at", self.settlement_evidence_checked_at),
        )
        for field_name in (
            "resolved_outcome_count",
            "calibration_feedback_complete_count",
            "error_taxonomy_mapped_count",
            "memory_writeback_pending_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_memory_writeback_pending_at is not None:
            object.__setattr__(
                self,
                "oldest_memory_writeback_pending_at",
                _as_utc(
                    "oldest_memory_writeback_pending_at",
                    self.oldest_memory_writeback_pending_at,
                ),
            )
        if self.calibration_feedback_complete_count > self.resolved_outcome_count:
            raise ValueError(
                "calibration_feedback_complete_count must not exceed "
                "resolved_outcome_count",
            )
        if self.error_taxonomy_mapped_count > self.resolved_outcome_count:
            raise ValueError(
                "error_taxonomy_mapped_count must not exceed resolved_outcome_count",
            )
        if (
            self.memory_writeback_pending_count == ZERO
            and self.oldest_memory_writeback_pending_at is not None
        ):
            raise ValueError(
                "oldest_memory_writeback_pending_at requires pending writebacks",
            )
        _require_hard_flags("aggregate", self)


@dataclass(frozen=True)
class ResearchOutcomeResolutionLearningSlaRow:
    aggregate_label: str
    resolved_outcome_count: Decimal
    settlement_evidence_checked_at: datetime
    settlement_evidence_age_seconds: Decimal
    calibration_feedback_complete_count: Decimal
    calibration_feedback_completion_ratio: Decimal
    error_taxonomy_mapped_count: Decimal
    error_taxonomy_coverage_ratio: Decimal
    memory_writeback_pending_count: Decimal
    oldest_memory_writeback_pending_at: datetime | None
    memory_writeback_urgency_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOutcomeResolutionLearningSlaRow, "row")
        _require_aggregate_label("aggregate_label", self.aggregate_label)
        object.__setattr__(
            self,
            "settlement_evidence_checked_at",
            _as_utc("settlement_evidence_checked_at", self.settlement_evidence_checked_at),
        )
        for field_name in (
            "resolved_outcome_count",
            "calibration_feedback_complete_count",
            "error_taxonomy_mapped_count",
            "memory_writeback_pending_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_evidence_age_seconds",
            "memory_writeback_urgency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_feedback_completion_ratio",
            "error_taxonomy_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_memory_writeback_pending_at is not None:
            object.__setattr__(
                self,
                "oldest_memory_writeback_pending_at",
                _as_utc(
                    "oldest_memory_writeback_pending_at",
                    self.oldest_memory_writeback_pending_at,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        _validate_row_materialized_fields(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchOutcomeResolutionLearningSlaReport:
    generated_at: datetime
    config_version: str
    aggregate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    resolved_outcome_count: Decimal
    stale_settlement_evidence_count: Decimal
    incomplete_calibration_feedback_count: Decimal
    insufficient_error_taxonomy_coverage_count: Decimal
    urgent_memory_writeback_count: Decimal
    missing_memory_writeback_age_count: Decimal
    min_calibration_feedback_completion_ratio: Decimal
    min_error_taxonomy_coverage_ratio: Decimal
    max_settlement_evidence_age_seconds: Decimal
    max_memory_writeback_urgency_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchOutcomeResolutionLearningSlaRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOutcomeResolutionLearningSlaReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "aggregate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "resolved_outcome_count",
            "stale_settlement_evidence_count",
            "incomplete_calibration_feedback_count",
            "insufficient_error_taxonomy_coverage_count",
            "urgent_memory_writeback_count",
            "missing_memory_writeback_age_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_calibration_feedback_completion_ratio",
            "min_error_taxonomy_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_settlement_evidence_age_seconds",
            "max_memory_writeback_urgency_seconds",
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
            _require_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_outcome_resolution_learning_sla_report(
    aggregates: Iterable[ResearchOutcomeResolutionLearningSlaAggregate],
    *,
    config: ResearchOutcomeResolutionLearningSlaConfig,
    generated_at: datetime,
) -> ResearchOutcomeResolutionLearningSlaReport:
    if type(config) is not ResearchOutcomeResolutionLearningSlaConfig:
        raise ValueError("config must be a ResearchOutcomeResolutionLearningSlaConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_aggregate(
                    aggregate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for aggregate in _normalize_aggregates(aggregates)
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.status for row in rows))
    return ResearchOutcomeResolutionLearningSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        aggregate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        resolved_outcome_count=_sum_decimal(
            tuple(row.resolved_outcome_count for row in rows),
        ),
        stale_settlement_evidence_count=_reason_count(
            rows,
            "settlement_evidence_stale",
        ),
        incomplete_calibration_feedback_count=_reason_count(
            rows,
            "calibration_feedback_incomplete",
        ),
        insufficient_error_taxonomy_coverage_count=_reason_count(
            rows,
            "error_taxonomy_coverage_gap",
        ),
        urgent_memory_writeback_count=_reason_count(rows, "memory_writeback_urgent"),
        missing_memory_writeback_age_count=_reason_count(
            rows,
            "missing_memory_writeback_age",
        ),
        min_calibration_feedback_completion_ratio=_min_decimal(
            tuple(row.calibration_feedback_completion_ratio for row in rows),
        ),
        min_error_taxonomy_coverage_ratio=_min_decimal(
            tuple(row.error_taxonomy_coverage_ratio for row in rows),
        ),
        max_settlement_evidence_age_seconds=_max_decimal(
            tuple(row.settlement_evidence_age_seconds for row in rows),
        ),
        max_memory_writeback_urgency_seconds=_max_decimal(
            tuple(row.memory_writeback_urgency_seconds for row in rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_outcome_resolution_learning_sla_report_payload(
    report: ResearchOutcomeResolutionLearningSlaReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchOutcomeResolutionLearningSlaReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        validate_research_outcome_resolution_learning_sla_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_research_outcome_resolution_learning_sla_public_payload(report)
        return _json_ready(report)
    raise ValueError("report must be a ResearchOutcomeResolutionLearningSlaReport")


def validate_research_outcome_resolution_learning_sla_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be an object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_values(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    supplied_digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _row_from_aggregate(
    aggregate: ResearchOutcomeResolutionLearningSlaAggregate,
    *,
    config: ResearchOutcomeResolutionLearningSlaConfig,
    generated_at: datetime,
) -> ResearchOutcomeResolutionLearningSlaRow:
    _require_not_future(
        "settlement_evidence_checked_at",
        aggregate.settlement_evidence_checked_at,
        generated_at,
    )
    if aggregate.oldest_memory_writeback_pending_at is not None:
        _require_not_future(
            "oldest_memory_writeback_pending_at",
            aggregate.oldest_memory_writeback_pending_at,
            generated_at,
        )
    settlement_evidence_age_seconds = _elapsed_seconds(
        aggregate.settlement_evidence_checked_at,
        generated_at,
    )
    calibration_feedback_completion_ratio = _ratio_decimal(
        aggregate.calibration_feedback_complete_count,
        aggregate.resolved_outcome_count,
    )
    error_taxonomy_coverage_ratio = _ratio_decimal(
        aggregate.error_taxonomy_mapped_count,
        aggregate.resolved_outcome_count,
    )
    memory_writeback_urgency_seconds = (
        _elapsed_seconds(aggregate.oldest_memory_writeback_pending_at, generated_at)
        if aggregate.oldest_memory_writeback_pending_at is not None
        else ZERO
    )
    reason_codes = _row_reason_codes(
        aggregate=aggregate,
        settlement_evidence_age_seconds=settlement_evidence_age_seconds,
        calibration_feedback_completion_ratio=calibration_feedback_completion_ratio,
        error_taxonomy_coverage_ratio=error_taxonomy_coverage_ratio,
        memory_writeback_urgency_seconds=memory_writeback_urgency_seconds,
        config=config,
    )
    return ResearchOutcomeResolutionLearningSlaRow(
        aggregate_label=aggregate.aggregate_label,
        resolved_outcome_count=aggregate.resolved_outcome_count,
        settlement_evidence_checked_at=aggregate.settlement_evidence_checked_at,
        settlement_evidence_age_seconds=settlement_evidence_age_seconds,
        calibration_feedback_complete_count=aggregate.calibration_feedback_complete_count,
        calibration_feedback_completion_ratio=calibration_feedback_completion_ratio,
        error_taxonomy_mapped_count=aggregate.error_taxonomy_mapped_count,
        error_taxonomy_coverage_ratio=error_taxonomy_coverage_ratio,
        memory_writeback_pending_count=aggregate.memory_writeback_pending_count,
        oldest_memory_writeback_pending_at=aggregate.oldest_memory_writeback_pending_at,
        memory_writeback_urgency_seconds=memory_writeback_urgency_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    aggregate: ResearchOutcomeResolutionLearningSlaAggregate,
    settlement_evidence_age_seconds: Decimal,
    calibration_feedback_completion_ratio: Decimal,
    error_taxonomy_coverage_ratio: Decimal,
    memory_writeback_urgency_seconds: Decimal,
    config: ResearchOutcomeResolutionLearningSlaConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if aggregate.memory_writeback_pending_count > ZERO:
        if aggregate.oldest_memory_writeback_pending_at is None:
            reason_codes.append("missing_memory_writeback_age")
        elif memory_writeback_urgency_seconds > config.memory_writeback_due_after_seconds:
            reason_codes.append("memory_writeback_urgent")
    if aggregate.resolved_outcome_count == ZERO:
        reason_codes.append("no_resolved_outcomes")
        return tuple(sorted(reason_codes, key=_reason_code_key))
    if settlement_evidence_age_seconds > config.settlement_evidence_stale_after_seconds:
        reason_codes.append("settlement_evidence_stale")
    if calibration_feedback_completion_ratio < config.calibration_feedback_min_ratio:
        reason_codes.append("calibration_feedback_incomplete")
    if error_taxonomy_coverage_ratio < config.error_taxonomy_min_ratio:
        reason_codes.append("error_taxonomy_coverage_gap")
    if not reason_codes:
        return (CLEAR_REASON_CODE,)
    return tuple(sorted(reason_codes, key=_reason_code_key))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "missing_memory_writeback_age" in reason_codes
        or "no_resolved_outcomes" in reason_codes
        or "memory_writeback_urgent" in reason_codes
    ):
        return "block"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "pass"
    return "watch"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchOutcomeResolutionLearningSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    }
    if not reason_codes:
        return (READY_REASON_CODE,)
    return tuple(sorted(reason_codes, key=_reason_code_key))


def _row_sort_key(row: ResearchOutcomeResolutionLearningSlaRow) -> tuple[int, str]:
    return (STATUS_WEIGHT[row.status], row.aggregate_label)


def _reason_code_key(reason_code: str) -> int:
    return REASON_CODE_WEIGHT[reason_code]


def _status_count(
    rows: tuple[ResearchOutcomeResolutionLearningSlaRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchOutcomeResolutionLearningSlaRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a non-negative int")
    return Decimal(value).quantize(QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM)


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end must not precede start")
    delta = end - start
    microseconds = (
        ((delta.days * 24 * 60 * 60) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    return (Decimal(microseconds) / MICROSECONDS_PER_SECOND).quantize(QUANTUM)


def _normalize_aggregates(
    aggregates: Iterable[ResearchOutcomeResolutionLearningSlaAggregate],
) -> tuple[ResearchOutcomeResolutionLearningSlaAggregate, ...]:
    if isinstance(aggregates, (str, bytes)):
        raise ValueError("aggregates must be iterable")
    try:
        normalized = tuple(aggregates)
    except TypeError as exc:
        raise ValueError("aggregates must be iterable") from exc
    for aggregate in normalized:
        if type(aggregate) is not ResearchOutcomeResolutionLearningSlaAggregate:
            raise ValueError(
                "aggregates must contain ResearchOutcomeResolutionLearningSlaAggregate",
            )
    return normalized


def _require_rows(
    rows: tuple[ResearchOutcomeResolutionLearningSlaRow, ...],
) -> tuple[ResearchOutcomeResolutionLearningSlaRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in normalized:
        if type(row) is not ResearchOutcomeResolutionLearningSlaRow:
            raise ValueError("rows must contain ResearchOutcomeResolutionLearningSlaRow")
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic status sort")
    return normalized


def _require_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be a tuple")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple") from exc
    if not reason_codes:
        raise ValueError("reason_codes must include at least one code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_string("reason_codes", reason_code)
        if reason_code not in REASON_CODE_WEIGHT:
            raise ValueError("reason_codes include an unknown code")
    return tuple(sorted(reason_codes, key=_reason_code_key))


def _validate_row_materialized_fields(
    row: ResearchOutcomeResolutionLearningSlaRow,
) -> None:
    if row.calibration_feedback_complete_count > row.resolved_outcome_count:
        raise ValueError(
            "calibration_feedback_complete_count must not exceed resolved_outcome_count",
        )
    if row.error_taxonomy_mapped_count > row.resolved_outcome_count:
        raise ValueError("error_taxonomy_mapped_count must not exceed resolved_outcome_count")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        row.memory_writeback_pending_count == ZERO
        and row.oldest_memory_writeback_pending_at is not None
    ):
        raise ValueError("oldest_memory_writeback_pending_at requires pending writebacks")
    if (
        row.memory_writeback_pending_count > ZERO
        and row.oldest_memory_writeback_pending_at is None
        and "missing_memory_writeback_age" not in row.reason_codes
    ):
        raise ValueError("missing memory writeback age must be flagged")


def _validate_report_materialized_fields(
    report: ResearchOutcomeResolutionLearningSlaReport,
) -> None:
    rows = report.rows
    if report.aggregate_count != _count(len(rows)):
        raise ValueError("aggregate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.resolved_outcome_count != _sum_decimal(
        tuple(row.resolved_outcome_count for row in rows),
    ):
        raise ValueError("resolved_outcome_count must match rows")
    if report.stale_settlement_evidence_count != _reason_count(
        rows,
        "settlement_evidence_stale",
    ):
        raise ValueError("stale_settlement_evidence_count must match rows")
    if report.incomplete_calibration_feedback_count != _reason_count(
        rows,
        "calibration_feedback_incomplete",
    ):
        raise ValueError("incomplete_calibration_feedback_count must match rows")
    if report.insufficient_error_taxonomy_coverage_count != _reason_count(
        rows,
        "error_taxonomy_coverage_gap",
    ):
        raise ValueError("insufficient_error_taxonomy_coverage_count must match rows")
    if report.urgent_memory_writeback_count != _reason_count(
        rows,
        "memory_writeback_urgent",
    ):
        raise ValueError("urgent_memory_writeback_count must match rows")
    if report.missing_memory_writeback_age_count != _reason_count(
        rows,
        "missing_memory_writeback_age",
    ):
        raise ValueError("missing_memory_writeback_age_count must match rows")
    if report.min_calibration_feedback_completion_ratio != _min_decimal(
        tuple(row.calibration_feedback_completion_ratio for row in rows),
    ):
        raise ValueError("min_calibration_feedback_completion_ratio must match rows")
    if report.min_error_taxonomy_coverage_ratio != _min_decimal(
        tuple(row.error_taxonomy_coverage_ratio for row in rows),
    ):
        raise ValueError("min_error_taxonomy_coverage_ratio must match rows")
    if report.max_settlement_evidence_age_seconds != _max_decimal(
        tuple(row.settlement_evidence_age_seconds for row in rows),
    ):
        raise ValueError("max_settlement_evidence_age_seconds must match rows")
    if report.max_memory_writeback_urgency_seconds != _max_decimal(
        tuple(row.memory_writeback_urgency_seconds for row in rows),
    ):
        raise ValueError("max_memory_writeback_urgency_seconds must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return value.quantize(QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of {STATUS_VALUES!r}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be a non-empty stripped string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains an unsafe public fragment")


def _require_aggregate_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not any(str(value).startswith(prefix) for prefix in SAFE_LABEL_PREFIXES):
        raise ValueError(f"{field_name} must be aggregate-safe")
    if str(value) == "aggregate:all":
        return
    if str(value).count(":") != 2:
        raise ValueError(f"{field_name} must be aggregate-safe")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exact")


def _require_not_future(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchOutcomeResolutionLearningSlaReport,
) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        _strip_digest(payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


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


def _json_ready_without_digest(
    report: ResearchOutcomeResolutionLearningSlaReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return format(value.quantize(QUANTUM), "f")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_FRAGMENTS)
