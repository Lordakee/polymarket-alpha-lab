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


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
EASTERN = timezone(timedelta(hours=-4))
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_basketball_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_basketball_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object):
    module = api()
    values = {
        "basketball_context_bucket": "playoff_rotation_pressure",
        "memory_cohort_bucket": "late_news_lineup_dependency",
        "specialist_memory_score": d("0.920000"),
        "lineup_memory_coverage_ratio": d("0.900000"),
        "rotation_memory_coverage_ratio": d("0.880000"),
        "fresh_evidence_packet_count": d("6.000000"),
        "total_evidence_packet_count": d("6.000000"),
        "latest_evidence_age_seconds": d("3600.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=15),
        "reason_codes": ("basketball_memory_signal_observed",),
    }
    values.update(overrides)
    return module.ResearchBasketballEventTeamMemorySignal(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_basketball_event_team_memory_report(
        items,
        config=cfg if cfg is not None else module.ResearchBasketballEventTeamMemoryReportConfig(),
        generated_at=generated_at,
    )


def assert_no_numeric_scalars(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload scalar: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_scalars(item)


def assert_no_raw_event_team_game_source_surface(value: Any) -> None:
    forbidden = (
        "event_id",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "game_id",
        "team_id",
        "team_name",
        "source_id",
        "source_url",
        "source_text",
        "raw_text",
        "://",
        "www.",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden), key
            assert_no_raw_event_team_game_source_surface(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_raw_event_team_game_source_surface(item)
    elif type(value) is str:
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden), value


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
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


def test_basketball_event_team_memory_aggregates_readiness_and_evidence_recency() -> None:
    report = build_report(
        signal(),
        signal(
            basketball_context_bucket="regular_season_rotation_watch",
            memory_cohort_bucket="starter_minutes_uncertainty",
            specialist_memory_score=d("0.760000"),
            lineup_memory_coverage_ratio=d("0.720000"),
            rotation_memory_coverage_ratio=d("0.650000"),
            fresh_evidence_packet_count=d("3.000000"),
            total_evidence_packet_count=d("5.000000"),
            latest_evidence_age_seconds=d("30000.000000"),
            observed_at=datetime(2026, 7, 8, 13, 45, tzinfo=EASTERN),
        ),
        signal(
            basketball_context_bucket="injury_cluster_block",
            memory_cohort_bucket="missing_rotation_precedent",
            specialist_memory_score=d("0.400000"),
            lineup_memory_coverage_ratio=d("0.500000"),
            rotation_memory_coverage_ratio=d("0.400000"),
            fresh_evidence_packet_count=d("1.000000"),
            total_evidence_packet_count=d("5.000000"),
            latest_evidence_age_seconds=d("100000.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "block"
    assert report.memory_readiness_status == "block"
    assert report.evidence_recency_status == "block"
    assert report.recommended_next_step == "refresh_basketball_specialist_memory_before_research"
    assert report.signal_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_specialist_memory_score == d("0.693333")
    assert report.average_lineup_memory_coverage_ratio == d("0.706667")
    assert report.average_rotation_memory_coverage_ratio == d("0.643333")
    assert report.fresh_evidence_packet_count == d("10.000000")
    assert report.total_evidence_packet_count == d("16.000000")
    assert report.aggregate_evidence_recency_score == d("0.625000")
    assert report.max_latest_evidence_age_seconds == d("100000.000000")
    assert report.reason_codes == (
        "basketball_event_team_memory_report_block",
        "specialist_memory_score_block",
        "lineup_memory_coverage_block",
        "rotation_memory_coverage_block",
        "evidence_recency_score_block",
        "evidence_age_block",
        "specialist_memory_score_watch",
        "lineup_memory_coverage_watch",
        "rotation_memory_coverage_watch",
        "evidence_recency_score_watch",
        "evidence_age_watch",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple(row.memory_status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.basketball_context_bucket == "injury_cluster_block"
    assert blocked.evidence_recency_score == d("0.200000")
    assert blocked.observed_at == GENERATED_AT - timedelta(minutes=15)
    assert blocked.reason_codes == (
        "basketball_memory_signal_observed",
        "basketball_event_team_memory_status_block",
        "specialist_memory_score_block",
        "lineup_memory_coverage_block",
        "rotation_memory_coverage_block",
        "evidence_recency_score_block",
        "evidence_age_block",
    )
    assert watched.memory_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 8, 17, 45, tzinfo=UTC)
    assert watched.reason_codes == (
        "basketball_memory_signal_observed",
        "basketball_event_team_memory_status_watch",
        "specialist_memory_score_watch",
        "lineup_memory_coverage_watch",
        "rotation_memory_coverage_watch",
        "evidence_recency_score_watch",
        "evidence_age_watch",
    )
    assert passed.reason_codes == (
        "basketball_memory_signal_observed",
        "basketball_event_team_memory_status_pass",
    )


def test_empty_report_blocks_without_raw_team_game_source_or_market_surfaces() -> None:
    report = build_report()

    assert report.report_status == "block"
    assert report.memory_readiness_status == "block"
    assert report.evidence_recency_status == "block"
    assert report.signal_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_specialist_memory_score == d("0.000000")
    assert report.aggregate_evidence_recency_score == d("0.000000")
    assert report.max_latest_evidence_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("basketball_event_team_memory_report_empty",)
    assert report.reason_code_counts == ()

    payload = api().research_basketball_event_team_memory_report_payload(report)
    assert_no_raw_event_team_game_source_surface(payload)


def test_payload_is_deterministic_decimal_stringed_safe_and_digest_checked() -> None:
    module = api()
    signals = (
        signal(),
        signal(
            basketball_context_bucket="regular_season_rotation_watch",
            memory_cohort_bucket="starter_minutes_uncertainty",
            specialist_memory_score=d("0.760000"),
            lineup_memory_coverage_ratio=d("0.720000"),
            rotation_memory_coverage_ratio=d("0.650000"),
            fresh_evidence_packet_count=d("3.000000"),
            total_evidence_packet_count=d("5.000000"),
            latest_evidence_age_seconds=d("30000.000000"),
        ),
    )
    first = build_report(*signals)
    second = build_report(*reversed(signals))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = module.research_basketball_event_team_memory_report_payload(first)
    repeat_payload = module.research_basketball_event_team_memory_report_payload(second)

    assert payload == first.payload
    assert payload == repeat_payload
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["signal_count"] == "2.000000"
    assert payload["aggregate_evidence_recency_score"] == "0.818182"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_numeric_scalars(payload)
    assert_no_raw_event_team_game_source_surface(payload)

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_basketball_event_team_memory_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2.000000"))

    unsafe = dict(payload)
    unsafe["source_url"] = "https://example.test/raw"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_basketball_event_team_memory_report_payload(unsafe)


def test_dataclasses_are_frozen_decimal_only_and_validate_bounds() -> None:
    module = api()
    sample_signal = signal()
    sample_report = build_report(sample_signal)

    dataclass_types = (
        module.ResearchBasketballEventTeamMemoryReportConfig,
        module.ResearchBasketballEventTeamMemorySignal,
        module.ResearchBasketballEventTeamMemoryRow,
        module.ResearchBasketballEventTeamMemoryReasonCodeCount,
        module.ResearchBasketballEventTeamMemoryReport,
    )
    for dataclass_type in dataclass_types:
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        sample_signal.specialist_memory_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sample_report.report_status = "pass"  # type: ignore[misc]

    for item in (module.ResearchBasketballEventTeamMemoryReportConfig(), sample_signal, sample_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="specialist_memory_score must be a Decimal"):
        signal(specialist_memory_score=0.9)
    with pytest.raises(ValueError, match="lineup_memory_coverage_ratio must be a Decimal"):
        signal(lineup_memory_coverage_ratio=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="fresh_evidence_packet_count must be integral"):
        signal(fresh_evidence_packet_count=d("1.500000"))
    with pytest.raises(ValueError, match="fresh_evidence_packet_count must be at most"):
        signal(
            fresh_evidence_packet_count=d("7.000000"),
            total_evidence_packet_count=d("6.000000"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 8, 17, 45))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 8, 17, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(signal(), cfg=object())
    with pytest.raises(ValueError, match="pass_min_specialist_memory_score"):
        module.ResearchBasketballEventTeamMemoryReportConfig(
            pass_min_specialist_memory_score=d("0.500000"),
            watch_min_specialist_memory_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="watch_max_latest_evidence_age_seconds"):
        module.ResearchBasketballEventTeamMemoryReportConfig(
            pass_max_latest_evidence_age_seconds=d("86400.000000"),
            watch_max_latest_evidence_age_seconds=d("21600.000000"),
        )


def test_module_has_narrow_report_only_surface_without_io_network_wallet_or_orders() -> None:
    module = api()
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_BASKETBALL_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
        "REASON_CODES",
        "STATUSES",
        "ResearchBasketballEventTeamMemoryReportConfig",
        "ResearchBasketballEventTeamMemorySignal",
        "ResearchBasketballEventTeamMemoryRow",
        "ResearchBasketballEventTeamMemoryReasonCodeCount",
        "ResearchBasketballEventTeamMemoryReport",
        "build_research_basketball_event_team_memory_report",
        "research_basketball_event_team_memory_report_payload",
    )

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
