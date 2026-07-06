from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 21, 0, tzinfo=UTC)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_official_update_watch_queue_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values = {
        "config_version": "research-packet-official-update-watch-queue-v2",
        "official_overdue_seconds": d("3600.000000"),
        "resolution_critical_due_seconds": d("900.000000"),
        "overdue_official_penalty": d("20.000000"),
        "missing_official_penalty": d("30.000000"),
        "resolution_critical_boost": d("25.000000"),
        "proxy_only_penalty": d("10.000000"),
        "watch_priority_floor": d("20.000000"),
        "blocked_priority_floor": d("45.000000"),
    }
    values.update(overrides)
    return api().ResearchPacketOfficialUpdateWatchQueueV2Config(**values)


def source(
    packet_id: str = "packet-alpha",
    source_id: str = "source-alpha",
    *,
    source_kind: str = "official",
    last_checked_age_seconds: int | None = 300,
    expected_update_age_seconds: int | None = None,
    source_priority_score: str = "0.000000",
    resolution_critical: bool = False,
):
    return api().ResearchPacketOfficialUpdateWatchQueueV2Input(
        packet_id=packet_id,
        source_id=source_id,
        source_kind=source_kind,
        last_checked_at=(
            None
            if last_checked_age_seconds is None
            else GENERATED_AT - timedelta(seconds=last_checked_age_seconds)
        ),
        expected_update_at=(
            None
            if expected_update_age_seconds is None
            else GENERATED_AT - timedelta(seconds=expected_update_age_seconds)
        ),
        source_priority_score=d(source_priority_score),
        resolution_critical=resolution_critical,
    )


def report(*sources: object, generated_at: datetime = GENERATED_AT, **overrides: object):
    return api().build_research_packet_official_update_watch_queue_v2(
        sources,
        config=config(**overrides),
        generated_at=generated_at,
    )


def test_official_update_watch_priority_is_deterministic() -> None:
    inputs = (
        source(
            "packet-c",
            "official-c",
            last_checked_age_seconds=7200,
            source_priority_score="5.000000",
        ),
        source(
            "packet-a",
            "official-a",
            last_checked_age_seconds=7200,
            source_priority_score="10.000000",
        ),
        source(
            "packet-b",
            "official-b",
            last_checked_age_seconds=600,
            source_priority_score="1.000000",
        ),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    assert tuple(row.packet_id for row in first.rows) == (
        "packet-a",
        "packet-c",
        "packet-b",
    )
    assert tuple(row.priority_rank for row in first.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.watch_status for row in first.rows) == ("watch", "watch", "pass")
    assert first == second


def test_overdue_official_source_penalties_drive_watch_status() -> None:
    priority_report = report(
        source(
            "packet-overdue",
            "official-overdue",
            last_checked_age_seconds=7200,
            source_priority_score="0.000000",
        ),
        source(
            "packet-expected",
            "official-expected",
            last_checked_age_seconds=7200,
            expected_update_age_seconds=1800,
            source_priority_score="30.000000",
        ),
    )
    rows = {row.packet_id: row for row in priority_report.rows}

    assert rows["packet-overdue"].official_update_overdue is True
    assert rows["packet-overdue"].official_update_priority_score == d("20.000000")
    assert rows["packet-overdue"].watch_status == "watch"
    assert rows["packet-overdue"].reason_codes == ("official_update_overdue",)
    assert rows["packet-expected"].official_update_priority_score == d("50.000000")
    assert rows["packet-expected"].watch_status == "blocked"
    assert priority_report.status == "blocked"
    assert priority_report.reason_codes == (
        "official_update_blocked_items_present",
        "overdue_official_sources_present",
    )


def test_resolution_critical_source_boosts_priority() -> None:
    priority_report = report(
        source(
            "packet-critical",
            "source-critical",
            source_kind="resolution_critical",
            last_checked_age_seconds=1000,
            source_priority_score="20.000000",
        ),
        source(
            "packet-proxy",
            "source-proxy",
            source_kind="proxy",
            expected_update_age_seconds=60,
            source_priority_score="5.000000",
        ),
    )
    rows = {row.packet_id: row for row in priority_report.rows}

    assert rows["packet-critical"].resolution_critical is True
    assert rows["packet-critical"].resolution_critical_due is True
    assert rows["packet-critical"].official_update_priority_score == d("45.000000")
    assert rows["packet-critical"].watch_status == "blocked"
    assert rows["packet-critical"].reason_codes == (
        "resolution_critical_source_due",
    )
    assert rows["packet-proxy"].proxy_only_official_gap is True
    assert rows["packet-proxy"].official_update_priority_score == d("15.000000")
    assert rows["packet-proxy"].watch_status == "pass"
    assert priority_report.resolution_critical_source_count == d("1")


def test_serialization_uses_decimal_strings_and_preserves_hard_flags() -> None:
    module = api()
    payload = module.research_packet_official_update_watch_queue_v2_payload(
        report(
            source(
                "packet-json",
                "official-json",
                last_checked_age_seconds=7200,
                source_priority_score="2.000000",
            ),
        ),
    )

    assert payload["generated_at"] == "2026-07-02T21:00:00+00:00"
    assert payload["source_count"] == "1"
    assert payload["watch_count"] == "1"
    assert payload["max_official_update_priority_score"] == "22.000000"
    assert payload["rows"][0]["priority_rank"] == "1"
    assert payload["rows"][0]["official_update_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["official_update_priority_score"] == "22.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["derived_validation_digest"].startswith("sha256:")
    json.dumps(payload, sort_keys=True)
    assert _has_no_float_values(payload)


def test_public_dataclasses_are_frozen_and_flags_are_hard_true() -> None:
    module = api()
    priority_report = report(source())

    for value in (config(), source(), priority_report.rows[0], priority_report):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(source(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(priority_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="source_priority_score must be a Decimal"):
        module.ResearchPacketOfficialUpdateWatchQueueV2Input(
            packet_id="packet-int",
            source_id="source-int",
            source_kind="official",
            last_checked_at=GENERATED_AT,
            expected_update_at=None,
            source_priority_score=1,
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    priority_report = report(
        source(
            "packet-tamper",
            "official-tamper",
            last_checked_age_seconds=7200,
            source_priority_score="2.000000",
        ),
    )
    row = priority_report.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, official_update_priority_score=d("99.000000"))

    tampered_row = object.__new__(api().ResearchPacketOfficialUpdateWatchQueueV2Row)
    for name, value in row.__dict__.items():
        object.__setattr__(tampered_row, name, value)
    object.__setattr__(tampered_row, "source_priority_score", d("3.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(priority_report, rows=(tampered_row,))


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("packet_id", "packet-live"),
        ("packet_id", "packet-auth"),
        ("packet_id", "packet-wallet"),
        ("packet_id", "packet-order"),
        ("packet_id", "packet-network"),
        ("packet_id", "packet-database"),
        ("packet_id", "packet-persist"),
        ("packet_id", "packet-signing"),
        ("packet_id", "packet-mutation"),
        ("packet_id", "packet-buy"),
        ("packet_id", "packet-sell"),
        ("packet_id", "packet-trade"),
    ),
)
def test_unsafe_public_values_are_rejected(field_name: str, field_value: str) -> None:
    values = {
        "packet_id": "packet-safe",
        "source_id": "source-safe",
        "source_kind": "official",
        "last_checked_at": GENERATED_AT,
        "expected_update_at": None,
        "source_priority_score": d("1.000000"),
    }
    values[field_name] = field_value

    with pytest.raises(ValueError, match="unsafe public value"):
        api().ResearchPacketOfficialUpdateWatchQueueV2Input(**values)


def test_unsafe_public_payload_keys_are_rejected() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public key"):
        module.research_packet_official_update_watch_queue_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_hint": "redacted",
            },
        )


def test_module_has_no_unsafe_surfaces() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/research_packet_official_update_watch_queue_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )

    assert imported_roots.isdisjoint(
        {
            "asyncio",
            "httpx",
            "pathlib",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        },
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "print", "__import__"}
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)


def _has_no_float_values(value: Any) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, dict):
        return all(_has_no_float_values(item) for item in value.values())
    if isinstance(value, list):
        return all(_has_no_float_values(item) for item in value)
    return True
