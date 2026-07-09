"""Report-only primary evidence staleness alert builder.

The module is deterministic and side-effect free. Callers provide already
sanitized evidence buckets and local scoring inputs; the report returns a
public-safe staleness alert snapshot without storage, network, scraping, or
execution surfaces.
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


DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_STALENESS_ALERT_CONFIG_VERSION = (
    "research-source-primary-evidence-staleness-alert-report-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_AUTHORITY_TIERS = (
    "official_primary",
    "primary",
    "secondary_primary",
    "unknown",
)
_AUTHORITY_TIER_GAPS = {
    "official_primary": Decimal("0.000000"),
    "primary": Decimal("0.150000"),
    "secondary_primary": Decimal("0.450000"),
    "unknown": Decimal("0.750000"),
}
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "size",
        "sizing",
        "recommend",
        "recommendation",
        "execute",
        "execution",
        "buy",
        "sell",
        "live",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "secret",
        "apikey",
        "auth",
        "raw",
    ),
)
_UNSAFE_TOKEN_PAIRS = (
    frozenset(("source", "text")),
    frozenset(("source", "url")),
    frozenset(("market", "id")),
    frozenset(("market", "slug")),
    frozenset(("candidate", "id")),
    frozenset(("table", "name")),
)
_UNSAFE_COMPACT_MARKERS = (
    "sourceurl",
    "sourcetext",
    "marketid",
    "marketslug",
    "candidateid",
    "tablename",
)
_REASON_CODE_SEQUENCE = (
    "empty_primary_evidence_alert",
    "verification_age_pressure",
    "low_authority_tier_pressure",
    "low_corroboration_pressure",
    "contradiction_pressure",
    "low_extraction_confidence_pressure",
    "deadline_proximity_pressure",
    "verification_overdue",
    "primary_evidence_alert_pass",
    "primary_evidence_alert_watch",
    "primary_evidence_alert_block",
)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceStalenessAlertConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_STALENESS_ALERT_CONFIG_VERSION
    )
    stale_after_seconds: Decimal = Decimal("86400.000000")
    deadline_window_seconds: Decimal = Decimal("172800.000000")
    watch_alert_score: Decimal = Decimal("0.250000")
    block_alert_score: Decimal = Decimal("0.750000")
    verification_age_weight: Decimal = Decimal("0.300000")
    authority_tier_weight: Decimal = Decimal("0.150000")
    corroboration_gap_weight: Decimal = Decimal("0.150000")
    contradiction_pressure_weight: Decimal = Decimal("0.150000")
    extraction_confidence_gap_weight: Decimal = Decimal("0.150000")
    deadline_proximity_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceStalenessAlertConfig:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceStalenessAlertConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceStalenessAlertConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_STALENESS_ALERT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("stale_after_seconds", "deadline_window_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_alert_score",
            "block_alert_score",
            "verification_age_weight",
            "authority_tier_weight",
            "corroboration_gap_weight",
            "contradiction_pressure_weight",
            "extraction_confidence_gap_weight",
            "deadline_proximity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_alert_score >= self.block_alert_score:
            raise ValueError("watch_alert_score must be below block_alert_score")
        weight_sum = _quantize(
            self.verification_age_weight
            + self.authority_tier_weight
            + self.corroboration_gap_weight
            + self.contradiction_pressure_weight
            + self.extraction_confidence_gap_weight
            + self.deadline_proximity_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("primary evidence alert weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceStalenessAlertInput:
    evidence_key: str
    authority_tier: str
    last_verified_at: datetime
    corroboration_count: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    deadline_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceStalenessAlertInput:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceStalenessAlertInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceStalenessAlertInput,
            "alert input",
        )
        object.__setattr__(
            self,
            "evidence_key",
            _require_evidence_key("evidence_key", self.evidence_key),
        )
        object.__setattr__(
            self,
            "authority_tier",
            _require_authority_tier("authority_tier", self.authority_tier),
        )
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_count_decimal(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _require_ratio_decimal(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        object.__setattr__(
            self,
            "extraction_confidence",
            _require_ratio_decimal(
                "extraction_confidence",
                self.extraction_confidence,
            ),
        )
        object.__setattr__(
            self,
            "deadline_at",
            _as_utc("deadline_at", self.deadline_at),
        )
        _require_hard_flags("alert input", self)
        _reject_unsafe_public_payload("alert input", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem,
            "public payload item",
        )
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount,
            "reason code count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceStalenessAlertRow:
    evidence_key: str
    authority_tier: str
    authority_tier_gap_score: Decimal
    last_verified_at: datetime
    verification_age_seconds: Decimal
    verification_age_pressure: Decimal
    corroboration_count: Decimal
    corroboration_gap_score: Decimal
    contradiction_pressure: Decimal
    extraction_confidence: Decimal
    extraction_confidence_gap_score: Decimal
    deadline_at: datetime
    deadline_proximity_score: Decimal
    alert_score: Decimal
    verification_overdue_by_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceStalenessAlertRow:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceStalenessAlertRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceStalenessAlertRow,
            "row",
        )
        object.__setattr__(
            self,
            "evidence_key",
            _require_evidence_key("evidence_key", self.evidence_key),
        )
        object.__setattr__(
            self,
            "authority_tier",
            _require_authority_tier("authority_tier", self.authority_tier),
        )
        object.__setattr__(
            self,
            "last_verified_at",
            _as_utc("last_verified_at", self.last_verified_at),
        )
        object.__setattr__(
            self,
            "deadline_at",
            _as_utc("deadline_at", self.deadline_at),
        )
        for field_name in (
            "verification_age_seconds",
            "corroboration_count",
            "verification_overdue_by_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_or_measure_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "authority_tier_gap_score",
            "verification_age_pressure",
            "corroboration_gap_score",
            "contradiction_pressure",
            "extraction_confidence",
            "extraction_confidence_gap_score",
            "deadline_proximity_score",
            "alert_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourcePrimaryEvidenceStalenessAlertReport:
    generated_at: datetime
    config_version: str
    stale_after_seconds: Decimal
    deadline_window_seconds: Decimal
    watch_alert_score: Decimal
    block_alert_score: Decimal
    status: str
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overdue_count: Decimal
    average_alert_score: Decimal
    max_alert_score: Decimal
    rows: tuple[ResearchSourcePrimaryEvidenceStalenessAlertRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount, ...]
    public_payload: tuple[ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePrimaryEvidenceStalenessAlertReport:
            raise TypeError(
                "ResearchSourcePrimaryEvidenceStalenessAlertReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourcePrimaryEvidenceStalenessAlertReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_STALENESS_ALERT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("stale_after_seconds", "deadline_window_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_alert_score",
            "block_alert_score",
            "average_alert_score",
            "max_alert_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_alert_score >= self.block_alert_score:
            raise ValueError("watch_alert_score must be below block_alert_score")
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
            "overdue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
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
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
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
            "ResearchSourcePrimaryEvidenceStalenessAlertReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_primary_evidence_staleness_alert_report(
    alert_inputs: Sequence[ResearchSourcePrimaryEvidenceStalenessAlertInput],
    *,
    generated_at: datetime,
    config: ResearchSourcePrimaryEvidenceStalenessAlertConfig | None = None,
    public_payload: Sequence[
        ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem
    ] = (),
) -> ResearchSourcePrimaryEvidenceStalenessAlertReport:
    """Build a local report-only primary evidence staleness alert snapshot."""

    if config is None:
        config = ResearchSourcePrimaryEvidenceStalenessAlertConfig()
    if type(config) is not ResearchSourcePrimaryEvidenceStalenessAlertConfig:
        raise ValueError(
            "config must be a ResearchSourcePrimaryEvidenceStalenessAlertConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(alert_inputs)
    for item in normalized_inputs:
        if item.last_verified_at > generated_at_utc:
            raise ValueError("last_verified_at must not be after generated_at")
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
        "watch_alert_score": config.watch_alert_score,
        "block_alert_score": config.block_alert_score,
        "status": _report_status(rows),
        "evidence_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "overdue_count": _decimal_count(
            sum(1 for row in rows if row.verification_overdue_by_seconds > _ZERO),
        ),
        "average_alert_score": _average(tuple(row.alert_score for row in rows)),
        "max_alert_score": max((row.alert_score for row in rows), default=_ZERO),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourcePrimaryEvidenceStalenessAlertReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_primary_evidence_staleness_alert_report_payload(
    report: ResearchSourcePrimaryEvidenceStalenessAlertReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourcePrimaryEvidenceStalenessAlertReport:
        raise ValueError(
            "report must be a ResearchSourcePrimaryEvidenceStalenessAlertReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def _row_from_input(
    item: ResearchSourcePrimaryEvidenceStalenessAlertInput,
    *,
    generated_at: datetime,
    config: ResearchSourcePrimaryEvidenceStalenessAlertConfig,
) -> ResearchSourcePrimaryEvidenceStalenessAlertRow:
    verification_age = _age_seconds(generated_at, item.last_verified_at)
    age_pressure = _verification_age_pressure(verification_age, config.stale_after_seconds)
    authority_gap = _AUTHORITY_TIER_GAPS[item.authority_tier]
    corroboration_gap = _corroboration_gap_score(item.corroboration_count)
    extraction_gap = _clamp_ratio(_ONE - item.extraction_confidence)
    deadline_proximity = _deadline_proximity_score(
        generated_at=generated_at,
        deadline_at=item.deadline_at,
        deadline_window_seconds=config.deadline_window_seconds,
    )
    alert_score = _alert_score(
        verification_age_pressure=age_pressure,
        authority_tier_gap_score=authority_gap,
        corroboration_gap_score=corroboration_gap,
        contradiction_pressure=item.contradiction_pressure,
        extraction_confidence_gap_score=extraction_gap,
        deadline_proximity_score=deadline_proximity,
        config=config,
    )
    overdue_by = _verification_overdue_by_seconds(
        verification_age,
        config.stale_after_seconds,
    )
    status = _row_status(
        alert_score=alert_score,
        verification_overdue_by_seconds=overdue_by,
        watch_alert_score=config.watch_alert_score,
        block_alert_score=config.block_alert_score,
    )
    return ResearchSourcePrimaryEvidenceStalenessAlertRow(
        evidence_key=item.evidence_key,
        authority_tier=item.authority_tier,
        authority_tier_gap_score=authority_gap,
        last_verified_at=item.last_verified_at,
        verification_age_seconds=verification_age,
        verification_age_pressure=age_pressure,
        corroboration_count=item.corroboration_count,
        corroboration_gap_score=corroboration_gap,
        contradiction_pressure=item.contradiction_pressure,
        extraction_confidence=item.extraction_confidence,
        extraction_confidence_gap_score=extraction_gap,
        deadline_at=item.deadline_at,
        deadline_proximity_score=deadline_proximity,
        alert_score=alert_score,
        verification_overdue_by_seconds=overdue_by,
        status=status,
        reason_codes=_row_reason_codes(
            verification_age_pressure=age_pressure,
            authority_tier_gap_score=authority_gap,
            corroboration_gap_score=corroboration_gap,
            contradiction_pressure=item.contradiction_pressure,
            extraction_confidence_gap_score=extraction_gap,
            deadline_proximity_score=deadline_proximity,
            verification_overdue_by_seconds=overdue_by,
            status=status,
        ),
    )


def _alert_score(
    *,
    verification_age_pressure: Decimal,
    authority_tier_gap_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence_gap_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchSourcePrimaryEvidenceStalenessAlertConfig,
) -> Decimal:
    return _clamp_ratio(
        (verification_age_pressure * config.verification_age_weight)
        + (authority_tier_gap_score * config.authority_tier_weight)
        + (corroboration_gap_score * config.corroboration_gap_weight)
        + (contradiction_pressure * config.contradiction_pressure_weight)
        + (extraction_confidence_gap_score * config.extraction_confidence_gap_weight)
        + (deadline_proximity_score * config.deadline_proximity_weight),
    )


def _verification_age_pressure(
    verification_age_seconds: Decimal,
    stale_after_seconds: Decimal,
) -> Decimal:
    if verification_age_seconds >= stale_after_seconds:
        return _ONE
    return _clamp_ratio(verification_age_seconds / stale_after_seconds)


def _corroboration_gap_score(corroboration_count: Decimal) -> Decimal:
    if corroboration_count >= Decimal("3.000000"):
        return _ZERO
    return _clamp_ratio((Decimal("3.000000") - corroboration_count) / Decimal("3.000000"))


def _deadline_proximity_score(
    *,
    generated_at: datetime,
    deadline_at: datetime,
    deadline_window_seconds: Decimal,
) -> Decimal:
    if deadline_at <= generated_at:
        return _ONE
    seconds_until = _age_seconds(deadline_at, generated_at)
    if seconds_until >= deadline_window_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (seconds_until / deadline_window_seconds))


def _verification_overdue_by_seconds(
    verification_age_seconds: Decimal,
    stale_after_seconds: Decimal,
) -> Decimal:
    if verification_age_seconds <= stale_after_seconds:
        return _ZERO
    return _quantize(verification_age_seconds - stale_after_seconds)


def _row_status(
    *,
    alert_score: Decimal,
    verification_overdue_by_seconds: Decimal,
    watch_alert_score: Decimal,
    block_alert_score: Decimal,
) -> str:
    if alert_score >= block_alert_score:
        return "block"
    if alert_score >= watch_alert_score:
        return "watch"
    if verification_overdue_by_seconds > _ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    verification_age_pressure: Decimal,
    authority_tier_gap_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_pressure: Decimal,
    extraction_confidence_gap_score: Decimal,
    deadline_proximity_score: Decimal,
    verification_overdue_by_seconds: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"primary_evidence_alert_{status}"]
    if verification_age_pressure >= Decimal("0.500000"):
        reason_codes.append("verification_age_pressure")
    if authority_tier_gap_score >= Decimal("0.450000"):
        reason_codes.append("low_authority_tier_pressure")
    if corroboration_gap_score >= Decimal("0.500000"):
        reason_codes.append("low_corroboration_pressure")
    if contradiction_pressure >= Decimal("0.500000"):
        reason_codes.append("contradiction_pressure")
    if extraction_confidence_gap_score >= Decimal("0.500000"):
        reason_codes.append("low_extraction_confidence_pressure")
    if deadline_proximity_score >= Decimal("0.500000"):
        reason_codes.append("deadline_proximity_pressure")
    if verification_overdue_by_seconds > _ZERO:
        reason_codes.append("verification_overdue")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchSourcePrimaryEvidenceStalenessAlertRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourcePrimaryEvidenceStalenessAlertRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_primary_evidence_alert",)
    return _normalize_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourcePrimaryEvidenceStalenessAlertRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchSourcePrimaryEvidenceStalenessAlertRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    alert_inputs: Sequence[ResearchSourcePrimaryEvidenceStalenessAlertInput],
) -> tuple[ResearchSourcePrimaryEvidenceStalenessAlertInput, ...]:
    if isinstance(alert_inputs, (str, bytes)) or not isinstance(alert_inputs, Sequence):
        raise ValueError("alert_inputs must be a sequence")
    normalized: list[ResearchSourcePrimaryEvidenceStalenessAlertInput] = []
    seen: set[str] = set()
    for item in alert_inputs:
        if type(item) is not ResearchSourcePrimaryEvidenceStalenessAlertInput:
            raise ValueError(
                "alert_inputs must contain "
                "ResearchSourcePrimaryEvidenceStalenessAlertInput values",
            )
        _require_hard_flags("alert input", item)
        if item.evidence_key in seen:
            raise ValueError("alert_inputs must not contain duplicate evidence_key values")
        seen.add(item.evidence_key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.evidence_key))


def _normalize_rows(
    rows: Sequence[ResearchSourcePrimaryEvidenceStalenessAlertRow],
) -> tuple[ResearchSourcePrimaryEvidenceStalenessAlertRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourcePrimaryEvidenceStalenessAlertRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourcePrimaryEvidenceStalenessAlertRow:
            raise ValueError(
                "rows must contain ResearchSourcePrimaryEvidenceStalenessAlertRow "
                "values",
            )
        _require_hard_flags("row", row)
        if row.evidence_key in seen:
            raise ValueError("rows must not contain duplicate evidence_key values")
        seen.add(row.evidence_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.evidence_key))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem],
) -> tuple[ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem values",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen:
            raise ValueError("public_payload must not contain duplicate keys")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount],
) -> tuple[ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount] = []
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount values",
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


def _validate_row_consistency(
    row: ResearchSourcePrimaryEvidenceStalenessAlertRow,
) -> None:
    if row.authority_tier_gap_score != _AUTHORITY_TIER_GAPS[row.authority_tier]:
        raise ValueError("authority_tier_gap_score must match authority_tier")
    if row.corroboration_gap_score != _corroboration_gap_score(row.corroboration_count):
        raise ValueError("corroboration_gap_score must match corroboration_count")
    if row.extraction_confidence_gap_score != _clamp_ratio(
        _ONE - row.extraction_confidence,
    ):
        raise ValueError(
            "extraction_confidence_gap_score must match extraction_confidence",
        )
    if row.status == "pass" and "primary_evidence_alert_pass" not in row.reason_codes:
        raise ValueError("pass rows must include primary_evidence_alert_pass")
    if row.status == "watch" and "primary_evidence_alert_watch" not in row.reason_codes:
        raise ValueError("watch rows must include primary_evidence_alert_watch")
    if row.status == "block" and "primary_evidence_alert_block" not in row.reason_codes:
        raise ValueError("block rows must include primary_evidence_alert_block")


def _validate_report_consistency(
    report: ResearchSourcePrimaryEvidenceStalenessAlertReport,
) -> None:
    if report.evidence_count != _decimal_count(len(report.rows)):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_overdue_count = _decimal_count(
        sum(1 for row in report.rows if row.verification_overdue_by_seconds > _ZERO),
    )
    if report.overdue_count != expected_overdue_count:
        raise ValueError("overdue_count must match rows")
    expected_average = _average(tuple(row.alert_score for row in report.rows))
    if report.average_alert_score != expected_average:
        raise ValueError("average_alert_score must match rows")
    expected_max = max((row.alert_score for row in report.rows), default=_ZERO)
    if report.max_alert_score != expected_max:
        raise ValueError("max_alert_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    for row in report.rows:
        expected_status = _row_status(
            alert_score=row.alert_score,
            verification_overdue_by_seconds=row.verification_overdue_by_seconds,
            watch_alert_score=report.watch_alert_score,
            block_alert_score=report.block_alert_score,
        )
        if row.status != expected_status:
            raise ValueError("row status must match report thresholds")
        expected_age_pressure = _verification_age_pressure(
            row.verification_age_seconds,
            report.stale_after_seconds,
        )
        if row.verification_age_pressure != expected_age_pressure:
            raise ValueError("row verification_age_pressure must match report thresholds")
        expected_overdue = _verification_overdue_by_seconds(
            row.verification_age_seconds,
            report.stale_after_seconds,
        )
        if row.verification_overdue_by_seconds != expected_overdue:
            raise ValueError("row verification_overdue_by_seconds must match thresholds")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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


def _require_evidence_key(field_name: str, value: object) -> str:
    normalized = _require_public_identifier(field_name, value)
    if not normalized.startswith("evidence_"):
        raise ValueError(f"{field_name} must use the evidence_ public namespace")
    return normalized


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_authority_tier(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _AUTHORITY_TIERS:
        raise ValueError(f"{field_name} must be a supported authority tier")
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


def _require_nonnegative_count_or_measure_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_or_measure_decimal(field_name, value)
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


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND),
    )


def _datetime_plus_decimal_seconds(start: datetime, seconds: Decimal) -> datetime:
    microseconds = int(
        (seconds * _MICROSECONDS_PER_SECOND).to_integral_value(
            rounding=ROUND_HALF_UP,
        ),
    )
    return start + timedelta(microseconds=microseconds)


def _report_values_without_digest(
    report: ResearchSourcePrimaryEvidenceStalenessAlertReport,
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
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
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
        return
    if type(value) in (bool, Decimal, datetime):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    _reject_unsafe_public_string(f"{path}.{key}", key)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if "/" in lowered or "\\" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    compact = re.sub(r"[^a-z0-9]", "", lowered)
    if any(marker in compact for marker in _UNSAFE_COMPACT_MARKERS):
        raise ValueError(f"{field_name} has unsafe public value")
    searchable = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    searchable = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", "_", searchable)
    tokens = set(re.findall(r"[a-z0-9]+", searchable.lower()))
    if tokens & _UNSAFE_PUBLIC_TOKENS:
        raise ValueError(f"{field_name} has unsafe public value")
    for token_pair in _UNSAFE_TOKEN_PAIRS:
        if token_pair.issubset(tokens):
            raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_STALENESS_ALERT_CONFIG_VERSION",
    "ResearchSourcePrimaryEvidenceStalenessAlertConfig",
    "ResearchSourcePrimaryEvidenceStalenessAlertInput",
    "ResearchSourcePrimaryEvidenceStalenessAlertPublicPayloadItem",
    "ResearchSourcePrimaryEvidenceStalenessAlertReasonCodeCount",
    "ResearchSourcePrimaryEvidenceStalenessAlertReport",
    "ResearchSourcePrimaryEvidenceStalenessAlertRow",
    "build_research_source_primary_evidence_staleness_alert_report",
    "research_source_primary_evidence_staleness_alert_report_payload",
)
