"""Report-only event authority source memory floor study.

The module is deterministic and side-effect free. Callers provide observations
from their own research process; the returned report exposes only derived public
keys, aggregate Decimal metrics, statuses, reason codes, and a payload digest.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "authority-source-memory-floor-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28
_PUBLIC_PAYLOAD_FORBIDDEN_FRAGMENTS = (
    "candidate",
    "market",
    "source_url",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommend",
    "question",
    "slug",
)


@dataclass(frozen=True)
class ResearchEventAuthoritySourceMemoryFloorConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_authority_count: Decimal = Decimal("2")
    min_authority_family_count: Decimal = Decimal("2")
    pass_memory_floor: Decimal = Decimal("0.700000")
    watch_memory_floor: Decimal = Decimal("0.400000")
    min_confidence_floor: Decimal = Decimal("0.500000")
    stale_age_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("min_authority_count", "min_authority_family_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_memory_floor",
            "watch_memory_floor",
            "min_confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_memory_floor <= self.watch_memory_floor:
            raise ValueError("pass_memory_floor must be greater than watch_memory_floor")
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventAuthoritySourceMemoryObservation:
    candidate_reference: str
    market_reference: str
    authority_reference: str
    authority_family: str
    observed_at: datetime
    memory_score: Decimal
    confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_canonical_string("market_reference", self.market_reference)
        _require_canonical_string("authority_reference", self.authority_reference)
        _require_canonical_string("authority_family", self.authority_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("memory_score", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventAuthoritySourceMemoryFloorRow:
    event_key: str
    authority_count: Decimal
    authority_family_count: Decimal
    observation_count: Decimal
    memory_floor_score: Decimal
    average_memory_score: Decimal
    confidence_floor_score: Decimal
    newest_age_seconds: Decimal
    stale_authority_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_string("event_key", self.event_key)
        for field_name in (
            "authority_count",
            "authority_family_count",
            "observation_count",
            "stale_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_floor_score",
            "average_memory_score",
            "confidence_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "newest_age_seconds",
            _require_nonnegative_decimal("newest_age_seconds", self.newest_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventAuthoritySourceMemoryFloorReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    authority_observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchEventAuthoritySourceMemoryFloorRow, ...]
    reason_codes: tuple[str, ...]
    payload_sha256: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "authority_observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_public_payload_without_digest(self))
        if self.payload_sha256 == "":
            object.__setattr__(self, "payload_sha256", expected_digest)
        elif self.payload_sha256 != expected_digest:
            raise ValueError("payload_sha256 does not match public payload")
        else:
            _require_digest_string("payload_sha256", self.payload_sha256)


def build_research_event_authority_source_memory_floor_report(
    observations: Iterable[object],
    *,
    config: ResearchEventAuthoritySourceMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchEventAuthoritySourceMemoryFloorReport:
    if type(config) is not ResearchEventAuthoritySourceMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchEventAuthoritySourceMemoryFloorConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchEventAuthoritySourceMemoryObservation]] = {}
    for item in normalized:
        grouped.setdefault(_event_key(item), []).append(item)

    rows = tuple(
        _row_from_event(
            event_key=event_key,
            observations=tuple(grouped[event_key]),
            config=config,
            generated_at=generated_at_utc,
        )
        for event_key in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)

    return ResearchEventAuthoritySourceMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        authority_observation_count=_decimal_count(len(normalized)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        status=_report_status(reason_codes),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_event_authority_source_memory_floor_public_payload(
    report: ResearchEventAuthoritySourceMemoryFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventAuthoritySourceMemoryFloorReport:
        raise ValueError(
            "report must be a ResearchEventAuthoritySourceMemoryFloorReport",
        )
    _require_hard_flags("report", report)
    payload = _public_payload_without_digest(report)
    payload["payload_sha256"] = report.payload_sha256
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    validate_research_event_authority_source_memory_floor_payload(payload)
    return payload


def validate_research_event_authority_source_memory_floor_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    if "payload_sha256" not in payload:
        raise ValueError("payload_sha256 is required")
    digest = payload["payload_sha256"]
    if type(digest) is not str:
        raise ValueError("payload_sha256 must be a string")
    _require_digest_string("payload_sha256", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("payload_sha256")
    if digest != _payload_digest(unsigned_payload):
        raise ValueError("payload_sha256 does not match public payload")
    _validate_payload_statuses(payload)
    return True


def _row_from_event(
    *,
    event_key: str,
    observations: tuple[ResearchEventAuthoritySourceMemoryObservation, ...],
    config: ResearchEventAuthoritySourceMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchEventAuthoritySourceMemoryFloorRow:
    sorted_observations = tuple(
        sorted(
            observations,
            key=lambda item: (
                _authority_key(item),
                item.authority_family,
                item.observed_at.isoformat(),
            ),
        ),
    )
    authority_keys = {_authority_key(item) for item in sorted_observations}
    authority_families = {item.authority_family for item in sorted_observations}
    memory_scores = tuple(item.memory_score for item in sorted_observations)
    confidence_scores = tuple(item.confidence_score for item in sorted_observations)
    newest_observed_at = max(item.observed_at for item in sorted_observations)
    stale_count = sum(
        Decimal(1)
        for item in sorted_observations
        if _age_seconds(generated_at, item.observed_at) >= config.stale_age_seconds
    )
    memory_floor_score = min(memory_scores)
    confidence_floor_score = min(confidence_scores)
    authority_count = _decimal_count(len(authority_keys))
    authority_family_count = _decimal_count(len(authority_families))
    status = _row_status(
        authority_count=authority_count,
        authority_family_count=authority_family_count,
        memory_floor_score=memory_floor_score,
        confidence_floor_score=confidence_floor_score,
        stale_authority_count=_decimal_count(stale_count),
        config=config,
    )
    return ResearchEventAuthoritySourceMemoryFloorRow(
        event_key=event_key,
        authority_count=authority_count,
        authority_family_count=authority_family_count,
        observation_count=_decimal_count(len(sorted_observations)),
        memory_floor_score=memory_floor_score,
        average_memory_score=_average_decimal(memory_scores),
        confidence_floor_score=confidence_floor_score,
        newest_age_seconds=_age_seconds(generated_at, newest_observed_at),
        stale_authority_count=_decimal_count(stale_count),
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            authority_count=authority_count,
            authority_family_count=authority_family_count,
            memory_floor_score=memory_floor_score,
            confidence_floor_score=confidence_floor_score,
            stale_authority_count=_decimal_count(stale_count),
            config=config,
        ),
    )


def _row_status(
    *,
    authority_count: Decimal,
    authority_family_count: Decimal,
    memory_floor_score: Decimal,
    confidence_floor_score: Decimal,
    stale_authority_count: Decimal,
    config: ResearchEventAuthoritySourceMemoryFloorConfig,
) -> str:
    if (
        authority_count < config.min_authority_count
        or authority_family_count < config.min_authority_family_count
        or memory_floor_score < config.watch_memory_floor
        or confidence_floor_score < config.min_confidence_floor
    ):
        return "block"
    if memory_floor_score < config.pass_memory_floor or stale_authority_count > ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    authority_count: Decimal,
    authority_family_count: Decimal,
    memory_floor_score: Decimal,
    confidence_floor_score: Decimal,
    stale_authority_count: Decimal,
    config: ResearchEventAuthoritySourceMemoryFloorConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return ("event_memory_floor_pass",)
    reason_codes: list[str] = []
    if authority_count < config.min_authority_count:
        reason_codes.append("insufficient_authority_count")
    if authority_family_count < config.min_authority_family_count:
        reason_codes.append("insufficient_authority_family_count")
    if memory_floor_score < config.watch_memory_floor:
        reason_codes.append("memory_floor_below_watch")
    elif memory_floor_score < config.pass_memory_floor:
        reason_codes.append("memory_floor_below_pass")
    if confidence_floor_score < config.min_confidence_floor:
        reason_codes.append("confidence_floor_below_minimum")
    if stale_authority_count > ZERO:
        reason_codes.append("stale_authority_observation")
    if not reason_codes:
        reason_codes.append(f"event_memory_floor_{status}")
    return _normalize_reason_codes("reason_codes", reason_codes, allow_empty=False)


def _report_reason_codes(
    rows: tuple[ResearchEventAuthoritySourceMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_event_observations",)
    if any(row.status == "block" for row in rows):
        return ("one_or_more_events_block",)
    if any(row.status == "watch" for row in rows):
        return ("one_or_more_events_watch",)
    return ("all_events_pass_memory_floor",)


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("all_events_pass_memory_floor",):
        return "pass"
    if reason_codes == ("one_or_more_events_watch",):
        return "watch"
    return "block"


def _validate_report_consistency(
    report: ResearchEventAuthoritySourceMemoryFloorReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.event_key)):
        raise ValueError("rows must be sorted by event_key")
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must equal rows length")
    if report.authority_observation_count != sum(
        (row.observation_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("authority_observation_count must equal row observations")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must equal rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must equal rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must equal rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    expected_status = _report_status(expected_reason_codes)
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchEventAuthoritySourceMemoryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventAuthoritySourceMemoryObservation:
            raise ValueError(
                "observations must contain only "
                "ResearchEventAuthoritySourceMemoryObservation values",
            )
        _require_hard_flags("observation", value)
    return values


def _normalize_rows(
    rows: Iterable[ResearchEventAuthoritySourceMemoryFloorRow],
) -> tuple[ResearchEventAuthoritySourceMemoryFloorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEventAuthoritySourceMemoryFloorRow:
            raise ValueError(
                "rows must contain only ResearchEventAuthoritySourceMemoryFloorRow values",
            )
        _require_hard_flags("row", value)
    return values


def _public_payload_without_digest(
    report: ResearchEventAuthoritySourceMemoryFloorReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "event_count": _decimal_payload(report.event_count),
        "authority_observation_count": _decimal_payload(
            report.authority_observation_count,
        ),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchEventAuthoritySourceMemoryFloorRow) -> dict[str, Any]:
    return {
        "event_key": row.event_key,
        "authority_count": _decimal_payload(row.authority_count),
        "authority_family_count": _decimal_payload(row.authority_family_count),
        "observation_count": _decimal_payload(row.observation_count),
        "memory_floor_score": _decimal_payload(row.memory_floor_score),
        "average_memory_score": _decimal_payload(row.average_memory_score),
        "confidence_floor_score": _decimal_payload(row.confidence_floor_score),
        "newest_age_seconds": _decimal_payload(row.newest_age_seconds),
        "stale_authority_count": _decimal_payload(row.stale_authority_count),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")
    status = payload.get("status")
    if status not in STATUSES:
        raise ValueError("status must be pass, watch, or block")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rows must contain dict values")
        row_status = row.get("status")
        if row_status not in STATUSES:
            raise ValueError("row status must be pass, watch, or block")
        if row.get("paper_only") is not True:
            raise ValueError("row paper_only must be True")
        if row.get("report_only") is not True:
            raise ValueError("row report_only must be True")
        if row.get("readonly") is not True:
            raise ValueError("row readonly must be True")


def _reject_unsafe_public_payload(value: object) -> None:
    for item in _walk_public_strings(value):
        normalized = item.lower()
        if any(fragment in normalized for fragment in _PUBLIC_PAYLOAD_FORBIDDEN_FRAGMENTS):
            raise ValueError("public payload contains a raw or sensitive surface")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _walk_public_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            strings.append(key)
            strings.extend(_walk_public_strings(item))
        return tuple(strings)
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_walk_public_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _payload_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _event_key(item: ResearchEventAuthoritySourceMemoryObservation) -> str:
    return _sha256_text(f"{item.candidate_reference}\0{item.market_reference}")


def _authority_key(item: ResearchEventAuthoritySourceMemoryObservation) -> str:
    return _sha256_text(item.authority_reference)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return _quantize(_require_nonnegative_decimal("newest_age_seconds", seconds))


def _status_count(
    rows: tuple[ResearchEventAuthoritySourceMemoryFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _decimal_count(value: int | Decimal) -> Decimal:
    return _quantize(Decimal(value))


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(QUANTUM)


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        _require_canonical_string(field_name, value)
    return tuple(sorted(set(values)))


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "ResearchEventAuthoritySourceMemoryFloorConfig",
    "ResearchEventAuthoritySourceMemoryObservation",
    "ResearchEventAuthoritySourceMemoryFloorReport",
    "ResearchEventAuthoritySourceMemoryFloorRow",
    "build_research_event_authority_source_memory_floor_report",
    "research_event_authority_source_memory_floor_public_payload",
    "validate_research_event_authority_source_memory_floor_payload",
)
