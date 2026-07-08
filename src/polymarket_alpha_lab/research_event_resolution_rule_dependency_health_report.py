"""Pure aggregate report for event resolution rule dependency health."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DEPENDENCY_HEALTH_REPORT_CONFIG_VERSION = (
    "research-event-resolution-rule-dependency-health-report-v0"
)

_DECIMAL_CONTEXT = Context(prec=64)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUSES = ("pass", "watch", "block")
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "".join(("raw", "_", "candidate")),
    "".join(("candidate", "_", "id")),
    "".join(("market", "_", "id")),
    "".join(("market", "-", "id")),
    "".join(("market", "_", "slug")),
    "".join(("market", "-", "slug")),
    "".join(("market", "_", "ques", "tion")),
    "".join(("market", "-", "ques", "tion")),
    "".join(("source", "_", "url")),
    "".join(("source", "-", "url")),
    "".join(("source", "_", "text")),
    "".join(("source", "-", "text")),
    "".join(("http", "://")),
    "".join(("https", "://")),
    "".join(("postgres", "ql", "://")),
    "".join(("mysql", "://")),
    "".join(("dsn",)),
    "".join(("table", "_", "name")),
    "".join(("private", "_", "tok", "en")),
    "".join(("tok", "en", "-secret")),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DEPENDENCY_HEALTH_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionRuleDependencyHealthAggregate",
    "ResearchEventResolutionRuleDependencyHealthConfig",
    "ResearchEventResolutionRuleDependencyHealthReport",
    "ResearchEventResolutionRuleDependencyHealthRow",
    "build_research_event_resolution_rule_dependency_health_report",
    "research_event_resolution_rule_dependency_health_report_payload",
    "validate_research_event_resolution_rule_dependency_health_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDependencyHealthConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DEPENDENCY_HEALTH_REPORT_CONFIG_VERSION
    )
    fresh_official_rule_age_seconds: Decimal = Decimal("3600.000000")
    stale_official_rule_age_seconds: Decimal = Decimal("86400.000000")
    watch_ambiguity_pressure: Decimal = Decimal("0.250000")
    block_ambiguity_pressure: Decimal = Decimal("0.600000")
    watch_impacted_research_packet_count: Decimal = Decimal("2.000000")
    block_impacted_research_packet_count: Decimal = Decimal("5.000000")
    watch_manual_escalation_urgency_score: Decimal = Decimal("0.500000")
    block_manual_escalation_urgency_score: Decimal = Decimal("0.800000")
    watch_dependency_health_score: Decimal = Decimal("0.250000")
    block_dependency_health_score: Decimal = Decimal("0.750000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionRuleDependencyHealthConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEventResolutionRuleDependencyHealthConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_DEPENDENCY_HEALTH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_official_rule_age_seconds",
            "stale_official_rule_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_ambiguity_pressure",
            "block_ambiguity_pressure",
            "watch_manual_escalation_urgency_score",
            "block_manual_escalation_urgency_score",
            "watch_dependency_health_score",
            "block_dependency_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_impacted_research_packet_count",
            "block_impacted_research_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.stale_official_rule_age_seconds <= self.fresh_official_rule_age_seconds:
            raise ValueError(
                "stale_official_rule_age_seconds must exceed "
                "fresh_official_rule_age_seconds",
            )
        _require_threshold_pair(
            "ambiguity_pressure",
            self.watch_ambiguity_pressure,
            self.block_ambiguity_pressure,
        )
        _require_threshold_pair(
            "impacted_research_packet_count",
            self.watch_impacted_research_packet_count,
            self.block_impacted_research_packet_count,
        )
        _require_threshold_pair(
            "manual_escalation_urgency",
            self.watch_manual_escalation_urgency_score,
            self.block_manual_escalation_urgency_score,
        )
        _require_threshold_pair(
            "dependency_health_score",
            self.watch_dependency_health_score,
            self.block_dependency_health_score,
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _apply_or_verify_digest(self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDependencyHealthAggregate:
    aggregate_key: str
    dependent_rule_count: Decimal
    official_rule_observed_at: datetime
    ambiguous_rule_count: Decimal = _ZERO
    impacted_research_packet_count: Decimal = _ZERO
    manual_escalation_urgency_score: Decimal = _ZERO
    private_context_values: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionRuleDependencyHealthAggregate does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "aggregate",
            self,
            ResearchEventResolutionRuleDependencyHealthAggregate,
        )
        _require_private_string("aggregate_key", self.aggregate_key)
        object.__setattr__(
            self,
            "dependent_rule_count",
            _normalize_positive_count("dependent_rule_count", self.dependent_rule_count),
        )
        object.__setattr__(
            self,
            "official_rule_observed_at",
            _as_utc("official_rule_observed_at", self.official_rule_observed_at),
        )
        for field_name in (
            "ambiguous_rule_count",
            "impacted_research_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_escalation_urgency_score",
            _normalize_probability(
                "manual_escalation_urgency_score",
                self.manual_escalation_urgency_score,
            ),
        )
        object.__setattr__(
            self,
            "private_context_values",
            _normalize_private_context_values(self.private_context_values),
        )
        if self.ambiguous_rule_count > self.dependent_rule_count:
            raise ValueError("ambiguous_rule_count must be at most dependent_rule_count")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDependencyHealthRow:
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    dependent_rule_count: Decimal
    official_rule_age_seconds: Decimal
    official_rule_freshness_score: Decimal
    ambiguous_rule_count: Decimal
    ambiguity_pressure: Decimal
    impacted_research_packet_count: Decimal
    manual_escalation_urgency_score: Decimal
    dependency_health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionRuleDependencyHealthRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventResolutionRuleDependencyHealthRow)
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_sha256_digest("aggregate_row_hash", self.aggregate_row_hash)
        for field_name in (
            "dependent_rule_count",
            "aggregate_row_number",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_rule_age_seconds",
            "ambiguous_rule_count",
            "impacted_research_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_rule_freshness_score",
            "ambiguity_pressure",
            "manual_escalation_urgency_score",
            "dependency_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.ambiguous_rule_count > self.dependent_rule_count:
            raise ValueError("ambiguous_rule_count must be at most dependent_rule_count")
        if self.ambiguity_pressure != _ratio(
            self.ambiguous_rule_count,
            self.dependent_rule_count,
        ):
            raise ValueError("ambiguity_pressure must match counts")
        _require_hard_flags(self)
        _reject_unsafe_public_surface("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventResolutionRuleDependencyHealthReport:
    generated_at: datetime
    config_version: str
    aggregate_row_count: Decimal
    dependent_rule_count: Decimal
    ambiguous_rule_count: Decimal
    impacted_research_packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_official_rule_freshness_score: Decimal
    ambiguity_pressure: Decimal
    max_manual_escalation_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionRuleDependencyHealthRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventResolutionRuleDependencyHealthReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventResolutionRuleDependencyHealthReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "aggregate_row_count",
            "dependent_rule_count",
            "ambiguous_rule_count",
            "impacted_research_packet_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_official_rule_freshness_score",
            "ambiguity_pressure",
            "max_manual_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        _reject_unsafe_public_surface("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_event_resolution_rule_dependency_health_report(
    aggregates: Iterable[ResearchEventResolutionRuleDependencyHealthAggregate],
    *,
    config: ResearchEventResolutionRuleDependencyHealthConfig,
    generated_at: datetime,
) -> ResearchEventResolutionRuleDependencyHealthReport:
    if type(config) is not ResearchEventResolutionRuleDependencyHealthConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionRuleDependencyHealthConfig",
        )
    _require_hard_flags(config)
    _reject_unsafe_public_surface("config", config)
    _verify_digest(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_aggregates(aggregates)
    for value in normalized:
        if value.official_rule_observed_at > generated_at:
            raise ValueError("official_rule_observed_at must not be after generated_at")

    prepared_rows = tuple(
        sorted(
            (
                _prepare_row(value, config=config, generated_at=generated_at)
                for value in normalized
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(value, aggregate_row_number=_count(index))
        for index, value in enumerate(prepared_rows, start=1)
    )
    return ResearchEventResolutionRuleDependencyHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        aggregate_row_count=_count(len(rows)),
        dependent_rule_count=_sum(tuple(row.dependent_rule_count for row in rows)),
        ambiguous_rule_count=_sum(tuple(row.ambiguous_rule_count for row in rows)),
        impacted_research_packet_count=_sum(
            tuple(row.impacted_research_packet_count for row in rows),
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_official_rule_freshness_score=_mean(
            tuple(row.official_rule_freshness_score for row in rows),
        ),
        ambiguity_pressure=_ratio(
            _sum(tuple(row.ambiguous_rule_count for row in rows)),
            _sum(tuple(row.dependent_rule_count for row in rows)),
        ),
        max_manual_escalation_urgency_score=max(
            (row.manual_escalation_urgency_score for row in rows),
            default=_ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows, config=config),
        rows=rows,
    )


def research_event_resolution_rule_dependency_health_report_payload(
    report: ResearchEventResolutionRuleDependencyHealthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionRuleDependencyHealthReport:
        _require_hard_flags(report)
        _reject_unsafe_public_surface("report", report)
        _verify_digest(report)
        payload = _payload_value(report)
    elif type(report) is dict:
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionRuleDependencyHealthReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_resolution_rule_dependency_health_report_payload(payload)
    return payload


def validate_research_event_resolution_rule_dependency_health_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


@dataclass(frozen=True)
class _PreparedRow:
    aggregate_row_hash: str
    dependent_rule_count: Decimal
    official_rule_age_seconds: Decimal
    official_rule_freshness_score: Decimal
    ambiguous_rule_count: Decimal
    ambiguity_pressure: Decimal
    impacted_research_packet_count: Decimal
    manual_escalation_urgency_score: Decimal
    dependency_health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchEventResolutionRuleDependencyHealthAggregate,
    *,
    config: ResearchEventResolutionRuleDependencyHealthConfig,
    generated_at: datetime,
) -> _PreparedRow:
    age_seconds = _age_seconds(generated_at, value.official_rule_observed_at)
    freshness_score = _official_rule_freshness_score(age_seconds, config)
    ambiguity_pressure = _ratio(value.ambiguous_rule_count, value.dependent_rule_count)
    impact_pressure = _clamp_probability(
        value.impacted_research_packet_count
        / config.block_impacted_research_packet_count,
    )
    dependency_health_score = _clamp_probability(
        (
            (_ONE - freshness_score)
            + ambiguity_pressure
            + impact_pressure
            + value.manual_escalation_urgency_score
        )
        / _FOUR,
    )
    status = _row_status(
        official_rule_freshness_score=freshness_score,
        ambiguity_pressure=ambiguity_pressure,
        impacted_research_packet_count=value.impacted_research_packet_count,
        manual_escalation_urgency_score=value.manual_escalation_urgency_score,
        dependency_health_score=dependency_health_score,
        config=config,
    )
    return _PreparedRow(
        aggregate_row_hash=_aggregate_row_hash(value.aggregate_key),
        dependent_rule_count=value.dependent_rule_count,
        official_rule_age_seconds=age_seconds,
        official_rule_freshness_score=freshness_score,
        ambiguous_rule_count=value.ambiguous_rule_count,
        ambiguity_pressure=ambiguity_pressure,
        impacted_research_packet_count=value.impacted_research_packet_count,
        manual_escalation_urgency_score=value.manual_escalation_urgency_score,
        dependency_health_score=dependency_health_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            official_rule_freshness_score=freshness_score,
            ambiguity_pressure=ambiguity_pressure,
            impacted_research_packet_count=value.impacted_research_packet_count,
            manual_escalation_urgency_score=value.manual_escalation_urgency_score,
            config=config,
        ),
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
) -> ResearchEventResolutionRuleDependencyHealthRow:
    return ResearchEventResolutionRuleDependencyHealthRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=value.aggregate_row_hash,
        dependent_rule_count=value.dependent_rule_count,
        official_rule_age_seconds=value.official_rule_age_seconds,
        official_rule_freshness_score=value.official_rule_freshness_score,
        ambiguous_rule_count=value.ambiguous_rule_count,
        ambiguity_pressure=value.ambiguity_pressure,
        impacted_research_packet_count=value.impacted_research_packet_count,
        manual_escalation_urgency_score=value.manual_escalation_urgency_score,
        dependency_health_score=value.dependency_health_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _official_rule_freshness_score(
    age_seconds: Decimal,
    config: ResearchEventResolutionRuleDependencyHealthConfig,
) -> Decimal:
    if age_seconds <= config.fresh_official_rule_age_seconds:
        return _ONE
    if age_seconds >= config.stale_official_rule_age_seconds:
        return _ZERO
    return _clamp_probability(_ONE - (age_seconds / config.stale_official_rule_age_seconds))


def _row_status(
    *,
    official_rule_freshness_score: Decimal,
    ambiguity_pressure: Decimal,
    impacted_research_packet_count: Decimal,
    manual_escalation_urgency_score: Decimal,
    dependency_health_score: Decimal,
    config: ResearchEventResolutionRuleDependencyHealthConfig,
) -> str:
    if (
        official_rule_freshness_score == _ZERO
        or ambiguity_pressure >= config.block_ambiguity_pressure
        or impacted_research_packet_count >= config.block_impacted_research_packet_count
        or manual_escalation_urgency_score
        >= config.block_manual_escalation_urgency_score
        or dependency_health_score >= config.block_dependency_health_score
    ):
        return "block"
    if (
        official_rule_freshness_score <= Decimal("0.500000")
        or ambiguity_pressure >= config.watch_ambiguity_pressure
        or impacted_research_packet_count >= config.watch_impacted_research_packet_count
        or manual_escalation_urgency_score
        >= config.watch_manual_escalation_urgency_score
        or dependency_health_score >= config.watch_dependency_health_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    official_rule_freshness_score: Decimal,
    ambiguity_pressure: Decimal,
    impacted_research_packet_count: Decimal,
    manual_escalation_urgency_score: Decimal,
    config: ResearchEventResolutionRuleDependencyHealthConfig,
) -> tuple[str, ...]:
    codes = {f"dependency_health_{status}"}
    if official_rule_freshness_score == _ZERO:
        codes.add("official_rule_freshness_block")
    elif official_rule_freshness_score <= Decimal("0.500000"):
        codes.add("official_rule_freshness_watch")
    if ambiguity_pressure >= config.block_ambiguity_pressure:
        codes.add("ambiguity_pressure_block")
    elif ambiguity_pressure >= config.watch_ambiguity_pressure:
        codes.add("ambiguity_pressure_watch")
    if impacted_research_packet_count >= config.block_impacted_research_packet_count:
        codes.add("impacted_research_packets_block")
    elif impacted_research_packet_count >= config.watch_impacted_research_packet_count:
        codes.add("impacted_research_packets_watch")
    if (
        manual_escalation_urgency_score
        >= config.block_manual_escalation_urgency_score
    ):
        codes.add("manual_escalation_urgency_block")
    elif (
        manual_escalation_urgency_score
        >= config.watch_manual_escalation_urgency_score
    ):
        codes.add("manual_escalation_urgency_watch")
    return _normalize_reason_codes(tuple(sorted(codes)))


def _report_status(
    rows: tuple[ResearchEventResolutionRuleDependencyHealthRow, ...],
) -> str:
    if not rows:
        return "block"
    return max((row.status for row in rows), key=lambda status: _STATUS_RANK[status])


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionRuleDependencyHealthRow, ...],
    *,
    config: ResearchEventResolutionRuleDependencyHealthConfig,
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_rule_dependency_health_rows",)
    status = _report_status(rows)
    if status == "pass":
        return ("dependency_health_pass",)

    codes = {f"dependency_health_{status}"}
    if any(row.status == "block" for row in rows):
        codes.add("health_row_block")
    elif any(row.status == "watch" for row in rows):
        codes.add("health_row_watch")

    if any(row.official_rule_freshness_score == _ZERO for row in rows):
        codes.add("official_rule_freshness_block")
    elif any(row.official_rule_freshness_score <= Decimal("0.500000") for row in rows):
        codes.add("official_rule_freshness_watch")

    aggregate_ambiguity_pressure = _ratio(
        _sum(tuple(row.ambiguous_rule_count for row in rows)),
        _sum(tuple(row.dependent_rule_count for row in rows)),
    )
    if aggregate_ambiguity_pressure >= config.block_ambiguity_pressure:
        codes.add("ambiguity_pressure_block")
    elif aggregate_ambiguity_pressure >= config.watch_ambiguity_pressure:
        codes.add("ambiguity_pressure_watch")

    impacted_count = _sum(tuple(row.impacted_research_packet_count for row in rows))
    if impacted_count >= config.block_impacted_research_packet_count:
        codes.add("impacted_research_packets_block")
    elif impacted_count >= config.watch_impacted_research_packet_count:
        codes.add("impacted_research_packets_watch")

    max_manual = max(
        (row.manual_escalation_urgency_score for row in rows),
        default=_ZERO,
    )
    if max_manual >= config.block_manual_escalation_urgency_score:
        codes.add("manual_escalation_urgency_block")
    elif max_manual >= config.watch_manual_escalation_urgency_score:
        codes.add("manual_escalation_urgency_watch")

    return _normalize_reason_codes(tuple(sorted(codes)))


def _prepared_row_sort_key(row: _PreparedRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.dependency_health_score,
        -row.manual_escalation_urgency_score,
        row.aggregate_row_hash,
    )


def _row_sort_key(
    row: ResearchEventResolutionRuleDependencyHealthRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.dependency_health_score,
        -row.manual_escalation_urgency_score,
        row.aggregate_row_hash,
    )


def _normalize_aggregates(
    values: Iterable[ResearchEventResolutionRuleDependencyHealthAggregate],
) -> tuple[ResearchEventResolutionRuleDependencyHealthAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        aggregates = tuple(values)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    seen: set[str] = set()
    for value in aggregates:
        if type(value) is not ResearchEventResolutionRuleDependencyHealthAggregate:
            raise ValueError(
                "aggregates must contain ResearchEventResolutionRuleDependencyHealthAggregate values",
            )
        _require_hard_flags(value)
        if value.aggregate_key in seen:
            raise ValueError("aggregates must be unique by aggregate_key")
        seen.add(value.aggregate_key)
    return aggregates


def _normalize_rows(
    rows: Iterable[ResearchEventResolutionRuleDependencyHealthRow],
) -> tuple[ResearchEventResolutionRuleDependencyHealthRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    previous_number = _ZERO
    hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventResolutionRuleDependencyHealthRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionRuleDependencyHealthRow values",
            )
        _require_hard_flags(row)
        _verify_digest(row)
        if row.aggregate_row_number <= previous_number:
            raise ValueError("rows must use deterministic aggregate_row_number sequence")
        previous_number = row.aggregate_row_number
        if row.aggregate_row_hash in hashes:
            raise ValueError("rows must be unique by aggregate_row_hash")
        hashes.add(row.aggregate_row_hash)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _validate_row_consistency(
    row: ResearchEventResolutionRuleDependencyHealthRow,
) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("dependency_health_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(
        reason_code.endswith("_watch") for reason_code in row.reason_codes
    ):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(
        reason_code.endswith("_block") for reason_code in row.reason_codes
    ):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchEventResolutionRuleDependencyHealthReport,
) -> None:
    if report.aggregate_row_count != _count(len(report.rows)):
        raise ValueError("aggregate_row_count must match rows")
    for field_name in (
        "dependent_rule_count",
        "ambiguous_rule_count",
        "impacted_research_packet_count",
    ):
        expected = _sum(tuple(getattr(row, field_name) for row in report.rows))
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_official_rule_freshness_score != _mean(
        tuple(row.official_rule_freshness_score for row in report.rows),
    ):
        raise ValueError("average_official_rule_freshness_score must match rows")
    if report.ambiguity_pressure != _ratio(
        report.ambiguous_rule_count,
        report.dependent_rule_count,
    ):
        raise ValueError("ambiguity_pressure must match rows")
    if report.max_manual_escalation_urgency_score != max(
        (row.manual_escalation_urgency_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_manual_escalation_urgency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _status_count(
    rows: tuple[ResearchEventResolutionRuleDependencyHealthRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    suffixes: list[str] = []
    for reason_code in reason_codes:
        suffix = reason_code.rsplit("_", 1)[-1]
        if suffix in _STATUSES:
            suffixes.append(suffix)
    if not suffixes:
        raise ValueError("reason_codes must include status suffix")
    return max(suffixes, key=lambda status: _STATUS_RANK[status])


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = (
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _quantize(value)


def _sum(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return _quantize(Decimal(value))


def _aggregate_row_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


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


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank string")


def _normalize_private_context_values(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("private_context_values must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value or value.strip() != value:
            raise ValueError("private_context_values must contain nonblank strings")
        if not any(character in value for character in ("-", "_", ":", "/", ".")):
            raise ValueError("private_context_values must contain trace references")
        normalized.append(value)
    return tuple(normalized)


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


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _is_sha256_hex(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_threshold_pair(label: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value <= watch_value:
        raise ValueError(f"block_{label} must exceed watch_{label}")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANTUM, rounding=ROUND_HALF_UP)


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


def _apply_or_verify_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_validation_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest does not match public payload")


def _verify_digest(value: object) -> None:
    current = getattr(value, _DIGEST_FIELD)
    if type(current) is not str or not _is_sha256_hex(current):
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    if current != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest does not match public payload")


def _derived_validation_digest(value: object) -> str:
    encoded = json.dumps(
        _canonical_digest_value(value, skip_current_digest=True),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _canonical_digest_value(value: object, *, skip_current_digest: bool) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_digest_value(
                getattr(value, field.name),
                skip_current_digest=False,
            )
            for field in fields(value)
            if not (skip_current_digest and field.name == _DIGEST_FIELD)
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
        return [
            _canonical_digest_value(item, skip_current_digest=False)
            for item in value
        ]
    if isinstance(value, list):
        return [
            _canonical_digest_value(item, skip_current_digest=False)
            for item in value
        ]
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if not (skip_current_digest and key == _DIGEST_FIELD):
                result[key] = _canonical_digest_value(
                    item,
                    skip_current_digest=False,
                )
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
            if type(current) is not str or not _is_sha256_hex(current):
                raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
            expected = _derived_validation_digest(value)
            if current != expected:
                raise ValueError("derived_validation_digest does not match public payload")
        for item in value.values():
            _validate_payload_digest_tree(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _is_sha256_hex(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
