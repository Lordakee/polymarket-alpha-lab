from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_equity_index_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_equity_index_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-equity-index-event-team-memory-report-test",
        "pass_min_memory_readiness_score": d("0.850000"),
        "watch_min_memory_readiness_score": d("0.600000"),
        "pass_min_calibration_note_coverage_ratio": d("0.800000"),
        "watch_min_calibration_note_coverage_ratio": d("0.550000"),
        "watch_max_unresolved_calibration_note_count": d("1"),
        "block_max_unresolved_calibration_note_count": d("3"),
        "pass_max_evidence_age_seconds": d("86400.000000"),
        "watch_max_evidence_age_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return module.ResearchEquityIndexEventTeamMemoryReportConfig(**values)


def memory_signal(**overrides: object):
    module = api()
    values = {
        "memory_readiness_score": d("0.950000"),
        "calibration_note_coverage_ratio": d("0.900000"),
        "unresolved_calibration_note_count": d("0"),
        "latest_evidence_age_seconds": d("3600.000000"),
        "evidence_packet_count": d("4"),
    }
    values.update(overrides)
    return module.ResearchEquityIndexEventTeamMemorySignal(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_equity_index_event_team_memory_report(
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


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if type(value) in (str, datetime):
        return
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


def assert_payload_omits_raw_surfaces(value: object) -> None:
    unsafe_fragments = (
        "identifier",
        "source_text",
        "source_url",
        "url",
        "http",
        "order",
        "trade",
        "wallet",
        "auth",
        "database",
        "network",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in unsafe_fragments), key
            assert_payload_omits_raw_surfaces(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_omits_raw_surfaces(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in unsafe_fragments), value


def test_equity_index_event_team_memory_report_summarizes_aggregate_readiness() -> None:
    report = build_report(
        memory_signal(),
        memory_signal(
            memory_readiness_score=d("0.700000"),
            calibration_note_coverage_ratio=d("0.700000"),
            unresolved_calibration_note_count=d("1"),
            latest_evidence_age_seconds=d("90000.000000"),
            evidence_packet_count=d("5"),
        ),
        memory_signal(
            memory_readiness_score=d("0.400000"),
            calibration_note_coverage_ratio=d("0.500000"),
            unresolved_calibration_note_count=d("1"),
            latest_evidence_age_seconds=d("72000.000000"),
            evidence_packet_count=d("3"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-equity-index-event-team-memory-report-test"
    assert report.report_status == "watch"
    assert report.memory_readiness_status == "watch"
    assert report.calibration_notes_status == "watch"
    assert report.evidence_recency_status == "watch"
    assert report.memory_signal_count == d("3")
    assert report.average_memory_readiness_score == d("0.683333")
    assert report.average_calibration_note_coverage_ratio == d("0.700000")
    assert report.unresolved_calibration_note_count == d("2")
    assert report.max_evidence_age_seconds == d("90000.000000")
    assert report.evidence_packet_count == d("12")
    assert report.reason_codes == (
        "equity_index_event_team_memory_report_watch",
        "memory_readiness_watch",
        "calibration_notes_watch",
        "evidence_recency_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_empty_report_blocks_without_memory_or_evidence() -> None:
    report = build_report()

    assert report.report_status == "block"
    assert report.memory_readiness_status == "block"
    assert report.calibration_notes_status == "block"
    assert report.evidence_recency_status == "block"
    assert report.memory_signal_count == d("0")
    assert report.average_memory_readiness_score == d("0.000000")
    assert report.average_calibration_note_coverage_ratio == d("0.000000")
    assert report.unresolved_calibration_note_count == d("0")
    assert report.max_evidence_age_seconds == d("0.000000")
    assert report.evidence_packet_count == d("0")
    assert report.reason_codes == (
        "equity_index_event_team_memory_report_block",
        "memory_readiness_block",
        "calibration_notes_block",
        "evidence_recency_block",
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    signals = (
        memory_signal(
            memory_readiness_score=d("0.700000"),
            calibration_note_coverage_ratio=d("0.700000"),
            unresolved_calibration_note_count=d("1"),
            latest_evidence_age_seconds=d("90000.000000"),
            evidence_packet_count=d("5"),
        ),
        memory_signal(),
    )
    first = build_report(*signals)
    second = build_report(*reversed(signals))

    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.research_equity_index_event_team_memory_report_payload(first)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["memory_signal_count"] == "2"
    assert payload["average_memory_readiness_score"] == "0.825000"
    assert payload["max_evidence_age_seconds"] == "90000.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    assert_payload_omits_raw_surfaces(payload)

    tampered = dict(payload)
    tampered["average_memory_readiness_score"] = "0.800000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_equity_index_event_team_memory_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_equity_index_event_team_memory_report_payload(
            {**payload, "raw_identifier": "SPX-event-123"},
        )


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_signal = memory_signal()
    sample_report = build_report(sample_signal)

    for item in (sample_config, sample_signal, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        memory_signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        memory_signal(readonly=False)


def test_validation_rejects_non_decimal_values_ranges_and_threshold_inversions() -> None:
    module = api()

    with pytest.raises(ValueError, match="memory_readiness_score must be exactly Decimal"):
        memory_signal(memory_readiness_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="calibration_note_coverage_ratio must be <= 1"):
        memory_signal(calibration_note_coverage_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="latest_evidence_age_seconds must be finite"):
        memory_signal(latest_evidence_age_seconds=Decimal("NaN"))
    with pytest.raises(ValueError, match="evidence_packet_count must be integral"):
        memory_signal(evidence_packet_count=d("2.5"))
    with pytest.raises(ValueError, match="pass_min_memory_readiness_score must not be below"):
        module.ResearchEquityIndexEventTeamMemoryReportConfig(
            pass_min_memory_readiness_score=d("0.500000"),
            watch_min_memory_readiness_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="watch_max_evidence_age_seconds must not be below"):
        module.ResearchEquityIndexEventTeamMemoryReportConfig(
            pass_max_evidence_age_seconds=d("604800.000000"),
            watch_max_evidence_age_seconds=d("86400.000000"),
        )


def test_report_rejects_digest_tampering_and_non_report_statuses() -> None:
    module = api()
    report = build_report(memory_signal())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report_status must be pass, watch, or block"):
        replace(
            report,
            report_status="blocked",
            derived_validation_digest=report.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="memory signals must not contain duplicates"):
        build_report(memory_signal(), memory_signal())

    payload = module.research_equity_index_event_team_memory_report_payload(report)
    payload.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_equity_index_event_team_memory_report_payload(payload)


def test_module_stays_pure_report_only_without_db_network_or_trading_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    assert not {
        "asyncio",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    } & imports

    source = MODULE_PATH.read_text().lower()
    forbidden_fragments = (
        "private_key",
        "wallet",
        "place_order",
        "cancel_order",
        "order_book",
        "trade_client",
        "source_url",
        "source_text",
        "raw_identifier",
    )
    assert not any(fragment in source for fragment in forbidden_fragments)
