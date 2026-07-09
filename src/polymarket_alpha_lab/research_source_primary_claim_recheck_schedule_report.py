"""Report-only primary-claim recheck schedule for sanitized claim buckets.

The module is deterministic and side-effect free. Callers provide already
sanitized claim buckets and local scoring inputs; the report returns a recheck
schedule snapshot without network, storage, scraping, execution, or trading
surfaces.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_RECHECK_SCHEDULE_CONFIG_VERSION = (
    "research-source-primary-claim-recheck-schedule-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "execution",
        "recommendation",
        "sizing",
        "secret",
        "credential",
        "apikey",
        "api_key",
        "private_key",
        "raw",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_recheck_schedule",
    "verification_age_pressure",
    "low_source_authority_pressure",
    "low_corroboration_depth_pressure",
    "contradiction_pressure",
    "low_extraction_confidence_pressure",
    "missing_critical_fields_pressure",
    "deadline_proximity_pressure",
    "recheck_overdue",
    "primary_claim_recheck_pass",
    "primary_claim_recheck_watch",
    "primary_claim_recheck_block",
)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimRecheckScheduleConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_RECHECK_SCHEDULE_CONFIG_VERSION
    )
    stale_after_seconds: Decimal = Decimal("86400.000000")
    deadline_window_seconds: Decimal = Decimal("86400.000000")
    base_recheck_interval_seconds: Decimal = Decimal("86400.000000")
    min_recheck_interval_seconds: Decimal = Decimal("900.000000")
    max_recheck_interval_seconds: Decimal = Decimal("604800.000000")
    watch_recheck_pressure_score: Decimal = Decimal("0.350000")
    block_recheck_pressure_score: Decimal = Decimal("0.750000")
    verification_age_weight: Decimal = Decimal("0.250000")
    authority_gap_weight: Decimal = Decimal("0.150000")
    corroboration_gap_weight: Decimal = Decimal("0.150000")
    contradiction_pressure_weight: Decimal = Decimal("0.150000")
    extraction_confidence_gap_weight: Decimal = Decimal("0.100000")
    missing_critical_field_weight: Decimal = Decimal("0.100000")
    deadline_proximity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimRecheckScheduleConfig:
            raise TypeError(
                "ResearchSourcePrimaryClaimRecheckScheduleConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryClaimRecheckScheduleConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourcePrimaryClaimRecheckScheduleConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_RECHECK_SCHEDULE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_after_seconds",
            "deadline_window_seconds",
            "base_recheck_interval_seconds",
            "min_recheck_interval_seconds",
            "max_recheck_interval_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_recheck_interval_seconds > self.base_recheck_interval_seconds:
            raise ValueError(
                "min_recheck_interval_seconds must not exceed "
                "base_recheck_interval_seconds",
            )
        if self.base_recheck_interval_seconds > self.max_recheck_interval_seconds:
            raise ValueError(
                "base_recheck_interval_seconds must not exceed "
                "max_recheck_interval_seconds",
            )
        for field_name in (
            "watch_recheck_pressure_score",
            "block_recheck_pressure_score",
            "verification_age_weight",
            "authority_gap_weight",
            "corroboration_gap_weight",
            "contradiction_pressure_weight",
            "extraction_confidence_gap_weight",
            "missing_critical_field_weight",
            "deadline_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_recheck_pressure_score >= self.block_recheck_pressure_score:
            raise ValueError(
                "watch_recheck_pressure_score must be below "
                "block_recheck_pressure_score",
            )
        weight_sum = _quantize(
            self.verification_age_weight
            + self.authority_gap_weight
            + self.corroboration_gap_weight
            + self.contradiction_pressure_weight
            + self.extraction_confidence_gap_weight
            + self.missing_critical_field_weight
            + self.deadline_proximity_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("recheck pressure weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimRecheckScheduleInput:
    claim_label: str
    authority_tier_label: str
    last_verified_at: datetime
    authority_score: Decimal
    corroborating_source_count: Decimal
    expected_corroborating_source_count: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    missing_critical_field_count: Decimal
    critical_field_count: Decimal
    decision_deadline_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimRecheckScheduleInput:
            raise TypeError(
                "ResearchSourcePrimaryClaimRecheckScheduleInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryClaimRecheckScheduleInput:
            raise ValueError(
                "schedule input must be exactly "
                "ResearchSourcePrimaryClaimRecheckScheduleInput",
            )
        for field_name in ("claim_label", "authority_tier_label"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        object.__setattr__(
            self,
            "decision_deadline_at",
            _as_utc("decision_deadline_at", self.decision_deadline_at),
        )
        for field_name in (
            "authority_score",
            "contradiction_pressure_score",
            "extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "corroborating_source_count",
            "missing_critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_corroborating_source_count",
            "critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.corroborating_source_count > self.expected_corroborating_source_count:
            raise ValueError(
                "corroborating_source_count must not exceed "
                "expected_corroborating_source_count",
            )
        if self.missing_critical_field_count > self.critical_field_count:
            raise ValueError(
                "missing_critical_field_count must not exceed critical_field_count",
            )
        _require_hard_flags("schedule input", self)
        _reject_unsafe_public_payload("schedule input", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem:
            raise TypeError(
                "ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount:
            raise TypeError(
                "ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimRecheckScheduleRow:
    claim_label: str
    authority_tier_label: str
    last_verified_at: datetime
    verification_age_seconds: Decimal
    verification_age_score: Decimal
    authority_score: Decimal
    authority_gap_score: Decimal
    corroborating_source_count: Decimal
    expected_corroborating_source_count: Decimal
    corroboration_depth_score: Decimal
    corroboration_gap_score: Decimal
    contradiction_pressure_score: Decimal
    extraction_confidence_score: Decimal
    extraction_confidence_gap_score: Decimal
    missing_critical_field_count: Decimal
    critical_field_count: Decimal
    missing_critical_field_score: Decimal
    decision_deadline_at: datetime
    seconds_to_deadline: Decimal
    deadline_proximity_score: Decimal
    recheck_pressure_score: Decimal
    recheck_interval_seconds: Decimal
    next_recheck_due_at: datetime
    overdue_by_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimRecheckScheduleRow:
            raise TypeError(
                "ResearchSourcePrimaryClaimRecheckScheduleRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryClaimRecheckScheduleRow:
            raise ValueError(
                "row must be exactly ResearchSourcePrimaryClaimRecheckScheduleRow",
            )
        for field_name in ("claim_label", "authority_tier_label"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "last_verified_at",
            "decision_deadline_at",
            "next_recheck_due_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "verification_age_seconds",
            "corroborating_source_count",
            "missing_critical_field_count",
            "seconds_to_deadline",
            "overdue_by_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_corroborating_source_count",
            "critical_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "verification_age_score",
            "authority_score",
            "authority_gap_score",
            "corroboration_depth_score",
            "corroboration_gap_score",
            "contradiction_pressure_score",
            "extraction_confidence_score",
            "extraction_confidence_gap_score",
            "missing_critical_field_score",
            "deadline_proximity_score",
            "recheck_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recheck_interval_seconds",
            _require_positive_decimal(
                "recheck_interval_seconds",
                self.recheck_interval_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryClaimRecheckScheduleReport:
    generated_at: datetime
    config_version: str
    stale_after_seconds: Decimal
    deadline_window_seconds: Decimal
    base_recheck_interval_seconds: Decimal
    min_recheck_interval_seconds: Decimal
    max_recheck_interval_seconds: Decimal
    watch_recheck_pressure_score: Decimal
    block_recheck_pressure_score: Decimal
    status: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overdue_claim_count: Decimal
    average_recheck_pressure_score: Decimal
    max_recheck_pressure_score: Decimal
    rows: tuple[ResearchSourcePrimaryClaimRecheckScheduleRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount,
        ...,
    ]
    public_payload: tuple[
        ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryClaimRecheckScheduleReport:
            raise TypeError(
                "ResearchSourcePrimaryClaimRecheckScheduleReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourcePrimaryClaimRecheckScheduleReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourcePrimaryClaimRecheckScheduleReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_RECHECK_SCHEDULE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "stale_after_seconds",
            "deadline_window_seconds",
            "base_recheck_interval_seconds",
            "min_recheck_interval_seconds",
            "max_recheck_interval_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_recheck_pressure_score",
            "block_recheck_pressure_score",
            "average_recheck_pressure_score",
            "max_recheck_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_recheck_pressure_score >= self.block_recheck_pressure_score:
            raise ValueError(
                "watch_recheck_pressure_score must be below "
                "block_recheck_pressure_score",
            )
        _require_status("status", self.status)
        for field_name in (
            "claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "overdue_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSourcePrimaryClaimRecheckScheduleReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_primary_claim_recheck_schedule_report(
    schedule_inputs: Sequence[ResearchSourcePrimaryClaimRecheckScheduleInput],
    *,
    generated_at: datetime,
    config: ResearchSourcePrimaryClaimRecheckScheduleConfig | None = None,
    public_payload: Sequence[
        ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem
    ] = (),
) -> ResearchSourcePrimaryClaimRecheckScheduleReport:
    """Build a local report-only primary-claim recheck schedule snapshot."""

    if config is None:
        config = ResearchSourcePrimaryClaimRecheckScheduleConfig()
    if type(config) is not ResearchSourcePrimaryClaimRecheckScheduleConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryClaimRecheckScheduleConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(schedule_inputs)
    for item in normalized_inputs:
        if item.last_verified_at > generated_at_utc:
            raise ValueError("last_verified_at must not be after generated_at")
        if item.decision_deadline_at < generated_at_utc:
            raise ValueError("decision_deadline_at must not be before generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = tuple(
        _row_from_input(item, generated_at=generated_at_utc, config=config)
        for item in normalized_inputs
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "stale_after_seconds": config.stale_after_seconds,
        "deadline_window_seconds": config.deadline_window_seconds,
        "base_recheck_interval_seconds": config.base_recheck_interval_seconds,
        "min_recheck_interval_seconds": config.min_recheck_interval_seconds,
        "max_recheck_interval_seconds": config.max_recheck_interval_seconds,
        "watch_recheck_pressure_score": config.watch_recheck_pressure_score,
        "block_recheck_pressure_score": config.block_recheck_pressure_score,
        "status": _report_status(rows),
        "claim_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "overdue_claim_count": _decimal_count(
            sum(1 for row in rows if row.overdue_by_seconds > _ZERO),
        ),
        "average_recheck_pressure_score": _average(
            tuple(row.recheck_pressure_score for row in rows),
        ),
        "max_recheck_pressure_score": max(
            (row.recheck_pressure_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourcePrimaryClaimRecheckScheduleReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_primary_claim_recheck_schedule_report_payload(
    report: ResearchSourcePrimaryClaimRecheckScheduleReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourcePrimaryClaimRecheckScheduleReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryClaimRecheckScheduleReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def _row_from_input(
    item: ResearchSourcePrimaryClaimRecheckScheduleInput,
    *,
    generated_at: datetime,
    config: ResearchSourcePrimaryClaimRecheckScheduleConfig,
) -> ResearchSourcePrimaryClaimRecheckScheduleRow:
    verification_age = _age_seconds(generated_at, item.last_verified_at)
    verification_age_score = _freshness_decay_score(
        verification_age,
        config.stale_after_seconds,
    )
    authority_gap = _clamp_ratio(_ONE - item.authority_score)
    corroboration_depth = _ratio(
        item.corroborating_source_count,
        item.expected_corroborating_source_count,
    )
    corroboration_gap = _clamp_ratio(_ONE - corroboration_depth)
    extraction_confidence_gap = _clamp_ratio(_ONE - item.extraction_confidence_score)
    missing_critical_field_score = _ratio(
        item.missing_critical_field_count,
        item.critical_field_count,
    )
    seconds_to_deadline = _seconds_until(generated_at, item.decision_deadline_at)
    deadline_proximity = _deadline_proximity_score(
        seconds_to_deadline,
        config.deadline_window_seconds,
    )
    pressure = _recheck_pressure_score(
        verification_age_score=verification_age_score,
        authority_gap_score=authority_gap,
        corroboration_gap_score=corroboration_gap,
        contradiction_pressure_score=item.contradiction_pressure_score,
        extraction_confidence_gap_score=extraction_confidence_gap,
        missing_critical_field_score=missing_critical_field_score,
        deadline_proximity_score=deadline_proximity,
        config=config,
    )
    interval = _recheck_interval_seconds(
        pressure,
        base_recheck_interval_seconds=config.base_recheck_interval_seconds,
        min_recheck_interval_seconds=config.min_recheck_interval_seconds,
        max_recheck_interval_seconds=config.max_recheck_interval_seconds,
    )
    due_at = _datetime_plus_decimal_seconds(item.last_verified_at, interval)
    overdue_by = _overdue_by_seconds(generated_at, due_at)
    status = _row_status(
        recheck_pressure_score=pressure,
        overdue_by_seconds=overdue_by,
        watch_recheck_pressure_score=config.watch_recheck_pressure_score,
        block_recheck_pressure_score=config.block_recheck_pressure_score,
    )
    return ResearchSourcePrimaryClaimRecheckScheduleRow(
        claim_label=item.claim_label,
        authority_tier_label=item.authority_tier_label,
        last_verified_at=item.last_verified_at,
        verification_age_seconds=verification_age,
        verification_age_score=verification_age_score,
        authority_score=item.authority_score,
        authority_gap_score=authority_gap,
        corroborating_source_count=item.corroborating_source_count,
        expected_corroborating_source_count=item.expected_corroborating_source_count,
        corroboration_depth_score=corroboration_depth,
        corroboration_gap_score=corroboration_gap,
        contradiction_pressure_score=item.contradiction_pressure_score,
        extraction_confidence_score=item.extraction_confidence_score,
        extraction_confidence_gap_score=extraction_confidence_gap,
        missing_critical_field_count=item.missing_critical_field_count,
        critical_field_count=item.critical_field_count,
        missing_critical_field_score=missing_critical_field_score,
        decision_deadline_at=item.decision_deadline_at,
        seconds_to_deadline=seconds_to_deadline,
        deadline_proximity_score=deadline_proximity,
        recheck_pressure_score=pressure,
        recheck_interval_seconds=interval,
        next_recheck_due_at=due_at,
        overdue_by_seconds=overdue_by,
        status=status,
        reason_codes=_row_reason_codes(
            verification_age_score=verification_age_score,
            authority_gap_score=authority_gap,
            corroboration_gap_score=corroboration_gap,
            contradiction_pressure_score=item.contradiction_pressure_score,
            extraction_confidence_gap_score=extraction_confidence_gap,
            missing_critical_field_count=item.missing_critical_field_count,
            deadline_proximity_score=deadline_proximity,
            overdue_by_seconds=overdue_by,
            status=status,
        ),
    )


def _recheck_pressure_score(
    *,
    verification_age_score: Decimal,
    authority_gap_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_pressure_score: Decimal,
    extraction_confidence_gap_score: Decimal,
    missing_critical_field_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchSourcePrimaryClaimRecheckScheduleConfig,
) -> Decimal:
    return _clamp_ratio(
        (verification_age_score * config.verification_age_weight)
        + (authority_gap_score * config.authority_gap_weight)
        + (corroboration_gap_score * config.corroboration_gap_weight)
        + (contradiction_pressure_score * config.contradiction_pressure_weight)
        + (extraction_confidence_gap_score * config.extraction_confidence_gap_weight)
        + (missing_critical_field_score * config.missing_critical_field_weight)
        + (deadline_proximity_score * config.deadline_proximity_weight),
    )


def _recheck_interval_seconds(
    recheck_pressure_score: Decimal,
    *,
    base_recheck_interval_seconds: Decimal,
    min_recheck_interval_seconds: Decimal,
    max_recheck_interval_seconds: Decimal,
) -> Decimal:
    raw_interval = _quantize(base_recheck_interval_seconds * (_ONE - recheck_pressure_score))
    bounded = max(min_recheck_interval_seconds, min(max_recheck_interval_seconds, raw_interval))
    return _quantize(bounded)


def _freshness_decay_score(
    verification_age_seconds: Decimal,
    stale_after_seconds: Decimal,
) -> Decimal:
    if verification_age_seconds >= stale_after_seconds:
        return _ONE
    return _clamp_ratio(verification_age_seconds / stale_after_seconds)


def _deadline_proximity_score(
    seconds_to_deadline: Decimal,
    deadline_window_seconds: Decimal,
) -> Decimal:
    if seconds_to_deadline >= deadline_window_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (seconds_to_deadline / deadline_window_seconds))


def _row_status(
    *,
    recheck_pressure_score: Decimal,
    overdue_by_seconds: Decimal,
    watch_recheck_pressure_score: Decimal,
    block_recheck_pressure_score: Decimal,
) -> str:
    if recheck_pressure_score >= block_recheck_pressure_score:
        return "block"
    if recheck_pressure_score >= watch_recheck_pressure_score:
        return "watch"
    if overdue_by_seconds > _ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    verification_age_score: Decimal,
    authority_gap_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_pressure_score: Decimal,
    extraction_confidence_gap_score: Decimal,
    missing_critical_field_count: Decimal,
    deadline_proximity_score: Decimal,
    overdue_by_seconds: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"primary_claim_recheck_{status}"]
    if verification_age_score > Decimal("0.500000"):
        reason_codes.append("verification_age_pressure")
    if authority_gap_score > Decimal("0.500000"):
        reason_codes.append("low_source_authority_pressure")
    if corroboration_gap_score > Decimal("0.500000"):
        reason_codes.append("low_corroboration_depth_pressure")
    if contradiction_pressure_score > Decimal("0.500000"):
        reason_codes.append("contradiction_pressure")
    if extraction_confidence_gap_score > Decimal("0.500000"):
        reason_codes.append("low_extraction_confidence_pressure")
    if missing_critical_field_count > _ZERO:
        reason_codes.append("missing_critical_fields_pressure")
    if deadline_proximity_score > Decimal("0.500000"):
        reason_codes.append("deadline_proximity_pressure")
    if overdue_by_seconds > _ZERO:
        reason_codes.append("recheck_overdue")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchSourcePrimaryClaimRecheckScheduleRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryClaimRecheckScheduleRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_recheck_schedule",)
    return _normalize_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourcePrimaryClaimRecheckScheduleRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchSourcePrimaryClaimRecheckScheduleRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    schedule_inputs: Sequence[ResearchSourcePrimaryClaimRecheckScheduleInput],
) -> tuple[ResearchSourcePrimaryClaimRecheckScheduleInput, ...]:
    if isinstance(schedule_inputs, (str, bytes)) or not isinstance(schedule_inputs, Sequence):
        raise ValueError("schedule_inputs must be a sequence")
    normalized: list[ResearchSourcePrimaryClaimRecheckScheduleInput] = []
    seen: set[str] = set()
    for item in schedule_inputs:
        if type(item) is not ResearchSourcePrimaryClaimRecheckScheduleInput:
            raise ValueError(
                "schedule_inputs must contain "
                "ResearchSourcePrimaryClaimRecheckScheduleInput values",
            )
        _require_hard_flags("schedule input", item)
        if item.claim_label in seen:
            raise ValueError("schedule_inputs must not contain duplicate claim_label values")
        seen.add(item.claim_label)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.claim_label))


def _normalize_rows(
    rows: Sequence[ResearchSourcePrimaryClaimRecheckScheduleRow],
) -> tuple[ResearchSourcePrimaryClaimRecheckScheduleRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourcePrimaryClaimRecheckScheduleRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryClaimRecheckScheduleRow:
            raise ValueError(
                "rows must contain ResearchSourcePrimaryClaimRecheckScheduleRow values",
            )
        _require_hard_flags("row", row)
        if row.claim_label in seen:
            raise ValueError("rows must not contain duplicate claim_label values")
        seen.add(row.claim_label)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.claim_label))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem],
) -> tuple[ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem values",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload must not contain duplicate keys")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount],
) -> tuple[ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount] = []
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(count.reason_code)
        normalized.append(count)
    return tuple(
        count
        for reason_code in _REASON_CODE_SEQUENCE
        for count in normalized
        if count.reason_code == reason_code
    )


def _validate_row_consistency(row: ResearchSourcePrimaryClaimRecheckScheduleRow) -> None:
    if row.authority_gap_score != _clamp_ratio(_ONE - row.authority_score):
        raise ValueError("authority_gap_score must match authority_score")
    expected_corroboration_depth = _ratio(
        row.corroborating_source_count,
        row.expected_corroborating_source_count,
    )
    if row.corroboration_depth_score != expected_corroboration_depth:
        raise ValueError("corroboration_depth_score must match source counts")
    if row.corroboration_gap_score != _clamp_ratio(_ONE - row.corroboration_depth_score):
        raise ValueError("corroboration_gap_score must match corroboration_depth_score")
    if row.extraction_confidence_gap_score != _clamp_ratio(
        _ONE - row.extraction_confidence_score,
    ):
        raise ValueError(
            "extraction_confidence_gap_score must match extraction_confidence_score",
        )
    expected_missing_score = _ratio(
        row.missing_critical_field_count,
        row.critical_field_count,
    )
    if row.missing_critical_field_score != expected_missing_score:
        raise ValueError("missing_critical_field_score must match critical field counts")
    if row.next_recheck_due_at != _datetime_plus_decimal_seconds(
        row.last_verified_at,
        row.recheck_interval_seconds,
    ):
        raise ValueError("next_recheck_due_at must match recheck_interval_seconds")
    if row.status == "pass" and "primary_claim_recheck_pass" not in row.reason_codes:
        raise ValueError("pass rows must include primary_claim_recheck_pass")
    if row.status == "watch" and "primary_claim_recheck_watch" not in row.reason_codes:
        raise ValueError("watch rows must include primary_claim_recheck_watch")
    if row.status == "block" and "primary_claim_recheck_block" not in row.reason_codes:
        raise ValueError("block rows must include primary_claim_recheck_block")


def _validate_report_consistency(
    report: ResearchSourcePrimaryClaimRecheckScheduleReport,
) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_overdue_count = _decimal_count(
        sum(1 for row in report.rows if row.overdue_by_seconds > _ZERO),
    )
    if report.overdue_claim_count != expected_overdue_count:
        raise ValueError("overdue_claim_count must match rows")
    expected_average = _average(tuple(row.recheck_pressure_score for row in report.rows))
    if report.average_recheck_pressure_score != expected_average:
        raise ValueError("average_recheck_pressure_score must match rows")
    expected_max = max((row.recheck_pressure_score for row in report.rows), default=_ZERO)
    if report.max_recheck_pressure_score != expected_max:
        raise ValueError("max_recheck_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    for row in report.rows:
        expected_status = _row_status(
            recheck_pressure_score=row.recheck_pressure_score,
            overdue_by_seconds=row.overdue_by_seconds,
            watch_recheck_pressure_score=report.watch_recheck_pressure_score,
            block_recheck_pressure_score=report.block_recheck_pressure_score,
        )
        if row.status != expected_status:
            raise ValueError("row status must match report thresholds")
        expected_overdue = _overdue_by_seconds(report.generated_at, row.next_recheck_due_at)
        if row.overdue_by_seconds != expected_overdue:
            raise ValueError("row overdue_by_seconds must match generated_at")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    seen: set[str] = set()
    for reason_code in reason_codes:
        seen.add(_require_reason_code("reason_code", reason_code))
    if not seen:
        raise ValueError("reason_codes must be nonempty")
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in seen)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    return _clamp_ratio(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND),
    )


def _seconds_until(generated_at: datetime, deadline_at: datetime) -> Decimal:
    if deadline_at <= generated_at:
        return _ZERO
    return _age_seconds(deadline_at, generated_at)


def _datetime_plus_decimal_seconds(start: datetime, seconds: Decimal) -> datetime:
    microseconds = int(
        (seconds * _MICROSECONDS_PER_SECOND).to_integral_value(
            rounding=ROUND_HALF_UP,
        ),
    )
    return start + timedelta(microseconds=microseconds)


def _overdue_by_seconds(generated_at: datetime, due_at: datetime) -> Decimal:
    if due_at >= generated_at:
        return _ZERO
    return _age_seconds(generated_at, due_at)


def _report_values_without_digest(
    report: ResearchSourcePrimaryClaimRecheckScheduleReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                f"{current_path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose mapping payloads")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{current_path} key must be a string")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers and not isinstance(value, tuple):
            raise ValueError(f"{label} must use tuple containers")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(token in lowered for token in _UNSAFE_PUBLIC_TOKENS):
        raise ValueError(f"unsafe public payload key at {path}.{key}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "www." in lowered:
        raise ValueError(f"unsafe public payload value for {field_name}")
    if any(token in lowered for token in _UNSAFE_PUBLIC_TOKENS):
        raise ValueError(f"unsafe public payload value for {field_name}")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_CLAIM_RECHECK_SCHEDULE_CONFIG_VERSION",
    "ResearchSourcePrimaryClaimRecheckScheduleConfig",
    "ResearchSourcePrimaryClaimRecheckScheduleInput",
    "ResearchSourcePrimaryClaimRecheckSchedulePublicPayloadItem",
    "ResearchSourcePrimaryClaimRecheckScheduleReasonCodeCount",
    "ResearchSourcePrimaryClaimRecheckScheduleReport",
    "ResearchSourcePrimaryClaimRecheckScheduleRow",
    "build_research_source_primary_claim_recheck_schedule_report",
    "research_source_primary_claim_recheck_schedule_report_payload",
)
