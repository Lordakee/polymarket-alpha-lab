from __future__ import annotations

import ast
import hashlib
import importlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_orderbook_spread_stability_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_orderbook_spread_stability_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_ORDERBOOK_SPREAD_STABILITY_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_spread_bps": d("100.000000"),
        "maximum_watch_spread_bps": d("500.000000"),
        "maximum_pass_depth_change_ratio": d("0.100000"),
        "maximum_watch_depth_change_ratio": d("0.300000"),
        "maximum_pass_snapshot_age_seconds": d("60.000000"),
        "maximum_watch_snapshot_age_seconds": d("300.000000"),
        "maximum_pass_fee_pressure_bps": d("50.000000"),
        "maximum_watch_fee_pressure_bps": d("150.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketOrderbookSpreadStabilityConfig(**values)


def snapshot(
    snapshot_label: str = "spread-stability-pass",
    *,
    observed_at: datetime | None = None,
    best_bid_price: Decimal = d("0.499000"),
    best_ask_price: Decimal = d("0.501000"),
    bid_depth: Decimal = d("1050.000000"),
    ask_depth: Decimal = d("950.000000"),
    previous_bid_depth: Decimal = d("1000.000000"),
    previous_ask_depth: Decimal = d("1000.000000"),
    fee_pressure_bps: Decimal = d("25.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketOrderbookSpreadStabilitySnapshot(
        snapshot_label=snapshot_label,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=30),
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        bid_depth=bid_depth,
        ask_depth=ask_depth,
        previous_bid_depth=previous_bid_depth,
        previous_ask_depth=previous_ask_depth,
        fee_pressure_bps=fee_pressure_bps,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_orderbook_spread_stability_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def resign(payload: dict[str, Any]) -> None:
    unsigned = deepcopy(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    payload["derived_validation_digest"] = hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()


def test_empty_report_is_blocked_readonly_and_digest_validated() -> None:
    module = api()
    empty = report()

    assert module.ORDERBOOK_SPREAD_STABILITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "ORDERBOOK_SPREAD_STABILITY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_ORDERBOOK_SPREAD_STABILITY_REPORT_CONFIG_VERSION",
        "ResearchMarketOrderbookSpreadStabilityConfig",
        "ResearchMarketOrderbookSpreadStabilitySnapshot",
        "ResearchMarketOrderbookSpreadStabilityReasonCodeCount",
        "ResearchMarketOrderbookSpreadStabilityReport",
        "ResearchMarketOrderbookSpreadStabilityRow",
        "build_research_market_orderbook_spread_stability_report",
        "research_market_orderbook_spread_stability_report_digest",
        "research_market_orderbook_spread_stability_report_payload",
        "validate_research_market_orderbook_spread_stability_report_payload",
    )
    assert type(empty) is module.ResearchMarketOrderbookSpreadStabilityReport
    assert is_dataclass(empty)
    assert empty.generated_at == GENERATED_AT
    assert empty.config == config()
    assert empty.snapshot_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.wide_spread_count == d("0")
    assert empty.bid_depth_change_count == d("0")
    assert empty.ask_depth_change_count == d("0")
    assert empty.stale_snapshot_count == d("0")
    assert empty.fee_pressure_count == d("0")
    assert empty.average_spread_bps is None
    assert empty.average_abs_bid_depth_change_ratio is None
    assert empty.average_abs_ask_depth_change_ratio is None
    assert empty.max_spread_bps == d("0.000000")
    assert empty.max_snapshot_age_seconds == d("0.000000")
    assert empty.max_fee_pressure_bps == d("0.000000")
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_spread_stability_snapshots",)
    assert empty.reason_code_counts == (
        module.ResearchMarketOrderbookSpreadStabilityReasonCodeCount(
            reason_code="no_spread_stability_snapshots",
            count=d("1"),
            row_ratio=d("0.000000"),
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    payload = module.research_market_orderbook_spread_stability_report_payload(empty)
    assert module.validate_research_market_orderbook_spread_stability_report_payload(
        payload,
    )


def test_reducer_classifies_stability_and_summarizes_supplied_snapshots() -> None:
    module = api()
    combined = report(
        snapshot(
            "alpha-block",
            observed_at=GENERATED_AT - timedelta(seconds=600),
            best_bid_price=d("0.450000"),
            best_ask_price=d("0.550000"),
            bid_depth=d("500.000000"),
            ask_depth=d("1500.000000"),
            fee_pressure_bps=d("250.000000"),
            reason_codes=("manual_check",),
        ),
        snapshot("beta-pass"),
        snapshot(
            "gamma-watch",
            observed_at=GENERATED_AT - timedelta(seconds=180),
            best_bid_price=d("0.490000"),
            best_ask_price=d("0.510000"),
            bid_depth=d("800.000000"),
            ask_depth=d("1200.000000"),
            fee_pressure_bps=d("100.000000"),
        ),
    )

    assert combined.snapshot_count == d("3")
    assert combined.pass_count == d("1")
    assert combined.watch_count == d("1")
    assert combined.block_count == d("1")
    assert combined.wide_spread_count == d("2")
    assert combined.bid_depth_change_count == d("2")
    assert combined.ask_depth_change_count == d("2")
    assert combined.stale_snapshot_count == d("2")
    assert combined.fee_pressure_count == d("2")
    assert combined.average_spread_bps == d("813.333333")
    assert combined.average_abs_bid_depth_change_ratio == d("0.250000")
    assert combined.average_abs_ask_depth_change_ratio == d("0.250000")
    assert combined.max_spread_bps == d("2000.000000")
    assert combined.max_snapshot_age_seconds == d("600.000000")
    assert combined.max_fee_pressure_bps == d("250.000000")
    assert combined.status == "block"
    assert combined.reason_codes == (
        "spread_stability_report_block",
        "spread_bps_block",
        "bid_depth_change_block",
        "ask_depth_change_block",
        "snapshot_age_block",
        "fee_pressure_block",
        "spread_bps_watch",
        "bid_depth_change_watch",
        "ask_depth_change_watch",
        "snapshot_age_watch",
        "fee_pressure_watch",
    )

    block_row, pass_row, watch_row = combined.rows
    assert tuple(row.public_row_ref for row in combined.rows) == (
        "spread_stability_snapshot_001",
        "spread_stability_snapshot_002",
        "spread_stability_snapshot_003",
    )
    assert tuple(row.stability_bucket for row in combined.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert block_row.spread_bps == d("2000.000000")
    assert block_row.bid_depth_change_ratio == d("-0.500000")
    assert block_row.ask_depth_change_ratio == d("0.500000")
    assert block_row.snapshot_age_seconds == d("600.000000")
    assert block_row.reason_codes == (
        "spread_stability_block",
        "spread_bps_block",
        "bid_depth_change_block",
        "ask_depth_change_block",
        "snapshot_age_block",
        "fee_pressure_block",
        "input_manual_check",
    )
    assert pass_row.spread_bps == d("40.000000")
    assert pass_row.stability_bucket == "pass"
    assert pass_row.reason_codes == (
        "spread_stability_pass",
        "spread_bps_pass",
        "bid_depth_change_pass",
        "ask_depth_change_pass",
        "snapshot_age_pass",
        "fee_pressure_pass",
    )
    assert watch_row.spread_bps == d("400.000000")
    assert watch_row.bid_depth_change_ratio == d("-0.200000")
    assert watch_row.ask_depth_change_ratio == d("0.200000")
    assert watch_row.stability_bucket == "watch"

    counts = {item.reason_code: item for item in combined.reason_code_counts}
    assert counts["spread_bps_watch"].count == d("1")
    assert counts["spread_bps_block"].count == d("1")
    assert counts["spread_bps_pass"].row_ratio == d("0.333333")


def test_public_payload_is_canonical_deterministic_and_decimal_string_only() -> None:
    module = api()
    first = report(
        snapshot("zulu-pass", reason_codes=("zeta", "alpha")),
        snapshot(
            "alpha-watch",
            observed_at=GENERATED_AT - timedelta(seconds=180),
            best_bid_price=d("0.490000"),
            best_ask_price=d("0.510000"),
            bid_depth=d("800.000000"),
            ask_depth=d("1200.000000"),
            fee_pressure_bps=d("100.000000"),
        ),
    )
    second = report(
        snapshot(
            "alpha-watch",
            observed_at=GENERATED_AT - timedelta(seconds=180),
            best_bid_price=d("0.490000"),
            best_ask_price=d("0.510000"),
            bid_depth=d("800.000000"),
            ask_depth=d("1200.000000"),
            fee_pressure_bps=d("100.000000"),
        ),
        snapshot("zulu-pass", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_orderbook_spread_stability_report_payload(
        first,
    )
    second_payload = module.research_market_orderbook_spread_stability_report_payload(
        second,
    )
    unsigned = deepcopy(first_payload)
    provided_digest = unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    rendered = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert provided_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert (
        module.research_market_orderbook_spread_stability_report_digest(first)
        == provided_digest
    )
    assert first_payload["snapshot_count"] == "2"
    assert first_payload["average_spread_bps"] == "220.000000"
    assert first_payload["rows"][0]["spread_bps"] == "400.000000"
    assert first_payload["rows"][0]["bid_depth_change_ratio"] == "-0.200000"
    assert first_payload["rows"][0]["observed_at"] == "2026-07-09T11:57:00Z"
    assert first_payload["config"]["maximum_pass_spread_bps"] == "100.000000"
    assert "alpha-watch" not in rendered
    assert "zulu-pass" not in rendered
    assert module.validate_research_market_orderbook_spread_stability_report_payload(
        first_payload,
    )
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )


def test_decimal_arithmetic_is_independent_of_the_ambient_context() -> None:
    items = (
        snapshot(
            "alpha-pass",
            observed_at=GENERATED_AT
            - timedelta(seconds=30, microseconds=123456),
            reason_codes=("manual_check",),
        ),
        snapshot("beta-pass"),
        snapshot("gamma-pass"),
    )
    baseline = report(*items)

    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        constrained = report(*items)

    assert constrained == baseline
    assert constrained.rows[0].snapshot_age_seconds == d("30.123456")
    counts = {item.reason_code: item for item in constrained.reason_code_counts}
    assert counts["input_manual_check"].row_ratio == d("0.333333")


def test_depth_change_absolute_metrics_ignore_ambient_decimal_context() -> None:
    item = snapshot(
        bid_depth=d("850.001000"),
        ask_depth=d("1149.999000"),
    )
    baseline = report(item)

    with localcontext(Context(prec=1, rounding=ROUND_DOWN)):
        constrained = report(item)

    assert constrained == baseline
    row = constrained.rows[0]
    assert row.absolute_bid_depth_change_ratio == d("0.149999")
    assert row.absolute_ask_depth_change_ratio == d("0.149999")
    assert row.stability_bucket == "watch"
    assert "bid_depth_change_watch" in row.reason_codes
    assert "ask_depth_change_watch" in row.reason_codes


def test_depth_change_consistency_validation_ignores_ambient_decimal_context() -> None:
    module = api()
    built = report(
        snapshot(
            bid_depth=d("850.001000"),
            ask_depth=d("1149.999000"),
        ),
    )

    with localcontext(Context(prec=1, rounding=ROUND_DOWN)):
        payload = module.research_market_orderbook_spread_stability_report_payload(
            built,
        )
        assert module.research_market_orderbook_spread_stability_report_digest(
            built,
        ) == payload["derived_validation_digest"]
        assert module.validate_research_market_orderbook_spread_stability_report_payload(
            payload,
        )


def test_more_than_999_snapshots_use_canonical_continuous_public_refs() -> None:
    module = api()
    built = report(
        *(snapshot(f"snapshot-{index:04d}") for index in range(1, 1002)),
    )

    assert built.snapshot_count == d("1001")
    assert tuple(row.public_row_ref for row in built.rows[997:]) == (
        "spread_stability_snapshot_998",
        "spread_stability_snapshot_999",
        "spread_stability_snapshot_1000",
        "spread_stability_snapshot_1001",
    )

    payload = module.research_market_orderbook_spread_stability_report_payload(built)
    assert module.validate_research_market_orderbook_spread_stability_report_payload(
        payload,
    )

    noncanonical = deepcopy(payload)
    noncanonical["rows"][999]["public_row_ref"] = "spread_stability_snapshot_01000"
    resign(noncanonical)
    with pytest.raises(ValueError, match="public_row_ref"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            noncanonical,
        )


def test_duplicate_snapshot_labels_are_rejected() -> None:
    with pytest.raises(ValueError, match="snapshot_label values must be unique"):
        report(
            snapshot("duplicate-label"),
            snapshot("duplicate-label"),
        )


def test_raw_decimal_bounds_signed_zero_and_non_finite_values_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="maximum_pass_spread_bps.*nonnegative"):
        config(maximum_pass_spread_bps=d("-0.0000004"))
    with pytest.raises(ValueError, match="spread pass threshold"):
        config(
            maximum_pass_spread_bps=d("100.0000004"),
            maximum_watch_spread_bps=d("100.0000003"),
        )
    with pytest.raises(ValueError, match="best_bid_price.*not exceed 1"):
        snapshot(best_bid_price=d("1.0000004"))
    with pytest.raises(ValueError, match="row_ratio.*between 0 and 1"):
        module.ResearchMarketOrderbookSpreadStabilityReasonCodeCount(
            reason_code="manual_check",
            count=d("1"),
            row_ratio=d("1.0000004"),
        )

    with pytest.raises(ValueError, match="maximum_pass_spread_bps.*signed zero"):
        config(maximum_pass_spread_bps=d("-0"))
    with pytest.raises(ValueError, match="fee_pressure_bps.*signed zero"):
        snapshot(fee_pressure_bps=d("-0.000000"))

    for non_finite in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="fee_pressure_bps.*finite"):
            snapshot(fee_pressure_bps=d(non_finite))

    signed_zero_payload = (
        module.research_market_orderbook_spread_stability_report_payload(
            report(snapshot()),
        )
    )
    signed_zero_payload["watch_count"] = "-0.000000"
    resign(signed_zero_payload)
    with pytest.raises(ValueError, match="watch_count.*signed zero"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            signed_zero_payload,
        )

    tiny_negative_change = report(
        snapshot(
            bid_depth=d("999999999.999999"),
            previous_bid_depth=d("1000000000.000000"),
        ),
    )
    assert tiny_negative_change.rows[0].bid_depth_change_ratio == d("0.000000")
    assert tiny_negative_change.rows[0].bid_depth_change_ratio.is_signed() is False


def test_raw_valid_depth_change_can_quantize_to_negative_one() -> None:
    module = api()
    built = report(
        snapshot(
            bid_depth=d("0.000001"),
            previous_bid_depth=d("10.000000"),
        ),
    )

    assert built.rows[0].bid_depth_change_ratio == d("-1.000000")
    assert built.rows[0].absolute_bid_depth_change_ratio == d("1.000000")
    assert built.rows[0].stability_bucket == "block"
    assert module.validate_research_market_orderbook_spread_stability_report_payload(
        module.research_market_orderbook_spread_stability_report_payload(built),
    )
    with pytest.raises(ValueError, match="bid_depth_change_ratio.*less than -1"):
        replace(
            built.rows[0],
            bid_depth_change_ratio=d("-1.0000004"),
        )


def test_unsupported_finite_decimal_magnitude_is_rejected_as_value_error() -> None:
    with pytest.raises(
        ValueError,
        match="fee_pressure_bps.*supported precision",
    ):
        snapshot(fee_pressure_bps=d("1E+100"))


def test_public_dataclasses_are_frozen_non_subclassable_and_exact_schema() -> None:
    module = api()
    expected_fields = {
        module.ResearchMarketOrderbookSpreadStabilityConfig: (
            "config_version",
            "maximum_pass_spread_bps",
            "maximum_watch_spread_bps",
            "maximum_pass_depth_change_ratio",
            "maximum_watch_depth_change_ratio",
            "maximum_pass_snapshot_age_seconds",
            "maximum_watch_snapshot_age_seconds",
            "maximum_pass_fee_pressure_bps",
            "maximum_watch_fee_pressure_bps",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchMarketOrderbookSpreadStabilitySnapshot: (
            "snapshot_label",
            "observed_at",
            "best_bid_price",
            "best_ask_price",
            "bid_depth",
            "ask_depth",
            "previous_bid_depth",
            "previous_ask_depth",
            "fee_pressure_bps",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchMarketOrderbookSpreadStabilityRow: (
            "public_row_ref",
            "observed_at",
            "best_bid_price",
            "best_ask_price",
            "bid_depth",
            "ask_depth",
            "previous_bid_depth",
            "previous_ask_depth",
            "spread_bps",
            "bid_depth_change_ratio",
            "ask_depth_change_ratio",
            "absolute_bid_depth_change_ratio",
            "absolute_ask_depth_change_ratio",
            "snapshot_age_seconds",
            "fee_pressure_bps",
            "stability_bucket",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchMarketOrderbookSpreadStabilityReasonCodeCount: (
            "reason_code",
            "count",
            "row_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
        module.ResearchMarketOrderbookSpreadStabilityReport: (
            "generated_at",
            "config",
            "snapshot_count",
            "pass_count",
            "watch_count",
            "block_count",
            "wide_spread_count",
            "bid_depth_change_count",
            "ask_depth_change_count",
            "stale_snapshot_count",
            "fee_pressure_count",
            "average_spread_bps",
            "average_abs_bid_depth_change_ratio",
            "average_abs_ask_depth_change_ratio",
            "max_spread_bps",
            "max_snapshot_age_seconds",
            "max_fee_pressure_bps",
            "status",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    for klass, expected in expected_fields.items():
        assert klass.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(klass)) == expected
        with pytest.raises(TypeError, match="cannot be subclassed"):
            type(f"{klass.__name__}Child", (klass,), {})


def test_exact_canonical_payload_schema_and_stable_row_sequence_are_enforced() -> None:
    module = api()
    built = report(snapshot("zulu-pass"), snapshot("alpha-pass"))
    payload = module.research_market_orderbook_spread_stability_report_payload(
        built,
    )

    assert tuple(payload) == tuple(
        field.name
        for field in fields(module.ResearchMarketOrderbookSpreadStabilityReport)
    )
    assert tuple(payload["config"]) == tuple(
        field.name
        for field in fields(module.ResearchMarketOrderbookSpreadStabilityConfig)
    )
    assert tuple(payload["rows"][0]) == tuple(
        field.name
        for field in fields(module.ResearchMarketOrderbookSpreadStabilityRow)
    )
    assert tuple(payload["reason_code_counts"][0]) == tuple(
        field.name
        for field in fields(
            module.ResearchMarketOrderbookSpreadStabilityReasonCodeCount,
        )
    )
    assert [row["public_row_ref"] for row in payload["rows"]] == [
        "spread_stability_snapshot_001",
        "spread_stability_snapshot_002",
    ]
    assert [
        item["reason_code"] for item in payload["reason_code_counts"]
    ] == sorted(item["reason_code"] for item in payload["reason_code_counts"])

    reordered = dict(reversed(tuple(payload.items())))
    with pytest.raises(ValueError, match="canonical fields"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            reordered,
        )

    reordered_config = deepcopy(payload)
    reordered_config["config"] = dict(
        reversed(tuple(reordered_config["config"].items())),
    )
    resign(reordered_config)
    with pytest.raises(ValueError, match="config.*canonical fields"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            reordered_config,
        )

    reordered_row = deepcopy(payload)
    reordered_row["rows"][0] = dict(
        reversed(tuple(reordered_row["rows"][0].items())),
    )
    resign(reordered_row)
    with pytest.raises(ValueError, match=r"rows\[0\].*canonical fields"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            reordered_row,
        )

    reordered_reason_count = deepcopy(payload)
    reordered_reason_count["reason_code_counts"][0] = dict(
        reversed(tuple(reordered_reason_count["reason_code_counts"][0].items())),
    )
    resign(reordered_reason_count)
    with pytest.raises(
        ValueError,
        match=r"reason_code_counts\[0\].*canonical fields",
    ):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            reordered_reason_count,
        )

    forged_row_ref = deepcopy(payload)
    forged_row_ref["rows"][0]["public_row_ref"] = "spread_stability_snapshot_007"
    resign(forged_row_ref)
    with pytest.raises(ValueError, match="public_row_ref"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_row_ref,
        )

    row = built.rows[0]
    with pytest.raises(ValueError, match="reason_codes.*deterministic sequence"):
        replace(
            row,
            reason_codes=(
                row.reason_codes[1],
                row.reason_codes[0],
                *row.reason_codes[2:],
            ),
        )


def test_custom_config_is_signed_and_resigned_payloads_recompute_all_derivations() -> None:
    module = api()
    baseline = report(snapshot())
    strict_config = config(
        maximum_pass_spread_bps=d("20.000000"),
        maximum_watch_spread_bps=d("30.000000"),
    )
    strict = report(snapshot(), cfg=strict_config)
    payload = module.research_market_orderbook_spread_stability_report_payload(
        strict,
    )

    assert baseline.rows[0].stability_bucket == "pass"
    assert strict.rows[0].stability_bucket == "block"
    assert strict.derived_validation_digest != baseline.derived_validation_digest
    assert payload["config"]["maximum_pass_spread_bps"] == "20.000000"
    assert payload["config"]["maximum_watch_spread_bps"] == "30.000000"
    assert module.validate_research_market_orderbook_spread_stability_report_payload(
        payload,
    )

    forged_config = deepcopy(payload)
    forged_config["config"]["maximum_watch_spread_bps"] = "50.000000"
    resign(forged_config)
    with pytest.raises(ValueError, match="stability_bucket"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_config,
        )

    forged_derived = deepcopy(payload)
    forged_derived["rows"][0]["spread_bps"] = "80.000000"
    forged_derived["average_spread_bps"] = "80.000000"
    forged_derived["max_spread_bps"] = "80.000000"
    resign(forged_derived)
    with pytest.raises(ValueError, match="spread_bps"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_derived,
        )

    for field_name, replacement in {
        "snapshot_count": "2",
        "pass_count": "1",
        "watch_count": "1",
        "block_count": "0",
        "wide_spread_count": "0",
        "bid_depth_change_count": "1",
        "ask_depth_change_count": "1",
        "stale_snapshot_count": "1",
        "fee_pressure_count": "1",
        "average_spread_bps": "41.000000",
        "average_abs_bid_depth_change_ratio": "0.100000",
        "average_abs_ask_depth_change_ratio": "0.100000",
        "max_spread_bps": "41.000000",
        "max_snapshot_age_seconds": "1.000000",
        "max_fee_pressure_bps": "1.000000",
        "status": "watch",
    }.items():
        forged_report_field = deepcopy(payload)
        forged_report_field[field_name] = replacement
        resign(forged_report_field)
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_market_orderbook_spread_stability_report_payload(
                forged_report_field,
            )

    forged_reason_counts = deepcopy(payload)
    forged_reason_counts["reason_code_counts"][0]["count"] = "2"
    resign(forged_reason_counts)
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_reason_counts,
        )

    forged_report_reasons = deepcopy(payload)
    forged_report_reasons["reason_codes"] = [
        "spread_stability_report_watch",
        "spread_bps_watch",
    ]
    resign(forged_report_reasons)
    with pytest.raises(ValueError, match="reason_codes"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_report_reasons,
        )

    for field_name, replacement in {
        "spread_bps": "41.000000",
        "bid_depth_change_ratio": "0.100000",
        "ask_depth_change_ratio": "0.100000",
        "absolute_bid_depth_change_ratio": "0.100000",
        "absolute_ask_depth_change_ratio": "0.100000",
        "snapshot_age_seconds": "1.000000",
        "stability_bucket": "watch",
    }.items():
        forged_row_field = deepcopy(payload)
        forged_row_field["rows"][0][field_name] = replacement
        resign(forged_row_field)
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_market_orderbook_spread_stability_report_payload(
                forged_row_field,
            )


def test_public_validator_rejects_tampering_and_forged_resigned_semantics() -> None:
    module = api()
    payload = module.research_market_orderbook_spread_stability_report_payload(
        report(snapshot()),
    )

    tampered = deepcopy(payload)
    tampered["rows"][0]["spread_bps"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            tampered,
        )

    forged_bucket = deepcopy(payload)
    forged_bucket["rows"][0]["stability_bucket"] = "block"
    forged_bucket["rows"][0]["reason_codes"][0] = "spread_stability_block"
    resign(forged_bucket)
    with pytest.raises(ValueError, match="stability_bucket"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_bucket,
        )

    forged_reason = deepcopy(payload)
    forged_reason["rows"][0]["reason_codes"][1] = "spread_bps_block"
    resign(forged_reason)
    with pytest.raises(ValueError, match="reason_codes"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            forged_reason,
        )

    noncanonical = deepcopy(payload)
    noncanonical["rows"][0]["spread_bps"] = "40.0"
    resign(noncanonical)
    with pytest.raises(ValueError, match="canonical"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            noncanonical,
        )

    unsafe_resigned = deepcopy(payload)
    unsafe_resigned["rows"][0]["reason_codes"].append("input_wallet_reference")
    resign(unsafe_resigned)
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_market_orderbook_spread_stability_report_payload(
            unsafe_resigned,
        )


def test_frozen_exact_decimal_inputs_and_report_revalidation() -> None:
    module = api()
    item = snapshot()
    built = report(item)

    for value in (
        config(),
        item,
        built,
        *built.rows,
        *built.reason_code_counts,
    ):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field_value is None:
                continue
            if field.name.endswith(
                (
                    "_bps",
                    "_count",
                    "_depth",
                    "_price",
                    "_ratio",
                    "_seconds",
                ),
            ):
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="maximum_pass_spread_bps"):
        config(maximum_pass_spread_bps=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_watch_depth_change_ratio"):
        config(maximum_watch_depth_change_ratio=DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="spread"):
        config(maximum_pass_spread_bps=d("600.000000"))
    with pytest.raises(ValueError, match="best_bid_price"):
        snapshot(best_bid_price=0.49)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="bid_depth"):
        snapshot(bid_depth=DecimalSubclass("1000.000000"))
    with pytest.raises(ValueError, match="best_ask_price"):
        snapshot(best_bid_price=d("0.500000"), best_ask_price=d("0.500000"))
    with pytest.raises(ValueError, match="previous_bid_depth"):
        snapshot(previous_bid_depth=d("0.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 9, 11, 59))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(
            observed_at=DatetimeSubclass(2026, 7, 9, 11, 59, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="snapshot_label"):
        snapshot("market_id_alpha")
    with pytest.raises(ValueError, match="reason_codes"):
        snapshot(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="report"):
        module.research_market_orderbook_spread_stability_report_payload(object())


def test_module_scope_is_report_only_readonly_and_external_io_free() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "place",
        "position",
        "recommend",
        "rollback",
        "sell",
        "send",
        "sizing",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)


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
