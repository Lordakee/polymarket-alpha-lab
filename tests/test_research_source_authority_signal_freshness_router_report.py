from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_authority_signal_freshness_router_report as api
from polymarket_alpha_lab.research_source_authority_signal_freshness_router_report import (
    ResearchSourceAuthoritySignalFreshnessRouterConfig,
    ResearchSourceAuthoritySignalFreshnessRouterInput,
    ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem,
    ResearchSourceAuthoritySignalFreshnessRouterReport,
    ResearchSourceAuthoritySignalFreshnessRouterRow,
    build_research_source_authority_signal_freshness_router_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _signal(
    *,
    raw_candidate_id: str = "candidate-private-123",
    raw_market_id: str = "market-private-456",
    raw_market_slug: str = "will-private-market-resolve",
    raw_market_question: str = "Will the private market resolve yes?",
    raw_source_reference: str = "https://news.example/path?token=secret",
    raw_source_excerpt: str | None = "raw source text with secret token",
    source_authority_score: Decimal = Decimal("0.800000"),
    signal_observed_at: datetime = NOW - timedelta(hours=1),
) -> ResearchSourceAuthoritySignalFreshnessRouterInput:
    return ResearchSourceAuthoritySignalFreshnessRouterInput(
        raw_candidate_id=raw_candidate_id,
        raw_market_id=raw_market_id,
        raw_market_slug=raw_market_slug,
        raw_market_question=raw_market_question,
        raw_source_reference=raw_source_reference,
        raw_source_excerpt=raw_source_excerpt,
        source_authority_score=source_authority_score,
        signal_observed_at=signal_observed_at,
    )


def _report(
    signals: tuple[ResearchSourceAuthoritySignalFreshnessRouterInput, ...],
    *,
    public_payload: tuple[
        ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem,
        ...,
    ] = (),
) -> ResearchSourceAuthoritySignalFreshnessRouterReport:
    return build_research_source_authority_signal_freshness_router_report(
        signals,
        generated_at=NOW,
        public_payload=public_payload,
    )


def test_router_status_counts_cover_pass_watch_and_block() -> None:
    report = _report(
        (
            _signal(raw_candidate_id="pass-candidate"),
            _signal(
                raw_candidate_id="watch-candidate",
                source_authority_score=Decimal("0.500000"),
            ),
            _signal(
                raw_candidate_id="block-candidate",
                signal_observed_at=NOW - timedelta(days=8),
            ),
        ),
    )

    assert report.router_status == "block"
    assert report.signal_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert {row.router_status for row in report.rows} == {"pass", "watch", "block"}
    assert set(report.reason_codes) >= {"router_pass", "router_watch", "router_block"}
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)


def test_payload_is_deterministic_decimal_string_only_and_redacted() -> None:
    first_signal = _signal(
        raw_candidate_id="candidate-alpha-raw",
        raw_market_id="market-alpha-raw",
        raw_market_slug="private-alpha-market-slug",
        raw_market_question="Will private alpha leak?",
        raw_source_reference="https://alpha.example/source?token=alpha-secret",
        raw_source_excerpt="alpha private source text",
        source_authority_score=Decimal("0.900000"),
    )
    second_signal = _signal(
        raw_candidate_id="candidate-beta-raw",
        raw_market_id="market-beta-raw",
        raw_market_slug="private-beta-market-slug",
        raw_market_question="Will private beta leak?",
        raw_source_reference="vendor://beta/private/source",
        raw_source_excerpt="beta private source text",
        source_authority_score=Decimal("0.500000"),
    )

    first = _report(
        (first_signal, second_signal),
        public_payload=(
            ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem(
                "safe_summary",
                "authority and freshness buckets only",
            ),
        ),
    )
    second = _report(
        (second_signal, first_signal),
        public_payload=(
            ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem(
                "safe_summary",
                "authority and freshness buckets only",
            ),
        ),
    )

    payload = first.payload
    assert payload == second.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["signal_count"] == "2.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    for row in payload["rows"]:
        signal_ref = row["signal_ref"]
        assert isinstance(signal_ref, str)
        assert signal_ref.startswith("sha256:")
        signal_digest = signal_ref.removeprefix("sha256:")
        assert len(signal_digest) == 64
        int(signal_digest, 16)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(first)

    public_blob = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate-alpha-raw",
        "candidate-beta-raw",
        "market-alpha-raw",
        "market-beta-raw",
        "private-alpha-market-slug",
        "private-beta-market-slug",
        "will private alpha leak",
        "will private beta leak",
        "https://alpha.example",
        "vendor://beta",
        "alpha private source text",
        "beta private source text",
        "token",
        "secret",
        "source_url",
        "source_text",
        "market_slug",
        "market_question",
    ):
        assert forbidden not in public_blob


def test_digest_and_public_payload_validation_reject_tampering() -> None:
    report = _report((_signal(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem(
                    "safe_summary",
                    "changed bucket summary",
                ),
            ),
        )

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth_token",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem(
                unsafe_key,
                "safe value",
            )

    for unsafe_value in (
        "https://example.test/source",
        "candidate_id=candidate-private-123",
        "market_slug=private-slug",
        "source_text=raw source text",
        "dsn=postgres://secret",
        "wallet surface",
        "order surface",
        "trade surface",
        "sizing surface",
        "recommendation surface",
        "auth token",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem(
                "safe_key",
                unsafe_value,
            )


def test_dataclasses_are_frozen_flags_are_hard_and_no_live_surfaces() -> None:
    report = _report((_signal(),))

    with pytest.raises(FrozenInstanceError):
        report.router_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(ResearchSourceAuthoritySignalFreshnessRouterReport):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceAuthoritySignalFreshnessRouterConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(_signal(), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    unsafe_surface_terms = (
        "database",
        "network",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "dsn",
        "table",
        "token",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_surface_terms)

    for cls in (
        ResearchSourceAuthoritySignalFreshnessRouterConfig,
        ResearchSourceAuthoritySignalFreshnessRouterPublicPayloadItem,
        ResearchSourceAuthoritySignalFreshnessRouterRow,
        ResearchSourceAuthoritySignalFreshnessRouterReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_surface_terms)

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
