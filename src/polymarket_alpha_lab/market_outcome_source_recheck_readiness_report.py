"""Readonly Polymarket outcome source recheck readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_READINESS_CONFIG_VERSION = (
    "market-outcome-source-recheck-readiness-v0"
)

SECOND_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

ROW_STATUSES = ("blocked", "watch", "ready")
REPORT_STATUSES = ("empty", "blocked", "watch", "ready")
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "ready": 2}

EMPTY_REASON = "market_outcome_source_recheck_readiness_empty"
READY_REASON = "market_outcome_source_recheck_ready"
MISSING_SOURCE_RECHECK_REASON = "market_outcome_source_missing_source_recheck"
MISSING_OFFICIAL_ACK_REASON = (
    "market_outcome_source_missing_official_source_acknowledgement"
)
STALE_RECHECK_REASON = "market_outcome_source_recheck_stale"
BLOCKED_STALE_RECHECK_REASON = "market_outcome_source_recheck_blocked_stale"

ROW_REASON_CODES = (
    READY_REASON,
    MISSING_SOURCE_RECHECK_REASON,
    MISSING_OFFICIAL_ACK_REASON,
    STALE_RECHECK_REASON,
    BLOCKED_STALE_RECHECK_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    READY_REASON,
    MISSING_SOURCE_RECHECK_REASON,
    MISSING_OFFICIAL_ACK_REASON,
    STALE_RECHECK_REASON,
    BLOCKED_STALE_RECHECK_REASON,
)
TRIGGER_REASON_CODES = tuple(
    reason_code
    for reason_code in REPORT_REASON_CODES
    if reason_code not in (EMPTY_REASON, READY_REASON)
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "account",
        "api_key",
        "auth",
        "balance",
        "broker",
        "cancel",
        "client_secret",
        "database",
        "exchange_mutation",
        "live",
        "network",
        "order",
        "persist",
        "private_key",
        "secret",
        "sign",
        "submit",
        "token",
        "trade",
        "trading",
        "wallet",
    ),
)


__all__ = (
    "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_READINESS_CONFIG_VERSION",
    "MarketOutcomeSourceRecheckReadinessConfig",
    "MarketOutcomeSourceRecheckReadinessSource",
    "MarketOutcomeSourceRecheckReadinessRow",
    "MarketOutcomeSourceRecheckReadinessReport",
    "build_market_outcome_source_recheck_readiness_report",
    "market_outcome_source_recheck_readiness_report_payload",
    "validate_market_outcome_source_recheck_readiness_public_payload",
)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckReadinessConfig:
    recheck_due_after_seconds: Decimal = Decimal("3600.000000")
    blocked_recheck_age_seconds: Decimal = Decimal("7200.000000")
    config_version: str = DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_READINESS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recheck_due_after_seconds",
            _require_positive_seconds(
                "recheck_due_after_seconds",
                self.recheck_due_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "blocked_recheck_age_seconds",
            _require_positive_seconds(
                "blocked_recheck_age_seconds",
                self.blocked_recheck_age_seconds,
            ),
        )
        if self.blocked_recheck_age_seconds <= self.recheck_due_after_seconds:
            raise ValueError(
                "blocked_recheck_age_seconds must be greater than "
                "recheck_due_after_seconds",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckReadinessSource:
    market_id: str
    market_slug: str
    category_id: str
    outcome_source_id: str
    outcome_source_last_rechecked_at: datetime | None
    official_source_acknowledged_at: datetime | None
    recheck_cadence_seconds: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_id",
            "market_slug",
            "category_id",
            "outcome_source_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_source_last_rechecked_at",
            _as_optional_utc(
                "outcome_source_last_rechecked_at",
                self.outcome_source_last_rechecked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_source_acknowledged_at",
            _as_optional_utc(
                "official_source_acknowledged_at",
                self.official_source_acknowledged_at,
            ),
        )
        if self.recheck_cadence_seconds is not None:
            object.__setattr__(
                self,
                "recheck_cadence_seconds",
                _require_positive_seconds(
                    "recheck_cadence_seconds",
                    self.recheck_cadence_seconds,
                ),
            )
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckReadinessRow:
    market_id: str
    market_slug: str
    category_id: str
    outcome_source_id: str
    outcome_source_last_rechecked_at: datetime | None
    official_source_acknowledged_at: datetime | None
    source_age_seconds: Decimal
    stale_recheck_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "market_id",
            "market_slug",
            "category_id",
            "outcome_source_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_source_last_rechecked_at",
            _as_optional_utc(
                "outcome_source_last_rechecked_at",
                self.outcome_source_last_rechecked_at,
            ),
        )
        object.__setattr__(
            self,
            "official_source_acknowledged_at",
            _as_optional_utc(
                "official_source_acknowledged_at",
                self.official_source_acknowledged_at,
            ),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_seconds("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_recheck_age_seconds",
            _require_nonnegative_seconds(
                "stale_recheck_age_seconds",
                self.stale_recheck_age_seconds,
            ),
        )
        _require_known_value("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketOutcomeSourceRecheckReadinessReport:
    generated_at: datetime
    config_version: str
    recheck_due_after_seconds: Decimal
    blocked_recheck_age_seconds: Decimal
    market_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_source_recheck_count: Decimal
    missing_official_source_acknowledgement_count: Decimal
    stale_recheck_count: Decimal
    blocked_stale_recheck_count: Decimal
    ready_ratio: Decimal
    max_source_age_seconds: Decimal
    max_stale_recheck_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketOutcomeSourceRecheckReadinessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "recheck_due_after_seconds",
            _require_positive_seconds(
                "recheck_due_after_seconds",
                self.recheck_due_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "blocked_recheck_age_seconds",
            _require_positive_seconds(
                "blocked_recheck_age_seconds",
                self.blocked_recheck_age_seconds,
            ),
        )
        for field_name in (
            "market_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "missing_source_recheck_count",
            "missing_official_source_acknowledgement_count",
            "stale_recheck_count",
            "blocked_stale_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio("ready_ratio", self.ready_ratio),
        )
        for field_name in ("max_source_age_seconds", "max_stale_recheck_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        _require_known_value("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_market_outcome_source_recheck_readiness_report(
    sources: list[MarketOutcomeSourceRecheckReadinessSource]
    | tuple[MarketOutcomeSourceRecheckReadinessSource, ...],
    *,
    config: MarketOutcomeSourceRecheckReadinessConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckReadinessReport:
    if type(config) is not MarketOutcomeSourceRecheckReadinessConfig:
        raise ValueError("config must be a MarketOutcomeSourceRecheckReadinessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_source(
                    source,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for source in _normalize_sources(sources)
            ),
            key=_row_sort_key,
        ),
    )
    market_count = _count(len(rows))
    ready_count = _count(sum(1 for row in rows if row.status == "ready"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    blocked_count = _count(sum(1 for row in rows if row.status == "blocked"))
    missing_source_recheck_count = _count(
        sum(1 for row in rows if MISSING_SOURCE_RECHECK_REASON in row.reason_codes),
    )
    missing_official_ack_count = _count(
        sum(1 for row in rows if MISSING_OFFICIAL_ACK_REASON in row.reason_codes),
    )
    stale_recheck_count = _count(
        sum(1 for row in rows if STALE_RECHECK_REASON in row.reason_codes),
    )
    blocked_stale_recheck_count = _count(
        sum(1 for row in rows if BLOCKED_STALE_RECHECK_REASON in row.reason_codes),
    )
    return MarketOutcomeSourceRecheckReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        recheck_due_after_seconds=config.recheck_due_after_seconds,
        blocked_recheck_age_seconds=config.blocked_recheck_age_seconds,
        market_count=market_count,
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        missing_source_recheck_count=missing_source_recheck_count,
        missing_official_source_acknowledgement_count=missing_official_ack_count,
        stale_recheck_count=stale_recheck_count,
        blocked_stale_recheck_count=blocked_stale_recheck_count,
        ready_ratio=_ratio(ready_count, market_count),
        max_source_age_seconds=_max_decimal(row.source_age_seconds for row in rows),
        max_stale_recheck_age_seconds=_max_decimal(
            row.stale_recheck_age_seconds for row in rows
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_outcome_source_recheck_readiness_report_payload(
    report: MarketOutcomeSourceRecheckReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeSourceRecheckReadinessReport:
        raise ValueError("report must be a MarketOutcomeSourceRecheckReadinessReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_market_outcome_source_recheck_readiness_public_payload(payload)
    return payload


def validate_market_outcome_source_recheck_readiness_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_source(
    source: MarketOutcomeSourceRecheckReadinessSource,
    *,
    config: MarketOutcomeSourceRecheckReadinessConfig,
    generated_at: datetime,
) -> MarketOutcomeSourceRecheckReadinessRow:
    if type(source) is not MarketOutcomeSourceRecheckReadinessSource:
        raise ValueError("source must be a MarketOutcomeSourceRecheckReadinessSource")
    _require_hard_flags("source", source)
    _validate_optional_not_after(
        "outcome_source_last_rechecked_at",
        source.outcome_source_last_rechecked_at,
        generated_at,
    )
    _validate_optional_not_after(
        "official_source_acknowledged_at",
        source.official_source_acknowledged_at,
        generated_at,
    )
    source_age_seconds = _optional_age_seconds(
        source.outcome_source_last_rechecked_at,
        generated_at,
    )
    cadence_seconds = (
        config.recheck_due_after_seconds
        if source.recheck_cadence_seconds is None
        else source.recheck_cadence_seconds
    )
    stale_recheck_age_seconds = _age_delta(source_age_seconds, cadence_seconds)
    reason_codes = _row_reason_codes(
        source,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return MarketOutcomeSourceRecheckReadinessRow(
        market_id=source.market_id,
        market_slug=source.market_slug,
        category_id=source.category_id,
        outcome_source_id=source.outcome_source_id,
        outcome_source_last_rechecked_at=source.outcome_source_last_rechecked_at,
        official_source_acknowledged_at=source.official_source_acknowledged_at,
        source_age_seconds=source_age_seconds,
        stale_recheck_age_seconds=stale_recheck_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    source: MarketOutcomeSourceRecheckReadinessSource,
    *,
    source_age_seconds: Decimal,
    config: MarketOutcomeSourceRecheckReadinessConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source.outcome_source_last_rechecked_at is None:
        reasons.append(MISSING_SOURCE_RECHECK_REASON)
    if source.official_source_acknowledged_at is None:
        reasons.append(MISSING_OFFICIAL_ACK_REASON)
    if (
        source.outcome_source_last_rechecked_at is not None
        and source_age_seconds > config.recheck_due_after_seconds
    ):
        reasons.append(STALE_RECHECK_REASON)
    if (
        source.outcome_source_last_rechecked_at is not None
        and source_age_seconds > config.blocked_recheck_age_seconds
    ):
        reasons.append(BLOCKED_STALE_RECHECK_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        MISSING_SOURCE_RECHECK_REASON in reason_codes
        or MISSING_OFFICIAL_ACK_REASON in reason_codes
        or BLOCKED_STALE_RECHECK_REASON in reason_codes
    ):
        return "blocked"
    if STALE_RECHECK_REASON in reason_codes:
        return "watch"
    return "ready"


def _report_status(rows: tuple[MarketOutcomeSourceRecheckReadinessRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[MarketOutcomeSourceRecheckReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in TRIGGER_REASON_CODES
    }
    if not found:
        return (READY_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in found)


def _row_sort_key(row: MarketOutcomeSourceRecheckReadinessRow) -> tuple[int, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.source_age_seconds, row.market_id)


def _normalize_sources(
    sources: list[MarketOutcomeSourceRecheckReadinessSource]
    | tuple[MarketOutcomeSourceRecheckReadinessSource, ...],
) -> tuple[MarketOutcomeSourceRecheckReadinessSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized: list[MarketOutcomeSourceRecheckReadinessSource] = []
    for source in sources:
        if type(source) is not MarketOutcomeSourceRecheckReadinessSource:
            raise ValueError("source must be a MarketOutcomeSourceRecheckReadinessSource")
        _require_hard_flags("source", source)
        normalized.append(source)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketOutcomeSourceRecheckReadinessRow, ...],
) -> tuple[MarketOutcomeSourceRecheckReadinessRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[MarketOutcomeSourceRecheckReadinessRow] = []
    for row in rows:
        if type(row) is not MarketOutcomeSourceRecheckReadinessRow:
            raise ValueError("row must be a MarketOutcomeSourceRecheckReadinessRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _validate_report_consistency(
    report: MarketOutcomeSourceRecheckReadinessReport,
) -> None:
    rows = report.rows
    expected_values = {
        "market_count": _count(len(rows)),
        "ready_count": _count(sum(1 for row in rows if row.status == "ready")),
        "watch_count": _count(sum(1 for row in rows if row.status == "watch")),
        "blocked_count": _count(sum(1 for row in rows if row.status == "blocked")),
        "missing_source_recheck_count": _count(
            sum(1 for row in rows if MISSING_SOURCE_RECHECK_REASON in row.reason_codes),
        ),
        "missing_official_source_acknowledgement_count": _count(
            sum(1 for row in rows if MISSING_OFFICIAL_ACK_REASON in row.reason_codes),
        ),
        "stale_recheck_count": _count(
            sum(1 for row in rows if STALE_RECHECK_REASON in row.reason_codes),
        ),
        "blocked_stale_recheck_count": _count(
            sum(1 for row in rows if BLOCKED_STALE_RECHECK_REASON in row.reason_codes),
        ),
        "ready_ratio": _ratio(
            _count(sum(1 for row in rows if row.status == "ready")),
            _count(len(rows)),
        ),
        "max_source_age_seconds": _max_decimal(row.source_age_seconds for row in rows),
        "max_stale_recheck_age_seconds": _max_decimal(
            row.stale_recheck_age_seconds for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _derived_validation_digest(
    report: MarketOutcomeSourceRecheckReadinessReport,
) -> str:
    return _digest_payload(_report_payload_without_digest(report))


def _report_payload_without_digest(
    report: MarketOutcomeSourceRecheckReadinessReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        _require_known_value(field_name, reason_code, allowed_values)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_seconds(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(SECOND_QUANTUM, rounding=ROUND_HALF_EVEN)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(SECOND_QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _max_decimal(values: Any) -> Decimal:
    maximum = ZERO
    for value in values:
        if value > maximum:
            maximum = value
    return maximum


def _age_delta(age_seconds: Decimal, cadence_seconds: Decimal) -> Decimal:
    delta = age_seconds - cadence_seconds
    if delta < ZERO:
        return ZERO
    return delta.quantize(SECOND_QUANTUM, rounding=ROUND_HALF_EVEN)


def _optional_age_seconds(observed_at: datetime | None, generated_at: datetime) -> Decimal:
    if observed_at is None:
        return ZERO
    return _seconds_between(observed_at, generated_at)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return (microseconds / MICROSECONDS_PER_SECOND).quantize(
        SECOND_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _validate_optional_not_after(
    field_name: str,
    value: datetime | None,
    generated_at: datetime,
) -> None:
    if value is not None and value > generated_at:
        raise ValueError(f"{field_name} must not be in the future")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be an exact Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
