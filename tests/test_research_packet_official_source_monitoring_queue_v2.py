from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_official_source_monitoring_queue_v2",
    )


def _config(**overrides: object) -> Any:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION
        ),
        "close_urgency_window_seconds": d("7200.000000"),
        "stale_official_source_age_seconds": d("3600.000000"),
        "contradiction_count_threshold": d("2.000000"),
        "probability_move_threshold": d("0.050000"),
        "resolution_criteria_sensitivity_threshold": d("0.700000"),
        "follow_up_priority_threshold": d("0.800000"),
    }
    values.update(overrides)
    return api.ResearchPacketOfficialSourceMonitoringQueueV2Config(**values)


def _row(
    packet_id: str,
    *,
    market_id: str | None = None,
    team_id: str = "politics",
    category_id: str = "politics",
    market_close_at: datetime = GENERATED_AT + timedelta(hours=24),
    latest_official_source_checked_at: datetime | None = GENERATED_AT
    - timedelta(seconds=600),
    official_source_count: Decimal = d("1.000000"),
    official_contradiction_count: Decimal = d("0.000000"),
    previous_probability: Decimal = d("0.420000"),
    current_probability: Decimal = d("0.430000"),
    resolution_criteria_sensitivity: Decimal = d("0.100000"),
    follow_up_priority_score: Decimal = d("0.100000"),
) -> Any:
    api = _api()
    return api.ResearchPacketOfficialSourceMonitoringQueueV2InputRow(
        packet_id=packet_id,
        market_id=market_id or f"{packet_id}_market",
        team_id=team_id,
        category_id=category_id,
        market_close_at=market_close_at,
        latest_official_source_checked_at=latest_official_source_checked_at,
        official_source_count=official_source_count,
        official_contradiction_count=official_contradiction_count,
        previous_probability=previous_probability,
        current_probability=current_probability,
        resolution_criteria_sensitivity=resolution_criteria_sensitivity,
        follow_up_priority_score=follow_up_priority_score,
    )


def test_monitoring_queue_prioritizes_phase_one_official_source_signals() -> None:
    api = _api()

    report = api.build_research_packet_official_source_monitoring_queue_v2(
        (
            _row("ready_packet"),
            _row(
                "probability_move_packet",
                team_id="crypto_btc",
                category_id="finance.crypto.btc",
                previous_probability=d("0.250000"),
                current_probability=d("0.340000"),
            ),
            _row(
                "close_packet",
                team_id="sports_soccer",
                category_id="sports.soccer",
                market_close_at=GENERATED_AT + timedelta(seconds=1800),
                latest_official_source_checked_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _row(
                "missing_packet",
                team_id="crypto_eth",
                category_id="finance.crypto.eth",
                latest_official_source_checked_at=None,
                official_source_count=d("0.000000"),
                official_contradiction_count=d("3.000000"),
                previous_probability=d("0.700000"),
                current_probability=d("0.620000"),
                resolution_criteria_sensitivity=d("0.850000"),
                follow_up_priority_score=d("0.900000"),
            ),
            _row(
                "stale_packet",
                team_id="macro_rates",
                category_id="finance.macro.rates",
                latest_official_source_checked_at=GENERATED_AT
                - timedelta(seconds=5400),
                follow_up_priority_score=d("0.850000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, api.ResearchPacketOfficialSourceMonitoringQueueV2Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION
    )
    assert report.report_status == "urgent"
    assert report.packet_count == d("5.000000")
    assert report.queue_item_count == d("4.000000")
    assert report.urgent_item_count == d("3.000000")
    assert report.market_close_urgency_count == d("1.000000")
    assert report.missing_official_source_count == d("1.000000")
    assert report.stale_official_source_count == d("1.000000")
    assert report.contradiction_count == d("1.000000")
    assert report.probability_move_count == d("2.000000")
    assert report.resolution_criteria_sensitivity_count == d("1.000000")
    assert report.follow_up_priority_count == d("2.000000")
    assert report.min_time_to_market_close_seconds == d("1800.000000")
    assert report.max_official_source_age_seconds == d("5400.000000")
    assert report.max_probability_move == d("0.090000")
    assert report.queue_pressure_ratio == d("0.800000")
    assert report.reason_codes == (
        "market_close_urgent",
        "official_source_missing",
        "official_source_stale",
        "official_source_contradiction_count",
        "market_probability_move",
        "resolution_criteria_sensitive",
        "follow_up_priority",
    )
    assert len(report.monitoring_digest) == 64

    item_type = api.ResearchPacketOfficialSourceMonitoringQueueV2Item
    assert report.queue_items == (
        item_type(
            packet_id="close_packet",
            market_id="close_packet_market",
            team_id="sports_soccer",
            category_id="sports.soccer",
            queue_status="urgent",
            priority_rank=d("1.000000"),
            market_close_at=GENERATED_AT + timedelta(seconds=1800),
            time_to_market_close_seconds=d("1800.000000"),
            latest_official_source_checked_at=GENERATED_AT - timedelta(seconds=900),
            official_source_age_seconds=d("900.000000"),
            official_source_count=d("1.000000"),
            official_contradiction_count=d("0.000000"),
            previous_probability=d("0.420000"),
            current_probability=d("0.430000"),
            probability_move=d("0.010000"),
            resolution_criteria_sensitivity=d("0.100000"),
            follow_up_priority_score=d("0.100000"),
            reason_codes=("market_close_urgent",),
            monitoring_digest=report.queue_items[0].monitoring_digest,
        ),
        item_type(
            packet_id="missing_packet",
            market_id="missing_packet_market",
            team_id="crypto_eth",
            category_id="finance.crypto.eth",
            queue_status="urgent",
            priority_rank=d("2.000000"),
            market_close_at=GENERATED_AT + timedelta(hours=24),
            time_to_market_close_seconds=d("86400.000000"),
            latest_official_source_checked_at=None,
            official_source_age_seconds=None,
            official_source_count=d("0.000000"),
            official_contradiction_count=d("3.000000"),
            previous_probability=d("0.700000"),
            current_probability=d("0.620000"),
            probability_move=d("0.080000"),
            resolution_criteria_sensitivity=d("0.850000"),
            follow_up_priority_score=d("0.900000"),
            reason_codes=(
                "official_source_missing",
                "official_source_contradiction_count",
                "market_probability_move",
                "resolution_criteria_sensitive",
                "follow_up_priority",
            ),
            monitoring_digest=report.queue_items[1].monitoring_digest,
        ),
        item_type(
            packet_id="stale_packet",
            market_id="stale_packet_market",
            team_id="macro_rates",
            category_id="finance.macro.rates",
            queue_status="urgent",
            priority_rank=d("3.000000"),
            market_close_at=GENERATED_AT + timedelta(hours=24),
            time_to_market_close_seconds=d("86400.000000"),
            latest_official_source_checked_at=GENERATED_AT - timedelta(seconds=5400),
            official_source_age_seconds=d("5400.000000"),
            official_source_count=d("1.000000"),
            official_contradiction_count=d("0.000000"),
            previous_probability=d("0.420000"),
            current_probability=d("0.430000"),
            probability_move=d("0.010000"),
            resolution_criteria_sensitivity=d("0.100000"),
            follow_up_priority_score=d("0.850000"),
            reason_codes=("official_source_stale", "follow_up_priority"),
            monitoring_digest=report.queue_items[2].monitoring_digest,
        ),
        item_type(
            packet_id="probability_move_packet",
            market_id="probability_move_packet_market",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            queue_status="watch",
            priority_rank=d("4.000000"),
            market_close_at=GENERATED_AT + timedelta(hours=24),
            time_to_market_close_seconds=d("86400.000000"),
            latest_official_source_checked_at=GENERATED_AT - timedelta(seconds=600),
            official_source_age_seconds=d("600.000000"),
            official_source_count=d("1.000000"),
            official_contradiction_count=d("0.000000"),
            previous_probability=d("0.250000"),
            current_probability=d("0.340000"),
            probability_move=d("0.090000"),
            resolution_criteria_sensitivity=d("0.100000"),
            follow_up_priority_score=d("0.100000"),
            reason_codes=("market_probability_move",),
            monitoring_digest=report.queue_items[3].monitoring_digest,
        ),
    )
    assert tuple(item.priority_rank for item in report.queue_items) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )
    assert len({item.monitoring_digest for item in report.queue_items}) == 4


def test_monitoring_queue_empty_payload_is_json_ready_and_digest_stable() -> None:
    api = _api()

    report = api.build_research_packet_official_source_monitoring_queue_v2(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    report_again = api.build_research_packet_official_source_monitoring_queue_v2(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report == report_again
    assert report.report_status == "clear"
    assert report.packet_count == d("0.000000")
    assert report.queue_item_count == d("0.000000")
    assert report.queue_pressure_ratio == d("0.000000")
    assert report.queue_items == ()
    assert report.reason_codes == ("official_source_monitoring_queue_clear",)

    payload = api.research_packet_official_source_monitoring_queue_v2_to_payload(report)
    assert payload == {
        "generated_at": GENERATED_AT.isoformat(),
        "config_version": (
            api.DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION
        ),
        "report_status": "clear",
        "packet_count": "0.000000",
        "queue_item_count": "0.000000",
        "urgent_item_count": "0.000000",
        "market_close_urgency_count": "0.000000",
        "missing_official_source_count": "0.000000",
        "stale_official_source_count": "0.000000",
        "contradiction_count": "0.000000",
        "probability_move_count": "0.000000",
        "resolution_criteria_sensitivity_count": "0.000000",
        "follow_up_priority_count": "0.000000",
        "min_time_to_market_close_seconds": "0.000000",
        "max_official_source_age_seconds": "0.000000",
        "max_probability_move": "0.000000",
        "queue_pressure_ratio": "0.000000",
        "reason_codes": ["official_source_monitoring_queue_clear"],
        "queue_items": [],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "monitoring_digest": report.monitoring_digest,
    }
    _assert_no_floats(payload)
    assert len(payload["monitoring_digest"]) == 64


def test_monitoring_queue_validates_decimal_time_flags_and_digest() -> None:
    api = _api()
    config = _config()

    with pytest.raises(FrozenInstanceError):
        config.probability_move_threshold = d("0.020000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability_move_threshold"):
        _config(probability_move_threshold=d("1.500000"))
    with pytest.raises(ValueError, match="follow_up_priority_threshold"):
        _config(follow_up_priority_threshold=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="generated_at"):
        api.build_research_packet_official_source_monitoring_queue_v2(
            (),
            config=config,
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="market_close_at"):
        _row("naive_close", market_close_at=datetime(2026, 7, 7, 14, 0))
    with pytest.raises(ValueError, match="latest_official_source_checked_at"):
        api.build_research_packet_official_source_monitoring_queue_v2(
            (
                _row(
                    "future_check",
                    latest_official_source_checked_at=GENERATED_AT
                    + timedelta(seconds=1),
                ),
            ),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="category_id"):
        _row("category_mismatch", team_id="crypto_btc", category_id="politics")
    with pytest.raises(ValueError, match="packet_id"):
        _row("wallet_packet")
    with pytest.raises(ValueError, match="official_source_count"):
        _row("non_decimal_count", official_source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="previous_probability"):
        _row("bad_probability", previous_probability=d("1.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_row("not_paper"), paper_only=False)
    with pytest.raises(ValueError, match="monitoring_digest"):
        replace(_row("digest_source"), monitoring_digest="bad")
    with pytest.raises(ValueError, match="monitoring_rows"):
        api.build_research_packet_official_source_monitoring_queue_v2(
            (object(),),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate packet_id and market_id"):
        api.build_research_packet_official_source_monitoring_queue_v2(
            (_row("duplicate"), _row("duplicate")),
            config=config,
            generated_at=GENERATED_AT,
        )


def test_monitoring_queue_scope_is_pure_report_only() -> None:
    api = _api()
    assert set(api.__all__) == {
        "DEFAULT_RESEARCH_PACKET_OFFICIAL_SOURCE_MONITORING_QUEUE_V2_CONFIG_VERSION",
        "ResearchPacketOfficialSourceMonitoringQueueV2Config",
        "ResearchPacketOfficialSourceMonitoringQueueV2InputRow",
        "ResearchPacketOfficialSourceMonitoringQueueV2Item",
        "ResearchPacketOfficialSourceMonitoringQueueV2Report",
        "build_research_packet_official_source_monitoring_queue_v2",
        "research_packet_official_source_monitoring_queue_v2_to_payload",
    }

    source = inspect.getsource(api)
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "buy",
        "connect",
        "execute",
        "open",
        "place_order",
        "request",
        "sell",
        "submit_order",
        "write",
    }

    imports: list[str] = []
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                calls.append(call_name.rsplit(".", maxsplit=1)[-1])

    assert not (set(name.split(".", maxsplit=1)[0] for name in imports) & forbidden_import_roots)
    assert not (set(calls) & forbidden_calls)
    for token in (
        "private_key",
        "place_order",
        "submit_order",
        "cancel_order",
        "live_trading",
        "database_write",
    ):
        assert token not in source


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_floats(item)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
