import ast
from dataclasses import FrozenInstanceError, dataclass, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.strategy_recommendation_team_load_digest import (
    REASON_CODES,
    StrategyRecommendationTeamLoadAssignment,
    StrategyRecommendationTeamLoadDigestConfig,
    StrategyRecommendationTeamLoadDigestReasonCodeCount,
    StrategyRecommendationTeamLoadDigestReport,
    StrategyRecommendationTeamLoadDigestTeamRow,
    build_strategy_recommendation_team_load_digest,
    strategy_recommendation_team_load_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "strategy-recommendation-team-load-digest-v0"


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


@dataclass(frozen=True)
class ForeignAssignmentShape:
    team_id: str = "team-a"
    candidate_id: str = "cand-a"
    market_category: str = "crypto"
    assigned_at: datetime = GENERATED_AT - timedelta(hours=1)
    research_due_at: datetime = GENERATED_AT + timedelta(hours=1)
    evidence_conflict_status: str = "none"
    team_specialization_categories: tuple[str, ...] = ("crypto",)
    team_review_capacity_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def assignment(
    candidate_id: str = "cand-a",
    *,
    team_id: str = "team-a",
    category: str = "crypto",
    due_delta: timedelta = timedelta(hours=1),
    conflict_status: str = "none",
    specializations: tuple[str, ...] = ("crypto",),
    capacity: str = "2",
    assigned_delta: timedelta = timedelta(hours=-1),
) -> StrategyRecommendationTeamLoadAssignment:
    return StrategyRecommendationTeamLoadAssignment(
        team_id=team_id,
        candidate_id=candidate_id,
        market_category=category,
        assigned_at=GENERATED_AT + assigned_delta,
        research_due_at=GENERATED_AT + due_delta,
        evidence_conflict_status=conflict_status,
        team_specialization_categories=specializations,
        team_review_capacity_count=d(capacity),
    )


def digest(
    assignments: tuple[StrategyRecommendationTeamLoadAssignment, ...],
    *,
    config: StrategyRecommendationTeamLoadDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationTeamLoadDigestReport:
    return build_strategy_recommendation_team_load_digest(
        assignments,
        config=config or StrategyRecommendationTeamLoadDigestConfig(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_floats(item)
    else:
        assert type(value) is not float


def test_empty_input_returns_report_only_pass_digest() -> None:
    report = digest(())

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.status == "pass"
    assert report.team_count == d("0")
    assert report.assigned_candidate_count == d("0")
    assert report.overdue_research_count == d("0")
    assert report.unresolved_evidence_conflict_count == d("0")
    assert report.category_specialization_fit_count == d("0")
    assert report.category_specialization_mismatch_count == d("0")
    assert report.category_specialization_fit_ratio == d("1.000000")
    assert report.review_capacity_count == d("0")
    assert report.review_capacity_headroom_count == d("0")
    assert report.team_rows == ()
    assert report.reason_codes == ("team_load_digest_empty",)
    assert report.reason_code_counts == (
        StrategyRecommendationTeamLoadDigestReasonCodeCount(
            "team_load_digest_empty",
            d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_healthy_load_summarizes_readiness_counts_and_capacity() -> None:
    report = digest(
        (
            assignment("cand-a", capacity="3"),
            assignment(
                "cand-b",
                assigned_delta=timedelta(hours=-2),
                due_delta=timedelta(hours=2),
                capacity="3",
            ),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.team_count == d("1")
    assert report.assigned_candidate_count == d("2")
    assert report.overdue_research_count == d("0")
    assert report.unresolved_evidence_conflict_count == d("0")
    assert report.category_specialization_fit_count == d("2")
    assert report.category_specialization_fit_ratio == d("1.000000")
    assert report.review_capacity_count == d("3")
    assert report.review_capacity_headroom_count == d("1")
    assert report.reason_codes == ("team_load_review_ready",)

    (row,) = report.team_rows
    assert row.team_id == "team-a"
    assert row.status == "pass"
    assert row.assigned_candidate_count == d("2")
    assert row.category_specialization_fit_ratio == d("1.000000")
    assert row.review_capacity_headroom_count == d("1")
    assert row.reason_codes == ("team_load_review_ready",)


def test_watch_overload_preserves_negative_decimal_headroom() -> None:
    report = digest(
        (
            assignment("cand-a", capacity="1"),
            assignment("cand-b", capacity="1"),
        ),
    )

    assert report.status == "watch"
    assert report.assigned_candidate_count == d("2")
    assert report.review_capacity_count == d("1")
    assert report.review_capacity_headroom_count == d("-1")
    assert report.reason_codes == ("team_load_review_capacity_overloaded",)
    assert report.team_rows[0].status == "watch"
    assert report.team_rows[0].reason_codes == (
        "team_load_review_capacity_overloaded",
    )


def test_blocked_backlog_uses_overdue_threshold() -> None:
    report = digest(
        (
            assignment("cand-a", due_delta=timedelta(minutes=-1), capacity="4"),
            assignment(
                "cand-b",
                assigned_delta=timedelta(hours=-3),
                due_delta=timedelta(hours=-2),
                capacity="4",
            ),
        ),
    )

    assert report.status == "blocked"
    assert report.overdue_research_count == d("2")
    assert report.reason_codes == ("team_load_overdue_research_backlog",)
    assert report.team_rows[0].reason_codes == (
        "team_load_overdue_research_backlog",
    )


def test_specialization_mismatch_is_watch() -> None:
    report = digest(
        (
            assignment(
                "cand-a",
                category="sports",
                specializations=("crypto",),
                capacity="2",
            ),
            assignment("cand-b", category="crypto", capacity="2"),
        ),
    )

    assert report.status == "watch"
    assert report.category_specialization_fit_count == d("1")
    assert report.category_specialization_mismatch_count == d("1")
    assert report.category_specialization_fit_ratio == d("0.500000")
    assert report.reason_codes == ("team_load_category_specialization_mismatch",)


def test_unresolved_conflicts_block_review_readiness() -> None:
    report = digest(
        (
            assignment(
                "cand-a",
                conflict_status="unresolved",
                capacity="2",
            ),
        ),
    )

    assert report.status == "blocked"
    assert report.unresolved_evidence_conflict_count == d("1")
    assert report.reason_codes == ("team_load_unresolved_evidence_conflicts",)


def test_rows_and_reason_code_rollups_are_stably_sorted() -> None:
    report = digest(
        (
            assignment("cand-z", team_id="team-z", capacity="3"),
            assignment("cand-b", team_id="team-b", conflict_status="unresolved"),
            assignment("cand-a", team_id="team-a", capacity="1"),
            assignment("cand-c", team_id="team-a", capacity="1"),
        ),
    )

    assert tuple(row.team_id for row in report.team_rows) == (
        "team-b",
        "team-a",
        "team-z",
    )
    assert report.reason_codes == (
        "team_load_unresolved_evidence_conflicts",
        "team_load_review_capacity_overloaded",
        "team_load_review_ready",
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == tuple(
        code for code in REASON_CODES if code in report.reason_codes
    )
    assert tuple(item.count for item in report.reason_code_counts) == (
        d("1"),
        d("1"),
        d("1"),
    )


def test_payload_helper_returns_decimal_strings_and_rejects_unsafe_payloads() -> None:
    report = digest((assignment("cand-a"),))
    payload = strategy_recommendation_team_load_digest_payload(report)

    assert payload["assigned_candidate_count"] == "1"
    assert payload["category_specialization_fit_ratio"] == "1.000000"
    assert payload["team_rows"][0]["review_capacity_headroom_count"] == "1"
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert_no_floats(payload)

    invalid_report = digest((assignment("cand-b"),))
    object.__setattr__(invalid_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        strategy_recommendation_team_load_digest_payload(invalid_report)

    with pytest.raises(ValueError, match="float"):
        strategy_recommendation_team_load_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "ratio": 0.25,
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_team_load_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_reference": "not allowed",
            },
        )


def test_validation_errors_reject_ambiguous_or_mutable_inputs() -> None:
    with pytest.raises(ValueError, match="config"):
        build_strategy_recommendation_team_load_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="inputs"):
        build_strategy_recommendation_team_load_digest(
            object(),
            config=StrategyRecommendationTeamLoadDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="exact team load assignments"):
        digest((ForeignAssignmentShape(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        digest((), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="team_id"):
        assignment(team_id=_StringSubclass("team-a"))
    with pytest.raises(ValueError, match="team_review_capacity_count"):
        assignment(capacity="1.5")
    with pytest.raises(ValueError, match="team_review_capacity_count"):
        StrategyRecommendationTeamLoadAssignment(
            team_id="team-a",
            candidate_id="cand-a",
            market_category="crypto",
            assigned_at=GENERATED_AT,
            research_due_at=GENERATED_AT + timedelta(hours=1),
            evidence_conflict_status="none",
            team_specialization_categories=("crypto",),
            team_review_capacity_count=_DecimalSubclass("1"),
        )
    with pytest.raises(ValueError, match="duplicate candidate"):
        digest((assignment("cand-a"), assignment("cand-a", team_id="team-b")))
    with pytest.raises(ValueError, match="team metadata"):
        digest(
            (
                assignment("cand-a", team_id="team-a", capacity="2"),
                assignment("cand-b", team_id="team-a", capacity="3"),
            ),
        )
    with pytest.raises(ValueError, match="team_specialization_categories"):
        StrategyRecommendationTeamLoadAssignment(
            team_id="team-a",
            candidate_id="cand-a",
            market_category="crypto",
            assigned_at=GENERATED_AT,
            research_due_at=GENERATED_AT + timedelta(hours=1),
            evidence_conflict_status="none",
            team_specialization_categories=("macro", "crypto"),
            team_review_capacity_count=d("1"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        assignment("cand-a", capacity="1", conflict_status="none").__class__(
            team_id="team-a",
            candidate_id="cand-b",
            market_category="crypto",
            assigned_at=GENERATED_AT,
            research_due_at=GENERATED_AT + timedelta(hours=1),
            evidence_conflict_status="none",
            team_specialization_categories=("crypto",),
            team_review_capacity_count=d("1"),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_and_numeric_fields_are_decimal() -> None:
    public_dataclasses = (
        StrategyRecommendationTeamLoadDigestConfig,
        StrategyRecommendationTeamLoadAssignment,
        StrategyRecommendationTeamLoadDigestTeamRow,
        StrategyRecommendationTeamLoadDigestReasonCodeCount,
        StrategyRecommendationTeamLoadDigestReport,
    )
    numeric_name_fragments = ("count", "ratio", "capacity", "threshold", "headroom")
    for dataclass_type in public_dataclasses:
        type_hints = get_type_hints(dataclass_type)
        for item in fields(dataclass_type):
            if item.name == "reason_code_counts":
                continue
            if any(fragment in item.name for fragment in numeric_name_fragments):
                assert type_hints[item.name] is Decimal

    report = digest((assignment("cand-a"),))
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.team_rows[0].team_id = "team-b"  # type: ignore[misc]


def test_static_module_has_no_db_network_trading_or_advice_surface_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_recommendation_team_load_digest.py"
    )
    module_source = module_path.read_text()
    module = ast.parse(module_source)
    imported_roots: set[str] = set()
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "typing",
        "polymarket_alpha_lab",
    }
    forbidden_terms = (
        "psycopg",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "wallet",
        "broker",
        "private_key",
        "api_key",
        "order_id",
        "signing",
        "signature",
        "trade",
        "trading",
        "advice",
        "auth",
        "open(",
    )
    lowered_source = module_source.lower()
    for term in forbidden_terms:
        assert term not in lowered_source
