from __future__ import annotations

import ast
import json
import re
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_recommendation_expected_value_digest import (
    StrategyRecommendationExpectedValueDigestConfig,
    StrategyRecommendationExpectedValueDigestInput,
    StrategyRecommendationExpectedValueDigestReasonCodeCount,
    StrategyRecommendationExpectedValueDigestReport,
    StrategyRecommendationExpectedValueDigestRow,
    build_strategy_recommendation_expected_value_digest_report,
    strategy_recommendation_expected_value_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyRecommendationExpectedValueDigestConfig:
    values = {
        "config_version": "strategy-recommendation-expected-value-digest-v0",
        "minimum_positive_expected_value": d("0.010000"),
        "watch_expected_value": d("0.000000"),
        "minimum_price_buffer": d("0.020000"),
        "minimum_confidence_adjustment": d("0.500000"),
        "stale_evidence_age_seconds": d("3600.000000"),
        "minimum_liquidity_depth": d("100.000000"),
    }
    values.update(overrides)
    return StrategyRecommendationExpectedValueDigestConfig(**values)


def recommendation(
    recommendation_id: str = "candidate-alpha",
    *,
    estimated_probability: Decimal = d("0.620000"),
    market_price: Decimal = d("0.500000"),
    estimated_cost: Decimal = d("0.520000"),
    confidence_adjustment: Decimal = d("0.900000"),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    liquidity_depth: Decimal = d("250.000000"),
    reason_codes: tuple[str, ...] = ("candidate_ev_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationExpectedValueDigestInput:
    return StrategyRecommendationExpectedValueDigestInput(
        recommendation_id=recommendation_id,
        estimated_probability=estimated_probability,
        market_price=market_price,
        estimated_cost=estimated_cost,
        confidence_adjustment=confidence_adjustment,
        evidence_observed_at=evidence_observed_at,
        liquidity_depth=liquidity_depth,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: StrategyRecommendationExpectedValueDigestInput,
    cfg: StrategyRecommendationExpectedValueDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationExpectedValueDigestReport:
    return build_strategy_recommendation_expected_value_digest_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_happy_path_scores_expected_value_quality_and_payload() -> None:
    digest = report(
        recommendation(
            "candidate-alpha",
            estimated_probability=d("0.650000"),
            market_price=d("0.500000"),
            estimated_cost=d("0.520000"),
            confidence_adjustment=d("0.800000"),
            liquidity_depth=d("300.000000"),
            reason_codes=("candidate_ev_input_available", "model_edge_positive"),
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
    assert digest.reason_codes == ("expected_value_digest_clear",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.recommendation_rows[0]
    assert row.quality_status == "pass"
    assert row.probability_edge == d("0.150000")
    assert row.price_cost_buffer == d("0.020000")
    assert row.confidence_adjusted_edge == d("0.120000")
    assert row.expected_value == d("0.100000")
    assert row.confidence_adjusted_expected_value == d("0.080000")
    assert row.evidence_age_seconds == d("900.000000")
    assert row.reason_codes == (
        "candidate_ev_input_available",
        "ev_quality_clear",
        "model_edge_positive",
    )

    payload = strategy_recommendation_expected_value_digest_payload(digest)
    assert payload["candidate_count"] == "1.000000"
    assert payload["recommendation_rows"][0]["expected_value"] == "0.100000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    json.dumps(payload, sort_keys=True)
    assert not _contains_float(payload)


def test_utc_normalization_for_generated_and_evidence_times() -> None:
    digest = report(
        recommendation(
            evidence_observed_at=datetime(
                2026,
                7,
                2,
                7,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            2,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.recommendation_rows[0].evidence_observed_at == datetime(
        2026,
        7,
        2,
        11,
        45,
        tzinfo=UTC,
    )
    assert digest.recommendation_rows[0].evidence_age_seconds == d("900.000000")


def test_naive_datetimes_are_rejected_at_phase1_boundary() -> None:
    with pytest.raises(ValueError, match="evidence_observed_at"):
        recommendation(evidence_observed_at=datetime(2026, 7, 2, 11, 45))

    with pytest.raises(ValueError, match="generated_at"):
        report(
            recommendation("aware-evidence"),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )


def test_quality_guards_emit_watch_and_blocked_reason_codes() -> None:
    digest = report(
        recommendation(
            "candidate-watch",
            estimated_probability=d("0.530000"),
            market_price=d("0.500000"),
            estimated_cost=d("0.520000"),
            confidence_adjustment=d("0.400000"),
            evidence_observed_at=GENERATED_AT - timedelta(hours=2),
            liquidity_depth=d("150.000000"),
        ),
        recommendation(
            "candidate-blocked",
            estimated_probability=d("0.470000"),
            market_price=d("0.500000"),
            estimated_cost=d("0.550000"),
            confidence_adjustment=d("0.800000"),
            liquidity_depth=d("20.000000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.reason_codes == (
        "expected_value_digest_blocked",
        "ev_confidence_adjustment_watch",
        "ev_evidence_stale_watch",
        "ev_liquidity_depth_blocked",
        "ev_price_cost_buffer_watch",
        "ev_probability_edge_blocked",
    )
    assert digest.recommendation_rows[0].recommendation_id == "candidate-blocked"
    assert digest.recommendation_rows[0].reason_codes == (
        "candidate_ev_input_available",
        "ev_liquidity_depth_blocked",
        "ev_price_cost_buffer_watch",
        "ev_probability_edge_blocked",
    )
    assert digest.recommendation_rows[1].reason_codes == (
        "candidate_ev_input_available",
        "ev_confidence_adjustment_watch",
        "ev_evidence_stale_watch",
    )


def test_expected_value_threshold_tiers_are_distinguishable() -> None:
    digest = report(
        recommendation(
            "below-minimum",
            estimated_probability=d("0.526000"),
            market_price=d("0.500000"),
            estimated_cost=d("0.520000"),
        ),
        recommendation(
            "below-watch",
            estimated_probability=d("0.524000"),
            market_price=d("0.500000"),
            estimated_cost=d("0.520000"),
        ),
        cfg=config(
            watch_expected_value=d("0.005000"),
            minimum_positive_expected_value=d("0.010000"),
        ),
    )

    rows_by_id = {row.recommendation_id: row for row in digest.recommendation_rows}
    assert rows_by_id["below-minimum"].reason_codes == (
        "candidate_ev_input_available",
        "ev_expected_value_below_minimum_watch",
    )
    assert rows_by_id["below-watch"].reason_codes == (
        "candidate_ev_input_available",
        "ev_expected_value_watch",
    )
    assert digest.reason_codes == (
        "expected_value_digest_watch",
        "ev_expected_value_below_minimum_watch",
        "ev_expected_value_watch",
    )


def test_deterministic_sorting_and_reason_code_counts() -> None:
    digest = report(
        recommendation(
            "zeta-watch",
            confidence_adjustment=d("0.250000"),
            reason_codes=("candidate_ev_input_available",),
        ),
        recommendation(
            "beta-blocked",
            estimated_probability=d("0.470000"),
            market_price=d("0.500000"),
            liquidity_depth=d("10.000000"),
            reason_codes=("candidate_ev_input_available",),
        ),
        recommendation(
            "alpha-pass",
            estimated_probability=d("0.610000"),
            market_price=d("0.500000"),
            reason_codes=("candidate_ev_input_available", "model_edge_positive"),
        ),
        recommendation(
            "alpha-blocked",
            estimated_probability=d("0.450000"),
            market_price=d("0.500000"),
            reason_codes=("candidate_ev_input_available",),
        ),
    )

    assert tuple(row.recommendation_id for row in digest.recommendation_rows) == (
        "beta-blocked",
        "alpha-blocked",
        "zeta-watch",
        "alpha-pass",
    )
    assert digest.reason_code_counts == (
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code="candidate_ev_input_available",
            count=d("4.000000"),
        ),
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code="ev_probability_edge_blocked",
            count=d("2.000000"),
        ),
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code="ev_confidence_adjustment_watch",
            count=d("1.000000"),
        ),
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code="ev_liquidity_depth_blocked",
            count=d("1.000000"),
        ),
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code="ev_quality_clear",
            count=d("1.000000"),
        ),
        StrategyRecommendationExpectedValueDigestReasonCodeCount(
            reason_code="model_edge_positive",
            count=d("1.000000"),
        ),
    )


def test_hard_flags_validation_and_decimal_public_numbers() -> None:
    digest = report(recommendation("frozen"))

    assert is_dataclass(StrategyRecommendationExpectedValueDigestConfig)
    assert is_dataclass(StrategyRecommendationExpectedValueDigestInput)
    assert is_dataclass(StrategyRecommendationExpectedValueDigestRow)
    assert is_dataclass(StrategyRecommendationExpectedValueDigestReasonCodeCount)
    assert is_dataclass(StrategyRecommendationExpectedValueDigestReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.recommendation_rows[0].expected_value = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        recommendation(paper_only=False)
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
        "max_expected_value",
        "min_confidence_adjusted_expected_value",
        "stale_evidence_count",
        "liquidity_guard_blocked_count",
    ):
        assert isinstance(getattr(digest, field_name), Decimal)


def test_validation_errors_cover_inputs_config_payload_and_consistency() -> None:
    with pytest.raises(ValueError, match="minimum_positive_expected_value"):
        config(minimum_positive_expected_value=d("-0.000001"))
    with pytest.raises(ValueError, match="minimum_confidence_adjustment"):
        config(minimum_confidence_adjustment=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="recommendation_id"):
        recommendation(recommendation_id=" candidate")
    with pytest.raises(ValueError, match="estimated_probability"):
        recommendation(estimated_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_price"):
        recommendation(market_price=d("1.000001"))
    with pytest.raises(ValueError, match="estimated_cost"):
        recommendation(estimated_cost=d("-0.000001"))
    with pytest.raises(ValueError, match="confidence_adjustment"):
        recommendation(confidence_adjustment=d("1.000001"))
    with pytest.raises(ValueError, match="liquidity_depth"):
        recommendation(liquidity_depth=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        recommendation(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="generated_at"):
        report(recommendation(), generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        report(recommendation(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)))

    digest = report(recommendation("consistent"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(digest, candidate_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="blocked")
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_expected_value_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_address": "blocked",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(recommendation_id="wallet_candidate")
    with pytest.raises(ValueError, match="unsafe"):
        recommendation(reason_codes=("candidate_ev_input_available", "sign_ready"))
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_expected_value_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "summary": "wallet value must not pass redaction",
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_expected_value_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "recommendation_rows": [
                    {
                        "paper_only": True,
                        "report_only": True,
                        "readonly": False,
                    },
                ],
            },
        )


def test_static_module_surface_excludes_forbidden_live_trading_terms() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_recommendation_expected_value_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "order",
        "sign",
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
