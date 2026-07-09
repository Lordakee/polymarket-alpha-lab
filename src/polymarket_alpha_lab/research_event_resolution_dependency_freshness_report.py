"""Report-only event resolution dependency freshness scorer."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any


CONFIG_VERSION = "research_event_resolution_dependency_freshness_report_v0"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_WEIGHT = {
    STATUS_BLOCK: Decimal("2"),
    STATUS_WATCH: Decimal("1"),
    STATUS_PASS: Decimal("0"),
}

REASON_PASS = "dependency_freshness_pass"
REASON_WATCH = "dependency_freshness_watch"
REASON_BLOCK = "dependency_freshness_block"
REASON_EMPTY = "dependency_freshness_report_empty"
REASON_INCOMPLETE_DEPENDENCY_SET = "incomplete_dependency_set"
REASON_STALE_VERIFIED_AGE = "stale_verified_dependency_age"
REASON_MISSING_VERIFIED_TIMESTAMP = "missing_verified_dependency_timestamp"
REASON_WEAK_SOURCE_AUTHORITY = "weak_source_authority"
REASON_CONTRADICTION_PRESSURE = "contradiction_pressure_present"
REASON_UNCLEAR_RESOLUTION_TIMING = "unclear_resolution_timing"
REASON_AMBIGUITY_RISK = "ambiguity_risk_present"
REASON_THIN_VERIFICATION_COVERAGE = "thin_verification_coverage"

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "http://",
    "https://",
    "dsn",
    "postgresql://",
    "postgres://",
    "table",
    "token",
    "secret",
    "wallet",
    "order",
    "trade",
    "live",
)


@dataclass(frozen=True)
class ResearchEventResolutionDependencyFreshnessConfig:
    config_version: str = CONFIG_VERSION
    dependency_completeness_weight: Decimal = Decimal("0.2000")
    latest_verified_age_weight: Decimal = Decimal("0.2000")
    source_authority_weight: Decimal = Decimal("0.1500")
    contradiction_pressure_weight: Decimal = Decimal("0.1000")
    timing_clarity_weight: Decimal = Decimal("0.1000")
    ambiguity_risk_weight: Decimal = Decimal("0.1000")
    verification_coverage_weight: Decimal = Decimal("0.1500")
    pass_freshness_threshold: Decimal = Decimal("0.8000")
    watch_freshness_threshold: Decimal = Decimal("0.5000")
    fresh_verified_age_hours: Decimal = Decimal("24")
    stale_verified_age_hours: Decimal = Decimal("48")
    clear_timing_precision_hours: Decimal = Decimal("24")
    unclear_timing_precision_hours: Decimal = Decimal("144")
    ambiguity_issue_block_count: Decimal = Decimal("4")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDependencyFreshnessConfig:
            raise TypeError(
                "ResearchEventResolutionDependencyFreshnessConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDependencyFreshnessConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionDependencyFreshnessConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "dependency_completeness_weight",
            "latest_verified_age_weight",
            "source_authority_weight",
            "contradiction_pressure_weight",
            "timing_clarity_weight",
            "ambiguity_risk_weight",
            "verification_coverage_weight",
            "pass_freshness_threshold",
            "watch_freshness_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_verified_age_hours",
            "stale_verified_age_hours",
            "clear_timing_precision_hours",
            "unclear_timing_precision_hours",
            "ambiguity_issue_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_freshness_threshold < self.watch_freshness_threshold:
            raise ValueError("pass_freshness_threshold must be at least watch_freshness_threshold")
        if self.stale_verified_age_hours < self.fresh_verified_age_hours:
            raise ValueError("stale_verified_age_hours must be at least fresh_verified_age_hours")
        if self.unclear_timing_precision_hours < self.clear_timing_precision_hours:
            raise ValueError(
                "unclear_timing_precision_hours must be at least clear_timing_precision_hours",
            )
        _require_weight_total(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionDependencyFreshnessInput:
    event_reference: str
    dependency_reference: str
    observed_at: datetime
    latest_verified_at: datetime | None
    dependency_required_count: Decimal
    dependency_verified_count: Decimal
    source_count: Decimal
    authoritative_source_count: Decimal
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    resolution_due_at: datetime | None
    timing_precision_hours: Decimal
    ambiguity_issue_count: Decimal
    verification_method_count: Decimal
    required_verification_method_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDependencyFreshnessInput:
            raise TypeError(
                "ResearchEventResolutionDependencyFreshnessInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDependencyFreshnessInput:
            raise ValueError("input must be exactly ResearchEventResolutionDependencyFreshnessInput")
        for field_name in ("event_reference", "dependency_reference"):
            _require_reference_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.latest_verified_at is not None:
            object.__setattr__(
                self,
                "latest_verified_at",
                _as_utc("latest_verified_at", self.latest_verified_at),
            )
        if self.resolution_due_at is not None:
            object.__setattr__(
                self,
                "resolution_due_at",
                _as_utc("resolution_due_at", self.resolution_due_at),
            )
        object.__setattr__(
            self,
            "dependency_required_count",
            _normalize_positive_count("dependency_required_count", self.dependency_required_count),
        )
        object.__setattr__(
            self,
            "dependency_verified_count",
            _normalize_count_decimal("dependency_verified_count", self.dependency_verified_count),
        )
        if self.dependency_verified_count > self.dependency_required_count:
            raise ValueError("dependency_verified_count must not exceed dependency_required_count")
        object.__setattr__(self, "source_count", _normalize_count_decimal("source_count", self.source_count))
        object.__setattr__(
            self,
            "authoritative_source_count",
            _normalize_count_decimal("authoritative_source_count", self.authoritative_source_count),
        )
        if self.authoritative_source_count > self.source_count:
            raise ValueError("authoritative_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_count_decimal("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "highest_contradiction_severity",
            _normalize_probability(
                "highest_contradiction_severity",
                self.highest_contradiction_severity,
            ),
        )
        for field_name in (
            "timing_precision_hours",
            "ambiguity_issue_count",
            "verification_method_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_verification_method_count",
            _normalize_positive_count(
                "required_verification_method_count",
                self.required_verification_method_count,
            ),
        )
        if self.verification_method_count > self.required_verification_method_count:
            raise ValueError(
                "verification_method_count must not exceed required_verification_method_count",
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes, allow_empty=True))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionDependencyFreshnessRow:
    event_reference_digest: str
    dependency_reference_digest: str
    observed_at: datetime
    latest_verified_at: datetime | None
    resolution_due_at: datetime | None
    latest_verified_age_hours: Decimal | None
    dependency_completeness_score: Decimal
    latest_verified_freshness_score: Decimal
    source_authority_score: Decimal
    contradiction_pressure_score: Decimal
    timing_clarity_score: Decimal
    ambiguity_risk_score: Decimal
    verification_coverage_score: Decimal
    freshness_score: Decimal
    dependency_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDependencyFreshnessRow:
            raise TypeError(
                "ResearchEventResolutionDependencyFreshnessRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDependencyFreshnessRow:
            raise ValueError("row must be exactly ResearchEventResolutionDependencyFreshnessRow")
        _require_sha256_digest("event_reference_digest", self.event_reference_digest)
        _require_sha256_digest("dependency_reference_digest", self.dependency_reference_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.latest_verified_at is not None:
            object.__setattr__(
                self,
                "latest_verified_at",
                _as_utc("latest_verified_at", self.latest_verified_at),
            )
        if self.resolution_due_at is not None:
            object.__setattr__(
                self,
                "resolution_due_at",
                _as_utc("resolution_due_at", self.resolution_due_at),
            )
        if self.latest_verified_age_hours is not None:
            object.__setattr__(
                self,
                "latest_verified_age_hours",
                _normalize_nonnegative_decimal(
                    "latest_verified_age_hours",
                    self.latest_verified_age_hours,
                ),
            )
        for field_name in (
            "dependency_completeness_score",
            "latest_verified_freshness_score",
            "source_authority_score",
            "contradiction_pressure_score",
            "timing_clarity_score",
            "ambiguity_risk_score",
            "verification_coverage_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("dependency_status", self.dependency_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEventResolutionDependencyFreshnessReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_freshness_score: Decimal
    weakest_freshness_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionDependencyFreshnessRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionDependencyFreshnessReport:
            raise TypeError(
                "ResearchEventResolutionDependencyFreshnessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionDependencyFreshnessReport:
            raise ValueError("report must be exactly ResearchEventResolutionDependencyFreshnessReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_freshness_score", "weakest_freshness_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", _report_validation_digest(self))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "research event resolution dependency freshness report",
            _payload_value(asdict(self)),
        )


def build_research_event_resolution_dependency_freshness_report(
    dependencies: tuple[ResearchEventResolutionDependencyFreshnessInput, ...],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> ResearchEventResolutionDependencyFreshnessReport:
    if type(dependencies) is not tuple:
        raise ValueError("dependencies must be a tuple")
    if type(config) is not ResearchEventResolutionDependencyFreshnessConfig:
        raise ValueError("config must be a ResearchEventResolutionDependencyFreshnessConfig")
    _require_hard_flags("config", config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_build_row(dependency, generated_at=normalized_generated_at, config=config) for dependency in dependencies),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchEventResolutionDependencyFreshnessReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        average_freshness_score=_average(row.freshness_score for row in rows),
        weakest_freshness_score=_minimum(row.freshness_score for row in rows),
        report_status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
    )


def research_event_resolution_dependency_freshness_payload(
    report: ResearchEventResolutionDependencyFreshnessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionDependencyFreshnessReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionDependencyFreshnessReport or object",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    dependency: ResearchEventResolutionDependencyFreshnessInput,
    *,
    generated_at: datetime,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> ResearchEventResolutionDependencyFreshnessRow:
    if type(dependency) is not ResearchEventResolutionDependencyFreshnessInput:
        raise ValueError(
            "dependencies must contain ResearchEventResolutionDependencyFreshnessInput values",
        )
    latest_verified_age_hours = _latest_verified_age_hours(
        generated_at=generated_at,
        latest_verified_at=dependency.latest_verified_at,
    )
    dependency_completeness_score = _capped_ratio(
        dependency.dependency_verified_count,
        dependency.dependency_required_count,
    )
    latest_verified_freshness_score = _latest_verified_freshness_score(
        latest_verified_age_hours,
        config,
    )
    source_authority_score = _source_authority_score(
        dependency.authoritative_source_count,
        dependency.source_count,
    )
    contradiction_pressure_score = _contradiction_pressure_score(
        contradiction_count=dependency.contradiction_count,
        highest_contradiction_severity=dependency.highest_contradiction_severity,
        source_count=dependency.source_count,
    )
    timing_clarity_score = _timing_clarity_score(dependency, config)
    ambiguity_risk_score = _ambiguity_risk_score(dependency.ambiguity_issue_count, config)
    verification_coverage_score = _capped_ratio(
        dependency.verification_method_count,
        dependency.required_verification_method_count,
    )
    freshness_score = _freshness_score(
        dependency_completeness_score=dependency_completeness_score,
        latest_verified_freshness_score=latest_verified_freshness_score,
        source_authority_score=source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        timing_clarity_score=timing_clarity_score,
        ambiguity_risk_score=ambiguity_risk_score,
        verification_coverage_score=verification_coverage_score,
        config=config,
    )
    dependency_status = _dependency_status(freshness_score, config)
    reason_codes = _row_reason_codes(
        dependency.reason_codes,
        latest_verified_at=dependency.latest_verified_at,
        dependency_completeness_score=dependency_completeness_score,
        latest_verified_freshness_score=latest_verified_freshness_score,
        source_authority_score=source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        timing_clarity_score=timing_clarity_score,
        ambiguity_risk_score=ambiguity_risk_score,
        verification_coverage_score=verification_coverage_score,
        dependency_status=dependency_status,
    )
    return ResearchEventResolutionDependencyFreshnessRow(
        event_reference_digest=_reference_digest(dependency.event_reference),
        dependency_reference_digest=_reference_digest(dependency.dependency_reference),
        observed_at=dependency.observed_at,
        latest_verified_at=dependency.latest_verified_at,
        resolution_due_at=dependency.resolution_due_at,
        latest_verified_age_hours=latest_verified_age_hours,
        dependency_completeness_score=dependency_completeness_score,
        latest_verified_freshness_score=latest_verified_freshness_score,
        source_authority_score=source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        timing_clarity_score=timing_clarity_score,
        ambiguity_risk_score=ambiguity_risk_score,
        verification_coverage_score=verification_coverage_score,
        freshness_score=freshness_score,
        dependency_status=dependency_status,
        reason_codes=reason_codes,
    )


def _latest_verified_age_hours(
    *,
    generated_at: datetime,
    latest_verified_at: datetime | None,
) -> Decimal | None:
    if latest_verified_at is None:
        return None
    delta = generated_at - latest_verified_at
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    if seconds <= ZERO:
        return ZERO
    return _quantize(seconds / Decimal("3600"))


def _latest_verified_freshness_score(
    latest_verified_age_hours: Decimal | None,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> Decimal:
    if latest_verified_age_hours is None:
        return ZERO
    if latest_verified_age_hours <= config.fresh_verified_age_hours:
        return ONE
    if latest_verified_age_hours >= config.stale_verified_age_hours:
        return ZERO
    stale_window = config.stale_verified_age_hours - config.fresh_verified_age_hours
    remaining = config.stale_verified_age_hours - latest_verified_age_hours
    return _capped_ratio(remaining, stale_window)


def _source_authority_score(authoritative_source_count: Decimal, source_count: Decimal) -> Decimal:
    if source_count == ZERO:
        return ZERO
    return _capped_ratio(authoritative_source_count, source_count)


def _contradiction_pressure_score(
    *,
    contradiction_count: Decimal,
    highest_contradiction_severity: Decimal,
    source_count: Decimal,
) -> Decimal:
    reference_floor = source_count if source_count >= ONE else ONE
    count_pressure = _capped_ratio(contradiction_count, reference_floor)
    return _quantize((count_pressure + highest_contradiction_severity) / Decimal("2"))


def _timing_clarity_score(
    dependency: ResearchEventResolutionDependencyFreshnessInput,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> Decimal:
    if dependency.resolution_due_at is None:
        return ZERO
    if dependency.timing_precision_hours <= config.clear_timing_precision_hours:
        return ONE
    if dependency.timing_precision_hours >= config.unclear_timing_precision_hours:
        return ZERO
    unclear_window = config.unclear_timing_precision_hours - config.clear_timing_precision_hours
    remaining = config.unclear_timing_precision_hours - dependency.timing_precision_hours
    return _capped_ratio(remaining, unclear_window)


def _ambiguity_risk_score(
    ambiguity_issue_count: Decimal,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> Decimal:
    return _capped_ratio(ambiguity_issue_count, config.ambiguity_issue_block_count)


def _freshness_score(
    *,
    dependency_completeness_score: Decimal,
    latest_verified_freshness_score: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure_score: Decimal,
    timing_clarity_score: Decimal,
    ambiguity_risk_score: Decimal,
    verification_coverage_score: Decimal,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> Decimal:
    return _quantize(
        dependency_completeness_score * config.dependency_completeness_weight
        + latest_verified_freshness_score * config.latest_verified_age_weight
        + source_authority_score * config.source_authority_weight
        + (ONE - contradiction_pressure_score) * config.contradiction_pressure_weight
        + timing_clarity_score * config.timing_clarity_weight
        + (ONE - ambiguity_risk_score) * config.ambiguity_risk_weight
        + verification_coverage_score * config.verification_coverage_weight,
    )


def _dependency_status(
    freshness_score: Decimal,
    config: ResearchEventResolutionDependencyFreshnessConfig,
) -> str:
    if freshness_score >= config.pass_freshness_threshold:
        return STATUS_PASS
    if freshness_score >= config.watch_freshness_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    latest_verified_at: datetime | None,
    dependency_completeness_score: Decimal,
    latest_verified_freshness_score: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure_score: Decimal,
    timing_clarity_score: Decimal,
    ambiguity_risk_score: Decimal,
    verification_coverage_score: Decimal,
    dependency_status: str,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(
        {
            STATUS_PASS: REASON_PASS,
            STATUS_WATCH: REASON_WATCH,
            STATUS_BLOCK: REASON_BLOCK,
        }[dependency_status],
    )
    if dependency_completeness_score < ONE:
        codes.add(REASON_INCOMPLETE_DEPENDENCY_SET)
    if latest_verified_freshness_score < ONE:
        codes.add(REASON_STALE_VERIFIED_AGE)
    if latest_verified_at is None:
        codes.add(REASON_MISSING_VERIFIED_TIMESTAMP)
    if source_authority_score < ONE:
        codes.add(REASON_WEAK_SOURCE_AUTHORITY)
    if contradiction_pressure_score > ZERO:
        codes.add(REASON_CONTRADICTION_PRESSURE)
    if timing_clarity_score < ONE:
        codes.add(REASON_UNCLEAR_RESOLUTION_TIMING)
    if ambiguity_risk_score > ZERO:
        codes.add(REASON_AMBIGUITY_RISK)
    if verification_coverage_score < ONE:
        codes.add(REASON_THIN_VERIFICATION_COVERAGE)
    return _normalize_reason_codes(tuple(sorted(codes)))


def _report_status(rows: tuple[ResearchEventResolutionDependencyFreshnessRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.dependency_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.dependency_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionDependencyFreshnessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY,)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionDependencyFreshnessRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return ((REASON_EMPTY, ONE),)
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, Decimal(counter[code])) for code in report_reason_codes)


def _row_sort_key(row: ResearchEventResolutionDependencyFreshnessRow) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.dependency_status],
        row.freshness_score,
        row.event_reference_digest,
        row.dependency_reference_digest,
    )


def _count_status(
    rows: tuple[ResearchEventResolutionDependencyFreshnessRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.dependency_status == status))


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _minimum(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(min(items))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    if numerator >= denominator:
        return ONE
    return _quantize(numerator / denominator)


def _reference_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_weight_total(config: ResearchEventResolutionDependencyFreshnessConfig) -> None:
    total = _quantize(
        config.dependency_completeness_weight
        + config.latest_verified_age_weight
        + config.source_authority_weight
        + config.contradiction_pressure_weight
        + config.timing_clarity_weight
        + config.ambiguity_risk_weight
        + config.verification_coverage_weight,
    )
    if total != ONE:
        raise ValueError("freshness weights must sum to 1")


def _validate_row_consistency(row: ResearchEventResolutionDependencyFreshnessRow) -> None:
    expected_status_reason = {
        STATUS_PASS: REASON_PASS,
        STATUS_WATCH: REASON_WATCH,
        STATUS_BLOCK: REASON_BLOCK,
    }[row.dependency_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include dependency_status reason")
    if row.latest_verified_at is None and row.latest_verified_age_hours is not None:
        raise ValueError("latest_verified_age_hours must be None when latest_verified_at is None")
    if row.latest_verified_at is not None and row.latest_verified_age_hours is None:
        raise ValueError("latest_verified_age_hours is required when latest_verified_at is present")


def _validate_report_consistency(report: ResearchEventResolutionDependencyFreshnessReport) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _count_status(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_freshness_score != _average(row.freshness_score for row in report.rows):
        raise ValueError("average_freshness_score must match rows")
    if report.weakest_freshness_score != _minimum(row.freshness_score for row in report.rows):
        raise ValueError("weakest_freshness_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionDependencyFreshnessRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchEventResolutionDependencyFreshnessRow for row in rows):
        raise ValueError("rows must contain ResearchEventResolutionDependencyFreshnessRow values")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts values must be pairs")
        code, count = item
        _require_canonical_string("reason_code_counts", code)
        if previous is not None and previous > code:
            raise ValueError("reason_code_counts must be sorted")
        normalized.append((code, _normalize_count_decimal("reason_code_counts", count)))
        previous = code
    return tuple(normalized)


def _normalize_reason_codes(value: object, *, allow_empty: bool = False) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("reason_codes is required")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    for code in codes:
        _require_canonical_string("reason_codes", code)
    return tuple(sorted(codes))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_finite_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")


def _require_reference_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            _require_canonical_string("payload key", key)
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type) and type(value).__module__ == __name__:
        return _payload_value(asdict(value))
    raise ValueError("public payload contains unsupported value")


def _report_validation_digest(report: ResearchEventResolutionDependencyFreshnessReport) -> str:
    return _derived_validation_digest(asdict(report))


def _require_report_validation_digest(report: ResearchEventResolutionDependencyFreshnessReport) -> None:
    if report.derived_validation_digest != _report_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = {
        key: _payload_value(value)
        for key, value in values.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(
        "research event resolution dependency freshness payload",
        payload,
    )
    _require_public_payload_flags(
        "research event resolution dependency freshness payload",
        payload,
    )
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _require_public_payload_flags(label: str, value: object) -> None:
    if type(value) is dict:
        for field_name in ("paper_only", "report_only", "readonly"):
            if value.get(field_name) is not True:
                raise ValueError(f"{label} {field_name} must be True")
        for child in value.values():
            _require_public_payload_flags(label, child)
        return
    if type(value) is list:
        for child in value:
            _require_public_payload_flags(label, child)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{label} must use safe serialized scalars")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload field in {label}")


__all__ = (
    "ResearchEventResolutionDependencyFreshnessConfig",
    "ResearchEventResolutionDependencyFreshnessInput",
    "ResearchEventResolutionDependencyFreshnessReport",
    "ResearchEventResolutionDependencyFreshnessRow",
    "build_research_event_resolution_dependency_freshness_report",
    "research_event_resolution_dependency_freshness_payload",
)
