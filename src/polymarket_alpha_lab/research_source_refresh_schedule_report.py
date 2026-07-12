"""Pure report-only research source refresh schedule readiness."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any, Mapping


DEFAULT_RESEARCH_SOURCE_REFRESH_SCHEDULE_REPORT_CONFIG_VERSION = (
    "research-source-refresh-schedule-report-v0"
)
RESEARCH_SOURCE_REFRESH_SCHEDULE_REFRESH_BANDS = ("ready", "watch", "blocked")

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SOURCE_COUNT = Decimal("8.000000")
SHA256_HEX_LENGTH = 64

READY_REASON = "research_source_refresh_schedule_all_sources_ready"
READY_RATIO_WATCH_REASON = "research_source_refresh_schedule_ready_ratio_watch"
READY_RATIO_BLOCKED_REASON = "research_source_refresh_schedule_ready_ratio_blocked"

OFFICIAL_API_BLOCKED_REASON = "research_source_refresh_schedule_official_api_blocked"
AGENT_REACH_ATTENTION_REASON = "research_source_refresh_schedule_agent_reach_attention"
SCRAPLING_ATTENTION_REASON = "research_source_refresh_schedule_scrapling_attention"
FRESHNESS_SLA_BLOCKED_REASON = (
    "research_source_refresh_schedule_source_freshness_sla_blocked"
)
MANUAL_FALLBACK_BLOCKED_REASON = (
    "research_source_refresh_schedule_manual_fallback_blocked"
)
REDACTION_BLOCKED_REASON = "research_source_refresh_schedule_redaction_blocked"
OPERATOR_SAFETY_BLOCKED_REASON = (
    "research_source_refresh_schedule_operator_safety_blocked"
)
SUPABASE_PERSISTENCE_BLOCKED_REASON = (
    "research_source_refresh_schedule_supabase_persistence_blocked"
)

BLOCKED_REASON_CODES = (
    OFFICIAL_API_BLOCKED_REASON,
    FRESHNESS_SLA_BLOCKED_REASON,
    MANUAL_FALLBACK_BLOCKED_REASON,
    REDACTION_BLOCKED_REASON,
    OPERATOR_SAFETY_BLOCKED_REASON,
    SUPABASE_PERSISTENCE_BLOCKED_REASON,
)
ATTENTION_REASON_CODES = (
    READY_REASON,
    AGENT_REACH_ATTENTION_REASON,
    SCRAPLING_ATTENTION_REASON,
    READY_RATIO_WATCH_REASON,
    READY_RATIO_BLOCKED_REASON,
)

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "token",
    "wal" + "let",
    "order_id",
    "trade_id",
    "live_surface",
    "recommendation",
    "table",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "candidate-",
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "token",
    "wal" + "let",
    "order",
    "trade",
    "live_surface",
    "recommendation",
)

REQUIRED_FLAGS = (
    "official_api_refresh_ready",
    "source_freshness_sla_ready",
    "manual_fallback_ready",
    "redaction_ready",
    "operator_safety_ready",
    "supabase_persistence_ready",
)
OPTIONAL_FLAGS = (
    "agent_reach_refresh_ready",
    "scrapling_refresh_ready",
)
ALL_REFRESH_FLAGS = (
    "official_api_refresh_ready",
    "agent_reach_refresh_ready",
    "scrapling_refresh_ready",
    "source_freshness_sla_ready",
    "manual_fallback_ready",
    "redaction_ready",
    "operator_safety_ready",
    "supabase_persistence_ready",
)

BLOCKED_REASON_BY_FLAG = {
    "official_api_refresh_ready": OFFICIAL_API_BLOCKED_REASON,
    "source_freshness_sla_ready": FRESHNESS_SLA_BLOCKED_REASON,
    "manual_fallback_ready": MANUAL_FALLBACK_BLOCKED_REASON,
    "redaction_ready": REDACTION_BLOCKED_REASON,
    "operator_safety_ready": OPERATOR_SAFETY_BLOCKED_REASON,
    "supabase_persistence_ready": SUPABASE_PERSISTENCE_BLOCKED_REASON,
}
ATTENTION_REASON_BY_FLAG = {
    "agent_reach_refresh_ready": AGENT_REACH_ATTENTION_REASON,
    "scrapling_refresh_ready": SCRAPLING_ATTENTION_REASON,
}


@dataclass(frozen=True)
class ResearchSourceRefreshScheduleReport:
    generated_at: datetime
    config_version: str
    official_api_refresh_ready: bool
    agent_reach_refresh_ready: bool
    scrapling_refresh_ready: bool
    source_freshness_sla_ready: bool
    manual_fallback_ready: bool
    redaction_ready: bool
    operator_safety_ready: bool
    supabase_persistence_ready: bool
    source_refresh_ready: bool
    refresh_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    ready_source_count: Decimal
    required_source_count: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceRefreshScheduleReport:
            raise TypeError(
                "ResearchSourceRefreshScheduleReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceRefreshScheduleReport:
            raise ValueError("report must be exactly ResearchSourceRefreshScheduleReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ALL_REFRESH_FLAGS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio("ready_ratio", self.ready_ratio),
        )
        object.__setattr__(
            self,
            "ready_source_count",
            _require_nonnegative_decimal("ready_source_count", self.ready_source_count),
        )
        object.__setattr__(
            self,
            "required_source_count",
            _require_positive_decimal(
                "required_source_count",
                self.required_source_count,
            ),
        )
        _require_bool("source_refresh_ready", self.source_refresh_ready)
        _require_refresh_band("refresh_band", self.refresh_band)
        _require_hard_flags("report", self)
        _validate_report(self)
        _require_or_set_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_source_refresh_schedule_report_payload(self)

    @property
    def digest(self) -> str:
        return research_source_refresh_schedule_report_digest(self)


def build_research_source_refresh_schedule_report(
    *,
    official_api_refresh_ready: bool,
    agent_reach_refresh_ready: bool,
    scrapling_refresh_ready: bool,
    source_freshness_sla_ready: bool,
    manual_fallback_ready: bool,
    redaction_ready: bool,
    operator_safety_ready: bool,
    supabase_persistence_ready: bool,
    generated_at: datetime,
    config_version: str = DEFAULT_RESEARCH_SOURCE_REFRESH_SCHEDULE_REPORT_CONFIG_VERSION,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceRefreshScheduleReport:
    values = {
        "official_api_refresh_ready": _require_bool(
            "official_api_refresh_ready",
            official_api_refresh_ready,
        ),
        "agent_reach_refresh_ready": _require_bool(
            "agent_reach_refresh_ready",
            agent_reach_refresh_ready,
        ),
        "scrapling_refresh_ready": _require_bool(
            "scrapling_refresh_ready",
            scrapling_refresh_ready,
        ),
        "source_freshness_sla_ready": _require_bool(
            "source_freshness_sla_ready",
            source_freshness_sla_ready,
        ),
        "manual_fallback_ready": _require_bool(
            "manual_fallback_ready",
            manual_fallback_ready,
        ),
        "redaction_ready": _require_bool("redaction_ready", redaction_ready),
        "operator_safety_ready": _require_bool(
            "operator_safety_ready",
            operator_safety_ready,
        ),
        "supabase_persistence_ready": _require_bool(
            "supabase_persistence_ready",
            supabase_persistence_ready,
        ),
    }
    blocked_reason_codes = _blocked_reason_codes(values)
    attention_reason_codes = _attention_reason_codes(values, blocked_reason_codes)
    ready_count = _count(sum(1 for flag in ALL_REFRESH_FLAGS if values[flag]))
    ready_ratio = (ready_count / SOURCE_COUNT).quantize(QUANT)
    refresh_band = _refresh_band(blocked_reason_codes, ready_ratio)
    return ResearchSourceRefreshScheduleReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=_require_canonical_string("config_version", config_version),
        **values,
        source_refresh_ready=refresh_band == "ready",
        refresh_band=refresh_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=ready_ratio,
        ready_source_count=ready_count,
        required_source_count=SOURCE_COUNT,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def research_source_refresh_schedule_report_payload(
    report: ResearchSourceRefreshScheduleReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceRefreshScheduleReport:
        raise ValueError("report must be a ResearchSourceRefreshScheduleReport")
    validate_research_source_refresh_schedule_report_digest(report)
    _require_hard_flags("report", report)
    payload = _public_payload_from_report(report, include_digest=True)
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def research_source_refresh_schedule_report_digest(
    report: ResearchSourceRefreshScheduleReport,
) -> str:
    if type(report) is not ResearchSourceRefreshScheduleReport:
        raise ValueError("report must be a ResearchSourceRefreshScheduleReport")
    return _payload_validation_digest(_public_payload_from_report(report, include_digest=False))


def validate_research_source_refresh_schedule_report_digest(
    report: ResearchSourceRefreshScheduleReport,
) -> None:
    if type(report) is not ResearchSourceRefreshScheduleReport:
        raise ValueError("report must be a ResearchSourceRefreshScheduleReport")
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    expected = research_source_refresh_schedule_report_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def validate_research_source_refresh_schedule_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _verify_public_digest(payload)


def _blocked_reason_codes(flags: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        BLOCKED_REASON_BY_FLAG[flag]
        for flag in REQUIRED_FLAGS
        if flags[flag] is False
    )


def _attention_reason_codes(
    flags: Mapping[str, bool],
    blocked_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons = [
        ATTENTION_REASON_BY_FLAG[flag]
        for flag in OPTIONAL_FLAGS
        if flags[flag] is False
    ]
    ready_count = _count(sum(1 for flag in ALL_REFRESH_FLAGS if flags[flag]))
    ready_ratio = (ready_count / SOURCE_COUNT).quantize(QUANT)
    if not blocked_reason_codes and not reasons:
        reasons.append(READY_REASON)
    elif blocked_reason_codes:
        reasons.append(READY_RATIO_BLOCKED_REASON)
    elif ready_ratio < ONE:
        reasons.append(READY_RATIO_WATCH_REASON)
    return tuple(reason for reason in ATTENTION_REASON_CODES if reason in reasons)


def _refresh_band(blocked_reason_codes: tuple[str, ...], ready_ratio: Decimal) -> str:
    if blocked_reason_codes:
        return "blocked"
    if ready_ratio == ONE:
        return "ready"
    return "watch"


def _validate_report(report: ResearchSourceRefreshScheduleReport) -> None:
    flags = {field_name: getattr(report, field_name) for field_name in ALL_REFRESH_FLAGS}
    blocked_reason_codes = _blocked_reason_codes(flags)
    attention_reason_codes = _attention_reason_codes(flags, blocked_reason_codes)
    ready_source_count = _count(sum(1 for flag in ALL_REFRESH_FLAGS if flags[flag]))
    ready_ratio = (ready_source_count / SOURCE_COUNT).quantize(QUANT)
    refresh_band = _refresh_band(blocked_reason_codes, ready_ratio)
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match refresh flags")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match refresh flags")
    if report.ready_source_count != ready_source_count:
        raise ValueError("ready_source_count must match refresh flags")
    if report.required_source_count != SOURCE_COUNT:
        raise ValueError("required_source_count must match source schedule")
    if report.ready_ratio != ready_ratio:
        raise ValueError("ready_ratio must match refresh flags")
    if report.refresh_band != refresh_band:
        raise ValueError("refresh_band must match readiness state")
    if report.source_refresh_ready is not (refresh_band == "ready"):
        raise ValueError("source_refresh_ready must match refresh_band")


def _public_payload_from_report(
    report: ResearchSourceRefreshScheduleReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "source_readiness": {
            field_name: getattr(report, field_name) for field_name in ALL_REFRESH_FLAGS
        },
        "source_refresh_ready": report.source_refresh_ready,
        "refresh_band": report.refresh_band,
        "blocked_reason_codes": list(report.blocked_reason_codes),
        "attention_reason_codes": list(report.attention_reason_codes),
        "ready_ratio": _decimal_payload(report.ready_ratio),
        "ready_source_count": _decimal_payload(report.ready_source_count),
        "required_source_count": _decimal_payload(report.required_source_count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _require_or_set_digest(report: ResearchSourceRefreshScheduleReport) -> None:
    expected = research_source_refresh_schedule_report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _payload_validation_digest(payload: Mapping[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    normalized = _json_ready(unsigned_payload)
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    expected = _payload_validation_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _decimal_payload(value: Decimal) -> str:
    return format(value.quantize(QUANT), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_text("public payload", value, is_key=False)
    return value


def _require_refresh_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_SOURCE_REFRESH_SCHEDULE_REFRESH_BANDS:
        raise ValueError(f"{field_name} must be a known refresh band")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in allowed_values:
            raise ValueError(f"{field_name} contains an unknown reason code")
    return tuple(reason_code for reason_code in allowed_values if reason_code in normalized)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != SHA256_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _reject_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text("public payload", key, is_key=True)
            _reject_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if type(value) is str:
        _reject_unsafe_public_text("public payload", value, is_key=False)


def _reject_unsafe_public_text(context: str, value: str, *, is_key: bool) -> None:
    lowered = value.lower()
    if is_key and value in {"paper_only", "report_only", "readonly"}:
        return
    fragments = UNSAFE_PUBLIC_KEY_FRAGMENTS if is_key else UNSAFE_PUBLIC_VALUE_FRAGMENTS
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{context} contains unsafe public payload details")


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


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_REFRESH_SCHEDULE_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_REFRESH_SCHEDULE_REFRESH_BANDS",
    "ResearchSourceRefreshScheduleReport",
    "build_research_source_refresh_schedule_report",
    "research_source_refresh_schedule_report_digest",
    "research_source_refresh_schedule_report_payload",
    "validate_research_source_refresh_schedule_public_payload",
    "validate_research_source_refresh_schedule_report_digest",
)
