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
    "src/polymarket_alpha_lab/research_domain_basketball_signal_memory_quality_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_basketball_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_input(**overrides: object):
    module = api()
    values = {
        "basketball_signal_bucket": "playoff_rotation_handoff",
        "memory_scope_bucket": "late_news_context",
        "team_memory_age_seconds": d("3600.000000"),
        "injury_memory_age_seconds": d("3600.000000"),
        "schedule_memory_age_seconds": d("3600.000000"),
        "context_memory_age_seconds": d("3600.000000"),
        "team_conflict_count": d("0.000000"),
        "injury_conflict_count": d("0.000000"),
        "schedule_conflict_count": d("0.000000"),
        "context_conflict_count": d("0.000000"),
        "team_missing_count": d("0.000000"),
        "injury_missing_count": d("0.000000"),
        "schedule_missing_count": d("0.000000"),
        "context_missing_count": d("0.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=30),
    }
    values.update(overrides)
    return module.ResearchDomainBasketballSignalMemoryQualityInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_basketball_signal_memory_quality_report(
        items,
        config=cfg
        if cfg is not None
        else module.ResearchDomainBasketballSignalMemoryQualityConfig(),
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


def assert_public_numerics_are_decimal(value: object) -> None:
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
            assert_public_numerics_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numerics_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numerics_are_decimal(item)


def assert_no_private_forecast_handoff_surface(value: Any) -> None:
    forbidden = (
        "candidate_id",
        "candidate_slug",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "game_id",
        "team_id",
        "team_name",
        "question",
        "url",
        "://",
        "www.",
        "source_text",
        "raw_text",
        "dsn",
        "table_name",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "network",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(term in lowered_key for term in forbidden), key
            assert_no_private_forecast_handoff_surface(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_private_forecast_handoff_surface(item)
    elif type(value) is str:
        lowered_value = value.lower()
        assert not any(term in lowered_value for term in forbidden), value


def test_basketball_signal_memory_quality_identifies_stale_conflicting_missing_inputs() -> None:
    report = build_report(
        memory_input(),
        memory_input(
            basketball_signal_bucket="starter_minutes_watch",
            memory_scope_bucket="injury_schedule_context",
            team_memory_age_seconds=d("30000.000000"),
            injury_memory_age_seconds=d("30000.000000"),
            schedule_memory_age_seconds=d("30000.000000"),
            context_memory_age_seconds=d("30000.000000"),
            team_conflict_count=d("1.000000"),
            injury_conflict_count=d("1.000000"),
            schedule_conflict_count=d("1.000000"),
            context_conflict_count=d("1.000000"),
            team_missing_count=d("1.000000"),
            injury_missing_count=d("1.000000"),
            schedule_missing_count=d("1.000000"),
            context_missing_count=d("1.000000"),
            observed_at=datetime(2026, 7, 8, 13, 45, tzinfo=EASTERN),
        ),
        memory_input(
            basketball_signal_bucket="availability_cluster_block",
            memory_scope_bucket="forecast_handoff_gap",
            team_memory_age_seconds=d("100000.000000"),
            injury_memory_age_seconds=d("100000.000000"),
            schedule_memory_age_seconds=d("100000.000000"),
            context_memory_age_seconds=d("100000.000000"),
            team_conflict_count=d("2.000000"),
            injury_conflict_count=d("2.000000"),
            schedule_conflict_count=d("2.000000"),
            context_conflict_count=d("2.000000"),
            team_missing_count=d("2.000000"),
            injury_missing_count=d("2.000000"),
            schedule_missing_count=d("2.000000"),
            context_missing_count=d("2.000000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "block"
    assert report.staleness_status == "block"
    assert report.conflict_status == "block"
    assert report.completeness_status == "block"
    assert report.handoff_gate == "paper_refresh_basketball_memory_before_forecast"
    assert report.memory_input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.stale_input_count == d("2.000000")
    assert report.conflicting_input_count == d("2.000000")
    assert report.missing_input_count == d("2.000000")
    assert report.total_conflict_count == d("12.000000")
    assert report.total_missing_count == d("12.000000")
    assert report.max_memory_age_seconds == d("100000.000000")
    assert report.average_memory_quality_score == d("0.550926")
    assert report.reason_codes == (
        "basketball_signal_memory_quality_report_block",
        "team_memory_stale_block",
        "injury_memory_stale_block",
        "schedule_memory_stale_block",
        "context_memory_stale_block",
        "team_memory_conflict_block",
        "injury_memory_conflict_block",
        "schedule_memory_conflict_block",
        "context_memory_conflict_block",
        "team_memory_missing_block",
        "injury_memory_missing_block",
        "schedule_memory_missing_block",
        "context_memory_missing_block",
        "team_memory_stale_watch",
        "injury_memory_stale_watch",
        "schedule_memory_stale_watch",
        "context_memory_stale_watch",
        "team_memory_conflict_watch",
        "injury_memory_conflict_watch",
        "schedule_memory_conflict_watch",
        "context_memory_conflict_watch",
        "team_memory_missing_watch",
        "injury_memory_missing_watch",
        "schedule_memory_missing_watch",
        "context_memory_missing_watch",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.basketball_signal_bucket == "availability_cluster_block"
    assert blocked.memory_quality_score == d("0.000000")
    assert blocked.observed_at == GENERATED_AT - timedelta(minutes=30)
    assert blocked.reason_codes == (
        "team_memory_stale_block",
        "injury_memory_stale_block",
        "schedule_memory_stale_block",
        "context_memory_stale_block",
        "team_memory_conflict_block",
        "injury_memory_conflict_block",
        "schedule_memory_conflict_block",
        "context_memory_conflict_block",
        "team_memory_missing_block",
        "injury_memory_missing_block",
        "schedule_memory_missing_block",
        "context_memory_missing_block",
    )
    assert watched.status == "watch"
    assert watched.max_memory_age_seconds == d("30000.000000")
    assert watched.memory_quality_score == d("0.652778")
    assert watched.observed_at == datetime(2026, 7, 8, 17, 45, tzinfo=UTC)
    assert watched.reason_codes == (
        "team_memory_stale_watch",
        "injury_memory_stale_watch",
        "schedule_memory_stale_watch",
        "context_memory_stale_watch",
        "team_memory_conflict_watch",
        "injury_memory_conflict_watch",
        "schedule_memory_conflict_watch",
        "context_memory_conflict_watch",
        "team_memory_missing_watch",
        "injury_memory_missing_watch",
        "schedule_memory_missing_watch",
        "context_memory_missing_watch",
    )
    assert passed.status == "pass"
    assert passed.reason_codes == ("basketball_signal_memory_quality_clear",)


def test_empty_report_blocks_before_forecast_handoff_without_private_surfaces() -> None:
    report = build_report()

    assert report.report_status == "block"
    assert report.staleness_status == "block"
    assert report.conflict_status == "block"
    assert report.completeness_status == "block"
    assert report.handoff_gate == "paper_refresh_basketball_memory_before_forecast"
    assert report.memory_input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.stale_input_count == d("0.000000")
    assert report.conflicting_input_count == d("0.000000")
    assert report.missing_input_count == d("0.000000")
    assert report.average_memory_quality_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("basketball_signal_memory_quality_report_empty",)
    assert report.reason_code_counts == ()

    payload = api().research_domain_basketball_signal_memory_quality_report_payload(report)
    assert_no_private_forecast_handoff_surface(payload)


def test_payload_is_deterministic_decimal_stringed_public_safe_and_digest_checked() -> None:
    module = api()
    inputs = (
        memory_input(),
        memory_input(
            basketball_signal_bucket="starter_minutes_watch",
            memory_scope_bucket="injury_schedule_context",
            team_memory_age_seconds=d("30000.000000"),
            injury_memory_age_seconds=d("30000.000000"),
            schedule_memory_age_seconds=d("30000.000000"),
            context_memory_age_seconds=d("30000.000000"),
            team_conflict_count=d("1.000000"),
            injury_conflict_count=d("1.000000"),
            schedule_conflict_count=d("1.000000"),
            context_conflict_count=d("1.000000"),
            team_missing_count=d("1.000000"),
            injury_missing_count=d("1.000000"),
            schedule_missing_count=d("1.000000"),
            context_missing_count=d("1.000000"),
        ),
    )
    first = build_report(*inputs)
    second = build_report(*reversed(inputs))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = module.research_domain_basketball_signal_memory_quality_report_payload(first)
    repeat_payload = module.research_domain_basketball_signal_memory_quality_report_payload(second)

    assert payload == first.payload
    assert payload == repeat_payload
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["memory_input_count"] == "2.000000"
    assert payload["average_memory_quality_score"] == "0.826389"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_numeric_scalars(payload)
    assert_no_private_forecast_handoff_surface(payload)

    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    expected_digest = module.hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    assert digest == expected_digest

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_basketball_signal_memory_quality_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2.000000"))

    unsafe = dict(payload)
    unsafe["market_slug"] = "unsafe-value"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_domain_basketball_signal_memory_quality_report_payload(unsafe)


def test_dataclasses_are_frozen_decimal_only_and_validate_inputs() -> None:
    module = api()
    sample_input = memory_input()
    sample_report = build_report(sample_input)

    dataclass_types = (
        module.ResearchDomainBasketballSignalMemoryQualityConfig,
        module.ResearchDomainBasketballSignalMemoryQualityInput,
        module.ResearchDomainBasketballSignalMemoryQualityRow,
        module.ResearchDomainBasketballSignalMemoryQualityReasonCodeCount,
        module.ResearchDomainBasketballSignalMemoryQualityReport,
    )
    for dataclass_type in dataclass_types:
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        sample_input.team_memory_age_seconds = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sample_report.report_status = "pass"  # type: ignore[misc]

    for item in (module.ResearchDomainBasketballSignalMemoryQualityConfig(), sample_input, sample_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numerics_are_decimal(item)

    with pytest.raises(ValueError, match="team_memory_age_seconds must be a Decimal"):
        memory_input(team_memory_age_seconds=1)
    with pytest.raises(ValueError, match="injury_memory_age_seconds must be a Decimal"):
        memory_input(injury_memory_age_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="team_conflict_count must be integral"):
        memory_input(team_conflict_count=d("1.500000"))
    with pytest.raises(ValueError, match="basketball_signal_bucket"):
        memory_input(basketball_signal_bucket="market-slug")
    with pytest.raises(ValueError, match="memory_scope_bucket"):
        memory_input(memory_scope_bucket="source_text")
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=datetime(2026, 7, 8, 17, 45))
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(observed_at=_DatetimeSubclass(2026, 7, 8, 17, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_input(), cfg=object())
    with pytest.raises(ValueError, match="pass_max_memory_age_seconds"):
        module.ResearchDomainBasketballSignalMemoryQualityConfig(
            pass_max_memory_age_seconds=d("90000.000000"),
            watch_max_memory_age_seconds=d("86400.000000"),
        )
    with pytest.raises(ValueError, match="watch_conflict_count"):
        module.ResearchDomainBasketballSignalMemoryQualityConfig(
            watch_conflict_count=d("3.000000"),
            block_conflict_count=d("2.000000"),
        )


def test_module_has_narrow_report_only_surface_without_io_network_wallet_or_orders() -> None:
    module = api()
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_BASKETBALL_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
        "REASON_CODES",
        "STATUSES",
        "ResearchDomainBasketballSignalMemoryQualityConfig",
        "ResearchDomainBasketballSignalMemoryQualityInput",
        "ResearchDomainBasketballSignalMemoryQualityRow",
        "ResearchDomainBasketballSignalMemoryQualityReasonCodeCount",
        "ResearchDomainBasketballSignalMemoryQualityReport",
        "build_research_domain_basketball_signal_memory_quality_report",
        "research_domain_basketball_signal_memory_quality_report_payload",
    )

    banned_import_roots = {
        "aiohttp",
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    banned_call_names = {
        "buy",
        "connect",
        "delete",
        "execute",
        "executemany",
        "get",
        "open",
        "order",
        "patch",
        "post",
        "put",
        "request",
        "sell",
        "send",
        "submit",
        "trade",
        "write",
    }
    banned_source_fragments = (
        "database",
        "dsn",
        "live_trading",
        "market_slug",
        "order",
        "private_key",
        "recommendation",
        "sizing",
        "source_text",
        "table_name",
        "token_id",
        "trade",
        "wallet",
    )

    lowered_source = source.lower()
    assert not any(fragment in lowered_source for fragment in banned_source_fragments)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in banned_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in banned_call_names
