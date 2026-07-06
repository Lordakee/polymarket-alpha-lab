"""Read-only paper outcome feedback contract v4 validation report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_STRATEGY_OUTCOME_FEEDBACK_CONTRACT_V4_VERSION = (
    "strategy-outcome-feedback-contract-v4"
)

OUTCOMES = ("win", "loss", "push", "void")
SOURCE_FAILURE_TAGS = (
    "stale_source",
    "resolution_rule_miss",
    "source_conflict",
    "missing_primary_source",
    "late_update",
    "model_assumption_miss",
)
REASON_CODES = (
    "feedback_contract_ready",
    "unsupported_outcome",
    "outcome_payout_mismatch",
    "missing_source_failure_tags",
    "missing_resolution_notes",
)
STATUSES = ("pass", "blocked")

COUNT_QUANTUM = Decimal("1")
AMOUNT_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_AMOUNT = Decimal("0.000000")
ONE_AMOUNT = Decimal("1.000000")
PUSH_PAYOUT = Decimal("0.500000")
SIGNED_FLOOR = Decimal("-1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "pass": Decimal("0"),
    "blocked": Decimal("1"),
}


@dataclass(frozen=True)
class StrategyOutcomeFeedbackContractV4Input:
    recommendation_id: str
    team_id: str
    category_id: str
    settled_at: datetime
    outcome: str
    payout: Decimal
    forecast_probability: Decimal
    cost_adjusted_edge: Decimal
    source_failure_tags: tuple[str, ...]
    resolution_notes: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "settled_at", _as_utc("settled_at", self.settled_at))
        _require_canonical_string("outcome", self.outcome)
        object.__setattr__(
            self,
            "payout",
            _normalize_unit_decimal("payout", self.payout),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_unit_decimal(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "source_failure_tags",
            _normalize_source_failure_tags(self.source_failure_tags),
        )
        object.__setattr__(
            self,
            "resolution_notes",
            _normalize_resolution_notes(self.resolution_notes),
        )
        require_paper_only_flags("StrategyOutcomeFeedbackContractV4Input", self)


@dataclass(frozen=True)
class StrategyOutcomeFeedbackContractV4Row:
    recommendation_id: str
    team_id: str
    category_id: str
    settled_at: datetime
    outcome: str
    payout: Decimal
    forecast_probability: Decimal
    cost_adjusted_edge: Decimal
    source_failure_tags: tuple[str, ...]
    resolution_notes: str
    validation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("recommendation_id", self.recommendation_id)
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "settled_at", _as_utc("settled_at", self.settled_at))
        _require_canonical_string("outcome", self.outcome)
        object.__setattr__(
            self,
            "payout",
            _normalize_unit_decimal("payout", self.payout),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_unit_decimal(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "source_failure_tags",
            _normalize_source_failure_tags(self.source_failure_tags),
        )
        object.__setattr__(
            self,
            "resolution_notes",
            _normalize_resolution_notes(self.resolution_notes),
        )
        _require_member("validation_status", self.validation_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("StrategyOutcomeFeedbackContractV4Row", self)


@dataclass(frozen=True)
class StrategyOutcomeFeedbackContractV4Report:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    feedback_ready_count: Decimal
    blocked_count: Decimal
    total_payout: Decimal
    average_forecast_probability: Decimal
    average_cost_adjusted_edge: Decimal
    source_failure_tagged_count: Decimal
    missing_resolution_notes_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyOutcomeFeedbackContractV4Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "feedback_ready_count",
            "blocked_count",
            "source_failure_tagged_count",
            "missing_resolution_notes_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_payout",
            _normalize_nonnegative_amount("total_payout", self.total_payout),
        )
        object.__setattr__(
            self,
            "average_forecast_probability",
            _normalize_unit_decimal(
                "average_forecast_probability",
                self.average_forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "average_cost_adjusted_edge",
            _normalize_signed_decimal(
                "average_cost_adjusted_edge",
                self.average_cost_adjusted_edge,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("strategy outcome feedback contract v4", self)
        require_paper_only_flags("StrategyOutcomeFeedbackContractV4Report", self)


def build_strategy_outcome_feedback_contract_v4_report(
    inputs: list[StrategyOutcomeFeedbackContractV4Input]
    | tuple[StrategyOutcomeFeedbackContractV4Input, ...],
    *,
    generated_at: datetime,
) -> StrategyOutcomeFeedbackContractV4Report:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_for_input(value, generated_at=generated_at_utc) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return StrategyOutcomeFeedbackContractV4Report(
        generated_at=generated_at_utc,
        config_version=DEFAULT_STRATEGY_OUTCOME_FEEDBACK_CONTRACT_V4_VERSION,
        source_row_count=_count(len(rows)),
        feedback_ready_count=_count(
            sum(1 for row in rows if row.validation_status == "pass"),
        ),
        blocked_count=_count(sum(1 for row in rows if row.validation_status == "blocked")),
        total_payout=_sum_amounts(rows, "payout"),
        average_forecast_probability=_average_amount(rows, "forecast_probability"),
        average_cost_adjusted_edge=_average_amount(rows, "cost_adjusted_edge"),
        source_failure_tagged_count=_count(
            sum(1 for row in rows if row.source_failure_tags),
        ),
        missing_resolution_notes_count=_count(
            sum(1 for row in rows if not row.resolution_notes),
        ),
        status=_status_rollup(tuple(row.validation_status for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_outcome_feedback_contract_v4_payload(
    report: StrategyOutcomeFeedbackContractV4Report,
) -> dict[str, Any]:
    if type(report) is not StrategyOutcomeFeedbackContractV4Report:
        raise ValueError("report must be a StrategyOutcomeFeedbackContractV4Report")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("strategy outcome feedback contract v4", report)
    return json_ready_no_floats(report)


def _row_for_input(
    value: StrategyOutcomeFeedbackContractV4Input,
    *,
    generated_at: datetime,
) -> StrategyOutcomeFeedbackContractV4Row:
    if value.settled_at > generated_at:
        raise ValueError("settled_at must not be after generated_at")
    reason_codes = _row_reason_codes(
        outcome=value.outcome,
        payout=value.payout,
        source_failure_tags=value.source_failure_tags,
        resolution_notes=value.resolution_notes,
    )
    return StrategyOutcomeFeedbackContractV4Row(
        recommendation_id=value.recommendation_id,
        team_id=value.team_id,
        category_id=value.category_id,
        settled_at=value.settled_at,
        outcome=value.outcome,
        payout=value.payout,
        forecast_probability=value.forecast_probability,
        cost_adjusted_edge=value.cost_adjusted_edge,
        source_failure_tags=value.source_failure_tags,
        resolution_notes=value.resolution_notes,
        validation_status=_validation_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    outcome: str,
    payout: Decimal,
    source_failure_tags: tuple[str, ...],
    resolution_notes: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if outcome not in OUTCOMES:
        codes.append("unsupported_outcome")
    elif not _payout_matches_outcome(outcome=outcome, payout=payout):
        codes.append("outcome_payout_mismatch")
    if outcome == "loss" and not source_failure_tags:
        codes.append("missing_source_failure_tags")
    if not resolution_notes:
        codes.append("missing_resolution_notes")
    if not codes:
        codes.append("feedback_contract_ready")
    return tuple(code for code in REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[StrategyOutcomeFeedbackContractV4Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("feedback_contract_ready",)
    codes = {
        code
        for row in rows
        for code in row.reason_codes
        if code != "feedback_contract_ready"
    }
    if not codes:
        return ("feedback_contract_ready",)
    return tuple(code for code in REASON_CODES if code in codes)


def _payout_matches_outcome(*, outcome: str, payout: Decimal) -> bool:
    if outcome == "win":
        return payout == ONE_AMOUNT
    if outcome == "loss":
        return payout == ZERO_AMOUNT
    if outcome == "push":
        return payout == PUSH_PAYOUT
    if outcome == "void":
        return payout == ZERO_AMOUNT
    return False


def _validation_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("feedback_contract_ready",):
        return "pass"
    return "blocked"


def _normalize_inputs(
    inputs: list[StrategyOutcomeFeedbackContractV4Input]
    | tuple[StrategyOutcomeFeedbackContractV4Input, ...],
) -> tuple[StrategyOutcomeFeedbackContractV4Input, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_recommendation_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyOutcomeFeedbackContractV4Input:
            raise ValueError(
                "inputs must contain StrategyOutcomeFeedbackContractV4Input values",
            )
        require_paper_only_flags("input", row)
        if row.recommendation_id in seen_recommendation_ids:
            raise ValueError(
                "inputs must not contain duplicate recommendation_id values",
            )
        seen_recommendation_ids.add(row.recommendation_id)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyOutcomeFeedbackContractV4Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not StrategyOutcomeFeedbackContractV4Row:
            raise ValueError(
                "rows must contain StrategyOutcomeFeedbackContractV4Row values",
            )
        require_paper_only_flags("row", row)
    return rows


def _validate_row(row: StrategyOutcomeFeedbackContractV4Row) -> None:
    expected = _row_reason_codes(
        outcome=row.outcome,
        payout=row.payout,
        source_failure_tags=row.source_failure_tags,
        resolution_notes=row.resolution_notes,
    )
    if row.reason_codes != expected:
        raise ValueError("reason_codes must match row status")
    if row.validation_status != _validation_status(row.reason_codes):
        raise ValueError("validation_status must match reason_codes")


def _validate_report(report: StrategyOutcomeFeedbackContractV4Report) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.feedback_ready_count != _count(
        sum(1 for row in report.rows if row.validation_status == "pass"),
    ):
        raise ValueError("feedback_ready_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in report.rows if row.validation_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.total_payout != _sum_amounts(report.rows, "payout"):
        raise ValueError("total_payout must match rows")
    if report.average_forecast_probability != _average_amount(
        report.rows,
        "forecast_probability",
    ):
        raise ValueError("average_forecast_probability must match rows")
    if report.average_cost_adjusted_edge != _average_amount(
        report.rows,
        "cost_adjusted_edge",
    ):
        raise ValueError("average_cost_adjusted_edge must match rows")
    if report.source_failure_tagged_count != _count(
        sum(1 for row in report.rows if row.source_failure_tags),
    ):
        raise ValueError("source_failure_tagged_count must match rows")
    if report.missing_resolution_notes_count != _count(
        sum(1 for row in report.rows if not row.resolution_notes),
    ):
        raise ValueError("missing_resolution_notes_count must match rows")
    if report.status != _status_rollup(tuple(row.validation_status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and recommendation_id")


def _row_sort_key(
    row: StrategyOutcomeFeedbackContractV4Row,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.validation_status],
        -_count(len(tuple(code for code in row.reason_codes if code != "feedback_contract_ready"))),
        row.recommendation_id,
    )


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    return "pass"


def _sum_amounts(
    rows: tuple[StrategyOutcomeFeedbackContractV4Row, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = sum((getattr(row, field_name) for row in rows), ZERO_AMOUNT)
    return _normalize_nonnegative_amount(field_name, value)


def _average_amount(
    rows: tuple[StrategyOutcomeFeedbackContractV4Row, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_AMOUNT
    with localcontext(DECIMAL_CONTEXT):
        value = sum((getattr(row, field_name) for row in rows), ZERO_AMOUNT) / _count(
            len(rows),
        )
    return _normalize_signed_decimal(field_name, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_signed_decimal(field_name, value)
    if normalized < ZERO_AMOUNT or normalized > ONE_AMOUNT:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_amount(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_AMOUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(AMOUNT_QUANTUM)


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < SIGNED_FLOOR or value > ONE_AMOUNT:
        raise ValueError(f"{field_name} must be between -1 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(AMOUNT_QUANTUM)


def _normalize_source_failure_tags(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("source_failure_tags must be a list or tuple")
    tags = tuple(value)
    for tag in tags:
        _require_member("source_failure_tags", tag, SOURCE_FAILURE_TAGS)
    if len(set(tags)) != len(tags):
        raise ValueError("source_failure_tags must be unique")
    if tuple(tag for tag in SOURCE_FAILURE_TAGS if tag in tags) != tags:
        raise ValueError("source_failure_tags must be deterministic")
    return tags


def _normalize_resolution_notes(value: object) -> str:
    if type(value) is not str:
        raise ValueError("resolution_notes must be a string")
    if value and value.strip() != value:
        raise ValueError("resolution_notes must be canonical")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_STRATEGY_OUTCOME_FEEDBACK_CONTRACT_V4_VERSION",
    "StrategyOutcomeFeedbackContractV4Input",
    "StrategyOutcomeFeedbackContractV4Report",
    "StrategyOutcomeFeedbackContractV4Row",
    "build_strategy_outcome_feedback_contract_v4_report",
    "strategy_outcome_feedback_contract_v4_payload",
)
