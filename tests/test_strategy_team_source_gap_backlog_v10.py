from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.strategy_team_source_gap_backlog_v10"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-source-gap-backlog-v10",
        "stale_packet_pressure_count": d("3"),
        "disagreement_pressure_count": d("3"),
        "urgent_resolution_hours": d("6.000000"),
        "near_resolution_hours": d("24.000000"),
        "high_priority_score_threshold": d("0.350000"),
        "critical_priority_score_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.StrategyTeamSourceGapBacklogV10Config(**values)


def backlog_item(
    *,
    backlog_id: str = "gap-alpha",
    team_id: str = "macro_research",
    market_slug: str = "fed-cuts-in-july",
    stale_packets: str = "0",
    required_sources: str = "3",
    current_sources: str = "3",
    disagreements: str = "0",
    resolution_hours: str = "72.000000",
    available_minutes: str = "60.000000",
    repair_minutes: str = "30.000000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyTeamSourceGapBacklogV10Input(
        backlog_id=backlog_id,
        team_id=team_id,
        market_slug=market_slug,
        stale_packet_count=d(stale_packets),
        required_source_count=d(required_sources),
        current_source_count=d(current_sources),
        disagreement_backlog_count=d(disagreements),
        hours_to_resolution=d(resolution_hours),
        available_specialist_minutes=d(available_minutes),
        estimated_repair_minutes=d(repair_minutes),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_team_source_gap_backlog_v10_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def _walk(value: Any):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_target_module_exists_before_behavior_checks() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_source_gap_backlog_prioritizes_stale_quorum_disagreement_urgency_and_capacity() -> None:
    digest = report(
        backlog_item(
            backlog_id="gap-critical",
            team_id="politics_resolution",
            market_slug="election-certification",
            stale_packets="4",
            required_sources="3",
            current_sources="1",
            disagreements="3",
            resolution_hours="3.000000",
            available_minutes="30.000000",
            repair_minutes="120.000000",
        ),
        backlog_item(
            backlog_id="gap-high",
            team_id="macro_policy",
            market_slug="fed-dot-plot",
            stale_packets="2",
            required_sources="4",
            current_sources="2",
            disagreements="1",
            resolution_hours="12.000000",
            available_minutes="90.000000",
            repair_minutes="120.000000",
        ),
        backlog_item(),
    )

    assert is_dataclass(digest)
    assert type(digest) is api().StrategyTeamSourceGapBacklogV10Report
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "strategy-team-source-gap-backlog-v10"
    assert digest.input_count == d("3")
    assert digest.backlog_item_count == d("3")
    assert digest.critical_priority_count == d("1")
    assert digest.high_priority_count == d("1")
    assert digest.medium_priority_count == d("0")
    assert digest.low_priority_count == d("1")
    assert digest.total_missing_source_count == d("4")
    assert digest.total_stale_packet_count == d("6")
    assert digest.total_disagreement_backlog_count == d("4")
    assert digest.total_estimated_repair_minutes == d("270.000000")
    assert digest.total_available_specialist_minutes == d("180.000000")
    assert digest.max_backlog_priority_score == d("0.875000")
    assert digest.mean_backlog_priority_score == d("0.461111")
    assert digest.priority_status == "critical"
    assert digest.reason_codes == (
        "team_source_gap_backlog_v10_stale_packets",
        "team_source_gap_backlog_v10_missing_source_quorum",
        "team_source_gap_backlog_v10_disagreement_backlog",
        "team_source_gap_backlog_v10_urgent_market",
        "team_source_gap_backlog_v10_specialist_capacity_shortfall",
        "team_source_gap_backlog_v10_high_priority_present",
        "team_source_gap_backlog_v10_critical_priority_present",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    critical, high, low = digest.rows
    assert critical.backlog_id == "gap-critical"
    assert critical.missing_source_count == d("2")
    assert critical.stale_packet_pressure == d("1.000000")
    assert critical.source_quorum_gap_ratio == d("0.666667")
    assert critical.disagreement_pressure == d("1.000000")
    assert critical.market_urgency == d("1.000000")
    assert critical.capacity_coverage_ratio == d("0.250000")
    assert critical.capacity_shortfall_minutes == d("90.000000")
    assert critical.capacity_shortfall_ratio == d("0.750000")
    assert critical.backlog_priority_score == d("0.875000")
    assert critical.priority_band == "critical"
    assert critical.recommended_action == "pause_market_until_source_gap_repaired"
    assert critical.reason_codes == (
        "team_source_gap_backlog_v10_stale_packets",
        "team_source_gap_backlog_v10_missing_source_quorum",
        "team_source_gap_backlog_v10_disagreement_backlog",
        "team_source_gap_backlog_v10_urgent_market",
        "team_source_gap_backlog_v10_specialist_capacity_shortfall",
    )

    assert high.backlog_id == "gap-high"
    assert high.missing_source_count == d("2")
    assert high.stale_packet_pressure == d("0.666667")
    assert high.source_quorum_gap_ratio == d("0.500000")
    assert high.disagreement_pressure == d("0.333333")
    assert high.market_urgency == d("0.666667")
    assert high.capacity_shortfall_ratio == d("0.250000")
    assert high.backlog_priority_score == d("0.508333")
    assert high.priority_band == "high"
    assert high.recommended_action == "assign_specialist_source_repair"

    assert low.backlog_id == "gap-alpha"
    assert low.missing_source_count == d("0")
    assert low.backlog_priority_score == d("0.000000")
    assert low.priority_band == "low"
    assert low.recommended_action == "monitor_source_backlog"
    assert low.reason_codes == ("team_source_gap_backlog_v10_clear",)


def test_empty_report_is_clear_readonly_and_payload_is_json_ready() -> None:
    module = api()
    digest = report()

    payload = module.strategy_team_source_gap_backlog_v10_payload(digest)
    encoded = json.dumps(payload, sort_keys=True)

    assert digest.input_count == d("0")
    assert digest.backlog_item_count == d("0")
    assert digest.priority_status == "clear"
    assert digest.max_backlog_priority_score == d("0.000000")
    assert digest.mean_backlog_priority_score == d("0.000000")
    assert digest.reason_codes == ("team_source_gap_backlog_v10_clear",)
    assert digest.rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert payload == digest.payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "0"
    assert payload["max_backlog_priority_score"] == "0.000000"
    assert payload["rows"] == []
    assert payload["reason_codes"] == ["team_source_gap_backlog_v10_clear"]
    assert type(payload["validation_digest"]) is str
    assert '"0.000000"' in encoded
    assert all(type(value) is not float for value in _walk(payload))
    assert all(type(value) is not int for value in _walk(payload))


def test_validation_rejects_non_decimal_bad_flags_and_tampered_rows_or_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="stale_packet_pressure_count"):
        config(stale_packet_pressure_count=d("0"))
    with pytest.raises(ValueError, match="disagreement_pressure_count"):
        config(disagreement_pressure_count=d("2.500000"))
    with pytest.raises(ValueError, match="near_resolution_hours"):
        config(urgent_resolution_hours=d("24.000000"), near_resolution_hours=d("6.000000"))
    with pytest.raises(ValueError, match="critical_priority_score_threshold"):
        config(
            high_priority_score_threshold=d("0.700000"),
            critical_priority_score_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("strategy-team-source-gap-backlog-v10"))

    with pytest.raises(ValueError, match="stale_packet_count must be a Decimal"):
        module.StrategyTeamSourceGapBacklogV10Input(
            backlog_id="gap-non-decimal",
            team_id="team",
            market_slug="market",
            stale_packet_count=1,
            required_source_count=d("3"),
            current_source_count=d("3"),
            disagreement_backlog_count=d("0"),
            hours_to_resolution=d("72.000000"),
            available_specialist_minutes=d("60.000000"),
            estimated_repair_minutes=d("30.000000"),
        )
    with pytest.raises(ValueError, match="current_source_count"):
        backlog_item(current_sources="1.500000")
    with pytest.raises(ValueError, match="required_source_count"):
        backlog_item(required_sources="0")
    with pytest.raises(ValueError, match="hours_to_resolution"):
        backlog_item(resolution_hours="-1.000000")
    with pytest.raises(ValueError, match="estimated_repair_minutes"):
        backlog_item(repair_minutes="0.000000")
    with pytest.raises(ValueError, match="available_specialist_minutes"):
        module.StrategyTeamSourceGapBacklogV10Input(
            backlog_id="gap-decimal-subclass",
            team_id="team",
            market_slug="market",
            stale_packet_count=d("0"),
            required_source_count=d("3"),
            current_source_count=d("3"),
            disagreement_backlog_count=d("0"),
            hours_to_resolution=d("72.000000"),
            available_specialist_minutes=_DecimalSubclass("60.000000"),
            estimated_repair_minutes=d("30.000000"),
        )
    with pytest.raises(ValueError, match="backlog_id"):
        backlog_item(backlog_id="")
    with pytest.raises(ValueError, match="paper_only"):
        backlog_item(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(backlog_item(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(backlog_item(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="duplicate backlog_id"):
        report(backlog_item(backlog_id="dup"), backlog_item(backlog_id="dup"))
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_team_source_gap_backlog_v10_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    digest = report(backlog_item())
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].priority_band = "critical"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.priority_status = "critical"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)
    with pytest.raises(ValueError, match="missing_source_count"):
        replace(digest.rows[0], missing_source_count=d("9"))
    with pytest.raises(ValueError, match="backlog_priority_score"):
        replace(
            digest.rows[0],
            backlog_priority_score=d("0.900000"),
            priority_band="critical",
            recommended_action="pause_market_until_source_gap_repaired",
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            digest.rows[0],
            reason_codes=("team_source_gap_backlog_v10_missing_source_quorum",),
        )
    with pytest.raises(ValueError, match="total_missing_source_count"):
        replace(digest, total_missing_source_count=d("9"))
    with pytest.raises(ValueError, match="priority_status"):
        replace(digest, priority_status="critical")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(digest, validation_digest="0")


def test_public_payload_rejects_tampering_missing_digest_and_live_surface() -> None:
    module = api()
    digest = report(backlog_item())
    payload = digest.payload

    assert module.strategy_team_source_gap_backlog_v10_payload(payload) == payload

    tampered_total = dict(payload)
    tampered_total["total_missing_source_count"] = "9"
    with pytest.raises(ValueError, match="total_missing_source_count"):
        module.strategy_team_source_gap_backlog_v10_payload(tampered_total)

    missing_digest = dict(payload)
    del missing_digest["validation_digest"]
    with pytest.raises(ValueError, match="validation_digest"):
        module.strategy_team_source_gap_backlog_v10_payload(missing_digest)

    unsafe_field = dict(payload)
    unsafe_field["wallet_address"] = "paper-wallet"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_team_source_gap_backlog_v10_payload(unsafe_field)

    unsafe_value = dict(payload)
    unsafe_value["market_slug"] = "connect-wallet"
    with pytest.raises(ValueError, match="unsafe live surface value"):
        module.strategy_team_source_gap_backlog_v10_payload(unsafe_value)


def test_public_types_are_frozen_decimal_only_and_exported() -> None:
    module = api()
    digest = report(backlog_item())

    assert module.__all__ == (
        "DEFAULT_STRATEGY_TEAM_SOURCE_GAP_BACKLOG_V10_CONFIG_VERSION",
        "PRIORITY_BANDS",
        "PRIORITY_STATUSES",
        "RECOMMENDED_ACTIONS",
        "ROW_REASON_CODES",
        "REPORT_REASON_CODES",
        "StrategyTeamSourceGapBacklogV10Config",
        "StrategyTeamSourceGapBacklogV10Input",
        "StrategyTeamSourceGapBacklogV10Row",
        "StrategyTeamSourceGapBacklogV10Report",
        "build_strategy_team_source_gap_backlog_v10_report",
        "strategy_team_source_gap_backlog_v10_payload",
    )
    for exported_name in module.__all__:
        exported_value = getattr(module, exported_name)
        if isinstance(exported_value, type):
            assert is_dataclass(exported_value)
            assert exported_value.__dataclass_params__.frozen is True

    for value in (config(), backlog_item(), digest.rows[0], digest):
        for field in fields(value):
            if field.name.endswith(
                (
                    "_count",
                    "_hours",
                    "_minutes",
                    "_ratio",
                    "_pressure",
                    "_urgency",
                    "_score",
                    "_threshold",
                ),
            ):
                assert field.type == "Decimal"
                assert type(getattr(value, field.name)) is Decimal


def test_module_scope_stays_pure_readonly_and_without_float_literals() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()

    for forbidden in (
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "broker",
        "place_order",
        "submit_order",
        "signing",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            assert type(node.value) is not int
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "open", "float", "int"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "request",
                    "read_text",
                    "write_text",
                }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in {
                    "httpx",
                    "os",
                    "pathlib",
                    "psycopg",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "supabase",
                }
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in {
                "httpx",
                "os",
                "pathlib",
                "psycopg",
                "requests",
                "socket",
                "sqlite3",
                "subprocess",
                "supabase",
            }
