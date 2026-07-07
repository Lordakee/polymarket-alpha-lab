from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.category_research_capacity_heatmap"
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    team_id: str,
    *,
    queue_count: str = "0",
    available_analyst_agent_slots: str = "1",
    capacity_gap_count: str = "0",
    capacity_status: str = "ready",
    backlog_assignment_count: str = "0",
    backlog_count: str = "0",
    backlog_pressure_status: str = "pass",
    memory_source_count: str = "1",
    memory_pass_count: str = "1",
    memory_watch_count: str = "0",
    memory_blocked_count: str = "0",
    memory_readiness_status: str = "pass",
):
    heatmap = api()
    return heatmap.CategoryResearchCapacityHeatmapInput(
        team_id=team_id,
        queue_count=d(queue_count),
        available_analyst_agent_slots=d(available_analyst_agent_slots),
        capacity_gap_count=d(capacity_gap_count),
        capacity_status=capacity_status,
        backlog_assignment_count=d(backlog_assignment_count),
        backlog_count=d(backlog_count),
        backlog_pressure_status=backlog_pressure_status,
        memory_source_count=d(memory_source_count),
        memory_pass_count=d(memory_pass_count),
        memory_watch_count=d(memory_watch_count),
        memory_blocked_count=d(memory_blocked_count),
        memory_readiness_status=memory_readiness_status,
    )


def rows(*signals):
    heatmap = api()
    return heatmap.build_category_research_capacity_heatmap_rows(
        signals,
        config=heatmap.CategoryResearchCapacityHeatmapConfig(),
    )


def report(*signals, public_payload=()):
    heatmap = api()
    return heatmap.build_category_research_capacity_heatmap_report(
        signals,
        generated_at=NOW,
        config=heatmap.CategoryResearchCapacityHeatmapConfig(),
        public_payload=public_payload,
    )


def test_builds_category_heatmap_rows_for_phase_1_subdomains() -> None:
    heatmap_rows = rows(
        signal(
            "politics",
            queue_count="2",
            available_analyst_agent_slots="2",
            backlog_assignment_count="10",
            backlog_count="1",
            memory_source_count="3",
            memory_pass_count="3",
        ),
        signal(
            "crypto_btc",
            queue_count="5",
            available_analyst_agent_slots="2",
            capacity_gap_count="1",
            capacity_status="overloaded",
            backlog_assignment_count="10",
            backlog_count="3",
            backlog_pressure_status="watch",
            memory_source_count="4",
            memory_pass_count="3",
            memory_watch_count="1",
            memory_readiness_status="watch",
        ),
        signal(
            "crypto_eth",
            queue_count="1",
            available_analyst_agent_slots="1",
            backlog_assignment_count="8",
            backlog_count="0",
            memory_source_count="2",
            memory_pass_count="2",
        ),
        signal(
            "macro_rates",
            queue_count="2",
            available_analyst_agent_slots="0",
            capacity_gap_count="2",
            capacity_status="blocked",
            backlog_assignment_count="4",
            backlog_count="2",
            backlog_pressure_status="blocked",
            memory_source_count="1",
            memory_pass_count="0",
            memory_blocked_count="1",
            memory_readiness_status="blocked",
        ),
        signal(
            "commodities_gold",
            queue_count="1",
            available_analyst_agent_slots="1",
            backlog_assignment_count="5",
            backlog_count="0",
            memory_source_count="2",
            memory_pass_count="2",
        ),
        signal(
            "commodities_oil",
            queue_count="1",
            available_analyst_agent_slots="1",
            backlog_assignment_count="5",
            backlog_count="0",
            memory_source_count="2",
            memory_pass_count="2",
        ),
        signal(
            "sports_soccer",
            queue_count="2",
            available_analyst_agent_slots="2",
            backlog_assignment_count="6",
            backlog_count="0",
            memory_source_count="2",
            memory_pass_count="2",
        ),
        signal(
            "sports_basketball",
            queue_count="1",
            available_analyst_agent_slots="1",
            backlog_assignment_count="3",
            backlog_count="0",
            memory_source_count="1",
            memory_pass_count="1",
        ),
        signal(
            "sports_other",
            queue_count="1",
            available_analyst_agent_slots="1",
            backlog_assignment_count="3",
            backlog_count="0",
            memory_source_count="1",
            memory_pass_count="1",
        ),
    )

    assert tuple(row.category_id for row in heatmap_rows) == (
        "politics",
        "crypto",
        "macro",
        "commodities",
        "sports",
    )

    crypto = heatmap_rows[1]
    assert crypto.configured_team_count == d("2")
    assert crypto.observed_team_count == d("2")
    assert crypto.queue_count == d("6")
    assert crypto.available_analyst_agent_slots == d("3")
    assert crypto.capacity_gap_count == d("1")
    assert crypto.capacity_pressure_ratio == d("2.000000")
    assert crypto.backlog_assignment_count == d("18")
    assert crypto.backlog_count == d("3")
    assert crypto.backlog_pressure_ratio == d("0.166667")
    assert crypto.memory_source_count == d("6")
    assert crypto.memory_pass_count == d("5")
    assert crypto.memory_watch_count == d("1")
    assert crypto.memory_blocked_count == d("0")
    assert crypto.memory_readiness_ratio == d("0.833333")
    assert crypto.capacity_status == "watch"
    assert crypto.backlog_pressure_status == "watch"
    assert crypto.memory_readiness_status == "watch"
    assert crypto.heatmap_status == "watch"
    assert crypto.reason_codes == (
        "category_capacity_watch",
        "category_backlog_watch",
        "category_memory_watch",
    )
    assert crypto.paper_only is True
    assert crypto.report_only is True
    assert crypto.readonly is True

    macro = heatmap_rows[2]
    assert macro.capacity_pressure_ratio == d("0.000000")
    assert macro.backlog_pressure_ratio == d("0.500000")
    assert macro.memory_readiness_ratio == d("0.000000")
    assert macro.heatmap_status == "blocked"
    assert macro.reason_codes == (
        "category_capacity_blocked",
        "category_backlog_blocked",
        "category_memory_blocked",
    )


def test_missing_category_inputs_emit_blocked_readonly_rows() -> None:
    heatmap_rows = rows(signal("politics"))
    crypto = heatmap_rows[1]

    assert crypto.category_id == "crypto"
    assert crypto.configured_team_count == d("2")
    assert crypto.observed_team_count == d("0")
    assert crypto.queue_count == d("0")
    assert crypto.capacity_pressure_ratio == d("0.000000")
    assert crypto.backlog_pressure_ratio == d("0.000000")
    assert crypto.memory_readiness_ratio == d("0.000000")
    assert crypto.capacity_status == "blocked"
    assert crypto.backlog_pressure_status == "blocked"
    assert crypto.memory_readiness_status == "blocked"
    assert crypto.heatmap_status == "blocked"
    assert crypto.reason_codes == ("category_source_missing",)


def test_heatmap_dataclasses_are_frozen_and_decimal_only() -> None:
    heatmap = api()
    row = rows(signal("politics"))[0]

    assert is_dataclass(row)
    with pytest.raises(FrozenInstanceError):
        row.queue_count = d("2")  # type: ignore[misc]

    with pytest.raises(ValueError, match="queue_count"):
        heatmap.CategoryResearchCapacityHeatmapInput(
            team_id="politics",
            queue_count=1,
            available_analyst_agent_slots=d("1"),
            capacity_gap_count=d("0"),
            capacity_status="ready",
            backlog_assignment_count=d("0"),
            backlog_count=d("0"),
            backlog_pressure_status="pass",
            memory_source_count=d("1"),
            memory_pass_count=d("1"),
            memory_watch_count=d("0"),
            memory_blocked_count=d("0"),
            memory_readiness_status="pass",
        )

    with pytest.raises(ValueError, match="duplicate"):
        rows(signal("politics"), signal("politics"))

    with pytest.raises(ValueError, match="paper_only"):
        replace(heatmap.CategoryResearchCapacityHeatmapConfig(), paper_only=False)


def test_report_payload_is_json_safe_and_digest_is_deterministic() -> None:
    heatmap = api()
    payload_item = heatmap.CategoryResearchCapacityHeatmapPublicPayloadItem(
        key="summary_ref",
        value="phase1_capacity_snapshot",
    )

    first_report = report(
        signal("politics"),
        signal(
            "crypto_btc",
            queue_count="4",
            available_analyst_agent_slots="1",
            capacity_status="overloaded",
            backlog_assignment_count="5",
            backlog_count="1",
            backlog_pressure_status="watch",
            memory_source_count="2",
            memory_pass_count="1",
            memory_watch_count="1",
            memory_readiness_status="watch",
        ),
        signal("crypto_eth"),
        public_payload=(payload_item,),
    )
    second_report = report(
        signal("politics"),
        signal(
            "crypto_btc",
            queue_count="4",
            available_analyst_agent_slots="1",
            capacity_status="overloaded",
            backlog_assignment_count="5",
            backlog_count="1",
            backlog_pressure_status="watch",
            memory_source_count="2",
            memory_pass_count="1",
            memory_watch_count="1",
            memory_readiness_status="watch",
        ),
        signal("crypto_eth"),
        public_payload=(payload_item,),
    )

    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert len(first_report.derived_validation_digest) == 64
    assert first_report.generated_at == NOW
    assert first_report.category_count == d("5")
    assert first_report.configured_team_count == d("9")
    assert first_report.observed_team_count == d("3")
    assert first_report.ready_category_count == d("1")
    assert first_report.watch_category_count == d("1")
    assert first_report.blocked_category_count == d("3")
    assert first_report.heatmap_status == "blocked"
    assert first_report.reason_codes == (
        "category_source_missing",
        "category_capacity_ready",
        "category_capacity_watch",
        "category_backlog_ready",
        "category_backlog_watch",
        "category_memory_ready",
        "category_memory_watch",
    )

    payload = first_report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["category_count"] == "5"
    assert payload["configured_team_count"] == "9"
    assert payload["category_rows"][1]["capacity_pressure_ratio"] == "2.000000"
    assert payload["public_payload"][0] == {
        "key": "summary_ref",
        "value": "phase1_capacity_snapshot",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert payload["derived_validation_digest"] == first_report.derived_validation_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(first_report)


def test_report_digest_and_public_payload_reject_tampering() -> None:
    heatmap = api()
    baseline = report(signal("politics"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(baseline, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            baseline,
            public_payload=(
                heatmap.CategoryResearchCapacityHeatmapPublicPayloadItem(
                    key="summary_ref",
                    value="changed",
                ),
            ),
        )

    with pytest.raises(ValueError, match="unsafe public"):
        heatmap.CategoryResearchCapacityHeatmapPublicPayloadItem(
            key="wallet_ref",
            value="safe",
        )


def test_heatmap_scope_excludes_trading_identity_storage_and_raw_market_text() -> None:
    heatmap = api()
    source = inspect.getsource(heatmap)
    tree = ast.parse(source)

    assert heatmap.__all__ == (
        "DEFAULT_CATEGORY_RESEARCH_CAPACITY_HEATMAP_CONFIG_VERSION",
        "CATEGORY_RESEARCH_CAPACITY_HEATMAP_CATEGORIES",
        "CategoryResearchCapacityHeatmapConfig",
        "CategoryResearchCapacityHeatmapInput",
        "CategoryResearchCapacityHeatmapPublicPayloadItem",
        "CategoryResearchCapacityHeatmapRow",
        "CategoryResearchCapacityHeatmapReport",
        "build_category_research_capacity_heatmap_rows",
        "build_category_research_capacity_heatmap_report",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "web3",
    }
    forbidden_fragments = (
        "fast",
        "live",
        "auth",
        "wallet",
        "order",
        "account",
        "slug",
        "question",
        "market",
        "store",
    )
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:
            _assert_no_non_decimal_public_numbers(getattr(value, field_name))
