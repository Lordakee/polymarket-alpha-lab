from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_probability_move_explanation_gap_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_probability_move_explanation_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    gap_key: str = "case_pass",
    *,
    probability_move_abs: Decimal = d("0.040000"),
    fresh_explanation_ratio: Decimal = d("0.900000"),
    catalyst_pressure_score: Decimal = d("0.100000"),
    liquidity_stress_score: Decimal = d("0.100000"),
    source_contradiction_score: Decimal = d("0.100000"),
    explanation_count: Decimal = d("4.000000"),
    stale_explanation_count: Decimal = d("0.000000"),
    observed_at: datetime = GENERATED_AT,
    public_context: str = "aggregate explanation coverage ok",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchProbabilityMoveExplanationGapInput(
        gap_key=gap_key,
        probability_move_abs=probability_move_abs,
        fresh_explanation_ratio=fresh_explanation_ratio,
        catalyst_pressure_score=catalyst_pressure_score,
        liquidity_stress_score=liquidity_stress_score,
        source_contradiction_score=source_contradiction_score,
        explanation_count=explanation_count,
        stale_explanation_count=stale_explanation_count,
        observed_at=observed_at,
        public_context=public_context,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchProbabilityMoveExplanationGapConfig(**overrides)


def _build_report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_probability_move_explanation_gap_report(
        rows,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_probability_move_explanation_gap_rollup_detects_pass_watch_block() -> None:
    module = api()
    pass_input = _input(
        "case_pass",
        probability_move_abs=d("0.040000"),
        fresh_explanation_ratio=d("0.900000"),
        catalyst_pressure_score=d("0.100000"),
        liquidity_stress_score=d("0.100000"),
        source_contradiction_score=d("0.100000"),
        explanation_count=d("4.000000"),
        stale_explanation_count=d("0.000000"),
    )
    watch_input = _input(
        "case_watch",
        probability_move_abs=d("0.090000"),
        fresh_explanation_ratio=d("0.500000"),
        catalyst_pressure_score=d("0.600000"),
        liquidity_stress_score=d("0.500000"),
        source_contradiction_score=d("0.400000"),
        explanation_count=d("2.000000"),
        stale_explanation_count=d("1.000000"),
    )
    block_input = _input(
        "case_block",
        probability_move_abs=d("0.180000"),
        fresh_explanation_ratio=d("0.150000"),
        catalyst_pressure_score=d("0.900000"),
        liquidity_stress_score=d("0.850000"),
        source_contradiction_score=d("0.900000"),
        explanation_count=d("1.000000"),
        stale_explanation_count=d("1.000000"),
    )

    report = _build_report(pass_input, watch_input, block_input)
    permuted = _build_report(block_input, pass_input, watch_input)
    payload = module.research_probability_move_explanation_gap_report_to_payload(report)
    permuted_payload = (
        module.research_probability_move_explanation_gap_report_to_payload(permuted)
    )

    assert is_dataclass(report)
    assert report.status == "block"
    assert report.gap_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.large_move_count == d("2.000000")
    assert report.stale_evidence_count == d("2.000000")
    assert report.catalyst_pressure_count == d("2.000000")
    assert report.liquidity_stress_count == d("2.000000")
    assert report.source_contradiction_count == d("2.000000")
    assert report.average_gap_score == d("0.527778")
    assert report.max_gap_score == d("0.930000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.gap_key for row in report.rows) == (
        "case_block",
        "case_watch",
        "case_pass",
    )

    blocked = report.rows[0]
    assert blocked.gap_score == d("0.930000")
    assert blocked.explanation_action == "withhold_until_public_explanation_gap_closes"
    assert blocked.reason_codes == (
        "probability_move_explanation_gap_block",
        "probability_move_without_fresh_explanation_block",
        "catalyst_pressure_unexplained_block",
        "liquidity_stress_unexplained_block",
        "source_contradiction_unresolved_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.gap_score == d("0.520000")
    assert watched.explanation_action == "refresh_public_aggregate_explanations"
    assert watched.reason_codes == (
        "probability_move_explanation_gap_watch",
        "probability_move_without_fresh_explanation_watch",
        "catalyst_pressure_unexplained_watch",
        "liquidity_stress_unexplained_watch",
        "source_contradiction_unresolved_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.gap_score == d("0.133333")
    assert passed.explanation_action == "maintain_public_explanation_monitoring"
    assert passed.reason_codes == ("probability_move_explanation_gap_pass",)

    assert report.reason_codes == (
        "probability_move_explanation_gap_block",
        "probability_move_explanation_gap_watch",
        "probability_move_explanation_gap_pass",
        "probability_move_without_fresh_explanation_block",
        "probability_move_without_fresh_explanation_watch",
        "catalyst_pressure_unexplained_block",
        "catalyst_pressure_unexplained_watch",
        "liquidity_stress_unexplained_block",
        "liquidity_stress_unexplained_watch",
        "source_contradiction_unresolved_block",
        "source_contradiction_unresolved_watch",
    )
    assert len(report.public_digest) == 64
    int(report.public_digest, 16)
    assert report.public_digest == module.research_probability_move_explanation_gap_digest(
        report,
    )
    assert payload == permuted_payload
    assert payload["public_digest"] == report.public_digest
    assert payload["rows"][0]["gap_score"] == "0.930000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    assert _forbidden_key_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_report_blocks_as_missing_public_explanations() -> None:
    module = api()
    local_generated_at = datetime(
        2026,
        7,
        8,
        12,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = _build_report(generated_at=local_generated_at)
    payload = module.research_probability_move_explanation_gap_report_to_payload(report)

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.gap_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "probability_move_explanation_gap_missing_inputs",
    )
    assert payload["status"] == "block"
    assert payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert payload["rows"] == []
    assert payload["public_digest"] == report.public_digest


def test_decimal_frozen_flags_and_consistency_are_validated() -> None:
    module = api()
    report = _build_report(_input())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="blocked")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="probability_move_abs must be a Decimal"):
        _input(probability_move_abs=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_explanation_ratio must be a Decimal"):
        _input(fresh_explanation_ratio=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_stress_score must be a Decimal"):
        _input(liquidity_stress_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="stale_explanation_count"):
        _input(explanation_count=d("1.000000"), stale_explanation_count=d("2.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        _input(paper_only=False)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="report_only must be True"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)


def test_datetime_and_config_thresholds_are_strict() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_probability_move_explanation_gap_report(
            (),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _input(observed_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="block_large_move_threshold"):
        _config(
            watch_large_move_threshold=d("0.150000"),
            block_large_move_threshold=d("0.100000"),
        )
    with pytest.raises(ValueError, match="watch_stale_explanation_ratio"):
        _config(
            watch_stale_explanation_ratio=d("0.200000"),
            block_stale_explanation_ratio=d("0.100000"),
        )
    with pytest.raises(ValueError, match="source_contradiction_block_threshold"):
        _config(
            source_contradiction_watch_threshold=d("0.900000"),
            source_contradiction_block_threshold=d("0.800000"),
        )


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("gap_key", "market_slug"),
        ("gap_key", "event_123"),
        ("gap_key", "source_abc"),
        ("public_context", "raw market slug appears"),
        ("public_context", "source url appears"),
        ("public_context", "recommend buying yes"),
        ("public_context", "wallet order token details"),
    ),
)
def test_public_surface_rejects_raw_identifiers_sources_and_advice(
    field_name: str,
    unsafe_value: str,
) -> None:
    values: dict[str, object] = {
        "gap_key": "case_safe",
        "probability_move_abs": d("0.040000"),
        "fresh_explanation_ratio": d("0.900000"),
        "catalyst_pressure_score": d("0.100000"),
        "liquidity_stress_score": d("0.100000"),
        "source_contradiction_score": d("0.100000"),
        "explanation_count": d("4.000000"),
        "stale_explanation_count": d("0.000000"),
        "observed_at": GENERATED_AT,
        "public_context": "aggregate explanation coverage ok",
    }
    values[field_name] = unsafe_value

    with pytest.raises(ValueError, match=field_name):
        api().ResearchProbabilityMoveExplanationGapInput(**values)


def test_report_payload_digest_is_deterministic_and_tamper_evident() -> None:
    module = api()
    row = _input(
        "case_watch",
        probability_move_abs=d("0.090000"),
        fresh_explanation_ratio=d("0.500000"),
        catalyst_pressure_score=d("0.600000"),
        liquidity_stress_score=d("0.500000"),
        source_contradiction_score=d("0.400000"),
        explanation_count=d("2.000000"),
        stale_explanation_count=d("1.000000"),
    )
    report = _build_report(row)
    rebuilt = _build_report(row)

    assert report.public_digest == rebuilt.public_digest
    assert module.research_probability_move_explanation_gap_digest_payload(report) == (
        module.research_probability_move_explanation_gap_digest_payload(rebuilt)
    )
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, watch_count=d("2.000000"))


def test_module_exposes_no_raw_identifier_or_live_execution_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    public_forbidden = (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "raw_event",
        "raw_market",
        "raw_source",
        "identifier",
        "recommendation",
        "sizing",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
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

    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in public_forbidden)
    for cls in (
        module.ResearchProbabilityMoveExplanationGapConfig,
        module.ResearchProbabilityMoveExplanationGapInput,
        module.ResearchProbabilityMoveExplanationGapRow,
        module.ResearchProbabilityMoveExplanationGapReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in public_forbidden)

    assert not calls.intersection(runtime_forbidden)
    assert not imports.intersection(runtime_forbidden)
    assert not any(hasattr(module, name) for name in runtime_forbidden)


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _forbidden_key_paths(value: object, path: str = "") -> tuple[str, ...]:
    forbidden = ("raw_event", "raw_market", "raw_source", "identifier")
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
