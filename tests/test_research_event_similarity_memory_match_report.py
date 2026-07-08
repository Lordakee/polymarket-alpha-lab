from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_event_similarity_memory_match_report as api
from polymarket_alpha_lab.research_event_similarity_memory_match_report import (
    ResearchEventSimilarityMemoryMatchConfig,
    ResearchEventSimilarityMemoryMatchInput,
    ResearchEventSimilarityMemoryMatchReasonCodeCount,
    ResearchEventSimilarityMemoryMatchReport,
    ResearchEventSimilarityMemoryMatchRetrievalNeedCount,
    ResearchEventSimilarityMemoryMatchRow,
    build_research_event_similarity_memory_match_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def pair(
    event_ref: str = "event_pass",
    *,
    memory_ref: str = "memory_a",
    domain_similarity_score: Decimal = d("0.800000"),
    settlement_rule_similarity_score: Decimal = d("0.800000"),
    info_channel_similarity_score: Decimal = d("0.800000"),
    historical_error_score: Decimal = d("0.100000"),
    review_need_score: Decimal = d("0.100000"),
    memory_age_days: Decimal = d("10.000000"),
    local_supabase_retrieval_needed: bool = True,
    local_postgres_retrieval_needed: bool = False,
) -> ResearchEventSimilarityMemoryMatchInput:
    return ResearchEventSimilarityMemoryMatchInput(
        event_ref=event_ref,
        memory_ref=memory_ref,
        domain_similarity_score=domain_similarity_score,
        settlement_rule_similarity_score=settlement_rule_similarity_score,
        info_channel_similarity_score=info_channel_similarity_score,
        historical_error_score=historical_error_score,
        review_need_score=review_need_score,
        memory_age_days=memory_age_days,
        local_supabase_retrieval_needed=local_supabase_retrieval_needed,
        local_postgres_retrieval_needed=local_postgres_retrieval_needed,
    )


def report(
    *rows: ResearchEventSimilarityMemoryMatchInput,
    generated_at: datetime = NOW,
    config: ResearchEventSimilarityMemoryMatchConfig | None = None,
) -> ResearchEventSimilarityMemoryMatchReport:
    return build_research_event_similarity_memory_match_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_rows_score_domain_rule_info_error_review_and_rollups() -> None:
    result = report(
        pair(),
        pair(
            "event_watch",
            memory_ref="memory_b",
            domain_similarity_score=d("0.600000"),
            settlement_rule_similarity_score=d("0.600000"),
            info_channel_similarity_score=d("0.600000"),
            historical_error_score=d("0.200000"),
            review_need_score=d("0.200000"),
            local_supabase_retrieval_needed=False,
            local_postgres_retrieval_needed=True,
        ),
        pair(
            "event_block",
            memory_ref="memory_c",
            domain_similarity_score=d("0.800000"),
            settlement_rule_similarity_score=d("0.800000"),
            info_channel_similarity_score=d("0.800000"),
            historical_error_score=d("0.700000"),
            review_need_score=d("0.700000"),
            local_supabase_retrieval_needed=True,
            local_postgres_retrieval_needed=True,
        ),
    )

    assert tuple(row.event_ref for row in result.rows) == (
        "event_block",
        "event_pass",
        "event_watch",
    )

    blocked, passed, watched = result.rows
    assert blocked.composite_similarity_score == d("0.660000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "high_historical_error",
        "review_required",
    )
    assert blocked.retrieval_need_codes == (
        "local_supabase_similarity_lookup",
        "local_postgres_similarity_lookup",
    )

    assert passed.composite_similarity_score == d("0.820000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("memory_similarity_pass",)
    assert passed.retrieval_need_codes == ("local_supabase_similarity_lookup",)

    assert watched.composite_similarity_score == d("0.640000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "low_domain_similarity",
        "low_settlement_rule_similarity",
        "low_info_channel_similarity",
        "low_composite_similarity",
    )
    assert watched.retrieval_need_codes == ("local_postgres_similarity_lookup",)

    assert result.report_status == "block"
    assert result.pair_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.review_required_count == d("1.000000")
    assert result.high_historical_error_count == d("1.000000")
    assert result.local_supabase_retrieval_count == d("2.000000")
    assert result.local_postgres_retrieval_count == d("2.000000")
    assert result.min_composite_similarity_score == d("0.640000")
    assert result.max_historical_error_score == d("0.700000")
    assert result.max_review_need_score == d("0.700000")
    assert result.reason_code_counts == (
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "low_domain_similarity",
            d("1.000000"),
        ),
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "low_settlement_rule_similarity",
            d("1.000000"),
        ),
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "low_info_channel_similarity",
            d("1.000000"),
        ),
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "low_composite_similarity",
            d("1.000000"),
        ),
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "high_historical_error",
            d("1.000000"),
        ),
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "review_required",
            d("1.000000"),
        ),
        ResearchEventSimilarityMemoryMatchReasonCodeCount(
            "memory_similarity_pass",
            d("1.000000"),
        ),
    )
    assert result.retrieval_need_counts == (
        ResearchEventSimilarityMemoryMatchRetrievalNeedCount(
            "local_supabase_similarity_lookup",
            d("2.000000"),
        ),
        ResearchEventSimilarityMemoryMatchRetrievalNeedCount(
            "local_postgres_similarity_lookup",
            d("2.000000"),
        ),
    )


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    result = report()

    assert result.report_status == "empty"
    assert result.rows == ()
    assert result.reason_code_counts == ()
    assert result.retrieval_need_counts == ()
    assert result.pair_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.review_required_count == d("0.000000")
    assert result.high_historical_error_count == d("0.000000")
    assert result.local_supabase_retrieval_count == d("0.000000")
    assert result.local_postgres_retrieval_count == d("0.000000")
    assert result.min_composite_similarity_score == d("0.000000")
    assert result.max_historical_error_score == d("0.000000")
    assert result.max_review_need_score == d("0.000000")


def test_payload_is_safe_json_with_decimal_strings_and_digest() -> None:
    result = report(pair())

    payload = result.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["pair_count"] == "1.000000"
    assert payload["min_composite_similarity_score"] == "0.820000"
    assert payload["rows"][0]["domain_similarity_score"] == "0.800000"
    assert payload["rows"][0]["composite_similarity_score"] == "0.820000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["retrieval_need_counts"][0]["count"] == "1.000000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(result.derived_validation_digest) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(result)
    _assert_no_unsafe_public_payload_terms(payload)


def test_frozen_dataclasses_decimal_only_and_digest_tamper_checks() -> None:
    result = report(pair())

    for value in (
        ResearchEventSimilarityMemoryMatchConfig(),
        pair(),
        result.rows[0],
        result.reason_code_counts[0],
        result.retrieval_need_counts[0],
        result,
    ):
        assert hasattr(value, "__dataclass_fields__")
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="domain_similarity_score"):
        pair(domain_similarity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_similarity_score"):
        pair(domain_similarity_score=d("1.100000"))
    with pytest.raises(ValueError, match="historical_error_score"):
        pair(historical_error_score=d("-0.100000"))
    with pytest.raises(ValueError, match="memory_age_days"):
        pair(memory_age_days=d("1.500000"))
    with pytest.raises(ValueError, match="local_supabase_retrieval_needed"):
        pair(local_supabase_retrieval_needed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventSimilarityMemoryMatchConfig(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=())
    with pytest.raises(ValueError, match="unique"):
        report(pair(), pair(memory_ref="memory_a"))


def test_unsafe_surfaces_and_runtime_io_are_not_exposed() -> None:
    unsafe_terms = (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchEventSimilarityMemoryMatchConfig,
        ResearchEventSimilarityMemoryMatchInput,
        ResearchEventSimilarityMemoryMatchRow,
        ResearchEventSimilarityMemoryMatchReasonCodeCount,
        ResearchEventSimilarityMemoryMatchRetrievalNeedCount,
        ResearchEventSimilarityMemoryMatchReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "supabase",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    with pytest.raises(ValueError, match="unsafe public"):
        pair(event_ref="candidate_alpha")
    with pytest.raises(ValueError, match="unsafe public"):
        pair(memory_ref="https://example.test/alpha")


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_no_unsafe_public_payload_terms(value: object) -> None:
    unsafe_terms = (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in unsafe_terms)
            _assert_no_unsafe_public_payload_terms(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_unsafe_public_payload_terms(item)
        return
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in unsafe_terms)
