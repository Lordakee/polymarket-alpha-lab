"""Report-only verification coverage for candidate-event research evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_VERIFICATION_COVERAGE_CONFIG_VERSION = (
    "verification-coverage-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.: -]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_COVERAGE_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "source",
    "url",
    "http://",
    "https://",
    "www.",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "buy",
    "sell",
    "trade",
    "trading",
    "advice",
    "recommend",
    "network",
    "database",
    "persist",
    "mutation",
    "write",
)
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "missing_confirming_evidence",
    "insufficient_family_independence",
    "missing_official_confirmation",
    "official_confirmation_present",
    "missing_counter_evidence",
    "counter_evidence_present",
    "refresh_stale",
    "refresh_current",
    "verification_coverage_pass",
    "verification_coverage_watch",
    "verification_coverage_block",
)


@dataclass(frozen=True)
class ResearchSourceVerificationCoverageConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_VERIFICATION_COVERAGE_CONFIG_VERSION
    min_independent_family_count: Decimal = Decimal("2.000000")
    min_verification_score: Decimal = Decimal("0.750000")
    max_refresh_age_minutes: Decimal = Decimal("180.000000")
    independence_weight: Decimal = Decimal("0.250000")
    official_confirmation_weight: Decimal = Decimal("0.250000")
    counter_evidence_weight: Decimal = Decimal("0.250000")
    refresh_timeliness_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceVerificationCoverageConfig:
            raise TypeError(
                "ResearchSourceVerificationCoverageConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceVerificationCoverageConfig:
            raise ValueError(
                "config must be exactly ResearchSourceVerificationCoverageConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_VERIFICATION_COVERAGE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_independent_family_count",
            _require_positive_count_decimal(
                "min_independent_family_count",
                self.min_independent_family_count,
            ),
        )
        object.__setattr__(
            self,
            "max_refresh_age_minutes",
            _require_positive_count_decimal(
                "max_refresh_age_minutes",
                self.max_refresh_age_minutes,
            ),
        )
        for field_name in (
            "min_verification_score",
            "independence_weight",
            "official_confirmation_weight",
            "counter_evidence_weight",
            "refresh_timeliness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.independence_weight
            + self.official_confirmation_weight
            + self.counter_evidence_weight
            + self.refresh_timeliness_weight
        ) != _ONE:
            raise ValueError("coverage weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceVerificationEvidence:
    event_id: str
    evidence_id: str
    family_id: str
    observed_at: datetime
    confidence_score: Decimal
    supports_event: bool = True
    is_official_confirmation: bool = False
    is_counter_evidence: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceVerificationEvidence:
            raise TypeError(
                "ResearchSourceVerificationEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceVerificationEvidence:
            raise ValueError(
                "evidence must be exactly ResearchSourceVerificationEvidence",
            )
        for field_name in ("event_id", "evidence_id", "family_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio_decimal("confidence_score", self.confidence_score),
        )
        for field_name in (
            "supports_event",
            "is_official_confirmation",
            "is_counter_evidence",
        ):
            _require_bool(field_name, getattr(self, field_name))
        if self.is_official_confirmation and not self.supports_event:
            raise ValueError("official confirmation must support event")
        if self.is_counter_evidence and self.supports_event:
            raise ValueError("counter evidence must not support event")
        if self.is_official_confirmation and self.is_counter_evidence:
            raise ValueError("evidence cannot be both official and counter evidence")
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchSourceVerificationPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceVerificationPublicPayloadItem:
            raise TypeError(
                "ResearchSourceVerificationPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceVerificationPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceVerificationPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_value("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceVerificationCoverageRow:
    event_id: str
    evidence_count: Decimal
    confirming_evidence_count: Decimal
    counter_evidence_count: Decimal
    independent_family_count: Decimal
    official_confirmation_count: Decimal
    stale_evidence_count: Decimal
    max_observed_age_minutes: Decimal
    verification_score: Decimal
    coverage_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceVerificationCoverageRow:
            raise TypeError(
                "ResearchSourceVerificationCoverageRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceVerificationCoverageRow:
            raise ValueError("row must be exactly ResearchSourceVerificationCoverageRow")
        _require_public_identifier("event_id", self.event_id)
        for field_name in (
            "evidence_count",
            "confirming_evidence_count",
            "counter_evidence_count",
            "independent_family_count",
            "official_confirmation_count",
            "stale_evidence_count",
            "max_observed_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "verification_score",
            _require_ratio_decimal("verification_score", self.verification_score),
        )
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceVerificationCoverageReport:
    generated_at: datetime
    config_version: str
    coverage_status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_verification_score: Decimal
    max_observed_age_minutes: Decimal
    rows: tuple[ResearchSourceVerificationCoverageRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSourceVerificationPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceVerificationCoverageReport:
            raise TypeError(
                "ResearchSourceVerificationCoverageReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceVerificationCoverageReport:
            raise ValueError(
                "report must be exactly ResearchSourceVerificationCoverageReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_VERIFICATION_COVERAGE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_coverage_status("coverage_status", self.coverage_status)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_verification_score", "max_observed_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
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
            "ResearchSourceVerificationCoverageReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_verification_coverage_report(
    evidence: Sequence[ResearchSourceVerificationEvidence],
    *,
    generated_at: datetime,
    config: ResearchSourceVerificationCoverageConfig | None = None,
    public_payload: Sequence[ResearchSourceVerificationPublicPayloadItem] = (),
) -> ResearchSourceVerificationCoverageReport:
    """Build a local report-only verification coverage snapshot."""

    if config is None:
        config = ResearchSourceVerificationCoverageConfig()
    if type(config) is not ResearchSourceVerificationCoverageConfig:
        raise ValueError("config must be a ResearchSourceVerificationCoverageConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("evidence observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_evidence, config, generated_at=generated_at)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "coverage_status": _report_status(rows),
        "event_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_verification_score": _average(
            tuple(row.verification_score for row in rows),
        ),
        "max_observed_age_minutes": (
            max((row.max_observed_age_minutes for row in rows), default=_ZERO)
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceVerificationCoverageReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    evidence: tuple[ResearchSourceVerificationEvidence, ...],
    config: ResearchSourceVerificationCoverageConfig,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceVerificationCoverageRow, ...]:
    grouped: dict[str, list[ResearchSourceVerificationEvidence]] = {}
    for item in evidence:
        grouped.setdefault(item.event_id, []).append(item)
    rows = [
        _row_for_group(event_id, tuple(items), config, generated_at=generated_at)
        for event_id, items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_group(
    event_id: str,
    evidence: tuple[ResearchSourceVerificationEvidence, ...],
    config: ResearchSourceVerificationCoverageConfig,
    *,
    generated_at: datetime,
) -> ResearchSourceVerificationCoverageRow:
    confirming_count = _decimal_count(sum(1 for item in evidence if item.supports_event))
    counter_count = _decimal_count(sum(1 for item in evidence if item.is_counter_evidence))
    official_count = _decimal_count(
        sum(1 for item in evidence if item.is_official_confirmation),
    )
    family_count = _decimal_count(len({item.family_id for item in evidence}))
    ages = tuple(_age_minutes(generated_at, item.observed_at) for item in evidence)
    stale_count = _decimal_count(
        sum(1 for age in ages if age > config.max_refresh_age_minutes),
    )
    max_age = max(ages, default=_ZERO)
    verification_score = _verification_score(
        family_count=family_count,
        official_count=official_count,
        counter_count=counter_count,
        stale_count=stale_count,
        evidence_count=_decimal_count(len(evidence)),
        config=config,
    )
    coverage_status = _row_status(
        confirming_count=confirming_count,
        family_count=family_count,
        official_count=official_count,
        counter_count=counter_count,
        stale_count=stale_count,
        verification_score=verification_score,
        config=config,
    )
    return ResearchSourceVerificationCoverageRow(
        event_id=event_id,
        evidence_count=_decimal_count(len(evidence)),
        confirming_evidence_count=confirming_count,
        counter_evidence_count=counter_count,
        independent_family_count=family_count,
        official_confirmation_count=official_count,
        stale_evidence_count=stale_count,
        max_observed_age_minutes=max_age,
        verification_score=verification_score,
        coverage_status=coverage_status,
        reason_codes=_row_reason_codes(
            confirming_count=confirming_count,
            family_count=family_count,
            official_count=official_count,
            counter_count=counter_count,
            stale_count=stale_count,
            coverage_status=coverage_status,
            config=config,
        ),
    )


def _verification_score(
    *,
    family_count: Decimal,
    official_count: Decimal,
    counter_count: Decimal,
    stale_count: Decimal,
    evidence_count: Decimal,
    config: ResearchSourceVerificationCoverageConfig,
) -> Decimal:
    score = _ZERO
    if family_count >= config.min_independent_family_count:
        score += config.independence_weight
    if official_count > _ZERO:
        score += config.official_confirmation_weight
    if counter_count > _ZERO:
        score += config.counter_evidence_weight
    if evidence_count > _ZERO and stale_count == _ZERO:
        score += config.refresh_timeliness_weight
    return _clamp_ratio(score)


def _row_status(
    *,
    confirming_count: Decimal,
    family_count: Decimal,
    official_count: Decimal,
    counter_count: Decimal,
    stale_count: Decimal,
    verification_score: Decimal,
    config: ResearchSourceVerificationCoverageConfig,
) -> str:
    if confirming_count == _ZERO or stale_count > _ZERO:
        return "block"
    if (
        family_count >= config.min_independent_family_count
        and official_count > _ZERO
        and counter_count > _ZERO
        and verification_score >= config.min_verification_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    confirming_count: Decimal,
    family_count: Decimal,
    official_count: Decimal,
    counter_count: Decimal,
    stale_count: Decimal,
    coverage_status: str,
    config: ResearchSourceVerificationCoverageConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if confirming_count == _ZERO:
        reason_codes.append("missing_confirming_evidence")
    if family_count < config.min_independent_family_count:
        reason_codes.append("insufficient_family_independence")
    if official_count > _ZERO:
        reason_codes.append("official_confirmation_present")
    else:
        reason_codes.append("missing_official_confirmation")
    if counter_count > _ZERO:
        reason_codes.append("counter_evidence_present")
    else:
        reason_codes.append("missing_counter_evidence")
    if stale_count > _ZERO:
        reason_codes.append("refresh_stale")
    else:
        reason_codes.append("refresh_current")
    reason_codes.append(f"verification_coverage_{coverage_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchSourceVerificationCoverageRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.coverage_status == "block" for row in rows):
        return "block"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceVerificationCoverageRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence", "verification_coverage_block")
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchSourceVerificationCoverageRow, ...],
    status: str,
) -> int:
    _require_coverage_status("status", status)
    return sum(1 for row in rows if row.coverage_status == status)


def _normalize_evidence(
    evidence: Sequence[ResearchSourceVerificationEvidence],
) -> tuple[ResearchSourceVerificationEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchSourceVerificationEvidence] = []
    for item in evidence:
        if type(item) is not ResearchSourceVerificationEvidence:
            raise ValueError("evidence items must be ResearchSourceVerificationEvidence")
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_id,
                item.family_id,
                item.evidence_id,
                item.observed_at.isoformat(),
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceVerificationCoverageRow],
) -> tuple[ResearchSourceVerificationCoverageRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceVerificationCoverageRow] = []
    for row in rows:
        if type(row) is not ResearchSourceVerificationCoverageRow:
            raise ValueError("rows must contain ResearchSourceVerificationCoverageRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.event_id))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourceVerificationPublicPayloadItem],
) -> tuple[ResearchSourceVerificationPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceVerificationPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchSourceVerificationPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchSourceVerificationPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_row_consistency(row: ResearchSourceVerificationCoverageRow) -> None:
    if row.confirming_evidence_count > row.evidence_count:
        raise ValueError("confirming_evidence_count must not exceed evidence_count")
    if row.counter_evidence_count > row.evidence_count:
        raise ValueError("counter_evidence_count must not exceed evidence_count")
    if row.official_confirmation_count > row.confirming_evidence_count:
        raise ValueError(
            "official_confirmation_count must not exceed confirming_evidence_count",
        )
    if row.stale_evidence_count > row.evidence_count:
        raise ValueError("stale_evidence_count must not exceed evidence_count")
    if row.evidence_count == _ZERO and row.max_observed_age_minutes != _ZERO:
        raise ValueError("max_observed_age_minutes must be zero without evidence")


def _validate_report_consistency(report: ResearchSourceVerificationCoverageReport) -> None:
    rows = report.rows
    if report.event_count != _decimal_count(len(rows)):
        raise ValueError("event_count does not match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count does not match rows")
    if report.coverage_status != _report_status(rows):
        raise ValueError("coverage_status does not match rows")
    if report.average_verification_score != _average(
        tuple(row.verification_score for row in rows),
    ):
        raise ValueError("average_verification_score does not match rows")
    if report.max_observed_age_minutes != max(
        (row.max_observed_age_minutes for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_observed_age_minutes does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_coverage_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _COVERAGE_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_value(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_VALUE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public value")
    return value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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
    if value < 0:
        raise ValueError("count must be nonnegative")
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


def _age_minutes(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    microseconds = (
        (delta.days * 86400 + delta.seconds) * 1_000_000
        + delta.microseconds
    )
    return _quantize(Decimal(microseconds) / Decimal("60000000"))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchSourceVerificationCoverageReport,
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
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_VERIFICATION_COVERAGE_CONFIG_VERSION",
    "ResearchSourceVerificationCoverageConfig",
    "ResearchSourceVerificationCoverageReport",
    "ResearchSourceVerificationCoverageRow",
    "ResearchSourceVerificationEvidence",
    "ResearchSourceVerificationPublicPayloadItem",
    "build_research_source_verification_coverage_report",
)
