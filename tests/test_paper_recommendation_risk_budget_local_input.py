from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.paper_recommendation_risk_budget import (
    PaperRecommendationRiskBudgetConfig,
    build_paper_recommendation_risk_budget_report,
)
from polymarket_alpha_lab.paper_recommendation_risk_budget_local_input import (
    PaperRecommendationRiskBudgetLocalSelectionReport,
    read_paper_recommendation_risk_budget_selection_report,
    paper_recommendation_risk_budget_nav_report_from_notional,
)


GENERATED_AT = datetime(2026, 6, 21, 12, 0, tzinfo=UTC)


def _write_json(path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _config() -> PaperRecommendationRiskBudgetConfig:
    return PaperRecommendationRiskBudgetConfig(
        config_version="risk-budget-v0",
        max_total_utilization=Decimal("0.250000"),
        max_single_recommendation_share=Decimal("0.100000"),
        min_remaining_notional=Decimal("10.000000"),
        max_selected_count=2,
    )


def test_jsonl_selection_report_feeds_existing_risk_budget_reducer(tmp_path):
    path = tmp_path / "selection.jsonl"
    path.write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "decision": "selected",
                        "selected_position_notional": "12.345678",
                    },
                ),
                json.dumps(
                    {
                        "decision": "skipped",
                        "selected_position_notional": "0.000000",
                    },
                ),
            ),
        ),
        encoding="utf-8",
    )

    selection_report = read_paper_recommendation_risk_budget_selection_report(path)
    nav_report = paper_recommendation_risk_budget_nav_report_from_notional(
        Decimal("1000.000000"),
    )
    risk_report = build_paper_recommendation_risk_budget_report(
        selection_report,
        nav_risk_metrics_report=nav_report,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert selection_report.paper_only is True
    assert selection_report.report_only is True
    assert selection_report.readonly is True
    assert tuple(row.decision for row in selection_report.selection_rows) == (
        "selected",
        "skipped",
    )
    assert selection_report.selection_rows[0].selected_position_notional == Decimal(
        "12.345678",
    )
    assert risk_report.status == "pass"
    assert risk_report.total_suggested_notional == Decimal("12.345678")
    assert risk_report.selected_count == 1


@pytest.mark.parametrize(
    "payload",
    (
        [
            {"decision": "selected", "selected_position_notional": "1.000000"},
            {"decision": "not_selected", "selected_position_notional": "0.000000"},
        ],
        {
            "selection_rows": [
                {"decision": "selected", "selected_position_notional": "1.000000"},
            ],
        },
        {"rows": [{"decision": "selected", "selected_position_notional": "1.000000"}]},
        {
            "inputs": [
                {"decision": "selected", "selected_position_notional": "1.000000"},
            ],
        },
        {
            "input_rows": [
                {"decision": "selected", "selected_position_notional": "1.000000"},
            ],
        },
        {"decision": "selected", "selected_position_notional": "1.000000"},
    ),
)
def test_json_array_envelopes_and_single_row_are_supported(tmp_path, payload):
    path = tmp_path / "selection.json"
    _write_json(path, payload)

    report = read_paper_recommendation_risk_budget_selection_report(str(path))

    assert type(report) is PaperRecommendationRiskBudgetLocalSelectionReport
    assert all(row.paper_only is True for row in report.selection_rows)
    assert report.selection_rows[0].decision == "selected"
    assert report.selection_rows[0].selected_position_notional == Decimal("1.000000")


@pytest.mark.parametrize(
    "content",
    (
        "",
        "   \n",
        "[]",
        '{"selection_rows": []}',
        '{"rows": []}',
        '{"inputs": []}',
        '{"input_rows": []}',
    ),
)
def test_empty_input_returns_empty_hard_flagged_selection_report(tmp_path, content):
    path = tmp_path / "empty-selection.json"
    path.write_text(content, encoding="utf-8")

    report = read_paper_recommendation_risk_budget_selection_report(path)

    assert report.selection_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    "row, match",
    (
        (
            {"decision": " selected", "selected_position_notional": "1.000000"},
            "decision",
        ),
        (
            {"decision": "recommend", "selected_position_notional": "1.000000"},
            "decision",
        ),
        (
            {"decision": "selected", "selected_position_notional": 1.0},
            "float",
        ),
        (
            {"decision": "selected", "selected_position_notional": 1},
            "string",
        ),
        (
            {"decision": "selected", "selected_position_notional": True},
            "bool",
        ),
        (
            {"decision": "selected", "selected_position_notional": "NaN"},
            "finite",
        ),
        (
            {"decision": "selected", "selected_position_notional": "-0.000001"},
            "nonnegative",
        ),
        (
            {"decision": "selected", "selected_position_notional": "1.0000001"},
            "quantized",
        ),
        ("not an object", "JSON object"),
    ),
)
def test_invalid_rows_are_rejected(tmp_path, row, match):
    path = tmp_path / "bad-selection.json"
    _write_json(path, [row])

    with pytest.raises(ValueError, match=match):
        read_paper_recommendation_risk_budget_selection_report(path)


def test_hard_flag_false_values_are_rejected(tmp_path):
    path = tmp_path / "bad-flags.json"
    _write_json(
        path,
        {
            "selection_rows": [
                {
                    "decision": "selected",
                    "selected_position_notional": "1.000000",
                    "paper_only": False,
                },
            ],
        },
    )

    with pytest.raises(ValueError, match="selection_row must be paper_only"):
        read_paper_recommendation_risk_budget_selection_report(path)


def test_envelope_hard_flag_false_values_are_rejected(tmp_path):
    path = tmp_path / "bad-envelope-flags.json"
    _write_json(
        path,
        {
            "selection_rows": [
                {
                    "decision": "selected",
                    "selected_position_notional": "1.000000",
                },
            ],
            "paper_only": False,
            "report_only": True,
            "readonly": True,
        },
    )

    with pytest.raises(ValueError, match="selection_report must be paper_only"):
        read_paper_recommendation_risk_budget_selection_report(path)


def test_nav_report_helper_recovers_optional_notional_and_is_frozen():
    present = paper_recommendation_risk_budget_nav_report_from_notional(
        Decimal("250.123456"),
    )
    absent = paper_recommendation_risk_budget_nav_report_from_notional(None)

    assert present.latest_exit_nav == Decimal("250.123456")
    assert present.paper_only is True
    assert present.report_only is True
    assert present.readonly is True
    assert absent.latest_exit_nav is None
    with pytest.raises(FrozenInstanceError):
        present.latest_exit_nav = Decimal("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="float"):
        paper_recommendation_risk_budget_nav_report_from_notional(1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quantized"):
        paper_recommendation_risk_budget_nav_report_from_notional(Decimal("1E+100"))
