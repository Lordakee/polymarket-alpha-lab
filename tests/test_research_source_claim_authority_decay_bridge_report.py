from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_claim_authority_decay_bridge_report as api
from polymarket_alpha_lab.research_source_claim_authority_decay_bridge_report import (
    ResearchSourceClaimAuthorityDecayBridgeConfig,
    ResearchSourceClaimAuthorityDecayBridgeInput,
    ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount,
    ResearchSourceClaimAuthorityDecayBridgeReport,
    ResearchSourceClaimAuthorityDecayBridgeRow,
    build_research_source_claim_authority_decay_bridge_report,
    research_source_claim_authority_decay_bridge_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def bridge_input(
    index: int,
    *,
    candidate_id: str | None = None,
    claim_key: str = "claim_alpha",
    source_family: str = "official",
    observed_at: datetime | None = None,
    source_authority_score: Decimal = d("0.900000"),
    claim_confidence_score: Decimal = d("0.800000"),
    supports_claim: bool = True,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceClaimAuthorityDecayBridgeInput:
    return ResearchSourceClaimAuthorityDecayBridgeInput(
        candidate_id=candidate_id or f"raw-candidate-{index:03d}",
        claim_key=claim_key,
        source_family=source_family,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        source_authority_score=source_authority_score,
        claim_confidence_score=claim_confidence_score,
        supports_claim=supports_claim,
        reason_codes=reason_codes,
    )


def report(
    inputs: tuple[ResearchSourceClaimAuthorityDecayBridgeInput, ...],
    *,
    config: ResearchSourceClaimAuthorityDecayBridgeConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceClaimAuthorityDecayBridgeReport:
    return build_research_source_claim_authority_decay_bridge_report(
        inputs,
        generated_at=generated_at,
        config=config,
    )


def test_fresh_high_authority_independent_sources_pass_without_candidate_id_leakage() -> None:
    bridge_report = report(
        (
            bridge_input(
                1,
                candidate_id="raw-candidate-alpha",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                source_authority_score=d("0.900000"),
                claim_confidence_score=d("0.800000"),
            ),
            bridge_input(
                2,
                candidate_id="raw-candidate-beta",
                source_family="primary",
                observed_at=GENERATED_AT - timedelta(hours=1),
                source_authority_score=d("0.800000"),
                claim_confidence_score=d("0.900000"),
            ),
        ),
    )

    row = bridge_report.rows[0]
    payload = research_source_claim_authority_decay_bridge_report_payload(bridge_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert bridge_report.status == "pass"
    assert bridge_report.claim_count == d("1.000000")
    assert bridge_report.candidate_count == d("2.000000")
    assert bridge_report.pass_count == d("1.000000")
    assert bridge_report.watch_count == d("0.000000")
    assert bridge_report.block_count == d("0.000000")
    assert row.claim_key == "claim_alpha"
    assert row.candidate_count == d("2.000000")
    assert row.supporting_candidate_count == d("2.000000")
    assert row.source_family_count == d("2.000000")
    assert row.average_authority_score == d("0.850000")
    assert row.average_claim_confidence_score == d("0.850000")
    assert row.average_decay_factor == d("0.968750")
    assert row.bridge_score == d("0.823438")
    assert row.status == "pass"
    assert "authority_decay_bridge_pass" in row.reason_codes
    assert "fresh_authority_support" in row.reason_codes
    assert "raw-candidate-alpha" not in encoded
    assert "raw-candidate-beta" not in encoded
    assert "candidate_id" not in encoded
    assert bridge_report.paper_only is True
    assert bridge_report.report_only is True
    assert bridge_report.readonly is True


def test_decay_and_low_diversity_produce_only_pass_watch_block_statuses() -> None:
    bridge_report = report(
        (
            bridge_input(
                1,
                claim_key="claim_watch",
                source_family="official",
                source_authority_score=d("0.950000"),
                claim_confidence_score=d("0.950000"),
            ),
            bridge_input(
                2,
                claim_key="claim_block",
                source_family="proxy",
                observed_at=GENERATED_AT - timedelta(days=2),
                source_authority_score=d("0.200000"),
                claim_confidence_score=d("0.200000"),
            ),
        ),
    )

    rows = {row.claim_key: row for row in bridge_report.rows}

    assert bridge_report.status == "block"
    assert bridge_report.pass_count == d("0.000000")
    assert bridge_report.watch_count == d("1.000000")
    assert bridge_report.block_count == d("1.000000")
    assert rows["claim_watch"].status == "watch"
    assert rows["claim_watch"].source_family_count == d("1.000000")
    assert "source_family_bridge_watch" in rows["claim_watch"].reason_codes
    assert rows["claim_block"].status == "block"
    assert rows["claim_block"].average_decay_factor == d("0.000000")
    assert rows["claim_block"].bridge_score == d("0.000000")
    assert "decayed_authority_support" in rows["claim_block"].reason_codes
    assert {
        bridge_report.status,
        *(row.status for row in bridge_report.rows),
    } <= {"pass", "watch", "block"}


def test_empty_input_returns_block_report_with_digest_and_reason_count() -> None:
    bridge_report = report(())

    assert bridge_report.status == "block"
    assert bridge_report.claim_count == d("0.000000")
    assert bridge_report.candidate_count == d("0.000000")
    assert bridge_report.average_bridge_score is None
    assert bridge_report.min_bridge_score is None
    assert bridge_report.rows == ()
    assert bridge_report.reason_codes == ("empty_candidates",)
    assert bridge_report.reason_code_counts == (
        ResearchSourceClaimAuthorityDecayBridgeReasonCodeCount(
            reason_code="empty_candidates",
            count=d("1.000000"),
        ),
    )
    assert len(bridge_report.derived_validation_digest) == 64


def test_payload_is_deterministic_json_ready_and_digest_validated() -> None:
    bridge_report = report(
        (
            bridge_input(2, source_family="primary"),
            bridge_input(1, source_family="official"),
        ),
    )

    payload_one = research_source_claim_authority_decay_bridge_report_payload(
        bridge_report,
    )
    payload_two = research_source_claim_authority_decay_bridge_report_payload(
        bridge_report,
    )

    assert payload_one == payload_two
    json.dumps(payload_one, sort_keys=True)
    assert payload_one["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload_one["candidate_count"] == "2.000000"
    assert payload_one["rows"][0]["bridge_score"] == "0.881250"
    assert payload_one["derived_validation_digest"] == bridge_report.derived_validation_digest
    assert isinstance(payload_one["derived_validation_digest"], str)
    _assert_no_decimal_objects(payload_one)
    _assert_no_non_decimal_public_numbers(bridge_report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(bridge_report, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_exact_types_decimal_only_and_hard_flagged() -> None:
    bridge_report = report(
        (
            bridge_input(1, source_family="official"),
            bridge_input(2, source_family="primary"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        bridge_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        bridge_report.rows[0].bridge_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceClaimAuthorityDecayBridgeConfig):
            pass

    with pytest.raises(ValueError, match="pass_bridge_score"):
        ResearchSourceClaimAuthorityDecayBridgeConfig(
            pass_bridge_score=0.7,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="source_authority_score"):
        bridge_input(1, source_authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((bridge_input(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (bridge_input(1),),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="status"):
        replace(bridge_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceClaimAuthorityDecayBridgeConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(bridge_input(1), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(bridge_report, readonly=False)


def test_public_payload_has_no_sensitive_market_source_or_execution_surfaces() -> None:
    bridge_report = report(
        (
            bridge_input(
                1,
                candidate_id="raw-sensitive-candidate-001",
                source_family="official",
            ),
            bridge_input(
                2,
                candidate_id="raw-sensitive-candidate-002",
                source_family="primary",
            ),
        ),
    )
    payload = research_source_claim_authority_decay_bridge_report_payload(bridge_report)
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw-sensitive-candidate-001",
        "raw-sensitive-candidate-002",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in encoded

    for cls in (ResearchSourceClaimAuthorityDecayBridgeRow, ResearchSourceClaimAuthorityDecayBridgeReport):
        for field in fields(cls):
            lowered = field.name.lower()
            assert "candidate_id" not in lowered
            assert "market" not in lowered
            assert "slug" not in lowered
            assert "question" not in lowered
            assert "url" not in lowered
            assert not lowered.endswith("_text")
            assert "dsn" not in lowered
            assert "table" not in lowered
            assert "token" not in lowered
            assert "wallet" not in lowered
            assert "order" not in lowered
            assert "trade" not in lowered
            assert "recommendation" not in lowered
            assert "sizing" not in lowered

    with pytest.raises(ValueError, match="claim_key"):
        bridge_input(1, claim_key="market_slug_123")
    with pytest.raises(ValueError, match="reason_code"):
        bridge_input(1, reason_codes=("source_url_present",))

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_claim_authority_decay_bridge_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    for forbidden_name in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "connect(",
        "open(",
    ):
        assert forbidden_name not in source


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
