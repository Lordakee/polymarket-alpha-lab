from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_energy_power_grid_frequency_event_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_energy_power_grid_frequency_event_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def event(
    source_id: str = "source-alpha",
    *,
    grid_region: str = "ercot_north",
    balancing_authority: str = "ercot",
    market_slug: str = "texas-grid-frequency-event",
    observed_at: datetime = datetime(2026, 7, 4, 17, 50, tzinfo=UTC),
    frequency_deviation_mhz: str | Decimal = "-12.000000",
    under_frequency_duration_seconds: str | Decimal = "5.000000",
    reserve_margin_percentage: str | Decimal = "12.000000",
    forced_outage_mw: str | Decimal = "120.000000",
    load_forecast_error_mw: str | Decimal = "140.000000",
    telemetry_age_seconds: str | Decimal = "60.000000",
    source_count: str | Decimal = "3.000000",
    source_disagreement_ratio: str | Decimal = "0.050000",
    upstream_reason_codes: tuple[str, ...] = ("scada_frequency_telemetry",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = digest()
    return module.MarketResearchEnergyPowerGridFrequencyEventDigestInput(
        source_id=source_id,
        grid_region=grid_region,
        balancing_authority=balancing_authority,
        market_slug=market_slug,
        observed_at=observed_at,
        frequency_deviation_mhz=(
            frequency_deviation_mhz
            if isinstance(frequency_deviation_mhz, Decimal)
            else d(frequency_deviation_mhz)
        ),
        under_frequency_duration_seconds=(
            under_frequency_duration_seconds
            if isinstance(under_frequency_duration_seconds, Decimal)
            else d(under_frequency_duration_seconds)
        ),
        reserve_margin_percentage=(
            reserve_margin_percentage
            if isinstance(reserve_margin_percentage, Decimal)
            else d(reserve_margin_percentage)
        ),
        forced_outage_mw=(
            forced_outage_mw
            if isinstance(forced_outage_mw, Decimal)
            else d(forced_outage_mw)
        ),
        load_forecast_error_mw=(
            load_forecast_error_mw
            if isinstance(load_forecast_error_mw, Decimal)
            else d(load_forecast_error_mw)
        ),
        telemetry_age_seconds=(
            telemetry_age_seconds
            if isinstance(telemetry_age_seconds, Decimal)
            else d(telemetry_age_seconds)
        ),
        source_count=source_count if isinstance(source_count, Decimal) else d(source_count),
        source_disagreement_ratio=(
            source_disagreement_ratio
            if isinstance(source_disagreement_ratio, Decimal)
            else d(source_disagreement_ratio)
        ),
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**kwargs: object):
    module = digest()
    return module.MarketResearchEnergyPowerGridFrequencyEventDigestConfig(**kwargs)


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_energy_power_grid_frequency_event_digest(
        rows,
        config=(
            cfg
            if cfg is not None
            else module.MarketResearchEnergyPowerGridFrequencyEventDigestConfig()
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def blocked_event():
    return event(
        "source-frequency-blocked",
        grid_region="ercot_north",
        balancing_authority="ercot",
        market_slug="ercot-frequency-breach",
        observed_at=datetime(2026, 7, 4, 13, 30, tzinfo=timezone(timedelta(hours=-4))),
        frequency_deviation_mhz="-72.250000",
        under_frequency_duration_seconds="420.000000",
        reserve_margin_percentage="2.500000",
        forced_outage_mw="1800.000000",
        load_forecast_error_mw="-2400.000000",
        telemetry_age_seconds="900.000000",
        source_count="1.000000",
        source_disagreement_ratio="0.650000",
        upstream_reason_codes=(
            "iso_frequency_alert",
            "scada_frequency_telemetry",
            "iso_frequency_alert",
        ),
    )


def watch_event():
    return event(
        "source-reserve-watch",
        grid_region="caiso_np15",
        balancing_authority="caiso",
        market_slug="caiso-reserve-frequency-watch",
        frequency_deviation_mhz="-32.000000",
        under_frequency_duration_seconds="80.000000",
        reserve_margin_percentage="5.000000",
        forced_outage_mw="650.000000",
        load_forecast_error_mw="-900.000000",
        telemetry_age_seconds="700.000000",
        source_count="2.000000",
        source_disagreement_ratio="0.250000",
        upstream_reason_codes=("reserve_margin_notice",),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(
        digest_report,
        module.MarketResearchEnergyPowerGridFrequencyEventDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-energy-power-grid-frequency-event-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_energy_power_grid_frequency_event_digest"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.frequency_event_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("energy_power_grid_frequency_event_empty",)
    assert digest_report.reason_code_counts == (
        module.MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount(
            reason_code="energy_power_grid_frequency_event_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_blocked_watch_and_pass_events_produce_meaningful_counts_and_score() -> None:
    digest_report = report(blocked_event(), watch_event(), event("source-pass"))

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_energy_power_grid_frequency_event_digest"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.frequency_deviation_event_count == d("2.000000")
    assert digest_report.under_frequency_event_count == d("2.000000")
    assert digest_report.low_reserve_margin_count == d("2.000000")
    assert digest_report.forced_outage_count == d("2.000000")
    assert digest_report.load_forecast_error_count == d("2.000000")
    assert digest_report.stale_telemetry_count == d("2.000000")
    assert digest_report.thin_source_quorum_count == d("1.000000")
    assert digest_report.source_disagreement_count == d("2.000000")
    assert digest_report.total_forced_outage_mw == d("2570.000000")
    assert digest_report.max_absolute_frequency_deviation_mhz == d("72.250000")
    assert digest_report.max_under_frequency_duration_seconds == d("420.000000")
    assert digest_report.min_reserve_margin_percentage == d("2.500000")
    assert digest_report.max_absolute_load_forecast_error_mw == d("2400.000000")
    assert digest_report.max_telemetry_age_seconds == d("900.000000")
    assert digest_report.frequency_event_risk_score == d("0.500000")

    assert tuple(row.market_slug for row in digest_report.rows) == (
        "ercot-frequency-breach",
        "caiso-reserve-frequency-watch",
        "texas-grid-frequency-event",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.frequency_event_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 4, 17, 30, tzinfo=UTC)
    assert blocked.absolute_frequency_deviation_mhz == d("72.250000")
    assert blocked.absolute_load_forecast_error_mw == d("2400.000000")
    assert blocked.risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == (
        "iso_frequency_alert",
        "scada_frequency_telemetry",
    )
    assert blocked.reason_codes == (
        "energy_power_grid_frequency_deviation_blocked",
        "energy_power_grid_under_frequency_duration_blocked",
        "energy_power_grid_low_reserve_margin_blocked",
        "energy_power_grid_forced_outage_blocked",
        "energy_power_grid_load_forecast_error_blocked",
        "energy_power_grid_stale_telemetry",
        "energy_power_grid_thin_source_quorum",
        "energy_power_grid_source_disagreement_blocked",
    )
    assert watch.frequency_event_status == "watch"
    assert watch.risk_score == d("0.500000")
    assert watch.reason_codes == (
        "energy_power_grid_frequency_deviation_watch",
        "energy_power_grid_under_frequency_duration_watch",
        "energy_power_grid_low_reserve_margin_watch",
        "energy_power_grid_forced_outage_watch",
        "energy_power_grid_load_forecast_error_watch",
        "energy_power_grid_stale_telemetry",
        "energy_power_grid_source_disagreement_watch",
    )
    assert passed.frequency_event_status == "pass"
    assert passed.reason_codes == ("energy_power_grid_frequency_event_passed",)

    assert digest_report.reason_codes == (
        "energy_power_grid_frequency_deviation_blocked",
        "energy_power_grid_frequency_deviation_watch",
        "energy_power_grid_under_frequency_duration_blocked",
        "energy_power_grid_under_frequency_duration_watch",
        "energy_power_grid_low_reserve_margin_blocked",
        "energy_power_grid_low_reserve_margin_watch",
        "energy_power_grid_forced_outage_blocked",
        "energy_power_grid_forced_outage_watch",
        "energy_power_grid_load_forecast_error_blocked",
        "energy_power_grid_load_forecast_error_watch",
        "energy_power_grid_stale_telemetry",
        "energy_power_grid_thin_source_quorum",
        "energy_power_grid_source_disagreement_blocked",
        "energy_power_grid_source_disagreement_watch",
        "energy_power_grid_frequency_event_watch_present",
    )
    assert tuple(
        (item.reason_code, item.count, item.row_ratio)
        for item in digest_report.reason_code_counts
    )[:3] == (
        (
            "energy_power_grid_frequency_deviation_blocked",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "energy_power_grid_frequency_deviation_watch",
            d("1.000000"),
            d("0.333333"),
        ),
        (
            "energy_power_grid_under_frequency_duration_blocked",
            d("1.000000"),
            d("0.333333"),
        ),
    )
    assert digest_report.reason_code_counts[-1] == (
        digest().MarketResearchEnergyPowerGridFrequencyEventDigestReasonCodeCount(
            reason_code="energy_power_grid_frequency_event_watch_present",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_non_default_thresholds_can_downgrade_moderate_grid_risk() -> None:
    cfg = config(
        watch_frequency_deviation_mhz=d("40.000000"),
        blocked_frequency_deviation_mhz=d("80.000000"),
        watch_under_frequency_duration_seconds=d("120.000000"),
        blocked_under_frequency_duration_seconds=d("600.000000"),
        watch_reserve_margin_percentage=d("4.000000"),
        blocked_reserve_margin_percentage=d("2.000000"),
        watch_forced_outage_mw=d("1000.000000"),
        blocked_forced_outage_mw=d("2200.000000"),
        watch_load_forecast_error_mw=d("1200.000000"),
        blocked_load_forecast_error_mw=d("2600.000000"),
        max_telemetry_age_seconds=d("800.000000"),
        watch_source_disagreement_ratio=d("0.300000"),
        blocked_source_disagreement_ratio=d("0.700000"),
    )

    digest_report = report(watch_event(), cfg=cfg)

    assert digest_report.digest_status == "pass"
    assert digest_report.rows[0].frequency_event_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "energy_power_grid_frequency_event_passed",
    )
    assert digest_report.reason_codes == ("energy_power_grid_frequency_event_clear",)
    assert digest_report.frequency_event_risk_score == d("0.000000")


def test_rows_reason_codes_and_counts_are_deterministic() -> None:
    first = watch_event()
    second = blocked_event()
    third = event("source-pass", market_slug="a-pass-market")

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "ercot-frequency-breach",
        "caiso-reserve-frequency-watch",
        "a-pass-market",
    )
    for row in forward.rows:
        assert len(row.reason_codes) == len(set(row.reason_codes))
    assert forward.reason_code_counts == tuple(
        sorted(
            forward.reason_code_counts,
            key=lambda item: forward.reason_codes.index(item.reason_code),
        ),
    )


def test_validation_frozen_dataclasses_and_hard_flags() -> None:
    module = digest()
    row = event("source-frozen")
    digest_report = report(row)

    assert row.observed_at == datetime(2026, 7, 4, 17, 50, tzinfo=UTC)
    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest_report.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest_report.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadInput",
            (module.MarketResearchEnergyPowerGridFrequencyEventDigestInput,),
            {},
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        event("bad-time", observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="frequency_deviation_mhz must be a Decimal"):
        event(
            "bad-decimal",
            frequency_deviation_mhz=_DecimalSubclass("-12.000000"),
        )
    with pytest.raises(ValueError, match="grid_region must be a plain str"):
        event("bad-string", grid_region=_StringSubclass("ercot_north"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_market_research_energy_power_grid_frequency_event_digest(
            (row,),
            config=module.MarketResearchEnergyPowerGridFrequencyEventDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs must contain"):
        report("not-an-input")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(event("source-dupe"), event("source-dupe"))
    with pytest.raises(ValueError, match="paper_only"):
        event("bad-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="watch_frequency_deviation_mhz"):
        config(
            watch_frequency_deviation_mhz=d("90.000000"),
            blocked_frequency_deviation_mhz=d("80.000000"),
        )
    with pytest.raises(ValueError, match="blocked_reserve_margin_percentage"):
        config(
            watch_reserve_margin_percentage=d("4.000000"),
            blocked_reserve_margin_percentage=d("5.000000"),
        )

    valid_row = digest_report.rows[0]
    with pytest.raises(ValueError, match="risk_score must match"):
        replace(valid_row, risk_score=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "energy_power_grid_frequency_event_passed",
                "energy_power_grid_stale_telemetry",
            ),
        )


def test_payload_uses_six_decimal_strings_and_safe_report_contract() -> None:
    module = digest()
    digest_report = report(blocked_event(), watch_event(), event("source-pass"))

    payload = module.market_research_energy_power_grid_frequency_event_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "3.000000"
    assert payload["frequency_event_risk_score"] == "0.500000"
    assert payload["total_forced_outage_mw"] == "2570.000000"
    assert payload["rows"][0]["frequency_deviation_mhz"] == "-72.250000"
    assert payload["rows"][0]["absolute_frequency_deviation_mhz"] == "72.250000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T17:30:00+00:00"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.333333"
    json.dumps(payload, sort_keys=True)

    def walk_payload(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth_token" not in lowered
                assert "authentication" not in lowered
                assert "submit" not in lowered
                assert "cancel" not in lowered
                assert "replace" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MarketResearchEnergyPowerGridFrequencyEventDigestConfig(),
        event("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_module_has_no_forbidden_side_effect_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "os",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "getenv",
        "environ",
    ):
        assert forbidden not in source.lower()
