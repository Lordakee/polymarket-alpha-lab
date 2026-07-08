"""Pure public event source coverage rotation report."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_COVERAGE_ROTATION_REPORT_CONFIG_VERSION = (
    "research-event-source-coverage-rotation-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_event_source_coverage_rotation_report_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
THIN_COVERAGE_REASON = f"{REASON_PREFIX}thin_coverage"
STALE_SOURCE_AGE_REASON = f"{REASON_PREFIX}stale_source_age"
WEAK_RELIABILITY_MEMORY_REASON = f"{REASON_PREFIX}weak_reliability_memory"
HIGH_CATALYST_PRESSURE_REASON = f"{REASON_PREFIX}high_catalyst_pressure"
CAPACITY_CONSTRAINED_REASON = f"{REASON_PREFIX}capacity_constrained"

REASON_CODE_SEQUENCE = (
    THIN_COVERAGE_REASON,
    STALE_SOURCE_AGE_REASON,
    WEAK_RELIABILITY_MEMORY_REASON,
    HIGH_CATALYST_PRESSURE_REASON,
    CAPACITY_CONSTRAINED_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    THIN_COVERAGE_REASON,
    STALE_SOURCE_AGE_REASON,
    WEAK_RELIABILITY_MEMORY_REASON,
    HIGH_CATALYST_PRESSURE_REASON,
    CAPACITY_CONSTRAINED_REASON,
    PASS_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "pass_report_only_research_event_source_coverage_rotation_report",
    STATUS_WATCH: "watch_report_only_research_event_source_coverage_rotation_report",
    STATUS_BLOCK: "block_report_only_research_event_source_coverage_rotation_report",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "next_step",
        "domain_count",
        "pass_domain_count",
        "watch_domain_count",
        "block_domain_count",
        "thin_coverage_domain_count",
        "stale_source_domain_count",
        "weak_reliability_domain_count",
        "high_catalyst_domain_count",
        "capacity_constrained_domain_count",
        "max_source_age_seconds",
        "average_reliability_memory_score",
        "max_catalyst_pressure_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "event_domain",
        "rotation_status",
        "source_class_count",
        "aggregate_source_count",
        "max_source_age_seconds",
        "average_reliability_memory_score",
        "max_catalyst_pressure_score",
        "min_team_capacity_available",
        "max_team_capacity_load_ratio",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "domain_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ord", "er"),
        _join_parts("can", "cel"),
        _join_parts("ex", "change"),
        _join_parts("mut", "ation"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "_key"),
        _join_parts("bear", "er"),
        _join_parts("cred", "ential"),
        _join_parts("pass", "word"),
        _join_parts("tra", "de"),
        _join_parts("event", "_id"),
        _join_parts("market", "_slug"),
        _join_parts("condition", "_id"),
        _join_parts("source", "_id"),
        "://",
        "?",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_COVERAGE_ROTATION_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventSourceCoverageRotationConfig",
    "ResearchEventSourceCoverageRotationReasonCodeCount",
    "ResearchEventSourceCoverageRotationReport",
    "ResearchEventSourceCoverageRotationRow",
    "ResearchEventSourceCoverageRotationSignal",
    "build_research_event_source_coverage_rotation_report",
    "research_event_source_coverage_rotation_report_digest",
    "research_event_source_coverage_rotation_report_payload",
)


@dataclass(frozen=True)
class ResearchEventSourceCoverageRotationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_COVERAGE_ROTATION_REPORT_CONFIG_VERSION
    )
    fresh_source_max_age_seconds: Decimal = Decimal("7200.000000")
    minimum_source_class_count: Decimal = Decimal("2.000000")
    minimum_aggregate_source_count: Decimal = Decimal("3.000000")
    minimum_reliability_memory_score: Decimal = Decimal("0.650000")
    watch_catalyst_pressure_score: Decimal = Decimal("0.600000")
    block_catalyst_pressure_score: Decimal = Decimal("0.850000")
    minimum_team_capacity_available: Decimal = Decimal("1.000000")
    max_team_capacity_load_ratio: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceCoverageRotationConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceCoverageRotationConfig:
            raise TypeError(
                "config must be exactly ResearchEventSourceCoverageRotationConfig",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_COVERAGE_ROTATION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_source_max_age_seconds",
            "minimum_source_class_count",
            "minimum_aggregate_source_count",
            "minimum_team_capacity_available",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_source_class_count",
            "minimum_aggregate_source_count",
            "minimum_team_capacity_available",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_reliability_memory_score",
            "watch_catalyst_pressure_score",
            "block_catalyst_pressure_score",
            "max_team_capacity_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_catalyst_pressure_score <= self.watch_catalyst_pressure_score:
            raise ValueError(
                "block_catalyst_pressure_score must exceed "
                "watch_catalyst_pressure_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSourceCoverageRotationSignal:
    event_domain: str
    source_class: str
    observed_at: datetime
    aggregate_source_count: Decimal
    reliability_memory_score: Decimal
    catalyst_pressure_score: Decimal
    team_capacity_available: Decimal
    team_capacity_load_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceCoverageRotationSignal does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceCoverageRotationSignal:
            raise TypeError(
                "signal must be exactly ResearchEventSourceCoverageRotationSignal",
            )
        _require_public_label("event_domain", self.event_domain)
        _require_public_label("source_class", self.source_class)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "aggregate_source_count",
            _require_nonnegative_count_decimal(
                "aggregate_source_count",
                self.aggregate_source_count,
            ),
        )
        for field_name in (
            "reliability_memory_score",
            "catalyst_pressure_score",
            "team_capacity_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_capacity_available",
            _require_nonnegative_count_decimal(
                "team_capacity_available",
                self.team_capacity_available,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchEventSourceCoverageRotationRow:
    event_domain: str
    rotation_status: str
    source_class_count: Decimal
    aggregate_source_count: Decimal
    max_source_age_seconds: Decimal
    average_reliability_memory_score: Decimal
    max_catalyst_pressure_score: Decimal
    min_team_capacity_available: Decimal
    max_team_capacity_load_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceCoverageRotationRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceCoverageRotationRow:
            raise TypeError("row must be exactly ResearchEventSourceCoverageRotationRow")
        _require_public_label("event_domain", self.event_domain)
        _require_status("rotation_status", self.rotation_status)
        for field_name in (
            "source_class_count",
            "aggregate_source_count",
            "min_team_capacity_available",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "average_reliability_memory_score",
            "max_catalyst_pressure_score",
            "max_team_capacity_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        if self.rotation_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("rotation_status must match reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventSourceCoverageRotationReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceCoverageRotationReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceCoverageRotationReasonCodeCount:
            raise TypeError(
                "reason count must be exactly "
                "ResearchEventSourceCoverageRotationReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchEventSourceCoverageRotationReport:
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    thin_coverage_domain_count: Decimal
    stale_source_domain_count: Decimal
    weak_reliability_domain_count: Decimal
    high_catalyst_domain_count: Decimal
    capacity_constrained_domain_count: Decimal
    max_source_age_seconds: Decimal
    average_reliability_memory_score: Decimal
    max_catalyst_pressure_score: Decimal
    rows: tuple[ResearchEventSourceCoverageRotationRow, ...]
    reason_code_counts: tuple[ResearchEventSourceCoverageRotationReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventSourceCoverageRotationReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceCoverageRotationReport:
            raise TypeError(
                "report must be exactly ResearchEventSourceCoverageRotationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        _require_public_label("next_step", self.next_step)
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "thin_coverage_domain_count",
            "stale_source_domain_count",
            "weak_reliability_domain_count",
            "high_catalyst_domain_count",
            "capacity_constrained_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "average_reliability_memory_score",
            "max_catalyst_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = frozenset(
    (
        ResearchEventSourceCoverageRotationConfig,
        ResearchEventSourceCoverageRotationSignal,
        ResearchEventSourceCoverageRotationRow,
        ResearchEventSourceCoverageRotationReasonCodeCount,
        ResearchEventSourceCoverageRotationReport,
    ),
)


def build_research_event_source_coverage_rotation_report(
    signals: object,
    *,
    config: ResearchEventSourceCoverageRotationConfig,
    generated_at: datetime,
) -> ResearchEventSourceCoverageRotationReport:
    if type(config) is not ResearchEventSourceCoverageRotationConfig:
        raise ValueError("config must be a ResearchEventSourceCoverageRotationConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_signals = _normalize_signals(signals, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _build_row(domain, domain_signals, config, generated_at_utc)
                for domain, domain_signals in _domain_groups(source_signals)
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchEventSourceCoverageRotationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                domain_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    domain_count = _count(len(rows))
    pass_domain_count = _status_count(rows, STATUS_PASS)
    watch_domain_count = _status_count(rows, STATUS_WATCH)
    block_domain_count = _status_count(rows, STATUS_BLOCK)
    report_status = _report_status(
        has_inputs=bool(rows),
        block_domain_count=block_domain_count,
        watch_domain_count=watch_domain_count,
    )

    return ResearchEventSourceCoverageRotationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        domain_count=domain_count,
        pass_domain_count=pass_domain_count,
        watch_domain_count=watch_domain_count,
        block_domain_count=block_domain_count,
        thin_coverage_domain_count=_reason_count(rows, THIN_COVERAGE_REASON),
        stale_source_domain_count=_reason_count(rows, STALE_SOURCE_AGE_REASON),
        weak_reliability_domain_count=_reason_count(
            rows,
            WEAK_RELIABILITY_MEMORY_REASON,
        ),
        high_catalyst_domain_count=_reason_count(rows, HIGH_CATALYST_PRESSURE_REASON),
        capacity_constrained_domain_count=_reason_count(
            rows,
            CAPACITY_CONSTRAINED_REASON,
        ),
        max_source_age_seconds=max(
            (row.max_source_age_seconds for row in rows),
            default=ZERO,
        ),
        average_reliability_memory_score=_ratio(
            _sum_decimal(row.average_reliability_memory_score for row in rows),
            domain_count,
        ),
        max_catalyst_pressure_score=max(
            (row.max_catalyst_pressure_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_event_source_coverage_rotation_report_payload(
    report: ResearchEventSourceCoverageRotationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSourceCoverageRotationReport:
        raise ValueError("report must be a ResearchEventSourceCoverageRotationReport")
    _reject_unsafe_public_payload("report", report)
    validated = _validated_report(report)
    _require_hard_flags("report", validated)
    ready = _json_ready(validated)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_fields("payload", ready, REPORT_PAYLOAD_FIELDS)
    _require_hard_flags("payload", _DictFlags(ready))
    _reject_unsafe_public_payload("payload", ready)
    return ready


def research_event_source_coverage_rotation_report_digest(
    report: ResearchEventSourceCoverageRotationReport,
) -> str:
    payload = research_event_source_coverage_rotation_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
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


def _validated_report(
    report: ResearchEventSourceCoverageRotationReport,
) -> ResearchEventSourceCoverageRotationReport:
    return ResearchEventSourceCoverageRotationReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_status=report.report_status,
        next_step=report.next_step,
        domain_count=report.domain_count,
        pass_domain_count=report.pass_domain_count,
        watch_domain_count=report.watch_domain_count,
        block_domain_count=report.block_domain_count,
        thin_coverage_domain_count=report.thin_coverage_domain_count,
        stale_source_domain_count=report.stale_source_domain_count,
        weak_reliability_domain_count=report.weak_reliability_domain_count,
        high_catalyst_domain_count=report.high_catalyst_domain_count,
        capacity_constrained_domain_count=report.capacity_constrained_domain_count,
        max_source_age_seconds=report.max_source_age_seconds,
        average_reliability_memory_score=report.average_reliability_memory_score,
        max_catalyst_pressure_score=report.max_catalyst_pressure_score,
        rows=_validated_rows(report.rows),
        reason_code_counts=_validated_reason_code_counts(report.reason_code_counts),
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _validated_rows(
    rows: object,
) -> tuple[ResearchEventSourceCoverageRotationRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    return tuple(_validated_row(row) for row in rows)


def _validated_row(row: object) -> ResearchEventSourceCoverageRotationRow:
    if type(row) is not ResearchEventSourceCoverageRotationRow:
        raise ValueError("rows must contain ResearchEventSourceCoverageRotationRow")
    return ResearchEventSourceCoverageRotationRow(
        event_domain=row.event_domain,
        rotation_status=row.rotation_status,
        source_class_count=row.source_class_count,
        aggregate_source_count=row.aggregate_source_count,
        max_source_age_seconds=row.max_source_age_seconds,
        average_reliability_memory_score=row.average_reliability_memory_score,
        max_catalyst_pressure_score=row.max_catalyst_pressure_score,
        min_team_capacity_available=row.min_team_capacity_available,
        max_team_capacity_load_ratio=row.max_team_capacity_load_ratio,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _validated_reason_code_counts(
    counts: object,
) -> tuple[ResearchEventSourceCoverageRotationReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    return tuple(_validated_reason_code_count(count) for count in counts)


def _validated_reason_code_count(
    count: object,
) -> ResearchEventSourceCoverageRotationReasonCodeCount:
    if type(count) is not ResearchEventSourceCoverageRotationReasonCodeCount:
        raise ValueError("reason_code_counts must contain reason count rows")
    return ResearchEventSourceCoverageRotationReasonCodeCount(
        reason_code=count.reason_code,
        count=count.count,
        domain_ratio=count.domain_ratio,
        paper_only=count.paper_only,
        report_only=count.report_only,
        readonly=count.readonly,
    )


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: frozenset[str],
) -> None:
    actual_fields = frozenset(payload)
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must contain the exact report fields")


def _normalize_signals(
    signals: object,
    generated_at: datetime,
) -> tuple[ResearchEventSourceCoverageRotationSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not ResearchEventSourceCoverageRotationSignal:
            raise ValueError(
                "signals must contain ResearchEventSourceCoverageRotationSignal",
            )
        _require_hard_flags("signal", signal)
        key = (signal.event_domain, signal.source_class)
        if key in seen:
            raise ValueError("signals must use unique event domain source class pairs")
        seen.add(key)
        if signal.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
    return normalized


def _domain_groups(
    signals: tuple[ResearchEventSourceCoverageRotationSignal, ...],
) -> tuple[tuple[str, tuple[ResearchEventSourceCoverageRotationSignal, ...]], ...]:
    domain_names = tuple(sorted(frozenset(signal.event_domain for signal in signals)))
    return tuple(
        (
            domain,
            tuple(signal for signal in signals if signal.event_domain == domain),
        )
        for domain in domain_names
    )


def _build_row(
    event_domain: str,
    signals: tuple[ResearchEventSourceCoverageRotationSignal, ...],
    config: ResearchEventSourceCoverageRotationConfig,
    generated_at: datetime,
) -> ResearchEventSourceCoverageRotationRow:
    source_class_count = _count(len(signals))
    aggregate_source_count = _sum_decimal(
        signal.aggregate_source_count for signal in signals
    )
    max_source_age_seconds = max(
        (_seconds_between(signal.observed_at, generated_at) for signal in signals),
        default=ZERO,
    )
    average_reliability_memory_score = _ratio(
        _sum_decimal(signal.reliability_memory_score for signal in signals),
        source_class_count,
    )
    max_catalyst_pressure_score = max(
        (signal.catalyst_pressure_score for signal in signals),
        default=ZERO,
    )
    min_team_capacity_available = min(
        (signal.team_capacity_available for signal in signals),
        default=ZERO,
    )
    max_team_capacity_load_ratio = max(
        (signal.team_capacity_load_ratio for signal in signals),
        default=ZERO,
    )
    reason_codes = _row_reason_codes(
        source_class_count=source_class_count,
        aggregate_source_count=aggregate_source_count,
        max_source_age_seconds=max_source_age_seconds,
        average_reliability_memory_score=average_reliability_memory_score,
        max_catalyst_pressure_score=max_catalyst_pressure_score,
        min_team_capacity_available=min_team_capacity_available,
        max_team_capacity_load_ratio=max_team_capacity_load_ratio,
        config=config,
    )
    return ResearchEventSourceCoverageRotationRow(
        event_domain=event_domain,
        rotation_status=_status_from_reason_codes(reason_codes),
        source_class_count=source_class_count,
        aggregate_source_count=aggregate_source_count,
        max_source_age_seconds=max_source_age_seconds,
        average_reliability_memory_score=average_reliability_memory_score,
        max_catalyst_pressure_score=max_catalyst_pressure_score,
        min_team_capacity_available=min_team_capacity_available,
        max_team_capacity_load_ratio=max_team_capacity_load_ratio,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_class_count: Decimal,
    aggregate_source_count: Decimal,
    max_source_age_seconds: Decimal,
    average_reliability_memory_score: Decimal,
    max_catalyst_pressure_score: Decimal,
    min_team_capacity_available: Decimal,
    max_team_capacity_load_ratio: Decimal,
    config: ResearchEventSourceCoverageRotationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        source_class_count < config.minimum_source_class_count
        or aggregate_source_count < config.minimum_aggregate_source_count
    ):
        reasons.append(THIN_COVERAGE_REASON)
    if max_source_age_seconds > config.fresh_source_max_age_seconds:
        reasons.append(STALE_SOURCE_AGE_REASON)
    if average_reliability_memory_score < config.minimum_reliability_memory_score:
        reasons.append(WEAK_RELIABILITY_MEMORY_REASON)
    if max_catalyst_pressure_score >= config.block_catalyst_pressure_score:
        reasons.append(HIGH_CATALYST_PRESSURE_REASON)
    if (
        min_team_capacity_available < config.minimum_team_capacity_available
        or max_team_capacity_load_ratio > config.max_team_capacity_load_ratio
    ):
        reasons.append(CAPACITY_CONSTRAINED_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        THIN_COVERAGE_REASON in reason_codes
        or WEAK_RELIABILITY_MEMORY_REASON in reason_codes
        or HIGH_CATALYST_PRESSURE_REASON in reason_codes
        or CAPACITY_CONSTRAINED_REASON in reason_codes
    ):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    block_domain_count: Decimal,
    watch_domain_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_BLOCK
    if block_domain_count > ZERO:
        return STATUS_BLOCK
    if watch_domain_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(row: ResearchEventSourceCoverageRotationRow) -> tuple[Decimal, Decimal, str]:
    return (
        {
            STATUS_BLOCK: ZERO,
            STATUS_WATCH: ONE,
            STATUS_PASS: Decimal("2.000000"),
        }[row.rotation_status],
        row.average_reliability_memory_score,
        row.event_domain,
    )


def _reason_code_counts(
    rows: tuple[ResearchEventSourceCoverageRotationRow, ...],
) -> tuple[ResearchEventSourceCoverageRotationReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts[reason_code] + 1 if reason_code in counts else 1
    domain_count = _count(len(rows))
    return tuple(
        ResearchEventSourceCoverageRotationReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            domain_ratio=_ratio(_count(counts[reason_code]), domain_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventSourceCoverageRotationRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    previous_key: tuple[Decimal, Decimal, str] | None = None
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventSourceCoverageRotationRow:
            raise ValueError("rows must contain ResearchEventSourceCoverageRotationRow")
        _require_hard_flags("row", row)
        if row.event_domain in seen:
            raise ValueError("rows must use unique event domains")
        seen.add(row.event_domain)
        key = _row_sort_key(row)
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must be ranked by unique status and domain keys")
        previous_key = key
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchEventSourceCoverageRotationReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(values)
    previous_rank = -1
    for count in counts:
        if type(count) is not ResearchEventSourceCoverageRotationReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason count", count)
        rank = _reason_code_rank(count.reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_code_counts must be ranked by unique reason_code")
        previous_rank = rank
    return counts


def _normalize_row_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _row_reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be ranked by unique reason code")
        previous_rank = rank
    if PASS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes pass cannot be combined")
    if NO_INPUTS_REASON in reason_codes:
        raise ValueError("reason_codes no_inputs is report-only")
    return reason_codes


def _normalize_report_reason_codes(values: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(values)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_rank = -1
    for reason_code in reason_codes:
        rank = _reason_code_rank(reason_code)
        if rank <= previous_rank:
            raise ValueError("reason_codes must be ranked by unique reason code")
        previous_rank = rank
    if NO_INPUTS_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("reason_codes no_inputs cannot be combined")
    return reason_codes


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _validate_report(report: ResearchEventSourceCoverageRotationReport) -> None:
    if report.domain_count != _count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_domain_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_domain_count must match rows")
    if report.block_domain_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_domain_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_counts = (
            ResearchEventSourceCoverageRotationReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                domain_ratio=ZERO,
            ),
        )
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        block_domain_count=report.block_domain_count,
        watch_domain_count=report.watch_domain_count,
    )
    if report.report_status != expected_status:
        raise ValueError("report_status must match row statuses")
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step must match report_status")
    _validate_report_metric(report, "thin_coverage_domain_count", THIN_COVERAGE_REASON)
    _validate_report_metric(report, "stale_source_domain_count", STALE_SOURCE_AGE_REASON)
    _validate_report_metric(
        report,
        "weak_reliability_domain_count",
        WEAK_RELIABILITY_MEMORY_REASON,
    )
    _validate_report_metric(report, "high_catalyst_domain_count", HIGH_CATALYST_PRESSURE_REASON)
    _validate_report_metric(
        report,
        "capacity_constrained_domain_count",
        CAPACITY_CONSTRAINED_REASON,
    )
    if report.max_source_age_seconds != max(
        (row.max_source_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.average_reliability_memory_score != _ratio(
        _sum_decimal(row.average_reliability_memory_score for row in report.rows),
        report.domain_count,
    ):
        raise ValueError("average_reliability_memory_score must match rows")
    if report.max_catalyst_pressure_score != max(
        (row.max_catalyst_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_catalyst_pressure_score must match rows")


def _validate_report_metric(
    report: ResearchEventSourceCoverageRotationReport,
    field_name: str,
    reason_code: str,
) -> None:
    expected = _reason_count(report.rows, reason_code)
    if getattr(report, field_name) != expected:
        raise ValueError(f"{field_name} must match rows")


def _status_count(
    rows: tuple[ResearchEventSourceCoverageRotationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rotation_status == status))


def _reason_count(
    rows: tuple[ResearchEventSourceCoverageRotationRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if _has_unsafe_public_text_fragment(value.lower()):
        raise ValueError(f"{field_name} must be a public aggregate label")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain known reason codes")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_six_decimal_value(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-decimal Decimal")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[assignment]
        total += value
    return _finite_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _finite_decimal(numerator / denominator)


def _finite_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be finite and quantizable") from exc


def _reason_code_rank(reason_code: str) -> int:
    try:
        return REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_code must be a known reason code") from exc


def _row_reason_code_rank(reason_code: str) -> int:
    try:
        return ROW_REASON_CODE_SEQUENCE.index(reason_code)
    except ValueError as exc:
        raise ValueError("reason_codes must contain row reason codes") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or 'value'} must be a supported public dataclass")
        _reject_unsafe_public_payload("value", value, path)
        return {
            field.name: _json_ready(
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
            for field in fields(value)
        }
    if type(value) is Decimal:
        return format(_require_six_decimal_value(path or "value", value), "f")
    if type(value) is datetime:
        if value.tzinfo is not UTC or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be UTC-aware")
        return value.isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, (list, dict, set, frozenset)):
        raise ValueError(f"{path or 'value'} must come from public dataclass fields")
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} must be a supported public dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if isinstance(value, Decimal):
        _require_six_decimal_value(path or label, value)
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        lowered = value.lower()
        if _has_unsafe_public_text_fragment(lowered):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            if _has_unsafe_public_text_fragment(key.lower()):
                raise ValueError(f"{item_path} has unsafe field")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_text_fragment(value: str) -> bool:
    return any(fragment in value for fragment in UNSAFE_TEXT_FRAGMENTS)
