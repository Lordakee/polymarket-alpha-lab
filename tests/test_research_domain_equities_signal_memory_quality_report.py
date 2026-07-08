from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_equities_signal_memory_quality_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_equities_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    module = api()
    values = {
        "config_version": "research-domain-equities-signal-memory-quality-report-test",
        "pass_min_coverage_ratio": d("0.900000"),
        "watch_min_coverage_ratio": d("0.700000"),
        "pass_max_conflict_ratio": d("0.050000"),
        "block_min_conflict_ratio": d("0.250000"),
        "pass_max_refresh_age_seconds": d("172800.000000"),
        "block_min_refresh_age_seconds": d("604800.000000"),
        "block_min_missing_catalyst_count": d("3.000000"),
    }
    values.update(overrides)
    return module.ResearchDomainEquitiesSignalMemoryQualityConfig(**values)


def memory_input(**overrides: object):
    module = api()
    values = {
        "team_key": "equities.index",
        "index_signal_group": "broad_index",
        "catalyst_family": "macro_calendar",
        "available_catalyst_count": d("10.000000"),
        "required_catalyst_count": d("10.000000"),
        "stale_catalyst_count": d("0.000000"),
        "conflicting_catalyst_count": d("0.000000"),
        "latest_refresh_age_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.ResearchDomainEquitiesSignalMemoryQualityInput(**values)


def build_report(*rows: object, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_equities_signal_memory_quality_report(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (str, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def assert_payload_public_safe(value: object) -> None:
    unsafe_terms = (
        _join_parts("raw_", "candidate"),
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        "slug",
        "question",
        _join_parts("source", "_text"),
        _join_parts("source", "_url"),
        "https://",
        "dsn",
        "table",
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        _join_parts("rec", "ommend"),
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in unsafe_terms), key
            assert_payload_public_safe(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_public_safe(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in unsafe_terms), value


def test_module_file_exists() -> None:
    assert MODULE_PATH.exists()


def test_report_identifies_stale_conflicting_and_missing_index_catalyst_memory() -> None:
    module = api()
    report = build_report(
        memory_input(team_key="equities.pass", catalyst_family="macro_calendar"),
        memory_input(
            team_key="equities.watch",
            catalyst_family="earnings_calendar",
            available_catalyst_count=d("8.000000"),
            required_catalyst_count=d("10.000000"),
            stale_catalyst_count=d("2.000000"),
            conflicting_catalyst_count=d("1.000000"),
            latest_refresh_age_seconds=d("300000.000000"),
        ),
        memory_input(
            team_key="equities.block",
            catalyst_family="central_bank",
            available_catalyst_count=d("4.000000"),
            required_catalyst_count=d("10.000000"),
            stale_catalyst_count=d("4.000000"),
            conflicting_catalyst_count=d("2.000000"),
            latest_refresh_age_seconds=d("800000.000000"),
        ),
    )

    assert isinstance(report, module.ResearchDomainEquitiesSignalMemoryQualityReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-domain-equities-signal-memory-quality-report-test"
    assert report.report_status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.missing_input_count == d("2.000000")
    assert report.conflicting_input_count == d("2.000000")
    assert report.stale_input_count == d("2.000000")
    assert report.total_available_catalyst_count == d("22.000000")
    assert report.total_required_catalyst_count == d("30.000000")
    assert report.total_missing_catalyst_count == d("8.000000")
    assert report.total_conflicting_catalyst_count == d("3.000000")
    assert report.total_stale_catalyst_count == d("6.000000")
    assert report.average_coverage_ratio == d("0.733333")
    assert report.average_conflict_ratio == d("0.208333")
    assert report.max_refresh_age_seconds == d("800000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.team_key for row in report.rows) == (
        "equities.block",
        "equities.watch",
        "equities.pass",
    )

    blocked = report.rows[0]
    assert blocked.public_status == "block"
    assert blocked.coverage_ratio == d("0.400000")
    assert blocked.conflict_ratio == d("0.500000")
    assert blocked.missing_catalyst_count == d("6.000000")
    assert blocked.reason_codes == (
        "research_domain_equities_signal_memory_quality_block_conflicting",
        "research_domain_equities_signal_memory_quality_block_missing",
        "research_domain_equities_signal_memory_quality_block_stale",
    )

    watched = report.rows[1]
    assert watched.public_status == "watch"
    assert watched.coverage_ratio == d("0.800000")
    assert watched.conflict_ratio == d("0.125000")
    assert watched.missing_catalyst_count == d("2.000000")
    assert watched.reason_codes == (
        "research_domain_equities_signal_memory_quality_watch_conflicting",
        "research_domain_equities_signal_memory_quality_watch_missing",
        "research_domain_equities_signal_memory_quality_watch_stale",
    )

    passed = report.rows[2]
    assert passed.public_status == "pass"
    assert passed.reason_codes == (
        "research_domain_equities_signal_memory_quality_pass",
    )
    assert report.reason_codes == tuple(item.reason_code for item in report.reason_code_counts)


def test_empty_report_blocks_before_forecast_handoff() -> None:
    module = api()
    report = build_report()

    assert report.report_status == "block"
    assert report.input_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_domain_equities_signal_memory_quality_no_inputs",
    )
    assert report.reason_code_counts == (
        module.ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount(
            reason_code="research_domain_equities_signal_memory_quality_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_decimal_string_only_and_digest_validated() -> None:
    module = api()
    first = build_report(
        memory_input(
            team_key="equities.watch",
            catalyst_family="earnings_calendar",
            available_catalyst_count=d("8.000000"),
            required_catalyst_count=d("10.000000"),
            stale_catalyst_count=d("2.000000"),
            conflicting_catalyst_count=d("1.000000"),
            latest_refresh_age_seconds=d("300000.000000"),
        ),
        memory_input(team_key="equities.pass", catalyst_family="macro_calendar"),
    )
    second = build_report(
        memory_input(team_key="equities.pass", catalyst_family="macro_calendar"),
        memory_input(
            team_key="equities.watch",
            catalyst_family="earnings_calendar",
            available_catalyst_count=d("8.000000"),
            required_catalyst_count=d("10.000000"),
            stale_catalyst_count=d("2.000000"),
            conflicting_catalyst_count=d("1.000000"),
            latest_refresh_age_seconds=d("300000.000000"),
        ),
    )

    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.research_domain_equities_signal_memory_quality_report_payload(first)
    assert payload == module.research_domain_equities_signal_memory_quality_report_payload(
        second,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00Z"
    assert payload["input_count"] == "2.000000"
    assert payload["average_coverage_ratio"] == "0.900000"
    assert payload["max_refresh_age_seconds"] == "300000.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)
    assert_payload_public_safe(payload)

    digest = module.research_domain_equities_signal_memory_quality_report_digest(first)
    assert digest == {
        "generated_at": "2026-07-08T12:00:00Z",
        "config_version": "research-domain-equities-signal-memory-quality-report-test",
        "report_status": "watch",
        "input_count": "2.000000",
        "pass_count": "1.000000",
        "watch_count": "1.000000",
        "block_count": "0.000000",
        "reason_codes": [
            "research_domain_equities_signal_memory_quality_watch_conflicting",
            "research_domain_equities_signal_memory_quality_watch_missing",
            "research_domain_equities_signal_memory_quality_watch_stale",
            "research_domain_equities_signal_memory_quality_pass",
        ],
        "derived_validation_digest": first.derived_validation_digest,
    }

    tampered = dict(payload)
    tampered["average_coverage_ratio"] = "0.910000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_equities_signal_memory_quality_report_payload(tampered)

    with pytest.raises(ValueError, match="public"):
        module.research_domain_equities_signal_memory_quality_report_payload(
            {**payload, "candidate_id": "abc"},
        )


def test_validates_frozen_dataclasses_decimal_only_statuses_and_hard_flags() -> None:
    module = api()
    sample_config = cfg()
    sample_input = memory_input()
    sample_report = build_report(sample_input)

    for cls in (
        module.ResearchDomainEquitiesSignalMemoryQualityConfig,
        module.ResearchDomainEquitiesSignalMemoryQualityInput,
        module.ResearchDomainEquitiesSignalMemoryQualityReasonCodeCount,
        module.ResearchDomainEquitiesSignalMemoryQualityReport,
        module.ResearchDomainEquitiesSignalMemoryQualityRow,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    for item in (sample_config, sample_input, sample_report, *sample_report.rows):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError, match="Decimal"):
        memory_input(available_catalyst_count=10)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="exactly str"):
        memory_input(team_key=_StringSubclass("equities.index"))
    with pytest.raises(TypeError, match="exactly Decimal"):
        memory_input(conflicting_catalyst_count=_DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="positive"):
        memory_input(required_catalyst_count=d("0.000000"))
    with pytest.raises(ValueError, match="stale_catalyst_count"):
        memory_input(available_catalyst_count=d("1.000000"), stale_catalyst_count=d("2.000000"))
    with pytest.raises(ValueError, match="conflicting_catalyst_count"):
        memory_input(
            available_catalyst_count=d("1.000000"),
            conflicting_catalyst_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="pass_min_coverage_ratio"):
        cfg(pass_min_coverage_ratio=d("0.600000"), watch_min_coverage_ratio=d("0.700000"))
    with pytest.raises(ValueError, match="block_min_conflict_ratio"):
        cfg(pass_max_conflict_ratio=d("0.300000"), block_min_conflict_ratio=d("0.250000"))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        memory_input(readonly=False)
    with pytest.raises(ValueError, match="public_status must be pass, watch, or block"):
        replace(sample_report.rows[0], public_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(sample_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="duplicates"):
        build_report(memory_input(), memory_input())


def test_public_inputs_reject_private_or_actionable_leaks() -> None:
    module = api()
    leak_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        "event_slug",
        "question_text",
        _join_parts("source", "_text"),
        _join_parts("source", "_url"),
        "https://example.test/path",
        "analytics_dsn",
        "memory_table",
        _join_parts("to", "ken", "_abc"),
        _join_parts("wal", "let", "_field"),
        _join_parts("au", "th", "_scope"),
        _join_parts("order", "_ticket"),
        _join_parts("trade", "_ticket"),
        _join_parts("buy", "_signal"),
        _join_parts("sell", "_signal"),
        _join_parts("rec", "ommend", "_path"),
        "position_size",
    )

    for value in leak_values:
        with pytest.raises(ValueError, match="public"):
            memory_input(catalyst_family=value)

    payload = module.research_domain_equities_signal_memory_quality_report_payload(
        build_report(memory_input()),
    )
    public = repr((payload, asdict(build_report(memory_input())))).lower()
    assert_payload_public_safe(payload)
    for token in leak_values:
        assert token.lower() not in public


def test_module_is_pure_report_only_without_io_or_action_surfaces() -> None:
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "asyncio",
        "builtins",
        "httpx",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "cancel",
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)

    forbidden_source_terms = (
        "private_key",
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        "place_order",
        "cancel_order",
        "order_book",
        "trade_client",
        _join_parts("source", "_url"),
        _join_parts("source", "_text"),
        "raw_identifier",
        "position_size",
    )
    lowered = module_source.lower()
    assert not any(term in lowered for term in forbidden_source_terms)
