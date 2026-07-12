from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any, Mapping


SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_STATUSES = (
    "ready",
    "attention",
    "blocked",
)
SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_REASON_CODES = (
    "team_memory_missing",
    "similar_market_count_missing",
    "recent_calibration_missing",
    "source_family_history_missing",
    "retrieval_latency_blocked",
    "schema_version_missing",
    "similar_market_count_below_ready",
    "recent_calibration_count_below_ready",
    "source_family_history_count_below_ready",
    "retrieval_latency_watch",
    "team_memory_retrieval_ready",
)

_PUBLIC_DATACLASS_NAMES = (
    "SpecialistTeamDomainMemoryRetrievalReadinessInput",
    "SpecialistTeamDomainMemoryRetrievalReadinessReport",
)
_DECIMAL_QUANTUM = Decimal("0.000000")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MIN_READY_SIMILAR_MARKET_COUNT = Decimal("3.000000")
_MIN_READY_RECENT_CALIBRATION_COUNT = Decimal("2.000000")
_MIN_READY_SOURCE_FAMILY_HISTORY_COUNT = Decimal("2.000000")
_MAX_READY_RETRIEVAL_LATENCY_MS = Decimal("500.000000")
_MAX_WATCH_RETRIEVAL_LATENCY_MS = Decimal("1000.000000")
_HEX_DIGITS = frozenset("0123456789abcdef")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in _PUBLIC_DATACLASS_NAMES:
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class SpecialistTeamDomainMemoryRetrievalReadinessInput(_FinalPublicDataclass):
    team_memory_exists: bool
    similar_market_count: Decimal
    recent_calibration_count: Decimal
    source_family_history_count: Decimal
    retrieval_latency_ms: Decimal
    schema_version_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamDomainMemoryRetrievalReadinessInput,
            "readiness",
        )
        _require_bool("team_memory_exists", self.team_memory_exists)
        _require_bool("schema_version_present", self.schema_version_present)
        for field_name in (
            "similar_market_count",
            "recent_calibration_count",
            "source_family_history_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "retrieval_latency_ms",
            _nonnegative_decimal("retrieval_latency_ms", self.retrieval_latency_ms),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class SpecialistTeamDomainMemoryRetrievalReadinessReport(_FinalPublicDataclass):
    team_memory_exists: bool
    similar_market_count: Decimal
    recent_calibration_count: Decimal
    source_family_history_count: Decimal
    retrieval_latency_ms: Decimal
    schema_version_present: bool
    retrieval_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamDomainMemoryRetrievalReadinessReport,
            "report",
        )
        _require_bool("team_memory_exists", self.team_memory_exists)
        _require_bool("schema_version_present", self.schema_version_present)
        for field_name in (
            "similar_market_count",
            "recent_calibration_count",
            "source_family_history_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "retrieval_latency_ms",
            _nonnegative_decimal("retrieval_latency_ms", self.retrieval_latency_ms),
        )
        _require_status(self.retrieval_status)
        object.__setattr__(
            self,
            "reason_codes",
            _reason_code_tuple(self.reason_codes),
        )
        _require_public_text("manual_next_step", self.manual_next_step)
        _require_hard_flags(self)
        expected_status, expected_reasons, expected_step = _findings_from_values(
            team_memory_exists=self.team_memory_exists,
            similar_market_count=self.similar_market_count,
            recent_calibration_count=self.recent_calibration_count,
            source_family_history_count=self.source_family_history_count,
            retrieval_latency_ms=self.retrieval_latency_ms,
            schema_version_present=self.schema_version_present,
        )
        if self.retrieval_status != expected_status:
            raise ValueError("retrieval_status must match readiness inputs")
        if self.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match readiness inputs")
        if self.manual_next_step != expected_step:
            raise ValueError("manual_next_step must match retrieval_status")
        _require_digest("payload_digest", self.payload_digest)
        if self.payload_digest != _report_digest(self):
            raise ValueError("payload_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_domain_memory_retrieval_readiness_report_payload(self)


def build_specialist_team_domain_memory_retrieval_readiness_report(
    readiness: SpecialistTeamDomainMemoryRetrievalReadinessInput,
) -> SpecialistTeamDomainMemoryRetrievalReadinessReport:
    if type(readiness) is not SpecialistTeamDomainMemoryRetrievalReadinessInput:
        raise ValueError(
            "readiness must be a SpecialistTeamDomainMemoryRetrievalReadinessInput",
        )
    _require_hard_flags(readiness)
    retrieval_status, reason_codes, manual_next_step = _findings_from_values(
        team_memory_exists=readiness.team_memory_exists,
        similar_market_count=readiness.similar_market_count,
        recent_calibration_count=readiness.recent_calibration_count,
        source_family_history_count=readiness.source_family_history_count,
        retrieval_latency_ms=readiness.retrieval_latency_ms,
        schema_version_present=readiness.schema_version_present,
    )
    report_values: dict[str, object] = {
        "team_memory_exists": readiness.team_memory_exists,
        "similar_market_count": readiness.similar_market_count,
        "recent_calibration_count": readiness.recent_calibration_count,
        "source_family_history_count": readiness.source_family_history_count,
        "retrieval_latency_ms": readiness.retrieval_latency_ms,
        "schema_version_present": readiness.schema_version_present,
        "retrieval_status": retrieval_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SpecialistTeamDomainMemoryRetrievalReadinessReport(
        **report_values,
        payload_digest=_digest_values(report_values),
    )


def specialist_team_domain_memory_retrieval_readiness_report_payload(
    report: SpecialistTeamDomainMemoryRetrievalReadinessReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamDomainMemoryRetrievalReadinessReport:
        raise ValueError(
            "report must be a SpecialistTeamDomainMemoryRetrievalReadinessReport",
        )
    _require_hard_flags(report)
    if report.payload_digest != _report_digest(report):
        raise ValueError("payload_digest must match report payload")
    return {
        "team_memory_exists": report.team_memory_exists,
        "similar_market_count": _payload_value(report.similar_market_count),
        "recent_calibration_count": _payload_value(report.recent_calibration_count),
        "source_family_history_count": _payload_value(
            report.source_family_history_count,
        ),
        "retrieval_latency_ms": _payload_value(report.retrieval_latency_ms),
        "schema_version_present": report.schema_version_present,
        "retrieval_status": report.retrieval_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "payload_digest": report.payload_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _findings_from_values(
    *,
    team_memory_exists: bool,
    similar_market_count: Decimal,
    recent_calibration_count: Decimal,
    source_family_history_count: Decimal,
    retrieval_latency_ms: Decimal,
    schema_version_present: bool,
) -> tuple[str, tuple[str, ...], str]:
    blocked: list[str] = []
    attention: list[str] = []
    if team_memory_exists is not True:
        blocked.append("team_memory_missing")
    if similar_market_count <= _ZERO:
        blocked.append("similar_market_count_missing")
    elif similar_market_count < _MIN_READY_SIMILAR_MARKET_COUNT:
        attention.append("similar_market_count_below_ready")
    if recent_calibration_count <= _ZERO:
        blocked.append("recent_calibration_missing")
    elif recent_calibration_count < _MIN_READY_RECENT_CALIBRATION_COUNT:
        attention.append("recent_calibration_count_below_ready")
    if source_family_history_count <= _ZERO:
        blocked.append("source_family_history_missing")
    elif source_family_history_count < _MIN_READY_SOURCE_FAMILY_HISTORY_COUNT:
        attention.append("source_family_history_count_below_ready")
    if retrieval_latency_ms > _MAX_WATCH_RETRIEVAL_LATENCY_MS:
        blocked.append("retrieval_latency_blocked")
    elif retrieval_latency_ms > _MAX_READY_RETRIEVAL_LATENCY_MS:
        attention.append("retrieval_latency_watch")
    if schema_version_present is not True:
        blocked.append("schema_version_missing")

    blocked_reasons = _sequenced_reasons(blocked)
    if blocked_reasons:
        return (
            "blocked",
            blocked_reasons,
            "Pause and manually collect or verify read-only team memory evidence.",
        )
    attention_reasons = _sequenced_reasons(attention)
    if attention_reasons:
        return (
            "attention",
            attention_reasons,
            "Manually review retrieval gaps before relying on team memory context.",
        )
    return (
        "ready",
        ("team_memory_retrieval_ready",),
        "Proceed with manual read-only retrieval review using public payload.",
    )


def _sequenced_reasons(reason_codes: list[str]) -> tuple[str, ...]:
    return tuple(
        reason_code
        for reason_code in SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_REASON_CODES
        if reason_code in reason_codes
    )


def _whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _six_place_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return decimal_value


def _six_place_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.quantize(_DECIMAL_QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_DECIMAL_QUANTUM)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, getattr(value, field_name))
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_status(value: object) -> None:
    if (
        type(value) is not str
        or value not in SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_STATUSES
    ):
        raise ValueError("retrieval_status must be supported")


def _reason_code_tuple(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for item in value:
        if (
            type(item) is not str
            or item
            not in SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_REASON_CODES
        ):
            raise ValueError("reason_codes must be supported")
        if item in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(item)
    if tuple(normalized) != _sequenced_reasons(normalized):
        raise ValueError("reason_codes must use canonical sequence")
    return tuple(normalized)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be public text")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64 or any(
        character not in _HEX_DIGITS for character in value
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _report_digest(
    report: SpecialistTeamDomainMemoryRetrievalReadinessReport,
) -> str:
    return _digest_values(
        {
            "team_memory_exists": report.team_memory_exists,
            "similar_market_count": report.similar_market_count,
            "recent_calibration_count": report.recent_calibration_count,
            "source_family_history_count": report.source_family_history_count,
            "retrieval_latency_ms": report.retrieval_latency_ms,
            "schema_version_present": report.schema_version_present,
            "retrieval_status": report.retrieval_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _digest_values(values: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _payload_value(dict(values.items())),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is dict:
        return {name: _payload_value(item) for name, item in value.items()}
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload value is not public JSON")


__all__ = (
    "SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_STATUSES",
    "SPECIALIST_TEAM_DOMAIN_MEMORY_RETRIEVAL_READINESS_REASON_CODES",
    "SpecialistTeamDomainMemoryRetrievalReadinessInput",
    "SpecialistTeamDomainMemoryRetrievalReadinessReport",
    "build_specialist_team_domain_memory_retrieval_readiness_report",
    "specialist_team_domain_memory_retrieval_readiness_report_payload",
)
