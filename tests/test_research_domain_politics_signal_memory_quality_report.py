from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_politics_signal_memory_quality_report.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_domain_politics_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_input(team_label: str, signal_family: str, **overrides: object):
    module = api()
    values = {
        "team_label": team_label,
        "signal_family": signal_family,
        "latest_memory_at": GENERATED_AT - timedelta(hours=6),
        "expected_memory_count": d("3"),
        "available_memory_count": d("3"),
        "conflicting_memory_count": d("0"),
        "stale_memory_count": d("0"),
        "coverage_score": d("1.000000"),
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchDomainPoliticsSignalMemoryQualityInput(**values)


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_domain_politics_signal_memory_quality_report(
        items,
        config=cfg or module.ResearchDomainPoliticsSignalMemoryQualityConfig(),
        generated_at=generated_at,
    )


def test_politics_signal_memory_quality_flags_stale_conflicting_and_missing_inputs() -> None:
    module = api()
    blocked = memory_input(
        "policy-desk",
        "election-calendar",
        latest_memory_at=GENERATED_AT - timedelta(days=45),
        expected_memory_count=d("4"),
        available_memory_count=d("1"),
        conflicting_memory_count=d("1"),
        stale_memory_count=d("2"),
        coverage_score=d("0.250000"),
    )
    watched = memory_input(
        "campaign-desk",
        "candidate-positioning",
        latest_memory_at=GENERATED_AT - timedelta(days=10),
        expected_memory_count=d("3"),
        available_memory_count=d("2"),
        stale_memory_count=d("1"),
        coverage_score=d("0.666667"),
    )
    passing = memory_input("governance-desk", "legislative-whip")

    quality = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        memory_input(
            "policy-desk",
            "election-calendar",
            latest_memory_at=GENERATED_AT - timedelta(days=45),
            expected_memory_count=d("4"),
            available_memory_count=d("1"),
            conflicting_memory_count=d("1"),
            stale_memory_count=d("1"),
            coverage_score=d("0.250000"),
        ),
    )

    assert type(quality) is module.ResearchDomainPoliticsSignalMemoryQualityReport
    assert is_dataclass(quality)
    assert quality.status == "block"
    assert quality.input_count == d("3")
    assert quality.row_count == d("3")
    assert quality.team_count == d("3")
    assert quality.signal_family_count == d("3")
    assert quality.pass_count == d("1")
    assert quality.watch_count == d("1")
    assert quality.block_count == d("1")
    assert quality.stale_input_count == d("2")
    assert quality.conflicting_input_count == d("1")
    assert quality.missing_input_count == d("2")
    assert quality.average_memory_quality_score == d("0.625000")
    assert quality.reason_codes == (
        "politics_signal_memory_conflicting_inputs",
        "politics_signal_memory_missing_inputs",
        "politics_signal_memory_stale_inputs",
        "politics_signal_memory_watch_coverage",
        "politics_signal_memory_watch_recency",
        "politics_signal_memory_quality_block",
        "politics_signal_memory_quality_watch",
    )
    assert quality.paper_only is True
    assert quality.report_only is True
    assert quality.readonly is True

    assert tuple(row.row_status for row in quality.rows) == ("block", "watch", "pass")
    assert quality.rows[0] == module.ResearchDomainPoliticsSignalMemoryQualityRow(
        team_label="policy-desk",
        signal_family="election-calendar",
        expected_memory_count=d("4"),
        available_memory_count=d("1"),
        missing_memory_count=d("3"),
        conflicting_memory_count=d("1"),
        stale_memory_count=d("2"),
        memory_age_seconds=d("3888000.000000"),
        freshness_score=d("0.000000"),
        coverage_score=d("0.250000"),
        non_conflict_score=d("0.000000"),
        completeness_score=d("0.250000"),
        memory_quality_score=d("0.125000"),
        row_status="block",
        reason_codes=(
            "politics_signal_memory_conflicting_inputs",
            "politics_signal_memory_missing_inputs",
            "politics_signal_memory_stale_inputs",
            "politics_signal_memory_quality_block",
        ),
    )

    payload = module.research_domain_politics_signal_memory_quality_report_payload(
        quality,
    )
    assert payload == quality.payload
    assert payload["rows"][0]["memory_quality_score"] == "0.125000"
    assert payload["rows"][0]["memory_age_seconds"] == "3888000.000000"
    assert payload["derived_validation_digest"] == quality.derived_validation_digest
    assert len(quality.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in quality.derived_validation_digest)
    assert quality.derived_validation_digest == rebuilt.derived_validation_digest
    assert quality.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_politics_memory_inputs_block_without_raw_public_surfaces() -> None:
    quality = report()

    assert quality.status == "block"
    assert quality.input_count == d("0")
    assert quality.row_count == d("0")
    assert quality.pass_count == d("0")
    assert quality.watch_count == d("0")
    assert quality.block_count == d("0")
    assert quality.stale_input_count == d("0")
    assert quality.conflicting_input_count == d("0")
    assert quality.missing_input_count == d("0")
    assert quality.average_memory_quality_score == d("0.000000")
    assert quality.reason_codes == ("no_politics_signal_memory_quality_inputs",)
    assert quality.rows == ()

    payload_text = repr(quality.payload).lower()
    for forbidden in _FORBIDDEN_PUBLIC_FRAGMENTS:
        assert forbidden not in payload_text


def test_politics_memory_report_is_frozen_decimal_only_public_safe_and_readonly() -> None:
    module = api()
    quality = report(memory_input("governance-desk", "legislative-whip"))

    assert module.POLITICS_SIGNAL_MEMORY_QUALITY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_POLITICS_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
        "POLITICS_SIGNAL_MEMORY_QUALITY_STATUSES",
        "POLITICS_SIGNAL_MEMORY_QUALITY_REASON_CODES",
        "ResearchDomainPoliticsSignalMemoryQualityConfig",
        "ResearchDomainPoliticsSignalMemoryQualityInput",
        "ResearchDomainPoliticsSignalMemoryQualityReport",
        "ResearchDomainPoliticsSignalMemoryQualityRow",
        "build_research_domain_politics_signal_memory_quality_report",
        "research_domain_politics_signal_memory_quality_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        quality.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="available_memory_count must be a Decimal"):
        memory_input(
            "governance-desk",
            "legislative-whip",
            available_memory_count=3,
        )
    with pytest.raises(ValueError, match="expected_memory_count must be a whole Decimal"):
        memory_input(
            "governance-desk",
            "legislative-whip",
            expected_memory_count=d("3.500000"),
        )
    with pytest.raises(ValueError, match="coverage_score must be a Decimal"):
        memory_input(
            "governance-desk",
            "legislative-whip",
            coverage_score=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="latest_memory_at"):
        memory_input(
            "governance-desk",
            "legislative-whip",
            latest_memory_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="latest_memory_at"):
        memory_input(
            "governance-desk",
            "legislative-whip",
            latest_memory_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_label"):
        memory_input(_StringSubclass("governance-desk"), "legislative-whip")
    with pytest.raises(ValueError, match="public-safe"):
        memory_input("wallet", "legislative-whip")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        memory_input(
            "governance-desk",
            "legislative-whip",
            redaction_confirmed=False,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            memory_input(
                "governance-desk",
                "legislative-whip",
                latest_memory_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchDomainPoliticsSignalMemoryQualityConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality, derived_validation_digest="0" * 64)
    assert (
        report(
            memory_input("governance-desk", "legislative-whip"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )

    _assert_public_numeric_values_are_decimal(quality)
    _assert_no_floats(quality.payload)


def test_politics_memory_payload_rejects_tampering_and_unsafe_dict_payloads() -> None:
    module = api()
    quality = report(memory_input("governance-desk", "legislative-whip"))
    payload = quality.payload

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_politics_signal_memory_quality_report_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["market_id"] = "abc"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_politics_signal_memory_quality_report_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["reason_codes"] = ["wallet"]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_domain_politics_signal_memory_quality_report_payload(unsafe_value)

    with pytest.raises(ValueError, match="pass, watch, or block"):
        replace(quality.rows[0], row_status="hold")


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
        "forecast",
        "handoff",
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
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


_FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "market_slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "private_token",
    "wallet",
    "auth",
    "order",
    "recommend",
    "sizing",
    "trade",
    "slug",
    "url",
    "token",
)


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
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)
