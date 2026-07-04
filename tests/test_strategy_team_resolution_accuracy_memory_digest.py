from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_resolution_accuracy_memory_digest.py"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 30, tzinfo=timezone(timedelta(hours=2)))
RESOLVED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_resolution_accuracy_memory_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    digest = api()
    values: dict[str, object] = {
        "config_version": "strategy-team-resolution-accuracy-memory-digest-test-v0",
        "min_pass_accuracy_rate": d("0.750000"),
        "min_watch_accuracy_rate": d("0.500000"),
        "max_pass_average_miss_severity": d("0.250000"),
        "max_watch_average_miss_severity": d("0.500000"),
        "severe_miss_threshold": d("0.500000"),
        "max_severe_miss_ratio": d("0.250000"),
        "min_source_reliability_score": d("0.600000"),
    }
    values.update(overrides)
    return digest.StrategyTeamResolutionAccuracyMemoryDigestConfig(**values)


def record(**overrides: object):
    digest = api()
    values: dict[str, object] = {
        "team_id": "macro_team",
        "category_id": "macro_rates",
        "event_ref": "fed-resolution-alpha",
        "source_ref": "official-resolution-source",
        "resolved_at": RESOLVED_AT,
        "predicted_probability": d("0.800000"),
        "resolved_outcome": True,
        "accuracy_hit": True,
        "miss_severity": d("0.100000"),
        "source_reliability_score": d("0.900000"),
        "source_count": d("1"),
    }
    values.update(overrides)
    return digest.StrategyTeamResolutionAccuracyMemoryRecord(**values)


def report(*records: object, cfg=None, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_strategy_team_resolution_accuracy_memory_digest(
        records,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_payload_numbers(value: Any) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        raise AssertionError(f"unexpected JSON numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_payload_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_payload_numbers(item)


def test_digest_summarizes_resolution_accuracy_miss_severity_and_source_memory() -> None:
    digest_report = report(
        record(
            team_id="sports_team",
            category_id="sports_soccer",
            event_ref="sports-final-a",
            source_ref="league-resolution-a",
            accuracy_hit=False,
            miss_severity=d("0.600000"),
            source_reliability_score=d("0.400000"),
        ),
        record(
            team_id="macro_team",
            category_id="macro_rates",
            event_ref="macro-final-a",
            source_ref="official-rates-a",
            accuracy_hit=True,
            miss_severity=d("0.050000"),
            source_reliability_score=d("0.900000"),
            source_count=d("2"),
        ),
        record(
            team_id="crypto_team",
            category_id="crypto_btc",
            event_ref="crypto-final-a",
            source_ref="exchange-resolution-a",
            accuracy_hit=True,
            miss_severity=d("0.200000"),
            source_reliability_score=d("0.600000"),
        ),
        record(
            team_id="sports_team",
            category_id="sports_soccer",
            event_ref="sports-final-b",
            source_ref="league-resolution-b",
            accuracy_hit=False,
            miss_severity=d("0.800000"),
            source_reliability_score=d("0.300000"),
        ),
        record(
            team_id="macro_team",
            category_id="macro_rates",
            event_ref="macro-final-b",
            source_ref="official-rates-b",
            accuracy_hit=True,
            miss_severity=d("0.150000"),
            source_reliability_score=d("0.800000"),
            source_count=d("3"),
        ),
        record(
            team_id="crypto_team",
            category_id="crypto_btc",
            event_ref="crypto-final-b",
            source_ref="exchange-resolution-b",
            accuracy_hit=False,
            miss_severity=d("0.400000"),
            source_reliability_score=d("0.500000"),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 4, 14, 30, tzinfo=UTC)
    assert digest_report.config_version == (
        "strategy-team-resolution-accuracy-memory-digest-test-v0"
    )
    assert digest_report.source_record_count == d("6")
    assert digest_report.team_category_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.resolved_event_count == d("6")
    assert digest_report.correct_event_count == d("3")
    assert digest_report.miss_event_count == d("3")
    assert digest_report.severe_miss_count == d("2")
    assert digest_report.accuracy_rate == d("0.500000")
    assert digest_report.average_miss_severity == d("0.366667")
    assert digest_report.average_source_reliability_score == d("0.666667")
    assert digest_report.average_paper_weight_adjustment == d("0.316167")
    assert digest_report.status == "blocked"
    assert digest_report.reason_codes == (
        "resolution_accuracy_memory_blocked",
        "resolution_accuracy_memory_watch",
        "resolution_accuracy_memory_pass",
        "resolved_accuracy_below_watch",
        "resolved_accuracy_below_pass",
        "miss_severity_above_watch",
        "miss_severity_above_pass",
        "severe_miss_ratio_high",
        "source_reliability_below_min",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.team_id for row in digest_report.rows) == (
        "sports_team",
        "crypto_team",
        "macro_team",
    )
    assert tuple(row.status for row in digest_report.rows) == (
        "blocked",
        "watch",
        "pass",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.accuracy_rate == d("0.000000")
    assert blocked.average_miss_severity == d("0.700000")
    assert blocked.severe_miss_ratio == d("1.000000")
    assert blocked.average_source_reliability_score == d("0.350000")
    assert blocked.paper_weight_adjustment == d("0.000000")
    assert blocked.reason_codes == (
        "resolution_accuracy_memory_blocked",
        "resolved_accuracy_below_watch",
        "miss_severity_above_watch",
        "severe_miss_ratio_high",
        "source_reliability_below_min",
    )

    assert watched.accuracy_rate == d("0.500000")
    assert watched.average_miss_severity == d("0.300000")
    assert watched.severe_miss_ratio == d("0.000000")
    assert watched.average_source_reliability_score == d("0.550000")
    assert watched.paper_weight_adjustment == d("0.192500")
    assert watched.reason_codes == (
        "resolution_accuracy_memory_watch",
        "resolved_accuracy_below_pass",
        "miss_severity_above_pass",
        "source_reliability_below_min",
    )

    assert passed.accuracy_rate == d("1.000000")
    assert passed.average_miss_severity == d("0.100000")
    assert passed.average_source_reliability_score == d("0.840000")
    assert passed.paper_weight_adjustment == d("0.756000")
    assert passed.reason_codes == ("resolution_accuracy_memory_pass",)


def test_empty_digest_is_watch_zeroed_report_only_memory() -> None:
    empty = report()

    assert empty.source_record_count == d("0")
    assert empty.team_category_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.resolved_event_count == d("0")
    assert empty.correct_event_count == d("0")
    assert empty.miss_event_count == d("0")
    assert empty.severe_miss_count == d("0")
    assert empty.accuracy_rate == d("0.000000")
    assert empty.average_miss_severity == d("0.000000")
    assert empty.average_source_reliability_score == d("0.000000")
    assert empty.average_paper_weight_adjustment == d("0.000000")
    assert empty.status == "watch"
    assert empty.reason_codes == (
        "strategy_team_resolution_accuracy_memory_digest_empty",
    )
    assert empty.rows == ()
    assert empty.reason_code_counts == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_reason_code_counts_are_unique_and_deterministic() -> None:
    digest = api()
    digest_report = report(
        record(
            team_id="a_team",
            category_id="a_category",
            event_ref="event-a",
            accuracy_hit=False,
            miss_severity=d("0.800000"),
            source_reliability_score=d("0.300000"),
        ),
        record(
            team_id="b_team",
            category_id="b_category",
            event_ref="event-b",
            accuracy_hit=True,
            miss_severity=d("0.300000"),
            source_reliability_score=d("0.500000"),
        ),
        record(
            team_id="b_team",
            category_id="b_category",
            event_ref="event-c",
            accuracy_hit=False,
            miss_severity=d("0.400000"),
            source_reliability_score=d("0.500000"),
        ),
    )

    assert digest_report.reason_code_counts == (
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="source_reliability_below_min",
            count=d("2"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="resolution_accuracy_memory_blocked",
            count=d("1"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="resolution_accuracy_memory_watch",
            count=d("1"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="resolved_accuracy_below_watch",
            count=d("1"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="resolved_accuracy_below_pass",
            count=d("1"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="miss_severity_above_watch",
            count=d("1"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="miss_severity_above_pass",
            count=d("1"),
        ),
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
            reason_code="severe_miss_ratio_high",
            count=d("1"),
        ),
    )


def test_payload_uses_decimal_strings_utc_datetimes_flags_and_redacted_refs() -> None:
    digest = api()
    digest_report = report(
        record(
            event_ref="https://example.invalid/private?api_key=secret-token",
            source_ref="wallet:0xabc-private-source",
            resolved_at=datetime(2026, 7, 4, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
            source_count=d("2"),
        ),
    )

    assert "secret" not in repr(digest_report).lower()
    assert "wallet" not in repr(digest_report).lower()
    payload = digest.strategy_team_resolution_accuracy_memory_digest_payload(digest_report)
    rendered = repr(payload).lower()
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T14:30:00+00:00"
    assert payload["source_record_count"] == "1"
    assert payload["rows"][0]["latest_resolved_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["accuracy_rate"] == "1.000000"
    assert payload["rows"][0]["event_refs"][0].startswith("event_ref_")
    assert payload["rows"][0]["source_refs"][0].startswith("source_ref_")
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_payload_numbers(payload)

    for forbidden in ("https", "api_key", "secret", "wallet", "0xabc", "private"):
        assert forbidden not in rendered


def test_validation_rejects_float_int_subclasses_bad_time_flags_and_duplicates() -> None:
    digest = api()

    with pytest.raises(ValueError, match="config"):
        digest.build_strategy_team_resolution_accuracy_memory_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="predicted_probability must be a Decimal"):
        record(predicted_probability=1)
    with pytest.raises(ValueError, match="miss_severity must be a Decimal"):
        record(miss_severity=0.1)
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        record(source_reliability_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        record(source_count=1)
    with pytest.raises(ValueError, match="accuracy_hit must be a bool"):
        record(accuracy_hit=1)
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        record(resolved_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        record(resolved_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(record(), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(record(), readonly=False)
    with pytest.raises(ValueError, match="records must be unique"):
        report(record(), record())

    digest_report = report(record())
    with pytest.raises(ValueError, match="source_record_count"):
        replace(digest_report, source_record_count=1)
    with pytest.raises(ValueError, match="rows"):
        replace(digest_report, rows=(object(),))
    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError) as exc_info:
        record(team_id="team_secret_marker")
    assert "team_secret_marker" not in str(exc_info.value)


def test_public_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    digest = api()
    digest_report = report(record())
    values = (
        config(),
        record(event_ref="numeric-field-event"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )
    numeric_suffixes = (
        "_count",
        "_rate",
        "_ratio",
        "_score",
        "_severity",
        "_adjustment",
        "_probability",
        "_threshold",
    )

    assert digest.__all__ == (
        "DEFAULT_STRATEGY_TEAM_RESOLUTION_ACCURACY_MEMORY_DIGEST_CONFIG_VERSION",
        "StrategyTeamResolutionAccuracyMemoryDigestConfig",
        "StrategyTeamResolutionAccuracyMemoryRecord",
        "StrategyTeamResolutionAccuracyMemoryReasonCodeCount",
        "StrategyTeamResolutionAccuracyMemoryReport",
        "StrategyTeamResolutionAccuracyMemoryRow",
        "build_strategy_team_resolution_accuracy_memory_digest",
        "strategy_team_resolution_accuracy_memory_digest_payload",
    )
    for exported_name in digest.__all__:
        exported = getattr(digest, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        digest.StrategyTeamResolutionAccuracyMemoryDigestConfig,
        digest.StrategyTeamResolutionAccuracyMemoryRecord,
        digest.StrategyTeamResolutionAccuracyMemoryRow,
        digest.StrategyTeamResolutionAccuracyMemoryReasonCodeCount,
        digest.StrategyTeamResolutionAccuracyMemoryReport,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes):
                assert hints[field.name] is Decimal


def test_module_scope_stays_pure_report_only_and_without_forbidden_surface_terms() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "market_slug",
        "question",
        "payload_json",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "psycopg",
        "sqlite",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "executemany",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
