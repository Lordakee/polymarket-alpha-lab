from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_multi_team_signal_arbitration_v4.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_multi_team_signal_arbitration_v4",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    team_id: str,
    *,
    condition_id: str = "condition-alpha",
    signal_side: str = "yes",
    probability: Decimal = d("0.640000"),
    confidence: Decimal = d("0.850000"),
    source_quality: Decimal = d("0.800000"),
    resolution_risk: Decimal = d("0.100000"),
):
    module = api()
    return module.StrategyMultiTeamSignalArbitrationV4Signal(
        condition_id=condition_id,
        team_id=team_id,
        signal_side=signal_side,
        probability=probability,
        confidence=confidence,
        source_quality=source_quality,
        resolution_risk=resolution_risk,
        source_reference="public-team-signal",
    )


def report(*signals: object, config: object | None = None):
    module = api()
    return module.build_strategy_multi_team_signal_arbitration_v4(
        signals,
        config=config or module.StrategyMultiTeamSignalArbitrationV4Config(),
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_arbitrates_multiple_professional_team_signals_for_same_market() -> None:
    digest = report(
        signal(
            "macro-policy",
            signal_side="yes",
            probability=d("0.640000"),
            confidence=d("0.850000"),
            source_quality=d("0.800000"),
            resolution_risk=d("0.100000"),
        ),
        signal(
            "crypto-market-structure",
            signal_side="yes",
            probability=d("0.680000"),
            confidence=d("0.900000"),
            source_quality=d("0.800000"),
            resolution_risk=d("0.150000"),
        ),
        signal(
            "resolution-risk",
            signal_side="no",
            probability=d("0.560000"),
            confidence=d("0.700000"),
            source_quality=d("0.700000"),
            resolution_risk=d("0.200000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.status == "accepted"
    assert digest.condition_count == d("1")
    assert digest.input_count == d("3")
    assert digest.reason_codes == ("arbitration_accepted",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.rows[0]
    assert row.condition_id == "condition-alpha"
    assert row.arbitration_status == "accepted"
    assert row.winning_side == "yes"
    assert row.team_count == d("3")
    assert row.winning_side_team_count == d("2")
    assert row.winning_side_weight_share == d("0.757426")
    assert row.consensus_probability == d("0.660000")
    assert row.average_confidence == d("0.816667")
    assert row.average_source_quality == d("0.766667")
    assert row.average_resolution_risk == d("0.150000")
    assert row.reason_codes == (
        "side_consensus_yes",
        "source_quality_supported",
        "resolution_risk_clear",
        "arbitration_accepted",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_blocks_split_low_quality_high_resolution_risk_market() -> None:
    digest = report(
        signal(
            "macro-policy",
            signal_side="yes",
            probability=d("0.520000"),
            confidence=d("0.700000"),
            source_quality=d("0.450000"),
            resolution_risk=d("0.400000"),
        ),
        signal(
            "resolution-risk",
            signal_side="no",
            probability=d("0.530000"),
            confidence=d("0.700000"),
            source_quality=d("0.440000"),
            resolution_risk=d("0.450000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.condition_count == d("1")
    assert digest.reason_codes == (
        "side_split",
        "source_quality_low",
        "resolution_risk_high",
        "arbitration_blocked",
    )

    row = digest.rows[0]
    assert row.arbitration_status == "blocked"
    assert row.winning_side == "none"
    assert row.consensus_probability == d("0.525000")
    assert row.winning_side_weight_share == d("0.527344")
    assert row.average_source_quality == d("0.445000")
    assert row.average_resolution_risk == d("0.425000")
    assert row.reason_codes == (
        "side_split",
        "source_quality_low",
        "resolution_risk_high",
        "arbitration_blocked",
    )


def test_empty_input_returns_readonly_decimal_report() -> None:
    digest = report()

    assert digest.status == "empty"
    assert digest.condition_count == d("0")
    assert digest.input_count == d("0")
    assert digest.rows == ()
    assert digest.reason_codes == ("multi_team_signal_arbitration_v4_empty",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_dataclasses_are_frozen_and_reject_float_or_subclassed_decimals() -> None:
    module = api()
    good_signal = signal("macro-policy")

    with pytest.raises(FrozenInstanceError):
        good_signal.confidence = d("0.900000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability must be a Decimal"):
        signal("macro-policy", probability=0.640000)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="confidence must be a Decimal"):
        signal("macro-policy", confidence=_DecimalSubclass("0.850000"))

    with pytest.raises(ValueError, match="config must be a StrategyMultiTeamSignalArbitrationV4Config"):
        module.build_strategy_multi_team_signal_arbitration_v4(
            (good_signal,),
            config=object(),
        )


def test_payload_is_json_ready_without_float_values() -> None:
    module = api()
    digest = report(signal("macro-policy"), signal("resolution-risk", signal_side="no"))

    payload = module.strategy_multi_team_signal_arbitration_v4_payload(digest)

    assert payload["input_count"] == "2"
    assert payload["rows"][0]["consensus_probability"] == "0.640000"
    assert payload["rows"][0]["paper_only"] is True
    assert_no_float_values(payload)


def test_module_scope_stays_paper_report_readonly_without_external_io_or_floats() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "get",
        "post",
        "place_order",
        "submit_order",
        "cancel_order",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.partition(".")[0] for alias in node.names}
            assert imported.isdisjoint(forbidden_imports)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.partition(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
        elif isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
