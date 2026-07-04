from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest

from polymarket_alpha_lab.market_research_energy_grid_reserve_margin_squeeze_digest import (
    DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION,
    MarketResearchEnergyGridReserveMarginSqueezeDigestConfig,
    MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow,
    MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount,
    MarketResearchEnergyGridReserveMarginSqueezeDigestReport,
    MarketResearchEnergyGridReserveMarginSqueezeDigestRow,
    build_market_research_energy_grid_reserve_margin_squeeze_digest,
    market_research_energy_grid_reserve_margin_squeeze_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_energy_grid_reserve_margin_squeeze_digest.py"
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEnergyGridReserveMarginSqueezeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION
        ),
        "fresh_snapshot_max_age_seconds": d("7200.000000"),
        "min_public_source_count": d("2.000000"),
        "watch_reserve_margin_ratio": d("0.100000"),
        "block_reserve_margin_ratio": d("0.060000"),
        "watch_load_utilization_ratio": d("0.900000"),
        "block_load_utilization_ratio": d("0.970000"),
        "watch_forced_outage_ratio": d("0.080000"),
        "block_forced_outage_ratio": d("0.150000"),
        "probability_shift_threshold": d("0.050000"),
    }
    values.update(overrides)
    return MarketResearchEnergyGridReserveMarginSqueezeDigestConfig(**values)


def input_row(
    grid_region: str = "ercot",
    grid_area: str = "ercot_north",
    *,
    condition_id: str = "condition_ercot_reserve_margin_squeeze",
    market_slug: str = "ercot-reserve-margin-under-six-percent",
    source_id: str = "iso_public_capacity_report",
    snapshot_at: datetime | None = None,
    available_capacity_mw: Decimal = d("78000.000000"),
    forecast_peak_load_mw: Decimal = d("68000.000000"),
    reserve_margin_ratio: Decimal = d("0.147059"),
    forced_outage_ratio: Decimal = d("0.030000"),
    public_source_count: Decimal = d("3.000000"),
    market_probability_before: Decimal = d("0.320000"),
    market_probability_after: Decimal = d("0.340000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow:
    return MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow(
        grid_region=grid_region,
        grid_area=grid_area,
        condition_id=condition_id,
        market_slug=market_slug,
        source_id=source_id,
        snapshot_at=snapshot_at or GENERATED_AT - timedelta(minutes=30),
        available_capacity_mw=available_capacity_mw,
        forecast_peak_load_mw=forecast_peak_load_mw,
        reserve_margin_ratio=reserve_margin_ratio,
        forced_outage_ratio=forced_outage_ratio,
        public_source_count=public_source_count,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...] = (),
    *,
    cfg: MarketResearchEnergyGridReserveMarginSqueezeDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEnergyGridReserveMarginSqueezeDigestReport:
    return build_market_research_energy_grid_reserve_margin_squeeze_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_reserve_margin_squeeze_digest_reduces_rows_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "caiso",
                "caiso_south",
                condition_id="condition_caiso_reserve_margin_watch",
                market_slug="caiso-reserve-margin-under-ten-percent",
                source_id="iso_capacity_public_summary",
                snapshot_at=GENERATED_AT - timedelta(hours=3),
                available_capacity_mw=d("52000.000000"),
                forecast_peak_load_mw=d("48000.000000"),
                reserve_margin_ratio=d("0.083333"),
                forced_outage_ratio=d("0.090000"),
                public_source_count=d("1.000000"),
                market_probability_before=d("0.410000"),
                market_probability_after=d("0.470000"),
            ),
            input_row(
                "pjm",
                "pjm_west",
                condition_id="condition_pjm_reserve_margin_block",
                market_slug="pjm-reserve-margin-under-six-percent",
                source_id="rto_public_reserve_report",
                snapshot_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4)))
                - timedelta(hours=1),
                available_capacity_mw=d("101000.000000"),
                forecast_peak_load_mw=d("99000.000000"),
                reserve_margin_ratio=d("0.020202"),
                forced_outage_ratio=d("0.180000"),
                public_source_count=d("2.000000"),
                market_probability_before=d("0.220000"),
                market_probability_after=d("0.330000"),
            ),
            input_row(),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=9))),
    )

    assert is_dataclass(summary)
    assert type(summary) is MarketResearchEnergyGridReserveMarginSqueezeDigestReport
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_ENERGY_GRID_RESERVE_MARGIN_SQUEEZE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_grid_reserve_margin_squeeze_digest"
    )
    assert summary.grid_count == d("3.000000")
    assert summary.clear_grid_count == d("1.000000")
    assert summary.watch_grid_count == d("1.000000")
    assert summary.blocked_grid_count == d("1.000000")
    assert summary.low_reserve_margin_count == d("2.000000")
    assert summary.high_load_utilization_count == d("2.000000")
    assert summary.forced_outage_pressure_count == d("2.000000")
    assert summary.stale_snapshot_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.probability_shift_count == d("2.000000")
    assert summary.min_reserve_margin_ratio == d("0.020202")
    assert summary.max_load_utilization_ratio == d("0.980198")
    assert summary.max_forced_outage_ratio == d("0.180000")
    assert summary.average_reserve_margin_ratio == d("0.083531")
    assert summary.average_capacity_surplus_mw == d("5333.333333")
    assert summary.max_snapshot_age_seconds == d("10800.000000")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(
        (row.squeeze_status, row.grid_region, row.grid_area)
        for row in summary.rows
    ) == (
        ("blocked", "pjm", "pjm_west"),
        ("watch", "caiso", "caiso_south"),
        ("clear", "ercot", "ercot_north"),
    )

    blocked = summary.rows[0]
    assert type(blocked) is MarketResearchEnergyGridReserveMarginSqueezeDigestRow
    assert blocked.snapshot_age_seconds == d("3600.000000")
    assert blocked.capacity_surplus_mw == d("2000.000000")
    assert blocked.load_utilization_ratio == d("0.980198")
    assert blocked.probability_change == d("0.110000")
    assert blocked.reason_codes == (
        "market_research_energy_grid_reserve_margin_squeeze_digest_reserve_margin_block",
        "market_research_energy_grid_reserve_margin_squeeze_digest_load_utilization_block",
        "market_research_energy_grid_reserve_margin_squeeze_digest_forced_outage_block",
        "market_research_energy_grid_reserve_margin_squeeze_digest_probability_shift",
    )

    watched = summary.rows[1]
    assert watched.squeeze_status == "watch"
    assert watched.snapshot_age_seconds == d("10800.000000")
    assert watched.capacity_surplus_mw == d("4000.000000")
    assert watched.load_utilization_ratio == d("0.923077")
    assert watched.reason_codes == (
        "market_research_energy_grid_reserve_margin_squeeze_digest_reserve_margin_watch",
        "market_research_energy_grid_reserve_margin_squeeze_digest_load_utilization_watch",
        "market_research_energy_grid_reserve_margin_squeeze_digest_forced_outage_watch",
        "market_research_energy_grid_reserve_margin_squeeze_digest_probability_shift",
        "market_research_energy_grid_reserve_margin_squeeze_digest_stale_snapshot",
        "market_research_energy_grid_reserve_margin_squeeze_digest_thin_sources",
    )

    clear = summary.rows[2]
    assert clear.squeeze_status == "clear"
    assert clear.snapshot_age_seconds == d("1800.000000")
    assert clear.capacity_surplus_mw == d("10000.000000")
    assert clear.load_utilization_ratio == d("0.871795")
    assert clear.probability_change == d("0.020000")
    assert clear.reason_codes == (
        "market_research_energy_grid_reserve_margin_squeeze_digest_clear",
    )

    assert summary.reason_code_counts == (
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "reserve_margin_block"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "load_utilization_block"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "forced_outage_block"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "probability_shift"
            ),
            count=d("2.000000"),
            grid_ratio=d("0.666667"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "reserve_margin_watch"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "load_utilization_watch"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "forced_outage_watch"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "stale_snapshot"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code=(
                "market_research_energy_grid_reserve_margin_squeeze_digest_"
                "thin_sources"
            ),
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code="market_research_energy_grid_reserve_margin_squeeze_digest_clear",
            count=d("1.000000"),
            grid_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_empty_reserve_margin_squeeze_digest_is_blocked_report_only_payload() -> None:
    summary = report()
    payload = market_research_energy_grid_reserve_margin_squeeze_digest_payload(summary)

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_energy_grid_reserve_margin_squeeze_digest"
    )
    assert summary.grid_count == ZERO
    assert summary.clear_grid_count == ZERO
    assert summary.watch_grid_count == ZERO
    assert summary.blocked_grid_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_energy_grid_reserve_margin_squeeze_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount(
            reason_code="market_research_energy_grid_reserve_margin_squeeze_digest_no_inputs",
            count=d("1.000000"),
            grid_ratio=ZERO,
        ),
    )
    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["grid_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()


def test_reserve_margin_squeeze_validates_contracts_flags_and_duplicates() -> None:
    assert is_dataclass(MarketResearchEnergyGridReserveMarginSqueezeDigestConfig)
    assert is_dataclass(MarketResearchEnergyGridReserveMarginSqueezeDigestInputRow)
    assert is_dataclass(MarketResearchEnergyGridReserveMarginSqueezeDigestRow)
    assert is_dataclass(MarketResearchEnergyGridReserveMarginSqueezeDigestReasonCodeCount)
    assert is_dataclass(MarketResearchEnergyGridReserveMarginSqueezeDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].reserve_margin_ratio = d("0.010000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("reserve-margin-v0"))
    with pytest.raises(ValueError, match="fresh_snapshot_max_age_seconds"):
        config(fresh_snapshot_max_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="block_reserve_margin_ratio"):
        config(
            watch_reserve_margin_ratio=d("0.100000"),
            block_reserve_margin_ratio=d("0.120000"),
        )
    with pytest.raises(ValueError, match="block_load_utilization_ratio"):
        config(
            watch_load_utilization_ratio=d("0.980000"),
            block_load_utilization_ratio=d("0.900000"),
        )
    with pytest.raises(ValueError, match="block_forced_outage_ratio"):
        config(
            watch_forced_outage_ratio=d("0.200000"),
            block_forced_outage_ratio=d("0.150000"),
        )
    with pytest.raises(ValueError, match="grid_region"):
        input_row(grid_region="ERCOT")
    with pytest.raises(ValueError, match="grid_area"):
        input_row(grid_area="ercot north")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="condition_submit_order")
    with pytest.raises(ValueError, match="market_slug"):
        input_row(market_slug="ERCOT Reserve")
    with pytest.raises(ValueError, match="source_id"):
        input_row(source_id="api_key")
    with pytest.raises(ValueError, match="snapshot_at"):
        input_row(snapshot_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="snapshot_at"):
        input_row(snapshot_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="available_capacity_mw"):
        input_row(available_capacity_mw=d("0.000000"))
    with pytest.raises(ValueError, match="forecast_peak_load_mw"):
        input_row(forecast_peak_load_mw=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="reserve_margin_ratio"):
        input_row(reserve_margin_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="forced_outage_ratio"):
        input_row(forced_outage_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_energy_grid_reserve_margin_squeeze_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_energy_grid_reserve_margin_squeeze_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        report((input_row(snapshot_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                input_row("ercot", "ercot_north", source_id="one"),
                input_row("ercot", "ercot_north", source_id="two"),
            ),
        )
    with pytest.raises(ValueError, match="squeeze_status"):
        replace(summary.rows[0], squeeze_status="blocked")
    with pytest.raises(ValueError, match="load_utilization_ratio"):
        replace(summary.rows[0], load_utilization_ratio=d("9.000000"))


def test_payload_uses_six_decimal_strings_and_no_raw_numeric_or_datetime_values() -> None:
    summary = report((input_row(),))
    payload = market_research_energy_grid_reserve_margin_squeeze_digest_payload(summary)

    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["grid_count"] == "1.000000"
    assert payload["average_reserve_margin_ratio"] == "0.147059"
    assert payload["rows"][0]["available_capacity_mw"] == "78000.000000"
    assert payload["rows"][0]["load_utilization_ratio"] == "0.871795"
    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    _assert_payload_has_no_raw_decimal_datetime_or_float(payload)


def test_dataclasses_are_frozen_and_public_numeric_hints_are_decimal_only() -> None:
    summary = report((input_row(),))

    for value in _walk_dataclasses(summary):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float(hint)
        for field in fields(value):
            if _is_public_numeric_field(field.name):
                field_value = getattr(value, field.name)
                assert field_value is None or type(field_value) is Decimal


def test_module_has_no_io_network_db_or_live_mutation_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "live_trading",
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
        "psycopg",
        "supabase",
        "sqlite3",
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


def _assert_payload_has_no_raw_decimal_datetime_or_float(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_payload_has_no_raw_decimal_datetime_or_float(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_payload_has_no_raw_decimal_datetime_or_float(item)
        return
    assert not isinstance(value, (Decimal, datetime, float))


def _is_public_numeric_field(name: str) -> bool:
    if name in ("rows", "reason_code_counts"):
        return False
    fragments = (
        "count",
        "ratio",
        "seconds",
        "capacity",
        "load",
        "mw",
        "probability",
        "threshold",
    )
    return any(fragment in name for fragment in fragments)


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))
