"""Readonly trace report for probability event research packet gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from hashlib import sha256
from json import dumps
from typing import Any, Mapping

from .team_paper_guard import require_paper_only_flags


PROBABILITY_EVENT_RESEARCH_PACKET_GATE_TRACE_REPORT_VERSION = (
    "probability-event-research-packet-gate-trace-report-v0"
)

GATE_NAMES = (
    "probability_screen",
    "source_quality",
    "memory_policy",
    "cost_gate",
    "operator_packet",
)
STATUSES = ("pass", "watch", "blocked")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
GATE_COUNT = Decimal("5")
UNSAFE_TEXT_TERMS = (
    "auth",
    "account",
    "wallet",
    "private_key",
    "key",
    "order",
    "live",
    "execution",
    "submit",
    "cancel",
    "place",
    "sign",
)


@dataclass(frozen=True)
class ProbabilityEventResearchPacketGateTraceStep:
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventResearchPacketGateTraceStep,
            "trace step",
        )
        object.__setattr__(
            self,
            "gate_status",
            _require_status("gate_status", self.gate_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("trace step", self)


@dataclass(frozen=True)
class ProbabilityEventResearchPacketGateTraceInput:
    event_ref: str
    probability_screen: ProbabilityEventResearchPacketGateTraceStep
    source_quality: ProbabilityEventResearchPacketGateTraceStep
    memory_policy: ProbabilityEventResearchPacketGateTraceStep
    cost_gate: ProbabilityEventResearchPacketGateTraceStep
    operator_packet: ProbabilityEventResearchPacketGateTraceStep
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventResearchPacketGateTraceInput,
            "trace input",
        )
        object.__setattr__(self, "event_ref", _require_public_label("event_ref", self.event_ref))
        for gate_name in GATE_NAMES:
            step = getattr(self, gate_name)
            if type(step) is not ProbabilityEventResearchPacketGateTraceStep:
                raise ValueError(f"{gate_name} must be a ProbabilityEventResearchPacketGateTraceStep")
            require_paper_only_flags(gate_name, step)
        require_paper_only_flags("trace input", self)


@dataclass(frozen=True)
class ProbabilityEventResearchPacketGateTraceRow:
    gate_name: str
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventResearchPacketGateTraceRow,
            "trace row",
        )
        object.__setattr__(
            self,
            "gate_name",
            _require_gate_name("gate_name", self.gate_name),
        )
        object.__setattr__(
            self,
            "gate_status",
            _require_status("gate_status", self.gate_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("trace row", self)


@dataclass(frozen=True)
class ProbabilityEventResearchPacketGateTraceReport:
    config_version: str
    event_ref: str
    trace_status: str
    blocking_gate: str
    watch_gates: tuple[str, ...]
    manual_next_step: str
    gate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    trace_rows: tuple[ProbabilityEventResearchPacketGateTraceRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventResearchPacketGateTraceReport,
            "trace report",
        )
        if type(self.config_version) is not str:
            raise ValueError("config_version must be a string")
        if (
            self.config_version
            != PROBABILITY_EVENT_RESEARCH_PACKET_GATE_TRACE_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(self, "event_ref", _require_public_label("event_ref", self.event_ref))
        object.__setattr__(
            self,
            "trace_status",
            _require_status("trace_status", self.trace_status),
        )
        if self.blocking_gate == "":
            object.__setattr__(self, "blocking_gate", "")
        else:
            object.__setattr__(
                self,
                "blocking_gate",
                _require_gate_name("blocking_gate", self.blocking_gate),
            )
        object.__setattr__(
            self,
            "watch_gates",
            _normalize_gate_names("watch_gates", self.watch_gates),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_public_label("manual_next_step", self.manual_next_step),
        )
        for field_name in (
            "gate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "trace_rows", _normalize_rows(self.trace_rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("trace report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_probability_event_research_packet_gate_trace_report(
    source_input: ProbabilityEventResearchPacketGateTraceInput,
) -> ProbabilityEventResearchPacketGateTraceReport:
    if type(source_input) is not ProbabilityEventResearchPacketGateTraceInput:
        raise ValueError(
            "source_input must be a ProbabilityEventResearchPacketGateTraceInput",
        )
    require_paper_only_flags("source input", source_input)
    rows = tuple(
        ProbabilityEventResearchPacketGateTraceRow(
            gate_name=gate_name,
            gate_status=getattr(source_input, gate_name).gate_status,
            reason_codes=getattr(source_input, gate_name).reason_codes,
        )
        for gate_name in GATE_NAMES
    )
    trace_status = _trace_status(rows)
    blocking_gate = next(
        (row.gate_name for row in rows if row.gate_status == "blocked"),
        "",
    )
    watch_gates = tuple(row.gate_name for row in rows if row.gate_status == "watch")
    return ProbabilityEventResearchPacketGateTraceReport(
        config_version=PROBABILITY_EVENT_RESEARCH_PACKET_GATE_TRACE_REPORT_VERSION,
        event_ref=source_input.event_ref,
        trace_status=trace_status,
        blocking_gate=blocking_gate,
        watch_gates=watch_gates,
        manual_next_step=_manual_next_step(trace_status),
        gate_count=GATE_COUNT,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        trace_rows=rows,
        reason_codes=_report_reason_codes(trace_status, rows),
    )


def probability_event_research_packet_gate_trace_report_payload(
    report: ProbabilityEventResearchPacketGateTraceReport | Mapping[str, object],
) -> Mapping[str, object]:
    if type(report) is not ProbabilityEventResearchPacketGateTraceReport:
        _validate_payload_digest(report)
        report = _report_from_payload(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return _ImmutablePayload(payload)


def _report_from_payload(
    payload: ProbabilityEventResearchPacketGateTraceReport | Mapping[str, object],
) -> ProbabilityEventResearchPacketGateTraceReport:
    if not isinstance(payload, Mapping):
        raise ValueError("report must be a trace report or payload mapping")
    rows_value = payload.get("trace_rows")
    if type(rows_value) is not list:
        raise ValueError("trace_rows must be a list")
    rows = tuple(
        ProbabilityEventResearchPacketGateTraceRow(
            gate_name=_require_payload_string("gate_name", row, index),
            gate_status=_require_payload_string("gate_status", row, index),
            reason_codes=_require_payload_string_list("reason_codes", row, index),
            paper_only=_require_payload_bool("paper_only", row, index),
            report_only=_require_payload_bool("report_only", row, index),
            readonly=_require_payload_bool("readonly", row, index),
        )
        for index, row in enumerate(rows_value)
    )
    return ProbabilityEventResearchPacketGateTraceReport(
        config_version=_require_payload_top_string(payload, "config_version"),
        event_ref=_require_payload_top_string(payload, "event_ref"),
        trace_status=_require_payload_top_string(payload, "trace_status"),
        blocking_gate=_require_payload_top_string(payload, "blocking_gate"),
        watch_gates=tuple(_require_payload_top_list(payload, "watch_gates")),
        manual_next_step=_require_payload_top_string(payload, "manual_next_step"),
        gate_count=_require_payload_decimal(payload, "gate_count"),
        pass_count=_require_payload_decimal(payload, "pass_count"),
        watch_count=_require_payload_decimal(payload, "watch_count"),
        blocked_count=_require_payload_decimal(payload, "blocked_count"),
        trace_rows=rows,
        reason_codes=tuple(_require_payload_top_list(payload, "reason_codes")),
        derived_validation_digest=_require_payload_top_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=_require_payload_top_bool(payload, "paper_only"),
        report_only=_require_payload_top_bool(payload, "report_only"),
        readonly=_require_payload_top_bool(payload, "readonly"),
    )


def _trace_status(
    rows: tuple[ProbabilityEventResearchPacketGateTraceRow, ...],
) -> str:
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_next_step(trace_status: str) -> str:
    if trace_status == "blocked":
        return "manual_review_blocking_gate_before_packet_use"
    if trace_status == "watch":
        return "manual_review_watch_gates_before_packet_use"
    return "manual_read_research_packet_gate_trace"


def _status_count(
    rows: tuple[ProbabilityEventResearchPacketGateTraceRow, ...],
    status: str,
) -> Decimal:
    total = ZERO_COUNT
    for row in rows:
        if row.gate_status == status:
            total += ONE_COUNT
    return total


def _report_reason_codes(
    trace_status: str,
    rows: tuple[ProbabilityEventResearchPacketGateTraceRow, ...],
) -> tuple[str, ...]:
    codes: list[str] = [f"research_packet_gate_trace_{trace_status}"]
    if trace_status != "pass":
        for row in rows:
            if row.gate_status in ("blocked", "watch"):
                codes.append(f"{row.gate_name}_{row.gate_status}")
    for row in rows:
        codes.extend(row.reason_codes)
    return _dedupe(codes)


def _validate_report_consistency(
    report: ProbabilityEventResearchPacketGateTraceReport,
) -> None:
    if tuple(row.gate_name for row in report.trace_rows) != GATE_NAMES:
        raise ValueError("trace_rows must match canonical gate order")
    if report.gate_count != GATE_COUNT:
        raise ValueError("gate_count must equal canonical trace gate count")
    pass_count = _status_count(report.trace_rows, "pass")
    watch_count = _status_count(report.trace_rows, "watch")
    blocked_count = _status_count(report.trace_rows, "blocked")
    if report.pass_count != pass_count:
        raise ValueError("pass_count does not match trace rows")
    if report.watch_count != watch_count:
        raise ValueError("watch_count does not match trace rows")
    if report.blocked_count != blocked_count:
        raise ValueError("blocked_count does not match trace rows")
    expected_status = _trace_status(report.trace_rows)
    if report.trace_status != expected_status:
        raise ValueError("trace_status does not match trace rows")
    expected_blocking_gate = next(
        (row.gate_name for row in report.trace_rows if row.gate_status == "blocked"),
        "",
    )
    if report.blocking_gate != expected_blocking_gate:
        raise ValueError("blocking_gate does not match trace rows")
    expected_watch_gates = tuple(
        row.gate_name for row in report.trace_rows if row.gate_status == "watch"
    )
    if report.watch_gates != expected_watch_gates:
        raise ValueError("watch_gates do not match trace rows")
    if report.manual_next_step != _manual_next_step(report.trace_status):
        raise ValueError("manual_next_step does not match trace_status")
    if report.reason_codes != _report_reason_codes(report.trace_status, report.trace_rows):
        raise ValueError("reason_codes do not match trace rows")


def _report_digest(report: ProbabilityEventResearchPacketGateTraceReport) -> str:
    payload = asdict(report)
    payload["derived_validation_digest"] = ""
    canonical = _json_ready(payload)
    return sha256(
        dumps(canonical, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()


def _validate_payload_digest(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("report must be a trace report or payload mapping")
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    canonical = dict(payload)
    canonical["derived_validation_digest"] = ""
    expected_digest = sha256(
        dumps(
            _json_ready(canonical),
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    ).hexdigest()
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value


def _normalize_rows(
    rows: object,
) -> tuple[ProbabilityEventResearchPacketGateTraceRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("trace_rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ProbabilityEventResearchPacketGateTraceRow:
            raise ValueError("trace_rows must contain trace rows")
        require_paper_only_flags("trace row", row)
    return normalized


def _normalize_gate_names(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(_require_gate_name(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return normalized


def _dedupe(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return tuple(deduped)


def _require_payload_string(field_name: str, value: object, index: int) -> str:
    if type(value) is not dict:
        raise ValueError("trace_rows must contain dict payloads")
    item = value.get(field_name)
    if type(item) is not str:
        raise ValueError(f"trace_rows[{index}].{field_name} must be a string")
    return item


def _require_payload_string_list(
    field_name: str,
    value: object,
    index: int,
) -> tuple[str, ...]:
    if type(value) is not dict:
        raise ValueError("trace_rows must contain dict payloads")
    item = value.get(field_name)
    if type(item) is not list:
        raise ValueError(f"trace_rows[{index}].{field_name} must be a list")
    if not all(type(child) is str for child in item):
        raise ValueError(f"trace_rows[{index}].{field_name} must contain strings")
    return tuple(item)


def _require_payload_bool(field_name: str, value: object, index: int) -> bool:
    if type(value) is not dict:
        raise ValueError("trace_rows must contain dict payloads")
    item = value.get(field_name)
    if type(item) is not bool:
        raise ValueError(f"trace_rows[{index}].{field_name} must be a bool")
    return item


def _require_payload_top_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_payload_top_list(
    payload: Mapping[str, object],
    field_name: str,
) -> list[str]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not all(type(item) is str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return value


def _require_payload_top_bool(payload: Mapping[str, object], field_name: str) -> bool:
    value = payload.get(field_name)
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_payload_decimal(payload: Mapping[str, object], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    return _require_count_decimal(field_name, Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    if normalized != value:
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    _reject_unsafe_text(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    _reject_unsafe_text(field_name, value)
    return value


def _require_gate_name(field_name: str, value: object) -> str:
    if type(value) is not str or value not in GATE_NAMES:
        raise ValueError(f"{field_name} must be a known gate name")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, blocked")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return value


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_TEXT_TERMS):
        raise ValueError(f"{field_name} contains unsupported live surface term")


class _ImmutablePayload(dict[str, object]):
    def __setitem__(self, key: str, value: object) -> None:
        raise TypeError("public_payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("public_payload is immutable")

    def clear(self) -> None:
        raise TypeError("public_payload is immutable")

    def pop(self, key: str, default: object = None) -> object:
        raise TypeError("public_payload is immutable")

    def popitem(self) -> tuple[str, object]:
        raise TypeError("public_payload is immutable")

    def setdefault(self, key: str, default: object = None) -> object:
        raise TypeError("public_payload is immutable")

    def update(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")


__all__ = (
    "PROBABILITY_EVENT_RESEARCH_PACKET_GATE_TRACE_REPORT_VERSION",
    "ProbabilityEventResearchPacketGateTraceInput",
    "ProbabilityEventResearchPacketGateTraceReport",
    "ProbabilityEventResearchPacketGateTraceRow",
    "ProbabilityEventResearchPacketGateTraceStep",
    "build_probability_event_research_packet_gate_trace_report",
    "probability_event_research_packet_gate_trace_report_payload",
)
