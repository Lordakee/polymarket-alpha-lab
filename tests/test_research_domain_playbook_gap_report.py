from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_domain_playbook_gap_report as api
from polymarket_alpha_lab.research_domain_playbook_gap_report import (
    ResearchDomainPlaybookGapConfig,
    ResearchDomainPlaybookGapInput,
    ResearchDomainPlaybookGapReasonCodeCount,
    ResearchDomainPlaybookGapReport,
    ResearchDomainPlaybookGapRow,
    build_research_domain_playbook_gap_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def domain(
    domain_slug: str = "politics",
    *,
    playbook_coverage_count: Decimal = d("4.000000"),
    data_feed_coverage_count: Decimal = d("3.000000"),
    settlement_rule_coverage_count: Decimal = d("2.000000"),
    team_memory_coverage_count: Decimal = d("2.000000"),
) -> ResearchDomainPlaybookGapInput:
    return ResearchDomainPlaybookGapInput(
        domain_slug=domain_slug,
        playbook_coverage_count=playbook_coverage_count,
        data_feed_coverage_count=data_feed_coverage_count,
        settlement_rule_coverage_count=settlement_rule_coverage_count,
        team_memory_coverage_count=team_memory_coverage_count,
    )


def report(
    *rows: ResearchDomainPlaybookGapInput,
    generated_at: datetime = NOW,
    config: ResearchDomainPlaybookGapConfig | None = None,
) -> ResearchDomainPlaybookGapReport:
    return build_research_domain_playbook_gap_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_builds_ordered_domain_gap_rows_and_summary_status() -> None:
    result = report(
        domain(),
        domain(
            "btc",
            team_memory_coverage_count=d("1.000000"),
        ),
        domain("equity_index"),
        domain(
            "gold",
            settlement_rule_coverage_count=d("0.000000"),
        ),
        domain("soccer"),
    )

    assert tuple(row.domain_slug for row in result.rows) == (
        "politics",
        "btc",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
    )

    politics, btc, equity_index, gold, soccer, basketball = result.rows
    assert politics.status == "pass"
    assert politics.reason_codes == ("domain_playbook_gap_pass",)
    assert politics.gap_score == d("1.000000")

    assert btc.status == "watch"
    assert btc.reason_codes == ("team_memory_gap",)
    assert btc.gap_score == d("0.875000")

    assert equity_index.status == "pass"
    assert soccer.status == "pass"

    assert gold.status == "block"
    assert gold.reason_codes == ("settlement_rule_gap",)
    assert gold.gap_score == d("0.750000")

    assert basketball.status == "block"
    assert basketball.reason_codes == (
        "playbook_gap",
        "data_feed_gap",
        "settlement_rule_gap",
        "team_memory_gap",
    )
    assert basketball.gap_score == d("0.000000")

    assert result.report_status == "block"
    assert result.domain_count == d("6.000000")
    assert result.pass_count == d("3.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("2.000000")
    assert result.playbook_gap_count == d("1.000000")
    assert result.data_feed_gap_count == d("1.000000")
    assert result.settlement_rule_gap_count == d("2.000000")
    assert result.team_memory_gap_count == d("2.000000")
    assert result.min_gap_score == d("0.000000")
    assert result.reason_code_counts == (
        ResearchDomainPlaybookGapReasonCodeCount("playbook_gap", d("1.000000")),
        ResearchDomainPlaybookGapReasonCodeCount("data_feed_gap", d("1.000000")),
        ResearchDomainPlaybookGapReasonCodeCount("settlement_rule_gap", d("2.000000")),
        ResearchDomainPlaybookGapReasonCodeCount("team_memory_gap", d("2.000000")),
        ResearchDomainPlaybookGapReasonCodeCount(
            "domain_playbook_gap_pass",
            d("3.000000"),
        ),
    )


def test_payload_is_safe_json_with_decimal_strings_and_stable_digest() -> None:
    result = report(domain())

    payload = result.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["domain_count"] == "6.000000"
    assert payload["rows"][0]["playbook_coverage_count"] == "4.000000"
    assert payload["rows"][0]["gap_score"] == "1.000000"
    assert payload["rows"][-1]["domain_slug"] == "basketball"
    assert payload["rows"][-1]["status"] == "block"
    assert payload["reason_code_counts"][0]["count"] == "5.000000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(result.derived_validation_digest) == 64
    assert result.derived_validation_digest == report(domain()).derived_validation_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(result)


def test_frozen_dataclasses_decimal_only_and_consistency_checks() -> None:
    result = report(domain())

    for value in (
        ResearchDomainPlaybookGapConfig(),
        domain(),
        result.rows[0],
        result.reason_code_counts[0],
        result,
    ):
        assert hasattr(value, "__dataclass_fields__")
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="playbook_coverage_count"):
        domain(playbook_coverage_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="playbook_coverage_count"):
        domain(playbook_coverage_count=d("4.0000004"))
    with pytest.raises(ValueError, match="team_memory_coverage_count"):
        domain(team_memory_coverage_count=d("1.500000"))
    with pytest.raises(ValueError, match="data_feed_coverage_count"):
        domain(data_feed_coverage_count=d("-1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchDomainPlaybookGapConfig(paper_only=False)
    with pytest.raises(ValueError, match="duplicate domain_slug"):
        report(domain("btc"), domain("btc"))
    with pytest.raises(ValueError, match="supported domain_slug"):
        report(domain("unsupported_domain"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        replace(result, rows=())


def test_unsafe_public_surfaces_are_rejected() -> None:
    unsafe_terms = (
        "raw",
        "market",
        "candidate",
        "dsn",
        "table",
        "token",
        "auth",
        "wallet",
        "order",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchDomainPlaybookGapConfig,
        ResearchDomainPlaybookGapInput,
        ResearchDomainPlaybookGapRow,
        ResearchDomainPlaybookGapReasonCodeCount,
        ResearchDomainPlaybookGapReport,
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
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    with pytest.raises(ValueError, match="unsafe public"):
        domain("wallet_domain")


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
