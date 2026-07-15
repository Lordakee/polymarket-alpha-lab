"""Read-only end-to-end readiness report for probability event screens."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
)


__all__ = (
    "END_TO_END_READINESS_BANDS",
    "ProbabilityEventScreenEndToEndReadinessInput",
    "ProbabilityEventScreenEndToEndReadinessReport",
    "build_probability_event_screen_end_to_end_readiness_report",
    "probability_event_screen_end_to_end_readiness_report_digest",
    "probability_event_screen_end_to_end_readiness_report_to_payload",
    "validate_probability_event_screen_end_to_end_readiness_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")

END_TO_END_READINESS_BANDS = ("ready", "attention", "blocked")
READY_REASON_CODE = "probability_event_screen_end_to_end_ready"

BLOCKED_REASON_SEQUENCE = (
    "end_to_end_acquisition_not_ready",
    "end_to_end_screen_contract_not_ready",
    "end_to_end_quality_index_not_ready",
    "end_to_end_manual_decision_gate_not_ready",
    "end_to_end_operator_runbook_not_ready",
    "end_to_end_release_gate_not_ready",
    "end_to_end_learning_feedback_not_ready",
    "end_to_end_supabase_persistence_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "end_to_end_paper_only_flag_not_set",
    "end_to_end_report_only_flag_not_set",
    "end_to_end_readonly_flag_not_set",
    READY_REASON_CODE,
)
FLAG_ATTENTION_REASON_CODES = ATTENTION_REASON_SEQUENCE[:-1]

PAYLOAD_KEYS = (
    "acquisition_ready",
    "screen_contract_ready",
    "quality_index_ready",
    "manual_decision_gate_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "learning_feedback_ready",
    "supabase_persistence_ready",
    "end_to_end_ready",
    "readiness_band",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

_BOOL_INPUT_FIELDS = (
    "acquisition_ready",
    "screen_contract_ready",
    "quality_index_ready",
    "manual_decision_gate_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "learning_feedback_ready",
    "supabase_persistence_ready",
)

_BLOCKING_CHECKS = (
    ("acquisition_ready", "end_to_end_acquisition_not_ready"),
    ("screen_contract_ready", "end_to_end_screen_contract_not_ready"),
    ("quality_index_ready", "end_to_end_quality_index_not_ready"),
    ("manual_decision_gate_ready", "end_to_end_manual_decision_gate_not_ready"),
    ("operator_runbook_ready", "end_to_end_operator_runbook_not_ready"),
    ("release_gate_ready", "end_to_end_release_gate_not_ready"),
    ("learning_feedback_ready", "end_to_end_learning_feedback_not_ready"),
    ("supabase_persistence_ready", "end_to_end_supabase_persistence_not_ready"),
)


class _EndToEndReadinessPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _EndToEndReadinessPublicDataclass and issubclass(
                base,
                _EndToEndReadinessPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventScreenEndToEndReadinessInput(
    _EndToEndReadinessPublicDataclass,
):
    acquisition_ready: bool
    screen_contract_ready: bool
    quality_index_ready: bool
    manual_decision_gate_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    learning_feedback_ready: bool
    supabase_persistence_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenEndToEndReadinessInput,
            "end-to-end readiness input",
        )
        for field_name in _BOOL_INPUT_FIELDS + (
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class ProbabilityEventScreenEndToEndReadinessReport(
    _EndToEndReadinessPublicDataclass,
):
    acquisition_ready: bool
    screen_contract_ready: bool
    quality_index_ready: bool
    manual_decision_gate_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    learning_feedback_ready: bool
    supabase_persistence_ready: bool
    end_to_end_ready: bool
    readiness_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenEndToEndReadinessReport,
            "end-to-end readiness report",
        )
        for field_name in _BOOL_INPUT_FIELDS + (
            "end_to_end_ready",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "readiness_band",
            _normalize_member("readiness_band", self.readiness_band),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_end_to_end_readiness_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_end_to_end_readiness_report_digest(self)


def build_probability_event_screen_end_to_end_readiness_report(
    readiness: ProbabilityEventScreenEndToEndReadinessInput,
) -> ProbabilityEventScreenEndToEndReadinessReport:
    if type(readiness) is not ProbabilityEventScreenEndToEndReadinessInput:
        raise ValueError(
            "readiness must be a ProbabilityEventScreenEndToEndReadinessInput",
        )

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _end_to_end_findings(readiness)
    )
    readiness_band = _readiness_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenEndToEndReadinessReport(
        acquisition_ready=readiness.acquisition_ready,
        screen_contract_ready=readiness.screen_contract_ready,
        quality_index_ready=readiness.quality_index_ready,
        manual_decision_gate_ready=readiness.manual_decision_gate_ready,
        operator_runbook_ready=readiness.operator_runbook_ready,
        release_gate_ready=readiness.release_gate_ready,
        learning_feedback_ready=readiness.learning_feedback_ready,
        supabase_persistence_ready=readiness.supabase_persistence_ready,
        end_to_end_ready=readiness_band == "ready",
        readiness_band=readiness_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_screen_end_to_end_readiness_report_to_payload(
    report: ProbabilityEventScreenEndToEndReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenEndToEndReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenEndToEndReadinessReport",
        )
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "acquisition_ready": report.acquisition_ready,
            "screen_contract_ready": report.screen_contract_ready,
            "quality_index_ready": report.quality_index_ready,
            "manual_decision_gate_ready": report.manual_decision_gate_ready,
            "operator_runbook_ready": report.operator_runbook_ready,
            "release_gate_ready": report.release_gate_ready,
            "learning_feedback_ready": report.learning_feedback_ready,
            "supabase_persistence_ready": report.supabase_persistence_ready,
            "end_to_end_ready": report.end_to_end_ready,
            "readiness_band": report.readiness_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_screen_end_to_end_readiness_public_payload(payload)
    return payload


def probability_event_screen_end_to_end_readiness_report_digest(
    report: ProbabilityEventScreenEndToEndReadinessReport,
) -> str:
    payload = probability_event_screen_end_to_end_readiness_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_screen_end_to_end_readiness_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical end-to-end readiness schema")
    reject_unsafe_surface_fields("end-to-end readiness public payload", payload)
    for field_name in (
        *_BOOL_INPUT_FIELDS,
        "end_to_end_ready",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_member("readiness_band", payload["readiness_band"])
    blocked_reason_codes = _normalize_payload_reason_codes(
        "blocked_reason_codes",
        payload["blocked_reason_codes"],
        BLOCKED_REASON_SEQUENCE,
    )
    attention_reason_codes = _normalize_payload_reason_codes(
        "attention_reason_codes",
        payload["attention_reason_codes"],
        ATTENTION_REASON_SEQUENCE,
    )
    ready_ratio_value = payload["ready_ratio"]
    if type(ready_ratio_value) is not str:
        raise ValueError("ready_ratio must be serialized as a string")
    ready_ratio = _normalize_ratio("ready_ratio", Decimal(ready_ratio_value))
    expected_blocked, _expected_attention, ready_component_count = _payload_findings(
        payload,
    )
    if blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if not _payload_attention_codes_are_valid(
        blocked_reason_codes,
        attention_reason_codes,
    ):
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _readiness_band(blocked_reason_codes, attention_reason_codes)
    if payload["readiness_band"] != expected_band:
        raise ValueError("readiness_band must match reason codes")
    if payload["end_to_end_ready"] is not (expected_band == "ready"):
        raise ValueError("end_to_end_ready must match readiness_band")
    if ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")
    return payload


def _payload_attention_codes_are_valid(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> bool:
    if blocked_reason_codes:
        return attention_reason_codes == ()
    if attention_reason_codes == (READY_REASON_CODE,):
        return True
    return bool(attention_reason_codes) and all(
        reason_code in FLAG_ATTENTION_REASON_CODES
        for reason_code in attention_reason_codes
    )


def _end_to_end_findings(
    readiness: ProbabilityEventScreenEndToEndReadinessInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0
    for field_name, reason_code in _BLOCKING_CHECKS:
        if getattr(readiness, field_name) is True:
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    attention: list[str] = []
    if readiness.paper_only is not True:
        attention.append("end_to_end_paper_only_flag_not_set")
    if readiness.report_only is not True:
        attention.append("end_to_end_report_only_flag_not_set")
    if readiness.readonly is not True:
        attention.append("end_to_end_readonly_flag_not_set")

    blocked_reason_codes = tuple(
        reason for reason in BLOCKED_REASON_SEQUENCE if reason in blocked
    )
    if blocked_reason_codes:
        return blocked_reason_codes, (), ready_component_count
    attention_reason_codes = tuple(
        reason for reason in ATTENTION_REASON_SEQUENCE if reason in attention
    )
    if not attention_reason_codes:
        attention_reason_codes = (READY_REASON_CODE,)
    return blocked_reason_codes, attention_reason_codes, ready_component_count


def _payload_findings(
    payload: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenEndToEndReadinessInput(
        acquisition_ready=payload["acquisition_ready"],  # type: ignore[arg-type]
        screen_contract_ready=payload["screen_contract_ready"],  # type: ignore[arg-type]
        quality_index_ready=payload["quality_index_ready"],  # type: ignore[arg-type]
        manual_decision_gate_ready=payload["manual_decision_gate_ready"],  # type: ignore[arg-type]
        operator_runbook_ready=payload["operator_runbook_ready"],  # type: ignore[arg-type]
        release_gate_ready=payload["release_gate_ready"],  # type: ignore[arg-type]
        learning_feedback_ready=payload["learning_feedback_ready"],  # type: ignore[arg-type]
        supabase_persistence_ready=payload["supabase_persistence_ready"],  # type: ignore[arg-type]
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    return _end_to_end_findings(source)


def _validate_report(report: ProbabilityEventScreenEndToEndReadinessReport) -> None:
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _report_findings(report)
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _readiness_band(blocked_reason_codes, attention_reason_codes)
    if report.readiness_band != expected_band:
        raise ValueError("readiness_band must match reason codes")
    if report.end_to_end_ready is not (expected_band == "ready"):
        raise ValueError("end_to_end_ready must match readiness_band")
    if report.ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")


def _report_findings(
    report: ProbabilityEventScreenEndToEndReadinessReport,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenEndToEndReadinessInput(
        acquisition_ready=report.acquisition_ready,
        screen_contract_ready=report.screen_contract_ready,
        quality_index_ready=report.quality_index_ready,
        manual_decision_gate_ready=report.manual_decision_gate_ready,
        operator_runbook_ready=report.operator_runbook_ready,
        release_gate_ready=report.release_gate_ready,
        learning_feedback_ready=report.learning_feedback_ready,
        supabase_persistence_ready=report.supabase_persistence_ready,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    return _end_to_end_findings(source)


def _readiness_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes != (READY_REASON_CODE,):
        return "attention"
    return "ready"


def _normalize_member(field_name: str, value: object) -> str:
    if type(value) is not str or value not in END_TO_END_READINESS_BANDS:
        raise ValueError(f"{field_name} must be a supported end-to-end readiness band")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value, supported_reason_codes)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(
            field_name,
            tuple(value),
            supported_reason_codes,
        )
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value, supported_reason_codes)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in supported_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(
        reason_code for reason_code in supported_reason_codes if reason_code in seen
    )
    if reason_codes != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio("ready_ratio", numerator / denominator)


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
