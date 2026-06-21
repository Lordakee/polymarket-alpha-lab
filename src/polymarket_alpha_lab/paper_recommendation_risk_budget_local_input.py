from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any

__all__ = (
    "PaperRecommendationRiskBudgetLocalNavReport",
    "PaperRecommendationRiskBudgetLocalSelectionReport",
    "PaperRecommendationRiskBudgetLocalSelectionRow",
    "paper_recommendation_risk_budget_nav_report_from_notional",
    "read_paper_recommendation_risk_budget_selection_report",
)


ZERO = Decimal("0")
NOTIONAL_QUANTUM = Decimal("0.000001")
DECISIONS = ("selected", "skipped", "not_selected")
_ROW_ENVELOPE_KEYS = ("selection_rows", "rows", "inputs", "input_rows")


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetLocalSelectionRow:
    decision: str
    selected_position_notional: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_decision("decision", self.decision)
        object.__setattr__(
            self,
            "selected_position_notional",
            _normalize_notional(
                "selected_position_notional",
                self.selected_position_notional,
            ),
        )
        _require_safety_flags("selection_row", self)


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetLocalSelectionReport:
    selection_rows: tuple[PaperRecommendationRiskBudgetLocalSelectionRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        rows = _normalize_selection_rows(self.selection_rows)
        object.__setattr__(self, "selection_rows", rows)
        _require_safety_flags("selection_report", self)


@dataclass(frozen=True)
class PaperRecommendationRiskBudgetLocalNavReport:
    latest_exit_nav: Decimal | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "latest_exit_nav",
            _normalize_optional_notional("latest_exit_nav", self.latest_exit_nav),
        )
        _require_safety_flags("nav_report", self)


def read_paper_recommendation_risk_budget_selection_report(
    path: Path | str,
) -> PaperRecommendationRiskBudgetLocalSelectionReport:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return PaperRecommendationRiskBudgetLocalSelectionReport(selection_rows=())

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        rows = _read_jsonl_rows(target, text)
    else:
        rows = tuple(
            _recover_row(row, path=target, row_number=row_number)
            for row_number, row in enumerate(
                _extract_row_payloads(payload, path=target),
                start=1,
            )
        )
    return PaperRecommendationRiskBudgetLocalSelectionReport(selection_rows=rows)


def paper_recommendation_risk_budget_nav_report_from_notional(
    value: Decimal | None,
) -> PaperRecommendationRiskBudgetLocalNavReport:
    return PaperRecommendationRiskBudgetLocalNavReport(latest_exit_nav=value)


def _read_jsonl_rows(
    path: Path,
    text: str,
) -> tuple[PaperRecommendationRiskBudgetLocalSelectionRow, ...]:
    rows: list[PaperRecommendationRiskBudgetLocalSelectionRow] = []
    for row_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} line {row_number} is not valid JSON: {exc}") from exc
        rows.append(_recover_row(payload, path=path, row_number=row_number))
    return tuple(rows)


def _extract_row_payloads(payload: object, *, path: Path) -> tuple[object, ...]:
    if isinstance(payload, list):
        return tuple(payload)
    if isinstance(payload, dict):
        for key in _ROW_ENVELOPE_KEYS:
            if key not in payload:
                continue
            _require_envelope_safety_flags(payload)
            value = payload[key]
            if not isinstance(value, list):
                raise ValueError(f"{path} {key} must be a JSON array")
            return tuple(value)
        return (payload,)
    raise ValueError(
        f"{path} input must be a JSON object, JSON array, or JSONL file",
    )


def _recover_row(
    payload: object,
    *,
    path: Path,
    row_number: int,
) -> PaperRecommendationRiskBudgetLocalSelectionRow:
    if not isinstance(payload, dict):
        raise ValueError(f"{path} row {row_number} must be a JSON object")
    try:
        return PaperRecommendationRiskBudgetLocalSelectionRow(
            decision=_required_field(payload, "decision"),
            selected_position_notional=_as_decimal(
                "selected_position_notional",
                _required_field(payload, "selected_position_notional"),
            ),
            paper_only=_optional_bool_field(payload, "paper_only", True),
            report_only=_optional_bool_field(payload, "report_only", True),
            readonly=_optional_bool_field(payload, "readonly", True),
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            f"{path} row {row_number} is not a valid selection row: {exc}",
        ) from exc


def _required_field(payload: dict[str, Any], field_name: str) -> object:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    return payload[field_name]


def _optional_bool_field(
    payload: dict[str, Any],
    field_name: str,
    default: bool,
) -> bool:
    value = payload.get(field_name, default)
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_envelope_safety_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if field_name in payload and payload[field_name] is not True:
            raise ValueError(f"selection_report must be {field_name}")


def _normalize_selection_rows(
    value: tuple[PaperRecommendationRiskBudgetLocalSelectionRow, ...],
) -> tuple[PaperRecommendationRiskBudgetLocalSelectionRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("selection_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("selection_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperRecommendationRiskBudgetLocalSelectionRow:
            raise ValueError(
                "selection_rows must contain "
                "PaperRecommendationRiskBudgetLocalSelectionRow values",
            )
        _require_safety_flags("selection_rows", row)
    return rows


def _require_decision(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DECISIONS:
        raise ValueError(f"{field_name} must be selected, skipped, or not_selected")


def _as_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must be a string")
    try:
        decimal = Decimal(str(value))
    except InvalidOperation:
        raise
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _normalize_optional_notional(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must not be a bool")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    return _normalize_notional(field_name, value)


def _normalize_notional(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        quantized = value.quantize(NOTIONAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantized to 0.000001") from exc
    if value != quantized:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return quantized


def _require_safety_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")
