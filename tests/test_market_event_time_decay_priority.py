from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_event_time_decay_priority import (
    MarketEventTimeDecayPriorityDigestCandidate,
    MarketEventTimeDecayPriorityDigestConfig,
    build_market_event_time_decay_priority_digest,
    market_event_time_decay_priority_digest_payload,
)


def _candidate(
    ref_suffix: str,
    *,
    hours_to_close: str,
    last_evidence_refresh_age_hours: str,
    upcoming_catalyst_hours: str,
    liquidity_decay_risk: str,
    settlement_revision_window_hours: str,
    evidence_staleness: str,
    reason_codes: tuple[str, ...] | None = None,
) -> MarketEventTimeDecayPriorityDigestCandidate:
    return MarketEventTimeDecayPriorityDigestCandidate(
        redacted_market_ref=f"redacted_market_ref_{ref_suffix}",
        hours_to_close=Decimal(hours_to_close),
        last_evidence_refresh_age_hours=Decimal(last_evidence_refresh_age_hours),
        upcoming_catalyst_hours=Decimal(upcoming_catalyst_hours),
        liquidity_decay_risk=Decimal(liquidity_decay_risk),
        settlement_revision_window_hours=Decimal(settlement_revision_window_hours),
        evidence_staleness=Decimal(evidence_staleness),
        reason_codes=reason_codes if reason_codes is not None else (f"seed_{ref_suffix}",),
    )


def _assert_payload_safe(value: object) -> None:
    unsafe_fragments = (
        "auth",
        "wallet",
        "order",
        "recommend",
        "position",
        "sizing",
        "network",
        "database",
        "env",
        "file",
        "persist",
        "write",
        "trade",
        "trading",
        "slug",
        "question",
        "url",
        "http",
        "polymarket.com",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert all(fragment not in lowered_key for fragment in unsafe_fragments)
            _assert_payload_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_payload_safe(item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        assert all(fragment not in lowered_value for fragment in unsafe_fragments)


def test_build_digest_outputs_research_priority_support_without_execution_surface() -> None:
    report = build_market_event_time_decay_priority_digest(
        (
            _candidate(
                "watch",
                hours_to_close="40",
                last_evidence_refresh_age_hours="18",
                upcoming_catalyst_hours="20",
                liquidity_decay_risk="0.500000",
                settlement_revision_window_hours="18",
                evidence_staleness="0.450000",
            ),
            _candidate(
                "blocked",
                hours_to_close="12",
                last_evidence_refresh_age_hours="80",
                upcoming_catalyst_hours="6",
                liquidity_decay_risk="0.900000",
                settlement_revision_window_hours="5",
                evidence_staleness="0.950000",
            ),
            _candidate(
                "research",
                hours_to_close="6",
                last_evidence_refresh_age_hours="10",
                upcoming_catalyst_hours="4",
                liquidity_decay_risk="0.850000",
                settlement_revision_window_hours="8",
                evidence_staleness="0.550000",
            ),
            _candidate(
                "quiet",
                hours_to_close="200",
                last_evidence_refresh_age_hours="2",
                upcoming_catalyst_hours="200",
                liquidity_decay_risk="0.050000",
                settlement_revision_window_hours="96",
                evidence_staleness="0.050000",
            ),
        ),
        config=MarketEventTimeDecayPriorityDigestConfig(),
    )

    assert report.candidate_count == Decimal("4.000000")
    assert report.research_now_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.no_action_count == Decimal("1.000000")
    assert report.status == "block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert [row.redacted_market_ref for row in report.rows] == [
        "redacted_market_ref_research",
        "redacted_market_ref_blocked",
        "redacted_market_ref_watch",
        "redacted_market_ref_quiet",
    ]
    assert [row.research_priority_status for row in report.rows] == [
        "research_now",
        "block",
        "watch",
        "no_action",
    ]
    assert report.rows[0].priority_score > report.rows[2].priority_score
    assert "research_time_decay_research_now" in report.rows[0].reason_codes
    assert "research_blocked_evidence_stale" in report.rows[1].reason_codes
    assert "research_time_decay_watch" in report.rows[2].reason_codes
    assert "research_time_decay_no_action" in report.rows[3].reason_codes

    payload = market_event_time_decay_priority_digest_payload(report)

    assert payload["candidate_count"] == "4.000000"
    assert payload["research_now_count"] == "1.000000"
    assert payload["block_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["priority_score"] == "0.690834"
    assert payload["rows"][0]["research_priority_support"] == (
        "phase_1_research_priority_only_no_execution"
    )
    _assert_payload_safe(payload)


def test_report_status_uses_research_priority_vocabulary_for_block_rows() -> None:
    report = build_market_event_time_decay_priority_digest(
        (
            _candidate(
                "block_vocab",
                hours_to_close="12",
                last_evidence_refresh_age_hours="80",
                upcoming_catalyst_hours="6",
                liquidity_decay_risk="0.900000",
                settlement_revision_window_hours="5",
                evidence_staleness="0.950000",
            ),
        ),
        config=MarketEventTimeDecayPriorityDigestConfig(),
    )

    payload = market_event_time_decay_priority_digest_payload(report)
    public_statuses = {
        payload["status"],
        *(row["research_priority_status"] for row in payload["rows"]),
    }

    assert report.status == "block"
    assert public_statuses <= {"research_now", "watch", "block", "no_action"}
    assert "blocked" not in public_statuses


def test_payload_count_fields_are_six_decimal_strings() -> None:
    report = build_market_event_time_decay_priority_digest(
        (
            _candidate(
                "research_count",
                hours_to_close="6",
                last_evidence_refresh_age_hours="10",
                upcoming_catalyst_hours="4",
                liquidity_decay_risk="0.850000",
                settlement_revision_window_hours="8",
                evidence_staleness="0.550000",
            ),
            _candidate(
                "quiet_count",
                hours_to_close="200",
                last_evidence_refresh_age_hours="2",
                upcoming_catalyst_hours="200",
                liquidity_decay_risk="0.050000",
                settlement_revision_window_hours="96",
                evidence_staleness="0.050000",
            ),
        ),
        config=MarketEventTimeDecayPriorityDigestConfig(),
    )

    payload = market_event_time_decay_priority_digest_payload(report)

    assert payload["candidate_count"] == "2.000000"
    assert payload["research_now_count"] == "1.000000"
    assert payload["block_count"] == "0.000000"
    assert payload["watch_count"] == "0.000000"
    assert payload["no_action_count"] == "1.000000"


def test_digest_dataclasses_are_frozen_and_accept_decimal_inputs_only() -> None:
    candidate = _candidate(
        "frozen",
        hours_to_close="24",
        last_evidence_refresh_age_hours="4",
        upcoming_catalyst_hours="12",
        liquidity_decay_risk="0.100000",
        settlement_revision_window_hours="48",
        evidence_staleness="0.100000",
    )

    with pytest.raises(FrozenInstanceError):
        candidate.hours_to_close = Decimal("12")

    with pytest.raises(ValueError, match="hours_to_close must be a Decimal"):
        MarketEventTimeDecayPriorityDigestCandidate(
            redacted_market_ref="redacted_market_ref_int",
            hours_to_close=24,
            last_evidence_refresh_age_hours=Decimal("4"),
            upcoming_catalyst_hours=Decimal("12"),
            liquidity_decay_risk=Decimal("0.100000"),
            settlement_revision_window_hours=Decimal("48"),
            evidence_staleness=Decimal("0.100000"),
            reason_codes=("seed_int",),
        )


def test_rejects_raw_market_references_and_unsafe_flags_or_rows() -> None:
    with pytest.raises(ValueError, match="redacted_market_ref must be redacted"):
        MarketEventTimeDecayPriorityDigestCandidate(
            redacted_market_ref="will-fed-cut-rates-july",
            hours_to_close=Decimal("24"),
            last_evidence_refresh_age_hours=Decimal("4"),
            upcoming_catalyst_hours=Decimal("12"),
            liquidity_decay_risk=Decimal("0.100000"),
            settlement_revision_window_hours=Decimal("48"),
            evidence_staleness=Decimal("0.100000"),
            reason_codes=("seed_slug",),
        )

    with pytest.raises(ValueError, match="must not contain URLs"):
        MarketEventTimeDecayPriorityDigestCandidate(
            redacted_market_ref="redacted_market_ref_https://polymarket.com/market/raw",
            hours_to_close=Decimal("24"),
            last_evidence_refresh_age_hours=Decimal("4"),
            upcoming_catalyst_hours=Decimal("12"),
            liquidity_decay_risk=Decimal("0.100000"),
            settlement_revision_window_hours=Decimal("48"),
            evidence_staleness=Decimal("0.100000"),
            reason_codes=("seed_url",),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        MarketEventTimeDecayPriorityDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="candidates must contain"):
        build_market_event_time_decay_priority_digest(
            ({"redacted_market_ref": "redacted_market_ref_dict"},),
            config=MarketEventTimeDecayPriorityDigestConfig(),
        )


@pytest.mark.parametrize(
    "reason_code",
    (
        "candidate_ref_alpha",
        "source_feed_alpha",
    ),
)
def test_rejects_candidate_or_source_surface_terms_in_reason_codes(
    reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="must not expose unsafe tokens"):
        _candidate(
            "unsafe_surface_reason",
            hours_to_close="24",
            last_evidence_refresh_age_hours="4",
            upcoming_catalyst_hours="12",
            liquidity_decay_risk="0.100000",
            settlement_revision_window_hours="48",
            evidence_staleness="0.100000",
            reason_codes=(reason_code,),
        )


@pytest.mark.parametrize(
    "reason_code",
    (
        "market_id_alpha",
        "condition_id_alpha",
        "source_alpha",
        "raw_text_capture",
    ),
)
def test_rejects_raw_market_source_or_text_terms_in_reason_codes(
    reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="must not expose unsafe tokens"):
        _candidate(
            "unsafe_raw_surface_reason",
            hours_to_close="24",
            last_evidence_refresh_age_hours="4",
            upcoming_catalyst_hours="12",
            liquidity_decay_risk="0.100000",
            settlement_revision_window_hours="48",
            evidence_staleness="0.100000",
            reason_codes=(reason_code,),
        )


@pytest.mark.parametrize(
    "reason_code",
    (
        "recommendation_buy",
        "position_sizing",
        "network_request",
        "database_write",
        "env_var_lookup",
        "file_write",
    ),
)
def test_rejects_execution_or_persistence_terms_in_reason_codes(
    reason_code: str,
) -> None:
    with pytest.raises(ValueError, match="must not expose unsafe tokens"):
        MarketEventTimeDecayPriorityDigestCandidate(
            redacted_market_ref="redacted_market_ref_unsafe_reason",
            hours_to_close=Decimal("24"),
            last_evidence_refresh_age_hours=Decimal("4"),
            upcoming_catalyst_hours=Decimal("12"),
            liquidity_decay_risk=Decimal("0.100000"),
            settlement_revision_window_hours=Decimal("48"),
            evidence_staleness=Decimal("0.100000"),
            reason_codes=(reason_code,),
        )


def test_tied_rows_sort_by_redacted_reference_deterministically() -> None:
    report = build_market_event_time_decay_priority_digest(
        (
            _candidate(
                "tie_b",
                hours_to_close="120",
                last_evidence_refresh_age_hours="4",
                upcoming_catalyst_hours="120",
                liquidity_decay_risk="0.100000",
                settlement_revision_window_hours="72",
                evidence_staleness="0.100000",
            ),
            _candidate(
                "tie_a",
                hours_to_close="120",
                last_evidence_refresh_age_hours="4",
                upcoming_catalyst_hours="120",
                liquidity_decay_risk="0.100000",
                settlement_revision_window_hours="72",
                evidence_staleness="0.100000",
            ),
        ),
        config=MarketEventTimeDecayPriorityDigestConfig(),
    )

    assert [row.redacted_market_ref for row in report.rows] == [
        "redacted_market_ref_tie_a",
        "redacted_market_ref_tie_b",
    ]
