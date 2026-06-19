from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_external_cost_assumptions import (
    PaperExternalCostAssumptionRow,
    PaperExternalCostAssumptionsReport,
    build_paper_external_cost_assumptions_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def cost_row(
    *,
    cost_name: str = "usdc_deposit_fee",
    cost_scope: str = "account",
    amount: Decimal = d("12.345678"),
    amortize_over_trades: int | None = 100,
    reason: str = "user supplied deposit fee estimate",
    flags: tuple[tuple[str, bool], ...] = (
        ("paper_only", True),
        ("report_only", True),
        ("readonly", True),
    ),
) -> PaperExternalCostAssumptionRow:
    return PaperExternalCostAssumptionRow(
        cost_name=cost_name,
        cost_scope=cost_scope,
        amount=amount,
        amortize_over_trades=amortize_over_trades,
        reason=reason,
        flags=flags,
    )


def build_report(
    *rows: PaperExternalCostAssumptionRow,
) -> PaperExternalCostAssumptionsReport:
    return build_paper_external_cost_assumptions_report(
        generated_at=GENERATED_AT,
        config_version="external-cost-assumptions-v0",
        rows=rows,
    )


def test_aggregates_costs_by_scope_and_computes_per_trade_estimate():
    eastern = timezone(timedelta(hours=-4))

    report = build_paper_external_cost_assumptions_report(
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
        config_version="external-cost-assumptions-v0",
        rows=(
            cost_row(
                cost_name="deposit_fee",
                cost_scope="account",
                amount=d("10.000000"),
                amortize_over_trades=100,
                reason="deposit cost estimate from user config",
            ),
            cost_row(
                cost_name="withdrawal_fee",
                cost_scope="cycle",
                amount=d("2.000000"),
                amortize_over_trades=20,
                reason="withdrawal cost estimate from user config",
            ),
            cost_row(
                cost_name="settlement_overhead",
                cost_scope="market",
                amount=d("0.300000"),
                amortize_over_trades=3,
                reason="settlement overhead assumption",
            ),
            cost_row(
                cost_name="opportunity_cost",
                cost_scope="trade",
                amount=d("0.030000"),
                amortize_over_trades=None,
                reason="per trade opportunity cost assumption",
            ),
            cost_row(
                cost_name="unamortized_network_buffer",
                cost_scope="cycle",
                amount=d("1.000000"),
                amortize_over_trades=None,
                reason="reported as cycle total but excluded from per trade estimate",
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "external-cost-assumptions-v0"
    assert report.row_count == 5
    assert report.total_account_cost == d("10.000000")
    assert report.total_cycle_cost == d("3.000000")
    assert report.total_market_cost == d("0.300000")
    assert report.total_trade_cost == d("0.030000")
    assert report.per_trade_cost_estimate == d("0.330000")
    assert [row.cost_name for row in report.rows] == [
        "deposit_fee",
        "withdrawal_fee",
        "settlement_overhead",
        "opportunity_cost",
        "unamortized_network_buffer",
    ]
    assert report.flags == (
        ("paper_only", True),
        ("report_only", True),
        ("readonly", True),
    )


def test_dataclasses_are_frozen():
    row = cost_row()
    report = build_report(row)

    with pytest.raises(FrozenInstanceError):
        row.amount = d("1.000000")
    with pytest.raises(FrozenInstanceError):
        report.rows = ()


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("amount", Decimal("-0.000001"), "amount"),
        ("amount", Decimal("-0.0000004"), "amount"),
        ("amount", Decimal("NaN"), "amount"),
        ("amount", _DecimalSubclass("1.000000"), "amount"),
        ("cost_scope", "wallet", "cost_scope"),
        ("cost_scope", "trade ", "cost_scope"),
        ("amortize_over_trades", 0, "amortize_over_trades"),
        ("amortize_over_trades", -1, "amortize_over_trades"),
        ("amortize_over_trades", True, "amortize_over_trades"),
    ),
)
def test_row_rejects_invalid_public_values(field_name, bad_value, match):
    with pytest.raises(ValueError, match=match):
        replace(cost_row(), **{field_name: bad_value})


def test_rejects_invalid_builder_and_report_values():
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_external_cost_assumptions_report(
            generated_at="2026-06-19T12:00:00Z",
            config_version="external-cost-assumptions-v0",
            rows=(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        PaperExternalCostAssumptionsReport(
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
            config_version="external-cost-assumptions-v0",
            row_count=0,
            total_account_cost=ZERO,
            total_cycle_cost=ZERO,
            total_market_cost=ZERO,
            total_trade_cost=ZERO,
            per_trade_cost_estimate=ZERO,
            rows=(),
        )
    with pytest.raises(ValueError, match="rows"):
        build_paper_external_cost_assumptions_report(
            generated_at=GENERATED_AT,
            config_version="external-cost-assumptions-v0",
            rows=[object()],
        )
    with pytest.raises(ValueError, match="row_count"):
        replace(build_report(cost_row()), row_count=2)
    with pytest.raises(ValueError, match="total_account_cost"):
        replace(build_report(cost_row()), total_account_cost=d("0.000000"))


def test_rejects_unsafe_flags():
    with pytest.raises(ValueError, match="flags"):
        cost_row(flags=(("paper_only", True), ("report_only", True)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(build_report(cost_row()), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(build_report(cost_row()), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(build_report(cost_row()), readonly=False)


def test_no_network_live_auth_order_or_signer_imports():
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "paper_external_cost_assumptions.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names.add(node.module or "")

    forbidden_fragments = {
        "auth",
        "client",
        "clob",
        "exchange",
        "http",
        "order",
        "private",
        "requests",
        "signer",
        "socket",
        "urllib",
        "wallet",
        "web3",
    }
    assert not {
        name
        for name in imported_names
        if any(fragment in name.lower() for fragment in forbidden_fragments)
    }
