from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=1)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_football_signal_memory_quality_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_domain_football_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_input(team_label: str, memory_context: str, **overrides: object):
    module = api()
    values = {
        "team_label": team_label,
        "memory_context": memory_context,
        "team_memory_count": d("1"),
        "injury_memory_count": d("1"),
        "weather_memory_count": d("1"),
        "schedule_memory_count": d("1"),
        "team_memory_age_seconds": d("3600.000000"),
        "injury_memory_age_seconds": d("3600.000000"),
        "weather_memory_age_seconds": d("3600.000000"),
        "schedule_memory_age_seconds": d("3600.000000"),
        "conflicting_memory_count": d("0"),
        "forecast_handoff_urgency_score": d("0.100000"),
        "observed_at": OBSERVED_AT,
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchDomainFootballSignalMemoryQualityInput(**values)


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_football_signal_memory_quality_report(
        items,
        config=cfg or module.ResearchDomainFootballSignalMemoryQualityConfig(),
        generated_at=generated_at,
    )


def test_scores_missing_stale_and_conflicting_team_memory_before_handoff() -> None:
    module = api()
    blocked = memory_input(
        "football-team-alpha",
        "forecast-handoff",
        injury_memory_count=d("0"),
        weather_memory_count=d("0"),
        team_memory_age_seconds=d("100000.000000"),
        injury_memory_age_seconds=d("0.000000"),
        weather_memory_age_seconds=d("0.000000"),
        schedule_memory_age_seconds=d("700000.000000"),
        conflicting_memory_count=d("2"),
        forecast_handoff_urgency_score=d("0.900000"),
    )
    watched = memory_input(
        "football-team-beta",
        "forecast-handoff",
        injury_memory_age_seconds=d("100000.000000"),
        conflicting_memory_count=d("1"),
        forecast_handoff_urgency_score=d("0.400000"),
    )
    passing = memory_input("football-team-gamma", "forecast-handoff")

    quality = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        memory_input(
            "football-team-alpha",
            "forecast-handoff",
            injury_memory_count=d("0"),
            weather_memory_count=d("0"),
            team_memory_age_seconds=d("100000.000000"),
            injury_memory_age_seconds=d("0.000000"),
            weather_memory_age_seconds=d("0.000000"),
            schedule_memory_age_seconds=d("700000.000000"),
            conflicting_memory_count=d("1"),
            forecast_handoff_urgency_score=d("0.900000"),
        ),
    )

    assert type(quality) is module.ResearchDomainFootballSignalMemoryQualityReport
    assert is_dataclass(quality)
    assert quality.status == "block"
    assert quality.input_count == d("3")
    assert quality.row_count == d("3")
    assert quality.team_count == d("3")
    assert quality.pass_count == d("1")
    assert quality.watch_count == d("1")
    assert quality.block_count == d("1")
    assert quality.missing_memory_lane_total == d("2")
    assert quality.stale_memory_lane_total == d("3")
    assert quality.conflicting_memory_total == d("3")
    assert quality.forecast_handoff_ready_count == d("1")
    assert quality.average_signal_memory_quality_score == d("0.570833")
    assert quality.reason_codes == (
        "team_memory_stale_watch",
        "injury_memory_missing",
        "injury_memory_stale_watch",
        "weather_memory_missing",
        "schedule_memory_stale_block",
        "memory_conflicts_block",
        "memory_conflicts_watch",
        "forecast_handoff_urgency_block",
        "football_signal_memory_quality_block",
        "football_signal_memory_quality_watch",
    )
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True

    assert tuple(row.row_status for row in quality.rows) == ("block", "watch", "pass")
    assert quality.rows[0] == module.ResearchDomainFootballSignalMemoryQualityRow(
        team_label="football-team-alpha",
        memory_context="forecast-handoff",
        missing_memory_lane_count=d("2"),
        stale_memory_lane_count=d("2"),
        conflicting_memory_count=d("2"),
        team_memory_age_seconds=d("100000.000000"),
        injury_memory_age_seconds=d("0.000000"),
        weather_memory_age_seconds=d("0.000000"),
        schedule_memory_age_seconds=d("700000.000000"),
        memory_coverage_ratio=d("0.500000"),
        memory_freshness_ratio=d("0.000000"),
        non_conflict_score=d("0.000000"),
        forecast_handoff_urgency_score=d("0.900000"),
        signal_memory_quality_score=d("0.150000"),
        row_status="block",
        observed_at=OBSERVED_AT,
        reason_codes=(
            "team_memory_stale_watch",
            "injury_memory_missing",
            "weather_memory_missing",
            "schedule_memory_stale_block",
            "memory_conflicts_block",
            "forecast_handoff_urgency_block",
            "football_signal_memory_quality_block",
        ),
    )
    assert quality.rows[1].signal_memory_quality_score == d("0.587500")
    assert quality.rows[1].reason_codes == (
        "injury_memory_stale_watch",
        "memory_conflicts_watch",
        "football_signal_memory_quality_watch",
    )
    assert quality.rows[2].signal_memory_quality_score == d("0.975000")
    assert quality.rows[2].reason_codes == ("football_signal_memory_quality_pass",)

    payload = module.research_domain_football_signal_memory_quality_report_payload(quality)
    assert payload == quality.payload
    assert payload["rows"][0]["signal_memory_quality_score"] == "0.150000"
    assert payload["rows"][0]["schedule_memory_age_seconds"] == "700000.000000"
    assert payload["derived_validation_digest"] == quality.derived_validation_digest
    assert len(quality.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in quality.derived_validation_digest)
    assert quality.derived_validation_digest == rebuilt.derived_validation_digest
    assert quality.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_input_blocks_without_raw_public_identifiers() -> None:
    quality = report()

    assert quality.status == "block"
    assert quality.input_count == d("0")
    assert quality.row_count == d("0")
    assert quality.pass_count == d("0")
    assert quality.watch_count == d("0")
    assert quality.block_count == d("0")
    assert quality.average_signal_memory_quality_score == d("0.000000")
    assert quality.reason_codes == ("no_football_signal_memory_inputs",)
    assert quality.rows == ()

    payload_text = repr(quality.payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "recommend",
        "sizing",
    ):
        assert forbidden not in payload_text


def test_report_is_frozen_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    quality = report(memory_input("football-team-gamma", "forecast-handoff"))
    payload = quality.payload

    assert module.FOOTBALL_SIGNAL_MEMORY_QUALITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_FOOTBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
        "FOOTBALL_SIGNAL_MEMORY_QUALITY_STATUSES",
        "FOOTBALL_SIGNAL_MEMORY_QUALITY_REASON_CODES",
        "ResearchDomainFootballSignalMemoryQualityConfig",
        "ResearchDomainFootballSignalMemoryQualityInput",
        "ResearchDomainFootballSignalMemoryQualityReport",
        "ResearchDomainFootballSignalMemoryQualityRow",
        "build_research_domain_football_signal_memory_quality_report",
        "research_domain_football_signal_memory_quality_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        quality.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="team_memory_count must be a Decimal"):
        memory_input("football-team-gamma", "forecast-handoff", team_memory_count=1)
    with pytest.raises(ValueError, match="team_memory_count must be a whole Decimal"):
        memory_input("football-team-gamma", "forecast-handoff", team_memory_count=d("1.5"))
    with pytest.raises(ValueError, match="forecast_handoff_urgency_score must be a Decimal"):
        memory_input(
            "football-team-gamma",
            "forecast-handoff",
            forecast_handoff_urgency_score=_DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(
            "football-team-gamma",
            "forecast-handoff",
            observed_at=datetime(2026, 7, 8, 11, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(
            "football-team-gamma",
            "forecast-handoff",
            observed_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_label"):
        memory_input(_StringSubclass("football-team-gamma"), "forecast-handoff")
    with pytest.raises(ValueError, match="public-safe"):
        memory_input("market_slug", "forecast-handoff")
    with pytest.raises(ValueError, match="public-safe"):
        memory_input("football-team-gamma", "source_text")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        memory_input("football-team-gamma", "forecast-handoff", redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            memory_input(
                "football-team-gamma",
                "forecast-handoff",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchDomainFootballSignalMemoryQualityConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_football_signal_memory_quality_report_payload(
            {**payload, "pass_count": "2"},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.research_domain_football_signal_memory_quality_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_domain_football_signal_memory_quality_report_payload(
            {**payload, "input_count": 1},
        )
    assert (
        report(
            memory_input("football-team-gamma", "forecast-handoff"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )

    _assert_public_numeric_values_are_decimal(quality)
    _assert_no_floats(payload)


def test_module_scope_has_no_external_or_decision_action_surface() -> None:
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
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _assert_public_numeric_values_are_decimal(getattr(value, field_name))
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)
