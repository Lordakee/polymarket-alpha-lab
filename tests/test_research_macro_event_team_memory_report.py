from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=3)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_macro_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_macro_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-macro-event-team-memory-report-v0",
        "watch_min_specialist_count": d("2"),
        "block_min_specialist_count": d("1"),
        "watch_min_playbook_count": d("2"),
        "block_min_playbook_count": d("1"),
        "watch_min_calibration_sample_count": d("30"),
        "block_min_calibration_sample_count": d("10"),
        "watch_stale_memory_hours": d("72.000000"),
        "block_stale_memory_hours": d("240.000000"),
        "watch_unresolved_evidence_gap_ratio": d("0.150000"),
        "block_unresolved_evidence_gap_ratio": d("0.350000"),
        "watch_min_evidence_family_coverage_ratio": d("0.700000"),
        "block_min_evidence_family_coverage_ratio": d("0.450000"),
        "watch_min_analog_case_count": d("3"),
        "block_min_analog_case_count": d("1"),
    }
    values.update(overrides)
    return report.ResearchMacroEventTeamMemoryConfig(**values)


def memory_input(**overrides: object):
    report = api()
    values = {
        "team_key": "macro_rates",
        "macro_domain": "rates",
        "specialist_count": d("3"),
        "playbook_count": d("3"),
        "calibration_sample_count": d("42"),
        "stale_memory_hours": d("24.000000"),
        "unresolved_evidence_gap_ratio": d("0.050000"),
        "evidence_family_coverage_ratio": d("0.850000"),
        "analog_case_count": d("4"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return report.ResearchMacroEventTeamMemoryInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_macro_event_team_memory_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
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


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_macro_event_team_memory_scores_pass_watch_and_block_readiness() -> None:
    report = build_report(
        memory_input(
            team_key="macro_employment",
            macro_domain="labor",
            specialist_count=d("0"),
            playbook_count=d("0"),
            calibration_sample_count=d("8"),
            stale_memory_hours=d("260.000000"),
            unresolved_evidence_gap_ratio=d("0.400000"),
            evidence_family_coverage_ratio=d("0.300000"),
            analog_case_count=d("0"),
        ),
        memory_input(
            team_key="macro_inflation",
            macro_domain="inflation",
            specialist_count=d("1"),
            playbook_count=d("1"),
            calibration_sample_count=d("20"),
            stale_memory_hours=d("80.000000"),
            unresolved_evidence_gap_ratio=d("0.180000"),
            evidence_family_coverage_ratio=d("0.650000"),
            analog_case_count=d("2"),
        ),
        memory_input(team_key="macro_rates", macro_domain="rates"),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-macro-event-team-memory-report-v0"
    assert report.team_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_macro_event_team_memory_block"
    assert report.reason_codes == (
        "macro_event_team_memory_queue_block",
        "specialist_coverage_block",
        "playbook_coverage_block",
        "calibration_sample_block",
        "memory_staleness_block",
        "evidence_gap_block",
        "evidence_family_coverage_block",
        "analog_case_block",
        "specialist_coverage_watch",
        "playbook_coverage_watch",
        "calibration_sample_watch",
        "memory_staleness_watch",
        "evidence_gap_watch",
        "evidence_family_coverage_watch",
        "analog_case_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.memory_status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.team_key == "macro_employment"
    assert blocked.reason_codes == (
        "specialist_coverage_block",
        "playbook_coverage_block",
        "calibration_sample_block",
        "memory_staleness_block",
        "evidence_gap_block",
        "evidence_family_coverage_block",
        "analog_case_block",
    )
    assert watched.team_key == "macro_inflation"
    assert watched.reason_codes == (
        "specialist_coverage_watch",
        "playbook_coverage_watch",
        "calibration_sample_watch",
        "memory_staleness_watch",
        "evidence_gap_watch",
        "evidence_family_coverage_watch",
        "analog_case_watch",
    )
    assert passed.reason_codes == ("macro_event_team_memory_ready",)

    assert report.min_specialist_count == d("0")
    assert report.min_playbook_count == d("0")
    assert report.min_calibration_sample_count == d("8")
    assert report.max_stale_memory_hours == d("260.000000")
    assert report.max_unresolved_evidence_gap_ratio == d("0.400000")
    assert report.min_evidence_family_coverage_ratio == d("0.300000")
    assert report.min_analog_case_count == d("0")

    assert report.reason_code_counts[0].reason_code == "macro_event_team_memory_ready"
    assert report.reason_code_counts[0].count == d("1")
    assert report.reason_code_counts[0].team_ratio == d("0.333333")


def test_empty_inputs_block_without_raw_event_or_source_identifiers() -> None:
    report = build_report()

    assert report.team_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_macro_event_team_memory_block"
    assert report.reason_codes == ("macro_event_team_memory_no_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()

    populated = build_report(memory_input())
    for value in (report, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_custom_config_changes_watch_thresholds_and_digest() -> None:
    custom = config(
        watch_min_specialist_count=d("4"),
        block_min_specialist_count=d("1"),
        watch_min_playbook_count=d("4"),
        block_min_playbook_count=d("1"),
        watch_min_calibration_sample_count=d("50"),
        block_min_calibration_sample_count=d("5"),
        watch_stale_memory_hours=d("10.000000"),
        block_stale_memory_hours=d("500.000000"),
        watch_unresolved_evidence_gap_ratio=d("0.020000"),
        block_unresolved_evidence_gap_ratio=d("0.900000"),
        watch_min_evidence_family_coverage_ratio=d("0.950000"),
        block_min_evidence_family_coverage_ratio=d("0.100000"),
        watch_min_analog_case_count=d("8"),
        block_min_analog_case_count=d("1"),
    )

    digest = build_report(memory_input(), cfg=custom)

    assert digest.status == "watch"
    assert digest.reason_codes == (
        "macro_event_team_memory_queue_watch",
        "specialist_coverage_watch",
        "playbook_coverage_watch",
        "calibration_sample_watch",
        "memory_staleness_watch",
        "evidence_gap_watch",
        "evidence_family_coverage_watch",
        "analog_case_watch",
    )
    assert digest.rows[0].reason_codes == digest.reason_codes[1:]


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report = api()
    first = build_report(
        memory_input(
            team_key="macro_growth",
            macro_domain="growth",
            specialist_count=d("1"),
            playbook_count=d("1"),
            calibration_sample_count=d("20"),
            stale_memory_hours=d("80.000000"),
            unresolved_evidence_gap_ratio=d("0.180000"),
            evidence_family_coverage_ratio=d("0.650000"),
            analog_case_count=d("2"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        memory_input(team_key="macro_rates", macro_domain="rates"),
        generated_at=datetime(
            2026,
            7,
            8,
            7,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        memory_input(team_key="macro_rates", macro_domain="rates"),
        memory_input(
            team_key="macro_growth",
            macro_domain="growth",
            specialist_count=d("1"),
            playbook_count=d("1"),
            calibration_sample_count=d("20"),
            stale_memory_hours=d("80.000000"),
            unresolved_evidence_gap_ratio=d("0.180000"),
            evidence_family_coverage_ratio=d("0.650000"),
            analog_case_count=d("2"),
            observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
        ),
    )

    payload = report.research_macro_event_team_memory_report_payload(first)
    repeat_payload = report.research_macro_event_team_memory_report_payload(second)

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T14:00:00+00:00"
    assert payload["team_count"] == "2"
    assert payload["rows"][0]["team_key"] == "macro_growth"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_identifier_keys = {
        "event_id",
        "event_slug",
        "market_slug",
        "source_id",
        "source_reference",
        "source_url",
        "raw_event_identifier",
        "raw_source_identifier",
    }
    assert unsafe_identifier_keys.isdisjoint(payload_keys(payload))
    payload_text = repr(payload).lower()
    for token in (
        "cpi-2026-07",
        "fred_series",
        "source_reference",
        "market_slug",
        "wallet",
        "order",
        "trade",
        "live execution",
    ):
        assert token not in payload_text

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_macro_event_team_memory_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    report = api()
    payload = report.research_macro_event_team_memory_report_payload(
        build_report(memory_input(team_key="macro_growth", macro_domain="growth")),
    )

    for key in (
        "event_id",
        "event_slug",
        "market_slug",
        "source_id",
        "source_reference",
        "source_url",
        "wallet_address",
        "order_id",
        "trade_id",
        "live_url",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_macro_event_team_memory_report_payload(unsafe)

    for value in (
        "cpi-2026-07 event id",
        "fred_series source id",
        "market slug",
        "source reference",
        "wallet signer",
        "order route",
        "trade route",
        "live execution",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_macro_event_team_memory_report_payload(unsafe)

    numeric = dict(payload)
    numeric["team_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report.research_macro_event_team_memory_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_macro_event_team_memory_report_payload(downgraded)


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    row = memory_input()

    with pytest.raises(FrozenInstanceError):
        row.specialist_count = d("4")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(specialist_count=3)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(unresolved_evidence_gap_ratio=0.12)
    with pytest.raises(ValueError, match="Decimal"):
        memory_input(stale_memory_hours=_DecimalSubclass("12.000000"))
    with pytest.raises(ValueError, match="integral"):
        memory_input(specialist_count=d("3.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory_input(), generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=datetime(2026, 7, 8, 13, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=_DatetimeSubclass(2026, 7, 8, 13, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_input(), memory_input())
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_input(), cfg=object())


def test_statuses_and_materialized_fields_are_tamper_evident() -> None:
    report = api()
    digest = build_report(memory_input())
    row = digest.rows[0]

    assert report.STATUSES == ("pass", "watch", "block")
    assert "ready" not in report.STATUSES
    assert "blocked" not in report.STATUSES

    with pytest.raises(ValueError, match="memory_status"):
        report.ResearchMacroEventTeamMemoryRow(
            **{
                **row.__dict__,
                "memory_status": "blocked",
            },
        )

    with pytest.raises(ValueError, match="status"):
        report.ResearchMacroEventTeamMemoryReport(
            **{
                **digest.__dict__,
                "status": "watch",
            },
        )

    object.__setattr__(digest.rows[0], "unresolved_evidence_gap_ratio", d("0.990000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_macro_event_team_memory_report_payload(digest)


def test_module_is_report_only_without_io_or_trading_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }
    forbidden_terms = (
        "wallet",
        "broker",
        "signing",
        "order",
        "trade",
        "account",
        "network",
        "database",
        "live",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names

    source = MODULE_PATH.read_text().lower()
    assert not any(term in source for term in forbidden_terms)

    for cls in (
        api().ResearchMacroEventTeamMemoryConfig,
        api().ResearchMacroEventTeamMemoryInput,
        api().ResearchMacroEventTeamMemoryRow,
        api().ResearchMacroEventTeamMemoryReasonCodeCount,
        api().ResearchMacroEventTeamMemoryReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
