from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_capture_redundancy_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_capture_redundancy_gap_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
RECENT_CAPTURED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "source-capture-redundancy-gap-report-v0",
        "min_capture_count": d("2"),
        "min_source_family_count": d("2"),
        "max_dominant_source_family_share": d("0.750000"),
        "max_capture_age_seconds": d("3600.000000"),
        "watch_contradiction_pressure": d("0.350000"),
        "block_contradiction_pressure": d("0.700000"),
        "watch_gap_pressure_score": d("0.250000"),
        "block_gap_pressure_score": d("0.600000"),
        "redundancy_gap_weight": d("0.300000"),
        "source_family_imbalance_weight": d("0.250000"),
        "freshness_gap_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceCaptureRedundancyGapConfig(**values)


def capture(
    group: str = "capture-alpha",
    *,
    source_family: str = "official_reporting",
    captured_at: datetime = RECENT_CAPTURED_AT,
    contradiction_pressure: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchSourceCaptureRecord(
        capture_group=group,
        source_family=source_family,
        captured_at=captured_at,
        contradiction_pressure=contradiction_pressure,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*captures: object, config: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_capture_redundancy_gap_report(
        captures,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_dataclass_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if isinstance(value, tuple):
        for item in value:
            assert_decimal_dataclass_numbers(item)
        return
    if not hasattr(value, "__dataclass_fields__"):
        return
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal, field.name
        elif isinstance(item, tuple) or hasattr(item, "__dataclass_fields__"):
            assert_decimal_dataclass_numbers(item)


def assert_no_payload_numbers(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_payload_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_payload_numbers(item)


def assert_no_forbidden_public_payload(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "database",
        "network",
        "live",
    )
    forbidden_value_fragments = (
        "candidate-",
        "market-",
        "slug",
        "question",
        "://",
        "www.",
        "source text",
        "postgres",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "database",
        "network",
        "live",
        "capture-alpha",
        "official_reporting",
        "domain_specialist",
        "independent_archive",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_forbidden_public_payload(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_pass_report_is_aggregate_readonly_and_digest_validated() -> None:
    module = api()
    clean = report(
        capture(
            "capture-alpha",
            source_family="official_reporting",
            contradiction_pressure=d("0.050000"),
        ),
        capture(
            "capture-alpha",
            source_family="domain_specialist",
            contradiction_pressure=d("0.100000"),
        ),
    )

    assert is_dataclass(clean)
    assert clean.status == "pass"
    assert clean.capture_group_count == d("1")
    assert clean.capture_count == d("2")
    assert clean.under_redundant_capture_group_count == d("0")
    assert clean.source_family_imbalance_group_count == d("0")
    assert clean.stale_capture_group_count == d("0")
    assert clean.contradiction_pressure_group_count == d("0")
    assert clean.gap_pressure_score == d("0.025000")
    assert clean.reason_codes == ("source_capture_redundancy_gap_pass",)
    assert clean.paper_only is True
    assert clean.report_only is True
    assert clean.readonly is True
    assert_decimal_dataclass_numbers(clean)

    payload = module.research_source_capture_redundancy_gap_report_payload(clean)
    digest = module.research_source_capture_redundancy_gap_report_digest(clean)
    json.dumps(payload, sort_keys=True)
    assert payload == clean.payload
    assert payload["status"] == "pass"
    assert payload["capture_group_count"] == "1"
    assert payload["capture_count"] == "2"
    assert payload["gap_pressure_score"] == "0.025000"
    assert payload["derived_validation_digest"] == digest
    assert len(digest) == 64
    assert module.research_source_capture_redundancy_gap_report_digest(clean) == digest
    assert_no_payload_numbers(payload)
    assert_no_forbidden_public_payload(payload)


def test_block_report_aggregates_redundancy_imbalance_freshness_and_contradictions() -> None:
    blocked = report(
        capture(
            "capture-alpha",
            captured_at=GENERATED_AT - timedelta(seconds=7200),
            contradiction_pressure=d("0.900000"),
        ),
        capture(
            "capture-beta",
            captured_at=GENERATED_AT - timedelta(seconds=9000),
            contradiction_pressure=d("0.800000"),
        ),
        capture(
            "capture-gamma",
            source_family="official_reporting",
            contradiction_pressure=d("0.850000"),
        ),
        capture(
            "capture-gamma",
            source_family="official_reporting",
            contradiction_pressure=d("0.750000"),
        ),
    )

    assert blocked.status == "block"
    assert blocked.capture_group_count == d("3")
    assert blocked.capture_count == d("4")
    assert blocked.under_redundant_capture_group_count == d("2")
    assert blocked.source_family_imbalance_group_count == d("3")
    assert blocked.stale_capture_group_count == d("2")
    assert blocked.stale_capture_count == d("2")
    assert blocked.contradiction_pressure_group_count == d("3")
    assert blocked.max_capture_age_seconds == d("9000.000000")
    assert blocked.max_dominant_source_family_share == d("1.000000")
    assert blocked.max_contradiction_pressure == d("0.900000")
    assert blocked.redundancy_gap_ratio == d("0.666667")
    assert blocked.source_family_imbalance_ratio == d("1.000000")
    assert blocked.freshness_gap_ratio == d("0.666667")
    assert blocked.contradiction_pressure_ratio == d("0.850000")
    assert blocked.gap_pressure_score == d("0.795834")
    assert blocked.reason_codes == (
        "capture_redundancy_gap_block",
        "source_family_imbalance_block",
        "freshness_gap_block",
        "contradiction_pressure_block",
        "source_capture_redundancy_gap_block",
    )
    assert blocked.reason_code_counts[0].reason_code == "capture_redundancy_gap_block"
    assert blocked.reason_code_counts[0].count == d("1")
    assert_no_forbidden_public_payload(blocked.payload)


def test_watch_status_uses_public_status_vocabulary_only() -> None:
    watched = report(
        capture("capture-alpha", source_family="official_reporting"),
        capture("capture-alpha", source_family="domain_specialist"),
        capture("capture-beta", source_family="official_reporting"),
    )

    assert watched.status == "watch"
    assert watched.reason_codes == (
        "capture_redundancy_gap_watch",
        "source_family_imbalance_watch",
        "source_capture_redundancy_gap_watch",
    )

    with pytest.raises(ValueError, match="status"):
        replace(watched, status="blocked")


def test_frozen_exact_decimal_inputs_and_hard_flags_are_enforced() -> None:
    module = api()
    clean = report(
        capture("capture-alpha", source_family="official_reporting"),
        capture("capture-alpha", source_family="domain_specialist"),
    )

    with pytest.raises(FrozenInstanceError):
        clean.status = "watch"  # type: ignore[misc]

    for value in (
        cfg(),
        capture(),
        clean,
        clean.reason_code_counts[0],
    ):
        assert is_dataclass(value)

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceCaptureRedundancyGapConfig):
            pass

    with pytest.raises(ValueError, match="min_capture_count"):
        cfg(min_capture_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure"):
        capture(contradiction_pressure=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure"):
        capture(contradiction_pressure=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        capture(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(clean, readonly=False)


def test_digest_rejects_tampering_and_serialization_is_deterministic() -> None:
    left = report(
        capture("capture-alpha", source_family="official_reporting"),
        capture("capture-alpha", source_family="domain_specialist"),
        capture("capture-beta", source_family="official_reporting"),
    )
    right = report(
        capture("capture-beta", source_family="official_reporting"),
        capture("capture-alpha", source_family="domain_specialist"),
        capture("capture-alpha", source_family="official_reporting"),
    )

    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, gap_pressure_score=d("0.000000"))


def test_rejects_raw_capture_surfaces_and_static_module_surface_is_report_only() -> None:
    module = api()
    unsafe_values = (
        "https://example.test/path",
        "candidate-market-raw",
        "question_text",
        "postgres_dsn",
        "table_name",
        "token_value",
        "wallet_item",
        "order_item",
        "trade_item",
        "auth_item",
        "network_item",
        "live_item",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            capture(value)

    unsafe_modules = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    }
    tree = ast.parse(MODULE_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert imported.isdisjoint(unsafe_modules)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in unsafe_modules

    forbidden_public_fragments = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "database",
        "network",
        "live",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)
    for cls in (
        module.ResearchSourceCaptureRedundancyGapConfig,
        module.ResearchSourceCaptureRecord,
        module.ResearchSourceCaptureRedundancyGapReasonCodeCount,
        module.ResearchSourceCaptureRedundancyGapReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_fragments)
