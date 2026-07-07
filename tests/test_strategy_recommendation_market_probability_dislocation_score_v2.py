from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = (
    "polymarket_alpha_lab."
    "strategy_recommendation_market_probability_dislocation_score_v2"
)
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_market_probability_dislocation_score_v2.py"
)
CONFIG_VERSION = "market-probability-dislocation-score-v2-test"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "target_probability_dislocation": d("0.100000"),
        "market_move_speed_watch": d("0.050000"),
        "market_move_speed_block": d("0.100000"),
        "liquidity_depth_ratio_watch": d("3.000000"),
        "liquidity_depth_ratio_block": d("1.000000"),
        "bid_ask_spread_watch": d("0.030000"),
        "bid_ask_spread_block": d("0.060000"),
        "source_age_watch_seconds": d("1800.000000"),
        "source_age_block_seconds": d("3600.000000"),
        "contradiction_severity_watch": d("0.200000"),
        "contradiction_severity_block": d("0.400000"),
        "cost_drag_watch": d("0.020000"),
        "cost_drag_block": d("0.050000"),
        "min_quality_score": d("0.700000"),
        "watch_quality_score": d("0.500000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarketProbabilityDislocationScoreV2Config(
        **values,
    )


def candidate(candidate_id: str = "candidate-strong", **overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": candidate_id,
        "market_id": "market-alpha",
        "market_slug": "event-alpha",
        "recommendation_side": "yes",
        "model_probability": d("0.650000"),
        "market_price": d("0.520000"),
        "market_move_speed": d("0.020000"),
        "liquidity_depth": d("300.000000"),
        "bid_ask_spread": d("0.010000"),
        "source_observed_at": GENERATED_AT - timedelta(seconds=900),
        "contradiction_severity": d("0.100000"),
        "cost_drag": d("0.010000"),
        "paper_notional": d("100.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "reason_codes": ("research_signal_available",),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarketProbabilityDislocationScoreV2Input(
        **values,
    )


def build_report(
    *items: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return (
        module.build_strategy_recommendation_market_probability_dislocation_score_v2_report(
            items,
            config=cfg or config(),
            generated_at=generated_at,
        )
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


def test_dislocation_quality_scores_model_market_gap_liquidity_freshness_and_costs() -> None:
    result = build_report(candidate())

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.candidate_count == d("1.000000")
    assert result.qualified_count == d("1.000000")
    assert result.watch_count == ZERO
    assert result.blocked_count == ZERO
    assert result.status == "qualified"
    assert result.reason_codes == (
        "market_probability_dislocation_qualified",
        "positive_net_probability_dislocation",
        "market_move_speed_stable",
        "liquidity_depth_sufficient",
        "spread_quality_passed",
        "source_freshness_passed",
        "contradiction_severity_low",
        "cost_drag_passed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    row = result.rows[0]
    assert row.candidate_id == "candidate-strong"
    assert row.market_id == "market-alpha"
    assert row.market_slug == "event-alpha"
    assert row.recommendation_side == "yes"
    assert row.raw_probability_dislocation == d("0.130000")
    assert row.net_probability_dislocation == d("0.110000")
    assert row.probability_dislocation_score == d("1.000000")
    assert row.market_movement_stability_score == d("0.800000")
    assert row.liquidity_depth_ratio == d("3.000000")
    assert row.liquidity_depth_score == d("1.000000")
    assert row.spread_quality_score == d("0.833333")
    assert row.source_freshness_age_seconds == d("900.000000")
    assert row.source_freshness_score == d("0.750000")
    assert row.contradiction_quality_score == d("0.750000")
    assert row.cost_drag_score == d("0.800000")
    assert row.dislocation_quality_score == d("0.847619")
    assert row.quality_status == "qualified"
    assert row.reason_codes == (
        "market_probability_dislocation_qualified",
        "positive_net_probability_dislocation",
        "market_move_speed_stable",
        "liquidity_depth_sufficient",
        "spread_quality_passed",
        "source_freshness_passed",
        "contradiction_severity_low",
        "cost_drag_passed",
    )
    assert row.derived_validation_digest
    assert result.derived_validation_digest

    payload = (
        api().strategy_recommendation_market_probability_dislocation_score_v2_payload(
            result,
        )
    )
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["dislocation_quality_score"] == "0.847619"
    assert payload["rows"][0]["derived_validation_digest"] == row.derived_validation_digest
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_float_values(payload)


def test_watch_and_blocked_reasons_are_deterministic_and_rows_ranked_by_quality() -> None:
    result = build_report(
        candidate(),
        candidate(
            "candidate-watch",
            model_probability=d("0.660000"),
            market_price=d("0.520000"),
            market_move_speed=d("0.055000"),
            liquidity_depth=d("250.000000"),
            bid_ask_spread=d("0.031000"),
            source_observed_at=GENERATED_AT - timedelta(seconds=1900),
            contradiction_severity=d("0.210000"),
            cost_drag=d("0.021000"),
        ),
        candidate(
            "candidate-blocked",
            model_probability=d("0.580000"),
            market_price=d("0.540000"),
            market_move_speed=d("0.120000"),
            liquidity_depth=d("50.000000"),
            bid_ask_spread=d("0.070000"),
            source_observed_at=GENERATED_AT - timedelta(seconds=4000),
            contradiction_severity=d("0.450000"),
            cost_drag=d("0.060000"),
        ),
    )

    assert result.status == "blocked"
    assert result.qualified_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.reason_codes == (
        "market_probability_dislocation_blocked",
        "market_probability_dislocation_watch",
        "market_probability_dislocation_qualified",
        "nonpositive_net_probability_dislocation",
        "positive_net_probability_dislocation",
        "market_move_speed_blocked",
        "liquidity_depth_blocked",
        "spread_quality_blocked",
        "source_freshness_blocked",
        "contradiction_severity_blocked",
        "cost_drag_blocked",
        "market_move_speed_watch",
        "liquidity_depth_watch",
        "spread_quality_watch",
        "source_freshness_watch",
        "contradiction_severity_watch",
        "cost_drag_watch",
        "market_move_speed_stable",
        "liquidity_depth_sufficient",
        "spread_quality_passed",
        "source_freshness_passed",
        "contradiction_severity_low",
        "cost_drag_passed",
    )
    assert tuple(row.candidate_id for row in result.rows) == (
        "candidate-strong",
        "candidate-watch",
        "candidate-blocked",
    )

    watched = result.rows[1]
    assert watched.quality_status == "watch"
    assert watched.raw_probability_dislocation == d("0.140000")
    assert watched.net_probability_dislocation == d("0.088000")
    assert watched.probability_dislocation_score == d("0.880000")
    assert watched.market_movement_stability_score == d("0.450000")
    assert watched.liquidity_depth_ratio == d("2.500000")
    assert watched.liquidity_depth_score == d("0.833333")
    assert watched.spread_quality_score == d("0.483333")
    assert watched.source_freshness_age_seconds == d("1900.000000")
    assert watched.source_freshness_score == d("0.472222")
    assert watched.contradiction_quality_score == d("0.475000")
    assert watched.cost_drag_score == d("0.580000")
    assert watched.dislocation_quality_score == d("0.596270")
    assert watched.reason_codes == (
        "market_probability_dislocation_watch",
        "positive_net_probability_dislocation",
        "market_move_speed_watch",
        "liquidity_depth_watch",
        "spread_quality_watch",
        "source_freshness_watch",
        "contradiction_severity_watch",
        "cost_drag_watch",
    )

    blocked = result.rows[2]
    assert blocked.quality_status == "blocked"
    assert blocked.net_probability_dislocation == d("-0.090000")
    assert blocked.probability_dislocation_score == ZERO
    assert blocked.market_movement_stability_score == ZERO
    assert blocked.liquidity_depth_ratio == d("0.500000")
    assert blocked.liquidity_depth_score == d("0.166667")
    assert blocked.dislocation_quality_score == d("0.023810")
    assert blocked.reason_codes == (
        "market_probability_dislocation_blocked",
        "nonpositive_net_probability_dislocation",
        "market_move_speed_blocked",
        "liquidity_depth_blocked",
        "spread_quality_blocked",
        "source_freshness_blocked",
        "contradiction_severity_blocked",
        "cost_drag_blocked",
    )


def test_empty_report_is_blocked_and_decimal_zeroed() -> None:
    result = build_report()

    assert result.candidate_count == ZERO
    assert result.qualified_count == ZERO
    assert result.watch_count == ZERO
    assert result.blocked_count == ZERO
    assert result.status == "blocked"
    assert result.reason_codes == ("market_probability_dislocation_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_frozen_dataclasses_decimal_only_flags_and_validation() -> None:
    module = api()
    result = build_report(candidate())

    assert is_dataclass(
        module.StrategyRecommendationMarketProbabilityDislocationScoreV2Config,
    )
    assert is_dataclass(
        module.StrategyRecommendationMarketProbabilityDislocationScoreV2Input,
    )
    assert is_dataclass(
        module.StrategyRecommendationMarketProbabilityDislocationScoreV2Row,
    )
    assert is_dataclass(
        module.StrategyRecommendationMarketProbabilityDislocationScoreV2Report,
    )
    with pytest.raises(FrozenInstanceError):
        result.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].dislocation_quality_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        candidate(readonly=False)
    with pytest.raises(ValueError, match="model_probability"):
        candidate(model_probability=0.65)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_price"):
        candidate(market_price=_DecimalSubclass("0.520000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 7, 11, 55, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(candidate(), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="source_observed_at"):
        build_report(
            candidate(
                "future-source",
                source_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_report(
            candidate("future-observed", observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_report(candidate(), candidate())
    with pytest.raises(ValueError, match="tuple"):
        candidate(reason_codes=["research_signal_available"])
    with pytest.raises(ValueError, match="unsafe"):
        candidate(candidate_id="wallet_candidate")
    with pytest.raises(ValueError, match="less than or equal"):
        config(market_move_speed_watch=d("0.200000"))
    with pytest.raises(ValueError, match="must not exceed"):
        config(liquidity_depth_ratio_block=d("4.000000"))

    for value in (result, *result.rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            if isinstance(item_value, tuple):
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_price",
                    "_speed",
                    "_depth",
                    "_spread",
                    "_severity",
                    "_drag",
                    "_notional",
                    "_dislocation",
                    "_score",
                    "_ratio",
                    "_seconds",
                ),
            ):
                assert type(item_value) is Decimal, item.name


def test_payload_revalidates_digest_flags_and_rejects_raw_numeric_or_unsafe_payloads() -> None:
    module = api()
    payload = (
        module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
            build_report(candidate()),
        )
    )

    assert (
        module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
            payload,
        )
        == payload
    )

    tampered_count = {**payload, "candidate_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
            tampered_count,
        )

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["dislocation_quality_score"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
            tampered_row,
        )

    downgraded = {**payload, "readonly": False}
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
            downgraded,
        )

    decimal_drift = {**payload, "candidate_count": d("1.000000")}
    with pytest.raises(ValueError, match="Decimal|string|JSON"):
        module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
            decimal_drift,
        )

    for term in (
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        unsafe_key = {**payload, f"{term}_reference": "paper"}
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
                unsafe_key,
            )

        unsafe_value = {**payload, "status": f"{term}_mode"}
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_recommendation_market_probability_dislocation_score_v2_payload(
                unsafe_value,
            )


def test_module_scope_has_no_io_mutation_or_external_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "submit",
        "post",
        "send",
        "login",
        "execute",
        "commit",
        "rollback",
        "write",
    }
    banned_attributes = banned_calls | {"session"}
    forbidden_terms = (
        "live trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "database",
        "network",
        "private_key",
        "supabase",
        "sqlite",
        "requests.",
        "urllib",
        "open(",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    assert [term for term in forbidden_terms if term in lowered] == []
