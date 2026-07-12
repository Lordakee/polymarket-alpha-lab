from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_event_time_decay_priority_report import (
    MarketEventTimeDecayPriorityReportConfig,
    MarketEventTimeDecayPriorityReportInput,
    MarketEventTimeDecayPriorityReportRow,
    build_market_event_time_decay_priority_report,
    market_event_time_decay_priority_report_digest,
    market_event_time_decay_priority_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_event_time_decay_priority_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketEventTimeDecayPriorityReportConfig:
    values = {
        "urgent_resolution_seconds": d("3600.000000"),
        "watch_resolution_seconds": d("86400.000000"),
        "stale_source_age_seconds": d("1800.000000"),
        "thin_liquidity_depth_usdc": d("5000.000000"),
        "must_review_floor_seconds": d("300.000000"),
        "config_version": "market-event-time-decay-priority-report-test-v0",
    }
    values.update(overrides)
    return MarketEventTimeDecayPriorityReportConfig(**values)


def event_input(
    event_ref: str,
    *,
    time_to_resolution_seconds: Decimal = d("7200.000000"),
    source_freshness_age_seconds: Decimal = d("600.000000"),
    edge_to_threshold_probability: Decimal = d("0.100000"),
    liquidity_depth_usdc: Decimal = d("10000.000000"),
    settlement_risk_band: str = "low",
    manual_review_pending: bool = False,
    team_memory_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEventTimeDecayPriorityReportInput:
    return MarketEventTimeDecayPriorityReportInput(
        event_ref=event_ref,
        time_to_resolution_seconds=time_to_resolution_seconds,
        source_freshness_age_seconds=source_freshness_age_seconds,
        edge_to_threshold_probability=edge_to_threshold_probability,
        liquidity_depth_usdc=liquidity_depth_usdc,
        settlement_risk_band=settlement_risk_band,
        manual_review_pending=manual_review_pending,
        team_memory_ready=team_memory_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *inputs: MarketEventTimeDecayPriorityReportInput,
    cfg: MarketEventTimeDecayPriorityReportConfig | None = None,
):
    return build_market_event_time_decay_priority_report(inputs, config=cfg or config())


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(value.values()) + tuple(item for v in value.values() for item in walk(v))
    if isinstance(value, list):
        return tuple(value) + tuple(item for v in value for item in walk(v))
    return (value,)


def float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if (
            field.name.endswith("_score")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_probability")
            or field.name.endswith("_usdc")
            or field.name.endswith("_count")
        ):
            assert type(value) is Decimal, field.name


def test_builds_time_decay_priority_report_with_review_deadlines_and_reasons() -> None:
    priority_report = report(
        event_input(
            "event-urgent-manual",
            time_to_resolution_seconds=d("900.000000"),
            source_freshness_age_seconds=d("2400.000000"),
            edge_to_threshold_probability=d("0.180000"),
            liquidity_depth_usdc=d("2500.000000"),
            settlement_risk_band="high",
            manual_review_pending=True,
            team_memory_ready=True,
        ),
        event_input(
            "event-blocked-memory",
            time_to_resolution_seconds=d("1800.000000"),
            source_freshness_age_seconds=d("300.000000"),
            edge_to_threshold_probability=d("0.120000"),
            liquidity_depth_usdc=d("8000.000000"),
            settlement_risk_band="medium",
            manual_review_pending=False,
            team_memory_ready=False,
        ),
        event_input(
            "event-watch",
            time_to_resolution_seconds=d("36000.000000"),
            source_freshness_age_seconds=d("900.000000"),
            edge_to_threshold_probability=d("0.060000"),
            liquidity_depth_usdc=d("9000.000000"),
            settlement_risk_band="medium",
        ),
        event_input(
            "event-low",
            time_to_resolution_seconds=d("604800.000000"),
            source_freshness_age_seconds=d("120.000000"),
            edge_to_threshold_probability=d("0.010000"),
            liquidity_depth_usdc=d("25000.000000"),
            settlement_risk_band="low",
        ),
    )

    assert is_dataclass(priority_report)
    assert priority_report.event_count == d("4")
    assert priority_report.urgent_count == d("1")
    assert priority_report.watch_count == d("1")
    assert priority_report.low_count == d("1")
    assert priority_report.blocked_count == d("1")
    assert priority_report.ready_count == d("3")
    assert priority_report.ready_ratio == d("0.750000")
    assert priority_report.status == "blocked"
    assert priority_report.paper_only is True
    assert priority_report.report_only is True
    assert priority_report.readonly is True

    assert tuple(row.event_ref for row in priority_report.rows) == (
        "event-blocked-memory",
        "event-urgent-manual",
        "event-watch",
        "event-low",
    )
    assert tuple(row.urgency_band for row in priority_report.rows) == (
        "blocked",
        "urgent",
        "watch",
        "low",
    )
    assert priority_report.rows[0].blocked_reason_codes == ("team_memory_not_ready",)
    assert priority_report.rows[0].attention_reason_codes == (
        "resolution_window_urgent",
        "settlement_risk_medium",
    )
    assert priority_report.rows[0].must_review_before_seconds == d("300.000000")
    assert priority_report.rows[1].urgency_score == d("1.000000")
    assert priority_report.rows[1].must_review_before_seconds == d("300.000000")
    assert priority_report.rows[1].blocked_reason_codes == ()
    assert priority_report.rows[1].attention_reason_codes == (
        "resolution_window_urgent",
        "source_freshness_stale",
        "edge_to_threshold_material",
        "liquidity_depth_thin",
        "settlement_risk_high",
        "manual_review_pending",
    )
    assert priority_report.rows[2].must_review_before_seconds == d("18000.000000")
    assert priority_report.rows[3].must_review_before_seconds == d("86400.000000")

    payload = market_event_time_decay_priority_report_payload(priority_report)

    assert payload["event_count"] == "4"
    assert payload["ready_ratio"] == "0.750000"
    assert payload["rows"][1]["urgency_score"] == "1.000000"
    assert payload["rows"][1]["must_review_before_seconds"] == "300.000000"
    assert payload["rows"][1]["attention_reason_codes"] == [
        "resolution_window_urgent",
        "source_freshness_stale",
        "edge_to_threshold_material",
        "liquidity_depth_thin",
        "settlement_risk_high",
        "manual_review_pending",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    digest = market_event_time_decay_priority_report_digest(priority_report)
    assert digest == priority_report.digest
    assert len(digest) == 64
    assert digest == market_event_time_decay_priority_report_digest(priority_report)


def test_empty_report_is_paper_only_json_ready_and_has_stable_digest() -> None:
    priority_report = report()

    assert priority_report.status == "empty"
    assert priority_report.reason_codes == ("time_decay_priority_report_empty",)
    assert priority_report.event_count == d("0")
    assert priority_report.ready_ratio == d("0.000000")
    assert priority_report.rows == ()

    payload = market_event_time_decay_priority_report_payload(priority_report)
    assert payload["status"] == "empty"
    assert payload["reason_codes"] == ["time_decay_priority_report_empty"]
    assert payload["rows"] == []
    assert payload["ready_ratio"] == "0.000000"
    assert payload["digest"] == priority_report.digest
    assert float_paths(payload) == ()


def test_public_dataclasses_are_frozen_and_validate_decimal_only_inputs() -> None:
    priority_report = report(event_input("event-ready"))

    with pytest.raises(FrozenInstanceError):
        priority_report.status = "urgent"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        priority_report.rows[0].urgency_band = "low"  # type: ignore[misc]
    with pytest.raises(ValueError, match="time_to_resolution_seconds must be a Decimal"):
        event_input("event-int", time_to_resolution_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="edge_to_threshold_probability must be between 0 and 1"):
        event_input("event-bad-edge", edge_to_threshold_probability=d("1.500000"))
    with pytest.raises(ValueError, match="settlement_risk_band must be one of"):
        event_input("event-bad-band", settlement_risk_band="critical")
    with pytest.raises(ValueError, match="readonly"):
        replace(priority_report, readonly=False)
    with pytest.raises(ValueError, match="rows must contain"):
        replace(priority_report, rows=(object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must match rows"):
        replace(priority_report, ready_ratio=d("0.000000"))

    explicit_row = MarketEventTimeDecayPriorityReportRow(
        event_ref=priority_report.rows[0].event_ref,
        time_to_resolution_seconds=priority_report.rows[0].time_to_resolution_seconds,
        source_freshness_age_seconds=priority_report.rows[0].source_freshness_age_seconds,
        edge_to_threshold_probability=priority_report.rows[0].edge_to_threshold_probability,
        liquidity_depth_usdc=priority_report.rows[0].liquidity_depth_usdc,
        settlement_risk_band=priority_report.rows[0].settlement_risk_band,
        manual_review_pending=priority_report.rows[0].manual_review_pending,
        team_memory_ready=priority_report.rows[0].team_memory_ready,
        urgency_score=priority_report.rows[0].urgency_score,
        urgency_band=priority_report.rows[0].urgency_band,
        must_review_before_seconds=priority_report.rows[0].must_review_before_seconds,
        blocked_reason_codes=priority_report.rows[0].blocked_reason_codes,
        attention_reason_codes=priority_report.rows[0].attention_reason_codes,
    )
    assert explicit_row == priority_report.rows[0]

    for instance in (config(), event_input("event-decimal"), priority_report, priority_report.rows[0]):
        assert_public_numeric_fields_are_decimal(instance)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_public_dataclasses_reject_truthy_non_true_hard_flags(flag_name: str) -> None:
    priority_report = report(event_input("event-ready"))

    with pytest.raises(ValueError, match=flag_name):
        config(**{flag_name: 1})
    with pytest.raises(ValueError, match=flag_name):
        event_input("event-flag", **{flag_name: 1})
    with pytest.raises(ValueError, match=flag_name):
        replace(priority_report.rows[0], **{flag_name: 1})
    with pytest.raises(ValueError, match=flag_name):
        replace(priority_report, **{flag_name: 1})


def test_rejects_duplicate_events_and_unsafe_public_surface_terms() -> None:
    with pytest.raises(ValueError, match="event_ref values must be unique"):
        report(event_input("event-dup"), event_input("event-dup"))
    with pytest.raises(ValueError, match="event_ref must not expose unsafe terms"):
        event_input("event-wallet")
    with pytest.raises(ValueError, match="event_ref must not contain URLs"):
        event_input("https://polymarket.com/event/raw")
    with pytest.raises(ValueError, match="config_version must not expose unsafe terms"):
        config(config_version="time-decay-live-trading-v0")


def test_module_does_not_import_io_network_persistence_or_execution_surfaces() -> None:
    tree = compile(
        MODULE_PATH.read_text(encoding="utf-8"),
        str(MODULE_PATH),
        "exec",
        ast.PyCF_ONLY_AST,
    )
    imported_names: set[str] = set()
    call_names: set[str] = set()
    attr_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                attr_names.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attr_names.add(node.attr)

    forbidden_imports = {
        "asyncio",
        "http",
        "jsonlines",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "execute",
        "executemany",
        "submit",
        "cancel",
        "sign",
        "place_order",
        "create_order",
    }
    forbidden_attrs = {
        "connect",
        "request",
        "urlopen",
        "execute",
        "executemany",
        "submit",
        "cancel",
        "sign",
        "place_order",
        "create_order",
    }

    assert imported_names.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert attr_names.isdisjoint(forbidden_attrs)
