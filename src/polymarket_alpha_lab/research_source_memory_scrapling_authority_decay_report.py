"""Readonly research memory scrapling authority decay report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_MEMORY_SCRAPLING_AUTHORITY_DECAY_CONFIG_VERSION = (
    "research-source-memory-scrapling-authority-decay-v0"
)

SECOND_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "memory_scrapling_authority_decay_empty"
PASS_REASON = "memory_scrapling_authority_decay_pass"
CAPTURE_STALE_REASON = "memory_scrapling_capture_stale"
CAPTURE_BLOCK_STALE_REASON = "memory_scrapling_capture_block_stale"
CONFIRMATION_MISSING_REASON = "memory_scrapling_confirmation_missing"
LOW_SIGNAL_SCORE_REASON = "memory_scrapling_low_signal_score"

ROW_REASON_CODES = (
    PASS_REASON,
    CAPTURE_STALE_REASON,
    CAPTURE_BLOCK_STALE_REASON,
    CONFIRMATION_MISSING_REASON,
    LOW_SIGNAL_SCORE_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    CAPTURE_STALE_REASON,
    CAPTURE_BLOCK_STALE_REASON,
    CONFIRMATION_MISSING_REASON,
    LOW_SIGNAL_SCORE_REASON,
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "dsn",
        "http://",
        "https://",
        "market",
        "private",
        "raw",
        "secret",
        "table",
        "text",
        "token",
        "url",
    ),
)
PUBLIC_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_MEMORY_SCRAPLING_AUTHORITY_DECAY_CONFIG_VERSION",
    "ResearchSourceMemoryScraplingAuthorityDecayConfig",
    "ResearchSourceMemoryScraplingAuthorityDecaySignal",
    "ResearchSourceMemoryScraplingAuthorityDecayRow",
    "ResearchSourceMemoryScraplingAuthorityDecayReport",
    "build_research_source_memory_scrapling_authority_decay_report",
    "research_source_memory_scrapling_authority_decay_report_payload",
    "validate_research_source_memory_scrapling_authority_decay_public_payload",
)


@dataclass(frozen=True)
class ResearchSourceMemoryScraplingAuthorityDecayConfig:
    stale_after_seconds: Decimal = Decimal("3600.000000")
    blocked_after_seconds: Decimal = Decimal("7200.000000")
    watch_decay_score: Decimal = Decimal("0.400000")
    block_decay_score: Decimal = Decimal("0.700000")
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_MEMORY_SCRAPLING_AUTHORITY_DECAY_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("stale_after_seconds", "blocked_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_decay_score", "block_decay_score"):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        if self.blocked_after_seconds <= self.stale_after_seconds:
            raise ValueError("blocked_after_seconds must exceed stale_after_seconds")
        if self.block_decay_score <= self.watch_decay_score:
            raise ValueError("block_decay_score must exceed watch_decay_score")
        object.__setattr__(
            self,
            "config_version",
            _require_public_config_string("config_version", self.config_version),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceMemoryScraplingAuthorityDecaySignal:
    entry_key: str
    group_key: str
    captured_at: datetime
    last_confirmed_at: datetime | None
    authority_score: Decimal
    memory_confidence_score: Decimal
    scrapling_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("entry_key", "group_key"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "last_confirmed_at",
            _as_optional_utc("last_confirmed_at", self.last_confirmed_at),
        )
        for field_name in (
            "authority_score",
            "memory_confidence_score",
            "scrapling_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchSourceMemoryScraplingAuthorityDecayRow:
    entry_key: str
    group_key: str
    captured_at: datetime
    last_confirmed_at: datetime | None
    capture_age_seconds: Decimal
    confirmation_age_seconds: Decimal
    authority_score: Decimal
    memory_confidence_score: Decimal
    scrapling_quality_score: Decimal
    authority_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("entry_key", "group_key"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "last_confirmed_at",
            _as_optional_utc("last_confirmed_at", self.last_confirmed_at),
        )
        for field_name in ("capture_age_seconds", "confirmation_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_score",
            "memory_confidence_score",
            "scrapling_quality_score",
            "authority_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _row_status(self.reason_codes, self.authority_decay_score):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceMemoryScraplingAuthorityDecayReport:
    generated_at: datetime
    config_version: str
    stale_after_seconds: Decimal
    blocked_after_seconds: Decimal
    watch_decay_score: Decimal
    block_decay_score: Decimal
    status: str
    entry_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_count: Decimal
    missing_confirmation_count: Decimal
    average_authority_decay_score: Decimal
    max_authority_decay_score: Decimal
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_config_string("config_version", self.config_version),
        )
        for field_name in ("stale_after_seconds", "blocked_after_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_decay_score", "block_decay_score"):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        for field_name in (
            "entry_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_count",
            "missing_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_decay_score",
            "max_authority_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _digest_payload(_public_payload_without_digest(self))
        if self.derived_validation_digest is None:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")


def build_research_source_memory_scrapling_authority_decay_report(
    signals: Any,
    *,
    config: ResearchSourceMemoryScraplingAuthorityDecayConfig,
    generated_at: datetime,
) -> ResearchSourceMemoryScraplingAuthorityDecayReport:
    if type(config) is not ResearchSourceMemoryScraplingAuthorityDecayConfig:
        raise ValueError(
            "config must be a ResearchSourceMemoryScraplingAuthorityDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)

    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_signals
            ),
            key=lambda row: (STATUS_WEIGHT[row.status], row.group_key, row.entry_key),
        ),
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceMemoryScraplingAuthorityDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        stale_after_seconds=config.stale_after_seconds,
        blocked_after_seconds=config.blocked_after_seconds,
        watch_decay_score=config.watch_decay_score,
        block_decay_score=config.block_decay_score,
        status=_summary_status(rows),
        entry_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        stale_count=_decimal_count(_reason_count(rows, CAPTURE_STALE_REASON)),
        missing_confirmation_count=_decimal_count(
            _reason_count(rows, CONFIRMATION_MISSING_REASON),
        ),
        average_authority_decay_score=_average_decay_score(rows),
        max_authority_decay_score=_max_decay_score(rows),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_source_memory_scrapling_authority_decay_report_payload(
    report: ResearchSourceMemoryScraplingAuthorityDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceMemoryScraplingAuthorityDecayReport:
        raise ValueError(
            "report must be a ResearchSourceMemoryScraplingAuthorityDecayReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_memory_scrapling_authority_decay_public_payload(payload)
    return payload


def validate_research_source_memory_scrapling_authority_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _require_payload_status_values(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_signal(
    signal: ResearchSourceMemoryScraplingAuthorityDecaySignal,
    *,
    config: ResearchSourceMemoryScraplingAuthorityDecayConfig,
    generated_at: datetime,
) -> ResearchSourceMemoryScraplingAuthorityDecayRow:
    _reject_future_datetime("captured_at", signal.captured_at, generated_at)
    if signal.last_confirmed_at is not None:
        _reject_future_datetime("last_confirmed_at", signal.last_confirmed_at, generated_at)
    capture_age_seconds = _seconds_between(signal.captured_at, generated_at)
    confirmation_age_seconds = (
        ZERO
        if signal.last_confirmed_at is None
        else _seconds_between(signal.last_confirmed_at, generated_at)
    )
    decay_score = _authority_decay_score(
        signal=signal,
        capture_age_seconds=capture_age_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal=signal,
        capture_age_seconds=capture_age_seconds,
        decay_score=decay_score,
        config=config,
    )
    return ResearchSourceMemoryScraplingAuthorityDecayRow(
        entry_key=signal.entry_key,
        group_key=signal.group_key,
        captured_at=signal.captured_at,
        last_confirmed_at=signal.last_confirmed_at,
        capture_age_seconds=capture_age_seconds,
        confirmation_age_seconds=confirmation_age_seconds,
        authority_score=signal.authority_score,
        memory_confidence_score=signal.memory_confidence_score,
        scrapling_quality_score=signal.scrapling_quality_score,
        authority_decay_score=decay_score,
        status=_row_status(reason_codes, decay_score),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    signal: ResearchSourceMemoryScraplingAuthorityDecaySignal,
    capture_age_seconds: Decimal,
    decay_score: Decimal,
    config: ResearchSourceMemoryScraplingAuthorityDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if capture_age_seconds > config.stale_after_seconds:
        reason_codes.append(CAPTURE_STALE_REASON)
    if capture_age_seconds > config.blocked_after_seconds:
        reason_codes.append(CAPTURE_BLOCK_STALE_REASON)
    if signal.last_confirmed_at is None:
        reason_codes.append(CONFIRMATION_MISSING_REASON)
    if decay_score >= config.watch_decay_score and not reason_codes:
        reason_codes.append(LOW_SIGNAL_SCORE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _authority_decay_score(
    *,
    signal: ResearchSourceMemoryScraplingAuthorityDecaySignal,
    capture_age_seconds: Decimal,
    config: ResearchSourceMemoryScraplingAuthorityDecayConfig,
) -> Decimal:
    age_range = config.blocked_after_seconds - config.stale_after_seconds
    age_pressure = (capture_age_seconds - config.stale_after_seconds) / age_range
    if age_pressure < ZERO:
        age_pressure = ZERO
    if age_pressure > ONE:
        age_pressure = ONE
    quality_floor = min(
        signal.authority_score,
        signal.memory_confidence_score,
        signal.scrapling_quality_score,
    )
    quality_pressure = ONE - quality_floor
    return _quantize_score(max(age_pressure, quality_pressure))


def _row_status(reason_codes: tuple[str, ...], decay_score: Decimal) -> str:
    if (
        CAPTURE_BLOCK_STALE_REASON in reason_codes
        or CONFIRMATION_MISSING_REASON in reason_codes
        or decay_score >= Decimal("0.700000")
    ):
        return "block"
    if (
        CAPTURE_STALE_REASON in reason_codes
        or LOW_SIGNAL_SCORE_REASON in reason_codes
        or decay_score >= Decimal("0.400000")
    ):
        return "watch"
    return "pass"


def _summary_status(
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in present)


def _validate_report(report: ResearchSourceMemoryScraplingAuthorityDecayReport) -> None:
    if report.blocked_after_seconds <= report.stale_after_seconds:
        raise ValueError("blocked_after_seconds must exceed stale_after_seconds")
    if report.block_decay_score <= report.watch_decay_score:
        raise ValueError("block_decay_score must exceed watch_decay_score")
    rows = report.rows
    if report.entry_count != _decimal_count(len(rows)):
        raise ValueError("entry_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.stale_count != _decimal_count(_reason_count(rows, CAPTURE_STALE_REASON)):
        raise ValueError("stale_count must match rows")
    if report.missing_confirmation_count != _decimal_count(
        _reason_count(rows, CONFIRMATION_MISSING_REASON),
    ):
        raise ValueError("missing_confirmation_count must match rows")
    if report.average_authority_decay_score != _average_decay_score(rows):
        raise ValueError("average_authority_decay_score must match rows")
    if report.max_authority_decay_score != _max_decay_score(rows):
        raise ValueError("max_authority_decay_score must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_signals(
    signals: Any,
) -> tuple[ResearchSourceMemoryScraplingAuthorityDecaySignal, ...]:
    if isinstance(signals, (str, bytes)) or not hasattr(signals, "__iter__"):
        raise ValueError("signals must be an iterable")
    normalized = tuple(signals)
    for item in normalized:
        if type(item) is not ResearchSourceMemoryScraplingAuthorityDecaySignal:
            raise ValueError(
                "signals must contain ResearchSourceMemoryScraplingAuthorityDecaySignal",
            )
        _require_hard_flags("signal", item)
    keys = [(item.group_key, item.entry_key) for item in normalized]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate group_key and entry_key pair")
    return normalized


def _normalize_rows(
    rows: Any,
) -> tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for item in normalized:
        if type(item) is not ResearchSourceMemoryScraplingAuthorityDecayRow:
            raise ValueError(
                "rows must contain ResearchSourceMemoryScraplingAuthorityDecayRow",
            )
        _require_hard_flags("row", item)
    return normalized


def _status_count(
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _average_decay_score(
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_score(
        sum((row.authority_decay_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _max_decay_score(
    rows: tuple[ResearchSourceMemoryScraplingAuthorityDecayRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize_score(max(row.authority_decay_score for row in rows))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize_seconds(seconds + microseconds)


def _reject_future_datetime(field_name: str, value: datetime, generated_at: datetime) -> None:
    if value > generated_at:
        raise ValueError(f"{field_name} cannot be in the future")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_seconds(_require_decimal(field_name, value))
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_seconds(_require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_seconds(_require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_score(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_score(_require_decimal(field_name, value))
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(SECOND_QUANTUM)


def _quantize_seconds(value: Decimal) -> Decimal:
    return value.quantize(SECOND_QUANTUM, rounding=ROUND_HALF_EVEN)


def _quantize_score(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_public_config_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a compact string")
    return value


def _normalize_reason_codes(
    field_name: str,
    values: Any,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in normalized:
        if value not in allowed_values:
            raise ValueError(f"{field_name} contains unknown reason code")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_payload_status_values(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _require_payload_status_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_status_values(item)


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


def _public_payload_without_digest(
    report: ResearchSourceMemoryScraplingAuthorityDecayReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_surface("report payload", payload)
    _reject_public_numerics(payload)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
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
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, bool):
        return
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
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
