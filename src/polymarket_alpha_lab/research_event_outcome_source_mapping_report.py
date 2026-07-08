"""Pure aggregate report for event outcome mapping by source class."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any


CONFIG_VERSION = "research-event-outcome-source-mapping-report-v0"
MAPPING_STATUSES = ("pass", "watch", "block")

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_SOURCE_CLASS_DISALLOWED_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "://",
    "/",
    "?",
    "#",
)
_UNSAFE_SURFACE_FRAGMENTS = (
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("au", "th")),
    "".join(("pri", "vate_key")),
    "".join(("li", "ve execution")),
    "".join(("pos", "ition sizing")),
)


@dataclass(frozen=True)
class ResearchEventOutcomeSourceMappingReportConfig:
    config_version: str = CONFIG_VERSION
    watch_coverage_ratio: Decimal = Decimal("0.950000")
    block_coverage_ratio: Decimal = Decimal("0.750000")
    watch_agreement_ratio: Decimal = Decimal("0.900000")
    block_agreement_ratio: Decimal = Decimal("0.750000")
    watch_stale_mapping_ratio: Decimal = Decimal("0.150000")
    block_stale_mapping_ratio: Decimal = Decimal("0.300000")
    watch_ambiguity_ratio: Decimal = Decimal("0.100000")
    block_ambiguity_ratio: Decimal = Decimal("0.250000")
    watch_recheck_urgency_ratio: Decimal = Decimal("0.200000")
    block_recheck_urgency_ratio: Decimal = Decimal("0.400000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventOutcomeSourceMappingReportConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventOutcomeSourceMappingReportConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_coverage_ratio",
            "block_coverage_ratio",
            "watch_agreement_ratio",
            "block_agreement_ratio",
            "watch_stale_mapping_ratio",
            "block_stale_mapping_ratio",
            "watch_ambiguity_ratio",
            "block_ambiguity_ratio",
            "watch_recheck_urgency_ratio",
            "block_recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_coverage_ratio > self.watch_coverage_ratio:
            raise ValueError("block_coverage_ratio must not exceed watch_coverage_ratio")
        if self.block_agreement_ratio > self.watch_agreement_ratio:
            raise ValueError("block_agreement_ratio must not exceed watch_agreement_ratio")
        if self.block_stale_mapping_ratio < self.watch_stale_mapping_ratio:
            raise ValueError(
                "block_stale_mapping_ratio must cover watch_stale_mapping_ratio",
            )
        if self.block_ambiguity_ratio < self.watch_ambiguity_ratio:
            raise ValueError("block_ambiguity_ratio must cover watch_ambiguity_ratio")
        if self.block_recheck_urgency_ratio < self.watch_recheck_urgency_ratio:
            raise ValueError(
                "block_recheck_urgency_ratio must cover watch_recheck_urgency_ratio",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventOutcomeSourceMappingAggregate:
    source_class: str
    outcome_count: Decimal
    mapped_outcome_count: Decimal
    agreeing_mapping_count: Decimal
    stale_mapping_count: Decimal
    ambiguous_mapping_count: Decimal
    recheck_due_count: Decimal
    max_mapping_age_seconds: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventOutcomeSourceMappingAggregate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("aggregate", self, ResearchEventOutcomeSourceMappingAggregate)
        _require_source_class("source_class", self.source_class)
        for field_name in (
            "outcome_count",
            "mapped_outcome_count",
            "agreeing_mapping_count",
            "stale_mapping_count",
            "ambiguous_mapping_count",
            "recheck_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_mapping_age_seconds",
            _normalize_nonnegative_decimal(
                "max_mapping_age_seconds",
                self.max_mapping_age_seconds,
            ),
        )
        _validate_aggregate_counts(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("aggregate", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventOutcomeSourceMappingRow:
    source_class: str
    status: str
    outcome_count: Decimal
    mapped_outcome_count: Decimal
    unmapped_outcome_count: Decimal
    agreeing_mapping_count: Decimal
    stale_mapping_count: Decimal
    ambiguous_mapping_count: Decimal
    recheck_due_count: Decimal
    coverage_ratio: Decimal
    agreement_ratio: Decimal
    stale_mapping_ratio: Decimal
    ambiguity_ratio: Decimal
    recheck_urgency_ratio: Decimal
    max_mapping_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventOutcomeSourceMappingRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventOutcomeSourceMappingRow)
        _require_source_class("source_class", self.source_class)
        _require_status("status", self.status)
        for field_name in (
            "outcome_count",
            "mapped_outcome_count",
            "unmapped_outcome_count",
            "agreeing_mapping_count",
            "stale_mapping_count",
            "ambiguous_mapping_count",
            "recheck_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_ratio",
            "agreement_ratio",
            "stale_mapping_ratio",
            "ambiguity_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_mapping_age_seconds",
            _normalize_nonnegative_decimal(
                "max_mapping_age_seconds",
                self.max_mapping_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventOutcomeSourceMappingReport:
    generated_at: datetime
    config_version: str
    status: str
    source_class_count: Decimal
    outcome_count: Decimal
    mapped_outcome_count: Decimal
    unmapped_outcome_count: Decimal
    agreeing_mapping_count: Decimal
    stale_mapping_count: Decimal
    ambiguous_mapping_count: Decimal
    recheck_due_count: Decimal
    coverage_ratio: Decimal
    agreement_ratio: Decimal
    stale_mapping_ratio: Decimal
    ambiguity_ratio: Decimal
    recheck_urgency_ratio: Decimal
    max_mapping_age_seconds: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rows: tuple[ResearchEventOutcomeSourceMappingRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventOutcomeSourceMappingReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventOutcomeSourceMappingReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "source_class_count",
            "outcome_count",
            "mapped_outcome_count",
            "unmapped_outcome_count",
            "agreeing_mapping_count",
            "stale_mapping_count",
            "ambiguous_mapping_count",
            "recheck_due_count",
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
            "coverage_ratio",
            "agreement_ratio",
            "stale_mapping_ratio",
            "ambiguity_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_mapping_age_seconds",
            _normalize_nonnegative_decimal(
                "max_mapping_age_seconds",
                self.max_mapping_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_event_outcome_source_mapping_report(
    aggregates: Iterable[ResearchEventOutcomeSourceMappingAggregate],
    *,
    config: ResearchEventOutcomeSourceMappingReportConfig,
    generated_at: datetime,
) -> ResearchEventOutcomeSourceMappingReport:
    if type(config) is not ResearchEventOutcomeSourceMappingReportConfig:
        raise ValueError("config must be a ResearchEventOutcomeSourceMappingReportConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    values = _normalize_aggregates(aggregates)
    rows = tuple(
        sorted(
            (_row_from_aggregate(value, config=config) for value in values),
            key=_row_sort_key,
        ),
    )
    outcome_count = _sum_decimal(row.outcome_count for row in rows)
    mapped_outcome_count = _sum_decimal(row.mapped_outcome_count for row in rows)
    agreeing_mapping_count = _sum_decimal(row.agreeing_mapping_count for row in rows)
    stale_mapping_count = _sum_decimal(row.stale_mapping_count for row in rows)
    ambiguous_mapping_count = _sum_decimal(row.ambiguous_mapping_count for row in rows)
    recheck_due_count = _sum_decimal(row.recheck_due_count for row in rows)
    status = _report_status(rows)
    return ResearchEventOutcomeSourceMappingReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        source_class_count=_decimal_count(len(rows)),
        outcome_count=outcome_count,
        mapped_outcome_count=mapped_outcome_count,
        unmapped_outcome_count=_quantize(outcome_count - mapped_outcome_count),
        agreeing_mapping_count=agreeing_mapping_count,
        stale_mapping_count=stale_mapping_count,
        ambiguous_mapping_count=ambiguous_mapping_count,
        recheck_due_count=recheck_due_count,
        coverage_ratio=_coverage_ratio(mapped_outcome_count, outcome_count),
        agreement_ratio=_agreement_ratio(agreeing_mapping_count, mapped_outcome_count),
        stale_mapping_ratio=_pressure_ratio(stale_mapping_count, mapped_outcome_count),
        ambiguity_ratio=_pressure_ratio(ambiguous_mapping_count, mapped_outcome_count),
        recheck_urgency_ratio=_pressure_ratio(recheck_due_count, mapped_outcome_count),
        max_mapping_age_seconds=_max_decimal(
            (row.max_mapping_age_seconds for row in rows),
            default=_ZERO,
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        rows=rows,
        reason_codes=_report_reason_codes(rows, status=status),
    )


def research_event_outcome_source_mapping_report_payload(
    report: ResearchEventOutcomeSourceMappingReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventOutcomeSourceMappingReport:
        raise ValueError("report must be a ResearchEventOutcomeSourceMappingReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_outcome_source_mapping_report_payload(payload)
    return payload


def validate_research_event_outcome_source_mapping_report_payload(payload: object) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_surface("payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_aggregate(
    value: ResearchEventOutcomeSourceMappingAggregate,
    *,
    config: ResearchEventOutcomeSourceMappingReportConfig,
) -> ResearchEventOutcomeSourceMappingRow:
    coverage_ratio = _coverage_ratio(value.mapped_outcome_count, value.outcome_count)
    agreement_ratio = _agreement_ratio(
        value.agreeing_mapping_count,
        value.mapped_outcome_count,
    )
    stale_mapping_ratio = _pressure_ratio(
        value.stale_mapping_count,
        value.mapped_outcome_count,
    )
    ambiguity_ratio = _pressure_ratio(
        value.ambiguous_mapping_count,
        value.mapped_outcome_count,
    )
    recheck_urgency_ratio = _pressure_ratio(
        value.recheck_due_count,
        value.mapped_outcome_count,
    )
    reason_codes = _row_reason_codes(
        coverage_ratio=coverage_ratio,
        agreement_ratio=agreement_ratio,
        stale_mapping_ratio=stale_mapping_ratio,
        ambiguity_ratio=ambiguity_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        config=config,
    )
    return ResearchEventOutcomeSourceMappingRow(
        source_class=value.source_class,
        status=_status_from_reason_codes(reason_codes),
        outcome_count=value.outcome_count,
        mapped_outcome_count=value.mapped_outcome_count,
        unmapped_outcome_count=_quantize(value.outcome_count - value.mapped_outcome_count),
        agreeing_mapping_count=value.agreeing_mapping_count,
        stale_mapping_count=value.stale_mapping_count,
        ambiguous_mapping_count=value.ambiguous_mapping_count,
        recheck_due_count=value.recheck_due_count,
        coverage_ratio=coverage_ratio,
        agreement_ratio=agreement_ratio,
        stale_mapping_ratio=stale_mapping_ratio,
        ambiguity_ratio=ambiguity_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        max_mapping_age_seconds=value.max_mapping_age_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    coverage_ratio: Decimal,
    agreement_ratio: Decimal,
    stale_mapping_ratio: Decimal,
    ambiguity_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
    config: ResearchEventOutcomeSourceMappingReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if coverage_ratio < config.block_coverage_ratio:
        reasons.append("coverage_gap_block")
    elif coverage_ratio < config.watch_coverage_ratio:
        reasons.append("coverage_gap_watch")
    if agreement_ratio < config.block_agreement_ratio:
        reasons.append("agreement_gap_block")
    elif agreement_ratio < config.watch_agreement_ratio:
        reasons.append("agreement_gap_watch")
    if stale_mapping_ratio >= config.block_stale_mapping_ratio:
        reasons.append("stale_mapping_pressure_block")
    elif stale_mapping_ratio >= config.watch_stale_mapping_ratio:
        reasons.append("stale_mapping_pressure_watch")
    if ambiguity_ratio >= config.block_ambiguity_ratio:
        reasons.append("ambiguity_pressure_block")
    elif ambiguity_ratio >= config.watch_ambiguity_ratio:
        reasons.append("ambiguity_pressure_watch")
    if recheck_urgency_ratio >= config.block_recheck_urgency_ratio:
        reasons.append("recheck_urgency_block")
    elif recheck_urgency_ratio >= config.watch_recheck_urgency_ratio:
        reasons.append("recheck_urgency_watch")
    status = _status_from_pressure_reasons(tuple(reasons))
    return (f"source_mapping_{status}", *reasons)


def _status_from_pressure_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    return reason_codes[0].removeprefix("source_mapping_")


def _normalize_aggregates(
    values: Iterable[ResearchEventOutcomeSourceMappingAggregate],
) -> tuple[ResearchEventOutcomeSourceMappingAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchEventOutcomeSourceMappingAggregate:
            raise ValueError(
                "aggregates must contain ResearchEventOutcomeSourceMappingAggregate values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("aggregate", value)
        _require_or_set_digest(value)
        if value.source_class in seen:
            raise ValueError("aggregates must not contain duplicate source_class values")
        seen.add(value.source_class)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchEventOutcomeSourceMappingRow],
) -> tuple[ResearchEventOutcomeSourceMappingRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchEventOutcomeSourceMappingRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain ResearchEventOutcomeSourceMappingRow values") from exc
    for row in rows:
        if type(row) is not ResearchEventOutcomeSourceMappingRow:
            raise ValueError("rows must contain ResearchEventOutcomeSourceMappingRow values")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic source_class sort")
    if len({row.source_class for row in rows}) != len(rows):
        raise ValueError("rows must be unique by source_class")
    return rows


def _validate_aggregate_counts(
    value: ResearchEventOutcomeSourceMappingAggregate,
) -> None:
    if value.mapped_outcome_count > value.outcome_count:
        raise ValueError("mapped_outcome_count must not exceed outcome_count")
    if value.agreeing_mapping_count > value.mapped_outcome_count:
        raise ValueError("agreeing_mapping_count must not exceed mapped_outcome_count")
    for field_name in (
        "stale_mapping_count",
        "ambiguous_mapping_count",
        "recheck_due_count",
    ):
        if getattr(value, field_name) > value.mapped_outcome_count:
            raise ValueError(f"{field_name} must not exceed mapped_outcome_count")
    if value.outcome_count == _ZERO and value.max_mapping_age_seconds != _ZERO:
        raise ValueError("max_mapping_age_seconds must be zero when outcome_count is zero")


def _validate_row_consistency(row: ResearchEventOutcomeSourceMappingRow) -> None:
    if row.unmapped_outcome_count != _quantize(row.outcome_count - row.mapped_outcome_count):
        raise ValueError("unmapped_outcome_count must match mapping coverage gap")
    if row.coverage_ratio != _coverage_ratio(row.mapped_outcome_count, row.outcome_count):
        raise ValueError("coverage_ratio must match mapping counts")
    if row.agreement_ratio != _agreement_ratio(
        row.agreeing_mapping_count,
        row.mapped_outcome_count,
    ):
        raise ValueError("agreement_ratio must match mapping counts")
    if row.stale_mapping_ratio != _pressure_ratio(
        row.stale_mapping_count,
        row.mapped_outcome_count,
    ):
        raise ValueError("stale_mapping_ratio must match mapping counts")
    if row.ambiguity_ratio != _pressure_ratio(
        row.ambiguous_mapping_count,
        row.mapped_outcome_count,
    ):
        raise ValueError("ambiguity_ratio must match mapping counts")
    if row.recheck_urgency_ratio != _pressure_ratio(
        row.recheck_due_count,
        row.mapped_outcome_count,
    ):
        raise ValueError("recheck_urgency_ratio must match mapping counts")
    if row.reason_codes[0] != f"source_mapping_{row.status}":
        raise ValueError("reason_codes must start with status reason")
    if row.status != _status_from_pressure_reasons(row.reason_codes[1:]):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchEventOutcomeSourceMappingReport,
) -> None:
    if report.source_class_count != _decimal_count(len(report.rows)):
        raise ValueError("source_class_count must match rows")
    if report.outcome_count != _sum_decimal(row.outcome_count for row in report.rows):
        raise ValueError("outcome_count must match rows")
    if report.mapped_outcome_count != _sum_decimal(
        row.mapped_outcome_count for row in report.rows
    ):
        raise ValueError("mapped_outcome_count must match rows")
    if report.unmapped_outcome_count != _quantize(
        report.outcome_count - report.mapped_outcome_count,
    ):
        raise ValueError("unmapped_outcome_count must match totals")
    if report.agreeing_mapping_count != _sum_decimal(
        row.agreeing_mapping_count for row in report.rows
    ):
        raise ValueError("agreeing_mapping_count must match rows")
    if report.stale_mapping_count != _sum_decimal(
        row.stale_mapping_count for row in report.rows
    ):
        raise ValueError("stale_mapping_count must match rows")
    if report.ambiguous_mapping_count != _sum_decimal(
        row.ambiguous_mapping_count for row in report.rows
    ):
        raise ValueError("ambiguous_mapping_count must match rows")
    if report.recheck_due_count != _sum_decimal(row.recheck_due_count for row in report.rows):
        raise ValueError("recheck_due_count must match rows")
    if report.coverage_ratio != _coverage_ratio(
        report.mapped_outcome_count,
        report.outcome_count,
    ):
        raise ValueError("coverage_ratio must match totals")
    if report.agreement_ratio != _agreement_ratio(
        report.agreeing_mapping_count,
        report.mapped_outcome_count,
    ):
        raise ValueError("agreement_ratio must match totals")
    if report.stale_mapping_ratio != _pressure_ratio(
        report.stale_mapping_count,
        report.mapped_outcome_count,
    ):
        raise ValueError("stale_mapping_ratio must match totals")
    if report.ambiguity_ratio != _pressure_ratio(
        report.ambiguous_mapping_count,
        report.mapped_outcome_count,
    ):
        raise ValueError("ambiguity_ratio must match totals")
    if report.recheck_urgency_ratio != _pressure_ratio(
        report.recheck_due_count,
        report.mapped_outcome_count,
    ):
        raise ValueError("recheck_urgency_ratio must match totals")
    if report.max_mapping_age_seconds != _max_decimal(
        (row.max_mapping_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_mapping_age_seconds must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, status=report.status):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(
    row: ResearchEventOutcomeSourceMappingRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_RANK[row.status],
        row.coverage_ratio,
        row.agreement_ratio,
        -row.stale_mapping_ratio,
        -row.ambiguity_ratio,
        -row.recheck_urgency_ratio,
        row.source_class,
    )


def _report_status(rows: tuple[ResearchEventOutcomeSourceMappingRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventOutcomeSourceMappingRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    reasons = [f"source_mapping_report_{status}"]
    for row in rows:
        for reason_code in row.reason_codes[1:]:
            if reason_code not in reasons:
                reasons.append(reason_code)
    return tuple(reasons)


def _status_count(
    rows: tuple[ResearchEventOutcomeSourceMappingRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += value
    return _quantize(total)


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return max(items)


def _coverage_ratio(mapped_count: Decimal, outcome_count: Decimal) -> Decimal:
    if outcome_count == _ZERO:
        return _ONE
    return _ratio(mapped_count, outcome_count)


def _agreement_ratio(agreeing_count: Decimal, mapped_count: Decimal) -> Decimal:
    if mapped_count == _ZERO:
        return _ONE
    return _ratio(agreeing_count, mapped_count)


def _pressure_ratio(count: Decimal, mapped_count: Decimal) -> Decimal:
    if mapped_count == _ZERO:
        return _ZERO
    return _ratio(count, mapped_count)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_source_class(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical source class")
    normalized = value.lower()
    if value != normalized:
        raise ValueError(f"{field_name} must be a lowercase source class")
    if any(fragment in normalized for fragment in _SOURCE_CLASS_DISALLOWED_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain a locator")
    if normalized.startswith("_") or normalized.endswith("_") or "__" in normalized:
        raise ValueError(f"{field_name} must be a canonical source class")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in normalized):
        raise ValueError(f"{field_name} must be a canonical source class")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MAPPING_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    seen: set[str] = set()
    for item in items:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must contain unique values")
        seen.add(item)
    return items


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD, None)
    expected = _derived_digest_for_value(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    normalized = _normalize_sha256(_DIGEST_FIELD, current)
    if normalized != expected:
        raise ValueError("derived_validation_digest must match public fields")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    return value


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, object] = {}
        for field in fields(value):
            result[field.name] = _payload_value(getattr(value, field.name))
        return result
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            result[key] = _payload_value(item)
        return result
    raise ValueError("value is not payload serializable")


def _derived_digest_for_value(value: object) -> str:
    payload = _payload_value(value)
    if not isinstance(payload, dict):
        raise ValueError("digest value must be an object")
    return _derived_digest_for_payload(payload)


def _derived_digest_for_payload(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(_DIGEST_FIELD, None)
    canonical = _canonical_payload(digest_payload)
    return hashlib.sha256(
        ("research_event_outcome_source_mapping_report|" + canonical).encode("utf-8"),
    ).hexdigest()


def _canonical_payload(value: object) -> str:
    if isinstance(value, dict):
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            parts.append(f"{len(key)}:{key}={_canonical_payload(value[key])}")
        return "{" + "|".join(parts) + "}"
    if isinstance(value, list):
        return "[" + "|".join(_canonical_payload(item) for item in value) + "]"
    if type(value) is str:
        return f"s{len(value)}:{value}"
    if type(value) is bool:
        return "b:1" if value else "b:0"
    if value is None:
        return "n:"
    raise ValueError("payload contains unsupported digest value")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        if _DIGEST_FIELD in value:
            current = value[_DIGEST_FIELD]
            if type(current) is not str:
                raise ValueError("derived_validation_digest must be a string")
            expected = _derived_digest_for_payload(value)
            if current != expected or not _is_sha256_hex(current):
                raise ValueError("derived_validation_digest does not match payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _require_public_payload_values(value: object) -> None:
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("payload numeric values must use Decimal-derived strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_payload_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_values(item)
        return
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(label, field.name)
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in _UNSAFE_SURFACE_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public value")


def _reject_unsafe_public_key(label: str, key: str) -> None:
    normalized = key.lower()
    if any(fragment in normalized for fragment in _UNSAFE_SURFACE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public field")


__all__ = (
    "CONFIG_VERSION",
    "MAPPING_STATUSES",
    "ResearchEventOutcomeSourceMappingReportConfig",
    "ResearchEventOutcomeSourceMappingAggregate",
    "ResearchEventOutcomeSourceMappingRow",
    "ResearchEventOutcomeSourceMappingReport",
    "build_research_event_outcome_source_mapping_report",
    "research_event_outcome_source_mapping_report_payload",
    "validate_research_event_outcome_source_mapping_report_payload",
)
