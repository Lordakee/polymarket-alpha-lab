from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 45, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_settlement_cost_refresh_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cost_input(**overrides: object):
    report = api()
    values = {
        "public_cost_key": "settlement-alpha",
        "sanitized_fee_ratio": d("0.006000"),
        "sanitized_spread_ratio": d("0.010000"),
        "sanitized_slippage_ratio": d("0.004000"),
        "sanitized_settlement_friction_ratio": d("0.003000"),
        "quote_age_seconds": d("30.000000"),
    }
    values.update(overrides)
    return report.ResearchMarketSettlementCostRefreshInput(**values)


def build_report(*inputs, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_market_settlement_cost_refresh_report(
        inputs,
        config=cfg or report.ResearchMarketSettlementCostRefreshConfig(),
        generated_at=generated_at,
    )


def sample_inputs():
    return (
        cost_input(public_cost_key="settlement-alpha"),
        cost_input(
            public_cost_key="settlement-beta",
            sanitized_fee_ratio=d("0.012000"),
            sanitized_spread_ratio=d("0.024000"),
            sanitized_slippage_ratio=d("0.011000"),
            sanitized_settlement_friction_ratio=d("0.012000"),
            quote_age_seconds=d("150.000000"),
        ),
        cost_input(
            public_cost_key="settlement-gamma",
            sanitized_fee_ratio=d("0.030000"),
            sanitized_spread_ratio=d("0.060000"),
            sanitized_slippage_ratio=d("0.030000"),
            sanitized_settlement_friction_ratio=d("0.035000"),
            quote_age_seconds=d("420.000000"),
        ),
    )


def test_report_aggregates_sanitized_settlement_cost_refresh_pressure() -> None:
    settlement_report = build_report(*sample_inputs())

    assert api().STATUSES == ("pass", "watch", "block")
    assert settlement_report.generated_at == GENERATED_AT
    assert settlement_report.input_count == d("3.000000")
    assert settlement_report.row_count == d("3.000000")
    assert settlement_report.pass_count == d("1.000000")
    assert settlement_report.watch_count == d("1.000000")
    assert settlement_report.block_count == d("1.000000")
    assert settlement_report.fee_pressure_count == d("2.000000")
    assert settlement_report.spread_pressure_count == d("2.000000")
    assert settlement_report.slippage_pressure_count == d("2.000000")
    assert settlement_report.settlement_friction_pressure_count == d("2.000000")
    assert settlement_report.quote_age_pressure_count == d("2.000000")
    assert settlement_report.mean_sanitized_fee_ratio == d("0.016000")
    assert settlement_report.mean_sanitized_spread_ratio == d("0.031333")
    assert settlement_report.mean_sanitized_slippage_ratio == d("0.015000")
    assert settlement_report.mean_sanitized_settlement_friction_ratio == d("0.016667")
    assert settlement_report.mean_quote_age_seconds == d("200.000000")
    assert settlement_report.mean_refresh_pressure_score == d("0.504630")
    assert settlement_report.status == "block"
    assert settlement_report.reason_codes == (
        "sanitized_fee_pressure",
        "sanitized_spread_pressure",
        "sanitized_slippage_pressure",
        "settlement_friction_pressure",
        "quote_age_freshness_pressure",
        "composite_refresh_pressure",
    )

    first, second, third = settlement_report.rows
    assert first.public_cost_key == "settlement-gamma"
    assert first.refresh_pressure_score == d("1.000000")
    assert first.status == "block"
    assert first.reason_codes == (
        "sanitized_fee_block",
        "sanitized_spread_block",
        "sanitized_slippage_block",
        "settlement_friction_block",
        "quote_age_freshness_block",
        "composite_refresh_pressure_block",
    )

    assert second.public_cost_key == "settlement-beta"
    assert second.refresh_pressure_score == d("0.388889")
    assert second.status == "watch"
    assert second.reason_codes == (
        "sanitized_fee_watch",
        "sanitized_spread_watch",
        "sanitized_slippage_watch",
        "settlement_friction_watch",
        "quote_age_freshness_watch",
        "composite_refresh_pressure_watch",
    )

    assert third.public_cost_key == "settlement-alpha"
    assert third.refresh_pressure_score == d("0.125000")
    assert third.status == "pass"
    assert third.reason_codes == ("settlement_cost_refresh_clear",)


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_validated() -> None:
    report_module = api()
    left = build_report(*sample_inputs())
    right = build_report(*reversed(sample_inputs()))

    left_payload = report_module.research_market_settlement_cost_refresh_report_payload(
        left,
    )
    right_payload = report_module.research_market_settlement_cost_refresh_report_payload(
        right,
    )
    left_digest = left.derived_validation_digest

    assert left_payload == right_payload
    assert left_digest == right.derived_validation_digest
    assert left_payload["derived_validation_digest"] == left_digest
    assert len(left_digest) == 64
    assert all(character in "0123456789abcdef" for character in left_digest)
    assert left_payload["generated_at"] == "2026-07-08T12:45:00+00:00"
    assert left_payload["rows"][0]["public_cost_key"] == "settlement-gamma"
    assert left_payload["rows"][0]["refresh_pressure_score"] == "1.000000"
    assert left_payload["paper_only"] is True
    assert left_payload["report_only"] is True
    assert left_payload["readonly"] is True
    assert "Decimal(" not in repr(left_payload)
    assert "datetime" not in repr(left_payload).lower()
    assert not any(type(value) is float for value in _walk_payload_values(left_payload))

    tampered = {
        field.name: getattr(left, field.name)
        for field in fields(report_module.ResearchMarketSettlementCostRefreshReport)
    }
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.ResearchMarketSettlementCostRefreshReport(**tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left.rows[0], refresh_pressure_score=d("0.900000"))


def test_empty_inputs_block_with_sanitized_public_reason() -> None:
    settlement_report = build_report()

    assert settlement_report.status == "block"
    assert settlement_report.input_count == d("0.000000")
    assert settlement_report.row_count == d("0.000000")
    assert settlement_report.mean_refresh_pressure_score == d("0.000000")
    assert settlement_report.reason_codes == ("settlement_cost_refresh_no_inputs",)
    assert settlement_report.reason_code_counts[0].reason_code == (
        "settlement_cost_refresh_no_inputs"
    )


def test_validates_decimal_only_metrics_statuses_flags_and_public_identifiers() -> None:
    report_module = api()

    with pytest.raises(ValueError, match="sanitized_fee_ratio must be a Decimal"):
        cost_input(sanitized_fee_ratio=0.006)

    with pytest.raises(ValueError, match="sanitized_spread_ratio must be a Decimal"):
        cost_input(sanitized_spread_ratio=1)

    with pytest.raises(ValueError, match="quote_age_seconds must be finite"):
        cost_input(quote_age_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="public_cost_key"):
        cost_input(public_cost_key="raw-market-secret")

    with pytest.raises(ValueError, match="public_cost_key"):
        cost_input(public_cost_key="question-url")

    with pytest.raises(ValueError, match="input must be report_only"):
        cost_input(report_only=False)

    settlement_report = build_report(cost_input())
    with pytest.raises(ValueError, match="status"):
        replace(settlement_report.rows[0], status="blocked")

    inconsistent = {
        field.name: getattr(settlement_report, field.name)
        for field in fields(report_module.ResearchMarketSettlementCostRefreshReport)
    }
    inconsistent["input_count"] = d("2.000000")
    inconsistent["derived_validation_digest"] = ""
    with pytest.raises(ValueError, match="input_count"):
        report_module.ResearchMarketSettlementCostRefreshReport(**inconsistent)

    with pytest.raises(ValueError, match="payload must be readonly"):
        report_module.research_market_settlement_cost_refresh_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        report_module.research_market_settlement_cost_refresh_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "mean_refresh_pressure_score": 0.1,
            },
        )


def test_public_dataclasses_are_frozen_and_module_has_no_execution_surface() -> None:
    settlement_report = build_report(cost_input())

    with pytest.raises(FrozenInstanceError):
        settlement_report.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        settlement_report.rows[0].refresh_pressure_score = d("0")  # type: ignore[misc]

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_settlement_cost_refresh_report.py"
    )
    text = module_path.read_text(encoding="utf-8")
    lowered = text.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "database",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "position",
        "live",
    ):
        assert forbidden not in lowered

    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)
