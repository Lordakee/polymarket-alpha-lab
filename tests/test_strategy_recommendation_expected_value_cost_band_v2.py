from __future__ import annotations

import ast
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_recommendation_expected_value_cost_band_v2 import (
    StrategyRecommendationExpectedValueCostBandV2Config,
    StrategyRecommendationExpectedValueCostBandV2Input,
    StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount,
    StrategyRecommendationExpectedValueCostBandV2Report,
    StrategyRecommendationExpectedValueCostBandV2Row,
    build_strategy_recommendation_expected_value_cost_band_v2_report,
    strategy_recommendation_expected_value_cost_band_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyRecommendationExpectedValueCostBandV2Config:
    values = {
        "config_version": "strategy-recommendation-expected-value-cost-band-v2",
        "minimum_pass_net_expected_value": d("0.020000"),
        "minimum_watch_net_expected_value": d("0.000000"),
        "minimum_confidence": d("0.500000"),
        "maximum_pass_cost_to_edge_ratio": d("0.500000"),
        "maximum_watch_cost_to_edge_ratio": d("0.800000"),
    }
    values.update(overrides)
    return StrategyRecommendationExpectedValueCostBandV2Config(**values)


def recommendation(
    recommendation_id: str = "candidate-alpha",
    *,
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    probability_edge: Decimal = d("0.120000"),
    confidence: Decimal = d("0.900000"),
    taker_fee: Decimal = d("0.010000"),
    spread: Decimal = d("0.015000"),
    slippage: Decimal = d("0.005000"),
    settlement_lag: Decimal = d("0.002000"),
    liquidity_haircut: Decimal = d("0.008000"),
    reason_codes: tuple[str, ...] = ("edge_input_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationExpectedValueCostBandV2Input:
    return StrategyRecommendationExpectedValueCostBandV2Input(
        recommendation_id=recommendation_id,
        observed_at=observed_at,
        probability_edge=probability_edge,
        confidence=confidence,
        taker_fee=taker_fee,
        spread=spread,
        slippage=slippage,
        settlement_lag=settlement_lag,
        liquidity_haircut=liquidity_haircut,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: StrategyRecommendationExpectedValueCostBandV2Input,
    cfg: StrategyRecommendationExpectedValueCostBandV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationExpectedValueCostBandV2Report:
    return build_strategy_recommendation_expected_value_cost_band_v2_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_happy_path_builds_pass_cost_band_payload_and_validation_digests() -> None:
    digest = report(
        recommendation(
            "candidate-alpha",
            probability_edge=d("0.150000"),
            confidence=d("0.800000"),
            taker_fee=d("0.010000"),
            spread=d("0.010000"),
            slippage=d("0.005000"),
            settlement_lag=d("0.002000"),
            liquidity_haircut=d("0.003000"),
            reason_codes=("edge_input_ready", "model_edge_positive"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.candidate_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.status == "pass"
    assert digest.reason_codes == ("cost_band_report_clear",)
    assert re.fullmatch(r"[0-9a-f]{64}", digest.validation_digest)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.recommendation_rows[0]
    assert row.recommendation_status == "pass"
    assert row.cost_band == "positive"
    assert row.confidence_adjusted_edge == d("0.120000")
    assert row.total_cost == d("0.030000")
    assert row.net_expected_value == d("0.090000")
    assert row.cost_to_edge_ratio == d("0.250000")
    assert row.edge_shortfall == ZERO
    assert re.fullmatch(r"[0-9a-f]{64}", row.validation_digest)
    assert row.reason_codes == (
        "cost_band_clear",
        "cost_band_liquidity_haircut_present",
        "cost_band_settlement_lag_present",
        "cost_band_slippage_present",
        "cost_band_spread_present",
        "cost_band_taker_fee_present",
        "edge_input_ready",
        "model_edge_positive",
    )

    payload = strategy_recommendation_expected_value_cost_band_v2_payload(digest)
    assert payload["candidate_count"] == "1.000000"
    assert payload["recommendation_rows"][0]["total_cost"] == "0.030000"
    assert payload["recommendation_rows"][0]["validation_digest"] == row.validation_digest
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_utc_normalization_for_generated_and_observed_times() -> None:
    digest = report(
        recommendation(
            observed_at=datetime(
                2026,
                7,
                7,
                7,
                55,
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

    assert digest.generated_at == GENERATED_AT
    assert digest.recommendation_rows[0].observed_at == datetime(
        2026,
        7,
        7,
        11,
        55,
        tzinfo=UTC,
    )


def test_status_bands_and_reason_codes_are_deterministic() -> None:
    digest = report(
        recommendation(
            "watch-ratio",
            probability_edge=d("0.100000"),
            confidence=d("0.800000"),
            taker_fee=d("0.030000"),
            spread=d("0.015000"),
            slippage=d("0.005000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
        recommendation(
            "blocked-net",
            probability_edge=d("0.050000"),
            confidence=d("0.700000"),
            taker_fee=d("0.020000"),
            spread=d("0.020000"),
            slippage=d("0.010000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
        recommendation(
            "pass-clean",
            probability_edge=d("0.140000"),
            confidence=d("0.900000"),
            taker_fee=d("0.005000"),
            spread=d("0.005000"),
            slippage=d("0.000000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert tuple(row.recommendation_id for row in digest.recommendation_rows) == (
        "blocked-net",
        "watch-ratio",
        "pass-clean",
    )
    assert digest.reason_codes == (
        "cost_band_report_blocked",
        "cost_band_cost_ratio_watch",
        "cost_band_net_expected_value_blocked",
    )

    rows_by_id = {row.recommendation_id: row for row in digest.recommendation_rows}
    assert rows_by_id["blocked-net"].recommendation_status == "blocked"
    assert rows_by_id["blocked-net"].cost_band == "negative"
    assert rows_by_id["blocked-net"].net_expected_value == d("-0.015000")
    assert rows_by_id["blocked-net"].edge_shortfall == d("0.015000")
    assert "cost_band_net_expected_value_blocked" in rows_by_id[
        "blocked-net"
    ].reason_codes
    assert rows_by_id["watch-ratio"].recommendation_status == "watch"
    assert rows_by_id["watch-ratio"].cost_band == "thin"
    assert rows_by_id["watch-ratio"].cost_to_edge_ratio == d("0.625000")
    assert "cost_band_cost_ratio_watch" in rows_by_id["watch-ratio"].reason_codes
    assert rows_by_id["pass-clean"].recommendation_status == "pass"


def test_report_rows_explain_probability_confidence_liquidity_cost_and_status_drivers() -> None:
    digest = report(
        recommendation(
            "pass-clear",
            probability_edge=d("0.150000"),
            confidence=d("0.800000"),
            taker_fee=d("0.010000"),
            spread=d("0.010000"),
            slippage=d("0.005000"),
            settlement_lag=d("0.002000"),
            liquidity_haircut=d("0.003000"),
        ),
        recommendation(
            "watch-confidence",
            probability_edge=d("0.120000"),
            confidence=d("0.400000"),
            taker_fee=ZERO,
            spread=ZERO,
            slippage=ZERO,
            settlement_lag=ZERO,
            liquidity_haircut=ZERO,
        ),
        recommendation(
            "blocked-liquidity-cost",
            probability_edge=d("0.050000"),
            confidence=d("0.700000"),
            taker_fee=d("0.020000"),
            spread=d("0.010000"),
            slippage=d("0.005000"),
            settlement_lag=ZERO,
            liquidity_haircut=d("0.020000"),
        ),
    )

    rows_by_id = {row.recommendation_id: row for row in digest.recommendation_rows}

    assert rows_by_id["pass-clear"].driver_explanations == (
        "Probability edge 0.150000 is positive.",
        "Confidence 0.800000 applies to edge 0.150000, leaving confidence-adjusted edge 0.120000.",
        "Liquidity haircut 0.003000 is included in total cost 0.030000.",
        "Costs total 0.030000 versus confidence-adjusted edge 0.120000, leaving net expected value 0.090000.",
        "Pass because net expected value 0.090000 meets the pass floor and cost-to-edge ratio 0.250000 is within limits.",
    )
    assert rows_by_id["watch-confidence"].driver_explanations[-1] == (
        "Watch because confidence 0.400000 is below the minimum confidence requirement."
    )
    assert rows_by_id["blocked-liquidity-cost"].driver_explanations == (
        "Probability edge 0.050000 is positive.",
        "Confidence 0.700000 applies to edge 0.050000, leaving confidence-adjusted edge 0.035000.",
        "Liquidity haircut 0.020000 is included in total cost 0.055000.",
        "Costs total 0.055000 versus confidence-adjusted edge 0.035000, leaving net expected value -0.020000.",
        "Blocked because net expected value -0.020000 is below the watch floor.",
    )

    payload = strategy_recommendation_expected_value_cost_band_v2_payload(digest)
    assert payload["recommendation_rows"][0]["driver_explanations"] == [
        "Probability edge 0.050000 is positive.",
        "Confidence 0.700000 applies to edge 0.050000, leaving confidence-adjusted edge 0.035000.",
        "Liquidity haircut 0.020000 is included in total cost 0.055000.",
        "Costs total 0.055000 versus confidence-adjusted edge 0.035000, leaving net expected value -0.020000.",
        "Blocked because net expected value -0.020000 is below the watch floor.",
    ]
    assert not _contains_float(payload)


def test_confidence_and_nonpositive_edge_guards_are_separate_from_cost_components() -> None:
    digest = report(
        recommendation(
            "low-confidence",
            confidence=d("0.400000"),
            taker_fee=d("0.000000"),
            spread=d("0.000000"),
            slippage=d("0.000000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
        recommendation(
            "negative-edge",
            probability_edge=d("-0.010000"),
            confidence=d("0.900000"),
            taker_fee=d("0.000000"),
            spread=d("0.000000"),
            slippage=d("0.000000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
    )

    rows_by_id = {row.recommendation_id: row for row in digest.recommendation_rows}
    assert rows_by_id["negative-edge"].recommendation_status == "blocked"
    assert rows_by_id["negative-edge"].reason_codes == (
        "cost_band_probability_edge_blocked",
        "edge_input_ready",
    )
    assert rows_by_id["low-confidence"].recommendation_status == "watch"
    assert rows_by_id["low-confidence"].reason_codes == (
        "cost_band_confidence_watch",
        "edge_input_ready",
    )


def test_reason_code_counts_are_stable() -> None:
    digest = report(
        recommendation(
            "alpha-watch",
            probability_edge=d("0.100000"),
            confidence=d("0.800000"),
            taker_fee=d("0.030000"),
            spread=d("0.015000"),
            slippage=d("0.005000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
        recommendation(
            "beta-watch",
            probability_edge=d("0.100000"),
            confidence=d("0.800000"),
            taker_fee=d("0.030000"),
            spread=d("0.015000"),
            slippage=d("0.005000"),
            settlement_lag=d("0.000000"),
            liquidity_haircut=d("0.000000"),
        ),
    )

    assert digest.reason_code_counts == (
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount(
            reason_code="cost_band_cost_ratio_watch",
            count=d("2.000000"),
        ),
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount(
            reason_code="cost_band_slippage_present",
            count=d("2.000000"),
        ),
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount(
            reason_code="cost_band_spread_present",
            count=d("2.000000"),
        ),
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount(
            reason_code="cost_band_taker_fee_present",
            count=d("2.000000"),
        ),
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount(
            reason_code="edge_input_ready",
            count=d("2.000000"),
        ),
    )


def test_frozen_hard_flags_decimal_only_and_no_float_acceptance() -> None:
    digest = report(recommendation("frozen"))

    assert is_dataclass(StrategyRecommendationExpectedValueCostBandV2Config)
    assert is_dataclass(StrategyRecommendationExpectedValueCostBandV2Input)
    assert is_dataclass(StrategyRecommendationExpectedValueCostBandV2Row)
    assert is_dataclass(StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount)
    assert is_dataclass(StrategyRecommendationExpectedValueCostBandV2Report)
    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.recommendation_rows[0].total_cost = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        recommendation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    for item in (digest, *digest.recommendation_rows, *digest.reason_code_counts):
        for field_name, value in item.__dict__.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name

    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "average_total_cost",
        "max_total_cost",
        "min_net_expected_value",
        "max_cost_to_edge_ratio",
        "max_edge_shortfall",
    ):
        assert isinstance(getattr(digest, field_name), Decimal)

    with pytest.raises(ValueError, match="probability_edge"):
        recommendation(probability_edge=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence"):
        recommendation(confidence=_DecimalSubclass("0.900000"))


def test_validation_errors_cover_config_input_payload_and_consistency() -> None:
    with pytest.raises(ValueError, match="minimum_pass_net_expected_value"):
        config(minimum_pass_net_expected_value=d("-0.000001"))
    with pytest.raises(ValueError, match="minimum_watch_net_expected_value"):
        config(
            minimum_pass_net_expected_value=d("0.010000"),
            minimum_watch_net_expected_value=d("0.020000"),
        )
    with pytest.raises(ValueError, match="maximum_pass_cost_to_edge_ratio"):
        config(
            maximum_pass_cost_to_edge_ratio=d("0.900000"),
            maximum_watch_cost_to_edge_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="recommendation_id"):
        recommendation(recommendation_id=" candidate")
    with pytest.raises(ValueError, match="taker_fee"):
        recommendation(taker_fee=d("-0.000001"))
    with pytest.raises(ValueError, match="spread"):
        recommendation(spread=d("0.0000001"))
    with pytest.raises(ValueError, match="slippage"):
        recommendation(slippage=d("-0.000001"))
    with pytest.raises(ValueError, match="settlement_lag"):
        recommendation(settlement_lag=d("-0.000001"))
    with pytest.raises(ValueError, match="liquidity_haircut"):
        recommendation(liquidity_haircut=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        recommendation(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="observed_at"):
        recommendation(observed_at=datetime(2026, 7, 7, 11, 55))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            recommendation("aware-observed"),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            recommendation("subclass-generated"),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(recommendation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    digest = report(recommendation("consistent"))
    row = digest.recommendation_rows[0]
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="blocked")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(digest, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="recommendation_status"):
        replace(row, recommendation_status="blocked")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        strategy_recommendation_expected_value_cost_band_v2_payload({"paper_only": True})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(recommendation_id="wallet_candidate")
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(reason_codes=("edge_input_ready", "sign_ready"))


def test_empty_report_is_deterministic_and_paper_only() -> None:
    digest = report()

    assert digest.status == "watch"
    assert digest.candidate_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.average_total_cost == ZERO
    assert digest.reason_codes == ("cost_band_report_empty",)
    assert digest.reason_code_counts == ()
    assert digest.recommendation_rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_static_module_surface_excludes_forbidden_runtime_and_mutation_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_expected_value_cost_band_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "order",
        "private_key",
        "investment_advice",
        "live_trading",
        "requests.",
        "urllib",
        "sqlite",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
    assert not re.search(r"\b(order|wallet|broker|auth|sign)\b", lowered)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
