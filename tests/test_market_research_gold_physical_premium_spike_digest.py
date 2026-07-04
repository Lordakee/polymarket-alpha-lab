from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_gold_physical_premium_spike_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-gold-physical-premium-spike-digest-v0",
        "watch_risk_score": d("0.350000"),
        "blocked_risk_score": d("0.700000"),
        "premium_component_ceiling_bps": d("500.000000"),
        "watch_physical_premium_bps": d("150.000000"),
        "blocked_physical_premium_bps": d("500.000000"),
        "high_lease_rate_pressure": d("0.700000"),
        "high_etf_flow_stress": d("0.700000"),
        "high_local_fx_stress": d("0.700000"),
        "high_delivery_delay_days": d("7.000000"),
        "delivery_component_ceiling_days": d("14.000000"),
        "max_source_age_seconds": d("900.000000"),
        "min_source_count": d("2.000000"),
    }
    values.update(overrides)
    return module.GoldPhysicalPremiumSpikeDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    region: str = "us",
    venue: str = "comex-warehouse",
    market_slug: str = "gold-physical-premium-spike-us",
    physical_premium_bps: Decimal = d("40.000000"),
    lease_rate_pressure: Decimal = d("0.050000"),
    etf_flow_stress: Decimal = d("0.050000"),
    local_fx_stress: Decimal = d("0.040000"),
    delivery_delay_days: Decimal = d("0.500000"),
    source_count: Decimal = d("3.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.GoldPhysicalPremiumSpikeObservation(
        source_id=source_id,
        region=region,
        venue=venue,
        market_slug=market_slug,
        physical_premium_bps=physical_premium_bps,
        lease_rate_pressure=lease_rate_pressure,
        etf_flow_stress=etf_flow_stress,
        local_fx_stress=local_fx_stress,
        delivery_delay_days=delivery_delay_days,
        source_count=source_count,
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_gold_physical_premium_spike_digest(
        inputs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_payload_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"payload numeric must be a string, found {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_payload_numbers(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_payload_numbers(child)


def test_blocked_physical_premium_spike_scores_source_context_and_payload() -> None:
    module = api()
    result = digest(
        (
            observation(
                "lbma-blocked",
                region="hk",
                venue="hong-kong-physical-desk",
                market_slug="gold-physical-premium-spike-hk",
                physical_premium_bps=d("650.000000"),
                lease_rate_pressure=d("0.900000"),
                etf_flow_stress=d("0.800000"),
                local_fx_stress=d("0.700000"),
                delivery_delay_days=d("21.000000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    9,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=(
                    "regional_import_quota",
                    "bullion_dealer_inventory_tight",
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.config_version == "market-research-gold-physical-premium-spike-digest-v0"
    assert result.input_count == d("1.000000")
    assert result.row_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.stale_source_count == d("0.000000")
    assert result.low_quorum_count == d("0.000000")
    assert result.max_risk_score == d("0.908000")
    assert result.average_risk_score == d("0.908000")
    assert result.digest_status == "blocked"
    assert result.recommended_next_step == (
        "block_report_only_market_research_gold_physical_premium_spike_digest"
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    row = result.rows[0]
    assert row.observed_at == datetime(2026, 7, 4, 13, 59, tzinfo=UTC)
    assert row.source_age_seconds == d("60.000000")
    assert row.region == "hk"
    assert row.venue == "hong-kong-physical-desk"
    assert row.market_slug == "gold-physical-premium-spike-hk"
    assert row.physical_premium_bps == d("650.000000")
    assert row.risk_score == d("0.908000")
    assert row.digest_status == "blocked"
    assert row.reason_codes == (
        "bullion_dealer_inventory_tight",
        "delivery_delay_elevated",
        "etf_flow_stress_high",
        "lease_rate_pressure_high",
        "local_fx_stress_high",
        "physical_gold_premium_spike_blocked",
        "physical_premium_bps_extreme",
        "regional_import_quota",
        "source_fresh",
        "source_quorum_met",
    )

    payload = module.market_research_gold_physical_premium_spike_digest_payload(result)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T14:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["max_risk_score"] == "0.908000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T13:59:00+00:00"
    assert payload["rows"][0]["physical_premium_bps"] == "650.000000"
    assert payload["rows"][0]["risk_score"] == "0.908000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_payload_numbers(payload)


def test_empty_watch_pass_and_reason_count_sorting_are_deterministic() -> None:
    module = api()
    empty = digest(())

    assert empty.digest_status == "blocked"
    assert empty.reason_codes == ("physical_gold_premium_spike_digest_empty",)
    assert empty.reason_code_counts == (
        module.GoldPhysicalPremiumSpikeReasonCodeCount(
            reason_code="physical_gold_premium_spike_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert empty.rows == ()

    inputs = (
        observation(
            "z-pass",
            market_slug="gold-physical-premium-spike-calm",
            upstream_reason_codes=("public_vault_survey",),
        ),
        observation(
            "m-watch",
            region="in",
            venue="mumbai-bullion-desk",
            market_slug="gold-physical-premium-spike-in",
            physical_premium_bps=d("220.000000"),
            lease_rate_pressure=d("0.450000"),
            etf_flow_stress=d("0.300000"),
            local_fx_stress=d("0.200000"),
            delivery_delay_days=d("4.000000"),
            upstream_reason_codes=("import_duty_watch",),
        ),
        observation(
            "a-blocked",
            region="cn",
            venue="shanghai-physical-desk",
            market_slug="gold-physical-premium-spike-cn",
            physical_premium_bps=d("650.000000"),
            lease_rate_pressure=d("0.900000"),
            etf_flow_stress=d("0.800000"),
            local_fx_stress=d("0.700000"),
            delivery_delay_days=d("21.000000"),
        ),
    )
    report_a = digest(inputs)
    report_b = digest(tuple(reversed(inputs)))

    assert report_a == report_b
    assert [
        (row.source_id, row.digest_status, row.risk_score)
        for row in report_a.rows
    ] == [
        ("a-blocked", "blocked", d("0.908000")),
        ("m-watch", "watch", d("0.364200")),
        ("z-pass", "pass", d("0.058000")),
    ]
    assert report_a.blocked_count == d("1.000000")
    assert report_a.watch_count == d("1.000000")
    assert report_a.pass_count == d("1.000000")
    assert report_a.max_risk_score == d("0.908000")
    assert report_a.average_risk_score == d("0.443400")
    assert report_a.digest_status == "blocked"
    assert report_a.reason_codes == tuple(sorted(report_a.reason_codes))
    assert report_a.reason_code_counts == tuple(
        sorted(report_a.reason_code_counts, key=lambda item: item.reason_code),
    )
    assert report_a.reason_code_counts[0].reason_code == "delivery_delay_elevated"
    assert report_a.reason_code_counts[0].count == d("1.000000")
    assert report_a.reason_code_counts[0].row_ratio == d("0.333333")

    watch = report_a.rows[1]
    assert watch.reason_codes == (
        "import_duty_watch",
        "physical_gold_premium_spike_watch",
        "physical_premium_bps_elevated",
        "source_fresh",
        "source_quorum_met",
    )
    passed = report_a.rows[2]
    assert passed.reason_codes == (
        "physical_gold_premium_spike_pass",
        "public_vault_survey",
        "source_fresh",
        "source_quorum_met",
    )


def test_source_freshness_and_quorum_block_low_risk_rows() -> None:
    result = digest(
        (
            observation(
                "stale-low-risk",
                observed_at=GENERATED_AT - timedelta(seconds=1200),
                source_count=d("1.000000"),
            ),
        ),
    )

    assert result.digest_status == "blocked"
    assert result.blocked_count == d("1.000000")
    assert result.stale_source_count == d("1.000000")
    assert result.low_quorum_count == d("1.000000")
    row = result.rows[0]
    assert row.risk_score == d("0.058000")
    assert row.digest_status == "blocked"
    assert row.source_age_seconds == d("1200.000000")
    assert row.source_count == d("1.000000")
    assert row.reason_codes == (
        "physical_gold_premium_spike_blocked",
        "source_quorum_low",
        "source_stale",
    )


def test_validates_flags_decimals_utc_duplicates_frozen_and_public_numerics() -> None:
    module = api()

    with pytest.raises(ValueError, match="physical_premium_bps"):
        observation(physical_premium_bps=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="lease_rate_pressure"):
        observation(lease_rate_pressure=d("1.100000"))

    with pytest.raises(ValueError, match="delivery_delay_days"):
        observation(delivery_delay_days=d("-0.100000"))

    with pytest.raises(ValueError, match="watch_risk_score"):
        config(watch_risk_score=0.35)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="watch_risk_score"):
        config(watch_risk_score=d("0.900000"), blocked_risk_score=d("0.700000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 14, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="config"):
        module.build_market_research_gold_physical_premium_spike_digest(
            (observation(),),
            config=object(),
            generated_at=GENERATED_AT,
        )

    result = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        result.rows = ()  # type: ignore[misc]

    with pytest.raises(ValueError, match="row_count"):
        replace(result, row_count=d("2.000000"))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(result, reason_code_counts=())

    classes = (
        module.GoldPhysicalPremiumSpikeDigestConfig,
        module.GoldPhysicalPremiumSpikeObservation,
        module.GoldPhysicalPremiumSpikeDigestRow,
        module.GoldPhysicalPremiumSpikeReasonCodeCount,
        module.GoldPhysicalPremiumSpikeDigestReport,
    )
    values = {
        module.GoldPhysicalPremiumSpikeDigestConfig: config(),
        module.GoldPhysicalPremiumSpikeObservation: observation(),
        module.GoldPhysicalPremiumSpikeDigestRow: result.rows[0],
        module.GoldPhysicalPremiumSpikeReasonCodeCount: result.reason_code_counts[0],
        module.GoldPhysicalPremiumSpikeDigestReport: result,
    }
    for type_ in classes:
        assert is_dataclass(type_)
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type
            value = getattr(values[type_], field.name)
            if type(value) in (int, float) or isinstance(value, Decimal):
                assert type(value) is Decimal, f"{type_.__name__}.{field.name}"


def test_static_module_has_no_forbidden_surface_imports_calls_or_literals() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urlopen",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "connect(",
        "execute(",
        "open(",
        "web3",
        "wallet",
        "private_key",
        "api_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "database",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/market_research_gold_physical_premium_spike_digest.py",
        ).read_text(),
    )
    forbidden_import_roots = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "request",
        "urlopen",
        "read",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
