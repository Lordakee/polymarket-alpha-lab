from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import importlib
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.candidate_decision_score import (
    CandidateDecisionScoreConfig,
    CandidateDecisionScoreInput,
    CandidateDecisionScoreReport,
    build_candidate_decision_score_report,
)
from polymarket_alpha_lab.candidate_decision_score_history_cli_format import (
    format_candidate_decision_score_history_cli_stdout,
)


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_score_history"
GENERATED_AT = datetime(2026, 7, 7, 12, 30, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing candidate decision score history module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    candidate_id: str = "candidate-alpha",
    market_id: str = "market-alpha",
    gross_edge: Decimal | None = d("0.060000"),
    estimated_cost_drag: Decimal = d("0.010000"),
    cost_score: Decimal = d("0.800000"),
    liquidity_score: Decimal = d("0.900000"),
    evidence_score: Decimal = d("0.850000"),
    resolution_score: Decimal = d("0.700000"),
    team_memory_score: Decimal = d("0.750000"),
    team_memory_policy: str = "allow",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CandidateDecisionScoreReport:
    report = build_candidate_decision_score_report(
        CandidateDecisionScoreInput(
            candidate_id=candidate_id,
            market_id=market_id,
            normalized_market_question=f"Will {candidate_id} resolve yes?",
            primary_team_id="politics",
            secondary_team_ids=("crypto_btc",),
            selected_side="yes",
            forecast_probability=d("0.620000"),
            executable_price=d("0.560000"),
            gross_edge=gross_edge,
            estimated_cost_drag=estimated_cost_drag,
            cost_score=cost_score,
            liquidity_score=liquidity_score,
            evidence_score=evidence_score,
            resolution_score=resolution_score,
            team_memory_score=team_memory_score,
            team_memory_policy=team_memory_policy,
            source_report_refs=(
                f"candidate-decision-team-memory:{candidate_id}:2026-07-07",
                f"candidate-resolution-risk:{market_id}:2026-07-07",
            ),
            adapter_reason_codes=(
                "team_memory_adapter_allow",
                "resolution_risk_adapter_passed",
            ),
        ),
        config=CandidateDecisionScoreConfig(config_version="candidate-decision-score-v1"),
        generated_at=generated_at,
    )
    object.__setattr__(report, "paper_only", paper_only)
    object.__setattr__(report, "report_only", report_only)
    object.__setattr__(report, "readonly", readonly)
    return report


def test_empty_history_report_has_zero_decimal_counts_and_flags() -> None:
    module = api()
    generated_at = datetime(2026, 7, 7, 8, 30, tzinfo=timezone(timedelta(hours=-4)))

    history = module.build_candidate_decision_score_history_report(
        [],
        generated_at=generated_at,
    )

    assert type(history) is module.CandidateDecisionScoreHistoryReport
    assert history.generated_at == GENERATED_AT
    assert history.status == "empty"
    assert history.source_report_count == d("0.000000")
    assert history.report_count == d("0.000000")
    assert history.first_source_generated_at is None
    assert history.latest_generated_at is None
    assert history.candidate_count == d("0.000000")
    assert history.action_reject_count == d("0.000000")
    assert history.action_watch_count == d("0.000000")
    assert history.action_research_more_count == d("0.000000")
    assert history.action_paper_recommend_count == d("0.000000")
    assert history.hard_blocked_count == d("0.000000")
    assert history.blocked_total == d("0.000000")
    assert history.watch_total == d("0.000000")
    assert history.paper_recommend_total == d("0.000000")
    assert history.rows == ()
    assert history.action_counts == ()
    assert history.hard_blocker_code_counts == ()
    assert history.reason_code_counts == ()
    assert history.reason_counts == ()
    assert history.primary_team_counts == ()
    assert history.paper_only is True
    assert history.report_only is True
    assert history.readonly is True

    assert format_candidate_decision_score_history_cli_stdout(history) == (
        "candidate-decision-score-history: "
        "generated_at=2026-07-07T12:30:00+00:00 "
        "status=empty "
        "report_count=0.000000 "
        "latest_generated_at=none "
        "action_counts=none "
        "reason_counts=none "
        "primary_team_counts=none "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )


def test_history_sorts_reports_and_summarizes_actions_reasons_and_hard_flags() -> None:
    module = api()
    t0 = datetime(2026, 7, 7, 11, 0, tzinfo=UTC)
    t1 = datetime(2026, 7, 7, 11, 5, tzinfo=UTC)
    t2 = datetime(2026, 7, 7, 11, 10, tzinfo=UTC)
    watch_report = _report(
        generated_at=t0,
        candidate_id="candidate-alpha",
        market_id="market-alpha",
        gross_edge=d("0.012000"),
    )
    rejected_report = _report(
        generated_at=t1,
        candidate_id="candidate-beta",
        market_id="market-beta",
        evidence_score=d("0.100000"),
    )
    paper_recommend_report = _report(
        generated_at=t2,
        candidate_id="candidate-alpha",
        market_id="market-alpha",
    )

    history = module.build_candidate_decision_score_history_report(
        (paper_recommend_report, rejected_report, watch_report),
        generated_at=datetime(2026, 7, 7, 11, 30, tzinfo=UTC),
    )

    assert history.source_report_count == d("3.000000")
    assert history.report_count == d("3.000000")
    assert history.status == "observed"
    assert history.first_source_generated_at == t0
    assert history.latest_generated_at == t2
    assert history.candidate_count == d("2.000000")
    assert history.action_reject_count == d("1.000000")
    assert history.action_watch_count == d("1.000000")
    assert history.action_research_more_count == d("0.000000")
    assert history.action_paper_recommend_count == d("1.000000")
    assert history.hard_blocked_count == d("1.000000")
    assert history.blocked_total == d("1.000000")
    assert history.watch_total == d("1.000000")
    assert history.paper_recommend_total == d("1.000000")
    assert tuple(row.candidate_id for row in history.rows) == (
        "candidate-alpha",
        "candidate-beta",
        "candidate-alpha",
    )
    assert tuple(row.action for row in history.rows) == (
        "watch",
        "reject",
        "paper_recommend",
    )
    assert history.rows[1].hard_blocker_count == d("1.000000")
    assert history.rows[1].hard_blocker_codes == (
        "evidence_score_below_blocking_threshold",
    )
    assert history.hard_blocker_code_counts == (
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="evidence_score_below_blocking_threshold",
            count=d("1.000000"),
        ),
    )
    assert history.action_counts == (
        module.CandidateDecisionScoreHistoryActionCount(
            action="paper_recommend",
            count=d("1.000000"),
        ),
        module.CandidateDecisionScoreHistoryActionCount(
            action="reject",
            count=d("1.000000"),
        ),
        module.CandidateDecisionScoreHistoryActionCount(
            action="watch",
            count=d("1.000000"),
        ),
    )
    assert history.reason_code_counts == (
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="resolution_risk_adapter_passed",
            count=d("2.000000"),
        ),
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="team_memory_adapter_allow",
            count=d("2.000000"),
        ),
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="candidate_decision_paper_recommend",
            count=d("1.000000"),
        ),
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="candidate_decision_reject",
            count=d("1.000000"),
        ),
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="candidate_decision_watch",
            count=d("1.000000"),
        ),
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="evidence_score_below_blocking_threshold",
            count=d("1.000000"),
        ),
        module.CandidateDecisionScoreHistoryReasonCodeCount(
            reason_code="net_edge_below_paper_recommend_threshold",
            count=d("1.000000"),
        ),
    )
    assert history.reason_counts == history.reason_code_counts
    assert history.primary_team_counts == (
        module.CandidateDecisionScoreHistoryTeamCount(
            team_id="politics",
            count=d("3.000000"),
        ),
    )
    stdout = format_candidate_decision_score_history_cli_stdout(history)
    assert stdout == (
        "candidate-decision-score-history: "
        "generated_at=2026-07-07T11:30:00+00:00 "
        "status=observed "
        "report_count=3.000000 "
        "latest_generated_at=2026-07-07T11:10:00+00:00 "
        "action_counts=paper_recommend:1.000000,reject:1.000000,watch:1.000000 "
        "reason_counts=resolution_risk_adapter_passed:2.000000,"
        "team_memory_adapter_allow:2.000000,"
        "candidate_decision_paper_recommend:1.000000,"
        "candidate_decision_reject:1.000000,"
        "candidate_decision_watch:1.000000,"
        "evidence_score_below_blocking_threshold:1.000000,"
        "net_edge_below_paper_recommend_threshold:1.000000 "
        "primary_team_counts=politics:3.000000 "
        "paper_only=True "
        "report_only=True "
        "readonly=True\n"
    )
    for sensitive_value in ("candidate-alpha", "candidate-beta", "market-alpha", "market-beta"):
        assert sensitive_value not in stdout


def test_history_accepts_a_single_report_value() -> None:
    module = api()
    source_report = _report(gross_edge=None)

    history = module.build_candidate_decision_score_history_report(
        source_report,
        generated_at=GENERATED_AT,
    )

    assert history.source_report_count == d("1.000000")
    assert history.latest_generated_at == GENERATED_AT
    assert history.candidate_count == d("1.000000")
    assert history.action_research_more_count == d("1.000000")
    assert history.rows[0].action == "research_more"


def test_history_rejects_duplicate_source_sort_keys() -> None:
    module = api()
    report = _report()

    with pytest.raises(ValueError, match="duplicate.*generated_at.*candidate"):
        module.build_candidate_decision_score_history_report(
            [report, report],
            generated_at=GENERATED_AT,
        )


def test_history_rejects_non_reports_and_false_hard_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="CandidateDecisionScoreReport"):
        module.build_candidate_decision_score_history_report(
            [object()],
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        module.build_candidate_decision_score_history_report(
            _report(paper_only=False),
            generated_at=GENERATED_AT,
        )


def test_history_dataclasses_are_frozen() -> None:
    module = api()
    history = module.build_candidate_decision_score_history_report(
        _report(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        history.action_watch_count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        history.rows[0].action = "watch"  # type: ignore[misc]


def test_history_rejects_naive_generated_at() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_candidate_decision_score_history_report(
            [],
            generated_at=datetime(2026, 7, 7, 12, 30),
        )


def test_history_report_validates_formatter_compatibility_fields() -> None:
    module = api()
    history = module.build_candidate_decision_score_history_report(
        _report(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="report_count must match"):
        module.CandidateDecisionScoreHistoryReport(
            **{
                **history.__dict__,
                "report_count": d("2.000000"),
            },
        )
    with pytest.raises(ValueError, match="reason_counts must match"):
        module.CandidateDecisionScoreHistoryReport(
            **{
                **history.__dict__,
                "reason_counts": (),
            },
        )
    with pytest.raises(ValueError, match="primary_team_counts must match"):
        module.CandidateDecisionScoreHistoryReport(
            **{
                **history.__dict__,
                "primary_team_counts": (),
            },
        )


def test_candidate_decision_score_history_module_keeps_pure_boundary() -> None:
    source_path = Path("src/polymarket_alpha_lab/candidate_decision_score_history.py")
    assert source_path.exists(), "missing candidate decision score history module"
    source = source_path.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "click",
        "argparse",
        "open(",
        ".write(",
        "wallet",
        "private_key",
        "account",
        "auth",
        "place_order",
        "create_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "live_trading",
    )

    assert [term for term in forbidden_terms if term in source] == []
