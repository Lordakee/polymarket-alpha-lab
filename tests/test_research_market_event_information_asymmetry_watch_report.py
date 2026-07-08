from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_event_information_asymmetry_watch_report"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, f"{MODULE_NAME} should exist"
    return importlib.import_module(MODULE_NAME)


def observation(
    aggregate_key: str,
    *,
    evidence_freshness_gap_hours: str = "1.000000",
    required_source_class_count: str = "4",
    observed_source_class_count: str = "4",
    book_movement_ratio: str = "0.050000",
    evidence_attribution_ratio: str = "0.050000",
    contradiction_pressure_score: str = "0.100000",
    manual_review_urgency_score: str = "0.100000",
) -> Any:
    api = module()
    return api.ResearchMarketEventInformationAsymmetryWatchObservation(
        aggregate_key=aggregate_key,
        evidence_freshness_gap_hours=d(evidence_freshness_gap_hours),
        required_source_class_count=d(required_source_class_count),
        observed_source_class_count=d(observed_source_class_count),
        book_movement_ratio=d(book_movement_ratio),
        evidence_attribution_ratio=d(evidence_attribution_ratio),
        contradiction_pressure_score=d(contradiction_pressure_score),
        manual_review_urgency_score=d(manual_review_urgency_score),
    )


def build_report(*rows: Any, config: Any | None = None) -> Any:
    api = module()
    return api.build_research_market_event_information_asymmetry_watch_report(
        rows,
        generated_at=GENERATED_AT,
        config=config
        or api.ResearchMarketEventInformationAsymmetryWatchReportConfig(),
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


def test_aggregates_information_asymmetry_pass_watch_and_block() -> None:
    report = build_report(
        observation(
            "candidate-pass|market_id:11|market_slug:secret-pass|question:Will pass?",
        ),
        observation(
            "candidate-watch|market_id:22|market_slug:secret-watch|question:Will watch?",
            evidence_freshness_gap_hours="8.000000",
            observed_source_class_count="2",
            book_movement_ratio="0.300000",
            evidence_attribution_ratio="0.100000",
            contradiction_pressure_score="0.300000",
            manual_review_urgency_score="0.300000",
        ),
        observation(
            "candidate-block|market_id:33|market_slug:secret-block|question:Will block?",
            evidence_freshness_gap_hours="48.000000",
            observed_source_class_count="1",
            book_movement_ratio="0.700000",
            evidence_attribution_ratio="0.200000",
            contradiction_pressure_score="0.700000",
            manual_review_urgency_score="0.800000",
        ),
    )

    assert report.status == "block"
    assert report.aggregate_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.max_evidence_freshness_gap_hours == d("48.000000")
    assert report.max_source_class_coverage_gap == d("0.750000")
    assert report.max_unexplained_book_movement_ratio == d("0.500000")
    assert report.max_contradiction_pressure_score == d("0.700000")
    assert report.max_manual_review_urgency_score == d("0.800000")
    assert report.average_manual_review_urgency_score == d("0.400000")

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    assert block_row.aggregate_row_number == d("1")
    assert block_row.aggregate_key_hash.startswith("sha256:")
    assert len(block_row.aggregate_key_hash) == 71
    assert block_row.source_class_coverage_gap == d("0.750000")
    assert block_row.unexplained_book_movement_ratio == d("0.500000")
    assert block_row.information_asymmetry_risk_score == d("0.750000")
    assert block_row.reason_codes == (
        "evidence_freshness_gap_block",
        "source_class_coverage_gap_block",
        "book_movement_unexplained_by_evidence_block",
        "contradiction_pressure_block",
        "manual_review_urgency_block",
        "information_asymmetry_block",
    )

    assert watch_row.aggregate_row_number == d("3")
    assert watch_row.source_class_coverage_gap == d("0.500000")
    assert watch_row.unexplained_book_movement_ratio == d("0.200000")
    assert watch_row.information_asymmetry_risk_score == d("0.320000")
    assert watch_row.reason_codes == (
        "evidence_freshness_gap_watch",
        "source_class_coverage_gap_watch",
        "book_movement_unexplained_by_evidence_watch",
        "contradiction_pressure_watch",
        "manual_review_urgency_watch",
        "information_asymmetry_watch",
    )
    assert pass_row.aggregate_row_number == d("2")
    assert pass_row.reason_codes == ("information_asymmetry_pass",)


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    api = module()
    pass_obs = observation(
        "candidate-pass|market_id:11|market_slug:secret-pass|question:Will pass?",
    )
    watch_obs = observation(
        "candidate-watch|market_id:22|market_slug:secret-watch|question:Will watch?",
        evidence_freshness_gap_hours="8.000000",
        observed_source_class_count="2",
        book_movement_ratio="0.300000",
        evidence_attribution_ratio="0.100000",
        contradiction_pressure_score="0.300000",
        manual_review_urgency_score="0.300000",
    )
    block_obs = observation(
        "candidate-block|market_id:33|market_slug:secret-block|question:Will block?",
        evidence_freshness_gap_hours="48.000000",
        observed_source_class_count="1",
        book_movement_ratio="0.700000",
        evidence_attribution_ratio="0.200000",
        contradiction_pressure_score="0.700000",
        manual_review_urgency_score="0.800000",
    )

    first = build_report(pass_obs, watch_obs, block_obs)
    second = build_report(block_obs, pass_obs, watch_obs)
    first_payload = (
        api.research_market_event_information_asymmetry_watch_report_public_payload(
            first,
        )
    )
    second_payload = (
        api.research_market_event_information_asymmetry_watch_report_public_payload(
            second,
        )
    )
    encoded_payload = json.dumps(first_payload, sort_keys=True)

    assert first.public_digest == second.public_digest
    assert first_payload == second_payload
    assert first_payload["public_digest"] == first.public_digest
    assert api.research_market_event_information_asymmetry_watch_report_public_digest(
        first,
    ) == first.public_digest
    assert len(first.public_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.public_digest)
    assert_no_public_numeric_scalars(first_payload)

    for raw_fragment in (
        "candidate-pass",
        "candidate-watch",
        "candidate-block",
        "secret-pass",
        "secret-watch",
        "secret-block",
        "will pass",
        "will watch",
        "will block",
    ):
        assert raw_fragment not in encoded_payload.lower()
    for unsafe_fragment in (
        "candidate_id",
        "raw_candidate",
        "raw_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "http://",
        "https://",
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
    numeric_payload["aggregate_count"] = 3
    with pytest.raises(ValueError, match="Decimal strings"):
        api.validate_research_market_event_information_asymmetry_watch_report_public_payload(
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
            api.validate_research_market_event_information_asymmetry_watch_report_public_payload(
                tampered,
            )

    with pytest.raises(ValueError, match="public_digest must match"):
        replace(first, public_digest="0" * 64)


def test_frozen_decimal_only_hard_flags_and_validation() -> None:
    api = module()

    class TaggedDecimal(Decimal):
        pass

    class TaggedDatetime(datetime):
        pass

    assert tuple(api.STATUSES) == ("pass", "watch", "block")

    config = api.ResearchMarketEventInformationAsymmetryWatchReportConfig()
    input_row = observation("candidate-validation|market_id:44")
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
        api.ResearchMarketEventInformationAsymmetryWatchReportConfig(
            max_pass_evidence_freshness_gap_hours=4,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="Decimal"):
        api.ResearchMarketEventInformationAsymmetryWatchObservation(
            aggregate_key="bad-decimal",
            evidence_freshness_gap_hours=TaggedDecimal("1"),
            required_source_class_count=d("4"),
            observed_source_class_count=d("4"),
            book_movement_ratio=d("0.1"),
            evidence_attribution_ratio=d("0.1"),
            contradiction_pressure_score=d("0.1"),
            manual_review_urgency_score=d("0.1"),
        )
    with pytest.raises(ValueError, match="aggregate_key"):
        observation(" ")
    with pytest.raises(ValueError, match="generated_at"):
        api.build_research_market_event_information_asymmetry_watch_report(
            (input_row,),
            generated_at=TaggedDatetime(2026, 7, 8, 12, 0, tzinfo=UTC),
            config=config,
        )
    with pytest.raises(ValueError, match="observed_source_class_count"):
        observation(
            "coverage-overflow",
            required_source_class_count="2",
            observed_source_class_count="3",
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
    api = module()
    empty = build_report()
    payload = api.research_market_event_information_asymmetry_watch_report_public_payload(
        empty,
    )

    assert empty.status == "block"
    assert empty.aggregate_count == d("0")
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
        "research_market_event_information_asymmetry_watch_report.py",
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
