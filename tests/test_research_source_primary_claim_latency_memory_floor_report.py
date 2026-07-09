from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json

import pytest

import polymarket_alpha_lab.research_source_primary_claim_latency_memory_floor_report as api
from polymarket_alpha_lab.research_source_primary_claim_latency_memory_floor_report import (
    ResearchSourcePrimaryClaimLatencyMemoryFloorConfig,
    ResearchSourcePrimaryClaimLatencyMemoryFloorInput,
    ResearchSourcePrimaryClaimLatencyMemoryFloorReport,
    ResearchSourcePrimaryClaimLatencyMemoryFloorRow,
    build_research_source_primary_claim_latency_memory_floor_report,
    research_source_primary_claim_latency_memory_floor_report_digest,
    research_source_primary_claim_latency_memory_floor_report_payload,
)


NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def latency_input(
    claim_ref: str,
    capture_ref: str,
    *,
    observed_age_seconds: int,
    latency_seconds: int,
    memory_score: Decimal,
    primary: bool = True,
    authority_family_ref: str = "official_records",
) -> ResearchSourcePrimaryClaimLatencyMemoryFloorInput:
    observed_at = NOW - timedelta(seconds=observed_age_seconds)
    return ResearchSourcePrimaryClaimLatencyMemoryFloorInput(
        claim_ref=claim_ref,
        capture_ref=capture_ref,
        authority_family_ref=authority_family_ref,
        primary=primary,
        observed_at=observed_at,
        captured_at=observed_at + timedelta(seconds=latency_seconds),
        memory_score=memory_score,
    )


def report(
    *items: ResearchSourcePrimaryClaimLatencyMemoryFloorInput,
    config: ResearchSourcePrimaryClaimLatencyMemoryFloorConfig | None = None,
    generated_at: datetime = NOW,
) -> ResearchSourcePrimaryClaimLatencyMemoryFloorReport:
    return build_research_source_primary_claim_latency_memory_floor_report(
        items,
        config=config if config is not None else ResearchSourcePrimaryClaimLatencyMemoryFloorConfig(),
        generated_at=generated_at,
    )


def test_report_scores_latency_memory_floor_and_redacts_raw_refs() -> None:
    latency_report = report(
        latency_input(
            "candidate-alpha-market-slug-question",
            "https://private.example/source-text/alpha-a",
            observed_age_seconds=2000,
            latency_seconds=600,
            memory_score=d("0.800000"),
        ),
        latency_input(
            "candidate-alpha-market-slug-question",
            "https://private.example/source-text/alpha-b",
            observed_age_seconds=2100,
            latency_seconds=600,
            memory_score=d("0.900000"),
        ),
        latency_input(
            "candidate-beta-market-slug-question",
            "https://private.example/source-text/beta-a",
            observed_age_seconds=3000,
            latency_seconds=1200,
            memory_score=d("0.700000"),
        ),
        latency_input(
            "candidate-beta-market-slug-question",
            "https://private.example/source-text/beta-b",
            observed_age_seconds=3100,
            latency_seconds=1200,
            memory_score=d("0.710000"),
        ),
        latency_input(
            "candidate-gamma-market-slug-question",
            "https://private.example/source-text/gamma-a",
            observed_age_seconds=5000,
            latency_seconds=4000,
            memory_score=d("0.400000"),
        ),
        latency_input(
            "candidate-gamma-market-slug-question",
            "https://private.example/source-text/gamma-b",
            observed_age_seconds=5100,
            latency_seconds=4000,
            memory_score=d("0.450000"),
        ),
    )

    assert latency_report.status == "block"
    assert latency_report.claim_count == d("3.000000")
    assert latency_report.input_count == d("6.000000")
    assert latency_report.pass_count == d("1.000000")
    assert latency_report.watch_count == d("1.000000")
    assert latency_report.block_count == d("1.000000")
    assert latency_report.latency_breach_count == d("2.000000")
    assert latency_report.memory_floor_breach_count == d("2.000000")
    assert latency_report.average_latency_seconds == d("1933.333333")
    assert latency_report.average_memory_floor_score == d("0.633333")

    assert tuple(row.status for row in latency_report.rows) == ("block", "watch", "pass")
    blocked_row, watch_row, pass_row = latency_report.rows
    assert blocked_row.max_latency_seconds == d("4000.000000")
    assert blocked_row.memory_floor_score == d("0.400000")
    assert blocked_row.reason_codes == (
        "primary_claim_latency_block",
        "memory_floor_block",
    )
    assert watch_row.max_latency_seconds == d("1200.000000")
    assert watch_row.memory_floor_score == d("0.700000")
    assert watch_row.reason_codes == (
        "primary_claim_latency_watch",
        "memory_floor_watch",
    )
    assert pass_row.max_latency_seconds == d("600.000000")
    assert pass_row.memory_floor_score == d("0.800000")
    assert pass_row.reason_codes == ("primary_claim_latency_memory_floor_pass",)
    assert all(row.claim_digest.startswith("sha256:") for row in latency_report.rows)

    payload = research_source_primary_claim_latency_memory_floor_report_payload(
        latency_report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    for raw_fragment in (
        "candidate-alpha-market-slug-question",
        "candidate-beta-market-slug-question",
        "candidate-gamma-market-slug-question",
        "https://private.example/source-text",
    ):
        assert raw_fragment not in encoded
    _assert_payload_has_no_forbidden_public_surface(payload)


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    latency_report = report(
        latency_input(
            "candidate-alpha-market-slug-question",
            "https://private.example/source-text/alpha-a",
            observed_age_seconds=2000,
            latency_seconds=600,
            memory_score=d("0.800000"),
        ),
    )

    payload = research_source_primary_claim_latency_memory_floor_report_payload(
        latency_report,
    )
    payload_again = research_source_primary_claim_latency_memory_floor_report_payload(
        latency_report,
    )

    assert payload == payload_again
    assert payload["claim_count"] == "1.000000"
    assert payload["rows"][0]["max_latency_seconds"] == "600.000000"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["derived_validation_digest"] == latency_report.derived_validation_digest
    assert (
        research_source_primary_claim_latency_memory_floor_report_digest(latency_report)
        == latency_report.derived_validation_digest
    )
    assert len(latency_report.derived_validation_digest) == 64
    payload_without_digest = dict(payload)
    digest = payload_without_digest.pop("derived_validation_digest")
    expected_digest = sha256(
        json.dumps(
            payload_without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert digest == expected_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(latency_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(latency_report, derived_validation_digest="0" * 64)


def test_validation_rejects_bad_types_flags_statuses_and_time_edges() -> None:
    with pytest.raises(ValueError, match="memory_score"):
        latency_input(
            "candidate-alpha-market-slug-question",
            "https://private.example/source-text/alpha-a",
            observed_age_seconds=2000,
            latency_seconds=600,
            memory_score=_DecimalSubclass("0.800000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_primary_claim_latency_memory_floor_report(
            (),
            config=ResearchSourcePrimaryClaimLatencyMemoryFloorConfig(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_primary_claim_latency_memory_floor_report(
            (),
            config=ResearchSourcePrimaryClaimLatencyMemoryFloorConfig(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="captured_at"):
        ResearchSourcePrimaryClaimLatencyMemoryFloorInput(
            claim_ref="candidate-alpha-market-slug-question",
            capture_ref="https://private.example/source-text/alpha-a",
            authority_family_ref="official_records",
            primary=True,
            observed_at=NOW,
            captured_at=NOW - timedelta(seconds=1),
            memory_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="captured_at"):
        report(
            latency_input(
                "candidate-alpha-market-slug-question",
                "https://private.example/source-text/alpha-a",
                observed_age_seconds=100,
                latency_seconds=200,
                memory_score=d("0.800000"),
            ),
        )

    latency_report = report(
        latency_input(
            "candidate-alpha-market-slug-question",
            "https://private.example/source-text/alpha-a",
            observed_age_seconds=2000,
            latency_seconds=600,
            memory_score=d("0.800000"),
        ),
    )
    with pytest.raises(ValueError, match="status"):
        replace(latency_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(latency_report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="claim_count"):
        replace(latency_report, claim_count=d("2.000000"))


def test_public_dataclasses_are_frozen_and_do_not_expose_live_surfaces() -> None:
    latency_report = report(
        latency_input(
            "candidate-alpha-market-slug-question",
            "https://private.example/source-text/alpha-a",
            observed_age_seconds=2000,
            latency_seconds=600,
            memory_score=d("0.800000"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        latency_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        latency_report.rows[0].memory_floor_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourcePrimaryClaimLatencyMemoryFloorRow):
            pass

    forbidden_public_terms = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_public_terms)

    for cls in (
        ResearchSourcePrimaryClaimLatencyMemoryFloorConfig,
        ResearchSourcePrimaryClaimLatencyMemoryFloorInput,
        ResearchSourcePrimaryClaimLatencyMemoryFloorReport,
        ResearchSourcePrimaryClaimLatencyMemoryFloorRow,
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


def test_empty_input_blocks_report_only_with_decimal_zeroes() -> None:
    latency_report = report()

    assert latency_report.status == "block"
    assert latency_report.claim_count == d("0.000000")
    assert latency_report.input_count == d("0.000000")
    assert latency_report.rows == ()
    assert latency_report.reason_codes == ("empty_latency_memory_floor",)
    assert tuple(
        (count.reason_code, count.count)
        for count in latency_report.reason_code_counts
    ) == (("empty_latency_memory_floor", d("1.000000")),)
    assert latency_report.paper_only is True
    assert latency_report.report_only is True
    assert latency_report.readonly is True


def _assert_payload_has_no_forbidden_public_surface(value: object) -> None:
    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "http",
        "source_text",
        "source-url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "network",
        "database",
        "position",
        "sizing",
        "recommend",
        "buy",
        "sell",
        "live",
    )
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            _assert_payload_has_no_forbidden_public_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_payload_has_no_forbidden_public_surface(item)


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
