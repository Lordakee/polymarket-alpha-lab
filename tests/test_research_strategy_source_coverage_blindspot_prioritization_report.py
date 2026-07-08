from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_source_coverage_blindspot_prioritization_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_source_coverage_blindspot_prioritization_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "strategy-source-coverage-blindspot-prioritization-report-v0",
        "min_family_coverage_ratio": d("0.750000"),
        "block_family_coverage_below_ratio": d("0.250000"),
        "min_corroborating_family_count": d("2"),
        "watch_priority_score": d("0.300000"),
        "block_priority_score": d("0.650000"),
        "max_source_age_seconds": d("10800.000000"),
        "coverage_gap_weight": d("0.450000"),
        "corroboration_gap_weight": d("0.350000"),
        "freshness_gap_weight": d("0.200000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchStrategySourceCoverageBlindspotPrioritizationConfig(**values)


def observation(
    strategy_lane: str = "macro_lane",
    source_family: str = "official_reporting",
    *,
    observed_at: datetime = OBSERVED_AT,
    expected_source_count: Decimal = d("4"),
    covered_source_count: Decimal = d("4"),
    corroborating_family_count: Decimal = d("2"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategySourceCoverageBlindspotObservation(
        strategy_lane=strategy_lane,
        source_family=source_family,
        observed_at=observed_at,
        expected_source_count=expected_source_count,
        covered_source_count=covered_source_count,
        corroborating_family_count=corroborating_family_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
):
    module = api()
    return module.build_research_strategy_source_coverage_blindspot_prioritization_report(
        observations,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"blindspot_rows", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "ratio",
                "score",
                "seconds",
                "rank",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_public_number_payload(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_public_number_payload(item_value)


def assert_no_forbidden_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "raw",
        "candidate",
        "market_id",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
        "database",
        "auth",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "market_id",
        "slug",
        "question",
        "source_text",
        "dsn",
        "wallet",
        "order",
        "trade",
        "token",
        "database",
        "auth",
        "buy",
        "sell",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_forbidden_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_empty_input_returns_pass_report_only_decimal_digest() -> None:
    module = api()
    empty_report = report()

    assert is_dataclass(empty_report)
    assert empty_report.generated_at == GENERATED_AT
    assert empty_report.config_version == (
        "strategy-source-coverage-blindspot-prioritization-report-v0"
    )
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == (
        "strategy_source_coverage_blindspot_prioritization_passed",
    )
    assert empty_report.observation_count == d("0")
    assert empty_report.blindspot_row_count == d("0")
    assert empty_report.pass_count == d("0")
    assert empty_report.watch_count == d("0")
    assert empty_report.block_count == d("0")
    assert empty_report.max_priority_score == d("0.000000")
    assert empty_report.average_priority_score == d("0.000000")
    assert empty_report.reason_code_counts == ()
    assert empty_report.blindspot_rows == ()
    assert empty_report.paper_only is True
    assert empty_report.report_only is True
    assert empty_report.readonly is True
    assert_decimal_public_numbers(empty_report)

    payload = module.research_strategy_source_coverage_blindspot_prioritization_payload(
        empty_report,
    )
    digest_value = (
        module.research_strategy_source_coverage_blindspot_prioritization_digest(
            empty_report,
        )
    )
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert payload["status"] == "pass"
    assert payload["observation_count"] == "0"
    assert payload["derived_validation_digest"] == digest_value
    assert len(digest_value) == 64


def test_report_ranks_sanitized_missing_coverage_and_corroboration_gaps() -> None:
    prioritized = report(
        observation(
            "lane-pass",
            "official_reporting",
            covered_source_count=d("4"),
            corroborating_family_count=d("2"),
        ),
        observation(
            "lane-watch",
            "independent_analysis",
            observed_at=GENERATED_AT - timedelta(seconds=3600),
            covered_source_count=d("2"),
            corroborating_family_count=d("1"),
        ),
        observation(
            "lane-block",
            "primary_record",
            observed_at=GENERATED_AT - timedelta(seconds=14400),
            covered_source_count=d("0"),
            corroborating_family_count=d("0"),
        ),
    )

    assert prioritized.status == "block"
    assert prioritized.observation_count == d("3")
    assert prioritized.blindspot_row_count == d("2")
    assert prioritized.pass_count == d("1")
    assert prioritized.watch_count == d("1")
    assert prioritized.block_count == d("1")
    assert tuple(row.strategy_lane for row in prioritized.blindspot_rows) == (
        "lane-block",
        "lane-watch",
    )

    blocked, watched = prioritized.blindspot_rows
    assert blocked.priority_rank == d("1")
    assert blocked.status == "block"
    assert blocked.source_family == "primary_record"
    assert blocked.expected_source_count == d("4")
    assert blocked.covered_source_count == d("0")
    assert blocked.missing_source_count == d("4")
    assert blocked.coverage_ratio == d("0.000000")
    assert blocked.coverage_shortfall_ratio == d("1.000000")
    assert blocked.corroboration_gap_count == d("2")
    assert blocked.corroboration_gap_ratio == d("1.000000")
    assert blocked.source_age_seconds == d("14400.000000")
    assert blocked.freshness_gap_ratio == d("1.000000")
    assert blocked.priority_score == d("1.000000")
    assert blocked.reason_codes == (
        "missing_source_family_coverage_block",
        "corroboration_gap_block",
        "source_family_staleness_block",
        "manual_research_priority_block",
    )

    assert watched.priority_rank == d("2")
    assert watched.status == "watch"
    assert watched.coverage_ratio == d("0.500000")
    assert watched.coverage_shortfall_ratio == d("0.500000")
    assert watched.corroboration_gap_count == d("1")
    assert watched.corroboration_gap_ratio == d("0.500000")
    assert watched.source_age_seconds == d("3600.000000")
    assert watched.freshness_gap_ratio == d("0.333333")
    assert watched.priority_score == d("0.466667")
    assert watched.reason_codes == (
        "missing_source_family_coverage_watch",
        "corroboration_gap_watch",
        "manual_research_priority_watch",
    )


def test_payload_is_decimal_string_json_ready_sanitized_and_deterministic() -> None:
    module = api()
    observations = (
        observation("lane-alpha", "official_reporting"),
        observation(
            "lane-beta",
            "independent_analysis",
            observed_at=GENERATED_AT - timedelta(seconds=3600),
            covered_source_count=d("2"),
            corroborating_family_count=d("1"),
        ),
        observation(
            "lane-gamma",
            "primary_record",
            covered_source_count=d("1"),
            corroborating_family_count=d("0"),
        ),
    )
    first = report(*observations)
    second = report(*reversed(observations))

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["blindspot_row_count"] == "2"
    assert payload["blindspot_rows"][0]["strategy_lane"] == "lane-gamma"
    assert payload["blindspot_rows"][0]["source_family"] == "primary_record"
    assert payload["blindspot_rows"][0]["priority_rank"] == "1"
    assert payload["blindspot_rows"][0]["coverage_ratio"] == "0.250000"
    assert payload["blindspot_rows"][1]["priority_score"] == "0.466667"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.derived_validation_digest == second.derived_validation_digest
    assert (
        module.research_strategy_source_coverage_blindspot_prioritization_digest(first)
        == first.derived_validation_digest
    )
    assert_no_public_number_payload(payload)
    assert_no_forbidden_public_surface(payload)
    assert_decimal_public_numbers(first)
    for row in first.blindspot_rows:
        assert_decimal_public_numbers(row)


def test_dataclasses_are_frozen_and_reject_subclassing_and_bad_flags() -> None:
    module = api()
    built = report(
        observation(
            "lane-alpha",
            "official_reporting",
            covered_source_count=d("1"),
            corroborating_family_count=d("0"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(
            module.ResearchStrategySourceCoverageBlindspotPrioritizationConfig,
        ):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(built.blindspot_rows[0], report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)


def test_strict_types_unsafe_inputs_and_live_surfaces_are_rejected() -> None:
    with pytest.raises(ValueError, match="covered_source_count must be a Decimal"):
        observation(covered_source_count=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="expected_source_count must be exactly Decimal"):
        observation(expected_source_count=_DecimalSubclass("4"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be a bool"):
        observation(paper_only=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        observation(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="observed_at cannot be after generated_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unsafe"):
        observation(strategy_lane="https://example.invalid/raw-market")

    with pytest.raises(ValueError, match="unsafe"):
        observation(source_family="wallet_order_trade")

    with pytest.raises(ValueError, match="covered_source_count"):
        observation(expected_source_count=d("1"), covered_source_count=d("2"))

    duplicate = observation("lane-dupe", "official_reporting")
    with pytest.raises(ValueError, match="unique"):
        report(duplicate, duplicate)

    with pytest.raises(ValueError, match="weights must sum to one"):
        cfg(freshness_gap_weight=d("0.100000"))


def test_digest_validation_rejects_report_tampering() -> None:
    built = report(
        observation(
            "lane-alpha",
            "official_reporting",
            covered_source_count=d("1"),
            corroborating_family_count=d("0"),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, max_priority_score=d("0.000000"))


def test_module_avoids_forbidden_imports_and_public_live_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = {name for name in dir(api()) if not name.startswith("_")}
    for forbidden_name in (
        "client",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "auth",
        "sizing",
        "recommendation",
        "dsn",
        "token",
    ):
        assert forbidden_name not in public_names
