"""Pure aggregate resolution-rule source alignment report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_RESOLUTION_RULE_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "research-resolution-rule-source-alignment-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_PRESSURE_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("raw", "_", "url")),
    "".join(("raw", "-", "url")),
    "".join(("source", "_", "url")),
    "".join(("source", "-", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("market", "_", "slug")),
    "".join(("market", "-", "slug")),
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
    "DEFAULT_RESEARCH_RESOLUTION_RULE_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION",
    "ResearchResolutionRuleSourceAlignmentAggregate",
    "ResearchResolutionRuleSourceAlignmentConfig",
    "ResearchResolutionRuleSourceAlignmentReport",
    "ResearchResolutionRuleSourceAlignmentRow",
    "build_research_resolution_rule_source_alignment_report",
    "research_resolution_rule_source_alignment_report_payload",
    "validate_research_resolution_rule_source_alignment_report_payload",
)


@dataclass(frozen=True)
class ResearchResolutionRuleSourceAlignmentConfig:
    config_version: str = (
        DEFAULT_RESEARCH_RESOLUTION_RULE_SOURCE_ALIGNMENT_REPORT_CONFIG_VERSION
    )
    min_rule_citation_completeness_ratio: Decimal = Decimal("1.000000")
    block_rule_citation_completeness_ratio: Decimal = Decimal("0.500000")
    min_official_source_agreement_ratio: Decimal = Decimal("0.800000")
    block_official_source_agreement_ratio: Decimal = Decimal("0.500000")
    watch_ambiguity_pressure_ratio: Decimal = Decimal("0.250000")
    block_ambiguity_pressure_ratio: Decimal = Decimal("0.600000")
    watch_stale_rule_memory_ratio: Decimal = Decimal("0.250000")
    block_stale_rule_memory_ratio: Decimal = Decimal("0.500000")
    watch_recheck_urgency_ratio: Decimal = Decimal("0.250000")
    block_recheck_urgency_ratio: Decimal = Decimal("0.600000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleSourceAlignmentConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchResolutionRuleSourceAlignmentConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_rule_citation_completeness_ratio",
            "block_rule_citation_completeness_ratio",
            "min_official_source_agreement_ratio",
            "block_official_source_agreement_ratio",
            "watch_ambiguity_pressure_ratio",
            "block_ambiguity_pressure_ratio",
            "watch_stale_rule_memory_ratio",
            "block_stale_rule_memory_ratio",
            "watch_recheck_urgency_ratio",
            "block_recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_rule_citation_completeness_ratio <= _ZERO:
            raise ValueError("min_rule_citation_completeness_ratio must be positive")
        if (
            self.block_rule_citation_completeness_ratio
            >= self.min_rule_citation_completeness_ratio
        ):
            raise ValueError(
                "block_rule_citation_completeness_ratio must be below "
                "min_rule_citation_completeness_ratio",
            )
        if self.min_official_source_agreement_ratio <= _ZERO:
            raise ValueError("min_official_source_agreement_ratio must be positive")
        if (
            self.block_official_source_agreement_ratio
            >= self.min_official_source_agreement_ratio
        ):
            raise ValueError(
                "block_official_source_agreement_ratio must be below "
                "min_official_source_agreement_ratio",
            )
        _require_pressure_threshold_pair(
            "watch_ambiguity_pressure_ratio",
            self.watch_ambiguity_pressure_ratio,
            "block_ambiguity_pressure_ratio",
            self.block_ambiguity_pressure_ratio,
        )
        _require_pressure_threshold_pair(
            "watch_stale_rule_memory_ratio",
            self.watch_stale_rule_memory_ratio,
            "block_stale_rule_memory_ratio",
            self.block_stale_rule_memory_ratio,
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
class ResearchResolutionRuleSourceAlignmentAggregate:
    rule_group: str
    rule_count: Decimal
    cited_rule_count: Decimal
    evidence_source_count: Decimal
    official_source_agreement_count: Decimal
    ambiguous_rule_count: Decimal = _ZERO
    stale_rule_memory_count: Decimal = _ZERO
    pending_recheck_count: Decimal = _ZERO
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleSourceAlignmentAggregate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("aggregate", self, ResearchResolutionRuleSourceAlignmentAggregate)
        _require_canonical_string("rule_group", self.rule_group)
        for field_name in (
            "rule_count",
            "cited_rule_count",
            "evidence_source_count",
            "official_source_agreement_count",
            "ambiguous_rule_count",
            "stale_rule_memory_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_aggregate_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("aggregate", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchResolutionRuleSourceAlignmentRow:
    rule_group: str
    rule_count: Decimal
    cited_rule_count: Decimal
    evidence_source_count: Decimal
    official_source_agreement_count: Decimal
    ambiguous_rule_count: Decimal
    stale_rule_memory_count: Decimal
    pending_recheck_count: Decimal
    rule_citation_completeness_ratio: Decimal
    official_source_agreement_ratio: Decimal
    ambiguity_pressure_ratio: Decimal
    stale_rule_memory_ratio: Decimal
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
            "ResearchResolutionRuleSourceAlignmentRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchResolutionRuleSourceAlignmentRow)
        _require_canonical_string("rule_group", self.rule_group)
        for field_name in (
            "rule_count",
            "cited_rule_count",
            "evidence_source_count",
            "official_source_agreement_count",
            "ambiguous_rule_count",
            "stale_rule_memory_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_citation_completeness_ratio",
            "official_source_agreement_ratio",
            "ambiguity_pressure_ratio",
            "stale_rule_memory_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchResolutionRuleSourceAlignmentReport:
    generated_at: datetime
    config_version: str
    rule_group_count: Decimal
    rule_count: Decimal
    cited_rule_count: Decimal
    evidence_source_count: Decimal
    official_source_agreement_count: Decimal
    ambiguous_rule_count: Decimal
    stale_rule_memory_count: Decimal
    pending_recheck_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rule_citation_completeness_ratio: Decimal
    official_source_agreement_ratio: Decimal
    ambiguity_pressure_ratio: Decimal
    stale_rule_memory_ratio: Decimal
    recheck_urgency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchResolutionRuleSourceAlignmentRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionRuleSourceAlignmentReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchResolutionRuleSourceAlignmentReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "rule_group_count",
            "rule_count",
            "cited_rule_count",
            "evidence_source_count",
            "official_source_agreement_count",
            "ambiguous_rule_count",
            "stale_rule_memory_count",
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
            "rule_citation_completeness_ratio",
            "official_source_agreement_ratio",
            "ambiguity_pressure_ratio",
            "stale_rule_memory_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _require_or_set_digest(self)


def build_research_resolution_rule_source_alignment_report(
    aggregates: Iterable[ResearchResolutionRuleSourceAlignmentAggregate],
    *,
    config: ResearchResolutionRuleSourceAlignmentConfig,
    generated_at: datetime,
) -> ResearchResolutionRuleSourceAlignmentReport:
    if type(config) is not ResearchResolutionRuleSourceAlignmentConfig:
        raise ValueError(
            "config must be a ResearchResolutionRuleSourceAlignmentConfig",
        )
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_aggregates(aggregates)
    rows = tuple(_row_from_aggregate(value, config=config) for value in normalized)

    rule_group_count = _decimal_count(len(rows))
    rule_count = _sum_counts(tuple(row.rule_count for row in rows))
    cited_rule_count = _sum_counts(tuple(row.cited_rule_count for row in rows))
    evidence_source_count = _sum_counts(tuple(row.evidence_source_count for row in rows))
    official_source_agreement_count = _sum_counts(
        tuple(row.official_source_agreement_count for row in rows),
    )
    ambiguous_rule_count = _sum_counts(tuple(row.ambiguous_rule_count for row in rows))
    stale_rule_memory_count = _sum_counts(
        tuple(row.stale_rule_memory_count for row in rows),
    )
    pending_recheck_count = _sum_counts(tuple(row.pending_recheck_count for row in rows))
    pressure_statuses = _pressure_statuses(
        config=config,
        rule_citation_completeness_ratio=_ratio(cited_rule_count, rule_count),
        official_source_agreement_ratio=_ratio(
            official_source_agreement_count,
            evidence_source_count,
        ),
        ambiguity_pressure_ratio=_ratio(ambiguous_rule_count, rule_count),
        stale_rule_memory_ratio=_ratio(stale_rule_memory_count, rule_count),
        recheck_urgency_ratio=_ratio(pending_recheck_count, rule_count),
    )

    return ResearchResolutionRuleSourceAlignmentReport(
        generated_at=generated_at,
        config_version=config.config_version,
        rule_group_count=rule_group_count,
        rule_count=rule_count,
        cited_rule_count=cited_rule_count,
        evidence_source_count=evidence_source_count,
        official_source_agreement_count=official_source_agreement_count,
        ambiguous_rule_count=ambiguous_rule_count,
        stale_rule_memory_count=stale_rule_memory_count,
        pending_recheck_count=pending_recheck_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        rule_citation_completeness_ratio=(
            pressure_statuses.rule_citation_completeness_ratio
        ),
        official_source_agreement_ratio=pressure_statuses.official_source_agreement_ratio,
        ambiguity_pressure_ratio=pressure_statuses.ambiguity_pressure_ratio,
        stale_rule_memory_ratio=pressure_statuses.stale_rule_memory_ratio,
        recheck_urgency_ratio=pressure_statuses.recheck_urgency_ratio,
        status=_summary_status(rows, pressure_statuses),
        reason_codes=_report_reason_codes(rows, pressure_statuses),
        rows=rows,
    )


def research_resolution_rule_source_alignment_report_payload(
    report: ResearchResolutionRuleSourceAlignmentReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionRuleSourceAlignmentReport:
        raise ValueError(
            "report must be a ResearchResolutionRuleSourceAlignmentReport",
        )
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_research_resolution_rule_source_alignment_report_payload(payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def validate_research_resolution_rule_source_alignment_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


@dataclass(frozen=True)
class _PressureStatuses:
    rule_citation_completeness_ratio: Decimal
    official_source_agreement_ratio: Decimal
    ambiguity_pressure_ratio: Decimal
    stale_rule_memory_ratio: Decimal
    recheck_urgency_ratio: Decimal
    rule_citation_completeness_status: str
    official_source_agreement_status: str
    ambiguity_pressure_status: str
    stale_rule_memory_status: str
    recheck_urgency_status: str


def _row_from_aggregate(
    aggregate: ResearchResolutionRuleSourceAlignmentAggregate,
    *,
    config: ResearchResolutionRuleSourceAlignmentConfig,
) -> ResearchResolutionRuleSourceAlignmentRow:
    pressure_statuses = _pressure_statuses(
        config=config,
        rule_citation_completeness_ratio=_ratio(
            aggregate.cited_rule_count,
            aggregate.rule_count,
        ),
        official_source_agreement_ratio=_ratio(
            aggregate.official_source_agreement_count,
            aggregate.evidence_source_count,
        ),
        ambiguity_pressure_ratio=_ratio(
            aggregate.ambiguous_rule_count,
            aggregate.rule_count,
        ),
        stale_rule_memory_ratio=_ratio(
            aggregate.stale_rule_memory_count,
            aggregate.rule_count,
        ),
        recheck_urgency_ratio=_ratio(
            aggregate.pending_recheck_count,
            aggregate.rule_count,
        ),
    )
    return ResearchResolutionRuleSourceAlignmentRow(
        rule_group=aggregate.rule_group,
        rule_count=aggregate.rule_count,
        cited_rule_count=aggregate.cited_rule_count,
        evidence_source_count=aggregate.evidence_source_count,
        official_source_agreement_count=aggregate.official_source_agreement_count,
        ambiguous_rule_count=aggregate.ambiguous_rule_count,
        stale_rule_memory_count=aggregate.stale_rule_memory_count,
        pending_recheck_count=aggregate.pending_recheck_count,
        rule_citation_completeness_ratio=(
            pressure_statuses.rule_citation_completeness_ratio
        ),
        official_source_agreement_ratio=pressure_statuses.official_source_agreement_ratio,
        ambiguity_pressure_ratio=pressure_statuses.ambiguity_pressure_ratio,
        stale_rule_memory_ratio=pressure_statuses.stale_rule_memory_ratio,
        recheck_urgency_ratio=pressure_statuses.recheck_urgency_ratio,
        status=_worst_status(pressure_statuses),
        reason_codes=_metric_reason_codes(pressure_statuses),
    )


def _pressure_statuses(
    *,
    config: ResearchResolutionRuleSourceAlignmentConfig,
    rule_citation_completeness_ratio: Decimal,
    official_source_agreement_ratio: Decimal,
    ambiguity_pressure_ratio: Decimal,
    stale_rule_memory_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
) -> _PressureStatuses:
    return _PressureStatuses(
        rule_citation_completeness_ratio=rule_citation_completeness_ratio,
        official_source_agreement_ratio=official_source_agreement_ratio,
        ambiguity_pressure_ratio=ambiguity_pressure_ratio,
        stale_rule_memory_ratio=stale_rule_memory_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        rule_citation_completeness_status=_lower_bound_status(
            rule_citation_completeness_ratio,
            minimum=config.min_rule_citation_completeness_ratio,
            block_floor=config.block_rule_citation_completeness_ratio,
        ),
        official_source_agreement_status=_lower_bound_status(
            official_source_agreement_ratio,
            minimum=config.min_official_source_agreement_ratio,
            block_floor=config.block_official_source_agreement_ratio,
        ),
        ambiguity_pressure_status=_upper_bound_status(
            ambiguity_pressure_ratio,
            watch_threshold=config.watch_ambiguity_pressure_ratio,
            block_threshold=config.block_ambiguity_pressure_ratio,
        ),
        stale_rule_memory_status=_upper_bound_status(
            stale_rule_memory_ratio,
            watch_threshold=config.watch_stale_rule_memory_ratio,
            block_threshold=config.block_stale_rule_memory_ratio,
        ),
        recheck_urgency_status=_upper_bound_status(
            recheck_urgency_ratio,
            watch_threshold=config.watch_recheck_urgency_ratio,
            block_threshold=config.block_recheck_urgency_ratio,
        ),
    )


def _lower_bound_status(value: Decimal, *, minimum: Decimal, block_floor: Decimal) -> str:
    if value < block_floor:
        return "block"
    if value < minimum:
        return "watch"
    return "pass"


def _upper_bound_status(
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


def _worst_status(pressure_statuses: _PressureStatuses) -> str:
    statuses = (
        pressure_statuses.rule_citation_completeness_status,
        pressure_statuses.official_source_agreement_status,
        pressure_statuses.ambiguity_pressure_status,
        pressure_statuses.stale_rule_memory_status,
        pressure_statuses.recheck_urgency_status,
    )
    return max(statuses, key=lambda status: _PRESSURE_STATUS_RANK[status])


def _summary_status(
    rows: tuple[ResearchResolutionRuleSourceAlignmentRow, ...],
    pressure_statuses: _PressureStatuses,
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return _worst_status(pressure_statuses)


def _metric_reason_codes(pressure_statuses: _PressureStatuses) -> tuple[str, ...]:
    return (
        "rule_citation_completeness_"
        + pressure_statuses.rule_citation_completeness_status,
        "official_source_agreement_"
        + pressure_statuses.official_source_agreement_status,
        "ambiguity_pressure_" + pressure_statuses.ambiguity_pressure_status,
        "stale_rule_memory_" + pressure_statuses.stale_rule_memory_status,
        "recheck_urgency_" + pressure_statuses.recheck_urgency_status,
    )


def _report_reason_codes(
    rows: tuple[ResearchResolutionRuleSourceAlignmentRow, ...],
    pressure_statuses: _PressureStatuses,
) -> tuple[str, ...]:
    if not rows:
        return ("no_rule_source_alignment_groups",)
    if _worst_status(pressure_statuses) == "pass" and all(
        row.status == "pass" for row in rows
    ):
        return ("rule_source_alignment_pass",)
    reason_codes = tuple(
        reason_code
        for reason_code in _metric_reason_codes(pressure_statuses)
        if not reason_code.endswith("_pass")
    )
    if any(row.status == "block" for row in rows):
        reason_codes = reason_codes + ("rule_source_alignment_group_block",)
    elif any(row.status == "watch" for row in rows):
        reason_codes = reason_codes + ("rule_source_alignment_group_watch",)
    if reason_codes:
        return reason_codes
    return ("rule_source_alignment_watch",)


def _normalize_aggregates(
    values: Iterable[ResearchResolutionRuleSourceAlignmentAggregate],
) -> tuple[ResearchResolutionRuleSourceAlignmentAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        aggregates = tuple(values)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    for value in aggregates:
        if type(value) is not ResearchResolutionRuleSourceAlignmentAggregate:
            raise ValueError(
                "aggregates must contain ResearchResolutionRuleSourceAlignmentAggregate values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("aggregate", value)
        _require_or_set_digest(value)
    rows = tuple(sorted(aggregates, key=lambda value: value.rule_group))
    if len({value.rule_group for value in rows}) != len(rows):
        raise ValueError("aggregates must be unique by rule_group")
    return rows


def _normalize_rows(
    values: Iterable[ResearchResolutionRuleSourceAlignmentRow],
) -> tuple[ResearchResolutionRuleSourceAlignmentRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain alignment rows")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain alignment rows") from exc
    for row in rows:
        if type(row) is not ResearchResolutionRuleSourceAlignmentRow:
            raise ValueError("rows must contain alignment rows")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.rule_group))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by rule_group")
    if len({row.rule_group for row in rows}) != len(rows):
        raise ValueError("rows must be unique by rule_group")
    return rows


def _validate_aggregate_consistency(
    aggregate: ResearchResolutionRuleSourceAlignmentAggregate,
) -> None:
    if aggregate.rule_count <= _ZERO:
        raise ValueError("rule_count must be positive")
    if aggregate.cited_rule_count > aggregate.rule_count:
        raise ValueError("cited_rule_count must be at most rule_count")
    if aggregate.official_source_agreement_count > aggregate.evidence_source_count:
        raise ValueError(
            "official_source_agreement_count must be at most evidence_source_count",
        )
    for field_name in (
        "ambiguous_rule_count",
        "stale_rule_memory_count",
        "pending_recheck_count",
    ):
        if getattr(aggregate, field_name) > aggregate.rule_count:
            raise ValueError(f"{field_name} must be at most rule_count")


def _validate_row_consistency(row: ResearchResolutionRuleSourceAlignmentRow) -> None:
    _validate_aggregate_consistency(
        ResearchResolutionRuleSourceAlignmentAggregate(
            rule_group=row.rule_group,
            rule_count=row.rule_count,
            cited_rule_count=row.cited_rule_count,
            evidence_source_count=row.evidence_source_count,
            official_source_agreement_count=row.official_source_agreement_count,
            ambiguous_rule_count=row.ambiguous_rule_count,
            stale_rule_memory_count=row.stale_rule_memory_count,
            pending_recheck_count=row.pending_recheck_count,
        ),
    )
    if row.rule_citation_completeness_ratio != _ratio(
        row.cited_rule_count,
        row.rule_count,
    ):
        raise ValueError("rule_citation_completeness_ratio must match counts")
    if row.official_source_agreement_ratio != _ratio(
        row.official_source_agreement_count,
        row.evidence_source_count,
    ):
        raise ValueError("official_source_agreement_ratio must match counts")
    if row.ambiguity_pressure_ratio != _ratio(
        row.ambiguous_rule_count,
        row.rule_count,
    ):
        raise ValueError("ambiguity_pressure_ratio must match counts")
    if row.stale_rule_memory_ratio != _ratio(
        row.stale_rule_memory_count,
        row.rule_count,
    ):
        raise ValueError("stale_rule_memory_ratio must match counts")
    if row.recheck_urgency_ratio != _ratio(
        row.pending_recheck_count,
        row.rule_count,
    ):
        raise ValueError("recheck_urgency_ratio must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchResolutionRuleSourceAlignmentReport,
) -> None:
    if report.rule_group_count != _decimal_count(len(report.rows)):
        raise ValueError("rule_group_count must match rows")
    for field_name in (
        "rule_count",
        "cited_rule_count",
        "evidence_source_count",
        "official_source_agreement_count",
        "ambiguous_rule_count",
        "stale_rule_memory_count",
        "pending_recheck_count",
    ):
        expected = _sum_counts(tuple(getattr(row, field_name) for row in report.rows))
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_ratios = {
        "rule_citation_completeness_ratio": _ratio(
            report.cited_rule_count,
            report.rule_count,
        ),
        "official_source_agreement_ratio": _ratio(
            report.official_source_agreement_count,
            report.evidence_source_count,
        ),
        "ambiguity_pressure_ratio": _ratio(
            report.ambiguous_rule_count,
            report.rule_count,
        ),
        "stale_rule_memory_ratio": _ratio(
            report.stale_rule_memory_count,
            report.rule_count,
        ),
        "recheck_urgency_ratio": _ratio(
            report.pending_recheck_count,
            report.rule_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.rule_group)):
        raise ValueError("rows must be sorted")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        _PressureStatuses(
            rule_citation_completeness_ratio=report.rule_citation_completeness_ratio,
            official_source_agreement_ratio=report.official_source_agreement_ratio,
            ambiguity_pressure_ratio=report.ambiguity_pressure_ratio,
            stale_rule_memory_ratio=report.stale_rule_memory_ratio,
            recheck_urgency_ratio=report.recheck_urgency_ratio,
            rule_citation_completeness_status=_status_from_metric_reason(
                "rule_citation_completeness",
                report.reason_codes,
                fallback="pass",
            ),
            official_source_agreement_status=_status_from_metric_reason(
                "official_source_agreement",
                report.reason_codes,
                fallback="pass",
            ),
            ambiguity_pressure_status=_status_from_metric_reason(
                "ambiguity_pressure",
                report.reason_codes,
                fallback="pass",
            ),
            stale_rule_memory_status=_status_from_metric_reason(
                "stale_rule_memory",
                report.reason_codes,
                fallback="pass",
            ),
            recheck_urgency_status=_status_from_metric_reason(
                "recheck_urgency",
                report.reason_codes,
                fallback="pass",
            ),
        ),
    ):
        raise ValueError("reason_codes must match rows")
    expected_status = "block" if not report.rows else "pass"
    if report.block_count > _ZERO:
        expected_status = "block"
    elif report.watch_count > _ZERO:
        expected_status = "watch"
    elif any(reason_code.endswith("_watch") for reason_code in report.reason_codes):
        expected_status = "watch"
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _status_from_metric_reason(
    metric_name: str,
    reason_codes: tuple[str, ...],
    *,
    fallback: str,
) -> str:
    for status in ("block", "watch", "pass"):
        if f"{metric_name}_{status}" in reason_codes:
            return status
    return fallback


def _status_count(
    rows: tuple[ResearchResolutionRuleSourceAlignmentRow, ...],
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
    encoded = json.dumps(
        _canonical_digest_value(value),
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
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
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
