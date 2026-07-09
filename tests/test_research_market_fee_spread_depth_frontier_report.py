from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_spread_depth_frontier_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def payload_with_recomputed_digest(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    digest_payload = dict(updated)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    updated["derived_validation_digest"] = hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()
    return updated


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_FRONTIER_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "maximum_pass_spread_width_ratio": d("0.030000"),
        "maximum_watch_spread_width_ratio": d("0.080000"),
        "minimum_pass_total_depth_band": d("1000.000000"),
        "minimum_watch_total_depth_band": d("250.000000"),
        "minimum_pass_slippage_cushion_ratio": d("0.050000"),
        "minimum_watch_slippage_cushion_ratio": d("0.020000"),
        "maximum_pass_book_age_seconds": d("120.000000"),
        "maximum_watch_book_age_seconds": d("600.000000"),
        "maximum_pass_volatility_ratio": d("0.100000"),
        "maximum_watch_volatility_ratio": d("0.250000"),
        "maximum_pass_settlement_friction_ratio": d("0.050000"),
        "maximum_watch_settlement_friction_ratio": d("0.150000"),
        "minimum_pass_frontier_score": d("0.750000"),
        "minimum_watch_frontier_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeSpreadDepthFrontierConfig(**values)


def frontier_input(
    private_item_ref: str = "private-alpha",
    *,
    private_group_ref: str = "group-alpha",
    book_observed_at: datetime | None = None,
    fee_drag_ratio: Decimal = d("0.005000"),
    spread_width_ratio: Decimal = d("0.010000"),
    near_depth_band: Decimal = d("800.000000"),
    mid_depth_band: Decimal = d("700.000000"),
    far_depth_band: Decimal = d("500.000000"),
    slippage_cushion_ratio: Decimal = d("0.080000"),
    volatility_ratio: Decimal = d("0.050000"),
    settlement_friction_ratio: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketFeeSpreadDepthFrontierInput(
        private_item_ref=private_item_ref,
        private_group_ref=private_group_ref,
        book_observed_at=(
            book_observed_at
            if book_observed_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        fee_drag_ratio=fee_drag_ratio,
        spread_width_ratio=spread_width_ratio,
        near_depth_band=near_depth_band,
        mid_depth_band=mid_depth_band,
        far_depth_band=far_depth_band,
        slippage_cushion_ratio=slippage_cushion_ratio,
        volatility_ratio=volatility_ratio,
        settlement_friction_ratio=settlement_friction_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_market_fee_spread_depth_frontier_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_frontier_report_blocks_review_without_exposing_private_refs() -> None:
    module = api()
    empty = report()

    assert module.FEE_SPREAD_DEPTH_FRONTIER_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "FEE_SPREAD_DEPTH_FRONTIER_STATUSES",
        "DEFAULT_RESEARCH_MARKET_FEE_SPREAD_DEPTH_FRONTIER_REPORT_CONFIG_VERSION",
        "ResearchMarketFeeSpreadDepthFrontierConfig",
        "ResearchMarketFeeSpreadDepthFrontierInput",
        "ResearchMarketFeeSpreadDepthFrontierReasonCodeCount",
        "ResearchMarketFeeSpreadDepthFrontierReport",
        "ResearchMarketFeeSpreadDepthFrontierRow",
        "build_research_market_fee_spread_depth_frontier_report",
        "research_market_fee_spread_depth_frontier_report_payload",
        "validate_research_market_fee_spread_depth_frontier_report_payload",
    )
    assert empty.generated_at == GENERATED_AT
    assert empty.status == "block"
    assert empty.input_count == ZERO
    assert empty.row_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.average_frontier_score == ZERO
    assert empty.reason_codes == ("frontier_no_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketFeeSpreadDepthFrontierReasonCodeCount(
            reason_code="frontier_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_pass_watch_and_block_fee_spread_depth_frontiers() -> None:
    combined = report(
        frontier_input(
            "item-block",
            private_group_ref="group-block",
            book_observed_at=GENERATED_AT - timedelta(seconds=900),
            fee_drag_ratio=d("0.040000"),
            spread_width_ratio=d("0.100000"),
            near_depth_band=d("50.000000"),
            mid_depth_band=d("25.000000"),
            far_depth_band=d("25.000000"),
            slippage_cushion_ratio=d("0.010000"),
            volatility_ratio=d("0.300000"),
            settlement_friction_ratio=d("0.200000"),
            reason_codes=("manual_check",),
        ),
        frontier_input("item-pass", private_group_ref="group-pass"),
        frontier_input(
            "item-watch",
            private_group_ref="group-watch",
            book_observed_at=GENERATED_AT - timedelta(seconds=300),
            fee_drag_ratio=d("0.020000"),
            spread_width_ratio=d("0.050000"),
            near_depth_band=d("200.000000"),
            mid_depth_band=d("200.000000"),
            far_depth_band=d("200.000000"),
            slippage_cushion_ratio=d("0.030000"),
            volatility_ratio=d("0.180000"),
            settlement_friction_ratio=d("0.080000"),
        ),
    )

    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.status == "block"
    assert combined.high_fee_drag_count == d("2.000000")
    assert combined.wide_spread_count == d("2.000000")
    assert combined.thin_depth_count == d("2.000000")
    assert combined.low_slippage_cushion_count == d("2.000000")
    assert combined.stale_book_count == d("2.000000")
    assert combined.high_volatility_count == d("2.000000")
    assert combined.high_settlement_friction_count == d("2.000000")
    assert combined.average_frontier_score == d("0.509127")
    assert combined.min_total_depth_band == d("100.000000")
    assert combined.max_fee_drag_ratio == d("0.040000")
    assert combined.max_spread_width_ratio == d("0.100000")
    assert combined.min_slippage_cushion_ratio == d("0.010000")
    assert combined.max_book_age_seconds == d("900.000000")
    assert combined.max_volatility_ratio == d("0.300000")
    assert combined.max_settlement_friction_ratio == d("0.200000")

    block_row, watch_row, pass_row = combined.rows
    assert tuple(row.status for row in combined.rows) == ("block", "watch", "pass")
    assert block_row.total_depth_band == d("100.000000")
    assert block_row.frontier_score == ZERO
    assert block_row.reason_codes == (
        "frontier_book_age_block",
        "frontier_depth_band_block",
        "frontier_fee_drag_block",
        "frontier_settlement_friction_block",
        "frontier_slippage_cushion_block",
        "frontier_spread_width_block",
        "frontier_status_block",
        "frontier_volatility_block",
        "input_manual_check",
    )
    assert watch_row.total_depth_band == d("600.000000")
    assert watch_row.fee_drag_score == d("0.500000")
    assert watch_row.spread_width_score == d("0.600000")
    assert watch_row.depth_band_score == d("0.466667")
    assert watch_row.slippage_cushion_score == d("0.333333")
    assert watch_row.book_age_score == d("0.625000")
    assert watch_row.volatility_score == d("0.466667")
    assert watch_row.settlement_friction_score == d("0.700000")
    assert watch_row.frontier_score == d("0.527381")
    assert pass_row.frontier_score == d("1.000000")
    assert "frontier_status_pass" in pass_row.reason_codes


def test_payload_is_deterministic_decimal_string_serialized_and_digest_validated() -> None:
    module = api()
    first = report(
        frontier_input("zulu-private", private_group_ref="group-z", reason_codes=("zeta", "alpha")),
        frontier_input("alpha-private", private_group_ref="group-a"),
    )
    second = report(
        frontier_input("alpha-private", private_group_ref="group-a"),
        frontier_input("zulu-private", private_group_ref="group-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_fee_spread_depth_frontier_report_payload(first)
    second_payload = module.research_market_fee_spread_depth_frontier_report_payload(second)
    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert provided_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["fee_drag_ratio"] == "0.005000"
    assert first_payload["rows"][0]["frontier_score"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert module.validate_research_market_fee_spread_depth_frontier_report_payload(
        first_payload,
    ) == first_payload

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_fee_spread_depth_frontier_report_payload(tampered)

    recomputed_bad_status = payload_with_recomputed_digest(
        dict(first_payload, status="monitor"),
    )
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_fee_spread_depth_frontier_report_payload(
            recomputed_bad_status,
        )

    bad_row = dict(first_payload["rows"][0])
    bad_row["status"] = "critical"
    recomputed_bad_row_status = payload_with_recomputed_digest(
        dict(first_payload, rows=[bad_row, *first_payload["rows"][1:]]),
    )
    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_fee_spread_depth_frontier_report_payload(
            recomputed_bad_row_status,
        )


def test_public_payload_excludes_private_refs_sensitive_text_and_decision_surfaces() -> None:
    module = api()
    built = report(
        frontier_input(
            "candidate-id-123-private",
            private_group_ref=(
                "market-id-99/will-this-question-resolve/"
                "https://example.test/source?token=secret&wallet=abc"
            ),
        ),
    )
    payload = module.research_market_fee_spread_depth_frontier_report_payload(built)
    rendered = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "candidate-id-123-private",
        "market-id-99",
        "will-this-question-resolve",
        "https://example.test",
        "source?token",
        "secret",
        "wallet",
        "private_item_ref",
        "private_group_ref",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "order",
        "trade",
        "live",
        "recommend",
        "position",
        "sizing",
    ):
        assert forbidden not in rendered

    unsafe_report = replace(built)
    object.__setattr__(unsafe_report, "reason_codes", ("frontier_status_pass", "token_seen"))
    object.__setattr__(unsafe_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_market_fee_spread_depth_frontier_report_payload(unsafe_report)


def test_rejects_bad_numeric_datetime_flag_status_and_digest_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="maximum_watch_spread_width_ratio"):
        config(maximum_watch_spread_width_ratio=0.08)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_pass_fee_drag_ratio"):
        config(maximum_pass_fee_drag_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(frontier_input(), generated_at=datetime(2026, 7, 8, 15, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(frontier_input(), generated_at=DatetimeSubclass(2026, 7, 8, 15, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="book_observed_at"):
        frontier_input(book_observed_at=datetime(2026, 7, 8, 15, 30))
    with pytest.raises(ValueError, match="book_observed_at"):
        report(frontier_input(book_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        frontier_input(fee_drag_ratio=d("NaN"))
    with pytest.raises(ValueError, match="spread_width_ratio"):
        frontier_input(spread_width_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="near_depth_band"):
        frontier_input(near_depth_band=-d("1.000000"))
    with pytest.raises(ValueError, match="slippage_cushion_ratio"):
        frontier_input(slippage_cushion_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        frontier_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(frontier_input(readonly=False))

    built = report(frontier_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="frontier_score"):
        replace(built.rows[0], frontier_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_fee_spread_depth_frontier_report_payload(object())

    unsafe_payload = module.research_market_fee_spread_depth_frontier_report_payload(built)
    unsafe_payload = dict(unsafe_payload)
    unsafe_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_fee_spread_depth_frontier_report_payload(
            unsafe_payload,
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(frontier_input())

    for item in (config(), frontier_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].frontier_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketFeeSpreadDepthFrontierConfig,
        module.ResearchMarketFeeSpreadDepthFrontierInput,
        module.ResearchMarketFeeSpreadDepthFrontierRow,
        module.ResearchMarketFeeSpreadDepthFrontierReasonCodeCount,
        module.ResearchMarketFeeSpreadDepthFrontierReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "private_item_ref",
                "private_group_ref",
                "config_version",
                "public_row_ref",
                "status",
                "reason_code",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "derived_validation_digest",
                "book_observed_at",
                "generated_at",
            }:
                continue
            assert field.type in (Decimal, "Decimal")


def test_owned_module_has_no_auth_storage_text_or_decision_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_spread_depth_frontier_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    for token in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "database",
        "network",
        "auth",
        "private_key",
        "api_key",
        "candidate_id",
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
        "live",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
    ):
        assert token not in text

    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "request",
        "create_order",
        "submit_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
