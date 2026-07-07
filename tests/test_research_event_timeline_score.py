from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_timeline_score"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} should exist"
    return importlib.import_module(MODULE_NAME)


def event(
    research_reference: str,
    *,
    catalyst_hours: int = 48,
    source_available_age_hours: int = 2,
    source_capture_lag_hours: int = 1,
    evidence_age_hours: int = 1,
    resolution_hours: int = 72,
    resolution_time_clarity_score: Decimal = d("0.950000"),
) -> Any:
    api = module()
    source_available_age_hours = max(
        source_available_age_hours,
        source_capture_lag_hours + 1,
    )
    source_first_available_at = GENERATED_AT - timedelta(
        hours=source_available_age_hours,
    )
    return api.ResearchEventTimelineScoreInput(
        research_reference=research_reference,
        observed_at=GENERATED_AT - timedelta(hours=1),
        catalyst_at=GENERATED_AT + timedelta(hours=catalyst_hours),
        source_first_available_at=source_first_available_at,
        source_captured_at=source_first_available_at
        + timedelta(hours=source_capture_lag_hours),
        evidence_observed_at=GENERATED_AT - timedelta(hours=evidence_age_hours),
        expected_resolution_at=GENERATED_AT + timedelta(hours=resolution_hours),
        resolution_time_clarity_score=resolution_time_clarity_score,
    )


def build_report(*rows: Any, config: Any | None = None) -> Any:
    api = module()
    return api.build_research_event_timeline_score(
        rows,
        generated_at=GENERATED_AT,
        config=config or api.ResearchEventTimelineScoreConfig(),
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_scores_pass_watch_and_block_research_queue_statuses() -> None:
    report = build_report(
        event("candidate-pass"),
        event(
            "candidate-watch",
            catalyst_hours=12,
            source_capture_lag_hours=6,
            evidence_age_hours=10,
            resolution_hours=12,
            resolution_time_clarity_score=d("0.650000"),
        ),
        event(
            "candidate-block",
            catalyst_hours=2,
            source_capture_lag_hours=18,
            evidence_age_hours=30,
            resolution_hours=2,
            resolution_time_clarity_score=d("0.400000"),
        ),
    )

    assert report.status == "block"
    assert report.research_event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.min_hours_until_catalyst == d("2.000000")
    assert report.max_source_capture_lag_hours == d("18.000000")
    assert report.max_evidence_age_hours == d("30.000000")
    assert report.min_hours_until_resolution == d("2.000000")

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.redacted_research_reference.startswith("research:")
    assert block_row.hours_until_catalyst == d("2.000000")
    assert block_row.source_capture_lag_hours == d("18.000000")
    assert block_row.evidence_age_hours == d("30.000000")
    assert block_row.hours_until_resolution == d("2.000000")
    assert block_row.timeline_quality_score == d("0.000000")
    assert block_row.reason_codes == (
        "catalyst_timing_block",
        "source_lag_block",
        "evidence_staleness_block",
        "resolution_timing_block",
        "resolution_time_clarity_block",
    )
    assert watch_row.timeline_quality_score == d("0.500000")
    assert watch_row.reason_codes == (
        "catalyst_timing_watch",
        "source_lag_watch",
        "evidence_staleness_watch",
        "resolution_timing_watch",
        "resolution_time_clarity_watch",
    )
    assert pass_row.timeline_quality_score == d("1.000000")
    assert pass_row.reason_codes == ("event_timeline_quality_pass",)


def test_decimal_exact_type_rejection() -> None:
    api = module()

    class TaggedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="Decimal"):
        api.ResearchEventTimelineScoreConfig(
            min_pass_catalyst_lead_hours=24,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        event(
            "candidate-bad-decimal",
            resolution_time_clarity_score=TaggedDecimal("0.900000"),
        )

    report = build_report(event("candidate-row"))
    with pytest.raises(ValueError, match="Decimal"):
        replace(report.rows[0], timeline_quality_score=TaggedDecimal("1.000000"))


def test_public_payload_rejects_leaks_and_decimal_numbers() -> None:
    api = module()
    report = build_report(event("candidate-secret-123"))
    payload = api.research_event_timeline_score_public_payload(report)
    encoded_payload = json.dumps(payload, sort_keys=True)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert "candidate-secret-123" not in encoded_payload
    for unsafe_fragment in (
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert unsafe_fragment not in encoded_payload.lower()
    assert_no_public_numeric_scalars(payload)

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "secret-market"
    with pytest.raises(ValueError, match="unsafe public payload"):
        api.research_event_timeline_score_public_payload(unsafe_payload)

    for key, value in (
        ("candidate_id", "candidate-secret-123"),
        ("source_url", "https://example.invalid/source"),
        ("safe_key", "source_text: leaked"),
        ("safe_key", "postgres dsn table"),
        ("safe_key", "wallet token auth"),
        ("safe_key", "buy sell trade position"),
        ("safe_key", "final recommendation"),
    ):
        tampered = dict(payload)
        tampered[key] = value
        with pytest.raises(ValueError, match="unsafe public payload"):
            api.validate_research_event_timeline_score_public_payload(tampered)

    numeric_payload = dict(payload)
    numeric_payload["research_event_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        api.research_event_timeline_score_public_payload(numeric_payload)


def test_hard_flags_and_frozen_records_are_enforced() -> None:
    api = module()
    config = api.ResearchEventTimelineScoreConfig()
    input_row = event("candidate-flags")
    report = build_report(input_row)
    row = report.rows[0]

    for record in (config, input_row, row, report):
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen
        assert record.paper_only is True
        assert record.report_only is True
        assert record.readonly is True
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
        with pytest.raises(FrozenInstanceError):
            record.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_public_payload_output_is_deterministic() -> None:
    api = module()
    first = build_report(
        event("candidate-c"),
        event("candidate-a", catalyst_hours=12),
        event("candidate-b", catalyst_hours=2),
    )
    second = build_report(
        event("candidate-b", catalyst_hours=2),
        event("candidate-c"),
        event("candidate-a", catalyst_hours=12),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert api.research_event_timeline_score_public_payload(
        first,
    ) == api.research_event_timeline_score_public_payload(second)


def test_module_has_no_persistence_network_or_trading_surface() -> None:
    source_path = Path("src/polymarket_alpha_lab/research_event_timeline_score.py")
    source = source_path.read_text()
    tree = ast.parse(source)

    forbidden_imports = {
        "aiohttp",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
    }
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert not (imported_modules & forbidden_imports)
    assert not (call_names & forbidden_calls)
