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


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_research_energy_lng_storage_constraint_digest.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_energy_lng_storage_constraint_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> object:
    digest_module = module()
    values = {
        "config_version": digest_module.DEFAULT_LNG_STORAGE_CONSTRAINT_DIGEST_CONFIG_VERSION,
        "watch_risk_score": d("0.500000"),
        "blocked_risk_score": d("0.800000"),
        "watch_storage_utilization": d("0.700000"),
        "blocked_storage_utilization": d("0.900000"),
        "watch_sendout_constraint_ratio": d("0.500000"),
        "blocked_sendout_constraint_ratio": d("0.800000"),
        "watch_cargo_queue_length": d("3.000000"),
        "blocked_cargo_queue_length": d("8.000000"),
        "watch_feedgas_drop_bcf_d": d("0.500000"),
        "blocked_feedgas_drop_bcf_d": d("1.500000"),
        "watch_weather_demand_pressure": d("0.400000"),
        "blocked_weather_demand_pressure": d("0.700000"),
        "max_source_age_seconds": d("21600.000000"),
        "min_source_quorum": d("2.000000"),
    }
    values.update(overrides)
    return digest_module.LNGStorageConstraintDigestConfig(**values)


def observation(
    source_id: str,
    *,
    terminal_id: str = "sabine-pass",
    region_id: str = "usgc",
    market_slug: str = "us-lng-feedgas-above-14bcfd",
    storage_utilization: str | Decimal = "0.920000",
    sendout_constraint_ratio: str | Decimal = "0.840000",
    cargo_queue_length: str | Decimal = "8.000000",
    feedgas_delta_bcf_d: str | Decimal = "-1.600000",
    weather_demand_pressure: str | Decimal = "0.720000",
    source_observed_at: datetime = GENERATED_AT - timedelta(minutes=45),
    upstream_reason_codes: tuple[str, ...] = (
        "lng_storage_terminal_report",
        "lng_storage_sendout_notice",
    ),
) -> object:
    digest_module = module()
    return digest_module.LNGStorageConstraintObservation(
        source_id=source_id,
        terminal_id=terminal_id,
        region_id=region_id,
        market_slug=market_slug,
        storage_utilization=(
            storage_utilization
            if isinstance(storage_utilization, Decimal)
            else d(storage_utilization)
        ),
        sendout_constraint_ratio=(
            sendout_constraint_ratio
            if isinstance(sendout_constraint_ratio, Decimal)
            else d(sendout_constraint_ratio)
        ),
        cargo_queue_length=(
            cargo_queue_length
            if isinstance(cargo_queue_length, Decimal)
            else d(cargo_queue_length)
        ),
        feedgas_delta_bcf_d=(
            feedgas_delta_bcf_d
            if isinstance(feedgas_delta_bcf_d, Decimal)
            else d(feedgas_delta_bcf_d)
        ),
        weather_demand_pressure=(
            weather_demand_pressure
            if isinstance(weather_demand_pressure, Decimal)
            else d(weather_demand_pressure)
        ),
        source_observed_at=source_observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(
    *rows: object,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> object:
    digest_module = module()
    return digest_module.build_market_research_energy_lng_storage_constraint_digest(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    digest_module = module()

    digest_report = report(
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(digest_report, digest_module.LNGStorageConstraintDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen is True
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-energy-lng-storage-constraint-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_energy_lng_storage_constraint_digest"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.terminal_count == d("0.000000")
    assert digest_report.source_count == d("0.000000")
    assert digest_report.fresh_source_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.source_quorum_gap_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.risk_score == d("0.000000")
    assert digest_report.max_storage_utilization == d("0.000000")
    assert digest_report.max_sendout_constraint_ratio == d("0.000000")
    assert digest_report.max_cargo_queue_length == d("0.000000")
    assert digest_report.min_feedgas_delta_bcf_d == d("0.000000")
    assert digest_report.max_weather_demand_pressure == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("lng_storage_constraint_digest_empty",)
    assert digest_report.reason_code_counts == (
        digest_module.LNGStorageConstraintReasonCodeCount(
            reason_code="lng_storage_constraint_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_lng_storage_constraint_pressure_reduces_rows_and_risk_deterministically() -> None:
    sabine_first = observation(
        "source-sabine-a",
        terminal_id="sabine-pass",
        region_id="usgc",
        market_slug="us-lng-feedgas-above-14bcfd",
        upstream_reason_codes=(
            "lng_storage_terminal_report",
            "lng_storage_sendout_notice",
            "lng_storage_source_correction",
        ),
    )
    sabine_second = observation(
        "source-sabine-b",
        terminal_id="sabine-pass",
        region_id="usgc",
        market_slug="us-lng-feedgas-above-14bcfd",
        storage_utilization="0.910000",
        sendout_constraint_ratio="0.790000",
        cargo_queue_length="6.000000",
        feedgas_delta_bcf_d="-1.200000",
        weather_demand_pressure="0.680000",
        source_observed_at=datetime(
            2026,
            7,
            4,
            10,
            15,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        upstream_reason_codes=("lng_storage_cargo_queue_report",),
    )
    corpus_fresh = observation(
        "source-corpus-a",
        terminal_id="corpus-christi",
        region_id="usgc",
        market_slug="corpus-lng-sendout-normal",
        storage_utilization="0.760000",
        sendout_constraint_ratio="0.550000",
        cargo_queue_length="3.000000",
        feedgas_delta_bcf_d="-0.550000",
        weather_demand_pressure="0.450000",
        upstream_reason_codes=("lng_storage_weather_demand_model",),
    )
    corpus_stale = observation(
        "source-corpus-b",
        terminal_id="corpus-christi",
        region_id="usgc",
        market_slug="corpus-lng-sendout-normal",
        storage_utilization="0.730000",
        sendout_constraint_ratio="0.530000",
        cargo_queue_length="2.000000",
        feedgas_delta_bcf_d="-0.400000",
        weather_demand_pressure="0.430000",
        source_observed_at=GENERATED_AT - timedelta(hours=8),
        upstream_reason_codes=("lng_storage_terminal_report",),
    )
    cove_first = observation(
        "source-cove-a",
        terminal_id="cove-point",
        region_id="midatlantic",
        market_slug="cove-point-storage-normal",
        storage_utilization="0.420000",
        sendout_constraint_ratio="0.120000",
        cargo_queue_length="0.000000",
        feedgas_delta_bcf_d="0.100000",
        weather_demand_pressure="0.160000",
        upstream_reason_codes=("lng_storage_terminal_report",),
    )
    cove_second = observation(
        "source-cove-b",
        terminal_id="cove-point",
        region_id="midatlantic",
        market_slug="cove-point-storage-normal",
        storage_utilization="0.390000",
        sendout_constraint_ratio="0.100000",
        cargo_queue_length="0.000000",
        feedgas_delta_bcf_d="0.050000",
        weather_demand_pressure="0.150000",
        upstream_reason_codes=("lng_storage_feedgas_flow_report",),
    )

    forward = report(
        cove_first,
        corpus_fresh,
        sabine_first,
        cove_second,
        corpus_stale,
        sabine_second,
    )
    reverse = report(
        sabine_second,
        corpus_stale,
        cove_second,
        sabine_first,
        corpus_fresh,
        cove_first,
    )

    assert forward == reverse
    assert forward.digest_status == "blocked"
    assert forward.input_count == d("6.000000")
    assert forward.row_count == d("3.000000")
    assert forward.terminal_count == d("3.000000")
    assert forward.source_count == d("6.000000")
    assert forward.fresh_source_count == d("5.000000")
    assert forward.stale_source_count == d("1.000000")
    assert forward.source_quorum_gap_count == d("1.000000")
    assert forward.blocked_count == d("1.000000")
    assert forward.watch_count == d("1.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.risk_score == d("1.000000")
    assert forward.max_storage_utilization == d("0.920000")
    assert forward.max_sendout_constraint_ratio == d("0.840000")
    assert forward.max_cargo_queue_length == d("8.000000")
    assert forward.min_feedgas_delta_bcf_d == d("-1.600000")
    assert forward.max_weather_demand_pressure == d("0.720000")
    assert tuple(row.terminal_id for row in forward.rows) == (
        "sabine-pass",
        "corpus-christi",
        "cove-point",
    )
    assert forward.reason_codes == (
        "lng_storage_constraint_blocked_present",
        "lng_storage_constraint_watch_present",
        "lng_storage_constraint_source_quorum_gap_present",
        "lng_storage_constraint_high_storage_utilization_present",
        "lng_storage_constraint_elevated_storage_utilization_present",
        "lng_storage_constraint_sendout_constrained_present",
        "lng_storage_constraint_sendout_tight_present",
        "lng_storage_constraint_cargo_queue_blocked_present",
        "lng_storage_constraint_cargo_queue_watch_present",
        "lng_storage_constraint_feedgas_drop_blocked_present",
        "lng_storage_constraint_feedgas_drop_watch_present",
        "lng_storage_constraint_weather_demand_pressure_present",
        "lng_storage_constraint_weather_demand_watch_present",
        "lng_storage_constraint_upstream_source_correction_present",
    )

    blocked, watched, passed = forward.rows
    assert blocked.constraint_status == "blocked"
    assert blocked.region_id == "usgc"
    assert blocked.market_slug == "us-lng-feedgas-above-14bcfd"
    assert blocked.storage_utilization == d("0.920000")
    assert blocked.sendout_constraint_ratio == d("0.840000")
    assert blocked.cargo_queue_length == d("8.000000")
    assert blocked.feedgas_delta_bcf_d == d("-1.600000")
    assert blocked.weather_demand_pressure == d("0.720000")
    assert blocked.metric_pressure_score == d("1.000000")
    assert blocked.evidence_pressure_score == d("0.000000")
    assert blocked.constraint_risk_score == d("1.000000")
    assert blocked.source_count == d("2.000000")
    assert blocked.fresh_source_count == d("2.000000")
    assert blocked.source_quorum_met is True
    assert blocked.latest_source_observed_at == datetime(2026, 7, 4, 14, 15, tzinfo=UTC)
    assert blocked.max_source_age_seconds == d("2700.000000")
    assert blocked.source_ids == ("source-sabine-a", "source-sabine-b")
    assert blocked.upstream_reason_codes == (
        "lng_storage_cargo_queue_report",
        "lng_storage_sendout_notice",
        "lng_storage_source_correction",
        "lng_storage_terminal_report",
    )
    assert blocked.reason_codes == (
        "lng_storage_constraint_high_storage_utilization",
        "lng_storage_constraint_sendout_constrained",
        "lng_storage_constraint_cargo_queue_blocked",
        "lng_storage_constraint_feedgas_drop_blocked",
        "lng_storage_constraint_weather_demand_pressure",
        "lng_storage_constraint_upstream_source_correction",
    )

    assert watched.constraint_status == "watch"
    assert watched.terminal_id == "corpus-christi"
    assert watched.metric_pressure_score == d("0.760000")
    assert watched.evidence_pressure_score == d("0.500000")
    assert watched.constraint_risk_score == d("0.760000")
    assert watched.fresh_source_count == d("1.000000")
    assert watched.stale_source_count == d("1.000000")
    assert watched.source_quorum_met is False
    assert watched.max_source_age_seconds == d("28800.000000")
    assert watched.reason_codes == (
        "lng_storage_constraint_source_quorum_gap",
        "lng_storage_constraint_elevated_storage_utilization",
        "lng_storage_constraint_sendout_tight",
        "lng_storage_constraint_cargo_queue_watch",
        "lng_storage_constraint_feedgas_drop_watch",
        "lng_storage_constraint_weather_demand_watch",
    )

    assert passed.constraint_status == "pass"
    assert passed.terminal_id == "cove-point"
    assert passed.constraint_risk_score == d("0.420000")
    assert passed.reason_codes == ("lng_storage_constraint_inline",)


def test_custom_thresholds_reason_count_sorting_and_payload_strings() -> None:
    digest_module = module()
    custom_cfg = cfg(
        watch_risk_score=d("0.650000"),
        blocked_risk_score=d("0.950000"),
        watch_storage_utilization=d("0.850000"),
        blocked_storage_utilization=d("0.970000"),
        watch_sendout_constraint_ratio=d("0.700000"),
        blocked_sendout_constraint_ratio=d("0.950000"),
        watch_cargo_queue_length=d("6.000000"),
        blocked_cargo_queue_length=d("12.000000"),
        watch_feedgas_drop_bcf_d=d("1.000000"),
        blocked_feedgas_drop_bcf_d=d("3.000000"),
        watch_weather_demand_pressure=d("0.600000"),
        blocked_weather_demand_pressure=d("0.900000"),
        min_source_quorum=d("1.000000"),
    )

    digest_report = report(
        observation(
            "source-watch-a",
            terminal_id="alpha-terminal",
            market_slug="alpha-lng-storage-watch",
            storage_utilization="0.900000",
            sendout_constraint_ratio="0.720000",
            cargo_queue_length="7.000000",
            feedgas_delta_bcf_d="-1.200000",
            weather_demand_pressure="0.610000",
        ),
        observation(
            "source-watch-b",
            terminal_id="beta-terminal",
            market_slug="beta-lng-storage-watch",
            storage_utilization="0.890000",
            sendout_constraint_ratio="0.710000",
            cargo_queue_length="6.000000",
            feedgas_delta_bcf_d="-1.100000",
            weather_demand_pressure="0.620000",
        ),
        config=custom_cfg,
    )

    assert digest_report.digest_status == "watch"
    assert digest_report.risk_score == d("0.900000")
    assert tuple(row.constraint_status for row in digest_report.rows) == ("watch", "watch")
    assert tuple(item.reason_code for item in digest_report.reason_code_counts) == (
        "lng_storage_constraint_watch_present",
        "lng_storage_constraint_elevated_storage_utilization_present",
        "lng_storage_constraint_sendout_tight_present",
        "lng_storage_constraint_cargo_queue_watch_present",
        "lng_storage_constraint_feedgas_drop_watch_present",
        "lng_storage_constraint_weather_demand_watch_present",
    )
    assert tuple(item.count for item in digest_report.reason_code_counts) == (
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
    )
    assert all(item.row_ratio == d("1.000000") for item in digest_report.reason_code_counts)

    payload = digest_module.market_research_energy_lng_storage_constraint_digest_payload(
        digest_report,
    )
    json.dumps(payload, allow_nan=False, sort_keys=True)
    assert _numeric_leaf_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-04T15:00:00+00:00"
    assert payload["risk_score"] == "0.900000"
    assert payload["source_count"] == "2.000000"
    assert payload["rows"][0]["storage_utilization"] == "0.900000"
    assert payload["rows"][0]["cargo_queue_length"] == "7.000000"
    assert payload["rows"][0]["latest_source_observed_at"] == "2026-07-04T14:15:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_validation_rejects_bad_inputs_flags_duplicates_and_inconsistent_rows() -> None:
    digest_module = module()

    with pytest.raises(ValueError, match="storage_utilization must be a Decimal"):
        observation(
            "bad-decimal",
            storage_utilization=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="storage_utilization must be no greater than one"):
        observation("bad-ratio", storage_utilization="1.100000")
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        observation(
            "bad-time",
            source_observed_at=datetime(2026, 7, 4, 14, 15),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest_module.build_market_research_energy_lng_storage_constraint_digest(
            (),
            config=cfg(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        report(
            observation(
                "future-source",
                source_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("dupe"), observation("dupe", terminal_id="other-terminal"))
    with pytest.raises(ValueError, match="blocked_risk_score must be at least watch_risk_score"):
        cfg(watch_risk_score=d("0.800000"), blocked_risk_score=d("0.700000"))
    with pytest.raises(ValueError, match="config paper_only must be True"):
        replace(cfg(), paper_only=False)

    digest_report = report(observation("source-valid-a"), observation("source-valid-b"))
    row = digest_report.rows[0]
    with pytest.raises(ValueError, match="constraint_risk_score must match row inputs"):
        replace(row, constraint_risk_score=d("0.123456"))
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="report report_only must be True"):
        replace(digest_report, report_only=False)

    frozen_observation = observation("frozen-source")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_public_numerics_are_decimals_and_production_surface_is_pure_report_only() -> None:
    digest_module = module()
    digest_report = report(observation("source-type-a"), observation("source-type-b"))

    for value in (
        cfg(),
        observation("source-type-c"),
        *tuple(_walk_dataclasses(digest_report)),
    ):
        assert value.__dataclass_params__.frozen is True
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for hint in get_type_hints(type(value)).values():
            assert not _type_uses_float(hint)
        for field in fields(value):
            if _is_public_numeric(field.name):
                field_value = getattr(value, field.name)
                assert type(field_value) is Decimal

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "submit_order",
        "cancel_order",
        "replace_order",
        "mutation",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "supabase",
        "subprocess",
        "getenv",
        "environ",
        "open(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "supabase",
        "sqlite3",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "getenv",
        "open",
        "urlopen",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots


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
        or field_name.endswith("_score")
        or field_name.endswith("_seconds")
        or field_name.endswith("_length")
        or field_name.endswith("_utilization")
        or field_name.endswith("_pressure")
        or field_name.endswith("_bcf_d")
    )


def _type_uses_float(hint: Any) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in get_args(hint))


def _numeric_leaf_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, bool):
        return ()
    if isinstance(value, (int, float, Decimal)):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_numeric_leaf_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_numeric_leaf_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
