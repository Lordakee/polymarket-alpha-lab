from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_strategy_authority_claim_memory_router_report as api
from polymarket_alpha_lab.research_strategy_authority_claim_memory_router_report import (
    AuthorityClaimMemoryRouterConfig,
    AuthorityClaimMemoryRouterInput,
    AuthorityClaimMemoryRouterReport,
    build_research_strategy_authority_claim_memory_router_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _claim(
    *,
    claim_ref: str = "claim-alpha",
    authority_score: Decimal = Decimal("0.850000"),
    memory_match_score: Decimal = Decimal("0.800000"),
    contradiction_score: Decimal = Decimal("0.050000"),
    freshness_score: Decimal = Decimal("0.700000"),
) -> AuthorityClaimMemoryRouterInput:
    return AuthorityClaimMemoryRouterInput(
        claim_ref=claim_ref,
        observed_at=NOW,
        authority_score=authority_score,
        memory_match_score=memory_match_score,
        contradiction_score=contradiction_score,
        freshness_score=freshness_score,
    )


def _report(
    claims: tuple[AuthorityClaimMemoryRouterInput, ...],
    *,
    generated_at: datetime = NOW,
    config: AuthorityClaimMemoryRouterConfig | None = None,
) -> AuthorityClaimMemoryRouterReport:
    return build_research_strategy_authority_claim_memory_router_report(
        claims,
        generated_at=generated_at,
        config=config,
    )


def test_router_scores_claims_without_exposing_raw_claim_refs() -> None:
    report = _report(
        (
            _claim(claim_ref="claim-pass"),
            _claim(
                claim_ref="claim-watch",
                authority_score=Decimal("0.650000"),
                memory_match_score=Decimal("0.500000"),
                contradiction_score=Decimal("0.250000"),
                freshness_score=Decimal("0.550000"),
            ),
            _claim(
                claim_ref="claim-block",
                authority_score=Decimal("0.300000"),
                memory_match_score=Decimal("0.300000"),
                contradiction_score=Decimal("0.750000"),
                freshness_score=Decimal("0.200000"),
            ),
        ),
    )

    states = {row.state for row in report.rows}
    assert states == {"pass", "watch", "block"}
    assert report.state == "block"
    assert report.claim_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert all(row.claim_digest not in {"claim-pass", "claim-watch", "claim-block"} for row in report.rows)

    payload_json = json.dumps(report.payload, sort_keys=True)
    assert "claim-pass" not in payload_json
    assert "claim-watch" not in payload_json
    assert "claim-block" not in payload_json


def test_payload_is_deterministic_json_ready_and_decimal_only() -> None:
    first = _report(
        (
            _claim(claim_ref="claim-b"),
            _claim(claim_ref="claim-a"),
        ),
    )
    second = _report(
        (
            _claim(claim_ref="claim-a"),
            _claim(claim_ref="claim-b"),
        ),
    )

    assert first.payload == second.payload
    json.dumps(first.payload, sort_keys=True)
    assert first.payload["claim_count"] == "2.000000"
    assert first.payload["rows"][0]["router_score"] == "0.767500"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)


def test_frozen_dataclasses_reject_subclassing_and_enforce_hard_flags() -> None:
    report = _report((_claim(),))

    with pytest.raises(FrozenInstanceError):
        report.state = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(AuthorityClaimMemoryRouterConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        AuthorityClaimMemoryRouterConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _claim().__class__(
            claim_ref="claim-alpha",
            observed_at=NOW,
            authority_score=Decimal("0.850000"),
            memory_match_score=Decimal("0.800000"),
            contradiction_score=Decimal("0.050000"),
            freshness_score=Decimal("0.700000"),
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_decimal_only_inputs_and_status_domain_are_enforced() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _claim(authority_score=1)  # type: ignore[arg-type]

    report = _report((_claim(),))
    with pytest.raises(ValueError, match="state"):
        replace(report.rows[0], state="blocked")

    for row in report.rows:
        assert row.state in {"pass", "watch", "block"}
    assert report.state in {"pass", "watch", "block"}


def test_digest_validation_rejects_tampering() -> None:
    report = _report((_claim(),))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, public_memos=(api.PublicPayloadMemo("memo", "changed"),))


def test_public_payload_rejects_raw_sensitive_strings() -> None:
    unsafe_values = (
        "https://example.invalid/path",
        "postgres://user:secret@example.invalid/db",
        "token=secret",
        "raw table export",
        "wallet key",
        "network call",
        "live trading",
        "position sizing",
        "candidate raw text",
        "market raw text",
        "source raw text",
    )

    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe"):
            api.PublicPayloadMemo("memo", value)


def test_no_unsafe_public_surfaces_or_capability_imports_are_exposed() -> None:
    forbidden_public_terms = (
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "network",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )
    allowed_public_names = {
        "build_research_strategy_authority_claim_memory_router_report",
        "DEFAULT_RESEARCH_STRATEGY_AUTHORITY_CLAIM_MEMORY_ROUTER_REPORT_VERSION",
        "AuthorityClaimMemoryRouterConfig",
        "AuthorityClaimMemoryRouterInput",
        "AuthorityClaimMemoryRouterRow",
        "AuthorityClaimMemoryRouterReport",
        "PublicPayloadMemo",
    }
    assert set(api.__all__) == allowed_public_names
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        AuthorityClaimMemoryRouterConfig,
        AuthorityClaimMemoryRouterInput,
        api.AuthorityClaimMemoryRouterRow,
        AuthorityClaimMemoryRouterReport,
        api.PublicPayloadMemo,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_terms)

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
