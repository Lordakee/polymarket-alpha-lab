from __future__ import annotations

import ast
import dataclasses
import inspect
import json
import re
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_recommendation_research_readiness_digest import (
    DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION,
    StrategyRecommendationResearchReadinessCandidate,
    StrategyRecommendationResearchReadinessDigestConfig,
    StrategyRecommendationResearchReadinessDigestReport,
    build_strategy_recommendation_research_readiness_digest,
    strategy_recommendation_research_readiness_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _candidate(
    *,
    candidate_id: str = "candidate-a",
    market_slug: str = "market-a",
    outcome_name: str = "Yes",
    source_count: Decimal = d("3"),
    evidence_collected_at: datetime = GENERATED_AT - timedelta(hours=1),
    rationale_summary: str = "Model edge is supported by public evidence.",
    rationale_evidence: str = "Independent public sources agree.",
    rationale_risk_notes: str = "Liquidity and rule ambiguity reviewed.",
    resolution_criteria: str = "Market resolves from the public final result.",
    resolution_source_name: str = "official-results",
    team_memory_feedback_refs: tuple[str, ...] = ("memory-feedback:alpha",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyRecommendationResearchReadinessCandidate:
    return StrategyRecommendationResearchReadinessCandidate(
        candidate_id=candidate_id,
        market_slug=market_slug,
        outcome_name=outcome_name,
        source_count=source_count,
        evidence_collected_at=evidence_collected_at,
        rationale_summary=rationale_summary,
        rationale_evidence=rationale_evidence,
        rationale_risk_notes=rationale_risk_notes,
        resolution_criteria=resolution_criteria,
        resolution_source_name=resolution_source_name,
        team_memory_feedback_refs=team_memory_feedback_refs,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build_report(
    *candidates: StrategyRecommendationResearchReadinessCandidate,
    config: StrategyRecommendationResearchReadinessDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyRecommendationResearchReadinessDigestReport:
    return build_strategy_recommendation_research_readiness_digest(
        candidates,
        config=config or StrategyRecommendationResearchReadinessDigestConfig(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_digest() -> None:
    report = _build_report()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.candidate_count == d("0")
    assert report.ready_candidate_count == d("0")
    assert report.needs_review_candidate_count == d("0")
    assert report.blocked_candidate_count == d("0")
    assert report.ready_candidate_ratio is None
    assert report.rows == ()
    assert report.reason_codes == ("readiness_empty_candidates",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_ready_candidates_roll_up_all_readiness_categories() -> None:
    report = _build_report(
        _candidate(candidate_id="candidate-b", market_slug="market-z"),
        _candidate(
            candidate_id="candidate-a",
            market_slug="market-a",
            evidence_collected_at=datetime(
                2026,
                7,
                2,
                7,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            2,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.digest_status == "research_ready"
    assert report.candidate_count == d("2")
    assert report.ready_candidate_count == d("2")
    assert report.ready_candidate_ratio == d("1.000000")
    assert report.source_quorum_met_count == d("2")
    assert report.source_quorum_gap_count == d("0")
    assert report.fresh_evidence_count == d("2")
    assert report.stale_evidence_count == d("0")
    assert report.complete_rationale_count == d("2")
    assert report.incomplete_rationale_count == d("0")
    assert report.resolution_criteria_covered_count == d("2")
    assert report.resolution_criteria_missing_count == d("0")
    assert report.team_memory_feedback_available_count == d("2")
    assert report.team_memory_feedback_missing_count == d("0")
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-a",
        "candidate-b",
    )
    assert report.rows[0].evidence_collected_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert report.rows[0].evidence_age_seconds == d("1800.000000")
    assert report.rows[0].criterion_count == d("5")
    assert report.rows[0].satisfied_criterion_count == d("5")
    assert report.rows[0].issue_count == d("0")
    assert report.rows[0].readiness_ratio == d("1.000000")
    assert report.reason_codes == (
        "readiness_source_quorum_met",
        "readiness_evidence_fresh",
        "readiness_rationale_complete",
        "readiness_resolution_criteria_covered",
        "readiness_team_memory_feedback_available",
    )


def test_source_quorum_gaps_are_reported_without_blocking_single_gap() -> None:
    report = _build_report(
        _candidate(source_count=d("1")),
        config=StrategyRecommendationResearchReadinessDigestConfig(
            minimum_source_count=d("3"),
        ),
    )

    assert report.digest_status == "needs_review"
    assert report.source_quorum_met_count == d("0")
    assert report.source_quorum_gap_count == d("1")
    assert report.rows[0].source_gap_count == d("2")
    assert report.rows[0].readiness_status == "needs_review"
    assert "readiness_source_quorum_gap" in report.rows[0].reason_codes


def test_stale_evidence_is_reported() -> None:
    report = _build_report(
        _candidate(evidence_collected_at=GENERATED_AT - timedelta(days=3)),
        config=StrategyRecommendationResearchReadinessDigestConfig(
            max_evidence_age_seconds=d("86400"),
        ),
    )

    assert report.digest_status == "needs_review"
    assert report.fresh_evidence_count == d("0")
    assert report.stale_evidence_count == d("1")
    assert report.rows[0].evidence_age_seconds == d("259200.000000")
    assert "readiness_evidence_stale" in report.rows[0].reason_codes


def test_incomplete_rationale_is_reported() -> None:
    report = _build_report(_candidate(rationale_evidence=" "))

    assert report.digest_status == "needs_review"
    assert report.complete_rationale_count == d("0")
    assert report.incomplete_rationale_count == d("1")
    assert "readiness_rationale_incomplete" in report.rows[0].reason_codes


def test_missing_resolution_criteria_is_reported() -> None:
    report = _build_report(_candidate(resolution_criteria="", resolution_source_name=" "))

    assert report.digest_status == "needs_review"
    assert report.resolution_criteria_covered_count == d("0")
    assert report.resolution_criteria_missing_count == d("1")
    assert "readiness_resolution_criteria_missing" in report.rows[0].reason_codes


def test_missing_team_memory_feedback_is_reported() -> None:
    report = _build_report(_candidate(team_memory_feedback_refs=()))

    assert report.digest_status == "needs_review"
    assert report.team_memory_feedback_available_count == d("0")
    assert report.team_memory_feedback_missing_count == d("1")
    assert "readiness_team_memory_feedback_missing" in report.rows[0].reason_codes


def test_rows_and_reason_codes_are_sorted_stably() -> None:
    report = _build_report(
        _candidate(
            candidate_id="candidate-c",
            market_slug="market-c",
            source_count=d("1"),
            rationale_summary="",
        ),
        _candidate(
            candidate_id="candidate-a",
            market_slug="market-a",
            team_memory_feedback_refs=(),
        ),
        _candidate(
            candidate_id="candidate-b",
            market_slug="market-b",
            evidence_collected_at=GENERATED_AT - timedelta(days=5),
            resolution_criteria="",
        ),
        config=StrategyRecommendationResearchReadinessDigestConfig(
            minimum_source_count=d("2"),
            max_evidence_age_seconds=d("86400"),
        ),
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-a",
        "candidate-b",
        "candidate-c",
    )
    assert report.reason_codes == (
        "readiness_source_quorum_met",
        "readiness_source_quorum_gap",
        "readiness_evidence_fresh",
        "readiness_evidence_stale",
        "readiness_rationale_complete",
        "readiness_rationale_incomplete",
        "readiness_resolution_criteria_covered",
        "readiness_resolution_criteria_missing",
        "readiness_team_memory_feedback_available",
        "readiness_team_memory_feedback_missing",
    )


def test_payload_contains_decimal_strings_and_no_floats() -> None:
    payload = strategy_recommendation_research_readiness_digest_payload(
        _build_report(_candidate()),
    )

    assert payload["candidate_count"] == "1"
    assert payload["ready_candidate_ratio"] == "1.000000"
    assert payload["rows"][0]["source_count"] == "3"
    assert payload["rows"][0]["evidence_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["generated_at"] == "2026-07-02T12:00:00Z"
    assert payload["rows"][0]["evidence_collected_at"] == "2026-07-02T11:00:00Z"
    json.dumps(payload, sort_keys=True)

    def assert_no_floats(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_floats(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_floats(item)
        else:
            assert type(value) is not float

    assert_no_floats(payload)


def test_payload_rejects_unsafe_surface_fields_and_hard_flag_mutations() -> None:
    report = _build_report(_candidate())
    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "wallet_surface", "not allowed")

    with pytest.raises(ValueError, match="unsafe live surface field"):
        strategy_recommendation_research_readiness_digest_payload(unsafe_report)
    with pytest.raises(ValueError, match="report_only"):
        strategy_recommendation_research_readiness_digest_payload(
            replace(report, report_only=False),
        )
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_research_readiness_digest_payload(
            replace(report, readonly=False),
        )
    nested_flag_report = _build_report(_candidate(candidate_id="nested-flag-row"))
    object.__setattr__(nested_flag_report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        strategy_recommendation_research_readiness_digest_payload(nested_flag_report)

    unsafe_value_report = _build_report(_candidate(candidate_id="unsafe-value-row"))
    object.__setattr__(unsafe_value_report.rows[0], "candidate_id", "wallet_candidate")
    with pytest.raises(ValueError, match="unsafe"):
        strategy_recommendation_research_readiness_digest_payload(unsafe_value_report)


def test_candidate_rejects_unsafe_surface_and_secret_text_values() -> None:
    secret = "postgres://paper:secret-token@localhost/polymarket"

    with pytest.raises(ValueError, match="unsafe"):
        _candidate(candidate_id="wallet_candidate")
    with pytest.raises(ValueError, match="unsafe"):
        _candidate(rationale_evidence=secret)
    with pytest.raises(ValueError, match="unsafe"):
        _candidate(team_memory_feedback_refs=(secret,))


def test_validation_errors_cover_bad_types_times_counts_consistency_and_flags() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        _candidate(candidate_id=_StringSubclass("candidate-a"))
    with pytest.raises(ValueError, match="source_count"):
        _candidate(source_count=d("-1"))
    with pytest.raises(ValueError, match="source_count"):
        _candidate(source_count=d("1.5"))
    with pytest.raises(ValueError, match="source_count"):
        _candidate(source_count=_DecimalSubclass("3"))
    with pytest.raises(ValueError, match="minimum_source_count"):
        StrategyRecommendationResearchReadinessDigestConfig(minimum_source_count=3)
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        StrategyRecommendationResearchReadinessDigestConfig(
            max_evidence_age_seconds=_DecimalSubclass("172800"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _build_report(_candidate(), generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        _build_report(_candidate(), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="evidence_collected_at"):
        _build_report(_candidate(evidence_collected_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(StrategyRecommendationResearchReadinessDigestConfig(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _candidate(readonly=False)
    with pytest.raises(ValueError, match="candidate_count"):
        StrategyRecommendationResearchReadinessDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION
            ),
            digest_status="research_ready",
            candidate_count=d("2"),
            ready_candidate_count=d("1"),
            needs_review_candidate_count=d("0"),
            blocked_candidate_count=d("0"),
            ready_candidate_ratio=d("1.000000"),
            needs_review_candidate_ratio=d("0.000000"),
            blocked_candidate_ratio=d("0.000000"),
            source_quorum_met_count=d("1"),
            source_quorum_gap_count=d("0"),
            fresh_evidence_count=d("1"),
            stale_evidence_count=d("0"),
            complete_rationale_count=d("1"),
            incomplete_rationale_count=d("0"),
            resolution_criteria_covered_count=d("1"),
            resolution_criteria_missing_count=d("0"),
            team_memory_feedback_available_count=d("1"),
            team_memory_feedback_missing_count=d("0"),
            rows=_build_report(_candidate()).rows,
            reason_codes=("readiness_source_quorum_met",),
        )


def test_public_numeric_count_and_ratio_fields_are_decimals() -> None:
    report = _build_report(_candidate())
    instances = (
        StrategyRecommendationResearchReadinessDigestConfig(),
        _candidate(),
        report.rows[0],
        report,
    )

    for instance in instances:
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, bool):
                continue
            assert type(value) is not int
            assert type(value) is not float
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                assert value is None or type(value) is Decimal


def test_dataclasses_are_frozen() -> None:
    candidate = _candidate()
    report = _build_report(candidate)

    with pytest.raises(FrozenInstanceError):
        candidate.source_count = d("4")
    with pytest.raises(FrozenInstanceError):
        report.rows[0].readiness_status = "needs_review"
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "blocked"


def test_module_scope_has_no_forbidden_external_or_action_surface_terms() -> None:
    import polymarket_alpha_lab.strategy_recommendation_research_readiness_digest as api

    source = inspect.getsource(api)
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "asyncpg",
        "aiohttp",
        "httpx",
        "pg8000",
        "psycopg",
        "pymysql",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "urllib",
        "web3",
    }
    for term in (
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "db",
        "database",
        "signing",
        "advice",
        "trade",
        "trading",
        "private_key",
    ):
        assert re.search(rf"\b{re.escape(term)}\b", source.lower()) is None
    assert api.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_RESEARCH_READINESS_DIGEST_CONFIG_VERSION",
        "StrategyRecommendationResearchReadinessCandidate",
        "StrategyRecommendationResearchReadinessDigestConfig",
        "StrategyRecommendationResearchReadinessDigestReport",
        "StrategyRecommendationResearchReadinessDigestRow",
        "build_strategy_recommendation_research_readiness_digest",
        "strategy_recommendation_research_readiness_digest_payload",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"read", "write"}
