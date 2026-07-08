from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_cross_validation_router import (
    ResearchSourceCrossValidationCandidate,
    ResearchSourceCrossValidationConfig,
    ResearchSourceCrossValidationReport,
    ResearchSourceCrossValidationRoute,
    build_research_source_cross_validation_report,
    research_source_cross_validation_public_payload,
    research_source_cross_validation_supabase_summary,
    validate_research_source_cross_validation_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    index: int,
    *,
    raw_candidate_id: str | None = None,
    evidence_family_count: Decimal = d("2"),
    independent_source_count: Decimal = d("2"),
    stale_source_count: Decimal = d("0"),
    contradiction_count: Decimal = d("0"),
    sensitive_source_count: Decimal = d("0"),
    policy_uncertainty_score: Decimal = d("0.100000"),
    resolution_risk_score: Decimal = d("0.100000"),
    urgency_score: Decimal = d("0.200000"),
    has_primary_source: bool = True,
    needs_legal_review: bool = False,
    needs_rules_review: bool = False,
    submitted_at: datetime | None = None,
) -> ResearchSourceCrossValidationCandidate:
    return ResearchSourceCrossValidationCandidate(
        raw_candidate_id=raw_candidate_id or f"raw-candidate-{index:03d}",
        raw_market_id=f"market-{index:03d}",
        raw_market_slug=f"raw-market-slug-{index:03d}",
        raw_market_question=f"Will event {index} resolve?",
        raw_source_refs=(
            f"https://example.invalid/source/{index}",
            f"source text snippet {index}",
        ),
        submitted_at=(
            submitted_at if submitted_at is not None else GENERATED_AT - timedelta(hours=1)
        ),
        evidence_family_count=evidence_family_count,
        independent_source_count=independent_source_count,
        stale_source_count=stale_source_count,
        contradiction_count=contradiction_count,
        sensitive_source_count=sensitive_source_count,
        policy_uncertainty_score=policy_uncertainty_score,
        resolution_risk_score=resolution_risk_score,
        urgency_score=urgency_score,
        has_primary_source=has_primary_source,
        needs_legal_review=needs_legal_review,
        needs_rules_review=needs_rules_review,
    )


def build_report(
    candidates: tuple[ResearchSourceCrossValidationCandidate, ...],
    *,
    config: ResearchSourceCrossValidationConfig | None = None,
) -> ResearchSourceCrossValidationReport:
    return build_research_source_cross_validation_report(
        candidates,
        config=config or ResearchSourceCrossValidationConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def flattened_strings(value: object) -> tuple[str, ...]:
    items: list[str] = []
    if type(value) is dict:
        for key, item in value.items():
            items.append(key)
            items.extend(flattened_strings(item))
    elif type(value) is list:
        for item in value:
            items.extend(flattened_strings(item))
    elif type(value) is str:
        items.append(value)
    return tuple(items)


def test_routes_cross_validation_tasks_to_human_teams_without_raw_leaks() -> None:
    report = build_report(
        (
            candidate(3, needs_legal_review=True, resolution_risk_score=d("0.910000")),
            candidate(1),
            candidate(
                2,
                independent_source_count=d("1"),
                policy_uncertainty_score=d("0.700000"),
                needs_rules_review=True,
                has_primary_source=False,
            ),
        ),
    )

    assert type(report) is ResearchSourceCrossValidationReport
    assert tuple(route.route_key for route in report.routes) == (
        "route-001",
        "route-002",
        "route-003",
    )
    assert tuple(route.assigned_team for route in report.routes) == (
        "evidence_operations",
        "rules_research",
        "legal_research",
    )
    assert tuple(route.status for route in report.routes) == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = research_source_cross_validation_public_payload(report)
    strings = "\n".join(flattened_strings(payload)).lower()
    for forbidden in (
        "raw-candidate",
        "market-",
        "raw-market-slug",
        "will event",
        "example.invalid",
        "source text snippet",
    ):
        assert forbidden not in strings


def test_pass_watch_and_block_reason_codes_are_deterministic() -> None:
    report = build_report(
        (
            candidate(
                2,
                independent_source_count=d("1"),
                evidence_family_count=d("1"),
                stale_source_count=d("1"),
                has_primary_source=False,
                policy_uncertainty_score=d("0.650000"),
            ),
            candidate(1),
            candidate(
                3,
                contradiction_count=d("1"),
                sensitive_source_count=d("1"),
                resolution_risk_score=d("0.870000"),
            ),
        ),
    )

    pass_route, watch_route, block_route = report.routes

    assert pass_route.status == "pass"
    assert pass_route.reason_codes == ("cross_validation_pass",)
    assert watch_route.status == "watch"
    assert watch_route.reason_codes == (
        "missing_primary_source",
        "needs_evidence_family_diversity",
        "needs_independent_sources",
        "policy_uncertainty_review",
        "stale_source_review",
    )
    assert block_route.status == "block"
    assert block_route.reason_codes == (
        "contradiction_review_required",
        "resolution_risk_review",
        "sensitive_source_manual_review",
    )
    assert report.reason_codes == (
        "contradiction_review_required",
        "cross_validation_block",
        "cross_validation_watch",
        "missing_primary_source",
        "needs_evidence_family_diversity",
        "needs_independent_sources",
        "policy_uncertainty_review",
        "resolution_risk_review",
        "sensitive_source_manual_review",
        "stale_source_review",
    )


def test_decimal_only_validation_rejects_float_int_subclass_and_bad_types() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        candidate(1, urgency_score=0.2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        candidate(1, policy_uncertainty_score=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceCrossValidationConfig(
            min_independent_source_count=2,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="bool"):
        replace(candidate(1), has_primary_source=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="submitted_at"):
        candidate(1, submitted_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="submitted_at"):
        build_report((candidate(1, submitted_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(1), paper_only=False)


def test_public_payload_rejects_leaks_numeric_scalars_false_flags_and_bad_status() -> None:
    payload = research_source_cross_validation_public_payload(build_report((candidate(1),)))

    unsafe_fragments = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    for fragment in unsafe_fragments:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{fragment}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_source_cross_validation_public_payload(unsafe_key_payload)

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["config_version"] = f"contains-{fragment}"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_source_cross_validation_public_payload(unsafe_value_payload)

    numeric_payload = dict(payload)
    numeric_payload["task_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        research_source_cross_validation_public_payload(numeric_payload)

    false_flag_payload = dict(payload)
    false_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_source_cross_validation_public_payload(false_flag_payload)

    bad_status_payload = dict(payload)
    bad_status_payload["status"] = "blocked"
    with pytest.raises(ValueError, match="status"):
        research_source_cross_validation_public_payload(bad_status_payload)


def test_public_payload_digest_and_supabase_summary_are_deterministic() -> None:
    unsorted_candidates = (
        candidate(3, needs_legal_review=True, resolution_risk_score=d("0.910000")),
        candidate(1),
        candidate(2, independent_source_count=d("1"), needs_rules_review=True),
    )
    report = build_report(unsorted_candidates)
    reordered_report = build_report(tuple(reversed(unsorted_candidates)))

    payload = research_source_cross_validation_public_payload(report)
    reordered_payload = research_source_cross_validation_public_payload(reordered_report)
    summary = research_source_cross_validation_supabase_summary(report)

    assert payload == reordered_payload
    assert payload["public_digest"] == report.public_digest
    assert len(report.public_digest) == 64
    int(report.public_digest, 16)
    assert_no_public_numeric_scalars(payload)
    assert validate_research_source_cross_validation_public_payload(payload)
    assert summary["public_digest"] == payload["public_digest"]
    assert summary["routes"] == payload["routes"]
    assert summary["status"] == payload["status"]
    assert_no_public_numeric_scalars(summary)

    tampered = dict(payload)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="public_digest"):
        research_source_cross_validation_public_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("public_digest")
    with pytest.raises(ValueError, match="public_digest"):
        research_source_cross_validation_public_payload(missing_digest)


def test_report_and_route_dataclasses_are_frozen_and_consistent() -> None:
    report = build_report((candidate(1),))
    route = report.routes[0]

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        route.assigned_team = "rules_research"  # type: ignore[misc]

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("2"))

    with pytest.raises(ValueError, match="status"):
        replace(route, status="blocked")

    assert type(route) is ResearchSourceCrossValidationRoute


def test_owned_module_has_no_network_filesystem_or_execution_surface() -> None:
    module_path = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_cross_validation_router.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "connect(",
        "execute(",
        "insert(",
        "update(",
        "delete(",
        "open(",
    )

    assert all(term not in source for term in forbidden_terms)
