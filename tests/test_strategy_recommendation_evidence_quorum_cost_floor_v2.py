from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.strategy_recommendation_evidence_quorum_cost_floor_v2"
)
CONFIG_VERSION = "strategy-recommendation-evidence-quorum-cost-floor-v2"
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
        "minimum_source_family_count": d("2.000000"),
        "required_source_family_count": d("3.000000"),
        "contradiction_severity_watch": d("0.200000"),
        "contradiction_severity_block": d("0.400000"),
        "taker_fee_rate_watch": d("0.010000"),
        "taker_fee_rate_block": d("0.020000"),
        "spread_cost_watch": d("0.030000"),
        "spread_cost_block": d("0.060000"),
        "slippage_cost_watch": d("0.020000"),
        "slippage_cost_block": d("0.030000"),
        "total_cost_watch": d("0.060000"),
        "total_cost_block": d("0.100000"),
        "edge_margin_watch": d("0.030000"),
        "edge_margin_block": d("0.000000"),
        "liquidity_depth_ratio_watch": d("2.000000"),
        "liquidity_depth_ratio_block": d("1.000000"),
        "close_urgency_watch_seconds": d("1800.000000"),
        "close_urgency_block_seconds": d("300.000000"),
        "minimum_recommendation_floor": d("0.700000"),
        "blocked_recommendation_floor": d("0.500000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationEvidenceQuorumCostFloorV2Config(**values)


def recommendation(recommendation_id: str = "candidate-alpha", **overrides: object) -> Any:
    module = api()
    values = {
        "recommendation_id": recommendation_id,
        "market_id": "market-alpha",
        "recommendation_side": "yes",
        "base_confidence": d("0.900000"),
        "source_family_count": d("3.000000"),
        "official_source_present": True,
        "contradiction_severity": d("0.050000"),
        "expected_edge": d("0.120000"),
        "taker_fee_rate": d("0.005000"),
        "spread_cost": d("0.010000"),
        "slippage_cost": d("0.005000"),
        "paper_notional": d("40.000000"),
        "liquidity_depth": d("120.000000"),
        "seconds_until_close": d("3600.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=15),
        "reason_codes": ("evidence_inputs_available",),
    }
    values.update(overrides)
    return module.StrategyRecommendationEvidenceQuorumCostFloorV2Input(**values)


def report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_recommendation_evidence_quorum_cost_floor_v2_report(
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


def test_pass_path_scores_evidence_quorum_cost_floor_and_payload() -> None:
    result = report(
        recommendation(
            recommendation_id="candidate-pass",
            market_id="market-pass",
            base_confidence=d("0.920000"),
            source_family_count=d("3.000000"),
            official_source_present=True,
            contradiction_severity=d("0.050000"),
            expected_edge=d("0.120000"),
            taker_fee_rate=d("0.005000"),
            spread_cost=d("0.010000"),
            slippage_cost=d("0.005000"),
            paper_notional=d("40.000000"),
            liquidity_depth=d("120.000000"),
            seconds_until_close=d("3600.000000"),
            reason_codes=("evidence_inputs_available", "source_catalogued"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.candidate_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == ZERO
    assert result.blocked_count == ZERO
    assert result.status == "pass"
    assert result.reason_codes == ("evidence_quorum_cost_floor_pass",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    row = result.rows[0]
    assert row.recommendation_id == "candidate-pass"
    assert row.market_id == "market-pass"
    assert row.recommendation_side == "yes"
    assert row.base_confidence == d("0.920000")
    assert row.source_family_score == d("1.000000")
    assert row.official_source_score == d("1.000000")
    assert row.contradiction_score == d("0.950000")
    assert row.total_cost == d("0.020000")
    assert row.cost_efficiency_score == d("0.800000")
    assert row.edge_margin == d("0.100000")
    assert row.edge_margin_score == d("1.000000")
    assert row.liquidity_depth_ratio == d("3.000000")
    assert row.liquidity_depth_score == d("1.000000")
    assert row.close_safety_score == d("1.000000")
    assert row.recommendation_floor == d("0.964286")
    assert row.floor_adjusted_confidence == d("0.920000")
    assert row.floor_status == "pass"
    assert row.reason_codes == (
        "evidence_quorum_cost_floor_pass",
        "evidence_inputs_available",
        "source_catalogued",
    )
    assert row.derived_validation_digest
    assert result.derived_validation_digest

    payload = api().strategy_recommendation_evidence_quorum_cost_floor_v2_payload(result)
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["recommendation_floor"] == "0.964286"
    assert payload["rows"][0]["derived_validation_digest"] == row.derived_validation_digest
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_float_values(payload)


def test_watch_and_blocked_reasons_are_deterministic_and_sorted_by_severity() -> None:
    result = report(
        recommendation(
            recommendation_id="candidate-watch",
            market_id="market-watch",
            base_confidence=d("0.750000"),
            source_family_count=d("2.000000"),
            contradiction_severity=d("0.250000"),
            expected_edge=d("0.090000"),
            taker_fee_rate=d("0.012000"),
            spread_cost=d("0.035000"),
            slippage_cost=d("0.023000"),
            paper_notional=d("100.000000"),
            liquidity_depth=d("150.000000"),
            seconds_until_close=d("1200.000000"),
        ),
        recommendation(
            recommendation_id="candidate-blocked",
            market_id="market-blocked",
            base_confidence=d("0.800000"),
            source_family_count=d("1.000000"),
            official_source_present=False,
            contradiction_severity=d("0.450000"),
            expected_edge=d("0.080000"),
            taker_fee_rate=d("0.025000"),
            spread_cost=d("0.070000"),
            slippage_cost=d("0.040000"),
            paper_notional=d("100.000000"),
            liquidity_depth=d("50.000000"),
            seconds_until_close=d("200.000000"),
        ),
    )

    assert result.status == "blocked"
    assert result.pass_count == ZERO
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.reason_codes == (
        "evidence_quorum_cost_floor_blocked",
        "evidence_quorum_cost_floor_watch",
        "source_family_count_blocked",
        "official_source_missing_blocked",
        "contradiction_severity_blocked",
        "taker_cost_blocked",
        "spread_cost_blocked",
        "slippage_cost_blocked",
        "total_cost_blocked",
        "edge_margin_blocked",
        "liquidity_depth_blocked",
        "close_urgency_blocked",
        "recommendation_floor_blocked",
        "source_family_count_watch",
        "contradiction_severity_watch",
        "taker_cost_watch",
        "spread_cost_watch",
        "slippage_cost_watch",
        "total_cost_watch",
        "edge_margin_watch",
        "liquidity_depth_watch",
        "close_urgency_watch",
        "recommendation_floor_watch",
    )
    assert tuple(row.recommendation_id for row in result.rows) == (
        "candidate-blocked",
        "candidate-watch",
    )

    blocked, watched = result.rows
    assert blocked.floor_status == "blocked"
    assert blocked.source_family_score == d("0.333333")
    assert blocked.official_source_score == ZERO
    assert blocked.total_cost == d("0.135000")
    assert blocked.edge_margin == d("-0.055000")
    assert blocked.cost_efficiency_score == ZERO
    assert blocked.edge_margin_score == ZERO
    assert blocked.liquidity_depth_ratio == d("0.500000")
    assert blocked.close_safety_score == d("0.111111")
    assert blocked.recommendation_floor == d("0.177778")
    assert blocked.floor_adjusted_confidence == d("0.177778")
    assert blocked.reason_codes == (
        "evidence_quorum_cost_floor_blocked",
        "source_family_count_blocked",
        "official_source_missing_blocked",
        "contradiction_severity_blocked",
        "taker_cost_blocked",
        "spread_cost_blocked",
        "slippage_cost_blocked",
        "total_cost_blocked",
        "edge_margin_blocked",
        "liquidity_depth_blocked",
        "close_urgency_blocked",
        "recommendation_floor_blocked",
        "evidence_inputs_available",
    )

    assert watched.floor_status == "watch"
    assert watched.source_family_score == d("0.666667")
    assert watched.total_cost == d("0.070000")
    assert watched.edge_margin == d("0.020000")
    assert watched.cost_efficiency_score == d("0.300000")
    assert watched.edge_margin_score == d("0.666667")
    assert watched.liquidity_depth_ratio == d("1.500000")
    assert watched.close_safety_score == d("0.666667")
    assert watched.recommendation_floor == d("0.685714")
    assert watched.floor_adjusted_confidence == d("0.685714")
    assert watched.reason_codes == (
        "evidence_quorum_cost_floor_watch",
        "source_family_count_watch",
        "contradiction_severity_watch",
        "taker_cost_watch",
        "spread_cost_watch",
        "slippage_cost_watch",
        "total_cost_watch",
        "edge_margin_watch",
        "liquidity_depth_watch",
        "close_urgency_watch",
        "recommendation_floor_watch",
        "evidence_inputs_available",
    )


def test_empty_report_is_blocked_and_decimal_zeroed() -> None:
    result = report()

    assert result.candidate_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.blocked_count == ZERO
    assert result.status == "blocked"
    assert result.reason_codes == ("evidence_quorum_cost_floor_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_revalidates_digest_flags_and_rejects_raw_numeric_payloads() -> None:
    module = api()
    result = report(recommendation())
    payload = module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(result)

    assert module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(payload) == payload

    tampered_count = {**payload, "candidate_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["recommendation_floor"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(tampered_row)

    downgraded = {**payload, "readonly": False}
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(downgraded)

    decimal_drift = {**payload, "candidate_count": d("1.000000")}
    with pytest.raises(ValueError, match="Decimal|string"):
        module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(decimal_drift)

    unsafe_key = {**payload, "wallet_reference": "paper"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(unsafe_key)

    unsafe_value = {**payload, "status": "live_mode"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_recommendation_evidence_quorum_cost_floor_v2_payload(unsafe_value)


def test_frozen_dataclasses_decimal_only_validation_and_tamper_checks() -> None:
    module = api()
    result = report(recommendation("candidate-frozen"))

    assert is_dataclass(module.StrategyRecommendationEvidenceQuorumCostFloorV2Config)
    assert is_dataclass(module.StrategyRecommendationEvidenceQuorumCostFloorV2Input)
    assert is_dataclass(module.StrategyRecommendationEvidenceQuorumCostFloorV2Row)
    assert is_dataclass(module.StrategyRecommendationEvidenceQuorumCostFloorV2Report)
    with pytest.raises(FrozenInstanceError):
        result.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].recommendation_floor = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="base_confidence"):
        recommendation(base_confidence=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_severity"):
        recommendation(contradiction_severity=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="official_source_present"):
        recommendation(official_source_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(recommendation("aware"), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            recommendation("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        recommendation(observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="recommendation_side"):
        recommendation(recommendation_side="maybe")
    with pytest.raises(ValueError, match="duplicate"):
        report(recommendation(), recommendation())
    with pytest.raises(ValueError, match="list or tuple"):
        recommendation(reason_codes={"evidence_inputs_available"})
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(recommendation_id="wallet_candidate")
    with pytest.raises(ValueError, match="less than or equal"):
        config(minimum_source_family_count=d("4.000000"))
    with pytest.raises(ValueError, match="must not exceed"):
        config(liquidity_depth_ratio_block=d("2.500000"))
    with pytest.raises(ValueError, match="must not exceed"):
        config(close_urgency_block_seconds=d("2000.000000"))

    with pytest.raises(ValueError, match="candidate_count"):
        replace(result, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], derived_validation_digest="bad")

    for value in (result, *result.rows):
        for item in fields(value):
            field_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
                "official_source_present",
            }:
                continue
            if isinstance(field_value, tuple):
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_confidence",
                    "_score",
                    "_seconds",
                    "_cost",
                    "_rate",
                    "_notional",
                    "_depth",
                    "_ratio",
                    "_floor",
                    "_edge",
                    "_margin",
                ),
            ):
                assert type(field_value) is Decimal, item.name


def test_utc_normalization_and_future_observations_are_rejected() -> None:
    result = report(
        recommendation(
            observed_at=datetime(
                2026,
                7,
                7,
                7,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            7,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    row = result.rows[0]
    assert result.generated_at == GENERATED_AT
    assert row.observed_at == datetime(2026, 7, 7, 11, 45, tzinfo=UTC)

    with pytest.raises(ValueError, match="observed_at"):
        report(
            recommendation(
                recommendation_id="future-observed",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )


def test_module_scope_has_no_io_mutation_or_external_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "strategy_recommendation_evidence_quorum_cost_floor_v2.py",
    )
    source = path.read_text(encoding="utf-8")
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
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
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
    assert re.search(r"\b(auth|wallet|broker|order|network)\b", lowered) is None
