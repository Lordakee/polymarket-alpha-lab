from __future__ import annotations

from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_team_specialist_memory_router import (
    DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION,
    ResearchTeamSpecialistMemoryRouterConfig,
    ResearchTeamSpecialistMemoryRouterDigest,
    ResearchTeamSpecialistMemoryRouterInput,
    ResearchTeamSpecialistMemoryRouterReport,
    ResearchTeamSpecialistMemoryRouterRow,
    build_research_team_specialist_memory_router_report,
    public_supabase_memory_router_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def route_input(
    public_event_key: str = "event.alpha",
    *,
    event_category: str = "politics",
    evidence_score: Decimal = d("0.900000"),
    coverage_score: Decimal = d("0.850000"),
    memory_fit_score: Decimal = d("0.800000"),
    reason_codes: tuple[str, ...] = ("public_event_category_match",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamSpecialistMemoryRouterInput:
    return ResearchTeamSpecialistMemoryRouterInput(
        public_event_key=public_event_key,
        event_category=event_category,
        evidence_score=evidence_score,
        coverage_score=coverage_score,
        memory_fit_score=memory_fit_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchTeamSpecialistMemoryRouterInput, ...],
    *,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecialistMemoryRouterReport:
    return build_research_team_specialist_memory_router_report(
        rows,
        config=ResearchTeamSpecialistMemoryRouterConfig(),
        generated_at=generated_at,
    )


def test_router_routes_public_categories_to_specialist_memory_queues() -> None:
    summary = report(
        (
            route_input("event.politics", event_category="politics"),
            route_input("event.crypto", event_category="finance.crypto.btc"),
            route_input("event.macro", event_category="finance.macro.rates"),
            route_input("event.gold", event_category="finance.commodities.gold"),
            route_input("event.soccer", event_category="sports.soccer"),
            route_input("event.basketball", event_category="sports.basketball"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_ROUTER_CONFIG_VERSION
    )
    assert summary.public_status == "pass"
    assert summary.next_step == "allow_local_memory_queue_plan"
    assert summary.event_count == d("6.000000")
    assert summary.pass_count == d("6.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.block_count == d("0.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    by_event_key = {row.public_event_key: row for row in summary.rows}
    assert by_event_key["event.politics"].specialist_team_id == "politics"
    assert by_event_key["event.crypto"].specialist_team_id == "crypto"
    assert by_event_key["event.macro"].specialist_team_id == "macro"
    assert by_event_key["event.gold"].specialist_team_id == "gold"
    assert by_event_key["event.soccer"].specialist_team_id == "soccer"
    assert by_event_key["event.basketball"].specialist_team_id == "basketball"
    assert by_event_key["event.crypto"].memory_queue_key == "team_memory.crypto.pass"

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].specialist_team_id = "crypto"  # type: ignore[misc]


def test_router_sets_pass_watch_and_block_statuses_with_decimal_scores() -> None:
    summary = report(
        (
            route_input("event.pass", event_category="crypto"),
            route_input(
                "event.watch",
                event_category="gold",
                evidence_score=d("0.620000"),
                coverage_score=d("0.650000"),
                memory_fit_score=d("0.700000"),
            ),
            route_input(
                "event.block",
                event_category="soccer",
                evidence_score=d("0.300000"),
                coverage_score=d("0.700000"),
                memory_fit_score=d("0.700000"),
            ),
        ),
    )

    assert tuple(row.public_status for row in summary.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.public_event_key for row in summary.rows) == (
        "event.block",
        "event.watch",
        "event.pass",
    )
    assert summary.public_status == "block"
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.rows[0].routing_score == d("0.566667")
    assert summary.rows[1].routing_score == d("0.656667")
    assert summary.rows[2].routing_score == d("0.850000")
    assert summary.rows[0].reason_codes == (
        "research_team_specialist_memory_router_low_evidence",
    )
    assert summary.rows[1].reason_codes == (
        "research_team_specialist_memory_router_watch_evidence",
        "research_team_specialist_memory_router_watch_coverage",
    )
    assert summary.rows[2].reason_codes == (
        "research_team_specialist_memory_router_pass",
    )


def test_router_rejects_bad_types_subclasses_flags_and_invalid_statuses() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        route_input(evidence_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="exactly str"):
        route_input(public_event_key=_StringSubclass("event.alpha"))

    with pytest.raises(TypeError, match="exactly Decimal"):
        route_input(evidence_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="paper_only"):
        route_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        route_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        route_input(readonly=False)

    with pytest.raises(ValueError, match="known public category"):
        route_input(event_category="sports.baseball")

    good = report((route_input(),))
    with pytest.raises(ValueError, match="public_status"):
        replace(good.rows[0], public_status="ready")

    with pytest.raises(ValueError, match="next_step"):
        replace(good, next_step="submit_memory")

    assert is_dataclass(ResearchTeamSpecialistMemoryRouterConfig)
    assert is_dataclass(ResearchTeamSpecialistMemoryRouterInput)
    assert is_dataclass(ResearchTeamSpecialistMemoryRouterRow)
    assert is_dataclass(ResearchTeamSpecialistMemoryRouterDigest)
    assert is_dataclass(ResearchTeamSpecialistMemoryRouterReport)
    assert ResearchTeamSpecialistMemoryRouterRow.__dataclass_params__.frozen is True


def test_router_rejects_public_leak_fragments_and_payload_stays_safe() -> None:
    unsafe_values = (
        "raw-candidate-123",
        "market-abc",
        "event-slug",
        "question-will-it-happen",
        "source-ref-alpha",
        "https://example.test/private",
        "dsn-prod",
        "table-public",
        "token-alpha",
        "wallet-alpha",
        "auth-alpha",
        "order-alpha",
        "position-alpha",
        "buy-alpha",
        "sell-alpha",
        "recommend-alpha",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            route_input(public_event_key=value)

    summary = report(
        (
            route_input("event.safe.2", event_category="macro"),
            route_input("event.safe.1", event_category="basketball"),
        ),
    )
    payload = public_supabase_memory_router_payload(summary)
    public = repr(payload).lower()
    for token in unsafe_values:
        assert token not in public
    assert "http" not in public
    assert "ready" not in public
    assert "blocked" not in public
    assert payload["public_status"] == "pass"
    assert tuple(row["public_status"] for row in payload["local_supabase_plan"]) == (
        "pass",
        "pass",
    )


def test_router_payload_is_deterministic_and_report_digest_is_consistent() -> None:
    inputs = (
        route_input("event.zeta", event_category="soccer"),
        route_input(
            "event.alpha",
            event_category="politics",
            evidence_score=d("0.600000"),
            coverage_score=d("0.620000"),
            memory_fit_score=d("0.610000"),
        ),
        route_input(
            "event.beta",
            event_category="crypto",
            evidence_score=d("0.200000"),
            coverage_score=d("0.900000"),
            memory_fit_score=d("0.900000"),
        ),
    )

    first = report(inputs)
    second = report(tuple(reversed(inputs)))

    assert public_supabase_memory_router_payload(first) == (
        public_supabase_memory_router_payload(second)
    )
    assert first.digest.public_status == first.public_status
    assert first.digest.event_count == first.event_count
    assert first.digest.pass_count == first.pass_count
    assert first.digest.watch_count == first.watch_count
    assert first.digest.block_count == first.block_count
    assert tuple(row.public_event_key for row in first.rows) == (
        "event.beta",
        "event.alpha",
        "event.zeta",
    )
    assert first.digest.team_status_counts == (
        ("crypto", "block", d("1.000000")),
        ("politics", "watch", d("1.000000")),
        ("soccer", "pass", d("1.000000")),
    )
    assert asdict(first)["digest"]["team_status_counts"] == first.digest.team_status_counts
