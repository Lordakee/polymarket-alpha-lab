from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_cost_depth_combined_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_COST_DEPTH_COMBINED_WATCH_REPORT_CONFIG_VERSION
        ),
        "max_pass_fee_age_seconds": d("3600.000000"),
        "max_watch_fee_age_seconds": d("14400.000000"),
        "max_pass_spread_stress": d("0.030000"),
        "max_watch_spread_stress": d("0.080000"),
        "min_pass_depth_balance": d("0.700000"),
        "min_watch_depth_balance": d("0.400000"),
        "max_pass_book_freshness_age_seconds": d("120.000000"),
        "max_watch_book_freshness_age_seconds": d("600.000000"),
        "max_pass_settlement_friction_rate": d("0.005000"),
        "max_watch_settlement_friction_rate": d("0.020000"),
        "max_pass_manual_recheck_urgency": d("0.300000"),
        "max_watch_manual_recheck_urgency": d("0.700000"),
        "fee_freshness_weight": d("0.150000"),
        "spread_stress_weight": d("0.200000"),
        "depth_balance_weight": d("0.200000"),
        "book_freshness_weight": d("0.150000"),
        "settlement_friction_weight": d("0.150000"),
        "manual_recheck_weight": d("0.150000"),
        "pass_combined_watch_score": d("0.700000"),
        "watch_combined_watch_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchMarketCostDepthCombinedWatchConfig(**values)


def watch_input(
    research_key: str = "combined-pass",
    *,
    fee_age_seconds: Decimal = d("1800.000000"),
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.510000"),
    bid_depth: Decimal = d("100.000000"),
    ask_depth: Decimal = d("100.000000"),
    book_observed_at: datetime | None = None,
    settlement_friction_rate: Decimal = d("0.002000"),
    manual_recheck_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketCostDepthCombinedWatchInput(
        research_key=research_key,
        fee_age_seconds=fee_age_seconds,
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        book_observed_at=(
            book_observed_at
            if book_observed_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        settlement_friction_rate=settlement_friction_rate,
        manual_recheck_urgency=manual_recheck_urgency,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_cost_depth_combined_watch_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_combined_watch_review() -> None:
    module = api()
    combined = report()

    assert module.COST_DEPTH_COMBINED_WATCH_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "COST_DEPTH_COMBINED_WATCH_STATUSES",
        "DEFAULT_RESEARCH_MARKET_COST_DEPTH_COMBINED_WATCH_REPORT_CONFIG_VERSION",
        "ResearchMarketCostDepthCombinedWatchConfig",
        "ResearchMarketCostDepthCombinedWatchInput",
        "ResearchMarketCostDepthCombinedWatchReasonCodeCount",
        "ResearchMarketCostDepthCombinedWatchReport",
        "ResearchMarketCostDepthCombinedWatchRow",
        "build_research_market_cost_depth_combined_watch_report",
        "research_market_cost_depth_combined_watch_report_digest",
        "research_market_cost_depth_combined_watch_report_payload",
    )
    assert type(combined) is module.ResearchMarketCostDepthCombinedWatchReport
    assert is_dataclass(combined)
    assert combined.generated_at == GENERATED_AT
    assert combined.config_version == (
        "research-market-cost-depth-combined-watch-report-v0"
    )
    assert combined.input_count == ZERO
    assert combined.pass_count == ZERO
    assert combined.watch_count == ZERO
    assert combined.block_count == ZERO
    assert combined.average_combined_watch_score is None
    assert combined.max_fee_age_seconds == ZERO
    assert combined.max_spread_stress == ZERO
    assert combined.min_depth_balance_score == ZERO
    assert combined.max_book_freshness_age_seconds == ZERO
    assert combined.max_settlement_friction_rate == ZERO
    assert combined.max_manual_recheck_urgency == ZERO
    assert combined.status == "block"
    assert combined.reason_codes == ("no_cost_depth_combined_watch_inputs",)
    assert combined.reason_code_counts == (
        module.ResearchMarketCostDepthCombinedWatchReasonCodeCount(
            reason_code="no_cost_depth_combined_watch_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert combined.rows == ()
    assert len(combined.derived_validation_digest) == 64
    assert combined.paper_only is True
    assert combined.report_only is True
    assert combined.readonly is True


def test_combined_watch_scores_pass_watch_and_block_inputs() -> None:
    combined = report(
        watch_input(
            "combined-watch",
            fee_age_seconds=d("7200.000000"),
            best_bid_price=d("0.480000"),
            best_ask_price=d("0.530000"),
            bid_depth=d("120.000000"),
            ask_depth=d("80.000000"),
            book_observed_at=GENERATED_AT - timedelta(seconds=300),
            settlement_friction_rate=d("0.010000"),
            manual_recheck_urgency=d("0.500000"),
        ),
        watch_input(
            "combined-block",
            fee_age_seconds=d("20000.000000"),
            best_bid_price=d("0.300000"),
            best_ask_price=d("0.450000"),
            bid_depth=d("200.000000"),
            ask_depth=d("20.000000"),
            book_observed_at=GENERATED_AT - timedelta(seconds=900),
            settlement_friction_rate=d("0.030000"),
            manual_recheck_urgency=d("0.900000"),
            reason_codes=("manual_combined_recheck",),
        ),
        watch_input("combined-pass"),
    )

    assert combined.input_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.average_combined_watch_score == d("0.476528")
    assert combined.max_fee_age_seconds == d("20000.000000")
    assert combined.max_spread_stress == d("0.150000")
    assert combined.min_depth_balance_score == d("0.100000")
    assert combined.max_book_freshness_age_seconds == d("900.000000")
    assert combined.max_settlement_friction_rate == d("0.030000")
    assert combined.max_manual_recheck_urgency == d("0.900000")
    assert combined.status == "block"
    assert combined.reason_codes == (
        "cost_depth_combined_watch_block",
        "fee_age_block",
        "spread_stress_block",
        "depth_imbalance_block",
        "book_freshness_block",
        "settlement_friction_block",
        "manual_recheck_urgency_block",
        "fee_age_watch",
        "spread_stress_watch",
        "depth_imbalance_watch",
        "book_freshness_watch",
        "settlement_friction_watch",
        "manual_recheck_urgency_watch",
    )

    block_row, pass_row, watch_row = combined.rows
    assert tuple(row.research_key for row in combined.rows) == (
        "combined-block",
        "combined-pass",
        "combined-watch",
    )
    assert tuple(row.status for row in combined.rows) == ("block", "pass", "watch")
    assert block_row.spread_stress == d("0.150000")
    assert block_row.depth_balance_score == d("0.100000")
    assert block_row.book_freshness_age_seconds == d("900.000000")
    assert block_row.combined_watch_score == d("0.035000")
    assert block_row.reason_codes == (
        "book_freshness_block",
        "cost_depth_combined_watch_block",
        "depth_imbalance_block",
        "fee_age_block",
        "input_manual_combined_recheck",
        "manual_recheck_urgency_block",
        "settlement_friction_block",
        "spread_stress_block",
    )
    assert pass_row.combined_watch_score == d("0.886250")
    assert pass_row.status == "pass"
    assert "manual_recheck_urgency_pass" in pass_row.reason_codes
    assert watch_row.combined_watch_score == d("0.508333")
    assert watch_row.status == "watch"
    assert "fee_age_watch" in watch_row.reason_codes
    assert "spread_stress_watch" in watch_row.reason_codes
    assert "depth_imbalance_watch" in watch_row.reason_codes
    assert "book_freshness_watch" in watch_row.reason_codes
    assert "settlement_friction_watch" in watch_row.reason_codes
    assert "manual_recheck_urgency_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        watch_input("combined-z", reason_codes=("zeta", "alpha")),
        watch_input("combined-a"),
    )
    second = report(
        watch_input("combined-a"),
        watch_input("combined-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_cost_depth_combined_watch_report_payload(first)
    second_payload = module.research_market_cost_depth_combined_watch_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_cost_depth_combined_watch_report_digest(first) == (
        first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["research_key"] == "combined-a"
    assert first_payload["rows"][0]["spread_stress"] == "0.020000"
    assert first_payload["rows"][0]["combined_watch_score"] == "0.886250"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "recommend" not in encoded.lower()
    assert "sizing" not in encoded.lower()
    assert "trade" not in encoded.lower()
    assert "order" not in encoded.lower()
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(watch_input())

    for value in (config(), watch_input(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_age",
                    "_balance",
                    "_count",
                    "_friction",
                    "_rate",
                    "_ratio",
                    "_score",
                    "_seconds",
                    "_stress",
                    "_urgency",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].combined_watch_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_pass_fee_age_seconds"):
        config(max_pass_fee_age_seconds=DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="max_watch_spread_stress"):
        config(max_watch_spread_stress=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="combined watch weights"):
        config(manual_recheck_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(watch_input(), generated_at=datetime(2026, 7, 8, 20, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            watch_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="book_observed_at"):
        report(watch_input(book_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="research_key"):
        watch_input(" raw-market")
    with pytest.raises(ValueError, match="research_key"):
        watch_input("market_slug_alpha")
    with pytest.raises(ValueError, match="fee_age_seconds"):
        watch_input(fee_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="best_ask_price"):
        watch_input(best_bid_price=d("0.520000"), best_ask_price=d("0.510000"))
    with pytest.raises(ValueError, match="bid_depth"):
        watch_input(bid_depth=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="book_observed_at"):
        watch_input(book_observed_at=datetime(2026, 7, 8, 20, 0))
    with pytest.raises(ValueError, match="settlement_friction_rate"):
        watch_input(settlement_friction_rate=d("1.100000"))
    with pytest.raises(ValueError, match="manual_recheck_urgency"):
        watch_input(manual_recheck_urgency=-d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        watch_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        watch_input(reason_codes=("source_url_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(watch_input(), paper_only=False)
    with pytest.raises(ValueError, match="combined_watch_score"):
        replace(populated.rows[0], combined_watch_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_cost_depth_combined_watch_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_raw_market_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_depth_combined_watch_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "market_id",
        "market_slug",
        "question",
        "condition_id",
        "token_id",
        "source_url",
        "source_text",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "condition_id",
        "execution",
        "market_id",
        "market_slug",
        "question",
        "raw_text",
        "source_reference",
        "source_text",
        "source_url",
        "token_id",
    }
