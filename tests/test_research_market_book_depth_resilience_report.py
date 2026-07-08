from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_book_depth_resilience_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_BOOK_DEPTH_RESILIENCE_REPORT_CONFIG_VERSION
        ),
        "min_pass_depth_balance": d("0.700000"),
        "min_watch_depth_balance": d("0.400000"),
        "max_pass_spread_stress": d("0.030000"),
        "max_watch_spread_stress": d("0.080000"),
        "max_pass_freshness_age_seconds": d("120.000000"),
        "max_watch_freshness_age_seconds": d("600.000000"),
        "max_pass_fee_rate": d("0.020000"),
        "max_watch_fee_rate": d("0.050000"),
        "max_pass_manual_recheck_urgency": d("0.300000"),
        "max_watch_manual_recheck_urgency": d("0.700000"),
        "depth_balance_weight": d("0.300000"),
        "spread_resilience_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "fee_friction_weight": d("0.150000"),
        "manual_recheck_weight": d("0.100000"),
        "pass_resilience_score": d("0.700000"),
        "watch_resilience_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchMarketBookDepthResilienceConfig(**values)


def depth_input(
    research_key: str = "resilience-pass",
    *,
    observed_at: datetime | None = None,
    bid_depth: Decimal = d("100.000000"),
    ask_depth: Decimal = d("100.000000"),
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.510000"),
    fee_rate: Decimal = d("0.010000"),
    manual_recheck_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketBookDepthResilienceInput(
        research_key=research_key,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(seconds=60)
        ),
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        fee_rate=fee_rate,
        manual_recheck_urgency=manual_recheck_urgency,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_book_depth_resilience_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_depth_resilience_review() -> None:
    module = api()
    resilience = report()

    assert module.BOOK_DEPTH_RESILIENCE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "BOOK_DEPTH_RESILIENCE_STATUSES",
        "DEFAULT_RESEARCH_MARKET_BOOK_DEPTH_RESILIENCE_REPORT_CONFIG_VERSION",
        "ResearchMarketBookDepthResilienceConfig",
        "ResearchMarketBookDepthResilienceInput",
        "ResearchMarketBookDepthResilienceReasonCodeCount",
        "ResearchMarketBookDepthResilienceReport",
        "ResearchMarketBookDepthResilienceRow",
        "build_research_market_book_depth_resilience_report",
        "research_market_book_depth_resilience_report_digest",
        "research_market_book_depth_resilience_report_payload",
    )
    assert type(resilience) is module.ResearchMarketBookDepthResilienceReport
    assert is_dataclass(resilience)
    assert resilience.generated_at == GENERATED_AT
    assert resilience.config_version == "research-market-book-depth-resilience-report-v0"
    assert resilience.input_count == ZERO
    assert resilience.pass_count == ZERO
    assert resilience.watch_count == ZERO
    assert resilience.block_count == ZERO
    assert resilience.average_resilience_score is None
    assert resilience.min_depth_balance_score == ZERO
    assert resilience.max_spread_stress == ZERO
    assert resilience.max_freshness_age_seconds == ZERO
    assert resilience.max_fee_rate == ZERO
    assert resilience.max_manual_recheck_urgency == ZERO
    assert resilience.status == "block"
    assert resilience.reason_codes == ("no_book_depth_resilience_inputs",)
    assert resilience.reason_code_counts == (
        module.ResearchMarketBookDepthResilienceReasonCodeCount(
            reason_code="no_book_depth_resilience_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert resilience.rows == ()
    assert len(resilience.derived_validation_digest) == 64
    assert resilience.paper_only is True
    assert resilience.report_only is True
    assert resilience.readonly is True


def test_depth_resilience_scores_pass_watch_and_block_inputs() -> None:
    resilience = report(
        depth_input(
            "resilience-watch",
            observed_at=GENERATED_AT - timedelta(seconds=300),
            bid_depth=d("120.000000"),
            ask_depth=d("80.000000"),
            best_bid_price=d("0.480000"),
            best_ask_price=d("0.530000"),
            fee_rate=d("0.030000"),
            manual_recheck_urgency=d("0.500000"),
        ),
        depth_input(
            "resilience-block",
            observed_at=GENERATED_AT - timedelta(seconds=900),
            bid_depth=d("200.000000"),
            ask_depth=d("20.000000"),
            best_bid_price=d("0.300000"),
            best_ask_price=d("0.450000"),
            fee_rate=d("0.070000"),
            manual_recheck_urgency=d("0.900000"),
            reason_codes=("manual_depth_recheck",),
        ),
        depth_input("resilience-pass"),
    )

    assert resilience.input_count == d("3.000000")
    assert resilience.pass_count == d("1.000000")
    assert resilience.watch_count == d("1.000000")
    assert resilience.block_count == d("1.000000")
    assert resilience.average_resilience_score == d("0.473750")
    assert resilience.min_depth_balance_score == d("0.100000")
    assert resilience.max_spread_stress == d("0.150000")
    assert resilience.max_freshness_age_seconds == d("900.000000")
    assert resilience.max_fee_rate == d("0.070000")
    assert resilience.max_manual_recheck_urgency == d("0.900000")
    assert resilience.status == "block"
    assert resilience.reason_codes == (
        "market_book_depth_resilience_block",
        "depth_balance_block",
        "spread_stress_block",
        "freshness_age_block",
        "fee_friction_block",
        "manual_recheck_urgency_block",
        "depth_balance_watch",
        "spread_stress_watch",
        "freshness_age_watch",
        "fee_friction_watch",
        "manual_recheck_urgency_watch",
    )

    block_row, pass_row, watch_row = resilience.rows
    assert tuple(row.research_key for row in resilience.rows) == (
        "resilience-block",
        "resilience-pass",
        "resilience-watch",
    )
    assert tuple(row.status for row in resilience.rows) == ("block", "pass", "watch")
    assert block_row.depth_balance_score == d("0.100000")
    assert block_row.spread_stress == d("0.150000")
    assert block_row.freshness_age_seconds == d("900.000000")
    assert block_row.resilience_score == d("0.040000")
    assert block_row.reason_codes == (
        "depth_balance_block",
        "fee_friction_block",
        "freshness_age_block",
        "input_manual_depth_recheck",
        "manual_recheck_urgency_block",
        "market_book_depth_resilience_block",
        "spread_stress_block",
    )
    assert pass_row.resilience_score == d("0.877500")
    assert pass_row.status == "pass"
    assert "spread_stress_pass" in pass_row.reason_codes
    assert watch_row.depth_balance_score == d("0.666667")
    assert watch_row.resilience_score == d("0.503750")
    assert watch_row.status == "watch"
    assert "depth_balance_watch" in watch_row.reason_codes
    assert "spread_stress_watch" in watch_row.reason_codes
    assert "freshness_age_watch" in watch_row.reason_codes
    assert "fee_friction_watch" in watch_row.reason_codes
    assert "manual_recheck_urgency_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        depth_input("resilience-z", reason_codes=("zeta", "alpha")),
        depth_input("resilience-a"),
    )
    second = report(
        depth_input("resilience-a"),
        depth_input("resilience-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_book_depth_resilience_report_payload(first)
    second_payload = module.research_market_book_depth_resilience_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_book_depth_resilience_report_digest(first) == (
        first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["research_key"] == "resilience-a"
    assert first_payload["rows"][0]["spread_stress"] == "0.020000"
    assert first_payload["rows"][0]["resilience_score"] == "0.877500"
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
    populated = report(depth_input())

    for value in (config(), depth_input(), populated, *populated.rows, *populated.reason_code_counts):
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
        populated.rows[0].resilience_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="min_pass_depth_balance"):
        config(min_pass_depth_balance=DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="max_watch_spread_stress"):
        config(max_watch_spread_stress=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(depth_input(), generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            depth_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(depth_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="research_key"):
        depth_input(" raw-depth")
    with pytest.raises(ValueError, match="bid_depth"):
        depth_input(bid_depth=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        depth_input(observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="best_bid_price"):
        depth_input(best_bid_price=d("1.100000"))
    with pytest.raises(ValueError, match="best_ask_price"):
        depth_input(best_bid_price=d("0.520000"), best_ask_price=d("0.510000"))
    with pytest.raises(ValueError, match="fee_rate"):
        depth_input(fee_rate=d("1.100000"))
    with pytest.raises(ValueError, match="manual_recheck_urgency"):
        depth_input(manual_recheck_urgency=-d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        depth_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(depth_input(), paper_only=False)
    with pytest.raises(ValueError, match="resilience_score"):
        replace(populated.rows[0], resilience_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_book_depth_resilience_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_raw_market_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_book_depth_resilience_report.py"
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
