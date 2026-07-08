"""Pure aggregate event-source-to-resolution bridge report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-event-source-resolution-bridge-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "://",
    "".join(("www", ".")),
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
    "".join(("candidate", "_", "id")),
    "".join(("candidate", "-", "id")),
    "".join(("ques", "tion")),
    "".join(("d", "sn")),
    "".join(("table", "_", "name")),
    "".join(("private", "_", "token")),
    "".join(("data", "base")),
    "".join(("secret")),
    "".join(("password")),
    "".join(("private", "_", "key")),
    "".join(("api", "_", "key")),
    "".join(("auth", "entication")),
    "".join(("auth", "orization")),
    "".join(("auth", "_", "token")),
    "".join(("bearer")),
    "".join(("credential")),
    "".join(("net", "work")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("li", "ve")),
    "".join(("si", "zing")),
    "".join(("recomm", "endation")),
    "".join(("tra", "de")),
    "".join(("tra", "ding")),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_BRIDGE_REPORT_CONFIG_VERSION",
    "ResearchEventSourceResolutionBridgeAggregate",
    "ResearchEventSourceResolutionBridgeConfig",
    "ResearchEventSourceResolutionBridgeReport",
    "ResearchEventSourceResolutionBridgeRow",
    "build_research_event_source_resolution_bridge_report",
    "research_event_source_resolution_bridge_report_payload",
    "validate_research_event_source_resolution_bridge_report_payload",
)


@dataclass(frozen=True)
class ResearchEventSourceResolutionBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_BRIDGE_REPORT_CONFIG_VERSION
    )
    min_source_quorum_ratio: Decimal = Decimal("0.800000")
    block_source_quorum_ratio: Decimal = Decimal("0.500000")
    min_rule_linkage_completeness_ratio: Decimal = Decimal("1.000000")
    block_rule_linkage_completeness_ratio: Decimal = Decimal("0.500000")
    min_freshness_ratio: Decimal = Decimal("0.800000")
    block_freshness_ratio: Decimal = Decimal("0.500000")
    watch_ambiguity_pressure_ratio: Decimal = Decimal("0.250000")
    block_ambiguity_pressure_ratio: Decimal = Decimal("0.600000")
    watch_manual_escalation_urgency_ratio: Decimal = Decimal("0.350000")
    block_manual_escalation_urgency_ratio: Decimal = Decimal("0.700000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionBridgeConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventSourceResolutionBridgeConfig)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_source_quorum_ratio",
            "block_source_quorum_ratio",
            "min_rule_linkage_completeness_ratio",
            "block_rule_linkage_completeness_ratio",
            "min_freshness_ratio",
            "block_freshness_ratio",
            "watch_ambiguity_pressure_ratio",
            "block_ambiguity_pressure_ratio",
            "watch_manual_escalation_urgency_ratio",
            "block_manual_escalation_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_lower_threshold_pair(
            "min_source_quorum_ratio",
            self.min_source_quorum_ratio,
            "block_source_quorum_ratio",
            self.block_source_quorum_ratio,
        )
        _require_lower_threshold_pair(
            "min_rule_linkage_completeness_ratio",
            self.min_rule_linkage_completeness_ratio,
            "block_rule_linkage_completeness_ratio",
            self.block_rule_linkage_completeness_ratio,
        )
        _require_lower_threshold_pair(
            "min_freshness_ratio",
            self.min_freshness_ratio,
            "block_freshness_ratio",
            self.block_freshness_ratio,
        )
        _require_upper_threshold_pair(
            "watch_ambiguity_pressure_ratio",
            self.watch_ambiguity_pressure_ratio,
            "block_ambiguity_pressure_ratio",
            self.block_ambiguity_pressure_ratio,
        )
        _require_upper_threshold_pair(
            "watch_manual_escalation_urgency_ratio",
            self.watch_manual_escalation_urgency_ratio,
            "block_manual_escalation_urgency_ratio",
            self.block_manual_escalation_urgency_ratio,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchEventSourceResolutionBridgeAggregate:
    event_scope: str
    required_source_count: Decimal
    bridged_source_count: Decimal
    required_rule_link_count: Decimal
    bridged_rule_link_count: Decimal
    evidence_item_count: Decimal
    fresh_evidence_count: Decimal
    ambiguous_evidence_count: Decimal = _ZERO
    manual_escalation_count: Decimal = _ZERO
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionBridgeAggregate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("aggregate", self, ResearchEventSourceResolutionBridgeAggregate)
        _require_canonical_string("event_scope", self.event_scope)
        for field_name in (
            "required_source_count",
            "bridged_source_count",
            "required_rule_link_count",
            "bridged_rule_link_count",
            "evidence_item_count",
            "fresh_evidence_count",
            "ambiguous_evidence_count",
            "manual_escalation_count",
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
class ResearchEventSourceResolutionBridgeRow:
    event_scope: str
    required_source_count: Decimal
    bridged_source_count: Decimal
    required_rule_link_count: Decimal
    bridged_rule_link_count: Decimal
    evidence_item_count: Decimal
    fresh_evidence_count: Decimal
    ambiguous_evidence_count: Decimal
    manual_escalation_count: Decimal
    source_quorum_ratio: Decimal
    rule_linkage_completeness_ratio: Decimal
    freshness_ratio: Decimal
    ambiguity_pressure_ratio: Decimal
    manual_escalation_urgency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionBridgeRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventSourceResolutionBridgeRow)
        _require_canonical_string("event_scope", self.event_scope)
        for field_name in (
            "required_source_count",
            "bridged_source_count",
            "required_rule_link_count",
            "bridged_rule_link_count",
            "evidence_item_count",
            "fresh_evidence_count",
            "ambiguous_evidence_count",
            "manual_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_quorum_ratio",
            "rule_linkage_completeness_ratio",
            "freshness_ratio",
            "ambiguity_pressure_ratio",
            "manual_escalation_urgency_ratio",
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
class ResearchEventSourceResolutionBridgeReport:
    generated_at: datetime
    config_version: str
    event_scope_count: Decimal
    required_source_count: Decimal
    bridged_source_count: Decimal
    required_rule_link_count: Decimal
    bridged_rule_link_count: Decimal
    evidence_item_count: Decimal
    fresh_evidence_count: Decimal
    ambiguous_evidence_count: Decimal
    manual_escalation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    source_quorum_ratio: Decimal
    rule_linkage_completeness_ratio: Decimal
    freshness_ratio: Decimal
    ambiguity_pressure_ratio: Decimal
    manual_escalation_urgency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventSourceResolutionBridgeRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceResolutionBridgeReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventSourceResolutionBridgeReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_scope_count",
            "required_source_count",
            "bridged_source_count",
            "required_rule_link_count",
            "bridged_rule_link_count",
            "evidence_item_count",
            "fresh_evidence_count",
            "ambiguous_evidence_count",
            "manual_escalation_count",
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
            "source_quorum_ratio",
            "rule_linkage_completeness_ratio",
            "freshness_ratio",
            "ambiguity_pressure_ratio",
            "manual_escalation_urgency_ratio",
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


def build_research_event_source_resolution_bridge_report(
    aggregates: Iterable[ResearchEventSourceResolutionBridgeAggregate],
    *,
    config: ResearchEventSourceResolutionBridgeConfig,
    generated_at: datetime,
) -> ResearchEventSourceResolutionBridgeReport:
    if type(config) is not ResearchEventSourceResolutionBridgeConfig:
        raise ValueError("config must be a ResearchEventSourceResolutionBridgeConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _require_or_set_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_aggregates(aggregates)
    rows = tuple(_row_from_aggregate(value, config=config) for value in normalized)

    event_scope_count = _decimal_count(len(rows))
    required_source_count = _sum_counts(tuple(row.required_source_count for row in rows))
    bridged_source_count = _sum_counts(tuple(row.bridged_source_count for row in rows))
    required_rule_link_count = _sum_counts(
        tuple(row.required_rule_link_count for row in rows),
    )
    bridged_rule_link_count = _sum_counts(
        tuple(row.bridged_rule_link_count for row in rows),
    )
    evidence_item_count = _sum_counts(tuple(row.evidence_item_count for row in rows))
    fresh_evidence_count = _sum_counts(tuple(row.fresh_evidence_count for row in rows))
    ambiguous_evidence_count = _sum_counts(
        tuple(row.ambiguous_evidence_count for row in rows),
    )
    manual_escalation_count = _sum_counts(
        tuple(row.manual_escalation_count for row in rows),
    )
    metric_statuses = _metric_statuses(
        config=config,
        source_quorum_ratio=_ratio(bridged_source_count, required_source_count),
        rule_linkage_completeness_ratio=_ratio(
            bridged_rule_link_count,
            required_rule_link_count,
        ),
        freshness_ratio=_ratio(fresh_evidence_count, evidence_item_count),
        ambiguity_pressure_ratio=_ratio(ambiguous_evidence_count, evidence_item_count),
        manual_escalation_urgency_ratio=_ratio(
            manual_escalation_count,
            evidence_item_count,
        ),
    )

    return ResearchEventSourceResolutionBridgeReport(
        generated_at=generated_at,
        config_version=config.config_version,
        event_scope_count=event_scope_count,
        required_source_count=required_source_count,
        bridged_source_count=bridged_source_count,
        required_rule_link_count=required_rule_link_count,
        bridged_rule_link_count=bridged_rule_link_count,
        evidence_item_count=evidence_item_count,
        fresh_evidence_count=fresh_evidence_count,
        ambiguous_evidence_count=ambiguous_evidence_count,
        manual_escalation_count=manual_escalation_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        source_quorum_ratio=metric_statuses.source_quorum_ratio,
        rule_linkage_completeness_ratio=(
            metric_statuses.rule_linkage_completeness_ratio
        ),
        freshness_ratio=metric_statuses.freshness_ratio,
        ambiguity_pressure_ratio=metric_statuses.ambiguity_pressure_ratio,
        manual_escalation_urgency_ratio=(
            metric_statuses.manual_escalation_urgency_ratio
        ),
        status=_summary_status(rows, metric_statuses),
        reason_codes=_report_reason_codes(rows, metric_statuses),
        rows=rows,
    )


def research_event_source_resolution_bridge_report_payload(
    report: ResearchEventSourceResolutionBridgeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSourceResolutionBridgeReport:
        raise ValueError("report must be a ResearchEventSourceResolutionBridgeReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface("report", report)
    _require_or_set_digest(report)
    for row in report.rows:
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    payload = _payload_value(report)
    validate_research_event_source_resolution_bridge_report_payload(payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def validate_research_event_source_resolution_bridge_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


@dataclass(frozen=True)
class _MetricStatuses:
    source_quorum_ratio: Decimal
    rule_linkage_completeness_ratio: Decimal
    freshness_ratio: Decimal
    ambiguity_pressure_ratio: Decimal
    manual_escalation_urgency_ratio: Decimal
    source_quorum_status: str
    rule_linkage_completeness_status: str
    freshness_status: str
    ambiguity_pressure_status: str
    manual_escalation_urgency_status: str


def _row_from_aggregate(
    aggregate: ResearchEventSourceResolutionBridgeAggregate,
    *,
    config: ResearchEventSourceResolutionBridgeConfig,
) -> ResearchEventSourceResolutionBridgeRow:
    metric_statuses = _metric_statuses(
        config=config,
        source_quorum_ratio=_ratio(
            aggregate.bridged_source_count,
            aggregate.required_source_count,
        ),
        rule_linkage_completeness_ratio=_ratio(
            aggregate.bridged_rule_link_count,
            aggregate.required_rule_link_count,
        ),
        freshness_ratio=_ratio(
            aggregate.fresh_evidence_count,
            aggregate.evidence_item_count,
        ),
        ambiguity_pressure_ratio=_ratio(
            aggregate.ambiguous_evidence_count,
            aggregate.evidence_item_count,
        ),
        manual_escalation_urgency_ratio=_ratio(
            aggregate.manual_escalation_count,
            aggregate.evidence_item_count,
        ),
    )
    return ResearchEventSourceResolutionBridgeRow(
        event_scope=aggregate.event_scope,
        required_source_count=aggregate.required_source_count,
        bridged_source_count=aggregate.bridged_source_count,
        required_rule_link_count=aggregate.required_rule_link_count,
        bridged_rule_link_count=aggregate.bridged_rule_link_count,
        evidence_item_count=aggregate.evidence_item_count,
        fresh_evidence_count=aggregate.fresh_evidence_count,
        ambiguous_evidence_count=aggregate.ambiguous_evidence_count,
        manual_escalation_count=aggregate.manual_escalation_count,
        source_quorum_ratio=metric_statuses.source_quorum_ratio,
        rule_linkage_completeness_ratio=(
            metric_statuses.rule_linkage_completeness_ratio
        ),
        freshness_ratio=metric_statuses.freshness_ratio,
        ambiguity_pressure_ratio=metric_statuses.ambiguity_pressure_ratio,
        manual_escalation_urgency_ratio=(
            metric_statuses.manual_escalation_urgency_ratio
        ),
        status=_worst_status(metric_statuses),
        reason_codes=_metric_reason_codes(metric_statuses),
    )


def _metric_statuses(
    *,
    config: ResearchEventSourceResolutionBridgeConfig,
    source_quorum_ratio: Decimal,
    rule_linkage_completeness_ratio: Decimal,
    freshness_ratio: Decimal,
    ambiguity_pressure_ratio: Decimal,
    manual_escalation_urgency_ratio: Decimal,
) -> _MetricStatuses:
    return _MetricStatuses(
        source_quorum_ratio=source_quorum_ratio,
        rule_linkage_completeness_ratio=rule_linkage_completeness_ratio,
        freshness_ratio=freshness_ratio,
        ambiguity_pressure_ratio=ambiguity_pressure_ratio,
        manual_escalation_urgency_ratio=manual_escalation_urgency_ratio,
        source_quorum_status=_lower_bound_status(
            source_quorum_ratio,
            minimum=config.min_source_quorum_ratio,
            block_floor=config.block_source_quorum_ratio,
        ),
        rule_linkage_completeness_status=_lower_bound_status(
            rule_linkage_completeness_ratio,
            minimum=config.min_rule_linkage_completeness_ratio,
            block_floor=config.block_rule_linkage_completeness_ratio,
        ),
        freshness_status=_lower_bound_status(
            freshness_ratio,
            minimum=config.min_freshness_ratio,
            block_floor=config.block_freshness_ratio,
        ),
        ambiguity_pressure_status=_upper_bound_status(
            ambiguity_pressure_ratio,
            watch_threshold=config.watch_ambiguity_pressure_ratio,
            block_threshold=config.block_ambiguity_pressure_ratio,
        ),
        manual_escalation_urgency_status=_upper_bound_status(
            manual_escalation_urgency_ratio,
            watch_threshold=config.watch_manual_escalation_urgency_ratio,
            block_threshold=config.block_manual_escalation_urgency_ratio,
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


def _worst_status(metric_statuses: _MetricStatuses) -> str:
    statuses = (
        metric_statuses.source_quorum_status,
        metric_statuses.rule_linkage_completeness_status,
        metric_statuses.freshness_status,
        metric_statuses.ambiguity_pressure_status,
        metric_statuses.manual_escalation_urgency_status,
    )
    return max(statuses, key=lambda status: _STATUS_RANK[status])


def _summary_status(
    rows: tuple[ResearchEventSourceResolutionBridgeRow, ...],
    metric_statuses: _MetricStatuses,
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return _worst_status(metric_statuses)


def _metric_reason_codes(metric_statuses: _MetricStatuses) -> tuple[str, ...]:
    return (
        "source_quorum_" + metric_statuses.source_quorum_status,
        "rule_linkage_completeness_"
        + metric_statuses.rule_linkage_completeness_status,
        "freshness_" + metric_statuses.freshness_status,
        "ambiguity_pressure_" + metric_statuses.ambiguity_pressure_status,
        "manual_escalation_urgency_"
        + metric_statuses.manual_escalation_urgency_status,
    )


def _report_reason_codes(
    rows: tuple[ResearchEventSourceResolutionBridgeRow, ...],
    metric_statuses: _MetricStatuses,
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_source_resolution_bridge_scopes",)
    if _worst_status(metric_statuses) == "pass" and all(
        row.status == "pass" for row in rows
    ):
        return ("event_source_resolution_bridge_pass",)
    reason_codes = tuple(
        reason_code
        for reason_code in _metric_reason_codes(metric_statuses)
        if not reason_code.endswith("_pass")
    )
    if any(row.status == "block" for row in rows):
        reason_codes = reason_codes + ("event_source_resolution_bridge_scope_block",)
    elif any(row.status == "watch" for row in rows):
        reason_codes = reason_codes + ("event_source_resolution_bridge_scope_watch",)
    if reason_codes:
        return reason_codes
    return ("event_source_resolution_bridge_watch",)


def _normalize_aggregates(
    values: Iterable[ResearchEventSourceResolutionBridgeAggregate],
) -> tuple[ResearchEventSourceResolutionBridgeAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        aggregates = tuple(values)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    for value in aggregates:
        if type(value) is not ResearchEventSourceResolutionBridgeAggregate:
            raise ValueError(
                "aggregates must contain ResearchEventSourceResolutionBridgeAggregate values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("aggregate", value)
        _require_or_set_digest(value)
    rows = tuple(sorted(aggregates, key=lambda value: value.event_scope))
    if len({value.event_scope for value in rows}) != len(rows):
        raise ValueError("aggregates must be unique by event_scope")
    return rows


def _normalize_rows(
    values: Iterable[ResearchEventSourceResolutionBridgeRow],
) -> tuple[ResearchEventSourceResolutionBridgeRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain bridge rows")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must contain bridge rows") from exc
    for row in rows:
        if type(row) is not ResearchEventSourceResolutionBridgeRow:
            raise ValueError("rows must contain bridge rows")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_scope))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted")
    if len({row.event_scope for row in rows}) != len(rows):
        raise ValueError("rows must be unique by event_scope")
    return rows


def _validate_aggregate_consistency(
    aggregate: ResearchEventSourceResolutionBridgeAggregate,
) -> None:
    if aggregate.required_source_count <= _ZERO:
        raise ValueError("required_source_count must be positive")
    if aggregate.required_rule_link_count <= _ZERO:
        raise ValueError("required_rule_link_count must be positive")
    if aggregate.evidence_item_count <= _ZERO:
        raise ValueError("evidence_item_count must be positive")
    if aggregate.bridged_source_count > aggregate.required_source_count:
        raise ValueError("bridged_source_count must be at most required_source_count")
    if aggregate.bridged_rule_link_count > aggregate.required_rule_link_count:
        raise ValueError(
            "bridged_rule_link_count must be at most required_rule_link_count",
        )
    for field_name in (
        "fresh_evidence_count",
        "ambiguous_evidence_count",
        "manual_escalation_count",
    ):
        if getattr(aggregate, field_name) > aggregate.evidence_item_count:
            raise ValueError(f"{field_name} must be at most evidence_item_count")


def _validate_row_consistency(row: ResearchEventSourceResolutionBridgeRow) -> None:
    _validate_aggregate_consistency(
        ResearchEventSourceResolutionBridgeAggregate(
            event_scope=row.event_scope,
            required_source_count=row.required_source_count,
            bridged_source_count=row.bridged_source_count,
            required_rule_link_count=row.required_rule_link_count,
            bridged_rule_link_count=row.bridged_rule_link_count,
            evidence_item_count=row.evidence_item_count,
            fresh_evidence_count=row.fresh_evidence_count,
            ambiguous_evidence_count=row.ambiguous_evidence_count,
            manual_escalation_count=row.manual_escalation_count,
        ),
    )
    expected_ratios = {
        "source_quorum_ratio": _ratio(
            row.bridged_source_count,
            row.required_source_count,
        ),
        "rule_linkage_completeness_ratio": _ratio(
            row.bridged_rule_link_count,
            row.required_rule_link_count,
        ),
        "freshness_ratio": _ratio(row.fresh_evidence_count, row.evidence_item_count),
        "ambiguity_pressure_ratio": _ratio(
            row.ambiguous_evidence_count,
            row.evidence_item_count,
        ),
        "manual_escalation_urgency_ratio": _ratio(
            row.manual_escalation_count,
            row.evidence_item_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(row, field_name) != expected:
            raise ValueError(f"{field_name} must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchEventSourceResolutionBridgeReport) -> None:
    if report.event_scope_count != _decimal_count(len(report.rows)):
        raise ValueError("event_scope_count must match rows")
    for field_name in (
        "required_source_count",
        "bridged_source_count",
        "required_rule_link_count",
        "bridged_rule_link_count",
        "evidence_item_count",
        "fresh_evidence_count",
        "ambiguous_evidence_count",
        "manual_escalation_count",
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
        "source_quorum_ratio": _ratio(
            report.bridged_source_count,
            report.required_source_count,
        ),
        "rule_linkage_completeness_ratio": _ratio(
            report.bridged_rule_link_count,
            report.required_rule_link_count,
        ),
        "freshness_ratio": _ratio(
            report.fresh_evidence_count,
            report.evidence_item_count,
        ),
        "ambiguity_pressure_ratio": _ratio(
            report.ambiguous_evidence_count,
            report.evidence_item_count,
        ),
        "manual_escalation_urgency_ratio": _ratio(
            report.manual_escalation_count,
            report.evidence_item_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.event_scope)):
        raise ValueError("rows must be sorted")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        _MetricStatuses(
            source_quorum_ratio=report.source_quorum_ratio,
            rule_linkage_completeness_ratio=report.rule_linkage_completeness_ratio,
            freshness_ratio=report.freshness_ratio,
            ambiguity_pressure_ratio=report.ambiguity_pressure_ratio,
            manual_escalation_urgency_ratio=(
                report.manual_escalation_urgency_ratio
            ),
            source_quorum_status=_status_from_metric_reason(
                "source_quorum",
                report.reason_codes,
                fallback="pass",
            ),
            rule_linkage_completeness_status=_status_from_metric_reason(
                "rule_linkage_completeness",
                report.reason_codes,
                fallback="pass",
            ),
            freshness_status=_status_from_metric_reason(
                "freshness",
                report.reason_codes,
                fallback="pass",
            ),
            ambiguity_pressure_status=_status_from_metric_reason(
                "ambiguity_pressure",
                report.reason_codes,
                fallback="pass",
            ),
            manual_escalation_urgency_status=_status_from_metric_reason(
                "manual_escalation_urgency",
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
    rows: tuple[ResearchEventSourceResolutionBridgeRow, ...],
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
    return max(suffixes, key=lambda status: _STATUS_RANK[status])


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


def _require_lower_threshold_pair(
    min_field_name: str,
    minimum: Decimal,
    block_field_name: str,
    block_floor: Decimal,
) -> None:
    if minimum <= _ZERO:
        raise ValueError(f"{min_field_name} must be positive")
    if block_floor >= minimum:
        raise ValueError(f"{block_field_name} must be below {min_field_name}")


def _require_upper_threshold_pair(
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
