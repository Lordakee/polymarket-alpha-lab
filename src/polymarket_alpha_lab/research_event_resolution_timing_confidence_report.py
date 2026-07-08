"""Report-only resolution timing confidence scorer."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIG_VERSION = "research_event_resolution_timing_confidence_v1"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))

REASON_EVENT_WINDOW_UNCLEAR = "event_window_unclear"
REASON_MISSING_LATEST_SIGNAL = "missing_latest_signal"
REASON_STALE_VERIFIED_SIGNAL = "stale_verified_signal"
REASON_WEAK_SOURCE_AUTHORITY = "weak_source_authority"
REASON_CONTRADICTION_PRESSURE = "contradiction_pressure"
REASON_INCOMPLETE_DEPENDENCIES = "incomplete_dependencies"
REASON_AMBIGUOUS_RESOLUTION = "ambiguous_resolution"
REASON_DEADLINE_PRESSURE = "deadline_pressure"
REASON_LOW_CONFIDENCE = "low_timing_confidence"

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "http",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ),
)


@dataclass(frozen=True)
class ResearchEventResolutionTimingConfidenceConfig:
    config_version: str = CONFIG_VERSION
    event_window_clarity_weight: Decimal = Decimal("0.2000")
    latest_verified_signal_recency_weight: Decimal = Decimal("0.1500")
    source_authority_weight: Decimal = Decimal("0.1500")
    contradiction_pressure_weight: Decimal = Decimal("0.1500")
    dependency_completeness_weight: Decimal = Decimal("0.1500")
    ambiguity_risk_weight: Decimal = Decimal("0.1000")
    deadline_proximity_weight: Decimal = Decimal("0.1000")
    pass_confidence_threshold: Decimal = Decimal("0.8500")
    watch_confidence_threshold: Decimal = Decimal("0.5000")
    min_event_window_clarity_score: Decimal = Decimal("0.4000")
    min_source_authority_score: Decimal = Decimal("0.6000")
    pass_source_authority_floor: Decimal = Decimal("0.7000")
    max_contradiction_pressure_score: Decimal = Decimal("0.7000")
    min_dependency_completeness_score: Decimal = Decimal("0.5000")
    max_ambiguity_risk_score: Decimal = Decimal("0.8000")
    min_deadline_proximity_score: Decimal = Decimal("0.2000")
    max_latest_verified_signal_age_hours: Decimal = Decimal("48")
    min_deadline_buffer_hours: Decimal = Decimal("12")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionTimingConfidenceConfig:
            raise TypeError(
                "ResearchEventResolutionTimingConfidenceConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingConfidenceConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionTimingConfidenceConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_window_clarity_weight",
            "latest_verified_signal_recency_weight",
            "source_authority_weight",
            "contradiction_pressure_weight",
            "dependency_completeness_weight",
            "ambiguity_risk_weight",
            "deadline_proximity_weight",
            "pass_confidence_threshold",
            "watch_confidence_threshold",
            "min_event_window_clarity_score",
            "min_source_authority_score",
            "pass_source_authority_floor",
            "max_contradiction_pressure_score",
            "min_dependency_completeness_score",
            "max_ambiguity_risk_score",
            "min_deadline_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_latest_verified_signal_age_hours",
            "min_deadline_buffer_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_weight_total(self)
        if self.pass_confidence_threshold < self.watch_confidence_threshold:
            raise ValueError("pass_confidence_threshold must be at least watch_confidence_threshold")
        if self.pass_source_authority_floor < self.min_source_authority_score:
            raise ValueError("pass_source_authority_floor must be at least min_source_authority_score")
        require_paper_only_flags("resolution timing confidence config", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimingConfidenceInput:
    event_reference: str
    observed_at: datetime
    event_window_started_at: datetime | None
    event_window_ended_at: datetime | None
    latest_verified_signal_at: datetime | None
    deadline_at: datetime | None
    event_window_clarity_score: Decimal
    source_authority_score: Decimal
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    required_dependency_count: Decimal
    verified_dependency_count: Decimal
    ambiguity_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionTimingConfidenceInput:
            raise TypeError(
                "ResearchEventResolutionTimingConfidenceInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingConfidenceInput:
            raise ValueError("input must be exactly ResearchEventResolutionTimingConfidenceInput")
        _require_canonical_string("event_reference", self.event_reference)
        observed_at = _as_utc("observed_at", self.observed_at)
        object.__setattr__(self, "observed_at", observed_at)
        for field_name in (
            "event_window_started_at",
            "event_window_ended_at",
            "latest_verified_signal_at",
            "deadline_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        if self.event_window_started_at is not None and self.event_window_ended_at is not None:
            if self.event_window_ended_at <= self.event_window_started_at:
                raise ValueError("event_window_ended_at must be after event_window_started_at")
        if self.latest_verified_signal_at is not None and self.latest_verified_signal_at > observed_at:
            raise ValueError("latest_verified_signal_at must not be after observed_at")
        if self.deadline_at is not None and self.deadline_at < observed_at:
            raise ValueError("deadline_at must not be before observed_at")
        for field_name in (
            "event_window_clarity_score",
            "source_authority_score",
            "highest_contradiction_severity",
            "ambiguity_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_count_decimal("contradiction_count", self.contradiction_count),
        )
        for field_name in ("required_dependency_count", "verified_dependency_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.verified_dependency_count > self.required_dependency_count:
            raise ValueError("verified_dependency_count must not exceed required_dependency_count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("resolution timing confidence input", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimingConfidenceRow:
    event_digest: str
    observed_at: datetime
    event_window_started_at: datetime | None
    event_window_ended_at: datetime | None
    latest_verified_signal_at: datetime | None
    deadline_at: datetime | None
    event_window_hours: Decimal | None
    latest_verified_signal_age_hours: Decimal | None
    hours_until_deadline: Decimal | None
    event_window_clarity_score: Decimal
    latest_verified_signal_recency_score: Decimal
    source_authority_score: Decimal
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    contradiction_pressure_score: Decimal
    required_dependency_count: Decimal
    verified_dependency_count: Decimal
    dependency_completeness_score: Decimal
    ambiguity_risk_score: Decimal
    deadline_proximity_score: Decimal
    confidence_score: Decimal
    timing_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionTimingConfidenceRow:
            raise TypeError(
                "ResearchEventResolutionTimingConfidenceRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingConfidenceRow:
            raise ValueError("row must be exactly ResearchEventResolutionTimingConfidenceRow")
        _require_sha256_digest("event_digest", self.event_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "event_window_started_at",
            "event_window_ended_at",
            "latest_verified_signal_at",
            "deadline_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        for field_name in (
            "event_window_hours",
            "latest_verified_signal_age_hours",
            "hours_until_deadline",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_nonnegative_decimal(field_name, value),
                )
        for field_name in (
            "event_window_clarity_score",
            "latest_verified_signal_recency_score",
            "source_authority_score",
            "highest_contradiction_severity",
            "contradiction_pressure_score",
            "dependency_completeness_score",
            "ambiguity_risk_score",
            "deadline_proximity_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_count",
            "required_dependency_count",
            "verified_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status(self.timing_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        require_paper_only_flags("resolution timing confidence row", self)


@dataclass(frozen=True)
class ResearchEventResolutionTimingConfidenceReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_score: Decimal
    weakest_confidence_score: Decimal
    rows: tuple[ResearchEventResolutionTimingConfidenceRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionTimingConfidenceReport:
            raise TypeError(
                "ResearchEventResolutionTimingConfidenceReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionTimingConfidenceReport:
            raise ValueError("report must be exactly ResearchEventResolutionTimingConfidenceReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_confidence_score", "weakest_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        require_paper_only_flags("resolution timing confidence report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "resolution timing confidence report",
            _payload_value(asdict(self)),
        )


def build_research_event_resolution_timing_confidence_report(
    events: tuple[ResearchEventResolutionTimingConfidenceInput, ...],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> ResearchEventResolutionTimingConfidenceReport:
    if type(events) is not tuple:
        raise ValueError("events must be a tuple")
    if type(config) is not ResearchEventResolutionTimingConfidenceConfig:
        raise ValueError("config must be a ResearchEventResolutionTimingConfidenceConfig")
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_build_row(event=event, config=config) for event in events),
            key=lambda row: row.event_digest,
        ),
    )
    return ResearchEventResolutionTimingConfidenceReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        average_confidence_score=_average(row.confidence_score for row in rows),
        weakest_confidence_score=_minimum(row.confidence_score for row in rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_resolution_timing_confidence_payload(
    report: ResearchEventResolutionTimingConfidenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionTimingConfidenceReport:
        require_paper_only_flags("resolution timing confidence report", report)
        _validate_report_consistency(report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchEventResolutionTimingConfidenceReport or object")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _build_row(
    *,
    event: ResearchEventResolutionTimingConfidenceInput,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> ResearchEventResolutionTimingConfidenceRow:
    if type(event) is not ResearchEventResolutionTimingConfidenceInput:
        raise ValueError("events must contain ResearchEventResolutionTimingConfidenceInput values")
    event_window_hours = _duration_hours(event.event_window_started_at, event.event_window_ended_at)
    latest_verified_signal_age_hours = _duration_hours(event.latest_verified_signal_at, event.observed_at)
    hours_until_deadline = _duration_hours(event.observed_at, event.deadline_at)
    latest_verified_signal_recency_score = _latest_verified_signal_recency_score(
        latest_verified_signal_age_hours,
        config,
    )
    contradiction_pressure_score = _contradiction_pressure_score(
        contradiction_count=event.contradiction_count,
        highest_contradiction_severity=event.highest_contradiction_severity,
        required_dependency_count=event.required_dependency_count,
    )
    dependency_completeness_score = _dependency_completeness_score(
        required_dependency_count=event.required_dependency_count,
        verified_dependency_count=event.verified_dependency_count,
    )
    deadline_proximity_score = _deadline_proximity_score(hours_until_deadline, config)
    confidence_score = _confidence_score(
        event_window_clarity_score=event.event_window_clarity_score,
        latest_verified_signal_recency_score=latest_verified_signal_recency_score,
        source_authority_score=event.source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        dependency_completeness_score=dependency_completeness_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        deadline_proximity_score=deadline_proximity_score,
        config=config,
    )
    timing_status = _timing_status(
        event_window_clarity_score=event.event_window_clarity_score,
        latest_verified_signal_recency_score=latest_verified_signal_recency_score,
        source_authority_score=event.source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        dependency_completeness_score=dependency_completeness_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        deadline_proximity_score=deadline_proximity_score,
        confidence_score=confidence_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        event.reason_codes,
        timing_status=timing_status,
        event_window_clarity_score=event.event_window_clarity_score,
        latest_verified_signal_at=event.latest_verified_signal_at,
        latest_verified_signal_recency_score=latest_verified_signal_recency_score,
        source_authority_score=event.source_authority_score,
        contradiction_pressure_score=contradiction_pressure_score,
        dependency_completeness_score=dependency_completeness_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        deadline_proximity_score=deadline_proximity_score,
        confidence_score=confidence_score,
        config=config,
    )
    return ResearchEventResolutionTimingConfidenceRow(
        event_digest=_event_digest(event.event_reference),
        observed_at=event.observed_at,
        event_window_started_at=event.event_window_started_at,
        event_window_ended_at=event.event_window_ended_at,
        latest_verified_signal_at=event.latest_verified_signal_at,
        deadline_at=event.deadline_at,
        event_window_hours=event_window_hours,
        latest_verified_signal_age_hours=latest_verified_signal_age_hours,
        hours_until_deadline=hours_until_deadline,
        event_window_clarity_score=event.event_window_clarity_score,
        latest_verified_signal_recency_score=latest_verified_signal_recency_score,
        source_authority_score=event.source_authority_score,
        contradiction_count=event.contradiction_count,
        highest_contradiction_severity=event.highest_contradiction_severity,
        contradiction_pressure_score=contradiction_pressure_score,
        required_dependency_count=event.required_dependency_count,
        verified_dependency_count=event.verified_dependency_count,
        dependency_completeness_score=dependency_completeness_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        deadline_proximity_score=deadline_proximity_score,
        confidence_score=confidence_score,
        timing_status=timing_status,
        reason_codes=reason_codes,
    )


def _latest_verified_signal_recency_score(
    latest_verified_signal_age_hours: Decimal | None,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> Decimal:
    if latest_verified_signal_age_hours is None:
        return ZERO
    if latest_verified_signal_age_hours >= config.max_latest_verified_signal_age_hours:
        return ZERO
    return _quantize(ONE - (latest_verified_signal_age_hours / config.max_latest_verified_signal_age_hours))


def _contradiction_pressure_score(
    *,
    contradiction_count: Decimal,
    highest_contradiction_severity: Decimal,
    required_dependency_count: Decimal,
) -> Decimal:
    dependency_floor = _maximum(ONE, required_dependency_count)
    count_pressure = _capped_ratio(contradiction_count, dependency_floor)
    return _quantize((count_pressure + highest_contradiction_severity) / Decimal("2"))


def _dependency_completeness_score(
    *,
    required_dependency_count: Decimal,
    verified_dependency_count: Decimal,
) -> Decimal:
    if required_dependency_count == ZERO:
        return ONE
    return _capped_ratio(verified_dependency_count, required_dependency_count)


def _deadline_proximity_score(
    hours_until_deadline: Decimal | None,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> Decimal:
    if hours_until_deadline is None:
        return ZERO
    return _capped_ratio(hours_until_deadline, config.min_deadline_buffer_hours)


def _confidence_score(
    *,
    event_window_clarity_score: Decimal,
    latest_verified_signal_recency_score: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure_score: Decimal,
    dependency_completeness_score: Decimal,
    ambiguity_risk_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> Decimal:
    return _quantize(
        event_window_clarity_score * config.event_window_clarity_weight
        + latest_verified_signal_recency_score * config.latest_verified_signal_recency_weight
        + source_authority_score * config.source_authority_weight
        + (ONE - contradiction_pressure_score) * config.contradiction_pressure_weight
        + dependency_completeness_score * config.dependency_completeness_weight
        + (ONE - ambiguity_risk_score) * config.ambiguity_risk_weight
        + deadline_proximity_score * config.deadline_proximity_weight,
    )


def _timing_status(
    *,
    event_window_clarity_score: Decimal,
    latest_verified_signal_recency_score: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure_score: Decimal,
    dependency_completeness_score: Decimal,
    ambiguity_risk_score: Decimal,
    deadline_proximity_score: Decimal,
    confidence_score: Decimal,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> str:
    if (
        confidence_score < config.watch_confidence_threshold
        or event_window_clarity_score < config.min_event_window_clarity_score
        or source_authority_score < config.min_source_authority_score
        or contradiction_pressure_score >= config.max_contradiction_pressure_score
        or dependency_completeness_score < config.min_dependency_completeness_score
        or ambiguity_risk_score >= config.max_ambiguity_risk_score
        or deadline_proximity_score < config.min_deadline_proximity_score
    ):
        return STATUS_BLOCK
    if (
        confidence_score >= config.pass_confidence_threshold
        and latest_verified_signal_recency_score > ZERO
        and source_authority_score >= config.pass_source_authority_floor
    ):
        return STATUS_PASS
    return STATUS_WATCH


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    timing_status: str,
    event_window_clarity_score: Decimal,
    latest_verified_signal_at: datetime | None,
    latest_verified_signal_recency_score: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure_score: Decimal,
    dependency_completeness_score: Decimal,
    ambiguity_risk_score: Decimal,
    deadline_proximity_score: Decimal,
    confidence_score: Decimal,
    config: ResearchEventResolutionTimingConfidenceConfig,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(timing_status)
    if event_window_clarity_score < config.min_event_window_clarity_score:
        codes.add(REASON_EVENT_WINDOW_UNCLEAR)
    if latest_verified_signal_at is None:
        codes.add(REASON_MISSING_LATEST_SIGNAL)
    elif latest_verified_signal_recency_score == ZERO:
        codes.add(REASON_STALE_VERIFIED_SIGNAL)
    if source_authority_score < config.min_source_authority_score:
        codes.add(REASON_WEAK_SOURCE_AUTHORITY)
    if contradiction_pressure_score >= config.max_contradiction_pressure_score:
        codes.add(REASON_CONTRADICTION_PRESSURE)
    if dependency_completeness_score < config.min_dependency_completeness_score:
        codes.add(REASON_INCOMPLETE_DEPENDENCIES)
    if ambiguity_risk_score >= config.max_ambiguity_risk_score:
        codes.add(REASON_AMBIGUOUS_RESOLUTION)
    if deadline_proximity_score < config.min_deadline_proximity_score:
        codes.add(REASON_DEADLINE_PRESSURE)
    if confidence_score < config.watch_confidence_threshold:
        codes.add(REASON_LOW_CONFIDENCE)
    return tuple(sorted(codes))


def _duration_hours(started_at: datetime | None, finished_at: datetime | None) -> Decimal | None:
    if started_at is None or finished_at is None:
        return None
    seconds = _duration_seconds(started_at, finished_at)
    if seconds <= ZERO:
        return ZERO
    return _quantize(seconds / Decimal("3600"))


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    return (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _event_digest(event_reference: str) -> str:
    return hashlib.sha256(event_reference.encode("utf-8")).hexdigest()


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionTimingConfidenceRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple((code, Decimal(counter[code])) for code in sorted(counter))


def _count_status(rows: tuple[ResearchEventResolutionTimingConfidenceRow, ...], status: str) -> Decimal:
    _require_status(status)
    return Decimal(sum(1 for row in rows if row.timing_status == status))


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


def _maximum(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    if numerator >= denominator:
        return ONE
    return _quantize(numerator / denominator)


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionTimingConfidenceRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    if not all(type(row) is ResearchEventResolutionTimingConfidenceRow for row in rows):
        raise ValueError("rows must contain ResearchEventResolutionTimingConfidenceRow values")
    if rows != tuple(sorted(rows, key=lambda row: row.event_digest)):
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


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("timing_status must be pass, watch, or block")


def _require_weight_total(config: ResearchEventResolutionTimingConfidenceConfig) -> None:
    total = _quantize(
        config.event_window_clarity_weight
        + config.latest_verified_signal_recency_weight
        + config.source_authority_weight
        + config.contradiction_pressure_weight
        + config.dependency_completeness_weight
        + config.ambiguity_risk_weight
        + config.deadline_proximity_weight,
    )
    if total != ONE:
        raise ValueError("confidence weights must sum to 1")


def _validate_row_consistency(row: ResearchEventResolutionTimingConfidenceRow) -> None:
    if row.verified_dependency_count > row.required_dependency_count:
        raise ValueError("verified_dependency_count must not exceed required_dependency_count")
    expected_dependency_score = _dependency_completeness_score(
        required_dependency_count=row.required_dependency_count,
        verified_dependency_count=row.verified_dependency_count,
    )
    if row.dependency_completeness_score != expected_dependency_score:
        raise ValueError("dependency_completeness_score must match dependency counts")


def _validate_report_consistency(report: ResearchEventResolutionTimingConfidenceReport) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _count_status(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_confidence_score != _average(row.confidence_score for row in report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.weakest_confidence_score != _minimum(row.confidence_score for row in report.rows):
        raise ValueError("weakest_confidence_score must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_validation_digest(report: ResearchEventResolutionTimingConfidenceReport) -> str:
    return _derived_validation_digest(asdict(report))


def _require_report_validation_digest(report: ResearchEventResolutionTimingConfidenceReport) -> None:
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


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("resolution timing confidence payload", payload)
    _require_public_payload_flags("resolution timing confidence payload", payload)
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
            _reject_unsafe_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_string(label, value)


def _reject_unsafe_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public field in {label}")


__all__ = (
    "ResearchEventResolutionTimingConfidenceConfig",
    "ResearchEventResolutionTimingConfidenceInput",
    "ResearchEventResolutionTimingConfidenceReport",
    "ResearchEventResolutionTimingConfidenceRow",
    "build_research_event_resolution_timing_confidence_report",
    "research_event_resolution_timing_confidence_payload",
)
