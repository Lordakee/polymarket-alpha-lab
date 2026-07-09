"""Report-only authority conflict decay scorer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIG_VERSION = "research_event_resolution_authority_conflict_decay_v1"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_EVENT_RESOLUTION_AUTHORITY_CONFLICT_DECAY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_AUTHORITY_UPDATE_MISSING = "authority_update_missing"
REASON_AUTHORITY_UPDATE_STALENESS_WATCH = "authority_update_staleness_watch"
REASON_AUTHORITY_UPDATE_STALENESS_BLOCK = "authority_update_staleness_block"
REASON_CONFLICT_AGE_WATCH = "authority_conflict_age_watch"
REASON_CONFLICT_AGE_BLOCK = "authority_conflict_age_block"
REASON_CONFLICT_SHARE_WATCH = "authority_conflict_share_watch"
REASON_CONFLICT_SHARE_BLOCK = "authority_conflict_share_block"
REASON_CONFLICT_RECENCY_WATCH = "authority_conflict_recency_watch"
REASON_CONFLICT_RECENCY_BLOCK = "authority_conflict_recency_block"
REASON_CONFLICT_SEVERITY_WATCH = "authority_conflict_severity_watch"
REASON_CONFLICT_SEVERITY_BLOCK = "authority_conflict_severity_block"
REASON_INDEPENDENCE_GAP = "resolution_authority_independence_gap"
REASON_EVIDENCE_GAP = "resolution_evidence_gap"
REASON_RECURRENCE_PRESSURE = "conflict_recurrence_pressure"
REASON_DECAY_ELEVATED = "authority_conflict_decay_elevated"

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "source url",
        "source_url",
        "url",
        "http",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "://",
    ),
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityConflictDecayConfig:
    config_version: str = CONFIG_VERSION
    conflict_age_weight: Decimal = Decimal("0.1500")
    authority_update_weight: Decimal = Decimal("0.1500")
    conflict_share_weight: Decimal = Decimal("0.2000")
    conflict_recency_weight: Decimal = Decimal("0.1500")
    conflict_severity_weight: Decimal = Decimal("0.1430")
    independence_weight: Decimal = Decimal("0.0820")
    resolution_evidence_weight: Decimal = Decimal("0.0750")
    recurrence_weight: Decimal = Decimal("0.0500")
    watch_decay_threshold: Decimal = Decimal("0.2500")
    block_decay_threshold: Decimal = Decimal("0.5000")
    max_conflict_age_hours: Decimal = Decimal("72")
    max_authority_update_age_hours: Decimal = Decimal("48")
    conflict_recency_window_hours: Decimal = Decimal("72")
    required_independent_authority_count: Decimal = Decimal("2")
    required_resolution_evidence_count: Decimal = Decimal("3")
    recurrence_block_count: Decimal = Decimal("4")
    watch_conflict_age_pressure_score: Decimal = Decimal("0.5000")
    block_conflict_age_pressure_score: Decimal = Decimal("1.0000")
    watch_authority_update_decay_score: Decimal = Decimal("0.5000")
    block_authority_update_decay_score: Decimal = Decimal("1.0000")
    watch_conflict_share: Decimal = Decimal("0.2500")
    block_conflict_share: Decimal = Decimal("0.6000")
    watch_conflict_recency_pressure_score: Decimal = Decimal("0.5000")
    block_conflict_recency_pressure_score: Decimal = Decimal("0.9000")
    watch_conflict_severity_score: Decimal = Decimal("0.2500")
    block_conflict_severity_score: Decimal = Decimal("0.7000")
    watch_independence_score: Decimal = Decimal("0.8000")
    block_independence_score: Decimal = Decimal("0.5000")
    watch_resolution_evidence_score: Decimal = Decimal("0.8000")
    block_resolution_evidence_score: Decimal = Decimal("0.5000")
    watch_recurrence_pressure_score: Decimal = Decimal("0.5000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityConflictDecayConfig:
            raise TypeError(
                "ResearchEventResolutionAuthorityConflictDecayConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventResolutionAuthorityConflictDecayConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "conflict_age_weight",
            "authority_update_weight",
            "conflict_share_weight",
            "conflict_recency_weight",
            "conflict_severity_weight",
            "independence_weight",
            "resolution_evidence_weight",
            "recurrence_weight",
            "watch_decay_threshold",
            "block_decay_threshold",
            "watch_conflict_age_pressure_score",
            "block_conflict_age_pressure_score",
            "watch_authority_update_decay_score",
            "block_authority_update_decay_score",
            "watch_conflict_share",
            "block_conflict_share",
            "watch_conflict_recency_pressure_score",
            "block_conflict_recency_pressure_score",
            "watch_conflict_severity_score",
            "block_conflict_severity_score",
            "watch_independence_score",
            "block_independence_score",
            "watch_resolution_evidence_score",
            "block_resolution_evidence_score",
            "watch_recurrence_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_conflict_age_hours",
            "max_authority_update_age_hours",
            "conflict_recency_window_hours",
            "required_independent_authority_count",
            "required_resolution_evidence_count",
            "recurrence_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("authority conflict decay config", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityConflictDecayInput:
    event_reference: str
    observed_at: datetime
    first_conflict_seen_at: datetime | None
    last_authority_update_at: datetime | None
    last_conflict_seen_at: datetime | None
    authoritative_signal_count: Decimal
    conflicting_signal_count: Decimal
    independent_authority_count: Decimal
    resolution_evidence_count: Decimal
    conflict_severity_score: Decimal
    conflict_recurrence_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityConflictDecayInput:
            raise TypeError(
                "ResearchEventResolutionAuthorityConflictDecayInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchEventResolutionAuthorityConflictDecayInput)
        _require_canonical_string("event_reference", self.event_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "first_conflict_seen_at",
            "last_authority_update_at",
            "last_conflict_seen_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
                if getattr(self, field_name) > self.observed_at:
                    raise ValueError(f"{field_name} must not be after observed_at")
        for field_name in (
            "authoritative_signal_count",
            "conflicting_signal_count",
            "independent_authority_count",
            "resolution_evidence_count",
            "conflict_recurrence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.authoritative_signal_count + self.conflicting_signal_count <= ZERO:
            raise ValueError("total signal count must be positive")
        if self.independent_authority_count > self.authoritative_signal_count:
            raise ValueError(
                "independent_authority_count must not exceed authoritative_signal_count",
            )
        object.__setattr__(
            self,
            "conflict_severity_score",
            _normalize_probability("conflict_severity_score", self.conflict_severity_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        require_paper_only_flags("authority conflict decay input", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityConflictDecayRow:
    event_digest: str
    observed_at: datetime
    first_conflict_seen_at: datetime | None
    last_authority_update_at: datetime | None
    last_conflict_seen_at: datetime | None
    conflict_age_hours: Decimal | None
    authority_update_age_hours: Decimal | None
    hours_since_last_conflict: Decimal | None
    authoritative_signal_count: Decimal
    conflicting_signal_count: Decimal
    independent_authority_count: Decimal
    resolution_evidence_count: Decimal
    conflict_share: Decimal
    conflict_age_pressure_score: Decimal
    authority_update_decay_score: Decimal
    conflict_recency_pressure_score: Decimal
    independence_score: Decimal
    resolution_evidence_score: Decimal
    conflict_severity_score: Decimal
    conflict_recurrence_count: Decimal
    recurrence_pressure_score: Decimal
    confidence_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityConflictDecayRow:
            raise TypeError(
                "ResearchEventResolutionAuthorityConflictDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventResolutionAuthorityConflictDecayRow)
        _require_sha256_digest("event_digest", self.event_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "first_conflict_seen_at",
            "last_authority_update_at",
            "last_conflict_seen_at",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _as_utc(field_name, value))
        for field_name in (
            "conflict_age_hours",
            "authority_update_age_hours",
            "hours_since_last_conflict",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_nonnegative_decimal(field_name, value),
                )
        for field_name in (
            "authoritative_signal_count",
            "conflicting_signal_count",
            "independent_authority_count",
            "resolution_evidence_count",
            "conflict_recurrence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "conflict_share",
            "conflict_age_pressure_score",
            "authority_update_decay_score",
            "conflict_recency_pressure_score",
            "independence_score",
            "resolution_evidence_score",
            "conflict_severity_score",
            "recurrence_pressure_score",
            "confidence_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("authority conflict decay row", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityConflictDecayReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_confidence_decay_score: Decimal
    highest_confidence_decay_score: Decimal
    highest_conflict_share: Decimal
    weakest_independence_score: Decimal
    status: str
    rows: tuple[ResearchEventResolutionAuthorityConflictDecayRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityConflictDecayReport:
            raise TypeError(
                "ResearchEventResolutionAuthorityConflictDecayReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEventResolutionAuthorityConflictDecayReport)
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
            "average_confidence_decay_score",
            "highest_confidence_decay_score",
            "highest_conflict_share",
            "weakest_independence_score",
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
        require_paper_only_flags("authority conflict decay report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "authority conflict decay report",
            _payload_value(asdict(self)),
        )


def build_research_event_resolution_authority_conflict_decay_report(
    events: tuple[ResearchEventResolutionAuthorityConflictDecayInput, ...],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> ResearchEventResolutionAuthorityConflictDecayReport:
    """Build a deterministic, report-only authority conflict decay snapshot."""

    if type(events) is not tuple:
        raise ValueError("events must be a tuple")
    if type(config) is not ResearchEventResolutionAuthorityConflictDecayConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionAuthorityConflictDecayConfig",
        )
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_build_row(event=event, config=config) for event in events),
            key=lambda row: row.event_digest,
        ),
    )
    return ResearchEventResolutionAuthorityConflictDecayReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        average_confidence_decay_score=_average(
            row.confidence_decay_score for row in rows
        ),
        highest_confidence_decay_score=_maximum_or_zero(
            row.confidence_decay_score for row in rows
        ),
        highest_conflict_share=_maximum_or_zero(row.conflict_share for row in rows),
        weakest_independence_score=_minimum_or_zero(row.independence_score for row in rows),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_resolution_authority_conflict_decay_payload(
    report: ResearchEventResolutionAuthorityConflictDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionAuthorityConflictDecayReport:
        require_paper_only_flags("authority conflict decay report", report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityConflictDecayReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def validate_research_event_resolution_authority_conflict_decay_digest(
    report: ResearchEventResolutionAuthorityConflictDecayReport,
) -> None:
    if type(report) is not ResearchEventResolutionAuthorityConflictDecayReport:
        raise ValueError("report must be a ResearchEventResolutionAuthorityConflictDecayReport")
    _require_report_validation_digest(report)


def research_event_resolution_authority_conflict_decay_digest(
    report: ResearchEventResolutionAuthorityConflictDecayReport,
) -> str:
    if type(report) is not ResearchEventResolutionAuthorityConflictDecayReport:
        raise ValueError("report must be a ResearchEventResolutionAuthorityConflictDecayReport")
    return _report_validation_digest(report)


def _build_row(
    *,
    event: ResearchEventResolutionAuthorityConflictDecayInput,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> ResearchEventResolutionAuthorityConflictDecayRow:
    if type(event) is not ResearchEventResolutionAuthorityConflictDecayInput:
        raise ValueError(
            "events must contain ResearchEventResolutionAuthorityConflictDecayInput values",
        )
    conflict_age_hours = _duration_hours(event.first_conflict_seen_at, event.observed_at)
    authority_update_age_hours = _duration_hours(
        event.last_authority_update_at,
        event.observed_at,
    )
    hours_since_last_conflict = _duration_hours(
        event.last_conflict_seen_at,
        event.observed_at,
    )
    conflict_share = _conflict_share(
        event.authoritative_signal_count,
        event.conflicting_signal_count,
    )
    conflict_age_pressure_score = _conflict_age_pressure_score(
        conflict_age_hours,
        config,
    )
    authority_update_decay_score = _authority_update_decay_score(
        authority_update_age_hours,
        config,
    )
    conflict_recency_pressure_score = _conflict_recency_pressure_score(
        hours_since_last_conflict,
        config,
    )
    independence_score = _capped_ratio(
        event.independent_authority_count,
        config.required_independent_authority_count,
    )
    resolution_evidence_score = _capped_ratio(
        event.resolution_evidence_count,
        config.required_resolution_evidence_count,
    )
    recurrence_pressure_score = _capped_ratio(
        event.conflict_recurrence_count,
        config.recurrence_block_count,
    )
    confidence_decay_score = _confidence_decay_score(
        conflict_age_pressure_score=conflict_age_pressure_score,
        authority_update_decay_score=authority_update_decay_score,
        conflict_share=conflict_share,
        conflict_recency_pressure_score=conflict_recency_pressure_score,
        conflict_severity_score=event.conflict_severity_score,
        independence_score=independence_score,
        resolution_evidence_score=resolution_evidence_score,
        recurrence_pressure_score=recurrence_pressure_score,
        config=config,
    )
    status = _row_status(
        conflict_age_pressure_score=conflict_age_pressure_score,
        authority_update_decay_score=authority_update_decay_score,
        conflict_share=conflict_share,
        conflict_recency_pressure_score=conflict_recency_pressure_score,
        conflict_severity_score=event.conflict_severity_score,
        independence_score=independence_score,
        resolution_evidence_score=resolution_evidence_score,
        recurrence_pressure_score=recurrence_pressure_score,
        confidence_decay_score=confidence_decay_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        event.reason_codes,
        status=status,
        first_conflict_seen_at=event.first_conflict_seen_at,
        last_authority_update_at=event.last_authority_update_at,
        last_conflict_seen_at=event.last_conflict_seen_at,
        conflict_age_pressure_score=conflict_age_pressure_score,
        authority_update_decay_score=authority_update_decay_score,
        conflict_share=conflict_share,
        conflict_recency_pressure_score=conflict_recency_pressure_score,
        conflict_severity_score=event.conflict_severity_score,
        independence_score=independence_score,
        resolution_evidence_score=resolution_evidence_score,
        recurrence_pressure_score=recurrence_pressure_score,
        confidence_decay_score=confidence_decay_score,
        config=config,
    )
    return ResearchEventResolutionAuthorityConflictDecayRow(
        event_digest=_event_digest(event.event_reference),
        observed_at=event.observed_at,
        first_conflict_seen_at=event.first_conflict_seen_at,
        last_authority_update_at=event.last_authority_update_at,
        last_conflict_seen_at=event.last_conflict_seen_at,
        conflict_age_hours=conflict_age_hours,
        authority_update_age_hours=authority_update_age_hours,
        hours_since_last_conflict=hours_since_last_conflict,
        authoritative_signal_count=event.authoritative_signal_count,
        conflicting_signal_count=event.conflicting_signal_count,
        independent_authority_count=event.independent_authority_count,
        resolution_evidence_count=event.resolution_evidence_count,
        conflict_share=conflict_share,
        conflict_age_pressure_score=conflict_age_pressure_score,
        authority_update_decay_score=authority_update_decay_score,
        conflict_recency_pressure_score=conflict_recency_pressure_score,
        independence_score=independence_score,
        resolution_evidence_score=resolution_evidence_score,
        conflict_severity_score=event.conflict_severity_score,
        conflict_recurrence_count=event.conflict_recurrence_count,
        recurrence_pressure_score=recurrence_pressure_score,
        confidence_decay_score=confidence_decay_score,
        status=status,
        reason_codes=reason_codes,
    )


def _conflict_share(authoritative_count: Decimal, conflicting_count: Decimal) -> Decimal:
    total = authoritative_count + conflicting_count
    if total <= ZERO:
        raise ValueError("total signal count must be positive")
    return _quantize(conflicting_count / total)


def _conflict_age_pressure_score(
    conflict_age_hours: Decimal | None,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> Decimal:
    if conflict_age_hours is None:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return _capped_ratio(conflict_age_hours, config.max_conflict_age_hours)


def _authority_update_decay_score(
    authority_update_age_hours: Decimal | None,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> Decimal:
    if authority_update_age_hours is None:
        return ONE.quantize(DECIMAL_QUANTUM)
    return _capped_ratio(
        authority_update_age_hours,
        config.max_authority_update_age_hours,
    )


def _conflict_recency_pressure_score(
    hours_since_last_conflict: Decimal | None,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> Decimal:
    if hours_since_last_conflict is None:
        return ZERO.quantize(DECIMAL_QUANTUM)
    if hours_since_last_conflict >= config.conflict_recency_window_hours:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return _quantize(
        ONE - (hours_since_last_conflict / config.conflict_recency_window_hours),
    )


def _confidence_decay_score(
    *,
    conflict_age_pressure_score: Decimal,
    authority_update_decay_score: Decimal,
    conflict_share: Decimal,
    conflict_recency_pressure_score: Decimal,
    conflict_severity_score: Decimal,
    independence_score: Decimal,
    resolution_evidence_score: Decimal,
    recurrence_pressure_score: Decimal,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> Decimal:
    return _quantize(
        conflict_age_pressure_score * config.conflict_age_weight
        + authority_update_decay_score * config.authority_update_weight
        + conflict_share * config.conflict_share_weight
        + conflict_recency_pressure_score * config.conflict_recency_weight
        + conflict_severity_score * config.conflict_severity_weight
        + (ONE - independence_score) * config.independence_weight
        + (ONE - resolution_evidence_score) * config.resolution_evidence_weight
        + recurrence_pressure_score * config.recurrence_weight,
    )


def _row_status(
    *,
    conflict_age_pressure_score: Decimal,
    authority_update_decay_score: Decimal,
    conflict_share: Decimal,
    conflict_recency_pressure_score: Decimal,
    conflict_severity_score: Decimal,
    independence_score: Decimal,
    resolution_evidence_score: Decimal,
    recurrence_pressure_score: Decimal,
    confidence_decay_score: Decimal,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> str:
    if (
        confidence_decay_score >= config.block_decay_threshold
        or conflict_age_pressure_score >= config.block_conflict_age_pressure_score
        or authority_update_decay_score >= config.block_authority_update_decay_score
        or conflict_share >= config.block_conflict_share
        or conflict_recency_pressure_score >= config.block_conflict_recency_pressure_score
        or conflict_severity_score >= config.block_conflict_severity_score
        or independence_score <= config.block_independence_score
        or resolution_evidence_score <= config.block_resolution_evidence_score
    ):
        return STATUS_BLOCK
    if (
        confidence_decay_score >= config.watch_decay_threshold
        or conflict_age_pressure_score >= config.watch_conflict_age_pressure_score
        or authority_update_decay_score >= config.watch_authority_update_decay_score
        or conflict_share >= config.watch_conflict_share
        or conflict_recency_pressure_score >= config.watch_conflict_recency_pressure_score
        or conflict_severity_score >= config.watch_conflict_severity_score
        or independence_score < config.watch_independence_score
        or resolution_evidence_score < config.watch_resolution_evidence_score
        or recurrence_pressure_score >= config.watch_recurrence_pressure_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    status: str,
    first_conflict_seen_at: datetime | None,
    last_authority_update_at: datetime | None,
    last_conflict_seen_at: datetime | None,
    conflict_age_pressure_score: Decimal,
    authority_update_decay_score: Decimal,
    conflict_share: Decimal,
    conflict_recency_pressure_score: Decimal,
    conflict_severity_score: Decimal,
    independence_score: Decimal,
    resolution_evidence_score: Decimal,
    recurrence_pressure_score: Decimal,
    confidence_decay_score: Decimal,
    config: ResearchEventResolutionAuthorityConflictDecayConfig,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(status)
    if first_conflict_seen_at is not None:
        if conflict_age_pressure_score >= config.block_conflict_age_pressure_score:
            codes.add(REASON_CONFLICT_AGE_BLOCK)
        elif conflict_age_pressure_score >= config.watch_conflict_age_pressure_score:
            codes.add(REASON_CONFLICT_AGE_WATCH)
    if last_authority_update_at is None:
        codes.add(REASON_AUTHORITY_UPDATE_MISSING)
        codes.add(REASON_AUTHORITY_UPDATE_STALENESS_BLOCK)
    elif authority_update_decay_score >= config.block_authority_update_decay_score:
        codes.add(REASON_AUTHORITY_UPDATE_STALENESS_BLOCK)
    elif authority_update_decay_score >= config.watch_authority_update_decay_score:
        codes.add(REASON_AUTHORITY_UPDATE_STALENESS_WATCH)
    if conflict_share >= config.block_conflict_share:
        codes.add(REASON_CONFLICT_SHARE_BLOCK)
    elif conflict_share >= config.watch_conflict_share:
        codes.add(REASON_CONFLICT_SHARE_WATCH)
    if last_conflict_seen_at is not None:
        if conflict_recency_pressure_score >= config.block_conflict_recency_pressure_score:
            codes.add(REASON_CONFLICT_RECENCY_BLOCK)
        elif conflict_recency_pressure_score >= config.watch_conflict_recency_pressure_score:
            codes.add(REASON_CONFLICT_RECENCY_WATCH)
    if conflict_severity_score >= config.block_conflict_severity_score:
        codes.add(REASON_CONFLICT_SEVERITY_BLOCK)
    elif conflict_severity_score >= config.watch_conflict_severity_score:
        codes.add(REASON_CONFLICT_SEVERITY_WATCH)
    if independence_score < config.watch_independence_score:
        codes.add(REASON_INDEPENDENCE_GAP)
    if resolution_evidence_score < config.watch_resolution_evidence_score:
        codes.add(REASON_EVIDENCE_GAP)
    if recurrence_pressure_score >= config.watch_recurrence_pressure_score:
        codes.add(REASON_RECURRENCE_PRESSURE)
    if confidence_decay_score >= config.watch_decay_threshold:
        codes.add(REASON_DECAY_ELEVATED)
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
    rows: tuple[ResearchEventResolutionAuthorityConflictDecayRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(ONE for row in rows if row.status == status)).quantize(
        DECIMAL_QUANTUM,
    )


def _report_status(rows: tuple[ResearchEventResolutionAuthorityConflictDecayRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionAuthorityConflictDecayRow, ...],
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
    ratio = _quantize(numerator / denominator)
    if ratio > ONE:
        return ONE.quantize(DECIMAL_QUANTUM)
    return ratio


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _event_digest(event_reference: str) -> str:
    return hashlib.sha256(event_reference.encode("utf-8")).hexdigest()


def _report_validation_digest(
    report: ResearchEventResolutionAuthorityConflictDecayReport,
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
    report: ResearchEventResolutionAuthorityConflictDecayReport,
) -> None:
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
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


def _validate_config(config: ResearchEventResolutionAuthorityConflictDecayConfig) -> None:
    weights = (
        config.conflict_age_weight
        + config.authority_update_weight
        + config.conflict_share_weight
        + config.conflict_recency_weight
        + config.conflict_severity_weight
        + config.independence_weight
        + config.resolution_evidence_weight
        + config.recurrence_weight
    )
    if weights != ONE.quantize(DECIMAL_QUANTUM):
        raise ValueError("decay weights must sum to 1.0000")
    if config.block_decay_threshold <= config.watch_decay_threshold:
        raise ValueError("block_decay_threshold must exceed watch_decay_threshold")
    threshold_pairs = (
        (
            "conflict_age_pressure",
            config.block_conflict_age_pressure_score,
            config.watch_conflict_age_pressure_score,
        ),
        (
            "authority_update_decay",
            config.block_authority_update_decay_score,
            config.watch_authority_update_decay_score,
        ),
        ("conflict_share", config.block_conflict_share, config.watch_conflict_share),
        (
            "conflict_recency_pressure",
            config.block_conflict_recency_pressure_score,
            config.watch_conflict_recency_pressure_score,
        ),
        (
            "conflict_severity",
            config.block_conflict_severity_score,
            config.watch_conflict_severity_score,
        ),
    )
    for label, block_value, watch_value in threshold_pairs:
        if block_value > watch_value:
            continue
        raise ValueError(f"block {label} threshold must exceed watch threshold")
    if config.block_independence_score >= config.watch_independence_score:
        raise ValueError("block independence threshold must be below watch threshold")
    if config.block_resolution_evidence_score >= config.watch_resolution_evidence_score:
        raise ValueError("block evidence threshold must be below watch threshold")


def _validate_row(row: ResearchEventResolutionAuthorityConflictDecayRow) -> None:
    for field_name in (
        "first_conflict_seen_at",
        "last_authority_update_at",
        "last_conflict_seen_at",
    ):
        value = getattr(row, field_name)
        if value is not None and value > row.observed_at:
            raise ValueError(f"{field_name} must not be after observed_at")
    if row.authoritative_signal_count + row.conflicting_signal_count <= ZERO:
        raise ValueError("total signal count must be positive")
    if row.independent_authority_count > row.authoritative_signal_count:
        raise ValueError(
            "independent_authority_count must not exceed authoritative_signal_count",
        )


def _validate_report(report: ResearchEventResolutionAuthorityConflictDecayReport) -> None:
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
    if report.average_confidence_decay_score != _average(
        row.confidence_decay_score for row in rows
    ):
        raise ValueError("average_confidence_decay_score must equal row average")
    if report.highest_confidence_decay_score != _maximum_or_zero(
        row.confidence_decay_score for row in rows
    ):
        raise ValueError("highest_confidence_decay_score must equal row maximum")
    if report.highest_conflict_share != _maximum_or_zero(row.conflict_share for row in rows):
        raise ValueError("highest_conflict_share must equal row maximum")
    if report.weakest_independence_score != _minimum_or_zero(
        row.independence_score for row in rows
    ):
        raise ValueError("weakest_independence_score must equal row minimum")
    if report.status != _report_status(rows):
        raise ValueError("status must reflect row statuses")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must equal row reason code counts")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventResolutionAuthorityConflictDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionAuthorityConflictDecayRow:
            raise ValueError("rows must contain ResearchEventResolutionAuthorityConflictDecayRow")
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
    if value not in RESEARCH_EVENT_RESOLUTION_AUTHORITY_CONFLICT_DECAY_STATUSES:
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
    "RESEARCH_EVENT_RESOLUTION_AUTHORITY_CONFLICT_DECAY_STATUSES",
    "ResearchEventResolutionAuthorityConflictDecayConfig",
    "ResearchEventResolutionAuthorityConflictDecayInput",
    "ResearchEventResolutionAuthorityConflictDecayReport",
    "ResearchEventResolutionAuthorityConflictDecayRow",
    "build_research_event_resolution_authority_conflict_decay_report",
    "research_event_resolution_authority_conflict_decay_digest",
    "research_event_resolution_authority_conflict_decay_payload",
    "validate_research_event_resolution_authority_conflict_decay_digest",
)
