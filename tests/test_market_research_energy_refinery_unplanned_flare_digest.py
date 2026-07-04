from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_energy_refinery_unplanned_flare_digest"
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_energy_refinery_unplanned_flare_digest.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> dict[str, Any]:
    module = importlib.import_module(MODULE_NAME)
    names = (
        "DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION",
        "EnergyRefineryUnplannedFlareDigestConfig",
        "EnergyRefineryUnplannedFlareInput",
        "EnergyRefineryUnplannedFlareReasonCodeCount",
        "EnergyRefineryUnplannedFlareRefineryRow",
        "EnergyRefineryUnplannedFlareDigest",
        "build_market_research_energy_refinery_unplanned_flare_digest",
        "market_research_energy_refinery_unplanned_flare_digest_payload",
    )
    missing = tuple(name for name in names if not hasattr(module, name))
    assert missing == ()
    return {name: getattr(module, name) for name in names}


def config(**overrides: object) -> Any:
    items = api()
    values = {
        "config_version": items[
            "DEFAULT_ENERGY_REFINERY_UNPLANNED_FLARE_DIGEST_CONFIG_VERSION"
        ],
        "watch_flare_event_ratio": d("0.200000"),
        "blocked_flare_event_ratio": d("0.400000"),
        "watch_outage_capacity_ratio": d("0.050000"),
        "blocked_outage_capacity_ratio": d("0.100000"),
        "min_sample_count": d("2.000000"),
    }
    values.update(overrides)
    return items["EnergyRefineryUnplannedFlareDigestConfig"](**values)


def input_row(
    source_id: str,
    *,
    refinery_id: str = "baytown",
    market_id: str = "baytown-refinery-flare-risk",
    region_id: str = "gulf-coast",
    unplanned_flare_event_count: str = "1.000000",
    sample_count: str = "5.000000",
    offline_capacity_bpd: str = "7000.000000",
    nameplate_capacity_bpd: str = "100000.000000",
    expected_offline_capacity_bpd: str = "1000.000000",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=30),
    reason_codes: tuple[str, ...] = ("refinery_unplanned_flare_input_observed",),
) -> Any:
    return api()["EnergyRefineryUnplannedFlareInput"](
        source_id=source_id,
        refinery_id=refinery_id,
        market_id=market_id,
        region_id=region_id,
        unplanned_flare_event_count=d(unplanned_flare_event_count),
        sample_count=d(sample_count),
        offline_capacity_bpd=d(offline_capacity_bpd),
        nameplate_capacity_bpd=d(nameplate_capacity_bpd),
        expected_offline_capacity_bpd=d(expected_offline_capacity_bpd),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def digest(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return api()["build_market_research_energy_refinery_unplanned_flare_digest"](
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def high_risk_digest() -> Any:
    return digest(
        input_row(
            "source-zeta",
            unplanned_flare_event_count="5.000000",
            sample_count="10.000000",
            offline_capacity_bpd="90000.000000",
            nameplate_capacity_bpd="500000.000000",
            expected_offline_capacity_bpd="20000.000000",
            observed_at=datetime(
                2026,
                7,
                4,
                6,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            reason_codes=(
                "refinery_unplanned_flare_input_observed",
                "refinery_unplanned_flare_revision",
            ),
        ),
        input_row(
            "source-alpha",
            refinery_id="delaware-city",
            market_id="delaware-city-refinery-flare-risk",
            region_id="mid-atlantic",
            unplanned_flare_event_count="1.000000",
            sample_count="5.000000",
            offline_capacity_bpd="7000.000000",
            nameplate_capacity_bpd="100000.000000",
            expected_offline_capacity_bpd="1000.000000",
        ),
        input_row(
            "source-clear",
            refinery_id="wood-river",
            market_id="wood-river-refinery-flare-risk",
            region_id="midwest",
            unplanned_flare_event_count="0.000000",
            sample_count="10.000000",
            offline_capacity_bpd="1000.000000",
            nameplate_capacity_bpd="300000.000000",
            expected_offline_capacity_bpd="1000.000000",
        ),
        input_row(
            "source-beta",
            unplanned_flare_event_count="1.000000",
            sample_count="5.000000",
            offline_capacity_bpd="30000.000000",
            nameplate_capacity_bpd="500000.000000",
            expected_offline_capacity_bpd="20000.000000",
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )


def test_empty_input_returns_report_only_zero_digest() -> None:
    report = digest()

    assert report.digest_status == "empty"
    assert report.recommended_next_step == (
        "monitor_report_only_market_research_energy_refinery_unplanned_flare_digest"
    )
    assert report.reason_codes == ("refinery_unplanned_flare_digest_empty",)
    assert report.refinery_count == d("0.000000")
    assert report.source_count == d("0.000000")
    assert report.total_unplanned_flare_event_count == d("0.000000")
    assert report.total_sample_count == d("0.000000")
    assert report.total_offline_capacity_bpd == d("0.000000")
    assert report.total_nameplate_capacity_bpd == d("0.000000")
    assert report.weighted_flare_event_ratio == d("0.000000")
    assert report.weighted_outage_capacity_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_digest_reduces_refineries_deterministically() -> None:
    items = api()
    report = high_risk_digest()

    assert type(report) is items["EnergyRefineryUnplannedFlareDigest"]
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-energy-refinery-unplanned-flare-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_energy_refinery_unplanned_flare_digest"
    )
    assert report.refinery_count == d("3.000000")
    assert report.source_count == d("4.000000")
    assert report.total_unplanned_flare_event_count == d("7.000000")
    assert report.total_sample_count == d("30.000000")
    assert report.total_offline_capacity_bpd == d("128000.000000")
    assert report.total_nameplate_capacity_bpd == d("1400000.000000")
    assert report.total_expected_offline_capacity_bpd == d("42000.000000")
    assert report.max_flare_event_ratio == d("0.400000")
    assert report.max_outage_capacity_ratio == d("0.120000")
    assert report.weighted_flare_event_ratio == d("0.233333")
    assert report.weighted_outage_capacity_ratio == d("0.091429")
    assert report.watch_refinery_count == d("1.000000")
    assert report.blocked_refinery_count == d("1.000000")
    assert report.reason_codes == (
        "refinery_unplanned_flare_watch_present",
        "refinery_unplanned_flare_blocked_present",
        "refinery_unplanned_flare_outage_watch_present",
        "refinery_unplanned_flare_outage_blocked_present",
        "refinery_unplanned_flare_revision_present",
    )
    assert tuple(row.refinery_id for row in report.rows) == (
        "baytown",
        "delaware-city",
        "wood-river",
    )

    blocked, watch, clear = report.rows
    assert type(blocked) is items["EnergyRefineryUnplannedFlareRefineryRow"]
    assert blocked.refinery_id == "baytown"
    assert blocked.region_ids == ("gulf-coast",)
    assert blocked.market_ids == ("baytown-refinery-flare-risk",)
    assert blocked.source_ids == ("source-beta", "source-zeta")
    assert blocked.unplanned_flare_event_count == d("6.000000")
    assert blocked.sample_count == d("15.000000")
    assert blocked.flare_event_ratio == d("0.400000")
    assert blocked.offline_capacity_bpd == d("120000.000000")
    assert blocked.nameplate_capacity_bpd == d("1000000.000000")
    assert blocked.expected_offline_capacity_bpd == d("40000.000000")
    assert blocked.outage_capacity_ratio == d("0.120000")
    assert blocked.expected_outage_capacity_ratio == d("0.040000")
    assert blocked.outage_surprise_ratio == d("0.080000")
    assert blocked.source_count == d("2.000000")
    assert blocked.latest_observed_at == datetime(2026, 7, 4, 11, 30, tzinfo=UTC)
    assert blocked.risk_status == "blocked"
    assert blocked.reason_codes == (
        "refinery_unplanned_flare_refinery_blocked",
        "refinery_unplanned_flare_outage_blocked",
        "refinery_unplanned_flare_revision_present",
    )

    assert watch.refinery_id == "delaware-city"
    assert watch.flare_event_ratio == d("0.200000")
    assert watch.outage_capacity_ratio == d("0.070000")
    assert watch.risk_status == "watch"
    assert watch.reason_codes == (
        "refinery_unplanned_flare_refinery_watch",
        "refinery_unplanned_flare_outage_watch",
    )
    assert clear.refinery_id == "wood-river"
    assert clear.risk_status == "clear"
    assert clear.reason_codes == ("refinery_unplanned_flare_refinery_clear",)


def test_reason_code_counts_payload_and_decimal_only_public_numerics() -> None:
    items = api()
    report = high_risk_digest()
    ReasonCount = items["EnergyRefineryUnplannedFlareReasonCodeCount"]

    assert report.reason_code_counts == (
        ReasonCount(
            reason_code="refinery_unplanned_flare_watch_present",
            refinery_count=d("1.000000"),
            refinery_ratio=d("0.333333"),
        ),
        ReasonCount(
            reason_code="refinery_unplanned_flare_blocked_present",
            refinery_count=d("1.000000"),
            refinery_ratio=d("0.333333"),
        ),
        ReasonCount(
            reason_code="refinery_unplanned_flare_outage_watch_present",
            refinery_count=d("1.000000"),
            refinery_ratio=d("0.333333"),
        ),
        ReasonCount(
            reason_code="refinery_unplanned_flare_outage_blocked_present",
            refinery_count=d("1.000000"),
            refinery_ratio=d("0.333333"),
        ),
        ReasonCount(
            reason_code="refinery_unplanned_flare_revision_present",
            refinery_count=d("1.000000"),
            refinery_ratio=d("0.333333"),
        ),
    )

    payload = items[
        "market_research_energy_refinery_unplanned_flare_digest_payload"
    ](report)
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["refinery_count"] == "3.000000"
    assert payload["weighted_outage_capacity_ratio"] == "0.091429"
    assert payload["rows"][0]["offline_capacity_bpd"] == "120000.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    for value in (
        *_walk_dataclasses(report),
        config(),
        input_row("type-check"),
    ):
        assert value.__dataclass_params__.frozen is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float(hint)
        for field in fields(value):
            if _is_public_numeric(field.name):
                field_value = getattr(value, field.name)
                assert field_value is None or type(field_value) is Decimal


def test_non_default_thresholds_can_keep_default_watch_input_clear() -> None:
    cfg = config(
        watch_flare_event_ratio=d("0.250000"),
        blocked_flare_event_ratio=d("0.500000"),
        watch_outage_capacity_ratio=d("0.080000"),
        blocked_outage_capacity_ratio=d("0.200000"),
    )

    report = digest(input_row("custom-thresholds"), cfg=cfg)

    assert report.digest_status == "clear"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_energy_refinery_unplanned_flare_digest"
    )
    assert report.reason_codes == ("refinery_unplanned_flare_clear",)
    assert report.watch_refinery_count == d("0.000000")
    assert report.blocked_refinery_count == d("0.000000")
    assert report.rows[0].risk_status == "clear"
    assert report.rows[0].reason_codes == ("refinery_unplanned_flare_refinery_clear",)


def test_validates_inputs_config_datetimes_and_duplicates() -> None:
    items = api()
    Input = items["EnergyRefineryUnplannedFlareInput"]
    build = items["build_market_research_energy_refinery_unplanned_flare_digest"]

    with pytest.raises(ValueError, match="unplanned_flare_event_count must be a Decimal"):
        Input(
            source_id="bad-decimal",
            refinery_id="baytown",
            market_id="baytown-refinery-flare-risk",
            region_id="gulf-coast",
            unplanned_flare_event_count=1,  # type: ignore[arg-type]
            sample_count=d("5.000000"),
            offline_capacity_bpd=d("7000.000000"),
            nameplate_capacity_bpd=d("100000.000000"),
            expected_offline_capacity_bpd=d("1000.000000"),
            observed_at=GENERATED_AT,
            reason_codes=("refinery_unplanned_flare_input_observed",),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        input_row("bad-time", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="config must be an .*Config"):
        build((), config=object(), generated_at=GENERATED_AT)

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build((), config=config(), generated_at="2026-07-04T12:00:00Z")

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest(input_row("dupe"), input_row("dupe", refinery_id="other"))

    with pytest.raises(ValueError, match="must not exceed sample_count"):
        input_row(
            "bad-flare-count",
            unplanned_flare_event_count="2.000000",
            sample_count="1.000000",
        )

    with pytest.raises(ValueError, match="offline_capacity_bpd must not exceed"):
        input_row(
            "bad-offline-capacity",
            offline_capacity_bpd="120000.000000",
            nameplate_capacity_bpd="100000.000000",
        )

    with pytest.raises(ValueError, match="expected_offline_capacity_bpd must not exceed"):
        input_row(
            "bad-expected-capacity",
            expected_offline_capacity_bpd="120000.000000",
            nameplate_capacity_bpd="100000.000000",
        )


def test_hard_flags_are_true_and_enforced_on_all_public_dataclasses() -> None:
    report = high_risk_digest()
    values = (
        config(),
        input_row("flag-input"),
        report,
        *report.rows,
        *report.reason_code_counts,
    )

    for value in values:
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=flag_name):
                replace(value, **{flag_name: False})

    row = input_row("frozen")
    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]


def test_static_production_surface_stays_pure_report_only() -> None:
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
        "exchange",
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


def _is_public_numeric(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_bpd")
    )


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))


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
