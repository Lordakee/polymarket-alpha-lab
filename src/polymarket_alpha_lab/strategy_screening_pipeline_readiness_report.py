"""Pure in-memory strategy screening pipeline readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28

CANONICAL_STAGE_NAMES = (
    "acquisition_ready",
    "research_packet_ready",
    "source_reliability_ready",
    "probability_sanity_ready",
    "cost_gate_ready",
    "team_routing_ready",
    "memory_context_ready",
    "position_sizing_ready",
    "manual_preflight_ready",
    "operator_output_safety_ready",
)
READY_STATUSES = ("blocked", "attention", "ready")
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyScreeningPipelineStageReadiness:
    ready: bool
    reason_codes: tuple[str, ...] = ()
    stage_label: str = "ready source"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.ready) is not bool:
            raise ValueError("ready must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "stage_label",
            _require_canonical_public_string("stage_label", self.stage_label),
        )
        if self.ready is False and not self.reason_codes:
            raise ValueError("blocked stages must provide at least one blocker reason")
        if self.ready is True:
            for reason_code in self.reason_codes:
                if "_attention" not in reason_code:
                    raise ValueError("attention reason codes must contain '_attention'")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyScreeningPipelineStageRow:
    stage_name: str
    ready: bool
    status: str
    reason_codes: tuple[str, ...]
    stage_label: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_known_value("stage_name", self.stage_name, CANONICAL_STAGE_NAMES)
        if type(self.ready) is not bool:
            raise ValueError("ready must be a bool")
        _require_known_value("status", self.status, READY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "stage_label",
            _require_canonical_public_string("stage_label", self.stage_label),
        )
        _validate_stage_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyScreeningPipelineReadinessReport:
    generated_at: datetime
    pipeline_ready: bool
    total_stage_count: Decimal
    ready_stage_count: Decimal
    blocked_stage_count: Decimal
    attention_stage_count: Decimal
    ready_stage_ratio: Decimal
    next_blocked_stage: str | None
    reason_codes: tuple[str, ...]
    stage_rows: tuple[StrategyScreeningPipelineStageRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if type(self.pipeline_ready) is not bool:
            raise ValueError("pipeline_ready must be a bool")
        for field_name in (
            "total_stage_count",
            "ready_stage_count",
            "blocked_stage_count",
            "attention_stage_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_stage_ratio",
            _normalize_ratio("ready_stage_ratio", self.ready_stage_ratio),
        )
        if self.next_blocked_stage is not None:
            _require_known_value(
                "next_blocked_stage",
                self.next_blocked_stage,
                CANONICAL_STAGE_NAMES,
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "stage_rows", _normalize_stage_rows(self.stage_rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        if self.public_digest == "":
            object.__setattr__(
                self,
                "public_digest",
                strategy_screening_pipeline_readiness_digest(self),
            )
        elif not _is_sha256_digest(self.public_digest):
            raise ValueError("public_digest must be a sha256 hex digest")
        elif self.public_digest != strategy_screening_pipeline_readiness_digest(self):
            raise ValueError("public_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return strategy_screening_pipeline_readiness_payload(self)


def build_strategy_screening_pipeline_readiness_report(
    *,
    generated_at: datetime,
    acquisition_ready: StrategyScreeningPipelineStageReadiness | bool,
    research_packet_ready: StrategyScreeningPipelineStageReadiness | bool,
    source_reliability_ready: StrategyScreeningPipelineStageReadiness | bool,
    probability_sanity_ready: StrategyScreeningPipelineStageReadiness | bool,
    cost_gate_ready: StrategyScreeningPipelineStageReadiness | bool,
    team_routing_ready: StrategyScreeningPipelineStageReadiness | bool,
    memory_context_ready: StrategyScreeningPipelineStageReadiness | bool,
    position_sizing_ready: StrategyScreeningPipelineStageReadiness | bool,
    manual_preflight_ready: StrategyScreeningPipelineStageReadiness | bool,
    operator_output_safety_ready: StrategyScreeningPipelineStageReadiness | bool,
) -> StrategyScreeningPipelineReadinessReport:
    generated_at = _as_utc("generated_at", generated_at)
    stage_inputs = {
        "acquisition_ready": acquisition_ready,
        "research_packet_ready": research_packet_ready,
        "source_reliability_ready": source_reliability_ready,
        "probability_sanity_ready": probability_sanity_ready,
        "cost_gate_ready": cost_gate_ready,
        "team_routing_ready": team_routing_ready,
        "memory_context_ready": memory_context_ready,
        "position_sizing_ready": position_sizing_ready,
        "manual_preflight_ready": manual_preflight_ready,
        "operator_output_safety_ready": operator_output_safety_ready,
    }
    rows = tuple(
        _row_from_stage_input(stage_name, stage_inputs[stage_name])
        for stage_name in CANONICAL_STAGE_NAMES
    )
    total_stage_count = _count(len(rows))
    ready_stage_count = _count(sum(1 for row in rows if row.ready))
    blocked_stage_count = _count(sum(1 for row in rows if row.status == "blocked"))
    attention_stage_count = _count(sum(1 for row in rows if row.status == "attention"))
    return StrategyScreeningPipelineReadinessReport(
        generated_at=generated_at,
        pipeline_ready=blocked_stage_count == ZERO and attention_stage_count == ZERO,
        total_stage_count=total_stage_count,
        ready_stage_count=ready_stage_count,
        blocked_stage_count=blocked_stage_count,
        attention_stage_count=attention_stage_count,
        ready_stage_ratio=_ratio(ready_stage_count, total_stage_count),
        next_blocked_stage=_next_blocked_stage(rows),
        reason_codes=_report_reason_codes(rows),
        stage_rows=rows,
    )


def strategy_screening_pipeline_readiness_payload(
    report: StrategyScreeningPipelineReadinessReport,
) -> dict[str, Any]:
    if type(report) is not StrategyScreeningPipelineReadinessReport:
        raise ValueError("report must be a StrategyScreeningPipelineReadinessReport")
    _require_hard_flags(report)
    payload = _json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def strategy_screening_pipeline_readiness_digest(
    report: StrategyScreeningPipelineReadinessReport,
) -> str:
    if type(report) is not StrategyScreeningPipelineReadinessReport:
        raise ValueError("report must be a StrategyScreeningPipelineReadinessReport")
    payload = _json_ready_no_floats(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _row_from_stage_input(
    stage_name: str,
    value: StrategyScreeningPipelineStageReadiness | bool,
) -> StrategyScreeningPipelineStageRow:
    if type(value) is bool:
        stage = StrategyScreeningPipelineStageReadiness(
            ready=value,
            reason_codes=() if value else (f"{stage_name}_blocked",),
            stage_label=_stage_label(stage_name),
        )
    elif type(value) is StrategyScreeningPipelineStageReadiness:
        stage = value
    else:
        raise ValueError(
            "readiness input must be a bool or StrategyScreeningPipelineStageReadiness",
        )
    status = _stage_status(stage)
    reason_codes = stage.reason_codes or (stage_name,)
    return StrategyScreeningPipelineStageRow(
        stage_name=stage_name,
        ready=stage.ready,
        status=status,
        reason_codes=reason_codes,
        stage_label=stage.stage_label,
    )


def _stage_status(stage: StrategyScreeningPipelineStageReadiness) -> str:
    if not stage.ready:
        return "blocked"
    if stage.reason_codes:
        return "attention"
    return "ready"


def _stage_label(stage_name: str) -> str:
    return stage_name.removesuffix("_ready").replace("_", " ")


def _next_blocked_stage(rows: tuple[StrategyScreeningPipelineStageRow, ...]) -> str | None:
    for row in rows:
        if row.status == "blocked":
            return row.stage_name
    return None


def _report_reason_codes(rows: tuple[StrategyScreeningPipelineStageRow, ...]) -> tuple[str, ...]:
    reasons: set[str] = set()
    non_ready_rows = tuple(row for row in rows if row.status != "ready")
    source_rows = non_ready_rows or rows
    for row in source_rows:
        reasons.update(row.reason_codes)
    return tuple(sorted(reasons))


def _validate_stage_row_consistency(row: StrategyScreeningPipelineStageRow) -> None:
    if row.status == "blocked" and row.ready is not False:
        raise ValueError("blocked stage rows must not be ready")
    if row.status == "attention" and row.ready is not True:
        raise ValueError("attention stage rows must be ready")
    if row.status == "ready" and row.ready is not True:
        raise ValueError("ready stage rows must be ready")
    if row.status == "ready" and row.reason_codes != (row.stage_name,):
        raise ValueError("ready stage reason_codes must contain only the stage ready code")
    if row.status == "blocked" and not row.reason_codes:
        raise ValueError("blocked stage rows must provide reason_codes")
    if row.status == "attention" and not row.reason_codes:
        raise ValueError("attention stage rows must provide reason_codes")


def _validate_report_consistency(report: StrategyScreeningPipelineReadinessReport) -> None:
    if tuple(row.stage_name for row in report.stage_rows) != CANONICAL_STAGE_NAMES:
        raise ValueError("stage_rows must match canonical stage order")
    total_stage_count = _count(len(report.stage_rows))
    ready_stage_count = _count(sum(1 for row in report.stage_rows if row.ready))
    blocked_stage_count = _count(sum(1 for row in report.stage_rows if row.status == "blocked"))
    attention_stage_count = _count(
        sum(1 for row in report.stage_rows if row.status == "attention"),
    )
    if report.total_stage_count != total_stage_count:
        raise ValueError("total_stage_count must match stage_rows")
    if report.ready_stage_count != ready_stage_count:
        raise ValueError("ready_stage_count must match stage_rows")
    if report.blocked_stage_count != blocked_stage_count:
        raise ValueError("blocked_stage_count must match stage_rows")
    if report.attention_stage_count != attention_stage_count:
        raise ValueError("attention_stage_count must match stage_rows")
    if report.ready_stage_ratio != _ratio(ready_stage_count, total_stage_count):
        raise ValueError("ready_stage_ratio must match stage_rows")
    if report.pipeline_ready is not (
        blocked_stage_count == ZERO and attention_stage_count == ZERO
    ):
        raise ValueError("pipeline_ready must match stage_rows")
    if report.next_blocked_stage != _next_blocked_stage(report.stage_rows):
        raise ValueError("next_blocked_stage must match stage_rows")
    if report.reason_codes != _report_reason_codes(report.stage_rows):
        raise ValueError("reason_codes must match stage_rows")


def _normalize_stage_rows(
    rows: tuple[StrategyScreeningPipelineStageRow, ...],
) -> tuple[StrategyScreeningPipelineStageRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("stage_rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyScreeningPipelineStageRow:
            raise ValueError("stage_rows must contain StrategyScreeningPipelineStageRow values")
    return rows


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_require_reason_code(value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized))


def _require_reason_code(value: str) -> str:
    if type(value) is not str or not value:
        raise ValueError("reason code must be a non-empty canonical string")
    if value.strip() != value or not value.replace("_", "").isalnum() or value.lower() != value:
        raise ValueError("reason code must be a non-empty canonical string")
    return value


def _require_canonical_public_string(field_name: str, value: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    lowered = value.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "sign",
        "trade",
        "live",
        "execution",
        "database",
    ):
        if forbidden in lowered:
            raise ValueError(f"{field_name} must not expose action or private surfaces")
    return value


def _require_known_value(field_name: str, value: str, known_values: tuple[str, ...]) -> None:
    if value not in known_values:
        raise ValueError(f"{field_name} must be one of {known_values}")


def _require_hard_flags(value: object) -> None:
    for field_name in HARD_FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _is_sha256_digest(value: str) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value)


def _json_ready_no_floats(value: object, *, include_digest: bool = True) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        source = asdict(value)
        if not include_digest:
            source.pop("public_digest", None)
        return {
            key: _json_ready_no_floats(item, include_digest=include_digest)
            for key, item in source.items()
        }
    if isinstance(value, tuple):
        return [_json_ready_no_floats(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready_no_floats(item, include_digest=include_digest) for item in value]
    if isinstance(value, dict):
        return {
            key: _json_ready_no_floats(item, include_digest=include_digest)
            for key, item in value.items()
        }
    return value


def _public_decimal_field_names(dataclass_type: type[object]) -> tuple[str, ...]:
    return tuple(
        field.name
        for field in fields(dataclass_type)
        if field.name.endswith("_count") or field.name.endswith("_ratio")
    )


REPORT_DECIMAL_FIELDS = _public_decimal_field_names(
    StrategyScreeningPipelineReadinessReport,
)
