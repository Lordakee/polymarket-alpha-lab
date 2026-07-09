"""Report-only event authority memory-decay research snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_EVENT_AUTHORITY_MEMORY_DECAY_CONFIG_VERSION = (
    "research-event-authority-memory-decay-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REASON_CODE_SEQUENCE = (
    "memory_block",
    "memory_watch",
    "authority_below_watch",
    "authority_below_pass",
    "parse_uncertainty",
    "contradiction_pressure",
    "authority_memory_pass",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "http",
    "://",
    "text",
    "dsn",
    "database",
    "db",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "live",
    "network",
    "sizing",
    "recommendation",
    "credential",
    "secret",
    "oauth",
    "auth_token",
)


@dataclass(frozen=True)
class EventSourceAuthorityMemoryDecayConfig:
    config_version: str = DEFAULT_EVENT_AUTHORITY_MEMORY_DECAY_CONFIG_VERSION
    authority_memory_watch_seconds: Decimal = Decimal("604800.000000")
    authority_memory_block_seconds: Decimal = Decimal("1209600.000000")
    memory_decay_weight: Decimal = Decimal("0.500000")
    min_pass_effective_authority_score: Decimal = Decimal("0.700000")
    min_watch_effective_authority_score: Decimal = Decimal("0.450000")
    min_parse_confidence: Decimal = Decimal("0.600000")
    contradiction_block_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventSourceAuthorityMemoryDecayConfig:
            raise TypeError(
                "EventSourceAuthorityMemoryDecayConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not EventSourceAuthorityMemoryDecayConfig:
            raise ValueError(
                "config must be exactly EventSourceAuthorityMemoryDecayConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_EVENT_AUTHORITY_MEMORY_DECAY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for name in (
            "authority_memory_watch_seconds",
            "authority_memory_block_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        if self.authority_memory_block_seconds <= self.authority_memory_watch_seconds:
            raise ValueError(
                "authority_memory_block_seconds must exceed "
                "authority_memory_watch_seconds",
            )
        for name in (
            "memory_decay_weight",
            "min_pass_effective_authority_score",
            "min_watch_effective_authority_score",
            "min_parse_confidence",
            "contradiction_block_ratio",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if (
            self.min_pass_effective_authority_score
            < self.min_watch_effective_authority_score
        ):
            raise ValueError(
                "min_pass_effective_authority_score must be at least "
                "min_watch_effective_authority_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class EventAuthorityObservation:
    event_ref_digest: str
    authority_ref_digest: str
    observed_at: datetime
    authority_score: Decimal
    parse_confidence: Decimal
    confirmation_count: Decimal
    contradiction_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EventAuthorityObservation:
            raise TypeError("EventAuthorityObservation does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not EventAuthorityObservation:
            raise ValueError("observation must be exactly EventAuthorityObservation")
        _require_sha256_digest("event_ref_digest", self.event_ref_digest)
        _require_sha256_digest("authority_ref_digest", self.authority_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in ("authority_score", "parse_confidence"):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in ("confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceAuthorityMemoryDecayRow:
    event_ref_digest: str
    authority_ref_digest: str
    observed_at: datetime
    memory_age_seconds: Decimal
    memory_decay_ratio: Decimal
    authority_score: Decimal
    parse_confidence: Decimal
    confirmation_count: Decimal
    contradiction_count: Decimal
    contradiction_ratio: Decimal
    effective_authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceAuthorityMemoryDecayRow:
            raise TypeError(
                "ResearchEventSourceAuthorityMemoryDecayRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceAuthorityMemoryDecayRow:
            raise ValueError(
                "row must be exactly ResearchEventSourceAuthorityMemoryDecayRow",
            )
        _require_sha256_digest("event_ref_digest", self.event_ref_digest)
        _require_sha256_digest("authority_ref_digest", self.authority_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "memory_age_seconds",
            "confirmation_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "memory_decay_ratio",
            "authority_score",
            "parse_confidence",
            "contradiction_ratio",
            "effective_authority_score",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventSourceAuthorityMemoryDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_memory_count: Decimal
    low_authority_count: Decimal
    parse_uncertainty_count: Decimal
    contradiction_pressure_count: Decimal
    max_memory_age_seconds: Decimal
    average_effective_authority_score: Decimal
    rows: tuple[ResearchEventSourceAuthorityMemoryDecayRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceAuthorityMemoryDecayReport:
            raise TypeError(
                "ResearchEventSourceAuthorityMemoryDecayReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceAuthorityMemoryDecayReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventSourceAuthorityMemoryDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_EVENT_AUTHORITY_MEMORY_DECAY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_memory_count",
            "low_authority_count",
            "parse_uncertainty_count",
            "contradiction_pressure_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _require_nonnegative_decimal(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "average_effective_authority_score",
            _require_ratio_decimal(
                "average_effective_authority_score",
                self.average_effective_authority_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
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
            "ResearchEventSourceAuthorityMemoryDecayReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_source_authority_memory_decay_report(
    observations: Sequence[EventAuthorityObservation],
    *,
    generated_at: datetime,
    config: EventSourceAuthorityMemoryDecayConfig | None = None,
) -> ResearchEventSourceAuthorityMemoryDecayReport:
    """Build a local, readonly report for authority memory-decay research."""

    if config is None:
        config = EventSourceAuthorityMemoryDecayConfig()
    if type(config) is not EventSourceAuthorityMemoryDecayConfig:
        raise ValueError("config must be exactly EventSourceAuthorityMemoryDecayConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation=observation,
                    generated_at=generated_at,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "observation_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "stale_memory_count": _decimal_count(
            sum(
                1
                for row in rows
                if "memory_watch" in row.reason_codes
                or "memory_block" in row.reason_codes
            ),
        ),
        "low_authority_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.effective_authority_score
                < config.min_pass_effective_authority_score
            ),
        ),
        "parse_uncertainty_count": _reason_count(rows, "parse_uncertainty"),
        "contradiction_pressure_count": _reason_count(rows, "contradiction_pressure"),
        "max_memory_age_seconds": max(
            (row.memory_age_seconds for row in rows),
            default=_ZERO,
        ),
        "average_effective_authority_score": _average(
            tuple(row.effective_authority_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventSourceAuthorityMemoryDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def validate_research_event_source_authority_memory_decay_public_payload(
    payload: Mapping[str, object],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "research_event_source_authority_memory_decay_public_payload",
        payload,
        allow_json_containers=True,
    )
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest")
    expected_digest = sha256_public_payload_digest(payload_without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return True


def sha256_public_payload_digest(payload: Mapping[str, object]) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    ready = _json_ready(dict(payload))
    _reject_unsafe_public_payload(
        "research_event_source_authority_memory_decay_public_payload",
        ready,
        allow_json_containers=True,
    )
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_observation(
    *,
    observation: EventAuthorityObservation,
    generated_at: datetime,
    config: EventSourceAuthorityMemoryDecayConfig,
) -> ResearchEventSourceAuthorityMemoryDecayRow:
    memory_age_seconds = _elapsed_seconds_decimal(generated_at, observation.observed_at)
    memory_decay_ratio = _clamp_ratio(
        memory_age_seconds / config.authority_memory_block_seconds,
    )
    contradiction_ratio = _contradiction_ratio(
        observation.confirmation_count,
        observation.contradiction_count,
    )
    effective_authority_score = _clamp_ratio(
        observation.authority_score * (_ONE - memory_decay_ratio * config.memory_decay_weight),
    )
    status = _row_status(
        memory_age_seconds=memory_age_seconds,
        effective_authority_score=effective_authority_score,
        parse_confidence=observation.parse_confidence,
        contradiction_ratio=contradiction_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        memory_age_seconds=memory_age_seconds,
        effective_authority_score=effective_authority_score,
        parse_confidence=observation.parse_confidence,
        contradiction_ratio=contradiction_ratio,
        config=config,
        status=status,
    )
    return ResearchEventSourceAuthorityMemoryDecayRow(
        event_ref_digest=observation.event_ref_digest,
        authority_ref_digest=observation.authority_ref_digest,
        observed_at=observation.observed_at,
        memory_age_seconds=memory_age_seconds,
        memory_decay_ratio=memory_decay_ratio,
        authority_score=observation.authority_score,
        parse_confidence=observation.parse_confidence,
        confirmation_count=observation.confirmation_count,
        contradiction_count=observation.contradiction_count,
        contradiction_ratio=contradiction_ratio,
        effective_authority_score=effective_authority_score,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    *,
    memory_age_seconds: Decimal,
    effective_authority_score: Decimal,
    parse_confidence: Decimal,
    contradiction_ratio: Decimal,
    config: EventSourceAuthorityMemoryDecayConfig,
) -> str:
    if (
        memory_age_seconds >= config.authority_memory_block_seconds
        or effective_authority_score < config.min_watch_effective_authority_score
        or parse_confidence < config.min_parse_confidence
        or contradiction_ratio >= config.contradiction_block_ratio
    ):
        return "block"
    if (
        memory_age_seconds >= config.authority_memory_watch_seconds
        or effective_authority_score < config.min_pass_effective_authority_score
        or contradiction_ratio > _ZERO
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    memory_age_seconds: Decimal,
    effective_authority_score: Decimal,
    parse_confidence: Decimal,
    contradiction_ratio: Decimal,
    config: EventSourceAuthorityMemoryDecayConfig,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_age_seconds >= config.authority_memory_block_seconds:
        reason_codes.append("memory_block")
    elif memory_age_seconds >= config.authority_memory_watch_seconds:
        reason_codes.append("memory_watch")
    if effective_authority_score < config.min_watch_effective_authority_score:
        reason_codes.append("authority_below_watch")
    elif effective_authority_score < config.min_pass_effective_authority_score:
        reason_codes.append("authority_below_pass")
    if parse_confidence < config.min_parse_confidence:
        reason_codes.append("parse_uncertainty")
    if contradiction_ratio >= config.contradiction_block_ratio:
        reason_codes.append("contradiction_pressure")
    if status == "pass" and not reason_codes:
        reason_codes.append("authority_memory_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _contradiction_ratio(
    confirmation_count: Decimal,
    contradiction_count: Decimal,
) -> Decimal:
    total_count = confirmation_count + contradiction_count
    if total_count == _ZERO:
        return _ZERO
    return _clamp_ratio(contradiction_count / total_count)


def _report_status(rows: tuple[ResearchEventSourceAuthorityMemoryDecayRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventSourceAuthorityMemoryDecayRow, ...],
) -> tuple[str, ...]:
    reason_codes = {code for row in rows for code in row.reason_codes}
    if not reason_codes:
        reason_codes.add("authority_memory_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Sequence[EventAuthorityObservation],
) -> tuple[EventAuthorityObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be a sequence of EventAuthorityObservation")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not EventAuthorityObservation:
            raise ValueError(
                "observations must contain only EventAuthorityObservation items",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchEventSourceAuthorityMemoryDecayRow],
) -> tuple[ResearchEventSourceAuthorityMemoryDecayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError(
            "rows must be a sequence of ResearchEventSourceAuthorityMemoryDecayRow",
        )
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventSourceAuthorityMemoryDecayRow:
            raise ValueError(
                "rows must contain only ResearchEventSourceAuthorityMemoryDecayRow items",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchEventSourceAuthorityMemoryDecayRow) -> tuple[str, str]:
    return (row.event_ref_digest, row.authority_ref_digest)


def _status_count(
    rows: tuple[ResearchEventSourceAuthorityMemoryDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchEventSourceAuthorityMemoryDecayRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a sequence of strings")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("unsupported reason_code")
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: _REASON_CODE_SEQUENCE.index(reason_code),
        ),
    )


def _validate_row_consistency(row: ResearchEventSourceAuthorityMemoryDecayRow) -> None:
    if row.status == "pass" and row.reason_codes != ("authority_memory_pass",):
        raise ValueError("pass row reason_codes must only include authority_memory_pass")
    block_reasons = {
        "memory_block",
        "authority_below_watch",
        "parse_uncertainty",
        "contradiction_pressure",
    }
    if row.status == "block" and not any(
        reason_code in block_reasons for reason_code in row.reason_codes
    ):
        raise ValueError("block row must include a block reason")
    if row.status == "watch" and (
        not row.reason_codes or any(reason_code in block_reasons for reason_code in row.reason_codes)
    ):
        raise ValueError("watch row must include only watch reasons")


def _validate_report_consistency(
    report: ResearchEventSourceAuthorityMemoryDecayReport,
) -> None:
    rows = report.rows
    if report.observation_count != _decimal_count(len(rows)):
        raise ValueError("observation_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must equal pass row count")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must equal watch row count")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must equal block row count")
    if report.stale_memory_count != _decimal_count(
        sum(
            1
            for row in rows
            if "memory_watch" in row.reason_codes or "memory_block" in row.reason_codes
        ),
    ):
        raise ValueError("stale_memory_count must equal stale-memory row count")
    if report.low_authority_count != _decimal_count(
        sum(1 for row in rows if "authority_below_pass" in row.reason_codes),
    ) + _decimal_count(
        sum(1 for row in rows if "authority_below_watch" in row.reason_codes),
    ):
        raise ValueError("low_authority_count must equal low-authority row count")
    if report.parse_uncertainty_count != _reason_count(rows, "parse_uncertainty"):
        raise ValueError("parse_uncertainty_count must equal row reason count")
    if report.contradiction_pressure_count != _reason_count(rows, "contradiction_pressure"):
        raise ValueError("contradiction_pressure_count must equal row reason count")
    if report.max_memory_age_seconds != max(
        (row.memory_age_seconds for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_memory_age_seconds must equal max row age")
    if report.average_effective_authority_score != _average(
        tuple(row.effective_authority_score for row in rows),
    ):
        raise ValueError(
            "average_effective_authority_score must equal average row score",
        )
    if report.status != _report_status(rows):
        raise ValueError("status must equal aggregate row status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must equal aggregate row reasons")


def _report_values_without_digest(
    report: ResearchEventSourceAuthorityMemoryDecayReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    return sha256_public_payload_digest(_json_ready(values))


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric values must use Decimal")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize_decimal(sum(values, _ZERO) / _decimal_count(len(values)))


def _elapsed_seconds_decimal(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    whole_seconds = Decimal(delta.days) * _SECONDS_PER_DAY + Decimal(delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize_decimal(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return value


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return value


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_public_identifier(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _require_status(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public surface in {label}")
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is str and _SHA256_RE.fullmatch(value):
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public surface in {label}")
    if not allow_json_containers:
        for field in fields(value):  # type: ignore[arg-type]
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"unsafe public surface in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
