from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


GENERATED_AT = datetime(2026, 7, 4, 17, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_energy_power_demand_peak_shock_digest"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_energy_power_demand_peak_shock_digest.py"
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def digest():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = digest()
    values = {
        "config_version": (
            module
            .DEFAULT_MARKET_RESEARCH_ENERGY_POWER_DEMAND_PEAK_SHOCK_DIGEST_CONFIG_VERSION
        ),
        "fresh_observation_max_age_seconds": d("1800.000000"),
        "min_source_count": d("2.000000"),
        "demand_peak_shock_ratio_threshold": d("0.120000"),
        "reserve_margin_watch_threshold": d("0.100000"),
        "heat_stress_celsius_threshold": d("5.000000"),
        "outage_share_threshold": d("0.150000"),
        "max_acknowledgement_lag_seconds": d("600.000000"),
    }
    values.update(overrides)
    return module.MarketResearchEnergyPowerDemandPeakShockDigestConfig(**values)


def input_row(
    research_key: str = "energy.power.demand.ready",
    *,
    condition_id: str = "condition_ercot_south",
    market_slug: str = "ercot-south-demand-peak-shock",
    power_market_key: str = "ercot.south.peak",
    power_region: str = "ercot",
    demand_zone: str = "south-zone",
    public_demand_reference: str = "ercot-public-demand-note",
    observed_at: datetime | None = None,
    acknowledged_at: object = _UNSET,
    source_count: Decimal = d("3.000000"),
    forecast_peak_mw: Decimal = d("36000.000000"),
    observed_peak_mw: Decimal = d("36720.000000"),
    reserve_margin_ratio: Decimal = d("0.220000"),
    temperature_anomaly_c: Decimal = d("2.000000"),
    outage_share_ratio: Decimal = d("0.050000"),
    source_config_version: str = "energy-power-demand-peak-shock-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = digest()
    return module.MarketResearchEnergyPowerDemandPeakShockDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        market_slug=market_slug,
        power_market_key=power_market_key,
        power_region=power_region,
        demand_zone=demand_zone,
        public_demand_reference=public_demand_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        acknowledged_at=(
            GENERATED_AT - timedelta(minutes=5)
            if acknowledged_at is _UNSET
            else acknowledged_at
        ),
        source_count=source_count,
        forecast_peak_mw=forecast_peak_mw,
        observed_peak_mw=observed_peak_mw,
        reserve_margin_ratio=reserve_margin_ratio,
        temperature_anomaly_c=temperature_anomaly_c,
        outage_share_ratio=outage_share_ratio,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = digest()
    return module.build_market_research_energy_power_demand_peak_shock_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_demand_peak_shock_digest_reduces_rows_redacts_and_sorts() -> None:
    module = digest()

    summary = report(
        (
            input_row(
                "energy.power.pjm.watch",
                condition_id="condition_pjm_west",
                market_slug="pjm-west-demand-peak-shock",
                power_market_key="pjm.west.peak",
                power_region="pjm",
                demand_zone="west-zone",
                public_demand_reference=(
                    "https://iso.example/pjm-demand?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(minutes=45),
                acknowledged_at=GENERATED_AT - timedelta(minutes=25),
                source_count=d("1.000000"),
                forecast_peak_mw=d("50000.000000"),
                observed_peak_mw=d("57000.000000"),
                reserve_margin_ratio=d("0.120000"),
                temperature_anomaly_c=d("5.500000"),
                outage_share_ratio=d("0.200000"),
            ),
            input_row(),
            input_row(
                "energy.power.ercot.blocked",
                condition_id="condition_ercot_north",
                market_slug="ercot-north-demand-peak-shock",
                power_market_key="ercot.north.peak",
                power_region="ercot",
                demand_zone="north-zone",
                public_demand_reference="wallet://private/ercot-demand-feed",
                observed_at=GENERATED_AT - timedelta(hours=2),
                acknowledged_at=None,
                source_count=d("2.000000"),
                forecast_peak_mw=d("10000.000000"),
                observed_peak_mw=d("11400.000000"),
                reserve_margin_ratio=d("0.080000"),
                temperature_anomaly_c=d("6.000000"),
                outage_share_ratio=d("0.100000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert isinstance(
        summary,
        module.MarketResearchEnergyPowerDemandPeakShockDigestReport,
    )
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_ENERGY_POWER_DEMAND_PEAK_SHOCK_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_power_demand_peak_shock_digest"
    )
    assert summary.power_demand_peak_shock_count == d("3.000000")
    assert summary.ready_shock_count == d("1.000000")
    assert summary.watch_shock_count == d("1.000000")
    assert summary.blocked_shock_count == d("1.000000")
    assert summary.demand_peak_shock_count == d("2.000000")
    assert summary.reserve_scarcity_count == d("1.000000")
    assert summary.heat_stress_count == d("2.000000")
    assert summary.outage_pressure_count == d("1.000000")
    assert summary.stale_observation_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_acknowledgement_count == d("1.000000")
    assert summary.slow_acknowledgement_count == d("1.000000")
    assert summary.average_peak_shock_ratio == d("0.100000")
    assert summary.max_observation_age_seconds == d("7200.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.power_market_key for row in summary.rows) == (
        "ercot.north.peak",
        "pjm.west.peak",
        "ercot.south.peak",
    )

    blocked = summary.rows[0]
    assert blocked.shock_status == "blocked"
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.acknowledgement_lag_seconds is None
    assert blocked.peak_demand_delta_mw == d("1400.000000")
    assert blocked.peak_shock_ratio == d("0.140000")
    assert blocked.redacted_public_demand_reference == "sha256:8b980fb43f7c"
    assert blocked.reason_codes == (
        "market_research_energy_power_demand_peak_shock_digest_demand_peak_shock",
        "market_research_energy_power_demand_peak_shock_digest_reserve_scarcity",
        "market_research_energy_power_demand_peak_shock_digest_heat_stress",
        (
            "market_research_energy_power_demand_peak_shock_digest_"
            "missing_acknowledgement"
        ),
        "market_research_energy_power_demand_peak_shock_digest_stale_observation",
    )

    watched = summary.rows[1]
    assert watched.shock_status == "watch"
    assert watched.observation_age_seconds == d("2700.000000")
    assert watched.acknowledgement_lag_seconds == d("1200.000000")
    assert watched.source_gap_count == d("1.000000")
    assert watched.peak_demand_delta_mw == d("7000.000000")
    assert watched.peak_shock_ratio == d("0.140000")
    assert watched.redacted_public_demand_reference == "sha256:64a17784ccc9"
    assert watched.reason_codes == (
        "market_research_energy_power_demand_peak_shock_digest_demand_peak_shock",
        "market_research_energy_power_demand_peak_shock_digest_heat_stress",
        "market_research_energy_power_demand_peak_shock_digest_outage_pressure",
        (
            "market_research_energy_power_demand_peak_shock_digest_"
            "slow_acknowledgement"
        ),
        "market_research_energy_power_demand_peak_shock_digest_stale_observation",
        "market_research_energy_power_demand_peak_shock_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.shock_status == "ready"
    assert ready.observation_age_seconds == d("900.000000")
    assert ready.acknowledgement_lag_seconds == d("600.000000")
    assert ready.peak_demand_delta_mw == d("720.000000")
    assert ready.peak_shock_ratio == d("0.020000")
    assert ready.redacted_public_demand_reference == "ercot-public-demand-note"
    assert ready.reason_codes == (
        "market_research_energy_power_demand_peak_shock_digest_ready",
    )

    assert summary.reason_code_counts == (
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_"
                "demand_peak_shock"
            ),
            count=d("2.000000"),
            shock_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_"
                "reserve_scarcity"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_heat_stress"
            ),
            count=d("2.000000"),
            shock_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_"
                "outage_pressure"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_"
                "slow_acknowledgement"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_"
                "stale_observation"
            ),
            count=d("2.000000"),
            shock_ratio=d("0.666667"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_thin_sources"
            ),
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code="market_research_energy_power_demand_peak_shock_digest_ready",
            count=d("1.000000"),
            shock_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.source_config_versions == (
        ("ercot.north.peak", "energy-power-demand-peak-shock-source-v0"),
        ("ercot.south.peak", "energy-power-demand-peak-shock-source-v0"),
        ("pjm.west.peak", "energy-power-demand-peak-shock-source-v0"),
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "iso.example",
        "https://",
        "wallet://",
        "ercot-demand-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
        "order",
    ):
        assert token not in public


def test_empty_demand_peak_shock_digest_is_blocked_and_report_only() -> None:
    module = digest()
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_power_demand_peak_shock_digest"
    )
    assert summary.power_demand_peak_shock_count == ZERO
    assert summary.ready_shock_count == ZERO
    assert summary.watch_shock_count == ZERO
    assert summary.blocked_shock_count == ZERO
    assert summary.average_peak_shock_ratio == ZERO
    assert summary.max_observation_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.rows == ()
    assert summary.source_config_versions == ()
    assert summary.reason_code_counts == (
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_power_demand_peak_shock_digest_no_inputs"
            ),
            count=d("1.000000"),
            shock_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_energy_power_demand_peak_shock_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_demand_peak_shock_payload_uses_decimal_strings_and_redacted_refs() -> None:
    module = digest()
    summary = report((input_row(),))
    payload = module.market_research_energy_power_demand_peak_shock_digest_payload(
        summary,
    )

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["power_demand_peak_shock_count"] == "1.000000"
    assert payload["average_peak_shock_ratio"] == "0.020000"
    assert payload["rows"][0]["source_count"] == "3.000000"
    assert payload["rows"][0]["peak_shock_ratio"] == "0.020000"
    assert payload["generated_at"] == "2026-07-04T17:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    assert "'public_demand_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_demand_peak_shock_validates_frozen_contracts_decimals_and_flags() -> None:
    module = digest()

    assert module.MarketResearchEnergyPowerDemandPeakShockDigestConfig.__dataclass_params__.frozen
    assert module.MarketResearchEnergyPowerDemandPeakShockDigestInputRow.__dataclass_params__.frozen
    assert module.MarketResearchEnergyPowerDemandPeakShockDigestRow.__dataclass_params__.frozen
    assert (
        module.MarketResearchEnergyPowerDemandPeakShockDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert module.MarketResearchEnergyPowerDemandPeakShockDigestReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        input_row().source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("energy-demand-peak-shock-v0"))
    with pytest.raises(ValueError, match="fresh_observation_max_age_seconds"):
        config(fresh_observation_max_age_seconds=_DecimalSubclass("1800.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="demand_peak_shock_ratio_threshold"):
        config(demand_peak_shock_ratio_threshold=0.12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="research_key"):
        input_row(_StringSubclass("energy.bad"))
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="Demand Peak Shock")
    with pytest.raises(ValueError, match="power_region"):
        input_row(power_region="broker-feed")
    with pytest.raises(ValueError, match="public_demand_reference"):
        input_row(public_demand_reference=" ")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 4, 16, 0))
    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(acknowledged_at=_DatetimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_count"):
        input_row(source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_peak_mw"):
        input_row(forecast_peak_mw=d("0.000000"))
    with pytest.raises(ValueError, match="observed_peak_mw"):
        input_row(observed_peak_mw=Decimal("NaN"))
    with pytest.raises(ValueError, match="reserve_margin_ratio"):
        input_row(reserve_margin_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="temperature_anomaly_c"):
        input_row(temperature_anomaly_c=_DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="outage_share_ratio"):
        input_row(outage_share_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_energy_power_demand_peak_shock_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_market_research_energy_power_demand_peak_shock_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 17, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="duplicate power_market_key"):
        report(
            (
                input_row("energy.power.one"),
                input_row("energy.power.two"),
            ),
        )


def test_demand_peak_shock_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="shock_status"):
        replace(
            ready,
            reason_codes=(
                "market_research_energy_power_demand_peak_shock_digest_demand_peak_shock",
                "market_research_energy_power_demand_peak_shock_digest_ready",
            ),
        )
    with pytest.raises(ValueError, match="peak_demand_delta_mw"):
        replace(ready, peak_demand_delta_mw=d("9.000000"))
    with pytest.raises(ValueError, match="redacted_public_demand_reference"):
        replace(ready, redacted_public_demand_reference="https://host?token=secret")

    with pytest.raises(ValueError, match="ready_shock_count"):
        replace(report((input_row(),)), ready_shock_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        replace(
            report(
                (
                    input_row(
                        "energy.power.z",
                        power_market_key="z.power.market",
                        market_slug="z-power-market",
                    ),
                    input_row(),
                ),
            ),
            rows=tuple(
                reversed(
                    report(
                        (
                            input_row(
                                "energy.power.z",
                                power_market_key="z.power.market",
                                market_slug="z-power-market",
                            ),
                            input_row(),
                        ),
                    ).rows,
                ),
            ),
        )


def test_public_numeric_fields_are_decimals_and_type_hints_avoid_float() -> None:
    summary = report((input_row(),))

    for value in _walk_dataclasses(summary):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float(hint)
        for field in fields(value):
            if _is_public_numeric_field(field.name):
                field_value = getattr(value, field.name)
                assert field_value is None or type(field_value) is Decimal


def test_module_has_no_io_durable_store_or_live_trading_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "submit_order",
        "cancel_order",
        "replace_order",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "fetch",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "send",
        "submit",
        "cancel",
        "trade",
        "order",
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


def _walk_dataclasses(value: object) -> tuple[object, ...]:
    found: list[object] = []
    if is_dataclass(value) and not isinstance(value, type):
        found.append(value)
        for field in fields(value):
            found.extend(_walk_dataclasses(getattr(value, field.name)))
    elif isinstance(value, tuple):
        for item in value:
            found.extend(_walk_dataclasses(item))
    return tuple(found)


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _is_public_numeric_field(name: str) -> bool:
    if "reference" in name or name in ("rows", "reason_code_counts"):
        return False
    fragments = (
        "count",
        "ratio",
        "seconds",
        "peak",
        "mw",
        "threshold",
        "anomaly",
    )
    return any(fragment in name for fragment in fragments)


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))
