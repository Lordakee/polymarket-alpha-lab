"""Pure aggregate retrieval completeness gate report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_RETRIEVAL_COMPLETENESS_GATE_REPORT_CONFIG_VERSION = (
    "research-source-retrieval-completeness-gate-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PRESSURE_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("raw", "_", "url")),
    "".join(("raw", "-", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("ques", "tion")),
    "".join(("http", "://")),
    "".join(("https", "://")),
    "".join(("www", ".")),
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("tra", "de")),
    "".join(("tra", "ding")),
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RETRIEVAL_COMPLETENESS_GATE_REPORT_CONFIG_VERSION",
    "ResearchSourceRetrievalCompletenessClassRow",
    "ResearchSourceRetrievalCompletenessGateConfig",
    "ResearchSourceRetrievalCompletenessGateReport",
    "ResearchSourceRetrievalSourceClassAggregate",
    "build_research_source_retrieval_completeness_gate_report",
    "research_source_retrieval_completeness_gate_report_payload",
    "validate_research_source_retrieval_completeness_gate_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceRetrievalCompletenessGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RETRIEVAL_COMPLETENESS_GATE_REPORT_CONFIG_VERSION
    )
    minimum_class_coverage_ratio: Decimal = Decimal("1.000000")
    block_class_coverage_ratio: Decimal = Decimal("0.500000")
    watch_stale_source_ratio: Decimal = Decimal("0.250000")
    block_stale_source_ratio: Decimal = Decimal("0.600000")
    watch_failed_retrieval_ratio: Decimal = Decimal("0.250000")
    block_failed_retrieval_ratio: Decimal = Decimal("0.500000")
    watch_recheck_urgency_ratio: Decimal = Decimal("0.250000")
    block_recheck_urgency_ratio: Decimal = Decimal("0.600000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalCompletenessGateConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceRetrievalCompletenessGateConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_class_coverage_ratio",
            "block_class_coverage_ratio",
            "watch_stale_source_ratio",
            "block_stale_source_ratio",
            "watch_failed_retrieval_ratio",
            "block_failed_retrieval_ratio",
            "watch_recheck_urgency_ratio",
            "block_recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.minimum_class_coverage_ratio <= _ZERO:
            raise ValueError("minimum_class_coverage_ratio must be positive")
        if self.block_class_coverage_ratio >= self.minimum_class_coverage_ratio:
            raise ValueError(
                "block_class_coverage_ratio must be below minimum_class_coverage_ratio",
            )
        _require_pressure_threshold_pair(
            "watch_stale_source_ratio",
            self.watch_stale_source_ratio,
            "block_stale_source_ratio",
            self.block_stale_source_ratio,
        )
        _require_pressure_threshold_pair(
            "watch_failed_retrieval_ratio",
            self.watch_failed_retrieval_ratio,
            "block_failed_retrieval_ratio",
            self.block_failed_retrieval_ratio,
        )
        _require_pressure_threshold_pair(
            "watch_recheck_urgency_ratio",
            self.watch_recheck_urgency_ratio,
            "block_recheck_urgency_ratio",
            self.block_recheck_urgency_ratio,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchSourceRetrievalSourceClassAggregate:
    source_class: str
    required_source_count: Decimal
    retrieval_attempt_count: Decimal
    retrieved_source_count: Decimal
    stale_source_count: Decimal = _ZERO
    failed_retrieval_count: Decimal = _ZERO
    pending_recheck_count: Decimal = _ZERO
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalSourceClassAggregate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("source_class", self.source_class)
        for field_name in (
            "required_source_count",
            "retrieval_attempt_count",
            "retrieved_source_count",
            "stale_source_count",
            "failed_retrieval_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_source_class_aggregate_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("source_class", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchSourceRetrievalCompletenessClassRow:
    source_class: str
    required_source_count: Decimal
    retrieval_attempt_count: Decimal
    retrieved_source_count: Decimal
    stale_source_count: Decimal
    failed_retrieval_count: Decimal
    pending_recheck_count: Decimal
    source_class_covered: bool
    retrieval_coverage_ratio: Decimal
    stale_source_ratio: Decimal
    failed_retrieval_pressure_ratio: Decimal
    recheck_urgency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalCompletenessClassRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("source_class", self.source_class)
        for field_name in (
            "required_source_count",
            "retrieval_attempt_count",
            "retrieved_source_count",
            "stale_source_count",
            "failed_retrieval_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if type(self.source_class_covered) is not bool:
            raise ValueError("source_class_covered must be a bool")
        for field_name in (
            "retrieval_coverage_ratio",
            "stale_source_ratio",
            "failed_retrieval_pressure_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_class_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchSourceRetrievalCompletenessGateReport:
    generated_at: datetime
    config_version: str
    source_class_count: Decimal
    covered_source_class_count: Decimal
    required_source_count: Decimal
    retrieval_attempt_count: Decimal
    retrieved_source_count: Decimal
    stale_source_count: Decimal
    failed_retrieval_count: Decimal
    pending_recheck_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    source_class_coverage_ratio: Decimal
    retrieval_coverage_ratio: Decimal
    stale_source_ratio: Decimal
    failed_retrieval_pressure_ratio: Decimal
    recheck_urgency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceRetrievalCompletenessClassRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRetrievalCompletenessGateReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceRetrievalCompletenessGateReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_class_count",
            "covered_source_class_count",
            "required_source_count",
            "retrieval_attempt_count",
            "retrieved_source_count",
            "stale_source_count",
            "failed_retrieval_count",
            "pending_recheck_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_coverage_ratio",
            "retrieval_coverage_ratio",
            "stale_source_ratio",
            "failed_retrieval_pressure_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_source_retrieval_completeness_gate_report(
    source_classes: Iterable[ResearchSourceRetrievalSourceClassAggregate],
    *,
    config: ResearchSourceRetrievalCompletenessGateConfig,
    generated_at: datetime,
) -> ResearchSourceRetrievalCompletenessGateReport:
    if type(config) is not ResearchSourceRetrievalCompletenessGateConfig:
        raise ValueError(
            "config must be a ResearchSourceRetrievalCompletenessGateConfig",
        )
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    aggregates = _normalize_source_class_aggregates(source_classes)
    rows = tuple(
        _row_from_source_class_aggregate(value, config=config) for value in aggregates
    )

    source_class_count = _decimal_count(len(rows))
    covered_source_class_count = _count_rows_by_coverage(rows)
    required_source_count = _sum_counts(tuple(row.required_source_count for row in rows))
    retrieval_attempt_count = _sum_counts(
        tuple(row.retrieval_attempt_count for row in rows),
    )
    retrieved_source_count = _sum_counts(
        tuple(row.retrieved_source_count for row in rows),
    )
    stale_source_count = _sum_counts(tuple(row.stale_source_count for row in rows))
    failed_retrieval_count = _sum_counts(
        tuple(row.failed_retrieval_count for row in rows),
    )
    pending_recheck_count = _sum_counts(
        tuple(row.pending_recheck_count for row in rows),
    )
    pressure_statuses = _aggregate_pressure_statuses(
        config=config,
        source_class_coverage_ratio=_ratio(
            covered_source_class_count,
            source_class_count,
        ),
        stale_source_ratio=_ratio(stale_source_count, retrieved_source_count),
        failed_retrieval_pressure_ratio=_ratio(
            failed_retrieval_count,
            retrieval_attempt_count,
        ),
        recheck_urgency_ratio=_ratio(pending_recheck_count, retrieved_source_count),
        has_rows=bool(rows),
    )
    reason_codes = _report_reason_codes(rows, pressure_statuses)

    return ResearchSourceRetrievalCompletenessGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_class_count=source_class_count,
        covered_source_class_count=covered_source_class_count,
        required_source_count=required_source_count,
        retrieval_attempt_count=retrieval_attempt_count,
        retrieved_source_count=retrieved_source_count,
        stale_source_count=stale_source_count,
        failed_retrieval_count=failed_retrieval_count,
        pending_recheck_count=pending_recheck_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        source_class_coverage_ratio=pressure_statuses.source_class_coverage_ratio,
        retrieval_coverage_ratio=_bounded_ratio(
            retrieved_source_count,
            required_source_count,
        ),
        stale_source_ratio=pressure_statuses.stale_source_ratio,
        failed_retrieval_pressure_ratio=(
            pressure_statuses.failed_retrieval_pressure_ratio
        ),
        recheck_urgency_ratio=pressure_statuses.recheck_urgency_ratio,
        status=_summary_status(rows, pressure_statuses),
        reason_codes=reason_codes,
        rows=rows,
    )


def research_source_retrieval_completeness_gate_report_payload(
    report: ResearchSourceRetrievalCompletenessGateReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceRetrievalCompletenessGateReport:
        raise ValueError(
            "report must be a ResearchSourceRetrievalCompletenessGateReport",
        )
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_research_source_retrieval_completeness_gate_report_payload(payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def validate_research_source_retrieval_completeness_gate_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


@dataclass(frozen=True)
class _AggregatePressureStatuses:
    source_class_coverage_ratio: Decimal
    stale_source_ratio: Decimal
    failed_retrieval_pressure_ratio: Decimal
    recheck_urgency_ratio: Decimal
    source_class_coverage_status: str
    stale_source_concentration_status: str
    failed_retrieval_pressure_status: str
    recheck_urgency_status: str


def _row_from_source_class_aggregate(
    value: ResearchSourceRetrievalSourceClassAggregate,
    *,
    config: ResearchSourceRetrievalCompletenessGateConfig,
) -> ResearchSourceRetrievalCompletenessClassRow:
    source_class_covered = value.retrieved_source_count >= value.required_source_count
    retrieval_coverage_ratio = _bounded_ratio(
        value.retrieved_source_count,
        value.required_source_count,
    )
    stale_source_ratio = _ratio(value.stale_source_count, value.retrieved_source_count)
    failed_retrieval_pressure_ratio = _ratio(
        value.failed_retrieval_count,
        value.retrieval_attempt_count,
    )
    recheck_urgency_ratio = _ratio(
        value.pending_recheck_count,
        value.retrieved_source_count,
    )
    pressure_statuses = _class_pressure_statuses(
        config=config,
        retrieval_coverage_ratio=retrieval_coverage_ratio,
        stale_source_ratio=stale_source_ratio,
        failed_retrieval_pressure_ratio=failed_retrieval_pressure_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
    )
    return ResearchSourceRetrievalCompletenessClassRow(
        source_class=value.source_class,
        required_source_count=value.required_source_count,
        retrieval_attempt_count=value.retrieval_attempt_count,
        retrieved_source_count=value.retrieved_source_count,
        stale_source_count=value.stale_source_count,
        failed_retrieval_count=value.failed_retrieval_count,
        pending_recheck_count=value.pending_recheck_count,
        source_class_covered=source_class_covered,
        retrieval_coverage_ratio=retrieval_coverage_ratio,
        stale_source_ratio=stale_source_ratio,
        failed_retrieval_pressure_ratio=failed_retrieval_pressure_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        status=_worst_status(pressure_statuses),
        reason_codes=_class_reason_codes(pressure_statuses),
    )


def _class_pressure_statuses(
    *,
    config: ResearchSourceRetrievalCompletenessGateConfig,
    retrieval_coverage_ratio: Decimal,
    stale_source_ratio: Decimal,
    failed_retrieval_pressure_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
) -> _AggregatePressureStatuses:
    return _AggregatePressureStatuses(
        source_class_coverage_ratio=retrieval_coverage_ratio,
        stale_source_ratio=stale_source_ratio,
        failed_retrieval_pressure_ratio=failed_retrieval_pressure_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        source_class_coverage_status=_coverage_status(
            retrieval_coverage_ratio,
            config=config,
        ),
        stale_source_concentration_status=_upper_pressure_status(
            stale_source_ratio,
            watch_threshold=config.watch_stale_source_ratio,
            block_threshold=config.block_stale_source_ratio,
        ),
        failed_retrieval_pressure_status=_upper_pressure_status(
            failed_retrieval_pressure_ratio,
            watch_threshold=config.watch_failed_retrieval_ratio,
            block_threshold=config.block_failed_retrieval_ratio,
        ),
        recheck_urgency_status=_upper_pressure_status(
            recheck_urgency_ratio,
            watch_threshold=config.watch_recheck_urgency_ratio,
            block_threshold=config.block_recheck_urgency_ratio,
        ),
    )


def _aggregate_pressure_statuses(
    *,
    config: ResearchSourceRetrievalCompletenessGateConfig,
    source_class_coverage_ratio: Decimal,
    stale_source_ratio: Decimal,
    failed_retrieval_pressure_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
    has_rows: bool,
) -> _AggregatePressureStatuses:
    return _AggregatePressureStatuses(
        source_class_coverage_ratio=source_class_coverage_ratio,
        stale_source_ratio=stale_source_ratio,
        failed_retrieval_pressure_ratio=failed_retrieval_pressure_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        source_class_coverage_status=(
            _coverage_status(source_class_coverage_ratio, config=config)
            if has_rows
            else "block"
        ),
        stale_source_concentration_status=_upper_pressure_status(
            stale_source_ratio,
            watch_threshold=config.watch_stale_source_ratio,
            block_threshold=config.block_stale_source_ratio,
        ),
        failed_retrieval_pressure_status=_upper_pressure_status(
            failed_retrieval_pressure_ratio,
            watch_threshold=config.watch_failed_retrieval_ratio,
            block_threshold=config.block_failed_retrieval_ratio,
        ),
        recheck_urgency_status=_upper_pressure_status(
            recheck_urgency_ratio,
            watch_threshold=config.watch_recheck_urgency_ratio,
            block_threshold=config.block_recheck_urgency_ratio,
        ),
    )


def _coverage_status(
    value: Decimal,
    *,
    config: ResearchSourceRetrievalCompletenessGateConfig,
) -> str:
    if value < config.block_class_coverage_ratio:
        return "block"
    if value < config.minimum_class_coverage_ratio:
        return "watch"
    return "pass"


def _upper_pressure_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return "block"
    if value >= watch_threshold:
        return "watch"
    return "pass"


def _worst_status(pressure_statuses: _AggregatePressureStatuses) -> str:
    statuses = (
        pressure_statuses.source_class_coverage_status,
        pressure_statuses.stale_source_concentration_status,
        pressure_statuses.failed_retrieval_pressure_status,
        pressure_statuses.recheck_urgency_status,
    )
    return max(statuses, key=lambda status: _PRESSURE_STATUS_RANK[status])


def _summary_status(
    rows: tuple[ResearchSourceRetrievalCompletenessClassRow, ...],
    pressure_statuses: _AggregatePressureStatuses,
) -> str:
    if not rows:
        return "block"
    return _worst_status(pressure_statuses)


def _class_reason_codes(
    pressure_statuses: _AggregatePressureStatuses,
) -> tuple[str, ...]:
    return (
        "failed_retrieval_pressure_"
        + pressure_statuses.failed_retrieval_pressure_status,
        "recheck_urgency_" + pressure_statuses.recheck_urgency_status,
        "source_class_coverage_" + pressure_statuses.source_class_coverage_status,
        "stale_source_concentration_"
        + pressure_statuses.stale_source_concentration_status,
    )


def _report_reason_codes(
    rows: tuple[ResearchSourceRetrievalCompletenessClassRow, ...],
    pressure_statuses: _AggregatePressureStatuses,
) -> tuple[str, ...]:
    if not rows:
        return ("no_retrieval_source_classes",)
    if _worst_status(pressure_statuses) == "pass":
        return ("retrieval_completeness_pass",)
    reason_codes = tuple(
        reason_code
        for reason_code in _class_reason_codes(pressure_statuses)
        if not reason_code.endswith("_pass")
    )
    if not reason_codes:
        return ("retrieval_completeness_watch",)
    return reason_codes


def _normalize_source_class_aggregates(
    values: Iterable[ResearchSourceRetrievalSourceClassAggregate],
) -> tuple[ResearchSourceRetrievalSourceClassAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("source_classes must be an iterable")
    try:
        aggregates = tuple(values)
    except TypeError as exc:
        raise ValueError("source_classes must be an iterable") from exc
    for value in aggregates:
        if type(value) is not ResearchSourceRetrievalSourceClassAggregate:
            raise ValueError(
                "source_classes must contain "
                "ResearchSourceRetrievalSourceClassAggregate values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("source_class", value)
        _require_or_set_digest(value)
    rows = tuple(sorted(aggregates, key=lambda value: value.source_class))
    if len({value.source_class for value in rows}) != len(rows):
        raise ValueError("source_classes must be unique")
    return rows


def _normalize_rows(
    values: Iterable[ResearchSourceRetrievalCompletenessClassRow],
) -> tuple[ResearchSourceRetrievalCompletenessClassRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain completeness class rows")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain completeness class rows") from exc
    for row in rows:
        if type(row) is not ResearchSourceRetrievalCompletenessClassRow:
            raise ValueError("rows must contain completeness class rows")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.source_class))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by source_class")
    if len({row.source_class for row in rows}) != len(rows):
        raise ValueError("rows must be unique")
    return rows


def _validate_source_class_aggregate_consistency(
    value: ResearchSourceRetrievalSourceClassAggregate,
) -> None:
    if value.required_source_count <= _ZERO:
        raise ValueError("required_source_count must be positive")
    if value.retrieved_source_count > value.retrieval_attempt_count:
        raise ValueError(
            "retrieved_source_count must be at most retrieval_attempt_count",
        )
    if (
        value.retrieved_source_count + value.failed_retrieval_count
        > value.retrieval_attempt_count
    ):
        raise ValueError(
            "failed_retrieval_count must fit within retrieval attempts",
        )
    if value.stale_source_count > value.retrieved_source_count:
        raise ValueError("stale_source_count must be at most retrieved_source_count")
    if value.pending_recheck_count > value.retrieved_source_count:
        raise ValueError(
            "pending_recheck_count must be at most retrieved_source_count",
        )


def _validate_class_row_consistency(
    row: ResearchSourceRetrievalCompletenessClassRow,
) -> None:
    _validate_source_class_aggregate_consistency(
        ResearchSourceRetrievalSourceClassAggregate(
            source_class=row.source_class,
            required_source_count=row.required_source_count,
            retrieval_attempt_count=row.retrieval_attempt_count,
            retrieved_source_count=row.retrieved_source_count,
            stale_source_count=row.stale_source_count,
            failed_retrieval_count=row.failed_retrieval_count,
            pending_recheck_count=row.pending_recheck_count,
        ),
    )
    if row.source_class_covered != (
        row.retrieved_source_count >= row.required_source_count
    ):
        raise ValueError("source_class_covered must match source counts")
    if row.retrieval_coverage_ratio != _bounded_ratio(
        row.retrieved_source_count,
        row.required_source_count,
    ):
        raise ValueError("retrieval_coverage_ratio must match source counts")
    if row.stale_source_ratio != _ratio(
        row.stale_source_count,
        row.retrieved_source_count,
    ):
        raise ValueError("stale_source_ratio must match source counts")
    if row.failed_retrieval_pressure_ratio != _ratio(
        row.failed_retrieval_count,
        row.retrieval_attempt_count,
    ):
        raise ValueError("failed_retrieval_pressure_ratio must match source counts")
    if row.recheck_urgency_ratio != _ratio(
        row.pending_recheck_count,
        row.retrieved_source_count,
    ):
        raise ValueError("recheck_urgency_ratio must match source counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchSourceRetrievalCompletenessGateReport,
) -> None:
    if report.source_class_count != _decimal_count(len(report.rows)):
        raise ValueError("source_class_count must match rows")
    if report.covered_source_class_count != _count_rows_by_coverage(report.rows):
        raise ValueError("covered_source_class_count must match rows")
    if report.required_source_count != _sum_counts(
        tuple(row.required_source_count for row in report.rows),
    ):
        raise ValueError("required_source_count must match rows")
    if report.retrieval_attempt_count != _sum_counts(
        tuple(row.retrieval_attempt_count for row in report.rows),
    ):
        raise ValueError("retrieval_attempt_count must match rows")
    if report.retrieved_source_count != _sum_counts(
        tuple(row.retrieved_source_count for row in report.rows),
    ):
        raise ValueError("retrieved_source_count must match rows")
    if report.stale_source_count != _sum_counts(
        tuple(row.stale_source_count for row in report.rows),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.failed_retrieval_count != _sum_counts(
        tuple(row.failed_retrieval_count for row in report.rows),
    ):
        raise ValueError("failed_retrieval_count must match rows")
    if report.pending_recheck_count != _sum_counts(
        tuple(row.pending_recheck_count for row in report.rows),
    ):
        raise ValueError("pending_recheck_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.source_class_coverage_ratio != _ratio(
        report.covered_source_class_count,
        report.source_class_count,
    ):
        raise ValueError("source_class_coverage_ratio must match rows")
    if report.retrieval_coverage_ratio != _bounded_ratio(
        report.retrieved_source_count,
        report.required_source_count,
    ):
        raise ValueError("retrieval_coverage_ratio must match rows")
    if report.stale_source_ratio != _ratio(
        report.stale_source_count,
        report.retrieved_source_count,
    ):
        raise ValueError("stale_source_ratio must match rows")
    if report.failed_retrieval_pressure_ratio != _ratio(
        report.failed_retrieval_count,
        report.retrieval_attempt_count,
    ):
        raise ValueError("failed_retrieval_pressure_ratio must match rows")
    if report.recheck_urgency_ratio != _ratio(
        report.pending_recheck_count,
        report.retrieved_source_count,
    ):
        raise ValueError("recheck_urgency_ratio must match rows")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.source_class)):
        raise ValueError("rows must be sorted")
    if report.status not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _count_rows_by_coverage(
    rows: tuple[ResearchSourceRetrievalCompletenessClassRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.source_class_covered))


def _status_count(
    rows: tuple[ResearchSourceRetrievalCompletenessClassRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    suffixes: list[str] = []
    for reason_code in reason_codes:
        suffix = reason_code.rsplit("_", 1)[-1]
        if suffix in _STATUSES:
            suffixes.append(suffix)
    if not suffixes:
        raise ValueError("reason_codes must include status suffixes")
    return max(suffixes, key=lambda status: _PRESSURE_STATUS_RANK[status])


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return min(_ONE, _ratio(numerator, denominator))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_canonical_string("reason_codes", value)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must be unique")
    return tuple(values)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {field_name}: {value}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_pressure_threshold_pair(
    watch_field_name: str,
    watch_threshold: Decimal,
    block_field_name: str,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed {watch_field_name}")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    for item in _surface_items(value):
        lowered = item.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}: {item}")


def _surface_items(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[str] = []
        for field in fields(value):
            items.append(field.name)
            items.extend(_surface_items(getattr(value, field.name)))
        return tuple(items)
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append(key)
            items.extend(_surface_items(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_surface_items(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match derived payload")


def _derived_digest(value: object) -> str:
    canonical = _canonical_digest_value(value)
    encoded = json.dumps(
        canonical,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_digest_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(getattr(value, field.name))
            for field in fields(value)
            if field.name != _DIGEST_FIELD
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("digest Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_digest_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if key != _DIGEST_FIELD:
                result[key] = _canonical_digest_value(item)
        return result
    raise ValueError("unsupported digest value")


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("public payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("value is not JSON serializable")


def _require_public_payload_values(value: object, path: str = "payload") -> None:
    if value is None:
        return
    if type(value) in (float, int):
        raise ValueError(f"{path} must not contain numeric JSON primitives")
    if type(value) is bool:
        return
    if type(value) is str:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _require_public_payload_values(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_public_payload_values(item, f"{path}[{index}]")
        return
    raise ValueError(f"{path} is not JSON serializable")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        if _DIGEST_FIELD in value:
            current = value[_DIGEST_FIELD]
            if type(current) is not str:
                raise ValueError("derived_validation_digest must be a string")
            expected = _derived_digest(value)
            if current != expected or not _is_sha256_hex(current):
                raise ValueError("derived_validation_digest does not match public payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)
