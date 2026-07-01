import importlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest

import polymarket_alpha_lab as lab
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)
from polymarket_alpha_lab.team_market_router import (
    TeamMarketRouteReport,
    TeamMarketRouteRow,
)
from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReasonCodeCount,
    TeamMemoryReadinessDigestReport,
    TeamMemoryReadinessDigestSourceStatus,
)


GENERATED_AT = datetime(2026, 7, 1, 14, 0, tzinfo=UTC)
QUANTUM = Decimal("0.000001")


def module():
    return importlib.import_module("polymarket_alpha_lab.team_research_assignment")


def d(value: str) -> Decimal:
    return Decimal(value)


def research_row(
    *,
    research_rank: int,
    market_slug: str,
    question: str,
    selected_side: str = "yes",
    scoring_side: str = "yes",
    queue_status: str = "ready",
    research_status: str = "ready",
    research_bucket: str = "ready_bucket",
    readiness_status: str = "pass",
    primary_reason_code: str = "candidate_research_ready",
    evidence_gap_codes: tuple[str, ...] = (),
    reason_codes: tuple[str, ...] = ("candidate_research_ready",),
) -> PaperStrategyCandidateResearchQueueRow:
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=research_rank,
        market_slug=market_slug,
        question=question,
        selected_side=selected_side,
        scoring_side=scoring_side,
        source_action="recommend",
        decision="skipped",
        queue_status=queue_status,
        research_status=research_status,
        research_bucket=research_bucket,
        assessment_status=research_status,
        source_status="active",
        readiness_status=readiness_status,
        recommendation_score=d("0.700000"),
        readiness_score=d("0.900000"),
        screening_score=d("0.800000"),
        net_edge_per_share=d("0.100000"),
        total_cost_per_share=d("0.010000"),
        confidence=d("0.900000"),
        spread=d("0.010000"),
        resolution_risk=d("0.020000"),
        suggested_notional=d("10.000000"),
        selected_position_notional=d("0.000000"),
        primary_reason_code=primary_reason_code,
        research_priority_score=d("0.800000"),
        evidence_gap_codes=evidence_gap_codes,
        reason_codes=reason_codes,
        explanation=f"{market_slug} is ready for paper-only research assignment.",
    )


def queue_report(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> PaperStrategyCandidateResearchQueueReport:
    ready_rows = tuple(row for row in rows if row.research_status == "ready")
    return PaperStrategyCandidateResearchQueueReport(
        generated_at=GENERATED_AT,
        config_version="candidate-research-queue-test-v0",
        source_config_version="candidate-source-test-v0",
        action_status="research_ready",
        recommended_next_step="review_candidate_research_queue",
        source_reason_code_counts=(("cycle_review_research_ready", 1),),
        research_status="ready",
        candidate_count=len(rows),
        research_ready_count=len(ready_rows),
        watch_count=sum(1 for row in rows if row.research_status == "watch"),
        blocked_count=sum(1 for row in rows if row.research_status == "blocked"),
        selected_count=sum(1 for row in rows if row.decision == "selected"),
        skipped_count=sum(1 for row in rows if row.decision == "skipped"),
        not_selected_count=sum(1 for row in rows if row.decision == "not_selected"),
        total_ready_notional=sum(
            (row.suggested_notional for row in ready_rows),
            d("0.000000"),
        ).quantize(QUANTUM),
        total_selected_notional=sum(
            (row.selected_position_notional for row in rows),
            d("0.000000"),
        ).quantize(QUANTUM),
        total_suggested_notional=sum(
            (
                row.suggested_notional
                for row in rows
                if row.source_action == "recommend"
            ),
            d("0.000000"),
        ).quantize(QUANTUM),
        top_research_priority_score=(
            rows[0].research_priority_score if rows else d("0.000000")
        ),
        average_research_ready_score=(
            (
                sum((row.research_priority_score for row in ready_rows), d("0.000000"))
                / Decimal(len(ready_rows))
            ).quantize(QUANTUM)
            if ready_rows
            else d("0.000000")
        ),
        primary_reason_code_counts=tuple(
            sorted(
                {
                    row.primary_reason_code: sum(
                        1
                        for counted_row in rows
                        if counted_row.primary_reason_code == row.primary_reason_code
                    )
                    for row in rows
                }.items(),
                key=lambda item: (-item[1], item[0]),
            ),
        ),
        rows=rows,
        reason_codes=("candidate_research_queue_ready",),
    )


def route_report(rows: tuple[TeamMarketRouteRow, ...]) -> TeamMarketRouteReport:
    return TeamMarketRouteReport(
        generated_at=GENERATED_AT,
        config_version="team-market-route-test-v0",
        route_count=len(rows),
        rows=rows,
    )


def route_row(
    *,
    market_slug: str,
    question: str,
    category_id: str,
    primary_team_id: str,
    secondary_team_ids: tuple[str, ...] = (),
    routing_confidence: Decimal = d("0.900000"),
) -> TeamMarketRouteRow:
    return TeamMarketRouteRow(
        condition_id=f"condition-{market_slug}",
        market_slug=market_slug,
        question=question,
        category_id=category_id,
        event_template="research-assignment-test",
        primary_team_id=primary_team_id,
        secondary_team_ids=secondary_team_ids,
        routing_confidence=routing_confidence,
        routing_reason_codes=("primary_source_category",),
    )


def memory_status(
    *,
    team_id: str,
    gate_status: str = "pass",
) -> TeamMemoryReadinessDigestSourceStatus:
    return TeamMemoryReadinessDigestSourceStatus(
        team_id=team_id,
        gate_status=gate_status,
        recommended_next_step={
            "pass": "allow_team_memory_readiness_use",
            "watch": "throttle_team_memory_readiness_use",
            "blocked": "block_team_memory_readiness_use",
        }[gate_status],
        source_config_version=f"{team_id}-history-gate-test-v0",
        latest_snapshot_age_seconds=60,
        source_snapshot_count=5,
        source_required_snapshot_count=3,
        source_status=gate_status,
    )


def memory_report(
    statuses: tuple[TeamMemoryReadinessDigestSourceStatus, ...],
) -> TeamMemoryReadinessDigestReport:
    pass_count = sum(1 for status in statuses if status.gate_status == "pass")
    watch_count = sum(1 for status in statuses if status.gate_status == "watch")
    blocked_count = sum(1 for status in statuses if status.gate_status == "blocked")
    if not statuses:
        digest_status = "blocked"
        reason_code = "team_memory_readiness_digest_empty_sources"
    elif blocked_count:
        digest_status = "blocked"
        reason_code = "team_memory_readiness_digest_blocked_sources_present"
    elif watch_count:
        digest_status = "watch"
        reason_code = "team_memory_readiness_digest_watch_sources_present"
    else:
        digest_status = "pass"
        reason_code = "team_memory_readiness_digest_passed"
    return TeamMemoryReadinessDigestReport(
        generated_at=GENERATED_AT,
        config_version="team-memory-readiness-digest-test-v0",
        digest_status=digest_status,
        recommended_next_step={
            "pass": "allow_team_memory_readiness_use",
            "watch": "throttle_team_memory_readiness_use",
            "blocked": "block_team_memory_readiness_use",
        }[digest_status],
        team_count=len(statuses),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        source_statuses=statuses,
        source_config_versions=tuple(
            sorted(
                (status.team_id, status.source_config_version) for status in statuses
            ),
        ),
        reason_code_counts=(
            TeamMemoryReadinessDigestReasonCodeCount(
                reason_code=reason_code,
                count=1,
            ),
        ),
        reason_codes=(reason_code,),
    )


def test_assigns_queue_rows_to_routed_teams_with_memory_readiness() -> None:
    assignment_module = module()
    btc_question = "Will Bitcoin trade above alpha by resolution?"
    politics_question = "Will the politics alpha market resolve yes?"
    source_queue = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question=btc_question,
                research_bucket="crypto",
                reason_codes=("candidate_research_ready", "fresh_evidence"),
            ),
            research_row(
                research_rank=2,
                market_slug="politics-alpha",
                question=politics_question,
                research_bucket="politics",
            ),
        ),
    )
    routes = route_report(
        (
            route_row(
                market_slug="btc-alpha",
                question=btc_question,
                category_id="finance.crypto.btc",
                primary_team_id="crypto_btc",
                secondary_team_ids=("macro_rates",),
            ),
            route_row(
                market_slug="politics-alpha",
                question=politics_question,
                category_id="politics",
                primary_team_id="politics",
            ),
        ),
    )
    memory = memory_report(
        (
            memory_status(team_id="crypto_btc", gate_status="pass"),
            memory_status(team_id="politics", gate_status="pass"),
        ),
    )

    report = assignment_module.build_team_research_assignment_report(
        source_queue,
        routes,
        memory,
        config=assignment_module.TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.assignment_status == "ready"
    assert report.recommended_next_step == "assign_team_research_work"
    assert report.assignment_count == 2
    assert report.assigned_count == 2
    assert tuple(row.market_slug for row in report.rows) == (
        "btc-alpha",
        "politics-alpha",
    )
    assert report.rows[0].team_id == "crypto_btc"
    assert report.rows[0].category_id == "finance.crypto.btc"
    assert report.rows[0].memory_readiness_status == "pass"
    assert report.rows[0].memory_use_policy == "allow"
    assert report.rows[0].assignment_status == "assigned"
    assert "team_research_assignment_assigned" in report.rows[0].assignment_reason_codes
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_missing_route_blocks_assignment_and_report() -> None:
    assignment_module = module()
    source_queue = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
            ),
        ),
    )

    report = assignment_module.build_team_research_assignment_report(
        source_queue,
        route_report(()),
        memory_report((memory_status(team_id="crypto_btc"),)),
        config=assignment_module.TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.assignment_status == "blocked"
    assert report.recommended_next_step == "block_team_research_assignment"
    assert report.blocked_count == 1
    assert report.rows[0].assignment_status == "blocked"
    assert report.rows[0].memory_use_policy == "block"
    assert "missing_team_market_route" in report.rows[0].assignment_reason_codes
    assert len(report.team_summaries) == 1
    assert report.team_summaries[0].team_id == "unassigned"
    assert report.team_summaries[0].memory_readiness_status == "missing"
    assert report.team_summaries[0].memory_use_policy == "block"
    assert report.team_summaries[0].assignment_count == 1
    assert report.team_summaries[0].blocked_count == 1


def test_missing_memory_readiness_blocks_routed_assignment() -> None:
    assignment_module = module()
    source_queue = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
            ),
        ),
    )
    routes = route_report(
        (
            route_row(
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
                category_id="finance.crypto.btc",
                primary_team_id="crypto_btc",
            ),
        ),
    )

    report = assignment_module.build_team_research_assignment_report(
        source_queue,
        routes,
        memory_report(()),
        config=assignment_module.TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.assignment_status == "blocked"
    assert report.rows[0].assignment_status == "blocked"
    assert report.rows[0].memory_use_policy == "block"
    assert "missing_team_memory_readiness" in report.rows[0].assignment_reason_codes


def test_queue_watch_status_yields_watch_assignment_when_memory_passes() -> None:
    assignment_module = module()
    source_queue = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-watch",
                question="Will Bitcoin watch market resolve yes?",
                queue_status="watch",
                research_status="watch",
                readiness_status="watch",
                primary_reason_code="readiness_watch",
                evidence_gap_codes=("readiness_watch",),
                reason_codes=("readiness_watch",),
            ),
        ),
    )
    routes = route_report(
        (
            route_row(
                market_slug="btc-watch",
                question="Will Bitcoin watch market resolve yes?",
                category_id="finance.crypto.btc",
                primary_team_id="crypto_btc",
            ),
        ),
    )

    report = assignment_module.build_team_research_assignment_report(
        source_queue,
        routes,
        memory_report((memory_status(team_id="crypto_btc", gate_status="pass"),)),
        config=assignment_module.TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.assignment_status == "watch"
    assert report.recommended_next_step == "review_team_research_assignments"
    assert report.watch_count == 1
    assert report.rows[0].assignment_status == "watch"
    assert report.rows[0].memory_use_policy == "allow"
    assert "source_queue_research_status_watch" in report.rows[0].assignment_reason_codes


def test_memory_watch_status_throttles_and_watches_assignment() -> None:
    assignment_module = module()
    source_queue = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
            ),
        ),
    )
    routes = route_report(
        (
            route_row(
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
                category_id="finance.crypto.btc",
                primary_team_id="crypto_btc",
            ),
        ),
    )

    report = assignment_module.build_team_research_assignment_report(
        source_queue,
        routes,
        memory_report((memory_status(team_id="crypto_btc", gate_status="watch"),)),
        config=assignment_module.TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.assignment_status == "watch"
    assert report.rows[0].memory_readiness_status == "watch"
    assert report.rows[0].memory_use_policy == "throttle"
    assert report.rows[0].assignment_status == "watch"
    assert "team_memory_readiness_watch" in report.rows[0].assignment_reason_codes


def test_memory_blocked_status_blocks_assignment() -> None:
    assignment_module = module()
    source_queue = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
            ),
        ),
    )
    routes = route_report(
        (
            route_row(
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
                category_id="finance.crypto.btc",
                primary_team_id="crypto_btc",
            ),
        ),
    )

    report = assignment_module.build_team_research_assignment_report(
        source_queue,
        routes,
        memory_report((memory_status(team_id="crypto_btc", gate_status="blocked"),)),
        config=assignment_module.TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.assignment_status == "blocked"
    assert report.rows[0].memory_readiness_status == "blocked"
    assert report.rows[0].memory_use_policy == "block"
    assert report.rows[0].assignment_status == "blocked"
    assert "team_memory_readiness_blocked" in report.rows[0].assignment_reason_codes


def test_assignment_row_rejects_status_drift_from_queue_and_memory_inputs() -> None:
    assignment_module = module()

    with pytest.raises(ValueError, match="assignment_status"):
        assignment_module.TeamResearchAssignmentRow(
            research_rank=1,
            market_slug="btc-alpha",
            question="Will Bitcoin trade above alpha by resolution?",
            selected_side="yes",
            scoring_side="yes",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            routing_confidence=d("0.900000"),
            secondary_team_ids=(),
            queue_research_status="ready",
            queue_research_bucket="ready_bucket",
            queue_readiness_status="pass",
            memory_readiness_status="pass",
            memory_use_policy="allow",
            assignment_status="watch",
            assignment_reason_codes=("team_research_assignment_assigned",),
            evidence_gap_codes=(),
            source_reason_codes=("candidate_research_ready",),
        )


def test_assignment_row_rejects_assigned_unassigned_sentinel() -> None:
    assignment_module = module()

    with pytest.raises(ValueError, match="unassigned"):
        assignment_module.TeamResearchAssignmentRow(
            research_rank=1,
            market_slug="btc-alpha",
            question="Will Bitcoin trade above alpha by resolution?",
            selected_side="yes",
            scoring_side="yes",
            team_id="unassigned",
            category_id="unrouted",
            routing_confidence=d("0.000000"),
            secondary_team_ids=(),
            queue_research_status="ready",
            queue_research_bucket="ready_bucket",
            queue_readiness_status="pass",
            memory_readiness_status="pass",
            memory_use_policy="allow",
            assignment_status="assigned",
            assignment_reason_codes=("team_research_assignment_assigned",),
            evidence_gap_codes=(),
            source_reason_codes=("candidate_research_ready",),
        )


def test_assignment_module_public_api_is_module_local() -> None:
    assignment_module = module()

    assert assignment_module.__all__ == (
        "DEFAULT_TEAM_RESEARCH_ASSIGNMENT_CONFIG_VERSION",
        "TeamResearchAssignmentConfig",
        "TeamResearchAssignmentReport",
        "TeamResearchAssignmentRow",
        "TeamResearchAssignmentTeamSummary",
        "build_team_research_assignment_report",
    )
    for name in assignment_module.__all__:
        assert not hasattr(lab, name)
