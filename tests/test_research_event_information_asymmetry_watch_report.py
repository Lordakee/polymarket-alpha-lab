from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_event_information_asymmetry_watch_report as api
from polymarket_alpha_lab.research_event_information_asymmetry_watch_report import (
    ResearchEventInformationAsymmetryWatchConfig,
    ResearchEventInformationAsymmetryWatchObservation,
    ResearchEventInformationAsymmetryWatchReport,
    build_research_event_information_asymmetry_watch_report,
    research_event_information_asymmetry_watch_report_payload,
    validate_research_event_information_asymmetry_watch_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    event_category: str,
    *,
    source_coverage_ratio: str = "0.900000",
    update_latency_hours: str = "1.000000",
    contradiction_rate: str = "0.050000",
    specialist_confidence_score: str = "0.850000",
    analysis_version: str = "analysis_v1",
) -> ResearchEventInformationAsymmetryWatchObservation:
    return ResearchEventInformationAsymmetryWatchObservation(
        event_category=event_category,
        source_coverage_ratio=d(source_coverage_ratio),
        update_latency_hours=d(update_latency_hours),
        contradiction_rate=d(contradiction_rate),
        specialist_confidence_score=d(specialist_confidence_score),
        analysis_version=analysis_version,
    )


def build_report(
    *observations: ResearchEventInformationAsymmetryWatchObservation,
    config: ResearchEventInformationAsymmetryWatchConfig | None = None,
) -> ResearchEventInformationAsymmetryWatchReport:
    return build_research_event_information_asymmetry_watch_report(
        observations,
        generated_at=GENERATED_AT,
        config=config or ResearchEventInformationAsymmetryWatchConfig(),
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


def test_flags_event_category_asymmetry_pass_watch_and_block() -> None:
    report = build_report(
        observation("baseball"),
        observation(
            "weather",
            source_coverage_ratio="0.600000",
            update_latency_hours="8.000000",
            contradiction_rate="0.250000",
            specialist_confidence_score="0.650000",
        ),
        observation(
            "politics",
            source_coverage_ratio="0.200000",
            update_latency_hours="36.000000",
            contradiction_rate="0.700000",
            specialist_confidence_score="0.100000",
        ),
    )

    assert report.status == "block"
    assert report.category_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_source_coverage_gap == d("0.800000")
    assert report.max_update_latency_hours == d("36.000000")
    assert report.max_contradiction_rate == d("0.700000")
    assert report.min_specialist_confidence_score == d("0.100000")
    assert report.average_information_asymmetry_risk_score == d("0.422917")

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.rank == d("2")
    assert block_row.event_category == "politics"
    assert block_row.source_coverage_gap == d("0.800000")
    assert block_row.update_latency_pressure == d("1.000000")
    assert block_row.specialist_confidence_gap == d("0.900000")
    assert block_row.information_asymmetry_risk_score == d("0.850000")
    assert block_row.reason_codes == (
        "source_coverage_gap_block",
        "update_latency_block",
        "contradiction_rate_block",
        "specialist_confidence_gap_block",
        "information_asymmetry_block",
    )

    assert watch_row.rank == d("3")
    assert watch_row.event_category == "weather"
    assert watch_row.source_coverage_gap == d("0.400000")
    assert watch_row.update_latency_pressure == d("0.333333")
    assert watch_row.specialist_confidence_gap == d("0.350000")
    assert watch_row.information_asymmetry_risk_score == d("0.333333")
    assert watch_row.reason_codes == (
        "source_coverage_gap_watch",
        "update_latency_watch",
        "contradiction_rate_watch",
        "specialist_confidence_gap_watch",
        "information_asymmetry_watch",
    )

    assert pass_row.rank == d("1")
    assert pass_row.event_category == "baseball"
    assert pass_row.reason_codes == ("information_asymmetry_pass",)


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    pass_obs = observation("baseball")
    watch_obs = observation(
        "weather",
        source_coverage_ratio="0.600000",
        update_latency_hours="8.000000",
        contradiction_rate="0.250000",
        specialist_confidence_score="0.650000",
    )
    block_obs = observation(
        "politics",
        source_coverage_ratio="0.200000",
        update_latency_hours="36.000000",
        contradiction_rate="0.700000",
        specialist_confidence_score="0.100000",
    )

    first = build_report(pass_obs, watch_obs, block_obs)
    second = build_report(block_obs, pass_obs, watch_obs)
    first_payload = research_event_information_asymmetry_watch_report_payload(first)
    second_payload = research_event_information_asymmetry_watch_report_payload(second)
    encoded_payload = json.dumps(first_payload, sort_keys=True)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in first.derived_validation_digest
    )
    assert first_payload["category_count"] == "3"
    assert first_payload["rows"][0]["information_asymmetry_risk_score"] == "0.850000"
    assert_no_public_numeric_scalars(first_payload)

    for unsafe_fragment in (
        "candidate_id",
        "candidate_reference",
        "raw_candidate",
        "raw_id",
        "market_id",
        "market_slug",
        "market_question",
        "question_text",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "private_key",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert unsafe_fragment not in encoded_payload.lower()

    numeric_payload = dict(first_payload)
    numeric_payload["category_count"] = 3
    with pytest.raises(ValueError, match="Decimal strings"):
        validate_research_event_information_asymmetry_watch_report_payload(
            numeric_payload,
        )

    for key, value in (
        ("candidate_id", "candidate-123"),
        ("market_slug", "secret-market"),
        ("source_url", "https://example.invalid/source"),
        ("safe_key", "source_text leaked"),
        ("safe_key", "wallet token private_key"),
        ("safe_key", "buy sell trade position"),
    ):
        tampered = dict(first_payload)
        tampered[key] = value
        with pytest.raises(ValueError, match="unsafe public payload"):
            validate_research_event_information_asymmetry_watch_report_payload(
                tampered,
            )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_frozen_decimal_only_hard_flags_and_validation() -> None:
    class TaggedDecimal(Decimal):
        pass

    class TaggedDatetime(datetime):
        pass

    assert tuple(api.STATUSES) == ("pass", "watch", "block")

    config = ResearchEventInformationAsymmetryWatchConfig()
    input_row = observation("validation")
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
        ResearchEventInformationAsymmetryWatchConfig(
            max_pass_update_latency_hours=4,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="Decimal"):
        ResearchEventInformationAsymmetryWatchObservation(
            event_category="bad-decimal",
            source_coverage_ratio=TaggedDecimal("0.9"),
            update_latency_hours=d("1"),
            contradiction_rate=d("0.1"),
            specialist_confidence_score=d("0.9"),
            analysis_version="analysis_v1",
        )
    with pytest.raises(ValueError, match="event_category"):
        observation(" ")
    with pytest.raises(ValueError, match="unsafe public payload"):
        observation("market_id:123")
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_information_asymmetry_watch_report(
            (input_row,),
            generated_at=TaggedDatetime(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=config,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_empty_report_is_blocked_report_only_and_module_has_no_side_effect_surfaces() -> None:
    empty = build_report()
    payload = research_event_information_asymmetry_watch_report_payload(empty)

    assert empty.status == "block"
    assert empty.category_count == d("0")
    assert empty.reason_codes == ("information_asymmetry_empty_input",)
    assert empty.reason_code_counts[0].reason_code == "information_asymmetry_empty_input"
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    source_path = Path(
        "src/polymarket_alpha_lab/"
        "research_event_information_asymmetry_watch_report.py",
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
