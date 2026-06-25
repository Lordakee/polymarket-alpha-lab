"""Pure bridge from probability selection summaries to scorer market data."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from decimal import Decimal

from polymarket_alpha_lab.paper_probability_selection_summary import (
    PaperProbabilitySelectionSummaryReport,
    PaperProbabilitySelectionSummaryRow,
)


__all__ = ("paper_probability_selection_summary_report_to_market_data",)

ZERO = Decimal("0")
ONE = Decimal("1")


def paper_probability_selection_summary_report_to_market_data(
    report: PaperProbabilitySelectionSummaryReport,
) -> tuple[dict[str, object], ...]:
    """Convert exact selection summary rows into autonomous scorer market_data."""

    if type(report) is not PaperProbabilitySelectionSummaryReport:
        raise ValueError("report must be exactly PaperProbabilitySelectionSummaryReport")
    _require_hard_flags("selection_report", report)
    _reject_floats("selection_report", report)
    return tuple(_row_to_market_data(row) for row in report.rows)


def _row_to_market_data(row: PaperProbabilitySelectionSummaryRow) -> dict[str, object]:
    if type(row) is not PaperProbabilitySelectionSummaryRow:
        raise ValueError("rows must contain exact PaperProbabilitySelectionSummaryRow values")
    _require_hard_flags("selection_row", row)
    confidence_score = _require_ratio_decimal(
        "recommendation_score",
        row.recommendation_score,
    )
    edge_score = _require_ratio_decimal("net_probability_edge", row.net_probability_edge)
    recommended_notional = _require_nonnegative_decimal(
        "executable_paper_shares",
        row.executable_paper_shares,
    )
    if row.worst_stressed_net_probability_edge is not None:
        _require_decimal(
            "worst_stressed_net_probability_edge",
            row.worst_stressed_net_probability_edge,
        )

    return {
        "condition_id": f"selection_summary:{row.market_slug}:{row.side}",
        "market_slug": row.market_slug,
        "question": row.question,
        "scoring_side": row.side,
        "confidence_score": confidence_score,
        "edge_score": edge_score,
        "recommended_notional": recommended_notional,
        "selection_status": row.selection_status,
        "reason_codes": tuple(sorted(row.reason_codes)),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _reject_floats(field_name: str, value: object) -> None:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _reject_floats(
                f"{field_name}.{item_field.name}",
                getattr(value, item_field.name),
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_floats(f"{field_name}.{key}", item)
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            _reject_floats(f"{field_name}.{index}", item)
