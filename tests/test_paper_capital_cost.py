from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from polymarket_alpha_lab.paper_capital_cost import (
    PaperCapitalCostConfig,
    PaperCapitalCostReport,
    PaperCapitalCostRow,
    build_paper_capital_cost_report,
)


GENERATED_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
CONFIG = PaperCapitalCostConfig(
    config_version="paper-capital-cost-v0",
    annual_capital_cost_rate=Decimal("0.120000"),
)


def _input(
    *,
    market_slug: str = "will-example-resolve-yes",
    question: str = "Will the example resolve yes?",
    side: str = "yes",
    paper_notional: Decimal = Decimal("100.000000"),
    paper_share_quantity: Decimal = Decimal("250.000000"),
    days_locked: int = 30,
) -> dict[str, object]:
    return {
        "market_slug": market_slug,
        "question": question,
        "side": side,
        "paper_notional": paper_notional,
        "paper_share_quantity": paper_share_quantity,
        "days_locked": days_locked,
    }


def test_paper_capital_cost_report_calculates_costs_from_explicit_inputs():
    config = PaperCapitalCostConfig(
        config_version="paper-capital-cost-v0",
        annual_capital_cost_rate=Decimal("0.100000"),
    )

    report = build_paper_capital_cost_report(
        [
            _input(
                paper_notional=Decimal("365.000000"),
                paper_share_quantity=Decimal("40.000000"),
                days_locked=10,
            ),
            SimpleNamespace(
                market_slug="will-example-resolve-no",
                question="Will the example resolve no?",
                side="no",
                paper_notional=Decimal("730.000000"),
                paper_share_quantity=Decimal("100.000000"),
                days_locked=20,
            ),
        ],
        config=config,
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, PaperCapitalCostReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-capital-cost-v0"
    assert report.row_count == 2
    assert report.total_paper_notional == Decimal("1095.000000")
    assert report.total_capital_cost == Decimal("5.000000")
    assert report.mean_capital_cost_per_share == Decimal("0.032500")
    assert report.capital_cost_rows == (
        PaperCapitalCostRow(
            market_slug="will-example-resolve-yes",
            question="Will the example resolve yes?",
            side="yes",
            paper_notional=Decimal("365.000000"),
            paper_share_quantity=Decimal("40.000000"),
            days_locked=10,
            annual_capital_cost_rate=Decimal("0.100000"),
            total_capital_cost=Decimal("1.000000"),
            capital_cost_per_share=Decimal("0.025000"),
        ),
        PaperCapitalCostRow(
            market_slug="will-example-resolve-no",
            question="Will the example resolve no?",
            side="no",
            paper_notional=Decimal("730.000000"),
            paper_share_quantity=Decimal("100.000000"),
            days_locked=20,
            annual_capital_cost_rate=Decimal("0.100000"),
            total_capital_cost=Decimal("4.000000"),
            capital_cost_per_share=Decimal("0.040000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only is True for row in report.capital_cost_rows)
    assert all(row.report_only is True for row in report.capital_cost_rows)
    assert all(row.readonly is True for row in report.capital_cost_rows)


def test_paper_capital_cost_report_preserves_input_sequence():
    report = build_paper_capital_cost_report(
        [
            _input(market_slug="first", question="First?", side="yes"),
            _input(market_slug="second", question="Second?", side="no"),
            _input(market_slug="third", question="Third?", side="yes"),
        ],
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert [row.market_slug for row in report.capital_cost_rows] == [
        "first",
        "second",
        "third",
    ]


def test_paper_capital_cost_report_zero_days_has_zero_cost():
    report = build_paper_capital_cost_report(
        [_input(days_locked=0)],
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.capital_cost_rows[0].total_capital_cost == Decimal("0.000000")
    assert report.capital_cost_rows[0].capital_cost_per_share == Decimal("0.000000")
    assert report.total_capital_cost == Decimal("0.000000")
    assert report.mean_capital_cost_per_share == Decimal("0.000000")


def test_paper_capital_cost_report_uses_decimal_rate_without_rate_quantization():
    config = PaperCapitalCostConfig(
        config_version="paper-capital-cost-v0",
        annual_capital_cost_rate=Decimal("0.1234567"),
    )

    report = build_paper_capital_cost_report(
        [
            _input(
                paper_notional=Decimal("1000000.000000"),
                paper_share_quantity=Decimal("10.000000"),
                days_locked=365,
            ),
        ],
        config=config,
        generated_at=GENERATED_AT,
    )

    row = report.capital_cost_rows[0]
    assert row.annual_capital_cost_rate == Decimal("0.1234567")
    assert row.total_capital_cost == Decimal("123456.700000")
    assert row.capital_cost_per_share == Decimal("12345.670000")


def test_paper_capital_cost_report_empty_inputs_returns_zero_totals():
    report = build_paper_capital_cost_report(
        [],
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.row_count == 0
    assert report.total_paper_notional == Decimal("0.000000")
    assert report.total_capital_cost == Decimal("0.000000")
    assert report.mean_capital_cost_per_share is None
    assert report.capital_cost_rows == ()


@pytest.mark.parametrize(
    ("config_kwargs", "match"),
    (
        ({"config_version": "", "annual_capital_cost_rate": Decimal("0")}, "config_version"),
        (
            {
                "config_version": "paper-capital-cost-v0",
                "annual_capital_cost_rate": Decimal("-0.000001"),
            },
            "annual_capital_cost_rate",
        ),
        (
            {
                "config_version": "paper-capital-cost-v0",
                "annual_capital_cost_rate": 0.12,
            },
            "annual_capital_cost_rate",
        ),
    ),
)
def test_paper_capital_cost_config_rejects_invalid_values(config_kwargs, match):
    with pytest.raises(ValueError, match=match):
        PaperCapitalCostConfig(**config_kwargs)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("paper_notional", Decimal("-0.000001")),
        ("paper_notional", Decimal("100.0000004")),
        ("paper_notional", 100),
        ("paper_share_quantity", Decimal("0")),
        ("paper_share_quantity", Decimal("-0.000001")),
        ("paper_share_quantity", Decimal("10.0000004")),
        ("paper_share_quantity", 10),
        ("days_locked", -1),
        ("days_locked", Decimal("1")),
        ("days_locked", True),
        ("side", "maybe"),
    ),
)
def test_paper_capital_cost_report_rejects_invalid_row_inputs(field_name, value):
    row_input = _input()
    row_input[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        build_paper_capital_cost_report(
            [row_input],
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_paper_capital_cost_builder_rejects_invalid_top_level_inputs():
    with pytest.raises(ValueError, match="config"):
        build_paper_capital_cost_report(
            [_input()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_capital_cost_report(
            [_input()],
            config=CONFIG,
            generated_at="now",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_capital_cost_report(
            object(),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="market_slug"):
        build_paper_capital_cost_report(
            [{"question": "Question?", "side": "yes"}],
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_paper_capital_cost_dataclasses_validate_flags_and_are_frozen():
    report = build_paper_capital_cost_report(
        [_input()],
        config=CONFIG,
        generated_at=GENERATED_AT,
    )
    row = report.capital_cost_rows[0]

    with pytest.raises(FrozenInstanceError):
        report.row_count = 1
    with pytest.raises(FrozenInstanceError):
        row.total_capital_cost = Decimal("0.000000")
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_paper_capital_cost_module_has_no_live_boundary_terms():
    import inspect
    import polymarket_alpha_lab.paper_capital_cost as module

    source = inspect.getsource(module).lower()

    for forbidden in (
        "auth",
        "account",
        "wallet",
        "order",
        "sign",
        "submit",
        "cancel",
        "network",
        "client",
    ):
        assert forbidden not in source
