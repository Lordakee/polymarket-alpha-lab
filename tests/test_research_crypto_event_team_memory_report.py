from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_crypto_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_crypto_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-crypto-event-team-memory-report-test",
        "pass_min_memory_quality_score": d("0.850000"),
        "watch_min_memory_quality_score": d("0.650000"),
        "pass_max_memory_age_seconds": d("86400.000000"),
        "watch_max_memory_age_seconds": d("604800.000000"),
        "pass_min_recent_case_coverage_ratio": d("0.800000"),
        "watch_min_recent_case_coverage_ratio": d("0.550000"),
        "watch_max_unresolved_memory_gap_count": d("1"),
        "block_max_unresolved_memory_gap_count": d("3"),
        "pass_min_screening_support_score": d("0.800000"),
        "watch_min_screening_support_score": d("0.550000"),
    }
    values.update(overrides)
    return module.ResearchCryptoEventTeamMemoryReportConfig(**values)


def memory_signal(**overrides: object):
    module = api()
    values = {
        "crypto_event_label": "protocol_governance",
        "specialist_memory_quality_score": d("0.950000"),
        "latest_memory_age_seconds": d("3600.000000"),
        "recent_case_coverage_ratio": d("0.900000"),
        "unresolved_memory_gap_count": d("0"),
        "screening_support_score": d("0.900000"),
        "screened_case_count": d("6"),
    }
    values.update(overrides)
    return module.ResearchCryptoEventTeamMemorySignal(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_crypto_event_team_memory_report(
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
        "condition",
        "slug",
        "source",
        "url",
        "http",
        "market",
        "wallet",
        "order",
        "trade",
        "live",
        "database",
        "network",
        "raw",
        "text",
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


def test_crypto_event_team_memory_report_scores_specialist_quality_and_recency() -> None:
    report = build_report(
        memory_signal(
            crypto_event_label="bridge_security",
            specialist_memory_quality_score=d("0.400000"),
            latest_memory_age_seconds=d("700000.000000"),
            recent_case_coverage_ratio=d("0.300000"),
            unresolved_memory_gap_count=d("4"),
            screening_support_score=d("0.400000"),
            screened_case_count=d("1"),
        ),
        memory_signal(
            crypto_event_label="etf_flows",
            specialist_memory_quality_score=d("0.700000"),
            latest_memory_age_seconds=d("90000.000000"),
            recent_case_coverage_ratio=d("0.700000"),
            unresolved_memory_gap_count=d("1"),
            screening_support_score=d("0.600000"),
            screened_case_count=d("4"),
        ),
        memory_signal(),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-crypto-event-team-memory-report-test"
    assert report.report_status == "block"
    assert report.memory_quality_status == "block"
    assert report.memory_recency_status == "block"
    assert report.case_coverage_status == "block"
    assert report.memory_gap_status == "block"
    assert report.screening_support_status == "block"
    assert report.memory_signal_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_memory_quality_score == d("0.683333")
    assert report.average_recent_case_coverage_ratio == d("0.633333")
    assert report.unresolved_memory_gap_count == d("5")
    assert report.max_memory_age_seconds == d("700000.000000")
    assert report.screened_case_count == d("11")
    assert report.reason_codes == (
        "crypto_event_team_memory_report_block",
        "memory_quality_block",
        "memory_recency_block",
        "case_coverage_block",
        "memory_gap_block",
        "screening_support_block",
        "memory_quality_watch",
        "memory_recency_watch",
        "case_coverage_watch",
        "memory_gap_watch",
        "screening_support_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.memory_status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.crypto_event_label == "bridge_security"
    assert blocked.reason_codes == (
        "memory_quality_block",
        "memory_recency_block",
        "case_coverage_block",
        "memory_gap_block",
        "screening_support_block",
    )
    assert watched.crypto_event_label == "etf_flows"
    assert watched.reason_codes == (
        "memory_quality_watch",
        "memory_recency_watch",
        "case_coverage_watch",
        "memory_gap_watch",
        "screening_support_watch",
    )
    assert passed.reason_codes == ("crypto_event_team_memory_ready",)


def test_empty_inputs_block_and_payload_stays_deterministic_decimal_only_and_safe() -> None:
    module = api()
    empty_report = build_report()

    assert empty_report.report_status == "block"
    assert empty_report.memory_quality_status == "block"
    assert empty_report.memory_recency_status == "block"
    assert empty_report.case_coverage_status == "block"
    assert empty_report.memory_gap_status == "block"
    assert empty_report.screening_support_status == "block"
    assert empty_report.memory_signal_count == d("0")
    assert empty_report.average_memory_quality_score == d("0.000000")
    assert empty_report.reason_codes == ("crypto_event_team_memory_report_no_inputs",)
    assert empty_report.rows == ()
    assert empty_report.reason_code_counts == ()

    signals = (
        memory_signal(
            crypto_event_label="etf_flows",
            specialist_memory_quality_score=d("0.700000"),
            latest_memory_age_seconds=d("90000.000000"),
            recent_case_coverage_ratio=d("0.700000"),
            unresolved_memory_gap_count=d("1"),
            screening_support_score=d("0.600000"),
            screened_case_count=d("4"),
        ),
        memory_signal(),
    )
    first = build_report(*signals)
    second = build_report(*reversed(signals))

    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.research_crypto_event_team_memory_report_payload(first)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["memory_signal_count"] == "2"
    assert payload["average_memory_quality_score"] == "0.825000"
    assert payload["max_memory_age_seconds"] == "90000.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    assert_payload_omits_raw_surfaces(payload)
    assert json.dumps(payload, sort_keys=True, separators=(",", ":"))

    tampered = dict(payload)
    tampered["average_memory_quality_score"] = "0.800000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_crypto_event_team_memory_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_crypto_event_team_memory_report_payload(
            {**payload, "raw_event_identifier": "crypto-market-123"},
        )


def test_dataclasses_are_frozen_decimal_only_hard_flagged_and_status_limited() -> None:
    module = api()
    sample_config = config()
    sample_signal = memory_signal()
    sample_report = build_report(sample_signal)

    for item in (sample_config, sample_signal, sample_report, *sample_report.rows):
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
    with pytest.raises(ValueError, match="finite Decimal"):
        memory_signal(specialist_memory_quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory_signal(), generated_at=_DatetimeSubclass(2026, 7, 8))
    with pytest.raises(ValueError, match="status"):
        module.ResearchCryptoEventTeamMemoryRow(
            crypto_event_label="protocol_governance",
            memory_status="clear",
            specialist_memory_quality_score=d("0.900000"),
            latest_memory_age_seconds=d("3600.000000"),
            recent_case_coverage_ratio=d("0.900000"),
            unresolved_memory_gap_count=d("0"),
            screening_support_score=d("0.900000"),
            screened_case_count=d("6"),
            reason_codes=("crypto_event_team_memory_ready",),
        )


def test_module_source_has_no_db_network_wallet_order_or_trading_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
