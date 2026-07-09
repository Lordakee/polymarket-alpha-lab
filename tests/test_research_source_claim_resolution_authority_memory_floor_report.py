from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_claim_resolution_authority_memory_floor_report import (
    ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate,
    ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow,
    ResearchSourceClaimResolutionAuthorityMemoryFloorConfig,
    ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount,
    ResearchSourceClaimResolutionAuthorityMemoryFloorReport,
    build_research_source_claim_resolution_authority_memory_floor_report,
    research_source_claim_resolution_authority_memory_floor_report_payload,
    validate_research_source_claim_resolution_authority_memory_floor_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceClaimResolutionAuthorityMemoryFloorConfig:
    values = {
        "config_version": "research-source-claim-resolution-authority-memory-floor-report-v0",
        "min_authority_score": d("0.750000"),
        "min_memory_floor_count": d("2"),
        "min_independent_source_count": d("2"),
        "min_resolution_signal_count": d("1"),
        "pass_authority_floor_ratio": d("0.600000"),
        "watch_authority_floor_ratio": d("0.333333"),
        "stale_age_seconds": d("86400"),
    }
    values.update(overrides)
    return ResearchSourceClaimResolutionAuthorityMemoryFloorConfig(**values)


def candidate(
    index: int,
    *,
    claim_id: str = "claim-alpha-secret",
    market_id: str = "market-secret-001",
    market_slug: str = "will-hidden-market-resolve-yes",
    market_question: str = "Will this hidden market resolve yes?",
    source_url: str = "https://secret.example/resolution-source",
    source_text: str = "raw source text that must stay out of payloads",
    source_family: str = "official",
    authority_score: Decimal = d("0.900000"),
    memory_floor_count: Decimal = d("2"),
    independent_source_count: Decimal = d("2"),
    resolution_signal_count: Decimal = d("1"),
    observed_at: datetime | None = None,
) -> ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate:
    return ResearchSourceClaimResolutionAuthorityMemoryFloorCandidate(
        candidate_id=f"candidate-secret-{index:03d}",
        claim_id=claim_id,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_url=source_url,
        source_text=source_text,
        source_family=source_family,
        authority_score=authority_score,
        memory_floor_count=memory_floor_count,
        independent_source_count=independent_source_count,
        resolution_signal_count=resolution_signal_count,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceClaimResolutionAuthorityMemoryFloorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceClaimResolutionAuthorityMemoryFloorReport:
    return build_research_source_claim_resolution_authority_memory_floor_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_hard_flags() -> None:
    floor_report = report(())

    assert type(floor_report) is ResearchSourceClaimResolutionAuthorityMemoryFloorReport
    assert floor_report.generated_at == GENERATED_AT
    assert floor_report.config_version == (
        "research-source-claim-resolution-authority-memory-floor-report-v0"
    )
    assert floor_report.claim_count == d("0")
    assert floor_report.candidate_count == d("0")
    assert floor_report.pass_count == d("0")
    assert floor_report.watch_count == d("0")
    assert floor_report.block_count == d("0")
    assert floor_report.status == "block"
    assert floor_report.reason_codes == ("no_authority_memory_floor_candidates",)
    assert floor_report.reason_code_counts == (
        ResearchSourceClaimResolutionAuthorityMemoryFloorReasonCodeCount(
            reason_code="no_authority_memory_floor_candidates",
            count=d("1"),
        ),
    )
    assert floor_report.rows == ()
    assert floor_report.paper_only is True
    assert floor_report.report_only is True
    assert floor_report.readonly is True


def test_candidates_build_sanitized_rows_and_digest_payload_without_raw_values() -> None:
    floor_report = report(
        (
            candidate(
                3,
                authority_score=d("0.900000"),
                memory_floor_count=d("3"),
                independent_source_count=d("2"),
                resolution_signal_count=d("2"),
                observed_at=GENERATED_AT - timedelta(minutes=30),
            ),
            candidate(
                1,
                authority_score=d("0.800000"),
                memory_floor_count=d("2"),
                independent_source_count=d("2"),
                resolution_signal_count=d("1"),
                observed_at=GENERATED_AT - timedelta(hours=1),
            ),
            candidate(
                2,
                authority_score=d("0.400000"),
                memory_floor_count=d("1"),
                independent_source_count=d("1"),
                resolution_signal_count=d("0"),
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
            candidate(
                4,
                claim_id="claim-beta-secret",
                market_id="market-secret-002",
                market_slug="will-hidden-market-resolve-no",
                market_question="Will this hidden market resolve no?",
                source_url="https://secret.example/other-resolution-source",
                source_text="other raw source text that must stay out",
                source_family="discussion",
                authority_score=d("0.200000"),
                memory_floor_count=d("0"),
                independent_source_count=d("1"),
                resolution_signal_count=d("0"),
                observed_at=GENERATED_AT - timedelta(days=2),
            ),
        ),
    )

    alpha_digest = hashlib.sha256(b"claim-alpha-secret").hexdigest()
    beta_digest = hashlib.sha256(b"claim-beta-secret").hexdigest()

    assert floor_report.status == "block"
    assert floor_report.claim_count == d("2")
    assert floor_report.candidate_count == d("4")
    assert floor_report.pass_count == d("1")
    assert floor_report.watch_count == d("0")
    assert floor_report.block_count == d("1")
    assert tuple(row.claim_digest for row in floor_report.rows) == (
        alpha_digest,
        beta_digest,
    )

    alpha = floor_report.rows[0]
    assert type(alpha) is ResearchSourceClaimResolutionAuthorityMemoryFloorClaimRow
    assert alpha.candidate_count == d("3")
    assert alpha.authority_candidate_count == d("2")
    assert alpha.independent_source_count == d("2")
    assert alpha.memory_floor_count == d("3")
    assert alpha.resolution_signal_count == d("2")
    assert alpha.latest_observed_at == GENERATED_AT - timedelta(minutes=30)
    assert alpha.latest_authority_age_seconds == d("1800")
    assert alpha.average_authority_score == d("0.700000")
    assert alpha.authority_floor_ratio == d("0.666667")
    assert alpha.status == "pass"
    assert alpha.reason_codes == (
        "authority_candidates_present",
        "authority_floor_ratio_pass",
        "authority_memory_floor_pass",
        "fresh_authority_memory_floor",
        "independent_sources_met",
        "memory_floor_met",
        "resolution_signals_met",
    )

    beta = floor_report.rows[1]
    assert beta.claim_digest == beta_digest
    assert beta.candidate_count == d("1")
    assert beta.authority_candidate_count == d("0")
    assert beta.independent_source_count == d("1")
    assert beta.memory_floor_count == d("0")
    assert beta.resolution_signal_count == d("0")
    assert beta.latest_authority_age_seconds == d("172800")
    assert beta.average_authority_score == d("0.200000")
    assert beta.authority_floor_ratio == d("0.000000")
    assert beta.status == "block"
    assert beta.reason_codes == (
        "authority_floor_ratio_block",
        "authority_memory_floor_block",
        "independent_sources_below_minimum",
        "memory_floor_below_minimum",
        "no_authority_candidates",
        "resolution_signals_below_minimum",
        "stale_authority_memory_floor",
    )

    payload = research_source_claim_resolution_authority_memory_floor_report_payload(
        floor_report,
    )
    payload_again = research_source_claim_resolution_authority_memory_floor_report_payload(
        floor_report,
    )
    digest_payload = dict(payload)
    validation_digest = digest_payload.pop("validation_sha256")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    encoded_payload = json.dumps(payload, sort_keys=True)

    assert payload == payload_again
    assert validation_digest == expected_digest
    assert validate_research_source_claim_resolution_authority_memory_floor_report_payload(
        payload,
    )
    assert not validate_research_source_claim_resolution_authority_memory_floor_report_payload(
        {**payload, "status": "pass"},
    )
    assert payload["rows"][0]["claim_digest"] == alpha_digest
    assert payload["rows"][0]["candidate_count"] == "3"
    assert payload["rows"][0]["average_authority_score"] == "0.700000"
    assert not any(type(value) in (int, float) for value in _walk_payload_values(payload))
    assert "candidate_id" not in encoded_payload
    assert "market_id" not in encoded_payload
    assert "market_slug" not in encoded_payload
    assert "market_question" not in encoded_payload
    assert "source_url" not in encoded_payload
    assert "source_text" not in encoded_payload
    assert "claim-alpha-secret" not in encoded_payload
    assert "candidate-secret" not in encoded_payload
    assert "market-secret" not in encoded_payload
    assert "will-hidden-market" not in encoded_payload
    assert "secret.example" not in encoded_payload
    assert "raw source text" not in encoded_payload


def test_stale_authority_floor_watches_without_blocking() -> None:
    floor_report = report(
        (
            candidate(
                1,
                claim_id="claim-gamma-secret",
                authority_score=d("0.900000"),
                memory_floor_count=d("2"),
                independent_source_count=d("2"),
                resolution_signal_count=d("1"),
                observed_at=GENERATED_AT - timedelta(days=2),
            ),
        ),
    )

    assert floor_report.status == "watch"
    assert floor_report.pass_count == d("0")
    assert floor_report.watch_count == d("1")
    assert floor_report.block_count == d("0")
    assert floor_report.rows[0].status == "watch"
    assert floor_report.rows[0].reason_codes == (
        "authority_candidates_present",
        "authority_floor_ratio_pass",
        "authority_memory_floor_watch",
        "independent_sources_met",
        "memory_floor_met",
        "resolution_signals_met",
        "stale_authority_memory_floor",
    )


def test_validation_rejects_non_decimal_numbers_unknown_statuses_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="min_authority_score"):
        config(min_authority_score=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="pass_authority_floor_ratio"):
        config(pass_authority_floor_ratio=0.6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score"):
        candidate(1, authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        candidate(1, observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(1, observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((candidate(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="candidate_id"):
        replace(candidate(1), candidate_id=" candidate-secret-001")
    with pytest.raises(ValueError, match="status"):
        replace(report((candidate(1),)).rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(1), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)


def test_public_dataclasses_are_frozen() -> None:
    floor_report = report((candidate(1),))

    with pytest.raises(FrozenInstanceError):
        floor_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        floor_report.rows[0].status = "watch"  # type: ignore[misc]


def test_owned_module_has_no_io_trading_or_recommendation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_claim_resolution_authority_memory_floor_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "wallet",
        "order_id",
        "trade_id",
        "live_trading",
        "sizing",
        "recommendation",
        "dsn",
        "table_name",
        "api_key",
        "bearer",
        "token",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
