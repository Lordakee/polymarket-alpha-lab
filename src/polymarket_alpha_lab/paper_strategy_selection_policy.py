"""Paper-only selection and sizing policy reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any


__all__ = (
    "PaperStrategySelectionPolicyConfig",
    "PaperStrategySelectionPolicyRow",
    "PaperStrategySelectionPolicyReport",
    "build_paper_strategy_selection_policy_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
NOTIONAL_QUANTUM = Decimal("0.000001")
SOURCE_ACTIONS = ("recommend", "watch", "reject")
SELECTED_SIDES = ("yes", "no", "none")
DECISIONS = ("selected", "skipped", "not_selected")
RECOMMENDATION_MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_recommendation"
RECOMMENDATION_REPORT_TYPE_NAME = "PaperStrategyCandidateRecommendationReport"


@dataclass(frozen=True)
class PaperStrategySelectionPolicyConfig:
    config_version: str
    base_position_notional: Decimal
    max_position_notional: Decimal
    max_total_notional: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "base_position_notional",
            self.base_position_notional,
        )
        if self.base_position_notional <= ZERO:
            raise ValueError("base_position_notional must be positive")
        _require_nonnegative_decimal(
            "max_position_notional",
            self.max_position_notional,
        )
        if self.max_position_notional <= ZERO:
            raise ValueError("max_position_notional must be positive")
        _require_nonnegative_decimal(
            "max_total_notional",
            self.max_total_notional,
        )
        if self.max_total_notional <= ZERO:
            raise ValueError("max_total_notional must be positive")


@dataclass(frozen=True)
class PaperStrategySelectionPolicyRow:
    market_slug: str
    question: str
    source_action: str
    selected_side: str
    recommendation_score: Decimal
    decision: str
    suggested_position_notional: Decimal
    selected_position_notional: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_source_action("source_action", self.source_action)
        _require_selected_side("selected_side", self.selected_side)
        _require_nonnegative_decimal(
            "recommendation_score",
            self.recommendation_score,
        )
        _require_decision("decision", self.decision)
        _require_notional("suggested_position_notional", self.suggested_position_notional)
        _require_notional("selected_position_notional", self.selected_position_notional)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class PaperStrategySelectionPolicyReport:
    generated_at: datetime
    config_version: str
    row_count: int
    selected_count: int
    skipped_count: int
    not_selected_count: int
    total_selected_notional: Decimal
    selection_rows: tuple[PaperStrategySelectionPolicyRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("row_count", self.row_count)
        _require_nonnegative_int("selected_count", self.selected_count)
        _require_nonnegative_int("skipped_count", self.skipped_count)
        _require_nonnegative_int("not_selected_count", self.not_selected_count)
        _require_notional("total_selected_notional", self.total_selected_notional)
        object.__setattr__(
            self,
            "selection_rows",
            _normalize_selection_rows(self.selection_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_selection_policy_report(
    recommendation_report: object,
    *,
    config: PaperStrategySelectionPolicyConfig,
    generated_at: datetime,
) -> PaperStrategySelectionPolicyReport:
    if type(config) is not PaperStrategySelectionPolicyConfig:
        raise ValueError("config must be a PaperStrategySelectionPolicyConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _validate_recommendation_report(recommendation_report)

    selection_rows: list[PaperStrategySelectionPolicyRow] = []
    total_selected_notional = ZERO
    total_cap_reached = False
    for source_row in _source_recommendation_rows(recommendation_report):
        row_action = _source_action(source_row)
        if row_action != "recommend":
            selection_rows.append(
                _not_selected_row(
                    source_row,
                    reason_code=f"source_action_{row_action}",
                ),
            )
            continue

        suggested_position_notional = _suggested_position_notional(source_row, config)
        if (
            total_cap_reached
            or total_selected_notional + suggested_position_notional
            > config.max_total_notional
        ):
            total_cap_reached = True
            selection_rows.append(
                _policy_row(
                    source_row,
                    decision="skipped",
                    suggested_position_notional=suggested_position_notional,
                    selected_position_notional=ZERO.quantize(NOTIONAL_QUANTUM),
                    reason_codes=(
                        "total_notional_cap_reached",
                        *_source_reason_codes(source_row),
                    ),
                ),
            )
            continue

        selection_rows.append(
            _policy_row(
                source_row,
                decision="selected",
                suggested_position_notional=suggested_position_notional,
                selected_position_notional=suggested_position_notional,
                reason_codes=("selected_by_policy", *_source_reason_codes(source_row)),
            ),
        )
        total_selected_notional = _quantize_notional(
            total_selected_notional + suggested_position_notional,
        )

    rows = tuple(selection_rows)
    return PaperStrategySelectionPolicyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        row_count=len(rows),
        selected_count=_decision_count(rows, "selected"),
        skipped_count=_decision_count(rows, "skipped"),
        not_selected_count=_decision_count(rows, "not_selected"),
        total_selected_notional=total_selected_notional,
        selection_rows=rows,
    )


def _not_selected_row(
    source_row: object,
    *,
    reason_code: str,
) -> PaperStrategySelectionPolicyRow:
    zero_notional = ZERO.quantize(NOTIONAL_QUANTUM)
    return _policy_row(
        source_row,
        decision="not_selected",
        suggested_position_notional=zero_notional,
        selected_position_notional=zero_notional,
        reason_codes=(reason_code, *_source_reason_codes(source_row)),
    )


def _policy_row(
    source_row: object,
    *,
    decision: str,
    suggested_position_notional: Decimal,
    selected_position_notional: Decimal,
    reason_codes: tuple[str, ...],
) -> PaperStrategySelectionPolicyRow:
    return PaperStrategySelectionPolicyRow(
        market_slug=_source_market_slug(source_row),
        question=_source_question(source_row),
        source_action=_source_action(source_row),
        selected_side=_source_selected_side(source_row),
        recommendation_score=_source_recommendation_score(source_row),
        decision=decision,
        suggested_position_notional=suggested_position_notional,
        selected_position_notional=selected_position_notional,
        reason_codes=reason_codes,
    )


def _suggested_position_notional(
    source_row: object,
    config: PaperStrategySelectionPolicyConfig,
) -> Decimal:
    raw_notional = config.base_position_notional * _source_recommendation_score(source_row)
    capped_notional = min(raw_notional, config.max_position_notional)
    return _quantize_notional(capped_notional)


def _validate_recommendation_report(recommendation_report: object) -> None:
    expected_type = _recommendation_report_type()
    if expected_type is None:
        if type(recommendation_report).__name__ != RECOMMENDATION_REPORT_TYPE_NAME:
            raise ValueError(
                "recommendation_report must be a "
                "PaperStrategyCandidateRecommendationReport",
            )
    elif type(recommendation_report) is not expected_type:
        raise ValueError(
            "recommendation_report must be a PaperStrategyCandidateRecommendationReport",
        )
    if getattr(recommendation_report, "paper_only", None) is not True:
        raise ValueError("recommendation_report must be paper_only")
    if getattr(recommendation_report, "report_only", None) is not True:
        raise ValueError("recommendation_report must be report_only")
    if getattr(recommendation_report, "readonly", None) is not True:
        raise ValueError("recommendation_report must be readonly")
    _source_recommendation_rows(recommendation_report)


def _recommendation_report_type() -> type[Any] | None:
    try:
        module = import_module(RECOMMENDATION_MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == RECOMMENDATION_MODULE_NAME:
            return None
        raise
    expected_type = getattr(module, RECOMMENDATION_REPORT_TYPE_NAME, None)
    if not isinstance(expected_type, type):
        return None
    return expected_type


def _source_recommendation_rows(recommendation_report: object) -> tuple[object, ...]:
    rows = _required_attr(recommendation_report, "recommendation_rows")
    if isinstance(rows, (str, bytes)):
        raise ValueError("recommendation_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("recommendation_rows must be an iterable") from exc
    for row in items:
        _validate_source_row(row)
    return items


def _validate_source_row(row: object) -> None:
    _source_market_slug(row)
    _source_question(row)
    _source_action(row)
    _source_selected_side(row)
    _source_recommendation_score(row)
    _source_reason_codes(row)


def _source_market_slug(row: object) -> str:
    value = _required_attr(row, "market_slug")
    _require_canonical_string("market_slug", value)
    return value


def _source_question(row: object) -> str:
    value = _required_attr(row, "question")
    _require_canonical_string("question", value)
    return value


def _source_action(row: object) -> str:
    value = _required_attr(row, "action")
    _require_source_action("action", value)
    return value


def _source_selected_side(row: object) -> str:
    value = _required_attr(row, "selected_side")
    _require_selected_side("selected_side", value)
    return value


def _source_recommendation_score(row: object) -> Decimal:
    value = _required_attr(row, "recommendation_score")
    _require_nonnegative_decimal("recommendation_score", value)
    if value > ONE:
        raise ValueError("recommendation_score must be at most 1")
    return value


def _source_reason_codes(row: object) -> tuple[str, ...]:
    value = _required_attr(row, "reason_codes")
    return _normalize_source_reason_codes(value)


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _validate_row_consistency(row: PaperStrategySelectionPolicyRow) -> None:
    if row.decision == "selected":
        if row.source_action != "recommend":
            raise ValueError("selected rows must come from recommend actions")
        if row.selected_side == "none":
            raise ValueError("selected rows must have a selected side")
        if row.selected_position_notional <= ZERO:
            raise ValueError("selected rows must have positive selected_position_notional")
        if row.selected_position_notional != row.suggested_position_notional:
            raise ValueError(
                "selected rows must use the suggested_position_notional",
            )
    elif row.selected_position_notional != ZERO.quantize(NOTIONAL_QUANTUM):
        raise ValueError("unselected rows must have zero selected_position_notional")
    if row.decision == "skipped" and row.source_action != "recommend":
        raise ValueError("skipped rows must come from recommend actions")
    if row.decision == "not_selected" and row.source_action == "recommend":
        raise ValueError("recommend actions must be selected or skipped")


def _validate_report_consistency(report: PaperStrategySelectionPolicyReport) -> None:
    if report.row_count != len(report.selection_rows):
        raise ValueError("row_count must match selection_rows")
    if report.selected_count != _decision_count(report.selection_rows, "selected"):
        raise ValueError("selected_count must match selection_rows")
    if report.skipped_count != _decision_count(report.selection_rows, "skipped"):
        raise ValueError("skipped_count must match selection_rows")
    if report.not_selected_count != _decision_count(
        report.selection_rows,
        "not_selected",
    ):
        raise ValueError("not_selected_count must match selection_rows")
    if (
        report.selected_count + report.skipped_count + report.not_selected_count
        != report.row_count
    ):
        raise ValueError("decision counts must match row_count")
    total_selected_notional = _quantize_notional(
        sum((row.selected_position_notional for row in report.selection_rows), ZERO),
    )
    if report.total_selected_notional != total_selected_notional:
        raise ValueError("total_selected_notional must match selection_rows")


def _decision_count(
    rows: tuple[PaperStrategySelectionPolicyRow, ...],
    decision: str,
) -> int:
    return sum(1 for row in rows if row.decision == decision)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_notional(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_notional(value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_source_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_ACTIONS:
        raise ValueError(f"{field_name} must be recommend, watch, or reject")


def _require_selected_side(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SELECTED_SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_decision(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DECISIONS:
        raise ValueError(f"{field_name} must be selected, skipped, or not_selected")


def _normalize_selection_rows(
    value: tuple[PaperStrategySelectionPolicyRow, ...],
) -> tuple[PaperStrategySelectionPolicyRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("selection_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("selection_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperStrategySelectionPolicyRow:
            raise ValueError(
                "selection_rows must contain PaperStrategySelectionPolicyRow values",
            )
    return rows


def _normalize_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    items = _normalize_source_reason_codes(value)
    if not items:
        raise ValueError("reason_codes must contain at least one value")
    return items


def _normalize_source_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string("reason_codes", item)
    return items


def _quantize_notional(value: Decimal) -> Decimal:
    _require_nonnegative_decimal("notional", value)
    return value.quantize(NOTIONAL_QUANTUM)
