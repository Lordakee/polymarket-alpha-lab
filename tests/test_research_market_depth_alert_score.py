from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_depth_alert_score"
CONFIG_VERSION = "research-market-depth-alert-score-v0"
GENERATED_AT = datetime(2026, 7, 7, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "min_pass_depth_score": d("0.700000"),
        "min_watch_depth_score": d("0.400000"),
        "min_pass_liquidity_change_score": d("0.000000"),
        "min_watch_liquidity_change_score": d("-0.250000"),
        "max_pass_spread": d("0.030000"),
        "max_watch_spread": d("0.060000"),
        "max_pass_cost_share": d("0.020000"),
        "max_watch_cost_share": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthAlertScoreConfig(**values)


def observation(
    private_candidate_id: str = "candidate-alpha-private",
    **overrides: object,
) -> Any:
    module = api()
    values = {
        "private_candidate_id": private_candidate_id,
        "private_market_id": "market-alpha-private",
        "private_market_slug": "market-alpha-private-slug",
        "private_market_question": "Will the private alpha market resolve?",
        "source_reference": "source-ref-private",
        "source_url": "https://example.invalid/private?token=secret-token",
        "source_text": "private source text for market-alpha-private",
        "observed_at": GENERATED_AT - timedelta(minutes=3),
        "redacted_depth_score": d("0.820000"),
        "liquidity_change_score": d("0.120000"),
        "spread": d("0.020000"),
        "cost_share": d("0.012000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthAlertScoreObservation(**values)


def report(
    *items: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_depth_alert_score_report(
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
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_public_payload_safe(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).lower()
    forbidden_fragments = (
        "candidate-alpha-private",
        "market-alpha-private",
        "market-alpha-private-slug",
        "will the private alpha market resolve",
        "source-ref-private",
        "example.invalid",
        "secret-token",
        "private source text",
        "private_candidate_id",
        "private_market_id",
        "private_market_slug",
        "private_market_question",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_reference",
        "source_url",
        "source_text",
        "source",
        "ref",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    for fragment in forbidden_fragments:
        assert fragment not in rendered
    assert_no_float_values(payload)


def test_pass_path_uses_redacted_depth_and_safe_payload() -> None:
    module = api()
    result = report(observation())

    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.status == "pass"
    assert result.reason_codes == ("market_depth_alert_score_pass", "depth_alert_pass")
    assert result.item_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.min_redacted_depth_score == d("0.820000")
    assert result.min_liquidity_change_score == d("0.120000")
    assert result.max_spread == d("0.020000")
    assert result.max_cost_share == d("0.012000")
    assert result.average_alert_score == d("0.908000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.derived_validation_digest

    row = result.rows[0]
    assert row.review_rank == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("depth_alert_pass",)
    assert row.depth_band == "deep"
    assert row.liquidity_change_band == "improving"
    assert row.spread_band == "tight"
    assert row.cost_share_band == "low"
    assert row.alert_score == d("0.908000")
    assert row.observed_age_seconds == d("180.000000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.derived_validation_digest

    payload = module.research_market_depth_alert_score_payload(result)
    assert payload["item_count"] == "1.000000"
    assert payload["rows"][0]["depth_band"] == "deep"
    assert payload["rows"][0]["alert_score"] == "0.908000"
    assert_public_payload_safe(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_watch_path_combines_depth_liquidity_spread_and_cost_reasons() -> None:
    result = report(
        observation(
            private_candidate_id="candidate-watch-private",
            redacted_depth_score=d("0.550000"),
            liquidity_change_score=d("-0.100000"),
            spread=d("0.040000"),
            cost_share=d("0.030000"),
        ),
    )

    assert result.status == "watch"
    assert result.pass_count == ZERO
    assert result.watch_count == d("1.000000")
    assert result.block_count == ZERO
    assert result.reason_codes == (
        "market_depth_alert_score_watch",
        "redacted_depth_watch",
        "liquidity_change_watch",
        "spread_watch",
        "cost_share_watch",
    )
    row = result.rows[0]
    assert row.status == "watch"
    assert row.depth_band == "adequate"
    assert row.liquidity_change_band == "softening"
    assert row.spread_band == "wide"
    assert row.cost_share_band == "elevated"
    assert row.alert_score == d("0.380000")
    assert row.reason_codes == (
        "redacted_depth_watch",
        "liquidity_change_watch",
        "spread_watch",
        "cost_share_watch",
    )


def test_block_path_prioritizes_block_reasons_and_sorts_deterministically() -> None:
    result = report(
        observation(private_candidate_id="candidate-pass-private"),
        observation(
            private_candidate_id="candidate-watch-private",
            private_market_id="market-watch-private",
            redacted_depth_score=d("0.550000"),
            liquidity_change_score=d("-0.100000"),
            spread=d("0.040000"),
            cost_share=d("0.030000"),
        ),
        observation(
            private_candidate_id="candidate-block-private",
            private_market_id="market-block-private",
            redacted_depth_score=d("0.300000"),
            liquidity_change_score=d("-0.300000"),
            spread=d("0.070000"),
            cost_share=d("0.060000"),
        ),
    )

    assert result.status == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.reason_codes == (
        "market_depth_alert_score_block",
        "redacted_depth_block",
        "liquidity_change_block",
        "spread_block",
        "cost_share_block",
        "redacted_depth_watch",
        "liquidity_change_watch",
        "spread_watch",
        "cost_share_watch",
        "depth_alert_pass",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.review_rank for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    blocked = result.rows[0]
    assert blocked.depth_band == "thin"
    assert blocked.liquidity_change_band == "deteriorating"
    assert blocked.spread_band == "very_wide"
    assert blocked.cost_share_band == "high"
    assert blocked.alert_score == d("0.000000")


def test_decimal_type_rejection_and_time_normalization_are_strict() -> None:
    eastern = timezone(timedelta(hours=-4))
    result = report(
        observation(
            observed_at=datetime(2026, 7, 7, 10, 57, tzinfo=eastern),
            redacted_depth_score=d("0.8200004"),
            liquidity_change_score=d("0.1200004"),
            spread=d("0.0200004"),
            cost_share=d("0.0120004"),
        ),
    )
    row = result.rows[0]
    assert row.redacted_depth_score == d("0.820000")
    assert row.liquidity_change_score == d("0.120000")
    assert row.spread == d("0.020000")
    assert row.cost_share == d("0.012000")
    assert row.observed_age_seconds == d("180.000000")

    with pytest.raises(ValueError, match="redacted_depth_score"):
        replace(observation(), redacted_depth_score=0.82)
    with pytest.raises(ValueError, match="liquidity_change_score"):
        replace(observation(), liquidity_change_score=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="spread"):
        replace(observation(), spread=Decimal("-0.000001"))
    with pytest.raises(ValueError, match="max_pass_spread"):
        config(max_pass_spread=0.03)
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 7, 15, 0))


def test_public_payload_rejects_leaks_and_unsafe_public_terms() -> None:
    module = api()
    result = report(observation())
    payload = module.research_market_depth_alert_score_payload(result)
    assert_public_payload_safe(payload)

    with pytest.raises(ValueError, match="unsafe public"):
        module.ResearchMarketDepthAlertScoreRow(
            review_rank=d("1.000000"),
            status="pass",
            reason_codes=("depth_alert_pass",),
            depth_band="deep",
            liquidity_change_band="improving",
            spread_band="tight",
            cost_share_band="low",
            redacted_depth_score=d("0.900000"),
            liquidity_change_score=d("0.100000"),
            spread=d("0.010000"),
            cost_share=d("0.010000"),
            alert_score=d("0.980000"),
            operator_note="buy this market",
            observed_age_seconds=d("0.000000"),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module._reject_unsafe_public_payload({"market_id": "abc"})  # noqa: SLF001
    with pytest.raises(ValueError, match="unsafe public"):
        module._reject_unsafe_public_payload({"safe": "source_ref_private"})  # noqa: SLF001


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    module = api()
    cfg = config()
    item = observation()
    result = report(item, cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        item.spread = d("0.999999")
    with pytest.raises(FrozenInstanceError):
        cfg.max_pass_spread = d("0.999999")
    with pytest.raises(FrozenInstanceError):
        result.rows = ()

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(item, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchMarketDepthAlertScoreReport(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            status="pass",
            reason_codes=("market_depth_alert_score_pass", "depth_alert_pass"),
            item_count=d("0.000000"),
            pass_count=d("0.000000"),
            watch_count=d("0.000000"),
            block_count=d("0.000000"),
            min_redacted_depth_score=d("0.000000"),
            min_liquidity_change_score=d("0.000000"),
            max_spread=d("0.000000"),
            max_cost_share=d("0.000000"),
            average_alert_score=d("0.000000"),
            rows=(),
            readonly=False,
        )


def test_output_is_deterministic_and_rejects_manual_inconsistency() -> None:
    first = report(
        observation(private_candidate_id="candidate-b-private", private_market_id="market-b"),
        observation(private_candidate_id="candidate-a-private", private_market_id="market-a"),
    )
    second = report(
        observation(private_candidate_id="candidate-a-private", private_market_id="market-a"),
        observation(private_candidate_id="candidate-b-private", private_market_id="market-b"),
    )

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.derived_validation_digest for row in first.rows) == tuple(
        row.derived_validation_digest for row in second.rows
    )

    with pytest.raises(ValueError, match="rows"):
        replace(first, rows=tuple(reversed(first.rows)))
    with pytest.raises(ValueError, match="alert_score"):
        replace(first.rows[0], alert_score=d("0.010000"))
    with pytest.raises(ValueError, match="duplicate private_candidate_id"):
        report(
            observation(private_candidate_id="duplicate-private"),
            observation(private_candidate_id="duplicate-private"),
        )
