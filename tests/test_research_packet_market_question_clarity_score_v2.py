from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect
import json

import pytest

import polymarket_alpha_lab.research_packet_market_question_clarity_score_v2 as clarity


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def clear_input(
    *,
    market_reference: str = "market_alpha",
    resolution_criteria: str | None = None,
) -> clarity.ResearchPacketMarketQuestionClarityScoreV2Input:
    if resolution_criteria is None:
        resolution_criteria = (
            "Resolves yes if final official result shows Falcons score "
            "at least 21 points on 2026-09-01."
        )
    return clarity.ResearchPacketMarketQuestionClarityScoreV2Input(
        market_reference=market_reference,
        question="Will Falcons score at least 21 points by 2026-09-01?",
        resolution_criteria=resolution_criteria,
        source_config_version="research-packet-market-question-clarity-score-v2",
    )


def build_report(
    *inputs: clarity.ResearchPacketMarketQuestionClarityScoreV2Input,
) -> clarity.ResearchPacketMarketQuestionClarityScoreV2Report:
    return clarity.build_research_packet_market_question_clarity_score_v2(
        inputs or (clear_input(),),
        config=clarity.ResearchPacketMarketQuestionClarityScoreV2Config(),
        generated_at=GENERATED_AT,
    )


def test_question_clarity_scoring_passes_clear_measurable_questions() -> None:
    report = build_report()
    row = report.rows[0]

    assert row.clarity_status == "pass"
    assert row.question_clarity_score == Decimal("0.850000")
    assert row.measurable_resolution_score == Decimal("1.000000")
    assert row.vague_condition_penalty == Decimal("0.000000")
    assert row.reason_codes == ("question_clarity_pass",)
    assert report.row_count == Decimal("1")
    assert report.pass_count == Decimal("1")
    assert type(row.question_clarity_score) is Decimal


def test_measurable_resolution_boosts_question_clarity_score() -> None:
    without_resolution = build_report(
        clear_input(market_reference="market_without", resolution_criteria=""),
    ).rows[0]
    with_resolution = build_report(clear_input(market_reference="market_with")).rows[0]

    assert with_resolution.measurable_resolution_score > without_resolution.measurable_resolution_score
    assert with_resolution.question_clarity_score > without_resolution.question_clarity_score
    assert without_resolution.reason_codes == (
        "clarity_score_below_pass_threshold",
        "measurable_resolution_missing",
    )


def test_vague_condition_penalties_lower_question_clarity_score() -> None:
    clear_row = build_report(clear_input(market_reference="market_clear")).rows[0]
    vague_row = build_report(
        clarity.ResearchPacketMarketQuestionClarityScoreV2Input(
            market_reference="market_vague",
            question="Will the event have a significant major outcome soon?",
            resolution_criteria="Resolves yes if final result is present on 2026-09-01.",
            source_config_version="research-packet-market-question-clarity-score-v2",
        ),
    ).rows[0]

    assert vague_row.vague_condition_penalty == Decimal("0.240000")
    assert vague_row.question_clarity_score < clear_row.question_clarity_score
    assert "vague_conditions_detected" in vague_row.reason_codes
    assert vague_row.clarity_status == "watch"


def test_payload_serializes_decimal_values_as_strings() -> None:
    report = build_report()
    payload = clarity.research_packet_market_question_clarity_score_v2_payload(report)
    row_payload = payload["rows"][0]

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["row_count"] == "1"
    assert payload["average_question_clarity_score"] == "0.850000"
    assert row_payload["question_clarity_score"] == "0.850000"
    assert row_payload["measurable_resolution_score"] == "1.000000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    json.dumps(payload)
    assert_no_public_numbers(payload)


def test_dataclasses_are_frozen() -> None:
    report = build_report()

    with pytest.raises(FrozenInstanceError):
        report.rows[0].clarity_status = "blocked"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        report.reason_codes = ("tampered",)  # type: ignore[misc]


def test_hard_flags_are_required() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        clarity.ResearchPacketMarketQuestionClarityScoreV2Config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        clarity.ResearchPacketMarketQuestionClarityScoreV2Input(
            market_reference="market_alpha",
            question="Will Falcons score at least 21 points by 2026-09-01?",
            resolution_criteria="Final official result shows the score.",
            report_only=False,
        )

    payload = clarity.research_packet_market_question_clarity_score_v2_payload(build_report())
    payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        clarity.research_packet_market_question_clarity_score_v2_payload(payload)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    object.__setattr__(report, "pass_count", Decimal("0"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        clarity.research_packet_market_question_clarity_score_v2_payload(report)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    payload = clarity.research_packet_market_question_clarity_score_v2_payload(build_report())

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_key"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        clarity.research_packet_market_question_clarity_score_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["note"] = "buy instruction"
    with pytest.raises(ValueError, match="unsafe"):
        clarity.research_packet_market_question_clarity_score_v2_payload(
            unsafe_value_payload,
        )

    with pytest.raises(ValueError, match="unsafe"):
        clarity.ResearchPacketMarketQuestionClarityScoreV2Input(
            market_reference="market_alpha",
            question="Will users buy the item by 2026-09-01?",
            resolution_criteria="Final official result shows the outcome.",
        )


def test_module_exposes_no_unsafe_surfaces() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    public_names = set(clarity.__all__) | {
        name for name in dir(clarity) if not name.startswith("_")
    }

    assert not [
        name
        for name in public_names
        if any(term in name.lower() for term in unsafe_terms)
    ]

    source = inspect.getsource(clarity)
    tree = ast.parse(source)
    imported_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names.append(node.module or "")

    unsafe_import_fragments = (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "clob",
    )
    assert not [
        name
        for name in imported_names
        if any(fragment in name.lower() for fragment in unsafe_import_fragments)
    ]


def assert_no_public_numbers(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numbers(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numbers(item)
        return
    if type(value) is bool or value is None:
        return
    assert type(value) not in (int, float, Decimal)
