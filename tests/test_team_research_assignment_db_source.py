import ast
import importlib
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

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
from polymarket_alpha_lab.team_research_assignment import (
    TeamResearchAssignmentConfig,
    TeamResearchAssignmentReport,
    build_team_research_assignment_report,
)


GENERATED_AT = datetime(2026, 7, 1, 14, 0, tzinfo=UTC)
QUANTUM = Decimal("0.000001")


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.team_research_assignment_db_source",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def research_row(
    *,
    research_rank: int,
    market_slug: str,
    question: str,
    research_bucket: str = "ready_bucket",
) -> PaperStrategyCandidateResearchQueueRow:
    return PaperStrategyCandidateResearchQueueRow(
        research_rank=research_rank,
        queue_rank=research_rank,
        market_slug=market_slug,
        question=question,
        selected_side="yes",
        scoring_side="yes",
        source_action="recommend",
        decision="skipped",
        queue_status="ready",
        research_status="ready",
        research_bucket=research_bucket,
        assessment_status="ready",
        source_status="active",
        readiness_status="pass",
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
        primary_reason_code="candidate_research_ready",
        research_priority_score=d("0.800000"),
        evidence_gap_codes=(),
        reason_codes=("candidate_research_ready",),
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


def route_row(
    *,
    market_slug: str,
    question: str,
    category_id: str = "finance.crypto.btc",
    primary_team_id: str = "crypto_btc",
) -> TeamMarketRouteRow:
    return TeamMarketRouteRow(
        condition_id=f"condition-{market_slug}",
        market_slug=market_slug,
        question=question,
        category_id=category_id,
        event_template="research-assignment-db-source-test",
        primary_team_id=primary_team_id,
        secondary_team_ids=(),
        routing_confidence=d("0.900000"),
        routing_reason_codes=("primary_source_category",),
    )


def route_report(
    rows: tuple[TeamMarketRouteRow, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "team-market-route-test-v0",
) -> TeamMarketRouteReport:
    return TeamMarketRouteReport(
        generated_at=generated_at,
        config_version=config_version,
        route_count=len(rows),
        rows=rows,
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
            sorted((status.team_id, status.source_config_version) for status in statuses),
        ),
        reason_code_counts=(
            TeamMemoryReadinessDigestReasonCodeCount(
                reason_code=reason_code,
                count=1,
            ),
        ),
        reason_codes=(reason_code,),
    )


def assignment_report() -> TeamResearchAssignmentReport:
    question = "Will Bitcoin trade above alpha by resolution?"
    return build_team_research_assignment_report(
        queue_report(
            (
                research_row(
                    research_rank=1,
                    market_slug="btc-alpha",
                    question=question,
                    research_bucket="crypto",
                ),
            ),
        ),
        route_report(
            (
                route_row(
                    market_slug="btc-alpha",
                    question=question,
                ),
            ),
        ),
        memory_report((memory_status(team_id="crypto_btc"),)),
        config=TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
    )


def load_kwargs_with_call_tracking(calls: list[str]) -> dict[str, object]:
    question = "Will Bitcoin trade above alpha by resolution?"
    source_queue_report = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question=question,
                research_bucket="crypto",
            ),
        ),
    )
    source_route_report = route_report(
        (route_row(market_slug="btc-alpha", question=question),),
    )
    source_memory_report = memory_report((memory_status(team_id="crypto_btc"),))
    source_assignment_report = assignment_report()

    def queue_loader(**kwargs: object) -> tuple[PaperStrategyCandidateResearchQueueReport]:
        calls.append("queue_loader")
        return (source_queue_report,)

    def route_loader(**kwargs: object) -> tuple[TeamMarketRouteReport]:
        calls.append("route_loader")
        return (source_route_report,)

    def memory_loader(**kwargs: object) -> TeamMemoryReadinessDigestReport:
        calls.append("memory_loader")
        return source_memory_report

    def assignment_builder(*args: object, **kwargs: object) -> TeamResearchAssignmentReport:
        calls.append("assignment_builder")
        return source_assignment_report

    return {
        "queue_loader": queue_loader,
        "route_loader": route_loader,
        "memory_loader": memory_loader,
        "assignment_builder": assignment_builder,
        "assignment_config": TeamResearchAssignmentConfig(),
        "generated_at": GENERATED_AT,
        "team_ids": ("crypto_btc",),
        "queue_source_config_version": "queue-source-v1",
        "queue_limit": 1,
        "route_limit": 25,
        "memory_config_version": "snapshot-v1",
        "memory_limit": 50,
    }


class _IntSubclass(int):
    pass


class _StrSubclass(str):
    pass


def test_loads_queue_routes_memory_then_builds_assignment() -> None:
    db_source = module()
    calls: list[tuple[str, object]] = []
    question = "Will Bitcoin trade above alpha by resolution?"
    source_queue_report = queue_report(
        (
            research_row(
                research_rank=1,
                market_slug="btc-alpha",
                question=question,
                research_bucket="crypto",
            ),
        ),
    )
    source_route_report = route_report(
        (route_row(market_slug="btc-alpha", question=question),),
    )
    source_memory_report = memory_report(
        (
            memory_status(team_id="crypto_btc"),
            memory_status(team_id="macro_rates"),
        ),
    )
    expected_assignment_report = assignment_report()
    assignment_config = TeamResearchAssignmentConfig()

    def queue_loader(**kwargs: object) -> tuple[PaperStrategyCandidateResearchQueueReport]:
        calls.append(("queue_loader", kwargs))
        return (source_queue_report,)

    def route_loader(**kwargs: object) -> tuple[TeamMarketRouteReport]:
        calls.append(("route_loader", kwargs))
        return (source_route_report,)

    def memory_loader(**kwargs: object) -> TeamMemoryReadinessDigestReport:
        calls.append(("memory_loader", kwargs))
        return source_memory_report

    def assignment_builder(
        queue_arg: object,
        route_arg: object,
        memory_arg: object,
        *,
        config: object,
        generated_at: object,
    ) -> TeamResearchAssignmentReport:
        calls.append(
            (
                "assignment_builder",
                {
                    "queue_report": queue_arg,
                    "route_report": route_arg,
                    "memory_report": memory_arg,
                    "config": config,
                    "generated_at": generated_at,
                },
            ),
        )
        return expected_assignment_report

    report = db_source.load_team_research_assignment_report(
        queue_loader=queue_loader,
        route_loader=route_loader,
        memory_loader=memory_loader,
        assignment_builder=assignment_builder,
        assignment_config=assignment_config,
        generated_at=GENERATED_AT,
        team_ids=("crypto_btc", "macro_rates"),
        queue_source_config_version="queue-source-v1",
        queue_limit=1,
        route_limit=25,
        memory_config_version="snapshot-v1",
        memory_limit=50,
    )

    assert report is expected_assignment_report
    assert calls == [
        (
            "queue_loader",
            {
                "source_config_version": "queue-source-v1",
                "action_status": "research_ready",
                "research_status": "ready",
                "limit": 1,
            },
        ),
        ("route_loader", {"limit": 25}),
        (
            "memory_loader",
            {
                "team_ids": ("crypto_btc", "macro_rates"),
                "config_version": "snapshot-v1",
                "limit": 50,
            },
        ),
        (
            "assignment_builder",
            {
                "queue_report": source_queue_report,
                "route_report": source_route_report,
                "memory_report": source_memory_report,
                "config": assignment_config,
                "generated_at": GENERATED_AT,
            },
        ),
    ]


@pytest.mark.parametrize(
    "queue_reports",
    [
        (),
        (
            queue_report(
                (
                    research_row(
                        research_rank=1,
                        market_slug="btc-alpha",
                        question="Will Bitcoin trade above alpha by resolution?",
                    ),
                ),
            ),
            queue_report(
                (
                    research_row(
                        research_rank=1,
                        market_slug="rates-alpha",
                        question="Will macro rates resolve above alpha?",
                        research_bucket="macro",
                    ),
                ),
            ),
        ),
    ],
)
def test_requires_exactly_one_queue_report_before_loading_routes_or_memory(
    queue_reports: tuple[PaperStrategyCandidateResearchQueueReport, ...],
) -> None:
    db_source = module()
    calls: list[str] = []

    def queue_loader(**kwargs: object) -> tuple[PaperStrategyCandidateResearchQueueReport, ...]:
        calls.append("queue_loader")
        return queue_reports

    def route_loader(**kwargs: object) -> tuple[TeamMarketRouteReport, ...]:
        calls.append("route_loader")
        return ()

    def memory_loader(**kwargs: object) -> TeamMemoryReadinessDigestReport:
        calls.append("memory_loader")
        return memory_report(())

    def assignment_builder(*args: object, **kwargs: object) -> TeamResearchAssignmentReport:
        calls.append("assignment_builder")
        return assignment_report()

    with pytest.raises(ValueError, match="exactly one queue report"):
        db_source.load_team_research_assignment_report(
            queue_loader=queue_loader,
            route_loader=route_loader,
            memory_loader=memory_loader,
            assignment_builder=assignment_builder,
            assignment_config=TeamResearchAssignmentConfig(),
            generated_at=GENERATED_AT,
            team_ids=("crypto_btc",),
        )

    assert calls == ["queue_loader"]


def test_merges_multiple_one_row_route_reports() -> None:
    db_source = module()
    first_generated_at = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    second_generated_at = datetime(2026, 7, 1, 13, 0, tzinfo=UTC)
    btc_route = route_row(
        market_slug="btc-alpha",
        question="Will Bitcoin trade above alpha by resolution?",
    )
    rates_route = route_row(
        market_slug="rates-alpha",
        question="Will macro rates resolve above alpha?",
        category_id="finance.macro.rates",
        primary_team_id="macro_rates",
    )

    merged = db_source.merge_team_market_route_reports(
        (
            route_report(
                (btc_route,),
                generated_at=first_generated_at,
                config_version="route-config-v1",
            ),
            route_report(
                (rates_route,),
                generated_at=second_generated_at,
                config_version="route-config-v2",
            ),
        ),
    )

    assert type(merged) is TeamMarketRouteReport
    assert merged.generated_at == first_generated_at
    assert merged.config_version == "route-config-v1"
    assert merged.route_count == 2
    assert merged.rows == (btc_route, rates_route)
    assert merged.paper_only is True
    assert merged.report_only is True
    assert merged.readonly is True


def test_duplicate_route_market_slugs_fail() -> None:
    db_source = module()
    first = route_report(
        (
            route_row(
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
            ),
        ),
    )
    second = route_report(
        (
            route_row(
                market_slug="btc-alpha",
                question="Will the duplicate Bitcoin route resolve yes?",
            ),
        ),
    )

    with pytest.raises(ValueError, match="unique market_slug"):
        db_source.merge_team_market_route_reports((first, second))


def test_route_readback_reports_must_be_one_row() -> None:
    db_source = module()

    with pytest.raises(ValueError, match="one-row"):
        db_source.merge_team_market_route_reports((route_report(()),))

    with pytest.raises(ValueError, match="one-row"):
        db_source.merge_team_market_route_reports(
            (
                route_report(
                    (
                        route_row(
                            market_slug="btc-alpha",
                            question="Will Bitcoin trade above alpha by resolution?",
                        ),
                        route_row(
                            market_slug="rates-alpha",
                            question="Will macro rates resolve above alpha?",
                            category_id="finance.macro.rates",
                            primary_team_id="macro_rates",
                        ),
                    ),
                ),
            ),
        )


@pytest.mark.parametrize(
    "bad_kwargs",
    [
        {"queue_loader": object()},
        {"route_loader": object()},
        {"memory_loader": object()},
        {"assignment_builder": object()},
    ],
)
def test_load_rejects_non_callable_loaders_and_builder(
    bad_kwargs: dict[str, object],
) -> None:
    db_source = module()
    kwargs = {
        "queue_loader": lambda **_kwargs: (
            queue_report(
                (
                    research_row(
                        research_rank=1,
                        market_slug="btc-alpha",
                        question="Will Bitcoin trade above alpha by resolution?",
                    ),
                ),
            ),
        ),
        "route_loader": lambda **_kwargs: (),
        "memory_loader": lambda **_kwargs: memory_report(()),
        "assignment_builder": lambda *_args, **_kwargs: assignment_report(),
        "assignment_config": TeamResearchAssignmentConfig(),
        "generated_at": GENERATED_AT,
        "team_ids": ("crypto_btc",),
    }
    kwargs.update(bad_kwargs)

    with pytest.raises(ValueError, match="callable"):
        db_source.load_team_research_assignment_report(**kwargs)


@pytest.mark.parametrize(
    ("bad_kwargs", "match"),
    [
        ({"team_ids": ["crypto_btc"]}, "team_ids"),
        ({"team_ids": ()}, "team_ids"),
        ({"team_ids": (" crypto_btc",)}, "team_ids"),
        ({"team_ids": ("crypto_btc ",)}, "team_ids"),
        ({"team_ids": ("unknown_team",)}, "team_ids"),
        ({"team_ids": ("crypto_btc", "crypto_btc")}, "duplicate team_ids"),
        ({"team_ids": (1,)}, "team_ids"),
        ({"team_ids": (_StrSubclass("crypto_btc"),)}, "team_ids"),
        ({"queue_limit": 0}, "queue_limit"),
        ({"queue_limit": -1}, "queue_limit"),
        ({"queue_limit": True}, "queue_limit"),
        ({"queue_limit": _IntSubclass(1)}, "queue_limit"),
        ({"route_limit": 0}, "route_limit"),
        ({"route_limit": -1}, "route_limit"),
        ({"route_limit": True}, "route_limit"),
        ({"route_limit": _IntSubclass(1)}, "route_limit"),
        ({"memory_limit": 0}, "memory_limit"),
        ({"memory_limit": -1}, "memory_limit"),
        ({"memory_limit": True}, "memory_limit"),
        ({"memory_limit": _IntSubclass(1)}, "memory_limit"),
        ({"queue_source_config_version": ""}, "queue_source_config_version"),
        ({"queue_source_config_version": " queue-source-v1"}, "queue_source_config_version"),
        ({"queue_source_config_version": "queue-source-v1 "}, "queue_source_config_version"),
        (
            {"queue_source_config_version": _StrSubclass("queue-source-v1")},
            "queue_source_config_version",
        ),
        ({"memory_config_version": ""}, "memory_config_version"),
        ({"memory_config_version": " snapshot-v1"}, "memory_config_version"),
        ({"memory_config_version": "snapshot-v1 "}, "memory_config_version"),
        (
            {"memory_config_version": _StrSubclass("snapshot-v1")},
            "memory_config_version",
        ),
    ],
)
def test_load_validates_inputs_before_calling_any_loader(
    bad_kwargs: dict[str, object],
    match: str,
) -> None:
    db_source = module()
    calls: list[str] = []
    kwargs = load_kwargs_with_call_tracking(calls)
    kwargs.update(bad_kwargs)

    with pytest.raises(ValueError, match=match):
        db_source.load_team_research_assignment_report(**kwargs)

    assert calls == []


class TeamResearchAssignmentConfigSubclass(TeamResearchAssignmentConfig):
    pass


def test_exact_assignment_config_type_is_required() -> None:
    db_source = module()

    with pytest.raises(ValueError, match="TeamResearchAssignmentConfig"):
        db_source.load_team_research_assignment_report(
            queue_loader=lambda **_kwargs: (
                queue_report(
                    (
                        research_row(
                            research_rank=1,
                            market_slug="btc-alpha",
                            question="Will Bitcoin trade above alpha by resolution?",
                        ),
                    ),
                ),
            ),
            route_loader=lambda **_kwargs: (),
            memory_loader=lambda **_kwargs: memory_report(()),
            assignment_builder=lambda *_args, **_kwargs: assignment_report(),
            assignment_config=TeamResearchAssignmentConfigSubclass(),
            generated_at=GENERATED_AT,
            team_ids=("crypto_btc",),
        )


def test_load_requires_hard_flags_on_returned_assignment_report() -> None:
    db_source = module()
    bad_report = object.__new__(TeamResearchAssignmentReport)
    object.__setattr__(bad_report, "paper_only", True)
    object.__setattr__(bad_report, "report_only", False)
    object.__setattr__(bad_report, "readonly", True)

    with pytest.raises(ValueError, match="report_only"):
        db_source.load_team_research_assignment_report(
            queue_loader=lambda **_kwargs: (
                queue_report(
                    (
                        research_row(
                            research_rank=1,
                            market_slug="btc-alpha",
                            question="Will Bitcoin trade above alpha by resolution?",
                        ),
                    ),
                ),
            ),
            route_loader=lambda **_kwargs: (
                route_report(
                    (
                        route_row(
                            market_slug="btc-alpha",
                            question="Will Bitcoin trade above alpha by resolution?",
                        ),
                    ),
                ),
            ),
            memory_loader=lambda **_kwargs: memory_report(
                (memory_status(team_id="crypto_btc"),),
            ),
            assignment_builder=lambda *_args, **_kwargs: bad_report,
            assignment_config=TeamResearchAssignmentConfig(),
            generated_at=GENERATED_AT,
            team_ids=("crypto_btc",),
        )


def test_load_requires_exact_assignment_report_type_from_builder() -> None:
    db_source = module()

    class AssignmentReportObject:
        paper_only = True
        report_only = True
        readonly = True

    report = AssignmentReportObject()

    with pytest.raises(ValueError, match="TeamResearchAssignmentReport"):
        db_source.load_team_research_assignment_report(
            queue_loader=lambda **_kwargs: (
                queue_report(
                    (
                        research_row(
                            research_rank=1,
                            market_slug="btc-alpha",
                            question="Will Bitcoin trade above alpha by resolution?",
                        ),
                    ),
                ),
            ),
            route_loader=lambda **_kwargs: (
                route_report(
                    (
                        route_row(
                            market_slug="btc-alpha",
                            question="Will Bitcoin trade above alpha by resolution?",
                        ),
                    ),
                ),
            ),
            memory_loader=lambda **_kwargs: memory_report(
                (memory_status(team_id="crypto_btc"),),
            ),
            assignment_builder=lambda *_args, **_kwargs: report,
            assignment_config=TeamResearchAssignmentConfig(),
            generated_at=GENERATED_AT,
            team_ids=("crypto_btc",),
        )


@pytest.mark.parametrize(
    "route_reports",
    [
        (),
        (route_report(()),),
    ],
)
def test_empty_route_readback_fails_before_loading_memory_or_building_assignment(
    route_reports: tuple[TeamMarketRouteReport, ...],
) -> None:
    db_source = module()
    calls: list[str] = []

    def queue_loader(**kwargs: object) -> tuple[PaperStrategyCandidateResearchQueueReport]:
        calls.append("queue_loader")
        return (
            queue_report(
                (
                    research_row(
                        research_rank=1,
                        market_slug="btc-alpha",
                        question="Will Bitcoin trade above alpha by resolution?",
                    ),
                ),
            ),
        )

    def route_loader(**kwargs: object) -> tuple[TeamMarketRouteReport, ...]:
        calls.append("route_loader")
        return route_reports

    def memory_loader(**kwargs: object) -> TeamMemoryReadinessDigestReport:
        calls.append("memory_loader")
        return memory_report((memory_status(team_id="crypto_btc"),))

    def assignment_builder(*args: object, **kwargs: object) -> TeamResearchAssignmentReport:
        calls.append("assignment_builder")
        return assignment_report()

    with pytest.raises(ValueError, match="route"):
        db_source.load_team_research_assignment_report(
            queue_loader=queue_loader,
            route_loader=route_loader,
            memory_loader=memory_loader,
            assignment_builder=assignment_builder,
            assignment_config=TeamResearchAssignmentConfig(),
            generated_at=GENERATED_AT,
            team_ids=("crypto_btc",),
        )

    assert calls == ["queue_loader", "route_loader"]


def test_merge_requires_hard_flags_on_each_route_report() -> None:
    db_source = module()
    bad_report = object.__new__(TeamMarketRouteReport)
    object.__setattr__(bad_report, "generated_at", GENERATED_AT)
    object.__setattr__(bad_report, "config_version", "route-config-v0")
    object.__setattr__(bad_report, "route_count", 1)
    object.__setattr__(
        bad_report,
        "rows",
        (
            route_row(
                market_slug="btc-alpha",
                question="Will Bitcoin trade above alpha by resolution?",
            ),
        ),
    )
    object.__setattr__(bad_report, "paper_only", True)
    object.__setattr__(bad_report, "report_only", True)
    object.__setattr__(bad_report, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        db_source.merge_team_market_route_reports((bad_report,))


def test_module_ast_has_no_db_env_cli_store_or_write_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "team_research_assignment_db_source.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    forbidden_import_fragments = (
        "psycopg",
        "env",
        "cli",
        "store",
    )
    forbidden_call_names = {
        "connect",
        "cursor",
        "execute",
        "commit",
        "rollback",
        "close",
        "open",
        "write",
        "persist",
    }
    forbidden_attr_names = {
        "connection",
        "cursor",
        "execute",
        "commit",
        "rollback",
        "close",
        "open",
        "write",
        "persist",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(
                    fragment in alias.name for fragment in forbidden_import_fragments
                )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            assert not any(
                fragment in module_name for fragment in forbidden_import_fragments
            )
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_attr_names
