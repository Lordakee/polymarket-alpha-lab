from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_universe_discovery_report import (
    MarketUniverseDiscoveryCandidate,
    MarketUniverseDiscoveryConfig,
    MarketUniverseDiscoveryReasonCodeCount,
    MarketUniverseDiscoveryReport,
    MarketUniverseDiscoveryRow,
    build_research_market_universe_discovery_report,
    research_market_universe_discovery_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedCandidateShape:
    candidate_id: str
    domain: str
    liquidity_score: Decimal
    settlement_clarity_score: Decimal
    source_availability_score: Decimal
    domain_coverage_score: Decimal
    source_family_count: Decimal
    settlement_requires_manual_review: bool = False
    reason_codes: tuple[str, ...] = ()
    raw_market: str | None = None
    raw_candidate: str | None = None
    raw_source: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    dsn: str | None = None
    table: str | None = None
    token: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketUniverseDiscoveryConfig:
    values = {
        "config_version": "research-market-universe-discovery-report-v0",
        "min_domain_coverage_score": d("0.650000"),
        "min_liquidity_score": d("0.600000"),
        "min_settlement_clarity_score": d("0.700000"),
        "min_source_availability_score": d("0.650000"),
        "min_source_family_count": d("2"),
        "pass_candidate_score": d("0.750000"),
        "watch_candidate_score": d("0.450000"),
        "domain_coverage_weight": d("0.250000"),
        "liquidity_weight": d("0.300000"),
        "settlement_clarity_weight": d("0.250000"),
        "source_availability_weight": d("0.200000"),
        "manual_review_penalty": d("0.200000"),
    }
    values.update(overrides)
    return MarketUniverseDiscoveryConfig(**values)


def candidate(
    index: int,
    *,
    candidate_id: str | None = None,
    domain: str = "politics",
    liquidity_score: Decimal = d("0.900000"),
    settlement_clarity_score: Decimal = d("0.850000"),
    source_availability_score: Decimal = d("0.800000"),
    domain_coverage_score: Decimal = d("0.750000"),
    source_family_count: Decimal = d("3"),
    settlement_requires_manual_review: bool = False,
    reason_codes: tuple[str, ...] = (),
    raw_market: str | None = None,
    raw_candidate: str | None = None,
    raw_source: str | None = None,
    source_url: str | None = None,
    source_text: str | None = None,
    dsn: str | None = None,
    table: str | None = None,
    token: str | None = None,
) -> MarketUniverseDiscoveryCandidate:
    return MarketUniverseDiscoveryCandidate(
        candidate_id=candidate_id or f"candidate-{index:03d}",
        domain=domain,
        liquidity_score=liquidity_score,
        settlement_clarity_score=settlement_clarity_score,
        source_availability_score=source_availability_score,
        domain_coverage_score=domain_coverage_score,
        source_family_count=source_family_count,
        settlement_requires_manual_review=settlement_requires_manual_review,
        reason_codes=reason_codes,
        raw_market=raw_market,
        raw_candidate=raw_candidate,
        raw_source=raw_source,
        source_url=source_url,
        source_text=source_text,
        dsn=dsn,
        table=table,
        token=token,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketUniverseDiscoveryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketUniverseDiscoveryReport:
    return build_research_market_universe_discovery_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_summary() -> None:
    discovery_report = report(())

    assert type(discovery_report) is MarketUniverseDiscoveryReport
    assert discovery_report.generated_at == GENERATED_AT
    assert discovery_report.config_version == "research-market-universe-discovery-report-v0"
    assert discovery_report.candidate_count == d("0")
    assert discovery_report.pass_count == d("0")
    assert discovery_report.watch_count == d("0")
    assert discovery_report.blocked_count == d("0")
    assert discovery_report.average_candidate_score is None
    assert discovery_report.status == "blocked"
    assert discovery_report.reason_codes == ("no_market_universe_candidates",)
    assert discovery_report.reason_code_counts == (
        MarketUniverseDiscoveryReasonCodeCount(
            reason_code="no_market_universe_candidates",
            count=d("1"),
        ),
    )
    assert discovery_report.rows == ()
    assert discovery_report.paper_only is True
    assert discovery_report.report_only is True
    assert discovery_report.readonly is True


def test_candidates_score_pass_watch_block_with_deterministic_ordering() -> None:
    discovery_report = report(
        (
            candidate(
                3,
                candidate_id="thin-settlement",
                domain="sports",
                liquidity_score=d("0.620000"),
                settlement_clarity_score=d("0.500000"),
                source_availability_score=d("0.850000"),
                domain_coverage_score=d("0.680000"),
                source_family_count=d("2"),
                settlement_requires_manual_review=True,
            ),
            candidate(
                1,
                candidate_id="broad-election",
                domain="politics",
                liquidity_score=d("0.900000"),
                settlement_clarity_score=d("0.850000"),
                source_availability_score=d("0.800000"),
                domain_coverage_score=d("0.750000"),
                source_family_count=d("3"),
                reason_codes=("manual_screened",),
            ),
            candidate(
                2,
                candidate_id="illiquid-crypto",
                domain="crypto",
                liquidity_score=d("0.200000"),
                settlement_clarity_score=d("0.400000"),
                source_availability_score=d("0.300000"),
                domain_coverage_score=d("0.500000"),
                source_family_count=d("1"),
            ),
        ),
    )

    assert discovery_report.status == "blocked"
    assert discovery_report.candidate_count == d("3")
    assert discovery_report.pass_count == d("1")
    assert discovery_report.watch_count == d("1")
    assert discovery_report.blocked_count == d("1")
    assert discovery_report.average_candidate_score == d("0.542000")

    assert tuple(row.candidate_id for row in discovery_report.rows) == (
        "broad-election",
        "illiquid-crypto",
        "thin-settlement",
    )

    pass_row = discovery_report.rows[0]
    assert type(pass_row) is MarketUniverseDiscoveryRow
    assert pass_row.domain == "politics"
    assert pass_row.candidate_score == d("0.830000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "domain_coverage_supported",
        "input_manual_screened",
        "liquidity_supported",
        "market_universe_candidate_pass",
        "settlement_clarity_supported",
        "source_availability_supported",
    )

    blocked_row = discovery_report.rows[1]
    assert blocked_row.candidate_score == d("0.345000")
    assert blocked_row.status == "blocked"
    assert blocked_row.reason_codes == (
        "insufficient_domain_coverage",
        "insufficient_liquidity",
        "insufficient_settlement_clarity",
        "insufficient_source_availability",
        "market_universe_candidate_blocked",
        "not_enough_source_families",
    )

    watch_row = discovery_report.rows[2]
    assert watch_row.candidate_score == d("0.451000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "domain_coverage_supported",
        "insufficient_settlement_clarity",
        "liquidity_supported",
        "market_universe_candidate_watch",
        "settlement_manual_review_required",
        "source_availability_supported",
    )


def test_payload_is_json_ready_decimal_only_and_redacts_raw_sensitive_inputs() -> None:
    discovery_report = report(
        (
            candidate(
                1,
                raw_market="raw market title",
                raw_candidate="raw candidate blob",
                raw_source="exchange-source",
                source_url="https://example.invalid/market?token=secret",
                source_text="long source text",
                dsn="postgres://user:pass@localhost/db",
                table="raw_markets",
                token="secret-token",
            ),
        ),
    )

    payload = research_market_universe_discovery_report_payload(discovery_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["candidate_score"] == "0.830000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded

    forbidden_fragments = (
        "raw_market",
        "raw_candidate",
        "raw_source",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "https://",
        "postgres://",
        "secret",
        "raw market title",
        "long source text",
    )
    lowered_payload = encoded.lower()
    assert all(fragment not in lowered_payload for fragment in forbidden_fragments)
    assert "trade" not in lowered_payload
    assert "buy" not in lowered_payload
    assert "sell" not in lowered_payload


def test_validation_rejects_bad_types_unknown_enums_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="liquidity_score"):
        candidate(1, liquidity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_count"):
        candidate(1, source_family_count=d("1.5"))
    with pytest.raises(ValueError, match="liquidity_score"):
        candidate(1, liquidity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="domain"):
        candidate(1, domain="unknown")
    with pytest.raises(ValueError, match="generated_at"):
        report((candidate(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (candidate(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(1), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        report((candidate(1),), cfg=config(readonly=False))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    discovery_report = report((candidate(1),))

    with pytest.raises(FrozenInstanceError):
        discovery_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        discovery_report.rows[0].candidate_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="candidate_score"):
        replace(discovery_report.rows[0], candidate_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(discovery_report, status="blocked")


def test_owned_module_has_no_live_trading_network_filesystem_or_secret_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_universe_discovery_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "private_key",
        "order",
        "cancel",
        "replace_order",
        "create_order",
        "post(",
        "put(",
        "delete(",
        "insert ",
        "update ",
        "advice",
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
