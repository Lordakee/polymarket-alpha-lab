from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_memory_retrieval_policy import (
    ResearchTeamMemoryRetrievalNeed,
    ResearchTeamMemoryRetrievalPolicyConfig,
    ResearchTeamMemoryRetrievalPolicyReasonCodeCount,
    ResearchTeamMemoryRetrievalPolicyReport,
    ResearchTeamMemoryRetrievalScoreRow,
    build_research_team_memory_retrieval_policy_report,
    research_team_memory_retrieval_policy_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedNeedShape:
    brief_id: str
    retrieval_lane: str
    query_intent_id: str
    retrieval_goal: str
    required_memory_count: Decimal
    available_memory_count: Decimal
    freshness_score: Decimal
    semantic_similarity_score: Decimal
    redaction_confirmed: bool = True
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamMemoryRetrievalPolicyConfig:
    values = {
        "config_version": "research-team-memory-retrieval-policy-v0",
        "pass_readiness_score": d("0.800000"),
        "watch_readiness_score": d("0.550000"),
        "coverage_weight": d("0.500000"),
        "freshness_weight": d("0.250000"),
        "semantic_similarity_weight": d("0.250000"),
        "domain_lane_weight": d("0.200000"),
        "event_type_lane_weight": d("0.200000"),
        "similar_history_lane_weight": d("0.200000"),
        "calibration_review_lane_weight": d("0.200000"),
        "conflict_case_lane_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchTeamMemoryRetrievalPolicyConfig(**values)


def need(
    lane: str,
    *,
    brief_id: str = "brief-alpha",
    required: str = "2",
    available: str = "3",
    freshness: str = "0.900000",
    similarity: str = "0.800000",
    query_intent_id: str | None = None,
    retrieval_goal: str | None = None,
    redaction_confirmed: bool = True,
    reason_codes: tuple[str, ...] = (),
) -> ResearchTeamMemoryRetrievalNeed:
    return ResearchTeamMemoryRetrievalNeed(
        brief_id=brief_id,
        retrieval_lane=lane,
        query_intent_id=query_intent_id or f"{lane}-query",
        retrieval_goal=retrieval_goal or f"Plan {lane} memory retrieval",
        required_memory_count=d(required),
        available_memory_count=d(available),
        freshness_score=d(freshness),
        semantic_similarity_score=d(similarity),
        redaction_confirmed=redaction_confirmed,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchTeamMemoryRetrievalPolicyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamMemoryRetrievalPolicyReport:
    return build_research_team_memory_retrieval_policy_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def complete_needs() -> tuple[ResearchTeamMemoryRetrievalNeed, ...]:
    return (
        need("domain", freshness="0.900000", similarity="0.800000"),
        need(
            "event_type",
            required="2",
            available="2",
            freshness="0.800000",
            similarity="0.800000",
        ),
        need(
            "similar_history",
            required="3",
            available="4",
            freshness="0.700000",
            similarity="0.900000",
        ),
        need(
            "calibration_review",
            required="2",
            available="3",
            freshness="0.800000",
            similarity="0.700000",
        ),
        need(
            "conflict_case",
            required="1",
            available="2",
            freshness="0.900000",
            similarity="0.700000",
        ),
    )


def test_empty_input_returns_block_report_only_policy() -> None:
    policy_report = report(())

    assert type(policy_report) is ResearchTeamMemoryRetrievalPolicyReport
    assert policy_report.generated_at == GENERATED_AT
    assert policy_report.config_version == "research-team-memory-retrieval-policy-v0"
    assert policy_report.brief_count == d("0")
    assert policy_report.need_count == d("0")
    assert policy_report.pass_count == d("0")
    assert policy_report.watch_count == d("0")
    assert policy_report.block_count == d("0")
    assert policy_report.average_memory_readiness_score is None
    assert policy_report.status == "block"
    assert policy_report.reason_codes == ("no_memory_retrieval_needs",)
    assert policy_report.reason_code_counts == (
        ResearchTeamMemoryRetrievalPolicyReasonCodeCount(
            reason_code="no_memory_retrieval_needs",
            count=d("1"),
        ),
    )
    assert policy_report.rows == ()
    assert policy_report.paper_only is True
    assert policy_report.report_only is True
    assert policy_report.readonly is True


def test_complete_local_memory_plan_passes_with_deterministic_scores() -> None:
    policy_report = report(complete_needs())

    assert policy_report.status == "pass"
    assert policy_report.brief_count == d("1")
    assert policy_report.need_count == d("5")
    assert policy_report.pass_count == d("1")
    assert policy_report.watch_count == d("0")
    assert policy_report.block_count == d("0")
    assert policy_report.average_memory_readiness_score == d("0.900000")
    assert policy_report.reason_codes == ("research_team_memory_retrieval_pass",)

    row = policy_report.rows[0]
    assert type(row) is ResearchTeamMemoryRetrievalScoreRow
    assert row.brief_id == "brief-alpha"
    assert row.required_lane_count == d("5")
    assert row.planned_lane_count == d("5")
    assert row.missing_lane_count == d("0")
    assert row.total_required_memory_count == d("10")
    assert row.total_available_memory_count == d("14")
    assert row.domain_memory_count == d("3")
    assert row.event_type_memory_count == d("2")
    assert row.similar_history_memory_count == d("4")
    assert row.calibration_review_memory_count == d("3")
    assert row.conflict_case_memory_count == d("2")
    assert row.domain_lane_score == d("0.925000")
    assert row.event_type_lane_score == d("0.900000")
    assert row.similar_history_lane_score == d("0.900000")
    assert row.calibration_review_lane_score == d("0.875000")
    assert row.conflict_case_lane_score == d("0.900000")
    assert row.memory_readiness_score == d("0.900000")
    assert row.status == "pass"
    assert row.retrieval_lanes == (
        "calibration_review",
        "conflict_case",
        "domain",
        "event_type",
        "similar_history",
    )
    assert row.reason_codes == (
        "all_memory_lanes_planned",
        "calibration_reviews_available",
        "conflict_cases_available",
        "local_memory_queries_planned",
        "research_team_memory_retrieval_pass",
    )


def test_complete_local_memory_plan_enters_watch_branch() -> None:
    policy_report = report(
        (
            need("domain", required="2", available="1", freshness="0.600000", similarity="0.600000"),
            need(
                "event_type",
                required="2",
                available="1",
                freshness="0.600000",
                similarity="0.600000",
            ),
            need(
                "similar_history",
                required="2",
                available="1",
                freshness="0.600000",
                similarity="0.600000",
            ),
            need(
                "calibration_review",
                required="2",
                available="1",
                freshness="0.600000",
                similarity="0.600000",
            ),
            need(
                "conflict_case",
                required="2",
                available="1",
                freshness="0.600000",
                similarity="0.600000",
            ),
        ),
    )

    row = policy_report.rows[0]
    assert policy_report.status == "watch"
    assert policy_report.pass_count == d("0")
    assert policy_report.watch_count == d("1")
    assert policy_report.block_count == d("0")
    assert policy_report.reason_codes == ("research_team_memory_retrieval_watch",)
    assert row.status == "watch"
    assert row.memory_readiness_score == d("0.550000")
    assert row.reason_codes == (
        "all_memory_lanes_planned",
        "calibration_reviews_available",
        "conflict_cases_available",
        "local_memory_queries_planned",
        "research_team_memory_retrieval_watch",
    )


def test_redaction_not_confirmed_blocks_complete_high_score_report_without_crashing() -> None:
    policy_report = report(
        tuple(
            replace(item, redaction_confirmed=False)
            if item.retrieval_lane == "domain"
            else item
            for item in complete_needs()
        ),
    )

    row = policy_report.rows[0]
    assert policy_report.status == "block"
    assert policy_report.pass_count == d("0")
    assert policy_report.watch_count == d("0")
    assert policy_report.block_count == d("1")
    assert policy_report.average_memory_readiness_score == d("0.900000")
    assert row.status == "block"
    assert row.redaction_issue_count == d("1")
    assert row.reason_codes == (
        "all_memory_lanes_planned",
        "calibration_reviews_available",
        "conflict_cases_available",
        "local_memory_queries_planned",
        "memory_redaction_not_confirmed",
        "research_team_memory_retrieval_block",
    )


def test_score_row_consistency_uses_configured_status_thresholds() -> None:
    policy_report = report(
        (
            need("domain", required="2", available="1", freshness="1.000000", similarity="1.000000"),
            need(
                "event_type",
                required="2",
                available="1",
                freshness="1.000000",
                similarity="1.000000",
            ),
            need(
                "similar_history",
                required="2",
                available="1",
                freshness="1.000000",
                similarity="1.000000",
            ),
            need(
                "calibration_review",
                required="2",
                available="1",
                freshness="1.000000",
                similarity="1.000000",
            ),
            need(
                "conflict_case",
                required="2",
                available="1",
                freshness="1.000000",
                similarity="1.000000",
            ),
        ),
        cfg=config(
            pass_readiness_score=d("0.700000"),
            watch_readiness_score=d("0.400000"),
        ),
    )

    row = policy_report.rows[0]
    assert row.memory_readiness_score == d("0.750000")
    assert row.status == "pass"
    assert row.pass_readiness_score == d("0.700000")
    assert row.watch_readiness_score == d("0.400000")


def test_score_row_consistency_accepts_configured_non_default_lane_weights() -> None:
    policy_report = report(
        complete_needs(),
        cfg=config(
            domain_lane_weight=d("0.400000"),
            event_type_lane_weight=d("0.300000"),
            similar_history_lane_weight=d("0.100000"),
            calibration_review_lane_weight=d("0.100000"),
            conflict_case_lane_weight=d("0.100000"),
        ),
    )

    row = policy_report.rows[0]
    assert policy_report.status == "pass"
    assert row.memory_readiness_score == d("0.907500")
    assert row.status == "pass"


def test_missing_similar_history_calibration_and_conflict_cases_block_plan() -> None:
    policy_report = report(
        (
            need("domain"),
            need(
                "event_type",
                required="2",
                available="2",
                freshness="0.800000",
                similarity="0.800000",
            ),
        ),
    )

    row = policy_report.rows[0]
    assert policy_report.status == "block"
    assert policy_report.block_count == d("1")
    assert policy_report.average_memory_readiness_score == d("0.365000")
    assert row.planned_lane_count == d("2")
    assert row.missing_lane_count == d("3")
    assert row.similar_history_memory_count == d("0")
    assert row.calibration_review_memory_count == d("0")
    assert row.conflict_case_memory_count == d("0")
    assert row.memory_readiness_score == d("0.365000")
    assert row.status == "block"
    assert row.reason_codes == (
        "missing_calibration_review_memory",
        "missing_conflict_case_memory",
        "missing_similar_history_memory",
        "research_team_memory_retrieval_block",
    )


def test_supplied_need_shapes_are_coerced_without_database_access() -> None:
    policy_report = report(
        tuple(
            SuppliedNeedShape(
                brief_id=item.brief_id,
                retrieval_lane=item.retrieval_lane,
                query_intent_id=item.query_intent_id,
                retrieval_goal=item.retrieval_goal,
                required_memory_count=item.required_memory_count,
                available_memory_count=item.available_memory_count,
                freshness_score=item.freshness_score,
                semantic_similarity_score=item.semantic_similarity_score,
                redaction_confirmed=item.redaction_confirmed,
                reason_codes=item.reason_codes,
            )
            for item in complete_needs()
        ),
    )

    assert policy_report.status == "pass"
    assert policy_report.rows[0].query_intent_ids == (
        "calibration_review-query",
        "conflict_case-query",
        "domain-query",
        "event_type-query",
        "similar_history-query",
    )


def test_payload_is_json_ready_decimal_only_and_excludes_sensitive_identifiers() -> None:
    policy_report = report(complete_needs())
    payload = research_team_memory_retrieval_policy_payload(policy_report)
    encoded = json.dumps(payload, sort_keys=True)
    encoded_lower = encoded.lower()

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["average_memory_readiness_score"] == "0.900000"
    assert payload["rows"][0]["memory_readiness_score"] == "0.900000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    for forbidden in (
        "dsn",
        "database_url",
        "table",
        "token",
        "raw_source",
        "source_id",
        "market_id",
        "market_slug",
        "market-",
        "postgres://",
        "postgresql://",
        "supabase.co",
    ):
        assert forbidden not in encoded_lower


def test_validation_rejects_bad_types_unknown_lanes_secrets_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="coverage_weight"):
        config(coverage_weight=d("0.400000"))
    with pytest.raises(ValueError, match="pass_readiness_score"):
        config(pass_readiness_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="semantic_similarity_weight"):
        config(semantic_similarity_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(complete_needs(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(complete_needs(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="retrieval_lane"):
        need("social_media")
    with pytest.raises(ValueError, match="available_memory_count"):
        replace(need("domain"), available_memory_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_score"):
        replace(need("domain"), freshness_score=d("1.000001"))
    with pytest.raises(ValueError, match="query_intent_id"):
        need("domain", query_intent_id="market-alpha")
    with pytest.raises(ValueError, match="retrieval_goal"):
        need("domain", retrieval_goal="Query raw_source notes")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        replace(need("domain"), redaction_confirmed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        need("domain", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(need("domain"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    policy_report = report(complete_needs())

    with pytest.raises(FrozenInstanceError):
        policy_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy_report.rows[0].memory_readiness_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_readiness_score"):
        replace(policy_report.rows[0], memory_readiness_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(policy_report, status="block")


def test_owned_module_has_no_database_network_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_memory_retrieval_policy.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "psycopg",
        "asyncpg",
        "sqlalchemy",
        "create_client",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "execute(",
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
