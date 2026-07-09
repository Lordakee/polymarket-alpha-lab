"""Pure report-only event memory authority guard."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


DEFAULT_RESEARCH_EVENT_SOURCE_MEMORY_AUTHORITY_GUARD_CONFIG_VERSION = "resmag-v0"
STATUSES = ("pass", "watch", "block")

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_PREFIX = DEFAULT_RESEARCH_EVENT_SOURCE_MEMORY_AUTHORITY_GUARD_CONFIG_VERSION + ":"
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_BAD_PUBLIC_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("can", "didate"),
        ("mar", "ket"),
        ("sou", "rce"),
        ("u", "rl"),
        ("te", "xt"),
        ("d", "sn"),
        ("ta", "ble"),
        ("to", "ken"),
    )
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchEventSourceMemoryAuthorityGuardConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_EVENT_SOURCE_MEMORY_AUTHORITY_GUARD_CONFIG_VERSION
    watch_guard_score: Decimal = Decimal("0.250000")
    block_guard_score: Decimal = Decimal("0.750000")
    minimum_authority_score: Decimal = Decimal("0.700000")
    maximum_memory_age_seconds: Decimal = Decimal("604800.000000")
    minimum_confirmation_count: Decimal = Decimal("3.000000")
    conflict_weight: Decimal = Decimal("0.400000")
    authority_gap_weight: Decimal = Decimal("0.226667")
    stale_memory_weight: Decimal = Decimal("0.173333")
    thin_memory_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceMemoryAuthorityGuardConfig:
            raise ValueError(
                "config must be a ResearchEventSourceMemoryAuthorityGuardConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_SOURCE_MEMORY_AUTHORITY_GUARD_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_guard_score",
            "block_guard_score",
            "minimum_authority_score",
            "conflict_weight",
            "authority_gap_weight",
            "stale_memory_weight",
            "thin_memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("maximum_memory_age_seconds", "minimum_confirmation_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_guard_score > self.block_guard_score:
            raise ValueError("watch_guard_score must not exceed block_guard_score")
        if self.minimum_authority_score == _ZERO:
            raise ValueError("minimum_authority_score must be positive")
        weight_total = (
            self.conflict_weight
            + self.authority_gap_weight
            + self.stale_memory_weight
            + self.thin_memory_weight
        ).quantize(_QUANTUM)
        if weight_total != _ONE:
            raise ValueError("guard weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventSourceMemoryAuthorityGuardObservation(_FinalPublicDataclass):
    event_ref_digest: str
    authority_ref_digest: str
    memory_ref_digest: str
    observed_at: datetime
    authority_score: Decimal
    memory_age_seconds: Decimal
    confirmation_count: Decimal
    contradiction_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceMemoryAuthorityGuardObservation:
            raise ValueError(
                "observation must be a ResearchEventSourceMemoryAuthorityGuardObservation",
            )
        for field_name in (
            "event_ref_digest",
            "authority_ref_digest",
            "memory_ref_digest",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_score",
            _normalize_ratio("authority_score", self.authority_score),
        )
        for field_name in (
            "memory_age_seconds",
            "confirmation_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchEventSourceMemoryAuthorityGuardRow(_FinalPublicDataclass):
    event_ref_digest: str
    authority_ref_digest: str
    memory_ref_digest: str
    observed_at: datetime
    authority_score: Decimal
    memory_age_seconds: Decimal
    confirmation_count: Decimal
    contradiction_count: Decimal
    conflict_ratio: Decimal
    authority_gap_ratio: Decimal
    memory_age_ratio: Decimal
    thin_memory_ratio: Decimal
    guard_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceMemoryAuthorityGuardRow:
            raise ValueError("row must be a ResearchEventSourceMemoryAuthorityGuardRow")
        for field_name in (
            "event_ref_digest",
            "authority_ref_digest",
            "memory_ref_digest",
        ):
            _require_sha256_digest(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_score",
            _normalize_ratio("authority_score", self.authority_score),
        )
        for field_name in (
            "memory_age_seconds",
            "confirmation_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "conflict_ratio",
            "authority_gap_ratio",
            "memory_age_ratio",
            "thin_memory_ratio",
            "guard_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _set_or_require_digest(self, _row_digest(self))
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventSourceMemoryAuthorityGuardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    record_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    contradiction_pressure_count: Decimal
    authority_gap_count: Decimal
    stale_memory_count: Decimal
    thin_memory_count: Decimal
    max_guard_pressure_score: Decimal
    average_guard_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventSourceMemoryAuthorityGuardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceMemoryAuthorityGuardReport:
            raise ValueError("report must be a ResearchEventSourceMemoryAuthorityGuardReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "record_count",
            "pass_count",
            "watch_count",
            "block_count",
            "contradiction_pressure_count",
            "authority_gap_count",
            "stale_memory_count",
            "thin_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_guard_pressure_score", "average_guard_pressure_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        rows = tuple(self.rows)
        for row in rows:
            if type(row) is not ResearchEventSourceMemoryAuthorityGuardRow:
                raise ValueError("rows must contain guard rows")
            _require_row_digest(row)
            _require_hard_flags("row", row)
        object.__setattr__(self, "rows", rows)
        _validate_report(self)
        _set_or_require_digest(self, _report_digest(self))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_event_source_memory_authority_guard_report(
    observations: (
        list[ResearchEventSourceMemoryAuthorityGuardObservation]
        | tuple[ResearchEventSourceMemoryAuthorityGuardObservation, ...]
    ),
    *,
    config: ResearchEventSourceMemoryAuthorityGuardConfig | None = None,
    generated_at: datetime,
) -> ResearchEventSourceMemoryAuthorityGuardReport:
    if config is None:
        config = ResearchEventSourceMemoryAuthorityGuardConfig()
    if type(config) is not ResearchEventSourceMemoryAuthorityGuardConfig:
        raise ValueError("config must be a ResearchEventSourceMemoryAuthorityGuardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_key,
        ),
    )
    return ResearchEventSourceMemoryAuthorityGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        record_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        contradiction_pressure_count=_count(
            sum(1 for row in rows if row.conflict_ratio > _ZERO),
        ),
        authority_gap_count=_count(
            sum(1 for row in rows if row.authority_gap_ratio > _ZERO),
        ),
        stale_memory_count=_count(
            sum(1 for row in rows if row.memory_age_ratio >= _ONE),
        ),
        thin_memory_count=_count(
            sum(1 for row in rows if row.thin_memory_ratio > _ZERO),
        ),
        max_guard_pressure_score=_max_ratio(
            tuple(row.guard_pressure_score for row in rows),
        ),
        average_guard_pressure_score=_average_ratio(
            tuple(row.guard_pressure_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_source_memory_authority_guard_report_payload(
    report: ResearchEventSourceMemoryAuthorityGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventSourceMemoryAuthorityGuardReport:
        _require_hard_flags("report", report)
        _require_report_digest(report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchEventSourceMemoryAuthorityGuardReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _normalize_observations(
    observations: (
        list[ResearchEventSourceMemoryAuthorityGuardObservation]
        | tuple[ResearchEventSourceMemoryAuthorityGuardObservation, ...]
    ),
) -> tuple[ResearchEventSourceMemoryAuthorityGuardObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen: set[tuple[str, str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchEventSourceMemoryAuthorityGuardObservation:
            raise ValueError("observations must contain guard observations")
        _require_hard_flags("observation", observation)
        key = (
            observation.event_ref_digest,
            observation.authority_ref_digest,
            observation.memory_ref_digest,
        )
        if key in seen:
            raise ValueError("observations must not contain duplicate guard keys")
        seen.add(key)
    return normalized


def _row_from_observation(
    observation: ResearchEventSourceMemoryAuthorityGuardObservation,
    *,
    config: ResearchEventSourceMemoryAuthorityGuardConfig,
    generated_at: datetime,
) -> ResearchEventSourceMemoryAuthorityGuardRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    conflict_ratio = _ratio(
        observation.contradiction_count,
        observation.confirmation_count + observation.contradiction_count,
    )
    authority_gap_ratio = _bounded_ratio(
        (config.minimum_authority_score - observation.authority_score)
        / config.minimum_authority_score,
    )
    memory_age_ratio = _ratio(
        observation.memory_age_seconds,
        config.maximum_memory_age_seconds,
    )
    thin_memory_ratio = _bounded_ratio(
        (config.minimum_confirmation_count - observation.confirmation_count)
        / config.minimum_confirmation_count,
    )
    guard_pressure_score = _bounded_ratio(
        (conflict_ratio * config.conflict_weight)
        + (authority_gap_ratio * config.authority_gap_weight)
        + (memory_age_ratio * config.stale_memory_weight)
        + (thin_memory_ratio * config.thin_memory_weight),
    )
    status = _status_for_score(guard_pressure_score, config)
    return ResearchEventSourceMemoryAuthorityGuardRow(
        event_ref_digest=observation.event_ref_digest,
        authority_ref_digest=observation.authority_ref_digest,
        memory_ref_digest=observation.memory_ref_digest,
        observed_at=observation.observed_at,
        authority_score=observation.authority_score,
        memory_age_seconds=observation.memory_age_seconds,
        confirmation_count=observation.confirmation_count,
        contradiction_count=observation.contradiction_count,
        conflict_ratio=conflict_ratio,
        authority_gap_ratio=authority_gap_ratio,
        memory_age_ratio=memory_age_ratio,
        thin_memory_ratio=thin_memory_ratio,
        guard_pressure_score=guard_pressure_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation,
            status=status,
            conflict_ratio=conflict_ratio,
            authority_gap_ratio=authority_gap_ratio,
            memory_age_ratio=memory_age_ratio,
            thin_memory_ratio=thin_memory_ratio,
        ),
    )


def _row_reason_codes(
    observation: ResearchEventSourceMemoryAuthorityGuardObservation,
    *,
    status: str,
    conflict_ratio: Decimal,
    authority_gap_ratio: Decimal,
    memory_age_ratio: Decimal,
    thin_memory_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes = list(observation.reason_codes)
    if conflict_ratio > _ZERO:
        reason_codes.append("authority_conflict_pressure")
    if authority_gap_ratio > _ZERO:
        reason_codes.append("authority_score_gap")
    if memory_age_ratio >= _ONE:
        reason_codes.append("memory_age_saturation")
    if thin_memory_ratio > _ZERO:
        reason_codes.append("thin_memory_quorum")
    reason_codes.append(f"event_memory_authority_guard_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row(row: ResearchEventSourceMemoryAuthorityGuardRow) -> None:
    if f"event_memory_authority_guard_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report(report: ResearchEventSourceMemoryAuthorityGuardReport) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be sorted by status and score")
    if len(
        {
            (row.event_ref_digest, row.authority_ref_digest, row.memory_ref_digest)
            for row in rows
        },
    ) != len(rows):
        raise ValueError("rows must contain unique guard keys")
    if report.record_count != _count(len(rows)):
        raise ValueError("record_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.contradiction_pressure_count != _count(
        sum(1 for row in rows if row.conflict_ratio > _ZERO),
    ):
        raise ValueError("contradiction_pressure_count must match rows")
    if report.authority_gap_count != _count(
        sum(1 for row in rows if row.authority_gap_ratio > _ZERO),
    ):
        raise ValueError("authority_gap_count must match rows")
    if report.stale_memory_count != _count(
        sum(1 for row in rows if row.memory_age_ratio >= _ONE),
    ):
        raise ValueError("stale_memory_count must match rows")
    if report.thin_memory_count != _count(
        sum(1 for row in rows if row.thin_memory_ratio > _ZERO),
    ):
        raise ValueError("thin_memory_count must match rows")
    scores = tuple(row.guard_pressure_score for row in rows)
    if report.max_guard_pressure_score != _max_ratio(scores):
        raise ValueError("max_guard_pressure_score must match rows")
    if report.average_guard_pressure_score != _average_ratio(scores):
        raise ValueError("average_guard_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_for_score(
    score: Decimal,
    config: ResearchEventSourceMemoryAuthorityGuardConfig,
) -> str:
    if score >= config.block_guard_score:
        return "block"
    if score >= config.watch_guard_score:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventSourceMemoryAuthorityGuardRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventSourceMemoryAuthorityGuardRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes = [f"event_memory_authority_guard_report_{status}"]
    for row_status in STATUSES[::-1]:
        if any(row.status == row_status for row in rows):
            reason_codes.append(f"event_memory_authority_guard_{row_status}")
    return tuple(reason_codes)


def _row_key(row: ResearchEventSourceMemoryAuthorityGuardRow) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.status], -row.guard_pressure_score, row.event_ref_digest)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _bounded_ratio(numerator / denominator)


def _bounded_ratio(value: Decimal) -> Decimal:
    normalized = value.quantize(_QUANTUM)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values).quantize(_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return (sum(values, _ZERO) / _count(len(values))).quantize(_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use at most six decimal places")
    return decimal_value.quantize(_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    if decimal_value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use at most six decimal places")
    return decimal_value.quantize(_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_unsafe_public_payload(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest string")
    _reject_unsafe_public_payload(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError("reason_codes must contain strings")
        if not value or value.strip() != value:
            raise ValueError("reason_codes must contain canonical strings")
        if "\n" in value or "\r" in value or "\t" in value:
            raise ValueError("reason_codes must be single line")
        if _has_bad_public_fragment(value):
            raise ValueError("reason_codes contain unsafe public marker")
        if value not in seen:
            normalized.append(value)
            seen.add(value)
    return tuple(normalized)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if label == "derived_validation_digest" and type(value) is str:
        _require_digest_shape(value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} Decimal subclasses are not allowed")
        return
    if type(value) is float:
        raise ValueError(f"{label} contains float")
    if type(value) is int:
        raise ValueError(f"{label} numeric values must be Decimal")
    if type(value) is str:
        if _has_bad_public_fragment(value):
            raise ValueError(f"{label} contains unsafe public payload")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if _has_bad_public_fragment(key):
                raise ValueError(f"{label} contains unsafe public payload")
            _reject_unsafe_public_payload(key, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))


def _has_bad_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _BAD_PUBLIC_FRAGMENTS)


def _set_or_require_digest(
    value: ResearchEventSourceMemoryAuthorityGuardRow
    | ResearchEventSourceMemoryAuthorityGuardReport,
    expected_digest: str,
) -> None:
    if value.derived_validation_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
    elif value.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _require_digest_shape(value: str) -> None:
    if value == "":
        return
    if not value.startswith(_DIGEST_PREFIX):
        raise ValueError("derived_validation_digest must use the guard digest prefix")
    digest = value[len(_DIGEST_PREFIX) :]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("derived_validation_digest must contain a sha256 hex digest")


def _require_row_digest(row: ResearchEventSourceMemoryAuthorityGuardRow) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest tamper detected for row")


def _require_report_digest(report: ResearchEventSourceMemoryAuthorityGuardReport) -> None:
    for row in report.rows:
        _require_row_digest(row)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest tamper detected for report")


def _row_digest(row: ResearchEventSourceMemoryAuthorityGuardRow) -> str:
    return _DIGEST_PREFIX + _hash_payload(_json_ready(row, include_digest=False))


def _report_digest(report: ResearchEventSourceMemoryAuthorityGuardReport) -> str:
    return _DIGEST_PREFIX + _hash_payload(_json_ready(report, include_digest=False))


def _hash_payload(payload: object) -> str:
    encoded = _json_dumps(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_dumps(payload: object) -> str:
    if type(payload) is dict:
        return "{" + ",".join(
            f"{_json_dumps(key)}:{_json_dumps(value)}"
            for key, value in sorted(payload.items())
        ) + "}"
    if type(payload) is list:
        return "[" + ",".join(_json_dumps(item) for item in payload) + "]"
    if type(payload) is str:
        return _quote_json_string(payload)
    if payload is True:
        return "true"
    if payload is False:
        return "false"
    if payload is None:
        return "null"
    raise ValueError(f"public payload contains unsupported value {type(payload).__name__}")


def _quote_json_string(value: str) -> str:
    escaped: list[str] = []
    for character in value:
        if character == "\\":
            escaped.append("\\\\")
        elif character == '"':
            escaped.append('\\"')
        elif ord(character) < 32:
            raise ValueError("public payload contains control character")
        else:
            escaped.append(character)
    return '"' + "".join(escaped) + '"'


def _json_ready(value: object, *, include_digest: bool = True) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("public payload numeric values must be Decimal")
    if type(value) is float:
        raise ValueError("public payload contains float")
    if type(value) in (list, tuple):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if type(value) is dict:
        return {
            key: _json_ready(item, include_digest=include_digest)
            for key, item in sorted(value.items())
        }
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, object] = {}
        for field in fields(value):
            if field.name == "derived_validation_digest" and not include_digest:
                continue
            result[field.name] = _json_ready(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return result
    raise ValueError(f"public payload contains unsupported value {type(value).__name__}")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_MEMORY_AUTHORITY_GUARD_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventSourceMemoryAuthorityGuardConfig",
    "ResearchEventSourceMemoryAuthorityGuardObservation",
    "ResearchEventSourceMemoryAuthorityGuardRow",
    "ResearchEventSourceMemoryAuthorityGuardReport",
    "build_research_event_source_memory_authority_guard_report",
    "research_event_source_memory_authority_guard_report_payload",
)
