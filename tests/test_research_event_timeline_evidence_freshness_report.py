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


MODULE_NAME = "polymarket_alpha_lab.research_event_timeline_evidence_freshness_report"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} should exist"
    return importlib.import_module(MODULE_NAME)


def aggregate(
    label: str,
    *,
    catalyst_hours: int = 48,
    evidence_age_hours: int = 2,
    source_update_age_hours: int = 1,
    expected_update_age_hours: int = -2,
    source_family_count: str | Decimal = "3",
    timeline_evidence_count: str | Decimal = "4",
    hard_recheck_flag: bool = False,
) -> Any:
    api = module()
    return api.ResearchEventTimelineEvidenceFreshnessReportInput(
        aggregate_label=label,
        catalyst_at=GENERATED_AT + timedelta(hours=catalyst_hours),
        latest_evidence_at=GENERATED_AT - timedelta(hours=evidence_age_hours),
        latest_source_update_at=GENERATED_AT - timedelta(hours=source_update_age_hours),
        expected_update_at=GENERATED_AT - timedelta(hours=expected_update_age_hours),
        source_family_count=(
            source_family_count
            if isinstance(source_family_count, Decimal)
            else d(source_family_count)
        ),
        timeline_evidence_count=(
            timeline_evidence_count
            if isinstance(timeline_evidence_count, Decimal)
            else d(timeline_evidence_count)
        ),
        hard_recheck_flag=hard_recheck_flag,
    )


def build_report(*rows: Any, config: Any | None = None) -> Any:
    api = module()
    return api.build_research_event_timeline_evidence_freshness_report(
        rows,
        generated_at=GENERATED_AT,
        config=config
        or api.ResearchEventTimelineEvidenceFreshnessReportConfig(),
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (Decimal, int, float)):
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


def test_aggregate_timeline_evidence_freshness_pass_watch_and_block() -> None:
    report = build_report(
        aggregate("aggregate-pass"),
        aggregate(
            "aggregate-watch",
            catalyst_hours=12,
            evidence_age_hours=12,
            source_update_age_hours=12,
            expected_update_age_hours=6,
            source_family_count="2",
            timeline_evidence_count="2",
        ),
        aggregate(
            "aggregate-block",
            catalyst_hours=2,
            evidence_age_hours=48,
            source_update_age_hours=48,
            expected_update_age_hours=48,
            source_family_count="1",
            timeline_evidence_count="1",
            hard_recheck_flag=True,
        ),
    )

    assert report.status == "block"
    assert report.aggregate_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.min_hours_until_catalyst == d("2.000000")
    assert report.max_stale_evidence_window_hours == d("48.000000")
    assert report.max_missing_update_pressure_hours == d("48.000000")
    assert report.max_source_recency_hours == d("48.000000")
    assert report.average_recheck_urgency_score == d("0.500000")

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    assert block_row.aggregate_public_label == "aggregate-001"
    assert block_row.hours_until_catalyst == d("2.000000")
    assert block_row.stale_evidence_window_hours == d("48.000000")
    assert block_row.missing_update_pressure_hours == d("48.000000")
    assert block_row.source_recency_hours == d("48.000000")
    assert block_row.source_family_count == d("1")
    assert block_row.timeline_evidence_count == d("1")
    assert block_row.recheck_urgency_score == d("1.000000")
    assert block_row.reason_codes == (
        "catalyst_timing_block",
        "stale_evidence_window_block",
        "missing_update_pressure_block",
        "source_recency_block",
        "coverage_block",
        "hard_recheck_flag",
        "timeline_evidence_freshness_block",
    )

    assert watch_row.recheck_urgency_score == d("0.500000")
    assert watch_row.reason_codes == (
        "catalyst_timing_watch",
        "stale_evidence_window_watch",
        "missing_update_pressure_watch",
        "source_recency_watch",
        "coverage_watch",
        "timeline_evidence_freshness_watch",
    )
    assert pass_row.recheck_urgency_score == d("0.000000")
    assert pass_row.reason_codes == ("timeline_evidence_freshness_pass",)


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    api = module()
    first = build_report(
        aggregate("safe-policy-c"),
        aggregate("safe-policy-a", catalyst_hours=12),
        aggregate(
            "safe-policy-b",
            catalyst_hours=2,
            evidence_age_hours=48,
            source_update_age_hours=48,
            expected_update_age_hours=48,
            source_family_count="1",
            timeline_evidence_count="1",
        ),
    )
    second = build_report(
        aggregate(
            "safe-policy-b",
            catalyst_hours=2,
            evidence_age_hours=48,
            source_update_age_hours=48,
            expected_update_age_hours=48,
            source_family_count="1",
            timeline_evidence_count="1",
        ),
        aggregate("safe-policy-c"),
        aggregate("safe-policy-a", catalyst_hours=12),
    )

    first_payload = api.research_event_timeline_evidence_freshness_report_public_payload(
        first,
    )
    second_payload = api.research_event_timeline_evidence_freshness_report_public_payload(
        second,
    )
    encoded_payload = json.dumps(first_payload, sort_keys=True)

    assert first.public_digest == second.public_digest
    assert first_payload == second_payload
    assert first_payload["public_digest"] == first.public_digest
    assert api.research_event_timeline_evidence_freshness_report_public_digest(
        first,
    ) == first.public_digest
    assert len(first.public_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.public_digest)
    assert_no_public_numeric_scalars(first_payload)

    assert "safe-policy-a" not in encoded_payload
    assert "safe-policy-b" not in encoded_payload
    assert "safe-policy-c" not in encoded_payload
    for unsafe_fragment in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "raw_id",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert unsafe_fragment not in encoded_payload.lower()

    numeric_payload = dict(first_payload)
    numeric_payload["aggregate_count"] = 3
    with pytest.raises(ValueError, match="Decimal strings"):
        api.validate_research_event_timeline_evidence_freshness_report_public_payload(
            numeric_payload,
        )

    leaky_payload = dict(first_payload)
    leaky_payload["market_slug"] = "secret-market"
    with pytest.raises(ValueError, match="unsafe public payload"):
        api.validate_research_event_timeline_evidence_freshness_report_public_payload(
            leaky_payload,
        )

    for key, value in (
        ("candidate_id", "candidate-123"),
        ("source_url", "https://example.invalid/source"),
        ("safe_key", "source_text leaked"),
        ("safe_key", "wallet token order"),
        ("safe_key", "buy sell trade position"),
    ):
        tampered = dict(first_payload)
        tampered[key] = value
        with pytest.raises(ValueError, match="unsafe public payload"):
            api.validate_research_event_timeline_evidence_freshness_report_public_payload(
                tampered,
            )

    with pytest.raises(ValueError, match="public_digest must match"):
        replace(first, public_digest="0" * 64)


def test_frozen_hard_flagged_decimal_only_records_and_validation() -> None:
    api = module()

    class TaggedDecimal(Decimal):
        pass

    class TaggedDatetime(datetime):
        pass

    config = api.ResearchEventTimelineEvidenceFreshnessReportConfig()
    input_row = aggregate("validation-aggregate")
    report = build_report(input_row)
    row = report.rows[0]

    for record in (config, input_row, row, report, report.reason_code_counts[0]):
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

    with pytest.raises(ValueError, match="Decimal"):
        api.ResearchEventTimelineEvidenceFreshnessReportConfig(
            max_pass_evidence_age_hours=6,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="Decimal"):
        aggregate("bad-decimal", source_family_count=TaggedDecimal("3"))
    with pytest.raises(ValueError, match="aggregate_label"):
        aggregate("market_slug:secret")
    with pytest.raises(ValueError, match="hard_recheck_flag"):
        aggregate("bad-bool", hard_recheck_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        api.build_research_event_timeline_evidence_freshness_report(
            (input_row,),
            generated_at=TaggedDatetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            config=config,
        )
    with pytest.raises(ValueError, match="latest_evidence_at"):
        aggregate("future-evidence", evidence_age_hours=-1)
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_empty_report_is_blocked_report_only_and_module_has_no_side_effect_surfaces() -> None:
    api = module()
    empty = build_report()
    payload = api.research_event_timeline_evidence_freshness_report_public_payload(empty)

    assert empty.status == "block"
    assert empty.aggregate_count == d("0")
    assert empty.reason_codes == ("timeline_evidence_freshness_empty",)
    assert empty.reason_code_counts[0].reason_code == "timeline_evidence_freshness_empty"
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    source_path = Path(
        "src/polymarket_alpha_lab/research_event_timeline_evidence_freshness_report.py",
    )
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
