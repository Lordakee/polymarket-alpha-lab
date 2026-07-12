"""Pure public redaction readiness report for research packets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_PUBLIC_REDACTION_READINESS_VERSION = (
    "research-packet-public-redaction-readiness-report-v0"
)

RAW_IDENTIFIER_FIELDS_PRESENT_BLOCKER = "raw_identifier_fields_present_blocker"
UNSAFE_TEXT_TOKENS_PRESENT_BLOCKER = "unsafe_text_tokens_present_blocker"
REDACTED_PAYLOAD_NOT_READY_BLOCKER = "redacted_payload_not_ready_blocker"
PUBLIC_PAYLOAD_AUDIT_FAILED_BLOCKER = "public_payload_audit_failed_blocker"
SOURCE_REFERENCE_NOT_REDACTED_BLOCKER = "source_reference_not_redacted_blocker"
STORAGE_TERMS_PRESENT_BLOCKER = "storage_terms_present_blocker"
CREDENTIAL_TERMS_PRESENT_BLOCKER = "credential_terms_present_blocker"
READY_REASON = "research_packet_public_redaction_ready"

RAW_IDENTIFIER_FIELDS_REMOVED_ATTENTION = "raw_identifier_fields_removed_attention"
UNSAFE_TEXT_TOKENS_REMOVED_ATTENTION = "unsafe_text_tokens_removed_attention"
OPERATOR_PUBLIC_PAYLOAD_REQUIRES_REDACTION_ATTENTION = (
    "operator_public_payload_requires_redaction_attention"
)

_BLOCKED_REASON_PRIORITY = (
    RAW_IDENTIFIER_FIELDS_PRESENT_BLOCKER,
    UNSAFE_TEXT_TOKENS_PRESENT_BLOCKER,
    REDACTED_PAYLOAD_NOT_READY_BLOCKER,
    PUBLIC_PAYLOAD_AUDIT_FAILED_BLOCKER,
    SOURCE_REFERENCE_NOT_REDACTED_BLOCKER,
    STORAGE_TERMS_PRESENT_BLOCKER,
    CREDENTIAL_TERMS_PRESENT_BLOCKER,
    READY_REASON,
)
_ATTENTION_REASON_PRIORITY = (
    RAW_IDENTIFIER_FIELDS_REMOVED_ATTENTION,
    UNSAFE_TEXT_TOKENS_REMOVED_ATTENTION,
    OPERATOR_PUBLIC_PAYLOAD_REQUIRES_REDACTION_ATTENTION,
)
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_CHECK_COUNT = Decimal("7.000000")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchPacketPublicRedactionReadinessInput(_FinalDataclass):
    raw_identifier_field_count: Decimal
    unsafe_text_token_count: Decimal
    redacted_payload_ready: bool
    public_payload_audit_passed: bool
    source_reference_redacted: bool
    dsn_or_table_terms_absent: bool
    wallet_or_auth_terms_absent: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchPacketPublicRedactionReadinessInput, "input")
        for field_name in (
            "raw_identifier_field_count",
            "unsafe_text_token_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "redacted_payload_ready",
            "public_payload_audit_passed",
            "source_reference_redacted",
            "dsn_or_table_terms_absent",
            "wallet_or_auth_terms_absent",
        ):
            _require_bool(field_name, getattr(self, field_name))
        require_paper_only_flags("research packet public redaction readiness input", self)


@dataclass(frozen=True)
class ResearchPacketPublicRedactionReadinessReport(_FinalDataclass):
    config_version: str
    redaction_ready: bool
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    blocked_item_count: Decimal
    ready_ratio: Decimal
    raw_identifier_field_count: Decimal
    unsafe_text_token_count: Decimal
    redacted_payload_ready: bool
    public_payload_audit_passed: bool
    source_reference_redacted: bool
    storage_terms_absent: bool
    credential_terms_absent: bool
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchPacketPublicRedactionReadinessReport, "report")
        _require_public_string("config_version", self.config_version)
        _require_bool("redaction_ready", self.redaction_ready)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                _BLOCKED_REASON_PRIORITY,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                _ATTENTION_REASON_PRIORITY,
            ),
        )
        for field_name in (
            "blocked_item_count",
            "raw_identifier_field_count",
            "unsafe_text_token_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio("ready_ratio", self.ready_ratio),
        )
        for field_name in (
            "redacted_payload_ready",
            "public_payload_audit_passed",
            "source_reference_redacted",
            "storage_terms_absent",
            "credential_terms_absent",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_public_string("digest", self.digest)
        _validate_report_consistency(self)
        require_paper_only_flags("research packet public redaction readiness report", self)


def build_research_packet_public_redaction_readiness_report(
    redaction_input: ResearchPacketPublicRedactionReadinessInput,
    *,
    config_version: str = DEFAULT_RESEARCH_PACKET_PUBLIC_REDACTION_READINESS_VERSION,
) -> ResearchPacketPublicRedactionReadinessReport:
    if type(redaction_input) is not ResearchPacketPublicRedactionReadinessInput:
        raise ValueError(
            "redaction_input must be a ResearchPacketPublicRedactionReadinessInput",
        )
    _require_public_string("config_version", config_version)
    require_paper_only_flags("research packet public redaction readiness input", redaction_input)

    blocked_reason_codes = _blocked_reason_codes(redaction_input)
    redaction_ready = not blocked_reason_codes
    if redaction_ready:
        blocked_reason_codes = (READY_REASON,)
    attention_reason_codes = _attention_reason_codes(
        redaction_input,
        redaction_ready=redaction_ready,
    )
    blocked_item_count = _blocked_item_count(
        redaction_input,
        redaction_ready=redaction_ready,
    )
    ready_ratio = _ready_ratio(redaction_input)
    report = ResearchPacketPublicRedactionReadinessReport(
        config_version=config_version,
        redaction_ready=redaction_ready,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        blocked_item_count=blocked_item_count,
        ready_ratio=ready_ratio,
        raw_identifier_field_count=redaction_input.raw_identifier_field_count,
        unsafe_text_token_count=redaction_input.unsafe_text_token_count,
        redacted_payload_ready=redaction_input.redacted_payload_ready,
        public_payload_audit_passed=redaction_input.public_payload_audit_passed,
        source_reference_redacted=redaction_input.source_reference_redacted,
        storage_terms_absent=redaction_input.dsn_or_table_terms_absent,
        credential_terms_absent=redaction_input.wallet_or_auth_terms_absent,
        digest="pending",
    )
    digest = research_packet_public_redaction_readiness_digest(report)
    return ResearchPacketPublicRedactionReadinessReport(
        config_version=report.config_version,
        redaction_ready=report.redaction_ready,
        blocked_reason_codes=report.blocked_reason_codes,
        attention_reason_codes=report.attention_reason_codes,
        blocked_item_count=report.blocked_item_count,
        ready_ratio=report.ready_ratio,
        raw_identifier_field_count=report.raw_identifier_field_count,
        unsafe_text_token_count=report.unsafe_text_token_count,
        redacted_payload_ready=report.redacted_payload_ready,
        public_payload_audit_passed=report.public_payload_audit_passed,
        source_reference_redacted=report.source_reference_redacted,
        storage_terms_absent=report.storage_terms_absent,
        credential_terms_absent=report.credential_terms_absent,
        digest=digest,
    )


def research_packet_public_redaction_readiness_payload(
    report: ResearchPacketPublicRedactionReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketPublicRedactionReadinessReport:
        raise ValueError("report must be a ResearchPacketPublicRedactionReadinessReport")
    require_paper_only_flags("research packet public redaction readiness report", report)
    _validate_report_consistency(report)
    expected_digest = research_packet_public_redaction_readiness_digest(report)
    if report.digest != expected_digest:
        raise ValueError("digest does not match report payload")
    payload = _public_payload_for_digest(report)
    payload["digest"] = expected_digest
    return payload


def research_packet_public_redaction_readiness_digest(
    report: ResearchPacketPublicRedactionReadinessReport,
) -> str:
    if type(report) is not ResearchPacketPublicRedactionReadinessReport:
        raise ValueError("report must be a ResearchPacketPublicRedactionReadinessReport")
    payload = _public_payload_for_digest(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _blocked_reason_codes(
    redaction_input: ResearchPacketPublicRedactionReadinessInput,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if redaction_input.raw_identifier_field_count > _ZERO and (
        not redaction_input.redacted_payload_ready
    ):
        reason_codes.append(RAW_IDENTIFIER_FIELDS_PRESENT_BLOCKER)
    if redaction_input.unsafe_text_token_count > _ZERO and (
        not redaction_input.redacted_payload_ready
    ):
        reason_codes.append(UNSAFE_TEXT_TOKENS_PRESENT_BLOCKER)
    if not redaction_input.redacted_payload_ready:
        reason_codes.append(REDACTED_PAYLOAD_NOT_READY_BLOCKER)
    if not redaction_input.public_payload_audit_passed:
        reason_codes.append(PUBLIC_PAYLOAD_AUDIT_FAILED_BLOCKER)
    if not redaction_input.source_reference_redacted:
        reason_codes.append(SOURCE_REFERENCE_NOT_REDACTED_BLOCKER)
    if not redaction_input.dsn_or_table_terms_absent:
        reason_codes.append(STORAGE_TERMS_PRESENT_BLOCKER)
    if not redaction_input.wallet_or_auth_terms_absent:
        reason_codes.append(CREDENTIAL_TERMS_PRESENT_BLOCKER)
    return _normalize_reason_codes(
        "blocked_reason_codes",
        tuple(reason_codes),
        _BLOCKED_REASON_PRIORITY,
    )


def _attention_reason_codes(
    redaction_input: ResearchPacketPublicRedactionReadinessInput,
    *,
    redaction_ready: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if redaction_input.raw_identifier_field_count > _ZERO and redaction_ready:
        reason_codes.append(RAW_IDENTIFIER_FIELDS_REMOVED_ATTENTION)
    if redaction_input.unsafe_text_token_count > _ZERO and redaction_ready:
        reason_codes.append(UNSAFE_TEXT_TOKENS_REMOVED_ATTENTION)
    if not redaction_ready:
        reason_codes.append(OPERATOR_PUBLIC_PAYLOAD_REQUIRES_REDACTION_ATTENTION)
    return _normalize_reason_codes(
        "attention_reason_codes",
        tuple(reason_codes),
        _ATTENTION_REASON_PRIORITY,
    )


def _blocked_item_count(
    redaction_input: ResearchPacketPublicRedactionReadinessInput,
    *,
    redaction_ready: bool,
) -> Decimal:
    if redaction_ready:
        return _ZERO
    failed_count_checks = sum(
        1
        for value in (
            redaction_input.raw_identifier_field_count,
            redaction_input.unsafe_text_token_count,
        )
        if value > _ZERO
    )
    failed_boolean_checks = sum(
        1
        for passed in (
            redaction_input.redacted_payload_ready,
            redaction_input.public_payload_audit_passed,
            redaction_input.source_reference_redacted,
            redaction_input.dsn_or_table_terms_absent,
            redaction_input.wallet_or_auth_terms_absent,
        )
        if not passed
    )
    return _quantize_count(Decimal(failed_count_checks + failed_boolean_checks))


def _ready_ratio(redaction_input: ResearchPacketPublicRedactionReadinessInput) -> Decimal:
    not_ready_check_count = sum(
        1
        for value in (
            redaction_input.raw_identifier_field_count,
            redaction_input.unsafe_text_token_count,
        )
        if value > _ZERO
    ) + sum(
        1
        for passed in (
            redaction_input.redacted_payload_ready,
            redaction_input.public_payload_audit_passed,
            redaction_input.source_reference_redacted,
            redaction_input.dsn_or_table_terms_absent,
            redaction_input.wallet_or_auth_terms_absent,
        )
        if not passed
    )
    if not_ready_check_count <= 0:
        return _ONE
    with localcontext(_DECIMAL_CONTEXT):
        ratio = (
            _CHECK_COUNT - min(Decimal(not_ready_check_count), _CHECK_COUNT)
        ) / _CHECK_COUNT
    return ratio.quantize(_QUANT)


def _public_payload_for_digest(
    report: ResearchPacketPublicRedactionReadinessReport,
) -> dict[str, Any]:
    payload = json_ready_no_floats(
        {
            "config_version": report.config_version,
            "redaction_ready": report.redaction_ready,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "blocked_item_count": report.blocked_item_count,
            "ready_ratio": report.ready_ratio,
            "raw_identifier_field_count": report.raw_identifier_field_count,
            "unsafe_text_token_count": report.unsafe_text_token_count,
            "redacted_payload_ready": report.redacted_payload_ready,
            "public_payload_audit_passed": report.public_payload_audit_passed,
            "source_reference_redacted": report.source_reference_redacted,
            "storage_terms_absent": report.storage_terms_absent,
            "credential_terms_absent": report.credential_terms_absent,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    reject_unsafe_surface_fields("research packet public redaction readiness payload", payload)
    return payload


def _validate_report_consistency(
    report: ResearchPacketPublicRedactionReadinessReport,
) -> None:
    has_blockers = any(
        reason.endswith("_blocker") for reason in report.blocked_reason_codes
    )
    if report.redaction_ready == has_blockers:
        raise ValueError("redaction_ready must be False when blocker reasons are present")
    if report.redaction_ready and report.blocked_reason_codes != (READY_REASON,):
        raise ValueError("ready reports must carry only the ready blocked reason code")
    if not report.redaction_ready and READY_REASON in report.blocked_reason_codes:
        raise ValueError("blocked reports must not carry the ready reason code")
    if report.redaction_ready and report.blocked_item_count != _ZERO:
        raise ValueError("ready reports must have zero blocked_item_count")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    for unsafe_fragment in ("wallet", "auth", "dsn", "table", "order"):
        if unsafe_fragment in lowered:
            raise ValueError(f"{field_name} must not contain unsafe public text")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_count(value)


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return normalized


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    priority: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    allowed = set(priority)
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"unknown {field_name}: {reason_code}")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=priority.index))


__all__ = (
    "DEFAULT_RESEARCH_PACKET_PUBLIC_REDACTION_READINESS_VERSION",
    "ResearchPacketPublicRedactionReadinessInput",
    "ResearchPacketPublicRedactionReadinessReport",
    "build_research_packet_public_redaction_readiness_report",
    "research_packet_public_redaction_readiness_digest",
    "research_packet_public_redaction_readiness_payload",
)
