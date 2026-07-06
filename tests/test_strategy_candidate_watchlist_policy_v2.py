from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_candidate_watchlist_policy_v2 import (
    StrategyCandidateWatchlistPolicyV2Candidate,
    StrategyCandidateWatchlistPolicyV2Config,
    StrategyCandidateWatchlistPolicyV2Decision,
    classify_strategy_candidate_watchlist_policy_v2,
    strategy_candidate_watchlist_policy_v2_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> StrategyCandidateWatchlistPolicyV2Config:
    values = {
        "minimum_edge": d("0.030000"),
        "minimum_source_count": 2,
        "minimum_liquidity_notional": d("1000.000000"),
        "price_review_minutes": 30,
        "source_review_minutes": 360,
        "liquidity_review_minutes": 60,
        "resolution_review_minutes": 720,
        "drop_review_minutes": 0,
    }
    values.update(overrides)
    return StrategyCandidateWatchlistPolicyV2Config(**values)


def candidate(**overrides: object) -> StrategyCandidateWatchlistPolicyV2Candidate:
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "outcome_name": "Yes",
        "best_ask_price": d("0.540000"),
        "target_entry_price": d("0.550000"),
        "estimated_edge": d("0.050000"),
        "source_count": 2,
        "available_liquidity_notional": d("1500.000000"),
        "resolution_is_clear": True,
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyCandidateWatchlistPolicyV2Candidate(**values)


@pytest.mark.parametrize(
    ("overrides", "expected_status", "expected_minutes", "expected_reason"),
    (
        (
            {"best_ask_price": d("0.570000")},
            "wait_for_price",
            30,
            "entry_price_above_target",
        ),
        (
            {"source_count": 1},
            "wait_for_source",
            360,
            "source_count_below_minimum",
        ),
        (
            {"available_liquidity_notional": d("999.999999")},
            "wait_for_liquidity",
            60,
            "liquidity_below_minimum",
        ),
        (
            {"resolution_is_clear": False},
            "wait_for_resolution_clarity",
            720,
            "resolution_clarity_missing",
        ),
        (
            {"estimated_edge": d("0.029999")},
            "drop",
            0,
            "estimated_edge_below_minimum",
        ),
    ),
)
def test_classifies_watchlist_status_with_review_and_reasons(
    overrides: dict[str, object],
    expected_status: str,
    expected_minutes: int,
    expected_reason: str,
) -> None:
    decision = classify_strategy_candidate_watchlist_policy_v2(
        candidate(**overrides),
        cfg(),
    )

    assert decision.watchlist_status == expected_status
    assert decision.next_review_minutes == expected_minutes
    assert decision.reason_codes[0] == (
        f"strategy_candidate_watchlist_v2_{expected_status}"
    )
    assert "candidate_screened" in decision.reason_codes
    assert expected_reason in decision.reason_codes
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_keeps_primary_status_but_reports_all_current_gaps() -> None:
    decision = classify_strategy_candidate_watchlist_policy_v2(
        candidate(
            source_count=1,
            available_liquidity_notional=d("250.000000"),
            resolution_is_clear=False,
            best_ask_price=d("0.610000"),
        ),
        cfg(),
    )

    assert decision.watchlist_status == "wait_for_source"
    assert decision.next_review_minutes == 360
    assert decision.reason_codes == (
        "strategy_candidate_watchlist_v2_wait_for_source",
        "candidate_screened",
        "source_count_below_minimum",
        "liquidity_below_minimum",
        "resolution_clarity_missing",
        "entry_price_above_target",
    )


def test_trade_ready_candidate_drops_from_watchlist() -> None:
    decision = classify_strategy_candidate_watchlist_policy_v2(candidate(), cfg())

    assert decision.watchlist_status == "drop"
    assert decision.next_review_minutes == 0
    assert decision.reason_codes == (
        "strategy_candidate_watchlist_v2_drop",
        "candidate_screened",
        "candidate_already_trade_ready",
    )


def test_payload_is_primitive_and_decimal_stringified() -> None:
    decision = classify_strategy_candidate_watchlist_policy_v2(
        candidate(best_ask_price=d("0.570000")),
        cfg(config_version="strategy-candidate-watchlist-policy-v2-custom"),
    )

    payload = strategy_candidate_watchlist_policy_v2_payload(decision)

    assert payload == {
        "config_version": "strategy-candidate-watchlist-policy-v2-custom",
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "outcome_name": "Yes",
        "watchlist_status": "wait_for_price",
        "next_review_minutes": 30,
        "best_ask_price": "0.570000",
        "target_entry_price": "0.550000",
        "estimated_edge": "0.050000",
        "source_count": 2,
        "available_liquidity_notional": "1500.000000",
        "resolution_is_clear": True,
        "reason_codes": [
            "strategy_candidate_watchlist_v2_wait_for_price",
            "candidate_screened",
            "entry_price_above_target",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def test_rejects_imprecise_and_mutable_input_types() -> None:
    with pytest.raises(ValueError, match="minimum_edge must be a Decimal"):
        cfg(minimum_edge=0.03)

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        candidate(reason_codes=["candidate_screened"])

    with pytest.raises(ValueError, match="resolution_is_clear must be a bool"):
        candidate(resolution_is_clear=1)


def test_enforces_paper_report_readonly_flags_and_decision_consistency() -> None:
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)

    with pytest.raises(ValueError, match="reason_codes must start"):
        StrategyCandidateWatchlistPolicyV2Decision(
            config_version="strategy-candidate-watchlist-policy-v2",
            candidate_id="candidate-alpha",
            market_slug="market-alpha",
            outcome_name="Yes",
            watchlist_status="wait_for_price",
            next_review_minutes=30,
            best_ask_price=d("0.570000"),
            target_entry_price=d("0.550000"),
            estimated_edge=d("0.050000"),
            source_count=2,
            available_liquidity_notional=d("1500.000000"),
            resolution_is_clear=True,
            reason_codes=("candidate_screened", "entry_price_above_target"),
        )
