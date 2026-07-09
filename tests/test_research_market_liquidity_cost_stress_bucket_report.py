from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_liquidity_cost_stress_bucket_report import (
    ResearchMarketLiquidityCostStressBucketConfig,
    ResearchMarketLiquidityCostStressBucketInput,
    ResearchMarketLiquidityCostStressBucketReasonCodeCount,
    ResearchMarketLiquidityCostStressBucketReport,
    ResearchMarketLiquidityCostStressBucketRow,
    build_research_market_liquidity_cost_stress_bucket_report,
    research_market_liquidity_cost_stress_bucket_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)


def stress_input(
    surface_group: str = "macro-deep",
    category: str = "macro",
    *,
    spread_rate: Decimal = Decimal("0.010000"),
    available_depth_usdc: Decimal = Decimal("10000.000000"),
    fee_drag_rate: Decimal = Decimal("0.001000"),
    slippage_cushion_rate: Decimal = Decimal("0.050000"),
    book_age_seconds: Decimal = Decimal("60.000000"),
    volatility_rate: Decimal = Decimal("0.050000"),
    settlement_friction_rate: Decimal = Decimal("0.020000"),
) -> ResearchMarketLiquidityCostStressBucketInput:
    return ResearchMarketLiquidityCostStressBucketInput(
        surface_group=surface_group,
        category=category,
        spread_rate=spread_rate,
        available_depth_usdc=available_depth_usdc,
        fee_drag_rate=fee_drag_rate,
        slippage_cushion_rate=slippage_cushion_rate,
        book_age_seconds=book_age_seconds,
        volatility_rate=volatility_rate,
        settlement_friction_rate=settlement_friction_rate,
    )


def test_bucket_report_uses_all_stress_dimensions_and_sorts_deterministically() -> None:
    config = ResearchMarketLiquidityCostStressBucketConfig()
    inputs = (
        stress_input(),
        stress_input(
            "policy-fragile",
            "policy",
            spread_rate=Decimal("0.080000"),
            available_depth_usdc=Decimal("100.000000"),
            fee_drag_rate=Decimal("0.070000"),
            slippage_cushion_rate=Decimal("0.001000"),
            book_age_seconds=Decimal("1200.000000"),
            volatility_rate=Decimal("0.550000"),
            settlement_friction_rate=Decimal("0.300000"),
        ),
        stress_input(
            "weather-thin",
            "weather",
            spread_rate=Decimal("0.040000"),
            available_depth_usdc=Decimal("750.000000"),
            fee_drag_rate=Decimal("0.030000"),
            slippage_cushion_rate=Decimal("0.010000"),
            book_age_seconds=Decimal("600.000000"),
            volatility_rate=Decimal("0.300000"),
            settlement_friction_rate=Decimal("0.120000"),
        ),
    )

    report = build_research_market_liquidity_cost_stress_bucket_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )
    repeated_report = build_research_market_liquidity_cost_stress_bucket_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.surface_group for row in report.rows] == [
        "policy-fragile",
        "weather-thin",
        "macro-deep",
    ]
    assert report == repeated_report
    assert report.report_status == "block"
    assert report.row_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.wide_spread_count == Decimal("2.000000")
    assert report.thin_depth_count == Decimal("1.000000")
    assert report.fragile_depth_count == Decimal("1.000000")
    assert report.high_fee_drag_count == Decimal("2.000000")
    assert report.low_slippage_cushion_count == Decimal("2.000000")
    assert report.stale_book_count == Decimal("2.000000")
    assert report.volatile_book_count == Decimal("2.000000")
    assert report.settlement_friction_count == Decimal("2.000000")
    assert report.max_stress_score == Decimal("1.000000")

    block_row, watch_row, pass_row = report.rows
    assert block_row.depth_band == "fragile"
    assert block_row.spread_status == "block"
    assert block_row.depth_status == "block"
    assert block_row.fee_drag_status == "block"
    assert block_row.slippage_cushion_status == "block"
    assert block_row.book_age_status == "block"
    assert block_row.volatility_status == "block"
    assert block_row.settlement_friction_status == "block"
    assert block_row.stress_score == Decimal("1.000000")
    assert block_row.status == "block"
    assert block_row.stress_bucket == "block"
    assert block_row.reason_codes == (
        "book_age_block",
        "depth_fragile_block",
        "fee_drag_block",
        "liquidity_cost_stress_block",
        "settlement_friction_block",
        "slippage_cushion_block",
        "spread_block",
        "volatility_block",
    )

    assert watch_row.depth_band == "thin"
    assert watch_row.stress_score == Decimal("0.500000")
    assert watch_row.status == "watch"
    assert watch_row.stress_bucket == "watch"
    assert pass_row.depth_band == "deep"
    assert pass_row.stress_score == Decimal("0.000000")
    assert pass_row.reason_codes == ("liquidity_cost_stress_pass",)


def test_payload_uses_decimal_strings_freezes_and_revalidates_digest() -> None:
    report = build_research_market_liquidity_cost_stress_bucket_report(
        (stress_input(),),
        generated_at=GENERATED_AT,
        config=ResearchMarketLiquidityCostStressBucketConfig(),
    )

    payload = research_market_liquidity_cost_stress_bucket_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["spread_rate"] == "0.010000"
    assert payload["rows"][0]["available_depth_usdc"] == "10000.000000"
    assert payload["reason_code_counts"][0]["row_count"] == "1.000000"
    assert payload["generated_at"] == "2026-07-08T15:30:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["row_count"] = "2.000000"

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_id"] = "raw"
    with pytest.raises(ValueError, match="unsafe"):
        research_market_liquidity_cost_stress_bucket_payload(unsafe_key_payload)


def test_public_payload_omits_raw_market_and_execution_surfaces() -> None:
    report = build_research_market_liquidity_cost_stress_bucket_report(
        (stress_input(),),
        generated_at=GENERATED_AT,
        config=ResearchMarketLiquidityCostStressBucketConfig(),
    )

    payload = research_market_liquidity_cost_stress_bucket_payload(report)
    forbidden_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )

    for key, value in _walk_key_values(payload):
        lowered_key = key.lower()
        assert not [fragment for fragment in forbidden_fragments if fragment in lowered_key]
        if type(value) is str:
            lowered_value = value.lower()
            assert "://" not in lowered_value
            assert not [fragment for fragment in forbidden_fragments if fragment in lowered_value]


def test_public_inputs_reject_source_and_private_identifier_leakage() -> None:
    forbidden_values = (
        "source_id_abc",
        "condition_id_123",
        "credential-cache",
        "secret-token",
        "order-size",
        "broker-account",
        "client-api_key",
        "database-cache",
        "network-endpoint",
        "persist-record",
        "file_path",
    )

    for forbidden_value in forbidden_values:
        with pytest.raises(ValueError, match="unsafe"):
            stress_input(surface_group=forbidden_value)
        with pytest.raises(ValueError, match="unsafe"):
            stress_input(category=forbidden_value)


def test_builder_rejects_duplicate_public_row_identity() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        build_research_market_liquidity_cost_stress_bucket_report(
            (
                stress_input("shared-surface", "macro"),
                stress_input(
                    "shared-surface",
                    "macro",
                    spread_rate=Decimal("0.040000"),
                ),
            ),
            generated_at=GENERATED_AT,
            config=ResearchMarketLiquidityCostStressBucketConfig(),
        )


def test_report_rejects_duplicate_public_row_identity() -> None:
    pass_row = build_research_market_liquidity_cost_stress_bucket_report(
        (stress_input("shared-surface", "macro"),),
        generated_at=GENERATED_AT,
        config=ResearchMarketLiquidityCostStressBucketConfig(),
    ).rows[0]
    watch_row = build_research_market_liquidity_cost_stress_bucket_report(
        (
            stress_input(
                "shared-surface",
                "macro",
                spread_rate=Decimal("0.040000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchMarketLiquidityCostStressBucketConfig(),
    ).rows[0]

    with pytest.raises(ValueError, match="duplicate"):
        ResearchMarketLiquidityCostStressBucketReport(
            generated_at=GENERATED_AT,
            config_version="research-market-liquidity-cost-stress-bucket-report-v0",
            report_status="watch",
            row_count=Decimal("2.000000"),
            pass_count=Decimal("1.000000"),
            watch_count=Decimal("1.000000"),
            block_count=Decimal("0.000000"),
            wide_spread_count=Decimal("1.000000"),
            thin_depth_count=Decimal("0.000000"),
            fragile_depth_count=Decimal("0.000000"),
            high_fee_drag_count=Decimal("0.000000"),
            low_slippage_cushion_count=Decimal("0.000000"),
            stale_book_count=Decimal("0.000000"),
            volatile_book_count=Decimal("0.000000"),
            settlement_friction_count=Decimal("0.000000"),
            max_stress_score=Decimal("0.071429"),
            rows=(watch_row, pass_row),
            reason_code_counts=(),
        )


def test_builder_revalidates_runtime_mutated_config() -> None:
    config = ResearchMarketLiquidityCostStressBucketConfig()
    object.__setattr__(
        config,
        "spread_watch_threshold",
        Decimal("0.900000"),
    )

    with pytest.raises(ValueError, match="spread thresholds"):
        build_research_market_liquidity_cost_stress_bucket_report(
            (stress_input(),),
            generated_at=GENERATED_AT,
            config=config,
        )


def test_dict_payload_rejects_noncanonical_numeric_objects() -> None:
    report = build_research_market_liquidity_cost_stress_bucket_report(
        (stress_input(),),
        generated_at=GENERATED_AT,
        config=ResearchMarketLiquidityCostStressBucketConfig(),
    )
    payload = research_market_liquidity_cost_stress_bucket_payload(report)
    noncanonical_payload = dict(payload)
    noncanonical_payload["row_count"] = Decimal("1.000000")

    with pytest.raises(ValueError, match="row_count must be a Decimal string"):
        research_market_liquidity_cost_stress_bucket_payload(noncanonical_payload)


def test_signed_dict_payload_rejects_non_report_statuses_and_public_surfaces() -> None:
    report = build_research_market_liquidity_cost_stress_bucket_report(
        (stress_input(),),
        generated_at=GENERATED_AT,
        config=ResearchMarketLiquidityCostStressBucketConfig(),
    )
    payload = research_market_liquidity_cost_stress_bucket_payload(report)

    tampered_count = dict(payload)
    tampered_count["row_count"] = "2.000000"
    _resign_payload(tampered_count)
    with pytest.raises(ValueError, match="row_count"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_count)

    tampered_status = dict(payload)
    tampered_status["report_status"] = "blocked"
    _resign_payload(tampered_status)
    with pytest.raises(ValueError, match="report_status"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_status)

    tampered_row_status = dict(payload)
    tampered_row_status["rows"] = [dict(payload["rows"][0])]
    tampered_row_status["rows"][0]["stress_bucket"] = "blocked"
    _resign_payload(tampered_row_status)
    with pytest.raises(ValueError, match="stress_bucket"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_row_status)

    tampered_surface_value = dict(payload)
    tampered_surface_value["rows"] = [dict(payload["rows"][0])]
    tampered_surface_value["rows"][0]["category"] = "execution"
    _resign_payload(tampered_surface_value)
    with pytest.raises(ValueError, match="unsafe"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_surface_value)

    tampered_source_identifier = dict(payload)
    tampered_source_identifier["rows"] = [dict(payload["rows"][0])]
    tampered_source_identifier["rows"][0]["surface_group"] = "source_id_abc"
    _resign_payload(tampered_source_identifier["rows"][0])
    _resign_payload(tampered_source_identifier)
    with pytest.raises(ValueError, match="unsafe"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_source_identifier)

    tampered_surface_field = dict(payload)
    tampered_surface_field["recommendation"] = "watch"
    _resign_payload(tampered_surface_field)
    with pytest.raises(ValueError, match="unsafe|unexpected"):
        research_market_liquidity_cost_stress_bucket_payload(tampered_surface_field)


def test_validation_rejects_invalid_numbers_dates_thresholds_and_flags() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_market_liquidity_cost_stress_bucket_report(
            (),
            generated_at=datetime(2026, 7, 8, 15, 30),
            config=ResearchMarketLiquidityCostStressBucketConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_market_liquidity_cost_stress_bucket_report(
            (),
            generated_at=datetime(2026, 7, 8, 15, 30, tzinfo=NoneOffsetTimezone()),
            config=ResearchMarketLiquidityCostStressBucketConfig(),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_research_market_liquidity_cost_stress_bucket_report(
            (),
            generated_at=DatetimeSubclass(2026, 7, 8, 15, 30, tzinfo=UTC),
            config=ResearchMarketLiquidityCostStressBucketConfig(),
        )
    with pytest.raises(ValueError, match="spread_rate must be a Decimal"):
        stress_input(spread_rate=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_depth_usdc must be nonnegative"):
        stress_input(available_depth_usdc=Decimal("-1"))
    with pytest.raises(ValueError, match="volatility_rate must be at most 1.000000"):
        stress_input(volatility_rate=Decimal("1.100000"))
    with pytest.raises(ValueError, match="slippage cushion floors"):
        ResearchMarketLiquidityCostStressBucketConfig(
            slippage_cushion_watch_floor=Decimal("0.001000"),
            slippage_cushion_block_floor=Decimal("0.005000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(ResearchMarketLiquidityCostStressBucketConfig(), paper_only=False)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = ResearchMarketLiquidityCostStressBucketConfig()
    input_row = stress_input()
    report = build_research_market_liquidity_cost_stress_bucket_report(
        (input_row,),
        generated_at=GENERATED_AT,
        config=config,
    )
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.surface_group = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        reason_count.row_count = Decimal("2.000000")  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchMarketLiquidityCostStressBucketConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(ResearchMarketLiquidityCostStressBucketInput):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class RowSubclass(ResearchMarketLiquidityCostStressBucketRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ReasonCountSubclass(ResearchMarketLiquidityCostStressBucketReasonCodeCount):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ReportSubclass(ResearchMarketLiquidityCostStressBucketReport):
            pass


def test_static_module_has_no_side_effect_or_execution_imports() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_market_liquidity_cost_stress_bucket_report.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "network",
        "database",
        "persist",
        "private_key",
    )

    assert not [term for term in forbidden_terms if term in source.lower()]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, (list, tuple)):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)


def _walk_key_values(value: object) -> tuple[tuple[str, object], ...]:
    if isinstance(value, dict):
        pairs: list[tuple[str, object]] = []
        for key, item in value.items():
            pairs.append((key, item))
            pairs.extend(_walk_key_values(item))
        return tuple(pairs)
    if isinstance(value, (list, tuple)):
        return tuple(pair for item in value for pair in _walk_key_values(item))
    return ()


def _resign_payload(payload: dict[str, object]) -> None:
    unsigned = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
