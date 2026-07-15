"""Read-only local Supabase persistence contract report for ProbabilityEventScreen."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re


__all__ = (
    "PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION",
    "ProbabilityEventScreenSupabaseContractInput",
    "ProbabilityEventScreenSupabaseContractPublicPayload",
    "ProbabilityEventScreenSupabaseContractReport",
    "build_probability_event_screen_supabase_contract_report",
    "validate_probability_event_screen_supabase_contract_public_payload",
)


PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION = (
    "probability-event-screen-supabase-contract-report-v0"
)
CONTRACT_NAME = "ProbabilityEventScreen"
PERSISTENCE_SURFACE = "local_supabase_postgres"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CHECK_COUNT = Decimal("7.000000")

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

CHECK_FIELDS = (
    "table_contract_ready",
    "required_columns_present",
    "jsonb_payload_ready",
    "redacted_payload_ready",
    "local_dsn_validated",
    "remote_host_blocked",
    "migration_revision_current",
)
BLOCKING_CHECK_FIELDS = (
    "table_contract_ready",
    "required_columns_present",
    "jsonb_payload_ready",
    "redacted_payload_ready",
    "local_dsn_validated",
    "remote_host_blocked",
)
ATTENTION_CHECK_FIELDS = ("migration_revision_current",)
REASON_CODE_BY_FIELD_STATE = {
    ("table_contract_ready", True): "table_contract_ready",
    ("table_contract_ready", False): "table_contract_missing",
    ("required_columns_present", True): "required_columns_present",
    ("required_columns_present", False): "required_columns_missing",
    ("jsonb_payload_ready", True): "jsonb_payload_ready",
    ("jsonb_payload_ready", False): "jsonb_payload_not_ready",
    ("redacted_payload_ready", True): "redacted_payload_ready",
    ("redacted_payload_ready", False): "redacted_payload_not_ready",
    ("local_dsn_validated", True): "local_dsn_validated",
    ("local_dsn_validated", False): "local_dsn_not_validated",
    ("remote_host_blocked", True): "remote_host_blocked",
    ("remote_host_blocked", False): "remote_host_not_blocked",
    ("migration_revision_current", True): "migration_revision_current",
    ("migration_revision_current", False): "migration_revision_outdated",
}
REASON_CODES = tuple(
    REASON_CODE_BY_FIELD_STATE[(field_name, state)]
    for field_name in CHECK_FIELDS
    for state in (True, False)
)
PAYLOAD_KEYS = (
    "config_version",
    "contract_name",
    "persistence_surface",
    "persistence_ready",
    "table_contract_ready",
    "required_columns_present",
    "jsonb_payload_ready",
    "redacted_payload_ready",
    "local_dsn_validated",
    "remote_host_blocked",
    "migration_revision_current",
    "check_count",
    "ready_check_count",
    "blocked_check_count",
    "attention_check_count",
    "ready_check_ratio",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)


class ProbabilityEventScreenSupabaseContractPublicPayload(dict[str, object]):
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
class ProbabilityEventScreenSupabaseContractInput:
    table_contract_ready: bool
    required_columns_present: bool
    jsonb_payload_ready: bool
    redacted_payload_ready: bool
    local_dsn_validated: bool
    remote_host_blocked: bool
    migration_revision_current: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenSupabaseContractInput:
            raise TypeError(
                "ProbabilityEventScreenSupabaseContractInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenSupabaseContractInput:
            raise ValueError(
                "input must be exactly ProbabilityEventScreenSupabaseContractInput",
            )
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class ProbabilityEventScreenSupabaseContractReport:
    config_version: str
    contract_name: str
    persistence_surface: str
    persistence_ready: bool
    table_contract_ready: bool
    required_columns_present: bool
    jsonb_payload_ready: bool
    redacted_payload_ready: bool
    local_dsn_validated: bool
    remote_host_blocked: bool
    migration_revision_current: bool
    check_count: Decimal
    ready_check_count: Decimal
    blocked_check_count: Decimal
    attention_check_count: Decimal
    ready_check_ratio: Decimal
    reason_codes: tuple[str, ...]
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventScreenSupabaseContractReport:
            raise TypeError(
                "ProbabilityEventScreenSupabaseContractReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventScreenSupabaseContractReport:
            raise ValueError(
                "report must be exactly ProbabilityEventScreenSupabaseContractReport",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        if self.contract_name != CONTRACT_NAME:
            raise ValueError("contract_name must be ProbabilityEventScreen")
        if self.persistence_surface != PERSISTENCE_SURFACE:
            raise ValueError("persistence_surface must be local_supabase_postgres")
        _require_bool("persistence_ready", self.persistence_ready)
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        for field_name in (
            "check_count",
            "ready_check_count",
            "blocked_check_count",
            "attention_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_check_ratio",
            _require_ratio_decimal("ready_check_ratio", self.ready_check_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("digest", self.digest)
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, digest=""))
        if self.digest != expected_digest:
            raise ValueError("digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventScreenSupabaseContractPublicPayload:
        payload = ProbabilityEventScreenSupabaseContractPublicPayload(
            _payload_items(self, digest=self.digest),
        )
        validate_probability_event_screen_supabase_contract_public_payload(payload)
        return payload


def build_probability_event_screen_supabase_contract_report(
    inputs: ProbabilityEventScreenSupabaseContractInput,
) -> ProbabilityEventScreenSupabaseContractReport:
    """Build a deterministic read-only local persistence readiness report."""

    if type(inputs) is not ProbabilityEventScreenSupabaseContractInput:
        raise ValueError(
            "inputs must be a ProbabilityEventScreenSupabaseContractInput",
        )
    _require_hard_flags(inputs)
    check_values = {field_name: getattr(inputs, field_name) for field_name in CHECK_FIELDS}
    ready_count = _count(sum(1 for value in check_values.values() if value is True))
    blocked_count = _count(
        sum(
            1
            for field_name in BLOCKING_CHECK_FIELDS
            if check_values[field_name] is not True
        ),
    )
    attention_count = _count(
        sum(
            1
            for field_name in ATTENTION_CHECK_FIELDS
            if check_values[field_name] is not True
        ),
    )
    values: dict[str, object] = {
        "config_version": PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION,
        "contract_name": CONTRACT_NAME,
        "persistence_surface": PERSISTENCE_SURFACE,
        "persistence_ready": ready_count == CHECK_COUNT,
        **check_values,
        "check_count": CHECK_COUNT,
        "ready_check_count": ready_count,
        "blocked_check_count": blocked_count,
        "attention_check_count": attention_count,
        "ready_check_ratio": _ratio(ready_count, CHECK_COUNT),
        "reason_codes": tuple(
            REASON_CODE_BY_FIELD_STATE[(field_name, check_values[field_name])]
            for field_name in CHECK_FIELDS
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventScreenSupabaseContractReport(
        **values,
        digest=_payload_digest(_payload_values(values, digest="")),
    )


def validate_probability_event_screen_supabase_contract_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical contract report schema")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != PROBABILITY_EVENT_SCREEN_SUPABASE_CONTRACT_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    if payload["contract_name"] != CONTRACT_NAME:
        raise ValueError("contract_name must be ProbabilityEventScreen")
    if payload["persistence_surface"] != PERSISTENCE_SURFACE:
        raise ValueError("persistence_surface must be local_supabase_postgres")
    for field_name in (
        "persistence_ready",
        *CHECK_FIELDS,
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    for field_name in (
        "check_count",
        "ready_check_count",
        "blocked_check_count",
        "attention_check_count",
    ):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _require_count_decimal(field_name, Decimal(value))
    ratio_value = payload["ready_check_ratio"]
    if type(ratio_value) is not str:
        raise ValueError("ready_check_ratio must be serialized as a string")
    _require_ratio_decimal("ready_check_ratio", Decimal(ratio_value))
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _normalize_reason_codes(reason_codes)
    digest = payload["digest"]
    _require_digest("digest", digest)
    unsigned = dict(payload)
    unsigned["digest"] = ""
    if digest != _payload_digest(unsigned):
        raise ValueError("digest must match public payload")
    return payload


def _validate_report(report: ProbabilityEventScreenSupabaseContractReport) -> None:
    check_values = {field_name: getattr(report, field_name) for field_name in CHECK_FIELDS}
    ready_count = _count(sum(1 for value in check_values.values() if value is True))
    blocked_count = _count(
        sum(
            1
            for field_name in BLOCKING_CHECK_FIELDS
            if check_values[field_name] is not True
        ),
    )
    attention_count = _count(
        sum(
            1
            for field_name in ATTENTION_CHECK_FIELDS
            if check_values[field_name] is not True
        ),
    )
    if report.check_count != CHECK_COUNT:
        raise ValueError("check_count must equal canonical check count")
    if report.ready_check_count != ready_count:
        raise ValueError("ready_check_count must match check fields")
    if report.blocked_check_count != blocked_count:
        raise ValueError("blocked_check_count must match check fields")
    if report.attention_check_count != attention_count:
        raise ValueError("attention_check_count must match check fields")
    if report.ready_check_ratio != _ratio(ready_count, report.check_count):
        raise ValueError("ready_check_ratio must match ready checks")
    if report.persistence_ready != (ready_count == CHECK_COUNT):
        raise ValueError("persistence_ready must match canonical checks")
    expected_reasons = tuple(
        REASON_CODE_BY_FIELD_STATE[(field_name, check_values[field_name])]
        for field_name in CHECK_FIELDS
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match canonical checks")


def _payload_items(
    report: ProbabilityEventScreenSupabaseContractReport,
    *,
    digest: str,
) -> dict[str, object]:
    return _payload_values(asdict_without_digest(report), digest=digest)


def asdict_without_digest(
    report: ProbabilityEventScreenSupabaseContractReport,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "contract_name": report.contract_name,
        "persistence_surface": report.persistence_surface,
        "persistence_ready": report.persistence_ready,
        "table_contract_ready": report.table_contract_ready,
        "required_columns_present": report.required_columns_present,
        "jsonb_payload_ready": report.jsonb_payload_ready,
        "redacted_payload_ready": report.redacted_payload_ready,
        "local_dsn_validated": report.local_dsn_validated,
        "remote_host_blocked": report.remote_host_blocked,
        "migration_revision_current": report.migration_revision_current,
        "check_count": report.check_count,
        "ready_check_count": report.ready_check_count,
        "blocked_check_count": report.blocked_check_count,
        "attention_check_count": report.attention_check_count,
        "ready_check_ratio": report.ready_check_ratio,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _payload_values(values: Mapping[str, object], *, digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "contract_name": values["contract_name"],
        "persistence_surface": values["persistence_surface"],
        "persistence_ready": values["persistence_ready"],
        "table_contract_ready": values["table_contract_ready"],
        "required_columns_present": values["required_columns_present"],
        "jsonb_payload_ready": values["jsonb_payload_ready"],
        "redacted_payload_ready": values["redacted_payload_ready"],
        "local_dsn_validated": values["local_dsn_validated"],
        "remote_host_blocked": values["remote_host_blocked"],
        "migration_revision_current": values["migration_revision_current"],
        "check_count": _decimal_text(values["check_count"]),
        "ready_check_count": _decimal_text(values["ready_check_count"]),
        "blocked_check_count": _decimal_text(values["blocked_check_count"]),
        "attention_check_count": _decimal_text(values["attention_check_count"]),
        "ready_check_ratio": _decimal_text(values["ready_check_ratio"]),
        "reason_codes": values["reason_codes"],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "digest": digest,
    }


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if len(value) != len(CHECK_FIELDS):
        raise ValueError("reason_codes must contain one code per check")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public label")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _require_ratio_decimal("ready_check_ratio", numerator / denominator)


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM, rounding=ROUND_HALF_UP), "f")


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=_json_default,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_default(value: object) -> object:
    if type(value) is tuple:
        return list(value)
    raise TypeError(f"unsupported public payload value: {value!r}")
