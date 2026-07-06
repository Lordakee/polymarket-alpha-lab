from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_signal_stability_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 16, 45, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_signal_stability_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "recommendation_id": "candidate-pass",
        "market_slug": "polymarket-event-alpha",
        "outcome_name": "yes",
        "source_verified_edge_start": d("0.120000"),
        "source_verified_edge_current": d("0.130000"),
        "market_probability_start": d("0.500000"),
        "market_probability_current": d("0.500000"),
        "uncertainty_band_start": d("0.050000"),
        "uncertainty_band_current": d("0.040000"),
        "specialist_confidence_start": d("0.850000"),
        "specialist_confidence_current": d("0.900000"),
        "liquidity_exit_risk_start": d("0.150000"),
        "liquidity_exit_risk_current": d("0.100000"),
        "resolution_ambiguity_start": d("0.120000"),
        "resolution_ambiguity_current": d("0.100000"),
        "portfolio_impact_start": d("0.100000"),
        "portfolio_impact_current": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationSignalStabilityGateV2Observation(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            observation(recommendation_id="candidate-pass"),
            observation(
                recommendation_id="candidate-watch",
                market_probability_current=d("0.575000"),
            ),
            observation(
                recommendation_id="candidate-blocked",
                source_verified_edge_current=d("0.050000"),
            ),
        )
    return module.build_strategy_recommendation_signal_stability_gate_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_decimal_int_or_float_payload_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_int_or_float_payload_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_decimal_int_or_float_payload_values(item)


def test_builds_recommendation_signal_stability_report_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.gate_status == "blocked"
    assert report.final_recommendation_blocked is True
    assert report.recommendation_count == d("3")
    assert report.pass_recommendation_count == d("1")
    assert report.watch_recommendation_count == d("1")
    assert report.blocked_recommendation_count == d("1")
    assert report.average_stability_score == d("0.908333")
    assert report.reason_codes == (
        "signal_stability_gate_watch_rows",
        "signal_stability_gate_blocked_rows",
    )

    assert tuple(row.recommendation_id for row in report.rows) == (
        "candidate-blocked",
        "candidate-watch",
        "candidate-pass",
    )
    assert tuple(row.validation_status for row in report.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert tuple(row.stability_score for row in report.rows) == (
        d("0.800000"),
        d("0.925000"),
        d("1.000000"),
    )
    assert report.rows[0].source_verified_edge_trend == d("-0.070000")
    assert report.rows[1].market_probability_movement == d("0.075000")
    assert "source_verified_edge_trend_weak" in report.rows[0].reason_codes
    assert "market_probability_movement_watch" in report.rows[1].reason_codes

    payload = report.payload
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["recommendation_count"] == "3"
    assert payload["average_stability_score"] == "0.908333"
    assert payload["generated_at"] == "2026-07-06T16:45:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_verified_edge_trend"] == "-0.070000"
    assert payload["rows"][1]["market_probability_movement"] == "0.075000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert "Decimal" not in rendered
    assert_no_decimal_int_or_float_payload_values(payload)


def test_empty_report_is_digest_backed_report_only_and_blocking() -> None:
    report = build_report(
        *(),
        generated_at=GENERATED_AT,
        use_default_items=False,
    )

    assert report.gate_status == "blocked"
    assert report.final_recommendation_blocked is True
    assert report.recommendation_count == d("0")
    assert report.average_stability_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("signal_stability_gate_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyRecommendationSignalStabilityGateV2Config()
    item = observation()
    report = build_report(item)
    row = report.rows[0]

    for obj in (config, item, row, report):
        assert obj.paper_only is True
        assert obj.report_only is True
        assert obj.readonly is True
        with pytest.raises(FrozenInstanceError):
            obj.paper_only = False  # type: ignore[misc]
        for field in fields(obj):
            value = getattr(obj, field.name)
            if field.name.endswith(
                (
                    "_score",
                    "_floor",
                    "_weight",
                    "_movement",
                    "_drift",
                    "_trend",
                    "_count",
                    "_start",
                    "_current",
                ),
            ):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="source_verified_edge_start must be exactly Decimal"):
        observation(source_verified_edge_start=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="market_probability_current must be exactly Decimal"):
        observation(market_probability_current=0)
    with pytest.raises(ValueError, match="market_probability_current must be <= 1.000000"):
        observation(market_probability_current=d("1.000001"))
    with pytest.raises(
        ValueError,
        match="uncertainty_band_current must use six decimal places or fewer",
    ):
        observation(uncertainty_band_current=d("0.0400004"))
    with pytest.raises(ValueError, match="portfolio_impact_current must be finite"):
        observation(portfolio_impact_current=Decimal("NaN"))
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)


def test_config_and_build_validation_reject_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="pass_stability_floor must be exactly Decimal"):
        module.StrategyRecommendationSignalStabilityGateV2Config(
            pass_stability_floor=0,
        )
    with pytest.raises(ValueError, match="watch_stability_floor must not exceed pass_stability_floor"):
        module.StrategyRecommendationSignalStabilityGateV2Config(
            watch_stability_floor=d("0.960000"),
        )
    with pytest.raises(ValueError, match="stability weights must sum to 1.000000"):
        module.StrategyRecommendationSignalStabilityGateV2Config(
            source_verified_edge_trend_weight=d("0.100000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyRecommendationSignalStabilityGateV2Config(paper_only=False)
    with pytest.raises(ValueError, match="observations must be an iterable"):
        module.build_strategy_recommendation_signal_stability_gate_v2(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="observation items must be StrategyRecommendationSignalStabilityGateV2Observation",
    ):
        module.build_strategy_recommendation_signal_stability_gate_v2(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate recommendation_id and market_slug"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_recommendation_signal_stability_gate_v2(
            [observation()],
            generated_at=datetime(2026, 7, 6),
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_stability_score=d("0.800000"))

    restored = module.StrategyRecommendationSignalStabilityGateV2Report.from_payload(
        report.payload,
    )
    assert restored == report

    tampered = dict(report.payload)
    tampered["average_stability_score"] = "0.800000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.StrategyRecommendationSignalStabilityGateV2Report.from_payload(tampered)


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live candidate",
        "auth candidate",
        "wallet candidate",
        "order candidate",
        "network candidate",
        "database candidate",
        "persist candidate",
        "signing candidate",
        "mutation candidate",
        "buy candidate",
        "sell candidate",
        "trade candidate",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            observation(market_slug=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade_signal",))


def test_module_scope_has_no_file_database_network_or_action_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    assert module.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_SIGNAL_STABILITY_GATE_V2_CONFIG_VERSION",
        "StrategyRecommendationSignalStabilityGateV2Config",
        "StrategyRecommendationSignalStabilityGateV2Observation",
        "StrategyRecommendationSignalStabilityGateV2Row",
        "StrategyRecommendationSignalStabilityGateV2Report",
        "build_strategy_recommendation_signal_stability_gate_v2",
        "strategy_recommendation_signal_stability_gate_v2_payload",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_roots = {
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "float",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(imported.split(".", 1)[0] in forbidden_import_roots for imported in imports)
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_decimal_int_or_float_payload_values([imports, call_names, attribute_names])
