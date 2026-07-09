"""Report-only resolution authority timing gap scorer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIG_VERSION = "research_event_resolution_authority_timing_gap_v1"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_EVENT_RESOLUTION_AUTHORITY_TIMING_GAP_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_AUTHORITY_UPDATE_MISSING = "authority_update_missing"
REASON_AUTHORITY_FRESHNESS_GAP = "authority_freshness_gap"
REASON_CADENCE_ADHERENCE_GAP = "cadence_adherence_gap"
REASON_LATEST_VERIFIED_MISSING = "latest_verified_missing"
REASON_LATEST_VERIFIED_STALE = "latest_verified_stale"
REASON_CONTRADICTION_PRESSURE = "contradiction_pressure"
REASON_AMBIGUITY_RISK = "ambiguity_risk"
REASON_VERIFICATION_COVERAGE_GAP = "verification_coverage_gap"
REASON_DEADLINE_MISSING = "deadline_missing"
REASON_DEADLINE_PRESSURE = "deadline_pressure"
REASON_TIMING_GAP_ELEVATED = "timing_gap_elevated"

ROW_REASON_ORDER = (
    STATUS_BLOCK,
    STATUS_PASS,
    STATUS_WATCH,
    REASON_AMBIGUITY_RISK,
    REASON_AUTHORITY_FRESHNESS_GAP,
    REASON_AUTHORITY_UPDATE_MISSING,
    REASON_CADENCE_ADHERENCE_GAP,
    REASON_CONTRADICTION_PRESSURE,
    REASON_DEADLINE_MISSING,
    REASON_DEADLINE_PRESSURE,
    REASON_LATEST_VERIFIED_MISSING,
    REASON_LATEST_VERIFIED_STALE,
    REASON_TIMING_GAP_ELEVATED,
    REASON_VERIFICATION_COVERAGE_GAP,
)

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "text",
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
class ResearchEventResolutionAuthorityTimingGapConfig:
    config_version: str = CONFIG_VERSION
    authority_freshness_weight: Decimal = Decimal("0.2000")
    cadence_adherence_weight: Decimal = Decimal("0.1500")
    latest_verified_age_weight: Decimal = Decimal("0.1500")
    contradiction_pressure_weight: Decimal = Decimal("0.1500")
    ambiguity_risk_weight: Decimal = Decimal("0.1000")
    verification_coverage_weight: Decimal = Decimal("0.1500")
    deadline_proximity_weight: Decimal = Decimal("0.1000")
    watch_gap_threshold: Decimal = Decimal("0.2500")
    block_gap_threshold: Decimal = Decimal("0.5000")
    max_authority_age_hours: Decimal = Decimal("72")
    max_latest_verified_age_hours: Decimal = Decimal("48")
    cadence_block_multiple: Decimal = Decimal("3")
    min_deadline_buffer_hours: Decimal = Decimal("12")
    watch_authority_freshness_score: Decimal = Decimal("0.6500")
    block_authority_freshness_score: Decimal = Decimal("0.1000")
    watch_cadence_adherence_score: Decimal = Decimal("0.7000")
    block_cadence_adherence_score: Decimal = Decimal("0.2500")
    watch_latest_verified_age_score: Decimal = Decimal("0.5000")
    block_latest_verified_age_score: Decimal = Decimal("0.1000")
    watch_contradiction_pressure_score: Decimal = Decimal("0.3500")
    block_contradiction_pressure_score: Decimal = Decimal("0.7000")
    watch_ambiguity_risk_score: Decimal = Decimal("0.5000")
    block_ambiguity_risk_score: Decimal = Decimal("0.8000")
    watch_verification_coverage_score: Decimal = Decimal("0.8000")
    block_verification_coverage_score: Decimal = Decimal("0.5000")
    watch_deadline_proximity_score: Decimal = Decimal("0.5000")
    block_deadline_proximity_score: Decimal = Decimal("0.2000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityTimingGapConfig:
            raise TypeError(
                "ResearchEventResolutionAuthorityTimingGapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventResolutionAuthorityTimingGapConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authority_freshness_weight",
            "cadence_adherence_weight",
            "latest_verified_age_weight",
            "contradiction_pressure_weight",
            "ambiguity_risk_weight",
            "verification_coverage_weight",
            "deadline_proximity_weight",
            "watch_gap_threshold",
            "block_gap_threshold",
            "watch_authority_freshness_score",
            "block_authority_freshness_score",
            "watch_cadence_adherence_score",
            "block_cadence_adherence_score",
            "watch_latest_verified_age_score",
            "block_latest_verified_age_score",
            "watch_contradiction_pressure_score",
            "block_contradiction_pressure_score",
            "watch_ambiguity_risk_score",
            "block_ambiguity_risk_score",
            "watch_verification_coverage_score",
            "block_verification_coverage_score",
            "watch_deadline_proximity_score",
            "block_deadline_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_authority_age_hours",
            "max_latest_verified_age_hours",
            "cadence_block_multiple",
            "min_deadline_buffer_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("authority timing gap config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityTimingGapInput:
    event_reference: str
    observed_at: datetime
    authority_last_updated_at: datetime | None
    expected_update_cadence_hours: Decimal
    latest_verified_at: datetime | None
    deadline_at: datetime | None
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    verification_required_count: Decimal
    verification_completed_count: Decimal
    ambiguity_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityTimingGapInput:
            raise TypeError(
                "ResearchEventResolutionAuthorityTimingGapInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchEventResolutionAuthorityTimingGapInput)
        _require_canonical_string("event_reference", self.event_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_last_updated_at",
            "latest_verified_at",
            "deadline_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        if (
            self.authority_last_updated_at is not None
            and self.authority_last_updated_at > self.observed_at
        ):
            raise ValueError("authority_last_updated_at must not be after observed_at")
        if self.latest_verified_at is not None and self.latest_verified_at > self.observed_at:
            raise ValueError("latest_verified_at must not be after observed_at")
        if self.deadline_at is not None and self.deadline_at < self.observed_at:
            raise ValueError("deadline_at must not be before observed_at")
        object.__setattr__(
            self,
            "expected_update_cadence_hours",
            _normalize_positive_decimal(
                "expected_update_cadence_hours",
                self.expected_update_cadence_hours,
            ),
        )
        object.__setattr__(
            self,
            "highest_contradiction_severity",
            _normalize_probability(
                "highest_contradiction_severity",
                self.highest_contradiction_severity,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_risk_score",
            _normalize_probability("ambiguity_risk_score", self.ambiguity_risk_score),
        )
        for field_name in (
            "contradiction_count",
            "verification_required_count",
            "verification_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.verification_completed_count > self.verification_required_count:
            raise ValueError(
                "verification_completed_count must not exceed verification_required_count",
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("authority timing gap input", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityTimingGapRow:
    event_digest: str
    observed_at: datetime
    authority_last_updated_at: datetime | None
    latest_verified_at: datetime | None
    deadline_at: datetime | None
    expected_update_cadence_hours: Decimal
    authority_age_hours: Decimal | None
    latest_verified_age_hours: Decimal | None
    hours_until_deadline: Decimal | None
    authority_freshness_score: Decimal
    cadence_adherence_score: Decimal
    latest_verified_age_score: Decimal
    contradiction_count: Decimal
    highest_contradiction_severity: Decimal
    contradiction_pressure_score: Decimal
    verification_required_count: Decimal
    verification_completed_count: Decimal
    verification_coverage_score: Decimal
    ambiguity_risk_score: Decimal
    deadline_proximity_score: Decimal
    gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityTimingGapRow:
            raise TypeError(
                "ResearchEventResolutionAuthorityTimingGapRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventResolutionAuthorityTimingGapRow)
        _require_sha256_digest("event_digest", self.event_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_last_updated_at",
            "latest_verified_at",
            "deadline_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        for field_name in (
            "expected_update_cadence_hours",
            "contradiction_count",
            "verification_required_count",
            "verification_completed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_or_measure_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_age_hours",
            "latest_verified_age_hours",
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
            "authority_freshness_score",
            "cadence_adherence_score",
            "latest_verified_age_score",
            "highest_contradiction_severity",
            "contradiction_pressure_score",
            "verification_coverage_score",
            "ambiguity_risk_score",
            "deadline_proximity_score",
            "gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("authority timing gap row", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityTimingGapReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_gap_score: Decimal
    highest_gap_score: Decimal
    weakest_authority_freshness_score: Decimal
    status: str
    rows: tuple[ResearchEventResolutionAuthorityTimingGapRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityTimingGapReport:
            raise TypeError(
                "ResearchEventResolutionAuthorityTimingGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventResolutionAuthorityTimingGapReport)
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
        for field_name in (
            "average_gap_score",
            "highest_gap_score",
            "weakest_authority_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
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
        _validate_report(self)
        require_paper_only_flags("authority timing gap report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "authority timing gap report",
            _payload_value(asdict(self)),
        )


def build_research_event_resolution_authority_timing_gap_report(
    events: tuple[ResearchEventResolutionAuthorityTimingGapInput, ...],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> ResearchEventResolutionAuthorityTimingGapReport:
    """Build a deterministic, report-only authority timing gap snapshot."""

    if type(events) is not tuple:
        raise ValueError("events must be a tuple")
    if type(config) is not ResearchEventResolutionAuthorityTimingGapConfig:
        raise ValueError("config must be a ResearchEventResolutionAuthorityTimingGapConfig")
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_build_row(event=event, config=config) for event in events),
            key=lambda row: row.event_digest,
        ),
    )
    return ResearchEventResolutionAuthorityTimingGapReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        average_gap_score=_average(row.gap_score for row in rows),
        highest_gap_score=_maximum_or_zero(row.gap_score for row in rows),
        weakest_authority_freshness_score=_minimum_or_zero(
            (row.authority_freshness_score for row in rows),
        ),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_resolution_authority_timing_gap_payload(
    report: ResearchEventResolutionAuthorityTimingGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionAuthorityTimingGapReport:
        require_paper_only_flags("authority timing gap report", report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityTimingGapReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def validate_research_event_resolution_authority_timing_gap_digest(
    report: ResearchEventResolutionAuthorityTimingGapReport,
) -> None:
    if type(report) is not ResearchEventResolutionAuthorityTimingGapReport:
        raise ValueError("report must be a ResearchEventResolutionAuthorityTimingGapReport")
    _require_report_validation_digest(report)


def research_event_resolution_authority_timing_gap_digest(
    report: ResearchEventResolutionAuthorityTimingGapReport,
) -> str:
    if type(report) is not ResearchEventResolutionAuthorityTimingGapReport:
        raise ValueError("report must be a ResearchEventResolutionAuthorityTimingGapReport")
    return _report_validation_digest(report)


def _build_row(
    *,
    event: ResearchEventResolutionAuthorityTimingGapInput,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> ResearchEventResolutionAuthorityTimingGapRow:
    if type(event) is not ResearchEventResolutionAuthorityTimingGapInput:
        raise ValueError(
            "events must contain ResearchEventResolutionAuthorityTimingGapInput values",
        )
    authority_age_hours = _duration_hours(event.authority_last_updated_at, event.observed_at)
    latest_verified_age_hours = _duration_hours(event.latest_verified_at, event.observed_at)
    hours_until_deadline = _duration_hours(event.observed_at, event.deadline_at)
    authority_freshness_score = _authority_freshness_score(authority_age_hours, config)
    cadence_adherence_score = _cadence_adherence_score(
        authority_age_hours=authority_age_hours,
        expected_update_cadence_hours=event.expected_update_cadence_hours,
        config=config,
    )
    latest_verified_age_score = _latest_verified_age_score(
        latest_verified_age_hours,
        config,
    )
    contradiction_pressure_score = _contradiction_pressure_score(
        contradiction_count=event.contradiction_count,
        highest_contradiction_severity=event.highest_contradiction_severity,
        verification_required_count=event.verification_required_count,
    )
    verification_coverage_score = _verification_coverage_score(
        required_count=event.verification_required_count,
        completed_count=event.verification_completed_count,
    )
    deadline_proximity_score = _deadline_proximity_score(hours_until_deadline, config)
    gap_score = _gap_score(
        authority_freshness_score=authority_freshness_score,
        cadence_adherence_score=cadence_adherence_score,
        latest_verified_age_score=latest_verified_age_score,
        contradiction_pressure_score=contradiction_pressure_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        verification_coverage_score=verification_coverage_score,
        deadline_proximity_score=deadline_proximity_score,
        config=config,
    )
    status = _row_status(
        authority_freshness_score=authority_freshness_score,
        cadence_adherence_score=cadence_adherence_score,
        latest_verified_age_score=latest_verified_age_score,
        contradiction_pressure_score=contradiction_pressure_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        verification_coverage_score=verification_coverage_score,
        deadline_proximity_score=deadline_proximity_score,
        gap_score=gap_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        event.reason_codes,
        status=status,
        authority_last_updated_at=event.authority_last_updated_at,
        latest_verified_at=event.latest_verified_at,
        deadline_at=event.deadline_at,
        authority_freshness_score=authority_freshness_score,
        cadence_adherence_score=cadence_adherence_score,
        latest_verified_age_score=latest_verified_age_score,
        contradiction_pressure_score=contradiction_pressure_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        verification_coverage_score=verification_coverage_score,
        deadline_proximity_score=deadline_proximity_score,
        gap_score=gap_score,
        config=config,
    )
    return ResearchEventResolutionAuthorityTimingGapRow(
        event_digest=_event_digest(event.event_reference),
        observed_at=event.observed_at,
        authority_last_updated_at=event.authority_last_updated_at,
        latest_verified_at=event.latest_verified_at,
        deadline_at=event.deadline_at,
        expected_update_cadence_hours=event.expected_update_cadence_hours,
        authority_age_hours=authority_age_hours,
        latest_verified_age_hours=latest_verified_age_hours,
        hours_until_deadline=hours_until_deadline,
        authority_freshness_score=authority_freshness_score,
        cadence_adherence_score=cadence_adherence_score,
        latest_verified_age_score=latest_verified_age_score,
        contradiction_count=event.contradiction_count,
        highest_contradiction_severity=event.highest_contradiction_severity,
        contradiction_pressure_score=contradiction_pressure_score,
        verification_required_count=event.verification_required_count,
        verification_completed_count=event.verification_completed_count,
        verification_coverage_score=verification_coverage_score,
        ambiguity_risk_score=event.ambiguity_risk_score,
        deadline_proximity_score=deadline_proximity_score,
        gap_score=gap_score,
        status=status,
        reason_codes=reason_codes,
    )


def _authority_freshness_score(
    authority_age_hours: Decimal | None,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> Decimal:
    if authority_age_hours is None:
        return ZERO
    if authority_age_hours >= config.max_authority_age_hours:
        return ZERO
    return _quantize(ONE - (authority_age_hours / config.max_authority_age_hours))


def _cadence_adherence_score(
    *,
    authority_age_hours: Decimal | None,
    expected_update_cadence_hours: Decimal,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> Decimal:
    if authority_age_hours is None:
        return ZERO
    if authority_age_hours <= expected_update_cadence_hours:
        return ONE.quantize(DECIMAL_QUANTUM)
    block_age = expected_update_cadence_hours * config.cadence_block_multiple
    if authority_age_hours >= block_age:
        return ZERO
    excess_age = authority_age_hours - expected_update_cadence_hours
    excess_window = block_age - expected_update_cadence_hours
    return _quantize(ONE - (excess_age / excess_window))


def _latest_verified_age_score(
    latest_verified_age_hours: Decimal | None,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> Decimal:
    if latest_verified_age_hours is None:
        return ZERO
    if latest_verified_age_hours >= config.max_latest_verified_age_hours:
        return ZERO
    return _quantize(ONE - (latest_verified_age_hours / config.max_latest_verified_age_hours))


def _contradiction_pressure_score(
    *,
    contradiction_count: Decimal,
    highest_contradiction_severity: Decimal,
    verification_required_count: Decimal,
) -> Decimal:
    count_floor = _maximum(ONE, verification_required_count)
    count_pressure = _capped_ratio(contradiction_count, count_floor)
    return _quantize((count_pressure + highest_contradiction_severity) / Decimal("2"))


def _verification_coverage_score(
    *,
    required_count: Decimal,
    completed_count: Decimal,
) -> Decimal:
    if required_count == ZERO:
        return ONE.quantize(DECIMAL_QUANTUM)
    return _capped_ratio(completed_count, required_count)


def _deadline_proximity_score(
    hours_until_deadline: Decimal | None,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> Decimal:
    if hours_until_deadline is None:
        return ZERO
    return _capped_ratio(hours_until_deadline, config.min_deadline_buffer_hours)


def _gap_score(
    *,
    authority_freshness_score: Decimal,
    cadence_adherence_score: Decimal,
    latest_verified_age_score: Decimal,
    contradiction_pressure_score: Decimal,
    ambiguity_risk_score: Decimal,
    verification_coverage_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> Decimal:
    return _quantize(
        (ONE - authority_freshness_score) * config.authority_freshness_weight
        + (ONE - cadence_adherence_score) * config.cadence_adherence_weight
        + (ONE - latest_verified_age_score) * config.latest_verified_age_weight
        + contradiction_pressure_score * config.contradiction_pressure_weight
        + ambiguity_risk_score * config.ambiguity_risk_weight
        + (ONE - verification_coverage_score) * config.verification_coverage_weight
        + (ONE - deadline_proximity_score) * config.deadline_proximity_weight,
    )


def _row_status(
    *,
    authority_freshness_score: Decimal,
    cadence_adherence_score: Decimal,
    latest_verified_age_score: Decimal,
    contradiction_pressure_score: Decimal,
    ambiguity_risk_score: Decimal,
    verification_coverage_score: Decimal,
    deadline_proximity_score: Decimal,
    gap_score: Decimal,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> str:
    if (
        gap_score >= config.block_gap_threshold
        or authority_freshness_score <= config.block_authority_freshness_score
        or cadence_adherence_score <= config.block_cadence_adherence_score
        or latest_verified_age_score <= config.block_latest_verified_age_score
        or contradiction_pressure_score >= config.block_contradiction_pressure_score
        or ambiguity_risk_score >= config.block_ambiguity_risk_score
        or verification_coverage_score <= config.block_verification_coverage_score
        or deadline_proximity_score <= config.block_deadline_proximity_score
    ):
        return STATUS_BLOCK
    if (
        gap_score >= config.watch_gap_threshold
        or authority_freshness_score < config.watch_authority_freshness_score
        or cadence_adherence_score < config.watch_cadence_adherence_score
        or latest_verified_age_score < config.watch_latest_verified_age_score
        or contradiction_pressure_score >= config.watch_contradiction_pressure_score
        or ambiguity_risk_score >= config.watch_ambiguity_risk_score
        or verification_coverage_score < config.watch_verification_coverage_score
        or deadline_proximity_score < config.watch_deadline_proximity_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    status: str,
    authority_last_updated_at: datetime | None,
    latest_verified_at: datetime | None,
    deadline_at: datetime | None,
    authority_freshness_score: Decimal,
    cadence_adherence_score: Decimal,
    latest_verified_age_score: Decimal,
    contradiction_pressure_score: Decimal,
    ambiguity_risk_score: Decimal,
    verification_coverage_score: Decimal,
    deadline_proximity_score: Decimal,
    gap_score: Decimal,
    config: ResearchEventResolutionAuthorityTimingGapConfig,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(status)
    if authority_last_updated_at is None:
        codes.add(REASON_AUTHORITY_UPDATE_MISSING)
    if authority_freshness_score < config.watch_authority_freshness_score:
        codes.add(REASON_AUTHORITY_FRESHNESS_GAP)
    if cadence_adherence_score < config.watch_cadence_adherence_score:
        codes.add(REASON_CADENCE_ADHERENCE_GAP)
    if latest_verified_at is None:
        codes.add(REASON_LATEST_VERIFIED_MISSING)
    if latest_verified_age_score < config.watch_latest_verified_age_score:
        codes.add(REASON_LATEST_VERIFIED_STALE)
    if contradiction_pressure_score >= config.watch_contradiction_pressure_score:
        codes.add(REASON_CONTRADICTION_PRESSURE)
    if ambiguity_risk_score >= config.watch_ambiguity_risk_score:
        codes.add(REASON_AMBIGUITY_RISK)
    if verification_coverage_score < config.watch_verification_coverage_score:
        codes.add(REASON_VERIFICATION_COVERAGE_GAP)
    if deadline_at is None:
        codes.add(REASON_DEADLINE_MISSING)
    if deadline_proximity_score < config.watch_deadline_proximity_score:
        codes.add(REASON_DEADLINE_PRESSURE)
    if gap_score >= config.watch_gap_threshold:
        codes.add(REASON_TIMING_GAP_ELEVATED)
    return _normalize_reason_codes(tuple(sorted(codes)))


def _duration_hours(started_at: datetime | None, finished_at: datetime | None) -> Decimal | None:
    if started_at is None or finished_at is None:
        return None
    if finished_at < started_at:
        raise ValueError("finished_at must not be before started_at")
    delta = finished_at - started_at
    seconds = Decimal(delta.days) * Decimal("86400") + Decimal(delta.seconds)
    seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds / Decimal("3600"))


def _count_status(
    rows: tuple[ResearchEventResolutionAuthorityTimingGapRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(ONE for row in rows if row.status == status)).quantize(
        DECIMAL_QUANTUM,
    )


def _report_status(rows: tuple[ResearchEventResolutionAuthorityTimingGapRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionAuthorityTimingGapRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, Decimal(count).quantize(DECIMAL_QUANTUM))
        for reason_code, count in sorted(counter.items())
    )


def _average(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return _quantize(sum(normalized_values, ZERO) / Decimal(len(normalized_values)))


def _maximum_or_zero(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return max(normalized_values).quantize(DECIMAL_QUANTUM)


def _minimum_or_zero(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return min(normalized_values).quantize(DECIMAL_QUANTUM)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _minimum(ONE, _quantize(numerator / denominator))


def _minimum(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return left
    return right


def _maximum(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _event_digest(event_reference: str) -> str:
    return hashlib.sha256(event_reference.encode("utf-8")).hexdigest()


def _report_validation_digest(
    report: ResearchEventResolutionAuthorityTimingGapReport,
) -> str:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_report_validation_digest(
    report: ResearchEventResolutionAuthorityTimingGapReport,
) -> None:
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_json_string_public_payload("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(DECIMAL_QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _require_json_string_public_payload(path: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} contains non-JSON public key")
            _require_json_string_public_payload(f"{path}.{key}", item)
        return
    if isinstance(value, list):
        for item in value:
            _require_json_string_public_payload(path, item)
        return
    if type(value) in (str, bool) or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{path} contains unsafe public numeric")
    raise ValueError(f"{path} contains non-JSON public value")


def _validate_config(config: ResearchEventResolutionAuthorityTimingGapConfig) -> None:
    weights = (
        config.authority_freshness_weight
        + config.cadence_adherence_weight
        + config.latest_verified_age_weight
        + config.contradiction_pressure_weight
        + config.ambiguity_risk_weight
        + config.verification_coverage_weight
        + config.deadline_proximity_weight
    )
    if weights != ONE.quantize(DECIMAL_QUANTUM):
        raise ValueError("gap weights must sum to 1.0000")
    if config.block_gap_threshold <= config.watch_gap_threshold:
        raise ValueError("block_gap_threshold must exceed watch_gap_threshold")
    if config.cadence_block_multiple <= ONE:
        raise ValueError("cadence_block_multiple must exceed 1")
    threshold_pairs = (
        ("authority_freshness", config.block_authority_freshness_score, config.watch_authority_freshness_score),
        ("cadence_adherence", config.block_cadence_adherence_score, config.watch_cadence_adherence_score),
        ("latest_verified_age", config.block_latest_verified_age_score, config.watch_latest_verified_age_score),
        ("verification_coverage", config.block_verification_coverage_score, config.watch_verification_coverage_score),
        ("deadline_proximity", config.block_deadline_proximity_score, config.watch_deadline_proximity_score),
    )
    for label, block_value, watch_value in threshold_pairs:
        if block_value >= watch_value:
            raise ValueError(f"block {label} threshold must be below watch threshold")
    if config.block_contradiction_pressure_score <= config.watch_contradiction_pressure_score:
        raise ValueError("block_contradiction_pressure_score must exceed watch threshold")
    if config.block_ambiguity_risk_score <= config.watch_ambiguity_risk_score:
        raise ValueError("block_ambiguity_risk_score must exceed watch threshold")


def _validate_row(row: ResearchEventResolutionAuthorityTimingGapRow) -> None:
    if row.authority_last_updated_at is not None and row.authority_last_updated_at > row.observed_at:
        raise ValueError("authority_last_updated_at must not be after observed_at")
    if row.latest_verified_at is not None and row.latest_verified_at > row.observed_at:
        raise ValueError("latest_verified_at must not be after observed_at")
    if row.deadline_at is not None and row.deadline_at < row.observed_at:
        raise ValueError("deadline_at must not be before observed_at")
    if row.verification_completed_count > row.verification_required_count:
        raise ValueError(
            "verification_completed_count must not exceed verification_required_count",
        )


def _validate_report(report: ResearchEventResolutionAuthorityTimingGapReport) -> None:
    rows = report.rows
    if report.row_count != Decimal(len(rows)).quantize(DECIMAL_QUANTUM):
        raise ValueError("row_count must equal rows length")
    expected_counts = {
        STATUS_PASS: report.pass_count,
        STATUS_WATCH: report.watch_count,
        STATUS_BLOCK: report.block_count,
    }
    for status, expected_count in expected_counts.items():
        if expected_count != _count_status(rows, status):
            raise ValueError(f"{status}_count must equal row status count")
    if report.average_gap_score != _average(row.gap_score for row in rows):
        raise ValueError("average_gap_score must equal row average")
    if report.highest_gap_score != _maximum_or_zero(row.gap_score for row in rows):
        raise ValueError("highest_gap_score must equal row maximum")
    if report.weakest_authority_freshness_score != _minimum_or_zero(
        row.authority_freshness_score for row in rows
    ):
        raise ValueError("weakest_authority_freshness_score must equal row minimum")
    if report.status != _report_status(rows):
        raise ValueError("status must reflect row statuses")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must equal row reason code counts")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventResolutionAuthorityTimingGapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionAuthorityTimingGapRow:
            raise ValueError("rows must contain ResearchEventResolutionAuthorityTimingGapRow")
    return tuple(rows)


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts entries must be pairs")
        reason_code, count = item
        normalized_reason = _normalize_reason_code(reason_code)
        if normalized_reason in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(normalized_reason)
        normalized.append(
            (
                normalized_reason,
                _normalize_count_decimal("reason_code_count", count),
            ),
        )
    return tuple(sorted(normalized, key=lambda item: item[0]))


def _normalize_reason_codes(
    reason_codes: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(sorted({_normalize_reason_code(reason) for reason in reason_codes}))
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    return normalized


def _normalize_reason_code(value: object) -> str:
    _require_canonical_string("reason_code", value)
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("reason_code contains unsafe text")
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _normalize_count_or_measure_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if field_name.endswith("_count") and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_status(field_name: str, value: object) -> None:
    if value not in RESEARCH_EVENT_RESOLUTION_AUTHORITY_TIMING_GAP_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 digest") from exc


def _reject_unsafe_public_payload(path: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{path} contains unsafe non-string key")
            _reject_unsafe_text(f"{path}.{key}", key)
            _reject_unsafe_public_payload(f"{path}.{key}", item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(path, item)
    elif type(value) is str:
        _reject_unsafe_text(path, value)


def _reject_unsafe_text(path: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path} contains unsafe public text")


__all__ = (
    "CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_AUTHORITY_TIMING_GAP_STATUSES",
    "ResearchEventResolutionAuthorityTimingGapConfig",
    "ResearchEventResolutionAuthorityTimingGapInput",
    "ResearchEventResolutionAuthorityTimingGapReport",
    "ResearchEventResolutionAuthorityTimingGapRow",
    "build_research_event_resolution_authority_timing_gap_report",
    "research_event_resolution_authority_timing_gap_digest",
    "research_event_resolution_authority_timing_gap_payload",
    "validate_research_event_resolution_authority_timing_gap_digest",
)
