import ast
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_candidate_information_edge_decay_v10 import (
    StrategyCandidateInformationEdgeDecayV10Input,
    StrategyCandidateInformationEdgeDecayV10Result,
    evaluate_strategy_candidate_information_edge_decay_v10,
    strategy_candidate_information_edge_decay_v10_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_information_edge_decay_v10.py"
)


def _input(**overrides):
    values = {
        "market_id": "nba-finals-game-7",
        "signal_age_minutes": Decimal("0.000000"),
        "probability_move_bps": Decimal("0.000000"),
        "spread_widening_bps": Decimal("0.000000"),
        "source_freshness_score": Decimal("1.000000"),
        "crowding_pressure_score": Decimal("0.000000"),
    }
    values.update(overrides)
    return StrategyCandidateInformationEdgeDecayV10Input(**values)


def test_fresh_candidate_information_edge_stays_in_screening_queue():
    result = evaluate_strategy_candidate_information_edge_decay_v10(_input())

    assert result.market_id == "nba-finals-game-7"
    assert result.decay_score == Decimal("0.000000")
    assert result.edge_decay_status == "fresh"
    assert result.screening_action == "continue_screening"
    assert result.reason_codes == ("candidate_information_edge_fresh",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_decaying_edge_score_combines_age_move_spread_freshness_and_crowding():
    result = evaluate_strategy_candidate_information_edge_decay_v10(
        _input(
            signal_age_minutes=Decimal("720.000000"),
            probability_move_bps=Decimal("150.000000"),
            spread_widening_bps=Decimal("50.000000"),
            source_freshness_score=Decimal("0.500000"),
            crowding_pressure_score=Decimal("0.500000"),
        ),
    )

    assert result.decay_score == Decimal("0.500000")
    assert result.edge_decay_status == "decaying"
    assert result.screening_action == "refresh_edge_before_screening"
    assert result.reason_codes == (
        "candidate_information_edge_decaying",
        "signal_age_stale",
        "probability_move_watch",
        "spread_widening_watch",
        "source_freshness_watch",
        "crowding_pressure_watch",
    )


def test_expired_edge_blocks_candidate_until_fresh_signal():
    result = evaluate_strategy_candidate_information_edge_decay_v10(
        _input(
            signal_age_minutes=Decimal("1440.000000"),
            probability_move_bps=Decimal("300.000000"),
            spread_widening_bps=Decimal("100.000000"),
            source_freshness_score=Decimal("0.000000"),
            crowding_pressure_score=Decimal("1.000000"),
        ),
    )

    assert result.decay_score == Decimal("1.000000")
    assert result.edge_decay_status == "expired"
    assert result.screening_action == "reject_candidate_until_fresh_signal"
    assert result.reason_codes == (
        "candidate_information_edge_expired",
        "signal_age_stale",
        "probability_move_material",
        "spread_widening_material",
        "source_freshness_low",
        "crowding_pressure_high",
    )


def test_payload_serializes_decimals_as_strings_and_preserves_readonly_flags():
    result = evaluate_strategy_candidate_information_edge_decay_v10(
        _input(
            signal_age_minutes=Decimal("720"),
            probability_move_bps=Decimal("150"),
            spread_widening_bps=Decimal("50"),
            source_freshness_score=Decimal("0.5"),
            crowding_pressure_score=Decimal("0.5"),
        ),
    )

    payload = strategy_candidate_information_edge_decay_v10_payload(result)

    assert payload["signal_age_minutes"] == "720.000000"
    assert payload["probability_move_bps"] == "150.000000"
    assert payload["spread_widening_bps"] == "50.000000"
    assert payload["source_freshness_score"] == "0.500000"
    assert payload["crowding_pressure_score"] == "0.500000"
    assert payload["decay_score"] == "0.500000"
    assert payload["reason_codes"] == [
        "candidate_information_edge_decaying",
        "signal_age_stale",
        "probability_move_watch",
        "spread_widening_watch",
        "source_freshness_watch",
        "crowding_pressure_watch",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_dataclasses_are_frozen_and_reject_unsafe_inputs():
    result = evaluate_strategy_candidate_information_edge_decay_v10(_input())

    with pytest.raises(FrozenInstanceError):
        result.edge_decay_status = "expired"

    with pytest.raises(ValueError, match="probability_move_bps must be a Decimal"):
        _input(probability_move_bps=0.5)

    with pytest.raises(ValueError, match="source_freshness_score must be between"):
        _input(source_freshness_score=Decimal("1.000001"))

    with pytest.raises(ValueError, match="paper_only"):
        _input(paper_only=False)

    with pytest.raises(ValueError, match="screening_action must match edge_decay_status"):
        StrategyCandidateInformationEdgeDecayV10Result(
            market_id="nba-finals-game-7",
            signal_age_minutes=Decimal("0"),
            probability_move_bps=Decimal("0"),
            spread_widening_bps=Decimal("0"),
            source_freshness_score=Decimal("1"),
            crowding_pressure_score=Decimal("0"),
            decay_score=Decimal("0"),
            edge_decay_status="fresh",
            screening_action="reject_candidate_until_fresh_signal",
            reason_codes=("candidate_information_edge_fresh",),
        )


def test_result_rejects_tampered_decay_score_status_and_reason_codes():
    base_values = {
        "market_id": "nba-finals-game-7",
        "signal_age_minutes": Decimal("0"),
        "probability_move_bps": Decimal("0"),
        "spread_widening_bps": Decimal("0"),
        "source_freshness_score": Decimal("1"),
        "crowding_pressure_score": Decimal("0"),
        "decay_score": Decimal("0"),
        "edge_decay_status": "fresh",
        "screening_action": "continue_screening",
        "reason_codes": ("candidate_information_edge_fresh",),
    }

    with pytest.raises(ValueError, match="decay_score must match input metrics"):
        StrategyCandidateInformationEdgeDecayV10Result(
            **{
                **base_values,
                "decay_score": Decimal("0.999999"),
                "edge_decay_status": "expired",
                "screening_action": "reject_candidate_until_fresh_signal",
                "reason_codes": ("candidate_information_edge_expired",),
            },
        )

    with pytest.raises(ValueError, match="edge_decay_status must match decay_score"):
        StrategyCandidateInformationEdgeDecayV10Result(
            **{
                **base_values,
                "edge_decay_status": "watch",
                "screening_action": "monitor_edge_decay",
                "reason_codes": ("candidate_information_edge_watch",),
            },
        )

    with pytest.raises(ValueError, match="reason_codes must match"):
        StrategyCandidateInformationEdgeDecayV10Result(
            **{
                **base_values,
                "reason_codes": (
                    "candidate_information_edge_fresh",
                    "unsupported_reason_code",
                ),
            },
        )


def test_module_scope_is_pure_readonly_decimal_only_static_surface():
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_fragments = (
        "auth",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sqlite",
        "trade",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "connect",
        "get",
        "open",
        "post",
        "put",
        "read",
        "request",
        "send",
        "submit",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = ""
            if isinstance(node, ast.Import):
                module = ".".join(alias.name for alias in node.names)
            else:
                module = node.module or ""
            normalized = module.replace("_", "").lower()
            assert not any(fragment in normalized for fragment in forbidden_import_fragments)
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
