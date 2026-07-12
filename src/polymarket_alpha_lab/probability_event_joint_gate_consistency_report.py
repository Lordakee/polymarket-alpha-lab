"""Pure in-memory probability event joint gate consistency report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_PROBABILITY_EVENT_JOINT_GATE_CONSISTENCY_CONFIG_VERSION",
    "ProbabilityEventJointGateConsistencyConfig",
    "ProbabilityEventJointGateConsistencyInput",
    "ProbabilityEventJointGateConsistencyReport",
    "ProbabilityEventJointGateConsistencyRow",
    "build_probability_event_joint_gate_consistency_report",
    "probability_event_joint_gate_consistency_report_payload",
)


DEFAULT_PROBABILITY_EVENT_JOINT_GATE_CONSISTENCY_CONFIG_VERSION = (
    "probability-event-joint-gate-consistency-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

SOURCE_QUALITY_STATUSES = ("pass", "watch", "blocked")
MEMORY_POLICY_STATUSES = ("allow", "throttle", "block")
COST_GATE_STATUSES = ("pass", "watch", "blocked")
TEAM_ROUTE_STATUSES = ("pass", "watch", "block")
JOINT_STATUSES = ("pass", "watch", "blocked")

GATE_FIELDS = (
    "source_quality_status",
    "memory_policy_status",
    "cost_gate_status",
    "team_route_status",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_probability_event_joint_gate_inputs"
REASON_PASS = "joint_gate_consistency_pass"
REASON_HAS_BLOCKED = "joint_gate_has_blocked_inputs"
REASON_HAS_WATCH = "joint_gate_has_watch_inputs"
REASON_WATCH_MANUAL = "watch_status_requires_manual_review"

BLOCK_REASON_BY_GATE = {
    "source_quality_status": "source_quality_status_blocked",
    "memory_policy_status": "memory_policy_status_blocked",
    "cost_gate_status": "cost_gate_status_blocked",
    "team_route_status": "team_route_status_blocked",
}
WATCH_REASON_BY_GATE = {
    "source_quality_status": "source_quality_status_watch",
    "memory_policy_status": "memory_policy_status_watch",
    "cost_gate_status": "cost_gate_status_watch",
    "team_route_status": "team_route_status_watch",
}
REASON_CODES = frozenset(
    (
        REASON_MISSING_INPUTS,
        REASON_PASS,
        REASON_HAS_BLOCKED,
        REASON_HAS_WATCH,
        REASON_WATCH_MANUAL,
        *BLOCK_REASON_BY_GATE.values(),
        *WATCH_REASON_BY_GATE.values(),
    ),
)

MANUAL_STEP_EMPTY = "manual_collect_joint_gate_inputs"
MANUAL_STEP_PASS = "continue_report_only_probability_event_review"
MANUAL_STEP_WATCH = "manual_review_watch_gate_before_edge_use"
MANUAL_STEP_BLOCKED = "manual_review_blocked_gate_before_edge_use"


class ProbabilityEventJointGateConsistencyPayload(dict[str, object]):
    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


class _FrozenList(tuple[object, ...]):
    def append(self, value: object) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Iterable[object]) -> None:
        raise TypeError("payload is immutable")

    def insert(self, index: int, value: object) -> None:
        raise TypeError("payload is immutable")

    def remove(self, value: object) -> None:
        raise TypeError("payload is immutable")

    def pop(self, index: int = -1) -> object:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def reverse(self) -> None:
        raise TypeError("payload is immutable")


@dataclass(frozen=True)
class ProbabilityEventJointGateConsistencyConfig:
    config_version: str = DEFAULT_PROBABILITY_EVENT_JOINT_GATE_CONSISTENCY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventJointGateConsistencyConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventJointGateConsistencyConfig, "config")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PROBABILITY_EVENT_JOINT_GATE_CONSISTENCY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_phase_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventJointGateConsistencyInput:
    event_ref: str
    source_quality_status: str
    memory_policy_status: str
    cost_gate_status: str
    team_route_status: str
    probability_edge: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventJointGateConsistencyInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventJointGateConsistencyInput, "input")
        object.__setattr__(self, "event_ref", _require_event_ref(self.event_ref))
        object.__setattr__(
            self,
            "source_quality_status",
            _require_member(
                "source_quality_status",
                self.source_quality_status,
                SOURCE_QUALITY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "memory_policy_status",
            _require_member(
                "memory_policy_status",
                self.memory_policy_status,
                MEMORY_POLICY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "cost_gate_status",
            _require_member("cost_gate_status", self.cost_gate_status, COST_GATE_STATUSES),
        )
        object.__setattr__(
            self,
            "team_route_status",
            _require_member(
                "team_route_status",
                self.team_route_status,
                TEAM_ROUTE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "probability_edge",
            _require_ratio_decimal("probability_edge", self.probability_edge),
        )
        _require_phase_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventJointGateConsistencyRow:
    event_ref: str
    event_ref_digest: str
    source_quality_status: str
    memory_policy_status: str
    cost_gate_status: str
    team_route_status: str
    probability_edge: Decimal
    joint_status: str
    inconsistent_gates: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventJointGateConsistencyRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventJointGateConsistencyRow, "row")
        object.__setattr__(self, "event_ref", _require_event_ref(self.event_ref))
        _require_sha256("event_ref_digest", self.event_ref_digest)
        if self.event_ref_digest != _digest_text(self.event_ref):
            raise ValueError("event_ref_digest must match event_ref")
        object.__setattr__(
            self,
            "source_quality_status",
            _require_member(
                "source_quality_status",
                self.source_quality_status,
                SOURCE_QUALITY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "memory_policy_status",
            _require_member(
                "memory_policy_status",
                self.memory_policy_status,
                MEMORY_POLICY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "cost_gate_status",
            _require_member("cost_gate_status", self.cost_gate_status, COST_GATE_STATUSES),
        )
        object.__setattr__(
            self,
            "team_route_status",
            _require_member(
                "team_route_status",
                self.team_route_status,
                TEAM_ROUTE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "probability_edge",
            _require_ratio_decimal("probability_edge", self.probability_edge),
        )
        object.__setattr__(
            self,
            "joint_status",
            _require_member("joint_status", self.joint_status, JOINT_STATUSES),
        )
        object.__setattr__(
            self,
            "inconsistent_gates",
            _normalize_gate_names("inconsistent_gates", self.inconsistent_gates),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_phase_flags("row", self)
        expected_status = _row_joint_status(self)
        expected_gates = _row_inconsistent_gates(self)
        expected_reasons = _row_reason_codes(self)
        if self.joint_status != expected_status:
            raise ValueError("joint_status must match gate statuses")
        if self.inconsistent_gates != expected_gates:
            raise ValueError("inconsistent_gates must match gate statuses")
        if self.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match gate statuses")
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _digest_for_dataclass(
                self,
                exclude=("derived_validation_digest",),
            ):
                raise ValueError("derived_validation_digest must match row payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_for_dataclass(self, exclude=("derived_validation_digest",)),
            )


@dataclass(frozen=True)
class ProbabilityEventJointGateConsistencyReport:
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    inconsistent_input_count: Decimal
    max_probability_edge: Decimal
    joint_status: str
    inconsistent_gates: tuple[str, ...]
    reason_codes: tuple[str, ...]
    manual_next_step: str
    rows: tuple[ProbabilityEventJointGateConsistencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventJointGateConsistencyReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventJointGateConsistencyReport, "report")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_PROBABILITY_EVENT_JOINT_GATE_CONSISTENCY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "inconsistent_input_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_probability_edge",
            _require_ratio_decimal("max_probability_edge", self.max_probability_edge),
        )
        object.__setattr__(
            self,
            "joint_status",
            _require_member("joint_status", self.joint_status, JOINT_STATUSES),
        )
        object.__setattr__(
            self,
            "inconsistent_gates",
            _normalize_gate_names("inconsistent_gates", self.inconsistent_gates),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_member(
                "manual_next_step",
                self.manual_next_step,
                (MANUAL_STEP_EMPTY, MANUAL_STEP_PASS, MANUAL_STEP_WATCH, MANUAL_STEP_BLOCKED),
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_phase_flags("report", self)

        expected = _report_expected_values(self.rows)
        for field_name, expected_value in expected.items():
            if getattr(self, field_name) != expected_value:
                raise ValueError(f"{field_name} must match rows")
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _digest_for_dataclass(
                self,
                exclude=("derived_validation_digest",),
            ):
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_for_dataclass(self, exclude=("derived_validation_digest",)),
            )


def build_probability_event_joint_gate_consistency_report(
    inputs: Iterable[object],
    *,
    config: object | None = None,
) -> ProbabilityEventJointGateConsistencyReport:
    cfg = ProbabilityEventJointGateConsistencyConfig() if config is None else config
    _require_exact_type(cfg, ProbabilityEventJointGateConsistencyConfig, "config")
    rows = tuple(_row_from_input(item) for item in inputs)
    rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.joint_status],
                row.event_ref,
                row.event_ref_digest,
            ),
        ),
    )
    expected = _report_expected_values(rows)
    return ProbabilityEventJointGateConsistencyReport(
        config_version=cfg.config_version,
        input_count=expected["input_count"],
        pass_count=expected["pass_count"],
        watch_count=expected["watch_count"],
        blocked_count=expected["blocked_count"],
        inconsistent_input_count=expected["inconsistent_input_count"],
        max_probability_edge=expected["max_probability_edge"],
        joint_status=expected["joint_status"],
        inconsistent_gates=expected["inconsistent_gates"],
        reason_codes=expected["reason_codes"],
        manual_next_step=expected["manual_next_step"],
        rows=rows,
        paper_only=cfg.paper_only,
        report_only=cfg.report_only,
        readonly=cfg.readonly,
    )


def probability_event_joint_gate_consistency_report_payload(
    report: ProbabilityEventJointGateConsistencyReport,
) -> ProbabilityEventJointGateConsistencyPayload:
    _require_exact_type(report, ProbabilityEventJointGateConsistencyReport, "report")
    return _freeze_mapping(
        {
            "config_version": report.config_version,
            "input_count": report.input_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "blocked_count": report.blocked_count,
            "inconsistent_input_count": report.inconsistent_input_count,
            "max_probability_edge": report.max_probability_edge,
            "joint_status": report.joint_status,
            "inconsistent_gates": report.inconsistent_gates,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "rows": tuple(_row_payload(row) for row in report.rows),
            "derived_validation_digest": report.derived_validation_digest,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _row_from_input(
    item: object,
) -> ProbabilityEventJointGateConsistencyRow:
    _require_exact_type(item, ProbabilityEventJointGateConsistencyInput, "input")
    gates = _input_gate_statuses(item)
    joint_status = _status_from_gates(gates)
    inconsistent_gates = _inconsistent_gates_from_statuses(gates)
    reason_codes = _reason_codes_for_gates(gates)
    return ProbabilityEventJointGateConsistencyRow(
        event_ref=item.event_ref,
        event_ref_digest=_digest_text(item.event_ref),
        source_quality_status=item.source_quality_status,
        memory_policy_status=item.memory_policy_status,
        cost_gate_status=item.cost_gate_status,
        team_route_status=item.team_route_status,
        probability_edge=item.probability_edge,
        joint_status=joint_status,
        inconsistent_gates=inconsistent_gates,
        reason_codes=reason_codes,
        paper_only=item.paper_only,
        report_only=item.report_only,
        readonly=item.readonly,
    )


def _row_payload(row: ProbabilityEventJointGateConsistencyRow) -> dict[str, object]:
    return {
        "event_ref_digest": row.event_ref_digest,
        "source_quality_status": row.source_quality_status,
        "memory_policy_status": row.memory_policy_status,
        "cost_gate_status": row.cost_gate_status,
        "team_route_status": row.team_route_status,
        "probability_edge": row.probability_edge,
        "joint_status": row.joint_status,
        "inconsistent_gates": row.inconsistent_gates,
        "reason_codes": row.reason_codes,
        "derived_validation_digest": row.derived_validation_digest,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _input_gate_statuses(
    item: ProbabilityEventJointGateConsistencyInput,
) -> dict[str, str]:
    return {
        "source_quality_status": item.source_quality_status,
        "memory_policy_status": item.memory_policy_status,
        "cost_gate_status": item.cost_gate_status,
        "team_route_status": item.team_route_status,
    }


def _row_gate_statuses(row: ProbabilityEventJointGateConsistencyRow) -> dict[str, str]:
    return {
        "source_quality_status": row.source_quality_status,
        "memory_policy_status": row.memory_policy_status,
        "cost_gate_status": row.cost_gate_status,
        "team_route_status": row.team_route_status,
    }


def _row_joint_status(row: ProbabilityEventJointGateConsistencyRow) -> str:
    return _status_from_gates(_row_gate_statuses(row))


def _row_inconsistent_gates(
    row: ProbabilityEventJointGateConsistencyRow,
) -> tuple[str, ...]:
    return _inconsistent_gates_from_statuses(_row_gate_statuses(row))


def _row_reason_codes(row: ProbabilityEventJointGateConsistencyRow) -> tuple[str, ...]:
    return _reason_codes_for_gates(_row_gate_statuses(row))


def _status_from_gates(gates: dict[str, str]) -> str:
    if any(_is_blocked_gate(field_name, status) for field_name, status in gates.items()):
        return "blocked"
    if any(_is_watch_gate(field_name, status) for field_name, status in gates.items()):
        return "watch"
    return "pass"


def _inconsistent_gates_from_statuses(gates: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        field_name
        for field_name in GATE_FIELDS
        if _is_blocked_gate(field_name, gates[field_name])
        or _is_watch_gate(field_name, gates[field_name])
    )


def _reason_codes_for_gates(gates: dict[str, str]) -> tuple[str, ...]:
    block_reasons = tuple(
        BLOCK_REASON_BY_GATE[field_name]
        for field_name in GATE_FIELDS
        if _is_blocked_gate(field_name, gates[field_name])
    )
    watch_reasons = tuple(
        WATCH_REASON_BY_GATE[field_name]
        for field_name in GATE_FIELDS
        if _is_watch_gate(field_name, gates[field_name])
    )
    if block_reasons:
        return block_reasons
    if watch_reasons:
        return (REASON_WATCH_MANUAL, *watch_reasons)
    return (REASON_PASS,)


def _is_blocked_gate(field_name: str, status: str) -> bool:
    if field_name == "memory_policy_status":
        return status == "block"
    if field_name == "team_route_status":
        return status == "block"
    return status == "blocked"


def _is_watch_gate(field_name: str, status: str) -> bool:
    if field_name == "memory_policy_status":
        return status == "throttle"
    return status == "watch"


def _report_expected_values(
    rows: tuple[ProbabilityEventJointGateConsistencyRow, ...],
) -> dict[str, object]:
    input_count = _decimal_count(len(rows))
    pass_count = _decimal_count(sum(1 for row in rows if row.joint_status == "pass"))
    watch_count = _decimal_count(sum(1 for row in rows if row.joint_status == "watch"))
    blocked_count = _decimal_count(
        sum(1 for row in rows if row.joint_status == "blocked"),
    )
    inconsistent_input_count = _decimal_count(
        sum(1 for row in rows if row.inconsistent_gates),
    )
    max_probability_edge = max((row.probability_edge for row in rows), default=ZERO)
    joint_status = _report_joint_status(rows)
    reason_codes = _report_reason_codes(rows, joint_status)
    return {
        "input_count": input_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "blocked_count": blocked_count,
        "inconsistent_input_count": inconsistent_input_count,
        "max_probability_edge": max_probability_edge,
        "joint_status": joint_status,
        "inconsistent_gates": _report_inconsistent_gates(rows),
        "reason_codes": reason_codes,
        "manual_next_step": _manual_next_step(joint_status, rows),
    }


def _report_joint_status(
    rows: tuple[ProbabilityEventJointGateConsistencyRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.joint_status == "blocked" for row in rows):
        return "blocked"
    if any(row.joint_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_inconsistent_gates(
    rows: tuple[ProbabilityEventJointGateConsistencyRow, ...],
) -> tuple[str, ...]:
    present = {gate for row in rows for gate in row.inconsistent_gates}
    return tuple(gate for gate in GATE_FIELDS if gate in present)


def _report_reason_codes(
    rows: tuple[ProbabilityEventJointGateConsistencyRow, ...],
    joint_status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    if joint_status == "pass":
        return (REASON_PASS,)
    row_reasons = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != REASON_PASS
    }
    if joint_status == "blocked":
        row_reasons.discard(REASON_WATCH_MANUAL)
        return (REASON_HAS_BLOCKED, *tuple(sorted(row_reasons)))
    row_reasons.discard(REASON_WATCH_MANUAL)
    return (REASON_HAS_WATCH, REASON_WATCH_MANUAL, *tuple(sorted(row_reasons)))


def _manual_next_step(
    joint_status: str,
    rows: tuple[ProbabilityEventJointGateConsistencyRow, ...],
) -> str:
    if not rows:
        return MANUAL_STEP_EMPTY
    if joint_status == "blocked":
        return MANUAL_STEP_BLOCKED
    if joint_status == "watch":
        return MANUAL_STEP_WATCH
    return MANUAL_STEP_PASS


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _require_event_ref(value: object) -> str:
    return _require_public_text("event_ref", value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_phase_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        field_value = getattr(value, field_name)
        if type(field_value) is not bool:
            raise ValueError(f"{field_name} must be bool")
        if field_value is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit six decimal places") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be at least 0.000000")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be at least 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_gate_names(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_member(field_name, value, GATE_FIELDS) for value in values)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    expected = tuple(gate for gate in GATE_FIELDS if gate in set(normalized))
    if normalized != expected:
        raise ValueError(f"{field_name} must use canonical sequence")
    return normalized


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} values must be strings")
        if value not in REASON_CODES:
            raise ValueError(f"{field_name} contains unsupported reason code")
        normalized.append(value)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ProbabilityEventJointGateConsistencyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ProbabilityEventJointGateConsistencyRow, "row")
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.joint_status],
                row.event_ref,
                row.event_ref_digest,
            ),
        ),
    )
    if rows != expected:
        raise ValueError("rows must use canonical sequence")
    return rows


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _digest_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _digest_for_dataclass(value: object, *, exclude: tuple[str, ...]) -> str:
    return sha256(
        json.dumps(
            _plain_value(value, exclude=exclude),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _plain_value(value: object, *, exclude: tuple[str, ...] = ()) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is bool or value is None or type(value) is str:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _plain_value(getattr(value, field.name), exclude=())
            for field in fields(value)
            if field.name not in exclude
        }
    if type(value) is tuple:
        return [_plain_value(item, exclude=()) for item in value]
    if type(value) is dict:
        return {
            str(key): _plain_value(item, exclude=())
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _freeze_mapping(
    value: dict[str, object],
) -> ProbabilityEventJointGateConsistencyPayload:
    return ProbabilityEventJointGateConsistencyPayload(
        {key: _freeze_value(item) for key, item in value.items()},
    )


def _freeze_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is tuple:
        return _FrozenList(_freeze_value(item) for item in value)
    if type(value) is dict:
        return ProbabilityEventJointGateConsistencyPayload(
            {key: _freeze_value(item) for key, item in value.items()},
        )
    raise ValueError(f"unsupported payload value {type(value).__name__}")
