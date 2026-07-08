from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_probability_gap_attribution_report.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_probability_gap_attribution_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    *,
    forecast_probability: Decimal = d("0.520000"),
    benchmark_probability: Decimal = d("0.500000"),
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    evidence_driver_score: Decimal = d("0.100000"),
    cost_driver_score: Decimal = d("0.050000"),
    settlement_driver_score: Decimal = d("0.050000"),
    domain_memory_driver_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyProbabilityGapAttributionInput(
        forecast_probability=forecast_probability,
        benchmark_probability=benchmark_probability,
        observed_at=observed_at,
        evidence_driver_score=evidence_driver_score,
        cost_driver_score=cost_driver_score,
        settlement_driver_score=settlement_driver_score,
        domain_memory_driver_score=domain_memory_driver_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchStrategyProbabilityGapAttributionConfig(**overrides)


def _build_report(*items, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_probability_gap_attribution_report(
        items,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_gap_attribution_rollup_aggregates_sanitized_driver_components() -> None:
    module = api()
    passing = _input()
    watched = _input(
        forecast_probability=d("0.650000"),
        benchmark_probability=d("0.500000"),
        observed_at=GENERATED_AT - timedelta(minutes=20),
        evidence_driver_score=d("0.450000"),
        cost_driver_score=d("0.300000"),
        settlement_driver_score=d("0.200000"),
        domain_memory_driver_score=d("0.150000"),
    )
    blocked = _input(
        forecast_probability=d("0.850000"),
        benchmark_probability=d("0.400000"),
        observed_at=GENERATED_AT - timedelta(minutes=30),
        evidence_driver_score=d("0.300000"),
        cost_driver_score=d("0.750000"),
        settlement_driver_score=d("0.700000"),
        domain_memory_driver_score=d("0.200000"),
    )

    report = _build_report(passing, watched, blocked)
    permuted = _build_report(blocked, passing, watched)
    payload = module.research_strategy_probability_gap_attribution_report_payload(report)
    permuted_payload = (
        module.research_strategy_probability_gap_attribution_report_payload(permuted)
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.attribution_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_forecast_probability == d("0.673333")
    assert report.average_benchmark_probability == d("0.466667")
    assert report.average_probability_gap_abs == d("0.206667")
    assert report.average_evidence_driver_score == d("0.283333")
    assert report.average_cost_driver_score == d("0.366667")
    assert report.average_settlement_driver_score == d("0.316667")
    assert report.average_domain_memory_driver_score == d("0.150000")
    assert report.dominant_driver == "cost"
    assert report.dominant_driver_score == d("0.366667")
    assert report.max_attribution_pressure == d("0.750000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked_row, watched_row, passing_row = report.rows
    assert blocked_row.rank == d("1.000000")
    assert blocked_row.probability_gap_abs == d("0.450000")
    assert blocked_row.probability_gap_direction == "forecast_above_benchmark"
    assert blocked_row.dominant_driver == "cost"
    assert blocked_row.dominant_driver_score == d("0.750000")
    assert blocked_row.attribution_pressure == d("0.750000")
    assert blocked_row.reason_codes == (
        "probability_gap_attribution_block",
        "gap_magnitude_block",
        "cost_driver_block",
        "settlement_driver_block",
    )
    assert watched_row.status == "watch"
    assert watched_row.reason_codes == (
        "probability_gap_attribution_watch",
        "gap_magnitude_watch",
        "evidence_driver_watch",
    )
    assert passing_row.status == "pass"
    assert passing_row.reason_codes == ("probability_gap_attribution_pass",)

    assert report.reason_codes == (
        "probability_gap_attribution_block",
        "probability_gap_attribution_watch",
        "probability_gap_attribution_pass",
        "gap_magnitude_block",
        "gap_magnitude_watch",
        "evidence_driver_watch",
        "cost_driver_block",
        "settlement_driver_block",
    )
    assert payload == permuted_payload
    assert payload["public_payload_digest"] == report.public_payload_digest
    assert report.public_payload_digest == (
        module.research_strategy_probability_gap_attribution_digest(report)
    )
    assert len(report.public_payload_digest) == 64
    int(report.public_payload_digest, 16)
    assert payload["rows"][0]["dominant_driver_score"] == "0.750000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _number_paths(payload) == ()
    assert _forbidden_key_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_gap_attribution_report_blocks_as_missing_inputs() -> None:
    module = api()
    generated_at = datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4)))

    report = _build_report(generated_at=generated_at)
    payload = module.research_strategy_probability_gap_attribution_report_payload(report)

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.attribution_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("probability_gap_attribution_missing_inputs",)
    assert payload["status"] == "block"
    assert payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert payload["rows"] == []
    assert payload["public_payload_digest"] == report.public_payload_digest


def test_decimal_frozen_flags_and_digest_tampering_are_validated() -> None:
    module = api()
    report = _build_report(_input())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        _input(forecast_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_driver_score must be a Decimal"):
        _input(cost_driver_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        _input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, public_payload_digest="0" * 64)
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, attribution_count=d("2.000000"))

    assert module.research_strategy_probability_gap_attribution_digest_payload(
        report,
    ) == module.research_strategy_probability_gap_attribution_digest_payload(
        _build_report(_input()),
    )


def test_datetime_and_threshold_validation_are_strict() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_strategy_probability_gap_attribution_report(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _input(observed_at=datetime(2026, 7, 8, 16, 0))

    class _NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _input(observed_at=datetime(2026, 7, 8, 16, 0, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        _build_report(_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="watch_probability_gap"):
        _config(
            watch_probability_gap=d("0.300000"),
            block_probability_gap=d("0.200000"),
        )
    with pytest.raises(ValueError, match="watch_driver_score"):
        _config(watch_driver_score=d("0.700000"), block_driver_score=d("0.600000"))


def test_public_payload_omits_raw_identifiers_and_action_surfaces() -> None:
    module = api()
    report = _build_report(_input())
    payload = module.research_strategy_probability_gap_attribution_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "candidate",
        "market",
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
        "buy",
        "sell",
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded


def test_module_scope_has_no_forbidden_runtime_or_literal_number_surfaces() -> None:
    module = api()
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    public_forbidden = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "database",
        "network",
        "auth",
        "live",
        "raw",
    )
    runtime_forbidden = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
        "open",
    )
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )

    for forbidden in public_forbidden:
        assert forbidden not in lowered
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in public_forbidden)
    for cls in (
        module.ResearchStrategyProbabilityGapAttributionConfig,
        module.ResearchStrategyProbabilityGapAttributionInput,
        module.ResearchStrategyProbabilityGapAttributionRow,
        module.ResearchStrategyProbabilityGapAttributionReasonCodeCount,
        module.ResearchStrategyProbabilityGapAttributionReport,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            assert not any(term in lowered_name for term in public_forbidden)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    assert not calls.intersection(runtime_forbidden)
    assert not imports.intersection(runtime_forbidden)
    assert not any(hasattr(module, name) for name in runtime_forbidden)


def _number_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) in (float, int, Decimal):
        return (path or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_number_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_number_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _forbidden_key_paths(value: object, path: str = "") -> tuple[str, ...]:
    forbidden = ("candidate", "market", "slug", "question", "url", "dsn", "table")
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            current_path = f"{path}.{key}" if path else str(key)
            if any(fragment in str(key).lower() for fragment in forbidden):
                paths.append(current_path)
            paths.extend(_forbidden_key_paths(item, current_path))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_forbidden_key_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
