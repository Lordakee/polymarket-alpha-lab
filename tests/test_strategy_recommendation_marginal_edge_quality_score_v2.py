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
    / "strategy_recommendation_marginal_edge_quality_score_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 14, 45, tzinfo=UTC)
CONFIG_VERSION = "marginal-edge-quality-score-v2-test"
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_marginal_edge_quality_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "target_marginal_edge": d("0.100000"),
        "min_quality_score": d("0.700000"),
        "watch_quality_score": d("0.500000"),
        "max_fee_drag": d("0.100000"),
        "max_spread": d("0.100000"),
        "confidence_boost_multiplier": d("0.100000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarginalEdgeQualityScoreV2Config(**values)


def candidate(candidate_id: str = "candidate-alpha", **overrides: object):
    module = api()
    values = {
        "candidate_id": candidate_id,
        "market_slug": "event-alpha",
        "recommendation_side": "yes",
        "forecast_probability": d("0.620000"),
        "implied_probability": d("0.500000"),
        "confidence": d("0.800000"),
        "fee_drag": d("0.020000"),
        "spread": d("0.030000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("source_signal_available",),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarginalEdgeQualityScoreV2Input(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_recommendation_marginal_edge_quality_score_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_marginal_edge_quality_scoring_uses_net_edge_costs_and_confidence() -> None:
    report = build_report(candidate())

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.candidate_count == d("1.000000")
    assert report.qualified_count == d("1.000000")
    assert report.watch_count == ZERO
    assert report.blocked_count == ZERO
    assert report.status == "qualified"
    assert report.reason_codes == ("marginal_edge_quality_qualified",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.candidate_id == "candidate-alpha"
    assert row.market_slug == "event-alpha"
    assert row.raw_marginal_edge == d("0.120000")
    assert row.net_marginal_edge == d("0.070000")
    assert row.edge_quality_score == d("0.700000")
    assert row.fee_spread_damping_score == d("0.750000")
    assert row.confidence_boost_score == d("0.870000")
    assert row.marginal_edge_quality_score == d("0.761000")
    assert row.quality_status == "qualified"
    assert row.reason_codes == (
        "marginal_edge_quality_qualified",
        "positive_net_marginal_edge",
        "fee_spread_damping_passed",
        "confidence_boost_applied",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_fee_and_spread_damping_pushes_thin_edges_to_watch_or_blocked() -> None:
    watched = build_report(
        candidate("candidate-watch", fee_drag=d("0.040000"), spread=d("0.040000")),
    ).rows[0]
    assert watched.net_marginal_edge == d("0.040000")
    assert watched.edge_quality_score == d("0.400000")
    assert watched.fee_spread_damping_score == d("0.600000")
    assert watched.confidence_boost_score == d("0.840000")
    assert watched.marginal_edge_quality_score == d("0.572000")
    assert watched.quality_status == "watch"
    assert "marginal_edge_quality_watch" in watched.reason_codes

    blocked = build_report(
        candidate("candidate-blocked", fee_drag=d("0.060000"), spread=d("0.070000")),
    ).rows[0]
    assert blocked.net_marginal_edge == d("-0.010000")
    assert blocked.edge_quality_score == ZERO
    assert blocked.fee_spread_damping_score == d("0.350000")
    assert blocked.marginal_edge_quality_score == d("0.310000")
    assert blocked.quality_status == "blocked"
    assert "nonpositive_net_marginal_edge" in blocked.reason_codes
    assert "fee_spread_damping_watch" in blocked.reason_codes


def test_confidence_boost_can_lift_borderline_quality_above_threshold() -> None:
    boosted = build_report(candidate(confidence=d("0.600000"))).rows[0]
    unboosted = build_report(
        candidate(confidence=d("0.600000")),
        cfg=config(confidence_boost_multiplier=ZERO),
    ).rows[0]

    assert boosted.confidence_boost_score == d("0.670000")
    assert boosted.marginal_edge_quality_score == d("0.701000")
    assert boosted.quality_status == "qualified"
    assert "confidence_boost_applied" in boosted.reason_codes
    assert unboosted.confidence_boost_score == d("0.600000")
    assert unboosted.marginal_edge_quality_score == d("0.680000")
    assert unboosted.quality_status == "watch"
    assert "confidence_boost_not_applied" in unboosted.reason_codes


def test_payload_serializes_decimals_as_strings_and_round_trips_json_payload() -> None:
    module = api()
    report = build_report(candidate(), candidate("candidate-watch", spread=d("0.080000")))
    payload = module.strategy_recommendation_marginal_edge_quality_score_v2_payload(report)

    assert payload["candidate_count"] == "2.000000"
    assert payload["qualified_count"] == "1.000000"
    assert payload["rows"][0]["marginal_edge_quality_score"] == "0.761000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.strategy_recommendation_marginal_edge_quality_score_v2_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)


def test_frozen_dataclasses_decimal_only_values_and_hard_flags() -> None:
    module = api()
    report = build_report(candidate())

    assert is_dataclass(module.StrategyRecommendationMarginalEdgeQualityScoreV2Config)
    assert is_dataclass(module.StrategyRecommendationMarginalEdgeQualityScoreV2Input)
    assert is_dataclass(module.StrategyRecommendationMarginalEdgeQualityScoreV2Row)
    assert is_dataclass(module.StrategyRecommendationMarginalEdgeQualityScoreV2Report)
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].marginal_edge_quality_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)
    with pytest.raises(ValueError, match="confidence"):
        candidate(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=_DecimalSubclass("0.620000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(candidate(), generated_at=datetime(2026, 7, 6, 15, 0))
    with pytest.raises(ValueError, match="unsafe"):
        candidate(candidate_id="wallet_candidate")
    with pytest.raises(ValueError, match="duplicate"):
        build_report(candidate(), candidate())
    with pytest.raises(ValueError, match="ordered"):
        candidate(reason_codes={"alpha_reason", "beta_reason"})

    for value in (report, *report.rows):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_drag",
                    "_spread",
                    "_edge",
                    "_score",
                ),
            ):
                assert type(item_value) is Decimal


def test_digest_tampering_and_unsafe_public_payloads_are_rejected() -> None:
    module = api()
    payload = module.strategy_recommendation_marginal_edge_quality_score_v2_payload(
        build_report(candidate()),
    )

    tampered_count = {**payload, "candidate_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_marginal_edge_quality_score_v2_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["marginal_edge_quality_score"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_marginal_edge_quality_score_v2_payload(tampered_row)

    downgraded = {**payload, "paper_only": False}
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_recommendation_marginal_edge_quality_score_v2_payload(downgraded)

    terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in terms:
        unsafe_key = {**payload, f"{term}_reference": "paper"}
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_recommendation_marginal_edge_quality_score_v2_payload(unsafe_key)

        unsafe_value = {**payload, "status": f"{term}_mode"}
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_recommendation_marginal_edge_quality_score_v2_payload(unsafe_value)

    decimal_drift = {**payload, "candidate_count": d("1.000000")}
    with pytest.raises(ValueError, match="Decimal|string|JSON"):
        module.strategy_recommendation_marginal_edge_quality_score_v2_payload(decimal_drift)


def test_module_has_no_unsafe_execution_or_stateful_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "live",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_public_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            lowered = node.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_terms)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
