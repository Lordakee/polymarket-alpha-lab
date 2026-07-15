"""Pure report-only reducer for source claim update latency breach checks."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_LATENCY_BREACH_CONFIG_VERSION = (
    "research-source-claim-update-latency-breach-v0"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "raw",
    "http",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "private",
    "secret",
    "credential",
)
_REASON_CODE_SEQUENCE = (
    "update_latency_watch",
    "update_latency_block",
    "source_authority_watch",
    "source_authority_block",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "corroboration_depth_watch",
    "corroboration_depth_block",
    "extraction_confidence_watch",
    "extraction_confidence_block",
    "missing_fields_watch",
    "missing_fields_block",
    "deadline_proximity_watch",
    "deadline_proximity_block",
    "claim_update_latency_pass",
)
_PUBLIC_ROW_SCHEMA = (
    "claim_bucket",
    "expected_update_cadence_seconds",
    "latest_verification_age_seconds",
    "latency_ratio",
    "source_authority_score",
    "contradiction_pressure",
    "corroboration_depth",
    "extraction_confidence",
    "missing_field_count",
    "deadline_seconds",
    "breach_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_REPORT_SCHEMA = (
    "generated_at",
    "config_version",
    "claim_bucket_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_latest_verification_age_seconds",
    "max_latency_ratio",
    "max_contradiction_pressure",
    "min_extraction_confidence",
    "min_deadline_seconds",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchSourceClaimUpdateLatencyBreachConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_LATENCY_BREACH_CONFIG_VERSION
    watch_latency_ratio: Decimal = Decimal("1.500000")
    block_latency_ratio: Decimal = Decimal("3.000000")
    watch_source_authority_score: Decimal = Decimal("0.500000")
    block_source_authority_score: Decimal = Decimal("0.250000")
    watch_contradiction_pressure: Decimal = Decimal("0.400000")
    block_contradiction_pressure: Decimal = Decimal("0.750000")
    watch_corroboration_depth: Decimal = Decimal("2")
    block_corroboration_depth: Decimal = Decimal("0")
    watch_extraction_confidence: Decimal = Decimal("0.700000")
    block_extraction_confidence: Decimal = Decimal("0.400000")
    watch_missing_field_count: Decimal = Decimal("1")
    block_missing_field_count: Decimal = Decimal("3")
    watch_deadline_seconds: Decimal = Decimal("7200.000000")
    block_deadline_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimUpdateLatencyBreachConfig:
            raise TypeError(
                "ResearchSourceClaimUpdateLatencyBreachConfig cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimUpdateLatencyBreachConfig:
            raise ValueError(
                "config must be exactly ResearchSourceClaimUpdateLatencyBreachConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_LATENCY_BREACH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_latency_ratio", "block_latency_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_source_authority_score",
            "block_source_authority_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_extraction_confidence",
            "block_extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_corroboration_depth",
            "block_corroboration_depth",
            "watch_missing_field_count",
            "block_missing_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_deadline_seconds", "block_deadline_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_before_block_high(
            "latency_ratio",
            self.watch_latency_ratio,
            self.block_latency_ratio,
        )
        _require_watch_before_block_high(
            "contradiction_pressure",
            self.watch_contradiction_pressure,
            self.block_contradiction_pressure,
        )
        _require_watch_before_block_high(
            "missing_field_count",
            self.watch_missing_field_count,
            self.block_missing_field_count,
        )
        _require_watch_before_block_low(
            "source_authority_score",
            self.watch_source_authority_score,
            self.block_source_authority_score,
        )
        _require_watch_before_block_low(
            "corroboration_depth",
            self.watch_corroboration_depth,
            self.block_corroboration_depth,
        )
        _require_watch_before_block_low(
            "extraction_confidence",
            self.watch_extraction_confidence,
            self.block_extraction_confidence,
        )
        _require_watch_before_block_low(
            "deadline_seconds",
            self.watch_deadline_seconds,
            self.block_deadline_seconds,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimUpdateLatencyObservation:
    claim_bucket: str
    expected_update_cadence_seconds: Decimal
    latest_verified_at: datetime | None
    source_authority_score: Decimal
    contradiction_pressure: Decimal
    corroboration_depth: Decimal
    extraction_confidence: Decimal
    missing_field_count: Decimal
    deadline_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimUpdateLatencyObservation:
            raise TypeError(
                "ResearchSourceClaimUpdateLatencyObservation cannot be subclassed",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimUpdateLatencyObservation:
            raise ValueError(
                "observation must be exactly ResearchSourceClaimUpdateLatencyObservation",
            )
        _require_public_identifier("claim_bucket", self.claim_bucket)
        object.__setattr__(
            self,
            "expected_update_cadence_seconds",
            _require_positive_decimal(
                "expected_update_cadence_seconds",
                self.expected_update_cadence_seconds,
            ),
        )
        if self.latest_verified_at is not None:
            object.__setattr__(
                self,
                "latest_verified_at",
                _as_utc("latest_verified_at", self.latest_verified_at),
            )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("corroboration_depth", "missing_field_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.deadline_at is not None:
            object.__setattr__(
                self,
                "deadline_at",
                _as_utc("deadline_at", self.deadline_at),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimUpdateLatencyBreachRow:
    claim_bucket: str
    expected_update_cadence_seconds: Decimal
    latest_verification_age_seconds: Decimal
    latency_ratio: Decimal
    source_authority_score: Decimal
    contradiction_pressure: Decimal
    corroboration_depth: Decimal
    extraction_confidence: Decimal
    missing_field_count: Decimal
    deadline_seconds: Decimal
    breach_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchSourceClaimUpdateLatencyBreachConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimUpdateLatencyBreachRow:
            raise TypeError(
                "ResearchSourceClaimUpdateLatencyBreachRow cannot be subclassed",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourceClaimUpdateLatencyBreachConfig | None,
    ) -> None:
        if type(self) is not ResearchSourceClaimUpdateLatencyBreachRow:
            raise ValueError("row must be exactly ResearchSourceClaimUpdateLatencyBreachRow")
        normalized_config = _normalize_validation_config(validation_config)
        object.__setattr__(self, "_validation_config", normalized_config)
        _require_public_identifier("claim_bucket", self.claim_bucket)
        object.__setattr__(
            self,
            "expected_update_cadence_seconds",
            _require_positive_decimal(
                "expected_update_cadence_seconds",
                self.expected_update_cadence_seconds,
            ),
        )
        for field_name in (
            "latest_verification_age_seconds",
            "latency_ratio",
            "deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_authority_score",
            "contradiction_pressure",
            "extraction_confidence",
            "breach_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("corroboration_depth", "missing_field_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self, normalized_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceClaimUpdateLatencyBreachReport:
    generated_at: datetime
    config_version: str
    claim_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_latest_verification_age_seconds: Decimal
    max_latency_ratio: Decimal
    max_contradiction_pressure: Decimal
    min_extraction_confidence: Decimal
    min_deadline_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceClaimUpdateLatencyBreachRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchSourceClaimUpdateLatencyBreachConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimUpdateLatencyBreachReport:
            raise TypeError(
                "ResearchSourceClaimUpdateLatencyBreachReport cannot be subclassed",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourceClaimUpdateLatencyBreachConfig | None,
    ) -> None:
        if type(self) is not ResearchSourceClaimUpdateLatencyBreachReport:
            raise ValueError(
                "report must be exactly ResearchSourceClaimUpdateLatencyBreachReport",
            )
        normalized_config = _normalize_validation_config(validation_config)
        object.__setattr__(self, "_validation_config", normalized_config)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_LATENCY_BREACH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("claim_bucket_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_latest_verification_age_seconds",
            "max_latency_ratio",
            "min_deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_contradiction_pressure", "min_extraction_confidence"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows, normalized_config))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self, normalized_config)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_claim_update_latency_breach_report(
    observations: Sequence[ResearchSourceClaimUpdateLatencyObservation],
    *,
    config: ResearchSourceClaimUpdateLatencyBreachConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceClaimUpdateLatencyBreachReport:
    if config is None:
        config = ResearchSourceClaimUpdateLatencyBreachConfig()
    config = _revalidate_config(config, label="config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    _reject_empty_observations(normalized)
    for item in normalized:
        if item.latest_verified_at is not None:
            _reject_future_time("latest_verified_at", item.latest_verified_at, generated_at)
        if item.deadline_at is not None and item.deadline_at < generated_at:
            raise ValueError("deadline_at must not be before generated_at")

    rows = tuple(
        sorted(
            (
                _row_for_observation(item, generated_at=generated_at, config=config)
                for item in normalized
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "claim_bucket_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "max_latest_verification_age_seconds": max(
            (row.latest_verification_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_latency_ratio": max((row.latency_ratio for row in rows), default=_ZERO),
        "max_contradiction_pressure": max(
            (row.contradiction_pressure for row in rows),
            default=_ZERO,
        ),
        "min_extraction_confidence": min(
            (row.extraction_confidence for row in rows),
            default=_ONE,
        ),
        "min_deadline_seconds": min((row.deadline_seconds for row in rows), default=_ZERO),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimUpdateLatencyBreachReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
        validation_config=config,
    )


def research_source_claim_update_latency_breach_report_payload(
    report: ResearchSourceClaimUpdateLatencyBreachReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceClaimUpdateLatencyBreachReport:
        validation_config = _normalize_validation_config(
            getattr(report, "_validation_config", None),
        )
        _validate_report_consistency(report, validation_config)
        expected_digest = _report_digest_from_values(
            _report_values_without_digest(report),
        )
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(report))
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _report_from_public_payload(payload, validation_config=validation_config)
        return payload
    if type(report) is dict:
        return validate_research_source_claim_update_latency_breach_public_payload(report)
    raise ValueError(
        "report must be a ResearchSourceClaimUpdateLatencyBreachReport or public payload",
    )


def validate_research_source_claim_update_latency_breach_public_payload(
    payload: dict[str, object],
    *,
    config: ResearchSourceClaimUpdateLatencyBreachConfig | None = None,
) -> dict[str, object]:
    validation_config = _normalize_validation_config(config)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    report = _report_from_public_payload(
        payload,
        validation_config=validation_config,
    )
    canonical = _json_ready(asdict(report))
    if type(canonical) is not dict:
        raise ValueError("public payload must be a JSON object")
    if canonical != payload:
        raise ValueError("public payload must be canonical")
    return canonical


def _report_from_public_payload(
    value: object,
    *,
    validation_config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> ResearchSourceClaimUpdateLatencyBreachReport:
    payload = _require_public_object_schema(
        "public payload",
        value,
        _PUBLIC_REPORT_SCHEMA,
    )
    generated_at = _public_datetime("generated_at", payload["generated_at"])
    config_version = _public_identifier("config_version", payload["config_version"])
    if config_version != validation_config.config_version:
        raise ValueError("config_version must be the supported config version")
    rows = tuple(
        _row_from_public_payload(item, validation_config=validation_config)
        for item in _require_public_array("rows", payload["rows"])
    )
    return ResearchSourceClaimUpdateLatencyBreachReport(
        generated_at=generated_at,
        config_version=config_version,
        claim_bucket_count=_public_decimal(
            "claim_bucket_count",
            payload["claim_bucket_count"],
            _require_nonnegative_whole_decimal,
        ),
        pass_count=_public_decimal(
            "pass_count",
            payload["pass_count"],
            _require_nonnegative_whole_decimal,
        ),
        watch_count=_public_decimal(
            "watch_count",
            payload["watch_count"],
            _require_nonnegative_whole_decimal,
        ),
        block_count=_public_decimal(
            "block_count",
            payload["block_count"],
            _require_nonnegative_whole_decimal,
        ),
        max_latest_verification_age_seconds=_public_decimal(
            "max_latest_verification_age_seconds",
            payload["max_latest_verification_age_seconds"],
            _require_nonnegative_decimal,
        ),
        max_latency_ratio=_public_decimal(
            "max_latency_ratio",
            payload["max_latency_ratio"],
            _require_nonnegative_decimal,
        ),
        max_contradiction_pressure=_public_decimal(
            "max_contradiction_pressure",
            payload["max_contradiction_pressure"],
            _require_ratio_decimal,
        ),
        min_extraction_confidence=_public_decimal(
            "min_extraction_confidence",
            payload["min_extraction_confidence"],
            _require_ratio_decimal,
        ),
        min_deadline_seconds=_public_decimal(
            "min_deadline_seconds",
            payload["min_deadline_seconds"],
            _require_nonnegative_decimal,
        ),
        status=_public_status("status", payload["status"]),
        reason_codes=_public_reason_codes("reason_codes", payload["reason_codes"]),
        rows=rows,
        derived_validation_digest=_public_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=validation_config,
    )


def _row_from_public_payload(
    value: object,
    *,
    validation_config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> ResearchSourceClaimUpdateLatencyBreachRow:
    payload = _require_public_object_schema("row", value, _PUBLIC_ROW_SCHEMA)
    return ResearchSourceClaimUpdateLatencyBreachRow(
        claim_bucket=_public_identifier("claim_bucket", payload["claim_bucket"]),
        expected_update_cadence_seconds=_public_decimal(
            "expected_update_cadence_seconds",
            payload["expected_update_cadence_seconds"],
            _require_positive_decimal,
        ),
        latest_verification_age_seconds=_public_decimal(
            "latest_verification_age_seconds",
            payload["latest_verification_age_seconds"],
            _require_nonnegative_decimal,
        ),
        latency_ratio=_public_decimal(
            "latency_ratio",
            payload["latency_ratio"],
            _require_nonnegative_decimal,
        ),
        source_authority_score=_public_decimal(
            "source_authority_score",
            payload["source_authority_score"],
            _require_ratio_decimal,
        ),
        contradiction_pressure=_public_decimal(
            "contradiction_pressure",
            payload["contradiction_pressure"],
            _require_ratio_decimal,
        ),
        corroboration_depth=_public_decimal(
            "corroboration_depth",
            payload["corroboration_depth"],
            _require_nonnegative_whole_decimal,
        ),
        extraction_confidence=_public_decimal(
            "extraction_confidence",
            payload["extraction_confidence"],
            _require_ratio_decimal,
        ),
        missing_field_count=_public_decimal(
            "missing_field_count",
            payload["missing_field_count"],
            _require_nonnegative_whole_decimal,
        ),
        deadline_seconds=_public_decimal(
            "deadline_seconds",
            payload["deadline_seconds"],
            _require_nonnegative_decimal,
        ),
        breach_score=_public_decimal(
            "breach_score",
            payload["breach_score"],
            _require_ratio_decimal,
        ),
        status=_public_status("status", payload["status"]),
        reason_codes=_public_reason_codes("reason_codes", payload["reason_codes"]),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
        validation_config=validation_config,
    )


def _require_public_object_schema(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if any(type(key) is not str for key in value):
        raise ValueError(f"{label} keys must be strings")
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} schema must use exact fields")
    return dict(value)


def _require_public_array(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _public_identifier(field_name: str, value: object) -> str:
    return _require_public_identifier(field_name, value)


def _public_decimal(
    field_name: str,
    value: object,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _public_status(field_name: str, value: object) -> str:
    return _require_status(field_name, value)


def _public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    items = _require_public_array(field_name, value)
    if not items or any(type(item) is not str for item in items):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = _normalize_reason_codes(items)
    if normalized != items:
        raise ValueError(f"{field_name} must be canonical")
    return normalized


def _public_sha256(field_name: str, value: object) -> str:
    return _require_sha256_digest(field_name, value)


def _public_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _row_for_observation(
    observation: ResearchSourceClaimUpdateLatencyObservation,
    *,
    generated_at: datetime,
    config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> ResearchSourceClaimUpdateLatencyBreachRow:
    latest_age = _latest_verification_age_seconds(observation, generated_at, config)
    with localcontext(_DECIMAL_CONTEXT):
        latency_ratio = _quantize(
            latest_age / observation.expected_update_cadence_seconds,
        )
    deadline_seconds = _deadline_seconds(observation, generated_at)
    reason_codes = _row_reason_codes(
        latest_verification_age_seconds=latest_age,
        latency_ratio=latency_ratio,
        source_authority_score=observation.source_authority_score,
        contradiction_pressure=observation.contradiction_pressure,
        corroboration_depth=observation.corroboration_depth,
        extraction_confidence=observation.extraction_confidence,
        missing_field_count=observation.missing_field_count,
        deadline_seconds=deadline_seconds,
        config=config,
    )
    return ResearchSourceClaimUpdateLatencyBreachRow(
        claim_bucket=observation.claim_bucket,
        expected_update_cadence_seconds=observation.expected_update_cadence_seconds,
        latest_verification_age_seconds=latest_age,
        latency_ratio=latency_ratio,
        source_authority_score=observation.source_authority_score,
        contradiction_pressure=observation.contradiction_pressure,
        corroboration_depth=observation.corroboration_depth,
        extraction_confidence=observation.extraction_confidence,
        missing_field_count=observation.missing_field_count,
        deadline_seconds=deadline_seconds,
        breach_score=_breach_score(
            reason_codes=reason_codes,
            latency_ratio=latency_ratio,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _latest_verification_age_seconds(
    observation: ResearchSourceClaimUpdateLatencyObservation,
    generated_at: datetime,
    config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> Decimal:
    if observation.latest_verified_at is None:
        with localcontext(_DECIMAL_CONTEXT):
            return _quantize(
                observation.expected_update_cadence_seconds
                * config.block_latency_ratio,
            )
    return _elapsed_seconds(observation.latest_verified_at, generated_at)


def _deadline_seconds(
    observation: ResearchSourceClaimUpdateLatencyObservation,
    generated_at: datetime,
) -> Decimal:
    if observation.deadline_at is None:
        return _ZERO
    return _elapsed_seconds(generated_at, observation.deadline_at)


def _row_reason_codes(
    *,
    latest_verification_age_seconds: Decimal,
    latency_ratio: Decimal,
    source_authority_score: Decimal,
    contradiction_pressure: Decimal,
    corroboration_depth: Decimal,
    extraction_confidence: Decimal,
    missing_field_count: Decimal,
    deadline_seconds: Decimal,
    config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_high_threshold_reason(
        reason_codes,
        prefix="update_latency",
        value=latency_ratio,
        watch_threshold=config.watch_latency_ratio,
        block_threshold=config.block_latency_ratio,
    )
    _append_low_threshold_reason(
        reason_codes,
        prefix="source_authority",
        value=source_authority_score,
        watch_threshold=config.watch_source_authority_score,
        block_threshold=config.block_source_authority_score,
    )
    _append_high_threshold_reason(
        reason_codes,
        prefix="contradiction_pressure",
        value=contradiction_pressure,
        watch_threshold=config.watch_contradiction_pressure,
        block_threshold=config.block_contradiction_pressure,
    )
    _append_low_threshold_reason(
        reason_codes,
        prefix="corroboration_depth",
        value=corroboration_depth,
        watch_threshold=config.watch_corroboration_depth,
        block_threshold=config.block_corroboration_depth,
    )
    _append_low_threshold_reason(
        reason_codes,
        prefix="extraction_confidence",
        value=extraction_confidence,
        watch_threshold=config.watch_extraction_confidence,
        block_threshold=config.block_extraction_confidence,
    )
    _append_high_threshold_reason(
        reason_codes,
        prefix="missing_fields",
        value=missing_field_count,
        watch_threshold=config.watch_missing_field_count,
        block_threshold=config.block_missing_field_count,
    )
    _append_low_threshold_reason(
        reason_codes,
        prefix="deadline_proximity",
        value=deadline_seconds,
        watch_threshold=config.watch_deadline_seconds,
        block_threshold=config.block_deadline_seconds,
    )
    if latest_verification_age_seconds == _ZERO and "update_latency_watch" in reason_codes:
        reason_codes.remove("update_latency_watch")
    if not reason_codes:
        reason_codes.append("claim_update_latency_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_high_threshold_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value >= watch_threshold:
        reason_codes.append(f"{prefix}_watch")


def _append_low_threshold_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value <= block_threshold:
        reason_codes.append(f"{prefix}_block")
    elif value <= watch_threshold:
        reason_codes.append(f"{prefix}_watch")


def _breach_score(
    *,
    reason_codes: tuple[str, ...],
    latency_ratio: Decimal,
    config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> Decimal:
    if reason_codes == ("claim_update_latency_pass",):
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        severity_total = _ZERO
        for reason_code in reason_codes:
            severity_total += (
                _ONE
                if reason_code.endswith("_block")
                else Decimal("0.500000")
                if reason_code.endswith("_watch")
                else _ZERO
            )
        severity_score = severity_total / Decimal("7")
        latency_excess = _clamp_ratio(
            (latency_ratio - config.watch_latency_ratio)
            / (config.block_latency_ratio - config.watch_latency_ratio),
        )
        return _clamp_ratio(
            severity_score + (latency_excess / Decimal("6.222222")),
        )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceClaimUpdateLatencyBreachRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimUpdateLatencyBreachRow, ...],
) -> tuple[str, ...]:
    if all(row.status == "pass" for row in rows):
        return ("claim_update_latency_pass",)
    return _normalize_reason_codes(
        tuple(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != "claim_update_latency_pass"
        ),
    )


def _status_count(
    rows: tuple[ResearchSourceClaimUpdateLatencyBreachRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchSourceClaimUpdateLatencyBreachRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        _STATUS_RANK[row.status],
        row.breach_score.copy_negate(),
        row.latency_ratio.copy_negate(),
        row.latest_verification_age_seconds.copy_negate(),
        row.deadline_seconds,
        row.claim_bucket,
    )


def _validate_row_consistency(
    row: ResearchSourceClaimUpdateLatencyBreachRow,
    config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> None:
    with localcontext(_DECIMAL_CONTEXT):
        expected_ratio = _quantize(
            row.latest_verification_age_seconds
            / row.expected_update_cadence_seconds,
        )
    if row.latency_ratio != expected_ratio:
        raise ValueError("latency_ratio must match cadence and latest verification age")
    expected_reason_codes = _row_reason_codes(
        latest_verification_age_seconds=row.latest_verification_age_seconds,
        latency_ratio=row.latency_ratio,
        source_authority_score=row.source_authority_score,
        contradiction_pressure=row.contradiction_pressure,
        corroboration_depth=row.corroboration_depth,
        extraction_confidence=row.extraction_confidence,
        missing_field_count=row.missing_field_count,
        deadline_seconds=row.deadline_seconds,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(expected_reason_codes):
        raise ValueError("status must match reason_codes")
    expected_breach_score = _breach_score(
        reason_codes=expected_reason_codes,
        latency_ratio=row.latency_ratio,
        config=config,
    )
    if row.breach_score != expected_breach_score:
        raise ValueError("breach_score must match row inputs")


def _validate_report_consistency(
    report: ResearchSourceClaimUpdateLatencyBreachReport,
    config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> None:
    _reject_empty_rows(report.rows)
    for row in report.rows:
        _validate_row_consistency(row, config)
    if report.claim_bucket_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_bucket_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_latest_verification_age_seconds != max(
        (row.latest_verification_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_latest_verification_age_seconds must match rows")
    if report.max_latency_ratio != max((row.latency_ratio for row in report.rows), default=_ZERO):
        raise ValueError("max_latency_ratio must match rows")
    if report.max_contradiction_pressure != max(
        (row.contradiction_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.min_extraction_confidence != min(
        (row.extraction_confidence for row in report.rows),
        default=_ONE,
    ):
        raise ValueError("min_extraction_confidence must match rows")
    if report.min_deadline_seconds != min(
        (row.deadline_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_deadline_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    claim_buckets = tuple(row.claim_bucket for row in report.rows)
    if len(claim_buckets) != len(set(claim_buckets)):
        raise ValueError("rows must contain unique claim_bucket values")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")


def _normalize_observations(
    observations: Sequence[ResearchSourceClaimUpdateLatencyObservation],
) -> tuple[ResearchSourceClaimUpdateLatencyObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceClaimUpdateLatencyObservation] = []
    seen: set[str] = set()
    for item in observations:
        revalidated = _revalidate_observation(item)
        if revalidated.claim_bucket in seen:
            raise ValueError("observations must contain unique claim_bucket values")
        seen.add(revalidated.claim_bucket)
        normalized.append(revalidated)
    return tuple(sorted(normalized, key=lambda item: item.claim_bucket))


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimUpdateLatencyBreachRow],
    validation_config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> tuple[ResearchSourceClaimUpdateLatencyBreachRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimUpdateLatencyBreachRow] = []
    for row in rows:
        normalized.append(_revalidate_row(row, validation_config))
    return tuple(sorted(normalized, key=_row_sort_key))


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
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _reject_empty_observations(
    observations: tuple[ResearchSourceClaimUpdateLatencyObservation, ...],
) -> None:
    if not observations:
        raise ValueError("observations must not be empty")


def _reject_empty_rows(rows: tuple[ResearchSourceClaimUpdateLatencyBreachRow, ...]) -> None:
    if not rows:
        raise ValueError("rows must not be empty")


def _reject_future_time(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")


def _normalize_validation_config(
    value: ResearchSourceClaimUpdateLatencyBreachConfig | None,
) -> ResearchSourceClaimUpdateLatencyBreachConfig:
    if value is None:
        return ResearchSourceClaimUpdateLatencyBreachConfig()
    return _revalidate_config(value, label="validation_config")


def _revalidate_config(
    value: ResearchSourceClaimUpdateLatencyBreachConfig,
    *,
    label: str,
) -> ResearchSourceClaimUpdateLatencyBreachConfig:
    if type(value) is not ResearchSourceClaimUpdateLatencyBreachConfig:
        raise ValueError(
            f"{label} must be a ResearchSourceClaimUpdateLatencyBreachConfig",
        )
    return ResearchSourceClaimUpdateLatencyBreachConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)}
    )


def _revalidate_observation(
    value: ResearchSourceClaimUpdateLatencyObservation,
) -> ResearchSourceClaimUpdateLatencyObservation:
    if type(value) is not ResearchSourceClaimUpdateLatencyObservation:
        raise ValueError(
            "observations must contain ResearchSourceClaimUpdateLatencyObservation values",
        )
    return ResearchSourceClaimUpdateLatencyObservation(
        **{field.name: getattr(value, field.name) for field in fields(value)}
    )


def _revalidate_row(
    value: ResearchSourceClaimUpdateLatencyBreachRow,
    validation_config: ResearchSourceClaimUpdateLatencyBreachConfig,
) -> ResearchSourceClaimUpdateLatencyBreachRow:
    if type(value) is not ResearchSourceClaimUpdateLatencyBreachRow:
        raise ValueError(
            "rows must contain ResearchSourceClaimUpdateLatencyBreachRow values",
        )
    return ResearchSourceClaimUpdateLatencyBreachRow(
        **{field.name: getattr(value, field.name) for field in fields(value)},
        validation_config=validation_config,
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_watch_before_block_high(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"block_{field_name} must be greater than or equal to watch")


def _require_watch_before_block_low(
    field_name: str,
    watch_value: Decimal,
    block_value: Decimal,
) -> None:
    if block_value > watch_value:
        raise ValueError(f"block_{field_name} must be less than or equal to watch")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize(raw)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must remain positive after quantization")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    with localcontext(_DECIMAL_CONTEXT):
        return raw.quantize(_COUNT_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        return Decimal(value).quantize(_COUNT_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if value >= _ONE:
        return _ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        try:
            return value.quantize(_QUANT)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must fit the fixed decimal context") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _elapsed_seconds(started_at: datetime, ended_at: datetime) -> Decimal:
    elapsed = ended_at - started_at
    if elapsed.days < 0:
        raise ValueError("elapsed seconds must be nonnegative")
    elapsed_microseconds = (
        ((elapsed.days * 86400) + elapsed.seconds) * 1000000
    ) + elapsed.microseconds
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(Decimal(elapsed_microseconds) / Decimal("1000000"))


def _report_values_without_digest(
    report: ResearchSourceClaimUpdateLatencyBreachReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
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
        if value.is_zero() and value.is_signed():
            raise ValueError("Decimal payload value must not be signed zero")
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
    allow_json_containers: bool = True,
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


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_UPDATE_LATENCY_BREACH_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceClaimUpdateLatencyBreachConfig",
    "ResearchSourceClaimUpdateLatencyBreachReport",
    "ResearchSourceClaimUpdateLatencyBreachRow",
    "ResearchSourceClaimUpdateLatencyObservation",
    "build_research_source_claim_update_latency_breach_report",
    "research_source_claim_update_latency_breach_report_payload",
    "validate_research_source_claim_update_latency_breach_public_payload",
)
