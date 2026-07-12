"""Read-only operator research packet completeness rollup report."""

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


DEFAULT_OPERATOR_RESEARCH_PACKET_COMPLETENESS_ROLLUP_VERSION = (
    "operator-research-packet-completeness-rollup-report-v0"
)

COMPLETE_REASON = "research_packet_completeness_rollup_complete"
EMPTY_REASON = "research_packet_rollup_empty"
MISSING_SOURCE_REASON = "research_packet_source_missing"
MISSING_COST_REASON = "research_packet_cost_missing"
MISSING_MEMORY_REASON = "research_packet_memory_missing"
INCOMPLETE_REASON = "research_packet_rollup_incomplete"

CONTINUE_MANUAL_REVIEW_STEP = "continue_manual_research_review"
COLLECT_RESEARCH_PACKETS_STEP = "manually_collect_research_packets"
COMPLETE_MISSING_FIELDS_STEP = "manually_complete_missing_research_packet_fields"

_REASON_PRIORITY = (
    COMPLETE_REASON,
    EMPTY_REASON,
    MISSING_SOURCE_REASON,
    MISSING_COST_REASON,
    MISSING_MEMORY_REASON,
    INCOMPLETE_REASON,
)
_STATUSES = ("complete", "empty", "incomplete")
_MANUAL_NEXT_STEPS = (
    CONTINUE_MANUAL_REVIEW_STEP,
    COLLECT_RESEARCH_PACKETS_STEP,
    COMPLETE_MISSING_FIELDS_STEP,
)
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class OperatorResearchPacketCompletenessRollupInput(_FinalDataclass):
    packet_count: Decimal
    complete_packet_count: Decimal
    missing_source_packet_count: Decimal
    missing_cost_packet_count: Decimal
    missing_memory_packet_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorResearchPacketCompletenessRollupInput, "input")
        for field_name in (
            "packet_count",
            "complete_packet_count",
            "missing_source_packet_count",
            "missing_cost_packet_count",
            "missing_memory_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.complete_packet_count > self.packet_count:
            raise ValueError("complete_packet_count cannot exceed packet_count")
        for field_name in (
            "missing_source_packet_count",
            "missing_cost_packet_count",
            "missing_memory_packet_count",
        ):
            if getattr(self, field_name) > self.packet_count:
                raise ValueError(f"{field_name} cannot exceed packet_count")
        require_paper_only_flags(
            "operator research packet completeness rollup input",
            self,
        )


@dataclass(frozen=True)
class OperatorResearchPacketCompletenessRollupReport(_FinalDataclass):
    config_version: str
    completeness_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    packet_count: Decimal
    complete_packet_count: Decimal
    missing_source_packet_count: Decimal
    missing_cost_packet_count: Decimal
    missing_memory_packet_count: Decimal
    incomplete_packet_count: Decimal
    completeness_ratio: Decimal
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, OperatorResearchPacketCompletenessRollupReport, "report")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "completeness_status",
            _normalize_member("completeness_status", self.completeness_status, _STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _normalize_member(
                "manual_next_step",
                self.manual_next_step,
                _MANUAL_NEXT_STEPS,
            ),
        )
        for field_name in (
            "packet_count",
            "complete_packet_count",
            "missing_source_packet_count",
            "missing_cost_packet_count",
            "missing_memory_packet_count",
            "incomplete_packet_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completeness_ratio",
            _require_ratio("completeness_ratio", self.completeness_ratio),
        )
        _require_public_string("payload_digest", self.payload_digest)
        _validate_report_consistency(self)
        require_paper_only_flags(
            "operator research packet completeness rollup report",
            self,
        )

    @property
    def public_payload(self) -> dict[str, Any]:
        return operator_research_packet_completeness_rollup_payload(self)


def build_operator_research_packet_completeness_rollup_report(
    rollup_input: OperatorResearchPacketCompletenessRollupInput,
    *,
    config_version: str = DEFAULT_OPERATOR_RESEARCH_PACKET_COMPLETENESS_ROLLUP_VERSION,
) -> OperatorResearchPacketCompletenessRollupReport:
    if type(rollup_input) is not OperatorResearchPacketCompletenessRollupInput:
        raise ValueError(
            "rollup_input must be an OperatorResearchPacketCompletenessRollupInput",
        )
    _require_public_string("config_version", config_version)
    require_paper_only_flags(
        "operator research packet completeness rollup input",
        rollup_input,
    )

    status = _completeness_status(rollup_input)
    reason_codes = _reason_codes(rollup_input, status)
    manual_next_step = _manual_next_step(status)
    incomplete_packet_count = rollup_input.packet_count - rollup_input.complete_packet_count
    completeness_ratio = _completeness_ratio(rollup_input)
    report = OperatorResearchPacketCompletenessRollupReport(
        config_version=config_version,
        completeness_status=status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        packet_count=rollup_input.packet_count,
        complete_packet_count=rollup_input.complete_packet_count,
        missing_source_packet_count=rollup_input.missing_source_packet_count,
        missing_cost_packet_count=rollup_input.missing_cost_packet_count,
        missing_memory_packet_count=rollup_input.missing_memory_packet_count,
        incomplete_packet_count=incomplete_packet_count,
        completeness_ratio=completeness_ratio,
        payload_digest="pending",
    )
    digest = operator_research_packet_completeness_rollup_payload_digest(report)
    return OperatorResearchPacketCompletenessRollupReport(
        config_version=report.config_version,
        completeness_status=report.completeness_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        packet_count=report.packet_count,
        complete_packet_count=report.complete_packet_count,
        missing_source_packet_count=report.missing_source_packet_count,
        missing_cost_packet_count=report.missing_cost_packet_count,
        missing_memory_packet_count=report.missing_memory_packet_count,
        incomplete_packet_count=report.incomplete_packet_count,
        completeness_ratio=report.completeness_ratio,
        payload_digest=digest,
    )


def operator_research_packet_completeness_rollup_payload(
    report: OperatorResearchPacketCompletenessRollupReport,
) -> dict[str, Any]:
    if type(report) is not OperatorResearchPacketCompletenessRollupReport:
        raise ValueError(
            "report must be an OperatorResearchPacketCompletenessRollupReport",
        )
    require_paper_only_flags(
        "operator research packet completeness rollup report",
        report,
    )
    _validate_report_consistency(report)
    expected_digest = operator_research_packet_completeness_rollup_payload_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest does not match report payload")
    payload = _public_payload_for_digest(report)
    payload["payload_digest"] = expected_digest
    return payload


def operator_research_packet_completeness_rollup_payload_digest(
    report: OperatorResearchPacketCompletenessRollupReport,
) -> str:
    if type(report) is not OperatorResearchPacketCompletenessRollupReport:
        raise ValueError(
            "report must be an OperatorResearchPacketCompletenessRollupReport",
        )
    payload = _public_payload_for_digest(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _completeness_status(
    rollup_input: OperatorResearchPacketCompletenessRollupInput,
) -> str:
    if rollup_input.packet_count == _ZERO:
        return "empty"
    if (
        rollup_input.complete_packet_count == rollup_input.packet_count
        and rollup_input.missing_source_packet_count == _ZERO
        and rollup_input.missing_cost_packet_count == _ZERO
        and rollup_input.missing_memory_packet_count == _ZERO
    ):
        return "complete"
    return "incomplete"


def _reason_codes(
    rollup_input: OperatorResearchPacketCompletenessRollupInput,
    status: str,
) -> tuple[str, ...]:
    if status == "complete":
        return (COMPLETE_REASON,)
    if status == "empty":
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if rollup_input.missing_source_packet_count > _ZERO:
        reason_codes.append(MISSING_SOURCE_REASON)
    if rollup_input.missing_cost_packet_count > _ZERO:
        reason_codes.append(MISSING_COST_REASON)
    if rollup_input.missing_memory_packet_count > _ZERO:
        reason_codes.append(MISSING_MEMORY_REASON)
    reason_codes.append(INCOMPLETE_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _manual_next_step(status: str) -> str:
    if status == "complete":
        return CONTINUE_MANUAL_REVIEW_STEP
    if status == "empty":
        return COLLECT_RESEARCH_PACKETS_STEP
    return COMPLETE_MISSING_FIELDS_STEP


def _completeness_ratio(
    rollup_input: OperatorResearchPacketCompletenessRollupInput,
) -> Decimal:
    if rollup_input.packet_count == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        ratio = rollup_input.complete_packet_count / rollup_input.packet_count
    return ratio.quantize(_QUANT)


def _public_payload_for_digest(
    report: OperatorResearchPacketCompletenessRollupReport,
) -> dict[str, Any]:
    payload = json_ready_no_floats(
        {
            "config_version": report.config_version,
            "completeness_status": report.completeness_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "packet_count": report.packet_count,
            "complete_packet_count": report.complete_packet_count,
            "missing_source_packet_count": report.missing_source_packet_count,
            "missing_cost_packet_count": report.missing_cost_packet_count,
            "missing_memory_packet_count": report.missing_memory_packet_count,
            "incomplete_packet_count": report.incomplete_packet_count,
            "completeness_ratio": report.completeness_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    reject_unsafe_surface_fields(
        "operator research packet completeness rollup payload",
        payload,
    )
    return payload


def _validate_report_consistency(
    report: OperatorResearchPacketCompletenessRollupReport,
) -> None:
    if report.complete_packet_count > report.packet_count:
        raise ValueError("complete_packet_count cannot exceed packet_count")
    expected_incomplete_packet_count = _quantize_count(
        report.packet_count - report.complete_packet_count,
    )
    if report.incomplete_packet_count != expected_incomplete_packet_count:
        raise ValueError("incomplete_packet_count must match packet counts")
    source = OperatorResearchPacketCompletenessRollupInput(
        packet_count=report.packet_count,
        complete_packet_count=report.complete_packet_count,
        missing_source_packet_count=report.missing_source_packet_count,
        missing_cost_packet_count=report.missing_cost_packet_count,
        missing_memory_packet_count=report.missing_memory_packet_count,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_status = _completeness_status(source)
    if report.completeness_status != expected_status:
        raise ValueError("completeness_status must match packet counts")
    if report.reason_codes != _reason_codes(source, expected_status):
        raise ValueError("reason_codes must match packet counts")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match completeness_status")
    if report.completeness_ratio != _completeness_ratio(source):
        raise ValueError("completeness_ratio must match packet counts")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    for unsafe_fragment in (
        "live",
        "auth",
        "wallet",
        "key",
        "sign",
        "execution",
        "order",
        "jsonl",
    ):
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


def _normalize_member(
    field_name: str,
    value: object,
    supported_values: tuple[str, ...],
) -> str:
    _require_public_string(field_name, value)
    if value not in supported_values:
        raise ValueError(f"{field_name} must be supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    allowed = set(_REASON_PRIORITY)
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"unknown {field_name}: {reason_code}")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=_REASON_PRIORITY.index))


__all__ = (
    "DEFAULT_OPERATOR_RESEARCH_PACKET_COMPLETENESS_ROLLUP_VERSION",
    "OperatorResearchPacketCompletenessRollupInput",
    "OperatorResearchPacketCompletenessRollupReport",
    "build_operator_research_packet_completeness_rollup_report",
    "operator_research_packet_completeness_rollup_payload",
    "operator_research_packet_completeness_rollup_payload_digest",
)
