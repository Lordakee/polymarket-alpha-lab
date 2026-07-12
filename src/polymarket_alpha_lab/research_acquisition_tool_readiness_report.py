"""Pure read-only acquisition tool readiness report reducer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
WATCH_LAST_SUCCESS_AGE_SECONDS = Decimal("86400.000000")
BLOCK_LAST_SUCCESS_AGE_SECONDS = Decimal("259200.000000")
ELEVATED_FAILED_ATTEMPT_COUNT = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

READY_REASON = "research_acquisition_tool_ready"
UNAVAILABLE_REASONS = {
    "official_api_unavailable",
    "agent_reach_unavailable",
    "scrapling_unavailable",
}

PUBLIC_PAYLOAD_FIELDS = (
    "official_api_available",
    "agent_reach_available",
    "scrapling_available",
    "last_success_age_seconds",
    "failed_attempt_count",
    "source_payload_redacted",
    "manual_fallback_required",
    "acquisition_tool_ready",
    "tool_quorum_ready",
    "available_tool_count",
    "blocked_tool_count",
    "attention_tool_count",
    "ready_ratio",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = PUBLIC_PAYLOAD_FIELDS[:-1]

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "candidate_slug",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_id",
    "source id",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "raw_url",
    "raw text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table_name",
    "table name",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "live_trading",
    "live trading",
    "sizing",
    "recommendation",
    "buy",
    "sell",
)

__all__ = (
    "ResearchAcquisitionToolReadinessReport",
    "build_research_acquisition_tool_readiness_report",
    "research_acquisition_tool_readiness_report_public_payload",
    "validate_research_acquisition_tool_readiness_report_public_payload",
)


@dataclass(frozen=True)
class ResearchAcquisitionToolReadinessReport:
    official_api_available: bool
    agent_reach_available: bool
    scrapling_available: bool
    last_success_age_seconds: Decimal
    failed_attempt_count: Decimal
    source_payload_redacted: bool
    manual_fallback_required: bool
    acquisition_tool_ready: bool
    tool_quorum_ready: bool
    available_tool_count: Decimal
    blocked_tool_count: Decimal
    attention_tool_count: Decimal
    ready_ratio: Decimal
    reason_codes: tuple[str, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchAcquisitionToolReadinessReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchAcquisitionToolReadinessReport, "report")
        for field_name in (
            "official_api_available",
            "agent_reach_available",
            "scrapling_available",
            "source_payload_redacted",
            "manual_fallback_required",
            "acquisition_tool_ready",
            "tool_quorum_ready",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "last_success_age_seconds",
            _require_nonnegative_decimal(
                "last_success_age_seconds",
                self.last_success_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "failed_attempt_count",
            _require_count_decimal("failed_attempt_count", self.failed_attempt_count),
        )
        for field_name in (
            "available_tool_count",
            "blocked_tool_count",
            "attention_tool_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)
        if self.digest == "":
            object.__setattr__(self, "digest", _report_digest(self))
        else:
            object.__setattr__(self, "digest", _require_sha256_digest("digest", self.digest))
            if self.digest != _report_digest(self):
                raise ValueError("digest must match report public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_acquisition_tool_readiness_report_public_payload(self)


def build_research_acquisition_tool_readiness_report(
    *,
    official_api_available: bool,
    agent_reach_available: bool,
    scrapling_available: bool,
    last_success_age_seconds: Decimal,
    failed_attempt_count: Decimal,
    source_payload_redacted: bool,
    manual_fallback_required: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchAcquisitionToolReadinessReport:
    _require_bool("official_api_available", official_api_available)
    _require_bool("agent_reach_available", agent_reach_available)
    _require_bool("scrapling_available", scrapling_available)
    _require_bool("source_payload_redacted", source_payload_redacted)
    _require_bool("manual_fallback_required", manual_fallback_required)
    _require_bool("paper_only", paper_only)
    _require_bool("report_only", report_only)
    _require_bool("readonly", readonly)
    last_success_age_seconds = _require_nonnegative_decimal(
        "last_success_age_seconds",
        last_success_age_seconds,
    )
    failed_attempt_count = _require_count_decimal(
        "failed_attempt_count",
        failed_attempt_count,
    )
    available_tool_count = _available_tool_count(
        official_api_available=official_api_available,
        agent_reach_available=agent_reach_available,
        scrapling_available=scrapling_available,
    )
    blocked_tool_count = _quantize(THREE - available_tool_count)
    tool_quorum_ready = available_tool_count >= Decimal("2.000000")
    ready_ratio = _safe_ratio(available_tool_count, THREE)
    reason_codes = _reason_codes(
        official_api_available=official_api_available,
        agent_reach_available=agent_reach_available,
        scrapling_available=scrapling_available,
        tool_quorum_ready=tool_quorum_ready,
        last_success_age_seconds=last_success_age_seconds,
        failed_attempt_count=failed_attempt_count,
        source_payload_redacted=source_payload_redacted,
        manual_fallback_required=manual_fallback_required,
    )
    return ResearchAcquisitionToolReadinessReport(
        official_api_available=official_api_available,
        agent_reach_available=agent_reach_available,
        scrapling_available=scrapling_available,
        last_success_age_seconds=last_success_age_seconds,
        failed_attempt_count=failed_attempt_count,
        source_payload_redacted=source_payload_redacted,
        manual_fallback_required=manual_fallback_required,
        acquisition_tool_ready=reason_codes == (READY_REASON,),
        tool_quorum_ready=tool_quorum_ready,
        available_tool_count=available_tool_count,
        blocked_tool_count=blocked_tool_count,
        attention_tool_count=_attention_tool_count(reason_codes),
        ready_ratio=ready_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def research_acquisition_tool_readiness_report_public_payload(
    report: ResearchAcquisitionToolReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchAcquisitionToolReadinessReport:
        raise ValueError("report must be a ResearchAcquisitionToolReadinessReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _report_public_payload(report)
    validate_research_acquisition_tool_readiness_report_public_payload(payload)
    return payload


def validate_research_acquisition_tool_readiness_report_public_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_exact_keys("public payload", payload, PUBLIC_PAYLOAD_FIELDS)
    _require_payload_hard_flags(payload)
    provided_digest = _require_sha256_digest("digest", payload["digest"])
    expected_digest = _payload_digest(
        {field_name: payload[field_name] for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST},
    )
    if provided_digest != expected_digest:
        raise ValueError("digest must match public payload")
    report = _report_from_payload(payload)
    if report.digest != provided_digest:
        raise ValueError("digest must match report payload")
    return payload


def _report_from_payload(payload: dict[str, Any]) -> ResearchAcquisitionToolReadinessReport:
    return ResearchAcquisitionToolReadinessReport(
        official_api_available=_bool_from_payload(
            "official_api_available",
            payload["official_api_available"],
        ),
        agent_reach_available=_bool_from_payload(
            "agent_reach_available",
            payload["agent_reach_available"],
        ),
        scrapling_available=_bool_from_payload(
            "scrapling_available",
            payload["scrapling_available"],
        ),
        last_success_age_seconds=_decimal_from_payload_string(
            "last_success_age_seconds",
            payload["last_success_age_seconds"],
        ),
        failed_attempt_count=_decimal_from_payload_string(
            "failed_attempt_count",
            payload["failed_attempt_count"],
            require_integral=True,
        ),
        source_payload_redacted=_bool_from_payload(
            "source_payload_redacted",
            payload["source_payload_redacted"],
        ),
        manual_fallback_required=_bool_from_payload(
            "manual_fallback_required",
            payload["manual_fallback_required"],
        ),
        acquisition_tool_ready=_bool_from_payload(
            "acquisition_tool_ready",
            payload["acquisition_tool_ready"],
        ),
        tool_quorum_ready=_bool_from_payload(
            "tool_quorum_ready",
            payload["tool_quorum_ready"],
        ),
        available_tool_count=_decimal_from_payload_string(
            "available_tool_count",
            payload["available_tool_count"],
            require_integral=True,
        ),
        blocked_tool_count=_decimal_from_payload_string(
            "blocked_tool_count",
            payload["blocked_tool_count"],
            require_integral=True,
        ),
        attention_tool_count=_decimal_from_payload_string(
            "attention_tool_count",
            payload["attention_tool_count"],
            require_integral=True,
        ),
        ready_ratio=_decimal_from_payload_string("ready_ratio", payload["ready_ratio"]),
        reason_codes=_normalize_reason_codes_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        digest=payload["digest"],
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _validate_report_consistency(report: ResearchAcquisitionToolReadinessReport) -> None:
    available_tool_count = _available_tool_count(
        official_api_available=report.official_api_available,
        agent_reach_available=report.agent_reach_available,
        scrapling_available=report.scrapling_available,
    )
    blocked_tool_count = _quantize(THREE - available_tool_count)
    tool_quorum_ready = available_tool_count >= Decimal("2.000000")
    reason_codes = _reason_codes(
        official_api_available=report.official_api_available,
        agent_reach_available=report.agent_reach_available,
        scrapling_available=report.scrapling_available,
        tool_quorum_ready=tool_quorum_ready,
        last_success_age_seconds=report.last_success_age_seconds,
        failed_attempt_count=report.failed_attempt_count,
        source_payload_redacted=report.source_payload_redacted,
        manual_fallback_required=report.manual_fallback_required,
    )
    if report.available_tool_count != available_tool_count:
        raise ValueError("available_tool_count must match tool availability")
    if report.blocked_tool_count != blocked_tool_count:
        raise ValueError("blocked_tool_count must match tool availability")
    if report.tool_quorum_ready is not tool_quorum_ready:
        raise ValueError("tool_quorum_ready must match tool availability")
    if report.ready_ratio != _safe_ratio(available_tool_count, THREE):
        raise ValueError("ready_ratio must match tool availability")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match report inputs")
    if report.attention_tool_count != _attention_tool_count(reason_codes):
        raise ValueError("attention_tool_count must match reason codes")
    if report.acquisition_tool_ready is not (reason_codes == (READY_REASON,)):
        raise ValueError("acquisition_tool_ready must match reason codes")


def _available_tool_count(
    *,
    official_api_available: bool,
    agent_reach_available: bool,
    scrapling_available: bool,
) -> Decimal:
    return _decimal_count(
        sum(
            (
                official_api_available,
                agent_reach_available,
                scrapling_available,
            ),
        ),
    )


def _reason_codes(
    *,
    official_api_available: bool,
    agent_reach_available: bool,
    scrapling_available: bool,
    tool_quorum_ready: bool,
    last_success_age_seconds: Decimal,
    failed_attempt_count: Decimal,
    source_payload_redacted: bool,
    manual_fallback_required: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not official_api_available:
        codes.append("official_api_unavailable")
    if not agent_reach_available:
        codes.append("agent_reach_unavailable")
    if not scrapling_available:
        codes.append("scrapling_unavailable")
    if not tool_quorum_ready:
        codes.append("tool_quorum_missing")
    if last_success_age_seconds >= BLOCK_LAST_SUCCESS_AGE_SECONDS:
        codes.append("last_success_age_block")
    elif last_success_age_seconds > WATCH_LAST_SUCCESS_AGE_SECONDS:
        codes.append("last_success_age_watch")
    if failed_attempt_count >= ELEVATED_FAILED_ATTEMPT_COUNT:
        codes.append("failed_attempts_elevated")
    elif failed_attempt_count > ZERO:
        codes.append("failed_attempts_present")
    if not source_payload_redacted:
        codes.append("source_payload_not_redacted")
    if manual_fallback_required:
        codes.append("manual_fallback_required")
    if not codes:
        return (READY_REASON,)
    return tuple(codes)


def _attention_tool_count(reason_codes: tuple[str, ...]) -> Decimal:
    return _decimal_count(
        sum(
            1
            for reason_code in reason_codes
            if reason_code != READY_REASON and reason_code not in UNAVAILABLE_REASONS
        ),
    )


def _report_public_payload(report: ResearchAcquisitionToolReadinessReport) -> dict[str, Any]:
    payload = _report_public_payload_without_digest(report)
    payload["digest"] = report.digest
    return payload


def _report_public_payload_without_digest(
    report: ResearchAcquisitionToolReadinessReport,
) -> dict[str, Any]:
    return {
        "official_api_available": report.official_api_available,
        "agent_reach_available": report.agent_reach_available,
        "scrapling_available": report.scrapling_available,
        "last_success_age_seconds": _decimal_payload_value(
            report.last_success_age_seconds,
        ),
        "failed_attempt_count": _decimal_payload_value(report.failed_attempt_count),
        "source_payload_redacted": report.source_payload_redacted,
        "manual_fallback_required": report.manual_fallback_required,
        "acquisition_tool_ready": report.acquisition_tool_ready,
        "tool_quorum_ready": report.tool_quorum_ready,
        "available_tool_count": _decimal_payload_value(report.available_tool_count),
        "blocked_tool_count": _decimal_payload_value(report.blocked_tool_count),
        "attention_tool_count": _decimal_payload_value(report.attention_tool_count),
        "ready_ratio": _decimal_payload_value(report.ready_ratio),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest(report: ResearchAcquisitionToolReadinessReport) -> str:
    return _payload_digest(_report_public_payload_without_digest(report))


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_payload_value(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _decimal_from_payload_string(
    field_name: str,
    value: object,
    *,
    require_integral: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = _quantize(decimal_value)
    if value != _decimal_payload_value(decimal_value):
        raise ValueError(f"{field_name} must use canonical decimal payload format")
    if require_integral and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return decimal_value


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value:
            raise ValueError(f"{field_name} must contain non-empty strings")
        _reject_unsafe_public_text(field_name, value)
        normalized.append(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _normalize_reason_codes_from_payload(
    field_name: str,
    values: object,
) -> tuple[str, ...]:
    if type(values) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(values))


def _require_hard_flags(
    label: str,
    value: ResearchAcquisitionToolReadinessReport,
) -> None:
    if value.paper_only is not True:
        raise ValueError(f"{label} paper_only must be True")
    if value.report_only is not True:
        raise ValueError(f"{label} report_only must be True")
    if value.readonly is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != expected_keys:
        raise ValueError(f"{label} must have exact public payload fields")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
    elif type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)
    elif hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:
            _reject_unsafe_public_text(f"{label} field", field_name)
            _reject_unsafe_public_payload(f"{label}.{field_name}", getattr(value, field_name))


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.casefold()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in normalized:
            raise ValueError(f"{label} contains unsafe public payload text")

