from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_historical_resolution_pattern_score"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_HISTORICAL_RESOLUTION_PATTERN_SCORE_CONFIG_VERSION
        ),
        "min_pass_pattern_score": d("0.750000"),
        "min_watch_pattern_score": d("0.500000"),
        "min_historical_event_count_for_pass": d("5.000000"),
        "min_historical_event_count_for_watch": d("2.000000"),
        "min_pass_outcome_similarity_score": d("0.700000"),
        "min_watch_outcome_similarity_score": d("0.400000"),
        "min_pass_resolution_rule_match_score": d("0.700000"),
        "min_watch_resolution_rule_match_score": d("0.400000"),
        "max_pass_historical_dispute_rate": d("0.100000"),
        "max_watch_historical_dispute_rate": d("0.300000"),
        "max_pass_historical_revision_rate": d("0.100000"),
        "max_watch_historical_revision_rate": d("0.250000"),
    }
    values.update(overrides)
    return module.CandidateDecisionHistoricalResolutionPatternScoreConfig(**values)


def candidate(
    redacted_candidate_ref: str = (
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    ),
    **overrides: object,
):
    module = api()
    values = {
        "redacted_candidate_ref": redacted_candidate_ref,
        "event_family_code": "macro-resolution",
        "historical_event_count": d("10.000000"),
        "outcome_similarity_score": d("0.900000"),
        "resolution_rule_match_score": d("0.850000"),
        "historical_dispute_rate": d("0.020000"),
        "historical_revision_rate": d("0.030000"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.CandidateDecisionHistoricalResolutionPatternScoreInput(**values)


def report(*candidates: object, cfg: object | None = None):
    module = api()
    return module.build_candidate_decision_historical_resolution_pattern_score_report(
        candidates,
        generated_at=GENERATED_AT,
        config=cfg if cfg is not None else config(),
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_scores_pass_watch_block_and_rolls_up_public_statuses() -> None:
    result = report(
        candidate(
            "candidate_ref_1111111111111111111111111111111111111111111111111111111111111111",
        ),
        candidate(
            "candidate_ref_2222222222222222222222222222222222222222222222222222222222222222",
            historical_event_count=d("3.000000"),
            outcome_similarity_score=d("0.650000"),
            historical_dispute_rate=d("0.150000"),
        ),
        candidate(
            "candidate_ref_3333333333333333333333333333333333333333333333333333333333333333",
            historical_event_count=d("1.000000"),
            outcome_similarity_score=d("0.300000"),
            resolution_rule_match_score=d("0.350000"),
            historical_dispute_rate=d("0.400000"),
            historical_revision_rate=d("0.300000"),
        ),
    )

    assert result.pattern_status == "block"
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert tuple(row.pattern_status for row in result.rows) == ("block", "watch", "pass")
    assert result.rows[0].pattern_score == ZERO
    assert result.rows[1].pattern_score == d("0.784000")
    assert result.rows[2].pattern_score == d("0.940000")
    assert result.rows[0].hard_blocker_codes == (
        "historical_event_count_block",
        "outcome_similarity_score_block",
        "resolution_rule_match_score_block",
        "historical_dispute_rate_block",
        "historical_revision_rate_block",
        "historical_resolution_pattern_score_block",
    )
    assert result.rows[1].reason_codes == (
        "historical_event_count_watch",
        "outcome_similarity_score_watch",
        "historical_dispute_rate_watch",
    )
    assert result.rows[2].reason_codes == ("historical_resolution_pattern_pass",)
    assert result.reason_codes == (
        "historical_event_count_block",
        "outcome_similarity_score_block",
        "resolution_rule_match_score_block",
        "historical_dispute_rate_block",
        "historical_revision_rate_block",
        "historical_resolution_pattern_score_block",
        "historical_event_count_watch",
        "outcome_similarity_score_watch",
        "historical_dispute_rate_watch",
        "historical_resolution_pattern_pass",
    )


def test_decimal_type_rejection_is_exact_and_dataclasses_are_frozen() -> None:
    module = api()
    result = report(candidate())

    for klass in (
        module.CandidateDecisionHistoricalResolutionPatternScoreConfig,
        module.CandidateDecisionHistoricalResolutionPatternScoreInput,
        module.CandidateDecisionHistoricalResolutionPatternScoreRow,
        module.CandidateDecisionHistoricalResolutionPatternReasonCodeCount,
        module.CandidateDecisionHistoricalResolutionPatternScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for record in (config(), candidate(), result.rows[0], result.reason_code_counts[0], result):
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            elif type(value) in (int, float):
                raise AssertionError(f"{field.name} must not be {type(value).__name__}")

    with pytest.raises(FrozenInstanceError):
        result.rows[0].pattern_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="historical_event_count"):
        candidate(historical_event_count=10)
    with pytest.raises(ValueError, match="outcome_similarity_score"):
        candidate(outcome_similarity_score=0.9)
    with pytest.raises(ValueError, match="resolution_rule_match_score"):
        candidate(resolution_rule_match_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="historical_event_count"):
        candidate(historical_event_count=d("2.500000"))


def test_leak_rejection_blocks_raw_identifiers_sources_and_execution_language() -> None:
    module = api()

    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        candidate("candidate:raw-event")
    with pytest.raises(ValueError, match="event_family_code"):
        candidate(event_family_code="market_id")
    with pytest.raises(ValueError, match="unsafe public payload"):
        candidate(reason_codes=("source_ref_hidden",))

    unsafe_payloads = (
        ({"candidate_id": "abc"}, "unsafe public payload key"),
        ({"market_slug": "raw-market"}, "unsafe public payload key"),
        ({"question": "will this resolve yes"}, "unsafe public payload key"),
        ({"source_url": "https://example.test/a"}, "unsafe public payload key"),
        ({"safe": "dsn=postgresql://local"}, "unsafe public payload value"),
        ({"safe": "records_table"}, "unsafe public payload value"),
        ({"safe": "private token"}, "unsafe public payload value"),
        ({"safe": "wallet credential"}, "unsafe public payload value"),
        ({"safe": "buy/sell recommendation"}, "unsafe public payload value"),
        ({"pattern_status": "blocked"}, "public status"),
        ({"candidate_count": 1}, "decimal strings"),
        ({"candidate_count": 1.0}, "decimal strings"),
    )
    for payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_historical_resolution_pattern_score_public_payload(
                payload,
            )


def test_hard_flags_are_required_and_visible_in_payload() -> None:
    module = api()
    result = report(candidate())
    payload = module.candidate_decision_historical_resolution_pattern_score_payload(result)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(candidate(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(result, paper_only=False)


def test_payload_is_deterministic_redacted_and_decimal_stringed() -> None:
    module = api()
    inputs = (
        candidate(
            "candidate_ref_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            historical_event_count=d("3.000000"),
        ),
        candidate(
            "candidate_ref_cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        ),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    first_payload = module.candidate_decision_historical_resolution_pattern_score_payload(first)
    second_payload = module.candidate_decision_historical_resolution_pattern_score_payload(second)

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table:",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommendation",
    ):
        assert forbidden not in rendered
    assert first_payload["candidate_count"] == "2.000000"
    assert first_payload["rows"][0]["pattern_status"] == "watch"
    assert first_payload["rows"][1]["pattern_status"] == "pass"
    assert_no_float_or_int_values(first_payload)


def test_report_digest_consistency_and_payload_validation() -> None:
    module = api()
    result = report(candidate())

    assert module.validate_candidate_decision_historical_resolution_pattern_score_public_payload(
        result.payload,
    ) is True
    assert_sha256(result.derived_validation_digest)
    assert result.report_sha256 == result.derived_validation_digest
    assert_sha256(result.rows[0].derived_validation_digest)
    assert result.rows[0].row_sha256 == result.rows[0].derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], pattern_score=d("0.123456"))
    with pytest.raises(ValueError, match="row_sha256"):
        replace(result.rows[0], row_sha256="0" * 64)
    with pytest.raises(ValueError, match="average_pattern_score"):
        replace(result, average_pattern_score=d("0.123456"))
    with pytest.raises(ValueError, match="report_sha256"):
        replace(result, report_sha256="0" * 64)


def test_empty_report_blocks_without_rows() -> None:
    empty = report()

    assert empty.pattern_status == "block"
    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.max_pattern_score == ZERO
    assert empty.min_pattern_score == ZERO
    assert empty.average_pattern_score == ZERO
    assert empty.reason_codes == ("historical_resolution_pattern_no_candidates",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()


def test_static_module_has_no_io_network_or_float_literals() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()

    assert "Paper-only report-only readonly" in module.BOUNDARY_STATEMENT
    assert "research-priority filtering only" in module.BOUNDARY_STATEMENT
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        ".write(",
        "private_key",
        "position_size",
        "execute_trade",
        "place_order",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_HISTORICAL_RESOLUTION_PATTERN_SCORE_CONFIG_VERSION",
        "BOUNDARY_STATEMENT",
        "CandidateDecisionHistoricalResolutionPatternScoreConfig",
        "CandidateDecisionHistoricalResolutionPatternScoreInput",
        "CandidateDecisionHistoricalResolutionPatternScoreRow",
        "CandidateDecisionHistoricalResolutionPatternReasonCodeCount",
        "CandidateDecisionHistoricalResolutionPatternScoreReport",
        "score_candidate_decision_historical_resolution_pattern",
        "build_candidate_decision_historical_resolution_pattern_score_report",
        "candidate_decision_historical_resolution_pattern_score_payload",
        "validate_candidate_decision_historical_resolution_pattern_score_public_payload",
    )
