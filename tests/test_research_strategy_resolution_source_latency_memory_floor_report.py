from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_resolution_source_latency_memory_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))


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
        "polymarket_alpha_lab.research_strategy_resolution_source_latency_memory_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def moment(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 8, hour, minute, tzinfo=UTC)


def observation(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "strategy_ref": "strategy-alpha-raw",
        "resolution_ref": "resolution-alpha-raw",
        "source_family": "official",
        "resolution_observed_at": moment(10),
        "source_first_seen_at": moment(10, 30),
        "memory_checked_at": moment(12),
        "source_confidence_score": d("0.950000"),
    }
    values.update(overrides)
    return report.ResearchStrategyResolutionSourceLatencyMemoryFloorObservation(**values)


def config(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "config_version": "research-strategy-resolution-source-latency-memory-floor-test-v0",
        "max_source_latency_minutes": d("240"),
        "max_memory_age_minutes": d("720"),
        "latency_penalty_weight": d("0.400000"),
        "memory_age_penalty_weight": d("0.400000"),
        "pass_memory_floor_score": d("0.700000"),
        "watch_memory_floor_score": d("0.450000"),
    }
    values.update(overrides)
    return report.ResearchStrategyResolutionSourceLatencyMemoryFloorConfig(**values)


def build_report(
    *items: object,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
    use_default_items: bool = True,
):
    report = api()
    if not items and use_default_items:
        items = (
            observation(
                strategy_ref="pass-strategy",
                resolution_ref="pass-resolution",
                resolution_observed_at=moment(10),
                source_first_seen_at=moment(10, 30),
                memory_checked_at=moment(12),
                source_confidence_score=d("0.950000"),
            ),
            observation(
                strategy_ref="watch-strategy",
                resolution_ref="watch-resolution",
                source_family="primary",
                resolution_observed_at=moment(8),
                source_first_seen_at=moment(10),
                memory_checked_at=moment(12),
                source_confidence_score=d("0.800000"),
            ),
            observation(
                strategy_ref="block-strategy",
                resolution_ref="block-resolution",
                source_family="secondary",
                resolution_observed_at=moment(6),
                source_first_seen_at=moment(10),
                memory_checked_at=moment(12),
                source_confidence_score=d("0.650000"),
            ),
        )
    return report.build_research_strategy_resolution_source_latency_memory_floor_report(
        items,
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


def test_report_rolls_up_resolution_source_latency_memory_floor() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.generated_at == datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
    assert report.config_version == (
        "research-strategy-resolution-source-latency-memory-floor-test-v0"
    )
    assert report.observation_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_source_latency_minutes == d("130.000000")
    assert report.average_memory_age_minutes == d("110.000000")
    assert report.average_source_memory_floor_score == d("0.522222")
    assert report.minimum_source_memory_floor_score == d("0.183333")
    assert report.status == "block"
    assert set(row.status for row in report.rows) <= {"pass", "watch", "block"}
    assert report.reason_codes == (
        "source_latency_memory_floor_block",
        "source_latency_memory_floor_watch",
        "source_latency_memory_floor_pass",
        "source_latency_pressure_high",
        "source_memory_floor_below_watch",
        "source_memory_floor_below_pass",
    )

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.source_latency_minutes for row in report.rows) == (
        d("240.000000"),
        d("120.000000"),
        d("30.000000"),
    )
    assert tuple(row.memory_age_minutes for row in report.rows) == (
        d("120.000000"),
        d("120.000000"),
        d("90.000000"),
    )
    assert tuple(row.source_memory_floor_score for row in report.rows) == (
        d("0.183333"),
        d("0.533333"),
        d("0.850000"),
    )


def test_empty_report_is_watch_report_only_and_zeroed() -> None:
    empty = build_report(
        cfg=config(),
        generated_at=GENERATED_AT,
        use_default_items=False,
    )

    assert empty.observation_count == d("0")
    assert empty.row_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.average_source_latency_minutes == d("0.000000")
    assert empty.average_memory_age_minutes == d("0.000000")
    assert empty.average_source_memory_floor_score == d("0.000000")
    assert empty.minimum_source_memory_floor_score == d("0.000000")
    assert empty.status == "watch"
    assert empty.reason_codes == (
        "source_latency_memory_floor_report_empty",
    )
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_payload_is_deterministic_decimal_string_json_with_sha256_digest() -> None:
    report_module = api()
    report = build_report()
    payload = report_module.research_strategy_resolution_source_latency_memory_floor_payload(
        report,
    )
    digest_payload = {
        key: item for key, item in payload.items() if key != "validation_digest"
    }
    expected_digest = sha256(
        json.dumps(
            digest_payload,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["observation_count"] == "3"
    assert payload["average_source_memory_floor_score"] == "0.522222"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["source_memory_floor_score"] == "0.183333"
    assert payload["rows"][0]["strategy_ref"].startswith("strategy_ref_")
    assert payload["rows"][0]["resolution_ref"].startswith("resolution_ref_")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["validation_digest"] == expected_digest
    assert report.validation_digest == expected_digest
    assert len(report.validation_digest) == 64
    assert_no_payload_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_public_payload_and_repr_redact_raw_refs_and_forbidden_surfaces() -> None:
    raw_strategy = "candidate-123|market-456|https://source.invalid/path?token=abc"
    raw_resolution = "Will this question resolve from wallet order trade text?"
    report = build_report(
        observation(strategy_ref=raw_strategy, resolution_ref=raw_resolution),
    )
    payload_rendered = json.dumps(report.payload, sort_keys=True).lower()
    repr_rendered = repr(report).lower()

    for forbidden in (
        "candidate-123",
        "market-456",
        "https://source.invalid",
        "token=abc",
        "will this question",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in payload_rendered
        assert forbidden not in repr_rendered


def test_validation_rejects_non_decimal_values_bad_times_flags_and_duplicates() -> None:
    report_module = api()

    with pytest.raises(ValueError, match="config"):
        report_module.build_research_strategy_resolution_source_latency_memory_floor_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="max_source_latency_minutes must be a Decimal"):
        config(max_source_latency_minutes=240)
    with pytest.raises(ValueError, match="source_confidence_score must be a Decimal"):
        observation(source_confidence_score=1)
    with pytest.raises(ValueError, match="source_confidence_score must be a Decimal"):
        observation(source_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="source_family must be a known value"):
        observation(source_family="free_text")
    with pytest.raises(ValueError, match="source_first_seen_at must be on or after"):
        observation(source_first_seen_at=moment(9), resolution_observed_at=moment(10))
    with pytest.raises(ValueError, match="memory_checked_at must be on or after"):
        observation(memory_checked_at=moment(10), source_first_seen_at=moment(11))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 8, 12))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 8, 12, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="memory_checked_at must not be in the future"):
        build_report(observation(memory_checked_at=moment(13)), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="records must be unique"):
        build_report(observation(), observation())


def test_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    report_module = api()
    report = build_report()
    values = (
        config(),
        observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    numeric_suffixes = (
        "_count",
        "_minutes",
        "_score",
        "_weight",
        "_rank",
        "rank",
    )

    assert report_module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_SOURCE_LATENCY_MEMORY_FLOOR_CONFIG_VERSION",
        "ResearchStrategyResolutionSourceLatencyMemoryFloorConfig",
        "ResearchStrategyResolutionSourceLatencyMemoryFloorObservation",
        "ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount",
        "ResearchStrategyResolutionSourceLatencyMemoryFloorReport",
        "ResearchStrategyResolutionSourceLatencyMemoryFloorRow",
        "build_research_strategy_resolution_source_latency_memory_floor_report",
        "research_strategy_resolution_source_latency_memory_floor_payload",
    )
    for exported_name in report_module.__all__:
        exported = getattr(report_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    for value in values:
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes) or field.name == "rank":
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        report_module.ResearchStrategyResolutionSourceLatencyMemoryFloorConfig,
        report_module.ResearchStrategyResolutionSourceLatencyMemoryFloorObservation,
        report_module.ResearchStrategyResolutionSourceLatencyMemoryFloorRow,
        report_module.ResearchStrategyResolutionSourceLatencyMemoryFloorReasonCodeCount,
        report_module.ResearchStrategyResolutionSourceLatencyMemoryFloorReport,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes) or field.name == "rank":
                assert hints[field.name] is Decimal


def test_report_revalidates_counts_sort_status_reason_codes_and_digest() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be deterministically sorted"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="observation_count must match rows"):
        replace(report, observation_count=d("2"))
    with pytest.raises(ValueError, match="status must match rows"):
        replace(report, status="watch")
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(report, reason_codes=("source_latency_memory_floor_pass",))
    with pytest.raises(ValueError, match="validation_digest must match report payload"):
        replace(report, validation_digest="0" * 64)
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]


def test_module_scope_stays_report_only_and_without_forbidden_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "network",
        "database",
        "live_trading",
        "sizing",
        "recommendation",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "open(",
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
        "send",
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
