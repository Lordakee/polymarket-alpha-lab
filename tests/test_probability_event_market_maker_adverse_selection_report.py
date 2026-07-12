from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab import probability_event_market_maker_adverse_selection_report as module
from polymarket_alpha_lab.probability_event_market_maker_adverse_selection_report import (
    ProbabilityEventMarketMakerAdverseSelectionReport,
    build_probability_event_market_maker_adverse_selection_report,
)


ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventMarketMakerAdverseSelectionReport:
    values = {
        "spread_probability": d("0.010000"),
        "recent_price_move_probability": d("0.020000"),
        "depth_imbalance_probability": d("0.100000"),
        "source_freshness_age_hours": d("1.000000"),
        "forecast_age_hours": d("2.000000"),
    }
    values.update(overrides)
    return build_probability_event_market_maker_adverse_selection_report(**values)


def test_low_adverse_selection_inputs_pass_with_decimal_adjusted_edge() -> None:
    safe_report = report()

    assert type(safe_report) is ProbabilityEventMarketMakerAdverseSelectionReport
    assert safe_report.adverse_selection_status == "pass"
    assert safe_report.risk_adjusted_edge_probability == d("0.925417")
    assert safe_report.reason_codes == ("adverse_selection_pass",)
    assert safe_report.manual_next_step == "continue_public_research_review"
    assert safe_report.paper_only is True
    assert safe_report.report_only is True
    assert safe_report.readonly is True

    for item in fields(safe_report):
        item_value = getattr(safe_report, item.name)
        if item.name in {
            "adverse_selection_status",
            "reason_codes",
            "manual_next_step",
            "payload_digest",
            "paper_only",
            "report_only",
            "readonly",
        }:
            continue
        assert type(item_value) is Decimal


def test_watch_and_block_reasons_are_public_and_deterministic() -> None:
    watch_report = report(
        spread_probability=d("0.080000"),
        recent_price_move_probability=d("0.070000"),
        depth_imbalance_probability=d("0.350000"),
        source_freshness_age_hours=d("8.000000"),
        forecast_age_hours=d("14.000000"),
    )
    block_report = report(
        spread_probability=d("0.160000"),
        recent_price_move_probability=d("0.180000"),
        depth_imbalance_probability=d("0.750000"),
        source_freshness_age_hours=d("30.000000"),
        forecast_age_hours=d("60.000000"),
    )

    assert watch_report.adverse_selection_status == "watch"
    assert watch_report.risk_adjusted_edge_probability == d("0.649500")
    assert watch_report.reason_codes == (
        "adverse_selection_score_watch",
        "depth_imbalance_probability_watch",
        "forecast_age_watch",
        "recent_price_move_probability_watch",
        "source_freshness_age_watch",
        "spread_probability_watch",
    )
    assert watch_report.manual_next_step == "manual_review_market_maker_adverse_selection"

    assert block_report.adverse_selection_status == "block"
    assert block_report.risk_adjusted_edge_probability == ZERO
    assert block_report.reason_codes == (
        "adverse_selection_score_block",
        "depth_imbalance_probability_block",
        "forecast_age_block",
        "recent_price_move_probability_block",
        "source_freshness_age_block",
        "spread_probability_block",
    )
    assert block_report.manual_next_step == "pause_until_manual_adverse_selection_clearance"


def test_public_payload_serializes_decimal_strings_and_self_verifies_digest() -> None:
    first = report(
        spread_probability=d("0.080000"),
        recent_price_move_probability=d("0.070000"),
        depth_imbalance_probability=d("0.350000"),
        source_freshness_age_hours=d("8.000000"),
        forecast_age_hours=d("14.000000"),
    )
    second = report(
        spread_probability=d("0.080000"),
        recent_price_move_probability=d("0.070000"),
        depth_imbalance_probability=d("0.350000"),
        source_freshness_age_hours=d("8.000000"),
        forecast_age_hours=d("14.000000"),
    )

    payload = first.public_payload
    encoded = json.dumps(payload, separators=(",", ":"))

    assert payload == second.public_payload
    assert payload["spread_probability"] == "0.080000"
    assert payload["risk_adjusted_edge_probability"] == "0.649500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == first.payload_digest
    assert len(first.payload_digest) == 64
    assert payload["payload_digest"] == module.probability_event_market_maker_adverse_selection_payload_digest(payload)
    assert all(type(value) not in (int, float) for value in _walk_values(payload))
    assert "raw_market_id" not in encoded

    with pytest.raises(TypeError, match="immutable"):
        payload["spread_probability"] = "0.010000"

    tampered = dict(payload)
    tampered["risk_adjusted_edge_probability"] = "0.000000"
    with pytest.raises(ValueError, match="payload_digest"):
        module.probability_event_market_maker_adverse_selection_payload_digest(tampered)


def test_validation_rejects_non_decimal_bad_ranges_bad_flags_and_inconsistent_manual_rows() -> None:
    with pytest.raises(ValueError, match="spread_probability"):
        report(spread_probability=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recent_price_move_probability"):
        report(recent_price_move_probability=_DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="depth_imbalance_probability"):
        report(depth_imbalance_probability=d("1.000001"))
    with pytest.raises(ValueError, match="source_freshness_age_hours"):
        report(source_freshness_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report(), paper_only=False)
    with pytest.raises(ValueError, match="adverse_selection_status"):
        replace(report(), adverse_selection_status="watch")
    with pytest.raises(ValueError, match="risk_adjusted_edge_probability"):
        replace(report(), risk_adjusted_edge_probability=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report(), reason_codes=("adverse_selection_score_watch",))

    frozen = report()
    with pytest.raises(FrozenInstanceError):
        frozen.manual_next_step = "changed"  # type: ignore[misc]


def test_module_surface_is_readonly_phase1_and_has_no_durable_or_action_paths() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "probability_event_market_maker_adverse_selection_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        ".write(",
        "jsonl",
        "persist",
        "durable",
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret",
        "signature",
        "signing",
        "execute",
        "execution",
        "place_",
        "submit_",
        "cancel_",
    )
    assert all(term not in source for term in forbidden_terms)
    assert set(module.__all__) == {
        "ProbabilityEventMarketMakerAdverseSelectionPayload",
        "ProbabilityEventMarketMakerAdverseSelectionReport",
        "build_probability_event_market_maker_adverse_selection_report",
        "probability_event_market_maker_adverse_selection_payload_digest",
    }


def _walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, tuple):
        for item in value:
            values.extend(_walk_values(item))
    else:
        values.append(value)
    return tuple(values)
