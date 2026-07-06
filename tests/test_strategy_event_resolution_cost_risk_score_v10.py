from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_event_resolution_cost_risk_score_v10 import (
    StrategyEventResolutionCostRiskScoreV10Input,
    StrategyEventResolutionCostRiskScoreV10Report,
    build_strategy_event_resolution_cost_risk_score_v10_report,
    strategy_event_resolution_cost_risk_score_v10_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_event_resolution_cost_risk_score_v10.py",
)


class StrategyEventResolutionCostRiskScoreV10InputSubclass(
    StrategyEventResolutionCostRiskScoreV10Input,
):
    pass


class StrategyEventResolutionCostRiskScoreV10ReportSubclass(
    StrategyEventResolutionCostRiskScoreV10Report,
):
    pass


def _report(
    *,
    market_id: str = "event-1",
    fee_drag_bps: Decimal = Decimal("0"),
    expected_slippage_bps: Decimal = Decimal("0"),
    dispute_ambiguity_score: Decimal = Decimal("0"),
    settlement_delay_hours: Decimal = Decimal("0"),
    resolution_source_confidence: Decimal = Decimal("1"),
) -> StrategyEventResolutionCostRiskScoreV10Report:
    return build_strategy_event_resolution_cost_risk_score_v10_report(
        market_id=market_id,
        fee_drag_bps=fee_drag_bps,
        expected_slippage_bps=expected_slippage_bps,
        dispute_ambiguity_score=dispute_ambiguity_score,
        settlement_delay_hours=settlement_delay_hours,
        resolution_source_confidence=resolution_source_confidence,
    )


def test_resolution_cost_risk_score_passes_clean_event_resolution_surface() -> None:
    report = _report()

    assert report.market_id == "event-1"
    assert report.cost_drag_bps == Decimal("0.000000")
    assert report.resolution_cost_risk_score == Decimal("0.000000")
    assert report.risk_status == "pass"
    assert report.required_followups == ()
    assert report.reason_codes == ("resolution_cost_risk_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    for value in (
        report.fee_drag_bps,
        report.expected_slippage_bps,
        report.dispute_ambiguity_score,
        report.settlement_delay_hours,
        report.resolution_source_confidence,
        report.cost_drag_bps,
        report.resolution_cost_risk_score,
    ):
        assert type(value) is Decimal


def test_resolution_cost_risk_score_watches_mixed_resolution_drag() -> None:
    report = _report(
        market_id="event-watch",
        fee_drag_bps=Decimal("25"),
        expected_slippage_bps=Decimal("40"),
        dispute_ambiguity_score=Decimal("0.50"),
        settlement_delay_hours=Decimal("72"),
        resolution_source_confidence=Decimal("0.70"),
    )

    assert report.cost_drag_bps == Decimal("65.000000")
    assert report.resolution_cost_risk_score == Decimal("0.379286")
    assert report.risk_status == "watch"
    assert report.required_followups == (
        "review_fee_drag",
        "review_expected_slippage",
        "clarify_dispute_ambiguity",
        "track_settlement_delay",
        "refresh_resolution_source_confidence",
    )
    assert report.reason_codes == (
        "fee_drag_present",
        "expected_slippage_present",
        "dispute_ambiguity_present",
        "settlement_delay_present",
        "resolution_source_confidence_gap",
    )


def test_resolution_cost_risk_score_blocks_and_clamps_severe_resolution_drag() -> None:
    report = _report(
        market_id="event-block",
        fee_drag_bps=Decimal("250"),
        expected_slippage_bps=Decimal("150"),
        dispute_ambiguity_score=Decimal("1"),
        settlement_delay_hours=Decimal("336"),
        resolution_source_confidence=Decimal("0"),
    )

    assert report.cost_drag_bps == Decimal("400.000000")
    assert report.resolution_cost_risk_score == Decimal("1.000000")
    assert report.risk_status == "blocked"
    assert report.required_followups == (
        "reduce_fee_drag",
        "reduce_expected_slippage",
        "resolve_dispute_ambiguity",
        "plan_settlement_delay",
        "refresh_resolution_source_confidence",
    )
    assert report.reason_codes == (
        "fee_drag_high",
        "expected_slippage_high",
        "dispute_ambiguity_high",
        "settlement_delay_long",
        "resolution_source_confidence_severe_gap",
    )


def test_resolution_cost_risk_payload_is_report_only_json_ready() -> None:
    report = _report(
        market_id="event-payload",
        fee_drag_bps=Decimal("25"),
        expected_slippage_bps=Decimal("40"),
        dispute_ambiguity_score=Decimal("0.50"),
        settlement_delay_hours=Decimal("72"),
        resolution_source_confidence=Decimal("0.70"),
    )

    payload = strategy_event_resolution_cost_risk_score_v10_payload(report)

    assert payload == report.payload
    assert payload == {
        "market_id": "event-payload",
        "fee_drag_bps": "25.000000",
        "expected_slippage_bps": "40.000000",
        "dispute_ambiguity_score": "0.500000",
        "settlement_delay_hours": "72.000000",
        "resolution_source_confidence": "0.700000",
        "cost_drag_bps": "65.000000",
        "resolution_cost_risk_score": "0.379286",
        "risk_status": "watch",
        "required_followups": [
            "review_fee_drag",
            "review_expected_slippage",
            "clarify_dispute_ambiguity",
            "track_settlement_delay",
            "refresh_resolution_source_confidence",
        ],
        "reason_codes": [
            "fee_drag_present",
            "expected_slippage_present",
            "dispute_ambiguity_present",
            "settlement_delay_present",
            "resolution_source_confidence_gap",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert all(not isinstance(value, Decimal) for value in payload.values())


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("market_id", "", "market_id"),
        ("market_id", " event-1 ", "market_id"),
        ("fee_drag_bps", 1, "fee_drag_bps"),
        ("fee_drag_bps", Decimal("-0.000001"), "fee_drag_bps"),
        ("expected_slippage_bps", Decimal("-0.000001"), "expected_slippage_bps"),
        ("dispute_ambiguity_score", Decimal("1.000001"), "dispute_ambiguity_score"),
        ("settlement_delay_hours", Decimal("-0.000001"), "settlement_delay_hours"),
        (
            "resolution_source_confidence",
            Decimal("-0.000001"),
            "resolution_source_confidence",
        ),
        ("paper_only", False, "paper_only"),
        ("report_only", False, "report_only"),
        ("readonly", False, "readonly"),
    ),
)
def test_resolution_cost_risk_input_validates_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    kwargs: dict[str, object] = {
        "market_id": "event-1",
        "fee_drag_bps": Decimal("0"),
        "expected_slippage_bps": Decimal("0"),
        "dispute_ambiguity_score": Decimal("0"),
        "settlement_delay_hours": Decimal("0"),
        "resolution_source_confidence": Decimal("1"),
        field_name: bad_value,
    }

    with pytest.raises(ValueError, match=message):
        StrategyEventResolutionCostRiskScoreV10Input(**kwargs)


def test_resolution_cost_risk_outputs_are_frozen_and_consistent() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.risk_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="risk_status"):
        replace(report, risk_status="blocked")
    with pytest.raises(ValueError, match="cost_drag_bps"):
        replace(report, cost_drag_bps=Decimal("1.000000"))
    with pytest.raises(ValueError, match="resolution_cost_risk_score"):
        replace(report, resolution_cost_risk_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="required_followups"):
        replace(report, required_followups=("review_fee_drag",))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=["resolution_cost_risk_clear"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_resolution_cost_risk_rejects_subclasses() -> None:
    input_row = StrategyEventResolutionCostRiskScoreV10Input(
        market_id="event-1",
        fee_drag_bps=Decimal("0"),
        expected_slippage_bps=Decimal("0"),
        dispute_ambiguity_score=Decimal("0"),
        settlement_delay_hours=Decimal("0"),
        resolution_source_confidence=Decimal("1"),
    )
    report = _report()

    with pytest.raises(ValueError, match="input"):
        StrategyEventResolutionCostRiskScoreV10InputSubclass(**input_row.__dict__)
    with pytest.raises(ValueError, match="report"):
        StrategyEventResolutionCostRiskScoreV10ReportSubclass(**report.__dict__)


def test_resolution_cost_risk_module_scope_stays_pure_readonly() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "typing",
    }

    lowered = source.lower()
    for banned_term in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "psycopg",
        "sqlite",
        "supabase",
        "private_key",
        "wallet",
        "auth",
        "clob",
        "gamma",
        "order placement",
        "open(",
    ):
        assert banned_term not in lowered
