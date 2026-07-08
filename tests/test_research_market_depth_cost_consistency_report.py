from __future__ import annotations

import hashlib
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
        "polymarket_alpha_lab.research_market_depth_cost_consistency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_COST_CONSISTENCY_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_available_depth": d("1000.000000"),
        "minimum_watch_available_depth": d("250.000000"),
        "maximum_pass_spread_ratio": d("0.030000"),
        "maximum_watch_spread_ratio": d("0.080000"),
        "maximum_pass_slippage_ratio": d("0.020000"),
        "maximum_watch_slippage_ratio": d("0.060000"),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "maximum_pass_quote_age_seconds": d("120.000000"),
        "maximum_watch_quote_age_seconds": d("600.000000"),
        "depth_weight": d("0.250000"),
        "spread_weight": d("0.200000"),
        "slippage_weight": d("0.200000"),
        "fee_drag_weight": d("0.150000"),
        "quote_freshness_weight": d("0.200000"),
        "pass_consistency_score": d("0.750000"),
        "watch_consistency_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthCostConsistencyConfig(**values)


def consistency_input(
    bucket_label: str = "depth-cost-pass",
    *,
    quote_observed_at: datetime | None = None,
    available_depth: Decimal = d("1500.000000"),
    spread_ratio: Decimal = d("0.010000"),
    slippage_ratio: Decimal = d("0.005000"),
    fee_drag_ratio: Decimal = d("0.002000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketDepthCostConsistencyInput(
        bucket_label=bucket_label,
        quote_observed_at=(
            quote_observed_at
            if quote_observed_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        available_depth=available_depth,
        spread_ratio=spread_ratio,
        slippage_ratio=slippage_ratio,
        fee_drag_ratio=fee_drag_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_depth_cost_consistency_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_depth_cost_consistency_review() -> None:
    module = api()
    empty = report()

    assert module.MARKET_DEPTH_COST_CONSISTENCY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "MARKET_DEPTH_COST_CONSISTENCY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_DEPTH_COST_CONSISTENCY_REPORT_CONFIG_VERSION",
        "ResearchMarketDepthCostConsistencyConfig",
        "ResearchMarketDepthCostConsistencyInput",
        "ResearchMarketDepthCostConsistencyReasonCodeCount",
        "ResearchMarketDepthCostConsistencyReport",
        "ResearchMarketDepthCostConsistencyRow",
        "build_research_market_depth_cost_consistency_report",
        "research_market_depth_cost_consistency_report_digest",
        "research_market_depth_cost_consistency_report_payload",
    )
    assert type(empty) is module.ResearchMarketDepthCostConsistencyReport
    assert is_dataclass(empty)
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == "research-market-depth-cost-consistency-report-v0"
    assert empty.input_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.low_depth_count == ZERO
    assert empty.wide_spread_count == ZERO
    assert empty.high_slippage_count == ZERO
    assert empty.high_fee_drag_count == ZERO
    assert empty.stale_quote_count == ZERO
    assert empty.average_consistency_score is None
    assert empty.min_available_depth == ZERO
    assert empty.max_spread_ratio == ZERO
    assert empty.max_slippage_ratio == ZERO
    assert empty.max_fee_drag_ratio == ZERO
    assert empty.max_quote_age_seconds == ZERO
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_depth_cost_consistency_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketDepthCostConsistencyReasonCodeCount(
            reason_code="no_depth_cost_consistency_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_pass_watch_and_block_depth_cost_consistency_inputs() -> None:
    combined = report(
        consistency_input(
            "alpha-block",
            quote_observed_at=GENERATED_AT - timedelta(seconds=900),
            available_depth=d("100.000000"),
            spread_ratio=d("0.100000"),
            slippage_ratio=d("0.080000"),
            fee_drag_ratio=d("0.040000"),
            reason_codes=("manual_cost_check",),
        ),
        consistency_input("beta-pass"),
        consistency_input(
            "gamma-watch",
            quote_observed_at=GENERATED_AT - timedelta(seconds=300),
            available_depth=d("800.000000"),
            spread_ratio=d("0.050000"),
            slippage_ratio=d("0.030000"),
            fee_drag_ratio=d("0.015000"),
        ),
    )

    assert combined.input_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.low_depth_count == d("2.000000")
    assert combined.wide_spread_count == d("2.000000")
    assert combined.high_slippage_count == d("2.000000")
    assert combined.high_fee_drag_count == d("2.000000")
    assert combined.stale_quote_count == d("2.000000")
    assert combined.average_consistency_score == d("0.501111")
    assert combined.min_available_depth == d("100.000000")
    assert combined.max_spread_ratio == d("0.100000")
    assert combined.max_slippage_ratio == d("0.080000")
    assert combined.max_fee_drag_ratio == d("0.040000")
    assert combined.max_quote_age_seconds == d("900.000000")
    assert combined.status == "block"
    assert combined.reason_codes == (
        "depth_cost_consistency_block",
        "available_depth_block",
        "spread_cost_block",
        "slippage_cost_block",
        "fee_drag_block",
        "quote_freshness_block",
        "available_depth_watch",
        "spread_cost_watch",
        "slippage_cost_watch",
        "fee_drag_watch",
        "quote_freshness_watch",
    )

    block_row, pass_row, watch_row = combined.rows
    assert tuple(row.public_row_ref for row in combined.rows) == (
        "depth_cost_group_001",
        "depth_cost_group_002",
        "depth_cost_group_003",
    )
    assert tuple(row.status for row in combined.rows) == ("block", "pass", "watch")
    assert block_row.available_depth == d("100.000000")
    assert block_row.depth_score == d("0.100000")
    assert block_row.quote_age_seconds == d("900.000000")
    assert block_row.consistency_score == d("0.025000")
    assert block_row.reason_codes == (
        "available_depth_block",
        "depth_cost_consistency_block",
        "fee_drag_block",
        "input_manual_cost_check",
        "quote_freshness_block",
        "slippage_cost_block",
        "spread_cost_block",
    )
    assert pass_row.consistency_score == d("0.928333")
    assert pass_row.status == "pass"
    assert "fee_drag_pass" in pass_row.reason_codes
    assert watch_row.consistency_score == d("0.550000")
    assert watch_row.status == "watch"
    assert "available_depth_watch" in watch_row.reason_codes
    assert "spread_cost_watch" in watch_row.reason_codes
    assert "slippage_cost_watch" in watch_row.reason_codes
    assert "fee_drag_watch" in watch_row.reason_codes
    assert "quote_freshness_watch" in watch_row.reason_codes


def test_custom_consistency_weights_build_valid_report() -> None:
    weighted = report(
        consistency_input(
            available_depth=d("500.000000"),
            spread_ratio=d("0.040000"),
            slippage_ratio=d("0.015000"),
            fee_drag_ratio=d("0.008000"),
        ),
        cfg=config(
            depth_weight=d("0.100000"),
            spread_weight=d("0.300000"),
            slippage_weight=d("0.250000"),
            fee_drag_weight=d("0.150000"),
            quote_freshness_weight=d("0.200000"),
        ),
    )

    assert weighted.input_count == d("1.000000")
    assert weighted.rows[0].consistency_score == d("0.677500")
    assert weighted.average_consistency_score == d("0.677500")
    assert weighted.rows[0].status == "watch"
    assert weighted.status == "watch"


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        consistency_input("zulu-depth-cost", reason_codes=("zeta", "alpha")),
        consistency_input("alpha-depth-cost"),
    )
    second = report(
        consistency_input("alpha-depth-cost"),
        consistency_input("zulu-depth-cost", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_depth_cost_consistency_report_payload(first)
    second_payload = module.research_market_depth_cost_consistency_report_payload(second)
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    public_encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_market_depth_cost_consistency_report_digest(first) == digest
    assert first.derived_validation_digest == digest
    assert first_payload["derived_validation_digest"] == digest
    assert first_payload["rows"][0]["public_row_ref"] == "depth_cost_group_001"
    assert first_payload["rows"][0]["available_depth"] == "1500.000000"
    assert first_payload["rows"][0]["consistency_score"] == "0.928333"
    assert "alpha-depth-cost" not in public_encoded
    assert "zulu-depth-cost" not in public_encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in public_encoded
    assert "buy" not in public_encoded.lower()
    assert "sell" not in public_encoded.lower()
    assert "recommend" not in public_encoded.lower()
    assert "sizing" not in public_encoded.lower()
    assert "trade" not in public_encoded.lower()
    assert "order" not in public_encoded.lower()
    assert not any(
        _has_forbidden_public_surface(value)
        for value in _walk_payload_keys(first_payload) + _walk_payload_strings(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(consistency_input())

    for value in (config(), consistency_input(), populated, *populated.rows, *populated.reason_code_counts):
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
                        "_age_seconds",
                        "_count",
                        "_depth",
                        "_drag_ratio",
                        "_ratio",
                        "_score",
                        "_seconds",
                        "_weight",
                    ),
                ):
                    assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].consistency_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="minimum_pass_available_depth"):
        config(minimum_pass_available_depth=DecimalSubclass("1000.000000"))
    with pytest.raises(ValueError, match="maximum_watch_spread_ratio"):
        config(maximum_watch_spread_ratio=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights"):
        config(quote_freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(consistency_input(), generated_at=datetime(2026, 7, 8, 20, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            consistency_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="quote_observed_at"):
        report(
            consistency_input(quote_observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="bucket_label"):
        consistency_input(" market-id")
    with pytest.raises(ValueError, match="bucket_label"):
        consistency_input("market_id_alpha")
    with pytest.raises(ValueError, match="bucket_label"):
        consistency_input("market_slug_alpha")
    with pytest.raises(ValueError, match="available_depth"):
        consistency_input(available_depth=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quote_observed_at"):
        consistency_input(quote_observed_at=datetime(2026, 7, 8, 20, 0))
    with pytest.raises(ValueError, match="spread_ratio"):
        consistency_input(spread_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="slippage_ratio"):
        consistency_input(slippage_ratio=-d("0.100000"))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        consistency_input(fee_drag_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        consistency_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        consistency_input(reason_codes=("source_url_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(consistency_input(), paper_only=False)
    with pytest.raises(ValueError, match="consistency_score"):
        replace(populated.rows[0], consistency_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_depth_cost_consistency_report_payload(object())
    with pytest.raises(ValueError, match="readonly"):
        replace(populated, readonly=False)


def test_owned_module_has_no_raw_market_decision_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_cost_consistency_report.py"
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
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
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


def _walk_payload_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def _has_forbidden_public_surface(value: str) -> bool:
    lowered = value.lower()
    return any(
        term in lowered
        for term in (
            "candidate_id",
            "condition_id",
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
        )
    )
