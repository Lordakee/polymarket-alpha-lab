"""Report-only digest for market event resolution dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


DEFAULT_MARKET_EVENT_RESOLUTION_DEPENDENCY_DIGEST_CONFIG_VERSION = (
    "market-event-resolution-dependency-digest-v0"
)
PASS_REASON_CODE = "market_event_resolution_dependency_digest_passed"
REDACTED_REFERENCE = "<redacted>"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
DECIMAL_PLACES = Decimal("0.000001")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "dependent_condition_count",
    "upstream_event_count",
    "unresolved_authority_count",
    "unresolved_authority_mappings",
    "shared_evidence_chain_gap_count",
    "lag_pressure_count",
    "max_lag_seconds",
    "mean_lag_seconds",
    "dependency_rows",
    "redacted_evidence_references",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS = (
    "api_key",
    "author" + "ization",
    "credential",
    "private" + "_key",
    "signing",
)
UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS = (
    "account",
    "auth",
    "balance",
    "cancel",
    "credential",
    "database",
    "live",
    "network",
    "or" + "der",
    "persist",
    "secret",
    "sign",
    "submit",
    "token",
    "tra" + "de",
    "wal" + "let",
)

__all__ = (
    "DEFAULT_MARKET_EVENT_RESOLUTION_DEPENDENCY_DIGEST_CONFIG_VERSION",
    "MarketEventResolutionDependencyConfig",
    "MarketEventResolutionDependencyInput",
    "MarketEventResolutionDependencyReport",
    "build_market_event_resolution_dependency_digest",
    "market_event_resolution_dependency_digest_payload",
)


@dataclass(frozen=True)
class MarketEventResolutionDependencyConfig:
    config_version: str = DEFAULT_MARKET_EVENT_RESOLUTION_DEPENDENCY_DIGEST_CONFIG_VERSION
    lag_warning_seconds: Decimal = Decimal("3600")
    lag_blocking_seconds: Decimal = Decimal("7200")
    min_evidence_chain_link_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventResolutionDependencyConfig:
            raise TypeError(
                "MarketEventResolutionDependencyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventResolutionDependencyConfig:
            raise ValueError(
                "config must be exactly MarketEventResolutionDependencyConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "lag_warning_seconds",
            _normalize_nonnegative_decimal(
                "lag_warning_seconds",
                self.lag_warning_seconds,
            ),
        )
        object.__setattr__(
            self,
            "lag_blocking_seconds",
            _normalize_nonnegative_decimal(
                "lag_blocking_seconds",
                self.lag_blocking_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_evidence_chain_link_count",
            _normalize_nonnegative_decimal(
                "min_evidence_chain_link_count",
                self.min_evidence_chain_link_count,
            ),
        )
        if self.lag_blocking_seconds < self.lag_warning_seconds:
            raise ValueError("lag_blocking_seconds must be >= lag_warning_seconds")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventResolutionDependencyInput:
    dependent_condition_id: str
    upstream_event_key: str
    authority_key: str
    authority_resolved: bool
    evidence_chain_keys: tuple[str, ...]
    upstream_resolved_at: datetime | None = None
    dependent_last_checked_at: datetime | None = None
    evidence_references: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventResolutionDependencyInput:
            raise TypeError(
                "MarketEventResolutionDependencyInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventResolutionDependencyInput:
            raise ValueError(
                "dependency input must be exactly MarketEventResolutionDependencyInput",
            )
        _require_canonical_string("dependent_condition_id", self.dependent_condition_id)
        _require_canonical_string("upstream_event_key", self.upstream_event_key)
        _require_canonical_string("authority_key", self.authority_key)
        if type(self.authority_resolved) is not bool:
            raise ValueError("authority_resolved must be a bool")
        object.__setattr__(
            self,
            "evidence_chain_keys",
            _normalize_string_tuple("evidence_chain_keys", self.evidence_chain_keys),
        )
        object.__setattr__(
            self,
            "upstream_resolved_at",
            _normalize_optional_utc("upstream_resolved_at", self.upstream_resolved_at),
        )
        object.__setattr__(
            self,
            "dependent_last_checked_at",
            _normalize_optional_utc(
                "dependent_last_checked_at",
                self.dependent_last_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "evidence_references",
            _normalize_sensitive_references(
                "evidence_references",
                self.evidence_references,
            ),
        )
        _require_hard_flags("dependency input", self)


@dataclass(frozen=True)
class MarketEventResolutionDependencyReport:
    generated_at: datetime
    config_version: str
    dependent_condition_count: Decimal
    upstream_event_count: Decimal
    unresolved_authority_count: Decimal
    unresolved_authority_mappings: tuple[tuple[str, tuple[str, ...]], ...]
    shared_evidence_chain_gap_count: Decimal
    lag_pressure_count: Decimal
    max_lag_seconds: Decimal
    mean_lag_seconds: Decimal
    dependency_rows: tuple[
        tuple[str, str, Decimal, Decimal, Decimal, tuple[str, ...]],
        ...
    ]
    redacted_evidence_references: tuple[tuple[str, tuple[str, ...]], ...]
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketEventResolutionDependencyReport:
            raise TypeError(
                "MarketEventResolutionDependencyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketEventResolutionDependencyReport:
            raise ValueError(
                "report must be exactly MarketEventResolutionDependencyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "dependent_condition_count",
            "upstream_event_count",
            "unresolved_authority_count",
            "shared_evidence_chain_gap_count",
            "lag_pressure_count",
            "max_lag_seconds",
            "mean_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_authority_mappings",
            _normalize_authority_mappings(self.unresolved_authority_mappings),
        )
        object.__setattr__(
            self,
            "dependency_rows",
            _normalize_dependency_rows(self.dependency_rows),
        )
        object.__setattr__(
            self,
            "redacted_evidence_references",
            _normalize_redacted_references(self.redacted_evidence_references),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_market_event_resolution_dependency_digest(
    dependencies: tuple[MarketEventResolutionDependencyInput, ...],
    *,
    config: MarketEventResolutionDependencyConfig,
    generated_at: datetime,
) -> MarketEventResolutionDependencyReport:
    if type(config) is not MarketEventResolutionDependencyConfig:
        raise ValueError("config must be a MarketEventResolutionDependencyConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_dependencies(dependencies)

    upstream_event_keys = frozenset(row.upstream_event_key for row in rows)
    unresolved_authority_mappings = _unresolved_authority_mappings(rows)
    shared_evidence_chain_gap_count = _count_decimal(
        sum(
            1
            for row in rows
            if Decimal(len(row.evidence_chain_keys))
            < config.min_evidence_chain_link_count
        ),
    )
    lag_values = tuple(_lag_seconds(row, generated_at_utc) for row in rows)
    lag_pressure_count = _count_decimal(
        sum(1 for lag_value in lag_values if lag_value >= config.lag_blocking_seconds),
    )
    max_lag_seconds = max(lag_values, default=ZERO)
    pressure_lag_values = tuple(
        lag_value if lag_value >= config.lag_blocking_seconds else ZERO
        for lag_value in lag_values
    )
    mean_lag_seconds = (
        _quantized(sum(pressure_lag_values, ZERO) / Decimal(len(pressure_lag_values)))
        if pressure_lag_values
        else _quantized(ZERO)
    )
    reason_codes = _report_reason_codes(
        unresolved_authority_count=_count_decimal(
            sum(1 for row in rows if not row.authority_resolved),
        ),
        shared_evidence_chain_gap_count=shared_evidence_chain_gap_count,
        lag_pressure_count=lag_pressure_count,
        max_lag_seconds=max_lag_seconds,
        config=config,
    )

    return MarketEventResolutionDependencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        dependent_condition_count=_count_decimal(len(rows)),
        upstream_event_count=_count_decimal(len(upstream_event_keys)),
        unresolved_authority_count=_count_decimal(
            sum(1 for row in rows if not row.authority_resolved),
        ),
        unresolved_authority_mappings=unresolved_authority_mappings,
        shared_evidence_chain_gap_count=shared_evidence_chain_gap_count,
        lag_pressure_count=lag_pressure_count,
        max_lag_seconds=_quantized(max_lag_seconds),
        mean_lag_seconds=mean_lag_seconds,
        dependency_rows=_dependency_rows(rows, generated_at_utc),
        redacted_evidence_references=_redacted_references(rows),
        status=_report_status(reason_codes),
        reason_codes=reason_codes,
    )


def market_event_resolution_dependency_digest_payload(
    report: MarketEventResolutionDependencyReport | dict[str, object],
) -> dict[str, Any]:
    if type(report) is MarketEventResolutionDependencyReport:
        _require_hard_flags("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _reject_unsafe_public_payload("report payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a MarketEventResolutionDependencyReport")


def _normalize_dependencies(
    dependencies: object,
) -> tuple[MarketEventResolutionDependencyInput, ...]:
    if type(dependencies) is not tuple:
        raise ValueError("dependencies must be a tuple")
    rows = tuple(dependencies)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketEventResolutionDependencyInput:
            raise ValueError("dependencies must contain exact dependency inputs")
        _require_hard_flags("dependency input", row)
        key = (row.upstream_event_key, row.authority_key, row.dependent_condition_id)
        if key in seen_keys:
            raise ValueError("dependencies must contain unique dependency keys")
        seen_keys.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.upstream_event_key,
                row.authority_key,
                row.dependent_condition_id,
            ),
        ),
    )


def _unresolved_authority_mappings(
    rows: tuple[MarketEventResolutionDependencyInput, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    by_event: dict[str, set[str]] = {}
    for row in rows:
        if row.authority_resolved:
            continue
        by_event.setdefault(row.upstream_event_key, set()).add(row.authority_key)
    return tuple(
        (event_key, tuple(sorted(authority_keys)))
        for event_key, authority_keys in sorted(by_event.items())
    )


def _dependency_rows(
    rows: tuple[MarketEventResolutionDependencyInput, ...],
    generated_at: datetime,
) -> tuple[tuple[str, str, Decimal, Decimal, Decimal, tuple[str, ...]], ...]:
    grouped: dict[tuple[str, str], list[MarketEventResolutionDependencyInput]] = {}
    for row in rows:
        grouped.setdefault((row.upstream_event_key, row.authority_key), []).append(row)

    digest_rows: list[tuple[str, str, Decimal, Decimal, Decimal, tuple[str, ...]]] = []
    for (upstream_event_key, authority_key), items in sorted(grouped.items()):
        condition_ids = tuple(sorted(row.dependent_condition_id for row in items))
        unresolved_count = _count_decimal(
            sum(1 for row in items if not row.authority_resolved),
        )
        max_lag_seconds = max((_lag_seconds(row, generated_at) for row in items), default=ZERO)
        digest_rows.append(
            (
                upstream_event_key,
                authority_key,
                _count_decimal(len(items)),
                unresolved_count,
                _quantized(max_lag_seconds),
                condition_ids,
            ),
        )
    return tuple(digest_rows)


def _redacted_references(
    rows: tuple[MarketEventResolutionDependencyInput, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (
            row.dependent_condition_id,
            tuple(REDACTED_REFERENCE for _reference in row.evidence_references),
        )
        for row in sorted(rows, key=lambda item: item.dependent_condition_id)
    )


def _lag_seconds(
    row: MarketEventResolutionDependencyInput,
    generated_at: datetime,
) -> Decimal:
    if row.upstream_resolved_at is None:
        return _quantized(ZERO)
    if generated_at < row.upstream_resolved_at:
        return _quantized(ZERO)
    return _quantized(
        Decimal(str((generated_at - row.upstream_resolved_at).total_seconds())),
    )


def _report_reason_codes(
    *,
    unresolved_authority_count: Decimal,
    shared_evidence_chain_gap_count: Decimal,
    lag_pressure_count: Decimal,
    max_lag_seconds: Decimal,
    config: MarketEventResolutionDependencyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if unresolved_authority_count > ZERO:
        reason_codes.append("unresolved_authority_mapping")
    if shared_evidence_chain_gap_count > ZERO:
        reason_codes.append("shared_evidence_chain_gap")
    if lag_pressure_count > ZERO:
        reason_codes.append("lag_pressure_blocking")
    elif max_lag_seconds >= config.lag_warning_seconds and max_lag_seconds > ZERO:
        reason_codes.append("lag_pressure_watch")
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(reason_codes))


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if "lag_pressure_blocking" in reason_codes or "unresolved_authority_mapping" in reason_codes:
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _validate_report_consistency(
    report: MarketEventResolutionDependencyReport,
) -> None:
    if report.status == "pass" and report.reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass report must use pass reason code")
    if report.status != "pass" and PASS_REASON_CODE in report.reason_codes:
        raise ValueError("non-pass report cannot use pass reason code")
    if report.unresolved_authority_count == ZERO and report.unresolved_authority_mappings:
        raise ValueError("unresolved_authority_mappings must match unresolved count")
    if report.unresolved_authority_count > ZERO and not report.unresolved_authority_mappings:
        raise ValueError("unresolved_authority_mappings must match unresolved count")
    if report.dependent_condition_count == ZERO:
        if report.dependency_rows:
            raise ValueError("dependency_rows must match dependency count")
    elif not report.dependency_rows:
        raise ValueError("dependency_rows must match dependency count")


def _report_public_payload_values(
    report: MarketEventResolutionDependencyReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "dependent_condition_count": _decimal_payload(report.dependent_condition_count),
        "upstream_event_count": _decimal_payload(report.upstream_event_count),
        "unresolved_authority_count": _decimal_payload(
            report.unresolved_authority_count,
        ),
        "unresolved_authority_mappings": [
            [event_key, list(authority_keys)]
            for event_key, authority_keys in report.unresolved_authority_mappings
        ],
        "shared_evidence_chain_gap_count": _decimal_payload(
            report.shared_evidence_chain_gap_count,
        ),
        "lag_pressure_count": _decimal_payload(report.lag_pressure_count),
        "max_lag_seconds": _decimal_payload(report.max_lag_seconds),
        "mean_lag_seconds": _decimal_payload(report.mean_lag_seconds),
        "dependency_rows": [
            [
                upstream_event_key,
                authority_key,
                _decimal_payload(dependent_condition_count),
                _decimal_payload(unresolved_authority_count),
                _decimal_payload(max_lag_seconds),
                list(condition_ids),
            ]
            for (
                upstream_event_key,
                authority_key,
                dependent_condition_count,
                unresolved_authority_count,
                max_lag_seconds,
                condition_ids,
            ) in report.dependency_rows
        ],
        "redacted_evidence_references": [
            [condition_id, list(references)]
            for condition_id, references in report.redacted_evidence_references
        ],
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: MarketEventResolutionDependencyReport,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: MarketEventResolutionDependencyReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return hashlib.sha256(
        ("market_event_resolution_dependency_digest_derived|" + "|".join(values)).encode(
            "utf-8",
        ),
    ).hexdigest()


def _digest_payload_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        encoded_items = tuple(_digest_payload_value(item) for item in value)
        return (
            "list:"
            + str(len(encoded_items))
            + ":"
            + "".join(f"{len(item)}:{item}" for item in encoded_items)
        )
    if type(value) is bool:
        return "bool:true" if value else "bool:false"
    string_value = str(value)
    return f"str:{len(string_value)}:{string_value}"


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    for field_name in (
        "dependent_condition_count",
        "upstream_event_count",
        "unresolved_authority_count",
        "shared_evidence_chain_gap_count",
        "lag_pressure_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in ("max_lag_seconds", "mean_lag_seconds"):
        _require_decimal_payload_string(field_name, payload[field_name], places=True)
    _validate_public_authority_mappings(payload["unresolved_authority_mappings"])
    _validate_public_dependency_rows(payload["dependency_rows"])
    _validate_public_redacted_references(payload["redacted_evidence_references"])
    _require_status("status", payload["status"])
    reason_codes = _validate_public_reason_codes(payload["reason_codes"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    if payload["status"] == "pass" and reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass payload must use pass reason code")
    if payload["status"] != "pass" and PASS_REASON_CODE in reason_codes:
        raise ValueError("non-pass payload cannot use pass reason code")


def _validate_public_authority_mappings(value: object) -> None:
    if type(value) is not list:
        raise ValueError("unresolved_authority_mappings must be a list")
    previous_event_key: str | None = None
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("unresolved_authority_mappings must contain pairs")
        event_key, authority_keys = item
        _require_canonical_string("unresolved_authority_mappings", event_key)
        _validate_public_string_list("unresolved_authority_mappings", authority_keys)
        if previous_event_key is not None and event_key <= previous_event_key:
            raise ValueError("unresolved_authority_mappings must be deterministic")
        previous_event_key = event_key


def _validate_public_dependency_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("dependency_rows must be a list")
    previous_key: tuple[str, str] | None = None
    for item in value:
        if type(item) is not list or len(item) != 6:
            raise ValueError("dependency_rows must contain dependency rows")
        (
            upstream_event_key,
            authority_key,
            dependent_condition_count,
            unresolved_authority_count,
            max_lag_seconds,
            condition_ids,
        ) = item
        _require_canonical_string("dependency_rows", upstream_event_key)
        _require_canonical_string("dependency_rows", authority_key)
        key = (upstream_event_key, authority_key)
        if previous_key is not None and key <= previous_key:
            raise ValueError("dependency_rows must be deterministic")
        previous_key = key
        _require_decimal_payload_string(
            "dependency_rows",
            dependent_condition_count,
            whole=True,
        )
        _require_decimal_payload_string(
            "dependency_rows",
            unresolved_authority_count,
            whole=True,
        )
        _require_decimal_payload_string("dependency_rows", max_lag_seconds, places=True)
        _validate_public_string_list("dependency_rows", condition_ids)


def _validate_public_redacted_references(value: object) -> None:
    if type(value) is not list:
        raise ValueError("redacted_evidence_references must be a list")
    previous_condition_id: str | None = None
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("redacted_evidence_references must contain pairs")
        condition_id, references = item
        _require_canonical_string("redacted_evidence_references", condition_id)
        normalized_references = _validate_public_string_list(
            "redacted_evidence_references",
            references,
        )
        if any(reference != REDACTED_REFERENCE for reference in normalized_references):
            raise ValueError("redacted_evidence_references must be redacted")
        if previous_condition_id is not None and condition_id <= previous_condition_id:
            raise ValueError("redacted_evidence_references must be deterministic")
        previous_condition_id = condition_id


def _validate_public_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _validate_public_string_list("reason_codes", value)
    if not reason_codes:
        raise ValueError("reason_codes is required")
    return reason_codes


def _validate_public_string_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    previous: str | None = None
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        if previous is not None and item <= previous:
            raise ValueError(f"{field_name} must be sorted")
        previous = item
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(normalized)


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    whole: bool = False,
    places: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite() or decimal_value < ZERO:
        raise ValueError(f"{field_name} must be a finite nonnegative Decimal string")
    if format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    if places and decimal_value.quantize(DECIMAL_PLACES) != decimal_value:
        raise ValueError(f"{field_name} must be a six-place Decimal-derived string")
    return decimal_value


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_authority_mappings(
    value: object,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if type(value) is not tuple:
        raise ValueError("unresolved_authority_mappings must be a tuple")
    rows: list[tuple[str, tuple[str, ...]]] = []
    previous_event_key: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("unresolved_authority_mappings must contain pairs")
        event_key, authority_keys = item
        _require_canonical_string("unresolved_authority_mappings", event_key)
        normalized_keys = _normalize_string_tuple(
            "unresolved_authority_mappings",
            authority_keys,
        )
        if previous_event_key is not None and event_key <= previous_event_key:
            raise ValueError("unresolved_authority_mappings must be deterministic")
        previous_event_key = event_key
        rows.append((event_key, normalized_keys))
    return tuple(rows)


def _normalize_dependency_rows(
    value: object,
) -> tuple[tuple[str, str, Decimal, Decimal, Decimal, tuple[str, ...]], ...]:
    if type(value) is not tuple:
        raise ValueError("dependency_rows must be a tuple")
    rows: list[tuple[str, str, Decimal, Decimal, Decimal, tuple[str, ...]]] = []
    previous_key: tuple[str, str] | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 6:
            raise ValueError("dependency_rows must contain dependency tuples")
        (
            upstream_event_key,
            authority_key,
            dependent_condition_count,
            unresolved_authority_count,
            max_lag_seconds,
            condition_ids,
        ) = item
        _require_canonical_string("dependency_rows", upstream_event_key)
        _require_canonical_string("dependency_rows", authority_key)
        key = (upstream_event_key, authority_key)
        if previous_key is not None and key <= previous_key:
            raise ValueError("dependency_rows must be deterministic")
        previous_key = key
        rows.append(
            (
                upstream_event_key,
                authority_key,
                _normalize_nonnegative_decimal(
                    "dependency_rows",
                    dependent_condition_count,
                ),
                _normalize_nonnegative_decimal(
                    "dependency_rows",
                    unresolved_authority_count,
                ),
                _normalize_nonnegative_decimal("dependency_rows", max_lag_seconds),
                _normalize_string_tuple("dependency_rows", condition_ids),
            ),
        )
    return tuple(rows)


def _normalize_redacted_references(
    value: object,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if type(value) is not tuple:
        raise ValueError("redacted_evidence_references must be a tuple")
    rows: list[tuple[str, tuple[str, ...]]] = []
    previous_condition_id: str | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("redacted_evidence_references must contain pairs")
        condition_id, references = item
        _require_canonical_string("redacted_evidence_references", condition_id)
        normalized_references = _normalize_string_tuple(
            "redacted_evidence_references",
            references,
        )
        if any(reference != REDACTED_REFERENCE for reference in normalized_references):
            raise ValueError("redacted_evidence_references must be redacted")
        if previous_condition_id is not None and condition_id <= previous_condition_id:
            raise ValueError("redacted_evidence_references must be deterministic")
        previous_condition_id = condition_id
        rows.append((condition_id, normalized_references))
    return tuple(rows)


def _normalize_sensitive_references(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    references = _normalize_string_tuple(field_name, value)
    for reference in references:
        if not _is_sensitive_reference(reference):
            raise ValueError(f"{field_name} must contain sensitive references")
    return references


def _is_sensitive_reference(value: str) -> bool:
    normalized = value.lower()
    return any(
        fragment in normalized
        for fragment in (
            "://",
            "token=",
            "api_key=",
            "secret",
            "authorization",
            "bearer ",
            "wallet",
            "account",
        )
    )


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(value)
    previous: str | None = None
    seen: set[str] = set()
    for item in normalized:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and item <= previous:
            raise ValueError(f"{field_name} must be sorted")
        previous = item
        seen.add(item)
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    reason_codes = _normalize_string_tuple("reason_codes", value)
    if not reason_codes:
        raise ValueError("reason_codes is required")
    return reason_codes


def _normalize_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < ZERO:
        raise ValueError(f"{field_name} must be a finite nonnegative Decimal")
    return value


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _quantized(value: Decimal) -> Decimal:
    return _normalize_nonnegative_decimal("decimal", value).quantize(DECIMAL_PLACES)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_nonnegative_decimal("payload decimal", value), "f")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if type(value) is str:
        if _is_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) in (Decimal, float, int):
        raise ValueError(f"{path or label} must use Decimal-derived strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_public_text(key):
                raise ValueError(f"unsafe field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) not in (bool, type(None)):
        raise ValueError(f"{path or label} is not public-payload serializable")


def _is_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS):
        return True
    tokens = _surface_text_tokens(normalized)
    return any(token in tokens for token in UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS)


def _surface_text_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)
