"""Read-only manual research audit log contract report for ProbabilityEventScreen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


__all__ = (
    "PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION",
    "ProbabilityEventScreenManualResearchAuditLogContractInput",
    "ProbabilityEventScreenManualResearchAuditLogContractPublicPayload",
    "ProbabilityEventScreenManualResearchAuditLogContractReport",
    "build_probability_event_screen_manual_research_audit_log_contract_report",
    "probability_event_screen_manual_research_audit_log_contract_report_digest",
    "probability_event_screen_manual_research_audit_log_contract_report_payload",
)


PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION = (
    "probability-event-screen-manual-research-audit-log-contract-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CHECK_COUNT = Decimal("7.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

CHECK_FIELDS = (
    "ephemeral_log_excluded",
    "public_safe_payload_ready",
    "supabase_persistence_ready",
    "redacted_identifiers_ready",
    "review_packet_index_ready",
    "operator_safety_ready",
    "no_live_execution_surface",
)
BLOCKING_REASON_BY_FIELD = {
    "ephemeral_log_excluded": "ephemeral_log_not_excluded",
    "public_safe_payload_ready": "public_safe_payload_not_ready",
    "redacted_identifiers_ready": "redacted_identifiers_not_ready",
    "operator_safety_ready": "operator_safety_not_ready",
    "no_live_execution_surface": "live_execution_surface_present",
}
ATTENTION_REASON_BY_FIELD = {
    "supabase_persistence_ready": "supabase_persistence_not_ready_attention",
    "review_packet_index_ready": "review_packet_index_not_ready_attention",
    "operator_safety_ready": "operator_safety_not_ready_attention",
    "no_live_execution_surface": "live_execution_surface_present_attention",
}
READY_REASON = "audit_log_contract_ready"
INCOMPLETE_ATTENTION_REASON = "audit_log_contract_incomplete_attention"
CONTRACT_BANDS = ("ready", "watch", "blocked")
BLOCKED_REASON_CODES = tuple(BLOCKING_REASON_BY_FIELD.values()) + (READY_REASON,)
ATTENTION_REASON_CODES = tuple(ATTENTION_REASON_BY_FIELD.values()) + (
    INCOMPLETE_ATTENTION_REASON,
)

PAYLOAD_KEYS = (
    "config_version",
    "audit_log_contract_ready",
    *CHECK_FIELDS,
    "contract_band",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)


class ProbabilityEventScreenManualResearchAuditLogContractPublicPayload(
    dict[str, object],
):
    """Immutable public payload for this read-only contract report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ProbabilityEventScreenManualResearchAuditLogContractInput:
    ephemeral_log_excluded: bool
    public_safe_payload_ready: bool
    supabase_persistence_ready: bool
    redacted_identifiers_ready: bool
    review_packet_index_ready: bool
    operator_safety_ready: bool
    no_live_execution_surface: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenManualResearchAuditLogContractInput:
            raise TypeError(
                "ProbabilityEventScreenManualResearchAuditLogContractInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenManualResearchAuditLogContractInput:
            raise ValueError(
                "input must be exactly "
                "ProbabilityEventScreenManualResearchAuditLogContractInput",
            )
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventScreenManualResearchAuditLogContractReport:
    config_version: str
    audit_log_contract_ready: bool
    ephemeral_log_excluded: bool
    public_safe_payload_ready: bool
    supabase_persistence_ready: bool
    redacted_identifiers_ready: bool
    review_packet_index_ready: bool
    operator_safety_ready: bool
    no_live_execution_surface: bool
    contract_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenManualResearchAuditLogContractReport:
            raise TypeError(
                "ProbabilityEventScreenManualResearchAuditLogContractReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenManualResearchAuditLogContractReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventScreenManualResearchAuditLogContractReport",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported report version")
        _require_bool("audit_log_contract_ready", self.audit_log_contract_ready)
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "contract_band",
            _require_contract_band("contract_band", self.contract_band),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_blocked_reason_codes(self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_attention_reason_codes(self.attention_reason_codes),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_hard_flags(self)
        _require_digest("digest", self.digest)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, digest=""))
        if self.digest != expected_digest:
            raise ValueError("digest must match public payload")

    @property
    def public_payload(
        self,
    ) -> ProbabilityEventScreenManualResearchAuditLogContractPublicPayload:
        payload = ProbabilityEventScreenManualResearchAuditLogContractPublicPayload(
            _payload_items(self, digest=self.digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_screen_manual_research_audit_log_contract_report(
    inputs: ProbabilityEventScreenManualResearchAuditLogContractInput,
) -> ProbabilityEventScreenManualResearchAuditLogContractReport:
    """Build a deterministic manual research audit log contract report."""

    if type(inputs) is not ProbabilityEventScreenManualResearchAuditLogContractInput:
        raise ValueError(
            "inputs must be a "
            "ProbabilityEventScreenManualResearchAuditLogContractInput",
        )
    _require_hard_flags(inputs)
    check_values = {field_name: getattr(inputs, field_name) for field_name in CHECK_FIELDS}
    blocked_reason_codes = _blocked_reason_codes(check_values)
    if all(value is True for value in check_values.values()):
        blocked_reason_codes = (READY_REASON,)
    ready_ratio = _ratio(
        _count(sum(1 for value in check_values.values() if value is True)),
        CHECK_COUNT,
    )
    values: dict[str, object] = {
        "config_version": (
            PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION
        ),
        "audit_log_contract_ready": all(
            value is True for value in check_values.values()
        ),
        **check_values,
        "contract_band": _contract_band(blocked_reason_codes, check_values),
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": _attention_reason_codes(check_values),
        "ready_ratio": ready_ratio,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventScreenManualResearchAuditLogContractReport(
        **values,
        digest=_payload_digest(_coerce_payload_values(values | {"digest": ""})),
    )


def probability_event_screen_manual_research_audit_log_contract_report_payload(
    report: (
        ProbabilityEventScreenManualResearchAuditLogContractReport
        | Mapping[str, object]
    ),
) -> ProbabilityEventScreenManualResearchAuditLogContractPublicPayload:
    if type(report) is ProbabilityEventScreenManualResearchAuditLogContractReport:
        _require_hard_flags(report)
        payload = report.public_payload
    elif isinstance(report, Mapping):
        payload = ProbabilityEventScreenManualResearchAuditLogContractPublicPayload(
            report,
        )
    else:
        raise ValueError(
            "report must be a "
            "ProbabilityEventScreenManualResearchAuditLogContractReport",
        )
    _validate_public_payload(payload)
    return payload


def probability_event_screen_manual_research_audit_log_contract_report_digest(
    report: (
        ProbabilityEventScreenManualResearchAuditLogContractReport
        | Mapping[str, object]
    ),
) -> str:
    payload = probability_event_screen_manual_research_audit_log_contract_report_payload(
        report,
    )
    digest = payload["digest"]
    if type(digest) is not str:
        raise ValueError("digest must be a string")
    return digest


def _blocked_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    return tuple(
        reason
        for field_name, reason in BLOCKING_REASON_BY_FIELD.items()
        if values[field_name] is not True
    )


def _attention_reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    reasons = tuple(
        reason
        for field_name, reason in ATTENTION_REASON_BY_FIELD.items()
        if values[field_name] is not True
    )
    if any(value is not True for value in values.values()):
        reasons = reasons + (INCOMPLETE_ATTENTION_REASON,)
    return reasons


def _contract_band(
    blocked_reason_codes: tuple[str, ...],
    values: Mapping[str, bool],
) -> str:
    if blocked_reason_codes and blocked_reason_codes != (READY_REASON,):
        return "blocked"
    if any(value is not True for value in values.values()):
        return "watch"
    return "ready"


def _validate_report(
    report: ProbabilityEventScreenManualResearchAuditLogContractReport,
) -> None:
    check_values = {field_name: getattr(report, field_name) for field_name in CHECK_FIELDS}
    blocked_reason_codes = _blocked_reason_codes(check_values)
    if all(value is True for value in check_values.values()):
        blocked_reason_codes = (READY_REASON,)
    attention_reason_codes = _attention_reason_codes(check_values)
    ready_ratio = _ratio(
        _count(sum(1 for value in check_values.values() if value is True)),
        CHECK_COUNT,
    )
    contract_band = _contract_band(blocked_reason_codes, check_values)
    if report.audit_log_contract_ready != all(
        value is True for value in check_values.values()
    ):
        raise ValueError("audit_log_contract_ready must match contract flags")
    if report.contract_band != contract_band:
        raise ValueError("contract_band must match contract flags")
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match contract flags")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match contract flags")
    if report.ready_ratio != ready_ratio:
        raise ValueError("ready_ratio must match contract flags")


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if set(payload) != set(PAYLOAD_KEYS):
        raise ValueError("public payload fields must match the report schema exactly")
    _require_public_label("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != PROBABILITY_EVENT_SCREEN_MANUAL_RESEARCH_AUDIT_LOG_CONTRACT_REPORT_VERSION
    ):
        raise ValueError("config_version must be the supported report version")
    _require_bool("audit_log_contract_ready", payload["audit_log_contract_ready"])
    for field_name in CHECK_FIELDS:
        _require_bool(field_name, payload[field_name])
    _require_contract_band("contract_band", payload["contract_band"])
    _normalize_blocked_reason_codes(_require_string_tuple(payload["blocked_reason_codes"]))
    _normalize_attention_reason_codes(
        _require_string_tuple(payload["attention_reason_codes"]),
    )
    _require_decimal_string("ready_ratio", payload["ready_ratio"])
    _require_digest("digest", payload["digest"])
    _require_hard_flags(_MappingFlags(payload))
    expected_digest = _payload_digest(dict(payload) | {"digest": ""})
    if payload["digest"] != expected_digest:
        raise ValueError("digest must match public payload")


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _payload_items(
    report: ProbabilityEventScreenManualResearchAuditLogContractReport,
    *,
    digest: str,
) -> dict[str, object]:
    values = {
        "config_version": report.config_version,
        "audit_log_contract_ready": report.audit_log_contract_ready,
        **{field_name: getattr(report, field_name) for field_name in CHECK_FIELDS},
        "contract_band": report.contract_band,
        "blocked_reason_codes": report.blocked_reason_codes,
        "attention_reason_codes": report.attention_reason_codes,
        "ready_ratio": report.ready_ratio,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "digest": digest,
    }
    return _coerce_payload_values(values)


def _coerce_payload_values(values: Mapping[str, object]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key in PAYLOAD_KEYS:
        value = values[key]
        if type(value) is Decimal:
            payload[key] = format(value, "f")
        elif isinstance(value, tuple):
            payload[key] = value
        else:
            payload[key] = value
    return payload


def _payload_digest(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_contract_band(field_name: str, value: object) -> str:
    if type(value) is not str or value not in CONTRACT_BANDS:
        raise ValueError(f"{field_name} must be a supported contract band")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value != value.to_integral_value() and value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use no more than six decimal places")
    return value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    parsed = Decimal(value)
    if format(_require_decimal(field_name, parsed), "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return parsed


def _normalize_blocked_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "blocked_reason_codes",
        values,
        allowed=BLOCKED_REASON_CODES,
    )


def _normalize_attention_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "attention_reason_codes",
        values,
        allowed=ATTENTION_REASON_CODES,
    )


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or any(type(value) is not str for value in values):
        raise ValueError(f"{field_name} must be a tuple of reason code strings")
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(value not in allowed for value in values):
        raise ValueError(f"{field_name} contains an unsupported reason code")
    return values


def _require_string_tuple(value: object) -> tuple[str, ...]:
    if type(value) is tuple and all(type(item) is str for item in value):
        return value
    if type(value) is list and all(type(item) is str for item in value):
        return tuple(value)
    raise ValueError("reason codes must be strings")


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)

