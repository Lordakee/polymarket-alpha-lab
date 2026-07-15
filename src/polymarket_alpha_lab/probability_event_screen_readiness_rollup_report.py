"""Read-only readiness rollup report for probability event screens."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
)


__all__ = (
    "ProbabilityEventScreenReadinessRollupInput",
    "ProbabilityEventScreenReadinessRollupReport",
    "READINESS_ROLLUP_BANDS",
    "build_probability_event_screen_readiness_rollup_report",
    "probability_event_screen_readiness_rollup_report_digest",
    "probability_event_screen_readiness_rollup_report_to_payload",
    "validate_probability_event_screen_readiness_rollup_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")

READINESS_ROLLUP_BANDS = ("ready", "attention", "blocked")
READY_REASON_CODE = "probability_event_screen_readiness_rollup_ready"

BLOCKED_REASON_SEQUENCE = (
    "rollup_end_to_end_not_ready",
    "rollup_system_health_not_ready",
    "rollup_validation_matrix_not_ready",
    "rollup_node_handoff_not_ready",
    "rollup_operator_dashboard_not_ready",
    "rollup_operator_runbook_not_ready",
    "rollup_release_gate_not_ready",
    "rollup_knowledge_base_index_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "rollup_paper_only_flag_not_set",
    "rollup_report_only_flag_not_set",
    "rollup_readonly_flag_not_set",
    READY_REASON_CODE,
)

PAYLOAD_KEYS = (
    "end_to_end_ready",
    "system_health_ready",
    "validation_matrix_ready",
    "node_handoff_ready",
    "operator_dashboard_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "knowledge_base_index_ready",
    "readiness_rollup_ready",
    "rollup_band",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

_BOOL_INPUT_FIELDS = (
    "end_to_end_ready",
    "system_health_ready",
    "validation_matrix_ready",
    "node_handoff_ready",
    "operator_dashboard_ready",
    "operator_runbook_ready",
    "release_gate_ready",
    "knowledge_base_index_ready",
)

_BLOCKING_CHECKS = (
    ("end_to_end_ready", "rollup_end_to_end_not_ready"),
    ("system_health_ready", "rollup_system_health_not_ready"),
    ("validation_matrix_ready", "rollup_validation_matrix_not_ready"),
    ("node_handoff_ready", "rollup_node_handoff_not_ready"),
    ("operator_dashboard_ready", "rollup_operator_dashboard_not_ready"),
    ("operator_runbook_ready", "rollup_operator_runbook_not_ready"),
    ("release_gate_ready", "rollup_release_gate_not_ready"),
    ("knowledge_base_index_ready", "rollup_knowledge_base_index_not_ready"),
)


class _RollupPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _RollupPublicDataclass and issubclass(
                base,
                _RollupPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventScreenReadinessRollupInput(_RollupPublicDataclass):
    end_to_end_ready: bool
    system_health_ready: bool
    validation_matrix_ready: bool
    node_handoff_ready: bool
    operator_dashboard_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    knowledge_base_index_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenReadinessRollupInput,
            "readiness rollup input",
        )
        for field_name in _BOOL_INPUT_FIELDS + (
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class ProbabilityEventScreenReadinessRollupReport(_RollupPublicDataclass):
    end_to_end_ready: bool
    system_health_ready: bool
    validation_matrix_ready: bool
    node_handoff_ready: bool
    operator_dashboard_ready: bool
    operator_runbook_ready: bool
    release_gate_ready: bool
    knowledge_base_index_ready: bool
    readiness_rollup_ready: bool
    rollup_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenReadinessRollupReport,
            "readiness rollup report",
        )
        for field_name in _BOOL_INPUT_FIELDS + (
            "readiness_rollup_ready",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "rollup_band",
            _normalize_member("rollup_band", self.rollup_band),
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
        return probability_event_screen_readiness_rollup_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_readiness_rollup_report_digest(self)


def build_probability_event_screen_readiness_rollup_report(
    readiness: ProbabilityEventScreenReadinessRollupInput,
) -> ProbabilityEventScreenReadinessRollupReport:
    if type(readiness) is not ProbabilityEventScreenReadinessRollupInput:
        raise ValueError(
            "readiness must be a ProbabilityEventScreenReadinessRollupInput",
        )

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _rollup_findings(readiness)
    )
    rollup_band = _rollup_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenReadinessRollupReport(
        end_to_end_ready=readiness.end_to_end_ready,
        system_health_ready=readiness.system_health_ready,
        validation_matrix_ready=readiness.validation_matrix_ready,
        node_handoff_ready=readiness.node_handoff_ready,
        operator_dashboard_ready=readiness.operator_dashboard_ready,
        operator_runbook_ready=readiness.operator_runbook_ready,
        release_gate_ready=readiness.release_gate_ready,
        knowledge_base_index_ready=readiness.knowledge_base_index_ready,
        readiness_rollup_ready=rollup_band == "ready",
        rollup_band=rollup_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_screen_readiness_rollup_report_to_payload(
    report: ProbabilityEventScreenReadinessRollupReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenReadinessRollupReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenReadinessRollupReport",
        )
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "end_to_end_ready": report.end_to_end_ready,
            "system_health_ready": report.system_health_ready,
            "validation_matrix_ready": report.validation_matrix_ready,
            "node_handoff_ready": report.node_handoff_ready,
            "operator_dashboard_ready": report.operator_dashboard_ready,
            "operator_runbook_ready": report.operator_runbook_ready,
            "release_gate_ready": report.release_gate_ready,
            "knowledge_base_index_ready": report.knowledge_base_index_ready,
            "readiness_rollup_ready": report.readiness_rollup_ready,
            "rollup_band": report.rollup_band,
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
    validate_probability_event_screen_readiness_rollup_public_payload(payload)
    return payload


def probability_event_screen_readiness_rollup_report_digest(
    report: ProbabilityEventScreenReadinessRollupReport,
) -> str:
    payload = probability_event_screen_readiness_rollup_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_screen_readiness_rollup_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical readiness rollup schema")
    reject_unsafe_surface_fields("readiness rollup public payload", payload)
    for field_name in (
        *_BOOL_INPUT_FIELDS,
        "readiness_rollup_ready",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_member("rollup_band", payload["rollup_band"])
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
    expected_blocked, ready_component_count = _payload_blocked_findings(payload)
    if blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match readiness fields")
    _validate_payload_attention_reason_codes(
        blocked_reason_codes,
        attention_reason_codes,
    )
    expected_band = _rollup_band(blocked_reason_codes, attention_reason_codes)
    if payload["rollup_band"] != expected_band:
        raise ValueError("rollup_band must match reason codes")
    if payload["readiness_rollup_ready"] is not (expected_band == "ready"):
        raise ValueError("readiness_rollup_ready must match rollup_band")
    if ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")
    return payload


def _rollup_findings(
    readiness: ProbabilityEventScreenReadinessRollupInput,
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
        attention.append("rollup_paper_only_flag_not_set")
    if readiness.report_only is not True:
        attention.append("rollup_report_only_flag_not_set")
    if readiness.readonly is not True:
        attention.append("rollup_readonly_flag_not_set")

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


def _payload_blocked_findings(
    payload: Mapping[str, object],
) -> tuple[tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0
    for field_name, reason_code in _BLOCKING_CHECKS:
        if payload[field_name] is True:
            ready_component_count += 1
        else:
            blocked.append(reason_code)
    return (
        tuple(reason for reason in BLOCKED_REASON_SEQUENCE if reason in blocked),
        ready_component_count,
    )


def _payload_findings(
    payload: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenReadinessRollupInput(
        end_to_end_ready=payload["end_to_end_ready"],  # type: ignore[arg-type]
        system_health_ready=payload["system_health_ready"],  # type: ignore[arg-type]
        validation_matrix_ready=payload["validation_matrix_ready"],  # type: ignore[arg-type]
        node_handoff_ready=payload["node_handoff_ready"],  # type: ignore[arg-type]
        operator_dashboard_ready=payload["operator_dashboard_ready"],  # type: ignore[arg-type]
        operator_runbook_ready=payload["operator_runbook_ready"],  # type: ignore[arg-type]
        release_gate_ready=payload["release_gate_ready"],  # type: ignore[arg-type]
        knowledge_base_index_ready=payload["knowledge_base_index_ready"],  # type: ignore[arg-type]
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    return _rollup_findings(source)


def _validate_payload_attention_reason_codes(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> None:
    if blocked_reason_codes:
        if attention_reason_codes:
            raise ValueError("attention_reason_codes must be empty when blocked")
        return
    if attention_reason_codes == (READY_REASON_CODE,):
        return
    if not attention_reason_codes:
        raise ValueError("attention_reason_codes must describe the rollup state")
    if READY_REASON_CODE in attention_reason_codes:
        raise ValueError("attention_reason_codes must not mix ready and attention codes")


def _validate_report(report: ProbabilityEventScreenReadinessRollupReport) -> None:
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _report_findings(report)
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _rollup_band(blocked_reason_codes, attention_reason_codes)
    if report.rollup_band != expected_band:
        raise ValueError("rollup_band must match reason codes")
    if report.readiness_rollup_ready is not (expected_band == "ready"):
        raise ValueError("readiness_rollup_ready must match rollup_band")
    if report.ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")


def _report_findings(
    report: ProbabilityEventScreenReadinessRollupReport,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenReadinessRollupInput(
        end_to_end_ready=report.end_to_end_ready,
        system_health_ready=report.system_health_ready,
        validation_matrix_ready=report.validation_matrix_ready,
        node_handoff_ready=report.node_handoff_ready,
        operator_dashboard_ready=report.operator_dashboard_ready,
        operator_runbook_ready=report.operator_runbook_ready,
        release_gate_ready=report.release_gate_ready,
        knowledge_base_index_ready=report.knowledge_base_index_ready,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    return _rollup_findings(source)


def _rollup_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes != (READY_REASON_CODE,):
        return "attention"
    return "ready"


def _normalize_member(field_name: str, value: object) -> str:
    if type(value) is not str or value not in READINESS_ROLLUP_BANDS:
        raise ValueError(f"{field_name} must be a supported readiness rollup band")
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
