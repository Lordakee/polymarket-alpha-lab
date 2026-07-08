from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_settlement_cost_pressure_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-market-settlement-cost-pressure-report-v0",
        "aggregate_spread_watch_ratio": d("0.020000"),
        "aggregate_spread_block_ratio": d("0.050000"),
        "fee_friction_watch_ratio": d("0.015000"),
        "fee_friction_block_ratio": d("0.040000"),
        "settlement_delay_watch_score": d("0.300000"),
        "settlement_delay_block_score": d("0.700000"),
        "depth_fade_watch_ratio": d("0.250000"),
        "depth_fade_block_ratio": d("0.600000"),
        "quote_staleness_watch_seconds": d("120.000000"),
        "quote_staleness_block_seconds": d("300.000000"),
        "watch_pressure_score": d("0.300000"),
        "block_pressure_score": d("0.700000"),
    }
    values.update(overrides)
    return report.ResearchMarketSettlementCostPressureConfig(**values)


def observation(**overrides: object):
    report = api()
    values = {
        "public_pressure_key": "aggregate-alpha",
        "observed_at": GENERATED_AT,
        "aggregate_spread_ratio": d("0.006000"),
        "fee_friction_ratio": d("0.004000"),
        "settlement_delay_risk_score": d("0.100000"),
        "depth_fade_ratio": d("0.100000"),
        "quote_staleness_seconds": d("30.000000"),
    }
    values.update(overrides)
    return report.ResearchMarketSettlementCostPressureObservation(**values)


def build_report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_market_settlement_cost_pressure_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def sample_rows():
    return (
        observation(public_pressure_key="aggregate-alpha"),
        observation(
            public_pressure_key="aggregate-beta",
            aggregate_spread_ratio=d("0.024000"),
            fee_friction_ratio=d("0.016000"),
            settlement_delay_risk_score=d("0.350000"),
            depth_fade_ratio=d("0.300000"),
            quote_staleness_seconds=d("150.000000"),
        ),
        observation(
            public_pressure_key="aggregate-gamma",
            aggregate_spread_ratio=d("0.060000"),
            fee_friction_ratio=d("0.050000"),
            settlement_delay_risk_score=d("0.800000"),
            depth_fade_ratio=d("0.650000"),
            quote_staleness_seconds=d("360.000000"),
        ),
    )


def test_report_summarizes_pass_watch_and_block_settlement_cost_pressure() -> None:
    settlement_report = build_report(*sample_rows())

    assert is_dataclass(settlement_report)
    assert api().STATUSES == ("pass", "watch", "block")
    assert settlement_report.generated_at == GENERATED_AT
    assert settlement_report.generated_at.tzinfo is UTC
    assert settlement_report.config_version == (
        "research-market-settlement-cost-pressure-report-v0"
    )
    assert settlement_report.input_count == d("3")
    assert settlement_report.row_count == d("3")
    assert settlement_report.pass_count == d("1")
    assert settlement_report.watch_count == d("1")
    assert settlement_report.block_count == d("1")
    assert settlement_report.spread_pressure_count == d("2")
    assert settlement_report.fee_friction_count == d("2")
    assert settlement_report.settlement_delay_risk_count == d("2")
    assert settlement_report.depth_fade_count == d("2")
    assert settlement_report.quote_staleness_count == d("2")
    assert settlement_report.mean_aggregate_spread_ratio == d("0.030000")
    assert settlement_report.mean_fee_friction_ratio == d("0.023333")
    assert settlement_report.mean_settlement_delay_risk_score == d("0.416667")
    assert settlement_report.mean_depth_fade_ratio == d("0.350000")
    assert settlement_report.mean_quote_staleness_seconds == d("180.000000")
    assert settlement_report.mean_pressure_score == d("0.533968")
    assert settlement_report.status == "block"
    assert settlement_report.reason_codes == (
        "aggregate_spread_pressure_detected",
        "fee_friction_detected",
        "settlement_delay_risk_detected",
        "depth_fade_detected",
        "quote_staleness_detected",
        "composite_settlement_cost_pressure_detected",
    )
    assert settlement_report.paper_only is True
    assert settlement_report.report_only is True
    assert settlement_report.readonly is True

    first, second, third = settlement_report.rows
    assert first.public_pressure_key == "aggregate-gamma"
    assert first.aggregate_spread_pressure == d("1.000000")
    assert first.fee_friction_pressure == d("1.000000")
    assert first.settlement_delay_pressure == d("1.000000")
    assert first.depth_fade_pressure == d("1.000000")
    assert first.quote_staleness_pressure == d("1.000000")
    assert first.pressure_score == d("1.000000")
    assert first.status == "block"
    assert first.reason_codes == (
        "aggregate_spread_blocking",
        "fee_friction_blocking",
        "settlement_delay_risk_blocking",
        "depth_fade_blocking",
        "quote_staleness_blocking",
        "composite_settlement_cost_pressure_blocking",
    )

    assert second.public_pressure_key == "aggregate-beta"
    assert second.pressure_score == d("0.476000")
    assert second.status == "watch"
    assert second.reason_codes == (
        "aggregate_spread_watch",
        "fee_friction_watch",
        "settlement_delay_risk_watch",
        "depth_fade_watch",
        "quote_staleness_watch",
        "composite_settlement_cost_pressure_watch",
    )

    assert third.public_pressure_key == "aggregate-alpha"
    assert third.pressure_score == d("0.125905")
    assert third.status == "pass"
    assert third.reason_codes == ("settlement_cost_pressure_clear",)


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_only() -> None:
    report_module = api()
    left = build_report(*sample_rows())
    right = build_report(*reversed(sample_rows()))

    left_payload = report_module.research_market_settlement_cost_pressure_report_payload(
        left,
    )
    right_payload = report_module.research_market_settlement_cost_pressure_report_payload(
        right,
    )
    left_digest = report_module.research_market_settlement_cost_pressure_report_digest(
        left,
    )
    right_digest = report_module.research_market_settlement_cost_pressure_report_digest(
        right,
    )

    assert left_payload == right_payload
    assert left_digest == right_digest
    assert left_digest == report_module.research_market_settlement_cost_pressure_report_digest(
        left_payload,
    )
    assert len(left_digest) == 64
    assert left_payload["generated_at"] == "2026-07-08T09:30:00+00:00"
    assert left_payload["input_count"] == "3"
    assert left_payload["rows"][0]["pressure_score"] == "1.000000"
    assert left_payload["paper_only"] is True
    assert left_payload["report_only"] is True
    assert left_payload["readonly"] is True
    assert "raw-market-secret" not in repr(left_payload)
    assert "raw-source-secret" not in repr(left_payload)
    assert "Decimal(" not in repr(left_payload)
    assert "datetime" not in repr(left_payload).lower()
    assert not any(type(value) is float for value in _walk_payload_values(left_payload))


def test_empty_inputs_block_with_public_no_observations_reason() -> None:
    settlement_report = build_report()

    assert settlement_report.status == "block"
    assert settlement_report.input_count == d("0")
    assert settlement_report.row_count == d("0")
    assert settlement_report.reason_codes == ("no_settlement_cost_pressure_observations",)
    assert settlement_report.mean_pressure_score == d("0.000000")


def test_validation_rejects_non_decimal_metrics_bad_time_and_unsafe_identifiers() -> None:
    report_module = api()

    with pytest.raises(ValueError, match="aggregate_spread_ratio must be a Decimal"):
        observation(aggregate_spread_ratio=0.006)

    with pytest.raises(ValueError, match="fee_friction_ratio must be a Decimal"):
        observation(fee_friction_ratio=1)

    with pytest.raises(ValueError, match="depth_fade_ratio must be a Decimal"):
        observation(depth_fade_ratio=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="quote_staleness_seconds must be finite"):
        observation(quote_staleness_seconds=Decimal("NaN"))

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        replace(observation(), observed_at=datetime(2026, 7, 8, 9, 30))

    with pytest.raises(ValueError, match="generated_at must be datetime"):
        build_report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 9, 30, tzinfo=UTC))

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="observation must be readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="aggregate_spread_block_ratio must exceed"):
        config(aggregate_spread_block_ratio=d("0.020000"))

    with pytest.raises(ValueError, match="public_pressure_key"):
        observation(public_pressure_key="raw-market-secret")

    with pytest.raises(ValueError, match="public_pressure_key"):
        observation(public_pressure_key="raw-source-secret")

    settlement_report = build_report(observation())
    with pytest.raises(ValueError, match="status is not supported"):
        replace(settlement_report.rows[0], status="blocked")

    with pytest.raises(ValueError, match="input_count"):
        replace(settlement_report, input_count=d("2"))

    with pytest.raises(ValueError, match="rows"):
        replace(settlement_report, rows=(settlement_report.rows[0],) * 2)

    with pytest.raises(ValueError, match="payload must be readonly"):
        report_module.research_market_settlement_cost_pressure_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        report_module.research_market_settlement_cost_pressure_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "mean_pressure_score": 0.1,
            },
        )


def test_public_dataclasses_are_frozen() -> None:
    settlement_report = build_report(observation())

    with pytest.raises(FrozenInstanceError):
        settlement_report.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        settlement_report.rows[0].pressure_score = d("0")  # type: ignore[misc]


def test_owned_module_has_no_execution_writes_or_recommendation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_settlement_cost_pressure_report.py"
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
        "wallet",
        "auth",
        "order",
        "trade",
        "execution",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
