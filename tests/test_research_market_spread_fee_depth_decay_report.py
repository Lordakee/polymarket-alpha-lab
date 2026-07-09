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


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_spread_fee_depth_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_SPREAD_FEE_DEPTH_DECAY_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_spread_width_ratio": d("0.020000"),
        "maximum_watch_spread_width_ratio": d("0.060000"),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "maximum_pass_depth_decay_ratio": d("0.250000"),
        "maximum_watch_depth_decay_ratio": d("0.600000"),
        "minimum_pass_current_depth_band": d("1000.000000"),
        "minimum_watch_current_depth_band": d("250.000000"),
        "maximum_pass_book_age_seconds": d("120.000000"),
        "maximum_watch_book_age_seconds": d("600.000000"),
        "minimum_pass_spread_fee_depth_decay_score": d("0.750000"),
        "minimum_watch_spread_fee_depth_decay_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketSpreadFeeDepthDecayConfig(**values)


def decay_input(
    private_item_ref: str = "private-alpha",
    *,
    private_group_ref: str = "group-alpha",
    observed_at: datetime | None = None,
    spread_width_ratio: Decimal = d("0.010000"),
    fee_drag_ratio: Decimal = d("0.005000"),
    current_depth_band: Decimal = d("1500.000000"),
    baseline_depth_band: Decimal = d("1700.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketSpreadFeeDepthDecayInput(
        private_item_ref=private_item_ref,
        private_group_ref=private_group_ref,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        spread_width_ratio=spread_width_ratio,
        fee_drag_ratio=fee_drag_ratio,
        current_depth_band=current_depth_band,
        baseline_depth_band=baseline_depth_band,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_spread_fee_depth_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_report_blocks_without_public_private_refs() -> None:
    module = api()
    empty = report()

    assert module.SPREAD_FEE_DEPTH_DECAY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "SPREAD_FEE_DEPTH_DECAY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_SPREAD_FEE_DEPTH_DECAY_REPORT_CONFIG_VERSION",
        "ResearchMarketSpreadFeeDepthDecayConfig",
        "ResearchMarketSpreadFeeDepthDecayInput",
        "ResearchMarketSpreadFeeDepthDecayReasonCodeCount",
        "ResearchMarketSpreadFeeDepthDecayReport",
        "ResearchMarketSpreadFeeDepthDecayRow",
        "build_research_market_spread_fee_depth_decay_report",
        "research_market_spread_fee_depth_decay_report_payload",
        "validate_research_market_spread_fee_depth_decay_report_payload",
    )
    assert empty.generated_at == GENERATED_AT
    assert empty.status == "block"
    assert empty.input_count == ZERO
    assert empty.row_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.average_spread_fee_depth_decay_score == ZERO
    assert empty.reason_codes == ("spread_fee_depth_decay_no_inputs",)
    assert empty.reason_code_counts == (
        module.ResearchMarketSpreadFeeDepthDecayReasonCodeCount(
            reason_code="spread_fee_depth_decay_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_pass_watch_and_block_spread_fee_depth_decay() -> None:
    combined = report(
        decay_input(
            "item-block",
            private_group_ref="group-block",
            observed_at=GENERATED_AT - timedelta(seconds=900),
            spread_width_ratio=d("0.100000"),
            fee_drag_ratio=d("0.040000"),
            current_depth_band=d("100.000000"),
            baseline_depth_band=d("1000.000000"),
            reason_codes=("manual_check",),
        ),
        decay_input("item-pass", private_group_ref="group-pass"),
        decay_input(
            "item-watch",
            private_group_ref="group-watch",
            observed_at=GENERATED_AT - timedelta(seconds=300),
            spread_width_ratio=d("0.040000"),
            fee_drag_ratio=d("0.020000"),
            current_depth_band=d("600.000000"),
            baseline_depth_band=d("1000.000000"),
        ),
    )

    assert combined.input_count == d("3.000000")
    assert combined.row_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.status == "block"
    assert combined.wide_spread_count == d("2.000000")
    assert combined.high_fee_drag_count == d("2.000000")
    assert combined.depth_decay_count == d("2.000000")
    assert combined.thin_depth_count == d("2.000000")
    assert combined.stale_book_count == d("2.000000")
    assert combined.average_spread_fee_depth_decay_score == d("0.510873")
    assert combined.min_current_depth_band == d("100.000000")
    assert combined.max_spread_width_ratio == d("0.100000")
    assert combined.max_fee_drag_ratio == d("0.040000")
    assert combined.max_depth_decay_ratio == d("0.900000")
    assert combined.max_book_age_seconds == d("900.000000")

    block_row, watch_row, pass_row = combined.rows
    assert tuple(row.status for row in combined.rows) == ("block", "watch", "pass")
    assert block_row.depth_retention_ratio == d("0.100000")
    assert block_row.depth_decay_ratio == d("0.900000")
    assert block_row.spread_fee_depth_decay_score == ZERO
    assert block_row.reason_codes == (
        "input_manual_check",
        "spread_fee_depth_decay_book_age_block",
        "spread_fee_depth_decay_current_depth_block",
        "spread_fee_depth_decay_depth_decay_block",
        "spread_fee_depth_decay_fee_drag_block",
        "spread_fee_depth_decay_spread_width_block",
        "spread_fee_depth_decay_status_block",
    )
    assert watch_row.depth_retention_ratio == d("0.600000")
    assert watch_row.depth_decay_ratio == d("0.400000")
    assert watch_row.spread_width_score == d("0.500000")
    assert watch_row.fee_drag_score == d("0.500000")
    assert watch_row.depth_decay_score == d("0.571429")
    assert watch_row.current_depth_score == d("0.466667")
    assert watch_row.book_age_score == d("0.625000")
    assert watch_row.spread_fee_depth_decay_score == d("0.532619")
    assert pass_row.spread_fee_depth_decay_score == d("1.000000")
    assert "spread_fee_depth_decay_status_pass" in pass_row.reason_codes


def test_payload_is_deterministic_decimal_string_serialized_and_digest_checked() -> None:
    module = api()
    first = report(
        decay_input("zulu-private", private_group_ref="group-z", reason_codes=("zeta", "alpha")),
        decay_input("alpha-private", private_group_ref="group-a"),
    )
    second = report(
        decay_input("alpha-private", private_group_ref="group-a"),
        decay_input("zulu-private", private_group_ref="group-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_spread_fee_depth_decay_report_payload(first)
    second_payload = module.research_market_spread_fee_depth_decay_report_payload(second)
    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert provided_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["spread_width_ratio"] == "0.010000"
    assert first_payload["rows"][0]["spread_fee_depth_decay_score"] == "1.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(first_payload)
    )
    assert module.validate_research_market_spread_fee_depth_decay_report_payload(
        first_payload,
    ) == first_payload

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "zulu-private",
        "alpha-private",
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
        "wallet",
        "order",
        "trade",
        "live",
        "recommend",
        "sizing",
    ):
        assert forbidden not in rendered

    tampered = dict(first_payload)
    tampered["row_count"] = "999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_spread_fee_depth_decay_report_payload(tampered)


def test_rejects_bad_numeric_datetime_flag_status_and_digest_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="maximum_pass_spread_width_ratio"):
        config(maximum_pass_spread_width_ratio=DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="maximum_watch_fee_drag_ratio"):
        config(maximum_watch_fee_drag_ratio=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_pass_spread_width_ratio"):
        config(maximum_pass_spread_width_ratio=d("0.070000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(decay_input(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(decay_input(), generated_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        decay_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report(decay_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="spread_width_ratio"):
        decay_input(spread_width_ratio=d("NaN"))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        decay_input(fee_drag_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_depth_band"):
        decay_input(current_depth_band=-d("1.000000"))
    with pytest.raises(ValueError, match="baseline_depth_band"):
        decay_input(baseline_depth_band=ZERO)
    with pytest.raises(ValueError, match="reason_codes"):
        decay_input(reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report(decay_input(readonly=False))

    built = report(decay_input())
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="spread_fee_depth_decay_score"):
        replace(built.rows[0], spread_fee_depth_decay_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(built, status="watch")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_market_spread_fee_depth_decay_report_payload(object())

    unsafe_payload = module.research_market_spread_fee_depth_decay_report_payload(built)
    unsafe_payload = dict(unsafe_payload)
    unsafe_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_spread_fee_depth_decay_report_payload(
            unsafe_payload,
        )


def test_public_objects_are_frozen_dataclasses_with_decimal_numeric_fields() -> None:
    module = api()
    built = report(decay_input())

    for item in (config(), decay_input(), built, *built.reason_code_counts, *built.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        built.row_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].spread_fee_depth_decay_score = ZERO  # type: ignore[misc]

    public_classes = (
        module.ResearchMarketSpreadFeeDepthDecayConfig,
        module.ResearchMarketSpreadFeeDepthDecayInput,
        module.ResearchMarketSpreadFeeDepthDecayRow,
        module.ResearchMarketSpreadFeeDepthDecayReasonCodeCount,
        module.ResearchMarketSpreadFeeDepthDecayReport,
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
                "observed_at",
                "generated_at",
            }:
                continue
            assert field.type in (Decimal, "Decimal")


def test_owned_module_has_no_storage_network_execution_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_spread_fee_depth_decay_report.py"
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
        "sqlite",
        "postgres",
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
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "connect(",
        "execute(",
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
