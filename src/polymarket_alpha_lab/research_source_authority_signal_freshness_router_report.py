"""Report-only authority/freshness router for research source signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_AUTHORITY_SIGNAL_FRESHNESS_ROUTER_CONFIG_VERSION = (
    "research-source-authority-signal-freshness-router-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROUTER_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "raw source",
    "source text",
    "dsn",
    "table",
    "token",
    "secret",
    "database",
    "network",
    "auth_token",
    "authentication",
    "authorization",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "sizing",
    "recommendation",
    "live",
)
_REASON_CODE_SEQUENCE = (
    "no_signals",
    "freshness_stale",
    "freshness_watch",
    "authority_below_watch",
    "authority_watch",
    "authority_pass",
    "router_block",
    "router_watch",
    "router_pass",
)


@dataclass(frozen=True)
class ResearchSourceAuthoritySignalFreshnessRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_SIGNAL_FRESHNESS_ROUTER_CONFIG_VERSION
    )
    pass_authority_score: Decimal = Decimal("0.750000")
    watch_authority_score: Decimal = Decimal("0.400000")
    fresh_within_seconds: Decimal = Decimal("86400.000000")
    stale_after_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritySignalFreshnessRouterConfig:
            raise TypeError(
                "ResearchSourceAuthoritySignalFreshnessRouterConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritySignalFreshnessRouterConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceAuthoritySignalFreshnessRouterConfig",
            )
        _require_public_key("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_SIGNAL_FRESHNESS_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("pass_authority_score", "watch_authority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_authority_score > self.pass_authority_score:
            raise ValueError(
                "watch_authority_score must not exceed pass_authority_score",
            )
        for field_name in ("fresh_within_seconds", "stale_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.fresh_within_seconds > self.stale_after_seconds:
            raise ValueError("fresh_within_seconds must not exceed stale_after_seconds")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritySignalFreshnessRouterInput:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    raw_source_reference: str
    raw_source_excerpt: str | None
    source_authority_score: Decimal
    signal_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritySignalFreshnessRouterInput:
            raise TypeError(
                "ResearchSourceAuthoritySignalFreshnessRouterInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritySignalFreshnessRouterInput:
            raise ValueError(
                "input must be exactly "
                "ResearchSourceAuthoritySignalFreshnessRouterInput",
            )
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
            "raw_source_reference",
        ):
            _require_raw_text(field_name, getattr(self, field_name))
        if self.raw_source_excerpt is not None:
            _require_raw_text("raw_source_excerpt", self.raw_source_excerpt)
        object.__setattr__(
            self,
            "source_authority_score",
            _require_ratio_decimal(
                "source_authority_score",
                self.source_authority_score,
            ),
        )
        object.__setattr__(
            self,
            "signal_observed_at",
            _as_utc("signal_observed_at", self.signal_observed_at),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem:
            raise TypeError(
                "ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem",
            )
        _require_public_key("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritySignalFreshnessRouterRow:
    signal_ref: str
    authority_score: Decimal
    freshness_age_seconds: Decimal
    router_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritySignalFreshnessRouterRow:
            raise TypeError(
                "ResearchSourceAuthoritySignalFreshnessRouterRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritySignalFreshnessRouterRow:
            raise ValueError(
                "row must be exactly ResearchSourceAuthoritySignalFreshnessRouterRow",
            )
        object.__setattr__(
            self,
            "signal_ref",
            _require_public_text("signal_ref", self.signal_ref),
        )
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        object.__setattr__(
            self,
            "freshness_age_seconds",
            _require_nonnegative_decimal(
                "freshness_age_seconds",
                self.freshness_age_seconds,
            ),
        )
        _require_router_status("router_status", self.router_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthoritySignalFreshnessRouterReport:
    generated_at: datetime
    config_version: str
    router_status: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_score: Decimal
    max_freshness_age_seconds: Decimal
    rows: tuple[ResearchSourceAuthoritySignalFreshnessRouterRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthoritySignalFreshnessRouterReport:
            raise TypeError(
                "ResearchSourceAuthoritySignalFreshnessRouterReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthoritySignalFreshnessRouterReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceAuthoritySignalFreshnessRouterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_key("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_SIGNAL_FRESHNESS_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_router_status("router_status", self.router_status)
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_score",
            _require_ratio_decimal(
                "average_authority_score",
                self.average_authority_score,
            ),
        )
        object.__setattr__(
            self,
            "max_freshness_age_seconds",
            _require_nonnegative_decimal(
                "max_freshness_age_seconds",
                self.max_freshness_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
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
            "ResearchSourceAuthoritySignalFreshnessRouterReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_authority_signal_freshness_router_report(
    signals: Sequence[ResearchSourceAuthoritySignalFreshnessRouterInput],
    *,
    generated_at: datetime,
    config: ResearchSourceAuthoritySignalFreshnessRouterConfig | None = None,
    public_payload: Sequence[
        ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem
    ] = (),
) -> ResearchSourceAuthoritySignalFreshnessRouterReport:
    """Build a local report-only source authority/freshness router snapshot."""

    if config is None:
        config = ResearchSourceAuthoritySignalFreshnessRouterConfig()
    if type(config) is not ResearchSourceAuthoritySignalFreshnessRouterConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthoritySignalFreshnessRouterConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_inputs(signals)
    for signal in normalized_signals:
        if signal.signal_observed_at > generated_at:
            raise ValueError("signal_observed_at must not be after generated_at")
    rows = _build_rows(normalized_signals, generated_at=generated_at, config=config)
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "router_status": _report_status(rows),
        "signal_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_authority_score": _average(
            tuple(row.authority_score for row in rows),
        ),
        "max_freshness_age_seconds": max(
            (row.freshness_age_seconds for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceAuthoritySignalFreshnessRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    signals: tuple[ResearchSourceAuthoritySignalFreshnessRouterInput, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceAuthoritySignalFreshnessRouterConfig,
) -> tuple[ResearchSourceAuthoritySignalFreshnessRouterRow, ...]:
    rows = tuple(_row_for_signal(signal, generated_at=generated_at, config=config) for signal in signals)
    return tuple(sorted(rows, key=lambda row: row.signal_ref))


def _row_for_signal(
    signal: ResearchSourceAuthoritySignalFreshnessRouterInput,
    *,
    generated_at: datetime,
    config: ResearchSourceAuthoritySignalFreshnessRouterConfig,
) -> ResearchSourceAuthoritySignalFreshnessRouterRow:
    freshness_age_seconds = _seconds_between(signal.signal_observed_at, generated_at)
    status = _row_status(
        authority_score=signal.source_authority_score,
        freshness_age_seconds=freshness_age_seconds,
        config=config,
    )
    return ResearchSourceAuthoritySignalFreshnessRouterRow(
        signal_ref=_signal_ref(signal),
        authority_score=signal.source_authority_score,
        freshness_age_seconds=freshness_age_seconds,
        router_status=status,
        reason_codes=_row_reason_codes(
            authority_score=signal.source_authority_score,
            freshness_age_seconds=freshness_age_seconds,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    authority_score: Decimal,
    freshness_age_seconds: Decimal,
    config: ResearchSourceAuthoritySignalFreshnessRouterConfig,
) -> str:
    if freshness_age_seconds > config.stale_after_seconds:
        return "block"
    if authority_score < config.watch_authority_score:
        return "block"
    if (
        authority_score >= config.pass_authority_score
        and freshness_age_seconds <= config.fresh_within_seconds
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    authority_score: Decimal,
    freshness_age_seconds: Decimal,
    status: str,
    config: ResearchSourceAuthoritySignalFreshnessRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if freshness_age_seconds > config.stale_after_seconds:
        reason_codes.append("freshness_stale")
    elif freshness_age_seconds > config.fresh_within_seconds:
        reason_codes.append("freshness_watch")
    if authority_score < config.watch_authority_score:
        reason_codes.append("authority_below_watch")
    elif authority_score < config.pass_authority_score:
        reason_codes.append("authority_watch")
    else:
        reason_codes.append("authority_pass")
    reason_codes.append(f"router_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchSourceAuthoritySignalFreshnessRouterRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.router_status == "block" for row in rows):
        return "block"
    if any(row.router_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthoritySignalFreshnessRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_signals", "router_block")
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchSourceAuthoritySignalFreshnessRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.router_status == status)


def _validate_row_consistency(
    row: ResearchSourceAuthoritySignalFreshnessRouterRow,
) -> None:
    if row.router_status == "pass" and "router_pass" not in row.reason_codes:
        raise ValueError("pass rows must include router_pass")
    if row.router_status == "watch" and "router_watch" not in row.reason_codes:
        raise ValueError("watch rows must include router_watch")
    if row.router_status == "block" and "router_block" not in row.reason_codes:
        raise ValueError("block rows must include router_block")


def _validate_report_consistency(
    report: ResearchSourceAuthoritySignalFreshnessRouterReport,
) -> None:
    if report.signal_count != _decimal_count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_authority_score != _average(
        tuple(row.authority_score for row in report.rows),
    ):
        raise ValueError("average_authority_score must match rows")
    expected_max_age = max(
        (row.freshness_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_freshness_age_seconds != expected_max_age:
        raise ValueError("max_freshness_age_seconds must match rows")
    if report.router_status != _report_status(report.rows):
        raise ValueError("router_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    signals: Sequence[ResearchSourceAuthoritySignalFreshnessRouterInput],
) -> tuple[ResearchSourceAuthoritySignalFreshnessRouterInput, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Sequence):
        raise ValueError("signals must be a sequence")
    normalized: list[ResearchSourceAuthoritySignalFreshnessRouterInput] = []
    for signal in signals:
        if type(signal) is not ResearchSourceAuthoritySignalFreshnessRouterInput:
            raise ValueError(
                "signals items must be "
                "ResearchSourceAuthoritySignalFreshnessRouterInput",
            )
        normalized.append(signal)
    return tuple(
        sorted(
            normalized,
            key=lambda signal: (
                signal.signal_observed_at,
                _signal_ref(signal),
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceAuthoritySignalFreshnessRouterRow],
) -> tuple[ResearchSourceAuthoritySignalFreshnessRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceAuthoritySignalFreshnessRouterRow] = []
    for row in rows:
        if type(row) is not ResearchSourceAuthoritySignalFreshnessRouterRow:
            raise ValueError(
                "rows must contain ResearchSourceAuthoritySignalFreshnessRouterRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.signal_ref))


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem
    ],
) -> tuple[ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_raw_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must not exceed 2048 characters")
    return value


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public key")
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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_router_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ROUTER_STATUSES:
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_key("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    return _require_nonnegative_decimal("freshness_age_seconds", seconds)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _signal_ref(signal: ResearchSourceAuthoritySignalFreshnessRouterInput) -> str:
    payload = {
        "candidate": signal.raw_candidate_id,
        "market": signal.raw_market_id,
        "slug": signal.raw_market_slug,
        "question": signal.raw_market_question,
        "reference": signal.raw_source_reference,
        "excerpt": signal.raw_source_excerpt,
        "authority": str(signal.source_authority_score),
        "observed_at": signal.signal_observed_at.isoformat(),
    }
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _report_values_without_digest(
    report: ResearchSourceAuthoritySignalFreshnessRouterReport,
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


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_SIGNAL_FRESHNESS_ROUTER_CONFIG_VERSION",
    "ResearchSourceAuthoritySignalFreshnessRouterConfig",
    "ResearchSourceAuthoritySignalFreshnessRouterInput",
    "ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem",
    "ResearchSourceAuthoritySignalFreshnessRouterReport",
    "ResearchSourceAuthoritySignalFreshnessRouterRow",
    "build_research_source_authority_signal_freshness_router_report",
)
