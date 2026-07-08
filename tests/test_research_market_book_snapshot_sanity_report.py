from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_book_snapshot_sanity_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_BOOK_SNAPSHOT_SANITY_REPORT_CONFIG_VERSION
        ),
        "max_pass_depth_age_seconds": d("120.000000"),
        "max_watch_depth_age_seconds": d("600.000000"),
        "max_pass_spread": d("0.030000"),
        "max_watch_spread": d("0.080000"),
        "max_pass_stale_quote_pressure": d("0.250000"),
        "max_watch_stale_quote_pressure": d("0.650000"),
        "max_pass_fee_cost_age_seconds": d("3600.000000"),
        "max_watch_fee_cost_age_seconds": d("14400.000000"),
        "max_pass_manual_recheck_urgency": d("0.300000"),
        "max_watch_manual_recheck_urgency": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchMarketBookSnapshotSanityConfig(**values)


def snapshot(
    research_key: str = "snapshot-pass",
    *,
    depth_age_seconds: Decimal = d("60.000000"),
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.510000"),
    stale_quote_pressure: Decimal = d("0.100000"),
    fee_cost_age_seconds: Decimal = d("1800.000000"),
    manual_recheck_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketBookSnapshotSanityInput(
        research_key=research_key,
        depth_age_seconds=depth_age_seconds,
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        stale_quote_pressure=stale_quote_pressure,
        fee_cost_age_seconds=fee_cost_age_seconds,
        manual_recheck_urgency=manual_recheck_urgency,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_book_snapshot_sanity_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_snapshot_sanity_review() -> None:
    module = api()
    sanity = report()

    assert module.BOOK_SNAPSHOT_SANITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "BOOK_SNAPSHOT_SANITY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_BOOK_SNAPSHOT_SANITY_REPORT_CONFIG_VERSION",
        "ResearchMarketBookSnapshotSanityConfig",
        "ResearchMarketBookSnapshotSanityInput",
        "ResearchMarketBookSnapshotSanityReasonCodeCount",
        "ResearchMarketBookSnapshotSanityReport",
        "ResearchMarketBookSnapshotSanityRow",
        "build_research_market_book_snapshot_sanity_report",
        "research_market_book_snapshot_sanity_report_digest",
        "research_market_book_snapshot_sanity_report_payload",
    )
    assert type(sanity) is module.ResearchMarketBookSnapshotSanityReport
    assert is_dataclass(sanity)
    assert sanity.generated_at == GENERATED_AT
    assert sanity.config_version == "research-market-book-snapshot-sanity-report-v0"
    assert sanity.input_count == ZERO
    assert sanity.pass_count == ZERO
    assert sanity.watch_count == ZERO
    assert sanity.block_count == ZERO
    assert sanity.average_snapshot_sanity_score is None
    assert sanity.max_depth_age_seconds == ZERO
    assert sanity.max_spread == ZERO
    assert sanity.max_stale_quote_pressure == ZERO
    assert sanity.max_fee_cost_age_seconds == ZERO
    assert sanity.max_manual_recheck_urgency == ZERO
    assert sanity.status == "block"
    assert sanity.reason_codes == ("no_book_snapshot_sanity_inputs",)
    assert sanity.reason_code_counts == (
        module.ResearchMarketBookSnapshotSanityReasonCodeCount(
            reason_code="no_book_snapshot_sanity_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert sanity.rows == ()
    assert sanity.paper_only is True
    assert sanity.report_only is True
    assert sanity.readonly is True


def test_snapshot_sanity_scores_pass_watch_and_block_inputs() -> None:
    sanity = report(
        snapshot(
            "snapshot-watch",
            depth_age_seconds=d("300.000000"),
            best_bid_price=d("0.480000"),
            best_ask_price=d("0.530000"),
            stale_quote_pressure=d("0.400000"),
            fee_cost_age_seconds=d("7200.000000"),
            manual_recheck_urgency=d("0.500000"),
        ),
        snapshot(
            "snapshot-block",
            depth_age_seconds=d("900.000000"),
            best_bid_price=d("0.350000"),
            best_ask_price=d("0.450000"),
            stale_quote_pressure=d("0.800000"),
            fee_cost_age_seconds=d("20000.000000"),
            manual_recheck_urgency=d("0.900000"),
            reason_codes=("manual_snapshot_recheck",),
        ),
        snapshot("snapshot-pass"),
    )

    assert sanity.input_count == d("3.000000")
    assert sanity.pass_count == d("1.000000")
    assert sanity.watch_count == d("1.000000")
    assert sanity.block_count == d("1.000000")
    assert sanity.average_snapshot_sanity_score == d("0.473333")
    assert sanity.max_depth_age_seconds == d("900.000000")
    assert sanity.max_spread == d("0.100000")
    assert sanity.max_stale_quote_pressure == d("0.800000")
    assert sanity.max_fee_cost_age_seconds == d("20000.000000")
    assert sanity.max_manual_recheck_urgency == d("0.900000")
    assert sanity.status == "block"
    assert sanity.reason_codes == (
        "book_snapshot_sanity_block",
        "depth_freshness_block",
        "spread_plausibility_block",
        "stale_quote_pressure_block",
        "fee_cost_freshness_block",
        "manual_recheck_urgency_block",
        "depth_freshness_watch",
        "spread_plausibility_watch",
        "stale_quote_pressure_watch",
        "fee_cost_freshness_watch",
        "manual_recheck_urgency_watch",
    )

    block_row, pass_row, watch_row = sanity.rows
    assert tuple(row.research_key for row in sanity.rows) == (
        "snapshot-block",
        "snapshot-pass",
        "snapshot-watch",
    )
    assert tuple(row.status for row in sanity.rows) == ("block", "pass", "watch")
    assert block_row.spread == d("0.100000")
    assert block_row.snapshot_sanity_score == d("0.060000")
    assert block_row.reason_codes == (
        "book_snapshot_sanity_block",
        "depth_freshness_block",
        "fee_cost_freshness_block",
        "input_manual_snapshot_recheck",
        "manual_recheck_urgency_block",
        "manual_snapshot_recheck_block",
        "spread_plausibility_block",
        "stale_quote_pressure_block",
    )
    assert pass_row.snapshot_sanity_score == d("0.865000")
    assert pass_row.status == "pass"
    assert "manual_snapshot_recheck_pass" in pass_row.reason_codes
    assert watch_row.snapshot_sanity_score == d("0.495000")
    assert watch_row.status == "watch"
    assert "depth_freshness_watch" in watch_row.reason_codes
    assert "spread_plausibility_watch" in watch_row.reason_codes
    assert "stale_quote_pressure_watch" in watch_row.reason_codes
    assert "fee_cost_freshness_watch" in watch_row.reason_codes
    assert "manual_recheck_urgency_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        snapshot("snapshot-z", reason_codes=("zeta", "alpha")),
        snapshot("snapshot-a"),
    )
    second = report(
        snapshot("snapshot-a"),
        snapshot("snapshot-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_book_snapshot_sanity_report_payload(first)
    second_payload = module.research_market_book_snapshot_sanity_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_book_snapshot_sanity_report_digest(first) == (
        module.research_market_book_snapshot_sanity_report_digest(second)
    )
    assert len(module.research_market_book_snapshot_sanity_report_digest(first)) == 64
    assert first_payload["rows"][0]["research_key"] == "snapshot-a"
    assert first_payload["rows"][0]["spread"] == "0.020000"
    assert first_payload["rows"][0]["snapshot_sanity_score"] == "0.865000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "trade" not in encoded.lower()
    assert "order" not in encoded.lower()
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    module = api()
    populated = report(snapshot())

    for value in (config(), snapshot(), populated, *populated.rows, *populated.reason_code_counts):
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
                    "_count",
                    "_score",
                    "_price",
                    "_seconds",
                    "_pressure",
                    "_urgency",
                    "_ratio",
                    "spread",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].snapshot_sanity_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_pass_depth_age_seconds"):
        config(max_pass_depth_age_seconds=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_depth_age_seconds"):
        config(max_watch_depth_age_seconds=_DecimalSubclass("600.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="research_key"):
        snapshot(" raw-snapshot")
    with pytest.raises(ValueError, match="depth_age_seconds"):
        snapshot(depth_age_seconds=60)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="best_bid_price"):
        snapshot(best_bid_price=d("1.100000"))
    with pytest.raises(ValueError, match="best_ask_price"):
        snapshot(best_bid_price=d("0.520000"), best_ask_price=d("0.510000"))
    with pytest.raises(ValueError, match="stale_quote_pressure"):
        snapshot(stale_quote_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="manual_recheck_urgency"):
        snapshot(manual_recheck_urgency=-d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        snapshot(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot(), paper_only=False)
    with pytest.raises(ValueError, match="snapshot_sanity_score"):
        replace(populated.rows[0], snapshot_sanity_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="report"):
        module.research_market_book_snapshot_sanity_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_side_effect_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_book_snapshot_sanity_report.py"
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
