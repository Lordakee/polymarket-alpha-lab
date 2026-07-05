from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_manufacturing_new_orders_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold": d("0.050000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchManufacturingNewOrdersDigestConfig(**values)


def signal(**overrides: object):
    module = api()
    values = {
        "condition_id": "condition_manufacturing_new_orders",
        "research_key": "research.manufacturing_new_orders.factory",
        "release_key": "manufacturing_new_orders.factory",
        "sector_key": "factory",
        "public_signal_reference": "public-manufacturing-release",
        "observed_at": OBSERVED_AT,
        "expected_change_ratio": d("0.010000"),
        "actual_change_ratio": d("0.015000"),
        "surprise_ratio": d("0.005000"),
        "source_count": d("3"),
        "revision_ratio": d("0.050000"),
        "confirmation_ratio": d("0.900000"),
        "base_confidence": d("0.920000"),
        "signal_config_version": "manufacturing-new-orders-signal-v0",
    }
    values.update(overrides)
    return module.MarketResearchManufacturingNewOrdersDigestSignal(**values)


def report(*signals: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_market_research_manufacturing_new_orders_digest(
        signals,
        config=cfg if cfg is not None else config(),
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


def test_digest_reduces_new_orders_signals_and_sorts_deterministically() -> None:
    result = report(
        signal(
            condition_id="condition_factory_stale",
            research_key="research.manufacturing_new_orders.factory",
            release_key="manufacturing_new_orders.factory",
            sector_key="factory",
            public_signal_reference="https://vendor.example/release?token=secret-123",
            observed_at=GENERATED_AT - timedelta(hours=3),
            expected_change_ratio=d("0.010000"),
            actual_change_ratio=d("-0.070000"),
            surprise_ratio=d("0.080000"),
            source_count=d("1"),
            revision_ratio=d("0.350000"),
            confirmation_ratio=d("0.420000"),
            base_confidence=d("0.880000"),
        ),
        signal(
            condition_id="condition_durable_watch",
            research_key="research.manufacturing_new_orders.durable_goods",
            release_key="manufacturing_new_orders.durable_goods",
            sector_key="durable_goods",
            public_signal_reference="private-durable-goods-feed",
            observed_at=GENERATED_AT - timedelta(hours=1),
            expected_change_ratio=d("0.020000"),
            actual_change_ratio=d("-0.040000"),
            surprise_ratio=d("0.060000"),
            source_count=d("2"),
            revision_ratio=d("0.120000"),
            confirmation_ratio=d("0.600000"),
            base_confidence=d("0.850000"),
        ),
        signal(
            condition_id="condition_core_ready",
            research_key="research.manufacturing_new_orders.core_capex",
            release_key="manufacturing_new_orders.core_capex",
            sector_key="core_capex",
            public_signal_reference="public-core-capex-release",
            observed_at=GENERATED_AT - timedelta(minutes=25),
            expected_change_ratio=d("0.012000"),
            actual_change_ratio=d("0.014000"),
            surprise_ratio=d("0.002000"),
            source_count=d("3"),
            revision_ratio=d("0.040000"),
            confirmation_ratio=d("0.900000"),
            base_confidence=d("0.920000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == (
        "market-research-manufacturing-new-orders-digest-v0"
    )
    assert result.digest_status == "blocked"
    assert result.recommended_next_step == (
        "block_report_only_market_research_manufacturing_new_orders_digest"
    )
    assert result.signal_count == d("3")
    assert result.ready_signal_count == d("1")
    assert result.watch_signal_count == d("1")
    assert result.blocked_signal_count == d("1")
    assert result.material_surprise_count == d("2")
    assert result.stale_signal_count == d("1")
    assert result.thin_source_count == d("1")
    assert result.high_revision_count == d("1")
    assert result.confirmation_gap_count == d("2")
    assert result.average_surprise_ratio == d("0.047333")
    assert result.max_signal_age_seconds == d("10800.000000")
    assert result.average_source_count == d("2.000000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.release_key for row in result.rows) == (
        "manufacturing_new_orders.factory",
        "manufacturing_new_orders.durable_goods",
        "manufacturing_new_orders.core_capex",
    )

    blocked, watched, ready = result.rows
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.surprise_delta == d("-0.080000")
    assert blocked.confidence_decay_factor == d("0.666667")
    assert blocked.final_confidence == d("0.586667")
    assert blocked.redacted_public_signal_reference == "sha256:3e3139475b34"
    assert blocked.reason_codes == (
        "market_research_manufacturing_new_orders_digest_stale_signal",
        "market_research_manufacturing_new_orders_digest_material_surprise",
        "market_research_manufacturing_new_orders_digest_thin_sources",
        "market_research_manufacturing_new_orders_digest_high_revision",
        "market_research_manufacturing_new_orders_digest_confirmation_gap",
        "market_research_manufacturing_new_orders_digest_low_confidence",
    )

    assert watched.digest_status == "watch"
    assert watched.signal_age_seconds == d("3600.000000")
    assert watched.surprise_delta == d("-0.060000")
    assert watched.confidence_decay_factor == d("1.000000")
    assert watched.final_confidence == d("0.850000")
    assert watched.redacted_public_signal_reference == "sha256:505667b274bb"
    assert watched.reason_codes == (
        "market_research_manufacturing_new_orders_digest_material_surprise",
        "market_research_manufacturing_new_orders_digest_confirmation_gap",
    )

    assert ready.digest_status == "ready"
    assert ready.signal_age_seconds == d("1500.000000")
    assert ready.surprise_delta == d("0.002000")
    assert ready.final_confidence == d("0.920000")
    assert ready.redacted_public_signal_reference == "public-core-capex-release"
    assert ready.reason_codes == (
        "market_research_manufacturing_new_orders_digest_ready",
    )

    assert tuple(item.reason_code for item in result.reason_code_counts) == (
        "market_research_manufacturing_new_orders_digest_confirmation_gap",
        "market_research_manufacturing_new_orders_digest_material_surprise",
        "market_research_manufacturing_new_orders_digest_high_revision",
        "market_research_manufacturing_new_orders_digest_low_confidence",
        "market_research_manufacturing_new_orders_digest_stale_signal",
        "market_research_manufacturing_new_orders_digest_thin_sources",
    )
    assert result.reason_code_counts[0].count == d("2")
    assert result.reason_code_counts[0].signal_ratio == d("0.666667")


def test_empty_digest_is_report_only_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.digest_status == "blocked"
    assert result.recommended_next_step == (
        "block_report_only_market_research_manufacturing_new_orders_digest"
    )
    assert result.signal_count == d("0")
    assert result.ready_signal_count == d("0")
    assert result.watch_signal_count == d("0")
    assert result.blocked_signal_count == d("0")
    assert result.material_surprise_count == d("0")
    assert result.stale_signal_count == d("0")
    assert result.thin_source_count == d("0")
    assert result.high_revision_count == d("0")
    assert result.confirmation_gap_count == d("0")
    assert result.average_surprise_ratio == ZERO
    assert result.max_signal_age_seconds == ZERO
    assert result.average_source_count == ZERO
    assert result.reason_codes == (
        "market_research_manufacturing_new_orders_digest_empty",
    )
    assert result.reason_code_counts == (
        api().MarketResearchManufacturingNewOrdersDigestReasonCodeCount(
            reason_code="market_research_manufacturing_new_orders_digest_empty",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    populated = report(signal())
    for value in (result, populated, *populated.rows, *populated.reason_code_counts):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            item = getattr(value, field.name)
            if field.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_seconds",
                    "_confidence",
                    "_factor",
                    "_delta",
                ),
            ):
                assert type(item) is Decimal


def test_payload_uses_decimal_strings_utc_datetimes_and_redacted_references() -> None:
    module = api()
    result = report(
        signal(
            public_signal_reference="https://vendor.example/new-orders?token=secret-123",
            observed_at=datetime(2026, 7, 3, 8, 30, tzinfo=timezone(timedelta(hours=-7))),
        ),
        generated_at=datetime(2026, 7, 3, 9, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.market_research_manufacturing_new_orders_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["ready_signal_count"] == "1.000000"
    assert payload["watch_signal_count"] == "0.000000"
    assert payload["blocked_signal_count"] == "0.000000"
    assert payload["average_surprise_ratio"] == "0.005000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-03T15:30:00+00:00"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["redacted_public_signal_reference"].startswith("sha256:")
    assert "secret-123" not in rendered
    assert "token=" not in rendered
    assert "wallet" not in rendered
    assert "private_key" not in rendered
    assert "authorization" not in rendered
    assert "api_key" not in rendered
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_mutable_flags_duplicates_and_inconsistent_rows() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_market_research_manufacturing_new_orders_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="market-research-manufacturing-new-orders-digest-v1")
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        module.MarketResearchManufacturingNewOrdersDigestReport(
            generated_at=_DatetimeSubclass(2026, 7, 3, 16, 0, tzinfo=UTC),
            config_version="market-research-manufacturing-new-orders-digest-v0",
            digest_status="ready",
            recommended_next_step=(
                "accept_report_only_market_research_manufacturing_new_orders_digest"
            ),
            signal_count=ZERO,
            ready_signal_count=ZERO,
            watch_signal_count=ZERO,
            blocked_signal_count=ZERO,
            material_surprise_count=ZERO,
            stale_signal_count=ZERO,
            thin_source_count=ZERO,
            high_revision_count=ZERO,
            confirmation_gap_count=ZERO,
            average_surprise_ratio=ZERO,
            max_signal_age_seconds=ZERO,
            average_source_count=ZERO,
            reason_codes=("market_research_manufacturing_new_orders_digest_empty",),
            reason_code_counts=(),
            rows=(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id=_StringSubclass("condition"))
    with pytest.raises(ValueError, match="surprise_ratio"):
        signal(surprise_ratio=0.05)
    with pytest.raises(ValueError, match="source_count"):
        signal(source_count=_DecimalSubclass("3"))
    with pytest.raises(ValueError, match="source_count"):
        signal(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="revision_ratio"):
        signal(revision_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 3, 15, 30))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 3, 15, 30, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="observed_at"):
        report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate condition_id"):
        report(signal(), signal())
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal(readonly=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(signal()).rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report(signal()), paper_only=False)
    with pytest.raises(ValueError, match="signal_count"):
        replace(report(signal()), signal_count=d("2"))
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(
            report(signal()),
            recommended_next_step=(
                "block_report_only_market_research_manufacturing_new_orders_digest"
            ),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report(),
            reason_codes=(
                "market_research_manufacturing_new_orders_digest_ready",
            ),
        )

    frozen = signal(condition_id="condition_frozen")
    with pytest.raises(FrozenInstanceError):
        frozen.release_key = "changed"  # type: ignore[misc]


def test_public_api_and_static_scope_are_pure_in_memory_report_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_MANUFACTURING_NEW_ORDERS_DIGEST_CONFIG_VERSION",
        "MarketResearchManufacturingNewOrdersDigestConfig",
        "MarketResearchManufacturingNewOrdersDigestReasonCodeCount",
        "MarketResearchManufacturingNewOrdersDigestReport",
        "MarketResearchManufacturingNewOrdersDigestRow",
        "MarketResearchManufacturingNewOrdersDigestSignal",
        "build_market_research_manufacturing_new_orders_digest",
        "market_research_manufacturing_new_orders_digest_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen
            for field in fields(exported):
                assert field.name not in {
                    "account_id",
                    "api_key",
                    "private_key",
                    "wallet_address",
                    "order_id",
                }

    source_path = Path(
        "src/polymarket_alpha_lab/market_research_manufacturing_new_orders_digest.py",
    )
    source = source_path.read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function_name = ""
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            assert function_name not in {
                "open",
                "connect",
                "request",
                "urlopen",
                "trade",
                "submit",
                "cancel",
                "sign",
            }

    lowered_public_names = " ".join(module.__all__).lower()
    assert "wallet" not in lowered_public_names
    assert "auth" not in lowered_public_names
    assert "private_key" not in lowered_public_names

    lowered_source = source.lower()
    for forbidden in (
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "password",
        "private",
        "private_key",
        "secret",
        "signature",
        "token",
        "wallet",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange_mutation",
    ):
        assert forbidden not in lowered_source
