"""Pure aggregate report for resolution outcome evidence gaps."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any


CONFIG_VERSION = "research-resolution-outcome-evidence-gap-report-v0"
OUTCOME_EVIDENCE_GAP_STATUSES = ("pass", "watch", "block")

_DIGEST_FIELD = "derived_validation_digest"
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_OUTCOME_GROUP_DISALLOWED_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "://",
    "/",
    "?",
    "#",
    ".",
)
_OUTCOME_GROUP_DISALLOWED_TERMS = (
    "condition",
    "id",
    "market",
    "question",
    "raw",
    "slug",
    "source",
    "url",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "condition_id",
    "event_id",
    "event_slug",
    "http://",
    "https://",
    "market_id",
    "market_slug",
    "raw_market",
    "raw_source",
    "source_id",
    "source_reference",
    "source_url",
    "www.",
    "://",
)


@dataclass(frozen=True)
class ResearchResolutionOutcomeEvidenceGapReportConfig:
    config_version: str = CONFIG_VERSION
    watch_official_evidence_coverage_ratio: Decimal = Decimal("0.900000")
    block_official_evidence_coverage_ratio: Decimal = Decimal("0.700000")
    watch_independent_corroboration_ratio: Decimal = Decimal("0.800000")
    block_independent_corroboration_ratio: Decimal = Decimal("0.500000")
    watch_rule_ambiguity_ratio: Decimal = Decimal("0.150000")
    block_rule_ambiguity_ratio: Decimal = Decimal("0.300000")
    watch_stale_outcome_evidence_ratio: Decimal = Decimal("0.200000")
    block_stale_outcome_evidence_ratio: Decimal = Decimal("0.400000")
    watch_escalation_urgency_ratio: Decimal = Decimal("0.250000")
    block_escalation_urgency_ratio: Decimal = Decimal("0.500000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionOutcomeEvidenceGapReportConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchResolutionOutcomeEvidenceGapReportConfig)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_official_evidence_coverage_ratio",
            "block_official_evidence_coverage_ratio",
            "watch_independent_corroboration_ratio",
            "block_independent_corroboration_ratio",
            "watch_rule_ambiguity_ratio",
            "block_rule_ambiguity_ratio",
            "watch_stale_outcome_evidence_ratio",
            "block_stale_outcome_evidence_ratio",
            "watch_escalation_urgency_ratio",
            "block_escalation_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.block_official_evidence_coverage_ratio
            > self.watch_official_evidence_coverage_ratio
        ):
            raise ValueError(
                "block_official_evidence_coverage_ratio must not exceed "
                "watch_official_evidence_coverage_ratio",
            )
        if (
            self.block_independent_corroboration_ratio
            > self.watch_independent_corroboration_ratio
        ):
            raise ValueError(
                "block_independent_corroboration_ratio must not exceed "
                "watch_independent_corroboration_ratio",
            )
        if self.block_rule_ambiguity_ratio < self.watch_rule_ambiguity_ratio:
            raise ValueError(
                "block_rule_ambiguity_ratio must cover watch_rule_ambiguity_ratio",
            )
        if self.block_stale_outcome_evidence_ratio < self.watch_stale_outcome_evidence_ratio:
            raise ValueError(
                "block_stale_outcome_evidence_ratio must cover "
                "watch_stale_outcome_evidence_ratio",
            )
        if self.block_escalation_urgency_ratio < self.watch_escalation_urgency_ratio:
            raise ValueError(
                "block_escalation_urgency_ratio must cover watch_escalation_urgency_ratio",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_surface("config", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeEvidenceGapAggregate:
    outcome_group: str
    outcome_count: Decimal
    official_evidence_count: Decimal
    independently_corroborated_count: Decimal
    rule_ambiguous_count: Decimal
    stale_outcome_evidence_count: Decimal
    escalation_due_count: Decimal
    max_outcome_evidence_age_seconds: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionOutcomeEvidenceGapAggregate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("aggregate", self, ResearchResolutionOutcomeEvidenceGapAggregate)
        _require_outcome_group("outcome_group", self.outcome_group)
        for field_name in (
            "outcome_count",
            "official_evidence_count",
            "independently_corroborated_count",
            "rule_ambiguous_count",
            "stale_outcome_evidence_count",
            "escalation_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_outcome_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "max_outcome_evidence_age_seconds",
                self.max_outcome_evidence_age_seconds,
            ),
        )
        _validate_aggregate_counts(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface("aggregate", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchResolutionOutcomeEvidenceGapRow:
    outcome_group: str
    status: str
    outcome_count: Decimal
    official_evidence_count: Decimal
    missing_official_evidence_count: Decimal
    independently_corroborated_count: Decimal
    uncorroborated_evidence_count: Decimal
    rule_ambiguous_count: Decimal
    stale_outcome_evidence_count: Decimal
    escalation_due_count: Decimal
    official_evidence_coverage_ratio: Decimal
    independent_corroboration_ratio: Decimal
    rule_ambiguity_ratio: Decimal
    stale_outcome_evidence_ratio: Decimal
    escalation_urgency_ratio: Decimal
    max_outcome_evidence_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchResolutionOutcomeEvidenceGapRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchResolutionOutcomeEvidenceGapRow)
        _require_outcome_group("outcome_group", self.outcome_group)
        _require_status("status", self.status)
        for field_name in (
            "outcome_count",
            "official_evidence_count",
            "missing_official_evidence_count",
            "independently_corroborated_count",
            "uncorroborated_evidence_count",
            "rule_ambiguous_count",
            "stale_outcome_evidence_count",
            "escalation_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_evidence_coverage_ratio",
            "independent_corroboration_ratio",
            "rule_ambiguity_ratio",
            "stale_outcome_evidence_ratio",
            "escalation_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_outcome_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "max_outcome_evidence_age_seconds",
                self.max_outcome_evidence_age_seconds,
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
class ResearchResolutionOutcomeEvidenceGapReport:
    generated_at: datetime
    config_version: str
    status: str
    outcome_group_count: Decimal
    outcome_count: Decimal
    official_evidence_count: Decimal
    missing_official_evidence_count: Decimal
    independently_corroborated_count: Decimal
    uncorroborated_evidence_count: Decimal
    rule_ambiguous_count: Decimal
    stale_outcome_evidence_count: Decimal
    escalation_due_count: Decimal
    official_evidence_coverage_ratio: Decimal
    independent_corroboration_ratio: Decimal
    rule_ambiguity_ratio: Decimal
    stale_outcome_evidence_ratio: Decimal
    escalation_urgency_ratio: Decimal
    max_outcome_evidence_age_seconds: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rows: tuple[ResearchResolutionOutcomeEvidenceGapRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchResolutionOutcomeEvidenceGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchResolutionOutcomeEvidenceGapReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "outcome_group_count",
            "outcome_count",
            "official_evidence_count",
            "missing_official_evidence_count",
            "independently_corroborated_count",
            "uncorroborated_evidence_count",
            "rule_ambiguous_count",
            "stale_outcome_evidence_count",
            "escalation_due_count",
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
            "official_evidence_coverage_ratio",
            "independent_corroboration_ratio",
            "rule_ambiguity_ratio",
            "stale_outcome_evidence_ratio",
            "escalation_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_outcome_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "max_outcome_evidence_age_seconds",
                self.max_outcome_evidence_age_seconds,
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


def build_research_resolution_outcome_evidence_gap_report(
    aggregates: Iterable[ResearchResolutionOutcomeEvidenceGapAggregate],
    *,
    config: ResearchResolutionOutcomeEvidenceGapReportConfig,
    generated_at: datetime,
) -> ResearchResolutionOutcomeEvidenceGapReport:
    if type(config) is not ResearchResolutionOutcomeEvidenceGapReportConfig:
        raise ValueError(
            "config must be a ResearchResolutionOutcomeEvidenceGapReportConfig",
        )
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
    official_evidence_count = _sum_decimal(row.official_evidence_count for row in rows)
    independently_corroborated_count = _sum_decimal(
        row.independently_corroborated_count for row in rows
    )
    rule_ambiguous_count = _sum_decimal(row.rule_ambiguous_count for row in rows)
    stale_outcome_evidence_count = _sum_decimal(
        row.stale_outcome_evidence_count for row in rows
    )
    escalation_due_count = _sum_decimal(row.escalation_due_count for row in rows)
    status = _report_status(rows)
    return ResearchResolutionOutcomeEvidenceGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        outcome_group_count=_decimal_count(len(rows)),
        outcome_count=outcome_count,
        official_evidence_count=official_evidence_count,
        missing_official_evidence_count=_quantize(outcome_count - official_evidence_count),
        independently_corroborated_count=independently_corroborated_count,
        uncorroborated_evidence_count=_quantize(
            official_evidence_count - independently_corroborated_count,
        ),
        rule_ambiguous_count=rule_ambiguous_count,
        stale_outcome_evidence_count=stale_outcome_evidence_count,
        escalation_due_count=escalation_due_count,
        official_evidence_coverage_ratio=_coverage_ratio(
            official_evidence_count,
            outcome_count,
        ),
        independent_corroboration_ratio=_corroboration_ratio(
            independently_corroborated_count,
            official_evidence_count,
        ),
        rule_ambiguity_ratio=_pressure_ratio(rule_ambiguous_count, outcome_count),
        stale_outcome_evidence_ratio=_pressure_ratio(
            stale_outcome_evidence_count,
            official_evidence_count,
        ),
        escalation_urgency_ratio=_pressure_ratio(escalation_due_count, outcome_count),
        max_outcome_evidence_age_seconds=_max_decimal(
            (row.max_outcome_evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        rows=rows,
        reason_codes=_report_reason_codes(rows, status=status),
    )


def research_resolution_outcome_evidence_gap_report_payload(
    report: ResearchResolutionOutcomeEvidenceGapReport,
) -> dict[str, object]:
    if type(report) is not ResearchResolutionOutcomeEvidenceGapReport:
        raise ValueError("report must be a ResearchResolutionOutcomeEvidenceGapReport")
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
    validate_research_resolution_outcome_evidence_gap_report_payload(payload)
    return payload


def validate_research_resolution_outcome_evidence_gap_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_surface("payload", payload)
    _require_public_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_aggregate(
    value: ResearchResolutionOutcomeEvidenceGapAggregate,
    *,
    config: ResearchResolutionOutcomeEvidenceGapReportConfig,
) -> ResearchResolutionOutcomeEvidenceGapRow:
    coverage_ratio = _coverage_ratio(value.official_evidence_count, value.outcome_count)
    corroboration_ratio = _corroboration_ratio(
        value.independently_corroborated_count,
        value.official_evidence_count,
    )
    rule_ambiguity_ratio = _pressure_ratio(value.rule_ambiguous_count, value.outcome_count)
    stale_evidence_ratio = _pressure_ratio(
        value.stale_outcome_evidence_count,
        value.official_evidence_count,
    )
    urgency_ratio = _pressure_ratio(value.escalation_due_count, value.outcome_count)
    reason_codes = _row_reason_codes(
        official_evidence_coverage_ratio=coverage_ratio,
        independent_corroboration_ratio=corroboration_ratio,
        rule_ambiguity_ratio=rule_ambiguity_ratio,
        stale_outcome_evidence_ratio=stale_evidence_ratio,
        escalation_urgency_ratio=urgency_ratio,
        config=config,
    )
    return ResearchResolutionOutcomeEvidenceGapRow(
        outcome_group=value.outcome_group,
        status=_status_from_reason_codes(reason_codes),
        outcome_count=value.outcome_count,
        official_evidence_count=value.official_evidence_count,
        missing_official_evidence_count=_quantize(
            value.outcome_count - value.official_evidence_count,
        ),
        independently_corroborated_count=value.independently_corroborated_count,
        uncorroborated_evidence_count=_quantize(
            value.official_evidence_count - value.independently_corroborated_count,
        ),
        rule_ambiguous_count=value.rule_ambiguous_count,
        stale_outcome_evidence_count=value.stale_outcome_evidence_count,
        escalation_due_count=value.escalation_due_count,
        official_evidence_coverage_ratio=coverage_ratio,
        independent_corroboration_ratio=corroboration_ratio,
        rule_ambiguity_ratio=rule_ambiguity_ratio,
        stale_outcome_evidence_ratio=stale_evidence_ratio,
        escalation_urgency_ratio=urgency_ratio,
        max_outcome_evidence_age_seconds=value.max_outcome_evidence_age_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    official_evidence_coverage_ratio: Decimal,
    independent_corroboration_ratio: Decimal,
    rule_ambiguity_ratio: Decimal,
    stale_outcome_evidence_ratio: Decimal,
    escalation_urgency_ratio: Decimal,
    config: ResearchResolutionOutcomeEvidenceGapReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_evidence_coverage_ratio < config.block_official_evidence_coverage_ratio:
        reasons.append("official_evidence_coverage_block")
    elif official_evidence_coverage_ratio < config.watch_official_evidence_coverage_ratio:
        reasons.append("official_evidence_coverage_watch")
    if independent_corroboration_ratio < config.block_independent_corroboration_ratio:
        reasons.append("independent_corroboration_block")
    elif independent_corroboration_ratio < config.watch_independent_corroboration_ratio:
        reasons.append("independent_corroboration_watch")
    if rule_ambiguity_ratio >= config.block_rule_ambiguity_ratio:
        reasons.append("rule_ambiguity_block")
    elif rule_ambiguity_ratio >= config.watch_rule_ambiguity_ratio:
        reasons.append("rule_ambiguity_watch")
    if stale_outcome_evidence_ratio >= config.block_stale_outcome_evidence_ratio:
        reasons.append("stale_outcome_evidence_block")
    elif stale_outcome_evidence_ratio >= config.watch_stale_outcome_evidence_ratio:
        reasons.append("stale_outcome_evidence_watch")
    if escalation_urgency_ratio >= config.block_escalation_urgency_ratio:
        reasons.append("escalation_urgency_block")
    elif escalation_urgency_ratio >= config.watch_escalation_urgency_ratio:
        reasons.append("escalation_urgency_watch")
    status = _status_from_pressure_reasons(tuple(reasons))
    return (f"outcome_evidence_gap_{status}", *reasons)


def _status_from_pressure_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    return reason_codes[0].removeprefix("outcome_evidence_gap_")


def _normalize_aggregates(
    values: Iterable[ResearchResolutionOutcomeEvidenceGapAggregate],
) -> tuple[ResearchResolutionOutcomeEvidenceGapAggregate, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchResolutionOutcomeEvidenceGapAggregate:
            raise ValueError(
                "aggregates must contain ResearchResolutionOutcomeEvidenceGapAggregate values",
            )
        _require_hard_flags(value)
        _reject_unsafe_public_surface("aggregate", value)
        _require_or_set_digest(value)
        if value.outcome_group in seen:
            raise ValueError("aggregates must not contain duplicate outcome_group values")
        seen.add(value.outcome_group)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchResolutionOutcomeEvidenceGapRow],
) -> tuple[ResearchResolutionOutcomeEvidenceGapRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must contain ResearchResolutionOutcomeEvidenceGapRow values")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchResolutionOutcomeEvidenceGapRow values",
        ) from exc
    for row in rows:
        if type(row) is not ResearchResolutionOutcomeEvidenceGapRow:
            raise ValueError("rows must contain ResearchResolutionOutcomeEvidenceGapRow values")
        _require_hard_flags(row)
        _reject_unsafe_public_surface("row", row)
        _require_or_set_digest(row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic outcome_group sort")
    if len({row.outcome_group for row in rows}) != len(rows):
        raise ValueError("rows must be unique by outcome_group")
    return rows


def _validate_aggregate_counts(
    value: ResearchResolutionOutcomeEvidenceGapAggregate,
) -> None:
    if value.official_evidence_count > value.outcome_count:
        raise ValueError("official_evidence_count must not exceed outcome_count")
    if value.independently_corroborated_count > value.official_evidence_count:
        raise ValueError(
            "independently_corroborated_count must not exceed official_evidence_count",
        )
    if value.rule_ambiguous_count > value.outcome_count:
        raise ValueError("rule_ambiguous_count must not exceed outcome_count")
    if value.stale_outcome_evidence_count > value.official_evidence_count:
        raise ValueError(
            "stale_outcome_evidence_count must not exceed official_evidence_count",
        )
    if value.escalation_due_count > value.outcome_count:
        raise ValueError("escalation_due_count must not exceed outcome_count")
    if value.outcome_count == _ZERO and value.max_outcome_evidence_age_seconds != _ZERO:
        raise ValueError(
            "max_outcome_evidence_age_seconds must be zero when outcome_count is zero",
        )


def _validate_row_consistency(row: ResearchResolutionOutcomeEvidenceGapRow) -> None:
    if row.missing_official_evidence_count != _quantize(
        row.outcome_count - row.official_evidence_count,
    ):
        raise ValueError("missing_official_evidence_count must match evidence gap")
    if row.uncorroborated_evidence_count != _quantize(
        row.official_evidence_count - row.independently_corroborated_count,
    ):
        raise ValueError("uncorroborated_evidence_count must match corroboration gap")
    if row.official_evidence_coverage_ratio != _coverage_ratio(
        row.official_evidence_count,
        row.outcome_count,
    ):
        raise ValueError("official_evidence_coverage_ratio must match counts")
    if row.independent_corroboration_ratio != _corroboration_ratio(
        row.independently_corroborated_count,
        row.official_evidence_count,
    ):
        raise ValueError("independent_corroboration_ratio must match counts")
    if row.rule_ambiguity_ratio != _pressure_ratio(
        row.rule_ambiguous_count,
        row.outcome_count,
    ):
        raise ValueError("rule_ambiguity_ratio must match counts")
    if row.stale_outcome_evidence_ratio != _pressure_ratio(
        row.stale_outcome_evidence_count,
        row.official_evidence_count,
    ):
        raise ValueError("stale_outcome_evidence_ratio must match counts")
    if row.escalation_urgency_ratio != _pressure_ratio(
        row.escalation_due_count,
        row.outcome_count,
    ):
        raise ValueError("escalation_urgency_ratio must match counts")
    if row.reason_codes[0] != f"outcome_evidence_gap_{row.status}":
        raise ValueError("reason_codes must start with status reason")
    if row.status != _status_from_pressure_reasons(row.reason_codes[1:]):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchResolutionOutcomeEvidenceGapReport,
) -> None:
    if report.outcome_group_count != _decimal_count(len(report.rows)):
        raise ValueError("outcome_group_count must match rows")
    if report.outcome_count != _sum_decimal(row.outcome_count for row in report.rows):
        raise ValueError("outcome_count must match rows")
    if report.official_evidence_count != _sum_decimal(
        row.official_evidence_count for row in report.rows
    ):
        raise ValueError("official_evidence_count must match rows")
    if report.missing_official_evidence_count != _quantize(
        report.outcome_count - report.official_evidence_count,
    ):
        raise ValueError("missing_official_evidence_count must match totals")
    if report.independently_corroborated_count != _sum_decimal(
        row.independently_corroborated_count for row in report.rows
    ):
        raise ValueError("independently_corroborated_count must match rows")
    if report.uncorroborated_evidence_count != _quantize(
        report.official_evidence_count - report.independently_corroborated_count,
    ):
        raise ValueError("uncorroborated_evidence_count must match totals")
    if report.rule_ambiguous_count != _sum_decimal(
        row.rule_ambiguous_count for row in report.rows
    ):
        raise ValueError("rule_ambiguous_count must match rows")
    if report.stale_outcome_evidence_count != _sum_decimal(
        row.stale_outcome_evidence_count for row in report.rows
    ):
        raise ValueError("stale_outcome_evidence_count must match rows")
    if report.escalation_due_count != _sum_decimal(
        row.escalation_due_count for row in report.rows
    ):
        raise ValueError("escalation_due_count must match rows")
    if report.official_evidence_coverage_ratio != _coverage_ratio(
        report.official_evidence_count,
        report.outcome_count,
    ):
        raise ValueError("official_evidence_coverage_ratio must match totals")
    if report.independent_corroboration_ratio != _corroboration_ratio(
        report.independently_corroborated_count,
        report.official_evidence_count,
    ):
        raise ValueError("independent_corroboration_ratio must match totals")
    if report.rule_ambiguity_ratio != _pressure_ratio(
        report.rule_ambiguous_count,
        report.outcome_count,
    ):
        raise ValueError("rule_ambiguity_ratio must match totals")
    if report.stale_outcome_evidence_ratio != _pressure_ratio(
        report.stale_outcome_evidence_count,
        report.official_evidence_count,
    ):
        raise ValueError("stale_outcome_evidence_ratio must match totals")
    if report.escalation_urgency_ratio != _pressure_ratio(
        report.escalation_due_count,
        report.outcome_count,
    ):
        raise ValueError("escalation_urgency_ratio must match totals")
    if report.max_outcome_evidence_age_seconds != _max_decimal(
        (row.max_outcome_evidence_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_outcome_evidence_age_seconds must match rows")
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
    row: ResearchResolutionOutcomeEvidenceGapRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_RANK[row.status],
        row.official_evidence_coverage_ratio,
        row.independent_corroboration_ratio,
        -row.rule_ambiguity_ratio,
        -row.stale_outcome_evidence_ratio,
        -row.escalation_urgency_ratio,
        row.outcome_group,
    )


def _report_status(rows: tuple[ResearchResolutionOutcomeEvidenceGapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionOutcomeEvidenceGapRow, ...],
    *,
    status: str,
) -> tuple[str, ...]:
    reasons = [f"outcome_evidence_gap_report_{status}"]
    for row in rows:
        for reason_code in row.reason_codes[1:]:
            if reason_code not in reasons:
                reasons.append(reason_code)
    return tuple(reasons)


def _status_count(
    rows: tuple[ResearchResolutionOutcomeEvidenceGapRow, ...],
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


def _coverage_ratio(official_count: Decimal, outcome_count: Decimal) -> Decimal:
    if outcome_count == _ZERO:
        return _ONE
    return _ratio(official_count, outcome_count)


def _corroboration_ratio(corroborated_count: Decimal, official_count: Decimal) -> Decimal:
    if official_count == _ZERO:
        return _ONE
    return _ratio(corroborated_count, official_count)


def _pressure_ratio(count: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _ratio(count, denominator)


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


def _require_outcome_group(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical outcome group")
    normalized = value.lower()
    if value != normalized:
        raise ValueError(f"{field_name} must be a lowercase outcome group")
    if any(fragment in normalized for fragment in _OUTCOME_GROUP_DISALLOWED_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain a locator")
    parts = normalized.split("_")
    if any(part in _OUTCOME_GROUP_DISALLOWED_TERMS for part in parts):
        raise ValueError(f"{field_name} must not contain raw identifier terms")
    if normalized.startswith("_") or normalized.endswith("_") or "__" in normalized:
        raise ValueError(f"{field_name} must be a canonical outcome group")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in normalized):
        raise ValueError(f"{field_name} must be a canonical outcome group")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in OUTCOME_EVIDENCE_GAP_STATUSES:
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
        if item.lower() != item:
            raise ValueError(f"{field_name} must contain lowercase values")
        if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_" for character in item):
            raise ValueError(f"{field_name} must contain canonical values")
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
        ("research_resolution_outcome_evidence_gap_report|" + canonical).encode("utf-8"),
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
        _reject_unsafe_public_surface(label, _payload_value(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


__all__ = (
    "CONFIG_VERSION",
    "OUTCOME_EVIDENCE_GAP_STATUSES",
    "ResearchResolutionOutcomeEvidenceGapAggregate",
    "ResearchResolutionOutcomeEvidenceGapReport",
    "ResearchResolutionOutcomeEvidenceGapReportConfig",
    "ResearchResolutionOutcomeEvidenceGapRow",
    "build_research_resolution_outcome_evidence_gap_report",
    "research_resolution_outcome_evidence_gap_report_payload",
    "validate_research_resolution_outcome_evidence_gap_report_payload",
)
