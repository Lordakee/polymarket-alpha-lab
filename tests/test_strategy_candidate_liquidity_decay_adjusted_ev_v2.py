from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.strategy_candidate_liquidity_decay_adjusted_ev_v2 as api
from polymarket_alpha_lab.strategy_candidate_liquidity_decay_adjusted_ev_v2 import (
    StrategyCandidateLiquidityDecayAdjustedEvV2Candidate,
    StrategyCandidateLiquidityDecayAdjustedEvV2Config,
    StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem,
    StrategyCandidateLiquidityDecayAdjustedEvV2Report,
    StrategyCandidateLiquidityDecayAdjustedEvV2Row,
    build_strategy_candidate_liquidity_decay_adjusted_ev_v2_report,
    strategy_candidate_liquidity_decay_adjusted_ev_v2_payload,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _candidate(
    *,
    candidate_id: str = "candidate_a",
    market_id: str = "market_a",
    model_probability: Decimal = Decimal("0.620000"),
    market_probability: Decimal = Decimal("0.560000"),
    fee_drag: Decimal = Decimal("0.005000"),
    top_depth_usd: Decimal = Decimal("5000.000000"),
    depth_decay_ratio: Decimal = Decimal("0.100000"),
    liquidity_stability_score: Decimal = Decimal("0.850000"),
) -> StrategyCandidateLiquidityDecayAdjustedEvV2Candidate:
    return StrategyCandidateLiquidityDecayAdjustedEvV2Candidate(
        candidate_id=candidate_id,
        market_id=market_id,
        evaluated_at=NOW,
        model_probability=model_probability,
        market_probability=market_probability,
        fee_drag=fee_drag,
        top_depth_usd=top_depth_usd,
        depth_decay_ratio=depth_decay_ratio,
        liquidity_stability_score=liquidity_stability_score,
    )


def _report(
    candidates: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2Candidate, ...],
    *,
    config: StrategyCandidateLiquidityDecayAdjustedEvV2Config | None = None,
    public_payload: tuple[StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem, ...] = (),
) -> StrategyCandidateLiquidityDecayAdjustedEvV2Report:
    return build_strategy_candidate_liquidity_decay_adjusted_ev_v2_report(
        candidates,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_scores_liquidity_decay_adjusted_ev_from_edge_cost_decay_and_boost() -> None:
    report = _report((_candidate(),))

    row = report.rows[0]
    assert row.raw_ev_score == Decimal("0.055000")
    assert row.depth_penalty == Decimal("0.000000")
    assert row.liquidity_decay_penalty == Decimal("0.006000")
    assert row.stable_liquidity_boost == Decimal("0.020000")
    assert row.adjusted_ev_score == Decimal("0.069000")
    assert row.status == "pass"
    assert report.report_status == "pass"
    assert "positive_adjusted_ev" in row.reason_codes
    assert "liquidity_decay_penalty" in row.reason_codes


def test_shallow_depth_penalty_reduces_adjusted_ev_and_marks_watch() -> None:
    deep_report = _report((_candidate(candidate_id="candidate_deep"),))
    shallow_report = _report(
        (
            _candidate(
                candidate_id="candidate_shallow",
                top_depth_usd=Decimal("100.000000"),
            ),
        ),
    )

    deep_row = deep_report.rows[0]
    shallow_row = shallow_report.rows[0]
    assert shallow_row.depth_penalty == Decimal("0.045000")
    assert shallow_row.adjusted_ev_score < deep_row.adjusted_ev_score
    assert shallow_row.status == "watch"
    assert shallow_report.report_status == "watch"
    assert "shallow_depth_penalty" in shallow_row.reason_codes


def test_stable_liquidity_boost_rewards_deep_stable_candidates() -> None:
    stable_report = _report((_candidate(candidate_id="candidate_stable"),))
    unstable_report = _report(
        (
            _candidate(
                candidate_id="candidate_unstable",
                liquidity_stability_score=Decimal("0.600000"),
            ),
        ),
    )

    stable_row = stable_report.rows[0]
    unstable_row = unstable_report.rows[0]
    assert stable_row.stable_liquidity_boost == Decimal("0.020000")
    assert unstable_row.stable_liquidity_boost == Decimal("0.000000")
    assert stable_row.adjusted_ev_score > unstable_row.adjusted_ev_score
    assert "stable_liquidity_boost" in stable_row.reason_codes


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    report = _report(
        (_candidate(),),
        public_payload=(
            StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem(
                "safe_key",
                "safe value",
            ),
        ),
    )

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["candidate_count"] == "1.000000"
    assert payload["average_adjusted_ev_score"] == "0.069000"
    assert payload["rows"][0]["top_depth_usd"] == "5000.000000"
    assert payload["rows"][0]["adjusted_ev_score"] == "0.069000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert strategy_candidate_liquidity_decay_adjusted_ev_v2_payload(payload) == payload
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report((_candidate(),))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(StrategyCandidateLiquidityDecayAdjustedEvV2Config):
            pass


def test_hard_readonly_report_only_paper_only_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        StrategyCandidateLiquidityDecayAdjustedEvV2Config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        StrategyCandidateLiquidityDecayAdjustedEvV2Candidate(
            candidate_id="candidate_a",
            market_id="market_a",
            evaluated_at=NOW,
            model_probability=Decimal("0.620000"),
            market_probability=Decimal("0.560000"),
            fee_drag=Decimal("0.005000"),
            top_depth_usd=Decimal("5000.000000"),
            depth_decay_ratio=Decimal("0.100000"),
            liquidity_stability_score=Decimal("0.850000"),
            report_only=False,
        )

    report = _report((_candidate(),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_dataclass_and_payload_tampering() -> None:
    report = _report((_candidate(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered_payload = {
        **report.payload,
        "average_adjusted_ev_score": "0.010000",
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_liquidity_decay_adjusted_ev_v2_payload(tampered_payload)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for term in (
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
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem(
                f"{term}_key",
                "safe value",
            )
        with pytest.raises(ValueError, match="unsafe public"):
            StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem(
                "safe_key",
                f"{term} value",
            )

    with pytest.raises(ValueError, match="unsafe public"):
        _candidate(candidate_id="buy_signal")


def test_no_unsafe_public_surfaces_are_exposed() -> None:
    unsafe_terms = (
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
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        StrategyCandidateLiquidityDecayAdjustedEvV2Candidate,
        StrategyCandidateLiquidityDecayAdjustedEvV2Config,
        StrategyCandidateLiquidityDecayAdjustedEvV2PublicPayloadItem,
        StrategyCandidateLiquidityDecayAdjustedEvV2Report,
        StrategyCandidateLiquidityDecayAdjustedEvV2Row,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
