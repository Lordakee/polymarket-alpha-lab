"""Pure report-only SLA buckets for source-authority contradiction rechecks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any
import weakref


DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_REPORT_CONFIG_VERSION = (
    "research-source-authority-contradiction-recheck-sla-report-v0"
)
RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_STATUSES = (
    "pass",
    "watch",
    "block",
)
RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_BUCKETS = (
    "routine",
    "accelerated",
    "immediate",
)

EMPTY_REASON = "source_authority_contradiction_recheck_sla_empty"
CLEAR_REASON = "source_authority_contradiction_recheck_sla_clear"
CONTRADICTION_SEVERITY_WATCH_REASON = "contradiction_severity_watch"
CONTRADICTION_SEVERITY_BLOCK_REASON = "contradiction_severity_block"
AUTHORITY_TIER_GAP_WATCH_REASON = "authority_tier_gap_watch"
AUTHORITY_TIER_GAP_BLOCK_REASON = "authority_tier_gap_block"
LAST_CHECKED_AGE_WATCH_REASON = "last_checked_age_watch"
LAST_CHECKED_AGE_BLOCK_REASON = "last_checked_age_block"
RESOLUTION_PROXIMITY_WATCH_REASON = "resolution_proximity_watch"
RESOLUTION_PROXIMITY_BLOCK_REASON = "resolution_proximity_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    CONTRADICTION_SEVERITY_BLOCK_REASON,
    AUTHORITY_TIER_GAP_BLOCK_REASON,
    LAST_CHECKED_AGE_BLOCK_REASON,
    RESOLUTION_PROXIMITY_BLOCK_REASON,
    CONTRADICTION_SEVERITY_WATCH_REASON,
    AUTHORITY_TIER_GAP_WATCH_REASON,
    LAST_CHECKED_AGE_WATCH_REASON,
    RESOLUTION_PROXIMITY_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason
    for reason in REPORT_REASON_CODES
    if reason not in (EMPTY_REASON, CLEAR_REASON)
)
BLOCK_REASON_CODES = (
    CONTRADICTION_SEVERITY_BLOCK_REASON,
    AUTHORITY_TIER_GAP_BLOCK_REASON,
    LAST_CHECKED_AGE_BLOCK_REASON,
    RESOLUTION_PROXIMITY_BLOCK_REASON,
)

DECIMAL_PRECISION = 64
DECIMAL_CONTEXT = Context(prec=DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
REDACTED_PUBLIC_LABEL_PREFIX = "redacted"
REDACTED_PUBLIC_LABEL_HEX_LENGTH = 16
LOWERCASE_HEX_DIGITS = frozenset("0123456789abcdef")

_PUBLIC_SNAPSHOTS: dict[int, tuple[tuple[str, Any], ...]] = {}
_PUBLIC_SNAPSHOT_REFS: dict[int, weakref.ReferenceType[object]] = {}

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "recommend",
    "sizing",
    "notional",
    "position",
    "stake",
    "wallet",
    "account",
    "balance",
    "order",
    "trade",
    "execution",
    "broker",
    "private_key",
    "credential",
    "authentication",
    "secret",
    "api_key",
    "token",
    "password",
    "dsn",
    "database",
    "table",
    "network",
    "file_path",
    "source_url",
    "raw_url",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "file://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "private_key",
    "credential",
    "authentication",
    "secret",
    "api_key",
    "wallet",
    "order",
    "trade",
    "execution",
)


class _FinalPublicDataclass:
    __slots__ = ("__weakref__",)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True, slots=True)
class ResearchSourceAuthorityContradictionRecheckSlaConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_REPORT_CONFIG_VERSION
    )
    contradiction_watch_severity: Decimal = Decimal("0.350000")
    contradiction_block_severity: Decimal = Decimal("0.700000")
    authority_tier_gap_watch: Decimal = Decimal("1.000000")
    authority_tier_gap_block: Decimal = Decimal("2.000000")
    last_checked_watch_age_seconds: Decimal = Decimal("3600.000000")
    last_checked_block_age_seconds: Decimal = Decimal("14400.000000")
    resolution_watch_seconds_remaining: Decimal = Decimal("86400.000000")
    resolution_block_seconds_remaining: Decimal = Decimal("21600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchSourceAuthorityContradictionRecheckSlaConfig,
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "contradiction_watch_severity",
            "contradiction_block_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_tier_gap_watch",
            "authority_tier_gap_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "last_checked_watch_age_seconds",
            "last_checked_block_age_seconds",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_public_payload(_json_ready(self))
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchSourceAuthorityContradictionRecheckSlaInput(_FinalPublicDataclass):
    contradiction_bucket: str
    contradiction_severity: Decimal
    authority_tier_gap: Decimal
    last_checked_age_seconds: Decimal
    resolution_seconds_remaining: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchSourceAuthorityContradictionRecheckSlaInput,
        )
        object.__setattr__(
            self,
            "contradiction_bucket",
            _require_public_label(
                "contradiction_bucket",
                self.contradiction_bucket,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_severity",
            _require_ratio(
                "contradiction_severity",
                self.contradiction_severity,
            ),
        )
        object.__setattr__(
            self,
            "authority_tier_gap",
            _require_nonnegative_whole_decimal(
                "authority_tier_gap",
                self.authority_tier_gap,
            ),
        )
        for field_name in (
            "last_checked_age_seconds",
            "resolution_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_public_payload(_json_ready(self))
        _store_public_snapshot(self)


ResearchSourceAuthorityContradictionRecheckSlaSignal = (
    ResearchSourceAuthorityContradictionRecheckSlaInput
)


@dataclass(frozen=True, slots=True)
class ResearchSourceAuthorityContradictionRecheckSlaRow(_FinalPublicDataclass):
    contradiction_bucket: str
    contradiction_severity: Decimal
    authority_tier_gap: Decimal
    last_checked_age_seconds: Decimal
    resolution_seconds_remaining: Decimal
    recheck_sla_bucket: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchSourceAuthorityContradictionRecheckSlaRow,
        )
        object.__setattr__(
            self,
            "contradiction_bucket",
            _require_public_label(
                "contradiction_bucket",
                self.contradiction_bucket,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_severity",
            _require_ratio(
                "contradiction_severity",
                self.contradiction_severity,
            ),
        )
        object.__setattr__(
            self,
            "authority_tier_gap",
            _require_nonnegative_whole_decimal(
                "authority_tier_gap",
                self.authority_tier_gap,
            ),
        )
        for field_name in (
            "last_checked_age_seconds",
            "resolution_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_sla_bucket("recheck_sla_bucket", self.recheck_sla_bucket)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row_shape(self)
        _require_hard_flags("row", self)
        _reject_public_payload(_json_ready(self))
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount,
        )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_public_payload(_json_ready(self))
        _store_public_snapshot(self)


@dataclass(frozen=True, slots=True)
class ResearchSourceAuthorityContradictionRecheckSlaReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    contradiction_watch_severity: Decimal
    contradiction_block_severity: Decimal
    authority_tier_gap_watch: Decimal
    authority_tier_gap_block: Decimal
    last_checked_watch_age_seconds: Decimal
    last_checked_block_age_seconds: Decimal
    resolution_watch_seconds_remaining: Decimal
    resolution_block_seconds_remaining: Decimal
    contradiction_count: Decimal
    routine_recheck_count: Decimal
    accelerated_recheck_count: Decimal
    immediate_recheck_count: Decimal
    severe_contradiction_count: Decimal
    material_authority_tier_gap_count: Decimal
    stale_last_checked_count: Decimal
    near_resolution_count: Decimal
    highest_contradiction_severity: Decimal
    highest_authority_tier_gap: Decimal
    oldest_last_checked_age_seconds: Decimal
    nearest_resolution_seconds_remaining: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchSourceAuthorityContradictionRecheckSlaReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "contradiction_watch_severity",
            "contradiction_block_severity",
            "highest_contradiction_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_tier_gap_watch",
            "authority_tier_gap_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "highest_authority_tier_gap",
            _require_nonnegative_whole_decimal(
                "highest_authority_tier_gap",
                self.highest_authority_tier_gap,
            ),
        )
        for field_name in (
            "last_checked_watch_age_seconds",
            "last_checked_block_age_seconds",
            "resolution_watch_seconds_remaining",
            "resolution_block_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_count",
            "routine_recheck_count",
            "accelerated_recheck_count",
            "immediate_recheck_count",
            "severe_contradiction_count",
            "material_authority_tier_gap_count",
            "stale_last_checked_count",
            "near_resolution_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "oldest_last_checked_age_seconds",
            "nearest_resolution_seconds_remaining",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _require_or_set_digest(self)
        _reject_public_payload(_json_ready(self))
        _store_public_snapshot(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_authority_contradiction_recheck_sla_report_payload(
            self,
        )

    @property
    def digest(self) -> str:
        return research_source_authority_contradiction_recheck_sla_report_digest(
            self,
        )


_PUBLIC_REPORT_SCHEMA = (
    "generated_at",
    "config_version",
    "contradiction_watch_severity",
    "contradiction_block_severity",
    "authority_tier_gap_watch",
    "authority_tier_gap_block",
    "last_checked_watch_age_seconds",
    "last_checked_block_age_seconds",
    "resolution_watch_seconds_remaining",
    "resolution_block_seconds_remaining",
    "contradiction_count",
    "routine_recheck_count",
    "accelerated_recheck_count",
    "immediate_recheck_count",
    "severe_contradiction_count",
    "material_authority_tier_gap_count",
    "stale_last_checked_count",
    "near_resolution_count",
    "highest_contradiction_severity",
    "highest_authority_tier_gap",
    "oldest_last_checked_age_seconds",
    "nearest_resolution_seconds_remaining",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_ROW_SCHEMA = (
    "contradiction_bucket",
    "contradiction_severity",
    "authority_tier_gap",
    "last_checked_age_seconds",
    "resolution_seconds_remaining",
    "recheck_sla_bucket",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_REASON_CODE_COUNT_SCHEMA = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


def build_research_source_authority_contradiction_recheck_sla_report(
    inputs: list[ResearchSourceAuthorityContradictionRecheckSlaInput]
    | tuple[ResearchSourceAuthorityContradictionRecheckSlaInput, ...],
    *,
    config: ResearchSourceAuthorityContradictionRecheckSlaConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityContradictionRecheckSlaReport:
    if type(config) is not ResearchSourceAuthorityContradictionRecheckSlaConfig:
        raise ValueError(
            "config must be a "
            "ResearchSourceAuthorityContradictionRecheckSlaConfig",
        )
    supplied_config = config
    config = ResearchSourceAuthorityContradictionRecheckSlaConfig(
        **asdict(supplied_config),
    )
    _require_untampered_public_dataclass(supplied_config, "config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(input_value, config=config)
                for input_value in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceAuthorityContradictionRecheckSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        contradiction_watch_severity=config.contradiction_watch_severity,
        contradiction_block_severity=config.contradiction_block_severity,
        authority_tier_gap_watch=config.authority_tier_gap_watch,
        authority_tier_gap_block=config.authority_tier_gap_block,
        last_checked_watch_age_seconds=config.last_checked_watch_age_seconds,
        last_checked_block_age_seconds=config.last_checked_block_age_seconds,
        resolution_watch_seconds_remaining=config.resolution_watch_seconds_remaining,
        resolution_block_seconds_remaining=config.resolution_block_seconds_remaining,
        contradiction_count=_count(len(rows)),
        routine_recheck_count=_sla_bucket_count(rows, "routine"),
        accelerated_recheck_count=_sla_bucket_count(rows, "accelerated"),
        immediate_recheck_count=_sla_bucket_count(rows, "immediate"),
        severe_contradiction_count=_reason_count(
            rows,
            (
                CONTRADICTION_SEVERITY_WATCH_REASON,
                CONTRADICTION_SEVERITY_BLOCK_REASON,
            ),
        ),
        material_authority_tier_gap_count=_reason_count(
            rows,
            (
                AUTHORITY_TIER_GAP_WATCH_REASON,
                AUTHORITY_TIER_GAP_BLOCK_REASON,
            ),
        ),
        stale_last_checked_count=_reason_count(
            rows,
            (
                LAST_CHECKED_AGE_WATCH_REASON,
                LAST_CHECKED_AGE_BLOCK_REASON,
            ),
        ),
        near_resolution_count=_reason_count(
            rows,
            (
                RESOLUTION_PROXIMITY_WATCH_REASON,
                RESOLUTION_PROXIMITY_BLOCK_REASON,
            ),
        ),
        highest_contradiction_severity=max(
            (row.contradiction_severity for row in rows),
            default=ZERO,
        ),
        highest_authority_tier_gap=max(
            (row.authority_tier_gap for row in rows),
            default=ZERO,
        ),
        oldest_last_checked_age_seconds=max(
            (row.last_checked_age_seconds for row in rows),
            default=ZERO,
        ),
        nearest_resolution_seconds_remaining=min(
            (row.resolution_seconds_remaining for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_authority_contradiction_recheck_sla_report_payload(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> dict[str, Any]:
    payload = _validated_report_public_payload(
        report,
        verify_stored_digest=True,
    )
    return _freeze_json(payload)


def research_source_authority_contradiction_recheck_sla_report_digest(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> str:
    payload = _validated_report_public_payload(
        report,
        verify_stored_digest=False,
    )
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_source_authority_contradiction_recheck_sla_report_digest(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> None:
    _validated_report_public_payload(report, verify_stored_digest=True)


def validate_research_source_authority_contradiction_recheck_sla_public_payload(
    payload: dict[str, Any],
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _report_from_public_payload(payload)
    _reject_public_payload(payload)
    return True


class FrozenJsonObject(dict[str, Any]):
    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _validated_report_public_payload(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
    *,
    verify_stored_digest: bool,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityContradictionRecheckSlaReport:
        raise ValueError(
            "report must be a "
            "ResearchSourceAuthorityContradictionRecheckSlaReport",
        )
    _require_untampered_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    if not verify_stored_digest:
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest", None)
        payload["derived_validation_digest"] = _canonical_digest(unsigned)
    validate_research_source_authority_contradiction_recheck_sla_public_payload(
        payload,
    )
    return payload


def _report_from_public_payload(
    value: object,
) -> ResearchSourceAuthorityContradictionRecheckSlaReport:
    payload = _require_public_object_schema(
        "public payload",
        value,
        _PUBLIC_REPORT_SCHEMA,
    )
    rows = tuple(
        _row_from_public_payload(item)
        for item in _require_public_array("rows", payload["rows"])
    )
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in _require_public_array(
            "reason_code_counts",
            payload["reason_code_counts"],
        )
    )
    return ResearchSourceAuthorityContradictionRecheckSlaReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        contradiction_watch_severity=_public_decimal(
            "contradiction_watch_severity",
            payload["contradiction_watch_severity"],
        ),
        contradiction_block_severity=_public_decimal(
            "contradiction_block_severity",
            payload["contradiction_block_severity"],
        ),
        authority_tier_gap_watch=_public_decimal(
            "authority_tier_gap_watch",
            payload["authority_tier_gap_watch"],
        ),
        authority_tier_gap_block=_public_decimal(
            "authority_tier_gap_block",
            payload["authority_tier_gap_block"],
        ),
        last_checked_watch_age_seconds=_public_decimal(
            "last_checked_watch_age_seconds",
            payload["last_checked_watch_age_seconds"],
        ),
        last_checked_block_age_seconds=_public_decimal(
            "last_checked_block_age_seconds",
            payload["last_checked_block_age_seconds"],
        ),
        resolution_watch_seconds_remaining=_public_decimal(
            "resolution_watch_seconds_remaining",
            payload["resolution_watch_seconds_remaining"],
        ),
        resolution_block_seconds_remaining=_public_decimal(
            "resolution_block_seconds_remaining",
            payload["resolution_block_seconds_remaining"],
        ),
        contradiction_count=_public_decimal(
            "contradiction_count",
            payload["contradiction_count"],
        ),
        routine_recheck_count=_public_decimal(
            "routine_recheck_count",
            payload["routine_recheck_count"],
        ),
        accelerated_recheck_count=_public_decimal(
            "accelerated_recheck_count",
            payload["accelerated_recheck_count"],
        ),
        immediate_recheck_count=_public_decimal(
            "immediate_recheck_count",
            payload["immediate_recheck_count"],
        ),
        severe_contradiction_count=_public_decimal(
            "severe_contradiction_count",
            payload["severe_contradiction_count"],
        ),
        material_authority_tier_gap_count=_public_decimal(
            "material_authority_tier_gap_count",
            payload["material_authority_tier_gap_count"],
        ),
        stale_last_checked_count=_public_decimal(
            "stale_last_checked_count",
            payload["stale_last_checked_count"],
        ),
        near_resolution_count=_public_decimal(
            "near_resolution_count",
            payload["near_resolution_count"],
        ),
        highest_contradiction_severity=_public_decimal(
            "highest_contradiction_severity",
            payload["highest_contradiction_severity"],
        ),
        highest_authority_tier_gap=_public_decimal(
            "highest_authority_tier_gap",
            payload["highest_authority_tier_gap"],
        ),
        oldest_last_checked_age_seconds=_public_decimal(
            "oldest_last_checked_age_seconds",
            payload["oldest_last_checked_age_seconds"],
        ),
        nearest_resolution_seconds_remaining=_public_decimal(
            "nearest_resolution_seconds_remaining",
            payload["nearest_resolution_seconds_remaining"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_public_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchSourceAuthorityContradictionRecheckSlaRow:
    payload = _require_public_object_schema("row", value, _PUBLIC_ROW_SCHEMA)
    return ResearchSourceAuthorityContradictionRecheckSlaRow(
        contradiction_bucket=_public_string(
            "contradiction_bucket",
            payload["contradiction_bucket"],
        ),
        contradiction_severity=_public_decimal(
            "contradiction_severity",
            payload["contradiction_severity"],
        ),
        authority_tier_gap=_public_decimal(
            "authority_tier_gap",
            payload["authority_tier_gap"],
        ),
        last_checked_age_seconds=_public_decimal(
            "last_checked_age_seconds",
            payload["last_checked_age_seconds"],
        ),
        resolution_seconds_remaining=_public_decimal(
            "resolution_seconds_remaining",
            payload["resolution_seconds_remaining"],
        ),
        recheck_sla_bucket=_public_string(
            "recheck_sla_bucket",
            payload["recheck_sla_bucket"],
        ),
        status=_public_string("status", payload["status"]),
        reason_codes=_public_string_tuple(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount:
    payload = _require_public_object_schema(
        "reason_code_count",
        value,
        _PUBLIC_REASON_CODE_COUNT_SCHEMA,
    )
    return ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount(
        reason_code=_public_string("reason_code", payload["reason_code"]),
        count=_public_decimal("count", payload["count"]),
        paper_only=_public_true_flag("paper_only", payload["paper_only"]),
        report_only=_public_true_flag("report_only", payload["report_only"]),
        readonly=_public_true_flag("readonly", payload["readonly"]),
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceAuthorityContradictionRecheckSlaInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    inputs = tuple(value)
    seen: set[str] = set()
    for input_value in inputs:
        if type(input_value) is not ResearchSourceAuthorityContradictionRecheckSlaInput:
            raise ValueError(
                "inputs must contain "
                "ResearchSourceAuthorityContradictionRecheckSlaInput",
            )
        _require_hard_flags("input", input_value)
        _require_untampered_public_dataclass(input_value, "input")
        if input_value.contradiction_bucket in seen:
            raise ValueError("inputs must be unique by contradiction_bucket")
        seen.add(input_value.contradiction_bucket)
    return tuple(sorted(inputs, key=lambda item: item.contradiction_bucket))


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityContradictionRecheckSlaRow:
            raise ValueError(
                "rows must contain "
                "ResearchSourceAuthorityContradictionRecheckSlaRow",
            )
        _require_hard_flags("row", row)
        _require_untampered_public_dataclass(row, "row")
        if row.contradiction_bucket in seen:
            raise ValueError("rows must be unique by contradiction_bucket")
        seen.add(row.contradiction_bucket)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if (
            type(count)
            is not ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        _require_untampered_public_dataclass(count, "reason_code_count")
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(count.reason_code)
    return counts


def _row_from_input(
    input_value: ResearchSourceAuthorityContradictionRecheckSlaInput,
    *,
    config: ResearchSourceAuthorityContradictionRecheckSlaConfig,
) -> ResearchSourceAuthorityContradictionRecheckSlaRow:
    reason_codes = _row_reason_codes(
        contradiction_severity=input_value.contradiction_severity,
        authority_tier_gap=input_value.authority_tier_gap,
        last_checked_age_seconds=input_value.last_checked_age_seconds,
        resolution_seconds_remaining=input_value.resolution_seconds_remaining,
        config=config,
    )
    return ResearchSourceAuthorityContradictionRecheckSlaRow(
        contradiction_bucket=input_value.contradiction_bucket,
        contradiction_severity=input_value.contradiction_severity,
        authority_tier_gap=input_value.authority_tier_gap,
        last_checked_age_seconds=input_value.last_checked_age_seconds,
        resolution_seconds_remaining=input_value.resolution_seconds_remaining,
        recheck_sla_bucket=_sla_bucket(reason_codes),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    contradiction_severity: Decimal,
    authority_tier_gap: Decimal,
    last_checked_age_seconds: Decimal,
    resolution_seconds_remaining: Decimal,
    config: ResearchSourceAuthorityContradictionRecheckSlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if contradiction_severity >= config.contradiction_block_severity:
        reasons.append(CONTRADICTION_SEVERITY_BLOCK_REASON)
    elif contradiction_severity >= config.contradiction_watch_severity:
        reasons.append(CONTRADICTION_SEVERITY_WATCH_REASON)
    if authority_tier_gap >= config.authority_tier_gap_block:
        reasons.append(AUTHORITY_TIER_GAP_BLOCK_REASON)
    elif authority_tier_gap >= config.authority_tier_gap_watch:
        reasons.append(AUTHORITY_TIER_GAP_WATCH_REASON)
    if last_checked_age_seconds >= config.last_checked_block_age_seconds:
        reasons.append(LAST_CHECKED_AGE_BLOCK_REASON)
    elif last_checked_age_seconds >= config.last_checked_watch_age_seconds:
        reasons.append(LAST_CHECKED_AGE_WATCH_REASON)
    if resolution_seconds_remaining <= config.resolution_block_seconds_remaining:
        reasons.append(RESOLUTION_PROXIMITY_BLOCK_REASON)
    elif resolution_seconds_remaining <= config.resolution_watch_seconds_remaining:
        reasons.append(RESOLUTION_PROXIMITY_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASON_CODES for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _sla_bucket(reason_codes: tuple[str, ...]) -> str:
    status = _row_status(reason_codes)
    return {
        "pass": "routine",
        "watch": "accelerated",
        "block": "immediate",
    }[status]


def _report_status(
    rows: tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason in REPORT_TRIGGER_REASON_CODES
    }
    if not present:
        return (CLEAR_REASON,)
    return tuple(reason for reason in REPORT_TRIGGER_REASON_CODES if reason in present)


def _reason_code_counts(
    rows: tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...],
) -> tuple[ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_count(1),
            ),
        )
    counts = tuple(
        ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount(
            reason_code=reason,
            count=_count(
                sum(1 for row in rows if reason in row.reason_codes),
            ),
        )
        for reason in ROW_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    return counts


def _row_sort_key(
    row: ResearchSourceAuthorityContradictionRecheckSlaRow,
) -> tuple[int, str]:
    return (STATUS_RANK[row.status], row.contradiction_bucket)


def _sla_bucket_count(
    rows: tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...],
    bucket: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.recheck_sla_bucket == bucket))


def _reason_count(
    rows: tuple[ResearchSourceAuthorityContradictionRecheckSlaRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason in row.reason_codes for reason in reasons)
        ),
    )


def _validate_config(
    config: ResearchSourceAuthorityContradictionRecheckSlaConfig,
) -> None:
    if config.contradiction_block_severity <= config.contradiction_watch_severity:
        raise ValueError(
            "contradiction_block_severity must exceed "
            "contradiction_watch_severity",
        )
    if config.authority_tier_gap_block <= config.authority_tier_gap_watch:
        raise ValueError(
            "authority_tier_gap_block must exceed authority_tier_gap_watch",
        )
    if (
        config.last_checked_block_age_seconds
        <= config.last_checked_watch_age_seconds
    ):
        raise ValueError(
            "last_checked_block_age_seconds must exceed "
            "last_checked_watch_age_seconds",
        )
    if (
        config.resolution_block_seconds_remaining
        >= config.resolution_watch_seconds_remaining
    ):
        raise ValueError(
            "resolution_block_seconds_remaining must be below "
            "resolution_watch_seconds_remaining",
        )


def _validate_row_shape(
    row: ResearchSourceAuthorityContradictionRecheckSlaRow,
) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.recheck_sla_bucket != _sla_bucket(row.reason_codes):
        raise ValueError("recheck_sla_bucket must match reason_codes")


def _validate_row_with_config(
    row: ResearchSourceAuthorityContradictionRecheckSlaRow,
    *,
    config: ResearchSourceAuthorityContradictionRecheckSlaConfig,
) -> None:
    expected_reason_codes = _row_reason_codes(
        contradiction_severity=row.contradiction_severity,
        authority_tier_gap=row.authority_tier_gap,
        last_checked_age_seconds=row.last_checked_age_seconds,
        resolution_seconds_remaining=row.resolution_seconds_remaining,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    _validate_row_shape(row)


def _validate_report(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> None:
    config = ResearchSourceAuthorityContradictionRecheckSlaConfig(
        config_version=report.config_version,
        contradiction_watch_severity=report.contradiction_watch_severity,
        contradiction_block_severity=report.contradiction_block_severity,
        authority_tier_gap_watch=report.authority_tier_gap_watch,
        authority_tier_gap_block=report.authority_tier_gap_block,
        last_checked_watch_age_seconds=report.last_checked_watch_age_seconds,
        last_checked_block_age_seconds=report.last_checked_block_age_seconds,
        resolution_watch_seconds_remaining=(
            report.resolution_watch_seconds_remaining
        ),
        resolution_block_seconds_remaining=(
            report.resolution_block_seconds_remaining
        ),
    )
    for row in report.rows:
        _validate_row_with_config(row, config=config)
    if report.contradiction_count != _count(len(report.rows)):
        raise ValueError("contradiction_count must match rows")
    expected_values = {
        "routine_recheck_count": _sla_bucket_count(report.rows, "routine"),
        "accelerated_recheck_count": _sla_bucket_count(
            report.rows,
            "accelerated",
        ),
        "immediate_recheck_count": _sla_bucket_count(report.rows, "immediate"),
        "severe_contradiction_count": _reason_count(
            report.rows,
            (
                CONTRADICTION_SEVERITY_WATCH_REASON,
                CONTRADICTION_SEVERITY_BLOCK_REASON,
            ),
        ),
        "material_authority_tier_gap_count": _reason_count(
            report.rows,
            (
                AUTHORITY_TIER_GAP_WATCH_REASON,
                AUTHORITY_TIER_GAP_BLOCK_REASON,
            ),
        ),
        "stale_last_checked_count": _reason_count(
            report.rows,
            (
                LAST_CHECKED_AGE_WATCH_REASON,
                LAST_CHECKED_AGE_BLOCK_REASON,
            ),
        ),
        "near_resolution_count": _reason_count(
            report.rows,
            (
                RESOLUTION_PROXIMITY_WATCH_REASON,
                RESOLUTION_PROXIMITY_BLOCK_REASON,
            ),
        ),
        "highest_contradiction_severity": max(
            (row.contradiction_severity for row in report.rows),
            default=ZERO,
        ),
        "highest_authority_tier_gap": max(
            (row.authority_tier_gap for row in report.rows),
            default=ZERO,
        ),
        "oldest_last_checked_age_seconds": max(
            (row.last_checked_age_seconds for row in report.rows),
            default=ZERO,
        ),
        "nearest_resolution_seconds_remaining": min(
            (row.resolution_seconds_remaining for row in report.rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")


def _require_or_set_digest(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest_from_public_payload(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _report_digest_from_public_payload(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_public_payload(payload)
    return _canonical_digest(payload)


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, datetime):
        return _datetime_text(value)
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("public payload contains an unsupported value")


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return FrozenJsonObject(
            {key: _freeze_json(item) for key, item in value.items()},
        )
    if isinstance(value, (list, tuple)):
        return FrozenJsonArray(_freeze_json(item) for item in value)
    return value


def _require_public_object_schema(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    if type(value) not in (dict, FrozenJsonObject):
        raise ValueError(f"{label} public payload schema must match exactly")
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} public payload schema must match exactly")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} public payload schema must use string keys")
    return dict(value)


def _require_public_array(label: str, value: object) -> tuple[Any, ...]:
    if type(value) not in (list, FrozenJsonArray):
        raise ValueError(f"{label} must be a JSON array")
    return tuple(value)


def _public_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    return value


def _public_string_tuple(label: str, value: object) -> tuple[str, ...]:
    items = _require_public_array(label, value)
    if any(type(item) is not str for item in items):
        raise ValueError(f"{label} must contain strings")
    return tuple(items)


def _public_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a canonical Decimal string") from exc
    normalized = _require_decimal(label, parsed)
    if _decimal_text(normalized) != value:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_datetime(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(label, parsed)
    if _datetime_text(normalized) != value:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return normalized


def _public_true_flag(label: str, value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{label} must be exactly True")
    return True


def _public_sha256(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a SHA-256 hex string")
    _require_sha256(label, value)
    return value


def _store_public_snapshot(value: object) -> None:
    identity = id(value)
    snapshot = _public_snapshot(value)

    def _clear_snapshot(reference: weakref.ReferenceType[object]) -> None:
        if _PUBLIC_SNAPSHOT_REFS.get(identity) is reference:
            _PUBLIC_SNAPSHOTS.pop(identity, None)
            _PUBLIC_SNAPSHOT_REFS.pop(identity, None)

    reference = weakref.ref(value, _clear_snapshot)
    _PUBLIC_SNAPSHOTS[identity] = snapshot
    _PUBLIC_SNAPSHOT_REFS[identity] = reference


def _require_untampered_public_dataclass(value: object, label: str) -> None:
    identity = id(value)
    expected = _PUBLIC_SNAPSHOTS.get(identity)
    reference = _PUBLIC_SNAPSHOT_REFS.get(identity)
    if type(expected) is not tuple or reference is None or reference() is not value:
        raise ValueError(f"{label} canonical snapshot is missing")
    try:
        actual = _public_snapshot(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} was modified after initialization") from exc
    if actual != expected:
        raise ValueError(f"{label} was modified after initialization")


def _require_untampered_report(
    report: ResearchSourceAuthorityContradictionRecheckSlaReport,
) -> None:
    if type(report.rows) is not tuple or type(report.reason_code_counts) is not tuple:
        raise ValueError("report was modified after initialization")
    for row in report.rows:
        if type(row) is not ResearchSourceAuthorityContradictionRecheckSlaRow:
            raise ValueError("report was modified after initialization")
        _require_hard_flags("row", row)
    for count in report.reason_code_counts:
        if (
            type(count)
            is not ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount
        ):
            raise ValueError("report was modified after initialization")
        _require_hard_flags("reason_code_count", count)
    _require_hard_flags("report", report)
    _validate_report(report)
    for row in report.rows:
        _require_untampered_public_dataclass(row, "row")
    for count in report.reason_code_counts:
        _require_untampered_public_dataclass(count, "reason_code_count")
    _require_untampered_public_dataclass(report, "report")


def _public_snapshot(value: object) -> tuple[tuple[str, Any], ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("public snapshot requires a dataclass instance")
    return tuple(
        (field.name, _snapshot_value(getattr(value, field.name)))
        for field in fields(value)
    )


def _snapshot_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return (
            "dataclass",
            type(value),
            tuple(
                (field.name, _snapshot_value(getattr(value, field.name)))
                for field in fields(value)
            ),
        )
    if type(value) is Decimal:
        return ("decimal", value.as_tuple())
    if type(value) is datetime:
        return ("datetime", value.isoformat(), value.fold)
    if type(value) is tuple:
        return ("tuple", tuple(_snapshot_value(item) for item in value))
    if type(value) is list:
        return ("list", tuple(_snapshot_value(item) for item in value))
    if type(value) is dict:
        return (
            "dict",
            tuple(
                (_snapshot_value(key), _snapshot_value(item))
                for key, item in value.items()
            ),
        )
    if value is None or type(value) in (str, bool, int, float):
        return (type(value), value)
    raise ValueError("public snapshot contains an unsupported value")


def _require_exact_type(label: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exactly {expected.__name__}")


def _require_supported_config_version(value: object) -> None:
    _require_canonical_string("config_version", value)
    if (
        value
        != DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _require_public_label(label: str, value: object) -> str:
    value = _require_canonical_string_shape(label, value)
    if len(value) > 120:
        raise ValueError(f"{label} must be at most 120 characters")
    return _redact_public_label(value)


def _require_canonical_string(label: str, value: object) -> str:
    value = _require_canonical_string_shape(label, value)
    _reject_unsafe_string(label, value)
    return value


def _require_canonical_string_shape(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be a non-empty canonical string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} must not contain control characters")
    return value


def _require_decimal(label: str, value: object) -> Decimal:
    raw = _require_raw_decimal(label, value)
    return _quantize_decimal(label, raw)


def _require_raw_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{label} must not be negative zero")
    return value


def _quantize_decimal(label: str, value: Decimal) -> Decimal:
    if value.as_tuple().exponent < QUANT.as_tuple().exponent:
        raise ValueError(f"{label} must not exceed six decimal places")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be quantizable to six decimals") from exc


def _require_nonnegative_decimal(label: str, value: object) -> Decimal:
    raw = _require_raw_decimal(label, value)
    if raw < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return _quantize_decimal(label, raw)


def _require_positive_decimal(label: str, value: object) -> Decimal:
    raw = _require_raw_decimal(label, value)
    if raw <= ZERO:
        raise ValueError(f"{label} must be positive")
    normalized = _quantize_decimal(label, raw)
    if normalized <= ZERO:
        raise ValueError(f"{label} must remain positive at six decimals")
    return normalized


def _require_ratio(label: str, value: object) -> Decimal:
    raw = _require_raw_decimal(label, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return _quantize_decimal(label, raw)


def _require_nonnegative_whole_decimal(label: str, value: object) -> Decimal:
    raw = _require_raw_decimal(label, value)
    if raw < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        is_whole = raw == raw.to_integral_value()
    if not is_whole:
        raise ValueError(f"{label} must be a whole Decimal")
    return _quantize_decimal(label, raw)


def _require_positive_whole_decimal(label: str, value: object) -> Decimal:
    raw = _require_raw_decimal(label, value)
    if raw <= ZERO:
        raise ValueError(f"{label} must be positive")
    with localcontext(DECIMAL_CONTEXT):
        is_whole = raw == raw.to_integral_value()
    if not is_whole:
        raise ValueError(f"{label} must be a whole Decimal")
    return _quantize_decimal(label, raw)


def _require_status(label: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_STATUSES
    ):
        raise ValueError(f"{label} must be a known status")


def _require_sla_bucket(label: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_BUCKETS
    ):
        raise ValueError(f"{label} must be a known SLA bucket")


def _normalize_reason_codes(
    label: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{label} must be a list or tuple")
    reasons = tuple(value)
    if not reasons:
        raise ValueError(f"{label} must not be empty")
    if any(type(reason) is not str or reason not in allowed for reason in reasons):
        raise ValueError(f"{label} must contain known reason codes")
    if len(set(reasons)) != len(reasons):
        raise ValueError(f"{label} must not contain duplicates")
    expected_order = tuple(reason for reason in allowed if reason in reasons)
    if reasons != expected_order:
        raise ValueError(f"{label} must use canonical ordering")
    return reasons


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be exactly True")
        if type(getattr(value, field_name)) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")


def _as_utc(label: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_text(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_text(value: Decimal) -> str:
    normalized = _require_decimal("decimal", value)
    return format(normalized, ".6f")


def _count(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value))


def _require_sha256(label: str, value: object) -> None:
    if type(value) is not str or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{label} must be a SHA-256 hex string")
    if value != value.lower():
        raise ValueError(f"{label} must be lowercase SHA-256 hex")
    if any(character not in LOWERCASE_HEX_DIGITS for character in value):
        raise ValueError(f"{label} must be a SHA-256 hex string")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_key(key)
            _reject_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_string("public value", value)
        return
    if value is None or type(value) in (bool, int, float, Decimal):
        return
    raise ValueError("public payload must use canonical string values")


def _reject_unsafe_key(value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"unsafe key is not allowed: {value}")


def _reject_unsafe_string(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{label} contains an unsafe value")


def _redact_public_label(value: str) -> str:
    lowered = value.casefold()
    if not any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        return value
    digest_prefix = sha256(value.encode("utf-8")).hexdigest()[
        :REDACTED_PUBLIC_LABEL_HEX_LENGTH
    ]
    return f"{REDACTED_PUBLIC_LABEL_PREFIX}_{digest_prefix}"


__all__ = [
    "AUTHORITY_TIER_GAP_BLOCK_REASON",
    "AUTHORITY_TIER_GAP_WATCH_REASON",
    "CLEAR_REASON",
    "CONTRADICTION_SEVERITY_BLOCK_REASON",
    "CONTRADICTION_SEVERITY_WATCH_REASON",
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_REPORT_CONFIG_VERSION",
    "EMPTY_REASON",
    "LAST_CHECKED_AGE_BLOCK_REASON",
    "LAST_CHECKED_AGE_WATCH_REASON",
    "RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_BUCKETS",
    "RESEARCH_SOURCE_AUTHORITY_CONTRADICTION_RECHECK_SLA_STATUSES",
    "RESOLUTION_PROXIMITY_BLOCK_REASON",
    "RESOLUTION_PROXIMITY_WATCH_REASON",
    "ResearchSourceAuthorityContradictionRecheckSlaConfig",
    "ResearchSourceAuthorityContradictionRecheckSlaInput",
    "ResearchSourceAuthorityContradictionRecheckSlaReasonCodeCount",
    "ResearchSourceAuthorityContradictionRecheckSlaReport",
    "ResearchSourceAuthorityContradictionRecheckSlaRow",
    "ResearchSourceAuthorityContradictionRecheckSlaSignal",
    "build_research_source_authority_contradiction_recheck_sla_report",
    "research_source_authority_contradiction_recheck_sla_report_digest",
    "research_source_authority_contradiction_recheck_sla_report_payload",
    "validate_research_source_authority_contradiction_recheck_sla_public_payload",
    "validate_research_source_authority_contradiction_recheck_sla_report_digest",
]
