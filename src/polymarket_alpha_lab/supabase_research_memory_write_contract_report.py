"""Read-only Supabase research memory contract report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re


__all__ = (
    "SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION",
    "SupabaseResearchMemoryWriteContractInput",
    "SupabaseResearchMemoryWriteContractPublicPayload",
    "SupabaseResearchMemoryWriteContractReport",
    "build_supabase_research_memory_write_contract_report",
    "supabase_research_memory_write_contract_report_digest",
    "supabase_research_memory_write_contract_report_payload",
)


SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION = (
    "supabase-research-memory-write-contract-report-v0"
)

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

CHECK_FIELDS = (
    "required_tables_present",
    "schema_version_declared",
    "idempotency_key_present",
    "source_digest_present",
    "local_postgres_dsn_validator_present",
    "local_postgres_only_confirmed",
    "hosted_database_absent",
    "no_file_persistence_confirmed",
)
REASON_BY_FIELD = {
    "required_tables_present": "required_tables_missing",
    "schema_version_declared": "schema_version_missing",
    "idempotency_key_present": "idempotency_key_missing",
    "source_digest_present": "source_digest_missing",
    "local_postgres_dsn_validator_present": "local_postgres_dsn_validator_missing",
    "local_postgres_only_confirmed": "local_postgres_only_not_confirmed",
    "hosted_database_absent": "hosted_database_not_confirmed_absent",
    "no_file_persistence_confirmed": "file_persistence_not_confirmed",
}
READY_REASON = "supabase_research_memory_write_contract_ready"
CONTRACT_STATUSES = ("ready", "blocked")
REASON_CODES = tuple(REASON_BY_FIELD.values()) + (READY_REASON,)
READY_MANUAL_NEXT_STEP = (
    "Manual reviewer may approve the planned local Supabase research memory "
    "contract for Phase 2 implementation review."
)
BLOCKED_MANUAL_NEXT_STEP = (
    "Manual reviewer must document the missing local Supabase research memory "
    "contract evidence before Phase 2 implementation review."
)

PAYLOAD_FIELDS = (
    "config_version",
    "required_tables_present",
    "schema_version_declared",
    "idempotency_key_present",
    "source_digest_present",
    "local_postgres_dsn_validator_present",
    "local_postgres_only_confirmed",
    "hosted_database_absent",
    "no_file_persistence_confirmed",
    "contract_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class SupabaseResearchMemoryWriteContractPublicPayload(dict[str, object]):
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
class SupabaseResearchMemoryWriteContractInput:
    required_tables_present: bool
    schema_version_declared: bool
    idempotency_key_present: bool
    source_digest_present: bool
    local_postgres_dsn_validator_present: bool
    local_postgres_only_confirmed: bool
    hosted_database_absent: bool
    no_file_persistence_confirmed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SupabaseResearchMemoryWriteContractInput:
            raise TypeError(
                "SupabaseResearchMemoryWriteContractInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SupabaseResearchMemoryWriteContractInput:
            raise ValueError("input must be exactly SupabaseResearchMemoryWriteContractInput")
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class SupabaseResearchMemoryWriteContractReport:
    config_version: str
    required_tables_present: bool
    schema_version_declared: bool
    idempotency_key_present: bool
    source_digest_present: bool
    local_postgres_dsn_validator_present: bool
    local_postgres_only_confirmed: bool
    hosted_database_absent: bool
    no_file_persistence_confirmed: bool
    contract_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SupabaseResearchMemoryWriteContractReport:
            raise TypeError(
                "SupabaseResearchMemoryWriteContractReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SupabaseResearchMemoryWriteContractReport:
            raise ValueError("report must be exactly SupabaseResearchMemoryWriteContractReport")
        _require_public_label("config_version", self.config_version)
        if self.config_version != SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION:
            raise ValueError("config_version must be the supported report version")
        for field_name in CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "contract_status",
            _require_contract_status("contract_status", self.contract_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags(self)
        _require_digest("payload_digest", self.payload_digest)
        _validate_report(self)
        expected_digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> SupabaseResearchMemoryWriteContractPublicPayload:
        payload = SupabaseResearchMemoryWriteContractPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_supabase_research_memory_write_contract_report(
    inputs: SupabaseResearchMemoryWriteContractInput,
) -> SupabaseResearchMemoryWriteContractReport:
    """Build a deterministic read-only Supabase research memory contract report."""

    if type(inputs) is not SupabaseResearchMemoryWriteContractInput:
        raise ValueError("inputs must be a SupabaseResearchMemoryWriteContractInput")
    _require_hard_flags(inputs)
    check_values = {field_name: getattr(inputs, field_name) for field_name in CHECK_FIELDS}
    reason_codes = _reason_codes(check_values)
    contract_status = _contract_status(reason_codes)
    values: dict[str, object] = {
        "config_version": SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION,
        **check_values,
        "contract_status": contract_status,
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(contract_status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SupabaseResearchMemoryWriteContractReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def supabase_research_memory_write_contract_report_payload(
    report: SupabaseResearchMemoryWriteContractReport | Mapping[str, object],
) -> SupabaseResearchMemoryWriteContractPublicPayload:
    if type(report) is SupabaseResearchMemoryWriteContractReport:
        _require_hard_flags(report)
        _validate_report(report)
        expected_digest = _payload_digest(_payload_items(report, payload_digest=""))
        if report.payload_digest != expected_digest:
            raise ValueError("payload_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return SupabaseResearchMemoryWriteContractPublicPayload(report)
    raise ValueError(
        "report must be a SupabaseResearchMemoryWriteContractReport or public payload",
    )


def supabase_research_memory_write_contract_report_digest(
    report: SupabaseResearchMemoryWriteContractReport | Mapping[str, object],
) -> str:
    return str(
        supabase_research_memory_write_contract_report_payload(report)[
            "payload_digest"
        ],
    )


def _reason_codes(values: Mapping[str, bool]) -> tuple[str, ...]:
    reasons = tuple(
        reason for field_name, reason in REASON_BY_FIELD.items() if values[field_name] is not True
    )
    if not reasons:
        return (READY_REASON,)
    return reasons


def _contract_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    return "blocked"


def _manual_next_step(contract_status: str) -> str:
    if contract_status == "ready":
        return READY_MANUAL_NEXT_STEP
    return BLOCKED_MANUAL_NEXT_STEP


def _validate_report(report: SupabaseResearchMemoryWriteContractReport) -> None:
    check_values = {field_name: getattr(report, field_name) for field_name in CHECK_FIELDS}
    reason_codes = _reason_codes(check_values)
    contract_status = _contract_status(reason_codes)
    manual_next_step = _manual_next_step(contract_status)
    if report.contract_status != contract_status:
        raise ValueError("contract_status must match contract checks")
    if report.reason_codes != reason_codes:
        raise ValueError("reason_codes must match contract checks")
    if report.manual_next_step != manual_next_step:
        raise ValueError("manual_next_step must match contract checks")


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if set(payload) != set(PAYLOAD_FIELDS):
        raise ValueError("public payload fields must match the report schema exactly")
    _require_public_label("config_version", payload["config_version"])
    if payload["config_version"] != SUPABASE_RESEARCH_MEMORY_WRITE_CONTRACT_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")
    for field_name in CHECK_FIELDS:
        _require_bool(field_name, payload[field_name])
    check_values = {field_name: payload[field_name] for field_name in CHECK_FIELDS}
    reason_codes = _reason_codes(check_values)  # type: ignore[arg-type]
    contract_status = _contract_status(reason_codes)
    manual_next_step = _manual_next_step(contract_status)
    if _require_contract_status("contract_status", payload["contract_status"]) != contract_status:
        raise ValueError("contract_status must match contract checks")
    if _normalize_reason_codes(_require_string_tuple(payload["reason_codes"])) != reason_codes:
        raise ValueError("reason_codes must match contract checks")
    if _require_manual_next_step("manual_next_step", payload["manual_next_step"]) != manual_next_step:
        raise ValueError("manual_next_step must match contract checks")
    _require_hard_flags(_MappingFlags(payload))
    _require_digest("payload_digest", payload["payload_digest"])
    expected_digest = _payload_digest(dict(payload) | {"payload_digest": ""})
    if payload["payload_digest"] != expected_digest:
        raise ValueError("payload_digest must match public payload")


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
    report: SupabaseResearchMemoryWriteContractReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    values = {
        "config_version": report.config_version,
        **{field_name: getattr(report, field_name) for field_name in CHECK_FIELDS},
        "contract_status": report.contract_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": payload_digest,
    }
    return _payload_values(values, payload_digest=payload_digest)


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field_name in PAYLOAD_FIELDS:
        value = payload_digest if field_name == "payload_digest" else values[field_name]
        if type(value) is Decimal:
            payload[field_name] = format(value, "f")
        else:
            payload[field_name] = value
    return payload


def _payload_digest(payload: Mapping[str, object]) -> str:
    canonical_payload = {field_name: payload[field_name] for field_name in PAYLOAD_FIELDS}
    canonical = json.dumps(canonical_payload, separators=(",", ":"))
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


def _require_contract_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in CONTRACT_STATUSES:
        raise ValueError(f"{field_name} must be a supported contract status")
    return value


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in (
        READY_MANUAL_NEXT_STEP,
        BLOCKED_MANUAL_NEXT_STEP,
    ):
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or any(type(value) is not str for value in values):
        raise ValueError("reason_codes must be a tuple of reason code strings")
    if len(values) != len(set(values)):
        raise ValueError("reason_codes must not contain duplicates")
    if any(value not in REASON_CODES for value in values):
        raise ValueError("reason_codes contains an unsupported reason code")
    return values


def _require_string_tuple(value: object) -> tuple[str, ...]:
    if type(value) is tuple and all(type(item) is str for item in value):
        return value
    if type(value) is list and all(type(item) is str for item in value):
        return tuple(value)
    raise ValueError("reason_codes must be strings")
