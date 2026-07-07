from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


ZERO = Decimal("0")
ONE = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

NO_CANDIDATES_REASON = "no_research_candidates"
PASS_REASON = "research_decision_threshold_pass"
WATCH_REASON = "research_decision_threshold_watch"
BLOCK_REASON = "research_decision_threshold_block"

REASON_CODE_SEQUENCE = (
    NO_CANDIDATES_REASON,
    "edge_threshold_met",
    "edge_below_minimum",
    "confidence_threshold_met",
    "confidence_below_minimum",
    "cost_threshold_met",
    "cost_above_limit",
    "risk_threshold_met",
    "risk_above_limit",
    "net_score_pass_threshold_met",
    "net_score_watch_threshold_met",
    "net_score_below_watch_threshold",
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
)


@dataclass(frozen=True)
class ResearchDecisionThresholdPolicyConfig:
    config_version: str = "research-decision-threshold-policy-v0"
    pass_net_score: Decimal = Decimal("0.550000")
    watch_net_score: Decimal = Decimal("0.300000")
    min_edge_score: Decimal = Decimal("0.250000")
    min_confidence_score: Decimal = Decimal("0.400000")
    max_cost_score: Decimal = Decimal("0.500000")
    max_risk_score: Decimal = Decimal("0.500000")
    edge_weight: Decimal = Decimal("0.400000")
    confidence_weight: Decimal = Decimal("0.300000")
    cost_weight: Decimal = Decimal("0.150000")
    risk_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionThresholdPolicyConfig:
            raise TypeError(
                "ResearchDecisionThresholdPolicyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionThresholdPolicyConfig:
            raise ValueError(
                "config must be exactly ResearchDecisionThresholdPolicyConfig",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "pass_net_score",
            "watch_net_score",
            "min_edge_score",
            "min_confidence_score",
            "max_cost_score",
            "max_risk_score",
            "edge_weight",
            "confidence_weight",
            "cost_weight",
            "risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_net_score > self.pass_net_score:
            raise ValueError("pass_net_score must be at least watch_net_score")
        _require_weight_sum(self)
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class ResearchDecisionThresholdPolicyInput:
    candidate_id: str
    edge_score: Decimal
    confidence_score: Decimal
    cost_score: Decimal
    risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionThresholdPolicyInput:
            raise TypeError(
                "ResearchDecisionThresholdPolicyInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionThresholdPolicyInput:
            raise ValueError(
                "input must be exactly ResearchDecisionThresholdPolicyInput",
            )
        _require_public_string("candidate_id", self.candidate_id)
        for field_name in (
            "edge_score",
            "confidence_score",
            "cost_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)
        reject_unsafe_surface_fields("input", self)


@dataclass(frozen=True)
class ResearchDecisionThresholdPolicyRow:
    candidate_id: str
    edge_score: Decimal
    confidence_score: Decimal
    cost_score: Decimal
    risk_score: Decimal
    weighted_edge_score: Decimal
    weighted_confidence_score: Decimal
    cost_drag_score: Decimal
    risk_drag_score: Decimal
    net_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    explanation: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionThresholdPolicyRow:
            raise TypeError(
                "ResearchDecisionThresholdPolicyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionThresholdPolicyRow:
            raise ValueError("row must be exactly ResearchDecisionThresholdPolicyRow")
        _require_public_string("candidate_id", self.candidate_id)
        for field_name in (
            "edge_score",
            "confidence_score",
            "cost_score",
            "risk_score",
            "weighted_edge_score",
            "weighted_confidence_score",
            "cost_drag_score",
            "risk_drag_score",
            "net_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_public_string("explanation", self.explanation)
        require_paper_only_flags("row", self)
        reject_unsafe_surface_fields("row", self)


@dataclass(frozen=True)
class ResearchDecisionThresholdPolicyReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionThresholdPolicyReasonCodeCount:
            raise TypeError(
                "ResearchDecisionThresholdPolicyReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionThresholdPolicyReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDecisionThresholdPolicyReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _require_ratio_decimal("candidate_ratio", self.candidate_ratio),
        )
        require_paper_only_flags("reason code count", self)
        reject_unsafe_surface_fields("reason code count", self)


@dataclass(frozen=True)
class ResearchDecisionThresholdPolicyReport:
    generated_at: datetime
    config_version: str
    status: str
    explanation: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_edge_score: Decimal
    average_confidence_score: Decimal
    average_cost_score: Decimal
    average_risk_score: Decimal
    average_net_score: Decimal
    rows: tuple[ResearchDecisionThresholdPolicyRow, ...]
    reason_code_counts: tuple[ResearchDecisionThresholdPolicyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDecisionThresholdPolicyReport:
            raise TypeError(
                "ResearchDecisionThresholdPolicyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionThresholdPolicyReport:
            raise ValueError(
                "report must be exactly ResearchDecisionThresholdPolicyReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_public_string("explanation", self.explanation)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_edge_score",
            "average_confidence_score",
            "average_cost_score",
            "average_risk_score",
            "average_net_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)


def build_research_decision_threshold_policy_report(
    inputs: Iterable[ResearchDecisionThresholdPolicyInput],
    *,
    config: ResearchDecisionThresholdPolicyConfig | None = None,
    generated_at: datetime,
) -> ResearchDecisionThresholdPolicyReport:
    cfg = config or ResearchDecisionThresholdPolicyConfig()
    if type(cfg) is not ResearchDecisionThresholdPolicyConfig:
        raise ValueError("config must be a ResearchDecisionThresholdPolicyConfig")
    require_paper_only_flags("config", cfg)
    reject_unsafe_surface_fields("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows = tuple(_build_row(input_row, config=cfg) for input_row in input_rows)
    candidate_count = _count(len(rows))
    pass_count = _count(_status_count(rows, STATUS_PASS))
    watch_count = _count(_status_count(rows, STATUS_WATCH))
    block_count = _count(_status_count(rows, STATUS_BLOCK))
    reason_code_counts = _reason_code_counts(rows, candidate_count)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchDecisionThresholdPolicyReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
                candidate_ratio=ONE,
            ),
        )
        reason_codes = (NO_CANDIDATES_REASON,)
    status = _report_status(
        has_rows=bool(rows),
        block_count=block_count,
        watch_count=watch_count,
    )
    return ResearchDecisionThresholdPolicyReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=status,
        explanation=_report_explanation(status, candidate_count, reason_codes),
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_edge_score=_average(row.edge_score for row in rows),
        average_confidence_score=_average(row.confidence_score for row in rows),
        average_cost_score=_average(row.cost_score for row in rows),
        average_risk_score=_average(row.risk_score for row in rows),
        average_net_score=_average(row.net_score for row in rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_decision_threshold_policy_report_payload(
    report: ResearchDecisionThresholdPolicyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDecisionThresholdPolicyReport:
        raise ValueError("report must be a ResearchDecisionThresholdPolicyReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("payload", payload)
    return payload


def _build_row(
    input_row: ResearchDecisionThresholdPolicyInput,
    *,
    config: ResearchDecisionThresholdPolicyConfig,
) -> ResearchDecisionThresholdPolicyRow:
    weighted_edge_score = _multiply(input_row.edge_score, config.edge_weight)
    weighted_confidence_score = _multiply(
        input_row.confidence_score,
        config.confidence_weight,
    )
    cost_drag_score = _multiply(input_row.cost_score, config.cost_weight)
    risk_drag_score = _multiply(input_row.risk_score, config.risk_weight)
    net_score = _net_score(
        weighted_edge_score,
        weighted_confidence_score,
        cost_drag_score,
        risk_drag_score,
    )
    reason_codes = _row_reason_codes(
        input_row=input_row,
        config=config,
        net_score=net_score,
    )
    status = _status_from_reason_codes(reason_codes)
    return ResearchDecisionThresholdPolicyRow(
        candidate_id=input_row.candidate_id,
        edge_score=input_row.edge_score,
        confidence_score=input_row.confidence_score,
        cost_score=input_row.cost_score,
        risk_score=input_row.risk_score,
        weighted_edge_score=weighted_edge_score,
        weighted_confidence_score=weighted_confidence_score,
        cost_drag_score=cost_drag_score,
        risk_drag_score=risk_drag_score,
        net_score=net_score,
        status=status,
        reason_codes=reason_codes,
        explanation=_row_explanation(input_row.candidate_id, status, net_score, reason_codes),
    )


def _row_reason_codes(
    *,
    input_row: ResearchDecisionThresholdPolicyInput,
    config: ResearchDecisionThresholdPolicyConfig,
    net_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if input_row.edge_score >= config.min_edge_score:
        reason_codes.append("edge_threshold_met")
    else:
        reason_codes.append("edge_below_minimum")
    if input_row.confidence_score >= config.min_confidence_score:
        reason_codes.append("confidence_threshold_met")
    else:
        reason_codes.append("confidence_below_minimum")
    if input_row.cost_score <= config.max_cost_score:
        reason_codes.append("cost_threshold_met")
    else:
        reason_codes.append("cost_above_limit")
    if input_row.risk_score <= config.max_risk_score:
        reason_codes.append("risk_threshold_met")
    else:
        reason_codes.append("risk_above_limit")
    if net_score >= config.pass_net_score:
        reason_codes.append("net_score_pass_threshold_met")
    elif net_score >= config.watch_net_score:
        reason_codes.append("net_score_watch_threshold_met")
    else:
        reason_codes.append("net_score_below_watch_threshold")

    if any(
        reason_code in reason_codes
        for reason_code in (
            "edge_below_minimum",
            "confidence_below_minimum",
            "cost_above_limit",
            "risk_above_limit",
            "net_score_below_watch_threshold",
        )
    ):
        reason_codes.append(BLOCK_REASON)
    elif "net_score_pass_threshold_met" in reason_codes:
        reason_codes.append(PASS_REASON)
    else:
        reason_codes.append(WATCH_REASON)
    return tuple(reason_codes)


def _row_explanation(
    candidate_id: str,
    status: str,
    net_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    return (
        "Research threshold row "
        f"candidate={candidate_id}; status={status}; net_score={net_score}; "
        f"reasons={','.join(reason_codes)}"
    )


def _report_explanation(
    status: str,
    candidate_count: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    return (
        "Research threshold report "
        f"status={status}; candidates={candidate_count}; "
        f"reasons={','.join(reason_codes)}"
    )


def _report_status(
    *,
    has_rows: bool,
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if not has_rows or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes or NO_CANDIDATES_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes:
        return STATUS_WATCH
    if PASS_REASON in reason_codes:
        return STATUS_PASS
    raise ValueError("reason_codes must include a terminal status reason")


def _reason_code_counts(
    rows: tuple[ResearchDecisionThresholdPolicyRow, ...],
    candidate_count: Decimal,
) -> tuple[ResearchDecisionThresholdPolicyReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDecisionThresholdPolicyReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            candidate_ratio=_ratio(counts[reason_code], candidate_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_inputs(
    inputs: Iterable[ResearchDecisionThresholdPolicyInput],
) -> tuple[ResearchDecisionThresholdPolicyInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of ResearchDecisionThresholdPolicyInput")
    rows = tuple(inputs)
    for row in rows:
        if type(row) is not ResearchDecisionThresholdPolicyInput:
            raise ValueError("inputs must contain ResearchDecisionThresholdPolicyInput")
        require_paper_only_flags("input", row)
        reject_unsafe_surface_fields("input", row)
    return tuple(sorted(rows, key=lambda row: row.candidate_id))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchDecisionThresholdPolicyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDecisionThresholdPolicyRow:
            raise ValueError("rows must contain ResearchDecisionThresholdPolicyRow")
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchDecisionThresholdPolicyReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchDecisionThresholdPolicyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDecisionThresholdPolicyReasonCodeCount",
            )
        require_paper_only_flags("reason code count", row)
    return rows


def _normalize_reason_codes(
    reason_codes: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        normalized.append(reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(normalized)


def _validate_report(report: ResearchDecisionThresholdPolicyReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_edge_score != _average(row.edge_score for row in report.rows):
        raise ValueError("average_edge_score must match rows")
    if report.average_confidence_score != _average(
        row.confidence_score for row in report.rows
    ):
        raise ValueError("average_confidence_score must match rows")
    if report.average_cost_score != _average(row.cost_score for row in report.rows):
        raise ValueError("average_cost_score must match rows")
    if report.average_risk_score != _average(row.risk_score for row in report.rows):
        raise ValueError("average_risk_score must match rows")
    if report.average_net_score != _average(row.net_score for row in report.rows):
        raise ValueError("average_net_score must match rows")
    expected_reason_code_counts = _reason_code_counts(
        report.rows,
        report.candidate_count,
    )
    if not report.rows:
        expected_reason_code_counts = (
            ResearchDecisionThresholdPolicyReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
                candidate_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = tuple(row.reason_code for row in expected_reason_code_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_rows=bool(report.rows),
        block_count=report.block_count,
        watch_count=report.watch_count,
    )
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be a single-line string")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} is not an allowed reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.to_integral_value()


def _require_weight_sum(config: ResearchDecisionThresholdPolicyConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = (
            config.edge_weight
            + config.confidence_weight
            + config.cost_weight
            + config.risk_weight
        )
    if _require_decimal("weight_total", total) != ONE:
        raise ValueError(
            "edge_weight, confidence_weight, cost_weight, and risk_weight must sum to 1",
        )


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = left * right
    return _require_decimal("weighted_score", value)


def _net_score(
    weighted_edge_score: Decimal,
    weighted_confidence_score: Decimal,
    cost_drag_score: Decimal,
    risk_drag_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            weighted_edge_score
            + weighted_confidence_score
            - cost_drag_score
            - risk_drag_score
        )
    return _require_decimal("net_score", value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(VALUE_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _require_ratio_decimal("ratio", value)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO.quantize(VALUE_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        total = sum(items, ZERO)
        value = total / Decimal(len(items))
    return _require_decimal("average", value)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _status_count(
    rows: tuple[ResearchDecisionThresholdPolicyRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


__all__ = (
    "ResearchDecisionThresholdPolicyConfig",
    "ResearchDecisionThresholdPolicyInput",
    "ResearchDecisionThresholdPolicyReasonCodeCount",
    "ResearchDecisionThresholdPolicyReport",
    "ResearchDecisionThresholdPolicyRow",
    "build_research_decision_threshold_policy_report",
    "research_decision_threshold_policy_report_payload",
)
