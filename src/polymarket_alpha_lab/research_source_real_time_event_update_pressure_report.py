"""Pure report-only real-time event source update pressure report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_REAL_TIME_EVENT_UPDATE_PRESSURE_CONFIG_VERSION = (
    "research-source-real-time-event-update-pressure-report-v0"
)

REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES = ("pass", "watch", "block")
NO_INPUT_REASON_CODE = "real_time_event_update_pressure_no_inputs"
CHECK_PREFIXES = (
    "stale_update",
    "update_velocity",
    "authority_tier",
    "corroboration",
    "contradiction_pressure",
    "extraction_confidence",
    "pressure_score",
)
REASON_CODES = (NO_INPUT_REASON_CODE,) + tuple(
    f"{prefix}_{status}"
    for prefix in CHECK_PREFIXES
    for status in REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES
)

AUTHORITY_TIER_SCORES: Mapping[str, Decimal] = {
    "official_primary": Decimal("1.000000"),
    "independent_expert": Decimal("0.850000"),
    "verified_secondary": Decimal("0.750000"),
    "public_archive": Decimal("0.650000"),
    "unverified_social": Decimal("0.000000"),
}
AUTHORITY_TIER_STATUSES: Mapping[str, str] = {
    "official_primary": "pass",
    "independent_expert": "pass",
    "verified_secondary": "watch",
    "public_archive": "watch",
    "unverified_social": "block",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")

UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        "://",
        "www.",
        "candidate",
        "condition_id",
        "credential",
        "database",
        "dsn",
        "live",
        "market_id",
        "market_slug",
        "private_key",
        "question",
        "raw",
        "recommendation",
        "secret",
        "sizing",
        "source_id",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "order",
    ),
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_pressure_score",
        "average_pressure_score",
        "max_update_velocity_per_hour",
        "max_contradiction_pressure",
        "min_extraction_confidence_score",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    ),
)
_REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_pressure_score",
    "average_pressure_score",
    "max_update_velocity_per_hour",
    "max_contradiction_pressure",
    "min_extraction_confidence_score",
)
_REPORT_RATIO_PAYLOAD_FIELDS = frozenset(
    (
        "max_pressure_score",
        "average_pressure_score",
        "max_contradiction_pressure",
        "min_extraction_confidence_score",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "pressure_group",
        "status",
        "update_count",
        "latest_observed_at",
        "latest_update_age_seconds",
        "update_velocity_per_hour",
        "authority_tier_score",
        "corroboration_score",
        "contradiction_pressure",
        "extraction_confidence_score",
        "pressure_score",
        "stale_update_status",
        "update_velocity_status",
        "authority_tier_status",
        "corroboration_status",
        "contradiction_status",
        "extraction_confidence_status",
        "pressure_score_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_DECIMAL_PAYLOAD_FIELDS = (
    "update_count",
    "latest_update_age_seconds",
    "update_velocity_per_hour",
    "authority_tier_score",
    "corroboration_score",
    "contradiction_pressure",
    "extraction_confidence_score",
    "pressure_score",
)
_ROW_RATIO_PAYLOAD_FIELDS = frozenset(
    (
        "authority_tier_score",
        "corroboration_score",
        "contradiction_pressure",
        "extraction_confidence_score",
        "pressure_score",
    ),
)
_ROW_STATUS_PAYLOAD_FIELDS = (
    "status",
    "stale_update_status",
    "update_velocity_status",
    "authority_tier_status",
    "corroboration_status",
    "contradiction_status",
    "extraction_confidence_status",
    "pressure_score_status",
)
_ROW_STATUS_REASON_PREFIXES = {
    "stale_update_status": "stale_update",
    "update_velocity_status": "update_velocity",
    "authority_tier_status": "authority_tier",
    "corroboration_status": "corroboration",
    "contradiction_status": "contradiction_pressure",
    "extraction_confidence_status": "extraction_confidence",
    "pressure_score_status": "pressure_score",
}
_REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_REAL_TIME_EVENT_UPDATE_PRESSURE_CONFIG_VERSION",
    "REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES",
    "REASON_CODES",
    "ResearchSourceRealTimeEventUpdatePressureConfig",
    "ResearchSourceRealTimeEventUpdatePressureObservation",
    "ResearchSourceRealTimeEventUpdatePressureReasonCodeCount",
    "ResearchSourceRealTimeEventUpdatePressureReport",
    "ResearchSourceRealTimeEventUpdatePressureRow",
    "build_research_source_real_time_event_update_pressure_report",
    "research_source_real_time_event_update_pressure_report_digest",
    "research_source_real_time_event_update_pressure_report_payload",
    "validate_research_source_real_time_event_update_pressure_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceRealTimeEventUpdatePressureConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_REAL_TIME_EVENT_UPDATE_PRESSURE_CONFIG_VERSION
    )
    max_pass_update_age_seconds: Decimal = Decimal("900.000000")
    max_watch_update_age_seconds: Decimal = Decimal("3600.000000")
    watch_update_velocity_per_hour: Decimal = Decimal("4.000000")
    block_update_velocity_per_hour: Decimal = Decimal("8.000000")
    min_pass_corroboration_score: Decimal = Decimal("0.750000")
    min_watch_corroboration_score: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.400000")
    min_pass_extraction_confidence_score: Decimal = Decimal("0.800000")
    min_watch_extraction_confidence_score: Decimal = Decimal("0.600000")
    max_pass_pressure_score: Decimal = Decimal("0.350000")
    max_watch_pressure_score: Decimal = Decimal("0.700000")
    update_velocity_weight: Decimal = Decimal("0.250000")
    authority_tier_weight: Decimal = Decimal("0.150000")
    corroboration_gap_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    extraction_confidence_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRealTimeEventUpdatePressureConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeEventUpdatePressureConfig:
            raise ValueError(
                "config must be a ResearchSourceRealTimeEventUpdatePressureConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_pass_update_age_seconds",
            "max_watch_update_age_seconds",
            "watch_update_velocity_per_hour",
            "block_update_velocity_per_hour",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_corroboration_score",
            "min_watch_corroboration_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "min_pass_extraction_confidence_score",
            "min_watch_extraction_confidence_score",
            "max_pass_pressure_score",
            "max_watch_pressure_score",
            "update_velocity_weight",
            "authority_tier_weight",
            "corroboration_gap_weight",
            "contradiction_pressure_weight",
            "extraction_confidence_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.max_pass_update_age_seconds > self.max_watch_update_age_seconds:
            raise ValueError("pass update age threshold cannot exceed watch threshold")
        if self.block_update_velocity_per_hour <= self.watch_update_velocity_per_hour:
            raise ValueError(
                "block_update_velocity_per_hour must exceed "
                "watch_update_velocity_per_hour",
            )
        if self.min_pass_corroboration_score < self.min_watch_corroboration_score:
            raise ValueError(
                "pass corroboration threshold cannot be below watch corroboration",
            )
        if self.max_pass_contradiction_pressure > self.max_watch_contradiction_pressure:
            raise ValueError(
                "pass contradiction pressure cannot exceed watch threshold",
            )
        if (
            self.min_pass_extraction_confidence_score
            < self.min_watch_extraction_confidence_score
        ):
            raise ValueError(
                "pass extraction confidence cannot be below watch threshold",
            )
        if self.max_pass_pressure_score > self.max_watch_pressure_score:
            raise ValueError("pass pressure score cannot exceed watch threshold")
        _require_weight_sum(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceRealTimeEventUpdatePressureObservation:
    pressure_group: str
    authority_tier: str
    observed_at: datetime
    updates_in_window: Decimal
    update_window_seconds: Decimal
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    contradiction_count: Decimal
    checked_claim_count: Decimal
    extraction_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRealTimeEventUpdatePressureObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeEventUpdatePressureObservation:
            raise ValueError(
                "observation must be a "
                "ResearchSourceRealTimeEventUpdatePressureObservation",
            )
        _require_public_label("pressure_group", self.pressure_group)
        _require_authority_tier("authority_tier", self.authority_tier)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "updates_in_window",
            "corroborating_source_count",
            "contradiction_count",
            "checked_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "update_window_seconds",
            _normalize_positive_decimal("update_window_seconds", self.update_window_seconds),
        )
        object.__setattr__(
            self,
            "required_corroborating_source_count",
            _normalize_positive_decimal(
                "required_corroborating_source_count",
                self.required_corroborating_source_count,
            ),
        )
        object.__setattr__(
            self,
            "extraction_confidence_score",
            _normalize_ratio(
                "extraction_confidence_score",
                self.extraction_confidence_score,
            ),
        )
        if self.corroborating_source_count > self.required_corroborating_source_count:
            raise ValueError(
                "corroborating_source_count cannot exceed "
                "required_corroborating_source_count",
            )
        if self.checked_claim_count == ZERO and self.contradiction_count != ZERO:
            raise ValueError(
                "contradiction_count requires a positive checked_claim_count",
            )
        if self.contradiction_count > self.checked_claim_count:
            raise ValueError("contradiction_count cannot exceed checked_claim_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceRealTimeEventUpdatePressureReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRealTimeEventUpdatePressureReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeEventUpdatePressureReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "ResearchSourceRealTimeEventUpdatePressureReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceRealTimeEventUpdatePressureRow:
    pressure_group: str
    status: str
    update_count: Decimal
    latest_observed_at: datetime
    latest_update_age_seconds: Decimal
    update_velocity_per_hour: Decimal
    authority_tier_score: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence_score: Decimal
    pressure_score: Decimal
    stale_update_status: str
    update_velocity_status: str
    authority_tier_status: str
    corroboration_status: str
    contradiction_status: str
    extraction_confidence_status: str
    pressure_score_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRealTimeEventUpdatePressureRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeEventUpdatePressureRow:
            raise ValueError(
                "row must be a ResearchSourceRealTimeEventUpdatePressureRow",
            )
        _require_public_label("pressure_group", self.pressure_group)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "update_count",
            _normalize_positive_decimal("update_count", self.update_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "latest_update_age_seconds",
            "update_velocity_per_hour",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_tier_score",
            "corroboration_score",
            "contradiction_pressure",
            "extraction_confidence_score",
            "pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_update_status",
            "update_velocity_status",
            "authority_tier_status",
            "corroboration_status",
            "contradiction_status",
            "extraction_confidence_status",
            "pressure_score_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        if self.status != _overall_status(_reason_code_status(code) for code in self.reason_codes):
            raise ValueError("row status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceRealTimeEventUpdatePressureReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_pressure_score: Decimal
    average_pressure_score: Decimal
    max_update_velocity_per_hour: Decimal
    max_contradiction_pressure: Decimal
    min_extraction_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceRealTimeEventUpdatePressureReasonCodeCount, ...]
    rows: tuple[ResearchSourceRealTimeEventUpdatePressureRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceRealTimeEventUpdatePressureReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRealTimeEventUpdatePressureReport:
            raise ValueError(
                "report must be a ResearchSourceRealTimeEventUpdatePressureReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pressure_score",
            "average_pressure_score",
            "max_contradiction_pressure",
            "min_extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_update_velocity_per_hour",
            _normalize_nonnegative_decimal(
                "max_update_velocity_per_hour",
                self.max_update_velocity_per_hour,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_source_real_time_event_update_pressure_report_payload(self)

    @property
    def payload(self) -> dict[str, Any]:
        return self.public_payload


def build_research_source_real_time_event_update_pressure_report(
    observations: Iterable[object],
    *,
    config: ResearchSourceRealTimeEventUpdatePressureConfig,
    generated_at: datetime,
) -> ResearchSourceRealTimeEventUpdatePressureReport:
    """Build a deterministic report-only source update pressure view."""

    if type(config) is not ResearchSourceRealTimeEventUpdatePressureConfig:
        raise ValueError(
            "config must be a ResearchSourceRealTimeEventUpdatePressureConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_future_observations(normalized, generated_at_utc)
    rows = tuple(
        _row_from_observations(
            pressure_group,
            group_observations,
            config=config,
            generated_at=generated_at_utc,
        )
        for pressure_group, group_observations in _grouped_observations(normalized)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchSourceRealTimeEventUpdatePressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        row_count=_count(len(rows)),
        pass_count=_row_status_count(rows, "pass"),
        watch_count=_row_status_count(rows, "watch"),
        block_count=_row_status_count(rows, "block"),
        max_pressure_score=max((row.pressure_score for row in rows), default=ZERO),
        average_pressure_score=_average_decimal(row.pressure_score for row in rows),
        max_update_velocity_per_hour=max(
            (row.update_velocity_per_hour for row in rows),
            default=ZERO,
        ),
        max_contradiction_pressure=max(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ),
        min_extraction_confidence_score=min(
            (row.extraction_confidence_score for row in rows),
            default=ZERO,
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_source_real_time_event_update_pressure_report_payload(
    report: ResearchSourceRealTimeEventUpdatePressureReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceRealTimeEventUpdatePressureReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
    elif type(report) is dict:
        _require_payload_hard_flags(report)
        _reject_unsafe_public_payload("payload", report, allow_mapping=True)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchSourceRealTimeEventUpdatePressureReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
    return payload


def research_source_real_time_event_update_pressure_report_digest(
    report: ResearchSourceRealTimeEventUpdatePressureReport,
) -> str:
    if type(report) is not ResearchSourceRealTimeEventUpdatePressureReport:
        raise ValueError(
            "report must be a ResearchSourceRealTimeEventUpdatePressureReport",
        )
    _require_hard_flags("report", report)
    digest = _report_derived_validation_digest(report)
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_source_real_time_event_update_pressure_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        if set(payload) != _REPORT_PAYLOAD_KEYS:
            return False
        _require_payload_hard_flags(payload)
        _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str:
            return False
        _require_sha256_digest("derived_validation_digest", digest)
        unsigned_payload = dict(payload)
        unsigned_payload.pop("derived_validation_digest", None)
        if digest != _payload_digest(unsigned_payload):
            return False
        _payload_datetime_string("generated_at", payload["generated_at"])
        _require_public_string("config_version", payload["config_version"])
        if payload.get("status") not in REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES:
            return False
        report_decimals = {
            field_name: _payload_decimal_string(
                field_name,
                payload[field_name],
                ratio=field_name in _REPORT_RATIO_PAYLOAD_FIELDS,
            )
            for field_name in _REPORT_DECIMAL_PAYLOAD_FIELDS
        }
        if type(payload.get("reason_codes")) is not list:
            return False
        reason_codes = _normalize_report_reason_codes(payload["reason_codes"])
        if type(payload.get("rows")) is not list:
            return False
        rows = payload["rows"]
        row_statuses: list[str] = []
        row_reason_codes: list[tuple[str, ...]] = []
        row_decimals: list[dict[str, Decimal]] = []
        pressure_groups: list[str] = []
        for row in rows:
            if type(row) is not dict:
                return False
            if set(row) != _ROW_PAYLOAD_KEYS:
                return False
            _require_payload_hard_flags(row)
            _require_public_label("pressure_group", row["pressure_group"])
            pressure_groups.append(row["pressure_group"])
            _payload_datetime_string("latest_observed_at", row["latest_observed_at"])
            for field_name in _ROW_STATUS_PAYLOAD_FIELDS:
                if row.get(field_name) not in REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES:
                    return False
            if type(row.get("reason_codes")) is not list:
                return False
            normalized_row_reason_codes = _normalize_row_reason_codes(
                row["reason_codes"],
            )
            row_reason_codes.append(normalized_row_reason_codes)
            expected_status_by_prefix = {
                code.rsplit("_", 1)[0]: _reason_code_status(code)
                for code in normalized_row_reason_codes
            }
            for field_name, reason_prefix in _ROW_STATUS_REASON_PREFIXES.items():
                if row[field_name] != expected_status_by_prefix[reason_prefix]:
                    return False
            if row["status"] != _overall_status(
                _reason_code_status(code) for code in normalized_row_reason_codes
            ):
                return False
            row_statuses.append(row["status"])
            row_decimals.append(
                {
                    field_name: _payload_decimal_string(
                        field_name,
                        row[field_name],
                        ratio=field_name in _ROW_RATIO_PAYLOAD_FIELDS,
                    )
                    for field_name in _ROW_DECIMAL_PAYLOAD_FIELDS
                },
            )
        if pressure_groups != sorted(pressure_groups):
            return False
        if len(set(pressure_groups)) != len(pressure_groups):
            return False
        if type(payload.get("reason_code_counts")) is not list:
            return False
        reason_code_count_pairs: list[tuple[str, Decimal]] = []
        for reason_code_count in payload["reason_code_counts"]:
            if type(reason_code_count) is not dict:
                return False
            if set(reason_code_count) != _REASON_CODE_COUNT_PAYLOAD_KEYS:
                return False
            _require_payload_hard_flags(reason_code_count)
            _require_reason_code("reason_code", reason_code_count["reason_code"])
            reason_code_count_pairs.append(
                (
                    reason_code_count["reason_code"],
                    _payload_decimal_string(
                        "count",
                        reason_code_count["count"],
                        positive=True,
                    ),
                ),
            )
        if len({reason_code for reason_code, _ in reason_code_count_pairs}) != len(
            reason_code_count_pairs,
        ):
            return False
        if tuple(reason_code for reason_code, _ in reason_code_count_pairs) != tuple(
            sorted(
                (reason_code for reason_code, _ in reason_code_count_pairs),
                key=REASON_CODES.index,
            ),
        ):
            return False

        expected_status = "pass" if not rows else _overall_status(row_statuses)
        if payload["status"] != expected_status:
            return False
        if report_decimals["row_count"] != _count(len(rows)):
            return False
        for target, field_name in (
            ("pass", "pass_count"),
            ("watch", "watch_count"),
            ("block", "block_count"),
        ):
            if report_decimals[field_name] != _count(
                sum(1 for status in row_statuses if status == target),
            ):
                return False
        flat_reason_codes = tuple(code for codes in row_reason_codes for code in codes)
        expected_reason_codes = (
            (NO_INPUT_REASON_CODE,)
            if not rows
            else tuple(code for code in REASON_CODES if code in flat_reason_codes)
        )
        if reason_codes != expected_reason_codes:
            return False
        expected_reason_code_count_pairs: tuple[tuple[str, Decimal], ...]
        if not rows:
            expected_reason_code_count_pairs = ()
        else:
            reason_code_counter = Counter(flat_reason_codes)
            expected_reason_code_count_pairs = tuple(
                (reason_code, _count(reason_code_counter[reason_code]))
                for reason_code in expected_reason_codes
            )
        if tuple(reason_code_count_pairs) != expected_reason_code_count_pairs:
            return False

        if report_decimals["max_pressure_score"] != max(
            (row["pressure_score"] for row in row_decimals),
            default=ZERO,
        ):
            return False
        if report_decimals["average_pressure_score"] != _average_decimal(
            row["pressure_score"] for row in row_decimals
        ):
            return False
        if report_decimals["max_update_velocity_per_hour"] != max(
            (row["update_velocity_per_hour"] for row in row_decimals),
            default=ZERO,
        ):
            return False
        if report_decimals["max_contradiction_pressure"] != max(
            (row["contradiction_pressure"] for row in row_decimals),
            default=ZERO,
        ):
            return False
        if report_decimals["min_extraction_confidence_score"] != min(
            (row["extraction_confidence_score"] for row in row_decimals),
            default=ZERO,
        ):
            return False
        return True
    except (InvalidOperation, KeyError, TypeError, ValueError):
        return False


def _payload_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    parsed = datetime.fromisoformat(value)
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _payload_decimal_string(
    field_name: str,
    value: object,
    *,
    ratio: bool = False,
    positive: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    decimal_value = Decimal(value)
    if ratio:
        normalized = _normalize_ratio(field_name, decimal_value)
    elif positive:
        normalized = _normalize_positive_decimal(field_name, decimal_value)
    else:
        normalized = _normalize_nonnegative_decimal(field_name, decimal_value)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _row_from_observations(
    pressure_group: str,
    observations: tuple[ResearchSourceRealTimeEventUpdatePressureObservation, ...],
    *,
    config: ResearchSourceRealTimeEventUpdatePressureConfig,
    generated_at: datetime,
) -> ResearchSourceRealTimeEventUpdatePressureRow:
    sorted_observations = tuple(sorted(observations, key=lambda item: item.observed_at))
    update_count = _count(len(sorted_observations))
    latest_observed_at = sorted_observations[-1].observed_at
    latest_update_age_seconds = _datetime_delta_seconds(generated_at, latest_observed_at)
    update_velocity_per_hour = _update_velocity_per_hour(sorted_observations)
    authority_tier_score = _average_decimal(
        AUTHORITY_TIER_SCORES[item.authority_tier] for item in sorted_observations
    )
    authority_tier_status = _overall_status(
        AUTHORITY_TIER_STATUSES[item.authority_tier] for item in sorted_observations
    )
    corroboration_score = _ratio(
        _sum_decimal(item.corroborating_source_count for item in sorted_observations),
        _sum_decimal(
            item.required_corroborating_source_count for item in sorted_observations
        ),
    )
    contradiction_pressure = _ratio(
        _sum_decimal(item.contradiction_count for item in sorted_observations),
        _sum_decimal(item.checked_claim_count for item in sorted_observations),
    )
    extraction_confidence_score = _average_decimal(
        item.extraction_confidence_score for item in sorted_observations
    )
    pressure_score = _pressure_score(
        update_velocity_per_hour=update_velocity_per_hour,
        authority_tier_score=authority_tier_score,
        corroboration_score=corroboration_score,
        contradiction_pressure=contradiction_pressure,
        extraction_confidence_score=extraction_confidence_score,
        config=config,
    )
    stale_update_status = _maximum_status(
        latest_update_age_seconds,
        pass_threshold=config.max_pass_update_age_seconds,
        watch_threshold=config.max_watch_update_age_seconds,
    )
    update_velocity_status = _velocity_status(update_velocity_per_hour, config)
    corroboration_status = _minimum_status(
        corroboration_score,
        pass_threshold=config.min_pass_corroboration_score,
        watch_threshold=config.min_watch_corroboration_score,
    )
    contradiction_status = _maximum_status(
        contradiction_pressure,
        pass_threshold=config.max_pass_contradiction_pressure,
        watch_threshold=config.max_watch_contradiction_pressure,
    )
    extraction_confidence_status = _minimum_status(
        extraction_confidence_score,
        pass_threshold=config.min_pass_extraction_confidence_score,
        watch_threshold=config.min_watch_extraction_confidence_score,
    )
    pressure_score_status = _maximum_status(
        pressure_score,
        pass_threshold=config.max_pass_pressure_score,
        watch_threshold=config.max_watch_pressure_score,
    )
    reason_codes = (
        f"stale_update_{stale_update_status}",
        f"update_velocity_{update_velocity_status}",
        f"authority_tier_{authority_tier_status}",
        f"corroboration_{corroboration_status}",
        f"contradiction_pressure_{contradiction_status}",
        f"extraction_confidence_{extraction_confidence_status}",
        f"pressure_score_{pressure_score_status}",
    )
    return ResearchSourceRealTimeEventUpdatePressureRow(
        pressure_group=pressure_group,
        status=_overall_status(_reason_code_status(code) for code in reason_codes),
        update_count=update_count,
        latest_observed_at=latest_observed_at,
        latest_update_age_seconds=latest_update_age_seconds,
        update_velocity_per_hour=update_velocity_per_hour,
        authority_tier_score=authority_tier_score,
        corroboration_score=corroboration_score,
        contradiction_pressure=contradiction_pressure,
        extraction_confidence_score=extraction_confidence_score,
        pressure_score=pressure_score,
        stale_update_status=stale_update_status,
        update_velocity_status=update_velocity_status,
        authority_tier_status=authority_tier_status,
        corroboration_status=corroboration_status,
        contradiction_status=contradiction_status,
        extraction_confidence_status=extraction_confidence_status,
        pressure_score_status=pressure_score_status,
        reason_codes=reason_codes,
    )


def _update_velocity_per_hour(
    observations: tuple[ResearchSourceRealTimeEventUpdatePressureObservation, ...],
) -> Decimal:
    updates = _sum_decimal(item.updates_in_window for item in observations)
    window_seconds = _sum_decimal(item.update_window_seconds for item in observations)
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_nonnegative_decimal(
            "update_velocity_per_hour",
            (updates / window_seconds) * SECONDS_PER_HOUR,
        )


def _pressure_score(
    *,
    update_velocity_per_hour: Decimal,
    authority_tier_score: Decimal,
    corroboration_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence_score: Decimal,
    config: ResearchSourceRealTimeEventUpdatePressureConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        velocity_pressure = _clamped_ratio(
            update_velocity_per_hour / config.block_update_velocity_per_hour,
        )
        authority_gap = _clamped_ratio(ONE - authority_tier_score)
        corroboration_gap = _clamped_ratio(ONE - corroboration_score)
        extraction_confidence_gap = _clamped_ratio(ONE - extraction_confidence_score)
        return _clamped_ratio(
            (velocity_pressure * config.update_velocity_weight)
            + (authority_gap * config.authority_tier_weight)
            + (corroboration_gap * config.corroboration_gap_weight)
            + (contradiction_pressure * config.contradiction_pressure_weight)
            + (
                extraction_confidence_gap
                * config.extraction_confidence_gap_weight
            ),
        )


def _velocity_status(
    update_velocity_per_hour: Decimal,
    config: ResearchSourceRealTimeEventUpdatePressureConfig,
) -> str:
    if update_velocity_per_hour >= config.block_update_velocity_per_hour:
        return "block"
    if update_velocity_per_hour >= config.watch_update_velocity_per_hour:
        return "watch"
    return "pass"


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchSourceRealTimeEventUpdatePressureObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized: list[ResearchSourceRealTimeEventUpdatePressureObservation] = []
    for value in values:
        if type(value) is not ResearchSourceRealTimeEventUpdatePressureObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceRealTimeEventUpdatePressureObservation values",
            )
        _require_hard_flags("observation", value)
        normalized.append(value)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.pressure_group,
                item.observed_at,
                item.authority_tier,
                item.updates_in_window,
                item.update_window_seconds,
                item.corroborating_source_count,
                item.required_corroborating_source_count,
                item.contradiction_count,
                item.checked_claim_count,
                item.extraction_confidence_score,
            ),
        ),
    )


def _grouped_observations(
    observations: tuple[ResearchSourceRealTimeEventUpdatePressureObservation, ...],
) -> tuple[tuple[str, tuple[ResearchSourceRealTimeEventUpdatePressureObservation, ...]], ...]:
    groups: dict[str, list[ResearchSourceRealTimeEventUpdatePressureObservation]] = {}
    for observation in observations:
        groups.setdefault(observation.pressure_group, []).append(observation)
    return tuple((key, tuple(values)) for key, values in sorted(groups.items()))


def _reject_future_observations(
    observations: tuple[ResearchSourceRealTimeEventUpdatePressureObservation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _report_status(
    rows: tuple[ResearchSourceRealTimeEventUpdatePressureRow, ...],
) -> str:
    if not rows:
        return "pass"
    return _overall_status(row.status for row in rows)


def _row_status_count(
    rows: tuple[ResearchSourceRealTimeEventUpdatePressureRow, ...],
    target: str,
) -> Decimal:
    _require_status("target", target)
    return _count(sum(1 for row in rows if row.status == target))


def _report_reason_codes(
    rows: tuple[ResearchSourceRealTimeEventUpdatePressureRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUT_REASON_CODE,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchSourceRealTimeEventUpdatePressureRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceRealTimeEventUpdatePressureReasonCodeCount, ...]:
    if reason_codes == (NO_INPUT_REASON_CODE,):
        return ()
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchSourceRealTimeEventUpdatePressureReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _minimum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return "pass"
    if value >= watch_threshold:
        return "watch"
    return "block"


def _maximum_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return "pass"
    if value <= watch_threshold:
        return "watch"
    return "block"


def _overall_status(statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    for status in values:
        _require_status("status", status)
    if "block" in values:
        return "block"
    if "watch" in values:
        return "watch"
    return "pass"


def _validate_report(report: ResearchSourceRealTimeEventUpdatePressureReport) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")
    if report.row_count == ZERO:
        if report.status != "pass":
            raise ValueError("empty report status must be pass")
        if report.reason_codes != (NO_INPUT_REASON_CODE,):
            raise ValueError("empty report reason_codes must use no-input reason")
        if report.reason_code_counts != ():
            raise ValueError("empty report reason_code_counts must be empty")
    else:
        if report.row_count != _count(len(report.rows)):
            raise ValueError("row_count must equal rows length")
        if report.pass_count + report.watch_count + report.block_count != report.row_count:
            raise ValueError("status counts must sum to row_count")
        if report.status != _report_status(report.rows):
            raise ValueError("status must match rows")
        if report.reason_codes != _report_reason_codes(report.rows):
            raise ValueError("reason_codes must match rows")
        if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
            raise ValueError("reason_code_counts must match rows")


def _reason_code_status(reason_code: str) -> str:
    if reason_code == NO_INPUT_REASON_CODE:
        return "pass"
    status = reason_code.rsplit("_", 1)[-1]
    _require_status("reason_code status", status)
    return status


def _report_payload(
    report: ResearchSourceRealTimeEventUpdatePressureReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "row_count": _payload_value(report.row_count),
        "pass_count": _payload_value(report.pass_count),
        "watch_count": _payload_value(report.watch_count),
        "block_count": _payload_value(report.block_count),
        "max_pressure_score": _payload_value(report.max_pressure_score),
        "average_pressure_score": _payload_value(report.average_pressure_score),
        "max_update_velocity_per_hour": _payload_value(
            report.max_update_velocity_per_hour,
        ),
        "max_contradiction_pressure": _payload_value(
            report.max_contradiction_pressure,
        ),
        "min_extraction_confidence_score": _payload_value(
            report.min_extraction_confidence_score,
        ),
        "reason_codes": _payload_value(report.reason_codes),
        "reason_code_counts": _payload_value(report.reason_code_counts),
        "rows": _payload_value(report.rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchSourceRealTimeEventUpdatePressureRow) -> dict[str, Any]:
    return {
        "pressure_group": row.pressure_group,
        "status": row.status,
        "update_count": _payload_value(row.update_count),
        "latest_observed_at": _payload_value(row.latest_observed_at),
        "latest_update_age_seconds": _payload_value(row.latest_update_age_seconds),
        "update_velocity_per_hour": _payload_value(row.update_velocity_per_hour),
        "authority_tier_score": _payload_value(row.authority_tier_score),
        "corroboration_score": _payload_value(row.corroboration_score),
        "contradiction_pressure": _payload_value(row.contradiction_pressure),
        "extraction_confidence_score": _payload_value(
            row.extraction_confidence_score,
        ),
        "pressure_score": _payload_value(row.pressure_score),
        "stale_update_status": row.stale_update_status,
        "update_velocity_status": row.update_velocity_status,
        "authority_tier_status": row.authority_tier_status,
        "corroboration_status": row.corroboration_status,
        "contradiction_status": row.contradiction_status,
        "extraction_confidence_status": row.extraction_confidence_status,
        "pressure_score_status": row.pressure_score_status,
        "reason_codes": _payload_value(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchSourceRealTimeEventUpdatePressureReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _payload_value(row.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) in (tuple, list):
        return [_payload_value(item) for item in value]
    if type(value) is ResearchSourceRealTimeEventUpdatePressureReasonCodeCount:
        return _reason_code_count_payload(value)
    if type(value) is ResearchSourceRealTimeEventUpdatePressureRow:
        return _row_payload(value)
    if type(value) is ResearchSourceRealTimeEventUpdatePressureReport:
        return _report_payload(value, include_digest=True)
    if isinstance(value, Mapping):
        return {key: _payload_value(item) for key, item in sorted(value.items())}
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _report_derived_validation_digest(
    report: ResearchSourceRealTimeEventUpdatePressureReport,
) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload("payload", payload, allow_mapping=True)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(normalized, ZERO) / Decimal(len(normalized)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return _quantize_decimal(sum(values, ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(numerator / denominator)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_decimal(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECOND_DIVISOR)
    )
    return _normalize_nonnegative_decimal("datetime_delta_seconds", seconds)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("decimal values must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    _reject_unsafe_public_string(field_name, value)


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    assert type(value) is str
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a sanitized public label")
    if not value[0].isalpha():
        raise ValueError(f"{field_name} must start with a letter")


def _require_authority_tier(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)
    if value not in AUTHORITY_TIER_SCORES:
        raise ValueError(f"{field_name} contains unsupported authority_tier")


def _require_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain a supported reason code")


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    values = _normalize_reason_code_tuple(value)
    if values == (NO_INPUT_REASON_CODE,):
        raise ValueError("row reason_codes must not use no-input reason")
    expected_prefixes = tuple(code.rsplit("_", 1)[0] for code in values)
    if expected_prefixes != CHECK_PREFIXES:
        raise ValueError("row reason_codes must cover every pressure check once")
    return values


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    values = _normalize_reason_code_tuple(value)
    if values == (NO_INPUT_REASON_CODE,):
        return values
    if NO_INPUT_REASON_CODE in values:
        raise ValueError("no-input reason cannot be combined")
    return values


def _normalize_reason_code_tuple(value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_codes must be a tuple or list")
    values = tuple(value)
    if not values:
        raise ValueError("reason_codes must be non-empty")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in values:
        _require_reason_code("reason_code", reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODES if reason_code in values)
    if values != expected:
        raise ValueError("reason_codes must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchSourceRealTimeEventUpdatePressureReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchSourceRealTimeEventUpdatePressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceRealTimeEventUpdatePressureReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", value)
    expected = tuple(sorted(values, key=lambda row: REASON_CODES.index(row.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceRealTimeEventUpdatePressureRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchSourceRealTimeEventUpdatePressureRow:
            raise ValueError(
                "rows must contain ResearchSourceRealTimeEventUpdatePressureRow values",
            )
        _require_hard_flags("row", value)
    expected = tuple(sorted(values, key=lambda row: row.pressure_group))
    if values != expected:
        raise ValueError("rows must be deterministically sorted")
    return values


def _require_weight_sum(
    config: ResearchSourceRealTimeEventUpdatePressureConfig,
) -> None:
    total = _sum_decimal(
        (
            config.update_velocity_weight,
            config.authority_tier_weight,
            config.corroboration_gap_weight,
            config.contradiction_pressure_weight,
            config.extraction_confidence_gap_weight,
        ),
    )
    if total != ONE:
        raise ValueError("pressure score weights must sum to 1.000000")


def _reject_unsafe_public_payload(
    context: str,
    value: object,
    *,
    allow_mapping: bool = False,
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
            _reject_unsafe_public_string(f"{context} key", field_name)
            _reject_unsafe_public_payload(
                f"{context}.{field_name}",
                getattr(value, field_name),
            )
        return
    if isinstance(value, Mapping):
        if not allow_mapping:
            raise ValueError(f"{context} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} payload keys must be strings")
            _reject_unsafe_public_string(f"{context} key", key)
            _reject_unsafe_public_payload(
                f"{context}.{key}",
                item,
                allow_mapping=True,
            )
        return
    if type(value) in (tuple, list):
        for item in value:
            _reject_unsafe_public_payload(context, item, allow_mapping=allow_mapping)
        return
    if type(value) is str:
        _reject_unsafe_public_string(context, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{context} Decimal value must be finite")
        return
    if type(value) is datetime:
        _as_utc("datetime payload value", value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{context} numeric value must use Decimal strings")
    raise ValueError(f"{context} contains unsupported public payload value")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{context} must expose {field_name}")
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = payload.get(field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value
