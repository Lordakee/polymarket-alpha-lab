from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_domain_assignment_policy import (
    ResearchEventDomainAssignmentCandidate,
    ResearchEventDomainAssignmentConfig,
    ResearchEventDomainAssignmentReasonCodeCount,
    ResearchEventDomainAssignmentReport,
    ResearchEventDomainAssignmentRow,
    build_research_event_domain_assignment_report,
    research_event_domain_assignment_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventDomainAssignmentConfig:
    values = {
        "config_version": "research-event-domain-assignment-policy-v0",
        "pass_confidence_score": d("0.700000"),
        "watch_confidence_score": d("0.350000"),
        "max_pass_ambiguity_score": d("0.250000"),
        "block_ambiguity_score": d("0.850000"),
    }
    values.update(overrides)
    return ResearchEventDomainAssignmentConfig(**values)


def candidate(
    event_key: str,
    *,
    title: str,
    summary: str = "Public event description",
    tags: tuple[str, ...] = (),
    confidence: Decimal | None = None,
    ambiguity: Decimal | None = None,
    manual_review: bool = False,
) -> ResearchEventDomainAssignmentCandidate:
    return ResearchEventDomainAssignmentCandidate(
        event_key=event_key,
        public_title=title,
        public_summary=summary,
        public_tags=tags,
        domain_confidence_score=confidence,
        ambiguity_score=ambiguity,
        manual_review_requested=manual_review,
    )


def report(
    rows: tuple[ResearchEventDomainAssignmentCandidate, ...],
    *,
    cfg: ResearchEventDomainAssignmentConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventDomainAssignmentReport:
    return build_research_event_domain_assignment_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_no_candidate_reason() -> None:
    domain_report = report(())

    assert type(domain_report) is ResearchEventDomainAssignmentReport
    assert domain_report.generated_at == GENERATED_AT
    assert domain_report.config_version == "research-event-domain-assignment-policy-v0"
    assert domain_report.policy_status == "block"
    assert domain_report.next_step == "hold_report_only_domain_route_assignment"
    assert domain_report.candidate_count == d("0")
    assert domain_report.assigned_count == d("0")
    assert domain_report.pass_count == d("0")
    assert domain_report.watch_count == d("0")
    assert domain_report.block_count == d("0")
    assert domain_report.review_required_count == d("0")
    assert domain_report.rows == ()
    assert domain_report.reason_codes == ("research_event_domain_assignment_no_candidates",)
    assert domain_report.reason_code_counts == (
        ResearchEventDomainAssignmentReasonCodeCount(
            reason_code="research_event_domain_assignment_no_candidates",
            count=d("1"),
        ),
    )
    assert domain_report.paper_only is True
    assert domain_report.report_only is True
    assert domain_report.readonly is True


def test_candidates_route_to_domain_teams_with_pass_watch_and_block_policy() -> None:
    domain_report = report(
        (
            candidate(
                "politics-election",
                title="US senate election vote deadline",
                summary="Congress policy poll update",
                tags=("senate", "vote", "election"),
            ),
            candidate(
                "btc-gold-cross",
                title="Bitcoin ETF and gold reserve reaction",
                summary="BTC and bullion desk mentions both themes",
                tags=("bitcoin", "gold"),
                manual_review=True,
            ),
            candidate(
                "unclear-award",
                title="Celebrity award announcement",
                summary="Public entertainment note",
                tags=("awards",),
            ),
        ),
    )

    assert domain_report.policy_status == "block"
    assert domain_report.candidate_count == d("3")
    assert domain_report.assigned_count == d("2")
    assert domain_report.pass_count == d("1")
    assert domain_report.watch_count == d("1")
    assert domain_report.block_count == d("1")
    assert domain_report.review_required_count == d("2")

    blocked, watched, passed = domain_report.rows
    assert blocked.event_key == "unclear-award"
    assert blocked.assigned_domain == "unassigned"
    assert blocked.assigned_team == "manual_research_triage"
    assert blocked.policy_status == "block"
    assert blocked.domain_confidence_score is None
    assert blocked.ambiguity_score == d("1.000000")
    assert blocked.route_reasons == (
        "research_event_domain_assignment_block",
        "research_event_domain_assignment_no_domain_match",
        "research_event_domain_assignment_high_ambiguity",
        "research_event_domain_assignment_low_confidence",
        "research_event_domain_assignment_ambiguous_domain",
    )
    assert blocked.review_requirements == (
        "research_event_domain_assignment_manual_triage_required",
        "research_event_domain_assignment_supply_public_domain_signal",
        "research_event_domain_assignment_resolve_domain_conflict",
        "research_event_domain_assignment_confirm_domain_boundary",
        "research_event_domain_assignment_add_public_context",
    )

    assert watched.event_key == "btc-gold-cross"
    assert watched.assigned_domain == "btc"
    assert watched.assigned_team == "btc_research_team"
    assert watched.policy_status == "watch"
    assert watched.domain_confidence_score == d("0.600000")
    assert watched.ambiguity_score == d("0.166667")
    assert watched.matched_signal_count == d("3")
    assert watched.competing_domain_count == d("1")
    assert watched.route_reasons == (
        "research_event_domain_assignment_watch",
        "research_event_domain_assignment_low_confidence",
        "research_event_domain_assignment_ambiguous_domain",
        "research_event_domain_assignment_manual_review_requested",
        "research_event_domain_assignment_domain_btc",
    )
    assert watched.review_requirements == (
        "research_event_domain_assignment_resolve_domain_conflict",
        "research_event_domain_assignment_team_lead_review",
        "research_event_domain_assignment_confirm_domain_boundary",
        "research_event_domain_assignment_add_public_context",
    )

    assert type(passed) is ResearchEventDomainAssignmentRow
    assert passed.event_key == "politics-election"
    assert passed.assigned_domain == "politics"
    assert passed.assigned_team == "politics_research_team"
    assert passed.policy_status == "pass"
    assert passed.domain_confidence_score == d("1.000000")
    assert passed.ambiguity_score == d("0.000000")
    assert passed.route_reasons == (
        "research_event_domain_assignment_pass",
        "research_event_domain_assignment_clear_route",
        "research_event_domain_assignment_domain_politics",
    )
    assert passed.review_requirements == (
        "research_event_domain_assignment_no_extra_review",
    )


def test_payload_is_public_json_ready_and_excludes_private_reference_terms() -> None:
    domain_report = report(
        (
            candidate(
                "basketball-playoff",
                title="NBA playoff rebounds line",
                summary="Basketball public note",
                tags=("nba", "basketball", "rebounds"),
            ),
            candidate(
                "index-close",
                title="Nasdaq and S&P closing level",
                summary="Equity index public note",
                tags=("nasdaq", "sp500", "index"),
            ),
        ),
    )

    payload = research_event_domain_assignment_report_payload(domain_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["domain_confidence_score"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert "raw_id" not in encoded
    assert "market_id" not in encoded
    assert "source_id" not in encoded
    assert "source" not in encoded


def test_validation_rejects_bad_types_private_references_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="pass_confidence_score"):
        config(pass_confidence_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_confidence_score"):
        config(watch_confidence_score=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="pass_confidence_score"):
        config(pass_confidence_score=d("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (candidate("btc", title="BTC halving"),),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (candidate("btc", title="BTC halving"),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_key"):
        candidate(" btc", title="BTC halving")
    with pytest.raises(ValueError, match="public_title"):
        candidate("btc", title="BTC condition_id leaked")
    with pytest.raises(ValueError, match="public_tags"):
        ResearchEventDomainAssignmentCandidate(
            event_key="btc",
            public_title="BTC halving",
            public_summary="Public note",
            public_tags=["btc"],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="domain_confidence_score"):
        candidate("btc", title="BTC halving", confidence=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ambiguity_score"):
        candidate("btc", title="BTC halving", ambiguity=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="manual_review_requested"):
        replace(
            candidate("btc", title="BTC halving"),
            manual_review_requested=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate("btc", title="BTC halving"), paper_only=False)
    with pytest.raises(ValueError, match="duplicate"):
        report(
            (
                candidate("btc", title="BTC halving"),
                candidate("btc", title="Bitcoin ETF"),
            ),
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    domain_report = report(
        (
            candidate(
                "gold-event",
                title="Gold bullion price fixing",
                summary="Precious metals public note",
                tags=("gold", "bullion"),
            ),
        ),
    )
    row = domain_report.rows[0]

    with pytest.raises(FrozenInstanceError):
        domain_report.policy_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.assigned_domain = "btc"  # type: ignore[misc]
    with pytest.raises(ValueError, match="assigned_team"):
        replace(row, assigned_team="btc_research_team")
    with pytest.raises(ValueError, match="domain_confidence_score"):
        replace(row, domain_confidence_score=d("0.100000"))
    with pytest.raises(ValueError, match="policy_status"):
        replace(domain_report, policy_status="watch")


def test_owned_module_has_no_trading_network_filesystem_execution_or_db_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_domain_assignment_policy.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
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
        "sqlite",
        "postgres",
        "trade(",
        "order(",
    )

    assert all(term not in text for term in forbidden_terms)


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
