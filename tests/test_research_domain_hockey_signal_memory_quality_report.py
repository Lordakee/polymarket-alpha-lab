from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_hockey_signal_memory_quality_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_domain_hockey_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_DOMAIN_HOCKEY_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
        ),
        "watch_memory_age_seconds": d("21600.000000"),
        "block_memory_age_seconds": d("86400.000000"),
        "watch_missing_memory_item_count": d("1"),
        "block_missing_memory_item_count": d("2"),
        "watch_stale_memory_item_count": d("1"),
        "block_stale_memory_item_count": d("2"),
        "watch_conflicting_memory_item_count": d("1"),
        "block_conflicting_memory_item_count": d("2"),
        "watch_min_quality_score": d("0.850000"),
        "block_min_quality_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchDomainHockeySignalMemoryQualityConfig(**values)


def memory_input(memory_kind: str, **overrides: object):
    module = api()
    values = {
        "event_label": "nhl_event_group",
        "team_label": "home_team",
        "memory_kind": memory_kind,
        "latest_memory_at": GENERATED_AT - timedelta(hours=1),
        "expected_memory_item_count": d("2"),
        "available_memory_item_count": d("2"),
        "stale_memory_item_count": d("0"),
        "conflicting_memory_item_count": d("0"),
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchDomainHockeySignalMemoryQualityInput(**values)


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_domain_hockey_signal_memory_quality_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_hockey_memory_quality_identifies_goalie_injury_schedule_travel_and_form_gaps() -> None:
    module = api()
    quality = report(
        memory_input(
            "injury",
            expected_memory_item_count=d("2"),
            available_memory_item_count=d("2"),
            conflicting_memory_item_count=d("1"),
        ),
        memory_input(
            "schedule",
            latest_memory_at=GENERATED_AT - timedelta(hours=36),
            expected_memory_item_count=d("1"),
            available_memory_item_count=d("1"),
            stale_memory_item_count=d("1"),
        ),
        memory_input(
            "travel",
            latest_memory_at=GENERATED_AT - timedelta(hours=8),
            expected_memory_item_count=d("2"),
            available_memory_item_count=d("1"),
            stale_memory_item_count=d("1"),
        ),
        memory_input(
            "team_form",
            expected_memory_item_count=d("3"),
            available_memory_item_count=d("3"),
        ),
    )
    rebuilt = report(
        memory_input("team_form", expected_memory_item_count=d("3"), available_memory_item_count=d("3")),
        memory_input("schedule", latest_memory_at=GENERATED_AT - timedelta(hours=36), expected_memory_item_count=d("1"), available_memory_item_count=d("1"), stale_memory_item_count=d("1")),
        memory_input("travel", latest_memory_at=GENERATED_AT - timedelta(hours=8), expected_memory_item_count=d("2"), available_memory_item_count=d("1"), stale_memory_item_count=d("1")),
        memory_input("injury", expected_memory_item_count=d("2"), available_memory_item_count=d("2"), conflicting_memory_item_count=d("1")),
    )

    assert type(quality) is module.ResearchDomainHockeySignalMemoryQualityReport
    assert is_dataclass(quality)
    assert quality.generated_at == GENERATED_AT
    assert quality.config_version == "research-domain-hockey-signal-memory-quality-report-v0"
    assert quality.event_team_count == d("1")
    assert quality.row_count == d("5")
    assert quality.required_memory_kind_count == d("5")
    assert quality.pass_count == d("1")
    assert quality.watch_count == d("2")
    assert quality.block_count == d("2")
    assert quality.missing_kind_count == d("1")
    assert quality.stale_kind_count == d("2")
    assert quality.conflicting_kind_count == d("1")
    assert quality.missing_memory_item_total == d("2")
    assert quality.stale_memory_item_total == d("2")
    assert quality.conflicting_memory_item_total == d("1")
    assert quality.max_memory_age_seconds == d("129600.000000")
    assert quality.min_memory_quality_score == d("0.000000")
    assert quality.status == "block"
    assert quality.reason_codes == (
        "hockey_goalie_memory_missing",
        "hockey_schedule_memory_stale",
        "hockey_signal_memory_age_block",
        "hockey_signal_memory_quality_block",
        "hockey_injury_memory_conflicting",
        "hockey_signal_memory_quality_watch",
        "hockey_travel_memory_missing",
        "hockey_travel_memory_stale",
        "hockey_signal_memory_age_watch",
        "hockey_team_form_memory_clear",
    )
    assert quality.derived_validation_digest == rebuilt.derived_validation_digest
    assert len(quality.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in quality.derived_validation_digest)
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True

    assert tuple(row.status for row in quality.rows) == (
        "block",
        "block",
        "watch",
        "watch",
        "pass",
    )
    goalie, schedule, injury, travel, team_form = quality.rows
    assert goalie == module.ResearchDomainHockeySignalMemoryQualityRow(
        event_label="nhl_event_group",
        team_label="home_team",
        memory_kind="goalie",
        latest_memory_at=None,
        expected_memory_item_count=d("1"),
        available_memory_item_count=d("0"),
        missing_memory_item_count=d("1"),
        stale_memory_item_count=d("0"),
        conflicting_memory_item_count=d("0"),
        memory_age_seconds=d("86400.000000"),
        completeness_score=d("0.000000"),
        freshness_score=d("0.000000"),
        non_conflict_score=d("0.000000"),
        memory_quality_score=d("0.000000"),
        status="block",
        reason_codes=(
            "hockey_goalie_memory_missing",
            "hockey_signal_memory_quality_block",
        ),
    )
    assert schedule.memory_kind == "schedule"
    assert schedule.memory_age_seconds == d("129600.000000")
    assert schedule.memory_quality_score == d("0.666667")
    assert schedule.reason_codes == (
        "hockey_schedule_memory_stale",
        "hockey_signal_memory_age_block",
        "hockey_signal_memory_quality_block",
    )
    assert injury.memory_kind == "injury"
    assert injury.non_conflict_score == d("0.500000")
    assert injury.memory_quality_score == d("0.819444")
    assert injury.reason_codes == (
        "hockey_injury_memory_conflicting",
        "hockey_signal_memory_quality_watch",
    )
    assert travel.memory_kind == "travel"
    assert travel.completeness_score == d("0.500000")
    assert travel.freshness_score == d("0.666667")
    assert travel.memory_quality_score == d("0.722222")
    assert travel.reason_codes == (
        "hockey_travel_memory_missing",
        "hockey_travel_memory_stale",
        "hockey_signal_memory_age_watch",
        "hockey_signal_memory_quality_watch",
    )
    assert team_form.memory_kind == "team_form"
    assert team_form.memory_quality_score == d("0.986111")
    assert team_form.reason_codes == ("hockey_team_form_memory_clear",)

    reason_counts = {item.reason_code: item.count for item in quality.reason_code_counts}
    assert reason_counts["hockey_goalie_memory_missing"] == d("1")
    assert reason_counts["hockey_signal_memory_quality_watch"] == d("2")


def test_empty_hockey_memory_inputs_block_without_raw_public_surfaces() -> None:
    quality = report()

    assert quality.status == "block"
    assert quality.event_team_count == d("0")
    assert quality.row_count == d("0")
    assert quality.required_memory_kind_count == d("0")
    assert quality.pass_count == d("0")
    assert quality.watch_count == d("0")
    assert quality.block_count == d("0")
    assert quality.missing_kind_count == d("0")
    assert quality.stale_kind_count == d("0")
    assert quality.conflicting_kind_count == d("0")
    assert quality.missing_memory_item_total == d("0")
    assert quality.stale_memory_item_total == d("0")
    assert quality.conflicting_memory_item_total == d("0")
    assert quality.max_memory_age_seconds == d("0.000000")
    assert quality.min_memory_quality_score == d("0.000000")
    assert quality.reason_codes == ("hockey_signal_memory_quality_no_inputs",)
    assert quality.rows == ()

    payload_text = repr(quality.payload).lower()
    for forbidden in _FORBIDDEN_PUBLIC_FRAGMENTS:
        assert forbidden not in payload_text

    populated = report(memory_input("goalie"))
    for value in (quality, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_total", "_score", "_seconds", "_ratio")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_validated() -> None:
    module = api()
    first = report(
        memory_input(
            "injury",
            latest_memory_at=datetime(
                2026,
                7,
                8,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            conflicting_memory_item_count=d("1"),
        ),
        memory_input("goalie"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = report(
        memory_input("goalie"),
        memory_input(
            "injury",
            latest_memory_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            conflicting_memory_item_count=d("1"),
        ),
    )

    payload = module.research_domain_hockey_signal_memory_quality_report_payload(first)
    repeat_payload = module.research_domain_hockey_signal_memory_quality_report_payload(second)
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()

    assert payload == repeat_payload
    assert payload == first.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["row_count"] == "5"
    assert payload["rows"][0]["memory_kind"] == "schedule"
    assert payload["rows"][0]["memory_quality_score"] == "0.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == expected_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_hockey_signal_memory_quality_report_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_hockey_signal_memory_quality_report_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["reason_codes"] = ["wallet"]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_hockey_signal_memory_quality_report_payload(unsafe_value)


def test_hockey_memory_report_is_frozen_validated_and_readonly() -> None:
    module = api()
    quality = report(memory_input("goalie"))

    assert module.HOCKEY_SIGNAL_MEMORY_QUALITY_STATUSES == ("pass", "watch", "block")
    assert module.HOCKEY_SIGNAL_MEMORY_KINDS == (
        "goalie",
        "injury",
        "schedule",
        "travel",
        "team_form",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_HOCKEY_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
        "HOCKEY_SIGNAL_MEMORY_QUALITY_STATUSES",
        "HOCKEY_SIGNAL_MEMORY_KINDS",
        "HOCKEY_SIGNAL_MEMORY_QUALITY_REASON_CODES",
        "ResearchDomainHockeySignalMemoryQualityConfig",
        "ResearchDomainHockeySignalMemoryQualityInput",
        "ResearchDomainHockeySignalMemoryQualityReasonCodeCount",
        "ResearchDomainHockeySignalMemoryQualityReport",
        "ResearchDomainHockeySignalMemoryQualityRow",
        "build_research_domain_hockey_signal_memory_quality_report",
        "research_domain_hockey_signal_memory_quality_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        quality.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="available_memory_item_count must be a Decimal"):
        memory_input("goalie", available_memory_item_count=2)
    with pytest.raises(ValueError, match="expected_memory_item_count must be a whole Decimal"):
        memory_input("goalie", expected_memory_item_count=d("2.500000"))
    with pytest.raises(ValueError, match="watch_min_quality_score must be a Decimal"):
        config(watch_min_quality_score=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="latest_memory_at"):
        memory_input("goalie", latest_memory_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="latest_memory_at"):
        memory_input(
            "goalie",
            latest_memory_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_label"):
        memory_input("goalie", team_label=_StringSubclass("home_team"))
    with pytest.raises(ValueError, match="public-safe"):
        memory_input("goalie", team_label="wallet")
    with pytest.raises(ValueError, match="memory_kind"):
        memory_input("special_teams")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        memory_input("goalie", redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            memory_input(
                "goalie",
                latest_memory_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            module.ResearchDomainHockeySignalMemoryQualityConfig(),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass, watch, or block"):
        replace(quality.rows[0], status="hold")

    assert (
        report(
            memory_input("goalie"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )
    assert_public_numeric_values_are_decimal(quality)
    assert_no_int_or_float_values(quality.payload)


def test_module_scope_has_no_external_or_decision_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }


_FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "url",
    "source",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "auth",
    "recommend",
    "sizing",
    "live",
)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def assert_public_numeric_values_are_decimal(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)
